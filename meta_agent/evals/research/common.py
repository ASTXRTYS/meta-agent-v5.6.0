"""Shared contracts and helpers for research-agent evals."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Mapping

try:
    import yaml

    HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    HAS_YAML = False

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..")
CANONICAL_EVAL_SUITE_PATH = os.path.join(
    ROOT_DIR,
    "workspace",
    "projects",
    "meta-agent",
    "evals",
    "eval-suite-prd.json",
)
CANONICAL_PRD_PATH = os.path.join(
    ROOT_DIR,
    "workspace",
    "projects",
    "meta-agent",
    "artifacts",
    "intake",
    "research-agent-prd.md",
)
CANONICAL_RESEARCH_BUNDLE_PATH = "/workspace/projects/meta-agent/artifacts/research/research-bundle.md"
CANONICAL_RESEARCH_DECOMPOSITION_PATH = "/workspace/projects/meta-agent/artifacts/research/research-decomposition.md"
RESEARCH_BUNDLE_FRONTMATTER_FIELDS = (
    "artifact",
    "project_id",
    "title",
    "version",
    "status",
    "stage",
    "authors",
    "lineage",
)
RESEARCH_BUNDLE_REQUIRED_SECTIONS = (
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


@lru_cache(maxsize=1)
def load_eval_suite() -> dict[str, Any]:
    with open(CANONICAL_EVAL_SUITE_PATH) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_prd_text() -> str:
    with open(CANONICAL_PRD_PATH) as f:
        return f.read()


@lru_cache(maxsize=1)
def get_canonical_eval_ids() -> tuple[str, ...]:
    data = load_eval_suite()
    return tuple(ev["id"] for ev in data.get("evals", []))


@lru_cache(maxsize=1)
def get_likert_eval_ids() -> tuple[str, ...]:
    data = load_eval_suite()
    return tuple(ev["id"] for ev in data.get("evals", []) if "anchors" in ev)


def validate_registry_ids(registry: Mapping[str, Any]) -> None:
    expected = set(get_canonical_eval_ids())
    actual = set(registry)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(
            f"Research eval registry mismatch. Missing={missing} Extra={extra}"
        )


def make_result(
    score: int,
    comment: str,
    *,
    reasoning: str | None = None,
    evidence: list[str] | None = None,
    confidence: str | None = None,
    flags: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "score": score,
        "comment": comment,
        "reasoning": reasoning or comment,
        "evidence": evidence or [],
        "confidence": confidence or _default_confidence(score),
        "flags": flags or [],
    }
    if details is not None:
        result["details"] = details
    return result


def _default_confidence(score: int) -> str:
    if score == -1:
        return "LOW"
    return "HIGH"


def normalize_url(url: str) -> str:
    return url.rstrip("/").rstrip(".").rstrip(",")


def extract_urls(text: str) -> list[str]:
    return [normalize_url(u) for u in re.findall(r'https?://[^\s\)>\]"\']+', text or "")]


def get_arg_path(args: Mapping[str, Any] | None) -> str:
    args = args or {}
    return str(args.get("file_path", args.get("path", "")))


def normalize_workspace_path(path: str) -> str:
    if not path:
        return path
    if path.endswith("/workspace/projects/meta-agent/artifacts/intake/prd.md"):
        return "/workspace/projects/meta-agent/artifacts/intake/research-agent-prd.md"
    if path.endswith("/workspace/projects/meta-agent/evals/eval-suite-prd.yaml"):
        return "/workspace/projects/meta-agent/evals/eval-suite-prd.json"
    return path


def extract_yaml_frontmatter(text: str) -> dict[str, Any] | None:
    if not text:
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    if HAS_YAML:
        try:
            frontmatter = yaml.safe_load(parts[1])
        except Exception:
            return None
        return frontmatter if isinstance(frontmatter, dict) else None

    frontmatter: dict[str, Any] = {}
    for line in parts[1].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("-") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    return frontmatter or None


def missing_research_bundle_frontmatter_fields(text: str) -> list[str]:
    frontmatter = extract_yaml_frontmatter(text)
    if not frontmatter:
        return list(RESEARCH_BUNDLE_FRONTMATTER_FIELDS)
    return [
        field
        for field in RESEARCH_BUNDLE_FRONTMATTER_FIELDS
        if field not in frontmatter
    ]


def normalize_markdown_heading(heading: str) -> str:
    normalized = heading.strip()
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = re.sub(r"^\d+(?:\.\d+)*[\)\.\-:]\s*", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.casefold()


def _heading_level(line: str) -> int:
    stripped = line.lstrip()
    level = len(stripped) - len(stripped.lstrip("#"))
    return level if level > 0 else 0


def find_markdown_headings(text: str, *, level: int | None = None) -> list[str]:
    if not text:
        return []
    headings: list[str] = []
    for line in text.splitlines():
        current_level = _heading_level(line)
        if current_level == 0:
            continue
        if level is not None and current_level != level:
            continue
        headings.append(line.strip())
    return headings


def present_research_bundle_sections(text: str) -> list[str]:
    normalized_titles = {
        normalize_markdown_heading(title): title
        for title in RESEARCH_BUNDLE_REQUIRED_SECTIONS
    }
    present: list[str] = []
    for heading in find_markdown_headings(text, level=2):
        canonical = normalized_titles.get(normalize_markdown_heading(heading))
        if canonical and canonical not in present:
            present.append(canonical)
    return present


def missing_research_bundle_sections(text: str) -> list[str]:
    present = set(present_research_bundle_sections(text))
    return [
        title for title in RESEARCH_BUNDLE_REQUIRED_SECTIONS if title not in present
    ]


def get_timestamp(tool_call: Mapping[str, Any]) -> float | None:
    value = tool_call.get("timestamp")
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def extract_functional_requirements(prd_text: str | None = None) -> list[dict[str, Any]]:
    text = prd_text or load_prd_text()
    lines = text.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Functional Requirements":
            start_idx = idx + 1
            break
    if start_idx is None:
        return []

    requirements: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    heading_re = re.compile(r"^###\s+([A-Z])\.\s+(.*)$")
    bullet_re = re.compile(r"^\s*-\s+(.*)$")

    for raw_line in lines[start_idx:]:
        if raw_line.startswith("## ") and not raw_line.startswith("### "):
            break
        heading_match = heading_re.match(raw_line.strip())
        if heading_match:
            if current:
                requirements.append(current)
            current = {
                "label": heading_match.group(1),
                "id": f"FR-{heading_match.group(1)}",
                "title": heading_match.group(2).strip(),
                "bullets": [],
            }
            continue
        if current is None:
            continue
        bullet_match = bullet_re.match(raw_line)
        if bullet_match:
            current["bullets"].append(bullet_match.group(1).strip())

    if current:
        requirements.append(current)

    return requirements


def format_fr_checklist(prd_text: str | None = None) -> str:
    requirements = extract_functional_requirements(prd_text)
    parts = []
    for requirement in requirements:
        bullets = requirement.get("bullets", [])
        preview = "; ".join(bullets[:3])
        if len(bullets) > 3:
            preview += "; ..."
        parts.append(
            f"{requirement['id']} {requirement['title']}: {preview}".rstrip(": ")
        )
    return "\n".join(parts)


def extract_markdown_section(
    text: str,
    heading_prefix: str | tuple[str, ...],
    *,
    level: int = 2,
) -> str:
    if not text:
        return ""
    targets = (heading_prefix,) if isinstance(heading_prefix, str) else heading_prefix
    normalized_targets = {normalize_markdown_heading(target) for target in targets}
    lines = text.splitlines()
    start = None
    start_level = level
    for idx, line in enumerate(lines):
        current_level = _heading_level(line)
        if current_level == 0:
            continue
        stripped = line.strip()
        if current_level == level and normalize_markdown_heading(stripped) in normalized_targets:
            start = idx
            start_level = current_level
            break
    if start is None:
        return ""

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        current_level = _heading_level(lines[idx])
        if current_level and current_level <= start_level:
            end = idx
            break

    return "\n".join(lines[start:end]).strip()
