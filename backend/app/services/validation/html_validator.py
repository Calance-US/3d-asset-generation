"""
Comprehensive HTML and JavaScript validation service for 3D visualizations.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import esprima
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in HTML/JS content."""

    type: str  # 'error', 'warning', 'info'
    category: str  # 'html', 'javascript', 'threejs', 'syntax'
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    severity: int = 1  # 1-5, where 5 is critical


@dataclass
class ValidationResult:
    """Result of HTML/JS validation."""

    is_valid: bool
    quality_score: float
    issues: List[ValidationIssue]
    metrics: Dict[str, Any]


class HTMLValidator:
    """Comprehensive HTML and JavaScript validator for 3D visualizations."""

    def __init__(self):
        self.js_error_patterns = [
            # Common JavaScript syntax errors
            (
                r"(?:let|const|var)\s+(\w+).*?(?:let|const|var)\s+\1",
                "Variable redeclaration: {match}",
            ),
            (
                r'import\s+.*?from\s+["\'][^"\']*["\'].*?import\s+.*?from\s+["\'][^"\']*["\']',
                "Duplicate imports detected",
            ),
            (r"\}\s*\{(?!\s*\})", "Missing semicolon between blocks"),
            (
                r"new\s+THREE\.\w+\([^)]*\)\s*\.(?!position|rotation|scale)",
                "Invalid method call on constructor",
            ),
            (
                r"scene\.add\(new\s+THREE\.\w+\([^)]*\)\.(?!position|rotation|scale)",
                "Invalid chaining on constructor",
            ),
            (r"\w+\s*=\s*=\s*\w+", "Assignment instead of comparison (use === or ==)"),
            (
                r"function\s+\w+\([^)]*\)\s*\{[^}]*\}(?!\s*[;}])",
                "Missing semicolon after function declaration",
            ),
        ]

        self.threejs_api_patterns = [
            # Three.js specific validation patterns
            (
                r"new\s+THREE\.MeshBasicMaterial\([^)]*(?:metalness|roughness)",
                "MeshBasicMaterial does not support metalness/roughness",
            ),
            (
                r"new\s+THREE\.LineBasicMaterial\([^)]*emissiveIntensity",
                "LineBasicMaterial does not support emissiveIntensity",
            ),
            (
                r'renderer\.shadowMap\.type\s*=\s*["\']?\w+["\']?(?!THREE\.)',
                "Shadow map type should use THREE.ShadowMapType constants",
            ),
            (
                r"camera\.outputColorSpace\s*=",
                "outputColorSpace is a renderer property, not camera",
            ),
            (
                r"geometry\.dispose\(\)\s*;\s*geometry\.dispose\(\)",
                "Double disposal of geometry",
            ),
            (
                r"new\s+THREE\.(\w+)Geometry\(\)\s*(?!;)",
                "Geometry should be disposed after use",
            ),
        ]

        self.html_required_elements = ["html", "head", "body", "script"]

        self.threejs_required_imports = ["THREE", "OrbitControls"]

    async def validate_html_content(self, html_content: str) -> ValidationResult:
        """
        Perform comprehensive validation of HTML content.

        Args:
            html_content: The HTML content to validate

        Returns:
            ValidationResult containing validation status and issues
        """
        issues = []
        metrics = {
            "html_elements": 0,
            "script_blocks": 0,
            "threejs_objects": 0,
            "event_listeners": 0,
            "validation_time": 0,
        }

        try:
            # 1. HTML Structure Validation
            html_issues = self._validate_html_structure(html_content)
            issues.extend(html_issues)

            # 2. JavaScript Syntax Validation
            js_issues = self._validate_javascript_syntax(html_content)
            issues.extend(js_issues)

            # 3. Three.js API Validation
            threejs_issues = self._validate_threejs_usage(html_content)
            issues.extend(threejs_issues)

            # 4. Import Validation
            import_issues = self._validate_imports(html_content)
            issues.extend(import_issues)

            # 5. Educational Content Validation
            content_issues = self._validate_educational_content(html_content)
            issues.extend(content_issues)

            # Calculate metrics
            metrics = self._calculate_metrics(html_content)

            # Calculate quality score
            quality_score = self._calculate_quality_score(issues, metrics)

            # Determine if valid (no critical errors)
            is_valid = not any(issue.severity >= 4 for issue in issues)

            logger.info(
                f"HTML validation completed: {len(issues)} issues found, quality score: {quality_score:.2f}"
            )

            return ValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                issues=issues,
                metrics=metrics,
            )

        except Exception as e:
            logger.error(f"Error during HTML validation: {str(e)}")
            issues.append(
                ValidationIssue(
                    type="error",
                    category="validation",
                    message=f"Validation failed: {str(e)}",
                    severity=5,
                )
            )

            return ValidationResult(
                is_valid=False, quality_score=0.0, issues=issues, metrics=metrics
            )

    def _validate_html_structure(self, html_content: str) -> List[ValidationIssue]:
        """Validate HTML document structure."""
        issues = []

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Check for required elements
            for element in self.html_required_elements:
                if not soup.find(element):
                    issues.append(
                        ValidationIssue(
                            type="error",
                            category="html",
                            message=f"Missing required HTML element: <{element}>",
                            severity=4,
                        )
                    )

            # Check DOCTYPE
            if not html_content.strip().startswith("<!DOCTYPE html>"):
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="html",
                        message="Missing or incorrect DOCTYPE declaration",
                        severity=2,
                    )
                )

            # Check for proper HTML5 structure
            html_tag = soup.find("html")
            if html_tag and hasattr(html_tag, "get") and not html_tag.get("lang"):
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="html",
                        message="Missing lang attribute on <html> element",
                        severity=1,
                    )
                )

            # Check meta viewport for responsiveness
            if not soup.find("meta", attrs={"name": "viewport"}):
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="html",
                        message="Missing viewport meta tag for responsive design",
                        severity=2,
                    )
                )

            # Check for script type="module"
            script_tags = soup.find_all("script")
            module_script_found = False
            for script in script_tags:
                if hasattr(script, "get") and script.get("type") == "module":
                    module_script_found = True
                    break

            if not module_script_found:
                issues.append(
                    ValidationIssue(
                        type="error",
                        category="html",
                        message="No script with type='module' found - required for ES6 imports",
                        severity=4,
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="html",
                    message=f"HTML parsing failed: {str(e)}",
                    severity=5,
                )
            )

        return issues

    def _validate_javascript_syntax(self, html_content: str) -> List[ValidationIssue]:
        """Validate JavaScript syntax within script tags."""
        issues = []

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            script_tags = soup.find_all("script")

            for i, script in enumerate(script_tags):
                if script.string:
                    js_code = script.string

                    # Basic syntax validation using esprima
                    try:
                        # Try parsing as ES6 module first (for script type="module")
                        if (
                            (hasattr(script, "get") and script.get("type") == "module")
                            or "import " in js_code
                            or "export " in js_code
                        ):
                            esprima.parseModule(js_code)
                        else:
                            esprima.parseScript(js_code)
                    except Exception as e:
                        issues.append(
                            ValidationIssue(
                                type="error",
                                category="javascript",
                                message=f"JavaScript syntax error in script block {i + 1}: {str(e)}",
                                severity=5,
                            )
                        )
                        continue

                    # Pattern-based validation
                    for pattern, message in self.js_error_patterns:
                        matches = re.finditer(
                            pattern, js_code, re.MULTILINE | re.DOTALL
                        )
                        for match in matches:
                            line_num = js_code[: match.start()].count("\n") + 1
                            issues.append(
                                ValidationIssue(
                                    type="error",
                                    category="javascript",
                                    message=message.format(match=match.group()),
                                    line_number=line_num,
                                    severity=3,
                                )
                            )

                    # Check for common issues
                    issues.extend(self._check_common_js_issues(js_code, i + 1))

        except Exception as e:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="javascript",
                    message=f"JavaScript validation failed: {str(e)}",
                    severity=4,
                )
            )

        return issues

    def _validate_threejs_usage(self, html_content: str) -> List[ValidationIssue]:
        """Validate Three.js specific API usage."""
        issues = []

        try:
            # Extract JavaScript code
            soup = BeautifulSoup(html_content, "html.parser")
            js_code = ""
            for script in soup.find_all("script"):
                if script.string:
                    js_code += script.string + "\n"

            # Three.js specific validation
            for pattern, message in self.threejs_api_patterns:
                matches = re.finditer(pattern, js_code, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_num = js_code[: match.start()].count("\n") + 1
                    issues.append(
                        ValidationIssue(
                            type="error",
                            category="threejs",
                            message=message,
                            line_number=line_num,
                            severity=3,
                        )
                    )

            # Check for required Three.js objects
            required_objects = ["scene", "camera", "renderer"]
            for obj in required_objects:
                if not re.search(rf"\b{obj}\s*=.*?new\s+THREE\.", js_code):
                    issues.append(
                        ValidationIssue(
                            type="error",
                            category="threejs",
                            message=f"Missing required Three.js object: {obj}",
                            severity=4,
                        )
                    )

            # Check for render loop
            if not re.search(r"requestAnimationFrame|setInterval.*render", js_code):
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="threejs",
                        message="No animation/render loop detected",
                        severity=2,
                    )
                )

            # Check for proper disposal
            geometry_creations = len(re.findall(r"new\s+THREE\.\w*Geometry", js_code))
            geometry_disposals = len(re.findall(r"\.dispose\(\)", js_code))

            if geometry_creations > 0 and geometry_disposals == 0:
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="threejs",
                        message="Geometries created but not disposed - potential memory leak",
                        severity=2,
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="threejs",
                    message=f"Three.js validation failed: {str(e)}",
                    severity=3,
                )
            )

        return issues

    def _validate_imports(self, html_content: str) -> List[ValidationIssue]:
        """Validate ES6 import statements."""
        issues = []

        try:
            # Extract JavaScript code
            soup = BeautifulSoup(html_content, "html.parser")
            js_code = ""
            for script in soup.find_all("script"):
                if script.string:
                    js_code += script.string + "\n"

            # Find all import statements
            import_pattern = r'import\s+.*?from\s+["\']([^"\']+)["\']'
            imports = re.findall(import_pattern, js_code)

            # Check for required imports
            for required_import in self.threejs_required_imports:
                import_found = False
                for imp in imports:
                    if required_import.lower() in imp.lower():
                        import_found = True
                        break

                if not import_found:
                    issues.append(
                        ValidationIssue(
                            type="error",
                            category="javascript",
                            message=f"Missing required import: {required_import}",
                            severity=4,
                        )
                    )

            # Check for valid CDN URLs
            for imp in imports:
                if "jsdelivr.net" in imp or "unpkg.com" in imp:
                    continue  # Valid CDN
                elif imp.startswith("./") or imp.startswith("../"):
                    issues.append(
                        ValidationIssue(
                            type="warning",
                            category="javascript",
                            message=f"Relative import may not work in standalone HTML: {imp}",
                            severity=2,
                        )
                    )
                elif not imp.startswith("http"):
                    issues.append(
                        ValidationIssue(
                            type="error",
                            category="javascript",
                            message=f"Invalid import path: {imp}",
                            severity=3,
                        )
                    )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="javascript",
                    message=f"Import validation failed: {str(e)}",
                    severity=3,
                )
            )

        return issues

    def _validate_educational_content(self, html_content: str) -> List[ValidationIssue]:
        """Validate educational content requirements."""
        issues = []

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            text_content = soup.get_text().lower()

            # Check for educational elements
            if "learning" not in text_content and "educational" not in text_content:
                issues.append(
                    ValidationIssue(
                        type="info",
                        category="educational",
                        message="No explicit educational content detected",
                        severity=1,
                    )
                )

            # Check for narration elements
            js_code = ""
            for script in soup.find_all("script"):
                if script.string:
                    js_code += script.string.lower() + "\n"

            if "speechsynthesis" not in js_code and "utterance" not in js_code:
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="educational",
                        message="No text-to-speech/narration functionality detected",
                        severity=2,
                    )
                )

            # Check for interactive controls
            if "addeventlistener" not in js_code and "onclick" not in js_code:
                issues.append(
                    ValidationIssue(
                        type="warning",
                        category="educational",
                        message="Limited interactivity detected",
                        severity=1,
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="educational",
                    message=f"Educational content validation failed: {str(e)}",
                    severity=2,
                )
            )

        return issues

    def _check_common_js_issues(
        self, js_code: str, script_num: int
    ) -> List[ValidationIssue]:
        """Check for common JavaScript issues."""
        issues = []

        # Check for unclosed brackets
        open_braces = js_code.count("{")
        close_braces = js_code.count("}")
        if open_braces != close_braces:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="javascript",
                    message=f"Mismatched braces in script {script_num}: {open_braces} open, {close_braces} close",
                    severity=4,
                )
            )

        # Check for unclosed parentheses
        open_parens = js_code.count("(")
        close_parens = js_code.count(")")
        if open_parens != close_parens:
            issues.append(
                ValidationIssue(
                    type="error",
                    category="javascript",
                    message=f"Mismatched parentheses in script {script_num}: {open_parens} open, {close_parens} close",
                    severity=4,
                )
            )

        # Check for console.log statements (should be removed in production)
        if "console.log" in js_code:
            issues.append(
                ValidationIssue(
                    type="info",
                    category="javascript",
                    message="Console.log statements found - consider removing for production",
                    severity=1,
                )
            )

        return issues

    def _calculate_metrics(self, html_content: str) -> Dict[str, Any]:
        """Calculate various metrics about the HTML content."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Basic metrics
            metrics = {
                "html_elements": len(soup.find_all()),
                "script_blocks": len(soup.find_all("script")),
                "style_blocks": len(soup.find_all("style")),
                "content_length": len(html_content),
            }

            # JavaScript-specific metrics
            js_code = ""
            for script in soup.find_all("script"):
                if script.string:
                    js_code += script.string + "\n"

            if js_code:
                metrics.update(
                    {
                        "js_length": len(js_code),
                        "threejs_objects": len(re.findall(r"new\s+THREE\.", js_code)),
                        "event_listeners": len(
                            re.findall(r"addEventListener", js_code)
                        ),
                        "functions_defined": len(
                            re.findall(r"function\s+\w+", js_code)
                        ),
                        "imports_count": len(re.findall(r"import\s+.*?from", js_code)),
                    }
                )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {"error": str(e)}

    def _calculate_quality_score(
        self, issues: List[ValidationIssue], metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score based on issues and metrics."""
        base_score = 10.0

        # Deduct points for issues
        for issue in issues:
            if issue.severity == 5:  # Critical
                base_score -= 3.0
            elif issue.severity == 4:  # High
                base_score -= 2.0
            elif issue.severity == 3:  # Medium
                base_score -= 1.0
            elif issue.severity == 2:  # Low
                base_score -= 0.5
            elif issue.severity == 1:  # Info
                base_score -= 0.1

        # Bonus points for good practices
        if metrics.get("threejs_objects", 0) > 0:
            base_score += 0.5
        if metrics.get("event_listeners", 0) > 0:
            base_score += 0.5
        if metrics.get("imports_count", 0) >= 2:
            base_score += 0.3

        # Ensure score is between 0 and 10
        return max(0.0, min(10.0, base_score))

    def get_quality_summary(self, result: ValidationResult) -> str:
        """Generate a human-readable quality summary."""
        summary_parts = []

        if result.is_valid:
            summary_parts.append("✅ HTML is valid")
        else:
            summary_parts.append("❌ HTML has critical issues")

        summary_parts.append(f"Quality Score: {result.quality_score:.1f}/10")

        # Issue breakdown
        error_count = sum(1 for issue in result.issues if issue.type == "error")
        warning_count = sum(1 for issue in result.issues if issue.type == "warning")
        info_count = sum(1 for issue in result.issues if issue.type == "info")

        if error_count > 0:
            summary_parts.append(f"🔴 {error_count} errors")
        if warning_count > 0:
            summary_parts.append(f"🟡 {warning_count} warnings")
        if info_count > 0:
            summary_parts.append(f"ℹ️ {info_count} info")

        return " | ".join(summary_parts)
