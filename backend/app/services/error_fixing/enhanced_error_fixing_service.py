"""
Enhanced Error Fixing Service with improved quality score tracking and better error resolution.

This service addresses the key issues identified in the validation and error fixing system:
1. Static quality scores that don't improve between attempts
2. Poor error reduction effectiveness
3. Need for more targeted fixing strategies
4. Better tracking of improvement metrics
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for targeted fixing strategies."""

    SYNTAX = "syntax"
    THREEJS_API = "threejs_api"
    SCIENTIFIC_ACCURACY = "scientific_accuracy"
    VARIABLE_DECLARATION = "variable_declaration"
    LIGHTING_REALISM = "lighting_realism"
    PERFORMANCE = "performance"
    EDUCATIONAL_CONTENT = "educational_content"


@dataclass
class ErrorFixingStrategy:
    """Strategy for fixing specific types of errors."""

    category: ErrorCategory
    temperature: float
    focus_instructions: str
    examples: List[str]
    success_indicators: List[str]


@dataclass
class QualityImprovementTracker:
    """Tracks quality improvements across fixing attempts."""

    initial_score: float
    current_score: float
    target_score: float
    error_reduction_rate: float
    critical_errors_fixed: int
    total_errors_fixed: int
    improvement_trend: List[float]
    stagnation_counter: int = 0

    def calculate_improvement_rate(self) -> float:
        """Calculate the rate of improvement between attempts."""
        if len(self.improvement_trend) < 2:
            return 0.0
        return self.improvement_trend[-1] - self.improvement_trend[-2]

    def is_improving(self) -> bool:
        """Check if quality is improving."""
        return self.calculate_improvement_rate() > 0.1

    def is_stagnating(self) -> bool:
        """Check if quality improvements have stagnated."""
        return self.stagnation_counter >= 2 and self.calculate_improvement_rate() < 0.05


