# LangSmith Development Guide

This project uses skills that contain up-to-date patterns and working reference scripts for LangSmith observability and evaluation.

## CRITICAL: Invoke Skills BEFORE Writing Code

**ALWAYS** invoke the relevant skill first - skills have the correct imports, patterns, and scripts that prevent common mistakes.

### LangSmith Skills
- **langsmith-trace** - Invoke for ANY trace querying or analysis
- **langsmith-dataset** - Invoke for ANY dataset creation from traces
- **langsmith-evaluator-architect** - Invoke for UI-ready evaluator profile design, judge prompts, JSON schemas, and SDK scaffolding
- **langsmith-evaluator** - Invoke for evaluator implementation, run functions, and evaluation execution

## Debugging Flow: Build → Trace → Dataset → Evaluate

When stuck or debugging, use this powerful workflow:
1. **Run agent** to generate traces in LangSmith
2. **Query traces** using `langsmith-trace` to find interesting examples
3. **Create dataset** using `langsmith-dataset` from those traces
4. **Design evaluator** using `langsmith-evaluator-architect` when you need judge prompts or LangSmith UI configs
5. **Build evaluator** using `langsmith-evaluator` when you need code, run functions, or execution wiring

Each skill includes reference scripts in `scripts/` - use these instead of writing from scratch.

## Environment Setup

Required environment variables:
```bash
LANGSMITH_API_KEY=<your-key>
LANGSMITH_PROJECT=<project-name>  # Optional, defaults to "default"
OPENAI_API_KEY=<your-key>  # For OpenAI models
ANTHROPIC_API_KEY=<your-key>  # For Anthropic models
```
