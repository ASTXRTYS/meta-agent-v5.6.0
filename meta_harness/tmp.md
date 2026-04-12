<*Question sent to SME:*>
---
I'm building an LLM application using Deep Agents as my harness. I have specifications for this LLM application and need guidance on how to make it possible. Some of the main things that I'm wrestling with is what should the topology of my agent be? Essentially, the actual harness itself. Yes, we'll be using the Deep Agent's harness, but obviously having one agent where all of these other agents that I'm mentioning as DICT agents clearly does not solve or satisfy the requirements that I'm mentioning here. We need to enable statefulness and enable loops where agents can loop together without having to bring in the project manager. Please read through all of my requirements and take into consideration, deeply think and consider what does Deep Agents offer for me to be able to make this system possible? I need the majority of your reasoning to go towards how I can create the statefulness and loops between agents, where each agent has its own state. Every time it's re-invoked, it gets back its same state and essentially has a solid understanding of all the decisions it's made thus far in the relevant project: its decision logs, its rationale, full reasoning trajectories, everything, so that the context is actually there. Each of these agents needs to do its own summarization, etc., its own context curating. I provided you all this information all as supporting context for you to be able to reason about this specifically. Don't focus so much on the file system, etc. I need you to focus more on how to make this possible. Basically, what I need you to wrestle with is: should these agents be sub-agents, compiled sub-agents of the PM, or do they all need to genuinely be their own create deep agent with their own checkpoint errs? Everything, and if so, how does the system work? How do these agents communicate with each other? How does the PM essentially then communicate to the harness engineer, "Hey, here's this, etc."
---
/Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/tmp.md this file is a temporary scratch pad where I typed up some high-level requirements that have not yet been resolved. Meaning there's some decision in regards to this LLM application that I have not been able to take due to not knowing what avenue or what final architecture I should choose.

I provided an SME with the contents of this file in the shape of a memo, and they addressed it and gave me some pretty good signal, but their response did not fully solve our dilemma. here is where the transcript is /Users/Jason/2026/v4/meta-agent-v5.6.0/meta_harness/SME.md

I'm going to provide you with the full transcript of the conversation with the SME. Ultimately, I'll be needing you to decide what the ultimate design should be. The good news is I don't need you to come up with specific schemas or state machine logic or anything of the sort. I simply need you to add at a high abstract level: at which abstraction should we be working in regards to Langchain? Is it deep agents? Are we going to have to implement Langgraph logic, and if so, how much? Etc. Treat this as a deep research task.

ability. to delegate to sub-agents who serve as your workers. Use them as you see fit. You have full agency on your strategy.
<*/Questions sent to SME*>
---

## HIGH-LEVEL REQUIREMENTS  ~~(NOT YET RESOLVED)~~  ✅ 

> **Status:** Initial topology and agent statefulness questions addressed in `meta_harness/SME.md` with assistance from a subject matter expert. Core decisions resolved: each agent should be its own `create_deep_agent()` with project-scoped `thread_id`, explicit handoff tools (not sub-agents), and filesystem-backed coordination.
>
> **Still open:** The suggested LangGraph coordination layer for deterministic phase gates, routing state, and pass/fail transitions. Need additional signal on how the thin coordinator integrates with the Deep Agents harness.

---

## Core Agent Roles

### Project Manager (PM)

- **Responsibility**: Business-oriented project manager with exceptional organizational skills
- **Function**: Translates stakeholder vision into clear requirements and evaluation criteria — defining **WHAT** success looks like
- **Key Capability**: Context building and project scope dissemination

### Harness Engineer

- **Responsibility**: PM's brightest technical coworker — the scientific authority on evaluation
- **Function**: Owns **HOW** to evaluate: scoring rubrics, LLM judge assembly, calibration methodology, runs experiments, designs eval harnesses, serves as full agent harness engineer and harness topology

---

## Critical Design Constraint: PM Self-Awareness

When the PM finishes shaping evaluation criteria and business-logic datasets with stakeholders, it must recognize:

> *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."*

This self-awareness — knowing where its expertise ends and the Harness Engineer's begins — is a core design constraint.

---

## Communication Architecture

### PM Context Broadcasting Mechanism

The PM should be able to send a "burst of information" to all relevant agents (researcher, architect, harness engineer) when project scope is clear.

**Implementation Option**: Shared `@AGENTS.md` file per project that serves as:

- A communication board accessible to all agents
- PM's mechanism for publishing high-signal project information
- Context engineering foundation in the agent memory filesystem

---

## Workflow Handoffs & Loops

### Phase 1: PM → Harness Engineer Handoff

1. **PM recognizes completion** of stakeholder discussions and PRD finalization
2. **PM communicates** to Harness Engineer:
   - Final PRD
   - Evaluation criteria
   - Rough draft datasets from stakeholder
3. **Harness Engineer responsibilities**:
   - Finalize datasets and evaluation criteria
   - Create scoring rubrics
   - Generate held-out datasets for LLM judge calibration and final phase experiments against target harness and target application
   - Create evaluation criteria and datasets for researcher consumption

