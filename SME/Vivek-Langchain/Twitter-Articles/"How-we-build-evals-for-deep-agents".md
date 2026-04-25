# Evals Shape Agent Behavior

**TL;DR:** The best agent evals directly measure an agent behavior we care about. Here’s how we source data, create metrics, and run well-scoped, targeted experiments over time to make agents more accurate and reliable.

## Evals shape agent behavior

We’ve been curating evaluations to measure and improve **Deep Agents**. Deep Agents is an open source, model-agnostic agent harness that powers products like Fleet and Open SWE. Evals define and shape agent behavior, which is why it’s so important to design them thoughtfully.

Every eval is a vector that shifts the behavior of your agentic system. For example, if an eval for efficient file reading fails, you’ll likely tweak the system prompt or the `read_file` tool description to nudge behavior until it passes. Every eval you keep applies pressure on the overall system over time.

It is crucial to be thoughtful when adding evals. It can be tempting to blindly add hundreds (or thousands) of tests. This leads to an illusion of “improving your agent” by scoring well on an eval suite that may not accurately reflect behaviors you care about in production.

**More evals ≠ better agents.** Instead, build targeted evals that reflect desired behaviors in production.

When building Deep Agents, we catalog the behaviors that matter in production, such as retrieving content across multiple files in the filesystem or accurately composing 5+ tool calls in sequence. Rather than using benchmark tasks in aggregate, we take the following approach to eval curation:

- Decide which behaviors we want our agent to follow.
- Then research and curate targeted evals that measure those behaviors in a verifiable way.

For each eval, add a docstring that explains how it measures an agent capability. This ensures each eval is self-documenting. We also tag each eval with categories like `tool_use` to enable grouped runs.

Review output traces to understand failure modes and update eval coverage.

Because we trace every eval run to a shared LangSmith project, anyone on the team can jump in to analyze issues, make fixes, and reassess the value of a given eval. This creates shared responsibility for adding and maintaining good evals. Running many models across many evals can also get expensive, so targeted evals save money while improving your agent.

In this post we cover:
- How we curate data
- How we define metrics
- How we run the evals

## How we curate data

There are a few ways we source evals:

- Using feedback from dogfooding our agents
- Pulling selected evals from external benchmarks (like Terminal Bench 2.0 or BFCL) and often adapting them for a particular agent
- Writing our own (artisanal) evals and unit tests by hand for behaviors we think are important

We dogfood our agents every day. Every error becomes an opportunity to write an eval and update our agent definition & context engineering practices.

> **Note:** We separate SDK unit and integration tests (system prompt passthrough, interrupt config, subagent routing) from model capability evals. Any model passes those tests, so including them in scoring adds no signal. You should absolutely write unit and integration tests, but this post focuses solely on model capability evals.

### Dogfooding agents & reading traces are great sources of evals

This makes finding mistakes possible. Traces give us data to understand agent behavior. Because traces are often large, we use a built-in agent like Polly or Insights to analyze them at scale. (You can do the same with other agents like Claude Code or the Deep Agents CLI, plus a way to pull down traces like the LangSmith CLI.) Our goal is to understand each failure mode, propose a fix, rerun the agent, and track progress and regressions over time.

For example, a large fraction of bug-fix PRs are now driven through Open SWE, our open-source background coding agent. Teams using it touch many different codebases with different context, conventions, and goals. This naturally leads to mistakes. Every interaction of Open SWE is traced, so those can easily become evals to make sure the mistake doesn’t happen again.

Other evals are pulled and adjusted from existing benchmarks like BFCL for function calling. For coding tasks, we integrate with Harbor to run selected tasks from datasets like Terminal Bench 2.0 in sandboxed environments. Many evals are written from scratch and act as focused tests to observe isolated behavior, like testing a `read_file` tool.

### We group evals by what they test

It’s helpful to have a taxonomy of evals to get a middle view of how agents perform (not a single number, not individual runs).

**Tip:** Create that taxonomy by looking at *what they test*, not where they come from. For example, tasks from FRAMES and BFCL could be tagged “external benchmarks,” but that would not show how they measure retrieval and tool use, respectively.

