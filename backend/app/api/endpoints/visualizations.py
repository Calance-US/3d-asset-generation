from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ...database.database import get_db
from ...models import Visualization
from ...schemas.visualization import VisualizationCreate, VisualizationResponse
from ...services.prompt_selector import PromptSelector
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.utils.embedding_utils import build_embedding_text_from_config
import json
from pydantic import BaseModel
import datetime
import logging
from app.utils import parse_html_content, serialize_datetimes
from app.schemas.schemas import GenerateRequest, HTMLResponse
from app.services.prompt_generator import PromptGenerator
from app.config.settings import settings
from app.database.database import create_prompt, create_history_entry
import aiohttp
from openai import AsyncOpenAI
from fastapi import Request
from app.services.model_repository import ModelRepository
import time
from bs4 import BeautifulSoup
from google.generativeai.types import HarmCategory, HarmBlockThreshold

router = APIRouter()
prompt_selector = PromptSelector()
logger = logging.getLogger(__name__)
prompt_generator = PromptGenerator()
model_repository = ModelRepository()

@router.post("/save", response_model=VisualizationResponse)
async def save_visualization(
    visualization: VisualizationCreate,
    db: Session = Depends(get_db)
) -> VisualizationResponse:
    """Save a visualization to the library."""
    try:
        # Generate embedding for the visualization
        embedding = EmbeddingService.generate_embedding(visualization.topic)
        embedding = embedding.tolist()  # Ensure JSON serializable

        # Create new visualization
        db_visualization = Visualization(
            topic=visualization.topic,
            subject=visualization.subject,
            html_content=visualization.html_content,
            config=visualization.config,
            embedding=embedding,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
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

@router.get("/", response_model=List[VisualizationResponse])
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

@router.get("/{visualization_id}", response_model=VisualizationResponse)
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

class SimilarVisualizationRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None
    top_k: int = 5

@router.post("/retrieve_similar", response_model=List[VisualizationResponse])
async def retrieve_similar_visualizations(
    request: SimilarVisualizationRequest,
    db: Session = Depends(get_db)
):
    """Retrieve similar visualizations based on user prompt and/or config for context injection."""
    # Combine prompt and config for embedding if config is provided
    if request.config:
        embedding_input = build_embedding_text_from_config(request.config)
    else:
        embedding_input = request.prompt
    embedding = EmbeddingService.generate_embedding(embedding_input)
    vector_store = get_vector_store()
    # Retrieve top_k similar visualizations from the vector store
    similar = await vector_store.get_similar_visualizations(embedding, limit=request.top_k)
    # Optionally, fetch full visualization details from the DB using metadata (e.g., by id)
    results = []
    for item in similar:
        meta = item['metadata']
        # If you store visualization id in metadata, fetch from DB for full details
        viz_id = meta.get('id')
        if viz_id:
            db_viz = db.query(Visualization).filter_by(id=viz_id).first()
            if db_viz:
                results.append(db_viz)
            else:
                # Fallback: return metadata as VisualizationResponse
                results.append(VisualizationResponse(**meta))
        else:
            # Fallback: return metadata as VisualizationResponse
            results.append(VisualizationResponse(**meta))
    return results

@router.post("/generate", response_model=HTMLResponse)
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
        similar = await vector_store.get_similar_visualizations(embedding, db, limit=settings.SIMILAR_VIS_LIMIT)
        # Build improved context string from similar visualizations
        context_blocks = []
        for idx, item in enumerate(similar, 1):
            meta = item['metadata']
            meta = serialize_datetimes(meta)
            viz_id = meta.get('id')
            viz = None
            if viz_id and isinstance(viz_id, int):
                viz = db.query(Visualization).filter_by(id=viz_id).first()
            # Prefer full visualization from DB if available
            if viz:
                context_blocks.append(
                    f"""### Example {idx}\n- **Summary:** {viz.config.get('scene_description', '')}\n- **Code Snippet:**  \n```code\n{viz.html_content[:1000]}{'... (truncated)' if len(viz.html_content) > 1000 else ''}\n```\n"""
                )
            else:
                context_blocks.append(
                    f"""### Example {idx}\n- **Summary:** {meta.get('summary', '')}\n- **Code Snippet:**  \n```code\n{meta.get('html_snippet', '')[:1000]}{'... (truncated)' if meta.get('html_snippet', '') and len(meta.get('html_snippet', '')) > 1000 else ''}\n```\n"""
                )
        if context_blocks:
            context_text = (
                "---\n"
                "## 📚 Context: Gold Standard Examples\n\n"
                "Below are high-quality, accurate examples for your reference. Use their structure, accuracy, and style as a guide for your own output.\n\n"
                + "---\n\n".join(context_blocks) +
                "---\n\n"
            )
        else:
            context_text = ""
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
        # Inject improved context into the prompt
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
            if not settings.OPENAI_API_KEY:
                logger.error("OpenAI API key not configured", extra={
                    "action": "generate_visualization",
                    "provider": "openai"
                })
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
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
            if not settings.GOOGLE_API_KEY:
                logger.error("Google API key not configured", extra={
                    "action": "generate_visualization",
                    "provider": "gemini"
                })
                raise HTTPException(status_code=400, detail="Google API key not configured")
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
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
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now()
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
            "id": str(datetime.datetime.now().timestamp()),
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
            "created_at": datetime.datetime.now()
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