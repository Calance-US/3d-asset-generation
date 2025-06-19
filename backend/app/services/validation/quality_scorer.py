"""
Quality Scoring Engine for 3D Educational Content

This module provides comprehensive quality scoring algorithms that integrate
results from all validation phases (HTML/JS, Scientific Accuracy, Realism,
and Runtime) into unified quality metrics and scores.
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for 3D educational content."""

    # Overall scores (0-10 scale)
    overall_quality_score: float
    technical_quality_score: float
    educational_quality_score: float
    user_experience_score: float

    # Phase-specific scores
    html_js_score: float
    scientific_accuracy_score: float
    realism_score: float
    runtime_performance_score: float

    # Detailed metrics
    syntax_correctness: float
    api_compliance: float
    unit_accuracy: float
    formula_correctness: float
    concept_alignment: float
    material_realism: float
    lighting_quality: float
    load_performance: float
    rendering_quality: float

    # Issue analysis
    critical_issues: int
    major_issues: int
    minor_issues: int
    warnings: int

    # Educational effectiveness
    age_appropriateness: float
    topic_coverage: float
    learning_objectives_met: float

    # Technical reliability
    browser_compatibility: float
    performance_consistency: float
    error_resilience: float


@dataclass
class QualityFeedback:
    """Feedback and recommendations for quality improvement."""

    score_breakdown: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    critical_fixes: List[str]
    improvement_suggestions: List[str]
    educational_recommendations: List[str]
    technical_recommendations: List[str]
    priority_actions: List[Tuple[str, int]]  # (action, priority 1-5)


@dataclass
class QualityTrend:
    """Quality trend analysis over time."""

    current_score: float
    previous_score: Optional[float]
    trend_direction: str  # "improving", "declining", "stable"
    trend_strength: float  # 0-1 scale
    improvement_rate: float
    consistency_score: float

    # Historical data
    score_history: List[float] = field(default_factory=list)
    timestamp_history: List[float] = field(default_factory=list)


@dataclass
class QualityResult:
    """Complete quality assessment result."""

    content_id: str
    title: str
    subject: str
    education_level: str

    # Quality assessment
    metrics: QualityMetrics
    feedback: QualityFeedback

    # Validation data
    validation_timestamp: float
    validation_duration: float

    # Pass/fail status
    passes_quality_threshold: bool
    recommended_for_use: bool
    requires_review: bool

    # Context filtering
    quality_tier: str  # "premium", "standard", "basic", "rejected"
    confidence_level: float  # 0-1 scale

    # Optional fields with defaults
    trend: Optional[QualityTrend] = None


