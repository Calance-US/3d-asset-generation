"""
Enhanced Scientific Accuracy Validation Service with improved JavaScript keyword handling.

This enhanced validator addresses issues identified in the conversation summary:
1. Better handling of JavaScript keywords that may conflict with scientific terms
2. Improved detection of scientific accuracy issues
3. More precise error reporting and suggestions
4. Better context awareness for educational content
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class EnhancedScientificIssue:
    """Enhanced representation of a scientific accuracy validation issue."""

    type: str  # 'error', 'warning', 'info'
    category: (
        str  # 'units', 'formula', 'concept', 'realistic_values', 'javascript_conflict'
    )
    message: str
    line_number: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical
    suggestion: Optional[str] = None
    scientific_context: Optional[str] = None
    javascript_context: Optional[str] = None  # New: JavaScript-specific context
    confidence: float = 1.0  # Confidence in the detection (0.0-1.0)


@dataclass
class EnhancedScientificValidationResult:
    """Enhanced result of scientific accuracy validation."""

    is_scientifically_accurate: bool
    accuracy_score: float  # 0-10 scale
    unit_compliance_score: float
    formula_accuracy_score: float
    concept_alignment_score: float
    javascript_safety_score: float  # New: Score for JavaScript context safety
    issues: List[EnhancedScientificIssue]
    detected_concepts: List[str]
    unit_analysis: Dict[str, int]
    javascript_conflicts: List[Dict[str, str]]  # New: Track JS keyword conflicts


class EnhancedScientificValidator:
    """Enhanced validator for scientific accuracy with improved JavaScript handling."""

    def __init__(self):
        # JavaScript keywords that might conflict with scientific terms
        self.javascript_keywords = {
            "let",
            "const",
            "var",
            "function",
            "class",
            "if",
            "else",
            "for",
            "while",
            "return",
            "break",
            "continue",
            "try",
            "catch",
            "finally",
            "throw",
            "new",
            "this",
            "super",
            "extends",
            "import",
            "export",
            "default",
            "async",
            "await",
            "yield",
            "static",
            "public",
            "private",
            "protected",
        }

        # JavaScript reserved words that have scientific meanings
        self.js_scientific_conflicts = {
            "static": "physics_static_electricity",
            "class": "classification_system",
            "function": "mathematical_function",
            "return": "light_return_reflection",
            "yield": "chemical_yield",
            "import": "molecular_import",
            "export": "cellular_export",
        }

        # Enhanced physics units with better detection patterns
        self.physics_units = {
            "length": {
                "units": [
                    "m",
                    "meter",
                    "meters",
                    "cm",
                    "centimeter",
                    "centimeters",
                    "mm",
                    "millimeter",
                    "millimeters",
                    "km",
                    "kilometer",
                    "kilometers",
                    "ft",
                    "feet",
                    "foot",
                    "in",
                    "inch",
                    "inches",
                ],
                "si_base": "m",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(m|meter|meters)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(cm|centimeter|centimeters)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(mm|millimeter|millimeters)\b",
                ],
                "common_errors": {
                    "meters per second": "m/s (not meters per second)",
                    "meter squared": "m² (not meter squared)",
                },
            },
            "mass": {
                "units": [
                    "kg",
                    "kilogram",
                    "kilograms",
                    "g",
                    "gram",
                    "grams",
                    "mg",
                    "milligram",
                    "milligrams",
                    "ton",
                    "tons",
                ],
                "si_base": "kg",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(kg|kilogram|kilograms)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(g|gram|grams)\b",
                ],
                "common_errors": {"grams per liter": "g/L (not grams per liter)"},
            },
            "time": {
                "units": [
                    "s",
                    "second",
                    "seconds",
                    "min",
                    "minute",
                    "minutes",
                    "h",
                    "hour",
                    "hours",
                    "ms",
                    "millisecond",
                    "milliseconds",
                ],
                "si_base": "s",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(s|second|seconds)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(min|minute|minutes)\b",
                ],
                "common_errors": {"seconds per meter": "s/m (not seconds per meter)"},
            },
            "current": {
                "units": [
                    "A",
                    "ampere",
                    "amperes",
                    "amp",
                    "amps",
                    "mA",
                    "milliamp",
                    "milliamps",
                    "μA",
                    "microamp",
                    "microamps",
                    "kA",
                ],
                "si_base": "A",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(A|ampere|amperes|amp|amps)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(mA|milliamp|milliamps)\b",
                ],
                "common_errors": {
                    "amperes per volt": "A/V (conductance, use S for siemens)",
                    "amp-hours": "Ah (not amp-hours)",
                },
            },
            "voltage": {
                "units": [
                    "V",
                    "volt",
                    "volts",
                    "kV",
                    "kilovolt",
                    "kilovolts",
                    "mV",
                    "millivolt",
                    "millivolts",
                    "μV",
                    "microvolt",
                    "microvolts",
                ],
                "si_base": "V",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(V|volt|volts)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(kV|kilovolt|kilovolts)\b",
                ],
                "common_errors": {
                    "volts per ampere": "V/A (resistance, use Ω for ohms)",
                    "voltage amperes": "VA (apparent power, not voltage amperes)",
                },
            },
            "resistance": {
                "units": [
                    "Ω",
                    "ohm",
                    "ohms",
                    "kΩ",
                    "kiloohm",
                    "kiloohms",
                    "MΩ",
                    "megohm",
                    "megohms",
                    "mΩ",
                    "milliohm",
                    "milliohms",
                ],
                "si_base": "Ω",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(Ω|ohm|ohms)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(kΩ|kiloohm|kiloohms)\b",
                ],
                "common_errors": {
                    "ohms per volt": "Ω/V (not a standard unit)",
                    "resistance volts": "Use V = IR relationship",
                },
            },
            "power": {
                "units": [
                    "W",
                    "watt",
                    "watts",
                    "kW",
                    "kilowatt",
                    "kilowatts",
                    "mW",
                    "milliwatt",
                    "milliwatts",
                    "MW",
                    "megawatt",
                    "megawatts",
                ],
                "si_base": "W",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(W|watt|watts)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(kW|kilowatt|kilowatts)\b",
                ],
                "common_errors": {
                    "watts per hour": "Wh (watt-hours, not watts per hour)",
                    "power volts": "Use P = VI relationship",
                },
            },
        }

        # Enhanced chemistry units
        self.chemistry_units = {
            "concentration": {
                "units": [
                    "M",
                    "molar",
                    "mol/L",
                    "moles per liter",
                    "mg/L",
                    "ppm",
                    "ppb",
                ],
                "si_base": "mol/L",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(M|molar)\b",
                    r"\b(\d+(?:\.\d+)?)\s*(mol/L|moles per liter)\b",
                ],
            },
            "ph": {
                "units": ["pH"],
                "range": (0, 14),
                "patterns": [r"\bpH\s*[=:]\s*(\d+(?:\.\d+)?)\b"],
            },
            "temperature": {
                "units": ["K", "kelvin", "°C", "celsius", "°F", "fahrenheit"],
                "si_base": "K",
                "patterns": [
                    r"\b(\d+(?:\.\d+)?)\s*(K|kelvin)\b",
                    r"\b(\d+(?:\.\d+)?)\s*°C\b",
                    r"\b(\d+(?:\.\d+)?)\s*°F\b",
                ],
            },
        }

        # Enhanced physics formulas with JavaScript-safe validation
        self.physics_formulas = {
            "ohms_law": {
                "formula": "V = I × R",
                "variables": {"V": "voltage", "I": "current", "R": "resistance"},
                "javascript_safe_vars": {
                    "voltage": "V",
                    "current": "I",
                    "resistance": "R",
                },
                "relationships": [
                    ("voltage", "current", "resistance", lambda i, r: i * r),
                    (
                        "current",
                        "voltage",
                        "resistance",
                        lambda v, r: v / r if r != 0 else None,
                    ),
                    (
                        "resistance",
                        "voltage",
                        "current",
                        lambda v, i: v / i if i != 0 else None,
                    ),
                ],
                "common_js_errors": [
                    "using 'let current' as variable name (conflicts with JavaScript)",
                    "using 'const resistance' incorrectly in calculations",
                ],
            },
            "power_law": {
                "formula": "P = V × I",
                "variables": {"P": "power", "V": "voltage", "I": "current"},
                "javascript_safe_vars": {"power": "P", "voltage": "V", "current": "I"},
                "relationships": [
                    ("power", "voltage", "current", lambda v, i: v * i),
                    (
                        "voltage",
                        "power",
                        "current",
                        lambda p, i: p / i if i != 0 else None,
                    ),
                    (
                        "current",
                        "power",
                        "voltage",
                        lambda p, v: p / v if v != 0 else None,
                    ),
                ],
            },
            "kinetic_energy": {
                "formula": "KE = ½mv²",
                "variables": {"KE": "energy", "m": "mass", "v": "velocity"},
                "javascript_safe_vars": {
                    "kineticEnergy": "KE",
                    "mass": "m",
                    "velocity": "v",
                },
                "relationships": [
                    ("energy", "mass", "velocity", lambda m, v: 0.5 * m * v**2)
                ],
            },
        }

        # Realistic value ranges for validation
        self.realistic_ranges = {
            "household_voltage": {"min": 110, "max": 240, "unit": "V"},
            "household_current": {"min": 1, "max": 100, "unit": "A"},
            "room_temperature": {"min": 15, "max": 35, "unit": "°C"},
            "human_mass": {"min": 30, "max": 200, "unit": "kg"},
            "car_speed": {"min": 0, "max": 300, "unit": "km/h"},
            "ph_range": {"min": 0, "max": 14, "unit": "pH"},
        }

    async def validate_enhanced_scientific_content(
        self,
        html_content: str,
        topic: str,
        subject: str,
        education_level: str = "High School",
        metadata: Optional[Dict] = None,
    ) -> EnhancedScientificValidationResult:
        """
        Perform enhanced scientific accuracy validation with JavaScript context awareness.

        Args:
            html_content: HTML content to validate
            topic: Topic of the content
            subject: Subject area (physics, chemistry, etc.)
            education_level: Target education level
            metadata: Additional metadata for validation

        Returns:
            Enhanced validation result with JavaScript safety analysis
        """
        issues = []
        detected_concepts = []
        unit_analysis = {}
        javascript_conflicts = []

        try:
            # Extract text content from HTML, preserving JavaScript context
            text_content, js_content = self._extract_text_and_js_content(html_content)

            # 1. Enhanced unit validation with JavaScript awareness
            unit_issues, unit_score, unit_counts = self._validate_enhanced_units(
                text_content, js_content, subject
            )
            issues.extend(unit_issues)
            unit_analysis.update(unit_counts)

            # 2. JavaScript-safe formula validation
            formula_issues, formula_score = self._validate_javascript_safe_formulas(
                text_content, js_content, subject, topic
            )
            issues.extend(formula_issues)

            # 3. Enhanced concept alignment with JavaScript conflict detection
            concept_issues, concept_score, concepts = (
                self._validate_enhanced_concept_alignment(
                    text_content, js_content, topic, subject, education_level
                )
            )
            issues.extend(concept_issues)
            detected_concepts.extend(concepts)

            # 4. JavaScript keyword conflict analysis
            js_conflict_issues, js_safety_score, conflicts = (
                self._analyze_javascript_conflicts(text_content, js_content, subject)
            )
            issues.extend(js_conflict_issues)
            javascript_conflicts.extend(conflicts)

            # 5. Realistic value validation with context awareness
            realism_issues = self._validate_enhanced_realistic_values(
                text_content, js_content, subject, topic
            )
            issues.extend(realism_issues)

            # Calculate overall accuracy score with JavaScript safety factor
            accuracy_score = self._calculate_enhanced_accuracy_score(
                unit_score, formula_score, concept_score, js_safety_score, len(issues)
            )

            # Determine if content is scientifically accurate
            is_accurate = (
                accuracy_score >= 7.0
                and js_safety_score >= 8.0
                and len([issue for issue in issues if issue.severity >= 4]) == 0
            )

            logger.info(
                f"Enhanced scientific validation completed for {subject} topic '{topic}'",
                extra={
                    "total_issues": len(issues),
                    "accuracy_score": accuracy_score,
                    "js_safety_score": js_safety_score,
                    "detected_concepts": detected_concepts,
                    "js_conflicts": len(javascript_conflicts),
                },
            )

            return EnhancedScientificValidationResult(
                is_scientifically_accurate=is_accurate,
                accuracy_score=accuracy_score,
                unit_compliance_score=unit_score,
                formula_accuracy_score=formula_score,
                concept_alignment_score=concept_score,
                javascript_safety_score=js_safety_score,
                issues=issues,
                detected_concepts=detected_concepts,
                unit_analysis=unit_analysis,
                javascript_conflicts=javascript_conflicts,
            )

        except Exception as e:
            logger.error(f"Enhanced scientific validation failed: {e}")
            return EnhancedScientificValidationResult(
                is_scientifically_accurate=False,
                accuracy_score=0.0,
                unit_compliance_score=0.0,
                formula_accuracy_score=0.0,
                concept_alignment_score=0.0,
                javascript_safety_score=0.0,
                issues=[
                    EnhancedScientificIssue(
                        type="error",
                        category="validation_error",
                        message=f"Validation system error: {str(e)}",
                        severity=5,
                    )
                ],
                detected_concepts=[],
                unit_analysis={},
                javascript_conflicts=[],
            )

    def _extract_text_and_js_content(self, html_content: str) -> Tuple[str, str]:
        """Extract text content and JavaScript content separately."""
        # Extract JavaScript content
        js_pattern = r"<script[^>]*>(.*?)</script>"
        js_matches = re.findall(js_pattern, html_content, re.DOTALL | re.IGNORECASE)
        js_content = "\n".join(js_matches)

        # Extract text content (remove HTML tags but keep content)
        text_content = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text_content = re.sub(r"<[^>]+>", " ", text_content)
        text_content = re.sub(r"\s+", " ", text_content).strip()

        return text_content, js_content

    def _validate_enhanced_units(
        self, text_content: str, js_content: str, subject: str
    ) -> Tuple[List[EnhancedScientificIssue], float, Dict[str, int]]:
        """Enhanced unit validation with JavaScript context awareness."""
        issues = []
        unit_counts = {}

        # Check for incorrect unit usage in both text and JavaScript
        all_content = text_content + " " + js_content

        # Common unit errors
        unit_errors = [
            (
                r"\b(\d+(?:\.\d+)?)\s*amperes?\s+(?:for\s+)?voltage",
                "voltage should be in volts (V), not amperes (A)",
            ),
            (
                r"\b(\d+(?:\.\d+)?)\s*volts?\s+(?:for\s+)?current",
                "current should be in amperes (A), not volts (V)",
            ),
            (
                r"\b(\d+(?:\.\d+)?)\s*watts?\s+(?:for\s+)?resistance",
                "resistance should be in ohms (Ω), not watts (W)",
            ),
            (
                r"\b(\d+(?:\.\d+)?)\s*meters?\s*per\s*second\s*per\s*second",
                "use m/s² for acceleration",
            ),
            (r"\b(\d+(?:\.\d+)?)\s*degrees?\s*kelvin", "use K (not degrees Kelvin)"),
        ]

        for pattern, error_msg in unit_errors:
            matches = re.finditer(pattern, all_content, re.IGNORECASE)
            for match in matches:
                # Check if this is in JavaScript context
                in_js = match.start() > len(text_content)
                context_type = "JavaScript code" if in_js else "display text"

                issues.append(
                    EnhancedScientificIssue(
                        type="error",
                        category="units",
                        message=f"Incorrect unit usage: {error_msg}",
                        severity=4,
                        suggestion=f"Correct the unit in {context_type}",
                        scientific_context=f"Found in {context_type}: {match.group()}",
                        javascript_context=context_type if in_js else None,
                        confidence=0.9,
                    )
                )

        # Validate unit consistency between JavaScript variables and display
        js_unit_vars = re.findall(
            r"(?:let|const|var)\s+(\w*(?:voltage|current|resistance|power)\w*)",
            js_content,
            re.IGNORECASE,
        )
        for var_name in js_unit_vars:
            if "voltage" in var_name.lower():
                if not re.search(r"\b\d+(?:\.\d+)?\s*V\b", text_content):
                    issues.append(
                        EnhancedScientificIssue(
                            type="warning",
                            category="units",
                            message=f"JavaScript variable '{var_name}' suggests voltage, but no voltage units (V) found in display",
                            severity=2,
                            suggestion="Ensure voltage values are displayed with correct units (V)",
                            javascript_context=f"Variable: {var_name}",
                            confidence=0.7,
                        )
                    )

        # Calculate unit compliance score
        total_checks = len(unit_errors) + len(js_unit_vars)
        error_count = len([issue for issue in issues if issue.category == "units"])
        unit_score = max(0, 10 - (error_count * 2)) if total_checks > 0 else 8.0

        return issues, unit_score, unit_counts

    def _validate_javascript_safe_formulas(
        self, text_content: str, js_content: str, subject: str, topic: str
    ) -> Tuple[List[EnhancedScientificIssue], float]:
        """Validate formulas with JavaScript safety considerations."""
        issues = []

        if subject.lower() == "physics":
            # Check for Ohm's law implementation
            if "ohm" in topic.lower() or "resistance" in topic.lower():
                # Look for correct formula implementation
                correct_patterns = [
                    r"voltage\s*[=:]\s*current\s*\*\s*resistance",
                    r"V\s*[=:]\s*I\s*\*\s*R",
                    r"current\s*[=:]\s*voltage\s*\/\s*resistance",
                    r"I\s*[=:]\s*V\s*\/\s*R",
                ]

                formula_found = any(
                    re.search(pattern, js_content, re.IGNORECASE)
                    for pattern in correct_patterns
                )

                if not formula_found:
                    issues.append(
                        EnhancedScientificIssue(
                            type="error",
                            category="formula",
                            message="Ohm's law formula not correctly implemented in JavaScript",
                            severity=4,
                            suggestion="Implement V = I * R or equivalent relationship in code",
                            scientific_context="Ohm's law: V = I × R",
                            javascript_context="Missing proper formula implementation",
                            confidence=0.8,
                        )
                    )

                # Check for JavaScript keyword conflicts in variable names
                problematic_vars = re.findall(
                    r"(?:let|const|var)\s+(class|function|return|static)\s*[=:]",
                    js_content,
                )
                for var_name in problematic_vars:
                    issues.append(
                        EnhancedScientificIssue(
                            type="error",
                            category="javascript_conflict",
                            message=f"Variable name '{var_name}' conflicts with JavaScript keyword",
                            severity=5,
                            suggestion=f"Use a different variable name like '{var_name}Value' or '{var_name}Param'",
                            javascript_context=f"JavaScript keyword conflict: {var_name}",
                            confidence=1.0,
                        )
                    )

        # Calculate formula accuracy score
        formula_error_count = len(
            [issue for issue in issues if issue.category == "formula"]
        )
        js_conflict_count = len(
            [issue for issue in issues if issue.category == "javascript_conflict"]
        )
        formula_score = max(0, 10 - (formula_error_count * 3) - (js_conflict_count * 2))

        return issues, formula_score

    def _validate_enhanced_concept_alignment(
        self,
        text_content: str,
        js_content: str,
        topic: str,
        subject: str,
        education_level: str,
    ) -> Tuple[List[EnhancedScientificIssue], float, List[str]]:
        """Enhanced concept alignment validation with JavaScript awareness."""
        issues = []
        detected_concepts = []

        topic_lower = topic.lower()
        all_content = text_content + " " + js_content

        # Physics concepts with JavaScript considerations
        if subject.lower() == "physics":
            physics_concepts = {
                "ohms_law": {
                    "keywords": ["ohm", "resistance", "voltage", "current"],
                    "required_elements": [
                        "voltage",
                        "current",
                        "resistance",
                        "circuit",
                    ],
                    "js_elements": ["calculation", "formula", "interaction"],
                    "educational_level": ["high school", "university"],
                },
                "power": {
                    "keywords": ["power", "watt", "energy"],
                    "required_elements": ["power", "voltage", "current"],
                    "js_elements": ["power calculation", "energy display"],
                    "educational_level": ["high school", "university"],
                },
            }

            for concept_name, concept_info in physics_concepts.items():
                if any(keyword in topic_lower for keyword in concept_info["keywords"]):
                    detected_concepts.append(concept_name)

                    # Check for required elements in content
                    missing_elements = []
                    for element in concept_info["required_elements"]:
                        if element not in all_content.lower():
                            missing_elements.append(element)

                    if missing_elements:
                        issues.append(
                            EnhancedScientificIssue(
                                type="warning",
                                category="concept",
                                message=f"Missing key elements for {concept_name}: {', '.join(missing_elements)}",
                                severity=2,
                                suggestion=f"Include visual representation or discussion of {', '.join(missing_elements)}",
                                scientific_context=f"{concept_name} requires these elements for complete understanding",
                                confidence=0.8,
                            )
                        )

                    # Check for JavaScript implementation elements
                    missing_js_elements = []
                    for js_element in concept_info["js_elements"]:
                        if js_element.replace(
                            " ", ""
                        ) not in js_content.lower().replace(" ", ""):
                            missing_js_elements.append(js_element)

                    if missing_js_elements and js_content.strip():
                        issues.append(
                            EnhancedScientificIssue(
                                type="info",
                                category="concept",
                                message=f"Could enhance {concept_name} with interactive {', '.join(missing_js_elements)}",
                                severity=1,
                                suggestion=f"Consider adding interactive {', '.join(missing_js_elements)} to improve learning",
                                javascript_context="Missing interactive elements",
                                confidence=0.6,
                            )
                        )

        concept_score = max(0, 10 - len(issues))
        return issues, concept_score, detected_concepts

    def _analyze_javascript_conflicts(
        self, text_content: str, js_content: str, subject: str
    ) -> Tuple[List[EnhancedScientificIssue], float, List[Dict[str, str]]]:
        """Analyze potential conflicts between JavaScript keywords and scientific terms."""
        issues = []
        conflicts = []

        # Find JavaScript variable declarations that might conflict
        var_declarations = re.findall(
            r"(?:let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)", js_content
        )

        for var_name in var_declarations:
            if var_name.lower() in self.javascript_keywords:
                conflict = {
                    "variable": var_name,
                    "keyword": var_name.lower(),
                    "context": "JavaScript keyword conflict",
                }
                conflicts.append(conflict)

                issues.append(
                    EnhancedScientificIssue(
                        type="error",
                        category="javascript_conflict",
                        message=f"Variable '{var_name}' conflicts with JavaScript reserved word",
                        severity=5,
                        suggestion=f"Rename variable to '{var_name}Value' or similar non-conflicting name",
                        javascript_context=f"Conflicts with JavaScript keyword: {var_name}",
                        confidence=1.0,
                    )
                )

            # Check for scientific terms that might be confusing in JS context
            if var_name.lower() in self.js_scientific_conflicts:
                scientific_meaning = self.js_scientific_conflicts[var_name.lower()]
                conflict = {
                    "variable": var_name,
                    "scientific_meaning": scientific_meaning,
                    "context": "Scientific term in JavaScript context",
                }
                conflicts.append(conflict)

                issues.append(
                    EnhancedScientificIssue(
                        type="warning",
                        category="javascript_conflict",
                        message=f"Variable '{var_name}' has scientific meaning that might be confusing in JavaScript context",
                        severity=2,
                        suggestion=f"Consider using more specific variable name related to {scientific_meaning}",
                        scientific_context=f"Scientific meaning: {scientific_meaning}",
                        javascript_context=f"Used as JavaScript variable: {var_name}",
                        confidence=0.7,
                    )
                )

        # Calculate JavaScript safety score
        conflict_count = len(
            [issue for issue in issues if issue.category == "javascript_conflict"]
        )
        js_safety_score = max(0, 10 - (conflict_count * 1.5))

        return issues, js_safety_score, conflicts

    def _validate_enhanced_realistic_values(
        self, text_content: str, js_content: str, subject: str, topic: str
    ) -> List[EnhancedScientificIssue]:
        """Enhanced realistic value validation with context awareness."""
        issues = []
        all_content = text_content + " " + js_content

        # Check for unrealistic values in both display and code
        value_patterns = [
            (r"(\d+(?:\.\d+)?)\s*V\b", "voltage", "household_voltage"),
            (r"(\d+(?:\.\d+)?)\s*A\b", "current", "household_current"),
            (r"(\d+(?:\.\d+)?)\s*°C\b", "temperature", "room_temperature"),
            (r"pH\s*[=:]\s*(\d+(?:\.\d+)?)", "ph", "ph_range"),
        ]

        for pattern, unit_type, range_key in value_patterns:
            matches = re.finditer(pattern, all_content, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                range_info = self.realistic_ranges.get(range_key, {})

                if range_info and ("min" in range_info and "max" in range_info):
                    if value < range_info["min"] or value > range_info["max"]:
                        # Determine if this is in JavaScript or display text
                        in_js = match.start() > len(text_content)
                        context = "JavaScript code" if in_js else "display text"

                        issues.append(
                            EnhancedScientificIssue(
                                type="warning",
                                category="realistic_values",
                                message=f"Unrealistic {unit_type} value: {value} {range_info['unit']} (typical range: {range_info['min']}-{range_info['max']} {range_info['unit']})",
                                severity=2,
                                suggestion=f"Use more realistic {unit_type} values for educational purposes",
                                scientific_context=f"Found in {context}",
                                javascript_context=context if in_js else None,
                                confidence=0.8,
                            )
                        )

        return issues

    def _calculate_enhanced_accuracy_score(
        self,
        unit_score: float,
        formula_score: float,
        concept_score: float,
        js_safety_score: float,
        total_issues: int,
    ) -> float:
        """Calculate enhanced accuracy score with JavaScript safety factor."""
        # Base score from individual components
        base_score = (
            unit_score * 0.3
            + formula_score * 0.25
            + concept_score * 0.25
            + js_safety_score * 0.2
        )

        # Apply penalty for total number of issues
        issue_penalty = min(total_issues * 0.5, 3.0)

        # Final score with JavaScript safety boost for clean code
        final_score = max(0, min(10, base_score - issue_penalty))

        # Bonus for JavaScript safety (clean, conflict-free code)
        if js_safety_score >= 9.0:
            final_score = min(10, final_score + 0.5)

        return final_score


# Create singleton instance
enhanced_scientific_validator = EnhancedScientificValidator()
