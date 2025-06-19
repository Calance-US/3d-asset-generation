"""
Performance Validation Service for 3D Educational Content

This module provides performance monitoring and validation capabilities
for runtime 3D content execution.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List

import psutil
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Performance validator for 3D content runtime execution."""

    def __init__(self):
        """Initialize the performance validator."""
        self.monitoring_active = False
        self.performance_data = []
        self.fps_samples = []
        self.memory_samples = []
        self.cpu_samples = []

        # Performance thresholds
        self.thresholds = {
            "max_load_time": 5.0,  # seconds
            "min_fps": 30.0,
            "max_memory_mb": 200.0,
            "max_cpu_percent": 80.0,
            "max_frame_time": 33.33,  # milliseconds (30 FPS)
            "max_texture_memory": 100.0,  # MB
        }

    async def validate_performance(
        self,
        file_path: str,
        timeout: int = 30,
        monitoring_interval: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Validate performance of 3D content during runtime execution.

        Args:
            file_path: Path to the HTML file to test
            timeout: Maximum monitoring time in seconds
            monitoring_interval: Interval between performance samples

        Returns:
            Dictionary with performance validation results
        """
        from .browser_tester import BrowserTester

        start_time = time.time()

        try:
            async with BrowserTester() as browser:
                # Load the content
                browser_result = await browser.test_content(
                    file_path,
                    timeout=timeout,
                    capture_screenshots=False,
                    wait_for_render=1.0,
                )

                if not browser_result["success"]:
                    return {
                        "success": False,
                        "error": "Failed to load content for performance testing",
                        "load_time": 0.0,
                        "first_render_time": 0.0,
                        "average_fps": 0.0,
                        "memory_usage": 0.0,
                        "cpu_usage": 0.0,
                        "gpu_usage": 0.0,
                        "network_requests": 0,
                        "failed_requests": 0,
                        "webgl_context_lost": False,
                        "three_js_objects": 0,
                        "texture_memory": 0.0,
                        "performance_issues": [],
                    }

                # Start performance monitoring
                await self._start_performance_monitoring(
                    browser.page, monitoring_interval
                )

                # Monitor for the specified duration
                monitor_time = min(timeout - 2, 10)  # Don't monitor for too long
                await asyncio.sleep(monitor_time)

                # Stop monitoring
                await self._stop_performance_monitoring()

                # Get final performance metrics
                final_metrics = await self._get_final_metrics(browser.page)

                # Analyze performance data
                analysis = self._analyze_performance_data()

                # Compile results
                result = {
                    "success": True,
                    "load_time": final_metrics.get("load_time", 0.0),
                    "first_render_time": final_metrics.get("first_render_time", 0.0),
                    "average_fps": analysis["average_fps"],
                    "min_fps": analysis["min_fps"],
                    "max_fps": analysis["max_fps"],
                    "memory_usage": analysis["peak_memory"],
                    "average_memory": analysis["average_memory"],
                    "cpu_usage": analysis["peak_cpu"],
                    "average_cpu": analysis["average_cpu"],
                    "gpu_usage": final_metrics.get("gpu_usage", 0.0),
                    "network_requests": browser_result.get("network_requests", 0),
                    "failed_requests": browser_result.get("failed_requests", 0),
                    "webgl_context_lost": final_metrics.get(
                        "webgl_context_lost", False
                    ),
                    "three_js_objects": final_metrics.get("three_js_objects", 0),
                    "texture_memory": final_metrics.get("texture_memory", 0.0),
                    "frame_consistency": analysis["frame_consistency"],
                    "memory_leaks_detected": analysis["memory_leaks_detected"],
                    "performance_issues": self._identify_performance_issues(
                        analysis, final_metrics
                    ),
                    "monitoring_duration": monitor_time,
                    "samples_collected": len(self.performance_data),
                }

                return result

        except Exception as e:
            logger.error(f"Performance validation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "load_time": 0.0,
                "first_render_time": 0.0,
                "average_fps": 0.0,
                "memory_usage": 0.0,
                "cpu_usage": 0.0,
                "gpu_usage": 0.0,
                "network_requests": 0,
                "failed_requests": 0,
                "webgl_context_lost": False,
                "three_js_objects": 0,
                "texture_memory": 0.0,
                "performance_issues": [f"System error: {str(e)}"],
            }

    async def _start_performance_monitoring(self, page: Page, interval: float):
        """Start continuous performance monitoring."""
        self.monitoring_active = True
        self.performance_data = []
        self.fps_samples = []
        self.memory_samples = []
        self.cpu_samples = []

        # Start monitoring task
        asyncio.create_task(self._monitor_performance_loop(page, interval))

    async def _monitor_performance_loop(self, page: Page, interval: float):
        """Main performance monitoring loop."""
        while self.monitoring_active:
            try:
                timestamp = time.time()

                # Get system metrics
                process = psutil.Process()
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                # Get browser performance metrics
                browser_metrics = await page.evaluate("""
                    () => {
                        const now = performance.now();
                        const memory = performance.memory || {};

                        // Try to get FPS from requestAnimationFrame
                        if (!window.fpsCounter) {
                            window.fpsCounter = {
                                frames: 0,
                                lastTime: now,
                                fps: 0
                            };
                        }

                        const deltaTime = now - window.fpsCounter.lastTime;
                        if (deltaTime >= 1000) {
                            window.fpsCounter.fps = (window.fpsCounter.frames * 1000) / deltaTime;
                            window.fpsCounter.frames = 0;
                            window.fpsCounter.lastTime = now;
                        }
                        window.fpsCounter.frames++;

                        // Get WebGL info if available
                        let webglInfo = {};
                        try {
                            const canvas = document.querySelector('canvas');
                            if (canvas) {
                                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                                if (gl) {
                                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                                    webglInfo = {
                                        context_lost: gl.isContextLost(),
                                        drawingBufferWidth: gl.drawingBufferWidth,
                                        drawingBufferHeight: gl.drawingBufferHeight,
                                    };
                                }
                            }
                        } catch (e) {
                            webglInfo.error = e.message;
                        }

                        // Get Three.js scene info if available
                        let threejsInfo = {};
                        try {
                            if (typeof THREE !== 'undefined' && window.scene) {
                                threejsInfo = {
                                    objects: window.scene.children.length,
                                    geometries: window.scene.children.filter(child => child.geometry).length,
                                    materials: window.scene.children.filter(child => child.material).length,
                                };
                            }
                        } catch (e) {
                            threejsInfo.error = e.message;
                        }

                        return {
                            timestamp: now,
                            fps: window.fpsCounter.fps,
                            memory_used: memory.usedJSHeapSize || 0,
                            memory_total: memory.totalJSHeapSize || 0,
                            memory_limit: memory.jsHeapSizeLimit || 0,
                            webgl: webglInfo,
                            threejs: threejsInfo
                        };
                    }
                """)

                # Compile performance sample
                sample = {
                    "timestamp": timestamp,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "browser_memory_mb": (browser_metrics.get("memory_used", 0))
                    / 1024
                    / 1024,
                    "fps": browser_metrics.get("fps", 0),
                    "webgl_context_lost": browser_metrics.get("webgl", {}).get(
                        "context_lost", False
                    ),
                    "three_js_objects": browser_metrics.get("threejs", {}).get(
                        "objects", 0
                    ),
                    "browser_metrics": browser_metrics,
                }

                self.performance_data.append(sample)
                self.fps_samples.append(sample["fps"])
                self.memory_samples.append(sample["memory_mb"])
                self.cpu_samples.append(sample["cpu_percent"])

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {str(e)}")
                await asyncio.sleep(interval)

    async def _stop_performance_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False

    async def _get_final_metrics(self, page: Page) -> Dict[str, Any]:
        """Get final performance metrics from the browser."""
        try:
            final_metrics = await page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    const memory = performance.memory || {};

                    // Get paint timing
                    const paintEntries = performance.getEntriesByType('paint');
                    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
                    const firstContentfulPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');

                    return {
                        load_time: perf ? (perf.loadEventEnd - perf.navigationStart) / 1000 : 0,
                        dom_load_time: perf ? (perf.domContentLoadedEventEnd - perf.navigationStart) / 1000 : 0,
                        first_render_time: firstPaint ? firstPaint.startTime / 1000 : 0,
                        first_contentful_paint: firstContentfulPaint ? firstContentfulPaint.startTime / 1000 : 0,
                        memory_used: memory.usedJSHeapSize || 0,
                        memory_total: memory.totalJSHeapSize || 0,
                        memory_limit: memory.jsHeapSizeLimit || 0,
                        texture_memory: 0, // Would need WebGL extension to get actual texture memory
                        gpu_usage: 0, // Browser doesn't expose GPU usage directly
                        webgl_context_lost: false, // Will be updated by monitoring
                        three_js_objects: 0, // Will be updated by monitoring
                    };
                }
            """)

            return final_metrics

        except Exception as e:
            logger.error(f"Failed to get final metrics: {str(e)}")
            return {}

    def _analyze_performance_data(self) -> Dict[str, Any]:
        """Analyze collected performance data."""
        if not self.performance_data:
            return {
                "average_fps": 0.0,
                "min_fps": 0.0,
                "max_fps": 0.0,
                "peak_memory": 0.0,
                "average_memory": 0.0,
                "peak_cpu": 0.0,
                "average_cpu": 0.0,
                "frame_consistency": 0.0,
                "memory_leaks_detected": False,
            }

        # FPS analysis
        valid_fps = [fps for fps in self.fps_samples if fps > 0]
        average_fps = sum(valid_fps) / len(valid_fps) if valid_fps else 0.0
        min_fps = min(valid_fps) if valid_fps else 0.0
        max_fps = max(valid_fps) if valid_fps else 0.0

        # Frame time consistency (lower is better)
        frame_times = [1000 / fps for fps in valid_fps if fps > 0]
        frame_consistency = 0.0
        if len(frame_times) > 1:
            avg_frame_time = sum(frame_times) / len(frame_times)
            variance = sum((ft - avg_frame_time) ** 2 for ft in frame_times) / len(
                frame_times
            )
            frame_consistency = (
                (variance**0.5) / avg_frame_time if avg_frame_time > 0 else 1.0
            )

        # Memory analysis
        peak_memory = max(self.memory_samples) if self.memory_samples else 0.0
        average_memory = (
            sum(self.memory_samples) / len(self.memory_samples)
            if self.memory_samples
            else 0.0
        )

        # Memory leak detection (simple heuristic)
        memory_leaks_detected = False
        if len(self.memory_samples) >= 5:
            # Check if memory usage trend is consistently increasing
            recent_samples = self.memory_samples[-5:]
            initial_samples = self.memory_samples[:5]
            if (
                sum(recent_samples) / len(recent_samples)
                > sum(initial_samples) / len(initial_samples) * 1.5
            ):
                memory_leaks_detected = True

        # CPU analysis
        peak_cpu = max(self.cpu_samples) if self.cpu_samples else 0.0
        average_cpu = (
            sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        )

        return {
            "average_fps": average_fps,
            "min_fps": min_fps,
            "max_fps": max_fps,
            "peak_memory": peak_memory,
            "average_memory": average_memory,
            "peak_cpu": peak_cpu,
            "average_cpu": average_cpu,
            "frame_consistency": frame_consistency,
            "memory_leaks_detected": memory_leaks_detected,
            "total_samples": len(self.performance_data),
        }

    def _identify_performance_issues(
        self, analysis: Dict[str, Any], final_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify performance issues based on analysis and thresholds."""
        issues = []

        # Load time issues
        load_time = final_metrics.get("load_time", 0.0)
        if load_time > self.thresholds["max_load_time"]:
            issues.append(
                f"Slow load time: {load_time:.2f}s (threshold: {self.thresholds['max_load_time']}s)"
            )

        # FPS issues
        avg_fps = analysis["average_fps"]
        if avg_fps > 0 and avg_fps < self.thresholds["min_fps"]:
            issues.append(
                f"Low FPS: {avg_fps:.1f} (threshold: {self.thresholds['min_fps']})"
            )

        min_fps = analysis["min_fps"]
        if min_fps > 0 and min_fps < self.thresholds["min_fps"] * 0.5:
            issues.append(f"Frame drops detected: minimum FPS {min_fps:.1f}")

        # Frame consistency issues
        if analysis["frame_consistency"] > 0.3:
            issues.append("Inconsistent frame timing detected - may cause stuttering")

        # Memory issues
        peak_memory = analysis["peak_memory"]
        if peak_memory > self.thresholds["max_memory_mb"]:
            issues.append(
                f"High memory usage: {peak_memory:.1f}MB (threshold: {self.thresholds['max_memory_mb']}MB)"
            )

        if analysis["memory_leaks_detected"]:
            issues.append(
                "Potential memory leak detected - memory usage trending upward"
            )

        # CPU issues
        peak_cpu = analysis["peak_cpu"]
        if peak_cpu > self.thresholds["max_cpu_percent"]:
            issues.append(
                f"High CPU usage: {peak_cpu:.1f}% (threshold: {self.thresholds['max_cpu_percent']}%)"
            )

        # WebGL context issues
        if final_metrics.get("webgl_context_lost", False):
            issues.append("WebGL context was lost during execution")

        # No FPS data
        if avg_fps == 0:
            issues.append("No FPS data collected - animation may not be running")

        return issues

    def get_performance_report(self, result: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        if not result.get("success", False):
            return f"❌ Performance validation failed: {result.get('error', 'Unknown error')}"

        report_lines = []

        # Overall status
        issues = result.get("performance_issues", [])
        if not issues:
            report_lines.append("✅ Performance validation passed")
        else:
            report_lines.append(f"⚠️ Performance validation found {len(issues)} issues")

        # Key metrics
        report_lines.append("📊 Key Metrics:")
        report_lines.append(f"   Load Time: {result.get('load_time', 0):.2f}s")
        report_lines.append(f"   Average FPS: {result.get('average_fps', 0):.1f}")
        report_lines.append(f"   Peak Memory: {result.get('memory_usage', 0):.1f}MB")
        report_lines.append(f"   Peak CPU: {result.get('cpu_usage', 0):.1f}%")

        # Issues
        if issues:
            report_lines.append("⚠️ Issues Found:")
            for issue in issues:
                report_lines.append(f"   • {issue}")

        # Recommendations
        if issues:
            report_lines.append("💡 Recommendations:")
            if result.get("load_time", 0) > 3:
                report_lines.append("   • Optimize asset loading and reduce file sizes")
            if result.get("average_fps", 0) < 30:
                report_lines.append(
                    "   • Reduce scene complexity or optimize rendering"
                )
            if result.get("memory_usage", 0) > 150:
                report_lines.append(
                    "   • Optimize textures and geometry to reduce memory usage"
                )
            if result.get("cpu_usage", 0) > 70:
                report_lines.append(
                    "   • Optimize JavaScript code and reduce computational complexity"
                )

        return "\n".join(report_lines)
