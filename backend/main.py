import os
import re
import logging
from typing import Literal, Optional, Dict, Any, List, Union, Tuple
import aiohttp
from openai import AsyncOpenAI
import requests
from fastapi import FastAPI, HTTPException, Depends, Request, Query
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
# from app.migrations.add_category_and_tags import run_migration
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
    EnhancedPromptResponse,
    EnhancementRequest
)
from app.models import HistoryEntry, Visualization, Tag
from app.api.api import api_router  # Import the API router
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.schemas.visualization import VisualizationResponse
from app.utils.embedding_utils import create_embedding_text, build_embedding_text_from_config

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

# Include the API router
app.include_router(api_router, prefix="/api/v1")

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

# Add visualization endpoints
class VisualizationCreate(BaseModel):
    topic: str
    subject: str
    html_content: str
    config: Dict[str, Any]

class VisualizationResponse(BaseModel):
    id: int
    topic: str
    subject: str
    html_content: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RetrieveSimilarResponse(BaseModel):
    results: List[Dict[str, Any]]

@app.post("/api/visualizations/save", response_model=VisualizationResponse)
async def save_visualization(
    visualization: VisualizationCreate,
    db: Session = Depends(get_db)
) -> VisualizationResponse:
    """Save a visualization to the library."""
    try:
        # Generate embedding for the visualization
        embedding = prompt_selector.generate_embedding(visualization.topic)

        # Create new visualization
        db_visualization = Visualization(
            topic=visualization.topic,
            subject=visualization.subject,
            html_content=visualization.html_content,
            config=visualization.config,
            embedding=embedding,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(db_visualization)
        db.commit()
        db.refresh(db_visualization)

        return VisualizationResponse(
            id=db_visualization.id,
            topic=db_visualization.topic,
            subject=db_visualization.subject,
            html_content=db_visualization.html_content,
            config=db_visualization.config,
            created_at=db_visualization.created_at,
            updated_at=db_visualization.updated_at
        )

    except Exception as e:
        logger.error("Error saving visualization", extra={
            "action": "save_visualization",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualizations", response_model=List[VisualizationResponse])
async def get_visualizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[VisualizationResponse]:
    """Get all visualizations."""
    try:
        visualizations = db.query(Visualization).offset(skip).limit(limit).all()
        return [
            VisualizationResponse(
                id=v.id,
                topic=v.topic,
                subject=v.subject,
                html_content=v.html_content,
                config=v.config,
                created_at=v.created_at,
                updated_at=v.updated_at
            )
            for v in visualizations
        ]
    except Exception as e:
        logger.error("Error getting visualizations", extra={
            "action": "get_visualizations",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualizations/{visualization_id}", response_model=VisualizationResponse)
async def get_visualization(
    visualization_id: int,
    db: Session = Depends(get_db)
) -> VisualizationResponse:
    """Get a specific visualization by ID."""
    try:
        visualization = db.query(Visualization).filter(Visualization.id == visualization_id).first()
        if not visualization:
            raise HTTPException(status_code=404, detail="Visualization not found")

        return VisualizationResponse(
            id=visualization.id,
            topic=visualization.topic,
            subject=visualization.subject,
            html_content=visualization.html_content,
            config=visualization.config,
            created_at=visualization.created_at,
            updated_at=visualization.updated_at
        )
    except Exception as e:
        logger.error("Error getting visualization", extra={
            "action": "get_visualization",
            "visualization_id": visualization_id,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

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

        # --- Retrieve similar visualizations for context injection ---
        vector_store = get_vector_store()
        # Prepare fields for embedding context
        if request.config:
            embedding_input = build_embedding_text_from_config(request.config.model_dump())
        else:
            embedding_input = request.topic
        embedding = EmbeddingService.generate_embedding(embedding_input)
        similar = await vector_store.get_similar_visualizations(embedding, limit=settings.SIMILAR_VIS_LIMIT)
        # Build context string from similar visualizations
        context_blocks = []
        for item in similar:
            meta = item['metadata']
            # Try to fetch full visualization from DB if id is present
            viz_id = meta.get('id')
            viz = None
            if viz_id:
                viz = db.query(Visualization).filter_by(id=viz_id).first()
            if viz:
                context_blocks.append(f"Example Visualization:\nTopic: {viz.topic}\nConfig: {json.dumps(viz.config, indent=2)}\nSummary: {viz.config.get('scene_description', '')}")
            else:
                # Fallback: use metadata
                context_blocks.append(f"Example Visualization:\nConfig: {json.dumps(meta, indent=2)}")
        context_text = "\n\n".join(context_blocks) if context_blocks else ""

        # --- Logging retrieval quality ---
        logger.info("Retrieval event", extra={
            "user_query": request.topic,
            "embedding_input": embedding_input,
            "retrieved": [
                {
                    "id": item['metadata'].get('id'),
                    "similarity": item.get('similarity'),
                    "summary": item['metadata'].get('scene_description', '')
                }
                for item in similar
            ]
        })

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

        # Inject retrieved context into the prompt
        if context_text:
            prompt_content = f"{context_text}\n\n---\n\n{prompt_content}"

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
                    "components": entry.components if isinstance(entry.components, list) else [],
                    "materials": entry.materials if isinstance(entry.materials, list) else [],
                    "lights": entry.lights if isinstance(entry.lights, list) else [],
                    "render_settings": entry.render_settings if isinstance(entry.render_settings, dict) else {},
                    "animation_speed": entry.animation_speed or 1.0,
                    "intro_narration_texts": entry.intro_narration_texts if isinstance(entry.intro_narration_texts, list) else [],
                    "supporting_narration_texts": entry.supporting_narration_texts if isinstance(entry.supporting_narration_texts, list) else [],
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

@app.post("/enhance-prompt")
async def enhance_prompt(request: EnhancementRequest):
    try:
        # Create enhancement prompt using the configuration
        enhancement_prompt = settings.ENHANCEMENT_PROMPT.format(
            topic=request.topic,
            subject=request.subject
        )

        logger.info("Enhancing prompt", extra={
            "action": "enhance_prompt",
            "topic": request.topic,
            "subject": request.subject,
            "provider": request.provider
        })

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

@app.post("/retrieve-similar", response_model=RetrieveSimilarResponse)
async def retrieve_similar_visualizations(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    top_k: int = Query(5, description="Number of similar results to return")
) -> RetrieveSimilarResponse:
    """Retrieve similar visualizations/snippets based on user prompt and config."""
    try:
        # Prepare embedding input using the same utility as /generate
        if request.config:
            embedding_input = build_embedding_text_from_config(request.config.model_dump())
        else:
            embedding_input = request.topic
        embedding = EmbeddingService.generate_embedding(embedding_input)
        vector_store = get_vector_store()
        similar = await vector_store.get_similar_visualizations(embedding, limit=top_k)
        # Optionally, add similarity scores if available
        results = []
        for item in similar:
            meta = item.get('metadata', {})
            score = item.get('score') if 'score' in item else None
            results.append({
                'metadata': meta,
                'score': score
            })
        return RetrieveSimilarResponse(results=results)
    except Exception as e:
        logger.error("Error retrieving similar visualizations", extra={
            "action": "retrieve_similar_visualizations",
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
            # migrate_from_json()
            # run_migration()  # Run the new migration
            pass
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

        # Initialize vector store
        vector_store = get_vector_store()
        try:
            vector_store.load(settings.VECTOR_STORE_PATH)
            logger.info("Vector store loaded successfully", extra={
                "action": "init_vector_store",
                "path": settings.VECTOR_STORE_PATH,
                "num_vectors": vector_store.faiss_index.ntotal if vector_store.faiss_index else 0
            })
        except FileNotFoundError:
            logger.info("No existing vector store found, starting fresh", extra={
                "action": "init_vector_store",
                "path": settings.VECTOR_STORE_PATH
            })
        except Exception as e:
            logger.error("Error loading vector store", extra={
                "action": "init_vector_store",
                "error": str(e)
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
