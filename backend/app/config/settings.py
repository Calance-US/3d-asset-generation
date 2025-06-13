from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from functools import lru_cache
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Migration Settings
    RUN_MIGRATIONS: bool = False
    
    # Model Repository Settings
    SKETCHFAB_API_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Model Settings
    OPENAI_MODEL: str = "gpt-4.1-mini"
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

    # Vector store settings
    VECTOR_STORE_PATH: str = str(Path(__file__).parent.parent.parent / "data" / "vector_store")
    VECTOR_STORE_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2 model

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 