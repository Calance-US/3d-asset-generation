import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any, Optional
from app.config.logging_config import logger

class PromptGenerator:
    def __init__(self):
        """Initialize the prompt generator with templates and schemas."""
        self.base_path = Path(__file__).parent.parent / "prompts"
        self.template_path = self.base_path / "template.prompt.txt"
        self.schema_path = self.base_path / "template.json"
        
        # Initialize Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.base_path)))
        
        # Load template and schema
        self.template = self._load_template()
        self.schema = self._load_schema()
        
        logger.info("Initialized PromptGenerator", extra={
            "action": "init",
            "template_directory": str(self.base_path)
        })

    def generate_prompt(self, config: Dict[str, Any]) -> str:
        """
        Generate a prompt using the provided configuration.
        
        Args:
            config: Dictionary containing the configuration for the prompt
            
        Returns:
            str: The generated prompt
        """
        try:
            logger.info("Generating prompt", extra={
                "action": "generate_prompt",
                "has_config": bool(config)
            })
            logger.debug("Input configuration", extra={
                "action": "generate_prompt",
                "config": config
            })
            
            # Merge with defaults
            merged_config = self._merge_defaults(config)
            logger.debug("Merged configuration", extra={
                "action": "generate_prompt",
                "config": merged_config
            })
            
            # Verify renderer configuration
            if "renderer" not in merged_config:
                logger.error("Renderer configuration missing", extra={
                    "action": "generate_prompt",
                    "config_keys": list(merged_config.keys())
                })
                raise ValueError("Renderer configuration is required")
            
            logger.debug("Renderer configuration", extra={
                "action": "generate_prompt",
                "renderer_config": merged_config["renderer"]
            })
            
            # Render template using Jinja2
            template = self.env.from_string(self.template)
            prompt = template.render(**merged_config)
            
            logger.info("Prompt generated", extra={
                "action": "generate_prompt",
                "prompt_length": len(prompt)
            })
            return prompt
            
        except Exception as e:
            logger.error("Error generating prompt", extra={
                "action": "generate_prompt",
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.exception("Full traceback")
            raise

    def generate_from_topic(self, topic: str, subject: str, education_level: str = "High School") -> str:
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
            logger.info("Generating prompt from topic", extra={
                "action": "generate_from_topic",
                "topic": topic,
                "subject": subject,
                "education_level": education_level
            })
            
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
                    "outputColorSpace": "SRGBColorSpace"
                },
                "camera_controls": "OrbitControls",
                "interactive_description": "Use mouse to rotate, zoom, and pan the view",
                "animated_elements": "None",
                "curve_points": [],
                "animation_speed": 1.0,
                "tts_language": "en-US",
                "tts_rate": 1.0,
                "tts_pitch": 1.0,
                "narration_texts": []
            }
            
            return self.generate_prompt(config)
            
        except Exception as e:
            logger.error("Error generating prompt from topic", extra={
                "action": "generate_from_topic",
                "topic": topic,
                "subject": subject,
                "error": str(e),
                "error_type": type(e).__name__
            })
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
            logger.debug("Merging configuration with defaults", extra={
                "action": "merge_with_defaults",
                "input_config": config
            })
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
                    "outputColorSpace": "SRGBColorSpace"
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
                    if key not in merged["renderer"] or is_empty(merged["renderer"][key]):
                        merged["renderer"][key] = default_value
            
            # Ensure outputColorSpace is properly formatted
            if merged["renderer"]["outputColorSpace"] == "sRGB":
                merged["renderer"]["outputColorSpace"] = "SRGBColorSpace"
            
            logger.debug("Merged configuration", extra={
                "action": "merge_with_defaults",
                "merged_config": merged
            })
            return merged
            
        except Exception as e:
            logger.error("Error merging configurations", extra={
                "action": "merge_with_defaults",
                "error": str(e),
                "error_type": type(e).__name__
            })
            logger.exception("Full traceback")
            raise

    def _load_template(self) -> str:
        """Load the template file."""
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error("Error loading template", extra={
                "action": "load_template",
                "template_name": self.template_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    def _load_schema(self) -> dict:
        """Load the JSON schema file."""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error loading schema", extra={
                "action": "load_schema",
                "schema_name": self.schema_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise 