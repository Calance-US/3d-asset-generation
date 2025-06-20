from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Environment Settings
    ENVIRONMENT: str = "development"

    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Google AI Settings
    GOOGLE_API_KEY: str = ""

    # Vector Store Settings
    VECTOR_STORE_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2 model
    VECTOR_STORE_COLLECTION_NAME: str = "visualizations"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_RECYCLE: int = 1800

    # Model Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:32b"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Generation Settings
    TEMPERATURE: float = 0.7
    STREAM: bool = False

    # Similar Visualizations Limit
    SIMILAR_VIS_LIMIT: int = 10

    # Validation System Configuration
    ENABLE_COMPREHENSIVE_VALIDATION: bool = True
    ENABLE_RUNTIME_VALIDATION: bool = False  # Expensive, enable for production
    VALIDATION_TIMEOUT_HTML: int = 30
    VALIDATION_TIMEOUT_SCIENTIFIC: int = 45
    VALIDATION_TIMEOUT_REALISM: int = 30
    VALIDATION_TIMEOUT_RUNTIME: int = 60

    # Quality Scoring Configuration
    QUALITY_SCORE_THRESHOLD: float = 7.0
    ENABLE_QUALITY_FILTERING: bool = True
    ENABLE_FEEDBACK_LOOP: bool = True

    # Context Filtering Configuration
    CONTEXT_FILTER_MIN_QUALITY: float = 7.0
    CONTEXT_FILTER_MAX_ITEMS: int = 5
    CONTEXT_FILTER_ENSURE_DIVERSITY: bool = True

    # New settings in app/config/settings.py
    MAX_LLM_RETRY: int = 3  # Maximum retry attempts
    ENABLE_ERROR_FIXING: bool = True  # Enable/disable error fixing
    SAVE_ALL_VALIDATION_ERRORS: bool = True  # Log all errors to database
    ERROR_FIXING_TEMPLATE_PATH: str = "error_fixing_template.prompt.txt"

    # Keycloak Configuration
    KEYCLOAK_SERVER_URL: str = "http://localhost:28080"
    KEYCLOAK_REALM: str = "local-apps"
    KEYCLOAK_CLIENT_ID: str = "3d-visualization-app"
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: str = "admin123"

    # JWT Configuration
    JWT_ALGORITHM: str = "RS256"
    JWT_AUDIENCE: str = "account"

    # Authentication Configuration
    AUTH_ENABLED: bool = True
    AUTH_BYPASS_DEVELOPMENT: bool = True  # Allow bypassing auth in dev mode

    # Gold Standards Analysis Prompt
    GOLD_STANDARD_ANALYSIS_PROMPT: str = """
    Given the following HTML visualization, analyze it and generate a configuration that matches this JSON schema:

    {json_schema}

    IMPORTANT:
    - Extract every distinct, meaningful section of JavaScript or HTML as a separate snippet.
    - For each function, event handler, setup/configuration block, or logical code section, create a separate snippet.
    - Do NOT combine multiple unrelated code blocks into a single snippet.
    - Err on the side of more, smaller snippets rather than fewer, larger ones.
    - The allowed values for snippet_type are: lighting, material, animation, narration, ui_controls, renderer_settings, camera_setup, full_scene, miscellaneous.
    - If a snippet does not fit any of the above categories, use 'miscellaneous' as the snippet_type.
    - Do NOT invent new snippet_type values.
    - Return ONLY a JSON object matching the schema above.
    - All field constraints (lengths, allowed values, etc.) must be respected.
    - Do not include any markdown formatting.
    - You MUST include at least one snippet in the snippets array.

    HTML Content:
    {html_content}
    """

    # Enhancement Prompt for generating new visualizations
    ENHANCEMENT_PROMPT: str = """Given the following concept prompt: "{topic}" in the subject of {subject},
    generate a detailed configuration for a 3D visualization. Return the response as a JSON object with the following structure.
    IMPORTANT: Keep all text fields concise and within the following limits:
    - topic_name: max 20 characters
    - key_concepts: max 200 characters
    - education_level: one of [Elementary, Middle School, High School, College]
    - learning_objectives: max 200 characters
    - interactive_features: max 200 characters
    - scene_description: max 1000 characters
    - component_name: max 50 characters
    - component_description: max 100 characters
    - material_type: one of [MeshStandardMaterial, MeshPhysicalMaterial, MeshPhongMaterial]
    - color, emissive: #RRGGBB
    - metalness, roughness, emissiveIntensity, intensity: float between 0 and 1 (inclusive)
    - light_type: max 50 characters
    - light_class: one of [DirectionalLight, AmbientLight, HemisphereLight]
    - interactive_description: max 200 characters
    - animated_elements: max 200 characters
    - intro_narration_texts: each max 500 characters
    - supporting_narration_texts: each max 100 characters
    - snippets[].summary: max 100 characters
    - snippets[].embedding_text: max 200 characters
    - snippets[].html_snippet: no limit

    JSON structure:
    {{
        "topic_name": "A short, concise name for the topic (max 20 chars)",
        "key_concepts": "Comma separated main concepts to be visualized (max 200 chars)",
        "education_level": "choose between Elementary, Middle School, High School or College",
        "learning_objectives": "What students will learn (max 200 chars)",
        "interactive_features": "What users can interact with in the scene (max 200 chars)",
        "scene_description": "A detailed description of the 3D scene with realistic details (max 1000 chars)",
        "components": [
            {{
                "component_name": "Name of a 3D component required in the 3D scene (max 50 chars)",
                "component_description": "Description of what this component represents in the 3D scene (max 100 chars)"
            }}
        ],
        "materials": [
            {{
                "material_name": "Name of the material (based on the components)",
                "material_type": "Type of material (choose between MeshStandardMaterial, MeshPhysicalMaterial, MeshPhongMaterial)",
                "color": "#RRGGBB",
                "metalness": 0.0-1.0,
                "roughness": 0.0-1.0,
                "emissive": "#RRGGBB",
                "emissiveIntensity": 0.0-1.0
            }}
        ],
        "lights": [
            {{
                "light_type": "Type of light (max 50 chars)",
                "light_class": "THREE.LightClass [choose between DirectionalLight, AmbientLight, HemisphereLight]",
                "light_color": "#RRGGBB",
                "intensity": 0.0-1.0
            }}
        ],
        "interactive_description": "How users can interact with the visualization (max 200 chars)",
        "animated_elements": "What components should be animated and how (max 200 chars)",
        "intro_narration_texts": [
            "Concise introductory narration texts about the topic to be played at the start (each max 500 chars)"
        ],
        "supporting_narration_texts": [
            "Short texts to be played during user interactions explaining controls or feedback (each max 100 chars)"
        ],
        "snippets": [
            {{
                "snippet_type": "lighting | material | animation | narration | ui_controls | renderer_settings | camera_setup | full_scene | miscellaneous",
                "summary": "Short, human-readable description of this snippet's role in the scene (max 100 chars)",
                "embedding_text": "Concise text (~100-200 chars) that describes this snippet for semantic retrieval (max 200 chars)",
                "html_snippet": "Exact HTML or JS snippet as extracted from the document"
            }}
        ]
    }}

    Make the response educational, scientifically accurate, and suitable for {subject} education.
    Focus on making the visualization clear and intuitive.
    IMPORTANT:
    1. Return ONLY the JSON object, no other text or explanation.
    2. Keep all text fields concise and within the specified limits to avoid truncation or validation errors.
    3. Ensure all JSON fields are properly closed.
    4. Do not include any markdown formatting.
    """

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
