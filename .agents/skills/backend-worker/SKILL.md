---
name: backend-worker
description: Implements Python backend code for Meta Harness — types, graph, tools, middleware, agent factories, system prompts, integration, and tests.
---

# Backend Worker

NOTE: Startup and cleanup are handled by `worker-base`. This skill defines the WORK PROCEDURE.

## When to Use This Skill

Any feature involving Python code: type definitions, PCG graph, handoff tools, middleware, agent factories, system prompts (.md files), sandbox integration, observability, model routing, Anthropic profile, and contract/integration tests.

## Required Skills

None — all work uses standard file editing and shell execution via pytest.

## Work Procedure

1. **Read context.** Read the feature description, `meta_harness/AD.md` §4 for architectural constraints, and `.factory/library/architecture.md` for system overview. For SDK-specific work, consult canonical references per `AGENTS.md`:
   - Deep Agents: `.reference/libs/deepagents/deepagents/`
   - CLI patterns: `.reference/libs/cli/deepagents_cli/`
   - LangGraph: `.venv/lib/python3.11/site-packages/langgraph/`
   - Middleware: `.venv/lib/python3.11/site-packages/langchain/agents/middleware/`
   - Anthropic: `.venv/lib/python3.11/site-packages/langchain_anthropic/middleware/`

2. **Write failing tests first (RED).** Create test file(s) in `meta_harness/tests/contract/` or `meta_harness/tests/integration/`. Tests must cover the feature's `expectedBehavior`. Use mocked LLM responses — no real API calls. Run: `cd meta_harness && .venv/bin/python -m pytest tests/ -v --tb=short -x -k <test_name>` — confirm tests FAIL.

3. **Implement (GREEN).** Write the implementation code. Follow SDK conventions:
   - One factory per agent, system prompts in `.md` files
   - `name=` on every agent, POSIX paths for backends
   - `Command(graph=Command.PARENT, goto="process_handoff", update={...})` for handoff tools
   - Never hand-roll what the SDK provides
   Run tests again — confirm they PASS.

4. **Verify.** Run the full test suite: `cd meta_harness && .venv/bin/python -m pytest tests/ -v --tb=short -x`. Fix any regressions. Check imports are correct by running `cd meta_harness && .venv/bin/python -c "from meta_harness.<module> import <class>"`.

5. **Commit** with a clear message describing what was built and why.

## Example Handoff

```json
{
  "salientSummary": "Implemented HandoffRecord Pydantic model with 11 fields (10 base + accepted), ProjectCoordinationState TypedDict with 6 keys and add_messages reducers, and all enums (AgentRole, Phase, HandoffReason). Wrote 15 contract tests covering serialization roundtrip, field validation, and enum completeness — all passing.",
  "whatWasImplemented": "meta_harness/schemas/handoff.py (HandoffRecord, AgentRole, Phase, HandoffReason enums), meta_harness/schemas/state.py (ProjectCoordinationState, ProjectCoordinationInput, ProjectCoordinationOutput, ProjectCoordinationContext)",
  "whatWasLeftUndone": "",
  "verification": {
    "commandsRun": [
      {"command": "cd meta_harness && .venv/bin/python -m pytest tests/contract/test_handoff_record.py -v", "exitCode": 0, "observation": "15 passed"},
      {"command": "cd meta_harness && .venv/bin/python -c 'from meta_harness.schemas.handoff import HandoffRecord, AgentRole'", "exitCode": 0, "observation": "imports clean"}
    ],
    "interactiveChecks": []
  },
  "tests": {
    "added": [
      {"file": "tests/contract/test_handoff_record.py", "cases": [
        {"name": "test_handoff_record_roundtrip", "verifies": "serialization/deserialization"},
        {"name": "test_handoff_record_validates_fields", "verifies": "required field enforcement"},
        {"name": "test_agent_role_enum_completeness", "verifies": "all 7 agents present"}
      ]}
    ]
  },
  "discoveredIssues": []
}
```

## When to Return to Orchestrator

- Feature depends on a module that doesn't exist yet (missing precondition)
- SDK behavior doesn't match what the AD specifies (architectural conflict)
- Cannot install a required dependency
- Tests reveal a design issue that requires AD-level decisions
