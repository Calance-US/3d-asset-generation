"""
Browser Testing Service for Runtime Validation

This module provides headless browser testing capabilities for 3D educational content
using Playwright for accurate runtime validation.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

logger = logging.getLogger(__name__)


class BrowserTester:
    """Headless browser tester for 3D content validation."""

    def __init__(self):
        """Initialize the browser tester."""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_browser()

    async def start_browser(self):
        """Start the headless browser."""
        try:
            self.playwright = await async_playwright().start()

            # Launch Chromium with WebGL support
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--allow-running-insecure-content",
                    "--enable-webgl",
                    "--enable-accelerated-2d-canvas",
                    "--enable-gpu-rasterization",
                    "--ignore-gpu-blacklist",
                    "--use-gl=swiftshader",  # Software WebGL for headless
                ],
            )

            # Create browser context with appropriate viewport
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=1,
                has_touch=False,
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True,
            )

            # Create a new page
            self.page = await self.context.new_page()

            # Enable console logging
            self.page.on("console", self._handle_console_message)
            self.page.on("pageerror", self._handle_page_error)
            self.page.on("requestfailed", self._handle_request_failed)

            logger.info("Browser started successfully")

        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            raise

    async def stop_browser(self):
        """Stop the browser and clean up resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Browser stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping browser: {str(e)}")

    async def test_content(
        self,
        file_path: str,
        timeout: int = 30,
        capture_screenshots: bool = True,
        wait_for_render: float = 3.0,
    ) -> Dict[str, Any]:
        """
        Test HTML content in the browser.

        Args:
            file_path: Path to the HTML file to test
            timeout: Maximum test time in seconds
            capture_screenshots: Whether to capture screenshots
            wait_for_render: Time to wait for initial render

        Returns:
            Dictionary with test results
        """
        if not self.page:
            await self.start_browser()

        # Initialize tracking variables
        console_messages = []
        javascript_errors = []
        console_warnings = []
        network_requests = []
        failed_requests = []

        # Set up event handlers for this test
        def handle_console(message):
            console_messages.append(
                {"type": message.type, "text": message.text, "timestamp": time.time()}
            )

            if message.type == "error":
                javascript_errors.append(
                    {
                        "message": message.text,
                        "timestamp": time.time(),
                        "type": "console_error",
                    }
                )
            elif message.type == "warning":
                console_warnings.append(
                    {"message": message.text, "timestamp": time.time()}
                )

        def handle_page_error(error):
            javascript_errors.append(
                {
                    "message": str(error),
                    "timestamp": time.time(),
                    "type": "page_error",
                    "stack": getattr(error, "stack", None),
                }
            )

        def handle_request(request):
            network_requests.append(
                {"url": request.url, "method": request.method, "timestamp": time.time()}
            )

        def handle_request_failed(request):
            failed_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "failure": request.failure,
                    "timestamp": time.time(),
                }
            )

        # Add event handlers for this test
        self.page.on("console", handle_console)
        self.page.on("pageerror", handle_page_error)
        self.page.on("request", handle_request)
        self.page.on("requestfailed", handle_request_failed)

        start_time = time.time()
        success = False
        screenshot_path = None

        try:
            # Convert file path to file:// URL
            file_url = Path(file_path).as_uri()

            # Navigate to the file
            logger.info(f"Loading content from: {file_url}")

            # Set a longer timeout for navigation
            await self.page.goto(
                file_url, timeout=timeout * 1000, wait_until="networkidle"
            )

            # Wait for initial render
            await asyncio.sleep(wait_for_render)

            # Check if page loaded successfully
            title = await self.page.title()
            url = self.page.url

            logger.info(f"Page loaded: {title} ({url})")

            # Wait for Three.js to potentially load
            try:
                await self.page.wait_for_function(
                    "typeof THREE !== 'undefined' || document.readyState === 'complete'",
                    timeout=5000,
                )
            except:
                # It's okay if Three.js doesn't load or times out
                pass

            # Capture screenshot if requested
            if capture_screenshots:
                screenshot_path = await self._capture_screenshot()

            # Check for WebGL support
            webgl_info = await self._check_webgl_support()

            # Check for Three.js
            threejs_info = await self._check_threejs_status()

            # Check for canvas elements
            canvas_info = await self._check_canvas_elements()

            # Monitor for a bit longer to catch any delayed errors
            await asyncio.sleep(1.0)

            success = True

        except Exception as e:
            logger.error(f"Browser test failed: {str(e)}")
            javascript_errors.append(
                {
                    "message": f"Browser navigation error: {str(e)}",
                    "timestamp": time.time(),
                    "type": "navigation_error",
                }
            )

        execution_time = time.time() - start_time

        # Compile results
        result = {
            "success": success,
            "execution_time": execution_time,
            "console_output": [msg["text"] for msg in console_messages],
            "javascript_errors": javascript_errors,
            "console_warnings": console_warnings,
            "network_requests": len(network_requests),
            "failed_requests": len(failed_requests),
            "failed_request_details": failed_requests,
            "screenshot_path": screenshot_path,
            "webgl_info": webgl_info if success else {},
            "threejs_info": threejs_info if success else {},
            "canvas_info": canvas_info if success else {},
            "page_title": await self.page.title()
            if success and self.page
            else "Failed to load",
            "final_url": self.page.url if success and self.page else file_url,
        }

        logger.info(
            f"Browser test completed - Success: {success}, "
            f"Errors: {len(javascript_errors)}, "
            f"Warnings: {len(console_warnings)}, "
            f"Time: {execution_time:.2f}s"
        )

        return result

    async def _capture_screenshot(self) -> Optional[str]:
        """Capture a screenshot of the current page."""
        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)

            # Generate unique filename
            timestamp = int(time.time() * 1000)
            screenshot_path = screenshots_dir / f"runtime_test_{timestamp}.png"

            # Capture full page screenshot
            await self.page.screenshot(
                path=str(screenshot_path), full_page=True, type="png"
            )

            logger.info(f"Screenshot captured: {screenshot_path}")
            return str(screenshot_path)

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            return None

    async def _check_webgl_support(self) -> Dict[str, Any]:
        """Check WebGL support and capabilities."""
        try:
            webgl_info = await self.page.evaluate("""
                () => {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    const gl2 = canvas.getContext('webgl2');

                    if (!gl) {
                        return { supported: false, version: 'none' };
                    }

                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');

                    return {
                        supported: true,
                        version: gl2 ? 'webgl2' : 'webgl1',
                        vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
                        renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
                        max_texture_size: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                        max_vertex_attribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
                        max_varying_vectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
                        extensions: gl.getSupportedExtensions() || []
                    };
                }
            """)

            return webgl_info

        except Exception as e:
            logger.error(f"Failed to check WebGL support: {str(e)}")
            return {"supported": False, "error": str(e)}

    async def _check_threejs_status(self) -> Dict[str, Any]:
        """Check Three.js loading status and version."""
        try:
            threejs_info = await self.page.evaluate("""
                () => {
                    if (typeof THREE === 'undefined') {
                        return { loaded: false, version: 'not_loaded' };
                    }

                    const scene_count = document.querySelectorAll('canvas').length;

                    return {
                        loaded: true,
                        version: THREE.REVISION || 'unknown',
                        canvas_elements: scene_count,
                        webgl_renderer_available: typeof THREE.WebGLRenderer !== 'undefined',
                        scene_class_available: typeof THREE.Scene !== 'undefined',
                        camera_class_available: typeof THREE.PerspectiveCamera !== 'undefined',
                        geometry_classes: {
                            box: typeof THREE.BoxGeometry !== 'undefined',
                            sphere: typeof THREE.SphereGeometry !== 'undefined',
                            plane: typeof THREE.PlaneGeometry !== 'undefined'
                        }
                    };
                }
            """)

            return threejs_info

        except Exception as e:
            logger.error(f"Failed to check Three.js status: {str(e)}")
            return {"loaded": False, "error": str(e)}

    async def _check_canvas_elements(self) -> Dict[str, Any]:
        """Check canvas elements and their properties."""
        try:
            canvas_info = await self.page.evaluate("""
                () => {
                    const canvases = document.querySelectorAll('canvas');
                    const canvas_data = [];

                    canvases.forEach((canvas, index) => {
                        const rect = canvas.getBoundingClientRect();
                        const context = canvas.getContext('webgl') || canvas.getContext('2d');

                        canvas_data.push({
                            index: index,
                            width: canvas.width,
                            height: canvas.height,
                            display_width: rect.width,
                            display_height: rect.height,
                            context_type: context ? (context.constructor.name || 'unknown') : 'none',
                            visible: rect.width > 0 && rect.height > 0,
                            in_viewport: rect.top >= 0 && rect.left >= 0 &&
                                        rect.bottom <= window.innerHeight &&
                                        rect.right <= window.innerWidth
                        });
                    });

                    return {
                        count: canvases.length,
                        canvases: canvas_data,
                        total_visible: canvas_data.filter(c => c.visible).length,
                        total_in_viewport: canvas_data.filter(c => c.in_viewport).length
                    };
                }
            """)

            return canvas_info

        except Exception as e:
            logger.error(f"Failed to check canvas elements: {str(e)}")
            return {"count": 0, "error": str(e)}

    def _handle_console_message(self, message):
        """Handle console messages from the page."""
        # This is a backup handler, actual handling is done in test_content
        pass

    def _handle_page_error(self, error):
        """Handle page errors."""
        # This is a backup handler, actual handling is done in test_content
        pass

    def _handle_request_failed(self, request):
        """Handle failed network requests."""
        # This is a backup handler, actual handling is done in test_content
        pass

    async def evaluate_custom_script(self, script: str) -> Any:
        """Evaluate custom JavaScript in the browser context."""
        try:
            if not self.page:
                await self.start_browser()

            result = await self.page.evaluate(script)
            return result

        except Exception as e:
            logger.error(f"Failed to evaluate script: {str(e)}")
            return None

    async def wait_for_element(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for an element to appear on the page."""
        try:
            if not self.page:
                return False

            await self.page.wait_for_selector(selector, timeout=timeout)
            return True

        except Exception as e:
            logger.debug(f"Element {selector} not found within timeout: {str(e)}")
            return False

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from the browser."""
        try:
            if not self.page:
                return {}

            # Get performance timing
            performance_data = await self.page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    const memory = performance.memory || {};

                    return {
                        load_time: perf ? (perf.loadEventEnd - perf.navigationStart) / 1000 : 0,
                        dom_load_time: perf ? (perf.domContentLoadedEventEnd - perf.navigationStart) / 1000 : 0,
                        first_paint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime / 1000 || 0,
                        memory_used: memory.usedJSHeapSize || 0,
                        memory_total: memory.totalJSHeapSize || 0,
                        memory_limit: memory.jsHeapSizeLimit || 0
                    };
                }
            """)

            return performance_data

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}