class EnhancedErrorFixingService:
    """Enhanced service for generating error-fixing prompts with better quality tracking."""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent / "prompts"
        self.template_path = self.base_path / settings.ERROR_FIXING_TEMPLATE_PATH
        self.env = Environment(loader=FileSystemLoader(str(self.base_path)))

        # Error fixing strategies for different categories
        self.fixing_strategies = self._initialize_fixing_strategies()

        # Track quality improvements across sessions
        self.quality_trackers: Dict[str, QualityImprovementTracker] = {}

    def _initialize_fixing_strategies(self) -> Dict[ErrorCategory, ErrorFixingStrategy]:
        """Initialize error fixing strategies for different error categories."""
        return {
            ErrorCategory.VARIABLE_DECLARATION: ErrorFixingStrategy(
                category=ErrorCategory.VARIABLE_DECLARATION,
                temperature=0.2,  # Very conservative for syntax fixes
                focus_instructions="""
Focus ONLY on variable declaration issues:
1. Find all variable redeclarations (let, const, var with same name)
2. Rename duplicate variables with descriptive, unique names
3. Ensure each variable has a single, clear declaration
4. Maintain original functionality and scope
""",
                examples=[
                    "// ❌ Wrong: let material = ...; let material = ...;",
                    "// ✅ Fixed: let standardMaterial = ...; let basicMaterial = ...;",
                ],
                success_indicators=[
                    "no duplicate variable names",
                    "unique identifiers",
                    "clear naming",
                ],
            ),
            ErrorCategory.THREEJS_API: ErrorFixingStrategy(
                category=ErrorCategory.THREEJS_API,
                temperature=0.3,
                focus_instructions="""
Focus on Three.js API compliance:
1. Ensure material properties match material type (MeshBasicMaterial vs MeshStandardMaterial)
2. Fix geometry creation and mesh instantiation patterns
3. Correct scene.add() and object hierarchy calls
4. Validate lighting setup for material types
""",
                examples=[
                    "// ❌ Wrong: MeshBasicMaterial with metalness/roughness",
                    "// ✅ Fixed: Use MeshStandardMaterial or remove PBR properties",
                ],
                success_indicators=[
                    "valid material properties",
                    "proper API usage",
                    "correct object hierarchy",
                ],
            ),
            ErrorCategory.SCIENTIFIC_ACCURACY: ErrorFixingStrategy(
                category=ErrorCategory.SCIENTIFIC_ACCURACY,
                temperature=0.4,
                focus_instructions="""
Focus on scientific accuracy improvements:
1. Correct units and measurements (V for volts, A for amperes, Ω for ohms)
2. Fix physical formulas and relationships
3. Ensure realistic scale and proportions
4. Validate educational content accuracy
""",
                examples=[
                    "// ❌ Wrong: '5 amperes' for voltage",
                    "// ✅ Fixed: '5 V' for voltage, '2 A' for current",
                ],
                success_indicators=[
                    "correct units",
                    "accurate formulas",
                    "realistic values",
                ],
            ),
            ErrorCategory.LIGHTING_REALISM: ErrorFixingStrategy(
                category=ErrorCategory.LIGHTING_REALISM,
                temperature=0.5,
                focus_instructions="""
Focus on lighting and visual realism:
1. Add appropriate lighting for PBR materials
2. Ensure ambient and directional lights are present
3. Fix shadow casting and receiving
4. Improve material appearance and realism
""",
                examples=[
                    "// ❌ Wrong: MeshStandardMaterial with no lights",
                    "// ✅ Fixed: Add AmbientLight and DirectionalLight",
                ],
                success_indicators=[
                    "proper lighting setup",
                    "realistic materials",
                    "good visual quality",
                ],
            ),
            ErrorCategory.SYNTAX: ErrorFixingStrategy(
                category=ErrorCategory.SYNTAX,
                temperature=0.1,  # Most conservative
                focus_instructions="""
Focus ONLY on JavaScript syntax errors:
1. Fix bracket/brace mismatches
2. Add missing semicolons
3. Correct function call syntax
4. Fix string/number literal formatting
""",
                examples=[
                    "// ❌ Wrong: function() { missing closing brace",
                    "// ✅ Fixed: function() { /* code */ }",
                ],
                success_indicators=[
                    "valid JavaScript syntax",
                    "balanced brackets",
                    "proper statements",
                ],
            ),
        }

    def create_enhanced_error_fixing_prompt(
        self,
        original_html: str,
        errors: List[Dict[str, Any]],
        attempt_number: int = 1,
        previous_quality_score: Optional[float] = None,
        target_quality_improvement: float = 1.0,
    ) -> str:
        """
        Create an enhanced error-fixing prompt with targeted strategies and quality tracking.

        Args:
            original_html: The original HTML content with errors
            errors: List of validation errors with details
            attempt_number: Current attempt number (1-based)
            previous_quality_score: Quality score from previous attempt
            target_quality_improvement: Target improvement in quality score

        Returns:
            Enhanced error-fixing prompt with targeted strategies
        """
        try:
            # Analyze error patterns and determine primary strategy
            error_analysis = self._analyze_error_patterns(errors)
            primary_strategy = self._select_primary_strategy(
                error_analysis, attempt_number
            )

            # Generate quality improvement guidance
            quality_guidance = self._generate_quality_improvement_guidance(
                previous_quality_score, target_quality_improvement, attempt_number
            )

            # Load and customize template
            template_content = self._load_template()

            # Format errors with enhanced details
            formatted_errors = self._format_errors_with_strategies(
                errors, error_analysis
            )

            # Create targeted fixing instructions
            targeted_instructions = self._create_targeted_instructions(
                primary_strategy, error_analysis, attempt_number
            )

            # Assemble the enhanced prompt
            enhanced_prompt = self._assemble_enhanced_prompt(
                template_content,
                original_html,
                formatted_errors,
                targeted_instructions,
                quality_guidance,
                attempt_number,
            )

            logger.info(
                f"Generated enhanced error-fixing prompt for attempt {attempt_number} "
                f"(strategy: {primary_strategy.category.value}, {len(enhanced_prompt)} chars)"
            )

            return enhanced_prompt

        except Exception as e:
            logger.error(f"Failed to generate enhanced error-fixing prompt: {e}")
            # Fallback to basic prompt
            return self._create_fallback_prompt(original_html, errors)

    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns to determine the best fixing strategy."""
        error_counts = {category: 0 for category in ErrorCategory}
        critical_errors = []
        error_details = {
            "variable_redeclarations": 0,
            "api_errors": 0,
            "syntax_errors": 0,
            "scientific_errors": 0,
            "lighting_errors": 0,
            "total_critical": 0,
            "total_warnings": 0,
        }

        for error in errors:
            severity = error.get("severity", "warning")
            error_type = error.get("error_type", "unknown")
            message = error.get("message", "").lower()

            # Count severity levels
            if severity == "critical":
                error_details["total_critical"] += 1
                critical_errors.append(error)
            else:
                error_details["total_warnings"] += 1

            # Categorize errors
            if "redeclaration" in error_type or "redeclared" in message:
                error_counts[ErrorCategory.VARIABLE_DECLARATION] += 1
                error_details["variable_redeclarations"] += 1
            elif "material" in message or "api" in error_type:
                error_counts[ErrorCategory.THREEJS_API] += 1
                error_details["api_errors"] += 1
            elif "syntax" in error_type or "bracket" in message:
                error_counts[ErrorCategory.SYNTAX] += 1
                error_details["syntax_errors"] += 1
            elif "unit" in message or "scientific" in error.get("phase", ""):
                error_counts[ErrorCategory.SCIENTIFIC_ACCURACY] += 1
                error_details["scientific_errors"] += 1
            elif "light" in message or "realism" in error.get("phase", ""):
                error_counts[ErrorCategory.LIGHTING_REALISM] += 1
                error_details["lighting_errors"] += 1

        return {
            "error_counts": error_counts,
            "error_details": error_details,
            "critical_errors": critical_errors,
            "dominant_category": max(error_counts, key=lambda k: error_counts.get(k, 0))
            if error_counts
            else None,
            "total_errors": len(errors),
        }

    def _select_primary_strategy(
        self, error_analysis: Dict[str, Any], attempt_number: int
    ) -> ErrorFixingStrategy:
        """Select the primary fixing strategy based on error analysis and attempt number."""
        error_counts = error_analysis["error_counts"]

        # On first attempt, prioritize critical syntax/variable errors
        if attempt_number == 1:
            if error_counts[ErrorCategory.VARIABLE_DECLARATION] > 0:
                return self.fixing_strategies[ErrorCategory.VARIABLE_DECLARATION]
            elif error_counts[ErrorCategory.SYNTAX] > 0:
                return self.fixing_strategies[ErrorCategory.SYNTAX]

        # On subsequent attempts, focus on the dominant error category
        dominant_category = error_analysis["dominant_category"]
        return self.fixing_strategies[dominant_category]

    def _generate_quality_improvement_guidance(
        self,
        previous_quality_score: Optional[float],
        target_improvement: float,
        attempt_number: int,
    ) -> str:
        """Generate guidance for quality score improvement."""
        if previous_quality_score is None:
            return """
