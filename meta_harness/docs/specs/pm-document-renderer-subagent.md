---
doc_type: spec
derived_from:
  - AD §4 Agent Primitive Decisions
  - AD §4 Phase Gates
  - AD §4 Repo and Workspace Layout
  - DECISIONS §Q1 (Repo structure naming — `task_agents/` bucket)
status: draft
last_synced: 2026-04-22
owners: ["@Jason"]
---

# PM Document-Renderer SubAgent Specification

> **Provenance:** Derived from `AD.md §4 Agent Primitive Decisions` (document rendering delegation), `§4 Phase Gates` (approval-mechanism document package production), and `§4 Repo and Workspace Layout` (`task_agents/` bucket naming). Closes the AD decision that `docx`, `pdf`, and `pptx` skills are **not** PM-allocated skills but belong to a PM-owned ephemeral Deep Agents SDK `SubAgent` dict spec invoked via the SDK `task` tool.
> **Status:** Draft · **Last synced with AD:** 2026-04-22 · **Consumers:** Developer (scaffolding, factory wiring), Evaluator (structural conformance), Harness Engineer (eval-time rendering if ever required).

## 1. Purpose

The parent AD locks two decisions:

1. **Document rendering is delegated, not PM-native.** The PM remains the document hub — it drafts, coauthors, and packages stakeholder artifacts — but the *rendering* step (producing `.docx`, `.pdf`, `.pptx` files) is delegated to a single role-owned ephemeral SDK `SubAgent` dict spec.
2. **The primitive is a declarative Deep Agents SDK `SubAgent` dict**, not a peer `create_deep_agent()` graph mounted under the PCG. Document rendering is stateless, single-task, and has no cross-project identity, which matches the `task`-tool invocation model (`.reference/libs/deepagents/deepagents/middleware/subagents.py:152-162`).

This spec renders those AD decisions into the concrete `SubAgent` dict fields, skill assignment, and module location a developer can scaffold against.

## 2. SDK Primitive and Invocation Model

The subagent is a **`SubAgent`** TypedDict (not `CompiledSubAgent`, not `AsyncSubAgent`). Required and optional fields are specified in `.reference/libs/deepagents/deepagents/middleware/subagents.py:22-88`:

```python
class SubAgent(TypedDict):
    name: str                                   # required
    description: str                            # required
    system_prompt: str                          # required
    tools: NotRequired[Sequence[BaseTool | Callable | dict[str, Any]]]
    model: NotRequired[str | BaseChatModel]
    middleware: NotRequired[list[AgentMiddleware]]
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]
    skills: NotRequired[list[str]]              # list of skill source paths
    permissions: NotRequired[list[FilesystemPermission]]
```

When the PM's `SubAgentMiddleware` (in every Deep Agent's base stack per `AD.md §4 Agent Primitive Decisions` and DECISIONS Q12) assembles the agent graph, `create_deep_agent()` attaches `SkillsMiddleware(backend=backend, sources=subagent_skills)` to each `SubAgent` whose `skills=[...]` is populated (`.reference/libs/deepagents/deepagents/graph.py:497-499`). Skills on a `SubAgent` are scoped *to that subagent only*; parent `skills_metadata` is excluded from the child's state (`middleware/subagents.py:137`).

**Invocation.** The PM invokes the subagent by calling the `task` tool, which is auto-installed by `SubAgentMiddleware` (`middleware/subagents.py:478`). The SDK description is the authoritative contract: *"Launch an ephemeral subagent to handle complex, multi-step independent tasks with isolated context windows … Each agent invocation is stateless … you will not be able to send additional messages to the agent"* (`middleware/subagents.py:152-162`). Every rendering request is one `task` call with a fully specified `description`.

**State isolation.** Every invocation drops `messages`, `todos`, `structured_response`, `skills_metadata`, and `memory_contents` from the parent state passed to the subagent (`middleware/subagents.py:137`, `345-360`). The subagent gets a fresh `HumanMessage` built from the `task` tool's `description` argument (`middleware/subagents.py:360`). Output returns to the PM as a single `ToolMessage` carrying the last child `AIMessage.text` (`middleware/subagents.py:347-352`). No cross-invocation memory; no project-role checkpoint namespace; no participation in the handoff protocol.

## 3. SubAgent Dict Spec

