import os
import re
import logging
from typing import Literal, Optional, Dict, Any, List, Union, Tuple
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
import logging.config
from bs4 import BeautifulSoup
import time
from sqlalchemy import func
import numpy as np

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
from app.config.logging_config import logger
from app.schemas.schemas import (
    ComponentConfig,
    MaterialConfig,
    LightConfig,
    RendererConfig,
    CurvePoint,
    PromptConfig,
    GenerateRequest,
    UpdatePromptRequest,
    CreatePromptRequest,
    BatchDeleteRequest,
    ImportPromptsRequest,
    HistoryEntryResponse,
    HistoryResponse,
    PromptResponse,
    PromptsResponse,
    SuccessResponse,
    HTMLResponse,
    ModelsResponse,
    EnhancedPromptResponse
)
from app.models import HistoryEntry

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
    logger.info("Mounted static files directory", extra={
        "directory": str(static_dir),
        "action": "mount_static_files"
    })
else:
    logger.warning("Static files directory not found", extra={
        "directory": str(static_dir),
        "action": "mount_static_files"
    })

# Initialize services
prompt_selector = PromptSelector()
model_repository = ModelRepository()
prompt_generator = PromptGenerator()

# Initialize OpenAI client if API key is available
if settings.OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
else:
    client = None
    logger.warning("OpenAI API key not found", extra={
        "provider": "openai",
        "action": "init_provider"
    })

# Initialize Google Gemini client if API key is available
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
else:
    gemini_model = None
    logger.warning("Google API key not found", extra={
        "provider": "gemini",
        "action": "init_provider"
    })

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
            logger.error("No HTML content found in the response", extra={
                "action": "validate_html",
                "response_length": len(text)
            })
            return ""

        # Find the last </html> tag
        html_end = text.rfind("</html>")
        if html_end == -1:
            logger.error("No closing HTML tag found in the response", extra={
                "action": "validate_html",
                "content_length": len(text)
            })
            return ""

        # Extract the HTML content
        html_content = text[html_start:html_end + 7]  # +7 for </html>

        # Validate that it's proper HTML
        if not html_content.strip().startswith(("<!DOCTYPE html>", "<html")):
            logger.error("Invalid HTML content in the response", extra={
                "action": "validate_html",
                "error": "No valid HTML tag found"
            })
            return ""

        try:
            BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error("Invalid HTML content", extra={
                "action": "validate_html",
                "error": str(e)
            })
            return ""

        return html_content

    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        return ""