## 🎯 QUALITY TARGET
Target: Achieve quality score > 6.0 (Good) or higher
Focus: Fix all critical errors to improve overall quality
"""

        current_target = min(10.0, previous_quality_score + target_improvement)
        improvement_percentage = (target_improvement / previous_quality_score) * 100

        return f"""
## 🎯 QUALITY IMPROVEMENT TARGET
Previous Score: {previous_quality_score:.1f}
Target Score: {current_target:.1f} (improvement: +{target_improvement:.1f}, {improvement_percentage:.1f}%)
Attempt: {attempt_number}

CRITICAL: The quality score MUST improve this attempt. Focus on:
1. Reducing the number of critical errors (highest impact)
2. Fixing the most severe issues first
3. Ensuring all fixes actually resolve the underlying problems
4. Not introducing new errors while fixing existing ones

If quality doesn't improve after this attempt, the fixing strategy will be changed.
"""

    def _create_targeted_instructions(
        self,
        strategy: ErrorFixingStrategy,
        error_analysis: Dict[str, Any],
        attempt_number: int,
    ) -> str:
        """Create targeted fixing instructions based on the selected strategy."""
        instructions = f"""
## 🔧 TARGETED FIXING STRATEGY (Attempt {attempt_number})

### Primary Focus: {strategy.category.value.replace("_", " ").title()}
Temperature: {strategy.temperature} ({"Conservative" if strategy.temperature < 0.3 else "Moderate" if strategy.temperature < 0.5 else "Creative"})

