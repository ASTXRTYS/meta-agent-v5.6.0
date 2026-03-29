"""Shared contracts and helpers for research-agent evals."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Mapping

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
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(target) for target in targets):
            start = idx
            break
    if start is None:
        return ""

    stop_prefix = "#" * level + " "
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith(stop_prefix):
            end = idx
            break

    return "\n".join(lines[start:end]).strip()
