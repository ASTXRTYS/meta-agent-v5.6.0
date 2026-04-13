---
name: langsmith-evaluator-feedback
description: "INVOKE THIS SKILL when converting evaluation-harness outputs into optimizer-safe feedback for a LangChain, LangGraph, or Deep Agents harness search loop that logs traces to LangSmith. Use it whenever a separate evaluator must give a proposer or hill-climbing agent enough signal to improve without leaking rubric logic, hidden-set details, or speculative trace diagnosis. Covers EBDR-1 (Evidence-Bounded Delta Routing), baseline-relative metric vectors, slice deltas, LangSmith trace routing, uncertainty, and anti-overfitting safeguards."
---
<oneliner>Turn evaluation results into an EBDR-1 feedback packet: what moved, what is blocked, where it moved, how trustworthy the signal is, and which LangSmith traces the optimizer should inspect next.</oneliner>

<scope>Use this skill for the evaluator-to-optimizer boundary.

The evaluator does not inspect raw traces. The optimizer does.

This skill complements:

- `langsmith-trace` when the optimizer needs to inspect the routed traces
- `langsmith-evaluator-architect` when you need judge prompts or UI evaluator design
- `langsmith-evaluator` when you need evaluator implementation or evaluation execution</scope>

<standard>

## EBDR-1: Evidence-Bounded Delta Routing

Treat evaluator feedback as a control surface, not as diagnosis.

Send only five signal families:

1. **Delta** — baseline-relative movement on objectives
2. **Boundary** — what blocks promotion and what remains soft
3. **Localization** — which revealed slices moved
4. **Routing** — which LangSmith traces the optimizer should inspect
5. **Uncertainty** — support, confidence, variance, and overfit risk

Do **not** send:

- evaluator prompt text, rubric text, hidden weights, or judge chain-of-thought
- hidden task identifiers, gold answers, or per-example holdout details
- root-cause claims based on traces you did not inspect
- direct code-fix recommendations
- long narrative summaries of failures

Why this works: the evaluator preserves directional signal while forcing the optimizer to do its own causal reasoning over traces.</standard>

<required_inputs>

## Required Inputs

Before generating feedback, gather these if they exist:

- `candidate_id`
- `baseline_id`
- `baseline_mode`: `previous_attempt` | `current_best` | `fixed_control` | `rolling_best`
- `evaluation_run_id`
- objective-level results with value, direction, and any pass/fail gate
- slice-level aggregates for any revealed categories
- failure-mode codes or labels emitted by the evaluator or harness
- LangSmith trace locators for revealed examples: run IDs, trace URLs, or both
- support / confidence / disagreement data if available

If baseline information is missing, say so in `needs_review` and fall back to the best declared comparison available.

If trace locators are missing, still emit the packet, but add `missing_trace_locator` to `needs_review` and leave `inspection_sets` empty.

If failure codes are missing, do not invent them. Leave `failure_modes` empty.</required_inputs>

<workflow>

## Workflow

1. **Normalize the raw evaluation output.** Convert the harness output into comparable objective entries. Preserve `value_type`, units, scale, statistic, and target metadata when available. Treat scores as typed signals, not as a presumed scalar.
2. **Declare the comparison basis.** Always name the baseline and baseline mode.
3. **Compute deltas.** For each objective, compute baseline-relative movement when possible.
4. **Tag objective roles.** Every objective must be one of:

- `hard` — promotion-blocking
- `soft` — optimization target
- `diagnostic` — useful for inspection, not for promotion

1. **Decide candidate status.** Emit `promote`, `revise`, `reject`, or `review`.
2. **Localize the movement.** Report which revealed slices improved, regressed, or mixed.
3. **Route the optimizer.** Build a small set of trace inspection sets using only run metadata and evaluation outputs.
4. **Set safeguards.** Report overfit, leakage, variance, and tamper risk.
5. **Filter the message.** Remove any rubric leakage, hidden-set detail, speculative diagnosis, or fix instructions.
6. **Emit one packet.** Output exactly one JSON object following the contract below.</workflow>

<decision_rules>

## Decision Rules

Use these meanings consistently:

