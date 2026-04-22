# Product Roles and Workflow

This document captures the agent role definitions, handoff phases, and communication
architecture for Meta Harness. It is the product-level requirements source — not
implementation rules. For the resolved architecture, see `AD.md` §2.

---

## Highest-Level Decisions

- Meta Harness will adopt the Deep Agents harness from langchain as its primary
  agent runtime/framework.
- Deep Agents is an excellent default harness layer for open-ended, multi-step
  agent work which can be perfectly tuned for a task by carefully crafted system
  prompts, task-specific tools, skills, and an opinionated file system for
  memory.
- From day one, we need to ship our LLM application to allow our agents to have their own virtual machine and their own virtual file system. With that being said, we need to also ship the capability to use our LLM application as a local-first system where the file system for memory and artifact persistence can be stored on the user's disk if the user so desires. There must be dual modality, local-first, and also the ability for the agent to spin up its own virtual machine and entirely run inside of a sandbox.
- For the deep agents abstraction, Langchain ships the majority of all needed logic to develop an agent harness or an LLM application. We must always leverage what the deep agents SDK provides and embrace middleware as an extension of the deep agent's harness abilities.
- A rewrite is allowed to be incremental. New v1 code should be clean enough
  that old v0.5 code can be ported over one behavior at a time.
- We will ship with our main agent, which is going to be the direct interface that most users will interact with. Other agents will be part of this LLM application, and it is to be decided whether they should be sub-agents or have the same or be their own standalone agent. The researcher, who is in charge of researching, should itself be fully stateful and capable of managing its own set of sub-agents, so the researcher must be its own deep agent as well. We will ship with an architect who, as I mentioned for the researcher, must be stateful, have its own memory, and be its own create deep agent that has access to all the benefits of the deep agent harness. The same applies for all of the agents that I will mention here:
- The planner, our planner agent
- our developer agent who serves as our coding agent, essentially our generator
- our harness engineer agent
- and our evaluator agent  All of these agents together serve as an LLM application for developing, observing, and shipping other LLM applications. The decision that I am wrestling with is: should we have the project manager as its own agent and all these other agents serve as sub-agents, or should each agent serve as its own deep agent separately without needing to be a sub-agent? In my articulation, I realize I must clarify that, when I say, "should these agents be sub-agents of the PM in a world where they do end up being the sub-agents of the PM," they must also be deep agents, even if they are sub-agents. The only thing that I am attempting to articulate is: should they be compiled as sub-agents, or should they be their own deep agent? This is the decision matrix that I am wrestling with.

## HIGH-LEVEL REQUIREMENTS (NOT YET RESOLVED)

### **"PM Scopes Criteria, Harness Engineer Owns the Science"**

---

### **Core Agent Roles**

#### **Project Manager (PM)**
- **Responsibility**: Business-oriented project manager with exceptional organizational skills
- **Function**: Translates stakeholder vision into clear requirements and evaluation criteria — defining **WHAT** success looks like
- **Key Capability**: Context building and project scope dissemination

#### **Harness Engineer**
- **Responsibility**: PM's brightest technical coworker — the scientific authority on evaluation
- **Function**: Owns **HOW** to evaluate: scoring rubrics, LLM judge assembly, calibration methodology,runs experiments, designs eval harnesses, serves as full agent harness engineer and harness topology

---

### **Critical Design Constraint: PM Self-Awareness**
When the PM finishes shaping evaluation criteria and business-logic datasets with stakeholders, it must recognize:

> *"I have the full PRD, product vision, all requirements, eval criteria, and business-logic datasets. Time to bring in the expert."*

This self-awareness — knowing where its expertise ends and the Harness Engineer's begins — is a core design constraint.

---

### **Communication Architecture**

#### **PM Context Broadcasting Mechanism**
The PM should be able to send a "burst of information" to all relevant agents (researcher, architect, harness engineer) when project scope is clear.

**Implementation Option**: Shared `@AGENTS.md` file per project that serves as:
- A communication board accessible to all agents
- PM's mechanism for publishing high-signal project information
- Context engineering foundation in the agent memory filesystem

---

### **Workflow Handoffs & Loops**

#### **Phase 1: PM → Harness Engineer Handoff**
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

#### **Feedback Loop Capability**
- Harness Engineer may have questions for PM → PM asks high-signal questions to stakeholder
- Harness Engineer can use `ask_user` middleware tool for targeted stakeholder questions
- Loop must be optional but available
- Deep Agent's CLI shows an example of this `ask_user` middleware and tool.

#### **Phase 2: Researcher ↔ Architect Collaboration**
- **Architect's role**: NOT to research, but to design based on research bundle and PRD
- **Researcher's role**: Identify SDKs, APIs, abstractions to satisfy PRD requirements (langchain abstraction biased due to the robustness and elegance of the full Langchain ecosystem (i.e., Langchain, Langgraph, and Deep Agents).

**Research Focus Areas**:
- LangChain ecosystem (LangGraph, Deep Agents)
- Model capabilities (Anthropic, OpenAI documentation)
- LLM application APIs (Fire, Crawl, LlamaIndex, etc.)
- Subject Matter Expert identification (curated SMEs provided in system prompt)

**Architect-Researcher Loop**:
- Architect identifies knowledge gaps ("I need more info on X SDK/API, I need to know more about this model's capabilities and the correct way to use these model-specific APIs.")
- Requests targeted research from Researcher
- Waits for Researcher completion before proceeding with final design

**Architect's Design Deliverables**:
- Full application design and specification
- Complete tool schemas
- System prompts and tool messages
- Zero-ambiguity architecture documentation
- Has full rein on designing his own designs. Is fully versed in an elegant approach to creating LLM applications. Is ambitious and confident enough to create novel designs that don't currently exist and has a full inventory of existing repos so that it can see how other production agents handle semantically similar situations that the architect may be facing when building his own target harness or application.
- Context for downstream planner agent

#### **Phase 3: Architect → Planner Handoff**
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

#### **Phase 4: Planner → Developer Handoff**
- **Planner receives**: Full design, spec, public eval criteria, public datasets
- **Planner creates**: End-to-end development plan with structured phases
- **Note**: Held-out datasets remain exclusively with Harness Engineer for final testing

#### **Phase 5: Development & Evaluation Loop**
- **Developer role**: Execute plan using spec as reference, orchestrate subagents, maintain context isolation
- **Developer as optimizer**: Pause between phases for evaluation and experimentation
- **Evaluation triggers**: Phase completion, major milestones

**Dual Evaluation System**:
1. **Harness Engineer**: Runs technical evaluations on target harness
2. **Evaluator Agent**: 
   - Validates code alignment with design spec and plan
   - Ensures naming conventions and SDK compliance
   - Tests UX/UI components (spins up frontend, records interactions)
   - Hard fails/passes development phases

#### **Final Delivery**
- Both Harness Engineer and Evaluator Agent run final acceptance tests
- Create comprehensive screen recordings of application interaction
- Bundle all deliverables including final artifacts and documentation