{strategy.focus_instructions}

### Error Pattern Analysis:
- Total Errors: {error_analysis["total_errors"]}
- Critical Errors: {error_analysis["error_details"]["total_critical"]}
- Variable Redeclarations: {error_analysis["error_details"]["variable_redeclarations"]}
- API Errors: {error_analysis["error_details"]["api_errors"]}
- Scientific Errors: {error_analysis["error_details"]["scientific_errors"]}

### Success Criteria:
"""

        for indicator in strategy.success_indicators:
            instructions += f"- {indicator}\n"

        if attempt_number > 1:
            instructions += f"""
### IMPORTANT: This is attempt {attempt_number}
The previous attempt(s) did not sufficiently improve quality. You MUST:
1. Use a different approach than previous attempts
2. Be more thorough in addressing root causes
3. Ensure your fixes actually resolve the validation errors
4. Double-check that you're not introducing new errors
"""

        return instructions

    def _format_errors_with_strategies(
        self, errors: List[Dict[str, Any]], error_analysis: Dict[str, Any]
    ) -> str:
        """Format errors with specific fixing strategies."""
        formatted_errors = ""

        # Group errors by category for better organization
        categorized_errors = {}
        for error in errors:
            phase = error.get("phase", "unknown")
            if phase not in categorized_errors:
                categorized_errors[phase] = []
            categorized_errors[phase].append(error)

        # Format errors by phase with priority indicators
        priority_phases = ["html_js", "scientific", "realism", "runtime"]

        for phase in priority_phases + list(
            set(categorized_errors.keys()) - set(priority_phases)
        ):
            if phase not in categorized_errors:
                continue

            phase_errors = categorized_errors[phase]
            formatted_errors += (
                f"\n### 🚨 {phase.upper()} PHASE ERRORS ({len(phase_errors)} errors)\n"
            )

            for i, error in enumerate(phase_errors, 1):
                severity = error.get("severity", "unknown")
                error_type = error.get("error_type", "unknown")
                message = error.get("message", "")
                location = error.get("location")
                suggestion = error.get("suggestion")
                context = error.get("context")

                # Add priority indicator
                priority = "🔴 CRITICAL" if severity == "critical" else "🟡 WARNING"

                formatted_errors += f"""
