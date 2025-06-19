"""
Feedback Loop System for Continuous Quality Improvement

This module implements feedback loops that use quality assessment results to
continuously improve the 3D content generation process through learning,
adaptation, and optimization mechanisms.
"""

import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class FeedbackMetrics:
    """Metrics for tracking feedback loop effectiveness."""

    total_validations: int
    success_rate: float
    average_quality_score: float
    improvement_rate: float

    # Pattern analysis
    common_issues: List[Tuple[str, int]]
    improvement_patterns: List[str]
    quality_trends: Dict[str, float]

    # Learning effectiveness
    adaptation_success_rate: float
    false_positive_rate: float
    false_negative_rate: float


@dataclass
class LearningPattern:
    """Pattern learned from quality feedback."""

    pattern_id: str
    pattern_type: str  # "issue", "success", "improvement"
    description: str
    confidence: float
    frequency: int

    # Pattern conditions
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]

    # Context
    subject_areas: List[str]
    education_levels: List[str]
    content_types: List[str]

    # Effectiveness tracking
    applications: int
    success_rate: float
    last_updated: float


@dataclass
class AdaptationRule:
    """Rule for adapting content generation based on feedback."""

    rule_id: str
    name: str
    description: str

    # Trigger conditions
    trigger_conditions: Dict[str, Any]
    confidence_threshold: float

    # Actions to take
    prompt_modifications: List[str]
    validation_adjustments: Dict[str, float]
    generation_parameters: Dict[str, Any]

    # Rule metadata
    priority: int
    active: bool
    success_count: int
    application_count: int
    created_timestamp: float
    last_applied: float


