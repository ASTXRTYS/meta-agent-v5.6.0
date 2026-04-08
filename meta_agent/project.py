"""Multi-project artifact isolation.

Spec References: Sections 3.1.1, 5.1

Each project gets its own directory tree under .agents/pm/projects/{project_id}/
with meta.yaml, artifact subdirectories, evals, logs, and per-agent memory.

NOTE: Consolidation opportunities:
- _write_yaml() duplicates YAML handling pattern from intake.py (stages/), test_infra.py (evals/infrastructure/)
- PROJECT_AGENTS constant is defined here but .agents/{agent}/AGENTS.md path construction is repeated in:
  * graph.py (root level)
  * research_agent.py, code_agent_runtime.py, plan_writer_runtime.py, verification_agent_runtime.py, evaluation_agent_runtime.py (subagents/)
- slugify() is a common utility that could use python-slugify or similar library
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any


def slugify(name: str) -> str:
    """Convert a project name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def create_thread_id(project_id: str, session_id: str | None = None) -> str:
    """Create a prefixed thread ID for a project."""
    sid = session_id or uuid.uuid4().hex[:8]
    return f"project-{project_id}-{sid}"


# Agent subdirectories created within each project
PROJECT_AGENTS = [
    "pm",
    "research-agent",
    "spec-writer",
    "plan-writer",
    "code-agent",
    "verification-agent",
]


def init_project(
    base_dir: str,
    project_name: str,
    description: str = "",
) -> dict[str, Any]:
    """Initialize a new project directory tree.

    Returns a dict with project_id, project_dir, and thread_id.
    """
    project_id = slugify(project_name)
    project_dir = os.path.join(base_dir, "projects", project_id)

    # Create directory tree
    dirs = [
        project_dir,
        os.path.join(project_dir, "artifacts", "intake"),
        os.path.join(project_dir, "artifacts", "research"),
        os.path.join(project_dir, "artifacts", "spec"),
        os.path.join(project_dir, "artifacts", "planning"),
        os.path.join(project_dir, "artifacts", "audit"),
        os.path.join(project_dir, "evals"),
        os.path.join(project_dir, "logs"),
    ]

    # Per-agent memory dirs
    for agent in PROJECT_AGENTS:
        dirs.append(os.path.join(project_dir, ".agents", agent))

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Create per-agent AGENTS.md files
    for agent in PROJECT_AGENTS:
        agents_md = os.path.join(project_dir, ".agents", agent, "AGENTS.md")
        if not os.path.exists(agents_md):
            with open(agents_md, "w") as f:
                f.write(f"# {agent} — Project Memory\n\n")

    # Create meta.yaml
    meta = {
        "project_name": project_name,
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "current_stage": "INTAKE",
        "description": description,
    }

    meta_path = os.path.join(project_dir, "meta.yaml")
    _write_yaml(meta_path, meta)

    thread_id = create_thread_id(project_id)

    return {
        "project_id": project_id,
        "project_dir": project_dir,
        "thread_id": thread_id,
        "meta": meta,
    }


def _write_yaml(path: str, data: dict) -> None:
    """Write a dict as YAML to a file."""
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback: write as simple key-value pairs
        with open(path, "w") as f:
            for k, v in data.items():
                f.write(f"{k}: {v}\n")
