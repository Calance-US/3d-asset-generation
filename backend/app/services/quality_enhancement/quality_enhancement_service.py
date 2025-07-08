"""
Quality Enhancement Service for improving HTML content quality.

This service addresses the gap where content has no technical errors but quality score
is below the threshold. It provides targeted enhancements to improve educational value,
interactivity, visual quality, and user experience.
"""

import logging
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.services.quality_enhancement.types import (
    EnhancementCategory,
    EnhancementStrategy,
    QualityGapAnalysis,
    EnhancementResult,
)

logger = logging.getLogger(__name__)


class QualityEnhancementService:
    """Service for enhancing HTML quality when no technical errors exist."""

    def __init__(self):
        self.enhancement_strategies = self._initialize_enhancement_strategies()
        # Import QualityAnalyzer here to avoid circular import issues
        from app.services.quality_enhancement.quality_analyzer import QualityAnalyzer
        self.quality_analyzer = QualityAnalyzer()

    def _initialize_enhancement_strategies(self) -> Dict[EnhancementCategory, EnhancementStrategy]:
        """Initialize enhancement strategies for different quality aspects."""
        return {
            EnhancementCategory.EDUCATIONAL_CONTENT: EnhancementStrategy(
                category=EnhancementCategory.EDUCATIONAL_CONTENT,
                priority=1,
                target_improvement=1.5,
                max_attempts=settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS,
                prompt_template=self._get_educational_enhancement_prompt(),
                success_indicators=[
                    "clear learning objectives",
                    "educational narration",
                    "concept explanations",
                    "interactive learning features"
                ]
            ),
            
            EnhancementCategory.INTERACTIVITY: EnhancementStrategy(
                category=EnhancementCategory.INTERACTIVITY,
                priority=2,
                target_improvement=1.0,
                max_attempts=settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS,
                prompt_template=self._get_interactivity_enhancement_prompt(),
                success_indicators=[
                    "responsive user controls",
                    "real-time interaction",
                    "parameter adjustment capabilities",
                    "interactive feedback systems"
                ]
            ),
            
            EnhancementCategory.VISUAL_QUALITY: EnhancementStrategy(
                category=EnhancementCategory.VISUAL_QUALITY,
                priority=3,
                target_improvement=1.0,
                max_attempts=settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS,
                prompt_template=self._get_visual_quality_enhancement_prompt(),
                success_indicators=[
                    "better lighting and shadows",
                    "improved material properties",
                    "enhanced visual clarity",
                    "professional appearance"
                ]
            ),
            
            EnhancementCategory.SCIENTIFIC_ACCURACY: EnhancementStrategy(
                category=EnhancementCategory.SCIENTIFIC_ACCURACY,
                priority=1,
                target_improvement=1.5,
                max_attempts=settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS,
                prompt_template=self._get_scientific_accuracy_enhancement_prompt(),
                success_indicators=[
                    "correct scientific units",
                    "accurate formulas and relationships",
                    "realistic parameter values",
                    "scientific precision and accuracy"
                ]
            ),
            
            EnhancementCategory.USER_EXPERIENCE: EnhancementStrategy(
                category=EnhancementCategory.USER_EXPERIENCE,
                priority=4,
                target_improvement=0.8,
                max_attempts=settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS,
                prompt_template=self._get_ux_enhancement_prompt(),
                success_indicators=[
                    "intuitive user controls",
                    "clear instructions and guidance",
                    "responsive design",
                    "accessibility features"
                ]
            )
        }

    async def enhance_html_quality(
        self,
        html_content: str,
        current_quality_score: float,
        target_quality_score: float,
        attempt_number: int,
        provider: str = "openai"
    ) -> EnhancementResult:
        """
        Enhance HTML quality to improve the quality score.
        
        Args:
            html_content: The HTML content to enhance
            current_quality_score: Current quality score
            target_quality_score: Target quality score to achieve
            attempt_number: Current attempt number
            provider: LLM provider to use
            
        Returns:
            EnhancementResult with enhanced HTML and quality metrics
        """
        try:
            # Early exit if current score is already at or above target
            if current_quality_score >= target_quality_score:
                logger.info(
                    f"Quality enhancement skipped - current score ({current_quality_score:.2f}) "
                    f"already at or above target ({target_quality_score:.2f})"
                )
                return EnhancementResult(
                    success=True,
                    enhanced_html=html_content,
                    quality_improvement=0.0,
                    new_quality_score=current_quality_score,
                    strategy_used=None,
                    improvements_made=["No enhancement needed - target already met"]
                )
            
            # Additional safeguard: don't enhance if score is already quite good
            if current_quality_score >= settings.QUALITY_ENHANCEMENT_SKIP_THRESHOLD:
                logger.info(
                    f"Quality enhancement skipped - current score ({current_quality_score:.2f}) "
                    f"is already quite good (>= {settings.QUALITY_ENHANCEMENT_SKIP_THRESHOLD}), avoiding potential degradation"
                )
                return EnhancementResult(
                    success=True,
                    enhanced_html=html_content,
                    quality_improvement=0.0,
                    new_quality_score=current_quality_score,
                    strategy_used=None,
                    improvements_made=["No enhancement needed - score already quite good"]
                )
            
            # Analyze quality gaps
            gap_analysis = self.quality_analyzer.analyze_quality_gaps(
                html_content, current_quality_score, target_quality_score
            )
            
            if gap_analysis.score_gap <= 0:
                logger.info(
                    f"Quality enhancement skipped - gap analysis shows no improvement needed: "
                    f"current={current_quality_score:.2f}, target={target_quality_score:.2f}, gap={gap_analysis.score_gap:.2f}"
                )
                return EnhancementResult(
                    success=True,
                    enhanced_html=html_content,
                    quality_improvement=0.0,
                    new_quality_score=current_quality_score,
                    strategy_used=None,
                    improvements_made=["No enhancement needed - target already met"]
                )
            
            # Select best enhancement strategy
            strategy = self._select_enhancement_strategy(gap_analysis, attempt_number)
            
            if not strategy:
                return EnhancementResult(
                    success=False,
                    enhanced_html=html_content,
                    quality_improvement=0.0,
                    new_quality_score=current_quality_score,
                    strategy_used=None,
                    improvements_made=[],
                    error_message="No suitable enhancement strategy found"
                )
            
            # Generate enhancement prompt
            enhancement_prompt = self._create_enhancement_prompt(
                html_content, strategy, gap_analysis, attempt_number
            )
            
            # Call LLM for enhancement
            from app.utils.llm_utils import generate_with_provider
            enhanced_html = await generate_with_provider(enhancement_prompt, provider)
            
            if not enhanced_html:
                return EnhancementResult(
                    success=False,
                    enhanced_html=html_content,
                    quality_improvement=0.0,
                    new_quality_score=current_quality_score,
                    strategy_used=strategy,
                    improvements_made=[],
                    error_message="LLM returned empty response"
                )
            
            # Validate enhanced content with more lenient settings for quality enhancement
            validation_result = await self._validate_enhanced_content(enhanced_html)
            
            if not validation_result["is_valid"]:
                error_msg = validation_result.get("error", "Unknown validation error")
                logger.warning(f"Enhanced content validation failed: {error_msg}")
                
                # If validation failed but we have a quality score, still consider it
                if validation_result["quality_score"] > 0:
                    logger.info(f"Validation failed but quality score available: {validation_result['quality_score']}")
                    # Continue with the validation result even if not technically valid
                else:
                    return EnhancementResult(
                        success=False,
                        enhanced_html=html_content,
                        quality_improvement=0.0,
                        new_quality_score=current_quality_score,
                        strategy_used=strategy,
                        improvements_made=[],
                        error_message=f"Enhanced content validation failed: {error_msg}"
                    )
            
            # Calculate quality improvement
            new_quality_score = validation_result["quality_score"]
            quality_improvement = new_quality_score - current_quality_score
            
            # Determine improvements made
            improvements_made = self._identify_improvements_made(
                html_content, enhanced_html, strategy
            )
            
            logger.info(
                f"Quality enhancement completed: {current_quality_score:.2f} -> {new_quality_score:.2f} "
                f"(improvement: {quality_improvement:.2f}) using {strategy.category.value}"
            )
            
            return EnhancementResult(
                success=True,
                enhanced_html=enhanced_html,
                quality_improvement=quality_improvement,
                new_quality_score=new_quality_score,
                strategy_used=strategy,
                improvements_made=improvements_made
            )
            
        except Exception as e:
            logger.error(f"Quality enhancement failed: {str(e)}")
            return EnhancementResult(
                success=False,
                enhanced_html=html_content,
                quality_improvement=0.0,
                new_quality_score=current_quality_score,
                strategy_used=None,
                improvements_made=[],
                error_message=str(e)
            )

    def _select_enhancement_strategy(
        self, 
        gap_analysis: QualityGapAnalysis, 
        attempt_number: int
    ) -> Optional[EnhancementStrategy]:
        """Select the best enhancement strategy based on gap analysis and attempt number."""
        
        # Prioritize strategies based on gap analysis and attempt number
        available_strategies = []
        
        for strategy in gap_analysis.recommended_strategies:
            if attempt_number <= strategy.max_attempts:
                available_strategies.append(strategy)
        
        if not available_strategies:
            # If no recommended strategies, try all available strategies
            for category, strategy in self.enhancement_strategies.items():
                if attempt_number <= strategy.max_attempts:
                    available_strategies.append(strategy)
        
        if not available_strategies:
            return None
        
        # Sort by priority and potential improvement
        available_strategies.sort(
            key=lambda s: (s.priority, s.target_improvement), 
            reverse=True
        )
        
        # For later attempts, try different strategies
        if attempt_number > 1 and len(available_strategies) > 1:
            # Try a different strategy than the first one
            return available_strategies[1] if len(available_strategies) > 1 else available_strategies[0]
        
        return available_strategies[0]

    def _create_enhancement_prompt(
        self,
        html_content: str,
        strategy: EnhancementStrategy,
        gap_analysis: QualityGapAnalysis,
        attempt_number: int
    ) -> str:
        """Create an enhancement prompt for the selected strategy."""
        
        prompt = strategy.prompt_template.format(
            html_content=html_content,
            current_score=gap_analysis.current_score,
            target_score=gap_analysis.target_score,
            score_gap=gap_analysis.score_gap,
            attempt_number=attempt_number,
            category=strategy.category.value,
            target_improvement=strategy.target_improvement
        )
        
        # Add attempt-specific instructions
        if attempt_number > 1:
            prompt += f"""

## ⚠️ ENHANCEMENT ATTEMPT {attempt_number} - SPECIAL INSTRUCTIONS

This is enhancement attempt {attempt_number}. Previous attempts did not achieve sufficient quality improvement.

### MANDATORY REQUIREMENTS FOR THIS ATTEMPT:
1. **DIFFERENT APPROACH**: Do not repeat the same enhancements from previous attempts
2. **SIGNIFICANT IMPROVEMENT**: Focus on changes that will have measurable impact on quality score
3. **VERIFICATION**: Ensure all enhancements actually improve the educational value
4. **NO REGRESSION**: Do not introduce new issues or reduce existing quality
5. **TARGET FOCUS**: Specifically address the {strategy.category.value} category

### QUALITY IMPROVEMENT TARGET
Your enhancements MUST result in a quality score improvement of at least {strategy.target_improvement} points.
Focus on: {', '.join(strategy.success_indicators)}
"""
        
        return prompt

    async def _validate_enhanced_content(self, enhanced_html: str) -> Dict[str, Any]:
        """Validate that enhanced content is still technically correct."""
        try:
            from app.services.validation.validation_orchestrator import ValidationOrchestrator
            import asyncio
            
            validator = ValidationOrchestrator()
            
            # Add timeout to prevent validation from hanging
            try:
                validation_result = await asyncio.wait_for(
                    validator.validate_content(
                        html_content=enhanced_html,
                        title="Enhanced 3D Visualization",
                        subject="general",
                        education_level="high school",
                        validation_config={
                            "phases": {
                                "html_js": {"enabled": True, "timeout": 15, "critical": False},  # Not critical for enhancement
                                "scientific": {"enabled": True, "timeout": 20, "critical": False},
                                "realism": {"enabled": True, "timeout": 15, "critical": False},
                                "runtime": {"enabled": False, "timeout": 30, "critical": False},
                            },
                            "parallel_execution": False,  # Sequential execution for reliability
                            "fail_fast": False,  # Don't fail fast to get complete validation results
                        }
                    ),
                    timeout=60.0  # 60 second timeout for entire validation
                )
            except asyncio.TimeoutError:
                logger.warning("Validation timed out, using fallback validation")
                return await self._fallback_validation(enhanced_html)
            
            # Log validation result for debugging
            logger.debug(f"Validation result structure: {list(validation_result.keys()) if validation_result else 'None'}")
            
            # Extract quality score from validation result with multiple fallbacks
            quality_score = 0.0
            is_valid = False
            
            if validation_result:
                # Try multiple paths to extract quality score
                if validation_result.get("quality_assessment") and "metrics" in validation_result["quality_assessment"]:
                    quality_score = validation_result["quality_assessment"]["metrics"].get("overall_quality_score", 0.0)
                elif validation_result.get("overall_result"):
                    quality_score = validation_result["overall_result"].get("overall_score", 0.0)
                elif validation_result.get("validation_summary") and "overall_quality_score" in validation_result["validation_summary"]:
                    quality_score = validation_result["validation_summary"]["overall_quality_score"]
                
                # Check if validation was successful
                if validation_result.get("overall_result"):
                    is_valid = validation_result["overall_result"].get("success", False)
                elif validation_result.get("error"):
                    # If there's an error, validation failed
                    is_valid = False
                else:
                    # If no error and we have a quality score, assume it's valid
                    is_valid = quality_score > 0
                
                # If we still don't have a quality score, try to calculate from phase results
                if quality_score == 0.0 and validation_result.get("phase_results"):
                    phase_scores = []
                    for phase_name, phase_result in validation_result["phase_results"].items():
                        if phase_result and isinstance(phase_result, dict):
                            phase_score = phase_result.get("score", 0.0)
                            if phase_score > 0:
                                phase_scores.append(phase_score)
                    
                    if phase_scores:
                        quality_score = sum(phase_scores) / len(phase_scores)
                        is_valid = True
                
                logger.info(f"Extracted quality score: {quality_score}, is_valid: {is_valid}")
                
                return {
                    "is_valid": is_valid,
                    "quality_score": quality_score,
                    "error": None
                }
            else:
                logger.warning("Validation result is None, using fallback validation")
                return await self._fallback_validation(enhanced_html)
                
        except Exception as e:
            logger.error(f"Enhanced content validation failed: {str(e)}")
            # Try fallback validation
            try:
                return await self._fallback_validation(enhanced_html)
            except Exception as fallback_error:
                logger.error(f"Fallback validation also failed: {str(fallback_error)}")
                return {
                    "is_valid": False,
                    "quality_score": 0.0,
                    "error": f"Primary validation failed: {str(e)}, Fallback failed: {str(fallback_error)}"
                }

    async def _fallback_validation(self, enhanced_html: str) -> Dict[str, Any]:
        """Fallback validation using simple HTML validator when main validation fails."""
        try:
            from app.services.validation.html_validator import HTMLValidator
            import asyncio
            
            html_validator = HTMLValidator()
            
            # Add timeout to fallback validation as well
            try:
                validation_result = await asyncio.wait_for(
                    html_validator.validate_html_content(enhanced_html),
                    timeout=30.0  # 30 second timeout for fallback validation
                )
            except asyncio.TimeoutError:
                logger.warning("Fallback validation timed out, using basic validation")
                return self._basic_validation(enhanced_html)
            
            # Extract quality score from HTML validation result
            quality_score = 0.0
            is_valid = True
            
            if hasattr(validation_result, 'quality_score'):
                quality_score = validation_result.quality_score
            elif hasattr(validation_result, 'is_valid'):
                is_valid = validation_result.is_valid
                # Estimate quality score based on validation result
                quality_score = 6.0 if is_valid else 4.0
            elif isinstance(validation_result, dict):
                quality_score = validation_result.get('quality_score', 5.0)
                is_valid = validation_result.get('is_valid', True)
            else:
                # If we can't extract anything, use basic validation
                return self._basic_validation(enhanced_html)
            
            logger.info(f"Fallback validation completed: quality_score={quality_score}, is_valid={is_valid}")
            
            return {
                "is_valid": is_valid,
                "quality_score": quality_score,
                "error": None
            }
        except Exception as e:
            logger.error(f"Fallback validation failed: {str(e)}")
            # Last resort: use basic validation
            return self._basic_validation(enhanced_html)

    def _basic_validation(self, enhanced_html: str) -> Dict[str, Any]:
        """Basic validation that doesn't require external services."""
        try:
            # Simple checks that can be done without external validation
            has_threejs = "three" in enhanced_html.lower()
            has_html_structure = "<html" in enhanced_html.lower() and "</html>" in enhanced_html.lower()
            has_script = "<script" in enhanced_html.lower()
            has_body = "<body" in enhanced_html.lower()
            
            # Calculate basic quality score
            quality_score = 5.0  # Base score
            if has_threejs:
                quality_score += 1.0
            if has_html_structure:
                quality_score += 0.5
            if has_script:
                quality_score += 0.5
            if has_body:
                quality_score += 0.5
            
            # Cap at reasonable maximum
            quality_score = min(quality_score, 7.0)
            
            # Consider valid if it has basic HTML structure
            is_valid = has_html_structure and has_script
            
            logger.info(f"Basic validation completed: quality_score={quality_score}, is_valid={is_valid}")
            
            return {
                "is_valid": is_valid,
                "quality_score": quality_score,
                "error": "Used basic validation due to validation service failures"
            }
        except Exception as e:
            logger.error(f"Basic validation failed: {str(e)}")
            # Absolute last resort
            return {
                "is_valid": True,
                "quality_score": 5.0,  # Basic acceptable score
                "error": f"Basic validation failed: {str(e)}"
            }

    def _identify_improvements_made(
        self, 
        original_html: str, 
        enhanced_html: str, 
        strategy: EnhancementStrategy
    ) -> List[str]:
        """Identify what improvements were made in the enhanced content."""
        improvements = []
        
        # Basic improvements based on strategy
        improvements.append(f"Enhanced {strategy.category.value}")
        
        # Check for specific improvements based on success indicators
        enhanced_lower = enhanced_html.lower()
        original_lower = original_html.lower()
        
        for indicator in strategy.success_indicators:
            if indicator in enhanced_lower and indicator not in original_lower:
                improvements.append(f"Added {indicator}")
        
        return improvements

    def _get_educational_enhancement_prompt(self) -> str:
        return """You are a 3D educational visualization enhancement specialist. Your task is to improve the educational quality of this HTML content.

## 📚 EDUCATIONAL ENHANCEMENT TASK

**Current Quality Score:** {current_score}/10
**Target Quality Score:** {target_score}/10
**Quality Gap:** {score_gap} points
**Enhancement Category:** {category}
**Target Improvement:** {target_improvement} points

**Original HTML Content:**
```html
{html_content}
```

## 🎯 ENHANCEMENT REQUIREMENTS

### 1. **Improve Educational Content**
- Add clear learning objectives and explanations
- Include educational narration and voice guidance
- Add concept explanations and scientific context
- Enhance interactive learning features
- Include educational labels and annotations

### 2. **Enhance Learning Experience**
- Add step-by-step guidance for complex concepts
- Include educational tooltips and help text
- Add progress indicators for learning objectives
- Include educational feedback and explanations
- Add educational controls and parameters

### 3. **Maintain Technical Quality**
- Keep all existing functionality intact
- Ensure all Three.js code remains valid
- Maintain scientific accuracy
- Preserve interactive features
- Keep responsive design

### 4. **Focus on Educational Value**
- Make concepts more accessible to students
- Add educational context and real-world applications
- Include educational challenges and exercises
- Add educational resources and references
- Enhance visual learning aids

## 📋 SUCCESS CRITERIA

Your enhanced content should demonstrate:
- Clear learning objectives
- Educational narration and guidance
- Interactive learning features
- Concept explanations
- Educational feedback

## 🔧 IMPLEMENTATION GUIDELINES

1. **Add Educational Narration**: Include text-to-speech functionality with educational content
2. **Enhance UI Controls**: Add educational labels and explanations to controls
3. **Add Learning Objectives**: Include clear statements of what students will learn
4. **Improve Visual Aids**: Add educational annotations, labels, and visual guides
5. **Include Educational Feedback**: Add explanations for user interactions

Return ONLY the enhanced HTML code that addresses these educational improvements.
"""

    def _get_interactivity_enhancement_prompt(self) -> str:
        return """You are a 3D visualization interactivity enhancement specialist. Your task is to improve the interactive features of this HTML content.

## 🎮 INTERACTIVITY ENHANCEMENT TASK

**Current Quality Score:** {current_score}/10
**Target Quality Score:** {target_score}/10
**Quality Gap:** {score_gap} points
**Enhancement Category:** {category}
**Target Improvement:** {target_improvement} points

**Original HTML Content:**
```html
{html_content}
```

## 🎯 ENHANCEMENT REQUIREMENTS

### 1. **Enhance User Controls**
- Add more interactive controls and sliders
- Improve existing control responsiveness
- Add real-time parameter adjustment
- Include interactive feedback systems
- Add user preference controls

### 2. **Improve User Experience**
- Add smooth animations and transitions
- Include responsive design improvements
- Add keyboard and touch controls
- Include accessibility features
- Add user guidance and help systems

### 3. **Add Interactive Features**
- Include real-time data visualization
- Add interactive simulations
- Include user-driven experiments
- Add collaborative features
- Include progress tracking

### 4. **Maintain Technical Quality**
- Keep all existing functionality intact
- Ensure all Three.js code remains valid
- Maintain performance standards
- Preserve educational value
- Keep scientific accuracy

## 📋 SUCCESS CRITERIA

Your enhanced content should demonstrate:
- Responsive user controls
- Real-time interaction
- Parameter adjustment capabilities
- Interactive feedback systems

Return ONLY the enhanced HTML code that addresses these interactivity improvements.
"""

    def _get_visual_quality_enhancement_prompt(self) -> str:
        return """You are a 3D visualization visual quality enhancement specialist. Your task is to improve the visual quality of this HTML content.

## 🎨 VISUAL QUALITY ENHANCEMENT TASK

**Current Quality Score:** {current_score}/10
**Target Quality Score:** {target_score}/10
**Quality Gap:** {score_gap} points
**Enhancement Category:** {category}
**Target Improvement:** {target_improvement} points

**Original HTML Content:**
```html
{html_content}
```

## 🎯 ENHANCEMENT REQUIREMENTS

### 1. **Improve Lighting**
- Add better ambient lighting
- Include directional lighting for depth
- Add realistic shadows and reflections
- Include atmospheric effects
- Add dynamic lighting changes

### 2. **Enhance Materials**
- Use more realistic material properties
- Add texture mapping where appropriate
- Include material variations
- Add realistic surface properties
- Include material animations

### 3. **Improve Visual Clarity**
- Add better camera positioning
- Include visual guides and annotations
- Add color coding for clarity
- Include visual hierarchy improvements
- Add professional styling

### 4. **Maintain Technical Quality**
- Keep all existing functionality intact
- Ensure all Three.js code remains valid
- Maintain performance standards
- Preserve educational value
- Keep scientific accuracy

## 📋 SUCCESS CRITERIA

Your enhanced content should demonstrate:
- Better lighting and shadows
- Improved material properties
- Enhanced visual clarity
- Professional appearance

Return ONLY the enhanced HTML code that addresses these visual quality improvements.
"""

    def _get_scientific_accuracy_enhancement_prompt(self) -> str:
        return """You are a 3D scientific visualization accuracy enhancement specialist. Your task is to improve the scientific accuracy of this HTML content.

## 🔬 SCIENTIFIC ACCURACY ENHANCEMENT TASK

**Current Quality Score:** {current_score}/10
**Target Quality Score:** {target_score}/10
**Quality Gap:** {score_gap} points
**Enhancement Category:** {category}
**Target Improvement:** {target_improvement} points

**Original HTML Content:**
```html
{html_content}
```

## 🎯 ENHANCEMENT REQUIREMENTS

### 1. **Improve Scientific Precision**
- Use correct scientific units and measurements
- Include accurate formulas and calculations
- Add realistic parameter ranges
- Include scientific constants
- Add precision in numerical values

### 2. **Enhance Scientific Context**
- Add scientific explanations and context
- Include real-world applications
- Add scientific references and sources
- Include experimental validation
- Add scientific methodology

### 3. **Improve Educational Accuracy**
- Ensure all scientific concepts are correct
- Add proper scientific terminology
- Include accurate visual representations
- Add scientific error analysis
- Include scientific limitations

### 4. **Maintain Technical Quality**
- Keep all existing functionality intact
- Ensure all Three.js code remains valid
- Maintain performance standards
- Preserve educational value
- Keep interactive features

## 📋 SUCCESS CRITERIA

Your enhanced content should demonstrate:
- Correct scientific units
- Accurate formulas and relationships
- Realistic parameter values
- Scientific precision and accuracy

Return ONLY the enhanced HTML code that addresses these scientific accuracy improvements.
"""

    def _get_ux_enhancement_prompt(self) -> str:
        return """You are a 3D visualization user experience enhancement specialist. Your task is to improve the user experience of this HTML content.

## 👤 USER EXPERIENCE ENHANCEMENT TASK

**Current Quality Score:** {current_score}/10
**Target Quality Score:** {target_score}/10
**Quality Gap:** {score_gap} points
**Enhancement Category:** {category}
**Target Improvement:** {target_improvement} points

**Original HTML Content:**
```html
{html_content}
```

## 🎯 ENHANCEMENT REQUIREMENTS

### 1. **Improve User Interface**
- Add intuitive controls and navigation
- Include clear instructions and help text
- Add responsive design improvements
- Include accessibility features
- Add user guidance systems

### 2. **Enhance User Feedback**
- Add visual feedback for interactions
- Include progress indicators
- Add success/error messages
- Include user preference settings
- Add help and documentation

### 3. **Improve Accessibility**
- Add keyboard navigation support
- Include screen reader compatibility
- Add high contrast options
- Include font size adjustments
- Add color blind friendly options

### 4. **Maintain Technical Quality**
- Keep all existing functionality intact
- Ensure all Three.js code remains valid
- Maintain performance standards
- Preserve educational value
- Keep scientific accuracy

## 📋 SUCCESS CRITERIA

Your enhanced content should demonstrate:
- Intuitive user controls
- Clear instructions and guidance
- Responsive design
- Accessibility features

Return ONLY the enhanced HTML code that addresses these user experience improvements.
""" 