@app.post("/generate", response_model=HTMLResponse)
async def generate_visualization(request: GenerateRequest, db: Session = Depends(get_db)) -> HTMLResponse:
    """Generate a 3D visualization based on the topic."""
    try:
        start_time = time.time()
        
        logger.info("Starting visualization generation", extra={
            "action": "generate_visualization",
            "has_config": bool(request.config)
        })
        logger.debug(f"Request config: {json.dumps(request.config.model_dump() if request.config else None, indent=2)}")

        # Generate the prompt using either custom config or basic topic info
        if request.config:
            logger.info("Using provided configuration", extra={
                "action": "generate_visualization",
                "config_type": "provided"
            })
            config_dict = request.config.model_dump()
            logger.debug("Configuration details", extra={
                "action": "generate_visualization",
                "config": config_dict
            })
            prompt_content = prompt_generator.generate_prompt(config_dict)
        else:
            logger.info("Using basic topic info", extra={
                "action": "generate_visualization",
                "config_type": "basic",
                "topic": request.topic,
                "subject": request.subject
            })
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

        generated_text: Optional[str] = None

        if request.provider == "openai":
            if not client:
                logger.error("OpenAI API key not configured", extra={
                    "action": "generate_visualization",
                    "provider": "openai"
                })
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
                        "prompt": f"{prompt_content}",
                        "stream": settings.STREAM
                    }
                ) as response:
                    if response.status != 200:
                        logger.error(f"Ollama request failed with status {response.status}", extra={
                            "action": "generate_visualization",
                            "provider": "ollama"
                        })
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")

                    result = await response.json()
                    generated_text = str(result.get("response", ""))

        elif request.provider == "gemini":
            if not gemini_model:
                logger.error("Google API key not configured", extra={
                    "action": "generate_visualization",
                    "provider": "gemini"
                })
                raise HTTPException(status_code=400, detail="Google API key not configured")

            response = gemini_model.generate_content(
                f"{prompt_content}",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            generated_text = response.text

        else:
            logger.error(f"Invalid provider specified: {request.provider}", extra={
                "action": "generate_visualization",
                "provider": request.provider
            })
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        # Parse the HTML content
        if generated_text is None:
            raise HTTPException(status_code=400, detail="No HTML content found in the response")

        html_content = parse_html_content(generated_text)
        if not html_content:
            logger.error("No HTML content found", extra={
                "action": "validate_html",
                "response_length": len(generated_text) if generated_text else 0
            })
            raise HTTPException(status_code=400, detail="No HTML content found in the response")

        if not html_content.endswith("</html>"):
            logger.error("No closing HTML tag found", extra={
                "action": "validate_html",
                "content_length": len(html_content)
            })
            raise HTTPException(status_code=400, detail="No closing HTML tag found in the response")

        try:
            BeautifulSoup(html_content, "html.parser")
        except Exception as e:
            logger.error("Invalid HTML content", extra={
                "action": "validate_html",
                "error": str(e)
            })
            raise HTTPException(status_code=400, detail="Invalid HTML content in the response")

        # Save to history
        # First create a prompt entry with all educational content
        prompt_entry = {
            "topic": request.topic,
            "subject": request.subject,
            "content": prompt_content,  # Save the actual generated prompt content
            "category": None,  # Optional field
            "key_concepts": request.config.key_concepts if request.config else None,
            "education_level": request.config.education_level if request.config else "High School",
            "learning_objectives": request.config.learning_objectives if request.config else None,
            "interactive_features": request.config.interactive_features if request.config else None,
            "embedding": None,  # Will be populated later if needed
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Log the values being passed to create_prompt
        logger.info("Creating prompt with values:", extra={
            "action": "create_prompt",
            "values": {
                "subject": prompt_entry["subject"],
                "topic": prompt_entry["topic"],
                "content": prompt_entry["content"],
                "category": prompt_entry["category"],
                "key_concepts": prompt_entry["key_concepts"],
                "education_level": prompt_entry["education_level"],
                "learning_objectives": prompt_entry["learning_objectives"],
                "interactive_features": prompt_entry["interactive_features"]
            }
        })
        
        # Create prompt with all fields
        prompt = create_prompt(
            db,
            subject=prompt_entry["subject"],
            topic=prompt_entry["topic"],
            content=prompt_entry["content"],
            category=prompt_entry["category"],
            key_concepts=prompt_entry["key_concepts"],
            education_level=prompt_entry["education_level"],
            learning_objectives=prompt_entry["learning_objectives"],
            interactive_features=prompt_entry["interactive_features"]
        )

        # Calculate generation time
        generation_time = time.time() - start_time

        # Then create the history entry with the prompt_id and visualization details
        history_entry = {
            "id": str(datetime.now().timestamp()),
            "prompt_id": prompt.id,
            "user_query": request.topic,
            "response": html_content,
            "provider": request.provider,
            "components": json.dumps([comp.model_dump() for comp in request.config.components]) if request.config else None,
            "materials": json.dumps([mat.model_dump() for mat in request.config.materials]) if request.config else None,
            "lights": json.dumps([light.model_dump() for light in request.config.lights]) if request.config else None,
            "render_settings": json.dumps(request.config.renderer.model_dump()) if request.config else None,
            "animation_speed": request.config.animation_speed if request.config else 1.0,
            "intro_narration_texts": json.dumps(request.config.intro_narration_texts) if request.config else None,
            "supporting_narration_texts": json.dumps(request.config.supporting_narration_texts) if request.config else None,
            "scene_description": request.config.scene_description if request.config else None,
            "generation_time": generation_time,
            "created_at": datetime.now()
        }
        create_history_entry(db, history_entry)

        return HTMLResponse(html=html_content)

    except Exception as e:
        logger.error("Error generating visualization", extra={
            "action": "generate_visualization",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{subject}", response_model=ModelsResponse)
async def get_available_models(subject: str) -> ModelsResponse:
    """Get available models for a subject."""
    try:
        models = model_repository.get_models(subject)
        return ModelsResponse(models=models)
    except Exception as e:
        logger.error("Error getting models", extra={
            "action": "get_models",
            "subject": subject,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=HistoryResponse)
async def get_history(db: Session = Depends(get_db)) -> HistoryResponse:
    """Get the history of generated visualizations."""
    try:
        history = get_all_history(db)
        return HistoryResponse(entries=[
            HistoryEntryResponse(
                id=entry.id,
                prompt=entry.user_query or "",
                provider=entry.provider or "Unknown",
                subject=entry.prompt.subject if entry.prompt else "Unknown",
                html=entry.response or "",
                timestamp=entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat(),
                # Add configuration fields
                config={
                    "topic_name": entry.prompt.topic if entry.prompt else "",
                    "key_concepts": entry.prompt.key_concepts if entry.prompt else "",
                    "education_level": entry.prompt.education_level if entry.prompt else "High School",
                    "learning_objectives": entry.prompt.learning_objectives if entry.prompt else "",
                    "interactive_features": entry.prompt.interactive_features if entry.prompt else "",
                    "components": json.loads(entry.components) if entry.components and entry.components.strip() else [],
                    "materials": json.loads(entry.materials) if entry.materials and entry.materials.strip() else [],
                    "lights": json.loads(entry.lights) if entry.lights and entry.lights.strip() else [],
                    "render_settings": json.loads(entry.render_settings) if entry.render_settings and entry.render_settings.strip() else {},
                    "animation_speed": entry.animation_speed or 1.0,
                    "intro_narration_texts": json.loads(entry.intro_narration_texts) if entry.intro_narration_texts and entry.intro_narration_texts.strip() else [],
                    "supporting_narration_texts": json.loads(entry.supporting_narration_texts) if entry.supporting_narration_texts and entry.supporting_narration_texts.strip() else [],
                    "interactive_description": entry.prompt.interactive_features if entry.prompt else "",
                    "scene_description": entry.scene_description if entry.scene_description else ""
                }
            )
            for entry in history
        ])
    except Exception as e:
        logger.error("Error getting history", extra={
            "action": "get_history",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{entry_id}", response_model=HistoryEntryResponse)
async def get_history_entry(entry_id: str, db: Session = Depends(get_db)) -> HistoryEntryResponse:
    """Get a specific history entry by ID."""
    try:
        entry = get_history_entry_by_id(db, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found")
        return HistoryEntryResponse(
            id=entry.id,
            prompt=entry.user_query or "",
            provider=entry.provider or "Unknown",
            subject=entry.prompt.subject if entry.prompt else "Unknown",
            html=entry.response or "",
            timestamp=entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat(),
            # Add configuration fields
            config={
                "topic_name": entry.prompt.topic if entry.prompt else "",
                "key_concepts": entry.prompt.key_concepts if entry.prompt else "",
                "education_level": entry.prompt.education_level if entry.prompt else "High School",
                "learning_objectives": entry.prompt.learning_objectives if entry.prompt else "",
                "interactive_features": entry.prompt.interactive_features if entry.prompt else "",
                "components": json.loads(entry.components) if entry.components else [],
                "materials": json.loads(entry.materials) if entry.materials else [],
                "lights": json.loads(entry.lights) if entry.lights else [],
                "render_settings": json.loads(entry.render_settings) if entry.render_settings else {},
                "animation_speed": entry.animation_speed or 1.0,
                "intro_narration_texts": json.loads(entry.intro_narration_texts) if entry.intro_narration_texts else [],
                "supporting_narration_texts": json.loads(entry.supporting_narration_texts) if entry.supporting_narration_texts else [],
                "interactive_description": entry.prompt.interactive_features if entry.prompt else "",
                "animated_elements": entry.prompt.interactive_features if entry.prompt else "",
                "three_js_url": "https://esm.sh/three@0.155.0",
                "orbit_controls_url": "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
                "camera_controls": "OrbitControls",
                "curve_points": [{"x": 0, "y": 0, "z": 0}],
                "tts_language": "en-US",
                "tts_rate": 1.0,
                "tts_pitch": 1.0,
                "scene_description": entry.scene_description if entry.scene_description else ""
            }
        )
    except Exception as e:
        logger.error("Error getting history entry", extra={
            "action": "get_history_entry",
            "entry_id": entry_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{entry_id}", response_model=SuccessResponse)
async def delete_history_entry(entry_id: str, db: Session = Depends(get_db)) -> SuccessResponse:
    """Delete a history entry."""
    try:
        remove_history_entry(db, entry_id)
        return SuccessResponse(status="success")
    except Exception as e:
        logger.error("Error deleting history entry", extra={
            "action": "delete_history_entry",
            "entry_id": entry_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt_endpoint(
    prompt_id: int,
    prompt_data: UpdatePromptRequest,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Update a prompt in the database."""
    try:
        update_data = {k: v for k, v in prompt_data.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")

        updated_prompt = update_prompt(db, prompt_id, update_data)
        if not updated_prompt:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")

        prompt_selector.initialize_index()

        return PromptResponse(
            id=updated_prompt.id,
            subject=updated_prompt.subject,
            topic=updated_prompt.topic,
            content=updated_prompt.content,
            category=updated_prompt.category,
            tags=[tag.name for tag in updated_prompt.tags]
        )

    except Exception as e:
        logger.error("Error updating prompt", extra={
            "action": "update_prompt",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompts", response_model=PromptsResponse)
async def get_all_prompts(
    subject: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> PromptsResponse:
    """Get all prompts from the database with optional filtering."""
    try:
        prompts = get_prompts(db, subject, category, tag, search)
        return PromptsResponse(prompts=[
            PromptResponse(
                id=prompt.id,
                subject=prompt.subject,
                topic=prompt.topic,
                content=prompt.content,
                category=prompt.category,
                tags=[tag.name for tag in prompt.tags]
            )
            for prompt in prompts
        ])
    except Exception as e:
        logger.error("Error getting prompts", extra={
            "action": "get_all_prompts",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts", response_model=PromptResponse)
async def create_prompt_endpoint(
    prompt_data: CreatePromptRequest,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Create a new prompt in the database."""
    try:
        new_prompt = create_prompt(
            db,
            subject=prompt_data.subject,
            topic=prompt_data.topic,
            content=prompt_data.content,
            category=prompt_data.category,
            tags=",".join(prompt_data.tags) if prompt_data.tags else ""
        )

        prompt_selector.initialize_index()

        return PromptResponse(
            id=new_prompt.id,
            subject=new_prompt.subject,
            topic=new_prompt.topic,
            content=new_prompt.content,
            category=new_prompt.category,
            tags=[tag.name for tag in new_prompt.tags]
        )

    except Exception as e:
        logger.error("Error creating prompt", extra={
            "action": "create_prompt",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/prompts/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete a prompt from the database."""
    try:
        success = delete_prompt(db, prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")

        prompt_selector.initialize_index()
        return SuccessResponse(status="success")

    except Exception as e:
        logger.error("Error deleting prompt", extra={
            "action": "delete_prompt",
            "prompt_id": prompt_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/{prompt_id}/duplicate", response_model=PromptResponse)
async def duplicate_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Duplicate a prompt."""
    try:
        duplicated = duplicate_prompt(db, prompt_id)
        if not duplicated:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")

        return PromptResponse(
            id=duplicated.id,
            subject=duplicated.subject,
            topic=duplicated.topic,
            content=duplicated.content,
            category=duplicated.category,
            tags=[tag.name for tag in duplicated.tags]
        )
    except Exception as e:
        logger.error("Error duplicating prompt", extra={
            "action": "duplicate_prompt",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/batch-delete", response_model=SuccessResponse)
async def batch_delete_prompts_endpoint(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete multiple prompts."""
    try:
        success = batch_delete_prompts(db, request.prompt_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete prompts")

        prompt_selector.initialize_index()
        return SuccessResponse(status="success")
    except Exception as e:
        logger.error("Error deleting prompts", extra={
            "action": "batch_delete_prompts",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/prompts/export", response_model=PromptsResponse)
async def export_prompts_endpoint(db: Session = Depends(get_db)) -> PromptsResponse:
    """Export all prompts."""
    try:
        prompts_data = export_prompts(db)
        return PromptsResponse(prompts=[
            PromptResponse(
                id=prompt["id"],
                subject=prompt["subject"],
                topic=prompt["topic"],
                content=prompt["content"],
                category=prompt["category"],
                tags=prompt["tags"]
            )
            for prompt in prompts_data
        ])
    except Exception as e:
        logger.error("Error exporting prompts", extra={
            "action": "export_prompts",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/prompts/import", response_model=SuccessResponse)
async def import_prompts_endpoint(
    request: ImportPromptsRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Import prompts."""
    try:
        success = import_prompts(db, request.prompts)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import prompts")
        return SuccessResponse(status="success")
    except Exception as e:
        logger.error("Error importing prompts", extra={
            "action": "import_prompts",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/enhance-prompt", response_model=EnhancedPromptResponse)
async def enhance_prompt(request: GenerateRequest, db: Session = Depends(get_db)) -> EnhancedPromptResponse:
    """Enhance a basic prompt into a detailed configuration using LLM."""
    try:
        logger.info("Enhancing prompt", extra={
            "action": "enhance_prompt",
            "topic": request.topic,
            "subject": request.subject,
            "provider": request.provider
        })

        # Create a prompt for the LLM to enhance the concept
        enhancement_prompt = f"""Given the following concept prompt: "{request.topic}" in the subject of {request.subject},
        generate a detailed configuration for a 3D visualization. Return the response as a JSON object with the following structure.
        IMPORTANT: Keep all text fields concise (max 200 characters) to avoid truncation.
        {{
            "topic_name": "A short, concise name for the topic (max 20 chars)",
            "key_concepts": "Comma separated main concepts to be visualized (max 200 chars)",
            "education_level": "choose between Elementary, Middle School, High School or College",
            "learning_objectives": "What students will learn (max 200 chars)",
            "interactive_features": "What users can interact with in the scene (max 200 chars)",
            "scene_description": "A detailed description of the 3D scene with realistic details(max 1000 chars)",
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
                    "metalness": 0.5,
                    "roughness": 0.5,
                    "emissive": "#RRGGBB",
                    "emissiveIntensity": 0.5
                }}
            ],
            "lights": [
                {{
                    "light_type": "Type of light (max 50 chars)",
                    "light_class": "THREE.LightClass [choose between DirectionalLight, AmbientLight, HemisphereLight]",
                    "light_color": "#RRGGBB",
                    "intensity": 0.5
                }}
            ],
            "interactive_description": "How users can interact with the visualization (max 200 chars)",
            "animated_elements": "What components should be animated and how (max 200 chars)",
            "intro_narration_texts": [
                "Concise introductory narration texts about the topic to be played at the start (each max 500 chars)"
            ],
            "supporting_narration_texts": [
                "Short texts to be played during user interactions explaining controls or feedback (each max 100 chars)"
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
                logger.error("OpenAI API key not configured", extra={
                    "action": "enhance_prompt",
                    "provider": "openai"
                })
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")

            logger.info("Using OpenAI for prompt enhancement", extra={
                "action": "enhance_prompt",
                "provider": "openai"
            })
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": enhancement_prompt}
                ],
                temperature=0.7
            )

            generated_text = response.choices[0].message.content
            logger.debug("OpenAI response received", extra={
                "action": "enhance_prompt",
                "provider": "openai",
                "response_length": len(generated_text) if generated_text else 0
            })

            if not generated_text:
                logger.error("No response from OpenAI", extra={
                    "action": "enhance_prompt",
                    "provider": "openai"
                })
                raise HTTPException(status_code=500, detail="No response from OpenAI")

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
                        "interactive_description", "animated_elements", "intro_narration_texts", "supporting_narration_texts", "scene_description"
                    ]
                    missing_fields = [field for field in required_fields if field not in enhanced_config]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                    # Truncate long text fields
                    for field in ["topic_name", "key_concepts", "learning_objectives", "interactive_features",
                                "interactive_description", "animated_elements"]:
                        if field in enhanced_config:
                            enhanced_config[field] = enhanced_config[field]

                    # Truncate component descriptions
                    for component in enhanced_config.get("components", []):
                        if "component_description" in component:
                            # Removed truncation logic
                            pass

                    # Truncate narration texts
                    enhanced_config["intro_narration_texts"] = [text for text in enhanced_config.get("intro_narration_texts", [])]
                    enhanced_config["supporting_narration_texts"] = [text for text in enhanced_config.get("supporting_narration_texts", [])]

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
            logger.info("Using Ollama for prompt enhancement", extra={
                "action": "enhance_prompt",
                "provider": "ollama"
            })
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
                        logger.error(f"Ollama request failed with status {response.status}", extra={
                            "action": "enhance_prompt",
                            "provider": "ollama"
                        })
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")

                    result = await response.json()
                    generated_text = result.get("response", "")
                    logger.debug("Ollama response received", extra={
                        "action": "enhance_prompt",
                        "provider": "ollama",
                        "response_length": len(generated_text)
                    })

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
                logger.error("Google API key not configured", extra={
                    "action": "enhance_prompt",
                    "provider": "gemini"
                })
                raise HTTPException(status_code=400, detail="Google API key not configured")

            logger.info("Using Gemini for prompt enhancement", extra={
                "action": "enhance_prompt",
                "provider": "gemini"
            })
            response = gemini_model.generate_content(
                enhancement_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            generated_text = response.text
            logger.debug("Gemini response received", extra={
                "action": "enhance_prompt",
                "provider": "gemini",
                "response_length": len(generated_text)
            })

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
            logger.error(f"Invalid provider specified: {request.provider}", extra={
                "action": "enhance_prompt",
                "provider": request.provider
            })
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        # Log the enhanced configuration
        logger.info("Successfully generated enhanced configuration", extra={
            "action": "enhance_prompt",
            "provider": request.provider
        })
        logger.debug(f"Enhanced configuration: {json.dumps(enhanced_config, indent=2)}")

        # Validate and return the enhanced configuration
        return EnhancedPromptResponse(**enhanced_config)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
    except Exception as e:
        logger.error("Error enhancing prompt", extra={
            "action": "enhance_prompt",
            "error": str(e),
            "error_type": type(e).__name__
        })
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/generation-stats", response_model=dict)
async def get_generation_stats(db: Session = Depends(get_db)) -> dict:
    """Get statistics about visualization generation times."""
    try:
        # Get all generation times
        generation_times = db.query(HistoryEntry.generation_time).filter(
            HistoryEntry.generation_time.isnot(None)
        ).all()
        
        if not generation_times:
            return {
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "total_generations": 0
            }
        
        # Convert to numpy array for calculations
        times = np.array([t[0] for t in generation_times])
        
        return {
            "mean": float(np.mean(times)),
            "median": float(np.median(times)),
            "p95": float(np.percentile(times, 95)),
            "p99": float(np.percentile(times, 99)),
            "total_generations": len(times)
        }
    except Exception as e:
        logger.error("Error getting generation stats", extra={
            "action": "get_generation_stats",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Run migrations only if RUN_MIGRATIONS setting is enabled."""
    try:
        # Test database connection
        db = next(get_db())
        prompts = get_prompts(db)
        logger.info("Database connection successful", extra={
            "action": "init_database",
            "prompt_count": len(prompts)
        })
        for prompt in prompts:
            logger.info("Found prompt", extra={
                "action": "init_database",
                "prompt_id": prompt.id,
                "subject": prompt.subject,
                "topic": prompt.topic
            })

        if settings.RUN_MIGRATIONS:
            logger.info("Running database migrations...", extra={
                "action": "run_migrations"
            })
            migrate_from_json()
            run_migration()  # Run the new migration
        else:
            logger.info("Skipping database migrations. Set RUN_MIGRATIONS=1 to run migrations.", extra={
                "action": "skip_migrations"
            })

        # Initialize prompt selector
        global prompt_selector
        prompt_selector = PromptSelector()
        logger.info("Prompt selector initialized", extra={
            "action": "init_prompt_selector"
        })

    except Exception as e:
        logger.error("Error during startup", extra={
            "action": "startup",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
