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

The Developer iterates. Each loop tightens the harness. System prompts get refined. Tool descriptions get sharper. Orchestration logic gets tuned. And with every iteration, the evaluation scores trend — visibly, measurably — toward your success criteria.

### 5. You See Everything

Every artifact the team produces — PRDs, datasets, eval scorecards, design specs, optimization trendlines — surfaces in the Meta Harness UI as a first-class, human-readable object. You don't need to dig through traces or parse nested JSON. You see:

- The dataset your stakeholders helped shape, rendered at a glance
- Evaluation scores trending upward (or regressing — and why)
- Each iteration of the optimization loop with clear before/after signals
- Direct links to LangSmith when you want the full forensic depth

The UI exists to make invisible work visible. When your team watches an optimization curve bend toward the target, that's not a dashboard metric — that's proof that the harness engineering process is working, backed by real data from real experiments.

---

## How It Works Under the Hood

Meta Harness is built on LangChain's Deep Agents SDK and orchestrated by LangGraph. Seven specialized agents run as peer Deep Agent graphs under a thin Project Coordination Graph — each with its own memory, checkpoint state, tools, and middleware stack.

Agents communicate through explicit handoff tools with structured records. Phase gates are enforced by middleware hooks, not by a central router. The coordination layer is plumbing — the intelligence lives in the agents.

Every handoff, every experiment, every evaluation is traced in LangSmith. The web app transforms that data into progress narratives. LangSmith is always one click away for anyone who wants the raw detail.

### The Agent Team

| Agent | Role |
|---|---|
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

The Developer is blind to evaluation artifacts. It sees only directional feedback. This information asymmetry is what makes the loop scientifically valid — the optimizer cannot overfit to the evaluator.

---

## Headless-First

Meta Harness goes where your team already works. The PM is available through Slack, Discord, email, the web app, a terminal UI, or API. A conference room of stakeholders can scope a project in a Slack thread. A solo founder can do it from the command line. Someone can start in Slack and pick up in the web app without losing context.

The web app is intentionally minimal — a chat interface for direct PM interaction, flanked by an artifact browser that surfaces PRDs, datasets, eval scorecards, and optimization trendlines. It's the single place where progress and ROI become visible, regardless of which channel the work happened in.

Every project maintains state across all entry points. The same artifacts appear in the same artifact browser whether you scoped the project in Discord or the web app.

---

## Your Agent Gets Its Own Computer

Every project gets a dedicated execution environment — a sandboxed workspace where agents can clone repositories, install dependencies, run commands, execute tests, commit changes, and open pull requests. This isn't a simulated filesystem. It's a real computing environment with git, package managers, and network access, isolated per project.

For existing codebases, the agent clones your repo, creates a working branch, implements against the plan, runs your test suite, and opens a draft PR when the work passes evaluation. For greenfield projects, the agent can build entirely within its environment and publish when you're ready.

Three execution modes serve different needs:

- **Managed sandbox** — Meta Harness provisions and manages the environment. Default for production and headless work.
- **External devbox** — Your organization brings its own sandbox provider, image, and security policy. Same capabilities, your governance.
- **Local workspace** — The agent operates on your machine, from the TUI. Opt-in, with guarded shell access. Good for trusted solo development.

The web app, TUI, Slack, and every other surface connect to the same project environment. File trees, diffs, command logs, PR status — all visible from wherever you're working.

---

## What You're Really Getting

Meta Harness democratizes harness engineering. The practice of scientifically tuning an AI agent — iterating on system prompts, tools, orchestration, middleware, and evaluation criteria in tight feedback loops until measurable success criteria are met — has been locked inside AI labs and specialist teams.

We make it participatory:

- **You define what good looks like.** Your domain expertise, your success criteria, your ground truth data. The PM helps you articulate it; the Harness Engineer turns it into science.
- **You watch it happen.** Every iteration, every experiment, every trend line is visible. Not as raw traces — as human-readable artifacts that tell the story of your agent getting better.
- **You weigh in when it matters.** Human-in-the-loop at key decision points: dataset approval, architecture review, eval criteria sign-off, taste calibration during development. Your judgment shapes the outcome.
- **You get proof, not promises.** Optimization curves backed by real evaluation data. Calibrated judges scoring against your criteria. Held-out test sets that prove generalization, not memorization.

The art of harness engineering — now open to everyone with a problem to solve.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | [Deep Agents SDK](https://pypi.org/project/deepagents/) |
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Observability | [LangSmith](https://smith.langchain.com) |
| Models | Anthropic Claude, OpenAI (model-agnostic, per-agent configurable) |
| Runtime | Python ≥ 3.12 |
| Sandbox | Daytona (default), with pluggable provider support |

---

## Project Status

Meta Harness is in active development. The architecture is locked — peer Deep Agent topology, middleware-enforced phase gates, project-scoped execution environments, and headless-first delivery. Implementation is underway.

---

*Built with [Deep Agents SDK](https://pypi.org/project/deepagents/) · Orchestrated by [LangGraph](https://github.com/langchain-ai/langgraph) · Traced by [LangSmith](https://smith.langchain.com)*
