"""
Scientific accuracy validation service for physics and chemistry concepts.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ScientificIssue:
    """Represents a scientific accuracy validation issue."""

    type: str  # 'error', 'warning', 'info'
    category: str  # 'units', 'formula', 'concept', 'realistic_values'
    message: str
    line_number: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical
    suggestion: Optional[str] = None
    scientific_context: Optional[str] = None


@dataclass
class ScientificValidationResult:
    """Result of scientific accuracy validation."""

    is_scientifically_accurate: bool
    accuracy_score: float  # 0-10 scale
    unit_compliance_score: float
    formula_accuracy_score: float
    concept_alignment_score: float
    issues: List[ScientificIssue]
    detected_concepts: List[str]
    unit_analysis: Dict[str, int]


class ScientificValidator:
    """Validator for scientific accuracy in physics and chemistry visualizations."""

    def __init__(self):
        # Physics units and their relationships
        self.physics_units = {
            # Base SI units
            "length": {
                "units": ["m", "meter", "meters", "cm", "mm", "km", "ft", "in"],
                "si_base": "m",
                "conversions": {
                    "cm": 0.01,
                    "mm": 0.001,
                    "km": 1000,
                    "ft": 0.3048,
                    "in": 0.0254,
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
                    "ton",
                ],
                "si_base": "kg",
                "conversions": {"g": 0.001, "mg": 0.000001, "ton": 1000},
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
                ],
                "si_base": "s",
                "conversions": {"min": 60, "h": 3600},
            },
            "current": {
                "units": ["A", "ampere", "amperes", "amp", "amps", "mA", "μA", "kA"],
                "si_base": "A",
                "conversions": {"mA": 0.001, "μA": 0.000001, "kA": 1000},
            },
            "voltage": {
                "units": ["V", "volt", "volts", "kV", "mV", "μV"],
                "si_base": "V",
                "conversions": {"kV": 1000, "mV": 0.001, "μV": 0.000001},
            },
            "resistance": {
                "units": ["Ω", "ohm", "ohms", "kΩ", "MΩ", "mΩ"],
                "si_base": "Ω",
                "conversions": {"kΩ": 1000, "MΩ": 1000000, "mΩ": 0.001},
            },
            "power": {
                "units": ["W", "watt", "watts", "kW", "MW", "mW", "μW"],
                "si_base": "W",
                "conversions": {"kW": 1000, "MW": 1000000, "mW": 0.001, "μW": 0.000001},
            },
            "energy": {
                "units": ["J", "joule", "joules", "kJ", "MJ", "eV", "keV", "MeV"],
                "si_base": "J",
                "conversions": {
                    "kJ": 1000,
                    "MJ": 1000000,
                    "eV": 1.602e-19,
                    "keV": 1.602e-16,
                    "MeV": 1.602e-13,
                },
            },
            "frequency": {
                "units": ["Hz", "hertz", "kHz", "MHz", "GHz", "THz"],
                "si_base": "Hz",
                "conversions": {
                    "kHz": 1000,
                    "MHz": 1000000,
                    "GHz": 1000000000,
                    "THz": 1000000000000,
                },
            },
            "force": {
                "units": ["N", "newton", "newtons", "kN", "MN", "mN"],
                "si_base": "N",
                "conversions": {"kN": 1000, "MN": 1000000, "mN": 0.001},
            },
            "pressure": {
                "units": [
                    "Pa",
                    "pascal",
                    "pascals",
                    "kPa",
                    "MPa",
                    "bar",
                    "atm",
                    "torr",
                ],
                "si_base": "Pa",
                "conversions": {
                    "kPa": 1000,
                    "MPa": 1000000,
                    "bar": 100000,
                    "atm": 101325,
                    "torr": 133.322,
                },
            },
        }

        # Chemistry units and their relationships
        self.chemistry_units = {
            "concentration": {
                "units": ["M", "molarity", "molar", "mol/L", "mM", "μM", "nM"],
                "si_base": "mol/L",
                "conversions": {"M": 1, "mM": 0.001, "μM": 0.000001, "nM": 0.000000001},
            },
            "amount": {
                "units": ["mol", "mole", "moles", "mmol", "μmol", "nmol"],
                "si_base": "mol",
                "conversions": {"mmol": 0.001, "μmol": 0.000001, "nmol": 0.000000001},
            },
            "volume": {
                "units": ["L", "liter", "liters", "mL", "μL", "nL", "dm³", "cm³"],
                "si_base": "L",
                "conversions": {
                    "mL": 0.001,
                    "μL": 0.000001,
                    "nL": 0.000000001,
                    "dm³": 1,
                    "cm³": 0.001,
                },
            },
            "temperature": {
                "units": ["K", "kelvin", "°C", "celsius", "°F", "fahrenheit"],
                "si_base": "K",
                "conversions": {
                    "°C": lambda c: c + 273.15,
                    "°F": lambda f: (f - 32) * 5 / 9 + 273.15,
                },
            },
            "ph": {"units": ["pH", "ph"], "si_base": "pH", "range": (0, 14)},
        }

        # Physics formulas and relationships
        self.physics_formulas = {
            "ohms_law": {
                "formula": "V = I × R",
                "variables": {"V": "voltage", "I": "current", "R": "resistance"},
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
            },
            "power_law": {
                "formula": "P = V × I",
                "variables": {"P": "power", "V": "voltage", "I": "current"},
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
                "relationships": [
                    ("energy", "mass", "velocity", lambda m, v: 0.5 * m * v**2)
                ],
            },
            "frequency_wavelength": {
                "formula": "c = λν",
                "variables": {
                    "c": "speed_of_light",
                    "λ": "wavelength",
                    "ν": "frequency",
                },
                "relationships": [
                    (
                        "wavelength",
                        "frequency",
                        lambda f: 299792458 / f if f != 0 else None,
                    ),
                    (
                        "frequency",
                        "wavelength",
                        lambda w: 299792458 / w if w != 0 else None,
                    ),
                ],
            },
        }

        # Chemistry formulas and relationships
        self.chemistry_formulas = {
            "concentration": {
                "formula": "C = n/V",
                "variables": {"C": "concentration", "n": "amount", "V": "volume"},
                "relationships": [
                    (
                        "concentration",
                        "amount",
                        "volume",
                        lambda n, v: n / v if v != 0 else None,
                    ),
                    ("amount", "concentration", "volume", lambda c, v: c * v),
                    (
                        "volume",
                        "amount",
                        "concentration",
                        lambda n, c: n / c if c != 0 else None,
                    ),
                ],
            },
            "ideal_gas_law": {
                "formula": "PV = nRT",
                "variables": {
                    "P": "pressure",
                    "V": "volume",
                    "n": "amount",
                    "R": "gas_constant",
                    "T": "temperature",
                },
                "gas_constant": 8.314,  # J/(mol·K)
            },
            "ph_calculation": {
                "formula": "pH = -log[H⁺]",
                "variables": {"pH": "ph", "[H⁺]": "hydrogen_concentration"},
            },
        }

        # Realistic value ranges for different quantities
        self.realistic_ranges = {
            # Physics
            "household_voltage": {
                "min": 100,
                "max": 240,
                "unit": "V",
                "typical": [110, 120, 220, 240],
            },
            "battery_voltage": {
                "min": 1.2,
                "max": 12,
                "unit": "V",
                "typical": [1.5, 3.7, 9, 12],
            },
            "household_current": {
                "min": 0.1,
                "max": 20,
                "unit": "A",
                "typical": [1, 5, 10, 15],
            },
            "led_current": {
                "min": 0.001,
                "max": 0.1,
                "unit": "A",
                "typical": [0.02, 0.03, 0.05],
            },
            "resistor_values": {
                "min": 1,
                "max": 10000000,
                "unit": "Ω",
                "typical": [100, 220, 470, 1000, 10000],
            },
            # Chemistry
            "room_temperature": {
                "min": 293,
                "max": 298,
                "unit": "K",
                "typical": [295, 298],
            },
            "body_temperature": {
                "min": 310,
                "max": 312,
                "unit": "K",
                "typical": [310.15],
            },
            "standard_pressure": {
                "min": 101000,
                "max": 102000,
                "unit": "Pa",
                "typical": [101325],
            },
            "biological_ph": {
                "min": 6.5,
                "max": 8.5,
                "unit": "pH",
                "typical": [7.0, 7.4],
            },
            "acid_ph": {"min": 0, "max": 6, "unit": "pH", "typical": [1, 2, 3, 4, 5]},
            "base_ph": {
                "min": 8,
                "max": 14,
                "unit": "pH",
                "typical": [9, 10, 11, 12, 13],
            },
        }

        # Common scientific concepts and their required elements
        self.physics_concepts = {
            "ohms_law": {
                "required_elements": ["voltage", "current", "resistance"],
                "visual_elements": ["circuit", "resistor", "battery", "wires"],
                "formulas": ["V = I × R", "I = V / R", "R = V / I"],
            },
            "kirchhoffs_laws": {
                "required_elements": ["voltage", "current", "nodes", "loops"],
                "visual_elements": ["circuit", "branches", "junctions"],
                "formulas": ["ΣI = 0", "ΣV = 0"],
            },
            "electromagnetic_induction": {
                "required_elements": ["magnetic_field", "conductor", "motion", "emf"],
                "visual_elements": ["coil", "magnet", "flux_lines"],
                "formulas": ["ε = -dΦ/dt"],
            },
        }

        self.chemistry_concepts = {
            "electrochemical_cells": {
                "required_elements": [
                    "anode",
                    "cathode",
                    "electrolyte",
                    "electrons",
                    "ions",
                ],
                "visual_elements": ["electrodes", "solution", "salt_bridge"],
                "formulas": ["E°cell = E°cathode - E°anode"],
            },
            "acid_base_reactions": {
                "required_elements": [
                    "acid",
                    "base",
                    "ph",
                    "hydrogen_ions",
                    "hydroxide_ions",
                ],
                "visual_elements": ["molecules", "ions", "ph_indicator"],
                "formulas": ["pH + pOH = 14", "Ka × Kb = Kw"],
            },
            "reaction_kinetics": {
                "required_elements": [
                    "rate",
                    "concentration",
                    "temperature",
                    "activation_energy",
                ],
                "visual_elements": ["molecules", "collision", "energy_diagram"],
                "formulas": ["rate = k[A]^m[B]^n"],
            },
        }

    async def validate_scientific_content(
        self,
        content: str,
        topic: str,
        subject: str,
        education_level: str = "High School",
    ) -> ScientificValidationResult:
        """
        Validate scientific accuracy of content.

        Args:
            content: HTML/JS content to validate
            topic: The specific topic being covered
            subject: Subject area (physics/chemistry)
            education_level: Target education level

        Returns:
            ScientificValidationResult with validation details
        """
        issues = []
        detected_concepts = []

        try:
            # 1. Unit validation
            unit_issues, unit_stats = self._validate_units(content, subject)
            issues.extend(unit_issues)

            # 2. Formula validation
            formula_issues = self._validate_formulas(content, subject, topic)
            issues.extend(formula_issues)

            # 3. Concept alignment validation
            concept_issues, concepts = self._validate_concept_alignment(
                content, topic, subject
            )
            issues.extend(concept_issues)
            detected_concepts.extend(concepts)

            # 4. Realistic value validation
            value_issues = self._validate_realistic_values(content, subject)
            issues.extend(value_issues)

            # 5. Educational level appropriateness
            level_issues = self._validate_education_level(
                content, education_level, subject
            )
            issues.extend(level_issues)

            # Calculate scores
            unit_score = self._calculate_unit_score(unit_issues)
            formula_score = self._calculate_formula_score(formula_issues)
            concept_score = self._calculate_concept_score(concept_issues)
            accuracy_score = (unit_score + formula_score + concept_score) / 3

            # Determine overall accuracy
            is_accurate = not any(issue.severity >= 4 for issue in issues)

            logger.info(
                f"Scientific validation completed for {subject} topic '{topic}'",
                extra={
                    "total_issues": len(issues),
                    "accuracy_score": accuracy_score,
                    "detected_concepts": detected_concepts,
                },
            )

            return ScientificValidationResult(
                is_scientifically_accurate=is_accurate,
                accuracy_score=accuracy_score,
                unit_compliance_score=unit_score,
                formula_accuracy_score=formula_score,
                concept_alignment_score=concept_score,
                issues=issues,
                detected_concepts=detected_concepts,
                unit_analysis=unit_stats,
            )

        except Exception as e:
            logger.error(f"Error during scientific validation: {str(e)}")
            issues.append(
                ScientificIssue(
                    type="error",
                    category="validation",
                    message=f"Scientific validation failed: {str(e)}",
                    severity=5,
                )
            )

            return ScientificValidationResult(
                is_scientifically_accurate=False,
                accuracy_score=0.0,
                unit_compliance_score=0.0,
                formula_accuracy_score=0.0,
                concept_alignment_score=0.0,
                issues=issues,
                detected_concepts=[],
                unit_analysis={},
            )

    def _validate_units(
        self, content: str, subject: str
    ) -> Tuple[List[ScientificIssue], Dict[str, int]]:
        """Validate units used in the content."""
        issues = []
        unit_stats = {}

        # Get appropriate units for the subject
        if subject.lower() == "physics":
            valid_units = self.physics_units
        elif subject.lower() == "chemistry":
            valid_units = {
                **self.chemistry_units,
                **self.physics_units,
            }  # Chemistry can use physics units too
        else:
            valid_units = {**self.physics_units, **self.chemistry_units}

        # First remove hexadecimal color codes to avoid false positives
        # Remove patterns like 0xff0000, 0x89b4e1, etc.
        hex_color_pattern = r"0x[0-9a-fA-F]+"
        content_without_hex = re.sub(hex_color_pattern, "", content)

        # Extract all numeric values with units (excluding hex colors)
        unit_pattern = r"(\d+(?:\.\d+)?)\s*([a-zA-Z°μ]+|Ω)"
        matches = re.findall(unit_pattern, content_without_hex.lower())

        for value_str, unit in matches:
            try:
                value = float(value_str)
                unit_found = False
                unit_category = None

                # Skip units that are clearly part of hex colors or CSS
                if unit in ["x", "xff", "xf", "xffffff", "ff", "f"] or len(unit) > 10:
                    continue

                # Check if unit is valid for any quantity
                for quantity, unit_info in valid_units.items():
                    if unit.lower() in [u.lower() for u in unit_info["units"]]:
                        unit_found = True
                        unit_category = quantity
                        unit_stats[unit] = unit_stats.get(unit, 0) + 1
                        break

                if not unit_found and unit not in [
                    "px",
                    "deg",
                    "rad",
                    "%",
                ]:  # Ignore display/angle units
                    issues.append(
                        ScientificIssue(
                            type="error",
                            category="units",
                            message=f"Invalid or inappropriate unit '{unit}' for {subject}",
                            severity=4,
                            suggestion=f"Use appropriate {subject} units like {self._get_common_units(subject)}",
                            scientific_context=f"Unit '{unit}' is not recognized in {subject} context",
                        )
                    )

                # Check for unit misuse (e.g., using current units for voltage)
                if unit_found and unit_category:
                    issues.extend(
                        self._check_unit_context(content, unit, unit_category, value)
                    )

            except ValueError:
                continue  # Skip non-numeric values

        return issues, unit_stats

    def _validate_formulas(
        self, content: str, subject: str, topic: str
    ) -> List[ScientificIssue]:
        """Validate formulas and mathematical relationships."""
        issues = []

        # Get relevant formulas for the subject
        if subject.lower() == "physics":
            formulas = self.physics_formulas
        elif subject.lower() == "chemistry":
            formulas = self.chemistry_formulas
        else:
            formulas = {**self.physics_formulas, **self.chemistry_formulas}

        # Check for formula presence and correctness
        topic_lower = topic.lower()

        if "ohm" in topic_lower or "circuit" in topic_lower:
            issues.extend(self._validate_ohms_law(content))

        if "electrochemical" in topic_lower or "cell" in topic_lower:
            issues.extend(self._validate_electrochemical_formulas(content))

        if "kinetic" in topic_lower or "energy" in topic_lower:
            issues.extend(self._validate_energy_formulas(content))

        # Check for common formula errors
        formula_errors = [
            (r"V\s*=\s*I\s*\+\s*R", "Ohm's law should be V = I × R, not V = I + R"),
            (r"P\s*=\s*V\s*\+\s*I", "Power law should be P = V × I, not P = V + I"),
            (
                r"pH\s*=\s*log\[H\+\]",
                "pH formula should be pH = -log[H⁺], note the negative sign",
            ),
        ]

        for pattern, message in formula_errors:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(
                    ScientificIssue(
                        type="error",
                        category="formula",
                        message=f"Incorrect formula: {message}",
                        severity=4,
                        suggestion="Use the correct mathematical relationship",
                    )
                )

        return issues

    def _validate_concept_alignment(
        self, content: str, topic: str, subject: str
    ) -> Tuple[List[ScientificIssue], List[str]]:
        """Validate alignment with scientific concepts."""
        issues = []
        detected_concepts = []

        # Get relevant concepts for the subject
        if subject.lower() == "physics":
            concepts = self.physics_concepts
        elif subject.lower() == "chemistry":
            concepts = self.chemistry_concepts
        else:
            concepts = {**self.physics_concepts, **self.chemistry_concepts}

        topic_lower = topic.lower()
        content_lower = content.lower()

        # Find relevant concepts based on topic
        relevant_concepts = []
        for concept_name, concept_info in concepts.items():
            if any(keyword in topic_lower for keyword in concept_name.split("_")):
                relevant_concepts.append((concept_name, concept_info))
                detected_concepts.append(concept_name)

        # Validate required elements are present
        for concept_name, concept_info in relevant_concepts:
            required_elements = concept_info.get("required_elements", [])
            missing_elements = []

            for element in required_elements:
                if element not in content_lower:
                    missing_elements.append(element)

            if missing_elements:
                issues.append(
                    ScientificIssue(
                        type="warning",
                        category="concept",
                        message=f"Missing key elements for {concept_name}: {', '.join(missing_elements)}",
                        severity=3,
                        suggestion=f"Include visual representation of {', '.join(missing_elements)}",
                        scientific_context=f"{concept_name} requires these elements for complete understanding",
                    )
                )

            # Check for visual elements
            visual_elements = concept_info.get("visual_elements", [])
            missing_visuals = []

            for visual in visual_elements:
                if visual not in content_lower:
                    missing_visuals.append(visual)

            if (
                len(missing_visuals) > len(visual_elements) / 2
            ):  # More than half missing
                issues.append(
                    ScientificIssue(
                        type="info",
                        category="concept",
                        message=f"Consider adding more visual elements for {concept_name}: {', '.join(missing_visuals[:3])}",
                        severity=1,
                        suggestion="Visual representations enhance understanding of scientific concepts",
                    )
                )

        return issues, detected_concepts

    def _validate_realistic_values(
        self, content: str, subject: str
    ) -> List[ScientificIssue]:
        """Validate that numerical values are realistic for the given subject."""
        issues = []

        # Extract numerical values and check against realistic ranges
        value_pattern = r"(\d+(?:\.\d+)?)\s*([a-zA-Z°μ]+|Ω)"
        matches = re.findall(value_pattern, content)

        for value_str, unit in matches:
            try:
                value = float(value_str)

                # Check against realistic ranges
                for range_name, range_info in self.realistic_ranges.items():
                    # Filter ranges by subject if applicable
                    if "subjects" in range_info and subject.lower() not in [
                        s.lower() for s in range_info["subjects"]
                    ]:
                        continue

                    if unit.lower() == range_info["unit"].lower():
                        min_val = range_info["min"]
                        max_val = range_info["max"]

                        if value < min_val or value > max_val:
                            issues.append(
                                ScientificIssue(
                                    type="warning",
                                    category="realistic_values",
                                    message=f"Value {value} {unit} may be unrealistic for typical {range_name.replace('_', ' ')} in {subject}",
                                    severity=2,
                                    suggestion=f"Consider values between {min_val} and {max_val} {unit}",
                                    scientific_context=f"Typical {range_name.replace('_', ' ')} values for {subject}: {range_info.get('typical', [])}",
                                )
                            )
                        break

            except ValueError:
                continue

        return issues

    def _validate_education_level(
        self, content: str, education_level: str, subject: str
    ) -> List[ScientificIssue]:
        """Validate appropriateness for education level."""
        issues = []

        content_lower = content.lower()

        # Define complexity indicators for different levels
        advanced_physics_concepts = [
            "quantum",
            "relativity",
            "thermodynamics",
            "maxwell",
            "electromagnetic field",
        ]
        advanced_chemistry_concepts = [
            "quantum chemistry",
            "molecular orbital",
            "advanced kinetics",
            "statistical mechanics",
        ]

        if education_level.lower() in ["high school", "secondary"]:
            # Check for overly advanced concepts
            for concept in advanced_physics_concepts + advanced_chemistry_concepts:
                if concept in content_lower:
                    issues.append(
                        ScientificIssue(
                            type="warning",
                            category="concept",
                            message=f"Concept '{concept}' may be too advanced for {education_level}",
                            severity=2,
                            suggestion=f"Consider simplifying or providing more foundational explanation for {education_level} level",
                        )
                    )

        return issues

    def _check_unit_context(
        self, content: str, unit: str, unit_category: str, value: float
    ) -> List[ScientificIssue]:
        """Check if units are used in the correct context."""
        issues = []

        # Common unit misuse patterns
        misuse_patterns = [
            # Using current units for voltage
            (
                r"voltage.*?(\d+(?:\.\d+)?)\s*[aA]",
                "Using current units (A) for voltage - should use volts (V)",
            ),
            (
                r"(\d+(?:\.\d+)?)\s*[aA].*?volt",
                "Using current units (A) for voltage - should use volts (V)",
            ),
            # Using voltage units for current
            (
                r"current.*?(\d+(?:\.\d+)?)\s*[vV]",
                "Using voltage units (V) for current - should use amperes (A)",
            ),
            (
                r"(\d+(?:\.\d+)?)\s*[vV].*?current",
                "Using voltage units (V) for current - should use amperes (A)",
            ),
            # Using resistance units for power
            (
                r"power.*?(\d+(?:\.\d+)?)\s*Ω",
                "Using resistance units (Ω) for power - should use watts (W)",
            ),
            # Temperature unit misuse
            (
                r"room.temperature.*?(\d+(?:\.\d+)?)\s*°?[cC](?!\s*\+)",
                "Room temperature in Celsius without proper notation",
            ),
        ]

        for pattern, message in misuse_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(
                    ScientificIssue(
                        type="error",
                        category="units",
                        message=message,
                        severity=4,
                        suggestion="Use the correct units for each physical quantity",
                    )
                )

        return issues

    def _validate_ohms_law(self, content: str) -> List[ScientificIssue]:
        """Validate Ohm's law implementation."""
        issues = []

        # Check for correct Ohm's law formula
        ohms_patterns = [
            r"V\s*=\s*I\s*[\*×]\s*R",  # V = I * R
            r"I\s*=\s*V\s*/\s*R",  # I = V / R
            r"R\s*=\s*V\s*/\s*I",  # R = V / I
        ]

        has_correct_formula = any(
            re.search(pattern, content, re.IGNORECASE) for pattern in ohms_patterns
        )

        if "ohm" in content.lower() and not has_correct_formula:
            issues.append(
                ScientificIssue(
                    type="error",
                    category="formula",
                    message="Ohm's law topic detected but correct formula not found",
                    severity=4,
                    suggestion="Include the correct Ohm's law formula: V = I × R",
                    scientific_context="Ohm's law is fundamental to circuit analysis",
                )
            )

        return issues

    def _validate_electrochemical_formulas(self, content: str) -> List[ScientificIssue]:
        """Validate electrochemical cell formulas."""
        issues = []

        if "electrochemical" in content.lower() or "galvanic" in content.lower():
            # Check for cell potential formula
            if not re.search(
                r"E.*?=.*?E.*?cathode.*?-.*?E.*?anode", content, re.IGNORECASE
            ):
                issues.append(
                    ScientificIssue(
                        type="warning",
                        category="formula",
                        message="Electrochemical cell topic but standard cell potential formula not clearly shown",
                        severity=2,
                        suggestion="Include E°cell = E°cathode - E°anode formula",
                        scientific_context="Cell potential calculation is fundamental to electrochemistry",
                    )
                )

        return issues

    def _validate_energy_formulas(self, content: str) -> List[ScientificIssue]:
        """Validate energy-related formulas."""
        issues = []

        if "kinetic energy" in content.lower():
            # Check for kinetic energy formula
            if not re.search(
                r"(?:KE|E_k)\s*=\s*(?:½|1/2|0\.5)\s*m\s*v²?", content, re.IGNORECASE
            ):
                issues.append(
                    ScientificIssue(
                        type="warning",
                        category="formula",
                        message="Kinetic energy topic but formula not clearly shown",
                        severity=2,
                        suggestion="Include the kinetic energy formula: KE = ½mv²",
                        scientific_context="Kinetic energy formula is fundamental to mechanics",
                    )
                )

        return issues

    def _get_common_units(self, subject: str) -> str:
        """Get common units for a subject."""
        if subject.lower() == "physics":
            return "V, A, Ω, W, Hz, m, kg, s, N, J"
        elif subject.lower() == "chemistry":
            return "M, mol/L, g, L, mL, K, °C, atm, Pa"
        else:
            return "appropriate SI units"

    def _calculate_unit_score(self, unit_issues: List[ScientificIssue]) -> float:
        """Calculate unit compliance score."""
        base_score = 10.0

        for issue in unit_issues:
            if issue.category == "units":
                if issue.severity >= 4:
                    base_score -= 3.0
                elif issue.severity == 3:
                    base_score -= 2.0
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_formula_score(self, formula_issues: List[ScientificIssue]) -> float:
        """Calculate formula accuracy score."""
        base_score = 10.0

        for issue in formula_issues:
            if issue.category == "formula":
                if issue.severity >= 4:
                    base_score -= 4.0
                elif issue.severity == 3:
                    base_score -= 2.5
                elif issue.severity == 2:
                    base_score -= 1.5
                elif issue.severity == 1:
                    base_score -= 0.5

        return max(0.0, min(10.0, base_score))

    def _calculate_concept_score(self, concept_issues: List[ScientificIssue]) -> float:
        """Calculate concept alignment score."""
        base_score = 10.0

        for issue in concept_issues:
            if issue.category == "concept":
                if issue.severity >= 4:
                    base_score -= 3.0
                elif issue.severity == 3:
                    base_score -= 2.0
                elif issue.severity == 2:
                    base_score -= 1.0
                elif issue.severity == 1:
                    base_score -= 0.3

        return max(0.0, min(10.0, base_score))

    def get_scientific_summary(self, result: ScientificValidationResult) -> str:
        """Generate a human-readable scientific validation summary."""
        summary_parts = []

        if result.is_scientifically_accurate:
            summary_parts.append("✅ Scientifically accurate")
        else:
            summary_parts.append("❌ Scientific accuracy issues found")

        summary_parts.append(f"Overall: {result.accuracy_score:.1f}/10")
        summary_parts.append(f"Units: {result.unit_compliance_score:.1f}/10")
        summary_parts.append(f"Formulas: {result.formula_accuracy_score:.1f}/10")
        summary_parts.append(f"Concepts: {result.concept_alignment_score:.1f}/10")

        # Issue breakdown
        error_count = sum(1 for issue in result.issues if issue.type == "error")
        warning_count = sum(1 for issue in result.issues if issue.type == "warning")

        if error_count > 0:
            summary_parts.append(f"🔴 {error_count} errors")
        if warning_count > 0:
            summary_parts.append(f"🟡 {warning_count} warnings")

        # Detected concepts
        if result.detected_concepts:
            summary_parts.append(f"Concepts: {', '.join(result.detected_concepts[:3])}")

        return " | ".join(summary_parts)
