import os
import re
import logging
from typing import Literal, Optional, Dict, Any, List, Union
import aiohttp
from openai import AsyncOpenAI
import requests
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
import openai
import json
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from sqlalchemy.orm import Session

from app.services.prompt_selector import PromptSelector
from app.services.model_repository import ModelRepository
from app.config.settings import settings
from app.database.database import (
    get_db,
    get_prompts,
    get_all_history,
    get_history_entry_by_id,
    create_history_entry,
    remove_history_entry,
    create_prompt,
    update_prompt,
    delete_prompt,
    duplicate_prompt,
    batch_delete_prompts,
    export_prompts,
    import_prompts,
    migrate_from_json
)
from app.migrations.add_category_and_tags import run_migration
from app.services.prompt_generator import PromptGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
static_dir = Path("static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Mounted static files directory")
else:
    logger.warning("Static files directory not found. Static file serving is disabled.")

# Initialize services
prompt_selector = PromptSelector()
model_repository = ModelRepository()
prompt_generator = PromptGenerator()

# Initialize OpenAI client if API key is available
if settings.OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
else:
    client = None
    logger.warning("OpenAI API key not found. OpenAI provider will not be available.")

# Initialize Google Gemini client if API key is available
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
else:
    gemini_model = None
    logger.warning("Google API key not found. Gemini provider will not be available.")

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

# Shared system prompt for all providers
SYSTEM_PROMPT = """You are a code generation assistant that converts natural language descriptions of educational interactive 3D scenes into standalone embeddable HTML files.

Your goal is to create 3D visualizations that help students quickly and intuitively understand core scientific or engineering concepts.

You must:

* Use only HTML, CSS, and JavaScript (ES6).
* Use browser-compatible Three.js modules via CDN imports using full URLs from [esm.sh](https://esm.sh), which rewrites internal imports for browser compatibility.
* Always import Three.js and its extensions (like OrbitControls) using esm.sh with versioned paths, for example:
  * import * as THREE from 'https://esm.sh/three@0.155.0';
  * import { OrbitControls } from 'https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls';

You must ensure that:
* The scene is educational, scientifically accurate, and clearly demonstrates the user-provided concept.
* Each component must be clearly identifiable and photorealistic.
* Include labels or visual cues (arrows, color changes, flows, toggles) that help explain what's happening.
* Animate key behaviors (e.g., current flow, wave motion, collisions).
* Structure the layout for maximum visual clarity, avoiding clutter.
* The scene must be interactive and fully 3D (rotate, zoom, pan via OrbitControls).
* The output must be a single complete valid HTML file and fully runnable inside an <iframe> and nothing else. Do not include explanations, tags like <think>, or commentary — only the HTML.

Now, given the following user prompt, return only a complete embeddable HTML document that implements it:
"""

def parse_html_content(text: str) -> str:
    """
    Parse and extract HTML content from the generated text.
    
    Args:
        text: The generated text that may contain HTML
        
    Returns:
        str: The extracted HTML content or empty string if not found
    """
    try:
        # Remove any markdown code block markers
        text = text.replace("```html", "").replace("```", "")
        
        # Find the first <!DOCTYPE html> or <html> tag
        html_start = text.find("<!DOCTYPE html>")
        if html_start == -1:
            html_start = text.find("<html>")
        
        if html_start == -1:
            logger.error("No HTML content found in the response")
            return ""
        
        # Find the last </html> tag
        html_end = text.rfind("</html>")
        if html_end == -1:
            logger.error("No closing HTML tag found in the response")
            return ""
        
        # Extract the HTML content
        html_content = text[html_start:html_end + 7]  # +7 for </html>
        
        # Validate that it's proper HTML
        if not html_content.strip().startswith(("<!DOCTYPE html>", "<html")):
            logger.error("Invalid HTML content in the response")
            return ""
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        return ""