```python
from deepagents.middleware.subagents import SubAgent

DOCUMENT_RENDERER_SUBAGENT: SubAgent = {
    "name": "document-renderer",
    "description": (
        "Renders a finished document package into stakeholder-friendly binary "
        "formats (.docx, .pdf, .pptx) from a complete source specification "
        "supplied by the caller. Stateless; each invocation must include the "
        "full document source and the requested output formats."
    ),
    "system_prompt": "<loaded from system_prompt.md — see §5>",
    "skills": [
        ".agents/skills/anthropic/skills/docx",
        ".agents/skills/anthropic/skills/pdf",
        ".agents/skills/anthropic/skills/pptx",
    ],
    # model: omitted — inherits PM's model by default (graph.py:478)
    # tools: omitted — inherits PM's tools (graph.py:514-520); filesystem
    #        write access is provided by the PM's FilesystemMiddleware.
    # middleware: omitted — SDK's base stack (TodoList, Filesystem,
    #             Summarization, PatchToolCalls) is prepended automatically
    #             per graph.py:487-496, plus SkillsMiddleware is appended
    #             when `skills` is populated (graph.py:497-499).
    # permissions: inherited from PM (graph.py:485).
    # interrupt_on: not used — rendering is non-interactive.
}
```

**Why `SubAgent` over `CompiledSubAgent`/`AsyncSubAgent`.**

- `CompiledSubAgent` is the escape hatch for pre-compiled custom graphs; it provides no stable `thread_id` config (`.reference/libs/deepagents/deepagents/middleware/subagents.py:488-493`) and would be over-engineered for a stateless rendering helper.
- `AsyncSubAgent` creates a new remote task thread per invocation (`.reference/libs/deepagents/deepagents/middleware/async_subagents.py:280-318`) — remote/background execution is not needed, and rendering is short enough to stay on the PM's thread.
- `SubAgent` with `skills=[...]` is exactly the primitive the SDK offers for scoped, ephemeral, skill-specialized task delegation. See also `AD.md §3 Option A` (rejected as the *core role* topology, but explicitly endorsed for "isolated tasks" at line 103).

## 4. Skill Allocation

Owned by `document-renderer`:

| Skill | Source path | Purpose |
|---|---|---|
| `docx` | `.agents/skills/anthropic/skills/docx` | Word document rendering for stakeholder review packages |
| `pdf` | `.agents/skills/anthropic/skills/pdf` | PDF generation for approval-gate deliverables |
| `pptx` | `.agents/skills/anthropic/skills/pptx` | Presentation generation for stakeholder deliverables |

These skills are **removed from the PM's `skills=[...]` list** in the same change that lands this spec — see `ALLOCATED-SKILLS.MD` and `AD.md §4 Agent Primitive Decisions`.

PM retains `doc-coauthoring`, `internal-comms`, and `prompt-architect` (custom). Authoring, coauthoring, and stakeholder-communication workflows stay on the PM; only the terminal render-to-binary step is delegated.

## 5. System Prompt

System-prompt *text* is spec-level detail. The **behavioral invariants** locked by AD for any document-rendering subagent are:

- **Stateless-task contract.** The subagent must treat the `task` tool description as the complete input. It must not request follow-up from the PM — there is no follow-up channel (`middleware/subagents.py:162`: *"The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result."*).
- **Output format discipline.** The subagent must only produce the requested file formats (`docx`/`pdf`/`pptx`) and the emitted artifact paths. It must not editorialize content, alter headings, reorganize sections, or add commentary the PM did not supply.
- **Skill invocation, not reinvention.** The subagent must invoke the installed `docx`/`pdf`/`pptx` skills rather than hand-rolling file generation.
- **Final message = artifact paths + one-line summary.** The `task` tool returns only the last child `AIMessage.text` to the PM (`middleware/subagents.py:347`). The subagent's final message must be a machine-parseable list of artifact paths plus a one-line render summary the PM can quote to the stakeholder.

The concrete prompt markdown file lives at `src/meta_harness/agents/project_manager/task_agents/document_renderer.system_prompt.md` once scaffolded. Spec-team refinement of the prompt text is in-scope; the invariants above are not.

## 6. Module Location

This subagent is the **first concrete instance** of the `task_agents/` bucket reserved by `DECISIONS.md §Q1` ("reserves `task_agents/` only for future role-owned ephemeral SDK `SubAgent` helpers") and `AD.md §4 Repo and Workspace Layout` ("SDK `SubAgent` dicts, if any are later needed for ephemeral isolated tasks, are reserved for a narrowly named `task_agents/` module inside the owning role").

```txt
src/meta_harness/
└── agents/
    └── project_manager/
        ├── agent.py                    # create_deep_agent(name="project-manager", subagents=[DOCUMENT_RENDERER_SUBAGENT, ...])
        ├── system_prompt.md
        └── task_agents/
            ├── __init__.py
            └── document_renderer.py    # exports DOCUMENT_RENDERER_SUBAGENT SubAgent dict
            └── document_renderer.system_prompt.md
```

