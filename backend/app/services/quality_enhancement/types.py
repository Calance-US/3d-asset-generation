"""
Shared types for quality enhancement services.

This module contains shared data structures to avoid circular imports
between quality enhancement services.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class EnhancementCategory(Enum):
    """Categories of quality enhancements."""
    EDUCATIONAL_CONTENT = "educational_content"
    INTERACTIVITY = "interactivity"
    VISUAL_QUALITY = "visual_quality"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    SCIENTIFIC_ACCURACY = "scientific_accuracy"
    USER_EXPERIENCE = "user_experience"


@dataclass
class EnhancementStrategy:
    """Strategy for enhancing a specific quality aspect."""
    category: EnhancementCategory
    priority: int
    target_improvement: float
    prompt_template: str
    success_indicators: List[str]
    max_attempts: int = 2


@dataclass
class QualityGapAnalysis:
    """Analysis of quality gaps and improvement opportunities."""
    current_score: float
    target_score: float
    score_gap: float
    improvement_opportunities: List[Dict[str, Any]]
    recommended_strategies: List[EnhancementStrategy]
    estimated_improvement: float


@dataclass
class EnhancementResult:
    """Result of a quality enhancement attempt."""
    success: bool
    enhanced_html: str
    quality_improvement: float
    new_quality_score: float
    strategy_used: Optional[EnhancementStrategy]
    improvements_made: List[str]
    error_message: Optional[str] = None


@dataclass
class ImprovementOpportunity:
    """Represents an opportunity to improve content quality."""
    category: EnhancementCategory
    current_level: str
    target_level: str
    improvement_potential: float
    enhancement_prompt: str
    priority: int
    confidence: float 