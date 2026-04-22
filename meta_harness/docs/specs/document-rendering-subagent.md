---
doc_type: spec
derived_from:
  - AD §4 Phase Gates
  - AD §4 Document Rendering Subagent (DICT)
  - AD §4 Agent Primitive Decisions
status: draft
last_synced: 2026-04-22
owners: ["@Jason"]
---

# Document Rendering Subagent Specification

> **Provenance:** Derived from `AD.md §4 Phase Gates`, `§4 Document Rendering Subagent (DICT)`, and `§4 Agent Primitive Decisions`.
> **Status:** Draft · **Last synced with AD:** 2026-04-22
> **Consumers:** Developer (implementation of PM factory + subagent registration), Evaluator (conformance), PM agent prompt author.

> **Review flags for Jason (per `AGENTS.md` → Naming Rules & Review Standard):**
> 1. Canonical subagent name — this spec uses `document-renderer` (kebab-case, matches existing role-name convention). Approve/rename before merge.
> 2. Module location — this spec places the subagent at `src/meta_harness/agents/project_manager/task_agents/document_renderer/`, matching the `task_agents/` reservation in `AD.md §Repo and Workspace Layout`. Approve/rename before merge.
> 3. Skill allocation — the three Anthropic rendering skills (`docx`, `pdf`, `pptx`) move from PM to this subagent. The PM retains `doc-coauthoring`, `internal-comms`, and `prompt-architect` (see `ALLOCATED-SKILLS.MD`). Approve.

## 1. Purpose

The **Document Rendering Subagent** is an ephemeral, PM-owned declarative
`SubAgent` (the SDK's "DICT" shape — a plain `SubAgent` dict invoked through
the built-in `task` tool) whose sole responsibility is to render a source
artifact set (markdown, structured data, images) into stakeholder-friendly
document packages in `.docx`, `.pdf`, and `.pptx` formats for the two
approval gates described in `AD.md §4 Phase Gates`:

- `scoping` → `research` — PRD + eval suite + business-logic datasets.
- `architecture` → `planning` — full design spec + tool schemas + system
  prompts.

Rendering is **not** a PM responsibility. The PM assembles the source
artifacts and delegates rendering to this subagent, then presents the
resulting file paths to the user via its dedicated approval tool.

### Why a separate subagent

Rendering is stateless, ephemeral, context-heavy, and bounded:

- **Stateless.** Each render is a self-contained job against provided
  source paths; there is no cross-render trajectory to resume.
- **Ephemeral.** No durable project-scoped checkpoint namespace is
  required — the SDK's `task` tool semantics are a natural fit.
- **Context-heavy.** The three Anthropic rendering skills (`docx`, `pdf`,
  `pptx`) carry large reference surfaces that would otherwise inflate the
  PM's context window even when no rendering is occurring.
- **Bounded output.** The return value is a small map of format → file
  path plus a short status string.

These properties map onto `AD.md §3 Option A` (declarative `SubAgent` dict
specs, rejected as the *core project-role* topology but explicitly
preserved for *isolated tasks*), and onto the `task_agents/` module slot
reserved in `AD.md §Repo and Workspace Layout` for "role-owned ephemeral
SDK `SubAgent` helpers."

## 2. Topology

This subagent is **direct**: the PM invokes it through the SDK `task`
tool. Invocation does **not** traverse the PCG and does **not** produce a
`HandoffRecord`. It is not a peer Deep Agent, it is not mounted under the
Project Coordination Graph, and it does not have its own checkpoint
namespace.

```txt
PM Deep Agent
│
├── task(subagent_type="document-renderer", description=...)
│       │
│       └── ephemeral document-renderer SubAgent (SDK task tool)
│               │
│               └── returns {formats: {docx, pdf, pptx}, paths: [...]}
│
└── (PM assembles approval-package tool call using returned paths)
```

The PM owns both the pre-render artifact set (in its role namespace
filesystem) and the post-render file paths. The subagent writes rendered
files into a subpath of the PM's namespace (see §6 Filesystem) so the PM
can reference them without a cross-namespace copy.

## 3. Subagent Declaration

Registered on the PM factory as a declarative `SubAgent` dict in
`subagents=[...]`. Illustrative shape (exact field names track the
SDK — verify against `.reference/` or `.venv/libs/deepagents` before
implementation):

```python
{
    "name": "document-renderer",
    "description": (
        "Render a source artifact set (markdown + structured data + "
        "images) into stakeholder-friendly document packages (.docx, "
        ".pdf, .pptx). Invoke when the PM needs to produce an approval "
        "gate package. Input: source_paths, target_formats, output_dir. "
        "Output: rendered file paths plus a short status string."
    ),
    "prompt": "<document_renderer_system_prompt.md>",
    "skills": [
        ".agents/skills/anthropic/skills/docx",
        ".agents/skills/anthropic/skills/pdf",
        ".agents/skills/anthropic/skills/pptx",
    ],
}
```

Because it is an SDK declarative `SubAgent`, the subagent inherits the
parent model/backend/middleware policy unless explicitly overridden. v1
inherits the PM's model and backend — rendering is not a model-selection
concern.

## 4. Invocation Contract

LLM-facing parameters on the `task` call (the parent `task` tool
signature is SDK-provided; these are the fields the PM is expected to
pass in the `description` / input payload):