class FeedbackLoop:
    """Continuous improvement system using quality feedback."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the feedback loop system."""
        self.storage_path = storage_path or "feedback_data.json"

        # Learning data structures
        self.quality_history: deque = deque(maxlen=1000)
        self.issue_patterns: Dict[str, LearningPattern] = {}
        self.success_patterns: Dict[str, LearningPattern] = {}
        self.adaptation_rules: Dict[str, AdaptationRule] = {}

        # Pattern recognition
        self.pattern_recognizer = PatternRecognizer()
        self.rule_generator = RuleGenerator()

        # Performance tracking
        self.metrics = FeedbackMetrics(
            total_validations=0,
            success_rate=0.0,
            average_quality_score=0.0,
            improvement_rate=0.0,
            common_issues=[],
            improvement_patterns=[],
            quality_trends={},
            adaptation_success_rate=0.0,
            false_positive_rate=0.0,
            false_negative_rate=0.0,
        )

        # Configuration
        self.config = {
            "min_pattern_frequency": 3,
            "pattern_confidence_threshold": 0.7,
            "adaptation_threshold": 0.8,
            "max_adaptation_rules": 50,
            "learning_rate": 0.1,
            "decay_factor": 0.95,
        }

        # Load existing data
        self._load_feedback_data()

    def process_quality_result(self, quality_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a quality assessment result and learn from it.

        Args:
            quality_result: Quality assessment result to learn from

        Returns:
            Dictionary with feedback processing results and recommendations
        """

        # Store quality result
        self.quality_history.append(quality_result)
        self.metrics.total_validations += 1

        # Extract learning data
        learning_data = self._extract_learning_data(quality_result)

        # Pattern recognition
        new_patterns = self.pattern_recognizer.identify_patterns(
            learning_data, self.quality_history
        )

        # Update pattern database
        patterns_updated = self._update_patterns(new_patterns)

        # Generate/update adaptation rules
        new_rules = self.rule_generator.generate_rules(
            self.issue_patterns, self.success_patterns
        )
        rules_updated = self._update_adaptation_rules(new_rules)

        # Calculate recommendations
        recommendations = self._generate_recommendations(quality_result)

        # Update metrics
        self._update_metrics()

        # Save feedback data
        self._save_feedback_data()

        return {
            "feedback_processed": True,
            "patterns_identified": len(new_patterns),
            "patterns_updated": patterns_updated,
            "rules_generated": len(new_rules),
            "rules_updated": rules_updated,
            "recommendations": recommendations,
            "learning_summary": self._get_learning_summary(),
        }

    def get_generation_adaptations(
        self, content_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get adaptations for content generation based on learned patterns.

        Args:
            content_request: Request for content generation

        Returns:
            Dictionary with generation adaptations and modifications
        """

        adaptations = {
            "prompt_modifications": [],
            "parameter_adjustments": {},
            "validation_focus": [],
            "quality_predictions": {},
        }

        # Extract request context
        subject = content_request.get("subject", "general")
        education_level = content_request.get("education_level", "unknown")
        content_type = content_request.get("content_type", "visualization")

        # Apply relevant adaptation rules
        applicable_rules = self._find_applicable_rules(content_request)

        for rule in applicable_rules:
            # Apply prompt modifications
            adaptations["prompt_modifications"].extend(rule.prompt_modifications)

            # Apply parameter adjustments
            adaptations["parameter_adjustments"].update(rule.generation_parameters)

            # Add validation focus areas
            validation_adjustments = rule.validation_adjustments
            for validation_type, weight in validation_adjustments.items():
                if validation_type not in adaptations["validation_focus"]:
                    adaptations["validation_focus"].append(validation_type)

        # Predict quality based on patterns
        quality_prediction = self._predict_quality(content_request)
        adaptations["quality_predictions"] = quality_prediction

        # Add pattern-based recommendations
        pattern_recommendations = self._get_pattern_recommendations(content_request)
        adaptations["pattern_recommendations"] = pattern_recommendations

        return adaptations

    def _extract_learning_data(self, quality_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract learning data from quality result."""

        return {
            "content_id": quality_result.get("content_id", "unknown"),
            "subject": quality_result.get("subject", "general"),
            "education_level": quality_result.get("education_level", "unknown"),
            "overall_score": quality_result.get("metrics", {}).get(
                "overall_quality_score", 0.0
            ),
            "technical_score": quality_result.get("metrics", {}).get(
                "technical_quality_score", 0.0
            ),
            "educational_score": quality_result.get("metrics", {}).get(
                "educational_quality_score", 0.0
            ),
            "ux_score": quality_result.get("metrics", {}).get(
                "user_experience_score", 0.0
            ),
            "critical_issues": quality_result.get("metrics", {}).get(
                "critical_issues", 0
            ),
            "major_issues": quality_result.get("metrics", {}).get("major_issues", 0),
            "quality_tier": quality_result.get("quality_tier", "basic"),
            "recommended": quality_result.get("recommended_for_use", False),
            "issues": quality_result.get("feedback", {}).get("weaknesses", []),
            "strengths": quality_result.get("feedback", {}).get("strengths", []),
            "timestamp": quality_result.get("validation_timestamp", 0.0),
        }

    def _update_patterns(self, new_patterns: List[LearningPattern]) -> int:
        """Update pattern database with new patterns."""

        updated_count = 0

        for pattern in new_patterns:
            if pattern.pattern_type == "issue":
                storage = self.issue_patterns
            elif pattern.pattern_type == "success":
                storage = self.success_patterns
            else:
                continue

            existing_pattern = storage.get(pattern.pattern_id)

            if existing_pattern:
                # Update existing pattern
                existing_pattern.frequency += 1
                existing_pattern.confidence = max(
                    existing_pattern.confidence, pattern.confidence
                )
                existing_pattern.last_updated = pattern.last_updated
                updated_count += 1
            else:
                # Add new pattern
                storage[pattern.pattern_id] = pattern
                updated_count += 1

        return updated_count

    def _update_adaptation_rules(self, new_rules: List[AdaptationRule]) -> int:
        """Update adaptation rules."""

        updated_count = 0

        for rule in new_rules:
            existing_rule = self.adaptation_rules.get(rule.rule_id)

            if existing_rule:
                # Update existing rule
                if rule.confidence_threshold > existing_rule.confidence_threshold:
                    existing_rule.confidence_threshold = rule.confidence_threshold
                    existing_rule.prompt_modifications = rule.prompt_modifications
                    existing_rule.validation_adjustments = rule.validation_adjustments
                    updated_count += 1
            else:
                # Add new rule
                if len(self.adaptation_rules) < self.config["max_adaptation_rules"]:
                    self.adaptation_rules[rule.rule_id] = rule
                    updated_count += 1

        return updated_count

    def _generate_recommendations(self, quality_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on patterns and rules."""

        recommendations = []

        # Analyze current result against patterns
        subject = quality_result.get("subject", "general")
        education_level = quality_result.get("education_level", "unknown")
        overall_score = quality_result.get("metrics", {}).get(
            "overall_quality_score", 0.0
        )

        # Pattern-based recommendations
        for pattern in self.issue_patterns.values():
            if (
                subject in pattern.subject_areas
                and education_level in pattern.education_levels
                and pattern.confidence > self.config["pattern_confidence_threshold"]
            ):
                recommendations.append(
                    f"Based on pattern analysis: {pattern.description}"
                )

        # Score-based recommendations
        if overall_score < 6.0:
            recommendations.append(
                "Focus on fundamental quality improvements across all validation phases"
            )
        elif overall_score < 8.0:
            recommendations.append(
                "Content shows promise but needs refinement in specific areas"
            )

        # Subject-specific recommendations
        subject_patterns = [
            p
            for p in self.success_patterns.values()
            if subject in p.subject_areas and p.confidence > 0.8
        ]

        if subject_patterns:
            best_pattern = max(subject_patterns, key=lambda p: p.confidence)
            recommendations.append(f"For {subject} content: {best_pattern.description}")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _find_applicable_rules(
        self, content_request: Dict[str, Any]
    ) -> List[AdaptationRule]:
        """Find adaptation rules applicable to the content request."""

        applicable_rules = []

        subject = content_request.get("subject", "general")
        education_level = content_request.get("education_level", "unknown")
        content_type = content_request.get("content_type", "visualization")

        for rule in self.adaptation_rules.values():
            if not rule.active:
                continue

            # Check trigger conditions
            conditions_met = True
            for condition, value in rule.trigger_conditions.items():
                if condition == "subject" and subject not in value:
                    conditions_met = False
                    break
                elif condition == "education_level" and education_level not in value:
                    conditions_met = False
                    break
                elif condition == "content_type" and content_type not in value:
                    conditions_met = False
                    break

            if (
                conditions_met
                and rule.success_count / max(rule.application_count, 1)
                >= rule.confidence_threshold
            ):
                applicable_rules.append(rule)

        # Sort by priority and success rate
        applicable_rules.sort(
            key=lambda r: (r.priority, r.success_count / max(r.application_count, 1)),
            reverse=True,
        )

        return applicable_rules[:10]  # Limit to top 10 rules

    def _predict_quality(self, content_request: Dict[str, Any]) -> Dict[str, float]:
        """Predict quality scores based on historical patterns."""

        subject = content_request.get("subject", "general")
        education_level = content_request.get("education_level", "unknown")

        # Find similar historical content
        similar_content = [
            entry
            for entry in self.quality_history
            if entry.get("subject") == subject
            and entry.get("education_level") == education_level
        ]

        if not similar_content:
            # Use overall averages
            similar_content = list(self.quality_history)

        if not similar_content:
            return {
                "overall_score": 7.0,
                "technical_score": 7.0,
                "educational_score": 7.0,
                "ux_score": 7.0,
                "confidence": 0.1,
            }

        # Calculate predictions
        overall_scores = [entry.get("overall_score", 0.0) for entry in similar_content]
        technical_scores = [
            entry.get("technical_score", 0.0) for entry in similar_content
        ]
        educational_scores = [
            entry.get("educational_score", 0.0) for entry in similar_content
        ]
        ux_scores = [entry.get("ux_score", 0.0) for entry in similar_content]

        return {
            "overall_score": statistics.mean(overall_scores) if overall_scores else 7.0,
            "technical_score": statistics.mean(technical_scores)
            if technical_scores
            else 7.0,
            "educational_score": statistics.mean(educational_scores)
            if educational_scores
            else 7.0,
            "ux_score": statistics.mean(ux_scores) if ux_scores else 7.0,
            "confidence": min(1.0, len(similar_content) / 10.0),
        }

    def _get_pattern_recommendations(
        self, content_request: Dict[str, Any]
    ) -> List[str]:
        """Get pattern-based recommendations for content generation."""

        recommendations = []
        subject = content_request.get("subject", "general")
        education_level = content_request.get("education_level", "unknown")

        # Success pattern recommendations
        relevant_success_patterns = [
            pattern
            for pattern in self.success_patterns.values()
            if subject in pattern.subject_areas
            and education_level in pattern.education_levels
            and pattern.confidence > 0.7
        ]

        for pattern in relevant_success_patterns[:3]:  # Top 3 patterns
            recommendations.append(f"Success pattern: {pattern.description}")

        # Issue avoidance recommendations
        relevant_issue_patterns = [
            pattern
            for pattern in self.issue_patterns.values()
            if subject in pattern.subject_areas
            and education_level in pattern.education_levels
            and pattern.confidence > 0.7
        ]

        for pattern in relevant_issue_patterns[:2]:  # Top 2 issue patterns
            recommendations.append(f"Avoid: {pattern.description}")

        return recommendations

    def _update_metrics(self):
        """Update feedback loop metrics."""

        if not self.quality_history:
            return

        # Basic metrics
        scores = [entry.get("overall_score", 0.0) for entry in self.quality_history]
        recommended = [
            entry.get("recommended", False) for entry in self.quality_history
        ]

        self.metrics.average_quality_score = statistics.mean(scores) if scores else 0.0
        self.metrics.success_rate = (
            sum(recommended) / len(recommended) if recommended else 0.0
        )

        # Improvement rate (last 20 vs previous 20)
        if len(self.quality_history) >= 40:
            recent_scores = scores[-20:]
            previous_scores = scores[-40:-20]

            recent_avg = statistics.mean(recent_scores)
            previous_avg = statistics.mean(previous_scores)

            self.metrics.improvement_rate = recent_avg - previous_avg

        # Common issues
        all_issues = []
        for entry in self.quality_history:
            all_issues.extend(entry.get("issues", []))

        issue_counts = defaultdict(int)
        for issue in all_issues:
            issue_counts[issue] += 1

        self.metrics.common_issues = sorted(
            issue_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Quality trends by subject
        subject_scores = defaultdict(list)
        for entry in self.quality_history:
            subject = entry.get("subject", "general")
            score = entry.get("overall_score", 0.0)
            subject_scores[subject].append(score)

        self.metrics.quality_trends = {
            subject: statistics.mean(scores)
            for subject, scores in subject_scores.items()
        }

    def _get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning progress."""

        return {
            "total_patterns": len(self.issue_patterns) + len(self.success_patterns),
            "issue_patterns": len(self.issue_patterns),
            "success_patterns": len(self.success_patterns),
            "active_rules": len(
                [r for r in self.adaptation_rules.values() if r.active]
            ),
            "average_quality": self.metrics.average_quality_score,
            "success_rate": self.metrics.success_rate,
            "improvement_rate": self.metrics.improvement_rate,
            "data_points": len(self.quality_history),
        }

    def _save_feedback_data(self):
        """Save feedback data to storage."""

        try:
            data = {
                "quality_history": list(self.quality_history),
                "issue_patterns": {
                    k: asdict(v) for k, v in self.issue_patterns.items()
                },
                "success_patterns": {
                    k: asdict(v) for k, v in self.success_patterns.items()
                },
                "adaptation_rules": {
                    k: asdict(v) for k, v in self.adaptation_rules.items()
                },
                "metrics": asdict(self.metrics),
                "config": self.config,
            }

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save feedback data: {str(e)}")

    def _load_feedback_data(self):
        """Load feedback data from storage."""

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            # Load quality history
            self.quality_history = deque(data.get("quality_history", []), maxlen=1000)

            # Load patterns
            issue_patterns_data = data.get("issue_patterns", {})
            for pattern_id, pattern_data in issue_patterns_data.items():
                self.issue_patterns[pattern_id] = LearningPattern(**pattern_data)

            success_patterns_data = data.get("success_patterns", {})
            for pattern_id, pattern_data in success_patterns_data.items():
                self.success_patterns[pattern_id] = LearningPattern(**pattern_data)

            # Load rules
            rules_data = data.get("adaptation_rules", {})
            for rule_id, rule_data in rules_data.items():
                self.adaptation_rules[rule_id] = AdaptationRule(**rule_data)

            # Load metrics
            metrics_data = data.get("metrics", {})
            if metrics_data:
                self.metrics = FeedbackMetrics(**metrics_data)

            # Load config
            self.config.update(data.get("config", {}))

        except FileNotFoundError:
            logger.info("No existing feedback data found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load feedback data: {str(e)}")


class PatternRecognizer:
    """Pattern recognition for quality feedback analysis."""

    def identify_patterns(
        self, learning_data: Dict[str, Any], history: deque
    ) -> List[LearningPattern]:
        """Identify patterns in quality data."""

        patterns = []

        # Issue patterns
        if learning_data.get("critical_issues", 0) > 0:
            patterns.extend(self._identify_issue_patterns(learning_data, history))

        # Success patterns
        if learning_data.get("overall_score", 0) >= 8.0:
            patterns.extend(self._identify_success_patterns(learning_data, history))

        return patterns

    def _identify_issue_patterns(
        self, learning_data: Dict[str, Any], history: deque
    ) -> List[LearningPattern]:
        """Identify patterns that lead to issues."""

        patterns = []
        subject = learning_data.get("subject", "general")
        education_level = learning_data.get("education_level", "unknown")

        # Find similar problematic content
        similar_issues = [
            entry
            for entry in history
            if entry.get("subject") == subject and entry.get("critical_issues", 0) > 0
        ]

        if len(similar_issues) >= 3:  # Minimum frequency for pattern
            pattern = LearningPattern(
                pattern_id=f"issue_{subject}_{education_level}",
                pattern_type="issue",
                description=f"Critical issues common in {subject} content for {education_level}",
                confidence=min(1.0, len(similar_issues) / 10.0),
                frequency=len(similar_issues),
                conditions={"subject": subject, "education_level": education_level},
                outcomes={"critical_issues": True},
                subject_areas=[subject],
                education_levels=[education_level],
                content_types=["visualization"],
                applications=0,
                success_rate=0.0,
                last_updated=learning_data.get("timestamp", 0.0),
            )
            patterns.append(pattern)

        return patterns

    def _identify_success_patterns(
        self, learning_data: Dict[str, Any], history: deque
    ) -> List[LearningPattern]:
        """Identify patterns that lead to success."""

        patterns = []
        subject = learning_data.get("subject", "general")
        education_level = learning_data.get("education_level", "unknown")

        # Find similar high-quality content
        similar_successes = [
            entry
            for entry in history
            if entry.get("subject") == subject and entry.get("overall_score", 0) >= 8.0
        ]

        if len(similar_successes) >= 3:  # Minimum frequency for pattern
            pattern = LearningPattern(
                pattern_id=f"success_{subject}_{education_level}",
                pattern_type="success",
                description=f"High quality {subject} content patterns for {education_level}",
                confidence=min(1.0, len(similar_successes) / 10.0),
                frequency=len(similar_successes),
                conditions={"subject": subject, "education_level": education_level},
                outcomes={"high_quality": True},
                subject_areas=[subject],
                education_levels=[education_level],
                content_types=["visualization"],
                applications=0,
                success_rate=1.0,
                last_updated=learning_data.get("timestamp", 0.0),
            )
            patterns.append(pattern)

        return patterns


class RuleGenerator:
    """Rule generation for adaptive content generation."""

    def generate_rules(
        self,
        issue_patterns: Dict[str, LearningPattern],
        success_patterns: Dict[str, LearningPattern],
    ) -> List[AdaptationRule]:
        """Generate adaptation rules from patterns."""

        rules = []

        # Generate rules from issue patterns
        for pattern in issue_patterns.values():
            if pattern.confidence > 0.7 and pattern.frequency >= 3:
                rule = self._create_issue_avoidance_rule(pattern)
                rules.append(rule)

        # Generate rules from success patterns
        for pattern in success_patterns.values():
            if pattern.confidence > 0.8 and pattern.frequency >= 3:
                rule = self._create_success_replication_rule(pattern)
                rules.append(rule)

        return rules

    def _create_issue_avoidance_rule(self, pattern: LearningPattern) -> AdaptationRule:
        """Create rule to avoid issues based on pattern."""

        return AdaptationRule(
            rule_id=f"avoid_{pattern.pattern_id}",
            name=f"Avoid {pattern.description}",
            description=f"Adaptation to avoid issues in {pattern.subject_areas[0]} content",
            trigger_conditions={
                "subject": pattern.subject_areas,
                "education_level": pattern.education_levels,
            },
            confidence_threshold=0.7,
            prompt_modifications=[
                f"Extra attention to quality in {pattern.subject_areas[0]} content",
                "Focus on avoiding common critical issues",
            ],
            validation_adjustments={
                "technical_quality": 1.2,
                "scientific_accuracy": 1.1,
            },
            generation_parameters={"quality_focus": True},
            priority=4,
            active=True,
            success_count=0,
            application_count=0,
            created_timestamp=pattern.last_updated,
            last_applied=0.0,
        )

    def _create_success_replication_rule(
        self, pattern: LearningPattern
    ) -> AdaptationRule:
        """Create rule to replicate successful patterns."""

        return AdaptationRule(
            rule_id=f"replicate_{pattern.pattern_id}",
            name=f"Replicate {pattern.description}",
            description=f"Adaptation to replicate success in {pattern.subject_areas[0]} content",
            trigger_conditions={
                "subject": pattern.subject_areas,
                "education_level": pattern.education_levels,
            },
            confidence_threshold=0.8,
            prompt_modifications=[
                f"Use successful patterns for {pattern.subject_areas[0]} content",
                "Emphasize elements that lead to high quality",
            ],
            validation_adjustments={
                "overall_quality": 1.1,
            },
            generation_parameters={"success_pattern": pattern.pattern_id},
            priority=3,
            active=True,
            success_count=0,
            application_count=0,
            created_timestamp=pattern.last_updated,
            last_applied=0.0,
        )
