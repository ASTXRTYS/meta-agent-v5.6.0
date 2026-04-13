# Environment

**What belongs here:** Required env vars, external dependencies, setup notes.
**What does NOT belong here:** Service ports/commands (use `.factory/services.yaml`).

## Required Environment Variables

```
LANGSMITH_API_KEY=<key>           # LangSmith tracing
LANGSMITH_TRACING=true            # Enable tracing
LANGSMITH_PROJECT=meta-harness    # Project name
LANGCHAIN_CALLBACKS_BACKGROUND=false  # Sync flush for evals
```

## Python Environment

- Python 3.14.3 (system)
- Meta Harness creates its own `.venv` inside `meta_harness/`
- Reference SDK at repo root `.reference/` and `.venv/` are READ-ONLY

## Key Dependencies

- `deepagents>=0.4.12` — agent harness SDK
- `langchain>=1.2.15` — core LLM framework
- `langgraph>=1.1.6` — graph orchestration
- `langchain-anthropic>=1.4.0` — Anthropic integration
- `langchain-collapse>=0.1.1` — CollapseMiddleware
- `textual>=3.0` — TUI framework
- `langgraph-checkpoint-sqlite` — local checkpointer
- `pydantic>=2.12` — data validation

## Machine Specs

- 8GB RAM, 8 CPU cores (macOS)
- No Docker required for v1
- SqliteSaver for local checkpoints (no external DB)
