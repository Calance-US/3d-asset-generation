"""
Runtime Validation System for 3D Educational Content

This module provides comprehensive runtime validation including:
- Browser-based execution testing
- JavaScript runtime error detection
- Performance monitoring
- WebGL/Three.js rendering validation
"""

import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RuntimeIssue:
    """Represents a runtime validation issue."""

    type: str  # "error", "warning", "performance", "rendering"
    category: str  # "javascript", "webgl", "performance", "network", "console"
    message: str
    severity: int  # 1-5 scale
    timestamp: float
    stack_trace: Optional[str] = None
    performance_data: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    line_number: Optional[int] = None
    file_name: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during runtime."""

    load_time: float  # Time to load and initialize
    first_render_time: float  # Time to first frame
    average_fps: float  # Average frames per second
    memory_usage: float  # Peak memory usage in MB
    gpu_usage: float  # GPU utilization percentage
    network_requests: int  # Number of network requests
    failed_requests: int  # Number of failed requests
    console_errors: int  # Number of console errors
    console_warnings: int  # Number of console warnings
    webgl_context_lost: bool  # Whether WebGL context was lost
    three_js_objects: int  # Number of Three.js objects created
    texture_memory: float  # Texture memory usage in MB


@dataclass
class RenderingValidation:
    """Results of rendering validation."""

    webgl_supported: bool
    webgl_version: str
    three_js_loaded: bool
    three_js_version: str
    scene_rendered: bool
    geometry_valid: bool
    materials_loaded: bool
    textures_loaded: bool
    lighting_functional: bool
    animation_smooth: bool
    viewport_responsive: bool
    rendering_errors: List[str]


@dataclass
class RuntimeValidationResult:
    """Complete runtime validation results."""

    is_runtime_valid: bool
    execution_successful: bool
    performance_score: float  # 0-10 scale
    rendering_score: float  # 0-10 scale
    overall_runtime_score: float  # 0-10 scale

    # Detailed results
    issues: List[RuntimeIssue] = field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    rendering_validation: Optional[RenderingValidation] = None

    # Execution details
    execution_time: float = 0.0
    peak_memory: float = 0.0
    console_output: List[str] = field(default_factory=list)
    network_activity: List[Dict] = field(default_factory=list)

    # Screenshots and artifacts
    screenshot_path: Optional[str] = None
    performance_trace: Optional[str] = None


class RuntimeValidator:
    """Main runtime validator for 3D educational content."""

    def __init__(self):
        """Initialize the runtime validator."""
        self.browser_tester = None
        self.performance_validator = None
        self.rendering_validator = None

        # Performance thresholds
        self.performance_thresholds = {
            "max_load_time": 5.0,  # seconds
            "min_fps": 30.0,
            "max_memory": 200.0,  # MB
            "max_gpu_usage": 80.0,  # percentage
            "max_console_errors": 0,
            "max_console_warnings": 5,
        }

        # Rendering requirements
        self.rendering_requirements = {
            "webgl_required": True,
            "three_js_required": True,
            "min_objects": 1,
            "materials_required": True,
            "lighting_required": True,
        }

    async def validate_runtime_content(
        self,
        html_content: str,
        title: str = "3D Content",
        timeout: int = 30,
        capture_screenshots: bool = True,
        performance_monitoring: bool = True,
    ) -> RuntimeValidationResult:
        """
        Validate 3D content through runtime execution.

        Args:
            html_content: The HTML content to validate
            title: Title for the content (for reporting)
            timeout: Maximum execution time in seconds
            capture_screenshots: Whether to capture screenshots
            performance_monitoring: Whether to monitor performance

        Returns:
            RuntimeValidationResult with comprehensive validation results
        """
        start_time = time.time()

        try:
            # Lazy import to avoid circular dependencies
            from .browser_tester import BrowserTester
            from .performance_validator import PerformanceValidator
            from .rendering_validator import RenderingValidator

            self.browser_tester = BrowserTester()
            self.performance_validator = PerformanceValidator()
            self.rendering_validator = RenderingValidator()

            # Create temporary file for the HTML content
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            ) as f:
                f.write(html_content)
                temp_file_path = f.name

            try:
                # Start browser testing
                browser_result = await self.browser_tester.test_content(
                    temp_file_path,
                    timeout=timeout,
                    capture_screenshots=capture_screenshots,
                )

                # Performance validation
                if performance_monitoring:
                    perf_result = await self.performance_validator.validate_performance(
                        temp_file_path, timeout=timeout
                    )
                else:
                    perf_result = None

                # Rendering validation
                rendering_result = await self.rendering_validator.validate_rendering(
                    temp_file_path, timeout=timeout
                )

                # Compile results
                result = self._compile_validation_results(
                    browser_result, perf_result, rendering_result, start_time
                )

                return result

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Runtime validation failed: {str(e)}")

            # Return failure result
            execution_time = time.time() - start_time
            return RuntimeValidationResult(
                is_runtime_valid=False,
                execution_successful=False,
                performance_score=0.0,
                rendering_score=0.0,
                overall_runtime_score=0.0,
                execution_time=execution_time,
                issues=[
                    RuntimeIssue(
                        type="error",
                        category="system",
                        message=f"Runtime validation system error: {str(e)}",
                        severity=5,
                        timestamp=time.time(),
                        suggestion="Check system configuration and dependencies",
                    )
                ],
            )

    def _compile_validation_results(
        self,
        browser_result: Dict,
        perf_result: Optional[Dict],
        rendering_result: Dict,
        start_time: float,
    ) -> RuntimeValidationResult:
        """Compile individual validation results into final result."""

        execution_time = time.time() - start_time
        all_issues = []

        # Process browser testing results
        execution_successful = browser_result.get("success", False)
        console_output = browser_result.get("console_output", [])

        # Add JavaScript errors as issues
        for error in browser_result.get("javascript_errors", []):
            all_issues.append(
                RuntimeIssue(
                    type="error",
                    category="javascript",
                    message=error.get("message", "Unknown JavaScript error"),
                    severity=4,
                    timestamp=error.get("timestamp", time.time()),
                    stack_trace=error.get("stack", None),
                    line_number=error.get("line", None),
                    file_name=error.get("file", None),
                    suggestion="Check JavaScript syntax and Three.js API usage",
                )
            )

        # Add console warnings
        for warning in browser_result.get("console_warnings", []):
            all_issues.append(
                RuntimeIssue(
                    type="warning",
                    category="console",
                    message=warning.get("message", "Console warning"),
                    severity=2,
                    timestamp=warning.get("timestamp", time.time()),
                    suggestion="Review console output for potential issues",
                )
            )

        # Process performance results
        performance_metrics = None
        performance_score = 10.0

        if perf_result:
            performance_metrics = PerformanceMetrics(
                load_time=perf_result.get("load_time", 0.0),
                first_render_time=perf_result.get("first_render_time", 0.0),
                average_fps=perf_result.get("average_fps", 0.0),
                memory_usage=perf_result.get("memory_usage", 0.0),
                gpu_usage=perf_result.get("gpu_usage", 0.0),
                network_requests=perf_result.get("network_requests", 0),
                failed_requests=perf_result.get("failed_requests", 0),
                console_errors=len(browser_result.get("javascript_errors", [])),
                console_warnings=len(browser_result.get("console_warnings", [])),
                webgl_context_lost=perf_result.get("webgl_context_lost", False),
                three_js_objects=perf_result.get("three_js_objects", 0),
                texture_memory=perf_result.get("texture_memory", 0.0),
            )

            # Calculate performance score based on thresholds
            performance_score = self._calculate_performance_score(performance_metrics)

            # Add performance issues
            perf_issues = self._check_performance_thresholds(performance_metrics)
            all_issues.extend(perf_issues)

        # Process rendering results
        rendering_validation = RenderingValidation(
            webgl_supported=rendering_result.get("webgl_supported", False),
            webgl_version=rendering_result.get("webgl_version", "unknown"),
            three_js_loaded=rendering_result.get("three_js_loaded", False),
            three_js_version=rendering_result.get("three_js_version", "unknown"),
            scene_rendered=rendering_result.get("scene_rendered", False),
            geometry_valid=rendering_result.get("geometry_valid", False),
            materials_loaded=rendering_result.get("materials_loaded", False),
            textures_loaded=rendering_result.get("textures_loaded", False),
            lighting_functional=rendering_result.get("lighting_functional", False),
            animation_smooth=rendering_result.get("animation_smooth", False),
            viewport_responsive=rendering_result.get("viewport_responsive", False),
            rendering_errors=rendering_result.get("rendering_errors", []),
        )

        # Calculate rendering score
        rendering_score = self._calculate_rendering_score(rendering_validation)

        # Add rendering issues
        for error in rendering_validation.rendering_errors:
            all_issues.append(
                RuntimeIssue(
                    type="error",
                    category="rendering",
                    message=error,
                    severity=4,
                    timestamp=time.time(),
                    suggestion="Check WebGL compatibility and Three.js scene setup",
                )
            )

        # Calculate overall score
        overall_runtime_score = (performance_score + rendering_score) / 2

        # Determine if runtime is valid
        is_runtime_valid = (
            execution_successful
            and overall_runtime_score >= 7.0
            and len([i for i in all_issues if i.severity >= 4]) == 0
        )

        return RuntimeValidationResult(
            is_runtime_valid=is_runtime_valid,
            execution_successful=execution_successful,
            performance_score=performance_score,
            rendering_score=rendering_score,
            overall_runtime_score=overall_runtime_score,
            issues=all_issues,
            performance_metrics=performance_metrics,
            rendering_validation=rendering_validation,
            execution_time=execution_time,
            peak_memory=performance_metrics.memory_usage
            if performance_metrics
            else 0.0,
            console_output=console_output,
            screenshot_path=browser_result.get("screenshot_path", None),
            performance_trace=perf_result.get("trace_path", None)
            if perf_result
            else None,
        )

    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate performance score from 0-10 based on metrics."""
        score = 10.0

        # Load time penalty
        if metrics.load_time > self.performance_thresholds["max_load_time"]:
            score -= min(
                3.0,
                (metrics.load_time - self.performance_thresholds["max_load_time"])
                * 0.5,
            )

        # FPS penalty
        if metrics.average_fps < self.performance_thresholds["min_fps"]:
            score -= min(
                2.0,
                (self.performance_thresholds["min_fps"] - metrics.average_fps) * 0.1,
            )

        # Memory penalty
        if metrics.memory_usage > self.performance_thresholds["max_memory"]:
            score -= min(
                2.0,
                (metrics.memory_usage - self.performance_thresholds["max_memory"])
                * 0.01,
            )

        # Console errors penalty
        if metrics.console_errors > self.performance_thresholds["max_console_errors"]:
            score -= min(2.0, metrics.console_errors * 0.5)

        # Console warnings penalty
        if (
            metrics.console_warnings
            > self.performance_thresholds["max_console_warnings"]
        ):
            score -= min(
                1.0,
                (
                    metrics.console_warnings
                    - self.performance_thresholds["max_console_warnings"]
                )
                * 0.2,
            )

        return max(0.0, score)

    def _calculate_rendering_score(self, rendering: RenderingValidation) -> float:
        """Calculate rendering score from 0-10 based on validation results."""
        score = 0.0

        # Required components
        if rendering.webgl_supported:
            score += 2.0
        if rendering.three_js_loaded:
            score += 2.0
        if rendering.scene_rendered:
            score += 2.0
        if rendering.geometry_valid:
            score += 1.5
        if rendering.materials_loaded:
            score += 1.0
        if rendering.lighting_functional:
            score += 1.0
        if rendering.animation_smooth:
            score += 0.5

        # Penalty for rendering errors
        score -= min(5.0, len(rendering.rendering_errors) * 0.5)

        return max(0.0, min(10.0, score))

    def _check_performance_thresholds(
        self, metrics: PerformanceMetrics
    ) -> List[RuntimeIssue]:
        """Check performance metrics against thresholds and create issues."""
        issues = []

        if metrics.load_time > self.performance_thresholds["max_load_time"]:
            issues.append(
                RuntimeIssue(
                    type="performance",
                    category="loading",
                    message=f"Load time {metrics.load_time:.2f}s exceeds threshold {self.performance_thresholds['max_load_time']}s",
                    severity=3,
                    timestamp=time.time(),
                    performance_data={"load_time": metrics.load_time},
                    suggestion="Optimize asset loading and reduce scene complexity",
                )
            )

        if metrics.average_fps < self.performance_thresholds["min_fps"]:
            issues.append(
                RuntimeIssue(
                    type="performance",
                    category="rendering",
                    message=f"Average FPS {metrics.average_fps:.1f} below threshold {self.performance_thresholds['min_fps']}",
                    severity=3,
                    timestamp=time.time(),
                    performance_data={"fps": metrics.average_fps},
                    suggestion="Reduce geometry complexity or optimize materials",
                )
            )

        if metrics.memory_usage > self.performance_thresholds["max_memory"]:
            issues.append(
                RuntimeIssue(
                    type="performance",
                    category="memory",
                    message=f"Memory usage {metrics.memory_usage:.1f}MB exceeds threshold {self.performance_thresholds['max_memory']}MB",
                    severity=3,
                    timestamp=time.time(),
                    performance_data={"memory": metrics.memory_usage},
                    suggestion="Optimize textures and geometry to reduce memory footprint",
                )
            )

        return issues

    def get_runtime_summary(self, result: RuntimeValidationResult) -> Dict[str, Any]:
        """Generate a summary of runtime validation results."""
        return {
            "runtime_valid": result.is_runtime_valid,
            "execution_successful": result.execution_successful,
            "overall_score": result.overall_runtime_score,
            "performance_score": result.performance_score,
            "rendering_score": result.rendering_score,
            "execution_time": result.execution_time,
            "peak_memory": result.peak_memory,
            "total_issues": len(result.issues),
            "critical_issues": len([i for i in result.issues if i.severity >= 4]),
            "performance_issues": len(
                [i for i in result.issues if i.category == "performance"]
            ),
            "rendering_issues": len(
                [i for i in result.issues if i.category == "rendering"]
            ),
            "javascript_errors": len(
                [i for i in result.issues if i.category == "javascript"]
            ),
            "webgl_supported": result.rendering_validation.webgl_supported
            if result.rendering_validation
            else False,
            "three_js_loaded": result.rendering_validation.three_js_loaded
            if result.rendering_validation
            else False,
            "scene_rendered": result.rendering_validation.scene_rendered
            if result.rendering_validation
            else False,
            "average_fps": result.performance_metrics.average_fps
            if result.performance_metrics
            else 0.0,
            "load_time": result.performance_metrics.load_time
            if result.performance_metrics
            else 0.0,
        }