| Field | Type | Required | Purpose |
|---|---|---|---|
| `source_paths` | `list[str]` | Yes | Paths to source artifacts in the PM's filesystem namespace (markdown, data, images). |
| `target_formats` | `list[Literal["docx","pdf","pptx"]]` | Yes | Which format(s) to render. At least one. |
| `output_dir` | `str` | Yes | PM-namespace directory the subagent writes rendered files into. |
| `title` | `str` | Yes | Package title for document headings and PPTX title slide. |
| `audience` | `Literal["stakeholder","internal"]` | No (default `"stakeholder"`) | Controls tone/format presets (e.g. executive summary slide). |
| `gate` | `Literal["scoping_to_research","architecture_to_planning"]` | No | Optional hint; lets the subagent pick gate-specific templates. |

## 5. Return Value

The subagent returns a single payload the PM can hand to its approval
presentation tool without additional post-processing:

```json
{
  "status": "ok" | "failed",
  "rendered": {
    "docx": "<path-or-null>",
    "pdf":  "<path-or-null>",
    "pptx": "<path-or-null>"
  },
  "warnings": ["..."],
  "error": "<string-or-null>"
}
```

- Every format requested in `target_formats` MUST appear as a key in
  `rendered`. Missing requested formats MUST cause `status = "failed"`
  and an `error` populated.
- `warnings` is for non-fatal issues (e.g. truncated source, skipped
  image).

## 6. Filesystem

The subagent writes into the PM's namespace under the caller-provided
`output_dir`. It MUST NOT write outside `output_dir`. It MUST NOT read
files outside `source_paths`. This preserves the PM's ownership of
project artifacts and avoids cross-namespace coupling.

Rendered files are referenced (not copied) by subsequent PM tool calls,
consistent with `AD.md §Handoff Protocol` ("Artifact paths are
references by default").

## 7. System Prompt Invariants

Per `AD.md §Agent Primitive Decisions` (Q12), system prompt text is
spec territory, but behavioral invariants are AD-locked. Invariants for
the document renderer:

- **Must recognize:** the invocation is a rendering job, not an
  authoring job. The subagent MUST NOT edit content semantics,
  paraphrase source markdown, or "improve" the source.
- **Must not do:** invoke non-rendering tools, cross into other role
  namespaces, trigger a PCG handoff, or block on user input. The
  subagent has no `AskUserMiddleware`.
- **Self-awareness trigger:** if a requested format cannot be rendered
  (e.g. missing dependency, unsupported source element), the subagent
  MUST return `status = "failed"` with an `error` rather than
  silently skipping.

Full system prompt lives at:
`src/meta_harness/agents/project_manager/task_agents/document_renderer/system_prompt.md`
(location pending Jason approval — see Review Flags).

## 8. Middleware Stack

Per `AD.md §Agent Primitive Decisions` (Q12, universal baseline),
declarative `SubAgent` dicts inherit the parent's middleware stack. This
subagent explicitly does NOT require:

- `AskUserMiddleware` — non-interactive by design.
- Phase gate middleware — it does not call handoff tools.
- `StagnationGuardMiddleware` tuning — rendering jobs are short; the PM's
  per-role threshold is adequate for the enclosing run.

It benefits from the universal baseline (`CollapseMiddleware`,
`ContextEditingMiddleware`, `SummarizationToolMiddleware`,
`ModelCallLimitMiddleware`) without modification.

## 9. Observability

Each invocation emits a LangSmith child run under the parent PM run,
provided by the SDK `task` tool's default tracing behavior. No custom
correlation metadata is required beyond what the SDK already emits; the
PM run already carries `project_id`, `project_thread_id`, and
`agent_name` per `AD.md §6 Required Signals`.

No PCG `HandoffRecord` is written — this is not a peer handoff.

## 10. Non-Responsibilities

Explicitly out of scope:

- Content authoring (owned by PM + `doc-coauthoring`).
- Stakeholder communication framing (owned by PM + `internal-comms`).
- Approval gate presentation / user interaction (owned by PM's dedicated
  approval tool; the subagent returns paths, not UI).
- Cross-gate state — each invocation is independent.
- Eval artifacts, research bundles, design specs themselves — only the
  *rendered* package wrapping them.

## 11. Open Items (for Jason)

1. **Subagent name.** `document-renderer` vs. alternatives
   (`doc-packager`, `stakeholder-doc-renderer`). Recommend
   `document-renderer` for clarity.
2. **Module path.** `agents/project_manager/task_agents/document_renderer/`
   — matches `AD.md §Repo and Workspace Layout` convention; confirm.
3. **Skill registration vs. inline prompt.** Rendering skills are
   delivered via Anthropic's skill directories. Confirm the SDK
   `SubAgent` dict accepts `skills=[...]` in the same shape as
   `create_deep_agent()` (verify against SDK source per `AGENTS.md` →
   Canonical SDK References before implementation).
4. **Autonomous mode.** When autonomous mode auto-advances gates, is
   rendering still invoked (for artifact emission / web app
   visibility) or skipped? Recommend: still invoked — the rendered
   package is a first-class artifact independent of user review.
5. **PPTX for scoping gate.** Do we need PPTX for *both* approval
   gates, or is PPTX reserved for the `architecture → planning` gate
   (design review) and DOCX/PDF sufficient for `scoping → research`?
