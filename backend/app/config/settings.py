from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str | None = None
    
    # Model Repository Settings
    SKETCHFAB_API_KEY: str = os.getenv("SKETCHFAB_API_KEY", "")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
    
    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Model Settings
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:32b"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Generation Settings
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 10000
    STREAM: bool = False
    
    # Model Catalog
    MODEL_CATALOG: Dict[str, List[str]] = {
        "anatomy": [
            "heart", "brain", "lungs", "kidney", "liver",
            "arteries", "veins", "muscles", "bones"
        ],
        "physics": [
            "electric_circuit", "wave_motion", "gravity",
            "magnetic_field", "optics", "mechanics"
        ],
        "chemistry": [
            "molecule", "atom", "reaction", "crystal",
            "polymer", "enzyme"
        ]
    }
    
    # Fallback Models
    FALLBACK_MODELS: Dict[str, str] = {
        "anatomy": "models/placeholder_anatomy.glb",
        "physics": "models/placeholder_physics.glb",
        "chemistry": "models/placeholder_chemistry.glb"
    }
    
    # HTML Templates
    THREE_JS_TEMPLATE: str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>3D Scene</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body { margin: 0; }
            canvas { display: block; }
        </style>
    </head>
    <body>
        <script>
            {scene_code}
        </script>
    </body>
    </html>
    """

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 