class QualityScorer:
    """Comprehensive quality scoring engine for 3D educational content."""

    def __init__(self):
        """Initialize the quality scorer."""

        # Quality thresholds
        self.quality_thresholds = {
            "premium": 8.5,
            "standard": 7.0,
            "basic": 5.0,
            "rejected": 0.0,
        }

        # Scoring weights for different aspects
        self.scoring_weights = {
            "technical_quality": 0.35,
            "educational_quality": 0.35,
            "user_experience": 0.30,
        }

        # Phase weights within technical quality
        self.technical_weights = {
            "html_js": 0.25,
            "scientific_accuracy": 0.25,
            "realism": 0.25,
            "runtime_performance": 0.25,
        }

        # Educational quality components
        self.educational_weights = {
            "accuracy": 0.40,
            "appropriateness": 0.30,
            "coverage": 0.30,
        }

        # User experience components
        self.ux_weights = {
            "performance": 0.40,
            "visual_quality": 0.35,
            "reliability": 0.25,
        }

        # Issue severity weights
        self.issue_weights = {
            "critical": -2.0,
            "major": -1.0,
            "minor": -0.3,
            "warning": -0.1,
        }

        # Quality history for trend analysis
        self.quality_history: Dict[str, List[Tuple[float, float]]] = {}

    def calculate_comprehensive_score(
        self,
        html_result: Optional[Dict] = None,
        scientific_result: Optional[Dict] = None,
        realism_result: Optional[Dict] = None,
        runtime_result: Optional[Dict] = None,
        content_metadata: Optional[Dict] = None,
    ) -> QualityResult:
        """
        Calculate comprehensive quality score from all validation phases.

        Args:
            html_result: Results from HTML/JS validation
            scientific_result: Results from scientific accuracy validation
            realism_result: Results from realism validation
            runtime_result: Results from runtime validation
            content_metadata: Additional content metadata

        Returns:
            QualityResult with comprehensive quality assessment
        """

        # Extract metadata
        content_id = (
            content_metadata.get("id", "unknown") if content_metadata else "unknown"
        )
        title = (
            content_metadata.get("title", "Untitled")
            if content_metadata
            else "Untitled"
        )
        subject = (
            content_metadata.get("subject", "general")
            if content_metadata
            else "general"
        )
        education_level = (
            content_metadata.get("education_level", "unknown")
            if content_metadata
            else "unknown"
        )

        # Calculate phase-specific scores
        html_js_score = self._calculate_html_js_score(html_result)
        scientific_score = self._calculate_scientific_score(scientific_result)
        realism_score = self._calculate_realism_score(realism_result)
        runtime_score = self._calculate_runtime_score(runtime_result)

        # Calculate composite scores
        technical_score = self._calculate_technical_quality(
            html_js_score, scientific_score, realism_score, runtime_score
        )

        educational_score = self._calculate_educational_quality(
            scientific_result, realism_result, content_metadata
        )

        ux_score = self._calculate_user_experience_score(
            runtime_result, realism_result, html_result
        )

        # Calculate overall quality score
        overall_score = (
            technical_score * self.scoring_weights["technical_quality"]
            + educational_score * self.scoring_weights["educational_quality"]
            + ux_score * self.scoring_weights["user_experience"]
        )

        # Analyze issues across all phases
        issue_analysis = self._analyze_issues(
            html_result, scientific_result, realism_result, runtime_result
        )

        # Calculate detailed metrics
        metrics = self._calculate_detailed_metrics(
            overall_score,
            technical_score,
            educational_score,
            ux_score,
            html_js_score,
            scientific_score,
            realism_score,
            runtime_score,
            issue_analysis,
            html_result,
            scientific_result,
            realism_result,
            runtime_result,
        )

        # Generate feedback and recommendations
        feedback = self._generate_feedback(
            metrics, html_result, scientific_result, realism_result, runtime_result
        )

        # Analyze quality trends
        trend = self._analyze_quality_trend(content_id, overall_score)

        # Determine quality tier and recommendations
        quality_tier = self._determine_quality_tier(overall_score)
        passes_threshold = overall_score >= self.quality_thresholds["basic"]
        recommended_for_use = overall_score >= self.quality_thresholds["standard"]
        requires_review = (
            overall_score < self.quality_thresholds["standard"]
            or issue_analysis["critical_issues"] > 0
        )

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(
            html_result, scientific_result, realism_result, runtime_result
        )

        return QualityResult(
            content_id=content_id,
            title=title,
            subject=subject,
            education_level=education_level,
            metrics=metrics,
            feedback=feedback,
            trend=trend,
            validation_timestamp=import_time(),
            validation_duration=0.0,  # Would be calculated by orchestrator
            passes_quality_threshold=passes_threshold,
            recommended_for_use=recommended_for_use,
            requires_review=requires_review,
            quality_tier=quality_tier,
            confidence_level=confidence_level,
        )

    def _calculate_html_js_score(self, result: Optional[Dict]) -> float:
        """Calculate HTML/JS validation score."""
        if not result:
            return 0.0

        # Base score from validation result
        base_score = result.get("overall_score", 0.0)

        # Adjust for specific issues
        syntax_errors = len(result.get("syntax_errors", []))
        api_errors = len(result.get("api_errors", []))

        # Penalty for errors
        penalty = min(5.0, syntax_errors * 0.5 + api_errors * 0.3)

        return max(0.0, min(10.0, base_score - penalty))

    def _calculate_scientific_score(self, result: Optional[Dict]) -> float:
        """Calculate scientific accuracy score."""
        if not result:
            return 0.0

        # Extract scores from scientific validation
        accuracy_score = result.get("accuracy_score", 0.0)
        unit_score = result.get("unit_compliance_score", 0.0)
        formula_score = result.get("formula_accuracy_score", 0.0)
        concept_score = result.get("concept_alignment_score", 0.0)

        # Weighted average
        return (
            accuracy_score * 0.4
            + unit_score * 0.2
            + formula_score * 0.2
            + concept_score * 0.2
        )

    def _calculate_realism_score(self, result: Optional[Dict]) -> float:
        """Calculate realism validation score."""
        if not result:
            return 0.0

        # Extract scores from realism validation
        overall_score = result.get("overall_realism_score", 0.0)
        material_score = result.get("material_realism_score", 0.0)
        lighting_score = result.get("lighting_quality_score", 0.0)
        scale_score = result.get("scale_accuracy_score", 0.0)

        # Weighted average
        return (
            overall_score * 0.4
            + material_score * 0.2
            + lighting_score * 0.2
            + scale_score * 0.2
        )

    def _calculate_runtime_score(self, result: Optional[Dict]) -> float:
        """Calculate runtime validation score."""
        if not result:
            return 0.0

        # Extract scores from runtime validation
        overall_score = result.get("overall_runtime_score", 0.0)
        performance_score = result.get("performance_score", 0.0)
        rendering_score = result.get("rendering_score", 0.0)

        # Weighted average
        return overall_score * 0.5 + performance_score * 0.3 + rendering_score * 0.2

    def _calculate_technical_quality(
        self, html_js: float, scientific: float, realism: float, runtime: float
    ) -> float:
        """Calculate overall technical quality score."""
        return (
            html_js * self.technical_weights["html_js"]
            + scientific * self.technical_weights["scientific_accuracy"]
            + realism * self.technical_weights["realism"]
            + runtime * self.technical_weights["runtime_performance"]
        )

    def _calculate_educational_quality(
        self,
        scientific_result: Optional[Dict],
        realism_result: Optional[Dict],
        metadata: Optional[Dict],
    ) -> float:
        """Calculate educational quality score."""

        # Scientific accuracy component
        accuracy_score = 0.0
        if scientific_result:
            accuracy_score = scientific_result.get("accuracy_score", 0.0)

        # Age appropriateness
        appropriateness_score = 8.0  # Default assumption
        if scientific_result:
            education_issues = len(scientific_result.get("education_level_issues", []))
            appropriateness_score = max(0.0, 10.0 - education_issues * 1.0)

        # Topic coverage
        coverage_score = 7.0  # Default assumption
        if scientific_result:
            detected_concepts = len(scientific_result.get("detected_concepts", []))
            coverage_score = min(10.0, max(5.0, detected_concepts * 2.0))

        return (
            accuracy_score * self.educational_weights["accuracy"]
            + appropriateness_score * self.educational_weights["appropriateness"]
            + coverage_score * self.educational_weights["coverage"]
        )

    def _calculate_user_experience_score(
        self,
        runtime_result: Optional[Dict],
        realism_result: Optional[Dict],
        html_result: Optional[Dict],
    ) -> float:
        """Calculate user experience score."""

        # Performance component
        performance_score = 7.0  # Default
        if runtime_result:
            performance_score = runtime_result.get("performance_score", 7.0)

        # Visual quality component
        visual_score = 7.0  # Default
        if realism_result:
            visual_score = realism_result.get("overall_realism_score", 7.0)

        # Reliability component
        reliability_score = 8.0  # Default
        if runtime_result:
            execution_success = runtime_result.get("execution_successful", True)
            reliability_score = 9.0 if execution_success else 3.0

            # Adjust for errors
            if runtime_result.get("issues"):
                critical_issues = len(
                    [i for i in runtime_result["issues"] if i.get("severity", 0) >= 4]
                )
                reliability_score = max(0.0, reliability_score - critical_issues * 2.0)

        return (
            performance_score * self.ux_weights["performance"]
            + visual_score * self.ux_weights["visual_quality"]
            + reliability_score * self.ux_weights["reliability"]
        )

    def _analyze_issues(self, *results) -> Dict[str, int]:
        """Analyze issues across all validation phases."""
        issue_counts = {
            "critical_issues": 0,
            "major_issues": 0,
            "minor_issues": 0,
            "warnings": 0,
        }

        for result in results:
            if not result:
                continue

            issues = result.get("issues", [])
            for issue in issues:
                severity = issue.get("severity", 1)
                if severity >= 4:
                    issue_counts["critical_issues"] += 1
                elif severity >= 3:
                    issue_counts["major_issues"] += 1
                elif severity >= 2:
                    issue_counts["minor_issues"] += 1
                else:
                    issue_counts["warnings"] += 1

        return issue_counts

    def _calculate_detailed_metrics(
        self,
        overall_score: float,
        technical_score: float,
        educational_score: float,
        ux_score: float,
        html_js_score: float,
        scientific_score: float,
        realism_score: float,
        runtime_score: float,
        issue_analysis: Dict[str, int],
        *results,
    ) -> QualityMetrics:
        """Calculate detailed quality metrics."""

        # Extract detailed component scores
        html_result, scientific_result, realism_result, runtime_result = results

        # Syntax and API compliance
        syntax_correctness = html_js_score
        api_compliance = html_js_score

        # Scientific accuracy components
        unit_accuracy = (
            scientific_result.get("unit_compliance_score", 0.0)
            if scientific_result
            else 0.0
        )
        formula_correctness = (
            scientific_result.get("formula_accuracy_score", 0.0)
            if scientific_result
            else 0.0
        )
        concept_alignment = (
            scientific_result.get("concept_alignment_score", 0.0)
            if scientific_result
            else 0.0
        )

        # Realism components
        material_realism = (
            realism_result.get("material_realism_score", 0.0) if realism_result else 0.0
        )
        lighting_quality = (
            realism_result.get("lighting_quality_score", 0.0) if realism_result else 0.0
        )

        # Runtime components
        load_performance = (
            runtime_result.get("performance_score", 0.0) if runtime_result else 0.0
        )
        rendering_quality = (
            runtime_result.get("rendering_score", 0.0) if runtime_result else 0.0
        )

        # Educational effectiveness
        age_appropriateness = 8.0  # Default
        topic_coverage = 7.0  # Default
        learning_objectives_met = 7.5  # Default

        # Technical reliability
        browser_compatibility = 8.0  # Default
        performance_consistency = load_performance
        error_resilience = max(0.0, 10.0 - issue_analysis["critical_issues"] * 2.0)

        return QualityMetrics(
            overall_quality_score=overall_score,
            technical_quality_score=technical_score,
            educational_quality_score=educational_score,
            user_experience_score=ux_score,
            html_js_score=html_js_score,
            scientific_accuracy_score=scientific_score,
            realism_score=realism_score,
            runtime_performance_score=runtime_score,
            syntax_correctness=syntax_correctness,
            api_compliance=api_compliance,
            unit_accuracy=unit_accuracy,
            formula_correctness=formula_correctness,
            concept_alignment=concept_alignment,
            material_realism=material_realism,
            lighting_quality=lighting_quality,
            load_performance=load_performance,
            rendering_quality=rendering_quality,
            critical_issues=issue_analysis["critical_issues"],
            major_issues=issue_analysis["major_issues"],
            minor_issues=issue_analysis["minor_issues"],
            warnings=issue_analysis["warnings"],
            age_appropriateness=age_appropriateness,
            topic_coverage=topic_coverage,
            learning_objectives_met=learning_objectives_met,
            browser_compatibility=browser_compatibility,
            performance_consistency=performance_consistency,
            error_resilience=error_resilience,
        )

    def _generate_feedback(self, metrics: QualityMetrics, *results) -> QualityFeedback:
        """Generate comprehensive feedback and recommendations."""

        html_result, scientific_result, realism_result, runtime_result = results

        # Score breakdown
        score_breakdown = {
            "Overall Quality": metrics.overall_quality_score,
            "Technical Quality": metrics.technical_quality_score,
            "Educational Quality": metrics.educational_quality_score,
            "User Experience": metrics.user_experience_score,
            "HTML/JS Compliance": metrics.html_js_score,
            "Scientific Accuracy": metrics.scientific_accuracy_score,
            "Visual Realism": metrics.realism_score,
            "Runtime Performance": metrics.runtime_performance_score,
        }

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        critical_fixes = []
        improvement_suggestions = []
        educational_recommendations = []
        technical_recommendations = []
        priority_actions = []

        # Analyze each component
        if metrics.technical_quality_score >= 8.0:
            strengths.append("Excellent technical implementation")
        elif metrics.technical_quality_score < 6.0:
            weaknesses.append("Technical implementation needs improvement")
            technical_recommendations.append(
                "Review HTML/JS code quality and Three.js usage"
            )

        if metrics.educational_quality_score >= 8.0:
            strengths.append("High educational value and accuracy")
        elif metrics.educational_quality_score < 6.0:
            weaknesses.append("Educational content quality needs improvement")
            educational_recommendations.append(
                "Verify scientific accuracy and age appropriateness"
            )

        if metrics.user_experience_score >= 8.0:
            strengths.append("Excellent user experience")
        elif metrics.user_experience_score < 6.0:
            weaknesses.append("User experience needs enhancement")
            improvement_suggestions.append("Optimize performance and visual quality")

        # Critical issues
        if metrics.critical_issues > 0:
            critical_fixes.append(
                f"Fix {metrics.critical_issues} critical issues immediately"
            )
            priority_actions.append(("Fix critical issues", 5))

        # Performance issues
        if metrics.load_performance < 6.0:
            improvement_suggestions.append("Optimize loading performance")
            priority_actions.append(("Improve performance", 4))

        # Scientific accuracy issues
        if metrics.scientific_accuracy_score < 7.0:
            educational_recommendations.append(
                "Review scientific accuracy and unit compliance"
            )
            priority_actions.append(("Verify scientific content", 4))

        # Rendering issues
        if metrics.rendering_quality < 6.0:
            technical_recommendations.append("Fix rendering and WebGL issues")
            priority_actions.append(("Fix rendering issues", 3))

        # Sort priority actions by priority
        priority_actions.sort(key=lambda x: x[1], reverse=True)

        return QualityFeedback(
            score_breakdown=score_breakdown,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_fixes=critical_fixes,
            improvement_suggestions=improvement_suggestions,
            educational_recommendations=educational_recommendations,
            technical_recommendations=technical_recommendations,
            priority_actions=priority_actions,
        )

    def _analyze_quality_trend(
        self, content_id: str, current_score: float
    ) -> QualityTrend:
        """Analyze quality trends over time."""
        import time

        current_time = time.time()

        # Get or create history for this content
        if content_id not in self.quality_history:
            self.quality_history[content_id] = []

        history = self.quality_history[content_id]

        # Add current score
        history.append((current_time, current_score))

        # Keep only recent history (last 30 entries)
        history = history[-30:]
        self.quality_history[content_id] = history

        # Analyze trend
        if len(history) < 2:
            return QualityTrend(
                current_score=current_score,
                previous_score=None,
                trend_direction="stable",
                trend_strength=0.0,
                improvement_rate=0.0,
                consistency_score=1.0,
                score_history=[current_score],
                timestamp_history=[current_time],
            )

        scores = [score for _, score in history]
        timestamps = [ts for ts, _ in history]

        previous_score = scores[-2]

        # Calculate trend
        if len(scores) >= 3:
            recent_scores = scores[-5:]  # Last 5 scores
            trend_slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)

            if trend_slope > 0.2:
                trend_direction = "improving"
                trend_strength = min(1.0, abs(trend_slope) / 2.0)
            elif trend_slope < -0.2:
                trend_direction = "declining"
                trend_strength = min(1.0, abs(trend_slope) / 2.0)
            else:
                trend_direction = "stable"
                trend_strength = 0.0
        else:
            trend_direction = "stable"
            trend_strength = 0.0

        # Calculate improvement rate
        if len(scores) >= 2:
            time_diff = timestamps[-1] - timestamps[0]
            score_diff = scores[-1] - scores[0]
            improvement_rate = score_diff / (time_diff / 86400)  # Per day
        else:
            improvement_rate = 0.0

        # Calculate consistency
        if len(scores) >= 3:
            score_variance = statistics.variance(scores)
            consistency_score = max(0.0, 1.0 - score_variance / 10.0)
        else:
            consistency_score = 1.0

        return QualityTrend(
            current_score=current_score,
            previous_score=previous_score,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            improvement_rate=improvement_rate,
            consistency_score=consistency_score,
            score_history=scores,
            timestamp_history=timestamps,
        )

    def _determine_quality_tier(self, score: float) -> str:
        """Determine quality tier based on score."""
        if score >= self.quality_thresholds["premium"]:
            return "premium"
        elif score >= self.quality_thresholds["standard"]:
            return "standard"
        elif score >= self.quality_thresholds["basic"]:
            return "basic"
        else:
            return "rejected"

    def _calculate_confidence_level(self, *results) -> float:
        """Calculate confidence level in the quality assessment."""
        confidence = 1.0

        # Reduce confidence if validation phases are missing
        valid_results = sum(1 for result in results if result is not None)
        total_phases = len(results)

        if valid_results < total_phases:
            confidence *= valid_results / total_phases

        # Reduce confidence for incomplete data
        for result in results:
            if result is None:
                continue

            # Check if result has minimal required data
            if not result.get("success", True):
                confidence *= 0.8

            # Check for validation errors
            if result.get("validation_errors", 0) > 0:
                confidence *= 0.9

        return max(0.1, min(1.0, confidence))

    def get_quality_summary(self, result: QualityResult) -> str:
        """Generate a human-readable quality summary."""
        lines = []

        # Header
        lines.append(f"🎯 Quality Assessment: {result.title}")
        lines.append(f"📚 Subject: {result.subject} | Level: {result.education_level}")
        lines.append(
            f"🏆 Overall Score: {result.metrics.overall_quality_score:.1f}/10 ({result.quality_tier.upper()})"
        )
        lines.append("")

        # Score breakdown
        lines.append("📊 Score Breakdown:")
        lines.append(
            f"   Technical Quality: {result.metrics.technical_quality_score:.1f}/10"
        )
        lines.append(
            f"   Educational Quality: {result.metrics.educational_quality_score:.1f}/10"
        )
        lines.append(
            f"   User Experience: {result.metrics.user_experience_score:.1f}/10"
        )
        lines.append("")

        # Status
        status_emoji = (
            "✅"
            if result.recommended_for_use
            else "⚠️"
            if result.passes_quality_threshold
            else "❌"
        )
        lines.append(
            f"{status_emoji} Status: {'Recommended' if result.recommended_for_use else 'Needs Review' if result.passes_quality_threshold else 'Rejected'}"
        )
        lines.append(f"🔍 Confidence: {result.confidence_level:.1%}")
        lines.append("")

        # Issues
        if result.metrics.critical_issues > 0:
            lines.append(f"🔴 Critical Issues: {result.metrics.critical_issues}")
        if result.metrics.major_issues > 0:
            lines.append(f"🟡 Major Issues: {result.metrics.major_issues}")
        if result.metrics.minor_issues > 0:
            lines.append(f"ℹ️ Minor Issues: {result.metrics.minor_issues}")

        # Strengths and weaknesses
        if result.feedback.strengths:
            lines.append("✨ Strengths:")
            for strength in result.feedback.strengths[:3]:
                lines.append(f"   • {strength}")

        if result.feedback.weaknesses:
            lines.append("⚠️ Areas for Improvement:")
            for weakness in result.feedback.weaknesses[:3]:
                lines.append(f"   • {weakness}")

        # Priority actions
        if result.feedback.priority_actions:
            lines.append("🎯 Priority Actions:")
            for action, priority in result.feedback.priority_actions[:3]:
                priority_emoji = (
                    "🔥" if priority >= 4 else "⚡" if priority >= 3 else "📌"
                )
                lines.append(f"   {priority_emoji} {action}")

        return "\n".join(lines)


def import_time():
    """Import time function - placeholder for actual time import."""
    import time

    return time.time()
