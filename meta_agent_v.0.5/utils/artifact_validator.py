from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class SectionSpec(BaseModel):
    name: str
    required: bool = True
    match_strategy: Literal["exact", "prefix", "regex"] = "exact"


class NestedKeySpec(BaseModel):
    name: str
    required: bool = True


class ArtifactProtocol(BaseModel):
    artifact_type: str
    format: Literal["markdown", "json"]
    required_frontmatter_fields: list[str] = Field(default_factory=list)
    required_sections: list[SectionSpec] = Field(default_factory=list)
    required_nested_keys: dict[str, list[NestedKeySpec]] = Field(default_factory=dict)


class Violation(BaseModel):
    violation_type: str
    detail: str
    expected: str | None = None


class ValidationResult(BaseModel):
    passed: bool
    completeness_score: float
    violations: list[Violation] = Field(default_factory=list)
    omission_log: list[str] = Field(default_factory=list)
    artifact_type: str
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _validate_markdown(content: str, protocol: ArtifactProtocol) -> ValidationResult:
    """Validate a markdown artifact against a protocol."""
    violations: list[Violation] = []
    omission_log: list[str] = []
    
    # Track counts for completeness score
    total_elements = len(protocol.required_frontmatter_fields) + len(protocol.required_sections)
    present_elements = 0
    
    if not content.strip():
        violations.append(Violation(violation_type="empty_content", detail="Artifact content is empty"))
        return ValidationResult(
            passed=False,
            completeness_score=0.0,
            violations=violations,
            artifact_type=protocol.artifact_type,
        )

    # 1. Parse frontmatter
    # Regex looks for --- at the start, followed by content, followed by ---
    frontmatter_match = re.match(r"^\s*---\s*\n(.*?)\n\s*---\s*\n", content, re.DOTALL)
    frontmatter_data = {}
    if frontmatter_match:
        try:
            frontmatter_data = yaml.safe_load(frontmatter_match.group(1)) or {}
            if not isinstance(frontmatter_data, dict):
                frontmatter_data = {}
        except yaml.YAMLError:
            pass  # Handled below by missing frontmatter logic
            
    # Check frontmatter fields
    for field in protocol.required_frontmatter_fields:
        if field in frontmatter_data:
            present_elements += 1
        else:
            violations.append(
                Violation(
                    violation_type="missing_frontmatter",
                    detail=f"Required frontmatter field '{field}' is missing",
                    expected=field,
                )
            )

    # 2. Extract Markdown headings
    # Match lines that start with 1 to 6 #'s
    headings = []
    for line in content.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if heading_match:
            headings.append(heading_match.group(2).strip())

    # 3. Check sections against protocol
    for spec in protocol.required_sections:
        found = False
        for heading in headings:
            if spec.match_strategy == "exact":
                if heading.lower() == spec.name.lower():
                    found = True
                    break
            elif spec.match_strategy == "prefix":
                if heading.lower().startswith(spec.name.lower()):
                    found = True
                    break
            elif spec.match_strategy == "regex":
                if re.search(spec.name, heading, re.IGNORECASE):
                    found = True
                    break
                    
        if found:
            present_elements += 1
        else:
            if spec.required:
                violations.append(
                    Violation(
                        violation_type="missing_section",
                        detail=f"Required section '{spec.name}' is missing",
                        expected=spec.name,
                    )
                )
            else:
                omission_log.append(spec.name)

    passed = len(violations) == 0
    score = present_elements / total_elements if total_elements > 0 else 1.0

    return ValidationResult(
        passed=passed,
        completeness_score=score,
        violations=violations,
        omission_log=omission_log,
        artifact_type=protocol.artifact_type,
    )


def _validate_json(content: str, protocol: ArtifactProtocol) -> ValidationResult:
    """Validate a JSON artifact against a protocol."""
    violations: list[Violation] = []
    omission_log: list[str] = []
    
    # Track counts for completeness score (JSON doesn't use frontmatter)
    total_elements = len(protocol.required_sections)
    present_elements = 0
    
    if not content.strip():
        violations.append(Violation(violation_type="empty_content", detail="Artifact content is empty"))
        return ValidationResult(
            passed=False,
            completeness_score=0.0,
            violations=violations,
            artifact_type=protocol.artifact_type,
        )

    try:
        data = json.loads(content)
        if not isinstance(data, dict):
             violations.append(Violation(violation_type="invalid_json", detail="JSON root must be an object"))
             return ValidationResult(
                passed=False,
                completeness_score=0.0,
                violations=violations,
                artifact_type=protocol.artifact_type,
             )
    except json.JSONDecodeError as e:
        violations.append(Violation(violation_type="invalid_json", detail=f"Failed to parse JSON: {e}"))
        return ValidationResult(
            passed=False,
            completeness_score=0.0,
            violations=violations,
            artifact_type=protocol.artifact_type,
        )

    # Note: For JSON format, required_sections items are treated as top-level keys
    for spec in protocol.required_sections:
        if spec.name in data:
            present_elements += 1
            
            # Additional logic for 'evals' array as specified in design
            if spec.name == "evals":
                val = data.get("evals")
                if isinstance(val, list) and len(val) == 0:
                    # Note: we don't decrement present_elements since the key IS present,
                    # but we add a violation because it's empty
                    violations.append(
                        Violation(
                            violation_type="empty_evals_array",
                            detail="'evals' key is present but contains an empty array",
                        )
                    )
                elif not isinstance(val, list):
                    # Edge case: key is present but not an array
                     violations.append(
                        Violation(
                            violation_type="invalid_type",
                            detail="'evals' key must be an array",
                        )
                    )

            # Check nested keys if defined for this top level key
            if spec.name in protocol.required_nested_keys:
                nested_obj = data.get(spec.name)
                if not isinstance(nested_obj, dict):
                    violations.append(
                        Violation(
                            violation_type="invalid_type",
                            detail=f"'{spec.name}' must be an object to check nested keys",
                        )
                    )
                else:
                    for nested_spec in protocol.required_nested_keys[spec.name]:
                        if nested_spec.name not in nested_obj:
                            if nested_spec.required:
                                violations.append(
                                    Violation(
                                        violation_type="missing_nested_key",
                                        detail=f"Required nested key '{nested_spec.name}' is missing in '{spec.name}'",
                                        expected=nested_spec.name,
                                    )
                                )
                            else:
                                omission_log.append(f"{spec.name}.{nested_spec.name}")
        else:
            if spec.required:
                violations.append(
                    Violation(
                        violation_type="missing_section",
                        detail=f"Required key '{spec.name}' is missing",
                        expected=spec.name,
                    )
                )
            else:
                omission_log.append(spec.name)

    passed = len(violations) == 0
    score = present_elements / total_elements if total_elements > 0 else 1.0

    return ValidationResult(
        passed=passed,
        completeness_score=score,
        violations=violations,
        omission_log=omission_log,
        artifact_type=protocol.artifact_type,
    )


def validate(content: str, protocol: ArtifactProtocol) -> ValidationResult:
    """Validate artifact content against a protocol. Pure function — no I/O."""
    if protocol.format == "markdown":
        return _validate_markdown(content, protocol)
    return _validate_json(content, protocol)
