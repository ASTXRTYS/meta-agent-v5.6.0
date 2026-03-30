"""Phase 3 gate evals (Layer 1): structural checks for research and spec artifacts.

These 7 evals verify that Phase 3 artifacts exist and meet structural
requirements.  They run as the phase gate — all must pass before Phase 4
can begin.

Layer 2 (38 research-agent behavioral evals) lives in meta_agent/evals/research/.

Eval IDs per development plan Section 3.3.1:

Binary:
  RESEARCH-001  Research bundle exists at correct path
  RESEARCH-002  Research bundle has PRD Coverage Matrix section
  SPEC-001      Technical specification exists at correct path
  SPEC-002      Spec has PRD Traceability Matrix with 100% coverage
  SPEC-003      Tier 2 eval suite JSON exists

Likert (deterministic proxies, upgradeable to LLM-as-judge):
  RESEARCH-003  Research quality — all 17 sections + PRD requirement mentions
  SPEC-004      Spec quality — all required sections + YAML frontmatter
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RESEARCH_BUNDLE_REL_PATH = "artifacts/research/research-bundle.md"
SPEC_REL_PATH = "artifacts/spec/technical-specification.md"
TIER2_EVAL_REL_PATH = "evals/eval-suite-architecture.json"

# Canonical 17 required sections for the research bundle (mirrors
# meta_agent.evals.research.common.RESEARCH_BUNDLE_REQUIRED_SECTIONS).
RESEARCH_BUNDLE_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Ecosystem Options with Tradeoffs",
    "Rejected Alternatives with Rationale",
    "Model Capability Matrix",
    "Technology Decision Trees",
    "Tool/Framework Capability Maps",
    "Pattern & Best Practice Catalog",
    "Integration Dependency Matrix",
    "SME Perspectives",
    "Risks and Caveats",
    "Confidence Assessment per Domain",
    "Research Methodology",
    "Unresolved Questions for Spec-Writer",
    "PRD Coverage Matrix",
    "Unresolved Research Gaps",
    "Skills Baseline Summary",
    "Gap and Contradiction Remediation Log",
    "Citation Index",
)

# Required sections for the technical specification (from spec-writer prompt).
SPEC_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Architecture Overview",
    "State Model",
    "Artifact Schemas",
    "Prompt Strategy",
    "System Prompts",
    "Tool Descriptions and Contracts",
    "Human Review Flows",
    "API Contracts",
    "Environment Configuration",
    "Testing Strategy",
    "Evaluation Strategy",
    "Error Handling",
    "Observability",
    "Safety and Guardrails",
    "Known Risks and Mitigations",
    "PRD Traceability Matrix",
    "Specification Gaps",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(path: str) -> str | None:
    """Read file contents, returning None if missing or unreadable."""
    try:
        with open(path) as f:
            return f.read()
    except (OSError, IOError):
        return None


def _normalize_heading(text: str) -> str:
    """Strip markdown heading markers and collapse whitespace for comparison."""
    text = re.sub(r"^#+\s*", "", text.strip())
    text = re.sub(r"^\d+(?:\.\d+)*[\)\.\-:]\s*", "", text)
    return re.sub(r"\s+", " ", text).casefold()


def _find_headings(content: str) -> list[str]:
    """Return all markdown headings (any level) from *content*."""
    headings: list[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            headings.append(stripped)
    return headings


def _present_sections(content: str, required: tuple[str, ...]) -> list[str]:
    """Return the subset of *required* sections found as headings in *content*."""
    normalized_map = {_normalize_heading(s): s for s in required}
    found: list[str] = []
    for heading in _find_headings(content):
        canonical = normalized_map.get(_normalize_heading(heading))
        if canonical and canonical not in found:
            found.append(canonical)
    return found


def _missing_sections(content: str, required: tuple[str, ...]) -> list[str]:
    """Return the subset of *required* sections NOT found in *content*."""
    present = set(_present_sections(content, required))
    return [s for s in required if s not in present]


def _has_yaml_frontmatter(content: str) -> bool:
    """Return True if *content* starts with valid YAML frontmatter."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False
    raw = parts[1].strip()
    if not raw:
        return False
    if HAS_YAML:
        try:
            parsed = yaml.safe_load(raw)
            return isinstance(parsed, dict)
        except Exception:
            return False
    # Fallback: at least one key: value line
    return any(":" in line for line in raw.splitlines())


def _count_prd_requirement_mentions(content: str, minimum: int = 3) -> tuple[bool, list[str]]:
    """Check that *content* references at least *minimum* distinct PRD requirements.

    Looks for patterns like FR-A, FR-B, REQ-001, R-1, etc.  Returns
    (passes, list_of_found_ids).
    """
    # Match common requirement ID patterns
    ids = set(re.findall(r"\bFR-[A-Z]\b", content, re.IGNORECASE))
    ids |= set(re.findall(r"\bREQ-\d+\b", content, re.IGNORECASE))
    ids |= set(re.findall(r"\bR-\d+\b", content, re.IGNORECASE))
    sorted_ids = sorted(ids)
    return len(sorted_ids) >= minimum, sorted_ids