**Error {i}: {priority}**
- **Type:** {error_type}
- **Message:** {message}
"""

                if location:
                    formatted_errors += f"- **Location:** {location}\n"
                if suggestion:
                    formatted_errors += f"- **Suggested Fix:** {suggestion}\n"
                if context:
                    formatted_errors += f"- **Context:** {context}\n"

                # Add specific fixing guidance based on error type
                if "redeclaration" in error_type:
                    formatted_errors += "- **Fix Strategy:** Rename variables with unique, descriptive names\n"
                elif "material" in message.lower():
                    formatted_errors += "- **Fix Strategy:** Check material type compatibility with properties\n"
                elif "unit" in message.lower():
                    formatted_errors += "- **Fix Strategy:** Use correct scientific units (V, A, Ω, etc.)\n"

                formatted_errors += "\n"

        return formatted_errors

    def _assemble_enhanced_prompt(
        self,
        template_content: str,
        original_html: str,
        formatted_errors: str,
        targeted_instructions: str,
        quality_guidance: str,
        attempt_number: int,
    ) -> str:
        """Assemble the complete enhanced error fixing prompt."""

        # Replace template variables
        enhanced_prompt = template_content.replace("{{ original_html }}", original_html)

        # Insert quality improvement guidance at the top
        enhanced_prompt = quality_guidance + "\n\n" + enhanced_prompt

        # Insert targeted instructions
        enhanced_prompt = enhanced_prompt.replace(
            "## 🎯 FIXING REQUIREMENTS",
            targeted_instructions + "\n\n## 🎯 FIXING REQUIREMENTS",
        )

        # Replace the error section with enhanced formatting
        if "**Validation Errors Detected:**" in enhanced_prompt:
            enhanced_prompt = enhanced_prompt.replace(
                "**Validation Errors Detected:**\n{% for error in validation_errors %}",
                f"**Validation Errors Detected:**\n{formatted_errors}",
            )
            # Clean up template artifacts
            enhanced_prompt = re.sub(
                r"\{\%.*?\%\}", "", enhanced_prompt, flags=re.DOTALL
            )
        else:
            # Fallback insertion
            enhanced_prompt = enhanced_prompt.replace(
                "{{ original_html }}",
                f"{original_html}\n\n**Validation Errors Detected:**\n{formatted_errors}",
            )

        # Add attempt-specific guidance
        if attempt_number > 1:
            enhanced_prompt += f"""

## ⚠️ RETRY ATTEMPT {attempt_number} - SPECIAL INSTRUCTIONS

This is retry attempt {attempt_number}. The previous attempt(s) failed to adequately improve the code quality.

### MANDATORY REQUIREMENTS FOR THIS ATTEMPT:
1. **DIFFERENT APPROACH**: Do not repeat the same fixes from previous attempts
2. **ROOT CAUSE FOCUS**: Address the underlying causes, not just symptoms
3. **VERIFICATION**: After each fix, mentally verify it solves the specific error
4. **QUALITY FIRST**: Prioritize fixes that will have the biggest impact on quality score
5. **NO NEW ERRORS**: Be extra careful not to introduce new problems

### QUALITY IMPROVEMENT IS MANDATORY
Your fixes MUST result in a measurably better quality score. Focus on:
- Eliminating ALL critical errors (severity = critical)
- Fixing as many errors as possible in a single pass
- Ensuring the code actually runs without errors
- Maintaining educational value and interactivity

