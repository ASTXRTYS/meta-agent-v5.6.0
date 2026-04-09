---
inclusion: always
---

# SDK Alignment Rules

## Mandatory Reference Protocol

Before suggesting, planning, implementing, or creating specs for anything in this codebase, you MUST consult the appropriate canonical references below. Do not rely solely on general knowledge or training data.

## LangChain / LangGraph

- Always read `.agents/skills/langchain` before any implementation, planning, or spec work involving LangChain or LangGraph.
- If the skill leaves you below 95% confidence on an import, middleware behavior, or SDK convention, escalate to the canonical SDK source at .reference/libs/deepagents/deepagents/`  or at the production example listed below.

## Deep Agents SDK

- The canonical SDK reference is `.reference/libs/deepagents/deepagents/`.
- A production usage example is at `.reference/libs/cli/deepagents_cli`.
- Any time you are uncertain about `create_deep_agent()`, middleware, backends, or SDK imports, read the local source directly — do not guess.

## LangSmith Tracing & Evaluations

- Always read `.agents/skills/langsmith` before implementing tracing, observability, or any evaluation logic.
- The canonical LangSmith Python SDK reference is `.venv/lib/python3.11/site-packages/langsmith/`.
- For evaluation logic specifically, also reference `.venv/lib/python3.11/site-packages/agentevals/` — this is the SDK used for creating evals in this project.
- These references apply to: discussing evals, planning eval structure, writing eval code, or running experiments.

## Confidence Threshold

If you are below 95% confident about how any import, middleware, or SDK behavior works, you MUST read the local source before proceeding. Skill files are baseline context — not exhaustive references.
