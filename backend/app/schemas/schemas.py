"""Pydantic schemas for the application."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Enums
class SnippetType(str, Enum):
    LIGHTING = "lighting"
    MATERIAL = "material"
    ANIMATION = "animation"
    NARRATION = "narration"
    UI_CONTROLS = "ui_controls"
    RENDERER_SETTINGS = "renderer_settings"
    CAMERA_SETUP = "camera_setup"
    FULL_SCENE = "full_scene"
    MISCELLANEOUS = "miscellaneous"

class EducationLevel(str, Enum):
    ELEMENTARY = "Elementary"
    MIDDLE_SCHOOL = "Middle School"
    HIGH_SCHOOL = "High School"
    COLLEGE = "College"

class MaterialType(str, Enum):
    STANDARD = "MeshStandardMaterial"
    PHYSICAL = "MeshPhysicalMaterial"
    PHONG = "MeshPhongMaterial"

class LightClass(str, Enum):
    DIRECTIONAL = "DirectionalLight"
    AMBIENT = "AmbientLight"
    HEMISPHERE = "HemisphereLight"

# Component Schemas
class ComponentConfig(BaseModel):
    component_name: str = Field(
        ..., description="Name of a 3D component required in the 3D scene (max 50 chars)"
    )
    component_description: str = Field(
        ..., description="Description of what this component represents in the 3D scene (max 100 chars)"
    )

class MaterialConfig(BaseModel):
    material_name: str = Field(
        ..., description="Name of the material (based on the components)"
    )
    material_type: MaterialType = Field(
        ..., description="Type of material (choose between MeshStandardMaterial, MeshPhysicalMaterial, MeshPhongMaterial)"
    )
    color: str = Field(
        ..., pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for the material (#RRGGBB)"
    )
    metalness: float = Field(
        ..., ge=0, le=1,
        description="Metalness value (0.0-1.0)"
    )
    roughness: float = Field(
        ..., ge=0, le=1,
        description="Roughness value (0.0-1.0)"
    )
    emissive: str = Field(
        ..., pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for the emissive property (#RRGGBB)"
    )
    emissiveIntensity: float = Field(
        ..., ge=0, le=1,
        description="Emissive intensity (0.0-1.0)"
    )

class LightConfig(BaseModel):
    light_type: str = Field(
        ..., max_length=50,
        description="Type of light (max 50 chars)"
    )
    light_class: LightClass = Field(
        ..., description="THREE.LightClass (choose between DirectionalLight, AmbientLight, HemisphereLight)"
    )
    light_color: str = Field(
        ..., pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for the light (#RRGGBB)"
    )
    intensity: float = Field(
        ..., ge=0, le=1,
        description="Light intensity (0.0-1.0)"
    )

class RendererConfig(BaseModel):
    antialias: bool
    shadowMapEnabled: bool
    shadowMapType: str
    toneMapping: str
    outputColorSpace: str = "SRGBColorSpace"

class CurvePoint(BaseModel):
    x: float
    y: float
    z: float

# Gold Standards Schemas
class SnippetSchema(BaseModel):
    snippet_type: SnippetType = Field(
        ..., description="Type of snippet: lighting, material, animation, narration, ui_controls, renderer_settings, camera_setup, full_scene, or miscellaneous"
    )
    summary: str = Field(
        ..., description="Short, human-readable description of this snippet's role in the scene (max 100 chars)"
    )
    embedding_text: str = Field(
        ..., description="Concise text (~100-200 chars) that describes this snippet for semantic retrieval (max 200 chars)"
    )
    html_snippet: str = Field(
        ..., description="Exact HTML or JS snippet as extracted from the document"
    )

class EnhancedConfigSchema(BaseModel):
    topic_name: str = Field(
        ..., description="A short, concise name for the topic (max 20 chars)"
    )
    key_concepts: str = Field(
        ..., description="Comma separated main concepts to be visualized (max 200 chars)"
    )
    education_level: EducationLevel = Field(
        ..., description="Choose between Elementary, Middle School, High School or College"
    )
    learning_objectives: str = Field(
        ..., description="What students will learn (max 200 chars)"
    )
    interactive_features: str = Field(
        ..., description="What users can interact with in the scene (max 200 chars)"
    )
    scene_description: str = Field(
        ..., description="A detailed description of the 3D scene with realistic details (max 1000 chars)"
    )
    components: List[ComponentConfig] = Field(
        ..., description="List of 3D components required in the 3D scene"
    )
    materials: List[MaterialConfig] = Field(
        ..., description="List of materials for the 3D components"
    )
    lights: List[LightConfig] = Field(
        ..., description="List of lights for the 3D scene"
    )
    interactive_description: str = Field(
        ..., description="How users can interact with the visualization (max 200 chars)"
    )
    animated_elements: str = Field(
        ..., description="What components should be animated and how (max 200 chars)"
    )
    intro_narration_texts: List[str] = Field(
        ..., description="Concise introductory narration texts about the topic to be played at the start (each max 500 chars)"
    )
    supporting_narration_texts: List[str] = Field(
        ..., description="Short texts to be played during user interactions explaining controls or feedback (each max 100 chars)"
    )
    snippets: List[SnippetSchema] = Field(
        ..., description="Array of code snippets extracted from the HTML/JavaScript, each with type, summary, embedding text, and code"
    )

    class Config:
        use_enum_values = True

# Request Schemas
class PromptConfig(BaseModel):
    topic_name: str
    key_concepts: str
    three_js_url: str
    orbit_controls_url: str
    additional_imports_comment: Optional[str] = None
    education_level: str
    learning_objectives: str
    interactive_features: str
    components: List[ComponentConfig]
    materials: List[MaterialConfig]
    lights: List[LightConfig]
    renderer: RendererConfig
    camera_controls: str
    interactive_description: str
    animated_elements: str
    curve_points: List[CurvePoint]
    animation_speed: float
    tts_language: str
    tts_rate: float
    tts_pitch: float
    intro_narration_texts: List[str]
    supporting_narration_texts: List[str]
    scene_description: str

class GenerateRequest(BaseModel):
    topic: str
    subject: str = "physics"  # Default to physics
    provider: str = "ollama"  # Default to Ollama
    modelType: Optional[str] = "generated"
    selectedModel: Optional[str] = None
    config: Optional[PromptConfig] = None  # Optional custom configuration

class UpdatePromptRequest(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None  # Always handle as a list

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        # Convert tags to comma-separated string for database
        if isinstance(data.get('tags'), list):
            data['tags'] = ', '.join(data['tags'])
        return data

class CreatePromptRequest(BaseModel):
    subject: str
    topic: str
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None  # Always handle as a list

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        # Convert tags to comma-separated string for database
        if isinstance(data.get('tags'), list):
            data['tags'] = ', '.join(data['tags'])
        return data

class BatchDeleteRequest(BaseModel):
    prompt_ids: List[int]

class ImportPromptsRequest(BaseModel):
    prompts: List[Dict]

# Response Schemas
class HistoryEntryResponse(BaseModel):
    id: str
    prompt: str
    provider: str
    subject: str
    html: str
    timestamp: str
    config: Optional[Dict[str, Any]] = None

class HistoryResponse(BaseModel):
    entries: List[HistoryEntryResponse]

class PromptResponse(BaseModel):
    id: int
    subject: str
    topic: str
    content: str
    category: Optional[str]
    tags: List[str]

class PromptsResponse(BaseModel):
    prompts: List[PromptResponse]

class SuccessResponse(BaseModel):
    status: str

class HTMLResponse(BaseModel):
    html: str

class ModelsResponse(BaseModel):
    models: List[str]

class EnhancedPromptResponse(BaseModel):
    topic_name: str
    key_concepts: str
    education_level: str
    learning_objectives: str
    interactive_features: str
    scene_description: str
    components: List[ComponentConfig]
    materials: List[MaterialConfig]
    lights: List[LightConfig]
    interactive_description: str
    animated_elements: str
    intro_narration_texts: List[str]
    supporting_narration_texts: List[str]
    snippets: List[Dict[str, str]] = []  # List of snippets with snippet_type, summary, embedding_text, and html_snippet

class EnhancementRequest(BaseModel):
    topic: str
    subject: str
    provider: str