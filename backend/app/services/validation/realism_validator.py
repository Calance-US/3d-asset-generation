"""
Realistic property validation service for materials and physical properties in 3D visualizations.
"""

import colorsys
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class RealismIssue:
    """Represents a realism validation issue."""

    type: str  # 'error', 'warning', 'info'
    category: str  # 'material', 'lighting', 'scale', 'color', 'physics'
    message: str
    line_number: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical
    suggestion: Optional[str] = None
    realistic_context: Optional[str] = None


@dataclass
class RealismValidationResult:
    """Result of realism validation."""

    is_realistic: bool
    realism_score: float  # 0-10 scale
    material_realism_score: float
    lighting_realism_score: float
    scale_realism_score: float
    color_harmony_score: float
    issues: List[RealismIssue]
    detected_materials: List[str]
    lighting_analysis: Dict[str, any]


class RealismValidator:
    """Validator for realistic materials, lighting, and physical properties."""

    def __init__(self):
        # Realistic material property ranges
        self.material_properties = {
            # Metals
            "metals": {
                "metalness": {"min": 0.8, "max": 1.0, "typical": 0.9},
                "roughness": {"min": 0.0, "max": 0.3, "typical": 0.1},
                "examples": ["aluminum", "steel", "copper", "gold", "silver", "iron"],
                "colors": {
                    "aluminum": "#C0C0C0",
                    "steel": "#71797E",
                    "copper": "#B87333",
                    "gold": "#FFD700",
                    "silver": "#C0C0C0",
                    "iron": "#464451",
                },
            },
            # Plastics
            "plastics": {
                "metalness": {"min": 0.0, "max": 0.1, "typical": 0.0},
                "roughness": {"min": 0.3, "max": 0.9, "typical": 0.6},
                "examples": ["abs", "pvc", "polystyrene", "acrylic", "nylon"],
                "colors": {
                    "typical_range": {
                        "hue": (0, 360),
                        "saturation": (0.2, 0.8),
                        "lightness": (0.3, 0.9),
                    }
                },
            },
            # Wood
            "wood": {
                "metalness": {"min": 0.0, "max": 0.05, "typical": 0.0},
                "roughness": {"min": 0.6, "max": 0.9, "typical": 0.8},
                "examples": ["oak", "pine", "mahogany", "birch", "maple"],
                "colors": {
                    "oak": "#8B4513",
                    "pine": "#FFA500",
                    "mahogany": "#C04000",
                    "birch": "#F5DEB3",
                    "maple": "#D2691E",
                },
            },
            # Glass
            "glass": {
                "metalness": {"min": 0.0, "max": 0.1, "typical": 0.0},
                "roughness": {"min": 0.0, "max": 0.1, "typical": 0.05},
                "transmission": {"min": 0.8, "max": 1.0, "typical": 0.95},
                "examples": ["clear_glass", "frosted_glass", "tinted_glass"],
                "colors": {
                    "clear_glass": "#FFFFFF",
                    "frosted_glass": "#F0F0F0",
                    "tinted_glass": "#E6E6FA",
                },
            },
            # Ceramics
            "ceramics": {
                "metalness": {"min": 0.0, "max": 0.05, "typical": 0.0},
                "roughness": {"min": 0.1, "max": 0.8, "typical": 0.3},
                "examples": ["porcelain", "terracotta", "stoneware"],
                "colors": {
                    "porcelain": "#FAEBD7",
                    "terracotta": "#E2725B",
                    "stoneware": "#8FBC8F",
                },
            },
            # Rubber
            "rubber": {
                "metalness": {"min": 0.0, "max": 0.0, "typical": 0.0},
                "roughness": {"min": 0.8, "max": 1.0, "typical": 0.9},
                "examples": ["silicone", "latex", "neoprene"],
                "colors": {
                    "typical_range": {
                        "hue": (0, 360),
                        "saturation": (0.1, 0.6),
                        "lightness": (0.1, 0.8),
                    }
                },
            },
            # Fabric/Textile
            "fabric": {
                "metalness": {"min": 0.0, "max": 0.0, "typical": 0.0},
                "roughness": {"min": 0.7, "max": 1.0, "typical": 0.9},
                "examples": ["cotton", "wool", "silk", "denim", "canvas"],
                "colors": {
                    "typical_range": {
                        "hue": (0, 360),
                        "saturation": (0.2, 0.9),
                        "lightness": (0.2, 0.9),
                    }
                },
            },
        }

        # Realistic lighting setups
        self.lighting_setups = {
            "three_point_lighting": {
                "key_light": {"intensity": 1.0, "position": "front_45_degrees"},
                "fill_light": {"intensity": 0.3, "position": "opposite_key"},
                "back_light": {"intensity": 0.5, "position": "behind_subject"},
                "ratio": "3:1:1.5",
            },
            "natural_lighting": {
                "sun": {"intensity": 1.0, "color": "#FFF8DC", "angle": "variable"},
                "sky": {"intensity": 0.3, "color": "#87CEEB", "type": "ambient"},
                "ground_bounce": {"intensity": 0.1, "color": "#F5F5DC"},
            },
            "indoor_lighting": {
                "ambient": {"intensity": 0.2, "color": "#FFFFFF"},
                "main_light": {"intensity": 0.8, "color": "#FFFACD"},
                "accent_lights": {"intensity": 0.4, "color": "#FFFFFF"},
            },
        }

        # Realistic scale relationships
        self.scale_references = {
            # Common objects for scale reference (in meters)
            "household_objects": {
                "coffee_cup": {"height": 0.1, "diameter": 0.08},
                "smartphone": {"height": 0.15, "width": 0.075, "depth": 0.008},
                "laptop": {"width": 0.35, "depth": 0.25, "thickness": 0.02},
                "book": {"height": 0.24, "width": 0.16, "thickness": 0.03},
                "chair": {"height": 0.8, "width": 0.5, "depth": 0.5},
                "table": {"height": 0.75, "width": 1.2, "depth": 0.8},
            },
            "electronic_components": {
                "resistor": {"length": 0.006, "diameter": 0.002},
                "led": {"diameter": 0.005, "height": 0.008},
                "battery_aa": {"height": 0.05, "diameter": 0.014},
                "battery_9v": {"height": 0.048, "width": 0.026, "depth": 0.017},
                "breadboard": {"width": 0.165, "height": 0.055, "depth": 0.01},
            },
            "chemistry_equipment": {
                "test_tube": {"height": 0.15, "diameter": 0.016},
                "beaker_250ml": {"height": 0.095, "diameter": 0.07},
                "erlenmeyer_flask": {"height": 0.105, "diameter": 0.065},
                "pipette": {"length": 0.23, "diameter": 0.007},
                "burette": {"height": 0.5, "diameter": 0.015},
            },
        }

        # Color harmony rules
        self.color_harmony_rules = {
            "complementary": "colors_opposite_on_color_wheel",
            "analogous": "colors_adjacent_on_color_wheel",
            "triadic": "three_colors_evenly_spaced",
            "split_complementary": "base_color_plus_two_adjacent_to_complement",
            "monochromatic": "different_shades_of_same_hue",
        }

        # Physics-based constraints
        self.physics_constraints = {
            "gravity": {
                "earth": 9.81,  # m/s²
                "objects_fall_down": True,
                "stable_configurations": ["supported_base", "hanging_from_above"],
            },
            "structural_integrity": {
                "max_cantilever_ratio": 3.0,  # length to support ratio
                "min_support_area": 0.1,  # fraction of object area for stable support
            },
            "electrical_circuits": {
                "current_flow": "positive_to_negative",
                "series_vs_parallel": "different_behavior",
                "wire_connections": "must_be_physically_connected",
            },
        }

        # Unrealistic combinations to flag
        self.unrealistic_combinations = [
            {
                "condition": lambda m, r: m > 0.8 and r > 0.7,
                "message": "Very high metalness with very high roughness is unrealistic",
                "suggestion": "Metals typically have lower roughness values (0.0-0.3)",
            },
            {
                "condition": lambda m, r: m < 0.1 and r < 0.1,
                "message": "Very low metalness with very low roughness (mirror-like non-metal)",
                "suggestion": "Consider if this ultra-smooth non-metallic surface is realistic",
            },
            {
                "condition": lambda m, r: 0.3 < m < 0.7,
                "message": "Intermediate metalness values (0.3-0.7) are rarely realistic",
                "suggestion": "Materials are typically either metallic (>0.8) or non-metallic (<0.2)",
            },
        ]

    async def validate_realism(
        self, content: str, components: List[Dict] = None, subject: str = "physics"
    ) -> RealismValidationResult:
        """
        Validate visual realism of the content.

        Args:
            content: HTML/JS content to validate
            components: List of component descriptions from config
            subject: Subject area for context

        Returns:
            RealismValidationResult with validation details
        """
        issues = []
        detected_materials = []
        lighting_analysis = {}

        try:
            # 1. Material property validation
            material_issues, materials = self._validate_material_properties(content)
            issues.extend(material_issues)
            detected_materials.extend(materials)

            # 2. Lighting setup validation
            lighting_issues, lighting_info = self._validate_lighting_setup(content)
            issues.extend(lighting_issues)
            lighting_analysis.update(lighting_info)

            # 3. Scale and proportion validation
            scale_issues = self._validate_proportions(
                content, components or [], subject
            )
            issues.extend(scale_issues)

            # 4. Color harmony validation
            color_issues = self._validate_color_harmony(content)
            issues.extend(color_issues)

            # 5. Physics-based validation
            physics_issues = self._validate_physics_constraints(content, subject)
            issues.extend(physics_issues)

            # Calculate scores
            material_score = self._calculate_material_score(material_issues)
            lighting_score = self._calculate_lighting_score(lighting_issues)
            scale_score = self._calculate_scale_score(scale_issues)
            color_score = self._calculate_color_score(color_issues)

            # Overall realism score
            realism_score = (
                material_score + lighting_score + scale_score + color_score
            ) / 4

            # Determine if realistic
            is_realistic = not any(issue.severity >= 4 for issue in issues)

            logger.info(
                "Realism validation completed",
                extra={
                    "total_issues": len(issues),
                    "realism_score": realism_score,
                    "detected_materials": detected_materials,
                },
            )

            return RealismValidationResult(
                is_realistic=is_realistic,
                realism_score=realism_score,
                material_realism_score=material_score,
                lighting_realism_score=lighting_score,
                scale_realism_score=scale_score,
                color_harmony_score=color_score,
                issues=issues,
                detected_materials=detected_materials,
                lighting_analysis=lighting_analysis,
            )

        except Exception as e:
            logger.error(f"Error during realism validation: {str(e)}")
            issues.append(
                RealismIssue(
                    type="error",
                    category="validation",
                    message=f"Realism validation failed: {str(e)}",
                    severity=5,
                )
            )

            return RealismValidationResult(
                is_realistic=False,
                realism_score=0.0,
                material_realism_score=0.0,
                lighting_realism_score=0.0,
                scale_realism_score=0.0,
                color_harmony_score=0.0,
                issues=issues,
                detected_materials=[],
                lighting_analysis={},
            )

    def _validate_material_properties(
        self, content: str
    ) -> Tuple[List[RealismIssue], List[str]]:
        """Validate material property combinations for realism."""
        issues = []
        detected_materials = []

        # Extract material definitions
        material_pattern = r"new\s+THREE\.Mesh\w*Material\s*\(\s*\{([^}]+)\}\s*\)"
        materials = re.finditer(material_pattern, content, re.MULTILINE | re.DOTALL)

        for match in materials:
            properties_str = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # Parse properties
            prop_pattern = r"(\w+):\s*([^,}]+)"
            properties = dict(re.findall(prop_pattern, properties_str))

            # Extract numeric values
            metalness = None
            roughness = None
            color = None

            try:
                if "metalness" in properties:
                    metalness = float(properties["metalness"].strip())
                if "roughness" in properties:
                    roughness = float(properties["roughness"].strip())
                if "color" in properties:
                    color = properties["color"].strip()
            except ValueError:
                continue

            # Validate material property combinations
            if metalness is not None and roughness is not None:
                # Check against unrealistic combinations
                for combo in self.unrealistic_combinations:
                    if combo["condition"](metalness, roughness):
                        issues.append(
                            RealismIssue(
                                type="warning",
                                category="material",
                                message=combo["message"],
                                line_number=line_num,
                                severity=2,
                                suggestion=combo["suggestion"],
                                realistic_context=f"Metalness: {metalness}, Roughness: {roughness}",
                            )
                        )

                # Suggest realistic material type
                suggested_material = self._suggest_material_type(metalness, roughness)
                if suggested_material:
                    detected_materials.append(suggested_material)

            # Validate color realism for specific materials
            if color and metalness is not None:
                color_issues = self._validate_material_color(
                    color, metalness, roughness
                )
                issues.extend(color_issues)

        return issues, detected_materials

    def _validate_lighting_setup(
        self, content: str
    ) -> Tuple[List[RealismIssue], Dict[str, any]]:
        """Validate lighting setup for realism."""
        issues = []
        lighting_info = {
            "light_count": 0,
            "light_types": [],
            "intensity_range": {"min": float("inf"), "max": 0},
            "has_ambient": False,
            "has_directional": False,
            "has_point": False,
        }

        # Find all light creations
        light_pattern = r"new\s+THREE\.(\w*Light)\s*\([^)]*intensity[:\s]*([0-9.]+)"
        lights = re.finditer(light_pattern, content, re.IGNORECASE)

        intensities = []
        light_types = []

        for match in lights:
            light_type = match.group(1)
            try:
                intensity = float(match.group(2))
                intensities.append(intensity)
                light_types.append(light_type)
                lighting_info["light_count"] += 1

                if light_type == "AmbientLight":
                    lighting_info["has_ambient"] = True
                elif light_type == "DirectionalLight":
                    lighting_info["has_directional"] = True
                elif light_type == "PointLight":
                    lighting_info["has_point"] = True

            except ValueError:
                continue

        lighting_info["light_types"] = light_types

        if intensities:
            lighting_info["intensity_range"]["min"] = min(intensities)
            lighting_info["intensity_range"]["max"] = max(intensities)

            # Check for realistic intensity ratios
            if len(intensities) > 1:
                intensity_ratio = max(intensities) / min(intensities)
                if intensity_ratio > 10.0:
                    issues.append(
                        RealismIssue(
                            type="warning",
                            category="lighting",
                            message=f"Very high light intensity ratio ({intensity_ratio:.1f}:1) may cause harsh lighting",
                            severity=2,
                            suggestion="Consider more balanced lighting ratios (typically 3:1 to 5:1)",
                            realistic_context="Professional lighting uses key:fill ratios of 2:1 to 4:1",
                        )
                    )

            # Check for extremely high intensities
            if max(intensities) > 5.0:
                issues.append(
                    RealismIssue(
                        type="warning",
                        category="lighting",
                        message=f"Very high light intensity ({max(intensities)}) may cause overexposure",
                        severity=2,
                        suggestion="Consider using intensities between 0.1 and 2.0 for realistic lighting",
                    )
                )

        # Check for basic lighting setup
        if lighting_info["light_count"] == 0:
            issues.append(
                RealismIssue(
                    type="error",
                    category="lighting",
                    message="No lights detected - scene will be completely dark",
                    severity=4,
                    suggestion="Add at least an ambient light and one directional light",
                )
            )
        elif lighting_info["light_count"] == 1 and lighting_info["has_ambient"]:
            issues.append(
                RealismIssue(
                    type="warning",
                    category="lighting",
                    message="Only ambient lighting - objects will appear flat",
                    severity=2,
                    suggestion="Add directional or point lights for depth and dimension",
                )
            )

        return issues, lighting_info

    def _validate_proportions(
        self, content: str, components: List[Dict], subject: str
    ) -> List[RealismIssue]:
        """Validate scale and proportions."""
        issues = []

        # Get appropriate scale references for the subject
        if subject.lower() == "physics":
            scale_refs = {
                **self.scale_references["household_objects"],
                **self.scale_references["electronic_components"],
            }
        elif subject.lower() == "chemistry":
            scale_refs = {
                **self.scale_references["household_objects"],
                **self.scale_references["chemistry_equipment"],
            }
        else:
            scale_refs = self.scale_references["household_objects"]

        # Extract geometry creations with dimensions
        geometry_pattern = r"new\s+THREE\.(\w+Geometry)\s*\(\s*([^)]+)\s*\)"
        geometries = re.finditer(geometry_pattern, content)

        for match in geometries:
            geometry_type = match.group(1)
            params_str = match.group(2)
            line_num = content[: match.start()].count("\n") + 1

            try:
                # Parse numeric parameters
                params = [
                    float(p.strip())
                    for p in params_str.split(",")
                    if p.strip().replace(".", "").isdigit()
                ]

                if geometry_type == "BoxGeometry" and len(params) >= 3:
                    width, height, depth = params[0], params[1], params[2]

                    # Check for unrealistic proportions
                    if max(width, height, depth) / min(width, height, depth) > 20:
                        issues.append(
                            RealismIssue(
                                type="warning",
                                category="scale",
                                message=f"Extreme aspect ratio in box geometry ({max(width, height, depth):.1f}:{min(width, height, depth):.1f})",
                                line_number=line_num,
                                severity=2,
                                suggestion="Consider more realistic proportions for better visual appearance",
                            )
                        )

                    # Check against known object scales
                    self._check_component_scale(
                        width, height, depth, components, issues, line_num
                    )

            except (ValueError, IndexError):
                continue

        return issues

    def _validate_color_harmony(self, content: str) -> List[RealismIssue]:
        """Validate color harmony and realistic color choices."""
        issues = []

        # Extract color values
        color_pattern = r"color:\s*(0x[0-9a-fA-F]{6}|#[0-9a-fA-F]{6}|[0-9]+)"
        colors = re.findall(color_pattern, content)

        if len(colors) < 2:
            return issues  # Can't evaluate harmony with fewer than 2 colors

        # Convert colors to HSL for analysis
        hsl_colors = []
        for color_str in colors:
            try:
                if color_str.startswith("0x"):
                    rgb = tuple(int(color_str[2:][i : i + 2], 16) for i in (0, 2, 4))
                elif color_str.startswith("#"):
                    rgb = tuple(int(color_str[1:][i : i + 2], 16) for i in (0, 2, 4))
                else:
                    # Decimal color value
                    color_int = int(color_str)
                    rgb = (
                        (color_int >> 16) & 255,
                        (color_int >> 8) & 255,
                        color_int & 255,
                    )

                # Convert to HSL
                r, g, b = [x / 255.0 for x in rgb]
                h, l, s = colorsys.rgb_to_hls(r, g, b)
                hsl_colors.append((h * 360, s, l))  # Convert hue to degrees

            except (ValueError, IndexError):
                continue

        if len(hsl_colors) >= 2:
            # Check for color harmony
            harmony_issues = self._analyze_color_harmony(hsl_colors)
            issues.extend(harmony_issues)

            # Check for realistic color choices
            realism_issues = self._analyze_color_realism(hsl_colors)
            issues.extend(realism_issues)

        return issues

    def _validate_physics_constraints(
        self, content: str, subject: str
    ) -> List[RealismIssue]:
        """Validate physics-based constraints."""
        issues = []

        # Check for objects floating without support
        position_pattern = (
            r"(\w+)\.position\.set\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)"
        )
        positions = re.finditer(position_pattern, content)

        floating_objects = []
        for match in positions:
            obj_name = match.group(1)
            try:
                x, y, z = (
                    float(match.group(2)),
                    float(match.group(3)),
                    float(match.group(4)),
                )
                if y > 0.5:  # Objects positioned high above ground
                    floating_objects.append((obj_name, y))
            except ValueError:
                continue

        if floating_objects and subject.lower() == "physics":
            for obj_name, height in floating_objects:
                if height > 2.0:  # Very high positioning
                    issues.append(
                        RealismIssue(
                            type="info",
                            category="physics",
                            message=f"Object '{obj_name}' positioned very high (y={height:.1f}) - ensure it has visible support",
                            severity=1,
                            suggestion="Add visual supports or indicate how the object is suspended",
                            realistic_context="Objects need support against gravity in realistic scenes",
                        )
                    )

        # Check for electrical circuit realism (physics subject)
        if subject.lower() == "physics" and any(
            word in content.lower()
            for word in ["circuit", "wire", "battery", "resistor"]
        ):
            # Ensure wires connect components
            if "wire" in content.lower() and "connect" not in content.lower():
                issues.append(
                    RealismIssue(
                        type="warning",
                        category="physics",
                        message="Circuit visualization should show clear connections between components",
                        severity=2,
                        suggestion="Add visual representations of wire connections between circuit elements",
                    )
                )

        return issues

    def _suggest_material_type(
        self, metalness: float, roughness: float
    ) -> Optional[str]:
        """Suggest a realistic material type based on properties."""
        for material_type, properties in self.material_properties.items():
            if material_type == "metals" and metalness >= 0.8:
                return "metal"
            elif (
                material_type == "plastics"
                and metalness <= 0.1
                and 0.3 <= roughness <= 0.9
            ):
                return "plastic"
            elif material_type == "wood" and metalness <= 0.05 and roughness >= 0.6:
                return "wood"
            elif material_type == "glass" and metalness <= 0.1 and roughness <= 0.1:
                return "glass"
        return None

    def _validate_material_color(
        self, color: str, metalness: float, roughness: float
    ) -> List[RealismIssue]:
        """Validate color realism for specific material types."""
        issues = []

        # For metals, check against realistic metal colors
        if metalness > 0.8:
            suggested_material = self._suggest_material_type(metalness, roughness)
            if suggested_material == "metal":
                # Extract color value and check against metal colors
                metal_colors = self.material_properties["metals"]["colors"]
                # This is a simplified check - in practice, you'd convert and compare color values
                if "bright" in color.lower() or "neon" in color.lower():
                    issues.append(
                        RealismIssue(
                            type="warning",
                            category="color",
                            message="Very bright or neon colors are unrealistic for metallic materials",
                            severity=2,
                            suggestion="Use more subdued colors typical of metals (grays, browns, muted tones)",
                        )
                    )

        return issues

    def _check_component_scale(
        self,
        width: float,
        height: float,
        depth: float,
        components: List[Dict],
        issues: List[RealismIssue],
        line_num: int,
    ):
        """Check if object scale matches expected component sizes."""
        if not components:
            return

        # Look for scale references in component descriptions
        for component in components:
            component_name = component.get("component_name", "").lower()

            # Check against known scale references
            for ref_name, ref_size in self.scale_references[
                "electronic_components"
            ].items():
                if ref_name in component_name:
                    expected_size = max(
                        ref_size.get("height", 0),
                        ref_size.get("width", 0),
                        ref_size.get("length", 0),
                    )
                    actual_size = max(width, height, depth)

                    if actual_size > expected_size * 100:  # 100x larger than realistic
                        issues.append(
                            RealismIssue(
                                type="warning",
                                category="scale",
                                message=f"Component '{component_name}' appears oversized (actual: {actual_size:.3f}m, typical: {expected_size:.3f}m)",
                                line_number=line_num,
                                severity=2,
                                suggestion=f"Consider scaling down to realistic size around {expected_size:.3f}m",
                            )
                        )

    def _analyze_color_harmony(
        self, hsl_colors: List[Tuple[float, float, float]]
    ) -> List[RealismIssue]:
        """Analyze color harmony between colors."""
        issues = []

        if len(hsl_colors) < 2:
            return issues

        # Check for complementary colors (opposite on color wheel)
        for i, (h1, s1, l1) in enumerate(hsl_colors):
            for j, (h2, s2, l2) in enumerate(hsl_colors[i + 1 :], i + 1):
                hue_diff = abs(h1 - h2)
                if hue_diff > 180:
                    hue_diff = 360 - hue_diff

                # Check for harsh complementary combinations
                if (
                    160 <= hue_diff <= 200
                    and s1 > 0.8
                    and s2 > 0.8
                    and l1 > 0.5
                    and l2 > 0.5
                ):
                    issues.append(
                        RealismIssue(
                            type="info",
                            category="color",
                            message="High-saturation complementary colors detected - may be visually harsh",
                            severity=1,
                            suggestion="Consider reducing saturation or lightness for more pleasant color harmony",
                        )
                    )

        return issues

    def _analyze_color_realism(
        self, hsl_colors: List[Tuple[float, float, float]]
    ) -> List[RealismIssue]:
        """Analyze color choices for realism."""
        issues = []

        # Check for overly saturated colors
        high_saturation_count = sum(1 for h, s, l in hsl_colors if s > 0.9)
        if (
            high_saturation_count > len(hsl_colors) * 0.7
        ):  # More than 70% high saturation
            issues.append(
                RealismIssue(
                    type="warning",
                    category="color",
                    message="Many highly saturated colors detected - may appear unrealistic",
                    severity=2,
                    suggestion="Mix in some more muted colors for realistic appearance",
                )
            )

        # Check for very dark or very light colors dominating
        very_dark = sum(1 for h, s, l in hsl_colors if l < 0.1)
        very_light = sum(1 for h, s, l in hsl_colors if l > 0.9)

        if very_dark > len(hsl_colors) * 0.8:
            issues.append(
                RealismIssue(
                    type="warning",
                    category="color",
                    message="Predominantly very dark colors - may lack visual interest",
                    severity=2,
                    suggestion="Add some lighter colors for better contrast and visibility",
                )
            )

        if very_light > len(hsl_colors) * 0.8:
            issues.append(
                RealismIssue(
                    type="warning",
                    category="color",
                    message="Predominantly very light colors - may appear washed out",
                    severity=2,
                    suggestion="Add some darker colors for better contrast and depth",
                )
            )

        return issues

    def _calculate_material_score(self, material_issues: List[RealismIssue]) -> float:
        """Calculate material realism score."""
        base_score = 10.0

        for issue in material_issues:
            if issue.category == "material":
                if issue.severity >= 4:
                    base_score -= 3.0
                elif issue.severity == 3:
                    base_score -= 2.0
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_lighting_score(self, lighting_issues: List[RealismIssue]) -> float:
        """Calculate lighting realism score."""
        base_score = 10.0

        for issue in lighting_issues:
            if issue.category == "lighting":
                if issue.severity >= 4:
                    base_score -= 4.0
                elif issue.severity == 3:
                    base_score -= 2.5
                elif issue.severity == 2:
                    base_score -= 1.5
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_scale_score(self, scale_issues: List[RealismIssue]) -> float:
        """Calculate scale realism score."""
        base_score = 10.0

        for issue in scale_issues:
            if issue.category == "scale":
                if issue.severity >= 4:
                    base_score -= 3.0
                elif issue.severity == 3:
                    base_score -= 2.0
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.3

        return max(0.0, min(10.0, base_score))

    def _calculate_color_score(self, color_issues: List[RealismIssue]) -> float:
        """Calculate color harmony score."""
        base_score = 10.0

        for issue in color_issues:
            if issue.category == "color":
                if issue.severity >= 4:
                    base_score -= 2.5
                elif issue.severity == 3:
                    base_score -= 1.5
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.2

        return max(0.0, min(10.0, base_score))

    def get_realism_summary(self, result: RealismValidationResult) -> str:
        """Generate a human-readable realism summary."""
        summary_parts = []

        if result.is_realistic:
            summary_parts.append("✅ Visually realistic")
        else:
            summary_parts.append("❌ Realism issues found")

        summary_parts.append(f"Overall: {result.realism_score:.1f}/10")
        summary_parts.append(f"Materials: {result.material_realism_score:.1f}/10")
        summary_parts.append(f"Lighting: {result.lighting_realism_score:.1f}/10")
        summary_parts.append(f"Scale: {result.scale_realism_score:.1f}/10")
        summary_parts.append(f"Colors: {result.color_harmony_score:.1f}/10")

        # Issue breakdown
        error_count = sum(1 for issue in result.issues if issue.type == "error")
        warning_count = sum(1 for issue in result.issues if issue.type == "warning")

        if error_count > 0:
            summary_parts.append(f"🔴 {error_count} errors")
        if warning_count > 0:
            summary_parts.append(f"🟡 {warning_count} warnings")

        # Detected materials
        if result.detected_materials:
            summary_parts.append(
                f"Materials: {', '.join(result.detected_materials[:3])}"
            )

        return " | ".join(summary_parts)