The `task_agents/` package lives **inside** the owning role's module (here, `project_manager/`). This matches the AD constraint that SubAgent dicts are *role-owned*, not a top-level bucket.

## 7. PM Wiring

In `src/meta_harness/agents/project_manager/agent.py`:

```python
from deepagents import create_deep_agent
from meta_harness.agents.project_manager.task_agents.document_renderer import (
    DOCUMENT_RENDERER_SUBAGENT,
)

def create_project_manager_agent(...):
    return create_deep_agent(
        model=...,
        tools=[...],
        system_prompt=...,
        skills=[
            ".agents/skills/anthropic/skills/doc-coauthoring",
            ".agents/skills/anthropic/skills/internal-comms",
            # NOTE: docx / pdf / pptx are NOT here — see document-renderer subagent.
            ".agents/skills/<prompt-architect path, TBD>",
        ],
        subagents=[
            DOCUMENT_RENDERER_SUBAGENT,
            # ... other PM-owned subagents if any
        ],
        middleware=[...],
        name="project-manager",
        ...
    )
```

The PM's system prompt must direct the PM to invoke `task(subagent_type="document-renderer", description=...)` when it needs to emit a stakeholder document package, rather than attempting to load `docx`/`pdf`/`pptx` skills itself.

## 8. Phase-Gate Integration

`AD.md §4 Phase Gates` describes the two approval transitions (`scoping → research`, `architecture → planning`) as moments where the PM presents a "document package (docx/pdf/pptx)" to the user. After this AD change, that text reads as delegation — the PM drafts and curates the package content, then calls the `document-renderer` subagent to produce the binaries, and attaches the returned artifact paths to the approval-gate record.

**Invariant preserved.** The approval mechanism remains prompt-driven and PM-owned (AD §4 Phase Gates: *"This is prompt-driven — the PM decides when to invoke the tool based on its system prompt — not a PCG-level interrupt"*). The `document-renderer` subagent does not emit handoff tools, does not write to `acceptance_stamps`, and does not participate in PCG dispatch. It is invisible to the PCG and invisible to the handoff protocol.

**Autonomous mode.** `AD.md §4 Phase Gates` — "In autonomous mode the PM still packages the documents but does not pause for user review." The autonomous-mode behavior is unchanged by this spec: the PM still calls the rendering subagent and stamps the approval itself.

## 9. What This Spec Does *Not* Cover

- **Exact prompt text** for `document_renderer.system_prompt.md`. Spec-team owns iteration.
- **Artifact registration.** Whether rendered files are written to the PM's filesystem, the project workspace, or the `artifact_manifest` Store namespace is a PM-side filesystem concern, not this subagent's concern. See `docs/specs/pcg-data-contracts.md §7` for the artifact-manifest contract once `OQ-H5` lands.
- **Additional document subagents.** If future stakeholder formats (HTML dashboards, spreadsheets, etc.) warrant separate subagents, each belongs in its own `SubAgent` dict spec with its own skills list — not as bolt-ons to this one.

## 10. Non-Goals and Rejections

- **Not a peer Deep Agent.** This subagent does not have a checkpoint namespace, does not appear in `ROLE_GRAPHS`, is not mounted by the PCG, does not emit `Command.PARENT`, and is not a participant in the handoff tool matrix. Any attempt to upgrade this subagent to peer-role status must first raise an AD decision against `AD.md §4 Specialist Loops` and `§4 LangGraph Project Coordination Graph`.
- **Not a general-purpose document agent.** Scope is strictly binary-format rendering. Content authoring, research, and stakeholder dialogue remain PM responsibilities.
- **Not an acceptance gate.** The subagent cannot refuse to render, defer to user, or emit acceptance stamps. If PM-provided content is malformed, the subagent reports the problem in its final message and the PM decides how to proceed.

## 11. Open Items Flagged for Jason

- **Subagent `name`.** Proposal: `"document-renderer"` (kebab-case, matching the SDK's `"general-purpose"` example at `middleware/subagents.py:135` and the `name="project-manager"` convention at `docs/specs/repo-and-workspace-layout.md:49`). If you prefer `"document_renderer"` or `"doc-renderer"`, flag before merge.
- **Module path.** Proposal: `src/meta_harness/agents/project_manager/task_agents/document_renderer.py`. This is the first concrete `task_agents/` use and the naming needs your approval per `AGENTS.md` → **Naming Rules** ("New module and file names must be approved by Jason before merging").
- **Interpretation of "DICT agent" (from the chat request).** Rendered here as "declarative Deep Agents SDK `SubAgent` **dict** spec" — the SDK primitive at `middleware/subagents.py:22-88`. If the intent was a different primitive, this spec should be pulled and reissued.
