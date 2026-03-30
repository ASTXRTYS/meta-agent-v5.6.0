"""Research agent prompt composition.

Loads the repo's intended markdown system prompt and layers a narrow
spec-alignment addendum over it so the live Phase 3 runtime follows the
canonical artifact paths and evaluator contract.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .sections import format_agents_md_section, format_workspace_section


PROMPT_MARKDOWN_PATH = Path(__file__).with_name("Research_Agent_System_Prompt.md")


LEGACY_PATH_REPLACEMENTS = {
    "/artifacts/research/decomposition.md": "artifacts/research/research-decomposition.md",
    "/artifacts/research/bundle.md": "artifacts/research/research-bundle.md",
}


RUNTIME_ALIGNMENT_ADDENDUM = """## Runtime Alignment Addendum

Follow this addendum whenever it is more specific than the markdown prompt above.

### Canonical Artifact Paths

- Persist the decomposition to `artifacts/research/research-decomposition.md`
- Persist HITL clusters to `artifacts/research/research-clusters.md`
- Persist sub-agent findings to `artifacts/research/sub-findings/*.md`
- Persist the final bundle to `artifacts/research/research-bundle.md`
- Update `.agents/research-agent/AGENTS.md` with a concise research summary

### Canonical 10-Phase Runtime Protocol

1. Read the full PRD and full Tier 1 eval suite without truncation.
2. Persist the research decomposition before any delegated or external research begins.
3. Consult the relevant skills in full, in decomposition priority order, before web research for that domain or execution phase.
4. Reason explicitly about delegation topology, then delegate parallel research via `task`.
5. Identify and remediate gaps and contradictions across returned findings.
6. Persist `artifacts/research/research-clusters.md` and request HITL approval before deep-dive verification.
7. Execute deep-dive verification against primary sources, code, issues, PRs, and real-world repositories.
8. Consult configured SMEs and tie their perspectives back to docs, skills, and technical findings.
9. Synthesize the final research bundle with the required 13-section schema.
10. Run an internal reflection loop of at most 5 passes until PRD coverage is verified or residual gaps are made explicit.

### Research Bundle Requirements

The final bundle must include these exact H2 headings:

1. Ecosystem Options with Tradeoffs
2. Rejected Alternatives with Rationale
3. Model Capability Matrix
4. SME Perspectives
5. Risks and Caveats
6. Confidence Assessment per Domain
7. Research Methodology
8. Unresolved Questions for Spec-Writer
9. PRD Coverage Matrix
10. Unresolved Research Gaps
11. Skills Baseline Summary
12. Gap and Contradiction Remediation Log
13. Citation Index

### Hard Runtime Rules

- You do not make architectural decisions for the spec-writer.
- The decomposition must exist before web research or deep-dive delegation begins.
- Every cited URL in the bundle must also appear in the runtime trace as a `web_fetch` call.
- Organize synthesis by topic, not by source, worker, or raw search dump.
- Keep unresolved gaps explicit for the downstream spec-writer and verification-agent.
- Preserve the repo default of `37 active + 1 deferred` research evals. Do not reactivate `RI-001` implicitly.
"""


@lru_cache(maxsize=1)
def _load_research_agent_prompt_markdown() -> str:
    """Load the intended markdown prompt and normalize stale path literals."""
    text = PROMPT_MARKDOWN_PATH.read_text()
    for old, new in LEGACY_PATH_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.strip()


def construct_research_agent_prompt(
    project_dir: str,
    project_id: str = "",
    agents_md: str = "",
) -> str:
    """Assemble the research-agent system prompt from the markdown source of truth."""
    sections = [
        _load_research_agent_prompt_markdown(),
        format_workspace_section(project_dir, project_id),
        RUNTIME_ALIGNMENT_ADDENDUM,
    ]
    if agents_md:
        sections.append(format_agents_md_section(agents_md))
    return "\n\n---\n\n".join(sections)
