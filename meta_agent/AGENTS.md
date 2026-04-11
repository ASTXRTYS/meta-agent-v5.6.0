# Repository Guidelines

## Project Structure & Module Organization
- `meta_agent/`: core runtime modules (`graph.py`, `server.py`, `model_config.py`, `backend.py`) plus `middleware/`, `tools/`, `stages/`, `subagents/`, and `evals/`.
- `tests/`: canonical suites in `contracts/`, `integration/`, `evals/`, and `drift/`; `tests/unit/` is legacy quarantine.
- `docs/`: architecture and testing references; `datasets/`: eval fixtures; `scripts/testing/`: inventory and traceability utilities.
- Root config: `pyproject.toml`, `Makefile`, `langgraph.json`, `.env.example`.

## Build, Test, and Development Commands
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
langgraph dev
```
- `make test`: run canonical tests (excludes `tests/unit/`).
- `make test-all`: run all tests including legacy quarantine.
- `make test-contracts`, `make test-integration`, `make test-drift`, `make test-evals`: run targeted suites.
- `make evals`, `make evals-p0`, `make evals-p1`, `make evals-p2`: run evaluation pipelines.
- `make lint`: syntax checks for key runtime modules.
- `python scripts/testing/generate_traceability.py`: regenerate testing traceability artifacts after catalog changes.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, explicit type hints.
- Naming: `snake_case` for modules/functions/files, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep shared contracts centralized (e.g., parsing/provisioning/backends) rather than duplicating logic across runtimes.
- Prefer small, composable functions and structured tool/middleware outputs.

## Testing Guidelines
- Use pytest markers correctly: `contract`, `integration`, `eval`, `drift`, `legacy`.
- Add new tests only to `tests/contracts/`, `tests/integration/`, `tests/evals/`, or `tests/drift/`.
- Do not add new tests to `tests/unit/`.
- Include `COVERS:` declarations (and `REPLACES:` when migrating legacy coverage).
- Run `make test` before opening a PR; run drift suites for backend/provisioner/memory changes.

## Commit & Pull Request Guidelines
- Match existing history style: `feat(scope): ...`, `fix: ...`, `refactor: ...`, `docs: ...`, `test: ...`, `chore: ...`.
- Keep commits focused and include related tests/docs updates.
- PRs should include: problem statement, approach, impacted paths, and validation commands/results.
- When implementation changes phase status, update `Full-Development-Plan.md` in the same PR.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and set required API keys.
- Never commit `.env` or secrets.
- Use the repository-local `.venv` to avoid dependency/version drift.
