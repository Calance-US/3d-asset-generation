from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

# Request schemas
class ComponentConfig(BaseModel):
    component_name: str
    component_description: str

class MaterialConfig(BaseModel):
    material_name: str
    color: str
    metalness: float
    roughness: float
    emissive: Optional[str] = None
    emissiveIntensity: Optional[float] = None

class LightConfig(BaseModel):
    light_type: str
    light_class: str
    light_color: str
    intensity: float
    additional_props: Optional[str] = None

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
    narration_texts: List[str]

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

# Response schemas
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
    components: List[ComponentConfig]
    materials: List[MaterialConfig]
    lights: List[LightConfig]
    interactive_description: str
    animated_elements: str
    narration_texts: List[str] 