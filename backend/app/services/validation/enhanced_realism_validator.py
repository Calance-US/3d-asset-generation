"""
Enhanced Realism Validation Service with improved lighting detection and better error reporting.

This enhanced validator addresses issues identified in the conversation summary:
1. Better lighting detection for Three.js scenes
2. More accurate material-lighting compatibility checks
3. Improved visual quality assessment
4. Better context-aware error reporting
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EnhancedRealismIssue:
    """Enhanced representation of a realism validation issue."""

    type: str  # 'error', 'warning', 'info'
    category: str  # 'lighting', 'materials', 'visual_quality', 'scene_setup'
    message: str
    line_number: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical
    suggestion: Optional[str] = None
    realistic_context: Optional[str] = None
    lighting_context: Optional[str] = None  # New: Lighting-specific context
    confidence: float = 1.0  # Confidence in the detection (0.0-1.0)


@dataclass
class LightingAnalysis:
    """Analysis of lighting setup in the scene."""

    has_ambient_light: bool = False
    has_directional_light: bool = False
    has_point_light: bool = False
    has_spotlight: bool = False
    ambient_intensity: Optional[float] = None
    directional_intensity: Optional[float] = None
    total_lights: int = 0
    lighting_score: float = 0.0
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class MaterialAnalysis:
    """Analysis of materials and their lighting compatibility."""

    has_basic_materials: bool = False
    has_standard_materials: bool = False
    has_phong_materials: bool = False
    basic_material_count: int = 0
    standard_material_count: int = 0
    material_lighting_compatibility: float = 0.0
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class EnhancedRealismValidationResult:
    """Enhanced result of realism validation."""

    is_realistic: bool
    realism_score: float  # 0-10 scale
    lighting_score: float
    material_score: float
    visual_quality_score: float
    scene_setup_score: float
    issues: List[EnhancedRealismIssue]
    lighting_analysis: LightingAnalysis
    material_analysis: MaterialAnalysis
    recommendations: List[str]


class EnhancedRealismValidator:
    """Enhanced validator for visual realism with improved lighting detection."""

    def __init__(self):
        # Three.js lighting types and their patterns
        self.lighting_patterns = {
            "ambient": {
                "patterns": [
                    r"new\s+THREE\.AmbientLight\s*\(",
                    r"THREE\.AmbientLight\s*\(",
                    r"AmbientLight\s*\(",
                ],
                "intensity_pattern": r"(?:new\s+)?THREE\.AmbientLight\s*\(\s*[^,]+,\s*([0-9.]+)",
                "color_pattern": r"(?:new\s+)?THREE\.AmbientLight\s*\(\s*(0x[0-9a-fA-F]+|[0-9]+)",
                "default_intensity": 0.5,
            },
            "directional": {
                "patterns": [
                    r"new\s+THREE\.DirectionalLight\s*\(",
                    r"THREE\.DirectionalLight\s*\(",
                    r"DirectionalLight\s*\(",
                ],
                "intensity_pattern": r"(?:new\s+)?THREE\.DirectionalLight\s*\(\s*[^,]+,\s*([0-9.]+)",
                "position_pattern": r"(?:directionalLight|light)\.position\.set\s*\(\s*([^)]+)\)",
                "default_intensity": 1.0,
            },
            "point": {
                "patterns": [
                    r"new\s+THREE\.PointLight\s*\(",
                    r"THREE\.PointLight\s*\(",
                    r"PointLight\s*\(",
                ],
                "intensity_pattern": r"(?:new\s+)?THREE\.PointLight\s*\(\s*[^,]+,\s*([0-9.]+)",
                "distance_pattern": r"(?:new\s+)?THREE\.PointLight\s*\(\s*[^,]+,\s*[^,]+,\s*([0-9.]+)",
                "default_intensity": 1.0,
            },
            "spot": {
                "patterns": [
                    r"new\s+THREE\.SpotLight\s*\(",
                    r"THREE\.SpotLight\s*\(",
                    r"SpotLight\s*\(",
                ],
                "intensity_pattern": r"(?:new\s+)?THREE\.SpotLight\s*\(\s*[^,]+,\s*([0-9.]+)",
                "angle_pattern": r"(?:new\s+)?THREE\.SpotLight\s*\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*([0-9.]+)",
                "default_intensity": 1.0,
            },
        }

        # Material types and their lighting requirements
        self.material_lighting_requirements = {
            "MeshBasicMaterial": {
                "requires_lighting": False,
                "compatible_lights": [],
                "description": "Self-illuminated, doesn't respond to lights",
                "realistic_use_cases": [
                    "UI elements",
                    "emissive objects",
                    "simple displays",
                ],
            },
            "MeshStandardMaterial": {
                "requires_lighting": True,
                "compatible_lights": ["ambient", "directional", "point", "spot"],
                "description": "PBR material, requires lighting for proper appearance",
                "realistic_use_cases": [
                    "most 3D objects",
                    "realistic materials",
                    "educational models",
                ],
            },
            "MeshPhongMaterial": {
                "requires_lighting": True,
                "compatible_lights": ["ambient", "directional", "point", "spot"],
                "description": "Classic lighting model, requires lighting",
                "realistic_use_cases": ["shiny objects", "metals", "plastics"],
            },
            "MeshLambertMaterial": {
                "requires_lighting": True,
                "compatible_lights": ["ambient", "directional", "point"],
                "description": "Diffuse lighting model, requires lighting",
                "realistic_use_cases": ["matte objects", "non-reflective surfaces"],
            },
        }

        # Realistic color ranges and values
        self.realistic_color_ranges = {
            "common_colors": {
                0xFF0000: "red",
                0x00FF00: "green",
                0x0000FF: "blue",
                0xFFFF00: "yellow",
                0xFF00FF: "magenta",
                0x00FFFF: "cyan",
                0xFFFFFF: "white",
                0x000000: "black",
                0x808080: "gray",
            },
            "material_colors": {
                "metal": [0xC0C0C0, 0x808080, 0x404040, 0xFFD700, 0xB87333],
                "plastic": [0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0xFF00FF],
                "wood": [0x8B4513, 0xD2691E, 0xA0522D, 0xCD853F],
                "glass": [0x87CEEB, 0x87CEFA, 0xF0F8FF, 0xE6E6FA],
            },
        }

        # Realistic lighting intensity ranges
        self.realistic_lighting_ranges = {
            "ambient": {"min": 0.1, "max": 0.8, "recommended": 0.3},
            "directional": {"min": 0.5, "max": 2.0, "recommended": 1.0},
            "point": {"min": 0.1, "max": 10.0, "recommended": 1.0},
            "spot": {"min": 0.5, "max": 5.0, "recommended": 1.5},
        }

    async def validate_enhanced_realism(
        self,
        html_content: str,
        topic: str,
        subject: str,
        education_level: str = "High School",
        metadata: Optional[Dict] = None,
    ) -> EnhancedRealismValidationResult:
        """
        Perform enhanced realism validation with improved lighting detection.

        Args:
            html_content: HTML content to validate
            topic: Topic of the content
            subject: Subject area
            education_level: Target education level
            metadata: Additional metadata for validation

        Returns:
            Enhanced validation result with detailed lighting analysis
        """
        issues = []
        recommendations = []

        try:
            # Extract JavaScript content for analysis
            js_content = self._extract_javascript_content(html_content)

            # 1. Enhanced lighting analysis
            lighting_analysis = self._analyze_enhanced_lighting(js_content)
            lighting_issues, lighting_score = self._validate_lighting_setup(
                lighting_analysis, js_content, topic, subject
            )
            issues.extend(lighting_issues)

            # 2. Enhanced material analysis
            material_analysis = self._analyze_enhanced_materials(js_content)
            material_issues, material_score = self._validate_material_setup(
                material_analysis, lighting_analysis, js_content
            )
            issues.extend(material_issues)

            # 3. Material-lighting compatibility check
            compatibility_issues, compatibility_score = (
                self._validate_material_lighting_compatibility(
                    material_analysis, lighting_analysis, js_content
                )
            )
            issues.extend(compatibility_issues)

            # 4. Visual quality assessment
            visual_issues, visual_score = self._assess_visual_quality(
                html_content, js_content, topic, subject
            )
            issues.extend(visual_issues)

            # 5. Scene setup validation
            scene_issues, scene_score = self._validate_scene_setup(
                js_content, topic, subject
            )
            issues.extend(scene_issues)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                lighting_analysis, material_analysis, issues
            )

            # Calculate overall realism score
            realism_score = self._calculate_enhanced_realism_score(
                lighting_score,
                material_score,
                compatibility_score,
                visual_score,
                scene_score,
                len(issues),
            )

            # Determine if content is realistic
            is_realistic = (
                realism_score >= 6.5
                and lighting_score >= 6.0
                and len([issue for issue in issues if issue.severity >= 4]) == 0
            )

            logger.info(
                f"Enhanced realism validation completed for {subject} topic '{topic}'",
                extra={
                    "total_issues": len(issues),
                    "realism_score": realism_score,
                    "lighting_score": lighting_score,
                    "material_lights_compatibility": compatibility_score,
                    "total_lights": lighting_analysis.total_lights,
                },
            )

            return EnhancedRealismValidationResult(
                is_realistic=is_realistic,
                realism_score=realism_score,
                lighting_score=lighting_score,
                material_score=material_score,
                visual_quality_score=visual_score,
                scene_setup_score=scene_score,
                issues=issues,
                lighting_analysis=lighting_analysis,
                material_analysis=material_analysis,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Enhanced realism validation failed: {e}")
            return EnhancedRealismValidationResult(
                is_realistic=False,
                realism_score=0.0,
                lighting_score=0.0,
                material_score=0.0,
                visual_quality_score=0.0,
                scene_setup_score=0.0,
                issues=[
                    EnhancedRealismIssue(
                        type="error",
                        category="validation_error",
                        message=f"Realism validation system error: {str(e)}",
                        severity=5,
                    )
                ],
                lighting_analysis=LightingAnalysis(),
                material_analysis=MaterialAnalysis(),
                recommendations=[],
            )

    def _extract_javascript_content(self, html_content: str) -> str:
        """Extract JavaScript content from HTML."""
        js_pattern = r"<script[^>]*>(.*?)</script>"
        js_matches = re.findall(js_pattern, html_content, re.DOTALL | re.IGNORECASE)
        return "\n".join(js_matches)

    def _analyze_enhanced_lighting(self, js_content: str) -> LightingAnalysis:
        """Enhanced analysis of lighting setup in the scene."""
        analysis = LightingAnalysis()

        for light_type, config in self.lighting_patterns.items():
            # Check if this light type exists
            light_found = any(
                re.search(pattern, js_content, re.IGNORECASE)
                for pattern in config["patterns"]
            )

            if light_found:
                analysis.total_lights += 1

                # Extract intensity if available
                if "intensity_pattern" in config:
                    intensity_match = re.search(
                        config["intensity_pattern"], js_content, re.IGNORECASE
                    )
                    if intensity_match:
                        try:
                            intensity = float(intensity_match.group(1))
                        except (ValueError, IndexError):
                            intensity = config["default_intensity"]
                    else:
                        intensity = config["default_intensity"]
                else:
                    intensity = config["default_intensity"]

                # Set light type flags and intensities
                if light_type == "ambient":
                    analysis.has_ambient_light = True
                    analysis.ambient_intensity = intensity
                elif light_type == "directional":
                    analysis.has_directional_light = True
                    analysis.directional_intensity = intensity
                elif light_type == "point":
                    analysis.has_point_light = True
                elif light_type == "spot":
                    analysis.has_spotlight = True

        # Calculate lighting score based on setup
        analysis.lighting_score = self._calculate_lighting_score(analysis)

        return analysis

    def _calculate_lighting_score(self, analysis: LightingAnalysis) -> float:
        """Calculate lighting quality score based on analysis."""
        score = 0.0

        # Base score for having any lights
        if analysis.total_lights > 0:
            score += 3.0

        # Bonus for ambient light (provides base illumination)
        if analysis.has_ambient_light:
            score += 2.0
            # Check intensity range
            if analysis.ambient_intensity:
                intensity_range = self.realistic_lighting_ranges["ambient"]
                if (
                    intensity_range["min"]
                    <= analysis.ambient_intensity
                    <= intensity_range["max"]
                ):
                    score += 1.0
                else:
                    analysis.issues.append(
                        f"Ambient light intensity {analysis.ambient_intensity} outside realistic range"
                    )

        # Bonus for directional light (provides main illumination)
        if analysis.has_directional_light:
            score += 2.5
            if analysis.directional_intensity:
                intensity_range = self.realistic_lighting_ranges["directional"]
                if (
                    intensity_range["min"]
                    <= analysis.directional_intensity
                    <= intensity_range["max"]
                ):
                    score += 0.5
                else:
                    analysis.issues.append(
                        f"Directional light intensity {analysis.directional_intensity} outside realistic range"
                    )

        # Bonus for additional lights
        if analysis.has_point_light:
            score += 1.0
        if analysis.has_spotlight:
            score += 1.0

        # Ideal lighting setup bonus (ambient + directional)
        if analysis.has_ambient_light and analysis.has_directional_light:
            score += 1.0

        return min(10.0, score)

    def _analyze_enhanced_materials(self, js_content: str) -> MaterialAnalysis:
        """Enhanced analysis of materials used in the scene."""
        analysis = MaterialAnalysis()

        # Material patterns
        material_patterns = {
            "MeshBasicMaterial": r"new\s+THREE\.MeshBasicMaterial\s*\(",
            "MeshStandardMaterial": r"new\s+THREE\.MeshStandardMaterial\s*\(",
            "MeshPhongMaterial": r"new\s+THREE\.MeshPhongMaterial\s*\(",
            "MeshLambertMaterial": r"new\s+THREE\.MeshLambertMaterial\s*\(",
        }

        for material_type, pattern in material_patterns.items():
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            count = len(matches)

            if material_type == "MeshBasicMaterial":
                analysis.has_basic_materials = count > 0
                analysis.basic_material_count = count
            elif material_type == "MeshStandardMaterial":
                analysis.has_standard_materials = count > 0
                analysis.standard_material_count = count
            elif material_type == "MeshPhongMaterial":
                analysis.has_phong_materials = count > 0

        return analysis

    def _validate_lighting_setup(
        self,
        lighting_analysis: LightingAnalysis,
        js_content: str,
        topic: str,
        subject: str,
    ) -> Tuple[List[EnhancedRealismIssue], float]:
        """Validate lighting setup and generate issues."""
        issues = []

        # Check if any lights exist
        if lighting_analysis.total_lights == 0:
            issues.append(
                EnhancedRealismIssue(
                    type="error",
                    category="lighting",
                    message="No lighting detected in the scene",
                    severity=4,
                    suggestion="Add at least an AmbientLight for basic illumination",
                    lighting_context="Scene has no light sources",
                    confidence=1.0,
                )
            )

        # Check for minimal lighting setup
        if (
            not lighting_analysis.has_ambient_light
            and lighting_analysis.total_lights > 0
        ):
            issues.append(
                EnhancedRealismIssue(
                    type="warning",
                    category="lighting",
                    message="No ambient lighting detected",
                    severity=2,
                    suggestion="Add AmbientLight for base illumination to avoid completely dark areas",
                    lighting_context="Scene lacks ambient illumination",
                    confidence=0.9,
                )
            )

        # Check for proper illumination sources
        if (
            not lighting_analysis.has_directional_light
            and not lighting_analysis.has_point_light
        ):
            if lighting_analysis.has_ambient_light:
                issues.append(
                    EnhancedRealismIssue(
                        type="warning",
                        category="lighting",
                        message="Only ambient lighting detected, scene may appear flat",
                        severity=2,
                        suggestion="Add DirectionalLight or PointLight for depth and shadows",
                        lighting_context="Scene lacks directional illumination",
                        confidence=0.8,
                    )
                )

        # Validate lighting intensities
        if lighting_analysis.ambient_intensity is not None:
            intensity_range = self.realistic_lighting_ranges["ambient"]
            if lighting_analysis.ambient_intensity < intensity_range["min"]:
                issues.append(
                    EnhancedRealismIssue(
                        type="warning",
                        category="lighting",
                        message=f"Ambient light intensity too low ({lighting_analysis.ambient_intensity})",
                        severity=2,
                        suggestion=f"Increase ambient light intensity to {intensity_range['recommended']} for better visibility",
                        lighting_context=f"Ambient intensity: {lighting_analysis.ambient_intensity}",
                        confidence=0.8,
                    )
                )
            elif lighting_analysis.ambient_intensity > intensity_range["max"]:
                issues.append(
                    EnhancedRealismIssue(
                        type="warning",
                        category="lighting",
                        message=f"Ambient light intensity too high ({lighting_analysis.ambient_intensity})",
                        severity=2,
                        suggestion=f"Reduce ambient light intensity to {intensity_range['recommended']} for more realistic lighting",
                        lighting_context=f"Ambient intensity: {lighting_analysis.ambient_intensity}",
                        confidence=0.8,
                    )
                )

        return issues, lighting_analysis.lighting_score

    def _validate_material_setup(
        self,
        material_analysis: MaterialAnalysis,
        lighting_analysis: LightingAnalysis,
        js_content: str,
    ) -> Tuple[List[EnhancedRealismIssue], float]:
        """Validate material setup and generate issues."""
        issues = []
        score = 5.0  # Base score

        # Check if materials exist
        total_materials = (
            material_analysis.basic_material_count
            + material_analysis.standard_material_count
        )

        if total_materials == 0:
            issues.append(
                EnhancedRealismIssue(
                    type="error",
                    category="materials",
                    message="No Three.js materials detected in the scene",
                    severity=4,
                    suggestion="Add materials to meshes using MeshBasicMaterial or MeshStandardMaterial",
                    realistic_context="Scene objects need materials for proper rendering",
                    confidence=1.0,
                )
            )
            score = 0.0
        else:
            # Bonus for using appropriate materials
            if material_analysis.has_standard_materials:
                score += 3.0  # PBR materials are more realistic
            if material_analysis.has_basic_materials:
                score += 1.0  # Basic materials are okay for simple scenes

            # Check material properties
            self._check_material_properties(js_content, issues, material_analysis)

        return issues, min(10.0, score)

    def _check_material_properties(
        self,
        js_content: str,
        issues: List[EnhancedRealismIssue],
        material_analysis: MaterialAnalysis,
    ):
        """Check material properties for realistic values."""
        # Check for invalid MeshBasicMaterial properties
        basic_invalid_props = ["metalness", "roughness", "emissive"]
        for prop in basic_invalid_props:
            pattern = rf"MeshBasicMaterial\s*\([^)]*{prop}\s*:"
            if re.search(pattern, js_content, re.IGNORECASE):
                issues.append(
                    EnhancedRealismIssue(
                        type="error",
                        category="materials",
                        message=f"MeshBasicMaterial doesn't support '{prop}' property",
                        severity=4,
                        suggestion=f"Use MeshStandardMaterial for {prop} property, or remove it",
                        realistic_context=f"MeshBasicMaterial with invalid property: {prop}",
                        confidence=1.0,
                    )
                )

        # Check for realistic metalness/roughness values
        metalness_pattern = r"metalness\s*:\s*([0-9.]+)"
        metalness_matches = re.findall(metalness_pattern, js_content, re.IGNORECASE)
        for metalness_str in metalness_matches:
            try:
                metalness = float(metalness_str)
                if metalness < 0 or metalness > 1:
                    issues.append(
                        EnhancedRealismIssue(
                            type="warning",
                            category="materials",
                            message=f"Metalness value {metalness} outside realistic range (0-1)",
                            severity=2,
                            suggestion="Use metalness values between 0 (non-metal) and 1 (pure metal)",
                            realistic_context=f"Metalness: {metalness}",
                            confidence=0.9,
                        )
                    )
            except ValueError:
                pass

        roughness_pattern = r"roughness\s*:\s*([0-9.]+)"
        roughness_matches = re.findall(roughness_pattern, js_content, re.IGNORECASE)
        for roughness_str in roughness_matches:
            try:
                roughness = float(roughness_str)
                if roughness < 0 or roughness > 1:
                    issues.append(
                        EnhancedRealismIssue(
                            type="warning",
                            category="materials",
                            message=f"Roughness value {roughness} outside realistic range (0-1)",
                            severity=2,
                            suggestion="Use roughness values between 0 (mirror-like) and 1 (completely rough)",
                            realistic_context=f"Roughness: {roughness}",
                            confidence=0.9,
                        )
                    )
            except ValueError:
                pass

    def _validate_material_lighting_compatibility(
        self,
        material_analysis: MaterialAnalysis,
        lighting_analysis: LightingAnalysis,
        js_content: str,
    ) -> Tuple[List[EnhancedRealismIssue], float]:
        """Validate compatibility between materials and lighting."""
        issues = []
        score = 8.0  # Start with good score

        # Check if PBR materials have adequate lighting
        if (
            material_analysis.has_standard_materials
            or material_analysis.has_phong_materials
        ):
            if lighting_analysis.total_lights == 0:
                issues.append(
                    EnhancedRealismIssue(
                        type="error",
                        category="lighting",
                        message="PBR/Phong materials require lighting to be visible",
                        severity=5,
                        suggestion="Add AmbientLight and DirectionalLight for proper material appearance",
                        lighting_context="PBR materials with no lighting",
                        realistic_context="PBR materials will appear black without lights",
                        confidence=1.0,
                    )
                )
                score = 0.0
            elif not lighting_analysis.has_ambient_light:
                issues.append(
                    EnhancedRealismIssue(
                        type="warning",
                        category="lighting",
                        message="PBR materials may have harsh shadows without ambient lighting",
                        severity=3,
                        suggestion="Add AmbientLight for softer, more realistic lighting",
                        lighting_context="PBR materials without ambient light",
                        confidence=0.8,
                    )
                )
                score -= 2.0

        # Calculate compatibility score
        material_analysis.material_lighting_compatibility = max(0.0, score)
        return issues, material_analysis.material_lighting_compatibility

    def _assess_visual_quality(
        self, html_content: str, js_content: str, topic: str, subject: str
    ) -> Tuple[List[EnhancedRealismIssue], float]:
        """Assess overall visual quality of the scene."""
        issues = []
        score = 6.0  # Base score

        # Check for renderer quality settings
        if "antialias: true" in js_content:
            score += 1.0
        else:
            issues.append(
                EnhancedRealismIssue(
                    type="info",
                    category="visual_quality",
                    message="Consider enabling antialiasing for smoother edges",
                    severity=1,
                    suggestion="Add 'antialias: true' to WebGLRenderer options",
                    realistic_context="Antialiasing improves visual quality",
                    confidence=0.7,
                )
            )

        # Check for shadow settings
        if (
            "shadowMap.enabled = true" in js_content
            or "shadowMapEnabled = true" in js_content
        ):
            score += 1.5
        else:
            issues.append(
                EnhancedRealismIssue(
                    type="info",
                    category="visual_quality",
                    message="Consider enabling shadows for more realistic lighting",
                    severity=1,
                    suggestion="Enable renderer.shadowMap.enabled = true and set castShadow/receiveShadow on objects",
                    realistic_context="Shadows add depth and realism",
                    confidence=0.6,
                )
            )

        # Check for realistic colors
        color_pattern = r"0x([0-9a-fA-F]{6})"
        colors = re.findall(color_pattern, js_content)
        if colors:
            score += 0.5

        # Check for excessive bright colors that might be unrealistic
        bright_colors = [
            color
            for color in colors
            if color.upper() in ["FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF"]
        ]
        if len(bright_colors) > 3:
            issues.append(
                EnhancedRealismIssue(
                    type="info",
                    category="visual_quality",
                    message="Many pure/bright colors detected, consider more realistic color palette",
                    severity=1,
                    suggestion="Use more muted, realistic colors for educational content",
                    realistic_context=f"Bright color count: {len(bright_colors)}",
                    confidence=0.5,
                )
            )

        return issues, min(10.0, score)

    def _validate_scene_setup(
        self, js_content: str, topic: str, subject: str
    ) -> Tuple[List[EnhancedRealismIssue], float]:
        """Validate overall scene setup."""
        issues = []
        score = 7.0  # Base score

        # Check for basic scene components
        if "new THREE.Scene()" not in js_content:
            issues.append(
                EnhancedRealismIssue(
                    type="error",
                    category="scene_setup",
                    message="No Three.js Scene detected",
                    severity=5,
                    suggestion="Create a scene with 'const scene = new THREE.Scene()'",
                    confidence=1.0,
                )
            )
            score = 0.0

        if "new THREE.WebGLRenderer" not in js_content:
            issues.append(
                EnhancedRealismIssue(
                    type="error",
                    category="scene_setup",
                    message="No WebGL Renderer detected",
                    severity=5,
                    suggestion="Create a renderer with 'const renderer = new THREE.WebGLRenderer()'",
                    confidence=1.0,
                )
            )
            score = 0.0

        # Check for camera
        camera_patterns = [
            r"new THREE\.PerspectiveCamera",
            r"new THREE\.OrthographicCamera",
        ]
        if not any(
            re.search(pattern, js_content, re.IGNORECASE) for pattern in camera_patterns
        ):
            issues.append(
                EnhancedRealismIssue(
                    type="error",
                    category="scene_setup",
                    message="No camera detected in scene",
                    severity=4,
                    suggestion="Add a camera (PerspectiveCamera or OrthographicCamera)",
                    confidence=0.9,
                )
            )
            score -= 3.0

        return issues, max(0.0, score)

    def _generate_recommendations(
        self,
        lighting_analysis: LightingAnalysis,
        material_analysis: MaterialAnalysis,
        issues: List[EnhancedRealismIssue],
    ) -> List[str]:
        """Generate recommendations for improving realism."""
        recommendations = []

        # Lighting recommendations
        if not lighting_analysis.has_ambient_light:
            recommendations.append("Add AmbientLight for base scene illumination")

        if (
            not lighting_analysis.has_directional_light
            and not lighting_analysis.has_point_light
        ):
            recommendations.append(
                "Add DirectionalLight for main scene lighting and shadows"
            )

        if (
            lighting_analysis.total_lights < 2
            and material_analysis.has_standard_materials
        ):
            recommendations.append(
                "Consider adding multiple lights for better material appearance"
            )

        # Material recommendations
        if (
            material_analysis.has_basic_materials
            and not material_analysis.has_standard_materials
        ):
            recommendations.append(
                "Consider using MeshStandardMaterial for more realistic lighting"
            )

        if (
            material_analysis.has_standard_materials
            and lighting_analysis.total_lights == 0
        ):
            recommendations.append(
                "PBR materials require lighting - add at least AmbientLight"
            )

        # Visual quality recommendations
        critical_issues = [issue for issue in issues if issue.severity >= 4]
        if critical_issues:
            recommendations.append(
                "Fix critical lighting/material issues for proper rendering"
            )

        return recommendations

    def _calculate_enhanced_realism_score(
        self,
        lighting_score: float,
        material_score: float,
        compatibility_score: float,
        visual_score: float,
        scene_score: float,
        total_issues: int,
    ) -> float:
        """Calculate enhanced realism score with weighted components."""
        # Weighted average of component scores
        component_score = (
            lighting_score * 0.35
            + material_score * 0.25
            + compatibility_score * 0.20
            + visual_score * 0.10
            + scene_score * 0.10
        )

        # Apply penalty for issues
        issue_penalty = min(total_issues * 0.3, 2.5)

        # Final score
        final_score = max(0, min(10, component_score - issue_penalty))

        # Bonus for excellent lighting setup
        if lighting_score >= 8.0 and compatibility_score >= 8.0:
            final_score = min(10, final_score + 0.5)

        return final_score


# Create singleton instance
enhanced_realism_validator = EnhancedRealismValidator()
