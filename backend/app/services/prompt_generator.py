import json
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from app.config.logging_config import logger
from app.config.settings import get_settings


class PromptGenerator:
    def __init__(self):
        """Initialize the prompt generator with templates and schemas."""
        self.base_path = Path(__file__).parent.parent / "prompts"
        self.template_path = self.base_path / "enhanced_template.prompt.txt"
        self.fallback_template_path = self.base_path / "template.prompt.txt"
        self.schema_path = self.base_path / "template.json"

        # Initialize Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.base_path)))

        # Load template and schema
        self.template = self._load_template()
        self.schema = self._load_schema()

        logger.info(
            "Initialized PromptGenerator with enhanced template",
            extra={"action": "init", "template_directory": str(self.base_path)},
        )

    def generate_prompt(self, config: Dict[str, Any]) -> str:
        """
        Generate a prompt using the provided configuration.

        Args:
            config: Dictionary containing the configuration for the prompt

        Returns:
            str: The generated prompt
        """
        try:
            logger.info(
                "Generating prompt",
                extra={"action": "generate_prompt", "has_config": bool(config)},
            )
            logger.debug(
                "Input configuration",
                extra={"action": "generate_prompt", "config": config},
            )

            # Merge with defaults
            merged_config = self._merge_defaults(config)
            logger.debug(
                "Merged configuration",
                extra={"action": "generate_prompt", "config": merged_config},
            )

            # Verify renderer configuration
            if "renderer" not in merged_config:
                logger.error(
                    "Renderer configuration missing",
                    extra={
                        "action": "generate_prompt",
                        "config_keys": list(merged_config.keys()),
                    },
                )
                raise ValueError("Renderer configuration is required")

            # Add validation-specific template variables
            merged_config = self._add_validation_context(merged_config)

            logger.debug(
                "Enhanced configuration with validation context",
                extra={
                    "action": "generate_prompt",
                    "renderer_config": merged_config["renderer"],
                    "has_validation_context": "subject" in merged_config,
                },
            )

            # Render template using Jinja2
            template = self.env.from_string(self.template)
            prompt = template.render(**merged_config)

            logger.info(
                "Enhanced prompt generated with validation rules",
                extra={"action": "generate_prompt", "prompt_length": len(prompt)},
            )
            return prompt

        except Exception as e:
            logger.error(
                "Error generating prompt",
                extra={
                    "action": "generate_prompt",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            logger.exception("Full traceback")
            raise

    def generate_from_topic(
        self, topic: str, subject: str, education_level: str = "High School"
    ) -> str:
        """
        Generate a prompt from a basic topic and subject.

        Args:
            topic: The main topic to generate a prompt for
            subject: The subject area (e.g., physics, chemistry)
            education_level: The target education level

        Returns:
            str: The generated prompt
        """
        try:
            logger.info(
                "Generating prompt from topic",
                extra={
                    "action": "generate_from_topic",
                    "topic": topic,
                    "subject": subject,
                    "education_level": education_level,
                },
            )

            # Create basic configuration
            config = {
                "topic_name": topic,
                "key_concepts": topic,
                "education_level": education_level,
                "learning_objectives": f"Understand the key concepts of {topic} in {subject}",
                "interactive_features": "Basic 3D navigation and interaction",
                "components": [],
                "materials": [],
                "lights": [],
                "renderer": {
                    "antialias": True,
                    "shadowMapEnabled": True,
                    "shadowMapType": "PCFSoftShadowMap",
                    "toneMapping": "ACESFilmicToneMapping",
                    "outputColorSpace": "SRGBColorSpace",
                },
                "camera_controls": "OrbitControls",
                "interactive_description": "Use mouse to rotate, zoom, and pan the view",
                "animated_elements": "None",
                "curve_points": [],
                "animation_speed": 1.0,
                "tts_language": "en-US",
                "tts_rate": 1.0,
                "tts_pitch": 1.0,
                "narration_texts": [],
            }

            return self.generate_prompt(config)

        except Exception as e:
            logger.error(
                "Error generating prompt from topic",
                extra={
                    "action": "generate_from_topic",
                    "topic": topic,
                    "subject": subject,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    def _merge_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge the provided configuration with default values.
        Only fills in empty or non-set properties, preserving existing values.

        Args:
            config: The user-provided configuration

        Returns:
            Dict[str, Any]: The merged configuration
        """
        try:
            logger.debug(
                "Merging configuration with defaults",
                extra={"action": "merge_with_defaults", "input_config": config},
            )
            logger.debug(f"Input config: {json.dumps(config, indent=2)}")

            def is_empty(value: Any) -> bool:
                if value is None:
                    return True
                if isinstance(value, str) and not value.strip():
                    return True
                if isinstance(value, list) and not value:
                    return True
                if isinstance(value, dict) and not value:
                    return True
                return False

            # Default configuration based on schema
            defaults = {
                "renderer": {
                    "antialias": True,
                    "shadowMapEnabled": True,
                    "shadowMapType": "PCFSoftShadowMap",
                    "toneMapping": "ACESFilmicToneMapping",
                    "outputColorSpace": "SRGBColorSpace",
                }
            }

            # Start with the provided configuration
            merged = config.copy()

            # Ensure renderer configuration exists and is properly formatted
            if "renderer" not in merged or is_empty(merged["renderer"]):
                merged["renderer"] = defaults["renderer"]
            else:
                # Merge renderer settings with defaults
                renderer_defaults = defaults["renderer"]
                for key, default_value in renderer_defaults.items():
                    if key not in merged["renderer"] or is_empty(
                        merged["renderer"][key]
                    ):
                        merged["renderer"][key] = default_value

            # Ensure outputColorSpace is properly formatted
            if merged["renderer"]["outputColorSpace"] == "sRGB":
                merged["renderer"]["outputColorSpace"] = "SRGBColorSpace"

            logger.debug(
                "Merged configuration",
                extra={"action": "merge_with_defaults", "merged_config": merged},
            )
            return merged

        except Exception as e:
            logger.error(
                "Error merging configurations",
                extra={
                    "action": "merge_with_defaults",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            logger.exception("Full traceback")
            raise

    def _load_template(self) -> str:
        """Load the template file, with fallback to original template."""
        try:
            # Try to load enhanced template first
            if self.template_path.exists():
                with open(self.template_path, "r") as f:
                    logger.info("Using enhanced template for better validation")
                    return f.read()
            else:
                logger.warning("Enhanced template not found, using fallback")
                with open(self.fallback_template_path, "r") as f:
                    return f.read()
        except Exception as e:
            logger.error(
                "Error loading template",
                extra={
                    "action": "load_template",
                    "template_name": self.template_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            # Try fallback template
            try:
                with open(self.fallback_template_path, "r") as f:
                    logger.info("Using fallback template due to error")
                    return f.read()
            except Exception as fallback_error:
                logger.error(f"Fallback template also failed: {str(fallback_error)}")
                raise e

    def _add_validation_context(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add validation-specific context to the configuration."""
        try:
            # Add subject-specific validation rules
            subject = config.get("subject", "physics").lower()

            # Add valid units for each subject
            if subject == "physics":
                config["valid_units"] = (
                    "V (volts), A (amperes), Ω (ohms), W (watts), Hz (hertz), m/s, kg, N, J"
                )
            elif subject == "chemistry":
                config["valid_units"] = (
                    "M (molarity), mol/L, g, kg, L, mL, K, °C, atm, Pa"
                )
            else:
                config["valid_units"] = "appropriate SI units"

            # Add Three.js CDN URLs if not present
            if "three_js_url" not in config:
                config["three_js_url"] = "https://esm.sh/three@0.155.0"
            if "orbit_controls_url" not in config:
                config["orbit_controls_url"] = (
                    "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls"
                )

            # Add additional imports comment
            if "additional_imports_comment" not in config:
                config["additional_imports_comment"] = (
                    "// Additional imports can be added here as needed"
                )

            # Ensure TTS settings are present
            if "tts_language" not in config:
                config["tts_language"] = "en-US"
            if "tts_rate" not in config:
                config["tts_rate"] = 1.0
            if "tts_pitch" not in config:
                config["tts_pitch"] = 1.0

            # Ensure narration texts are lists
            if "intro_narration_texts" not in config:
                config["intro_narration_texts"] = []
            if "supporting_narration_texts" not in config:
                config["supporting_narration_texts"] = []

            logger.debug(
                "Added validation context to configuration",
                extra={
                    "action": "add_validation_context",
                    "subject": subject,
                    "has_cdn_urls": "three_js_url" in config,
                },
            )

            return config

        except Exception as e:
            logger.error(
                "Error adding validation context",
                extra={
                    "action": "add_validation_context",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return config

    def _load_schema(self) -> dict:
        """Load the JSON schema file."""
        try:
            with open(self.schema_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(
                "Error loading schema",
                extra={
                    "action": "load_schema",
                    "schema_name": self.schema_path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    def inject_local_models_into_prompt(
        self,
        topic: str,
        subject: str,
        components: List[dict],
        base_prompt: str
    ) -> str:
        """Inject relevant local model references into the generation prompt."""
        
        settings = get_settings()
        if not settings.ENABLE_MODEL_SEARCH:
            return base_prompt
        
        # Ensure components is a list of dicts
        if components and not isinstance(components[0], dict):
            try:
                components = [
                    c.model_dump() if hasattr(c, 'model_dump') else
                    c.dict() if hasattr(c, 'dict') else
                    vars(c) for c in components
                ]
            except Exception as e:
                logger.warning(f"Failed to convert components to dicts: {e}")
                components = [vars(c) for c in components]
        
        try:
            from ..database.database import get_db
            from ..services.local_model_service import LocalModelService
            
            db = next(get_db())
            service = LocalModelService(db)
            
            # Find relevant models using multiple search strategies
            relevant_models = []
            
            # Strategy 1: Search by topic and subject
            topic_models = service.get_models_for_visualization(
                topic=topic,
                subject=subject,
                components=components
            )
            relevant_models.extend(topic_models)
            
            # Strategy 2: Search by individual components
            for component in components:
                component_name = component.get("component_name", "")
                component_desc = component.get("component_description", "")
                if component_name or component_desc:
                    component_models = service.search_models(
                        query=f"{component_name} {component_desc}",
                        subject=subject,
                        limit=3
                    )
                    relevant_models.extend(component_models)
            
            # Strategy 3: Search by subject for general models
            subject_models = service.search_models(
                query=subject,
                subject=subject,
                limit=2
            )
            relevant_models.extend(subject_models)
            
            # Remove duplicates and limit results
            unique_models = list({model.id: model for model in relevant_models}.values())
            unique_models = unique_models[:5]  # Limit to top 5 models
            
            # Debug log: which models are being injected
            if unique_models:
                logger.info(f"Injecting {len(unique_models)} local 3D models into prompt for topic: {topic}, subject: {subject}")
                for model in unique_models:
                    logger.debug(f"Injected model: id={model.id}, name={model.model_name}, subject={model.subject}, tags={model.tags}, url={model.get_api_url()}")
            else:
                logger.debug(f"No relevant models found for topic: {topic}, subject: {subject}")
                return base_prompt
            
            # Create comprehensive model reference section
            model_references = "\n\n## Available 3D Models for Your Visualization:\n"
            model_references += "You have access to these pre-built 3D models that you can use in your visualization:\n\n"
            
            for i, model in enumerate(unique_models, 1):
                model_references += f"### Model {i}: {model.model_name}\n"
                model_references += f"- **Description**: {model.description or 'No description available'}\n"
                model_references += f"- **Category**: {model.category or 'N/A'}\n"
                model_references += f"- **Subject**: {model.subject or 'N/A'}\n"
                if model.tags:
                    model_references += f"- **Tags**: {', '.join(model.tags)}\n"
                model_references += f"- **File Type**: {model.model_type.upper()}\n"
                model_references += f"- **API URL**: `{model.get_api_url()}`\n\n"
            
            # Add usage instructions
            model_references += "### How to Use These Models:\n"
            model_references += "1. **Load the model**: Use the GLTFLoader to load the model from the API URL\n"
            model_references += "2. **Make it the centerpiece**: Position the model prominently in your scene\n"
            model_references += "3. **Scale appropriately**: Adjust the model's scale to fit your visualization\n"
            model_references += "4. **Add interactions**: Create controls to rotate, zoom, or animate the model\n\n"
            
            model_references += "### Example Code:\n"
            model_references += "```javascript\n"
            model_references += "// Load a 3D model\n"
            model_references += "const loader = new THREE.GLTFLoader();\n"
            model_references += f"loader.load('{unique_models[0].get_api_url()}', (gltf) => {{\n"
            model_references += "    const model = gltf.scene;\n"
            model_references += "    // Position the model\n"
            model_references += "    model.position.set(0, 0, 0);\n"
            model_references += "    // Scale if needed\n"
            model_references += "    model.scale.set(1, 1, 1);\n"
            model_references += "    // Add to scene\n"
            model_references += "    scene.add(model);\n"
            model_references += "});\n"
            model_references += "```\n\n"
            
            # Add integration instructions
            model_references += "### Integration Guidelines:\n"
            model_references += "- **PRIORITIZE these models**: Use these pre-built models as the PRIMARY 3D objects in your visualization\n"
            model_references += "- **Minimize custom geometry**: Only create custom Three.js geometry for elements that complement the models\n"
            model_references += "- **Focus on interactions**: Spend more time on animations, controls, and educational features rather than building complex geometry\n"
            model_references += "- **Handle loading**: Always handle loading states and errors when loading models\n"
            model_references += "- **Optimize performance**: Consider model complexity and use LOD (Level of Detail) if needed\n\n"
            
            # Inject into prompt
            enhanced_prompt = base_prompt + model_references
            enhanced_prompt += "\n\n**CRITICAL INSTRUCTION**: When creating your visualization, you MUST use these pre-built models as the main 3D objects. "
            enhanced_prompt += "DO NOT create extensive custom geometry that duplicates what these models provide. "
            enhanced_prompt += "Instead, focus on:\n"
            enhanced_prompt += "1. Loading and displaying these models prominently\n"
            enhanced_prompt += "2. Adding animations and interactions to the models\n"
            enhanced_prompt += "3. Creating UI controls and educational features\n"
            enhanced_prompt += "4. Adding only minimal custom geometry for effects, labels, or complementary elements\n\n"
            enhanced_prompt += "**AVOID**: Creating large custom scenes that compete with or duplicate the provided 3D models.\n"
            
            return enhanced_prompt
            
        except Exception as e:
            logger.warning(f"Failed to inject local models: {e}")
            return base_prompt
