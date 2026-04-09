# Full Test Suite & Evaluation Guidelines

This document serves as the canonical reference for the testing directories, catalogs, legacy quarantine protocol, and the evaluation toolchain logic used across the project.

## Test Suite Structure

The test suite has two layers: the canonical new suite and a quarantined legacy suite.

### Directory Layout

| Directory | Purpose | Marker | Mock Policy |
| --- | --- | --- | --- |
| tests/contracts/ | Fast invariant tests — no I/O, no model calls | pytest.mark.contract | No unittest.mock allowed |
| tests/integration/ | App composition tests — may use tmp_path, mocks | pytest.mark.integration | Mocks permitted |
| tests/evals/ | Live behavioral tests — real API calls | pytest.mark.eval | Auto-skipped without ANTHROPIC_API_KEY |
| tests/drift/ | Regression/drift guards | pytest.mark.drift | No mocks |
| tests/unit/ | LEGACY QUARANTINE — do not add new tests here | pytest.mark.legacy | Frozen at ceiling of 410 tests |
| tests/_support/ | Shared helpers (fake models, builders, assertions) | N/A — not test files | N/A |

### Makefile Targets

| Target | What It Runs |
| --- | --- |
| make test | New suite only (excludes tests/unit/) — this is the default |
| make test-all | Everything including legacy |
| make test-contracts | Contract tests only |
| make test-integration | Integration tests only |
| make test-evals | Eval tests only (skipped without API key) |
| make test-drift | Drift tests only |
| make test-legacy | Legacy quarantine only |

### When Writing New Tests

1. **Choose the right directory** based on the table above
2. **Add the correct marker** as `pytestmark = pytest.mark.<marker>` at the top of the file
3. **Add **`REPLACES:`** comments** if your test replaces legacy coverage:`# REPLACES: tests/unit/test_backend.py::TestCreateCompositeBackend`
4. **Add **`COVERS:`** declarations** mapping to catalog component IDs:`# COVERS: backend.composite_routing, backend.filesystem_virtual`
5. **Never add tests to **`tests/unit/` — the legacy ratchet (ceiling=410) will fail CI

### Legacy Test Ratchet

The legacy suite is frozen at a ceiling of 410 tests. This number must only decrease as legacy tests are replaced by new canonical tests. The drift test `test_legacy_ratchet.py` enforces this. If you replace a legacy test, delete the legacy version and update the `REPLACES:` comment in the new test.

## Test Catalog Maintenance

Three YAML catalogs in `docs/testing/` track the components that need test coverage. **You must update these catalogs when changing the application.**

### Catalogs

| File | What It Tracks | When to Update |
| --- | --- | --- |
| docs/testing/runtime_components.yaml | Tools, middleware, subagents, state fields, guardrails (82 components) | Adding/removing/renaming a tool, middleware, subagent, state field, or guardrail |
| docs/testing/sdk_touchpoints.yaml | SDK symbols imported and how they're used (17 touchpoints) | Adding a new SDK import or changing usage pattern |
| docs/testing/intentional_stubs.yaml | Phase-deferred stubs with justification (14 stubs) | Adding a new stub, retiring a stub, or a stub becoming real |

### After Any Catalog Change

Regenerate the traceability matrix:

```bash
python scripts/testing/generate_traceability.py
```

This updates `docs/testing/TEST_TRACEABILITY.md` and `docs/testing/TEST_TRACEABILITY.json`.

### Drift Enforcement

Drift tests automatically catch catalog staleness:

- **Catalog parity** — fails if `runtime_components.yaml` doesn't match what's in `meta_agent/`
- **SDK touchpoints** — fails if new SDK imports aren't cataloged
- **Stub allowlist** — fails if new stubs (both `NotImplementedError` and soft stubs like `return {"status": "pending"}`) aren't in the allowlist
- **Collection hygiene** — fails if test files are missing markers or `REPLACES:` comments

If a drift test fails after your change, update the relevant catalog and regenerate traceability.

### Inventory Scripts

| Script | Purpose |
| --- | --- |
| scripts/testing/extract_runtime_inventory.py | Scans meta_agent/ for runtime components via AST |
| scripts/testing/extract_sdk_touchpoints.py | Scans imports for SDK symbol usage |
| scripts/testing/generate_traceability.py | Builds the coverage traceability matrix from catalogs + COVERS declarations |

## LangSmith Datasets (Pre-loaded)

- `meta-agent-phase-0-scaffolding` (15 examples, ID: `835a9b10-371f-413c-99f9-bdc19e2c4c25`)
- `meta-agent-phase-1-orchestrator` (18 examples, ID: `70f34716-7d60-4042-a565-c086b063809d`)
- `meta-agent-phase-2-intake-prd` (11 scenarios, ID: `b7c0535f-c17f-48bd-8663-e2dda2bd8f07`)

## Research Eval Calibration

- Seed artifacts live under `.agents/pm/projects/meta-agent/` and are expanded into a 5-scenario calibration dataset by `meta_agent.evals.research.synthetic_trace_adapter`.
- Build the raw LangSmith-ready dataset with `python -m meta_agent.evals.research.dataset_builder --datasets-dir datasets --output /tmp/research-agent-eval-calibration.json`.
- Run the synthetic calibration experiment with `python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets`.
- The default LangSmith experiment path materializes a timestamped dataset from the local canonical examples. Pass `--dataset-name <existing-dataset>` to reuse an already-uploaded LangSmith dataset instead.
- The registry contains 38 defined evals, reported as 37 active + 1 deferred unless `--include-deferred` is used.
- The frozen calibration baseline validates evaluator behavior only. It does not measure live runtime performance because end-to-end experiments against the implemented research-agent runtime are still pending.

## Experiment Reporting (New)

The research eval package now supports dual-channel reporting:

- **Local Markdown Reports:** Detailed human-readable reports with failure analysis, judge reasoning, evidence summaries, confidence, flags, and experiment metadata. Generated automatically with `--report-dir` flag.
- **LangSmith UI:** Full traceability, filtering, and deep-dive analysis capabilities.

### Report Generation Commands

```bash
# Runner with markdown reports
python -m meta_agent.evals.research.runner --mode trace --report-dir reports

# LangSmith experiment with markdown reports
python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets --report-dir reports

# LangSmith experiment reusing an existing dataset
python -m meta_agent.evals.research.langsmith_experiment --datasets-dir datasets --dataset-name research-agent-eval-calibration --report-dir reports
```

Reports are persisted under `.agents/pm/projects/meta-agent/evals/reports/` and include:

- Executive summary with pass/fail counts
- Registry coverage totals (`defined`, `active`, `deferred`)
- Detailed failure blocks with judge reasoning, evidence, confidence, and flags
- Passing evaluations summary table
- Experiment metadata and configuration, including scenario labeling for multi-scenario LangSmith calibration runs
