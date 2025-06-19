"""
Quality-Based Context Filtering System

This module provides intelligent context filtering based on quality assessments,
allowing the system to prioritize high-quality examples and patterns while
filtering out low-quality content for training and generation contexts.
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextItem:
    """Represents a context item with quality metadata."""

    item_id: str
    content: str
    quality_score: float
    quality_tier: str
    subject: str
    education_level: str
    content_type: str

    # Quality breakdown
    technical_score: float
    educational_score: float
    ux_score: float

    # Metadata
    timestamp: float
    usage_count: int
    success_rate: float

    # Context relevance
    relevance_score: float
    similarity_score: float

    # Tags and categorization
    tags: List[str]
    keywords: List[str]
    concepts: List[str]


@dataclass
class FilterCriteria:
    """Criteria for filtering context items."""

    min_quality_score: float = 7.0
    max_quality_score: float = 10.0

    # Quality tiers to include
    allowed_tiers: List[str] = None

    # Subject and level filtering
    subjects: List[str] = None
    education_levels: List[str] = None
    content_types: List[str] = None

    # Performance filtering
    min_success_rate: float = 0.0
    min_usage_count: int = 0

    # Relevance filtering
    min_relevance_score: float = 0.0
    min_similarity_score: float = 0.0

    # Diversity requirements
    ensure_diversity: bool = True
    max_similar_items: int = 3

    # Temporal filtering
    max_age_days: Optional[float] = None
    prefer_recent: bool = True


@dataclass
class FilterResult:
    """Result of context filtering operation."""

    filtered_items: List[ContextItem]
    total_items_considered: int
    items_filtered_out: int
    filtering_stats: Dict[str, Any]

    # Quality statistics
    average_quality: float
    quality_distribution: Dict[str, int]

    # Diversity metrics
    subject_diversity: int
    level_diversity: int
    concept_coverage: int

    # Recommendations
    filtering_effectiveness: float
    recommendations: List[str]


class ContextFilter:
    """Quality-based context filtering system."""

    def __init__(self):
        """Initialize the context filter."""

        # Filter configuration
        self.default_criteria = FilterCriteria(
            min_quality_score=7.0,
            allowed_tiers=["premium", "standard"],
            ensure_diversity=True,
            max_similar_items=3,
            prefer_recent=True,
        )

        # Quality thresholds for different use cases
        self.use_case_thresholds = {
            "training": {"min_quality": 8.0, "tiers": ["premium"]},
            "examples": {"min_quality": 7.5, "tiers": ["premium", "standard"]},
            "reference": {"min_quality": 7.0, "tiers": ["premium", "standard"]},
            "debugging": {
                "min_quality": 0.0,
                "tiers": ["premium", "standard", "basic", "rejected"],
            },
        }

        # Similarity calculation cache
        self.similarity_cache = {}

        # Filter statistics
        self.filter_stats = {
            "total_filters_applied": 0,
            "items_processed": 0,
            "average_filter_effectiveness": 0.0,
            "common_filter_reasons": defaultdict(int),
        }

    def filter_context(
        self,
        context_items: List[ContextItem],
        criteria: Optional[FilterCriteria] = None,
        use_case: str = "examples",
        target_count: Optional[int] = None,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> FilterResult:
        """
        Filter context items based on quality and relevance criteria.

        Args:
            context_items: List of context items to filter
            criteria: Filtering criteria (uses defaults if None)
            use_case: Use case for filtering ("training", "examples", "reference", "debugging")
            target_count: Target number of items to return
            request_context: Context of the current request for relevance scoring

        Returns:
            FilterResult with filtered items and statistics
        """

        if not context_items:
            return FilterResult(
                filtered_items=[],
                total_items_considered=0,
                items_filtered_out=0,
                filtering_stats={},
                average_quality=0.0,
                quality_distribution={},
                subject_diversity=0,
                level_diversity=0,
                concept_coverage=0,
                filtering_effectiveness=0.0,
                recommendations=[],
            )

        # Use appropriate criteria
        if criteria is None:
            criteria = self._get_criteria_for_use_case(use_case)

        # Update relevance scores if request context provided
        if request_context:
            context_items = self._update_relevance_scores(
                context_items, request_context
            )

        # Apply filtering stages
        stage_results = {}

        # Stage 1: Quality filtering
        quality_filtered = self._apply_quality_filter(context_items, criteria)
        stage_results["quality_filter"] = {
            "items_remaining": len(quality_filtered),
            "items_removed": len(context_items) - len(quality_filtered),
        }

        # Stage 2: Relevance filtering
        relevance_filtered = self._apply_relevance_filter(quality_filtered, criteria)
        stage_results["relevance_filter"] = {
            "items_remaining": len(relevance_filtered),
            "items_removed": len(quality_filtered) - len(relevance_filtered),
        }

        # Stage 3: Diversity filtering
        diversity_filtered = self._apply_diversity_filter(relevance_filtered, criteria)
        stage_results["diversity_filter"] = {
            "items_remaining": len(diversity_filtered),
            "items_removed": len(relevance_filtered) - len(diversity_filtered),
        }

        # Stage 4: Performance filtering
        performance_filtered = self._apply_performance_filter(
            diversity_filtered, criteria
        )
        stage_results["performance_filter"] = {
            "items_remaining": len(performance_filtered),
            "items_removed": len(diversity_filtered) - len(performance_filtered),
        }

        # Stage 5: Temporal filtering
        temporal_filtered = self._apply_temporal_filter(performance_filtered, criteria)
        stage_results["temporal_filter"] = {
            "items_remaining": len(temporal_filtered),
            "items_removed": len(performance_filtered) - len(temporal_filtered),
        }

        # Stage 6: Final ranking and selection
        final_items = self._rank_and_select(temporal_filtered, criteria, target_count)
        stage_results["final_selection"] = {
            "items_remaining": len(final_items),
            "items_removed": len(temporal_filtered) - len(final_items),
        }

        # Calculate statistics
        filter_stats = self._calculate_filter_stats(stage_results)
        quality_stats = self._calculate_quality_stats(final_items)
        diversity_stats = self._calculate_diversity_stats(final_items)

        # Generate recommendations
        recommendations = self._generate_filter_recommendations(
            context_items, final_items, criteria, stage_results
        )

        # Update global statistics
        self._update_global_stats(len(context_items), len(final_items), filter_stats)

        return FilterResult(
            filtered_items=final_items,
            total_items_considered=len(context_items),
            items_filtered_out=len(context_items) - len(final_items),
            filtering_stats=filter_stats,
            average_quality=quality_stats["average_quality"],
            quality_distribution=quality_stats["distribution"],
            subject_diversity=diversity_stats["subject_diversity"],
            level_diversity=diversity_stats["level_diversity"],
            concept_coverage=diversity_stats["concept_coverage"],
            filtering_effectiveness=filter_stats.get("effectiveness", 0.0),
            recommendations=recommendations,
        )

    def _get_criteria_for_use_case(self, use_case: str) -> FilterCriteria:
        """Get filtering criteria for specific use case."""

        base_criteria = FilterCriteria()

        if use_case in self.use_case_thresholds:
            thresholds = self.use_case_thresholds[use_case]
            base_criteria.min_quality_score = thresholds["min_quality"]
            base_criteria.allowed_tiers = thresholds["tiers"]

        # Use case specific adjustments
        if use_case == "training":
            base_criteria.min_success_rate = 0.8
            base_criteria.ensure_diversity = True
            base_criteria.max_similar_items = 2

        elif use_case == "examples":
            base_criteria.min_success_rate = 0.6
            base_criteria.ensure_diversity = True
            base_criteria.prefer_recent = True

        elif use_case == "reference":
            base_criteria.min_success_rate = 0.5
            base_criteria.ensure_diversity = False
            base_criteria.prefer_recent = False

        elif use_case == "debugging":
            base_criteria.min_quality_score = 0.0
            base_criteria.min_success_rate = 0.0
            base_criteria.ensure_diversity = False
            base_criteria.allowed_tiers = ["premium", "standard", "basic", "rejected"]

        return base_criteria

    def _update_relevance_scores(
        self, context_items: List[ContextItem], request_context: Dict[str, Any]
    ) -> List[ContextItem]:
        """Update relevance scores based on request context."""

        request_subject = request_context.get("subject", "")
        request_level = request_context.get("education_level", "")
        request_keywords = request_context.get("keywords", [])
        request_concepts = request_context.get("concepts", [])

        for item in context_items:
            relevance_score = 0.0

            # Subject relevance
            if item.subject == request_subject:
                relevance_score += 0.3
            elif request_subject in item.tags:
                relevance_score += 0.2

            # Education level relevance
            if item.education_level == request_level:
                relevance_score += 0.2

            # Keyword relevance
            if request_keywords:
                keyword_matches = len(set(request_keywords) & set(item.keywords))
                relevance_score += min(0.3, keyword_matches * 0.1)

            # Concept relevance
            if request_concepts:
                concept_matches = len(set(request_concepts) & set(item.concepts))
                relevance_score += min(0.2, concept_matches * 0.05)

            item.relevance_score = min(1.0, relevance_score)

        return context_items

    def _apply_quality_filter(
        self, items: List[ContextItem], criteria: FilterCriteria
    ) -> List[ContextItem]:
        """Apply quality-based filtering."""

        filtered_items = []

        for item in items:
            # Quality score filter
            if not (
                criteria.min_quality_score
                <= item.quality_score
                <= criteria.max_quality_score
            ):
                continue

            # Quality tier filter
            if (
                criteria.allowed_tiers
                and item.quality_tier not in criteria.allowed_tiers
            ):
                continue

            # Subject filter
            if criteria.subjects and item.subject not in criteria.subjects:
                continue

            # Education level filter
            if (
                criteria.education_levels
                and item.education_level not in criteria.education_levels
            ):
                continue

            # Content type filter
            if (
                criteria.content_types
                and item.content_type not in criteria.content_types
            ):
                continue

            filtered_items.append(item)

        return filtered_items

    def _apply_relevance_filter(
        self, items: List[ContextItem], criteria: FilterCriteria
    ) -> List[ContextItem]:
        """Apply relevance-based filtering."""

        filtered_items = []

        for item in items:
            # Relevance score filter
            if item.relevance_score < criteria.min_relevance_score:
                continue

            # Similarity score filter
            if item.similarity_score < criteria.min_similarity_score:
                continue

            filtered_items.append(item)

        return filtered_items

    def _apply_diversity_filter(
        self, items: List[ContextItem], criteria: FilterCriteria
    ) -> List[ContextItem]:
        """Apply diversity-based filtering."""

        if not criteria.ensure_diversity:
            return items

        # Group items by similarity
        similarity_groups = self._group_by_similarity(items)

        filtered_items = []

        for group in similarity_groups:
            # Sort group by quality and relevance
            group.sort(key=lambda x: (x.quality_score, x.relevance_score), reverse=True)

            # Take top items from each group
            selected_count = min(len(group), criteria.max_similar_items)
            filtered_items.extend(group[:selected_count])

        return filtered_items

    def _apply_performance_filter(
        self, items: List[ContextItem], criteria: FilterCriteria
    ) -> List[ContextItem]:
        """Apply performance-based filtering."""

        filtered_items = []

        for item in items:
            # Success rate filter
            if item.success_rate < criteria.min_success_rate:
                continue

            # Usage count filter
            if item.usage_count < criteria.min_usage_count:
                continue

            filtered_items.append(item)

        return filtered_items

    def _apply_temporal_filter(
        self, items: List[ContextItem], criteria: FilterCriteria
    ) -> List[ContextItem]:
        """Apply temporal filtering."""

        import time

        if not criteria.max_age_days:
            return items

        current_time = time.time()
        max_age_seconds = criteria.max_age_days * 24 * 60 * 60

        filtered_items = []

        for item in items:
            age_seconds = current_time - item.timestamp
            if age_seconds <= max_age_seconds:
                filtered_items.append(item)

        return filtered_items

    def _rank_and_select(
        self,
        items: List[ContextItem],
        criteria: FilterCriteria,
        target_count: Optional[int],
    ) -> List[ContextItem]:
        """Rank items and select final set."""

        # Calculate composite scores
        for item in items:
            composite_score = (
                item.quality_score * 0.4
                + item.relevance_score * 0.3
                + item.success_rate * 10 * 0.2
                + min(item.usage_count / 10, 1.0) * 0.1
            )

            # Boost recent items if preferred
            if criteria.prefer_recent:
                import time

                age_days = (time.time() - item.timestamp) / (24 * 60 * 60)
                recency_boost = max(0, 1.0 - age_days / 365) * 0.1
                composite_score += recency_boost

            item.similarity_score = composite_score  # Reuse field for composite score

        # Sort by composite score
        items.sort(key=lambda x: x.similarity_score, reverse=True)

        # Select target count
        if target_count:
            return items[:target_count]

        return items

    def _group_by_similarity(self, items: List[ContextItem]) -> List[List[ContextItem]]:
        """Group items by similarity."""

        groups = []
        used_items = set()

        for item in items:
            if item.item_id in used_items:
                continue

            # Create new group
            group = [item]
            used_items.add(item.item_id)

            # Find similar items
            for other_item in items:
                if other_item.item_id in used_items:
                    continue

                similarity = self._calculate_similarity(item, other_item)
                if similarity > 0.7:  # High similarity threshold
                    group.append(other_item)
                    used_items.add(other_item.item_id)

            groups.append(group)

        return groups

    def _calculate_similarity(self, item1: ContextItem, item2: ContextItem) -> float:
        """Calculate similarity between two context items."""

        # Use cache if available
        cache_key = f"{item1.item_id}_{item2.item_id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]

        similarity = 0.0

        # Subject similarity
        if item1.subject == item2.subject:
            similarity += 0.3

        # Education level similarity
        if item1.education_level == item2.education_level:
            similarity += 0.2

        # Content type similarity
        if item1.content_type == item2.content_type:
            similarity += 0.1

        # Keyword similarity
        if item1.keywords and item2.keywords:
            common_keywords = len(set(item1.keywords) & set(item2.keywords))
            total_keywords = len(set(item1.keywords) | set(item2.keywords))
            if total_keywords > 0:
                similarity += (common_keywords / total_keywords) * 0.2

        # Concept similarity
        if item1.concepts and item2.concepts:
            common_concepts = len(set(item1.concepts) & set(item2.concepts))
            total_concepts = len(set(item1.concepts) | set(item2.concepts))
            if total_concepts > 0:
                similarity += (common_concepts / total_concepts) * 0.2

        # Cache result
        self.similarity_cache[cache_key] = similarity

        return similarity

    def _calculate_filter_stats(self, stage_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate filtering statistics."""

        total_removed = sum(stage["items_removed"] for stage in stage_results.values())
        final_remaining = stage_results["final_selection"]["items_remaining"]

        # Calculate effectiveness
        if total_removed + final_remaining > 0:
            effectiveness = final_remaining / (total_removed + final_remaining)
        else:
            effectiveness = 0.0

        return {
            "stage_results": stage_results,
            "total_items_removed": total_removed,
            "effectiveness": effectiveness,
            "stages_applied": len(stage_results),
        }

    def _calculate_quality_stats(self, items: List[ContextItem]) -> Dict[str, Any]:
        """Calculate quality statistics for filtered items."""

        if not items:
            return {"average_quality": 0.0, "distribution": {}}

        scores = [item.quality_score for item in items]
        tiers = [item.quality_tier for item in items]

        # Quality distribution
        tier_counts = defaultdict(int)
        for tier in tiers:
            tier_counts[tier] += 1

        return {
            "average_quality": statistics.mean(scores),
            "distribution": dict(tier_counts),
        }

    def _calculate_diversity_stats(self, items: List[ContextItem]) -> Dict[str, int]:
        """Calculate diversity statistics."""

        if not items:
            return {"subject_diversity": 0, "level_diversity": 0, "concept_coverage": 0}

        subjects = set(item.subject for item in items)
        levels = set(item.education_level for item in items)

        all_concepts = set()
        for item in items:
            all_concepts.update(item.concepts)

        return {
            "subject_diversity": len(subjects),
            "level_diversity": len(levels),
            "concept_coverage": len(all_concepts),
        }

    def _generate_filter_recommendations(
        self,
        original_items: List[ContextItem],
        filtered_items: List[ContextItem],
        criteria: FilterCriteria,
        stage_results: Dict[str, Dict],
    ) -> List[str]:
        """Generate recommendations for filter improvement."""

        recommendations = []

        # Check filter effectiveness
        if len(filtered_items) == 0:
            recommendations.append("Filter criteria too restrictive - no items passed")
            recommendations.append(
                "Consider lowering quality thresholds or expanding allowed tiers"
            )
        elif len(filtered_items) == len(original_items):
            recommendations.append("Filter criteria too permissive - no items filtered")
            recommendations.append(
                "Consider raising quality thresholds or adding more restrictive criteria"
            )

        # Check diversity
        if criteria.ensure_diversity:
            subjects = set(item.subject for item in filtered_items)
            if len(subjects) < 2:
                recommendations.append(
                    "Low subject diversity - consider expanding subject criteria"
                )

        # Check quality distribution
        if filtered_items:
            avg_quality = statistics.mean(item.quality_score for item in filtered_items)
            if avg_quality < 7.0:
                recommendations.append(
                    "Average quality below recommended threshold - consider stricter quality filtering"
                )

        # Check stage effectiveness
        quality_removed = stage_results.get("quality_filter", {}).get(
            "items_removed", 0
        )
        if quality_removed > len(original_items) * 0.8:
            recommendations.append(
                "Quality filter removing too many items - consider adjusting thresholds"
            )

        return recommendations[:5]  # Limit to top 5 recommendations

    def _update_global_stats(self, items_in: int, items_out: int, filter_stats: Dict):
        """Update global filtering statistics."""

        self.filter_stats["total_filters_applied"] += 1
        self.filter_stats["items_processed"] += items_in

        # Update average effectiveness
        current_effectiveness = filter_stats.get("effectiveness", 0.0)
        total_filters = self.filter_stats["total_filters_applied"]

        if total_filters == 1:
            self.filter_stats["average_filter_effectiveness"] = current_effectiveness
        else:
            # Running average
            prev_avg = self.filter_stats["average_filter_effectiveness"]
            self.filter_stats["average_filter_effectiveness"] = (
                prev_avg * (total_filters - 1) + current_effectiveness
            ) / total_filters

    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of filtering statistics."""

        return {
            "total_filters_applied": self.filter_stats["total_filters_applied"],
            "total_items_processed": self.filter_stats["items_processed"],
            "average_effectiveness": self.filter_stats["average_filter_effectiveness"],
            "cache_size": len(self.similarity_cache),
            "use_case_configurations": len(self.use_case_thresholds),
        }

    def clear_cache(self):
        """Clear similarity calculation cache."""
        self.similarity_cache.clear()

    def add_use_case_config(self, use_case: str, config: Dict[str, Any]):
        """Add configuration for a new use case."""
        self.use_case_thresholds[use_case] = config
