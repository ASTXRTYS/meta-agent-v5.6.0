# @Vtrivedy10 (Viv) SME Input — Onboarding Guide

**Author:** @Vtrivedy10 — agents & evals @LangChain, prev @awscloud, PhD CS @templeuniv  
**Scope:** Harness engineering, hill-climbing agents, optimizer agents, evaluation design, overfitting mitigation, LangSmith workflows, Model-Harness training loops  
**Last Updated:** April 2026

---

## What's In This Directory

```
SME/Vivek-Langchain/
├── Readme.md              # This file — orientation + conceptual summary
└── Twitter-Articles/
    └── "How-we-build-evals-for-deep-agents".md  # Detailed eval recipes from LangChain
```

**Source Material:** Exhaustive extracts from Viv's X posts and replies (April 2026). All quotes below are verbatim; context preserved where he replies in threads.

---

## Core Mental Models (The 30-Second Version)

### 1. The Model-Harness Training Loop
Every great team will run a variant of this:

```
Model + Harness → Run Evals → Mine Traces → Identify Failure Modes → 
Tune Harness (prompts, tools, hooks) → Accumulate Data Moat → 
Fine-Tune Model on Collected Data → Repeat
```

**Why this works now:** (1) Harness engineering is democratized, (2) open models crossed an intelligence threshold (GLM 5), (3) LangSmith enables trace collection at scale, (4) fine-tuning infra is accessible (PrimeIntellect).

> *"The cycle of harness engineering → finetuning with open models is gonna give us an explosion of task-specific frontier-level performance at a fraction of the cost."*

### 2. Harness Engineering Derived from Model Limitations
Work backwards from what a model *can't* do today. Filesystems, bash, compaction, Ralph Loops — all primitives added because models lack those capabilities natively.

> *"Models are fundamentally token input/output machines. They cannot do useful things in the world without a harness."*

### 3. The "No General-Purpose Harness" Principle
There is no general-purpose agent/harness. "General purpose" just means "reasonable tradeoff between acceptable performance and time/money spent."

> *"Teams that want top 1% agent performance obsessively tweak the harness per Task+Model... models are non-fungible in their harness."*

Viv's bullish take: **just-in-time harness creation** — a base harness customized per task via an optimizer agent + human-in-the-loop.

### 4. Evals as Training Data
```
agent = fit(model, harness, evals)
```

- Evals encode desired behavior (like training data encodes gradients in ML)
- Rubrics "densify" feedback (scalar → multi-category) for hill-climbing
- "Spring cleaning" evals matters — deprecate ones you no longer need
- Batching edits across tasks beats per-task optimization (avoids overfitting)

> *"Prompt/harness opt on individual tasks is prone to local (over)fitting behaviors... grouping edits across batches of tasks is often much better."*

### 5. Model-Harness Codesign + RL
GEPA (<1 year old) sparked the hill-climbing movement. The frontier: combining harness optimization with RL.

> *"Eventually harness opt hits the wall of model intelligence. We can break through by RLing on good evals... new weights shape intelligence where an updated harness can better use these new weights."*

---

## Key Techniques & Practices

| Practice | Rationale |
|----------|-----------|
| **Holdout sets** | Ground hill-climbing to avoid overfitting on evals |
| **Rubrics over binary pass/fail** | Dense feedback signal for optimization |
| **Trace mining in LangSmith** | Find errors → cluster → correct → experiment |
| **Batch edits across tasks** | Higher-leverage strategies vs. local task tuning |
| **Spring-clean evals** | Evals are model/harness dependent; stale ones mislead |
| **LLM-as-judge for traces without ground truth** | Environment feedback + rubrics enable reflection |

---

## LangSmith as the Enabling Infrastructure

Viv consistently points to LangSmith as the substrate that makes the loop practical:

> *"We have mechanisms to collect traces and analyze them at massive scale... Traces + Evals are the lifeblood of agent improvement loops."*

**Workflow:** Run agent → Capture traces → Generate evals from traces → Tune harness → Retest → Mine *new* traces for self-improvement data.

---

## Deeper Reading

| File | Content |
|------|---------|
| `Twitter-Articles/"How-we-build-evals-for-deep-agents".md` | LangChain's eval design recipes, CI integration, LangSmith at-scale practices |
| **Original extracts below** | Verbatim post/reply compilation by topic (preserved for reference) |

---

## Verbatim Source Extracts (By Topic)

<details>
<summary><strong>1. Model-Harness Training Loop & Harness Engineering Philosophy</strong> (Click to expand)</summary>

**Main Post — "The Model-Harness Training Loop" (Apr 3 2026)**  
"The Model-Harness Training Loop  

imo every great team in the world will use some version of this loop to build the best agents for their tasks  

this is now possible because:  
1. Harness Engineering is becoming more democratized and accessible  
2. Open models have crossed an intelligence threshold (ex: GLM 5)  
3. We have mechanisms to collect traces and analyze them at massive scale (ex: LangSmith)  
4. The infra to fine-tune models is becoming more accessible (ex: @PrimeIntellect)  

