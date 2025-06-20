import datetime
import json
import logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.config.settings import settings
from app.database.database import create_history_entry, create_prompt, get_db
from app.models import User, Visualization
from app.schemas.schemas import GenerateRequest, HTMLResponse
from app.schemas.visualization import VisualizationCreate, VisualizationResponse
from app.services.error_fixing.error_fixing_service import error_fixing_service
from app.services.error_fixing.validation_error_service import validation_error_service
from app.services.model_repository import ModelRepository
from app.services.prompt_generator import PromptGenerator
from app.services.prompt_selector import PromptSelector
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.services.validation.html_validator import HTMLValidator
from app.services.validation.realism_validator import RealismValidator
from app.services.validation.scientific_validator import ScientificValidator
from app.services.validation.simple_orchestrator import SimpleValidationOrchestrator
from app.services.validation.threejs_validator import ThreeJSValidator
from app.utils import parse_html_content, serialize_datetimes
from app.utils.embedding_utils import build_embedding_text_from_config
from fastapi import APIRouter, Depends, HTTPException
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()
prompt_selector = PromptSelector()
logger = logging.getLogger(__name__)
prompt_generator = PromptGenerator()
html_validator = HTMLValidator()
threejs_validator = ThreeJSValidator()
scientific_validator = ScientificValidator()
realism_validator = RealismValidator()
model_repository = ModelRepository()

# Initialize comprehensive validation system
validation_orchestrator = SimpleValidationOrchestrator()


