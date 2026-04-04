"""Eval test utilities — trajectory scoring and agent scenario helpers.

Trajectory scoring infrastructure adapted from the Deep Agents SDK reference:
  .reference/libs/evals/tests/evals/utils.py

Provides trajectory construction, two-tier assertion scoring
(success = hard-fail, efficiency = logged only), and a ``run_agent``
entry point that invokes a compiled graph and validates the result.

REPLACES: tests/unit/test_evals.py (partial — run_agent_scenario stub)
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pytest
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.graph.state import CompiledStateGraph

# Optional LangSmith integration — gracefully degrade when unavailable.
try:
    from langsmith import testing as t
    from langsmith.run_helpers import get_current_run_tree

    _HAS_LANGSMITH = True
except ImportError:
    _HAS_LANGSMITH = False

# Optional deepagents backend utils (used for file assertions / initial_files).
try:
    from deepagents.backends.utils import create_file_data, file_data_to_string
except ImportError:

    def create_file_data(content: str) -> dict[str, str]:  # type: ignore[misc]
        return {"content": content}

    def file_data_to_string(data: dict[str, str]) -> str:  # type: ignore[misc]
        if isinstance(data, str):
            return data
        return data.get("content", "")


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core trajectory data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentStep:
    """A single step in an agent trajectory."""

    index: int
    """1-indexed step number."""
    action: AIMessage
    """AI message output (may contain tool calls)."""
    observations: list[ToolMessage]
    """Tool responses received during this step."""

    def __post_init__(self) -> None:
        if self.index <= 0:
            msg = "index must be positive"
            raise ValueError(msg)


@dataclass(frozen=True)
class AgentTrajectory:
    """Complete trajectory produced by an agent invocation."""

    steps: list[AgentStep]
    files: dict[str, str]

    @property
    def answer(self) -> str:
        """Text content of the last agent step."""
        return self.steps[-1].action.text

    def pretty(self) -> str:
        """Human-readable summary for failure diagnostics."""
        lines: list[str] = []
        for step in self.steps:
            lines.append(f"step {step.index}:")
            tool_calls = step.action.tool_calls
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name")
                    args = tc.get("args")
                    lines.append(f"  - {name} {args}")
            text = step.action.text
            if text and text.strip():
                text_preview = text.strip().replace("\n", "\\n")
                lines.append(f"  text: {text_preview}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Assertion base classes
# ---------------------------------------------------------------------------


class SuccessAssertion:
    """Correctness assertion — hard-fails the test when violated."""

    def check(self, trajectory: AgentTrajectory) -> bool:
        raise NotImplementedError

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class EfficiencyAssertion:
    """Efficiency assertion — logged but never fails the test."""

    def check(self, trajectory: AgentTrajectory) -> bool:
        raise NotImplementedError

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_common_zero_width(text: str) -> str:
    """Remove common zero-width Unicode characters."""
    return text.translate(
        {
            ord("\u200b"): None,
            ord("\u200c"): None,
            ord("\u200d"): None,
            ord("\ufeff"): None,
        }
    )


def _coerce_result_files_to_strings(raw_files: object) -> dict[str, str]:
    """Coerce the ``files`` value from an agent result into ``dict[str, str]``."""
    if raw_files is None:
        return {}
    if not isinstance(raw_files, Mapping):
        msg = f"Expected files to be dict, got {type(raw_files)}"
        raise TypeError(msg)

    files: dict[str, str] = {}
    for path, file_data in raw_files.items():
        if not isinstance(path, str):
            msg = f"Expected file path to be str, got {type(path)}"
            raise TypeError(msg)
        if isinstance(file_data, str):
            files[path] = file_data
        elif isinstance(file_data, Mapping) and "content" in file_data:
            files[path] = file_data_to_string(dict(file_data))
        else:
            msg = f"Unexpected file representation for {path}: {type(file_data)}"
            raise TypeError(msg)
    return files


# ---------------------------------------------------------------------------
# Concrete success assertions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FinalTextContains(SuccessAssertion):
    """Final agent text must contain *text*."""

    text: str
    case_insensitive: bool = False

    def check(self, trajectory: AgentTrajectory) -> bool:
        haystack = _strip_common_zero_width(trajectory.answer)
        needle = _strip_common_zero_width(self.text)
        if self.case_insensitive:
            haystack, needle = haystack.lower(), needle.lower()
        return needle in haystack

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        return (
            f"Expected final text to contain {self.text!r} "
            f"(case_insensitive={self.case_insensitive}), "
            f"got: {_strip_common_zero_width(trajectory.answer)!r}"
        )


@dataclass(frozen=True)
class FinalTextExcludes(SuccessAssertion):
    """Final agent text must NOT contain *text*."""

    text: str
    case_insensitive: bool = False

    def check(self, trajectory: AgentTrajectory) -> bool:
        haystack = _strip_common_zero_width(trajectory.answer)
        needle = _strip_common_zero_width(self.text)
        if self.case_insensitive:
            haystack, needle = haystack.lower(), needle.lower()
        return needle not in haystack

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        return (
            f"Expected final text NOT to contain {self.text!r}, "
            f"got: {_strip_common_zero_width(trajectory.answer)!r}"
        )


@dataclass(frozen=True)
class FileEquals(SuccessAssertion):
    """A file in the trajectory must equal *content* exactly."""

    path: str
    content: str

    def check(self, trajectory: AgentTrajectory) -> bool:
        return trajectory.files.get(self.path) == self.content

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        actual = trajectory.files.get(self.path)
        if actual is None:
            return f"File {self.path!r} not found in trajectory files"
        return f"File {self.path!r} content mismatch.\nExpected:\n{self.content!r}\nActual:\n{actual!r}"


@dataclass(frozen=True)
class FileContains(SuccessAssertion):
    """A file in the trajectory must contain *substring*."""

    path: str
    substring: str

    def check(self, trajectory: AgentTrajectory) -> bool:
        content = trajectory.files.get(self.path)
        return content is not None and self.substring in content

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        actual = trajectory.files.get(self.path)
        if actual is None:
            return f"File {self.path!r} not found in trajectory files"
        return f"File {self.path!r} does not contain {self.substring!r}.\nActual:\n{actual!r}"


@dataclass(frozen=True)
class FileExcludes(SuccessAssertion):
    """A file in the trajectory must NOT contain *substring*."""

    path: str
    substring: str

    def check(self, trajectory: AgentTrajectory) -> bool:
        return self.substring not in trajectory.files.get(self.path, "")

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        actual = trajectory.files.get(self.path, "")
        return f"File {self.path!r} unexpectedly contains {self.substring!r}.\nActual:\n{actual!r}"


# ---------------------------------------------------------------------------
# Concrete efficiency assertions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentSteps(EfficiencyAssertion):
    """Trajectory must have exactly *n* agent steps."""

    n: int

    def check(self, trajectory: AgentTrajectory) -> bool:
        return len(trajectory.steps) == self.n

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        return f"Expected {self.n} agent steps, got {len(trajectory.steps)}"


@dataclass(frozen=True)
class ToolCallRequests(EfficiencyAssertion):
    """Trajectory must have exactly *n* total tool call requests."""

    n: int

    def check(self, trajectory: AgentTrajectory) -> bool:
        actual = sum(len(s.action.tool_calls) for s in trajectory.steps)
        return actual == self.n

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        actual = sum(len(s.action.tool_calls) for s in trajectory.steps)
        return f"Expected {self.n} tool call requests, got {actual}"


@dataclass(frozen=True)
class ToolCall(EfficiencyAssertion):
    """A specific tool call must appear in the trajectory."""

    name: str
    step: int | None = None
    args_contains: dict[str, object] | None = None
    args_equals: dict[str, object] | None = None

    def check(self, trajectory: AgentTrajectory) -> bool:
        return bool(self._find_matches(trajectory))

    def describe_failure(self, trajectory: AgentTrajectory) -> str:
        step_desc = f" in step {self.step}" if self.step is not None else ""
        return (
            f"Missing expected tool call{step_desc}: name={self.name!r}, "
            f"args_contains={self.args_contains!r}, args_equals={self.args_equals!r}"
        )

    def _matches_tool_call(self, tc: dict[str, object]) -> bool:
        if tc.get("name") != self.name:
            return False
        if self.args_contains is not None:
            args = tc.get("args")
            if not isinstance(args, dict):
                return False
            if not all(args.get(k) == v for k, v in self.args_contains.items()):
                return False
        return self.args_equals is None or tc.get("args") == self.args_equals

    def _find_matches(self, trajectory: AgentTrajectory) -> list[dict[str, object]]:
        if self.step is not None:
            if self.step > len(trajectory.steps):
                return []
            steps_to_search = [trajectory.steps[self.step - 1]]
        else:
            steps_to_search = trajectory.steps
        return [
            tc
            for s in steps_to_search
            for tc in s.action.tool_calls
            if self._matches_tool_call(tc)
        ]


# ---------------------------------------------------------------------------
# Factory functions (public API)
# ---------------------------------------------------------------------------


def final_text_contains(
    text: str,
    *,
    case_insensitive: bool = False,
) -> FinalTextContains:
    """Create a ``FinalTextContains`` success assertion."""
    return FinalTextContains(text=text, case_insensitive=case_insensitive)


def final_text_excludes(
    text: str,
    *,
    case_insensitive: bool = False,
) -> FinalTextExcludes:
    """Create a ``FinalTextExcludes`` success assertion."""
    return FinalTextExcludes(text=text, case_insensitive=case_insensitive)


def file_equals(path: str, content: str) -> FileEquals:
    """Create a ``FileEquals`` success assertion."""
    return FileEquals(path=path, content=content)


def file_contains(path: str, substring: str) -> FileContains:
    """Create a ``FileContains`` success assertion."""
    return FileContains(path=path, substring=substring)


def file_excludes(path: str, substring: str) -> FileExcludes:
    """Create a ``FileExcludes`` success assertion."""
    return FileExcludes(path=path, substring=substring)


def agent_steps(n: int) -> AgentSteps:
    """Create an ``AgentSteps`` efficiency assertion."""
    return AgentSteps(n=n)


def tool_call_requests(n: int) -> ToolCallRequests:
    """Create a ``ToolCallRequests`` efficiency assertion."""
    return ToolCallRequests(n=n)


def tool_call(
    name: str,
    *,
    step: int | None = None,
    args_contains: dict[str, object] | None = None,
    args_equals: dict[str, object] | None = None,
) -> ToolCall:
    """Create a ``ToolCall`` efficiency assertion."""
    return ToolCall(
        name=name,
        step=step,
        args_contains=args_contains,
        args_equals=args_equals,
    )


# ---------------------------------------------------------------------------
# TrajectoryScorer (two-tier builder)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrajectoryScorer:
    """Two-tier assertion container.

    ``.success()`` appends hard-fail correctness assertions.
    ``.expect()`` appends logged-only efficiency assertions.
    """

    _success: tuple[SuccessAssertion, ...] = ()
    _expectations: tuple[EfficiencyAssertion, ...] = ()

    def success(self, *assertions: SuccessAssertion) -> TrajectoryScorer:
        """Append correctness assertions that hard-fail the test."""
        return TrajectoryScorer(
            _success=(*self._success, *assertions),
            _expectations=self._expectations,
        )

    def expect(
        self,
        *,
        agent_steps: int | None = None,
        tool_call_requests: int | None = None,
        tool_calls: list[ToolCall] | None = None,
    ) -> TrajectoryScorer:
        """Append efficiency assertions that are logged but never fail."""
        new: list[EfficiencyAssertion] = []
        if agent_steps is not None:
            new.append(AgentSteps(n=agent_steps))
        if tool_call_requests is not None:
            new.append(ToolCallRequests(n=tool_call_requests))
        if tool_calls is not None:
            new.extend(tool_calls)
        return TrajectoryScorer(
            _success=self._success,
            _expectations=(*self._expectations, *new),
        )


# ---------------------------------------------------------------------------
# Internal: trajectory construction & assertion runner
# ---------------------------------------------------------------------------


def _trajectory_from_result(result: Mapping[str, object]) -> AgentTrajectory:
    """Build an ``AgentTrajectory`` from a raw agent invoke result."""
    steps: list[AgentStep] = []
    current_step: AgentStep | None = None

    messages_obj = result.get("messages")
    if not isinstance(messages_obj, list):
        msg = f"Expected result['messages'] to be list, got {type(messages_obj)}"
        raise TypeError(msg)

    for msg_obj in messages_obj[1:]:
        if isinstance(msg_obj, AIMessage):
            if current_step is not None:
                steps.append(current_step)
            current_step = AgentStep(
                index=len(steps) + 1,
                action=msg_obj,
                observations=[],
            )
        elif isinstance(msg_obj, ToolMessage):
            if current_step is not None:
                current_step.observations.append(msg_obj)

    if current_step is not None:
        steps.append(current_step)

    return AgentTrajectory(
        steps=steps,
        files=_coerce_result_files_to_strings(result.get("files")),
    )


@dataclass
class EfficiencyResult:
    """Per-test efficiency data collected during the session."""

    expected_steps: int | None
    actual_steps: int
    expected_tool_calls: int | None
    actual_tool_calls: int
    duration_s: float | None = None
    passed: bool | None = None


_on_efficiency_result: Callable[[EfficiencyResult], None] | None = None
"""Callback set by a reporter plugin to collect per-test efficiency data."""


def _log_efficiency(
    trajectory: AgentTrajectory,
    scorer: TrajectoryScorer,
) -> EfficiencyResult | None:
    """Log efficiency feedback (to LangSmith when available)."""
    actual_steps = len(trajectory.steps)
    actual_tool_calls = sum(len(s.action.tool_calls) for s in trajectory.steps)

    if _HAS_LANGSMITH:
        try:
            t.log_feedback(key="agent_steps", value=actual_steps)
            t.log_feedback(key="tool_call_requests", value=actual_tool_calls)
        except Exception:  # noqa: BLE001
            pass

    expected_steps: int | None = None
    expected_tool_calls: int | None = None
    for assertion in scorer._expectations:
        if isinstance(assertion, AgentSteps):
            expected_steps = assertion.n
        elif isinstance(assertion, ToolCallRequests):
            expected_tool_calls = assertion.n

    if _HAS_LANGSMITH:
        try:
            if expected_steps is not None:
                t.log_feedback(key="expected_agent_steps", value=expected_steps)
            if expected_tool_calls is not None:
                t.log_feedback(
                    key="expected_tool_call_requests", value=expected_tool_calls
                )
        except Exception:  # noqa: BLE001
            pass

    if expected_steps is None and expected_tool_calls is None:
        return None

    return EfficiencyResult(
        expected_steps=expected_steps,
        actual_steps=actual_steps,
        expected_tool_calls=expected_tool_calls,
        actual_tool_calls=actual_tool_calls,
    )


def _assert_expectations(
    trajectory: AgentTrajectory,
    scorer: TrajectoryScorer,
) -> None:
    """Run all assertions. Success = hard-fail; efficiency = log only."""
    eff_result = _log_efficiency(trajectory, scorer)
    if eff_result is not None and _on_efficiency_result is not None:
        _on_efficiency_result(eff_result)

    success = True
    for assertion in scorer._success:
        if not assertion.check(trajectory):
            success = False
            if _HAS_LANGSMITH:
                try:
                    t.log_feedback(key="correctness", value=0)
                except Exception:  # noqa: BLE001
                    pass
            pytest.fail(
                f"success check failed: {assertion.describe_failure(trajectory)}"
                f"\n\ntrajectory:\n{trajectory.pretty()}",
                pytrace=False,
            )
    if success and _HAS_LANGSMITH:
        try:
            t.log_feedback(key="correctness", value=1)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Public entry point — trajectory-based
# ---------------------------------------------------------------------------


def run_agent(
    agent: CompiledStateGraph[Any, Any],
    *,
    query: str | list[AnyMessage],
    model: BaseChatModel,
    initial_files: dict[str, str] | None = None,
    scorer: TrajectoryScorer | None = None,
    thread_id: str | None = None,
    eval_metadata: dict[str, object] | None = None,
) -> AgentTrajectory:
    """Invoke *agent*, build trajectory, and validate with *scorer*.

    Adapted from the Deep Agents SDK reference ``run_agent`` with
    optional LangSmith logging.
    """
    if isinstance(query, str):
        invoke_inputs: dict[str, Any] = {
            "messages": [{"role": "user", "content": query}],
        }
    else:
        invoke_inputs = {"messages": query}

    if initial_files is not None:
        invoke_inputs["files"] = {
            path: create_file_data(content)
            for path, content in initial_files.items()
        }

    if thread_id is None:
        thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Optional LangSmith input logging
    if _HAS_LANGSMITH:
        try:
            run_tree = get_current_run_tree()
            model_str = str(
                getattr(model, "model", None)
                or getattr(model, "model_name", "")
            )
            logged_inputs: dict[str, Any] = {
                "test_name": run_tree.name if run_tree else "unknown",
                "model": model_str,
            }
            if eval_metadata is not None:
                logged_inputs["eval_metadata"] = eval_metadata
            t.log_inputs(logged_inputs)
            if run_tree is not None:
                run_tree.inputs = logged_inputs
        except Exception:  # noqa: BLE001
            logger.debug("LangSmith input logging skipped", exc_info=True)

    result = agent.invoke(invoke_inputs, config)

    if _HAS_LANGSMITH:
        try:
            t.log_outputs(result)
        except Exception:  # noqa: BLE001
            logger.debug("LangSmith output logging skipped", exc_info=True)

    if not isinstance(result, Mapping):
        msg = f"Expected invoke result to be Mapping, got {type(result)}"
        raise TypeError(msg)

    trajectory = _trajectory_from_result(result)
    if scorer is not None:
        _assert_expectations(trajectory, scorer)
    return trajectory


# ---------------------------------------------------------------------------
# Legacy scenario helper (pre-trajectory)
# ---------------------------------------------------------------------------


def run_agent_scenario(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
    """Run the meta-agent with given messages and return the final state.

    Args:
        messages: List of {"role": "user", "content": "..."} dicts.
        **kwargs: Passed to graph.invoke config.  Accepts ``thread_id``
            (pulled out and placed inside ``configurable``) and any other
            keys forwarded to the LangGraph config dict.

    Returns:
        Final state dict from graph.invoke.
    """
    from meta_agent.graph import create_graph
    from meta_agent.state import create_initial_state
    from langchain_core.messages import HumanMessage

    graph = create_graph()
    state = create_initial_state(project_id=kwargs.pop("project_id", "eval-run"))
    state["messages"] = [
        HumanMessage(content=m["content"]) for m in messages if m.get("role") == "user"
    ]

    thread_id = kwargs.pop("thread_id", f"eval-{id(messages)}")
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    config.update(kwargs)

    return graph.invoke(state, config=config)
