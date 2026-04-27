# Meta Harness

**Your agent team for building, tuning, and shipping AI applications.**

Meta Harness puts a full team of specialized AI agents at your fingertips — a Project Manager, Researcher, Architect, Planner, Developer, Harness Engineer, and Evaluator — that work together to take your idea from a conversation to a production-ready agent harness. You define what success looks like. They do the engineering.

---

## The Problem

Building AI agents that actually work in production is hard. Not because the models aren't capable — but because the process of getting from "this agent kind of works" to "this agent reliably does what my business needs" is a grind. It requires:

- Translating business requirements into precise evaluation criteria
- Crafting datasets that represent what "good" actually looks like for your use case
- Designing scoring rubrics and LLM judges that can measure quality at scale
- Running experiments in tight loops — tweaking system prompts, tools, orchestration logic, middleware — and measuring whether each change moved the needle
- Maintaining scientific rigor throughout: held-out test sets, information isolation between the builder and the evaluator, calibrated judges

This is harness engineering. Until now, it's been a discipline practiced by a small number of specialists at frontier AI labs. It requires deep expertise in evaluation science, agent architecture, and iterative optimization — and it's almost entirely invisible to the people paying for the results.

Meta Harness changes that.

---

## What Meta Harness Does

Meta Harness is an agents-as-a-service platform. You talk to our Project Manager — through the web app, a terminal, Slack, Discord, email, or any channel where your team already works — and describe what you need your agent to do. From there, our agent team runs the full lifecycle:

### 1. You Shape the Requirements

The PM works with you and your stakeholders to build a Product Requirements Document. This isn't a form you fill out — it's a conversation. The PM asks the right questions, captures your domain knowledge, and translates your vision into clear success criteria and evaluation datasets.

This is where your expertise matters most. You know your business, your users, your edge cases. The PM's job is to extract that knowledge and structure it so the rest of the team can act on it.

### 2. The Harness Engineer Builds the Science

Once the PRD is solid, the Harness Engineer takes over the evaluation side. This agent is the scientific authority — it designs scoring rubrics, assembles LLM judges, creates held-out datasets for calibration, and builds the complete evaluation harness that will measure whether the target agent is actually getting better.

The Harness Engineer doesn't just set up evals once. It intervenes at every stage — when the Architect introduces new components, when the Planner structures the build phases, and throughout the development loop — ensuring that every piece of the system has rigorous, measurable criteria.

### 3. Research and Architecture Happen in Parallel

The Researcher digs into SDKs, APIs, model capabilities, and ecosystem tools relevant to your requirements. The Architect takes that research bundle plus the PRD and designs the full system — tool schemas, system prompts, orchestration logic, component definitions. These two agents loop with each other: the Architect identifies knowledge gaps, the Researcher fills them, and the design gets sharper with each pass.

### 4. The Developer Builds — and the Optimization Loop Begins

This is where Meta Harness does something fundamentally different from traditional development.

The Developer works phase by phase through the implementation plan. After each phase, it submits its work to two independent reviewers:

- The **Evaluator** checks whether the code matches the spec and plan — hard pass/fail on compliance
- The **Harness Engineer** runs the evaluation harness against the current build and returns an EBDR-1 feedback packet — directional guidance on what's working and what isn't

Here's the critical design constraint: **the Developer never sees the evaluation artifacts**. It doesn't know the rubrics, the judge configurations, or the held-out datasets. It only sees the feedback. This information isolation prevents the optimizer from gaming the evaluator — the same principle that makes scientific peer review work.

The Developer iterates. Each loop tightens the harness. System prompts get refined. Tool descriptions get sharper. Orchestration logic gets tuned. And with every iteration, the Harness Engineer publishes evaluation analytics — graphs, metrics, and scorecards that show whether the target harness is moving toward the success criteria you established with the PM and refined through the evaluation process.

### 5. You See Everything

Every artifact the team produces — PRDs, datasets, eval scorecards, design specs, and Harness Engineer analytics — surfaces in the Meta Harness UI as a first-class, human-readable object. You don't need to dig through traces or parse nested JSON. You see:

