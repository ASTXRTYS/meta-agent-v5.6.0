"""Safety and guardrails foundation.

Spec References: Sections 19.1-19.6, 19.8

File system restrictions, command execution guardrails, recursion limits,
token budget guards, and eval dataset immutability.
"""

from __future__ import annotations

import os
from typing import Any


# ---------------------------------------------------------------------------
# Recursion limits per agent — Section 19.5
# ---------------------------------------------------------------------------

RECURSION_LIMITS: dict[str, int] = {
    "pm": 200,
    "code-agent": 150,
    "research-agent": 100,
    "spec-writer": 50,
    "plan-writer": 50,
    "verification-agent": 50,
    "test-agent": 50,
    "document-renderer": 50,
    "observation-agent": 50,
    "evaluation-agent": 50,
    "audit-agent": 50,
}


# ---------------------------------------------------------------------------
# Token budget guards — Section 19.6
# ---------------------------------------------------------------------------

TOKEN_BUDGET_LIMITS: dict[str, int] = {
    "default": 100_000,
    "research-agent": 1_000_000,
    "spec-writer": 200_000,
    "verification-agent": 200_000,
}


def get_token_budget(agent_name: str) -> int:
    """Get the token budget warning threshold for an agent."""
    return TOKEN_BUDGET_LIMITS.get(agent_name, TOKEN_BUDGET_LIMITS["default"])


# ---------------------------------------------------------------------------
# File system restrictions — Section 19.1
# ---------------------------------------------------------------------------

FILESYSTEM_CONFIG = {
    "virtual_mode": True,
    "block_path_traversal": True,
    "block_symlinks": True,
}


def validate_path(path: str, workspace_root: str = "workspace") -> bool:
    """Validate a file path against safety restrictions.

    Blocks path traversal (../) and symlinks.
    """
    # Block path traversal
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        return False

    # Block absolute paths outside workspace
    if os.path.isabs(path):
        abs_workspace = os.path.abspath(workspace_root)
        if not os.path.abspath(path).startswith(abs_workspace):
            return False

    # Block symlinks
    full_path = os.path.join(workspace_root, path) if not os.path.isabs(path) else path
    if os.path.islink(full_path):
        return False

    return True


# ---------------------------------------------------------------------------
# Command execution guardrails — Section 19.2
# ---------------------------------------------------------------------------

COMMAND_EXECUTION_CONFIG = {
    "hitl_gated": True,  # Always requires HITL approval
    "timeout_seconds": 300,
    "working_dir_restriction": "/workspace/",
}


def validate_command(command: str, working_dir: str = "") -> dict[str, Any]:
    """Validate a command against execution guardrails.

    All commands are HITL-gated. This function pre-validates.
    """
    result: dict[str, Any] = {
        "allowed": True,
        "hitl_required": True,
        "timeout": COMMAND_EXECUTION_CONFIG["timeout_seconds"],
        "warnings": [],
    }

    # Check working directory restriction
    if working_dir and not working_dir.startswith("/workspace/"):
        if not working_dir.startswith("workspace"):
            result["warnings"].append(
                f"Working directory '{working_dir}' is outside /workspace/"
            )

    return result


# ---------------------------------------------------------------------------
# Eval dataset immutability — Section 19.8
# ---------------------------------------------------------------------------

def is_eval_immutable(current_stage: str) -> bool:
    """Check if eval datasets are read-only in the current stage.

    Eval datasets are immutable during EXECUTION stage.
    Only user via HITL can modify them.
    """
    return current_stage == "EXECUTION"


def validate_eval_write(
    current_stage: str, path: str, is_hitl: bool = False
) -> bool:
    """Check if writing to an eval file is allowed.

    Returns True if the write is permitted.
    """
    if not is_eval_immutable(current_stage):
        return True

    # During EXECUTION, only HITL-approved writes are allowed
    if is_hitl:
        return True

    # Check if the path is an eval file
    if "/evals/" in path or path.endswith((".yaml", ".yml")):
        return False

    return True
