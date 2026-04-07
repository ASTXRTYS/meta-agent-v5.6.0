"""Document renderer subagent configuration.

Spec References: Sections 6.9, 6.9.1-6.9.3

Dict-based subagent (not Deep Agent) that renders Markdown artifacts
to DOCX and PDF formats.

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


PROMPT_MARKDOWN_PATH = Path(__file__).resolve().parent.parent / "prompts" / "Document_Renderer_System_Prompt.md"


@lru_cache(maxsize=1)
def _load_prompt_markdown() -> str:
    """Load the canonical markdown prompt."""
    return PROMPT_MARKDOWN_PATH.read_text().strip()


# Document renderer configuration per Section 6.9
DOCUMENT_RENDERER_CONFIG = {
    "type": "dict_based",
    "effort": "low",
    "recursion_limit": 1000,
    "tools": ["read_file", "write_file", "ls"],
    "skills": ["anthropic/docx", "anthropic/pdf"],
    "middleware": ["ToolErrorMiddleware"],
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "low"},
}

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


def build_document_renderer_subagent(
    skills_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """Build an SDK-compatible SubAgent dict for the document-renderer.

    ⚠️ SDK NON-COMPLIANCE — MISSING REQUIRED FIELDS
    DeepAgents SubAgent TypedDict requires: name, description, system_prompt, model, tools
    This builder is missing: model, tools (only provides skills)
    Runtime will fail when SubAgentMiddleware validates with new backend API.
    
    See: configs.py build_pm_subagents() which calls this function.

    Correct pattern options:
      1. Add "model" and "tools" to the returned dict for declarative SubAgent
      2. Convert to return CompiledSubAgent with pre-compiled runnable
         (see research_agent.py:create_research_agent_subagent for pattern)

    Shared builder used by both the PM orchestrator (build_pm_subagents)
    and the research-agent runtime so the document-renderer is available
    as a named subagent in both contexts.

    Args:
        skills_dirs: Resolved skill directory paths.  Only the Anthropic
            skills dir (containing docx/, pdf/) is passed through.

    Returns:
        SubAgent-compatible dict ready for create_deep_agent(subagents=...).
    """
    from meta_agent.middleware.tool_error_handler import ToolErrorMiddleware

    anthropic_skills_dir = next(
        # ⚠️ FRAGILE: String-matching on paths is brittle (matches "not-anthropic/", "anthropic-skills/", etc.)
        # TODO: Use explicit skill name mapping or path normalization
        (d for d in (skills_dirs or []) if "anthropic" in d), None
    )

    entry: dict[str, Any] = {
        "name": "document-renderer",
        "description": DOCUMENT_RENDERER_DESCRIPTION,
        "system_prompt": DOCUMENT_RENDERER_SYSTEM_PROMPT,
        "middleware": [ToolErrorMiddleware()],
    }
    if anthropic_skills_dir:
        entry["skills"] = [anthropic_skills_dir]
    return entry


def get_render_config() -> dict[str, Any]:
    """Get the document renderer configuration."""
    return DOCUMENT_RENDERER_CONFIG.copy()


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
