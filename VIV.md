1. Avoiding optimizer agents from overfitting (reward hacking in auto-research/meta-harness/hill-climbing loops)Main post – “A Note from Experience”ID: 2039716329561751928 (Thu, 02 Apr 2026)

A Note from Experience:if you’re running auto-research or meta-harness loops using evals your agent can see…pls look at your data for agent updates! agents love overfitting and will rationalize it. it’s easy to get carried away seeing your eval number jump from 20% to 80% (i do this), but we need to verify the changes for leakage this is analogous to reward hacking in RL, we define a metric, the agent does anything to “make number go up” it’s our job to design the system to prevent this for hill-climbing evals, some notes:

- keep a hold-out set per category, you want to measure some sort of “generalization”
- review everything manually (ex: prompt changes, new subagents)
- try limiting the updatable set for any given turn (prompt, subagent, etc)

it’s awesome to throw a bunch of data and compute into a problem and just get good results, but getting the design right is pretty iterative today worth checking if that 50% boost was rlly a 50% boost :)

Key reply on programmatic hooks/middlewareID: 2039720923968782383 (same thread)

programatic hooks/middleware that inject feedback into context (ex: cannot proceed if x files edited tg)

Reply on overfitting to the hill (in Meta-Harness thread)ID: 2038663045002477604 (Mon, 30 Mar 2026)

awesome work!! how do you guys think about “overfitting to the hill”? hold out set? guidelines + manual inspection? love this flavor and have found success with it on tb2 as well at langchain there’s some fun tradeoffs between generalization vs “let me just rock at this task”

Broader take on “overfitting is bad” heuristic for agentsID: 2032209301784154237 (Thu, 12 Mar 2026)

anyone from traditional ML is taught in ML 101 that “overfitting is bad, it doesn’t generalize” but I think it’s worth reconsidering this heuristic in a world of agents because we’re starting to get sparks of usable

- “just-in-time agents” and
- “disposable agents”

the heuristic is there because training a trad ML model took a non-trivial amount of time/compute and if the model didn’t generalize well to slightly out of distribution data, then we had to retrain which isn’t time or cost efficient but we’re probably way more cost/time efficient at fitting agents to narrow datasets via evals and harness engineering today imo evals are the mechanism to distill behavior into an agent. The key is that evals need to be a good enough proxy to capture what the agent should do Every eval that an agent hill climbs on is like a noisy vector that shifts the behavior of the agent towards passing that eval This is of course the hard part. But agents today have passed a threshold where they can efficiently hill climb to overfit themselves to verifiable evals See karpathy’s auto-research and other examples of autonomous benchmaxxing actually I may want an agent to overfit to the narrowish task it’s doing right now at the expense of being good at every other task because maybe we can just-in-time produce + dispose of that agent, then continue working from there on the next task in a way this captures this raging debate today on if LLMs truly generalize or if they’ve just overfit the massive amount pre-training and especially post-training behaviors they need and the question comes up “if LLMs overfit to all the stuff someone actually cares about, does it practically matter that they don’t generalize to other things”? In the limit, I say yes, but for agents doing narrow tasks as part of bigger work, I just want the task to be done correctly I think there’s open questions on:

- ok so how do I generate this eval set to overfit on just-in-time?
- does this work?
- why not just make models smarter overall so they don’t overfit?

i have the same questions but wanted to sort of brain dump this because i think there’s some subset of work where this will be useful and i already see the ability of agents to quickly and autonomously fit themselves to narrow evals as always more to do

1. Best way to provide feedback to an optimizer (guardrails, human-in-loop, programmatic constraints, Judge mechanisms)Multi-player auto-research game idea (Optimizer + Eval Agent + Judge)ID: 2034802115021840829 (Fri, 20 Mar 2026)

idea for one of these nights:auto-research as a multi-player game

- Eval Agent generates a set of evals for user specified goal
- Optimizer hill climbs evals until threshold reached
- Optimizer acceptance is gated by “number go up” + Judge that tries to prevent reward hacking (this is hard)
- Once threshold passed, Eval Agent generates harder evals
- Loop
- Evals are a grounded way of adapting agent behavior
- Getting agents to not reward hack is very hard, I’m curious to see
- Reward design is really important, the above isn’t perfect. I imagine I’ll see some behavior where one agent adversarially nukes the setup

but still optimization with multi-player games, self-play, etc is interesting

