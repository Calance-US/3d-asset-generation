import logging
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ErrorFixingService:
    """Service for generating error-fixing prompts and managing retry logic."""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent / "prompts"
        self.template_path = self.base_path / settings.ERROR_FIXING_TEMPLATE_PATH
        self.env = Environment(loader=FileSystemLoader(str(self.base_path)))

    def create_error_fixing_prompt(
        self, original_html: str, errors: List[Dict[str, Any]]
    ) -> str:
        """
        Create an error-fixing prompt based on validation errors.

        Args:
            original_html: The original HTML content with errors
            errors: List of validation errors with details

        Returns:
            Formatted error-fixing prompt
        """
        try:
            # Try to read template file directly if Jinja2 fails
            template_file = self.base_path / settings.ERROR_FIXING_TEMPLATE_PATH
            if template_file.exists():
                with open(template_file, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Format errors for template
                formatted_errors = []
                for error in errors:
                    formatted_errors.append(
                        {
                            "phase": error.get("phase", "unknown"),
                            "severity": error.get("severity", "unknown"),
                            "error_type": error.get("error_type", "unknown"),
                            "message": error.get("message", ""),
                            "location": error.get("location"),
                            "suggestion": error.get("suggestion"),
                            "context": error.get("context"),
                        }
                    )

                # Simple template replacement for now
                errors_text = ""
                for error in formatted_errors:
                    errors_text += f"### {error['phase']} - {error['severity']}\n"
                    errors_text += f"**Error Type:** {error['error_type']}\n"
                    errors_text += f"**Message:** {error['message']}\n"
                    if error["location"]:
                        errors_text += f"**Location:** {error['location']}\n"
                    if error["suggestion"]:
                        errors_text += f"**Suggested Fix:** {error['suggestion']}\n"
                    if error["context"]:
                        errors_text += f"**Context:** {error['context']}\n"
                    errors_text += "\n"

                # Replace template variables manually
                prompt = template_content.replace("{{ original_html }}", original_html)
                prompt = prompt.replace("{% for error in validation_errors %}", "")
                prompt = prompt.replace("{% endfor %}", "")

                # Insert the formatted errors
                if "### {{ error.phase }} - {{ error.severity }}" in prompt:
                    prompt = prompt.replace(
                        "### {{ error.phase }} - {{ error.severity }}", errors_text
                    )
                else:
                    # Fallback: insert errors after the original HTML section
                    prompt = prompt.replace(
                        "{{ original_html }}",
                        f"{original_html}\n\n**Validation Errors Detected:**\n{errors_text}",
                    )

                logger.info(f"Generated error-fixing prompt ({len(prompt)} characters)")
                return prompt
            else:
                logger.error(f"Template file not found: {template_file}")
                return self._create_fallback_prompt(original_html, errors)

        except Exception as e:
            logger.error(f"Failed to generate error-fixing prompt: {e}")
            # Fallback to simple template
            return self._create_fallback_prompt(original_html, errors)

    def _create_fallback_prompt(
        self, original_html: str, errors: List[Dict[str, Any]]
    ) -> str:
        """Fallback prompt generation if template loading fails."""
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

    def format_errors_for_logging(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format errors for database storage."""
        formatted_errors = []
        for error in errors:
            formatted_errors.append(
                {
                    "phase": error.get("phase", "unknown"),
                    "severity": error.get("severity", "unknown"),
                    "error_type": error.get("error_type", "unknown"),
                    "message": error.get("message", ""),
                    "location": error.get("location"),
                    "suggestion": error.get("suggestion"),
                    "context": error.get("context"),
                }
            )
        return formatted_errors

    def should_retry(self, errors: List[Dict[str, Any]], attempt: int) -> bool:
        """
        Determine if we should retry based on error types and attempt number.

        Args:
            errors: List of validation errors
            attempt: Current attempt number (0-based)

        Returns:
            True if we should retry, False otherwise
        """
        if attempt >= settings.MAX_LLM_RETRY:
            return False

        # Don't retry for certain types of errors that are unlikely to be fixed
        critical_unfixable_errors = [
            "missing_required_field",
            "invalid_template_structure",
            "system_error",
        ]

        for error in errors:
            if error.get("error_type") in critical_unfixable_errors:
                logger.info(
                    f"Skipping retry due to unfixable error: {error.get('error_type')}"
                )
                return False

        return True

    def get_retry_strategy(
        self, errors: List[Dict[str, Any]], attempt: int
    ) -> Dict[str, Any]:
        """
        Get retry strategy based on error patterns.

        Args:
            errors: List of validation errors
            attempt: Current attempt number

        Returns:
            Dictionary with retry strategy parameters
        """
        # Count error types
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Adjust strategy based on predominant error types
        strategy = {
            "temperature": 0.7,  # Default temperature
            "include_examples": True,
            "focus_areas": [],
        }

        # If many syntax errors, be more conservative
        if (
            error_types.get("variable_redeclaration", 0) > 2
            or error_types.get("syntax_error", 0) > 2
        ):
            strategy["temperature"] = 0.3
            strategy["focus_areas"].append("syntax")

        # If API errors, focus on Three.js compliance
        if (
            error_types.get("invalid_material_property", 0) > 0
            or error_types.get("api_error", 0) > 0
        ):
            strategy["focus_areas"].append("threejs_api")

        # If scientific errors, focus on accuracy
        if (
            error_types.get("incorrect_units", 0) > 0
            or error_types.get("scientific_error", 0) > 0
        ):
            strategy["focus_areas"].append("scientific_accuracy")

        # On later attempts, be more conservative
        if attempt > 1:
            strategy["temperature"] = max(0.1, strategy["temperature"] - 0.2)

        return strategy


# Create singleton instance
error_fixing_service = ErrorFixingService()