If you cannot achieve significant quality improvement, indicate the specific technical limitations preventing improvement.
"""

        return enhanced_prompt

    def _load_template(self) -> str:
        """Load the error fixing template."""
        try:
            template_file = self.base_path / settings.ERROR_FIXING_TEMPLATE_PATH
            if template_file.exists():
                with open(template_file, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.error(f"Template file not found: {template_file}")
                return self._get_fallback_template()
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            return self._get_fallback_template()

    def _get_fallback_template(self) -> str:
        """Get a fallback template if the main template can't be loaded."""
        return """
You are a 3D visualization debugging assistant. Fix the HTML code to address all validation errors.

ORIGINAL HTML:
{{ original_html }}

Return ONLY the corrected HTML code that addresses all the errors.
Ensure the code maintains all educational content and interactive features.
"""

    def _create_fallback_prompt(
        self, original_html: str, errors: List[Dict[str, Any]]
    ) -> str:
        """Fallback prompt generation if enhanced processing fails."""
        errors_text = "\n".join(
            [
                f"- {error.get('phase', 'unknown')}: {error.get('message', '')}"
                for error in errors
            ]
        )

        return f"""Fix the following HTML code by addressing these validation errors:

ERRORS TO FIX:
{errors_text}

ORIGINAL HTML:
{original_html}

Return ONLY the corrected HTML code that addresses all the errors above.
Ensure the code maintains all educational content and interactive features.
"""

    def track_quality_improvement(
        self,
        session_id: str,
        attempt_number: int,
        quality_score: float,
        errors_fixed: int,
        critical_errors_fixed: int,
    ) -> QualityImprovementTracker:
        """Track quality improvements across attempts for a session."""
        if session_id not in self.quality_trackers:
            self.quality_trackers[session_id] = QualityImprovementTracker(
                initial_score=quality_score,
                current_score=quality_score,
                target_score=min(10.0, quality_score + 2.0),
                error_reduction_rate=0.0,
                critical_errors_fixed=0,
                total_errors_fixed=0,
                improvement_trend=[quality_score],
            )

        tracker = self.quality_trackers[session_id]
        tracker.current_score = quality_score
        tracker.improvement_trend.append(quality_score)
        tracker.total_errors_fixed += errors_fixed
        tracker.critical_errors_fixed += critical_errors_fixed

        # Check for stagnation
        if not tracker.is_improving():
            tracker.stagnation_counter += 1
        else:
            tracker.stagnation_counter = 0

        return tracker

    def should_change_strategy(self, session_id: str, attempt_number: int) -> bool:
        """Determine if the fixing strategy should be changed."""
        if session_id not in self.quality_trackers:
            return False

        tracker = self.quality_trackers[session_id]

        # Change strategy if stagnating or after 2 attempts with same approach
        return tracker.is_stagnating() or attempt_number >= 3

    def get_adaptive_strategy(
        self, session_id: str, errors: List[Dict[str, Any]], attempt_number: int
    ) -> ErrorFixingStrategy:
        """Get an adaptive strategy based on previous attempt results."""
        if not self.should_change_strategy(session_id, attempt_number):
            error_analysis = self._analyze_error_patterns(errors)
            return self._select_primary_strategy(error_analysis, attempt_number)

        # If normal strategy isn't working, try a more aggressive approach
        logger.info(
            f"Switching to adaptive strategy for session {session_id}, attempt {attempt_number}"
        )

        # Create a custom adaptive strategy
        return ErrorFixingStrategy(
            category=ErrorCategory.SYNTAX,  # Start with most fundamental issues
            temperature=0.1,  # Very conservative
            focus_instructions="""
ADAPTIVE STRATEGY - Previous attempts failed to improve quality significantly.

Focus on FUNDAMENTAL issues first:
1. Fix ALL syntax errors that prevent code execution
2. Resolve ALL variable redeclaration issues
3. Ensure basic Three.js scene setup is correct
4. Only then address advanced issues

Be extremely careful and systematic. Test each fix mentally before proceeding.
""",
            examples=[],
            success_indicators=[
                "code executes without errors",
                "no console errors",
                "basic scene renders",
            ],
        )

    async def fix_html_errors(
        self, html_content: str, validation_errors: list, provider: str = "openai"
    ) -> dict:
        """
        Fix HTML errors using the enhanced error fixing system.

        Args:
            html_content: The HTML content to fix
            validation_errors: List of validation errors
            provider: LLM provider to use for fixing

        Returns:
            Dict containing fixed HTML and metadata
        """
        try:
            # Create a fixing prompt
            fixing_prompt = self.create_enhanced_error_fixing_prompt(
                original_html=html_content,
                errors=validation_errors,
                attempt_number=1,
                previous_quality_score=None,
                target_quality_improvement=2.0,
            )

            # Call the LLM to fix the HTML
            from app.utils.llm_utils import generate_with_provider
            
            fixed_html = await generate_with_provider(fixing_prompt, provider)
            
            if not fixed_html:
                logger.warning("LLM returned empty response for HTML fixing")
                return {
                    "success": False,
                    "error": "LLM returned empty response",
                    "fixed_html": html_content,
                    "errors_addressed": 0,
                    "provider": provider,
                }

            return {
                "success": True,
                "fixed_html": fixed_html,
                "prompt": fixing_prompt,
                "errors_addressed": len(validation_errors),
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"Error in fix_html_errors: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixed_html": html_content,
                "errors_addressed": 0,
            }


# Create singleton instance
enhanced_error_fixing_service = EnhancedErrorFixingService()