- `promote` — candidate should become the new working baseline
- `revise` — candidate contains useful signal but should not replace the baseline yet
- `reject` — candidate failed a hard gate, tamper check, or clearly regressed
- `review` — signal quality is too weak, too suspicious, or too incomplete for autonomous iteration

Set `pareto_status` to:

- `dominates`
- `dominated`
- `non_dominated`
- `not_applicable`
- `unknown`

For `non_dominated` candidates, prefer:

- `promote` only when no hard objective regressed and at least one non-diagnostic objective improved without high safeguard risk
- `revise` when the candidate is frontier-worthy but still too concentrated, noisy, or costly to replace the baseline

Use short, templated prose only:

- `headline` should say what moved and what blocked or qualified the result
- `focus` should say what the optimizer should inspect next

Good `focus`: `Inspect timeout-heavy retrieval failures in the retrieval slice before broader edits.`

Bad `focus`: `Rewrite the retry policy and change the planner prompt to avoid hallucinating tool calls.`</decision_rules>

<granularity>

## Granularity And Leakage Control

Set `granularity_mode` to one of:

- `fine` — exact deltas are safe for revealed slices with solid support
- `normal` — exact top-level objective deltas, bucketed hidden or aggregate-only slices
- `coarse` — bucket almost everything except hard-gate pass/fail

Use coarser reporting when:

- overfit or leakage risk is elevated
- support is low
- the only available signal comes from hidden or aggregate-only slices
- hidden slices are moving more than revealed slices

Use `delta_bucket` values:

- `large_regression`
- `small_regression`
- `flat`
- `small_improvement`
- `large_improvement`
- `unknown`

For `aggregate_only` slices, prefer bucketed trends over exact per-example detail.If slice support falls below the evaluation system's safe minimum, merge, bucket, or suppress exact values and add `low_support` to `needs_review` or `flag_codes`.In `coarse` mode, `current_value`, `baseline_value`, and `delta` may be `null` when exact reporting is not safe.Never attach hidden-slice traces to the packet.</granularity>

<routing_policy>

## Trace Routing Policy

The core rule is **route, do not diagnose**.

Build at most **5 inspection sets** and at most **8 total trace references**.Prefer diverse, high-signal sets over many redundant failures.

Use these inspection set kinds:

- `blocker_single` — a trace tied to a failed hard objective
- `largest_regression` — the strongest revealed regression
- `contrastive_pair` — one failure and one success from the same revealed slice or objective family
- `representative_success` — a trace from the best-improved revealed slice
- `variance_case` — a trace from a noisy or disagreement-heavy region

Selection order:

1. Include `blocker_single` if any hard objective failed.
2. Include `largest_regression` if any revealed regression exists.
3. Include `contrastive_pair` when a matched success/failure pair exists in the same revealed slice or objective family.
4. Include `representative_success` when the candidate has any meaningful gain.
5. Include `variance_case` when disagreement, variance, or instability is materially elevated.

Pairing rules for `contrastive_pair`:

- Match on revealed slice first
- Match on objective family second
- Match on environment or model metadata if available
- Never fabricate a match just to satisfy the format

The routing layer should help the optimizer perform its own counterfactual reasoning without handing it evaluator internals.</routing_policy>

<output_contract>

## Output Contract

Always return **one JSON object** with these exact top-level keys:

- `feedback_standard`
- `schema_version`
- `candidate_id`
- `baseline_id`
- `baseline_mode`
- `evaluation_run_id`
- `decision`
- `objectives`
- `slice_deltas`
- `failure_modes`
- `inspection_sets`
- `safeguards`
- `needs_review`
- `provenance`

Use this exact shape:

```json
{
  "feedback_standard": "EBDR-1",
  "schema_version": "optimizer_feedback_packet.v1",
  "candidate_id": "cand_123",
  "baseline_id": "cand_122",
  "baseline_mode": "current_best",
  "evaluation_run_id": "eval_456",
  "decision": {
    "status": "revise",
    "pareto_status": "non_dominated",
    "headline": "Solve rate improved, but latency regressed and gains are concentrated in one revealed slice.",
    "focus": "Inspect the routed retrieval traces before broader edits.",
    "blocking_objective_ids": [],
    "reason_codes": ["mixed_tradeoff", "single_slice_gain"],
    "confidence": 0.82,
    "revision_scope": "targeted"
  },
  "objectives": [
    {
      "objective_id": "solve_rate",
      "label": "Solve rate",
      "value_type": "number",
      "role": "hard",
      "direction": "maximize",
      "unit": "ratio",
      "scale": "0_to_1",
      "statistic": "mean",
      "current_value": 0.71,
      "baseline_value": 0.66,
      "delta": 0.05,
      "delta_bucket": "small_improvement",
      "threshold": 0.7,
      "target_value": null,
      "tolerance": null,
      "passed": true,
      "support": 120,
      "confidence": 0.91,
      "variance": null,
      "disagreement": null
    }
  ],
  "slice_deltas": [
    {
      "slice_id": "retrieval",
      "label": "retrieval",
      "visibility": "revealed",
      "support": 36,
      "trend": "mixed",
      "objective_deltas": [
        {
          "objective_id": "solve_rate",
          "delta": 0.11,
          "delta_bucket": "large_improvement"
        }
      ]
    }
  ],
  "failure_modes": [
    {
      "failure_mode_id": "timeout",
      "label": "timeout",
      "severity": "major",
      "count": 5,
      "baseline_count": 2,
      "delta_count": 3,
      "objective_ids": ["solve_rate", "latency_p95_ms"],
      "slice_ids": ["retrieval"]
    }
  ],
  "inspection_sets": [
    {
      "inspection_set_id": "inspect_1",
      "kind": "contrastive_pair",
      "priority": 1,
      "focus": "Compare a retrieval failure against a nearby retrieval success in the same slice.",
      "objective_ids": ["solve_rate"],
      "slice_ids": ["retrieval"],
      "trace_refs": [
        {
          "run_id": "run_fail_1",
          "trace_url": "https://smith.langchain.com/o/.../r/run_fail_1",
          "role": "failure",
          "trace_origin": "candidate"
        },
        {
          "run_id": "run_success_1",
          "trace_url": "https://smith.langchain.com/o/.../r/run_success_1",
          "role": "success",
          "trace_origin": "candidate"
        }
      ]
    }
  ],
  "safeguards": {
    "granularity_mode": "normal",
    "overfit_risk": "medium",
    "noise_risk": "low",
    "leakage_risk": "medium",
    "iteration_exposure_risk": "low",
    "tamper_suspected": false,
    "flag_codes": ["single_slice_gain"]
  },
  "needs_review": [],
  "provenance": {
    "created_at": "2026-04-06T19:15:00Z",
    "evaluator_trace_access": false,
    "signal_sources": ["metric_vector", "slice_aggregates", "failure_tags", "trace_locators"],
    "project_name": "your-langsmith-project",
    "dataset_version": "dataset_v3",
    "evaluator_version": "evaluator_v7",
    "judge_version": "judge_v4",
    "feedback_generator_version": "langsmith-evaluator-feedback@1"
  }
}
```

</output_contract>

<field_rules>

## Field Rules

### `decision`

- `status`: `promote` | `revise` | `reject` | `review`
- `pareto_status`: `dominates` | `dominated` | `non_dominated` | `not_applicable` | `unknown`
- `reason_codes`: stable, machine-readable codes only
- `revision_scope`: `local` | `targeted` | `broad` | `unknown`

Suggested `reason_codes`:

- `hard_gate_failed`
- `net_gain`
- `mixed_tradeoff`
- `single_slice_gain`
- `single_metric_gain`
- `holdout_trend_down`
- `low_support`
- `high_variance`
- `missing_trace_locator`
- `missing_baseline`
- `tamper_signal`
- `distribution_shift_signal`

### `objectives`

- `value_type`: `number` | `integer` | `boolean` | `string`
- `role`: `hard` | `soft` | `diagnostic`
- `direction`: `maximize` | `minimize` | `target`
- `unit`, `scale`, and `statistic` should be included whenever known
- `delta` is the raw arithmetic difference `current_value - baseline_value` for numeric objectives; interpret desirability through `direction`
- for non-numeric objectives or coarse reporting, set `delta` to `null` and rely on `delta_bucket`
- for `direction: target`, include `target_value` and, if available, `tolerance`
- `passed` may be `null` for purely soft objectives with no threshold
- include `variance` or `disagreement` when the evaluation system exposes them