# ---------------------------------------------------------------------------
# Binary evals
# ---------------------------------------------------------------------------

def eval_research_001(project_dir: str) -> dict[str, Any]:
    """RESEARCH-001: Research bundle exists at correct path.

    Binary — checks that the research bundle markdown file is present.
    """
    path = os.path.join(project_dir, RESEARCH_BUNDLE_REL_PATH)
    exists = os.path.isfile(path)
    return {
        "pass": exists,
        "score": 1.0 if exists else 0.0,
        "reason": (
            f"Research bundle found at {path}"
            if exists
            else f"Research bundle not found at {path}"
        ),
    }


def eval_research_002(project_dir: str) -> dict[str, Any]:
    """RESEARCH-002: Research bundle has PRD Coverage Matrix section.

    Binary — checks for the presence of the 'PRD Coverage Matrix' heading.
    """
    path = os.path.join(project_dir, RESEARCH_BUNDLE_REL_PATH)
    content = _read_file(path)
    if content is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Cannot read research bundle at {path}",
        }

    present = _present_sections(content, ("PRD Coverage Matrix",))
    found = len(present) > 0
    return {
        "pass": found,
        "score": 1.0 if found else 0.0,
        "reason": (
            "PRD Coverage Matrix section present in research bundle"
            if found
            else "PRD Coverage Matrix section missing from research bundle"
        ),
    }


def eval_spec_001(project_dir: str) -> dict[str, Any]:
    """SPEC-001: Technical specification exists at correct path.

    Binary — checks that the spec markdown file is present.
    """
    path = os.path.join(project_dir, SPEC_REL_PATH)
    exists = os.path.isfile(path)
    return {
        "pass": exists,
        "score": 1.0 if exists else 0.0,
        "reason": (
            f"Technical specification found at {path}"
            if exists
            else f"Technical specification not found at {path}"
        ),
    }


def eval_spec_002(project_dir: str) -> dict[str, Any]:
    """SPEC-002: Spec has PRD Traceability Matrix with 100% coverage confirmed.

    Binary — verifies the 'PRD Traceability Matrix' heading exists and the
    section body contains an explicit 100% coverage assertion.
    """
    path = os.path.join(project_dir, SPEC_REL_PATH)
    content = _read_file(path)
    if content is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Cannot read spec at {path}",
        }

    # Check heading exists
    present = _present_sections(content, ("PRD Traceability Matrix",))
    if not present:
        return {
            "pass": False,
            "score": 0.0,
            "reason": "PRD Traceability Matrix section missing from spec",
        }

    # Extract the section body to check for 100% coverage assertion
    section_text = _extract_section_body(content, "PRD Traceability Matrix")
    has_full_coverage = bool(
        re.search(r"100\s*%", section_text)
        or "full coverage" in section_text.lower()
        or "all requirements" in section_text.lower()
        or "complete coverage" in section_text.lower()
    )

    return {
        "pass": has_full_coverage,
        "score": 1.0 if has_full_coverage else 0.0,
        "reason": (
            "PRD Traceability Matrix present with 100% coverage confirmed"
            if has_full_coverage
            else "PRD Traceability Matrix present but no 100% coverage assertion found"
        ),
    }


def _extract_section_body(content: str, heading_title: str) -> str:
    """Extract the body text under a given heading (up to the next same-level heading)."""
    target_norm = _normalize_heading(heading_title)
    lines = content.splitlines()
    start_idx = None
    start_level = 0

    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if _normalize_heading(stripped) == target_norm:
            start_idx = idx + 1
            start_level = level
            break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        stripped = lines[idx].lstrip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if level <= start_level:
            end_idx = idx
            break

    return "\n".join(lines[start_idx:end_idx])


def eval_spec_003(project_dir: str) -> dict[str, Any]:
    """SPEC-003: Tier 2 eval suite created (eval-suite-architecture.json exists).

    Binary — checks for the eval suite JSON artifact.
    """
    path = os.path.join(project_dir, TIER2_EVAL_REL_PATH)
    exists = os.path.isfile(path)

    if not exists:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Tier 2 eval suite not found at {path}",
        }

    # Bonus: verify it's valid JSON (fail fast on corrupt files)
    content = _read_file(path)
    if content is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Cannot read eval suite at {path}",
        }
    try:
        json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Eval suite exists but is not valid JSON: {e}",
        }

    return {
        "pass": True,
        "score": 1.0,
        "reason": f"Tier 2 eval suite exists at {path} and is valid JSON",
    }


# ---------------------------------------------------------------------------
# Likert evals (deterministic proxies — upgradeable to LLM-as-judge)
# ---------------------------------------------------------------------------

