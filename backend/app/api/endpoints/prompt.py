import json
import logging
from typing import Optional

import aiohttp
from app.auth.dependencies import get_current_user
from app.config.settings import settings
from app.database.database import (
    batch_delete_prompts,
    create_prompt,
    delete_prompt,
    duplicate_prompt,
    export_prompts,
    get_db,
    get_prompts,
    import_prompts,
    update_prompt,
)
from app.models import User
from app.schemas.schemas import (
    BatchDeleteRequest,
    CreatePromptRequest,
    EnhancedPromptResponse,
    EnhancementRequest,
    ImportPromptsRequest,
    PromptResponse,
    PromptsResponse,
    SuccessResponse,
    UpdatePromptRequest,
)
from app.services.prompt_selector import PromptSelector
from fastapi import APIRouter, Depends, HTTPException
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)
prompt_selector = PromptSelector()

gemini_model = None
client = None
try:
    if settings.OPENAI_API_KEY:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    if settings.GOOGLE_API_KEY:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
except Exception:
    pass


@router.post("/enhance-prompt")
async def enhance_prompt(request: EnhancementRequest):
    try:
        enhancement_prompt = settings.ENHANCEMENT_PROMPT.format(
            topic=request.topic, subject=request.subject
        )
        logger.info(
            "Enhancing prompt",
            extra={
                "action": "enhance_prompt",
                "topic": request.topic,
                "subject": request.subject,
                "provider": request.provider,
            },
        )
        if request.provider == "openai":
            if not client:
                logger.error(
                    "OpenAI API key not configured",
                    extra={"action": "enhance_prompt", "provider": "openai"},
                )
                raise HTTPException(
                    status_code=400, detail="OpenAI API key not configured"
                )
            logger.info(
                "Using OpenAI for prompt enhancement",
                extra={"action": "enhance_prompt", "provider": "openai"},
            )
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": enhancement_prompt}],
                temperature=0.7,
            )
            generated_text = response.choices[0].message.content
            logger.debug(
                "OpenAI response received",
                extra={
                    "action": "enhance_prompt",
                    "provider": "openai",
                    "response_length": len(generated_text) if generated_text else 0,
                },
            )
            if not generated_text:
                logger.error(
                    "No response from OpenAI",
                    extra={"action": "enhance_prompt", "provider": "openai"},
                )
                raise HTTPException(status_code=500, detail="No response from OpenAI")
            try:
                cleaned_text = (
                    generated_text.replace("```json", "").replace("```", "").strip()
                )
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                enhanced_config = json.loads(cleaned_text)
                # Validate required fields
                required_fields = [
                    "topic_name",
                    "key_concepts",
                    "education_level",
                    "learning_objectives",
                    "interactive_features",
                    "components",
                    "materials",
                    "lights",
                    "interactive_description",
                    "animated_elements",
                    "intro_narration_texts",
                    "supporting_narration_texts",
                    "scene_description",
                ]
                missing_fields = [
                    field for field in required_fields if field not in enhanced_config
                ]
                if missing_fields:
                    raise ValueError(
                        f"Missing required fields: {', '.join(missing_fields)}"
                    )
            except Exception as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                logger.error(f"Raw response: {generated_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse LLM response as JSON: {str(e)}",
                )
        elif request.provider == "ollama":
            logger.info(
                "Using Ollama for prompt enhancement",
                extra={"action": "enhance_prompt", "provider": "ollama"},
            )
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": enhancement_prompt,
                        "stream": False,
                    },
                ) as response:
                    if response.status != 200:
                        logger.error(
                            f"Ollama request failed with status {response.status}",
                            extra={"action": "enhance_prompt", "provider": "ollama"},
                        )
                        raise HTTPException(
                            status_code=500, detail="Failed to generate with Ollama"
                        )
                    result = await response.json()
                    generated_text = result.get("response", "")
                    logger.debug(
                        "Ollama response received",
                        extra={
                            "action": "enhance_prompt",
                            "provider": "ollama",
                            "response_length": len(generated_text),
                        },
                    )
                    try:
                        cleaned_text = (
                            generated_text.replace("```json", "")
                            .replace("```", "")
                            .strip()
                        )
                        start_idx = cleaned_text.find("{")
                        end_idx = cleaned_text.rfind("}") + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            cleaned_text = cleaned_text[start_idx:end_idx]
                        enhanced_config = json.loads(cleaned_text)
                    except Exception as e:
                        logger.error(
                            f"Failed to parse Ollama response as JSON: {str(e)}"
                        )
                        logger.error(f"Raw response: {generated_text}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to parse Ollama response as JSON: {str(e)}",
                        )
        elif request.provider == "gemini":
            if not gemini_model:
                logger.error(
                    "Google API key not configured",
                    extra={"action": "enhance_prompt", "provider": "gemini"},
                )
                raise HTTPException(
                    status_code=400, detail="Google API key not configured"
                )
            logger.info(
                "Using Gemini for prompt enhancement",
                extra={"action": "enhance_prompt", "provider": "gemini"},
            )
            response = gemini_model.generate_content(
                enhancement_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
            generated_text = response.text
            logger.debug(
                "Gemini response received",
                extra={
                    "action": "enhance_prompt",
                    "provider": "gemini",
                    "response_length": len(generated_text),
                },
            )
            try:
                cleaned_text = (
                    generated_text.replace("```json", "").replace("```", "").strip()
                )
                start_idx = cleaned_text.find("{")
                end_idx = cleaned_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = cleaned_text[start_idx:end_idx]
                enhanced_config = json.loads(cleaned_text)
            except Exception as e:
                logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
                logger.error(f"Raw response: {generated_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse Gemini response as JSON: {str(e)}",
                )
        else:
            logger.error(
                f"Invalid provider specified: {request.provider}",
                extra={"action": "enhance_prompt", "provider": request.provider},
            )
            raise HTTPException(status_code=400, detail="Invalid provider specified")
        logger.info(
            "Successfully generated enhanced configuration",
            extra={"action": "enhance_prompt", "provider": request.provider},
        )
        logger.debug(f"Enhanced configuration: {json.dumps(enhanced_config, indent=2)}")
        return EnhancedPromptResponse(**enhanced_config)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to parse LLM response as JSON"
        )
    except Exception as e:
        logger.error(
            "Error enhancing prompt",
            extra={
                "action": "enhance_prompt",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PromptsResponse)
async def get_all_prompts(
    subject: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
) -> PromptsResponse:
    """Get all prompts from the database with optional filtering."""
    try:
        prompts = get_prompts(db, subject, category, tag, search)
        return PromptsResponse(
            prompts=[
                PromptResponse(
                    id=prompt.id,
                    subject=prompt.subject,
                    topic=prompt.topic,
                    content=prompt.content,
                    category=prompt.category,
                    tags=[tag.name for tag in prompt.tags],
                )
                for prompt in prompts
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PromptResponse)
async def create_prompt_endpoint(
    prompt_data: CreatePromptRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PromptResponse:
    """Create a new prompt in the database."""
    try:
        new_prompt = create_prompt(
            db,
            subject=prompt_data.subject,
            topic=prompt_data.topic,
            content=prompt_data.content,
            category=prompt_data.category,
            tags=",".join(prompt_data.tags) if prompt_data.tags else "",
            user_id=current_user.id,
        )
        prompt_selector.initialize_index()
        return PromptResponse(
            id=new_prompt.id,
            subject=new_prompt.subject,
            topic=new_prompt.topic,
            content=new_prompt.content,
            category=new_prompt.category,
            tags=[tag.name for tag in new_prompt.tags],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt_endpoint(
    prompt_id: int, prompt_data: UpdatePromptRequest, db: Session = Depends(get_db)
) -> PromptResponse:
    """Update a prompt in the database."""
    try:
        update_data = {k: v for k, v in prompt_data.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update"
            )
        updated_prompt = update_prompt(db, prompt_id, update_data)
        if not updated_prompt:
            raise HTTPException(
                status_code=404, detail=f"Prompt with ID {prompt_id} not found"
            )
        prompt_selector.initialize_index()
        return PromptResponse(
            id=updated_prompt.id,
            subject=updated_prompt.subject,
            topic=updated_prompt.topic,
            content=updated_prompt.content,
            category=updated_prompt.category,
            tags=[tag.name for tag in updated_prompt.tags],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt_endpoint(
    prompt_id: int, db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete a prompt from the database."""
    try:
        success = delete_prompt(db, prompt_id)
        if not success:
            raise HTTPException(
                status_code=404, detail=f"Prompt with ID {prompt_id} not found"
            )
        prompt_selector.initialize_index()
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{prompt_id}/duplicate", response_model=PromptResponse)
async def duplicate_prompt_endpoint(
    prompt_id: int, db: Session = Depends(get_db)
) -> PromptResponse:
    """Duplicate a prompt."""
    try:
        duplicated = duplicate_prompt(db, prompt_id)
        if not duplicated:
            raise HTTPException(
                status_code=404, detail=f"Prompt with ID {prompt_id} not found"
            )
        return PromptResponse(
            id=duplicated.id,
            subject=duplicated.subject,
            topic=duplicated.topic,
            content=duplicated.content,
            category=duplicated.category,
            tags=[tag.name for tag in duplicated.tags],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-delete", response_model=SuccessResponse)
async def batch_delete_prompts_endpoint(
    request: BatchDeleteRequest, db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete multiple prompts."""
    try:
        success = batch_delete_prompts(db, request.prompt_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete prompts")
        prompt_selector.initialize_index()
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", response_model=PromptsResponse)
async def export_prompts_endpoint(db: Session = Depends(get_db)) -> PromptsResponse:
    """Export all prompts."""
    try:
        prompts_data = export_prompts(db)
        return PromptsResponse(
            prompts=[
                PromptResponse(
                    id=prompt["id"],
                    subject=prompt["subject"],
                    topic=prompt["topic"],
                    content=prompt["content"],
                    category=prompt["category"],
                    tags=prompt["tags"],
                )
                for prompt in prompts_data
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=SuccessResponse)
async def import_prompts_endpoint(
    request: ImportPromptsRequest, db: Session = Depends(get_db)
) -> SuccessResponse:
    """Import prompts."""
    try:
        success = import_prompts(db, request.prompts)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import prompts")
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
