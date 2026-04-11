"""Document renderer subagent configuration.

Spec References: Sections 6.9, 6.9.1-6.9.3

Deep Agent that renders Markdown artifacts to DOCX and PDF formats.
Utilizes MemoryMiddleware for stateful document rendering context.

- Tools: read_file, write_file
- Skills: docx, pdf
- Effort: low
- Rendering trigger: PRD (INTAKE/PRD_REVIEW) -> DOCX + PDF
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from meta_agent.backend import create_bare_filesystem_backend, create_composite_backend, create_store, create_checkpointer
from meta_agent.model_config import resolve_agent_model
from meta_agent.subagents.provisioner import build_provisioning_plan


PROMPT_MARKDOWN_PATH = Path(__file__).resolve().parent.parent / "prompts" / "Document_Renderer_System_Prompt.md"


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


# Canonical description shared by both PM and research-agent subagent lists.
DOCUMENT_RENDERER_DESCRIPTION = (
    "Document formatter. Converts Markdown artifacts into "
    "professionally formatted DOCX and PDF files."
)

# Canonical system prompt for the document-renderer subagent.
DOCUMENT_RENDERER_SYSTEM_PROMPT = _load_prompt_markdown()


def create_document_renderer_subagent(
    skills_dirs: list[str] | None = None,
) -> CompiledSubAgent:
    """Build an SDK-compatible CompiledSubAgent for the document-renderer.

    Args:
        skills_dirs: Resolved skill directory paths.

    Returns:
        CompiledSubAgent ready for the orchestrator.
    """
    resolution = resolve_agent_model('document-renderer')
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()
    provisioning_plan = build_provisioning_plan(
        agent_name="document-renderer",
        model_spec=resolution.model_spec,
        summarization_model=resolution.model,
        project_dir="",
        repo_root=repo_root,
        composite_backend=composite_backend,
        bare_fs=bare_fs,
        skills_dirs=skills_dirs,
    )

    graph = create_deep_agent(
        model=resolution.model,
        tools=[],  # Filesystem tools auto-attached
        system_prompt=DOCUMENT_RENDERER_SYSTEM_PROMPT,
        middleware=provisioning_plan.middleware,
        skills=provisioning_plan.deep_agent_skills,
        backend=composite_backend,
        checkpointer=create_checkpointer(),
        store=create_store(),
        name="document-renderer",
    )

    return CompiledSubAgent(
        name="document-renderer",
        description=DOCUMENT_RENDERER_DESCRIPTION,
        runnable=graph,
    )

