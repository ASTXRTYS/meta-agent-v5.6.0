# Research Agent Experiment Report

- **Experiment:** research-calibration-phase-all-golden_path
- **Timestamp:** 2026-03-30T18:12:30Z
- **Scenario:** golden_path
- **Mode:** calibration
- **defined_eval_count:** 38
- **active_eval_count:** 37
- **deferred_eval_count:** 1
- **phase_number:** 3
- **phase_name:** RESEARCH
- **phases:** all
- **data_dir:** datasets
- **dataset_source:** local_synthetic_trace_adapter

## Summary

- **Binary:** 20/20 passed
- **Likert:** mean 4.4, min 4, max 5, below threshold: 0
- **Overall:** PASSED
- **Registry coverage:** 38 defined, 37 active, 1 deferred
- **Reported evals:** 38 (0 failed, 0 below threshold, 37 passed, 1 deferred)
## Passing Evals

| Eval ID | Score | Confidence | Key finding |
|---------|-------|------------|-------------|
| RB-001 | 1 | HIGH | RB-001: PRD fully read (trace flag) |
| RB-002 | 1 | HIGH | RB-002: eval suite read before research started |
| RB-003 | 1 | HIGH | RB-003: decomposition persisted (trace flag) |
| RB-004 | 1 | HIGH | RB-004: 76 web tool calls |
| RB-005 | 1 | HIGH | RB-005: citations were fetched and structured claim checks found no unsupported ... |
| RB-006 | 1 | HIGH | RB-006: 19 Anthropic research calls |
| RB-007 | 1 | HIGH | RB-007: 31 skills read (trace flag) |
| RB-008 | 1 | HIGH | RB-008: 5 task calls (trace flag) |
| RB-009 | 1 | HIGH | RB-009: trace explicitly marks sub-agents parallel |
| RB-010 | 1 | HIGH | RB-010: sub-findings were read after sub-agents completed |
| RB-011 | 1 | HIGH | RB-011: HITL approval occurred before deep-dive research |
| RI-002 | 1 | HIGH | RI-002: all PRD functional areas are evidenced across bundle, trace, decompositi... |
| RI-003 | 1 | HIGH | RI-003: eval implementation considerations are explicitly covered |
| RINFRA-001 | 1 | HIGH | RINFRA-001: path=True, content=True, writes=True |
| RINFRA-002 | 1 | HIGH | RINFRA-002: all fields present |
| RINFRA-003 | 5 | HIGH | RINFRA-003: This research bundle demonstrates exceptional completeness and quali... |
| RINFRA-004 | 4 | HIGH | RINFRA-004: The research bundle demonstrates strong citation quality with specif... |
| RQ-001 | 5 | HIGH | RQ-001: This decomposition file systematically maps EVERY PRD requirement to spe... |
| RQ-002 | 4 | HIGH | RQ-002: The agent systematically explored all major ecosystem options across eve... |
| RQ-003 | 4 | HIGH | RQ-003: The agent demonstrated deep research by examining API references, source... |
| RQ-004 | 4 | HIGH | RQ-004: Citations are accurate with specific URLs and proper source attribution.... |
| RQ-005 | 4 | HIGH | RQ-005: This bundle provides clear ecosystem options with trade-offs, model capa... |
| RQ-006 | 4 | HIGH | RQ-006: The agent systematically consulted all 6 specified SME handles (@hwchase... |
| RQ-007 | 5 | HIGH | RQ-007: The agent demonstrates exceptional skill trigger relevance and timing, s... |
| RQ-008 | 5 | HIGH | RQ-008: The agent demonstrates exhaustive skill reading with comprehensive refle... |
| RQ-009 | 5 | HIGH | RQ-009: Skills are a primary driver of research strategy throughout the agent's ... |
| RQ-010 | 5 | HIGH | RQ-010: The agent demonstrates sophisticated metacognitive reasoning about deleg... |
| RQ-011 | 4 | HIGH | RQ-011: The research bundle demonstrates strong synthesis by reorganizing findin... |
| RQ-012 | 5 | HIGH | RQ-012: This HITL presentation demonstrates expertly curated research clusters t... |
| RQ-013 | 4 | HIGH | RQ-013: The agent systematically identifies 3 contradictions and 3 gaps with exp... |
| RR-001 | 4 | HIGH | RR-001: The agent demonstrates meaningful reflection at each major decision poin... |
| RR-002 | 4 | HIGH | RR-002: The agent systematically builds relationships across source types, cross... |
| RR-003 | 4 | HIGH | RR-003: The agent demonstrates active monitoring and prompt course corrections t... |
| RS-001 | 1 | HIGH | RS-001: prd in state=True |
| RS-002 | 1 | HIGH | RS-002: eval suite in state=True |
| RS-003 | 1 | HIGH | RS-003: all config fields present |
| RS-004 | 1 | HIGH | RS-004: explicit output state present |

## Deferred Evals

- **RI-001:** RI-001: DEFERRED — awaiting spec-writer agent

## Judge Backend

- **Provider:** anthropic
- **Model:** claude-sonnet-4-20250514
