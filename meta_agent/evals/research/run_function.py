"""Run function bridge for langsmith.evaluate().

Invokes the real research-agent graph, collects outputs, and returns
them in the shape that RESEARCH_EVAL_REGISTRY evaluators expect.
"""

from __future__ import annotations

from typing import Any

from langsmith import traceable

from meta_agent.subagents.research_agent import run_research_agent_live


# ---------------------------------------------------------------------------
# Checkpoint eval map (Section 3.2.8 of the development plan)
# Each checkpoint is a superset of the previous one.
# ---------------------------------------------------------------------------

_CHECKPOINT_1_IDS: list[str] = [
    "RS-001", "RS-002", "RS-003", "RS-004",
    "RINFRA-001", "RINFRA-002",
    "RB-001", "RB-002", "RB-003",
]

_CHECKPOINT_2_IDS: list[str] = _CHECKPOINT_1_IDS + [
    "RB-004", "RB-007", "RB-008", "RB-009", "RB-010",
    "RQ-007", "RQ-008", "RQ-009", "RQ-010",
]

_CHECKPOINT_3_IDS: list[str] = _CHECKPOINT_2_IDS + [
    "RB-005", "RB-006", "RB-011",
    "RQ-006", "RQ-012", "RQ-013",
    "RR-001", "RR-002", "RR-003",
]

# checkpoint_4 is all active (non-deferred) evals -- resolved lazily so the
# registry can be imported without circular issues at module level.
_CHECKPOINT_4_IDS: list[str] | None = None


def _all_active_eval_ids() -> list[str]:
    """Return every non-deferred eval ID from the registry."""
    global _CHECKPOINT_4_IDS
    if _CHECKPOINT_4_IDS is None:
        from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY

        _CHECKPOINT_4_IDS = [
            eval_id
            for eval_id, meta in RESEARCH_EVAL_REGISTRY.items()
            if meta["type"] != "deferred"
        ]
    return _CHECKPOINT_4_IDS


CHECKPOINT_EVAL_MAP: dict[str, list[str] | None] = {
    "checkpoint_1": _CHECKPOINT_1_IDS,
    "checkpoint_2": _CHECKPOINT_2_IDS,
    "checkpoint_3": _CHECKPOINT_3_IDS,
    "checkpoint_4": None,  # resolved to all active evals at call time
}


# ---------------------------------------------------------------------------
# Run function -- the bridge between langsmith.evaluate() and the runtime
# ---------------------------------------------------------------------------

@traceable(name="research-agent-eval-run")
def run_research_agent(inputs: dict) -> dict:
    """Run function for langsmith.evaluate().

    Takes dataset inputs, invokes the real research-agent runtime,
    returns outputs in the shape evaluators expect.
    """
    return run_research_agent_live(inputs)


# ---------------------------------------------------------------------------
# Checkpoint runner -- invoke a subset of evals via langsmith.evaluate()
# ---------------------------------------------------------------------------

def run_checkpoint(
    checkpoint_eval_ids: list[str],
    dataset_name: str = "research-agent-eval-calibration",
    experiment_prefix: str = "phase3",
) -> Any:
    """Run a subset of evals against the real agent via langsmith.evaluate().

    Parameters
    ----------
    checkpoint_eval_ids:
        List of eval IDs to run, e.g. ``CHECKPOINT_EVAL_MAP["checkpoint_1"]``.
    dataset_name:
        Name of the LangSmith dataset to evaluate against.
    experiment_prefix:
        Prefix for the experiment name shown in LangSmith UI.

    Returns
    -------
    The ``ExperimentResults`` object returned by ``langsmith.evaluate()``.
    """
    from langsmith import evaluate

    from meta_agent.evals.research.evaluators import RESEARCH_EVAL_REGISTRY
    from meta_agent.evals.research.langsmith_experiment import _make_langsmith_evaluator

    evaluators = [
        _make_langsmith_evaluator(eval_id, RESEARCH_EVAL_REGISTRY[eval_id]["fn"])
        for eval_id in checkpoint_eval_ids
        if eval_id in RESEARCH_EVAL_REGISTRY
    ]

    results = evaluate(
        run_research_agent,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_prefix,
    )
    return results


def run_named_checkpoint(
    checkpoint_name: str,
    dataset_name: str = "research-agent-eval-calibration",
    experiment_prefix: str | None = None,
) -> Any:
    """Convenience wrapper: run a named checkpoint from CHECKPOINT_EVAL_MAP.

    Parameters
    ----------
    checkpoint_name:
        One of ``"checkpoint_1"`` .. ``"checkpoint_4"``.
    dataset_name:
        Name of the LangSmith dataset to evaluate against.
    experiment_prefix:
        Prefix for the experiment name; defaults to the checkpoint name.
    """
    eval_ids = CHECKPOINT_EVAL_MAP.get(checkpoint_name)
    if eval_ids is None:
        eval_ids = _all_active_eval_ids()
    return run_checkpoint(
        eval_ids,
        dataset_name=dataset_name,
        experiment_prefix=experiment_prefix or checkpoint_name,
    )
