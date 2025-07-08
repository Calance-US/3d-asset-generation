"""
Quality Analyzer for identifying improvement opportunities in HTML content.

This service analyzes HTML content to determine what aspects need improvement
to reach a target quality score.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.services.quality_enhancement.types import (
    EnhancementCategory,
    EnhancementStrategy,
    QualityGapAnalysis,
    ImprovementOpportunity,
)

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analyzes HTML content to identify quality improvement opportunities."""

    def __init__(self):
        self.quality_indicators = self._initialize_quality_indicators()

    def _initialize_quality_indicators(self) -> Dict[EnhancementCategory, Dict[str, Any]]:
        """Initialize quality indicators for each enhancement category."""
        return {
            EnhancementCategory.EDUCATIONAL_CONTENT: {
                "indicators": [
                    "learning objective",
                    "educational",
                    "narration",
                    "explanation",
                    "concept",
                    "instruction",
                    "guidance",
                    "tutorial",
                    "lesson",
                    "teaching"
                ],
                "weight": 0.25,
                "max_improvement": 2.0
            },
            
            EnhancementCategory.INTERACTIVITY: {
                "indicators": [
                    "addEventListener",
                    "onclick",
                    "onchange",
                    "oninput",
                    "slider",
                    "control",
                    "interactive",
                    "user input",
                    "parameter",
                    "adjustment"
                ],
                "weight": 0.20,
                "max_improvement": 1.5
            },
            
            EnhancementCategory.VISUAL_QUALITY: {
                "indicators": [
                    "lighting",
                    "shadow",
                    "material",
                    "texture",
                    "color",
                    "visual",
                    "appearance",
                    "rendering",
                    "quality",
                    "aesthetic"
                ],
                "weight": 0.15,
                "max_improvement": 1.0
            },
            
            EnhancementCategory.SCIENTIFIC_ACCURACY: {
                "indicators": [
                    "unit",
                    "formula",
                    "calculation",
                    "scientific",
                    "accuracy",
                    "precision",
                    "measurement",
                    "constant",
                    "physics",
                    "chemistry"
                ],
                "weight": 0.20,
                "max_improvement": 1.5
            },
            
            EnhancementCategory.USER_EXPERIENCE: {
                "indicators": [
                    "interface",
                    "ui",
                    "ux",
                    "user experience",
                    "accessibility",
                    "responsive",
                    "intuitive",
                    "guidance",
                    "help",
                    "feedback"
                ],
                "weight": 0.20,
                "max_improvement": 1.0
            }
        }

    def analyze_quality_gaps(
        self,
        html_content: str,
        current_score: float,
        target_score: float
    ) -> QualityGapAnalysis:
        """
        Analyze what aspects need improvement to reach target score.
        
        Args:
            html_content: The HTML content to analyze
            current_score: Current quality score
            target_score: Target quality score to achieve
            
        Returns:
            QualityGapAnalysis with improvement opportunities and strategies
        """
        score_gap = target_score - current_score
        
        if score_gap <= 0:
            return QualityGapAnalysis(
                current_score=current_score,
                target_score=target_score,
                score_gap=0.0,
                improvement_opportunities=[],
                recommended_strategies=[],
                estimated_improvement=0.0
            )
        
        # Analyze each quality category
        improvement_opportunities = []
        category_scores = {}
        
        for category, config in self.quality_indicators.items():
            opportunity = self._analyze_category(
                html_content, category, config, current_score, target_score
            )
            if opportunity:
                improvement_opportunities.append(opportunity)
                category_scores[category] = opportunity.improvement_potential
        
        # Sort opportunities by improvement potential
        improvement_opportunities.sort(
            key=lambda x: x.improvement_potential, reverse=True
        )
        
        # Select recommended strategies
        recommended_strategies = self._select_recommended_strategies(
            improvement_opportunities, score_gap
        )
        
        # Estimate total improvement
        estimated_improvement = min(
            sum(opp.improvement_potential for opp in improvement_opportunities[:3]),
            score_gap
        )
        
        return QualityGapAnalysis(
            current_score=current_score,
            target_score=target_score,
            score_gap=score_gap,
            improvement_opportunities=improvement_opportunities,
            recommended_strategies=recommended_strategies,
            estimated_improvement=estimated_improvement
        )

    def _analyze_category(
        self,
        html_content: str,
        category: EnhancementCategory,
        config: Dict[str, Any],
        current_score: float,
        target_score: float
    ) -> Optional[ImprovementOpportunity]:
        """Analyze a specific quality category."""
        
        # Count indicators present in the content
        content_lower = html_content.lower()
        indicators = config["indicators"]
        present_indicators = sum(
            1 for indicator in indicators if indicator in content_lower
        )
        
        # Calculate current level (0-1 scale) - be more lenient in headless environment
        current_level = min(present_indicators / len(indicators), 1.0)
        
        # Apply headless environment adjustment - be more generous with improvement potential
        if current_level < 0.3:  # If very few indicators present
            current_level *= 0.8  # Boost current level to be more lenient
        
        # Determine target level based on score gap
        score_gap = target_score - current_score
        target_level = min(current_level + (score_gap * config["weight"] * 1.2), 1.0)  # 20% more improvement potential
        
        # Calculate improvement potential
        improvement_potential = (target_level - current_level) * config["max_improvement"]
        
        # Lower threshold for meaningful improvement in headless environment
        if improvement_potential < 0.05:  # Lowered from 0.1
            return None
        
        # Determine priority based on improvement potential and category importance
        priority = self._calculate_priority(category, improvement_potential)
        
        # Calculate confidence based on analysis quality
        confidence = self._calculate_confidence(content_lower, indicators)
        
        # Generate enhancement prompt
        enhancement_prompt = self._generate_enhancement_prompt(
            category, current_level, target_level, improvement_potential
        )
        
        return ImprovementOpportunity(
            category=category,
            current_level=self._level_to_description(current_level),
            target_level=self._level_to_description(target_level),
            improvement_potential=improvement_potential,
            enhancement_prompt=enhancement_prompt,
            priority=priority,
            confidence=confidence
        )

    def _calculate_priority(
        self, 
        category: EnhancementCategory, 
        improvement_potential: float
    ) -> int:
        """Calculate priority for an improvement opportunity."""
        
        # Base priorities (lower number = higher priority)
        base_priorities = {
            EnhancementCategory.EDUCATIONAL_CONTENT: 1,
            EnhancementCategory.SCIENTIFIC_ACCURACY: 1,
            EnhancementCategory.INTERACTIVITY: 2,
            EnhancementCategory.VISUAL_QUALITY: 3,
            EnhancementCategory.USER_EXPERIENCE: 4,
            EnhancementCategory.PERFORMANCE: 5,
            EnhancementCategory.ACCESSIBILITY: 6
        }
        
        base_priority = base_priorities.get(category, 10)
        
        # Adjust priority based on improvement potential
        if improvement_potential > 1.0:
            return base_priority - 1  # Higher priority for high potential
        elif improvement_potential < 0.3:
            return base_priority + 1  # Lower priority for low potential
        
        return base_priority

    def _calculate_confidence(self, content_lower: str, indicators: List[str]) -> float:
        """Calculate confidence in the analysis based on content quality."""
        
        # Count how many indicators are present
        present_count = sum(1 for indicator in indicators if indicator in content_lower)
        
        # Calculate confidence based on indicator coverage
        coverage = present_count / len(indicators)
        
        # Higher confidence if we have good coverage or very low coverage
        if coverage > 0.7 or coverage < 0.2:
            return 0.9
        elif coverage > 0.4:
            return 0.7
        else:
            return 0.5

    def _level_to_description(self, level: float) -> str:
        """Convert numerical level to descriptive text."""
        if level >= 0.8:
            return "excellent"
        elif level >= 0.6:
            return "good"
        elif level >= 0.4:
            return "fair"
        elif level >= 0.2:
            return "poor"
        else:
            return "very poor"

    def _generate_enhancement_prompt(
        self,
        category: EnhancementCategory,
        current_level: float,
        target_level: float,
        improvement_potential: float
    ) -> str:
        """Generate a specific enhancement prompt for the category."""
        
        category_descriptions = {
            EnhancementCategory.EDUCATIONAL_CONTENT: "educational content and learning features",
            EnhancementCategory.INTERACTIVITY: "interactive features and user controls",
            EnhancementCategory.VISUAL_QUALITY: "visual quality and appearance",
            EnhancementCategory.SCIENTIFIC_ACCURACY: "scientific accuracy and precision",
            EnhancementCategory.USER_EXPERIENCE: "user experience and interface design"
        }
        
        description = category_descriptions.get(category, "content quality")
        
        return f"Enhance {description} from {self._level_to_description(current_level)} to {self._level_to_description(target_level)} level (potential improvement: {improvement_potential:.1f} points)"

    def _select_recommended_strategies(
        self,
        improvement_opportunities: List[ImprovementOpportunity],
        score_gap: float
    ) -> List[EnhancementStrategy]:
        """Select recommended enhancement strategies based on opportunities."""
        
        # Sort opportunities by priority and improvement potential
        sorted_opportunities = sorted(
            improvement_opportunities,
            key=lambda x: (x.priority, x.improvement_potential),
            reverse=False  # Lower priority number = higher priority
        )
        
        # Select top strategies that can address the score gap
        recommended_strategies = []
        total_improvement = 0.0
        
        for opportunity in sorted_opportunities:
            if total_improvement >= score_gap:
                break
                
            # Create strategy for this opportunity
            strategy = EnhancementStrategy(
                category=opportunity.category,
                priority=opportunity.priority,
                target_improvement=opportunity.improvement_potential,
                prompt_template="",  # Will be filled by enhancement service
                success_indicators=[]  # Will be filled by enhancement service
            )
            
            recommended_strategies.append(strategy)
            total_improvement += opportunity.improvement_potential
        
        return recommended_strategies

    def get_quality_breakdown(self, html_content: str) -> Dict[str, Any]:
        """Get a detailed breakdown of quality aspects in the content."""
        
        breakdown = {}
        content_lower = html_content.lower()
        
        for category, config in self.quality_indicators.items():
            indicators = config["indicators"]
            present_indicators = [
                indicator for indicator in indicators 
                if indicator in content_lower
            ]
            
            missing_indicators = [
                indicator for indicator in indicators 
                if indicator not in content_lower
            ]
            
            coverage = len(present_indicators) / len(indicators)
            
            breakdown[category.value] = {
                "coverage": coverage,
                "score": coverage * 10.0,  # Convert to 0-10 scale
                "present_indicators": present_indicators,
                "missing_indicators": missing_indicators,
                "total_indicators": len(indicators)
            }
        
        return breakdown 