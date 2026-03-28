"""MetaAgentStateMiddleware — extends graph state with custom fields.

Uses the SDK's state_schema merging pattern (same as TodoListMiddleware)
to add current_stage, decision_log, assumption_log, approval_history,
and other meta-agent fields directly into the graph state.

Tools return Command(update={...}) to update these fields.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional

from typing_extensions import NotRequired

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import AgentState

from meta_agent.state import (
    ApprovalEntry,
    AssumptionEntry,
    DecisionEntry,
    WorkflowStage,
)


class MetaAgentStateSchema(AgentState):
    """Extends AgentState with meta-agent custom fields.

    All list fields use Annotated[list, operator.add] for append-mode
    accumulation — Command(update={"decision_log": [entry]}) appends
    rather than replaces.
    """

    # Core workflow state
    current_stage: NotRequired[str]
    project_id: NotRequired[str]
    current_prd_path: NotRequired[Optional[str]]
    current_spec_path: NotRequired[Optional[str]]
    current_plan_path: NotRequired[Optional[str]]
    current_research_path: NotRequired[Optional[str]]
    active_participation_mode: NotRequired[bool]

    # Append-only structured logs
    decision_log: Annotated[list, operator.add]
    assumption_log: Annotated[list, operator.add]
    approval_history: Annotated[list, operator.add]
    artifacts_written: Annotated[list[str], operator.add]

    # Execution tracking
    execution_plan_tasks: NotRequired[list[dict]]
    current_task_id: NotRequired[Optional[str]]
    completed_task_ids: Annotated[list[str], operator.add]
    execution_summary: NotRequired[dict]
    test_summary: NotRequired[dict]
    progress_log: Annotated[list[str], operator.add]

    # Eval-related state
    eval_suites: NotRequired[list[str]]
    eval_results: NotRequired[dict]
    current_eval_phase: NotRequired[Optional[str]]


class MetaAgentStateMiddleware(AgentMiddleware):
    """Middleware that merges MetaAgentStateSchema into the graph state.

    The SDK's factory reads ``state_schema`` from each middleware and
    merges all fields via ``_resolve_schema``.  This is the same
    pattern used by ``TodoListMiddleware``.
    """

    state_schema = MetaAgentStateSchema  # type: ignore[assignment]

    def before_agent(self, state: Any, runtime: Any) -> dict[str, Any] | None:
        """Initialize default values on first run.

        Only sets defaults for fields that are missing — never overwrites
        values already present from a resumed checkpoint.
        """
        state_dict = dict(state) if hasattr(state, "items") else {}
        updates: dict[str, Any] = {}

        if not state_dict.get("current_stage"):
            updates["current_stage"] = WorkflowStage.INTAKE.value
        if not state_dict.get("project_id"):
            updates["project_id"] = ""
        if "active_participation_mode" not in state_dict:
            updates["active_participation_mode"] = False

        return updates if updates else None