#### Feedback Loop Capability

- Harness Engineer may have questions for PM → PM asks high-signal questions to stakeholder
- Harness Engineer can use `ask_user` middleware tool for targeted stakeholder questions
- Loop must be optional but available
- Deep Agent's CLI shows an example of this `ask_user` middleware and tool

### Phase 2: Researcher ↔ Architect Collaboration

- **Architect's role**: NOT to research, but to design based on research bundle and PRD
- **Researcher's role**: Identify SDKs, APIs, abstractions to satisfy PRD requirements (LangChain abstraction biased due to the robustness and elegance of the full LangChain ecosystem — LangChain, LangGraph, and Deep Agents)

#### Research Focus Areas

- LangChain ecosystem (LangGraph, Deep Agents)
- Model capabilities (Anthropic, OpenAI documentation)
- LLM application APIs (Fire, Crawl, LlamaIndex, etc.)
- Subject Matter Expert identification (curated SMEs provided in system prompt)

#### Architect-Researcher Loop

- Architect identifies knowledge gaps ("I need more info on X SDK/API, I need to know more about this model's capabilities and the correct way to use these model-specific APIs.")
- Requests targeted research from Researcher
- Waits for Researcher completion before proceeding with final design

#### Architect's Design Deliverables

- Full application design and specification
- Complete tool schemas
- System prompts and tool messages
- Zero-ambiguity architecture documentation
- Has full rein on designing his own designs. Is fully versed in an elegant approach to creating LLM applications. Is ambitious and confident enough to create novel designs that don't currently exist and has a full inventory of existing repos so that it can see how other production agents handle semantically similar situations that the architect may be facing when building his own target harness or application
- Context for downstream planner agent

### Phase 3: Architect → Planner Handoff

1. **Architect completes** full design specification (may be multiple documents):
   - Requirements document
   - Design document
   - Task list with phases
2. **Harness Engineer re-engagement** before planner receives work:
   - May have questions for the architect when creating eval harness, evaluation logic, data sets, etc.
   - Evaluates new tools/system prompts introduced by architect
   - Creates evaluation criteria for target harness components
   - Designs evaluation harness for development phase
   - Manages dataset strategy (public vs held-out)
   - Establishes LangSmith upload strategy for visibility

**Data Management Principle**: All agent artifacts and memory must exist in the filesystem (virtual or disk-based)

### Phase 4: Planner → Developer Handoff

- **Planner receives**: Full design, spec, public eval criteria, public datasets
- **Planner creates**: End-to-end development plan with structured phases
- **Note**: Held-out datasets remain exclusively with Harness Engineer for final testing

### Phase 5: Development & Evaluation Loop

- **Developer role**: Execute plan using spec as reference, orchestrate subagents, maintain context isolation
- **Developer as optimizer**: Pause between phases for evaluation and experimentation
- **Evaluation triggers**: Phase completion, major milestones

#### Dual Evaluation System

1. **Harness Engineer**: Runs technical evaluations on target harness
2. **Evaluator Agent**:
   - Validates code alignment with design spec and plan
   - Ensures naming conventions and SDK compliance
   - Tests UX/UI components (spins up frontend, records interactions)
   - Hard fails/passes development phases

### Final Delivery

- Both Harness Engineer and Evaluator Agent run final acceptance tests
- Create comprehensive screen recordings of application interaction
- Bundle all deliverables including final artifacts and documentation

---

## Agent-Backed Filesystem

### Full Backend Memory File System Structure

*Proposed; subject to change.*

```
~/Agents/
├── AGENTS.md                    ← shared team memory (PM writes here)
├── pm/
│   ├── AGENTS.md                ← PM core memory (always loaded via memory=)
│   ├── memory/                  ← PM on-demand memory files (selectively loaded)
│   ├── skills/                  ← PM skills (SKILL.md subdirs)
│   └── projects/                ← PM project tracking (all tagged with a project ID)
├── architect/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/                ← Architect project specs
│       ├── specs-(Previous)     ← Previous spec versions (tagged with project ID)
│       └── target-spec/         ← Current target specification
├── researcher/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── research-bundles/    ← Compiled research artifacts (tagged with project ID)
├── planner/
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── plans/               ← Generated development plans
├── dev/                         ← Developer / Generator / Optimizer
│   ├── AGENTS.md
│   ├── memory/
│   ├── skills/
│   └── projects/
│       └── wip/                 ← Work-in-progress implementations
└── harness-engineer/
    ├── AGENTS.md
    ├── memory/
    ├── skills/
    └── projects/
        ├── eval-harnesses/      ← Evaluation harness definitions
        ├── datasets/
        │   ├── public/          ← Public datasets for dev phases
        │   └── held-out/        ← Held-out datasets for final eval
        ├── rubrics/             ← Scoring rubrics and criteria
        └── experiments/         ← Experiment logs and results
```