- The dataset your stakeholders helped shape, rendered at a glance
- Evaluation graphs and metrics showing progress toward your stated success criteria
- Each iteration of the build-and-evaluation loop with clear before/after signals
- Direct links to LangSmith when you want the full forensic depth

The UI exists to make invisible work visible. When your team sees the target harness move closer to the criteria they helped define, that is not a vanity dashboard — it is product evidence that the harness engineering process is working, backed by real data from real experiments.

---

## How It Works Under the Hood

Meta Harness is built on LangChain's Deep Agents SDK and orchestrated by LangGraph. Seven specialized agents run as **peer Deep Agent graphs mounted under a thin Project Coordination Graph (PCG)** — each with its own checkpoint namespace, memory, tools, and middleware stack.

The PCG has one deterministic coordination node, `dispatch_handoff`, plus seven mounted role Deep Agent subgraph nodes. No LLM calls. No conditional edges. Routing is pure `Command(goto=Send(...))` dispatch. Agents communicate through explicit handoff tools that emit `Command.PARENT` with structured `HandoffRecord` payloads. Phase gates are enforced by middleware hooks on handoff tools, not by the coordination graph.

Every handoff, every experiment, every evaluation is traced in LangSmith. The web app transforms that data into progress narratives. LangSmith is always one click away for anyone who wants the raw detail.

### The Agent Team

| Agent | Role |
|-------|------|
| **Project Manager** | Your point of contact. Translates stakeholder vision into requirements, coordinates the pipeline, surfaces decisions that need your input. |
| **Harness Engineer** | The evaluation scientist. Owns rubrics, LLM judges, calibration, held-out datasets, and the optimization feedback loop. |
| **Researcher** | Deep ecosystem research — SDKs, APIs, model capabilities, evidence synthesis. |
| **Architect** | System design and technical specification. Tool schemas, system prompts, component definitions. |
| **Planner** | Implementation strategy with phased eval breakpoints. |
| **Developer** | The optimizer. Builds phase by phase, iterates against evaluation feedback until success criteria are met. |
| **Evaluator** | Acceptance gatekeeper. Pass/fail on spec compliance, code quality, and deliverable completeness. |

### The Optimization Loop

```
Developer implements a phase
        │
        ├──→ Evaluator: pass/fail on spec compliance
        │
        ├──→ Harness Engineer: runs evals, returns feedback
        │
        ▼
Developer iterates until both gates pass
        │
        ▼
    Next phase
```

The Developer is blind to evaluation artifacts. It sees only directional feedback (EBDR-1 packets). This information asymmetry is what makes the loop scientifically valid — the optimizer cannot overfit to the evaluator.

### Architecture Decisions

- **Peer Deep Agent topology**: Each role is a `create_deep_agent()` graph mounted as a subgraph node. No ephemeral `task` subagents for project roles.
- **Command.PARENT handoffs**: All agent transitions bubble through the PCG via explicit `Command(graph=PARENT, goto="dispatch_handoff")` emissions.
- **Thread kinds**: `pm_session` for intake/conversation, `project` for execution. Project threads own project-scoped execution environments.
- **Headless-first**: PM available via web app, TUI, and API. Same lifecycle across all surfaces.

---

## Headless-First

Meta Harness goes where your team already works. The PM is available through the web app, a terminal TUI, and API — with the same lifecycle and artifact visibility across all surfaces. A solo founder can scope a project from the command line; a team can collaborate through the web interface. All entry points share the same project state and artifact browser.

The web app is intentionally minimal — a chat interface for direct PM interaction, flanked by an artifact browser that surfaces PRDs, datasets, eval scorecards, and Harness Engineer-published analytics views. It's the single place where progress and ROI become visible, regardless of which surface the work originated from.

Every project maintains state across all entry points. The same artifacts appear in the same artifact browser whether you scoped the project in the TUI or the web app.

---

## Your Agent Gets Its Own Computer

Every project gets a dedicated execution environment — a sandboxed workspace where agents can clone repositories, install dependencies, run commands, execute tests, commit changes, and open pull requests. This isn't a simulated filesystem. It's a real computing environment with git, package managers, and network access, isolated per project.

