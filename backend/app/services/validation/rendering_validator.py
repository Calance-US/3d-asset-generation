"""
Rendering Validation Service for 3D Educational Content

This module provides comprehensive rendering validation capabilities
for WebGL and Three.js content, including scene analysis and visual quality checks.
"""

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RenderingValidator:
    """Rendering validator for 3D content WebGL and Three.js validation."""

    def __init__(self):
        """Initialize the rendering validator."""
        self.validation_scripts = {
            "webgl_check": """
                () => {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    const gl2 = canvas.getContext('webgl2');

                    if (!gl) {
                        return {
                            supported: false,
                            version: 'none',
                            error: 'WebGL not supported'
                        };
                    }

                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    const extensions = gl.getSupportedExtensions() || [];

                    return {
                        supported: true,
                        version: gl2 ? 'webgl2' : 'webgl1',
                        vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
                        renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
                        max_texture_size: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                        max_vertex_attribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
                        max_varying_vectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
                        max_fragment_uniform_vectors: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),
                        max_vertex_uniform_vectors: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS),
                        extensions: extensions,
                        context_lost: gl.isContextLost(),
                        aliased_line_width_range: gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE),
                        aliased_point_size_range: gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE),
                        max_viewport_dims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
                        shading_language_version: gl.getParameter(gl.SHADING_LANGUAGE_VERSION)
                    };
                }
            """,
            "threejs_analysis": """
                () => {
                    if (typeof THREE === 'undefined') {
                        return {
                            loaded: false,
                            version: 'not_loaded',
                            error: 'Three.js not loaded'
                        };
                    }

                    // Check for scene
                    let sceneInfo = {
                        exists: false,
                        objects: 0,
                        geometries: 0,
                        materials: 0,
                        lights: 0,
                        cameras: 0,
                        meshes: 0,
                        groups: 0
                    };

                    if (window.scene && window.scene instanceof THREE.Scene) {
                        sceneInfo.exists = true;

                        const traverse = (obj) => {
                            sceneInfo.objects++;

                            if (obj.geometry) sceneInfo.geometries++;
                            if (obj.material) sceneInfo.materials++;
                            if (obj.isLight) sceneInfo.lights++;
                            if (obj.isCamera) sceneInfo.cameras++;
                            if (obj.isMesh) sceneInfo.meshes++;
                            if (obj.isGroup) sceneInfo.groups++;

                            obj.children.forEach(traverse);
                        };

                        window.scene.children.forEach(traverse);
                    }

                    // Check for renderer
                    let rendererInfo = {
                        exists: false,
                        type: 'unknown',
                        size: { width: 0, height: 0 },
                        pixel_ratio: 1,
                        antialias: false,
                        canvas_exists: false
                    };

                    if (window.renderer) {
                        rendererInfo.exists = true;
                        rendererInfo.type = window.renderer.constructor.name;

                        if (window.renderer.getSize) {
                            const size = window.renderer.getSize(new THREE.Vector2());
                            rendererInfo.size = { width: size.x, height: size.y };
                        }

                        if (window.renderer.getPixelRatio) {
                            rendererInfo.pixel_ratio = window.renderer.getPixelRatio();
                        }

                        if (window.renderer.antialias !== undefined) {
                            rendererInfo.antialias = window.renderer.antialias;
                        }

                        if (window.renderer.domElement) {
                            rendererInfo.canvas_exists = true;
                        }
                    }

                    // Check for camera
                    let cameraInfo = {
                        exists: false,
                        type: 'unknown',
                        fov: 0,
                        aspect: 0,
                        near: 0,
                        far: 0,
                        position: { x: 0, y: 0, z: 0 }
                    };

                    if (window.camera) {
                        cameraInfo.exists = true;
                        cameraInfo.type = window.camera.constructor.name;

                        if (window.camera.fov !== undefined) cameraInfo.fov = window.camera.fov;
                        if (window.camera.aspect !== undefined) cameraInfo.aspect = window.camera.aspect;
                        if (window.camera.near !== undefined) cameraInfo.near = window.camera.near;
                        if (window.camera.far !== undefined) cameraInfo.far = window.camera.far;
                        if (window.camera.position) {
                            cameraInfo.position = {
                                x: window.camera.position.x,
                                y: window.camera.position.y,
                                z: window.camera.position.z
                            };
                        }
                    }

                    return {
                        loaded: true,
                        version: THREE.REVISION || 'unknown',
                        scene: sceneInfo,
                        renderer: rendererInfo,
                        camera: cameraInfo,
                        classes_available: {
                            Scene: typeof THREE.Scene !== 'undefined',
                            WebGLRenderer: typeof THREE.WebGLRenderer !== 'undefined',
                            PerspectiveCamera: typeof THREE.PerspectiveCamera !== 'undefined',
                            BoxGeometry: typeof THREE.BoxGeometry !== 'undefined',
                            SphereGeometry: typeof THREE.SphereGeometry !== 'undefined',
                            PlaneGeometry: typeof THREE.PlaneGeometry !== 'undefined',
                            MeshBasicMaterial: typeof THREE.MeshBasicMaterial !== 'undefined',
                            MeshLambertMaterial: typeof THREE.MeshLambertMaterial !== 'undefined',
                            MeshPhongMaterial: typeof THREE.MeshPhongMaterial !== 'undefined',
                            DirectionalLight: typeof THREE.DirectionalLight !== 'undefined',
                            PointLight: typeof THREE.PointLight !== 'undefined',
                            AmbientLight: typeof THREE.AmbientLight !== 'undefined'
                        }
                    };
                }
            """,
            "canvas_analysis": """
                () => {
                    const canvases = document.querySelectorAll('canvas');
                    const canvasData = [];

                    canvases.forEach((canvas, index) => {
                        const rect = canvas.getBoundingClientRect();
                        const context = canvas.getContext('webgl') ||
                                      canvas.getContext('webgl2') ||
                                      canvas.getContext('2d');

                        let contextInfo = {
                            type: 'none',
                            lost: false,
                            attributes: {}
                        };

                        if (context) {
                            if (context instanceof WebGLRenderingContext) {
                                contextInfo.type = 'webgl';
                                contextInfo.lost = context.isContextLost();

                                // Get context attributes
                                const attrs = context.getContextAttributes();
                                if (attrs) {
                                    contextInfo.attributes = {
                                        alpha: attrs.alpha,
                                        antialias: attrs.antialias,
                                        depth: attrs.depth,
                                        premultipliedAlpha: attrs.premultipliedAlpha,
                                        preserveDrawingBuffer: attrs.preserveDrawingBuffer,
                                        stencil: attrs.stencil
                                    };
                                }
                            } else if (context instanceof WebGL2RenderingContext) {
                                contextInfo.type = 'webgl2';
                                contextInfo.lost = context.isContextLost();

                                const attrs = context.getContextAttributes();
                                if (attrs) {
                                    contextInfo.attributes = attrs;
                                }
                            } else {
                                contextInfo.type = '2d';
                            }
                        }

                        canvasData.push({
                            index: index,
                            width: canvas.width,
                            height: canvas.height,
                            display_width: rect.width,
                            display_height: rect.height,
                            visible: rect.width > 0 && rect.height > 0,
                            in_viewport: rect.top >= 0 && rect.left >= 0 &&
                                        rect.bottom <= window.innerHeight &&
                                        rect.right <= window.innerWidth,
                            context: contextInfo,
                            style: {
                                position: window.getComputedStyle(canvas).position,
                                zIndex: window.getComputedStyle(canvas).zIndex,
                                display: window.getComputedStyle(canvas).display
                            }
                        });
                    });

                    return {
                        total_count: canvases.length,
                        webgl_count: canvasData.filter(c => c.context.type.includes('webgl')).length,
                        visible_count: canvasData.filter(c => c.visible).length,
                        viewport_count: canvasData.filter(c => c.in_viewport).length,
                        canvases: canvasData
                    };
                }
            """,
            "rendering_test": """
                () => {
                    // Test if scene is actually rendering
                    let renderingTest = {
                        attempted: false,
                        successful: false,
                        error: null,
                        frame_rendered: false,
                        animation_detected: false
                    };

                    try {
                        if (window.renderer && window.scene && window.camera) {
                            renderingTest.attempted = true;

                            // Try to render one frame
                            window.renderer.render(window.scene, window.camera);
                            renderingTest.successful = true;
                            renderingTest.frame_rendered = true;

                            // Check for animation loop
                            if (window.animate || window.animationId) {
                                renderingTest.animation_detected = true;
                            }
                        }
                    } catch (error) {
                        renderingTest.error = error.message;
                    }

                    return renderingTest;
                }
            """,
        }

    async def validate_rendering(
        self, file_path: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Validate rendering capabilities and quality of 3D content.

        Args:
            file_path: Path to the HTML file to validate
            timeout: Maximum validation time in seconds

        Returns:
            Dictionary with rendering validation results
        """
        from .browser_tester import BrowserTester

        try:
            async with BrowserTester() as browser:
                # Load the content
                browser_result = await browser.test_content(
                    file_path,
                    timeout=timeout,
                    capture_screenshots=True,
                    wait_for_render=2.0,
                )

                if not browser_result["success"]:
                    return {
                        "webgl_supported": False,
                        "webgl_version": "unknown",
                        "three_js_loaded": False,
                        "three_js_version": "unknown",
                        "scene_rendered": False,
                        "geometry_valid": False,
                        "materials_loaded": False,
                        "textures_loaded": False,
                        "lighting_functional": False,
                        "animation_smooth": False,
                        "viewport_responsive": False,
                        "rendering_errors": [
                            f"Failed to load content: {browser_result.get('error', 'Unknown error')}"
                        ],
                        "validation_details": {},
                    }

                # Run validation scripts
                webgl_info = await browser.page.evaluate(
                    self.validation_scripts["webgl_check"]
                )
                threejs_info = await browser.page.evaluate(
                    self.validation_scripts["threejs_analysis"]
                )
                canvas_info = await browser.page.evaluate(
                    self.validation_scripts["canvas_analysis"]
                )

                # Wait a moment for any animations to start
                await asyncio.sleep(1.0)

                rendering_test = await browser.page.evaluate(
                    self.validation_scripts["rendering_test"]
                )

                # Analyze results
                validation_result = self._analyze_rendering_results(
                    webgl_info,
                    threejs_info,
                    canvas_info,
                    rendering_test,
                    browser_result,
                )

                return validation_result

        except Exception as e:
            logger.error(f"Rendering validation failed: {str(e)}")
            return {
                "webgl_supported": False,
                "webgl_version": "unknown",
                "three_js_loaded": False,
                "three_js_version": "unknown",
                "scene_rendered": False,
                "geometry_valid": False,
                "materials_loaded": False,
                "textures_loaded": False,
                "lighting_functional": False,
                "animation_smooth": False,
                "viewport_responsive": False,
                "rendering_errors": [f"System error: {str(e)}"],
                "validation_details": {},
            }

    def _analyze_rendering_results(
        self,
        webgl_info: Dict[str, Any],
        threejs_info: Dict[str, Any],
        canvas_info: Dict[str, Any],
        rendering_test: Dict[str, Any],
        browser_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze rendering validation results and compile final assessment."""

        rendering_errors = []
        validation_details = {
            "webgl": webgl_info,
            "threejs": threejs_info,
            "canvas": canvas_info,
            "rendering_test": rendering_test,
            "browser_errors": browser_result.get("javascript_errors", []),
        }

        # WebGL validation
        webgl_supported = webgl_info.get("supported", False)
        webgl_version = webgl_info.get("version", "unknown")

        if not webgl_supported:
            rendering_errors.append("WebGL is not supported in this environment")

        # Three.js validation
        three_js_loaded = threejs_info.get("loaded", False)
        three_js_version = threejs_info.get("version", "unknown")

        if not three_js_loaded:
            rendering_errors.append("Three.js library not loaded")

        # Scene validation
        scene_rendered = False
        geometry_valid = False
        materials_loaded = False
        lighting_functional = False

        if three_js_loaded:
            scene_info = threejs_info.get("scene", {})
            renderer_info = threejs_info.get("renderer", {})
            camera_info = threejs_info.get("camera", {})

            # Check scene structure
            if scene_info.get("exists", False):
                geometry_valid = scene_info.get("geometries", 0) > 0
                materials_loaded = scene_info.get("materials", 0) > 0
                lighting_functional = scene_info.get("lights", 0) > 0

                if scene_info.get("objects", 0) == 0:
                    rendering_errors.append("Scene exists but contains no objects")

                if not geometry_valid:
                    rendering_errors.append("No geometries found in scene")

                if not materials_loaded:
                    rendering_errors.append("No materials found in scene")

                if not lighting_functional:
                    rendering_errors.append(
                        "No lights found in scene - may appear dark"
                    )
            else:
                rendering_errors.append("No Three.js scene found")

            # Check renderer
            if not renderer_info.get("exists", False):
                rendering_errors.append("No Three.js renderer found")
            elif renderer_info.get("type") != "WebGLRenderer":
                rendering_errors.append(
                    f"Non-WebGL renderer detected: {renderer_info.get('type')}"
                )

            # Check camera
            if not camera_info.get("exists", False):
                rendering_errors.append("No camera found")

            # Check rendering test
            if rendering_test.get("attempted", False):
                if rendering_test.get("successful", False):
                    scene_rendered = True
                else:
                    error_msg = rendering_test.get("error", "Unknown rendering error")
                    rendering_errors.append(f"Rendering failed: {error_msg}")
            else:
                rendering_errors.append(
                    "Could not attempt rendering - missing renderer, scene, or camera"
                )

        # Canvas validation
        canvas_count = canvas_info.get("total_count", 0)
        webgl_canvas_count = canvas_info.get("webgl_count", 0)
        visible_canvas_count = canvas_info.get("visible_count", 0)

        if canvas_count == 0:
            rendering_errors.append("No canvas elements found")
        elif webgl_canvas_count == 0:
            rendering_errors.append("No WebGL canvas contexts found")
        elif visible_canvas_count == 0:
            rendering_errors.append("Canvas elements exist but are not visible")

        # Check for context loss
        for canvas in canvas_info.get("canvases", []):
            if canvas.get("context", {}).get("lost", False):
                rendering_errors.append("WebGL context was lost")
                break

        # Texture validation (basic)
        textures_loaded = True  # Assume true unless we find evidence otherwise

        # Animation validation
        animation_smooth = rendering_test.get("animation_detected", False)

        # Viewport responsiveness (basic check)
        viewport_responsive = True
        if canvas_count > 0:
            for canvas in canvas_info.get("canvases", []):
                if canvas.get("visible", False):
                    # Check if canvas has reasonable size
                    if (
                        canvas.get("display_width", 0) < 100
                        or canvas.get("display_height", 0) < 100
                    ):
                        viewport_responsive = False
                        rendering_errors.append(
                            "Canvas appears too small for proper viewing"
                        )
                    break

        # Add browser-level errors
        js_errors = browser_result.get("javascript_errors", [])
        for error in js_errors:
            if any(
                keyword in error.get("message", "").lower()
                for keyword in ["webgl", "three", "canvas", "render"]
            ):
                rendering_errors.append(
                    f"JavaScript error: {error.get('message', 'Unknown error')}"
                )

        return {
            "webgl_supported": webgl_supported,
            "webgl_version": webgl_version,
            "three_js_loaded": three_js_loaded,
            "three_js_version": three_js_version,
            "scene_rendered": scene_rendered,
            "geometry_valid": geometry_valid,
            "materials_loaded": materials_loaded,
            "textures_loaded": textures_loaded,
            "lighting_functional": lighting_functional,
            "animation_smooth": animation_smooth,
            "viewport_responsive": viewport_responsive,
            "rendering_errors": rendering_errors,
            "validation_details": validation_details,
            "summary": {
                "canvas_count": canvas_count,
                "webgl_canvas_count": webgl_canvas_count,
                "visible_canvas_count": visible_canvas_count,
                "scene_objects": threejs_info.get("scene", {}).get("objects", 0),
                "scene_geometries": threejs_info.get("scene", {}).get("geometries", 0),
                "scene_materials": threejs_info.get("scene", {}).get("materials", 0),
                "scene_lights": threejs_info.get("scene", {}).get("lights", 0),
                "rendering_attempted": rendering_test.get("attempted", False),
                "rendering_successful": rendering_test.get("successful", False),
            },
        }

    def get_rendering_score(self, result: Dict[str, Any]) -> float:
        """Calculate a rendering quality score from 0-10."""
        score = 0.0

        # Base requirements (6 points total)
        if result.get("webgl_supported", False):
            score += 1.5
        if result.get("three_js_loaded", False):
            score += 1.5
        if result.get("scene_rendered", False):
            score += 1.5
        if result.get("geometry_valid", False):
            score += 1.5

        # Quality factors (4 points total)
        if result.get("materials_loaded", False):
            score += 1.0
        if result.get("lighting_functional", False):
            score += 1.0
        if result.get("animation_smooth", False):
            score += 1.0
        if result.get("viewport_responsive", False):
            score += 1.0

        # Penalties for errors
        error_count = len(result.get("rendering_errors", []))
        score -= min(5.0, error_count * 0.5)

        return max(0.0, min(10.0, score))

    def get_rendering_report(self, result: Dict[str, Any]) -> str:
        """Generate a human-readable rendering validation report."""
        score = self.get_rendering_score(result)
        errors = result.get("rendering_errors", [])

        report_lines = []

        # Overall status
        if score >= 8.0:
            report_lines.append("✅ Rendering validation passed with high quality")
        elif score >= 6.0:
            report_lines.append("⚠️ Rendering validation passed with some issues")
        else:
            report_lines.append("❌ Rendering validation failed")

        report_lines.append(f"🎨 Rendering Score: {score:.1f}/10.0")

        # Core capabilities
        report_lines.append("🔧 Core Capabilities:")
        report_lines.append(
            f"   WebGL: {'✅' if result.get('webgl_supported') else '❌'} {result.get('webgl_version', 'unknown')}"
        )
        report_lines.append(
            f"   Three.js: {'✅' if result.get('three_js_loaded') else '❌'} v{result.get('three_js_version', 'unknown')}"
        )
        report_lines.append(
            f"   Scene Rendering: {'✅' if result.get('scene_rendered') else '❌'}"
        )

        # Content validation
        report_lines.append("🎯 Content Validation:")
        report_lines.append(
            f"   Geometry: {'✅' if result.get('geometry_valid') else '❌'}"
        )
        report_lines.append(
            f"   Materials: {'✅' if result.get('materials_loaded') else '❌'}"
        )
        report_lines.append(
            f"   Lighting: {'✅' if result.get('lighting_functional') else '❌'}"
        )
        report_lines.append(
            f"   Animation: {'✅' if result.get('animation_smooth') else '❌'}"
        )

        # Scene statistics
        summary = result.get("summary", {})
        if summary:
            report_lines.append("📊 Scene Statistics:")
            report_lines.append(f"   Canvas Elements: {summary.get('canvas_count', 0)}")
            report_lines.append(
                f"   WebGL Contexts: {summary.get('webgl_canvas_count', 0)}"
            )
            report_lines.append(f"   Scene Objects: {summary.get('scene_objects', 0)}")
            report_lines.append(f"   Geometries: {summary.get('scene_geometries', 0)}")
            report_lines.append(f"   Materials: {summary.get('scene_materials', 0)}")
            report_lines.append(f"   Lights: {summary.get('scene_lights', 0)}")

        # Issues
        if errors:
            report_lines.append(f"⚠️ Issues Found ({len(errors)}):")
            for error in errors[:5]:  # Show first 5 errors
                report_lines.append(f"   • {error}")
            if len(errors) > 5:
                report_lines.append(f"   ... and {len(errors) - 5} more issues")

        return "\n".join(report_lines)
