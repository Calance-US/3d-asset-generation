"""
Three.js API specific validation service for 3D visualizations.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ThreeJSIssue:
    """Represents a Three.js specific validation issue."""

    type: str  # 'error', 'warning', 'info'
    category: str  # 'api', 'performance', 'memory', 'best_practice'
    message: str
    line_number: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical
    suggestion: Optional[str] = None


@dataclass
class ThreeJSValidationResult:
    """Result of Three.js validation."""

    is_valid: bool
    api_compliance_score: float
    performance_score: float
    memory_score: float
    issues: List[ThreeJSIssue]
    detected_objects: List[str]
    api_usage_stats: Dict[str, int]


class ThreeJSValidator:
    """Validator for Three.js API usage and best practices."""

    def __init__(self):
        # Valid Three.js material types and their supported properties
        self.material_properties = {
            "MeshBasicMaterial": {
                "required": ["color"],
                "optional": [
                    "map",
                    "alphaMap",
                    "aoMap",
                    "envMap",
                    "fog",
                    "lightMap",
                    "reflectivity",
                    "refractionRatio",
                    "wireframe",
                    "wireframeLinewidth",
                ],
                "forbidden": [
                    "metalness",
                    "roughness",
                    "normalMap",
                    "bumpMap",
                    "emissive",
                    "emissiveIntensity",
                ],
            },
            "MeshLambertMaterial": {
                "required": ["color"],
                "optional": [
                    "map",
                    "alphaMap",
                    "aoMap",
                    "emissive",
                    "emissiveMap",
                    "emissiveIntensity",
                    "envMap",
                    "lightMap",
                    "reflectivity",
                    "refractionRatio",
                    "wireframe",
                ],
                "forbidden": ["metalness", "roughness", "normalMap", "bumpMap"],
            },
            "MeshPhongMaterial": {
                "required": ["color"],
                "optional": [
                    "map",
                    "alphaMap",
                    "aoMap",
                    "bumpMap",
                    "bumpScale",
                    "emissive",
                    "emissiveMap",
                    "emissiveIntensity",
                    "envMap",
                    "lightMap",
                    "normalMap",
                    "normalScale",
                    "reflectivity",
                    "refractionRatio",
                    "shininess",
                    "specular",
                    "specularMap",
                    "wireframe",
                ],
                "forbidden": ["metalness", "roughness"],
            },
            "MeshStandardMaterial": {
                "required": ["color"],
                "optional": [
                    "map",
                    "alphaMap",
                    "aoMap",
                    "bumpMap",
                    "bumpScale",
                    "emissive",
                    "emissiveMap",
                    "emissiveIntensity",
                    "envMap",
                    "lightMap",
                    "metalness",
                    "metalnessMap",
                    "normalMap",
                    "normalScale",
                    "roughness",
                    "roughnessMap",
                    "wireframe",
                ],
                "forbidden": ["specular", "shininess"],
            },
            "MeshPhysicalMaterial": {
                "required": ["color"],
                "optional": [
                    "map",
                    "alphaMap",
                    "aoMap",
                    "bumpMap",
                    "bumpScale",
                    "clearcoat",
                    "clearcoatMap",
                    "clearcoatNormalMap",
                    "clearcoatRoughness",
                    "clearcoatRoughnessMap",
                    "emissive",
                    "emissiveMap",
                    "emissiveIntensity",
                    "envMap",
                    "ior",
                    "lightMap",
                    "metalness",
                    "metalnessMap",
                    "normalMap",
                    "normalScale",
                    "roughness",
                    "roughnessMap",
                    "sheen",
                    "sheenColor",
                    "sheenRoughness",
                    "transmission",
                    "transmissionMap",
                    "thickness",
                    "thicknessMap",
                    "wireframe",
                ],
                "forbidden": ["specular", "shininess"],
            },
            "LineBasicMaterial": {
                "required": ["color"],
                "optional": ["linewidth", "linecap", "linejoin", "fog"],
                "forbidden": [
                    "metalness",
                    "roughness",
                    "emissive",
                    "emissiveIntensity",
                    "map",
                    "normalMap",
                ],
            },
            "LineDashedMaterial": {
                "required": ["color", "dashSize", "gapSize"],
                "optional": ["linewidth", "scale", "fog"],
                "forbidden": [
                    "metalness",
                    "roughness",
                    "emissive",
                    "emissiveIntensity",
                    "map",
                    "normalMap",
                ],
            },
            "PointsMaterial": {
                "required": ["color"],
                "optional": ["map", "alphaMap", "size", "sizeAttenuation", "fog"],
                "forbidden": [
                    "metalness",
                    "roughness",
                    "emissive",
                    "emissiveIntensity",
                    "normalMap",
                ],
            },
        }

        # Valid shadow map types
        self.shadow_map_types = [
            "BasicShadowMap",
            "PCFShadowMap",
            "PCFSoftShadowMap",
            "VSMShadowMap",
        ]

        # Valid tone mapping types
        self.tone_mapping_types = [
            "NoToneMapping",
            "LinearToneMapping",
            "ReinhardToneMapping",
            "CineonToneMapping",
            "ACESFilmicToneMapping",
        ]

        # Valid color spaces
        self.color_spaces = [
            "SRGBColorSpace",
            "LinearSRGBColorSpace",
            "DisplayP3ColorSpace",
            "Rec2020ColorSpace",
            "XYZColorSpace",
        ]

        # Performance patterns to check
        self.performance_patterns = [
            (
                r"setInterval\(\s*function\s*\(\s*\)\s*\{[^}]*renderer\.render",
                "Using setInterval for render loop - use requestAnimationFrame instead",
            ),
            (
                r"new\s+THREE\.\w+Geometry\([^)]*\)\s*(?![\s;])",
                "Creating geometry in render loop - move outside for better performance",
            ),
            (
                r"renderer\.render\([^)]*\)[\s\S]*?renderer\.render\([^)]*\)",
                "Multiple render calls detected - may cause performance issues",
            ),
            (
                r"scene\.add\([^)]*\)[\s\S]*?scene\.remove\([^)]*\)",
                "Adding and removing objects frequently - consider object pooling",
            ),
        ]

        # Memory management patterns
        self.memory_patterns = [
            (
                r"new\s+THREE\.\w*Geometry\s*\([^)]*\)(?![^;]*\.dispose\(\))",
                "Geometry created without disposal - potential memory leak",
            ),
            (
                r"new\s+THREE\.\w*Material\s*\([^)]*\)(?![^;]*\.dispose\(\))",
                "Material created without disposal - potential memory leak",
            ),
            (
                r"new\s+THREE\.TextureLoader\(\)\.load\([^)]*\)(?![^;]*\.dispose\(\))",
                "Texture loaded without disposal - potential memory leak",
            ),
        ]

        # Required Three.js objects for a basic scene
        self.required_objects = {
            "scene": r"(?:const|let|var)\s+\w*scene\w*\s*=\s*new\s+THREE\.Scene\(\)",
            "camera": r"(?:const|let|var)\s+\w*camera\w*\s*=\s*new\s+THREE\.\w*Camera\(",
            "renderer": r"(?:const|let|var)\s+\w*renderer\w*\s*=\s*new\s+THREE\.WebGLRenderer\(",
        }

        # Best practice patterns
        self.best_practice_patterns = [
            (
                r"renderer\.setSize\(\s*window\.innerWidth\s*,\s*window\.innerHeight\s*\)",
                "Good: Using window dimensions for renderer size",
            ),
            (
                r'window\.addEventListener\(\s*["\']resize["\']',
                "Good: Handling window resize events",
            ),
            (
                r"camera\.aspect\s*=\s*window\.innerWidth\s*/\s*window\.innerHeight",
                "Good: Updating camera aspect ratio on resize",
            ),
            (
                r"controls\.update\(\)",
                "Good: Updating orbit controls in animation loop",
            ),
        ]

    async def validate_threejs_code(self, js_code: str) -> ThreeJSValidationResult:
        """
        Validate Three.js code for API compliance and best practices.

        Args:
            js_code: JavaScript code containing Three.js usage

        Returns:
            ThreeJSValidationResult with validation details
        """
        issues = []
        detected_objects = []
        api_usage_stats = {}

        try:
            # 1. Validate material usage
            material_issues = self._validate_materials(js_code)
            issues.extend(material_issues)

            # 2. Validate renderer configuration
            renderer_issues = self._validate_renderer_config(js_code)
            issues.extend(renderer_issues)

            # 3. Check for required objects
            required_issues, detected = self._validate_required_objects(js_code)
            issues.extend(required_issues)
            detected_objects.extend(detected)

            # 4. Validate performance patterns
            performance_issues = self._validate_performance_patterns(js_code)
            issues.extend(performance_issues)

            # 5. Check memory management
            memory_issues = self._validate_memory_management(js_code)
            issues.extend(memory_issues)

            # 6. Validate API usage
            api_issues, stats = self._validate_api_usage(js_code)
            issues.extend(api_issues)
            api_usage_stats.update(stats)

            # 7. Check best practices
            best_practice_issues = self._validate_best_practices(js_code)
            issues.extend(best_practice_issues)

            # Calculate scores
            api_compliance_score = self._calculate_api_compliance_score(issues)
            performance_score = self._calculate_performance_score(issues)
            memory_score = self._calculate_memory_score(issues)

            # Determine overall validity
            is_valid = not any(issue.severity >= 4 for issue in issues)

            logger.info(f"Three.js validation completed: {len(issues)} issues found")

            return ThreeJSValidationResult(
                is_valid=is_valid,
                api_compliance_score=api_compliance_score,
                performance_score=performance_score,
                memory_score=memory_score,
                issues=issues,
                detected_objects=detected_objects,
                api_usage_stats=api_usage_stats,
            )

        except Exception as e:
            logger.error(f"Error during Three.js validation: {str(e)}")
            issues.append(
                ThreeJSIssue(
                    type="error",
                    category="validation",
                    message=f"Three.js validation failed: {str(e)}",
                    severity=5,
                )
            )

            return ThreeJSValidationResult(
                is_valid=False,
                api_compliance_score=0.0,
                performance_score=0.0,
                memory_score=0.0,
                issues=issues,
                detected_objects=[],
                api_usage_stats={},
            )

    def _validate_materials(self, js_code: str) -> List[ThreeJSIssue]:
        """Validate Three.js material usage."""
        issues = []

        # Find all material creations
        material_pattern = r"new\s+THREE\.(\w+Material)\s*\(\s*\{([^}]*)\}\s*\)"
        materials = re.finditer(material_pattern, js_code, re.MULTILINE | re.DOTALL)

        for match in materials:
            material_type = match.group(1)
            properties_str = match.group(2)
            line_num = js_code[: match.start()].count("\n") + 1

            if material_type not in self.material_properties:
                issues.append(
                    ThreeJSIssue(
                        type="warning",
                        category="api",
                        message=f"Unknown material type: {material_type}",
                        line_number=line_num,
                        severity=2,
                    )
                )
                continue

            # Parse properties
            prop_pattern = r"(\w+):\s*([^,}]+)"
            properties = re.findall(prop_pattern, properties_str)

            material_config = self.material_properties[material_type]

            for prop_name, prop_value in properties:
                prop_name = prop_name.strip()

                # Check forbidden properties
                if prop_name in material_config.get("forbidden", []):
                    issues.append(
                        ThreeJSIssue(
                            type="error",
                            category="api",
                            message=f"{material_type} does not support property '{prop_name}'",
                            line_number=line_num,
                            severity=4,
                            suggestion=f"Remove '{prop_name}' property or use a different material type",
                        )
                    )

                # Validate property values
                if prop_name == "metalness" or prop_name == "roughness":
                    try:
                        value = float(prop_value.strip())
                        if not (0.0 <= value <= 1.0):
                            issues.append(
                                ThreeJSIssue(
                                    type="warning",
                                    category="api",
                                    message=f"{prop_name} should be between 0.0 and 1.0, got {value}",
                                    line_number=line_num,
                                    severity=2,
                                    suggestion=f"Clamp {prop_name} value to range [0.0, 1.0]",
                                )
                            )
                    except ValueError:
                        pass  # Not a numeric value, skip validation

                # Validate realistic material combinations
                if material_type in ["MeshStandardMaterial", "MeshPhysicalMaterial"]:
                    issues.extend(
                        self._validate_material_realism(
                            material_type, properties, line_num
                        )
                    )

        return issues

    def _validate_material_realism(
        self, material_type: str, properties: List[Tuple[str, str]], line_num: int
    ) -> List[ThreeJSIssue]:
        """Validate material property combinations for realism."""
        issues = []

        metalness = None
        roughness = None

        for prop_name, prop_value in properties:
            if prop_name == "metalness":
                try:
                    metalness = float(prop_value.strip())
                except ValueError:
                    continue
            elif prop_name == "roughness":
                try:
                    roughness = float(prop_value.strip())
                except ValueError:
                    continue

        if metalness is not None and roughness is not None:
            # Check for unrealistic combinations
            if metalness > 0.8 and roughness > 0.7:
                issues.append(
                    ThreeJSIssue(
                        type="warning",
                        category="best_practice",
                        message="Unrealistic material: very high metalness with very high roughness",
                        line_number=line_num,
                        severity=1,
                        suggestion="Metals typically have lower roughness when highly metallic",
                    )
                )
            elif metalness < 0.1 and roughness < 0.1:
                issues.append(
                    ThreeJSIssue(
                        type="info",
                        category="best_practice",
                        message="Very smooth non-metallic material - ensure this is intentional",
                        line_number=line_num,
                        severity=1,
                        suggestion="Consider if this material combination is realistic for your object",
                    )
                )

        return issues

    def _validate_renderer_config(self, js_code: str) -> List[ThreeJSIssue]:
        """Validate WebGL renderer configuration."""
        issues = []

        # Find renderer creation
        renderer_pattern = r"new\s+THREE\.WebGLRenderer\s*\(\s*\{([^}]*)\}\s*\)"
        renderer_match = re.search(renderer_pattern, js_code, re.MULTILINE | re.DOTALL)

        if renderer_match:
            config_str = renderer_match.group(1)
            line_num = js_code[: renderer_match.start()].count("\n") + 1

            # Check for antialias
            if "antialias" not in config_str:
                issues.append(
                    ThreeJSIssue(
                        type="info",
                        category="best_practice",
                        message="Consider enabling antialiasing for better visual quality",
                        line_number=line_num,
                        severity=1,
                        suggestion="Add 'antialias: true' to renderer options",
                    )
                )

        # Validate shadow map configuration
        shadow_map_pattern = r"renderer\.shadowMap\.type\s*=\s*THREE\.(\w+)"
        shadow_matches = re.finditer(shadow_map_pattern, js_code)

        for match in shadow_matches:
            shadow_type = match.group(1)
            line_num = js_code[: match.start()].count("\n") + 1

            if shadow_type not in self.shadow_map_types:
                issues.append(
                    ThreeJSIssue(
                        type="error",
                        category="api",
                        message=f"Invalid shadow map type: {shadow_type}",
                        line_number=line_num,
                        severity=3,
                        suggestion=f"Use one of: {', '.join(self.shadow_map_types)}",
                    )
                )

        # Validate tone mapping
        tone_mapping_pattern = r"renderer\.toneMapping\s*=\s*THREE\.(\w+)"
        tone_matches = re.finditer(tone_mapping_pattern, js_code)

        for match in tone_matches:
            tone_type = match.group(1)
            line_num = js_code[: match.start()].count("\n") + 1

            if tone_type not in self.tone_mapping_types:
                issues.append(
                    ThreeJSIssue(
                        type="error",
                        category="api",
                        message=f"Invalid tone mapping type: {tone_type}",
                        line_number=line_num,
                        severity=3,
                        suggestion=f"Use one of: {', '.join(self.tone_mapping_types)}",
                    )
                )

        # Validate color space
        color_space_pattern = r"renderer\.outputColorSpace\s*=\s*THREE\.(\w+)"
        color_matches = re.finditer(color_space_pattern, js_code)

        for match in color_matches:
            color_space = match.group(1)
            line_num = js_code[: match.start()].count("\n") + 1

            if color_space not in self.color_spaces:
                issues.append(
                    ThreeJSIssue(
                        type="error",
                        category="api",
                        message=f"Invalid color space: {color_space}",
                        line_number=line_num,
                        severity=3,
                        suggestion=f"Use one of: {', '.join(self.color_spaces)}",
                    )
                )

        return issues

    def _validate_required_objects(
        self, js_code: str
    ) -> Tuple[List[ThreeJSIssue], List[str]]:
        """Validate presence of required Three.js objects."""
        issues = []
        detected_objects = []

        for obj_name, pattern in self.required_objects.items():
            if re.search(pattern, js_code, re.IGNORECASE):
                detected_objects.append(obj_name)
            else:
                issues.append(
                    ThreeJSIssue(
                        type="error",
                        category="api",
                        message=f"Missing required Three.js object: {obj_name}",
                        severity=4,
                        suggestion=f"Create a {obj_name} object using appropriate Three.js constructor",
                    )
                )

        return issues, detected_objects

    def _validate_performance_patterns(self, js_code: str) -> List[ThreeJSIssue]:
        """Validate performance-related patterns."""
        issues = []

        for pattern, message in self.performance_patterns:
            matches = re.finditer(pattern, js_code, re.MULTILINE | re.DOTALL)
            for match in matches:
                line_num = js_code[: match.start()].count("\n") + 1
                issues.append(
                    ThreeJSIssue(
                        type="warning",
                        category="performance",
                        message=message,
                        line_number=line_num,
                        severity=2,
                    )
                )

        return issues

    def _validate_memory_management(self, js_code: str) -> List[ThreeJSIssue]:
        """Validate memory management patterns."""
        issues = []

        for pattern, message in self.memory_patterns:
            matches = re.finditer(pattern, js_code, re.MULTILINE | re.DOTALL)
            for match in matches:
                line_num = js_code[: match.start()].count("\n") + 1
                issues.append(
                    ThreeJSIssue(
                        type="warning",
                        category="memory",
                        message=message,
                        line_number=line_num,
                        severity=2,
                        suggestion="Call .dispose() on geometries, materials, and textures when no longer needed",
                    )
                )

        return issues

    def _validate_api_usage(
        self, js_code: str
    ) -> Tuple[List[ThreeJSIssue], Dict[str, int]]:
        """Validate general Three.js API usage and collect statistics."""
        issues = []
        stats = {
            "geometries": 0,
            "materials": 0,
            "lights": 0,
            "meshes": 0,
            "cameras": 0,
            "controls": 0,
        }

        # Count different object types
        patterns = {
            "geometries": r"new\s+THREE\.\w*Geometry",
            "materials": r"new\s+THREE\.\w*Material",
            "lights": r"new\s+THREE\.\w*Light",
            "meshes": r"new\s+THREE\.Mesh",
            "cameras": r"new\s+THREE\.\w*Camera",
            "controls": r"new\s+\w*Controls",
        }

        for category, pattern in patterns.items():
            matches = re.findall(pattern, js_code)
            stats[category] = len(matches)

        # Check for deprecated API usage
        deprecated_patterns = [
            (
                r"THREE\.Geometry\(\)",
                "THREE.Geometry is deprecated - use THREE.BufferGeometry",
            ),
            (r"\.setRGB\(", ".setRGB() is deprecated - use .setHSL() or .set()"),
            (
                r"THREE\.Face3",
                "THREE.Face3 is deprecated - use BufferGeometry with indices",
            ),
        ]

        for pattern, message in deprecated_patterns:
            matches = re.finditer(pattern, js_code)
            for match in matches:
                line_num = js_code[: match.start()].count("\n") + 1
                issues.append(
                    ThreeJSIssue(
                        type="warning",
                        category="api",
                        message=message,
                        line_number=line_num,
                        severity=2,
                    )
                )

        return issues, stats

    def _validate_best_practices(self, js_code: str) -> List[ThreeJSIssue]:
        """Validate Three.js best practices."""
        issues = []

        # Check for animation loop
        if not re.search(r"requestAnimationFrame", js_code):
            issues.append(
                ThreeJSIssue(
                    type="warning",
                    category="best_practice",
                    message="No requestAnimationFrame found - animations may not work smoothly",
                    severity=2,
                    suggestion="Use requestAnimationFrame for smooth animations",
                )
            )

        # Check for proper resize handling
        if not re.search(r"window\.addEventListener.*resize", js_code):
            issues.append(
                ThreeJSIssue(
                    type="info",
                    category="best_practice",
                    message="No window resize handler found - scene may not be responsive",
                    severity=1,
                    suggestion="Add window resize event listener to handle viewport changes",
                )
            )

        # Check for control updates
        if "Controls" in js_code and not re.search(r"controls\.update\(\)", js_code):
            issues.append(
                ThreeJSIssue(
                    type="info",
                    category="best_practice",
                    message="Controls created but update() not called in animation loop",
                    severity=1,
                    suggestion="Call controls.update() in your animation loop",
                )
            )

        return issues

    def _calculate_api_compliance_score(self, issues: List[ThreeJSIssue]) -> float:
        """Calculate API compliance score based on issues."""
        base_score = 10.0

        for issue in issues:
            if issue.category == "api":
                if issue.severity == 5:
                    base_score -= 3.0
                elif issue.severity == 4:
                    base_score -= 2.0
                elif issue.severity == 3:
                    base_score -= 1.0
                elif issue.severity == 2:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_performance_score(self, issues: List[ThreeJSIssue]) -> float:
        """Calculate performance score based on issues."""
        base_score = 10.0

        for issue in issues:
            if issue.category == "performance":
                if issue.severity >= 3:
                    base_score -= 2.0
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_memory_score(self, issues: List[ThreeJSIssue]) -> float:
        """Calculate memory management score based on issues."""
        base_score = 10.0

        for issue in issues:
            if issue.category == "memory":
                if issue.severity >= 3:
                    base_score -= 1.5
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def get_validation_summary(self, result: ThreeJSValidationResult) -> str:
        """Generate a human-readable validation summary."""
        summary_parts = []

        if result.is_valid:
            summary_parts.append("✅ Three.js code is valid")
        else:
            summary_parts.append("❌ Three.js code has critical issues")

        summary_parts.append(f"API Compliance: {result.api_compliance_score:.1f}/10")
        summary_parts.append(f"Performance: {result.performance_score:.1f}/10")
        summary_parts.append(f"Memory: {result.memory_score:.1f}/10")

        # Issue breakdown
        error_count = sum(1 for issue in result.issues if issue.type == "error")
        warning_count = sum(1 for issue in result.issues if issue.type == "warning")

        if error_count > 0:
            summary_parts.append(f"🔴 {error_count} errors")
        if warning_count > 0:
            summary_parts.append(f"🟡 {warning_count} warnings")

        # Object counts
        if result.api_usage_stats:
            objects_summary = []
            for obj_type, count in result.api_usage_stats.items():
                if count > 0:
                    objects_summary.append(f"{count} {obj_type}")
            if objects_summary:
                summary_parts.append(f"Objects: {', '.join(objects_summary)}")

        return " | ".join(summary_parts)
