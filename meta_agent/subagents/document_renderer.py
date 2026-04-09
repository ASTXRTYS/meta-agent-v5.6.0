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

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent
from meta_agent.backend import create_bare_filesystem_backend, create_composite_backend, create_store, create_checkpointer
from meta_agent.model import get_configured_model
from meta_agent.subagents.provisioner import build_provisioning_plan


PROMPT_MARKDOWN_PATH = Path(__file__).resolve().parent.parent / "prompts" / "Document_Renderer_System_Prompt.md"


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()




# Rendering triggers per Section 6.9.2
RENDERING_TRIGGERS: dict[str, list[str]] = {
    "INTAKE": ["prd"],
    "PRD_REVIEW": ["prd"],
    "SPEC_GENERATION": ["technical-specification"],
    "SPEC_REVIEW": ["technical-specification"],
    "PLANNING": ["implementation-plan"],
}

# Output format per Section 6.9.3
OUTPUT_FORMATS = ["docx", "pdf"]


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
    model = get_configured_model(effort="low")
    repo_root = Path(__file__).resolve().parents[2]
    composite_backend = create_composite_backend(repo_root)
    bare_fs = create_bare_filesystem_backend()
    provisioning_plan = build_provisioning_plan(
        agent_name="document-renderer",
        project_dir="",
        repo_root=repo_root,
        composite_backend=composite_backend,
        bare_fs=bare_fs,
        skills_dirs=skills_dirs,
    )

    graph = create_deep_agent(
        model=model,
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





def should_render(stage: str, artifact_name: str) -> bool:
    """Check if an artifact should be rendered in the given stage."""
    triggers = RENDERING_TRIGGERS.get(stage, [])
    return artifact_name in triggers


def get_output_path(source_path: str, output_format: str) -> str:
    """Get the output path for a rendered document.

    Per Section 6.9.3: rendered docs alongside source Markdown.
    """
    # ⚠️ INCONSISTENT: Using os.path despite importing pathlib.Path
    # Other agents use Path operations consistently. TODO: Use Path(source_path).stem
    base, _ = os.path.splitext(source_path)
    return f"{base}.{output_format}"


def render_artifact(
    source_path: str,
    stage: str,
) -> dict[str, Any]:
    """Render an artifact to DOCX and PDF formats.

    ⚠️ STUB IMPLEMENTATION — DOES NOT ACTUALLY RENDER
    This function returns "status": "pending" and defers to the subagent,
    but the subagent invocation logic is elsewhere (or missing). The actual
    rendering to DOCX/PDF never occurs in this code path.
    
    TODO: Either implement actual rendering here via skills/docx/pdf, or
    remove this function and wire the subagent invocation properly.

    Per Section 6.9.3, rendered documents are placed alongside the source
    Markdown and regenerated on revision.

    Args:
        source_path: Path to the source Markdown file.
        stage: Current workflow stage.

    Returns:
        Dict with render results (paths, status).
    """
    artifact_name = os.path.basename(source_path).replace(".md", "")

    if not should_render(stage, artifact_name):
        return {
            "rendered": False,
            "reason": f"No rendering trigger for {artifact_name} in {stage}",
        }

    if not os.path.isfile(source_path):
        return {
            "rendered": False,
            "reason": f"Source file not found: {source_path}",
        }

    # Generate output paths
    outputs = {}
    for fmt in OUTPUT_FORMATS:
        output_path = get_output_path(source_path, fmt)
        outputs[fmt] = output_path

    # Stub render — actual rendering delegated to document-renderer subagent
    # with skills anthropic/docx and anthropic/pdf
    return {
        "rendered": True,
        "source": source_path,
        "outputs": outputs,
        "status": "pending",
        "note": "Rendering delegated to document-renderer subagent",
    }