Here are some categories we define and what they test:

*(Original post included a table/image here showing the eval taxonomy. The key idea is grouping by behavior such as retrieval, tool use, multi-turn interaction, etc.)*

Today, all evals are end-to-end runs of an agent on a task. We intentionally encourage diversity in eval structure. Some tasks finish in a single step from an input prompt, while others take 10+ turns with another model simulating a user.

## How we define metrics

When choosing a model for our agent, we start with **correctness**. If a model can’t reliably complete the tasks we care about, nothing else matters. We run multiple models on our evals and refine the harness over time to address the issues we uncover.

Measuring correctness depends on what’s being tested:
- Most internal evals use custom assertions (e.g., “did the agent parallelize tool calls?”).
- External benchmarks like BFCL use exact matching against ground truth.
- For semantic correctness (e.g., whether the agent persisted the correct thing in memory), we use LLM-as-a-judge.

Once several models clear that bar, we move to **efficiency**. Two models that solve the same task can behave very differently in practice. One might take extra turns, make unnecessary tool calls, or move more slowly because of model size. In production, those differences show up as higher latency, higher cost, and a worse user experience.

All together, the metrics we measure for each evaluator run are:

**Solve rate** measures how quickly an agent solves a task, normalized by the expected number of steps. Like latency ratio, it captures end-to-end time to solve the task (model round trips, provider latency, wrong turns, and tool execution time). For simple tasks where we can define an ideal trajectory, solve rate can be easier to work with than latency ratio because it only requires measuring the given agent’s task duration.

This gives us a simple way to choose models with a targeted eval set:
1. Check correctness first: Which models are accurate enough on the tasks you actually care about?
2. Then compare efficiency: Among the models that are good enough, which one gives the best tradeoff between correctness, latency, and cost?

### Example of useful metrics around evals

To make model comparisons actionable, we examine *how* models succeed and fail. One primitive we use is an **ideal trajectory** — a sequence of steps that produces a correct outcome with no “unnecessary” actions.

For simple, well-scoped tasks, the optimal path is usually obvious. For more open-ended tasks, we approximate a trajectory using the best-performing model we’ve seen so far and revisit the baseline as models and harnesses improve.

**Example request:**
> “What is the current time and weather where I live?”

**Ideal trajectory:**
- Fewest necessary tool calls (resolve user → resolve location → fetch time and weather)
- Parallelizes independent tool calls where possible
- Produces the final answer without unnecessary intermediate turns

**Ideal trajectory stats:** 4 steps, 4 tool calls, ~8 seconds

**Inefficient but still correct trajectory:** 6 steps, 5 tool calls, ~14 seconds (includes an unnecessary tool call and doesn’t parallelize).

Both runs are correct, but the second increases latency and cost and creates more opportunities for failure.

This framing lets us evaluate both correctness *and* efficiency. We maintain and update metrics to distill runs into measurable numbers we can use to compare experiments.

## How we run evals

We use **pytest** with GitHub Actions to run evals in CI so changes run in a clean, reproducible environment. Each eval creates a Deep Agent instance with a given model, feeds it a task, and computes correctness and efficiency metrics.

We can also run a subset of evals using tags to save costs and measure targeted experiments. For example, if building an agent that requires a lot of local file processing and synthesis, we may focus on the `file_operations` and `tool_use` tagged subsets.

Our eval architecture and implementation is open sourced in the [Deep Agents repository](https://github.com/langchain-ai/deep-agents).

## What’s next

We’re expanding our eval suite and doing more work around open-source LLMs! Some things we’re excited to share soon:
- How open models measure against closed frontier models across eval categories
- Evals as a mechanism to auto-improve agents for tasks in real time
- Openly share how we maintain, reduce, and expand evals per agent over time

Thanks to the great team who helped review and co-write this: @masondrxy, @veryboldbagel, @hwchase17.

Also published on the LangChain blog.

**Deep Agents is fully open source.** Try it and let us know what you think! We’re excited to help teams build great agents & evals.