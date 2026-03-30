"""Stage wiring package for the meta-agent system.

Implements the logic for each workflow stage including
entry conditions, exit conditions, and stage-specific behaviors.
"""

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
