"""Multi-project artifact isolation.

Spec References: Sections 3.1.1, 5.1

Each project gets its own directory tree under .agents/pm/projects/{project_id}/
with meta.yaml, artifact subdirectories, evals, logs, and per-agent memory.

Agent Registry Ecosystem
~~~~~~~~~~~~~~~~~~~~~~~~
Four registries must stay in sync when adding, removing, or modifying agents:

1. **PROJECT_AGENTS** (this file)
   Controls which agents get a project-local ``.agents/<name>/AGENTS.md``
   scaffolded by ``init_project()``.  Agents that only need repo-root memory
   (e.g. ``document-renderer``) are intentionally excluded.

2. **PROFILE_REGISTRY** (``subagents/provisioner.py``)
   Declares the middleware stack for each agent.  ``build_provisioning_plan()``
   assembles middleware from these profiles — never hand-roll middleware.

3. **AGENT_MODEL_REGISTRY** (``model_config.py``)
   Per-agent model spec, effort level, and server-tool features.
   ``resolve_agent_model(name)`` looks up this registry.

4. **TOOL_REGISTRY** (``tools/registry.py``)
   Per-agent tool inventory.  SDK-provided tools (filesystem) are noted but
   auto-attached by middleware; custom tools are registered via ``tools=[]``.

Adding a new agent checklist:
  1. Add to PROJECT_AGENTS below (if it needs project-local memory).
  2. Add a SubagentProvisioningProfile to PROFILE_REGISTRY.
  3. Add an AgentModelConfig to AGENT_MODEL_REGISTRY.
  4. Add a tool list to TOOL_REGISTRY.
  5. Create a ``create_<agent>_graph()`` factory in ``subagents/``.
  6. Register the agent config in ``subagents/configs.py``.
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


# Agents that receive project-local .agents/<name>/AGENTS.md scaffolding.
# Must stay in sync with PROFILE_REGISTRY entries where use_project_memory=True.
# document-renderer is intentionally absent (repo-root memory only).
PROJECT_AGENTS = [
    "pm",
    "research-agent",
    "spec-writer",
    "plan-writer",
    "code-agent",
    "verification-agent",
    "evaluation-agent",
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
