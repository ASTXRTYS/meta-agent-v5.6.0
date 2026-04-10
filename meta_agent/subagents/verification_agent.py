"""Verification-agent helpers.
"""

from __future__ import annotations

import json
import re
from typing import Any


VERIFICATION_STATUSES = {"pass", "needs_revision", "blocked"}
REQUIRED_VERDICT_FIELDS = {
    "artifact_type",
    "source_path",
    "status",
    "coverage_summary",
    "gaps",
    "recommended_action",
}


def parse_verification_verdict(text: str) -> dict[str, Any]:
    """Parse the verification-agent JSON verdict from plain text."""
    candidate = text.strip()
    if "```json" in candidate:
        match = re.search(r"```json\s*(\{.*?\})\s*```", candidate, re.DOTALL)
        if match:
            candidate = match.group(1)
    elif "```" in candidate:
        match = re.search(r"```\s*(\{.*?\})\s*```", candidate, re.DOTALL)
        if match:
            candidate = match.group(1)

    verdict = json.loads(candidate)
    missing = REQUIRED_VERDICT_FIELDS - set(verdict.keys())
    if missing:
        raise ValueError(f"Verification verdict missing fields: {sorted(missing)}")
    status = verdict.get("status")
    if status not in VERIFICATION_STATUSES:
        raise ValueError(f"Invalid verification status: {status}")
    if not isinstance(verdict.get("gaps"), list):
        raise ValueError("Verification verdict 'gaps' must be a list")
    return verdict
