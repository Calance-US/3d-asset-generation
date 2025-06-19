"""
Integrated Validation Orchestrator

This module provides a unified orchestrator that combines all validation phases
(HTML/JS, Scientific Accuracy, Realism, Runtime) with quality scoring, feedback
loops, and context filtering into a comprehensive validation pipeline.
"""

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationOrchestrator:
    """Integrated orchestrator for comprehensive 3D content validation."""

    def __init__(self):
        """Initialize the validation orchestrator."""

        # Import validators lazily to avoid circular imports
        self._html_validator = None
        self._scientific_validator = None
        self._realism_validator = None
        self._runtime_validator = None
        self._quality_scorer = None
        self._feedback_loop = None
        self._context_filter = None

        # Validation configuration
        self.config = {
            "phases": {
                "html_js": {"enabled": True, "timeout": 30, "critical": True},
                "scientific": {"enabled": True, "timeout": 60, "critical": True},
                "realism": {"enabled": True, "timeout": 45, "critical": False},
                "runtime": {"enabled": True, "timeout": 120, "critical": False},
            },
            "quality_scoring": {"enabled": True, "threshold": 7.0},
            "feedback_loop": {"enabled": True, "learning": True},
            "context_filtering": {"enabled": True, "use_case": "examples"},
            "parallel_execution": True,
            "fail_fast": False,
            "generate_reports": True,
        }

        # Performance tracking
        self.performance_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "average_validation_time": 0.0,
            "phase_performance": {
                "html_js": {"count": 0, "avg_time": 0.0, "success_rate": 0.0},
                "scientific": {"count": 0, "avg_time": 0.0, "success_rate": 0.0},
                "realism": {"count": 0, "avg_time": 0.0, "success_rate": 0.0},
                "runtime": {"count": 0, "avg_time": 0.0, "success_rate": 0.0},
            },
        }

    def _get_validators(self):
        """Lazy initialization of validators."""
        if self._html_validator is None:
            from .context_filter import ContextFilter
            from .feedback_loop import FeedbackLoop
            from .html_validator import HTMLValidator
            from .quality_scorer import QualityScorer
            from .realism_validator import RealismValidator
            from .runtime_validator import RuntimeValidator
            from .scientific_validator import ScientificValidator

            self._html_validator = HTMLValidator()
            self._scientific_validator = ScientificValidator()
            self._realism_validator = RealismValidator()
            self._runtime_validator = RuntimeValidator()
            self._quality_scorer = QualityScorer()
            self._feedback_loop = FeedbackLoop()
            self._context_filter = ContextFilter()

    async def validate_content(
        self,
        html_content: str,
        title: str = "3D Content",
        subject: str = "general",
        education_level: str = "high school",
        content_metadata: Optional[Dict[str, Any]] = None,
        validation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation of 3D educational content.

        Args:
            html_content: The HTML content to validate
            title: Title of the content
            subject: Subject area (physics, chemistry, biology, etc.)
            education_level: Target education level
            content_metadata: Additional metadata about the content
            validation_config: Configuration overrides for validation

        Returns:
            Comprehensive validation results with quality scores and recommendations
        """

        start_time = time.time()

        # Initialize validators
        self._get_validators()

        # Merge configuration
        config = self.config.copy()
        if validation_config:
            config.update(validation_config)

        # Prepare metadata
        if content_metadata is None:
            content_metadata = {}

        content_metadata.update(
            {
                "title": title,
                "subject": subject,
                "education_level": education_level,
                "validation_timestamp": start_time,
            }
        )

        validation_result = {
            "content_metadata": content_metadata,
            "validation_config": config,
            "validation_start_time": start_time,
            "phase_results": {},
            "quality_assessment": None,
            "feedback_processing": None,
            "overall_result": None,
            "recommendations": [],
            "validation_summary": {},
        }

        try:
            # Execute validation phases
            if config["parallel_execution"]:
                phase_results = await self._execute_phases_parallel(
                    html_content, title, subject, education_level, config
                )
            else:
                phase_results = await self._execute_phases_sequential(
                    html_content, title, subject, education_level, config
                )

            validation_result["phase_results"] = phase_results

            # Quality scoring
            if config["quality_scoring"]["enabled"]:
                quality_result = await self._perform_quality_scoring(
                    phase_results, content_metadata
                )
                validation_result["quality_assessment"] = quality_result

            # Feedback loop processing
            if config["feedback_loop"]["enabled"]:
                feedback_result = await self._process_feedback_loop(
                    validation_result["quality_assessment"]
                )
                validation_result["feedback_processing"] = feedback_result

            # Generate overall result
            overall_result = self._generate_overall_result(
                phase_results, validation_result.get("quality_assessment"), config
            )
            validation_result["overall_result"] = overall_result

            # Generate recommendations
            recommendations = self._generate_recommendations(validation_result)
            validation_result["recommendations"] = recommendations

            # Create validation summary
            validation_summary = self._create_validation_summary(validation_result)
            validation_result["validation_summary"] = validation_summary

            # Update performance metrics
            self._update_performance_metrics(validation_result, start_time)

            logger.info(
                f"Validation completed for '{title}' - "
                f"Overall Score: {overall_result.get('overall_score', 0):.1f}/10"
            )

        except Exception as e:
            logger.error(f"Validation failed for '{title}': {str(e)}")
            validation_result["error"] = str(e)
            validation_result["overall_result"] = {
                "success": False,
                "overall_score": 0.0,
                "critical_failure": True,
                "error_message": str(e),
            }

        finally:
            validation_result["validation_end_time"] = time.time()
            validation_result["validation_duration"] = (
                validation_result["validation_end_time"] - start_time
            )

        return validation_result

    async def _execute_phases_parallel(
        self,
        html_content: str,
        title: str,
        subject: str,
        education_level: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute validation phases in parallel."""

        tasks = []
        phase_configs = config["phases"]

        # HTML/JS validation
        if phase_configs["html_js"]["enabled"]:
            tasks.append(
                self._execute_html_validation(
                    html_content, title, phase_configs["html_js"]["timeout"]
                )
            )
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0, result=None)))

        # Scientific validation
        if phase_configs["scientific"]["enabled"]:
            tasks.append(
                self._execute_scientific_validation(
                    html_content,
                    title,
                    subject,
                    education_level,
                    phase_configs["scientific"]["timeout"],
                )
            )
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0, result=None)))

        # Realism validation
        if phase_configs["realism"]["enabled"]:
            tasks.append(
                self._execute_realism_validation(
                    html_content, title, subject, phase_configs["realism"]["timeout"]
                )
            )
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0, result=None)))

        # Runtime validation
        if phase_configs["runtime"]["enabled"]:
            tasks.append(
                self._execute_runtime_validation(
                    html_content, title, phase_configs["runtime"]["timeout"]
                )
            )
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0, result=None)))

        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "html_js": results[0] if not isinstance(results[0], Exception) else None,
            "scientific": results[1] if not isinstance(results[1], Exception) else None,
            "realism": results[2] if not isinstance(results[2], Exception) else None,
            "runtime": results[3] if not isinstance(results[3], Exception) else None,
        }

    async def _execute_phases_sequential(
        self,
        html_content: str,
        title: str,
        subject: str,
        education_level: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute validation phases sequentially."""

        phase_results = {}
        phase_configs = config["phases"]

        # HTML/JS validation (always first)
        if phase_configs["html_js"]["enabled"]:
            html_result = await self._execute_html_validation(
                html_content, title, phase_configs["html_js"]["timeout"]
            )
            phase_results["html_js"] = html_result

            # Check for critical failure
            if (
                config["fail_fast"]
                and phase_configs["html_js"]["critical"]
                and not html_result.get("success", False)
            ):
                logger.warning(
                    "Critical HTML/JS validation failure - stopping validation"
                )
                return phase_results

        # Scientific validation
        if phase_configs["scientific"]["enabled"]:
            scientific_result = await self._execute_scientific_validation(
                html_content,
                title,
                subject,
                education_level,
                phase_configs["scientific"]["timeout"],
            )
            phase_results["scientific"] = scientific_result

            # Check for critical failure
            if (
                config["fail_fast"]
                and phase_configs["scientific"]["critical"]
                and not scientific_result.get("is_scientifically_accurate", False)
            ):
                logger.warning(
                    "Critical scientific validation failure - stopping validation"
                )
                return phase_results

        # Realism validation
        if phase_configs["realism"]["enabled"]:
            realism_result = await self._execute_realism_validation(
                html_content, title, subject, phase_configs["realism"]["timeout"]
            )
            phase_results["realism"] = realism_result

        # Runtime validation
        if phase_configs["runtime"]["enabled"]:
            runtime_result = await self._execute_runtime_validation(
                html_content, title, phase_configs["runtime"]["timeout"]
            )
            phase_results["runtime"] = runtime_result

        return phase_results

    async def _execute_html_validation(
        self, html_content: str, title: str, timeout: int
    ) -> Optional[Dict[str, Any]]:
        """Execute HTML/JS validation phase."""
        try:
            if not self._html_validator:
                return {"success": False, "error": "HTML validator not initialized"}

            start_time = time.time()
            result = await asyncio.wait_for(
                self._html_validator.validate_html_content(html_content, title),
                timeout=timeout,
            )

            # Convert result to dict if needed
            if hasattr(result, "__dict__"):
                result = asdict(result)
            elif not isinstance(result, dict):
                result = {"success": False, "error": "Invalid result format"}

            result["validation_time"] = time.time() - start_time
            return result
        except asyncio.TimeoutError:
            return {"success": False, "error": f"HTML validation timeout ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": f"HTML validation error: {str(e)}"}

    async def _execute_scientific_validation(
        self,
        html_content: str,
        title: str,
        subject: str,
        education_level: str,
        timeout: int,
    ) -> Optional[Dict[str, Any]]:
        """Execute scientific accuracy validation phase."""
        try:
            if not self._scientific_validator:
                return {
                    "success": False,
                    "error": "Scientific validator not initialized",
                }

            start_time = time.time()
            result = await asyncio.wait_for(
                self._scientific_validator.validate_scientific_content(
                    html_content, title, subject, education_level
                ),
                timeout=timeout,
            )

            # Convert result to dict if needed
            if hasattr(result, "__dict__"):
                result = asdict(result)
            elif not isinstance(result, dict):
                result = {
                    "is_scientifically_accurate": False,
                    "error": "Invalid result format",
                }

            result["validation_time"] = time.time() - start_time
            return result
        except asyncio.TimeoutError:
            return {
                "is_scientifically_accurate": False,
                "error": f"Scientific validation timeout ({timeout}s)",
            }
        except Exception as e:
            return {
                "is_scientifically_accurate": False,
                "error": f"Scientific validation error: {str(e)}",
            }

    async def _execute_realism_validation(
        self, html_content: str, title: str, subject: str, timeout: int
    ) -> Optional[Dict[str, Any]]:
        """Execute realism validation phase."""
        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                self._realism_validator.validate_realism_content(
                    html_content, title, subject
                ),
                timeout=timeout,
            )

            # Convert result to dict if needed
            if hasattr(result, "__dict__"):
                result = asdict(result)
            elif not isinstance(result, dict):
                result = {"is_realistic": False, "error": "Invalid result format"}

            result["validation_time"] = time.time() - start_time
            return result
        except asyncio.TimeoutError:
            return {
                "is_realistic": False,
                "error": f"Realism validation timeout ({timeout}s)",
            }
        except Exception as e:
            return {
                "is_realistic": False,
                "error": f"Realism validation error: {str(e)}",
            }

    async def _execute_runtime_validation(
        self, html_content: str, title: str, timeout: int
    ) -> Optional[Dict[str, Any]]:
        """Execute runtime validation phase."""
        try:
            start_time = time.time()
            result = await asyncio.wait_for(
                self._runtime_validator.validate_runtime_content(
                    html_content, title, timeout=timeout
                ),
                timeout=timeout + 10,  # Extra buffer for runtime validation
            )

            # Convert result to dict if needed
            if hasattr(result, "__dict__"):
                result = asdict(result)
            elif not isinstance(result, dict):
                result = {"is_runtime_valid": False, "error": "Invalid result format"}

            result["validation_time"] = time.time() - start_time
            return result
        except asyncio.TimeoutError:
            return {
                "is_runtime_valid": False,
                "error": f"Runtime validation timeout ({timeout}s)",
            }
        except Exception as e:
            return {
                "is_runtime_valid": False,
                "error": f"Runtime validation error: {str(e)}",
            }

    async def _perform_quality_scoring(
        self, phase_results: Dict[str, Any], content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive quality scoring."""
        try:
            quality_result = self._quality_scorer.calculate_comprehensive_score(
                html_result=phase_results.get("html_js"),
                scientific_result=phase_results.get("scientific"),
                realism_result=phase_results.get("realism"),
                runtime_result=phase_results.get("runtime"),
                content_metadata=content_metadata,
            )

            # Convert to dict if needed
            if hasattr(quality_result, "__dict__"):
                return asdict(quality_result)

            return quality_result
        except Exception as e:
            logger.error(f"Quality scoring failed: {str(e)}")
            return {"error": f"Quality scoring error: {str(e)}"}

    async def _process_feedback_loop(
        self, quality_assessment: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process feedback loop for continuous improvement."""
        try:
            if not quality_assessment or "error" in quality_assessment:
                return {
                    "feedback_processed": False,
                    "error": "No valid quality assessment",
                }

            feedback_result = self._feedback_loop.process_quality_result(
                quality_assessment
            )
            return feedback_result
        except Exception as e:
            logger.error(f"Feedback loop processing failed: {str(e)}")
            return {"feedback_processed": False, "error": f"Feedback error: {str(e)}"}

    def _generate_overall_result(
        self,
        phase_results: Dict[str, Any],
        quality_assessment: Optional[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate overall validation result."""

        # Count successful phases
        successful_phases = 0
        total_phases = 0
        critical_failures = []

        for phase_name, phase_config in config["phases"].items():
            if not phase_config["enabled"]:
                continue

            total_phases += 1
            phase_result = phase_results.get(phase_name)

            if phase_result and not phase_result.get("error"):
                # Check phase-specific success criteria
                if phase_name == "html_js":
                    success = phase_result.get("success", False)
                elif phase_name == "scientific":
                    success = phase_result.get("is_scientifically_accurate", False)
                elif phase_name == "realism":
                    success = phase_result.get("is_realistic", False)
                elif phase_name == "runtime":
                    success = phase_result.get("is_runtime_valid", False)
                else:
                    success = False

                if success:
                    successful_phases += 1
                elif phase_config["critical"]:
                    critical_failures.append(phase_name)

        # Calculate overall score
        overall_score = 0.0
        if quality_assessment and "metrics" in quality_assessment:
            overall_score = quality_assessment["metrics"].get(
                "overall_quality_score", 0.0
            )
        else:
            # Fallback calculation
            if total_phases > 0:
                overall_score = (successful_phases / total_phases) * 10.0

        # Determine overall success
        quality_threshold = config["quality_scoring"]["threshold"]
        overall_success = (
            len(critical_failures) == 0
            and overall_score >= quality_threshold
            and successful_phases
            >= (total_phases * 0.75)  # At least 75% phases successful
        )

        return {
            "success": overall_success,
            "overall_score": overall_score,
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "critical_failures": critical_failures,
            "quality_threshold": quality_threshold,
            "meets_quality_threshold": overall_score >= quality_threshold,
            "phase_success_rate": successful_phases / max(total_phases, 1),
            "critical_failure": len(critical_failures) > 0,
            "recommended_for_use": overall_success and overall_score >= 7.5,
        }

    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations."""

        recommendations = []
        phase_results = validation_result.get("phase_results", {})
        overall_result = validation_result.get("overall_result", {})
        quality_assessment = validation_result.get("quality_assessment", {})

        # Overall quality recommendations
        overall_score = overall_result.get("overall_score", 0.0)
        if overall_score < 5.0:
            recommendations.append(
                "🔴 CRITICAL: Content requires major improvements across all areas"
            )
        elif overall_score < 7.0:
            recommendations.append(
                "🟡 NEEDS IMPROVEMENT: Content shows promise but needs refinement"
            )
        elif overall_score >= 8.5:
            recommendations.append("✅ EXCELLENT: Content meets high quality standards")

        # Phase-specific recommendations
        for phase_name, phase_result in phase_results.items():
            if not phase_result or phase_result.get("error"):
                recommendations.append(
                    f"🔧 {phase_name.upper()}: Validation failed - check implementation"
                )
                continue

            # HTML/JS specific
            if phase_name == "html_js" and not phase_result.get("success", False):
                recommendations.append(
                    "🔧 HTML/JS: Fix syntax errors and Three.js API compliance issues"
                )

            # Scientific specific
            elif phase_name == "scientific" and not phase_result.get(
                "is_scientifically_accurate", False
            ):
                recommendations.append(
                    "🔬 SCIENTIFIC: Verify units, formulas, and scientific accuracy"
                )

            # Realism specific
            elif phase_name == "realism" and not phase_result.get(
                "is_realistic", False
            ):
                recommendations.append(
                    "🎨 REALISM: Improve material properties, lighting, and visual quality"
                )

            # Runtime specific
            elif phase_name == "runtime" and not phase_result.get(
                "is_runtime_valid", False
            ):
                recommendations.append(
                    "⚡ RUNTIME: Fix performance issues and browser compatibility"
                )

        # Quality-based recommendations
        if quality_assessment and "feedback" in quality_assessment:
            feedback = quality_assessment["feedback"]
            if "critical_fixes" in feedback:
                for fix in feedback["critical_fixes"][:3]:
                    recommendations.append(f"🚨 CRITICAL FIX: {fix}")

        # Limit recommendations
        return recommendations[:10]

    def _create_validation_summary(
        self, validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a summary of validation results."""

        phase_results = validation_result.get("phase_results", {})
        overall_result = validation_result.get("overall_result", {})
        quality_assessment = validation_result.get("quality_assessment", {})

        # Phase summary
        phase_summary = {}
        for phase_name, phase_result in phase_results.items():
            if phase_result:
                phase_summary[phase_name] = {
                    "success": self._get_phase_success(phase_name, phase_result),
                    "score": self._get_phase_score(phase_name, phase_result),
                    "validation_time": phase_result.get("validation_time", 0.0),
                    "has_error": "error" in phase_result,
                }
            else:
                phase_summary[phase_name] = {
                    "success": False,
                    "score": 0.0,
                    "validation_time": 0.0,
                    "has_error": True,
                }

        # Quality summary
        quality_summary = {}
        if quality_assessment and "metrics" in quality_assessment:
            metrics = quality_assessment["metrics"]
            quality_summary = {
                "overall_score": metrics.get("overall_quality_score", 0.0),
                "technical_score": metrics.get("technical_quality_score", 0.0),
                "educational_score": metrics.get("educational_quality_score", 0.0),
                "ux_score": metrics.get("user_experience_score", 0.0),
                "quality_tier": quality_assessment.get("quality_tier", "unknown"),
                "critical_issues": metrics.get("critical_issues", 0),
                "major_issues": metrics.get("major_issues", 0),
            }

        return {
            "validation_duration": validation_result.get("validation_duration", 0.0),
            "overall_success": overall_result.get("success", False),
            "overall_score": overall_result.get("overall_score", 0.0),
            "phases": phase_summary,
            "quality": quality_summary,
            "recommendations_count": len(validation_result.get("recommendations", [])),
            "critical_failures": overall_result.get("critical_failures", []),
            "recommended_for_use": overall_result.get("recommended_for_use", False),
        }

    def _get_phase_success(self, phase_name: str, phase_result: Dict[str, Any]) -> bool:
        """Get success status for a specific phase."""
        if phase_name == "html_js":
            return phase_result.get("success", False)
        elif phase_name == "scientific":
            return phase_result.get("is_scientifically_accurate", False)
        elif phase_name == "realism":
            return phase_result.get("is_realistic", False)
        elif phase_name == "runtime":
            return phase_result.get("is_runtime_valid", False)
        return False

    def _get_phase_score(self, phase_name: str, phase_result: Dict[str, Any]) -> float:
        """Get score for a specific phase."""
        if phase_name == "html_js":
            return phase_result.get("overall_score", 0.0)
        elif phase_name == "scientific":
            return phase_result.get("accuracy_score", 0.0)
        elif phase_name == "realism":
            return phase_result.get("overall_realism_score", 0.0)
        elif phase_name == "runtime":
            return phase_result.get("overall_runtime_score", 0.0)
        return 0.0

    def _update_performance_metrics(
        self, validation_result: Dict[str, Any], start_time: float
    ):
        """Update performance tracking metrics."""

        self.performance_metrics["total_validations"] += 1

        overall_success = validation_result.get("overall_result", {}).get(
            "success", False
        )
        if overall_success:
            self.performance_metrics["successful_validations"] += 1

        # Update average validation time
        duration = validation_result.get("validation_duration", 0.0)
        total_validations = self.performance_metrics["total_validations"]

        if total_validations == 1:
            self.performance_metrics["average_validation_time"] = duration
        else:
            current_avg = self.performance_metrics["average_validation_time"]
            self.performance_metrics["average_validation_time"] = (
                current_avg * (total_validations - 1) + duration
            ) / total_validations

        # Update phase-specific metrics
        phase_results = validation_result.get("phase_results", {})
        for phase_name, phase_result in phase_results.items():
            if (
                phase_result
                and phase_name in self.performance_metrics["phase_performance"]
            ):
                phase_metrics = self.performance_metrics["phase_performance"][
                    phase_name
                ]

                phase_metrics["count"] += 1
                phase_time = phase_result.get("validation_time", 0.0)
                phase_success = self._get_phase_success(phase_name, phase_result)

                # Update average time
                if phase_metrics["count"] == 1:
                    phase_metrics["avg_time"] = phase_time
                else:
                    phase_metrics["avg_time"] = (
                        phase_metrics["avg_time"] * (phase_metrics["count"] - 1)
                        + phase_time
                    ) / phase_metrics["count"]

                # Update success rate
                current_successes = phase_metrics["success_rate"] * (
                    phase_metrics["count"] - 1
                )
                if phase_success:
                    current_successes += 1
                phase_metrics["success_rate"] = (
                    current_successes / phase_metrics["count"]
                )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of orchestrator performance."""

        total_validations = self.performance_metrics["total_validations"]
        successful_validations = self.performance_metrics["successful_validations"]

        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / max(total_validations, 1),
            "average_validation_time": self.performance_metrics[
                "average_validation_time"
            ],
            "phase_performance": self.performance_metrics["phase_performance"].copy(),
            "configuration": self.config.copy(),
        }

    def update_configuration(self, new_config: Dict[str, Any]):
        """Update orchestrator configuration."""
        self.config.update(new_config)
        logger.info("Orchestrator configuration updated")

    async def validate_batch(
        self,
        content_batch: List[Dict[str, Any]],
        batch_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Validate a batch of content items."""

        if batch_config is None:
            batch_config = {"parallel_batch": True, "max_concurrent": 5}

        if batch_config.get("parallel_batch", True):
            # Process batch in parallel with concurrency limit
            semaphore = asyncio.Semaphore(batch_config.get("max_concurrent", 5))

            async def validate_with_semaphore(content_item):
                async with semaphore:
                    return await self.validate_content(**content_item)

            tasks = [validate_with_semaphore(item) for item in content_batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "error": f"Batch item {i} failed: {str(result)}",
                            "content_metadata": content_batch[i],
                            "overall_result": {"success": False, "overall_score": 0.0},
                        }
                    )
                else:
                    processed_results.append(result)

            return processed_results
        else:
            # Process batch sequentially
            results = []
            for content_item in content_batch:
                try:
                    result = await self.validate_content(**content_item)
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "error": f"Batch item failed: {str(e)}",
                            "content_metadata": content_item,
                            "overall_result": {"success": False, "overall_score": 0.0},
                        }
                    )

            return results