@app.post("/generate")
async def generate_visualization(request: GenerateRequest, db: Session = Depends(get_db)):
    """Generate a 3D visualization based on the topic."""
    try:
        logger.info("Starting visualization generation")
        logger.debug(f"Request config: {json.dumps(request.config.model_dump() if request.config else None, indent=2)}")

        # Generate the prompt using either custom config or basic topic info
        if request.config:
            logger.info("Using provided configuration")
            config_dict = request.config.model_dump()
            logger.debug(f"Converted config to dict: {json.dumps(config_dict, indent=2)}")
            prompt_content = prompt_generator.generate_prompt(config_dict)
        else:
            logger.info("Using basic topic info")
            prompt_content = prompt_generator.generate_from_topic(
                request.topic,
                request.subject,
                education_level="High School"
            )

        # Debug log the generated prompt
        logger.info("Generated Prompt Configuration:")
        logger.info(json.dumps(
            request.config.model_dump() if request.config else {
                "topic": request.topic,
                "subject": request.subject,
                "education_level": "High School"
            },
            indent=2
        ))
        logger.info("\nGenerated Prompt Content:")
        logger.info(prompt_content)

        if request.provider == "openai":
            if not client:
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            
            # Generate with OpenAI
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content
            
        elif request.provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt_content}",
                        "stream": settings.STREAM
                    }
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")
                    
                    result = await response.json()
                    generated_text = result.get("response", "")
            
        elif request.provider == "gemini":
            if not gemini_model:
                raise HTTPException(status_code=400, detail="Google API key not configured")
            
            response = await gemini_model.generate_content(
                f"{SYSTEM_PROMPT}\n\n{prompt_content}",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            generated_text = response.text
            
        else:
            raise HTTPException(status_code=400, detail="Invalid provider specified")
        
        # Parse the HTML content
        html_content = parse_html_content(generated_text)
        if not html_content:
            raise HTTPException(status_code=500, detail="Failed to generate valid HTML content")
        
        # Save to history
        history_entry = {
            "id": str(datetime.now().timestamp()),
            "prompt": request.topic,
            "provider": request.provider,
            "subject": request.subject,
            "html": html_content,
            "timestamp": datetime.now()
        }
        create_history_entry(db, history_entry)
        
        return {"html": html_content}
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{subject}")
async def get_available_models(subject: str):
    """Get available models for a subject."""
    try:
        models = model_repository.get_models(subject)
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting models for subject {subject}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    """Get the history of generated visualizations."""
    try:
        history = get_all_history(db)
        return {"entries": [
            {
                "id": entry.id,
                "prompt": entry.prompt,
                "provider": entry.provider,
                "subject": entry.subject,
                "html": entry.html,
                "timestamp": entry.timestamp.isoformat()
            }
            for entry in history
        ]}
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{entry_id}")
async def get_history_entry(entry_id: str, db: Session = Depends(get_db)):
    """Get a specific history entry by ID."""
    try:
        entry = get_history_entry_by_id(db, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found")
        return {
            "id": entry.id,
            "prompt": entry.prompt,
            "provider": entry.provider,
            "subject": entry.subject,
            "html": entry.html,
            "timestamp": entry.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting history entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{entry_id}")
async def delete_history_entry(entry_id: str, db: Session = Depends(get_db)):
    """Delete a history entry."""
    try:
        remove_history_entry(db, entry_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting history entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/prompts/{prompt_id}")
async def update_prompt_endpoint(
    prompt_id: int,
    prompt_data: UpdatePromptRequest,
    db: Session = Depends(get_db)
):
    """
    Update a prompt in the database.
    
    Args:
        prompt_id: ID of the prompt to update
        prompt_data: Updated prompt data
        db: Database session
        
    Returns:
        Updated prompt data
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in prompt_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No valid fields provided for update"
            )
        
        # Update the prompt
        updated_prompt = update_prompt(db, prompt_id, update_data)
        
        if not updated_prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with ID {prompt_id} not found"
            )
        
        # Reinitialize FAISS index with updated prompts
        prompt_selector.initialize_index()
        
        # Return the updated prompt
        return {
            "id": updated_prompt.id,
            "subject": updated_prompt.subject,
            "topic": updated_prompt.topic,
            "content": updated_prompt.content,
            "category": updated_prompt.category,
            "tags": [tag.name for tag in updated_prompt.tags]
        }
        
    except Exception as e:
        logger.error(f"Error updating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompts")
async def get_all_prompts(
    subject: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all prompts from the database with optional filtering."""
    try:
        prompts = get_prompts(db, subject, category, tag, search)
        return {
            "prompts": [
                {
                    "id": prompt.id,
                    "subject": prompt.subject,
                    "topic": prompt.topic,
                    "content": prompt.content,
                    "category": prompt.category,
                    "tags": [tag.name for tag in prompt.tags]
                }
                for prompt in prompts
            ]
        }
    except Exception as e:
        logger.error(f"Error getting prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts")
async def create_prompt_endpoint(
    prompt_data: CreatePromptRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new prompt in the database.
    
    Args:
        prompt_data: New prompt data
        db: Database session
        
    Returns:
        Created prompt data
    """
    try:
        # Create the prompt
        new_prompt = create_prompt(
            db,
            subject=prompt_data.subject,
            topic=prompt_data.topic,
            content=prompt_data.content,
            category=prompt_data.category,
            tags=prompt_data.tags
        )
        
        # Reinitialize FAISS index with updated prompts
        prompt_selector.initialize_index()
        
        # Return the created prompt
        return {
            "id": new_prompt.id,
            "subject": new_prompt.subject,
            "topic": new_prompt.topic,
            "content": new_prompt.content,
            "category": new_prompt.category,
            "tags": [tag.name for tag in new_prompt.tags]
        }
        
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/prompts/{prompt_id}")
async def delete_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a prompt from the database.
    
    Args:
        prompt_id: ID of the prompt to delete
        db: Database session
        
    Returns:
        Success status
    """
    try:
        success = delete_prompt(db, prompt_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with ID {prompt_id} not found"
            )
        
        # Reinitialize FAISS index with updated prompts
        prompt_selector.initialize_index()
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error deleting prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/{prompt_id}/duplicate")
async def duplicate_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Duplicate a prompt."""
    try:
        duplicated = duplicate_prompt(db, prompt_id)
        if not duplicated:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with ID {prompt_id} not found"
            )
        
        return {
            "id": duplicated.id,
            "subject": duplicated.subject,
            "topic": duplicated.topic,
            "content": duplicated.content,
            "category": duplicated.category,
            "tags": [tag.name for tag in duplicated.tags]
        }
    except Exception as e:
        logger.error(f"Error duplicating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/batch-delete")
async def batch_delete_prompts_endpoint(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple prompts."""
    try:
        success = batch_delete_prompts(db, request.prompt_ids)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete prompts"
            )
        
        # Reinitialize FAISS index with updated prompts
        prompt_selector.initialize_index()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompts/export")
async def export_prompts_endpoint(db: Session = Depends(get_db)):
    """Export all prompts."""
    try:
        prompts_data = export_prompts(db)
        return {"prompts": prompts_data}
    except Exception as e:
        logger.error(f"Error exporting prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/import")
async def import_prompts_endpoint(
    request: ImportPromptsRequest,
    db: Session = Depends(get_db)
):
    """Import prompts."""
    try:
        success = import_prompts(db, request.prompts)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to import prompts"
            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error importing prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhance-prompt")
async def enhance_prompt(request: GenerateRequest):
    """Enhance a basic prompt into a detailed configuration using LLM."""
    try:
        logger.info(f"Enhancing prompt for topic: '{request.topic}' in subject: {request.subject} using provider: {request.provider}")
        
        # Create a prompt for the LLM to enhance the concept
        enhancement_prompt = f"""Given the following concept prompt: "{request.topic}" in the subject of {request.subject},
        generate a detailed configuration for a 3D visualization. Return the response as a JSON object with the following structure.
        IMPORTANT: Keep all text fields concise (max 200 characters) to avoid truncation.
        {{
            "topic_name": "A short, concise name for the topic (max 50 chars)",
            "key_concepts": "Main concepts to be visualized (max 200 chars)",
            "education_level": "High School",
            "learning_objectives": "What students will learn (max 200 chars)",
            "interactive_features": "What users can interact with (max 200 chars)",
            "components": [
                {{
                    "component_name": "Name of a 3D component (max 50 chars)",
                    "component_description": "Description of what this component represents (max 100 chars)"
                }}
            ],
            "materials": [
                {{
                    "material_name": "Name of the material [threejs material class - chose between MeshStandardMaterial, MeshPhysicalMaterial, MeshPhongMaterial]",
                    "color": "0xRRGGBB",
                    "metalness": 0.5,
                    "roughness": 0.5
                }}
            ],
            "lights": [
                {{
                    "light_type": "Type of light (max 50 chars)",
                    "light_class": "THREE.LightClass [threejs light class - chose between DirectionalLight, AmbientLight, HemisphereLight]",
                    "light_color": "0xRRGGBB",
                    "intensity": 0.5
                }}
            ],
            "interactive_description": "How users can interact with the visualization (max 200 chars)",
            "animated_elements": "What elements should be animated and how (max 200 chars)",
            "narration_texts": [
                "Text to be narrated during the visualization (max 100 chars each)"
            ]
        }}

        Make the response educational, scientifically accurate, and suitable for {request.subject} education.
        Focus on making the visualization clear and intuitive.
        IMPORTANT: 
        1. Return ONLY the JSON object, no other text or explanation.
        2. Keep all text fields concise to avoid truncation.
        3. Ensure all JSON fields are properly closed.
        4. Do not include any markdown formatting.
        """
        
        logger.debug(f"Enhancement prompt created: {enhancement_prompt}")

        if request.provider == "openai":
            if not client:
                logger.error("OpenAI API key not configured")
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            
            logger.info("Using OpenAI for prompt enhancement")
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content
            logger.debug(f"OpenAI response received: {generated_text[:200]}...")
            
            # Clean the response to ensure it's valid JSON
            try:
                # Remove any markdown code block markers
                cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
                # Try to find the first { and last }
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                
                # Validate JSON structure
                try:
                    enhanced_config = json.loads(cleaned_text)
                    # Validate required fields
                    required_fields = [
                        "topic_name", "key_concepts", "education_level", "learning_objectives",
                        "interactive_features", "components", "materials", "lights",
                        "interactive_description", "animated_elements", "narration_texts"
                    ]
                    missing_fields = [field for field in required_fields if field not in enhanced_config]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                    
                    # Truncate long text fields
                    for field in ["topic_name", "key_concepts", "learning_objectives", "interactive_features", 
                                "interactive_description", "animated_elements"]:
                        if field in enhanced_config and len(enhanced_config[field]) > 200:
                            enhanced_config[field] = enhanced_config[field][:197] + "..."
                    
                    # Truncate component descriptions
                    for component in enhanced_config.get("components", []):
                        if "component_description" in component and len(component["component_description"]) > 100:
                            component["component_description"] = component["component_description"][:97] + "..."
                    
                    # Truncate narration texts
                    enhanced_config["narration_texts"] = [
                        text[:97] + "..." if len(text) > 100 else text
                        for text in enhanced_config.get("narration_texts", [])
                    ]
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON structure: {str(e)}")
                    logger.error(f"Cleaned text: {cleaned_text}")
                    raise
                
                logger.debug(f"Cleaned and validated response: {json.dumps(enhanced_config, indent=2)}")
                
            except Exception as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                logger.error(f"Raw response: {generated_text}")
                raise HTTPException(status_code=500, detail=f"Failed to parse LLM response as JSON: {str(e)}")
            
        elif request.provider == "ollama":
            logger.info("Using Ollama for prompt enhancement")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": enhancement_prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        logger.error(f"Ollama request failed with status {response.status}")
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")
                    
                    result = await response.json()
                    generated_text = result.get("response", "")
                    logger.debug(f"Ollama response received: {generated_text[:200]}...")
                    
                    try:
                        # Clean the response to ensure it's valid JSON
                        cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
                        start_idx = cleaned_text.find("{")
                        end_idx = cleaned_text.rfind("}") + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            cleaned_text = cleaned_text[start_idx:end_idx]
                        
                        logger.debug(f"Cleaned response: {cleaned_text[:200]}...")
                        enhanced_config = json.loads(cleaned_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Ollama response as JSON: {str(e)}")
                        logger.error(f"Raw response: {generated_text}")
                        raise HTTPException(status_code=500, detail=f"Failed to parse Ollama response as JSON: {str(e)}")
            
        elif request.provider == "gemini":
            if not gemini_model:
                logger.error("Google API key not configured")
                raise HTTPException(status_code=400, detail="Google API key not configured")
            
            logger.info("Using Gemini for prompt enhancement")
            response = await gemini_model.generate_content(
                enhancement_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            generated_text = response.text
            logger.debug(f"Gemini response received: {generated_text[:200]}...")
            
            try:
                # Clean the response to ensure it's valid JSON
                cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                
                logger.debug(f"Cleaned response: {cleaned_text[:200]}...")
                enhanced_config = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
                logger.error(f"Raw response: {generated_text}")
                raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response as JSON: {str(e)}")
            
        else:
            logger.error(f"Invalid provider specified: {request.provider}")
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        # Log the enhanced configuration
        logger.info("Successfully generated enhanced configuration")
        logger.debug(f"Enhanced configuration: {json.dumps(enhanced_config, indent=2)}")

        # Validate and return the enhanced configuration
        return EnhancedPromptResponse(**enhanced_config)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
    except Exception as e:
        logger.error(f"Error enhancing prompt: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Run migrations only if RUN_MIGRATIONS setting is enabled."""
    try:
        # Test database connection
        db = next(get_db())
        prompts = get_prompts(db)
        logger.info(f"Database connection successful. Found {len(prompts)} prompts.")
        for prompt in prompts:
            logger.info(f"Prompt: id={prompt.id}, subject={prompt.subject}, topic={prompt.topic}")
        
        if settings.RUN_MIGRATIONS:
            logger.info("Running database migrations...")
            migrate_from_json()
            run_migration()  # Run the new migration
        else:
            logger.info("Skipping database migrations. Set RUN_MIGRATIONS=1 to run migrations.")
            
        # Initialize prompt selector
        global prompt_selector
        prompt_selector = PromptSelector()
        logger.info("Prompt selector initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
