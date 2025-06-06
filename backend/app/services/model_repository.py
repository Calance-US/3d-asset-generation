import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from ..config.settings import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ModelRepository:
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent.parent / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        # Default models for each subject
        self.default_models = {
            "physics": ["circuit", "battery", "resistor", "capacitor", "inductor"],
            "chemistry": ["atom", "molecule", "reaction", "periodic_table"],
            "biology": ["cell", "dna", "protein", "enzyme"],
            "mathematics": ["graph", "vector", "matrix", "function"]
        }

    def get_models(self, subject: str) -> List[str]:
        """
        Get list of available models for a subject.
        
        Args:
            subject: The subject area (physics, chemistry, biology, mathematics)
            
        Returns:
            List[str]: List of available model names for the subject
        """
        try:
            # First check if there are custom models in the models directory
            subject_dir = self.models_dir / subject
            if subject_dir.exists():
                models = [f.stem for f in subject_dir.glob("*.glb")]
                if models:
                    return models
            
            # Return default models if no custom models found
            return self.default_models.get(subject, self.default_models["physics"])
            
        except Exception as e:
            logger.error(f"Error getting models for subject {subject}: {str(e)}")
            return self.default_models.get(subject, self.default_models["physics"])

    def get_model_path(self, model_name: str, subject: str) -> Optional[str]:
        """
        Get the local path for a 3D model.
        
        Args:
            model_name: Name of the model
            subject: Subject area
            
        Returns:
            Optional[str]: Path to the model file if it exists, None otherwise
        """
        try:
            model_path = self.models_dir / subject / f"{model_name}.glb"
            if model_path.exists():
                return str(model_path)
            return None
        except Exception as e:
            logger.error(f"Error getting model path for {model_name} in {subject}: {str(e)}")
            return None

    def add_model(self, model_name: str, subject: str, model_file: bytes) -> bool:
        """
        Add a new model to the repository.
        
        Args:
            model_name: Name of the model
            subject: Subject area
            model_file: Binary content of the model file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subject_dir = self.models_dir / subject
            subject_dir.mkdir(exist_ok=True)
            
            model_path = subject_dir / f"{model_name}.glb"
            with open(model_path, 'wb') as f:
                f.write(model_file)
            return True
        except Exception as e:
            logger.error(f"Error adding model {model_name} for {subject}: {str(e)}")
            return False

    def remove_model(self, model_name: str, subject: str) -> bool:
        """
        Remove a model from the repository.
        
        Args:
            model_name: Name of the model
            subject: Subject area
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            model_path = self.models_dir / subject / f"{model_name}.glb"
            if model_path.exists():
                model_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing model {model_name} from {subject}: {str(e)}")
            return False 