@router.post("/save", response_model=VisualizationResponse)
async def save_visualization(
    visualization: VisualizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
            user_id=current_user.id,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
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
            updated_at=db_visualization.updated_at,
        )

    except Exception as e:
        logger.error(
            "Error saving visualization",
            extra={
                "action": "save_visualization",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[VisualizationResponse])
async def get_visualizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
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
                updated_at=v.updated_at,
            )
            for v in visualizations
        ]
    except Exception as e:
        logger.error(
            "Error getting visualizations",
            extra={
                "action": "get_visualizations",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{visualization_id}", response_model=VisualizationResponse)
async def get_visualization(
    visualization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
) -> VisualizationResponse:
    """Get a specific visualization by ID."""
    try:
        visualization = (
            db.query(Visualization).filter(Visualization.id == visualization_id).first()
        )
        if not visualization:
            raise HTTPException(status_code=404, detail="Visualization not found")
        return VisualizationResponse(
            id=visualization.id,
            topic=visualization.topic,
            subject=visualization.subject,
            html_content=visualization.html_content,
            config=visualization.config,
            created_at=visualization.created_at,
            updated_at=visualization.updated_at,
        )
    except Exception as e:
        logger.error(
            "Error getting visualization",
            extra={
                "action": "get_visualization",
                "visualization_id": visualization_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


class SimilarVisualizationRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None
    top_k: int = 5


@router.post("/generate", response_model=HTMLResponse)
async def generate_visualization(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    """Generate a 3D visualization based on the topic."""
    try:
        start_time = time.time()
        logger.info(
            "Starting visualization generation",
            extra={
                "action": "generate_visualization",
                "has_config": bool(request.config),
            },
        )
        logger.debug(
            f"Request config: {json.dumps(request.config.model_dump() if request.config else None, indent=2)}"
        )
        # --- Retrieve similar visualizations for context injection ---
        vector_store = get_vector_store()
        # Prepare fields for embedding context
        if request.config:
            embedding_input = build_embedding_text_from_config(
                request.config.model_dump()
            )
        else:
            embedding_input = request.topic
        embedding = EmbeddingService.generate_embedding(embedding_input)
        similar = await vector_store.get_similar_visualizations(
            embedding, db, limit=settings.SIMILAR_VIS_LIMIT
        )

        # Filter to limit 1 example per snippet_type
        seen_snippet_types = set()
        filtered_similar = []
        for item in similar:
            meta = item["metadata"]
            snippet_type = meta.get("snippet_type", "miscellaneous")
            if snippet_type not in seen_snippet_types:
                seen_snippet_types.add(snippet_type)
                filtered_similar.append(item)

        # Build improved context string from similar visualizations
        context_blocks = []
        for idx, item in enumerate(filtered_similar, 1):
            meta = item["metadata"]
            meta = serialize_datetimes(meta)
            viz_id = meta.get("id")
            viz = None
            if viz_id and isinstance(viz_id, int):
                viz = db.query(Visualization).filter_by(id=viz_id).first()
            # Prefer full visualization from DB if available
            if viz:
                config_dict = viz.config if isinstance(viz.config, dict) else {}
                context_blocks.append(
                    f"""### Example {idx}\n- **Summary:** {config_dict.get("scene_description", "")}\n- **Code Snippet:**  \n```code\n{viz.html_content[:1000]}{"... (truncated)" if len(viz.html_content) > 1000 else ""}\n```\n"""
                )
            else:
                meta_dict = meta if isinstance(meta, dict) else {}
                html_snippet = meta_dict.get("html_snippet", "")
                context_blocks.append(
                    f"""### Example {idx}\n- **Summary:** {meta_dict.get("summary", "")}\n- **Code Snippet:**  \n```code\n{html_snippet[:1000]}{"... (truncated)" if html_snippet and len(html_snippet) > 1000 else ""}\n```\n"""
                )
        if context_blocks:
            context_text = (
                "---\n"
                "## 📚 Context: Gold Standard Examples\n\n"
                "Below are high-quality, accurate examples for your reference. Use their structure, accuracy, and style as a guide for your own output.\n\n"
                + "---\n\n".join(context_blocks)
                + "---\n\n"
            )
        else:
            context_text = ""
        # --- Logging retrieval quality ---
        logger.info(
            "Retrieval event",
            extra={
                "user_query": request.topic,
                "embedding_input": embedding_input,
                "retrieved": [
                    {
                        "id": item["metadata"].get("id"),
                        "similarity": item.get("similarity"),
                        "summary": item["metadata"].get("scene_description", ""),
                    }
                    for item in filtered_similar
                ],
            },
        )
        # Generate the prompt using either custom config or basic topic info
        if request.config:
            logger.info(
                "Using provided configuration",
                extra={"action": "generate_visualization", "config_type": "provided"},
            )
            config_dict = request.config.model_dump()
            logger.debug(
                "Configuration details",
                extra={"action": "generate_visualization", "config": config_dict},
            )
            prompt_content = prompt_generator.generate_prompt(config_dict)
        else:
            logger.info(
                "Using basic topic info",
                extra={
                    "action": "generate_visualization",
                    "config_type": "basic",
                    "topic": request.topic,
                    "subject": request.subject,
                },
            )
            prompt_content = prompt_generator.generate_from_topic(
                request.topic, request.subject, education_level="High School"
            )
        # Inject improved context into the prompt
        if context_text:
            prompt_content = f"{context_text}\n\n---\n\n{prompt_content}"
        # Debug log the generated prompt
        logger.info("Generated Prompt Configuration:")
        logger.info(
            json.dumps(
                request.config.model_dump()
                if request.config
                else {
                    "topic": request.topic,
                    "subject": request.subject,
                    "education_level": "High School",
                },
                indent=2,
            )
        )
        logger.info("\nGenerated Prompt Content:")
        logger.info(prompt_content)
        generated_text: Optional[str] = None
        if request.provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.error(
                    "OpenAI API key not configured",
                    extra={"action": "generate_visualization", "provider": "openai"},
                )
                raise HTTPException(
                    status_code=400, detail="OpenAI API key not configured"
                )
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt_content}],
                temperature=settings.TEMPERATURE,
            )
            generated_text = response.choices[0].message.content
        elif request.provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": f"{prompt_content}",
                        "stream": settings.STREAM,
                    },
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Ollama request failed with status {response.status}",
                            extra={
                                "action": "generate_visualization",
                                "provider": "ollama",
                            },
                        )
                        raise HTTPException(
                            status_code=500, detail="Failed to generate with Ollama"
                        )
                    result = await response.json()
                    generated_text = str(result.get("response", ""))
        elif request.provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                logger.error(
                    "Google API key not configured",
                    extra={"action": "generate_visualization", "provider": "gemini"},
                )
                raise HTTPException(
                    status_code=400, detail="Google API key not configured"
                )
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
                },
            )
            generated_text = response.text
        else:
            logger.error(
                f"Invalid provider specified: {request.provider}",
                extra={
                    "action": "generate_visualization",
                    "provider": request.provider,
                },
            )
            raise HTTPException(status_code=400, detail="Invalid provider specified")
        # Parse the HTML content
        if generated_text is None:
            raise HTTPException(
                status_code=400, detail="No HTML content found in the response"
            )
        html_content = parse_html_content(generated_text)
        if not html_content:
            logger.error(
                "No HTML content found",
                extra={
                    "action": "validate_html",
                    "response_length": len(generated_text) if generated_text else 0,
                },
            )
            raise HTTPException(
                status_code=400, detail="No HTML content found in the response"
            )
        if not html_content.endswith("</html>"):
            logger.error(
                "No closing HTML tag found",
                extra={"action": "validate_html", "content_length": len(html_content)},
            )
            raise HTTPException(
                status_code=400, detail="No closing HTML tag found in the response"
            )
        # Enhanced validation with error fixing and retry logic
        prompt = None  # Will be created first for error tracking
        final_validation_result = None

        # Enhanced validation and retry loop
        for attempt in range(settings.MAX_LLM_RETRY + 1):
            logger.info(
                f"🔄 Validation attempt {attempt + 1}/{settings.MAX_LLM_RETRY + 1}"
            )

            try:
                validation_start_time = time.time()

                # Prepare content metadata
                content_metadata = {
                    "provider": request.provider,
                    "topic": request.topic,
                    "subject": request.subject,
                    "education_level": request.config.education_level
                    if request.config
                    else "High School",
                    "generation_time": time.time() - start_time,
                    "content_length": len(html_content),
                    "components": [
                        comp.model_dump() for comp in request.config.components
                    ]
                    if request.config and hasattr(request.config, "components")
                    else [],
                    "key_concepts": request.config.key_concepts
                    if request.config
                    else [],
                    "learning_objectives": request.config.learning_objectives
                    if request.config
                    else [],
                }

                # Configure validation based on request
                validation_config = {
                    "phases": {
                        "html_js": {
                            "enabled": True,
                            "timeout": settings.VALIDATION_TIMEOUT_HTML,
                            "critical": True,
                        },
                        "scientific": {
                            "enabled": True,
                            "timeout": settings.VALIDATION_TIMEOUT_SCIENTIFIC,
                            "critical": True,
                        },
                        "realism": {
                            "enabled": True,
                            "timeout": settings.VALIDATION_TIMEOUT_REALISM,
                            "critical": False,
                        },
                        "runtime": {
                            "enabled": settings.ENABLE_RUNTIME_VALIDATION,
                            "timeout": settings.VALIDATION_TIMEOUT_RUNTIME,
                            "critical": False,
                        },
                    },
                    "quality_scoring": {
                        "enabled": settings.ENABLE_QUALITY_FILTERING,
                        "threshold": settings.QUALITY_SCORE_THRESHOLD,
                    },
                    "feedback_loop": {
                        "enabled": settings.ENABLE_FEEDBACK_LOOP,
                        "learning": True,
                    },
                    "parallel_execution": True,
                    "fail_fast": False,
                }

                # Execute comprehensive validation
                validation_result = await validation_orchestrator.validate_content(
                    html_content=html_content,
                    title=request.topic,
                    subject=request.subject,
                    education_level=content_metadata["education_level"],
                    content_metadata=content_metadata,
                    validation_config=validation_config,
                )

                validation_time = time.time() - validation_start_time

                # Log comprehensive validation results
                logger.info(
                    "Comprehensive validation completed",
                    extra={
                        "action": "comprehensive_validation",
                        "attempt": attempt + 1,
                        "validation_time": validation_time,
                        "overall_success": validation_result["overall_success"],
                        "overall_quality_score": validation_result[
                            "overall_quality_score"
                        ],
                        "quality_tier": validation_result["quality_tier"],
                        "phase_results": {
                            "html_js": validation_result["phase_results"]["html_js"][
                                "success"
                            ],
                            "scientific": validation_result["phase_results"][
                                "scientific"
                            ]["success"],
                            "realism": validation_result["phase_results"]["realism"][
                                "success"
                            ],
                            "runtime": validation_result["phase_results"]
                            .get("runtime", {})
                            .get("success")
                            if validation_result["phase_results"].get("runtime")
                            else None,
                        },
                        "critical_issues_count": len(
                            validation_result["critical_issues"]
                        ),
                        "recommendation_count": len(
                            validation_result["recommendations"]
                        ),
                    },
                )

                if validation_result["overall_success"]:
                    logger.info("✅ Validation successful!")
                    final_validation_result = validation_result
                    break
                else:
                    logger.warning(
                        f"❌ Validation failed with {len(validation_result['critical_issues'])} critical issues"
                    )

                    # Extract errors in the format expected by error fixing service
                    validation_errors = []
                    for issue in validation_result["critical_issues"]:
                        # Handle both dict and string issue formats
                        if isinstance(issue, dict):
                            validation_errors.append(
                                {
                                    "phase": issue.get("phase", "unknown"),
                                    "severity": "critical",
                                    "error_type": issue.get("type", "unknown"),
                                    "message": issue.get("message", ""),
                                    "location": issue.get("location"),
                                    "suggestion": issue.get("suggestion"),
                                    "context": issue.get("context"),
                                }
                            )
                        else:
                            # Handle string issues
                            validation_errors.append(
                                {
                                    "phase": "unknown",
                                    "severity": "critical",
                                    "error_type": "validation_error",
                                    "message": str(issue),
                                    "location": None,
                                    "suggestion": None,
                                    "context": None,
                                }
                            )

                    # Add non-critical issues as warnings
                    for recommendation in validation_result.get("recommendations", []):
                        # Handle both dict and string recommendation formats
                        if isinstance(recommendation, dict):
                            validation_errors.append(
                                {
                                    "phase": recommendation.get("phase", "unknown"),
                                    "severity": "warning",
                                    "error_type": recommendation.get("type", "unknown"),
                                    "message": recommendation.get("message", ""),
                                    "location": recommendation.get("location"),
                                    "suggestion": recommendation.get("suggestion"),
                                    "context": recommendation.get("context"),
                                }
                            )
                        else:
                            # Handle string recommendations
                            validation_errors.append(
                                {
                                    "phase": "unknown",
                                    "severity": "warning",
                                    "error_type": "recommendation",
                                    "message": str(recommendation),
                                    "location": None,
                                    "suggestion": None,
                                    "context": None,
                                }
                            )

                    # Create prompt entry on first attempt if not already created
                    if prompt is None:
                        prompt_entry = {
                            "topic": request.topic,
                            "subject": request.subject,
                            "content": prompt_content,
                            "category": None,
                            "key_concepts": request.config.key_concepts
                            if request.config
                            else None,
                            "education_level": request.config.education_level
                            if request.config
                            else "High School",
                            "learning_objectives": request.config.learning_objectives
                            if request.config
                            else None,
                            "interactive_features": request.config.interactive_features
                            if request.config
                            else None,
                            "embedding": None,
                            "created_at": datetime.datetime.now(),
                            "updated_at": datetime.datetime.now(),
                        }

                        prompt = create_prompt(
                            db,
                            subject=prompt_entry["subject"],
                            topic=prompt_entry["topic"],
                            content=prompt_entry["content"],
                            category=prompt_entry["category"],
                            key_concepts=prompt_entry["key_concepts"],
                            education_level=prompt_entry["education_level"],
                            learning_objectives=prompt_entry["learning_objectives"],
                            interactive_features=prompt_entry["interactive_features"],
                        )

                    # Save validation errors to database
                    if settings.SAVE_ALL_VALIDATION_ERRORS:
                        error_metadata = {
                            "prompt_id": prompt.id if prompt else None,
                            "attempt_number": attempt + 1,
                            "quality_score": validation_result["overall_quality_score"],
                            "provider": request.provider,
                        }
                        validation_error_service.save_validation_errors(
                            db, validation_errors, error_metadata
                        )

                    # If this is the last attempt, return failure
                    if attempt >= settings.MAX_LLM_RETRY:
                        logger.error(
                            f"🔴 Maximum retry attempts ({settings.MAX_LLM_RETRY}) exhausted"
                        )

                        error_messages = [
                            error["message"] for error in validation_errors[:5]
                        ]
                        raise HTTPException(
                            status_code=400,
                            detail=f"Content validation failed after {attempt + 1} attempts: {'; '.join(error_messages)}",
                        )

                    # Try to fix the HTML using error-fixing prompt
                    if settings.ENABLE_ERROR_FIXING:
                        logger.info(
                            f"🔧 Attempting to fix HTML using error-fixing prompt (attempt {attempt + 1})"
                        )

                        try:
                            # Generate error-fixing prompt
                            fixing_prompt = (
                                error_fixing_service.create_error_fixing_prompt(
                                    html_content, validation_errors
                                )
                            )

                            # Get fixed HTML from LLM (reuse the same provider logic)
                            fixed_generated_text = None

                            if request.provider == "openai":
                                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                                response = await client.chat.completions.create(
                                    model=settings.OPENAI_MODEL,
                                    messages=[
                                        {"role": "user", "content": fixing_prompt}
                                    ],
                                    temperature=0.3,  # Lower temperature for fixes
                                )
                                fixed_generated_text = response.choices[
                                    0
                                ].message.content

                            elif request.provider == "ollama":
                                async with aiohttp.ClientSession() as session:
                                    async with session.post(
                                        f"{settings.OLLAMA_BASE_URL}/api/generate",
                                        json={
                                            "model": settings.OLLAMA_MODEL,
                                            "prompt": fixing_prompt,
                                            "stream": settings.STREAM,
                                        },
                                    ) as response:
                                        if response.status == 200:
                                            result = await response.json()
                                            fixed_generated_text = str(
                                                result.get("response", "")
                                            )

                            elif request.provider == "gemini":
                                import google.generativeai as genai

                                genai.configure(api_key=settings.GOOGLE_API_KEY)
                                gemini_model = genai.GenerativeModel(
                                    settings.GEMINI_MODEL
                                )
                                response = gemini_model.generate_content(
                                    fixing_prompt,
                                    safety_settings={
                                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                    },
                                )
                                fixed_generated_text = response.text

                            # Parse the fixed HTML
                            if fixed_generated_text:
                                fixed_html_content = parse_html_content(
                                    fixed_generated_text
                                )
                                if fixed_html_content:
                                    html_content = fixed_html_content
                                    logger.info(
                                        f"🔧 HTML fixed successfully ({len(fixed_html_content):,} characters)"
                                    )
                                else:
                                    logger.warning(
                                        "⚠️ Failed to parse fixed HTML, using original"
                                    )
                            else:
                                logger.warning(
                                    "⚠️ No fixed HTML generated, using original"
                                )

                        except Exception as e:
                            logger.error(f"🔴 Error fixing failed: {e}")
                            # Continue with original HTML for next validation attempt

            except Exception as e:
                logger.error(
                    f"🔴 Validation attempt {attempt + 1} failed with exception: {e}"
                )
                if attempt >= settings.MAX_LLM_RETRY:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Validation system error after {attempt + 1} attempts: {str(e)}",
                    )

        # If we get here without final_validation_result, something went wrong
        if final_validation_result is None:
            raise HTTPException(
                status_code=500,
                detail="Validation completed but no final result available",
            )

        # Create prompt entry if not already created during retry process
        if prompt is None:
            prompt_entry = {
                "topic": request.topic,
                "subject": request.subject,
                "content": prompt_content,
                "category": None,
                "key_concepts": request.config.key_concepts if request.config else None,
                "education_level": request.config.education_level
                if request.config
                else "High School",
                "learning_objectives": request.config.learning_objectives
                if request.config
                else None,
                "interactive_features": request.config.interactive_features
                if request.config
                else None,
                "embedding": None,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
            }

            prompt = create_prompt(
                db,
                subject=prompt_entry["subject"],
                topic=prompt_entry["topic"],
                content=prompt_entry["content"],
                category=prompt_entry["category"],
                key_concepts=prompt_entry["key_concepts"],
                education_level=prompt_entry["education_level"],
                learning_objectives=prompt_entry["learning_objectives"],
                interactive_features=prompt_entry["interactive_features"],
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
            "components": json.dumps(
                [comp.model_dump() for comp in request.config.components]
            )
            if request.config
            else None,
            "materials": json.dumps(
                [mat.model_dump() for mat in request.config.materials]
            )
            if request.config
            else None,
            "lights": json.dumps(
                [light.model_dump() for light in request.config.lights]
            )
            if request.config
            else None,
            "render_settings": json.dumps(request.config.renderer.model_dump())
            if request.config
            else None,
            "animation_speed": request.config.animation_speed
            if request.config
            else 1.0,
            "intro_narration_texts": json.dumps(request.config.intro_narration_texts)
            if request.config
            else None,
            "supporting_narration_texts": json.dumps(
                request.config.supporting_narration_texts
            )
            if request.config
            else None,
            "scene_description": request.config.scene_description
            if request.config
            else None,
            "generation_time": generation_time,
            "created_at": datetime.datetime.now(),
        }
        create_history_entry(db, history_entry)
        return HTMLResponse(
            html=html_content, validation_results=final_validation_result
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions (like validation failures)
    except Exception as e:
        logger.error(
            "Error generating visualization",
            extra={
                "action": "generate_visualization",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-batch")
async def validate_batch_content(
    batch_request: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Validate multiple 3D visualizations in batch."""
    try:
        content_batch = batch_request.get("content_batch", [])
        batch_config = batch_request.get("batch_config", {})

        # Configure batch processing
        batch_config.setdefault("parallel_processing", True)
        batch_config.setdefault("max_concurrent", 5)
        batch_config.setdefault("quality_threshold", settings.QUALITY_SCORE_THRESHOLD)
        batch_config.setdefault("generate_report", True)

        # Execute batch validation
        batch_results = await validation_orchestrator.validate_batch(
            content_batch, batch_config
        )

        logger.info(
            "Batch validation completed",
            extra={
                "action": "batch_validation",
                "total_items": len(content_batch),
                "successful_validations": batch_results["summary"][
                    "successful_validations"
                ],
                "average_quality": batch_results["summary"]["average_quality_score"],
                "processing_time": batch_results["summary"]["total_processing_time"],
            },
        )

        return batch_results

    except Exception as e:
        logger.error(
            "Batch validation failed",
            extra={"action": "batch_validation_error", "error": str(e)},
        )
        raise HTTPException(
            status_code=500, detail=f"Batch validation failed: {str(e)}"
        )