For existing codebases, the agent clones your repo, creates a working branch, implements against the plan, runs your test suite, and opens a draft PR when the work passes evaluation. For greenfield projects, the agent can build entirely within its environment and publish when you're ready.

Three execution modes serve different needs:

- **Managed sandbox** — Meta Harness provisions and manages the environment. Default for production and headless work.
- **External devbox** — Your organization brings its own sandbox provider, image, and security policy. Same capabilities, your governance.
- **Local workspace** — The agent operates on your machine, from the TUI. Opt-in, with guarded shell access. Good for trusted solo development.

The web app, TUI, and API all connect to the same project environment. File trees, diffs, command logs, PR status — all visible from wherever you're working.

---

## What You're Really Getting

Meta Harness democratizes harness engineering. The practice of scientifically tuning an AI agent — iterating on system prompts, tools, orchestration, middleware, and evaluation criteria in tight feedback loops until measurable success criteria are met — has been locked inside AI labs and specialist teams.

We make it participatory:

- **You define what good looks like.** Your domain expertise, your success criteria, your ground truth data. The PM helps you articulate it; the Harness Engineer turns it into science.
- **You watch it happen.** Every iteration and experiment is visible through human-readable artifacts, graphs, and metrics that tell the story of your target harness getting better.
- **You weigh in when it matters.** Human-in-the-loop at key decision points: dataset approval, architecture review, eval criteria sign-off, taste calibration during development. Your judgment shapes the outcome.
- **You get proof, not promises.** Harness Engineer analytics backed by real evaluation data. Calibrated judges scoring against your criteria. Held-out test sets that prove generalization, not memorization.

The art of harness engineering — now open to everyone with a problem to solve.

---

## Tech Stack


| Layer           | Technology                                                        |
| --------------- | ----------------------------------------------------------------- |
| Agent Framework | [Deep Agents SDK](https://pypi.org/project/deepagents/)           |
| Orchestration   | [LangGraph](https://github.com/langchain-ai/langgraph)            |
| Observability   | [LangSmith](https://smith.langchain.com)                          |
| Models          | Anthropic Claude, OpenAI (model-agnostic, per-agent configurable) |
| Runtime         | Python ≥ 3.12                                                     |
| Sandbox         | Daytona (default), with pluggable provider support                |


---

## Repository Navigation

### SME/ — Subject Matter Expert Input

The `SME/` folder contains primary source material that heavily influenced Meta Harness's design philosophy. This is not documentation — it's the raw intellectual substrate.

**`SME/Vivek-Langchain/`** — Essays, threads, and articles from @Vtrivedy10 (Viv), Agents & Evals at LangChain. This is the single highest-signal external input for harness engineering mental models.

| Path | What You'll Find |
|------|------------------|
| `Vivek-Langchain/Readme.md` | Onboarding guide to Viv's core mental models: the Model-Harness Training Loop, "no general-purpose harness" principle, evals-as-training-data, and the GEPA hill-climbing lineage |
| `Vivek-Langchain/Twitter-Articles/` | Long-form articles derived from Twitter threads: eval recipes for Deep Agents, harness engineering anatomy, iterative improvement patterns |
| `Vivek-Langchain/blogs/` | Blog posts on trace-driven agent improvement |
| `Vivek-Langchain/Tweets_*` | Raw tweet and reply extracts (preserved for verbatim citation) |

**How to use this material:**

1. **For harness design decisions** — Start with `Readme.md` "Core Mental Models" section. These principles constrain/validate design choices.
2. **For eval design specifics** — See `Twitter-Articles/"How-we-build-evals-for-deep-agents".md` for concrete LangChain recipes, CI integration patterns, and LangSmith-at-scale practices.
3. **For verbatim attribution** — Use the `Tweets_*` extracts for direct quotes with original context preserved.

---

## Project Status

Meta Harness is in active development. The architecture is locked — peer Deep Agent topology, middleware-enforced phase gates, project-scoped execution environments, and headless-first delivery. Implementation is underway.

---

*Built with [Deep Agents SDK](https://pypi.org/project/deepagents/) · Orchestrated by [LangGraph](https://github.com/langchain-ai/langgraph) · Traced by [LangSmith](https://smith.langchain.com)*