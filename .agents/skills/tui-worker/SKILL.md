---
name: tui-worker
description: Implements Textual TUI for Meta Harness — widgets, themes, layout, pipeline awareness, adopted from Deep Agents CLI.
---

# TUI Worker

NOTE: Startup and cleanup are handled by `worker-base`. This skill defines the WORK PROCEDURE.

## When to Use This Skill

Any feature involving the Textual TUI: MetaHarnessApp, pipeline awareness widgets, theme system, CLI widget adoption, CSS layout, and tuistory snapshot tests.

## Required Skills

- `tuistory` — for TUI snapshot testing. Invoke when verifying widget rendering.

## Work Procedure

1. **Read context.** Read the feature description and `.factory/library/architecture.md`. For CLI adoption decisions, investigate the Deep Agents CLI source at `.reference/libs/cli/deepagents_cli/` — specifically `app.py`, `widgets/`, `theme.py`, `app.tcss`.

2. **Investigate CLI widgets.** Before implementing any widget, read the corresponding CLI widget source to understand the pattern. Do not blindly copy — adapt for Meta Harness's multi-agent pipeline needs. Key files:
   - `widgets/ask_user.py` — AskUserMenu
   - `widgets/approval.py` — ApprovalMenu
   - `widgets/chat_input.py` — ChatInput
   - `widgets/messages.py` — message rendering
   - `widgets/status.py` — StatusBar
   - `widgets/welcome.py` — WelcomeBanner
   - `theme.py` — ThemeColors, ThemeEntry, registry

3. **Write tests first (RED).** Create tuistory snapshot test or unit test in `meta_harness/tests/tui/`. For widget logic tests, use pytest directly. For rendering tests, use tuistory to capture terminal snapshots. Run tests — confirm FAIL.

4. **Implement (GREEN).** Write Textual widget code in `meta_harness/tui/`. Follow patterns:
   - CSS in external `.tcss` files
   - Reactive attributes for state
   - Message passing for widget communication
   - Workers (`@work`) for async operations
   Run tests — confirm PASS.

5. **Verify rendering.** Use tuistory to capture a snapshot of the widget/app and visually verify it renders correctly. Each flow tested = one `interactiveChecks` entry.

6. **Commit** with a clear message.

## Example Handoff

```json
{
  "salientSummary": "Implemented MetaHarnessApp with pipeline-aware compose layout: active agent indicator, phase progress bar, chat area with message rendering, and status bar. Forked theme.py from CLI with Meta Harness brand palette. tuistory snapshot confirms correct layout.",
  "whatWasImplemented": "meta_harness/tui/app.py (MetaHarnessApp), meta_harness/tui/theme.py (MetaHarnessTheme), meta_harness/tui/app.tcss, meta_harness/tui/widgets/agent_indicator.py, meta_harness/tui/widgets/phase_progress.py",
  "whatWasLeftUndone": "",
  "verification": {
    "commandsRun": [
      {"command": "cd meta_harness && .venv/bin/python -m pytest tests/tui/ -v", "exitCode": 0, "observation": "6 passed"}
    ],
    "interactiveChecks": [
      {"action": "tuistory snapshot of MetaHarnessApp compose", "observed": "Active agent shows 'PM', phase progress shows 6 phases with 'scoping' highlighted, chat area renders, status bar shows model and phase"}
    ]
  },
  "tests": {
    "added": [
      {"file": "tests/tui/test_app_layout.py", "cases": [
        {"name": "test_app_composes_without_error", "verifies": "app launches cleanly"},
        {"name": "test_agent_indicator_shows_name", "verifies": "active agent displayed"}
      ]}
    ]
  },
  "discoveredIssues": []
}
```

## When to Return to Orchestrator

- CLI widget cannot be imported (dependency issue)
- Textual version incompatibility
- tuistory cannot capture the TUI (environment issue)
- Pipeline state not available from backend (missing PCG integration)
