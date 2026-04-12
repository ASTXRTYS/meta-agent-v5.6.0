---
trigger: always_on
---
**You have full agency.** 
- Every step you take should be deliberate — choose the single next action that maximizes understanding of the specific problem at hand. Targeted searches beat breadth. Pause between each tool call to synthesize what you learned and determine if you truly need more context or if you're ready to proceed.


Before writing code or specs: **Parse intent, then consult `meta_harness/AGENTS.md`**.

That file contains:
- **Naming Rules** — function/class naming conventions
- **Canonical SDK References** — local source paths for Deep Agents, LangGraph, LangSmith, agentevals
- **Harness-First Architecture** — middleware vs tools, backend patterns, sub-agent taxonomy
- **External Reference Links** — GitHub repos and PyPI packages for release history

**Hard rules:**
1. If <95% confident on any SDK behavior (imports, middleware, harness init), consult the canonical source in `.reference/` or `.venv/` before proceeding.
2. Do not hand-roll logic the SDK already handles.
3. Targeted skill reading beats breadth — only load skills relevant to this specific request.

**Research tasks:** When the user asks you to research, you **must** consult `meta_harness/AGENTS.md` first. Use:
- **External Reference Links** — GitHub repos and PyPI packages for release history, commits, recent changes
- **Canonical SDK References** — local paths in `.reference/` and `.venv/` for authoritative implementation details
- **Skills** — `.agents/skills/` for structured guidance (Claude API, LangGraph, LangSmith, Deep Agents, agentevals) *Reference these skills for baseline and abstract knowledge, the signal in your skills is high and can amplify the preciseness of your next step and decisions in research scenarios*

Skills provide high-signal patterns, but they leave gaps around "taste" and edge cases. Always supplement skill guidance with canonical SDK source inspection when the answer isn't 100% clear from the skill file.