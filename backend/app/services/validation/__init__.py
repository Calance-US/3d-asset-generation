"""
Validation services for HTML, JavaScript, Three.js, scientific accuracy, and realism.
"""

# from .browser_tester import BrowserTester  # Commented out due to missing playwright dependency
# from .context_filter import ContextFilter, ContextItem, FilterCriteria, FilterResult
# from .feedback_loop import (
#     AdaptationRule,
#     FeedbackLoop,
#     FeedbackMetrics,
#     LearningPattern,
# )
from .html_validator import HTMLValidator, ValidationIssue, ValidationResult

# from .performance_validator import PerformanceValidator
# from .quality_scorer import (
#     QualityFeedback,
#     QualityMetrics,
#     QualityResult,
#     QualityScorer,
#     QualityTrend,
# )
from .realism_validator import RealismIssue, RealismValidationResult, RealismValidator

# from .rendering_validator import RenderingValidator
# from .runtime_validator import (
#     PerformanceMetrics,
#     RenderingValidation,
#     RuntimeIssue,
#     RuntimeValidationResult,
#     RuntimeValidator,
# )
from .scientific_validator import (
    ScientificIssue,
    ScientificValidationResult,
    ScientificValidator,
)

# from .validation_orchestrator import ValidationOrchestrator
from .simple_orchestrator import SimpleValidationOrchestrator
from .threejs_validator import ThreeJSIssue, ThreeJSValidationResult, ThreeJSValidator

__all__ = [
    # Phase 1: HTML/JS Validation
    "HTMLValidator",
    "ValidationIssue",
    "ValidationResult",
    "ThreeJSValidator",
    "ThreeJSIssue",
    "ThreeJSValidationResult",
    # Phase 2: Scientific Accuracy & Realism
    "ScientificValidator",
    "ScientificIssue",
    "ScientificValidationResult",
    "RealismValidator",
    "RealismIssue",
    "RealismValidationResult",
    # Phase 3: Runtime Validation
    # "RuntimeValidator",
    # "RuntimeIssue",
    # "RuntimeValidationResult",
    # "PerformanceMetrics",
    # "RenderingValidation",
    # "BrowserTester",
    # "PerformanceValidator",
    # "RenderingValidator",
    # Phase 4: Quality Scoring & Feedback Loops
    # "QualityScorer",
    # "QualityMetrics",
    # "QualityResult",
    # "QualityFeedback",
    # "QualityTrend",
    # "FeedbackLoop",
    # "FeedbackMetrics",
    # "LearningPattern",
    # "AdaptationRule",
    # "ContextFilter",
    # "ContextItem",
    # "FilterCriteria",
    # "FilterResult",
    # "ValidationOrchestrator",
    "SimpleValidationOrchestrator",
]
