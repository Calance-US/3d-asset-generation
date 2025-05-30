from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..config.settings import settings
from .prompt_selector import PromptSelector
import os

class PromptParser:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.entity_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing educational prompts and extracting relevant 3D model requirements.
            Extract the following information from the user's prompt:
            1. Main subject (anatomy, physics, chemistry)
            2. Required 3D models/components
            3. Required animations or interactions
            4. Educational context (grade level, complexity)
            
            Return the information in a structured format."""),
            ("user", "{prompt}")
        ])
        
        self.prompt_augmentation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating educational 3D scenes.
            Given the following information:
            1. User's original prompt
            2. Available 3D models
            3. Required animations
            
            Generate a detailed scene description that will be used to create an interactive 3D visualization.
            Focus on educational value and accuracy."""),
            ("user", "{context}")
        ])

        # Initialize prompt selector
        self.prompt_selector = PromptSelector()

    async def get_prompt(self, subject: str, topic: str) -> str:
        """
        Get the appropriate prompt template for a given subject and topic.
        
        Args:
            subject: The subject (physics, chemistry, biology)
            topic: The specific topic (e.g., "ohm's law", "atomic structure")
            
        Returns:
            str: The formatted prompt template
        """
        # Use the prompt selector to find the best matching prompt
        selected_subject, selected_file = self.prompt_selector.select_prompt(topic)
        
        # Get the prompt content
        prompt_content = self.prompt_selector.get_prompt_content(selected_subject, selected_file)
        
        # Format the prompt with the topic
        return prompt_content.format(topic=topic)

    async def extract_entities(self, prompt: str) -> Dict[str, Any]:
        """Extract entities from the prompt using LangChain."""
        # For now, return a simple structure
        return {
            "subject": "physics",  # This would be determined by the prompt
            "models": ["circuit"],  # This would be determined by the prompt
            "animations": ["electron_flow"],  # This would be determined by the prompt
            "context": {}  # Additional context would be extracted here
        }

    async def augment_prompt(self, prompt: str, models: List[str], animations: List[str]) -> str:
        """Augment the prompt with model and animation information."""
        # For now, just return the original prompt
        return prompt

    def _extract_subject(self, content: str) -> str:
        """Extract the main subject from the content."""
        subjects = ["anatomy", "physics", "chemistry"]
        for subject in subjects:
            if subject in content.lower():
                return subject
        return "unknown"

    def _extract_models(self, content: str) -> List[str]:
        """Extract required 3D models from the content."""
        # This is a simplified example - you might want to use a more sophisticated extraction method
        models = []
        for category, model_list in settings.MODEL_CATALOG.items():
            for model in model_list:
                if model in content.lower():
                    models.append(model)
        return models

    def _extract_animations(self, content: str) -> List[str]:
        """Extract required animations from the content."""
        # This is a simplified example - you might want to use a more sophisticated extraction method
        animations = []
        animation_keywords = ["rotate", "move", "flow", "pulse", "expand", "contract"]
        for keyword in animation_keywords:
            if keyword in content.lower():
                animations.append(keyword)
        return animations

    def _extract_context(self, content: str) -> Dict[str, Any]:
        """Extract educational context from the content."""
        # This is a simplified example - you might want to use a more sophisticated extraction method
        context = {
            "grade_level": "unknown",
            "complexity": "medium"
        }
        
        # Extract grade level
        for grade in range(1, 13):
            if f"grade {grade}" in content.lower():
                context["grade_level"] = grade
                break
        
        # Extract complexity
        if "simple" in content.lower() or "basic" in content.lower():
            context["complexity"] = "low"
        elif "complex" in content.lower() or "advanced" in content.lower():
            context["complexity"] = "high"
            
        return context 