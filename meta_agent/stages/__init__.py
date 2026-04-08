"""Stage wiring package for the meta-agent system.

Implements the logic for each workflow stage including
entry conditions, exit conditions, and stage-specific behaviors.
"""

# TODO: Investigate helper function duplication across stages
# ISSUE: _get_field() utility is duplicated in intake.py (lines 173-179),
# prd_review.py (lines 173-182), and referenced in spec_review.py (line 13).
# This helper extracts fields from dataclasses or dicts and is used for
# polymorphic field access across stage implementations.
# RECOMMENDED ACTION: Extract _get_field() to meta_agent/stages/common.py
# and import it in all stage files. Affected files: intake.py, prd_review.py,
# spec_review.py, research.py.

# TODO: Investigate path construction inconsistency across stages
# ISSUE: Stage files use a mix of f-string concatenation and os.path.join()
# for path construction. spec_review.py and spec_generation.py use f-strings,
# while research.py uses os.path.join(). This breaks cross-platform compatibility
# (Windows uses backslashes).
# RECOMMENDED ACTION: Standardize all path construction to os.path.join() or
# pathlib.Path across all stage files. Affected files: spec_review.py, spec_generation.py,
# research.py.

# TODO: Investigate method signature inconsistency across stages
# ISSUE: check_entry_conditions() takes no state parameter in spec_review.py,
# but research.py and spec_generation.py both accept state: dict[str, Any] | None
# for path overrides. This breaks the polymorphic stage interface pattern.
# RECOMMENDED ACTION: Define base stage interface with consistent signature
# accepting optional state parameter, or document why spec_review intentionally
# deviates. Affected files: spec_review.py, research.py, spec_generation.py.

# TODO: Investigate missing validation helpers across stages
# ISSUE: Multiple stages lack content validation for artifacts. spec_review.py
# blindly trusts file existence without validating structure (lines 71-73),
# intake.py uses naive substring validation (lines 171-173), and spec_generation.py
# has no spec validation at all. Only research.py has proper section validation.
# RECOMMENDED ACTION: Create validation helpers in meta_agent/stages/common.py
# for common artifact types (PRD, spec, eval suites) and use across all stages.
# Affected files: spec_review.py, intake.py, spec_generation.py, research.py.

# TODO: Investigate missing revision cycle tracking across stages
# ISSUE: prd_review.py has MAX_REVISION_CYCLES and increment methods, but
# spec_review.py lacks any iteration guardrails (lines 39-41, 72-74). This makes
# spec_review vulnerable to infinite revision loops. spec_generation.py has
# disconnected tracking between instance state and workflow state.
# RECOMMENDED ACTION: Extract revision tracking to base stage class in
# meta_agent/stages/common.py with MAX_REVISION_CYCLES, increment_revision_count(),
# and at_revision_limit() methods. Affected files: prd_review.py, spec_review.py,
# spec_generation.py.

from .intake import IntakeStage
from .prd_review import PrdReviewStage
from .research import ResearchStage
from .spec_generation import SpecGenerationStage
from .spec_review import SpecReviewStage

__all__ = [
    "IntakeStage",
    "PrdReviewStage",
    "ResearchStage",
    "SpecGenerationStage",
    "SpecReviewStage",
]