Follow-up on curriculum learning angleID: 2034862482750095666 (same thread)

hmmm there’s also a nice curriculum learning angle

- treat additional evals as curricula
- Eval Agent should adapt evals as Optimizer saturates them
- Easy to Hard learning, Composable skills over time based on current learnable frontier

lots of actual research mental models map onto multi-player auto-research this sounds fun enough to have codex take a crack

Human + trace-driven feedbackID: 2040096422511440380 (Fri, 03 Apr 2026)

human feedback is great, we review our evals and prompt changes as a team ex on traces: for our background coding agent, a human is using it and generates a trace. if we want to turn that trace into an eval we’ll read it also ppl ping in Slack all the time with their experience of using the agent

Just-in-time harness customization (agent + human in the loop)ID: 2040204202501181868 (Fri, 03 Apr 2026)

i’m quite bullish on a decent base harness that we customize per task/goal with an agent + human in the loop basically what prompts, tools, hooks, feedback mechanisms, orchestration do we need our v1 will be meh but that’s ok, evals and trace data are what we’ll use to improve each of the levers before this to me is better than a “general agent” that hasn’t selected prompts/tools tailored to the task. and probably in some cases I’m terribly wrong and the agent just in-context learns everything

1. Communicating what an evaluation harness outputs as scores, etc. (scores as training data, constraints, rubrics for hill-climbing)Evals as multi-objective constraints / hill-climbing signal (Knapsack analogy)ID: 2037924832453530004 (Sat, 28 Mar 2026)

“we’re doing constrained optimization” —> a loose mental model on evals as an input to hill climbing and self-improving agents going back to classical CS class - the Knapsack problem! we’re constrained on the weight allowance of our bag and each item has a weight and value, we want to maximize value the weight allowance is a hard constraint, we can’t submit if the total weight exceeds that very smart computer scientists found algorithms to optimize that objective for any arbitrary task we want to do in the world, there is no algorithm instead we use an agent to do “intelligent search” over the option space via agent actions evals are like a multi-objective constraint on the problem the agent is trying to solve, some evals are “blocking”, we won’t proceed if these fail and some are “soft” but important in the overall hill climbing these hard and soft determinations are often human derived as we move towards self-building agents and harnesses, evals are a great way to constrain the solution space by guiding the agent towards solutions that pass those evals this is why it’s so important that evals capture the behavior we care about! Agents directly or indirectly will use them to define themselves autonomous agents are often search machines over the space of all programs. that’s a massive space and only a subset of it corresponds to being “good at our task” evals are the way we climb the gradient to fin that space which is for another time but… evals are like training data! many interesting analogs between evals, classical optimization theory, ML/RL, agent engineering very exciting time to be in the intersection of any of these :)

Evals rhyme with training data + decompose behavior into scores/rubricsID: 2039029715533455860 (Tue, 31 Mar 2026)

evals rhyme with training data the same rigor and care we put into data quality/curation for training should go into eval design training data updates the weights of our models, each example contributes a weight push in some direction to correctly classify that datapoint Evals do the same when we use them to optimize agents without touching weights —> harness engineering cool work like auto-hill-climbing, meta-harness, etc rely on evals as the signal to ground agent updates noisy evals —> noisy signal —> bad agent harness

RL mapping / reflective optimization on failed evalsID: 2037367147421200693 (Fri, 27 Mar 2026)

there’s a great mapping between reward design/RL and writing great evals empathy towards agents failure modes is a good way to improve agents and their feedback mechanisms we basically decompose behavior we want agents to exhibit into scores that reflect whether that behavior was achieved relatedly, very bullish on good evals as “training data” for gradient-free hill climbing ie. make your harness better for the task using signal from evals

@cwolferesearch

has great content on RL with rubrics and I think the mental model translates well to evals reflective optimization on failed evals takes signal from the scores into actionable sub-pieces an agent can improve on good eval sets do that explicitly with diverse and curated design some of the best eval builders would thrive as great RL environments builders, would love to see that :)

Beyond raw scores — understand what the harness actually measuresID: 2038588018957730035 (Mon, 30 Mar 2026)

evals & benchmarks! another awesome blog from Cameron, recommended reading shows what’s actually inside all of the datasets every new model release reports score on + how they’re sourced every eval should measure the agent behavior we want in production benchmarks try to do a decent job proxying broad capabilities like “multi-hop reasoning” but it’s no substitute for reading and understanding each eval with your team