Open models give every team the opportunity to try this, not just frontier labs..."

**Reply (to @nichochar):** "agree with this, there's full companies that fully optimize on harness eng and they kill it in their vertical but there's def another ceiling to push through beyond harness eng which you get from touching the weights, basically vertical focused RL"

**Reply (to @spenceships on Ralph Loops):** "Ralph loop + a well designed context system, hooks, experiment setup is basically good auto-research but agree blind Ralph loops are bad... Geoff's whole point with Ralph is to design the loop well"

**Main Post — "Harness Engineering Derived from what Models can't do alone" (Apr 14 2026)**  
"Harness Engineering Derived from what Models can't do alone:  

It feels like a good time to step back and reshare some basic mental models for why harnesses exist in the first place - working backwards from The Model  

Why the Harness Exists:  
Harnesses exist to augment and shape models to do useful work for us. Models are fundamentally token input and output machines  

They cannot do useful things in the world without a harness..."
</details>

<details>
<summary><strong>2. Task-Specific vs "General Purpose" Harnesses</strong> (Click to expand)</summary>

**Main Post — Hot Take (Apr 3 2026)**  
"ok hot take, who (dis)agrees? The general purpose agent/harness doesn't exist  

the best harnesses are deeply Task specific and when we use a "default harness" out-of-the-box, we're just making a tradeoff between  
- acceptable task performance  
- time+money spent designing around our task(s)  

that's a totally fair tradeoff to make..."

**Reply (to @bu7emba on just-in-time):** "i'm quite bullish on a decent base harness that we customize per task/goal with an agent + human in the loop basically what prompts, tools, hooks, feedback mechanisms, orchestration do we need our v1 will be meh but that's ok, evals and trace data are what we'll use to improve..."
</details>

<details>
<summary><strong>3. Hill-Climbing Agents, Evals as Training Data</strong> (Click to expand)</summary>

**Main Post — "Data Driven Agent Design with Evals & Hill Climbing Algorithms" (Apr 17 2026)**  
"Data Driven Agent Design with Evals & Hill Climbing Algorithms  

this is a mental model dump i've been thinking through + iterating on as we're building self-improvement infra around agents:  
- mining Trace Data to find errors and tweak the agent harness  
- building + maintaining evals  
- using evals to guide the agent update/generation process  

What are the inputs for fitting an agent:  
the main idea is what does a sklearn fit(model, data) function look like for agents  

agent = fit (model, harness, evals)  

Data Driven Agent Design:  
Evals are training data for agents - every eval encodes behavior we want to see in our agent..."

**Reply (to @hammad_khan23 on mining traces without ground truth):** "asking the real questions 💯 few things: -if we have evals, we have verifiers - for traces without ground truth, LLM judge with examples and categories of issues... cluster errors from traces, try to correct, and run experiments..."
</details>

<details>
<summary><strong>4. GEPA, Hill-Climbing + RL, Model-Harness Codesign</strong> (Click to expand)</summary>

**Main Post — GEPA Reflection (Apr 24 2026)**  
"GEPA <1 years old 😮  

incredible the impact that the ideas here have spawned on hill climbing + improving agents  

does anyone know of cool work on looping/GEPA/Optimize_Anything + RL?  

main ideas:  
- eventually harness opt hits the wall of model intelligence  
- we can break through that wall by RLing on good evals that increase model ability in the eval domains  
- new weights shape intelligence where an updated harness can better use these new weights  
- loop  

Model-Harness codesign is really interesting, we're pushing here much more with using traces to create datasets for self-improvement"

**Reply (to @JoshPurtell):** "related in my resounding experience, prompt/harness opt on individual tasks is prone to local (over)fitting behaviors on the task level but grouping edits across batches of tasks is often much better..."
</details>

<details>
<summary><strong>5. LangSmith & Trace Infrastructure</strong> (Click to expand)</summary>

**Recurring themes:**
- "We have mechanisms to collect traces and analyze them at massive scale (ex: LangSmith)"
- "start mining its traces in LangSmith to create data for self-improvement 🚀"
- "Traces + Evals are the lifeblood of agent improvement loops"
- "Evals encode the behavior we want agents to have in production. Generating evals from traces is how we figure out how to measure the changes we're making over time."

**Reply (to @vertr_ai):** "This loop is how the agent market fragments into verticals. Every harness-train cycle builds a data moat competitors can't replicate."
</details>

---

## How to Use This Material

1. **For harness design decisions:** Check the "Core Mental Models" section first — Viv's principles should constrain/validate design choices.

2. **For eval design specifics:** See `Twitter-Articles/"How-we-build-evals-for-deep-agents".md` — contains concrete LangChain recipes.

3. **For verbatim quotes/attribution:** Expand the source sections above — all quotes are verbatim from Viv's X posts for direct citation.

4. **For staying current:** Viv posts actively. This extract is current as of April 2026. Key themes to watch: RL + harness codesign, just-in-time harness creation, eval generation from traces at scale.

---

*End of onboarding guide. For questions or to request updated extracts, ping the Meta Harness team.*