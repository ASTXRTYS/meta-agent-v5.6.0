"""Stage wiring package for the meta-agent system.

This package implements the Formalized Stage Interface (FSI), providing
a unified contract for workflow stage transitions, persistent state synchronization,
and rich telemetry.

All workflow stages inherit from the BaseStage abstract base class.
"""

from .base import BaseStage, ConditionResult
from .intake import IntakeStage
from .prd_review import PrdReviewStage
from .research import ResearchStage
from .spec_generation import SpecGenerationStage
from .spec_review import SpecReviewStage

__all__ = [
    "BaseStage",
    "ConditionResult",
    "IntakeStage",
    "PrdReviewStage",
    "ResearchStage",
    "SpecGenerationStage",
    "SpecReviewStage",
]