def eval_research_003(project_dir: str) -> dict[str, Any]:
    """RESEARCH-003: Research quality.

    Deterministic proxy for a Likert eval:
    - Checks that all 17 required sections are present
    - Checks that at least 3 distinct PRD requirement IDs are mentioned

    Scoring (1-5):
      5: all 17 sections + >= 3 PRD req mentions
      4: >= 15 sections + >= 3 PRD req mentions
      3: >= 12 sections + >= 1 PRD req mention
      2: >= 8 sections
      1: < 8 sections or bundle unreadable
    """
    path = os.path.join(project_dir, RESEARCH_BUNDLE_REL_PATH)
    content = _read_file(path)

    if content is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Cannot read research bundle at {path}",
        }

    present = _present_sections(content, RESEARCH_BUNDLE_REQUIRED_SECTIONS)
    missing = _missing_sections(content, RESEARCH_BUNDLE_REQUIRED_SECTIONS)
    section_count = len(present)

    prd_ok, prd_ids = _count_prd_requirement_mentions(content, minimum=3)
    prd_any = len(prd_ids) >= 1

    # Determine Likert score
    if section_count == len(RESEARCH_BUNDLE_REQUIRED_SECTIONS) and prd_ok:
        score = 5.0
    elif section_count >= 15 and prd_ok:
        score = 4.0
    elif section_count >= 12 and prd_any:
        score = 3.0
    elif section_count >= 8:
        score = 2.0
    else:
        score = 1.0

    passes = score >= 3.0  # Threshold per spec is >= 3.0

    reason_parts = [f"{section_count}/{len(RESEARCH_BUNDLE_REQUIRED_SECTIONS)} required sections present"]
    if missing:
        reason_parts.append(f"missing: {missing}")
    reason_parts.append(f"{len(prd_ids)} PRD requirement IDs mentioned: {prd_ids}")

    return {
        "pass": passes,
        "score": score,
        "reason": "; ".join(reason_parts),
    }


def eval_spec_004(project_dir: str) -> dict[str, Any]:
    """SPEC-004: Spec quality.

    Deterministic proxy for a Likert eval:
    - Checks that all required spec sections are present
    - Checks that the spec has YAML frontmatter

    Scoring (1-5):
      5: all 17 sections + frontmatter
      4: >= 15 sections + frontmatter
      3: >= 12 sections (frontmatter optional at this tier)
      2: >= 8 sections
      1: < 8 sections or spec unreadable
    """
    path = os.path.join(project_dir, SPEC_REL_PATH)
    content = _read_file(path)

    if content is None:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Cannot read spec at {path}",
        }

    present = _present_sections(content, SPEC_REQUIRED_SECTIONS)
    missing = _missing_sections(content, SPEC_REQUIRED_SECTIONS)
    section_count = len(present)
    has_frontmatter = _has_yaml_frontmatter(content)

    # Determine Likert score
    if section_count == len(SPEC_REQUIRED_SECTIONS) and has_frontmatter:
        score = 5.0
    elif section_count >= 15 and has_frontmatter:
        score = 4.0
    elif section_count >= 12:
        score = 3.0
    elif section_count >= 8:
        score = 2.0
    else:
        score = 1.0

    passes = score >= 3.0  # Threshold per spec is >= 3.0

    reason_parts = [f"{section_count}/{len(SPEC_REQUIRED_SECTIONS)} required sections present"]
    if missing:
        reason_parts.append(f"missing: {missing}")
    reason_parts.append(f"YAML frontmatter: {'present' if has_frontmatter else 'absent'}")

    return {
        "pass": passes,
        "score": score,
        "reason": "; ".join(reason_parts),
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PHASE3_GATE_EVAL_REGISTRY: dict[str, dict[str, Any]] = {
    "RESEARCH-001": {
        "fn": eval_research_001,
        "name": "Research Bundle Exists",
        "type": "binary",
        "threshold": 1.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "RESEARCH-002": {
        "fn": eval_research_002,
        "name": "Research Bundle Has PRD Coverage Matrix",
        "type": "binary",
        "threshold": 1.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "RESEARCH-003": {
        "fn": eval_research_003,
        "name": "Research Quality",
        "type": "likert",
        "threshold": 3.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "SPEC-001": {
        "fn": eval_spec_001,
        "name": "Technical Specification Exists",
        "type": "binary",
        "threshold": 1.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "SPEC-002": {
        "fn": eval_spec_002,
        "name": "Spec Has PRD Traceability Matrix",
        "type": "binary",
        "threshold": 1.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "SPEC-003": {
        "fn": eval_spec_003,
        "name": "Tier 2 Eval Suite Created",
        "type": "binary",
        "threshold": 1.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
    "SPEC-004": {
        "fn": eval_spec_004,
        "name": "Spec Quality",
        "type": "likert",
        "threshold": 3.0,
        "category": "phase3_gate",
        "priority": "P0",
        "phase": 3,
        "input_type": "project_dir",
    },
}

# Convenience: list of all Phase 3 gate eval IDs in canonical order.
PHASE3_GATE_EVAL_IDS: list[str] = [
    "RESEARCH-001",
    "RESEARCH-002",
    "RESEARCH-003",
    "SPEC-001",
    "SPEC-002",
    "SPEC-003",
    "SPEC-004",
]