### `slice_deltas`

- `visibility`: `revealed` | `aggregate_only`
- `trend`: `improved` | `regressed` | `mixed` | `flat` | `inconclusive`
- Use exact deltas only when allowed by `granularity_mode`

### `failure_modes`

- Use only codes actually emitted by the evaluator or harness
- If emitted codes are private to the rubric, map them to an approved public taxonomy or omit them
- `severity`: `critical` | `major` | `minor` | `info`
- include `baseline_count` and `delta_count` whenever a baseline comparison exists

### `inspection_sets`

- `kind`: `blocker_single` | `largest_regression` | `contrastive_pair` | `representative_success` | `variance_case`
- `trace_refs.role`: `failure` | `success` | `reference`
- `trace_refs.trace_origin`: `candidate` | `baseline` | `reference`
- Keep `focus` short and routing-oriented
- avoid repeated exposure of the same trace when a diverse routing set is available

### `safeguards`

- risk fields: `low` | `medium` | `high` | `unknown`
- `flag_codes` should be machine-readable

### `needs_review`

Use this list when:

- signal is incomplete
- the baseline is missing or underspecified
- hidden-slice movement materially exceeds revealed movement
- support is too weak for safe automation
- tamper is suspected
- trace locators are missing
- iteration history suggests repeated exposure of the same benchmark region</field_rules>

<forbidden_content>

## Forbidden Content Filter

Before returning the packet, remove:

- rubric text
- judge instructions
- chain-of-thought or hidden reasoning
- hidden test names or per-example holdout outcomes
- gold answers or solution fragments
- private evaluator labels that have not been mapped to a public taxonomy
- speculative phrases like `the root cause is` unless the evaluator directly observed that cause from authorized data
- code-level prescriptions such as `change the system prompt` or `rewrite the planner`

The evaluator is allowed to say **what moved** and **what to inspect next**.The evaluator is not allowed to say **why the trace failed internally**.</forbidden_content>

<translation_patterns>

## Translation Patterns

### Binary benchmarks

Use one or more hard objectives such as pass rate, plus optional soft objectives such as latency or cost.

### Likert or rubric-graded benchmarks

Map the judged quality objective to `soft` unless it is release-blocking. Keep policy or safety objectives as `hard`.

### Vector or Pareto benchmarks

Preserve the vector. Do not collapse it into a scalar. Set `pareto_status` accordingly.

### Hidden or holdout slices

Expose only allowed aggregate trends. Do not expose hidden traces.</translation_patterns>

<quality_bar>

## Quality Bar

A strong packet is:

- baseline-relative
- mostly structured
- sparse in prose
- explicit about uncertainty
- explicit about which slices moved
- explicit about what blocks promotion
- explicit about which traces the optimizer should inspect
- conservative when leakage or overfit risk is high

A weak packet:

- retells failures in prose
- gives a single scalar with no decomposition
- hides uncertainty
- includes no trace routing
- leaks rubric details
- makes causal claims without trace access</quality_bar>

<example_interaction_pattern>

## Example Interaction Pattern

If the user gives you raw evaluation output for a LangGraph coding harness and asks for feedback to send to the optimizer:

1. Normalize the metrics and slices
2. Compute deltas against the declared baseline
3. Decide `promote`, `revise`, `reject`, or `review`
4. Build 1-5 inspection sets using LangSmith run IDs or URLs
5. Return the JSON packet only, unless the user explicitly asks for commentary

If the user asks for a human-readable explanation too, give the JSON packet first, then a short summary that mirrors it without adding new information.</example_interaction_pattern>s for a human-readable explanation too, give the JSON packet first, then a short summary that mirrors it without adding new information.</example_interaction_pattern>rn>

If the user asks for a human-readable explanation too, give the JSON packet first, then a short summary that mirrors it without adding new information.</example_interaction_pattern>s for a human-readable explanation too, give the JSON packet first, then a short summary that mirrors it without adding new information.</example_interaction_pattern>rn>n.</example_interaction_pattern>rn>adable explanation too, give the JSON packet first, then a short summary that mirrors it without adding new information.</example_interaction_pattern>rn>n.</example_interaction_pattern>rn>