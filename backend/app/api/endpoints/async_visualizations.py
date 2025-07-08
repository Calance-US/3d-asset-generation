"""
Enhanced Async Visualization Generation with Database-Backed Task Management

This module provides async visualization generation with tasks persisted in the database
using AsyncTask and AsyncTaskStage models instead of in-memory storage.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from app.auth.dependencies import get_current_user
from app.config.settings import settings
from app.database.database import create_history_entry, create_prompt, get_db
from app.models import AsyncTask, AsyncTaskStage, User
from app.schemas.schemas import GenerateRequest
from app.services.error_fixing.enhanced_error_fixing_service import (
    enhanced_error_fixing_service,
)
from app.services.error_fixing.error_fixing_service import ErrorFixingService
from app.services.prompt_generator import PromptGenerator
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.utils.embedding_utils import build_embedding_text_from_config
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from openai import AsyncOpenAI
from sqlalchemy.orm import Session


# Define task status enum
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# Define base stage names for visualization generation
BASE_VISUALIZATION_STAGES = [
    "initialization",
    "context_retrieval",
    "prompt_generation",
    "llm_generation",
    "result_preparation",
    "finalization",
]

def get_visualization_stages() -> List[str]:
    """Get the complete list of visualization stages including validation attempts."""
    stages = BASE_VISUALIZATION_STAGES.copy()
    
    # Insert validation attempts before result_preparation
    validation_index = stages.index("result_preparation")
    for i in range(1, settings.MAX_VALIDATION_ATTEMPTS + 1):
        stages.insert(validation_index, f"validation_attempt_{i}")
    
    # Insert post-validation enhancement stage after validation attempts
    enhancement_index = validation_index + settings.MAX_VALIDATION_ATTEMPTS
    stages.insert(enhancement_index, "post_validation_enhancement")
    
    return stages

VISUALIZATION_STAGES = get_visualization_stages()


router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
prompt_generator = PromptGenerator()
error_fixing_service = ErrorFixingService()

# Initialize validation orchestrator
from app.services.validation.validation_orchestrator import ValidationOrchestrator
validation_orchestrator = ValidationOrchestrator()


# Database-backed task management functions
def create_async_task(
    db: Session,
    task_type: str,
    request_data: Dict[str, Any],
    user_id: int,
    timeout_minutes: int = 15,
    max_retries: int = 3,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new async task in the database."""
    task_id = str(uuid.uuid4())

    task = AsyncTask(
        id=task_id,
        task_type=task_type,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress_percentage=0,
        total_stages=len(VISUALIZATION_STAGES),
        expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
        user_id=user_id,
    )

    # Set request data using the model method
    task.set_request_data(request_data)

    db.add(task)

    # Create stages
    for i, stage_name in enumerate(VISUALIZATION_STAGES):
        stage = AsyncTaskStage(
            task_id=task_id,
            name=stage_name,
            status="pending",
            order_index=i + 1,
            progress_percentage=0,
            message=f"Preparing {stage_name}",
        )
        db.add(stage)

    db.commit()
    return task_id


def update_task_status(
    db: Session, task_id: str, status: str, error_message: Optional[str] = None
) -> None:
    """Update task status in database."""
    task: Optional[AsyncTask] = (
        db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    )
    if task is not None:
        task.status = status  # type: ignore
        task.updated_at = datetime.utcnow()  # type: ignore
        if error_message:
            task.error_message = error_message  # type: ignore
        if status == "completed":
            task.completed_at = datetime.utcnow()  # type: ignore
            task.progress_percentage = 100  # type: ignore
        db.commit()


def start_task_stage(
    db: Session, task_id: str, stage_name: str, message: Optional[str] = None
) -> None:
    """Start a task stage."""
    task: Optional[AsyncTask] = (
        db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    )
    if task is not None:
        task.current_stage = stage_name  # type: ignore
        task.updated_at = datetime.utcnow()  # type: ignore
        if task.started_at is None:  # type: ignore
            task.status = "running"  # type: ignore
            task.started_at = datetime.utcnow()  # type: ignore

        # Create or update stage
        stage: Optional[AsyncTaskStage] = (
            db.query(AsyncTaskStage)
            .filter(
                AsyncTaskStage.task_id == task_id, AsyncTaskStage.name == stage_name
            )
            .first()
        )
        if stage is not None:
            stage.status = "running"  # type: ignore
            stage.started_at = datetime.utcnow()  # type: ignore
            stage.message = message or f"Started {stage_name}"  # type: ignore
        db.commit()


def update_task_stage(
    db: Session,
    task_id: str,
    stage_name: str,
    progress: int,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Update a task stage."""
    stage: Optional[AsyncTaskStage] = (
        db.query(AsyncTaskStage)
        .filter(AsyncTaskStage.task_id == task_id, AsyncTaskStage.name == stage_name)
        .first()
    )
    if stage is not None:
        stage.progress_percentage = progress  # type: ignore
        if message:
            stage.message = message  # type: ignore
        if details:
            stage.details = details  # type: ignore

        # Update overall task progress
        task: Optional[AsyncTask] = (
            db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
        )
        if task is not None:
            # Calculate average progress across all stages
            stages = (
                db.query(AsyncTaskStage).filter(AsyncTaskStage.task_id == task_id).all()
            )
            if stages:
                total_progress = sum(s.progress_percentage for s in stages)
                task.progress_percentage = total_progress // len(stages)  # type: ignore
            task.updated_at = datetime.utcnow()  # type: ignore
        db.commit()


def complete_task_stage(
    db: Session,
    task_id: str,
    stage_name: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Complete a task stage."""
    stage: Optional[AsyncTaskStage] = (
        db.query(AsyncTaskStage)
        .filter(AsyncTaskStage.task_id == task_id, AsyncTaskStage.name == stage_name)
        .first()
    )
    if stage is not None:
        stage.status = "completed"  # type: ignore
        stage.progress_percentage = 100  # type: ignore
        stage.completed_at = datetime.utcnow()  # type: ignore
        stage.message = message or f"Completed {stage_name}"  # type: ignore
        if details:
            stage.details = details  # type: ignore
        db.commit()


def fail_task_stage(
    db: Session,
    task_id: str,
    stage_name: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Fail a task stage."""
    try:
        stage: Optional[AsyncTaskStage] = (
            db.query(AsyncTaskStage)
            .filter(AsyncTaskStage.task_id == task_id, AsyncTaskStage.name == stage_name)
            .first()
        )
        if stage is not None:
            stage.status = "failed"  # type: ignore
            stage.completed_at = datetime.utcnow()  # type: ignore
            stage.error_message = error_message  # type: ignore
            if details:
                stage.details = details  # type: ignore
            db.commit()

        # Fail the entire task
        update_task_status(db, task_id, "failed", error_message)
    except Exception as e:
        logger.error(f"Error in fail_task_stage: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback session in fail_task_stage: {rollback_error}")
        # Try to update task status even if stage update failed
        try:
            update_task_status(db, task_id, "failed", error_message)
        except Exception as status_error:
            logger.error(f"Failed to update task status in fail_task_stage: {status_error}")


def complete_task(db: Session, task_id: str, result: Dict[str, Any]) -> None:
    """Complete a task with results."""
    task: Optional[AsyncTask] = (
        db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    )
    if task is not None:
        task.status = "completed"  # type: ignore
        task.completed_at = datetime.utcnow()  # type: ignore
        task.updated_at = datetime.utcnow()  # type: ignore
        task.progress_percentage = 100  # type: ignore
        task.result = result  # type: ignore
        db.commit()


@router.post("/generate-async")
async def generate_visualization_async(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Start async visualization generation and return task ID immediately.

    Returns:
        Dict with task_id for polling status
    """
    try:
        # Create async task in database
        task_id = create_async_task(
            db=db,
            task_type="visualization_generation",
            request_data=request.model_dump(),
            timeout_minutes=15,
            max_retries=settings.MAX_LLM_RETRY,
            user_id=current_user.id,
            metadata={
                "provider": request.provider,
                "topic": request.topic,
                "subject": request.subject,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        # Start background processing
        background_tasks.add_task(_process_visualization_generation, task_id, request, current_user.id)

        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Visualization generation started. Use task_id to poll for status.",
            "poll_url": f"/api/v1/async-visualizations/status/{task_id}",
        }

    except Exception as e:
        logger.error(f"Error creating async task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create async task")


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get the current status of a visualization generation task."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Get stages
    stages = (
        db.query(AsyncTaskStage)
        .filter(AsyncTaskStage.task_id == task_id)
        .order_by(AsyncTaskStage.order_index)
        .all()
    )

    # Find current stage
    current_stage = None
    for stage in stages:
        if stage.status == "running":  # type: ignore
            current_stage = {
                "name": stage.name,
                "status": stage.status,
                "start_time": stage.started_at.isoformat()
                if stage.started_at  # type: ignore
                else None,
                "end_time": stage.completed_at.isoformat()
                if stage.completed_at  # type: ignore
                else None,
                "progress_percentage": stage.progress_percentage,
                "message": stage.message,
                "details": stage.details or {},
                "error": stage.error_message,
            }
            break

    # Format stages
    formatted_stages = []
    for stage in stages:
        formatted_stages.append(
            {
                "name": stage.name,
                "status": stage.status,
                "start_time": stage.started_at.isoformat()
                if stage.started_at  # type: ignore
                else None,
                "end_time": stage.completed_at.isoformat()
                if stage.completed_at  # type: ignore
                else None,
                "progress_percentage": stage.progress_percentage,
                "message": stage.message,
                "details": stage.details or {},
                "error": stage.error_message,
            }
        )

    return {
        "task_id": task.id,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,  # type: ignore
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # type: ignore
        "overall_progress": task.progress_percentage,
        "current_stage": current_stage,
        "stages": formatted_stages,
        "retry_count": 0,  # Can be added to AsyncTask model later
        "max_retries": 3,  # Can be added to AsyncTask model later
        "is_expired": False,  # Can implement expiration logic later
        "result": task.result,
        "error": task.error_message,
        "metadata": task.request_data or {},
    }


@router.get("/result/{task_id}")
async def get_task_result(task_id: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Get the result of a completed visualization generation task."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status in ["pending", "running"]:  # type: ignore
        raise HTTPException(
            status_code=202,
            detail=f"Task {task_id} is still {task.status}. Please wait for completion.",
        )

    if task.status == "failed":  # type: ignore
        raise HTTPException(
            status_code=500,
            detail=f"Task {task_id} failed: {task.error_message}",
        )

    if task.status != "completed":  # type: ignore
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} has status {task.status}",
        )

    result = task.get_result()
    if not result or "html_content" not in result:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} completed but no HTML result found",
        )

    return HTMLResponse(content=result["html_content"])


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Cancel a running visualization generation task."""
    task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status not in ["pending", "running"]:
        return {
            "task_id": task_id,
            "status": task.status,
            "message": f"Task {task_id} is already {task.status} and cannot be cancelled",
        }

    # Update task status to cancelled
    update_task_status(db, task_id, "cancelled")

    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": f"Task {task_id} has been cancelled",
    }


@router.get("/tasks")
async def list_recent_tasks(
    limit: int = 20, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List recent visualization generation tasks."""
    tasks = (
        db.query(AsyncTask)
        .filter(AsyncTask.task_type == "visualization_generation")
        .order_by(AsyncTask.created_at.desc())
        .limit(limit)
        .all()
    )

    formatted_tasks = []
    for task in tasks:
        formatted_tasks.append(
            {
                "task_id": task.id,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None,  # type: ignore
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,  # type: ignore
                "topic": (task.request_data or {}).get("topic", ""),  # type: ignore
                "provider": (task.request_data or {}).get("provider", ""),  # type: ignore
                "overall_progress": task.progress_percentage,
                "current_stage": task.current_stage,
            }
        )

    # Get statistics
    total_tasks = (
        db.query(AsyncTask)
        .filter(AsyncTask.task_type == "visualization_generation")
        .count()
    )
    completed_tasks = (
        db.query(AsyncTask)
        .filter(
            AsyncTask.task_type == "visualization_generation",
            AsyncTask.status == "completed",
        )
        .count()
    )
    failed_tasks = (
        db.query(AsyncTask)
        .filter(
            AsyncTask.task_type == "visualization_generation",
            AsyncTask.status == "failed",
        )
        .count()
    )
    running_tasks = (
        db.query(AsyncTask)
        .filter(
            AsyncTask.task_type == "visualization_generation",
            AsyncTask.status == "running",
        )
        .count()
    )

    return {
        "tasks": formatted_tasks,
        "total": len(formatted_tasks),
        "statistics": {
            "total_tasks": total_tasks,
            "status_distribution": {
                "pending": db.query(AsyncTask)
                .filter(
                    AsyncTask.task_type == "visualization_generation",
                    AsyncTask.status == "pending",
                )
                .count(),
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "cancelled": db.query(AsyncTask)
                .filter(
                    AsyncTask.task_type == "visualization_generation",
                    AsyncTask.status == "cancelled",
                )
                .count(),
                "timeout": db.query(AsyncTask)
                .filter(
                    AsyncTask.task_type == "visualization_generation",
                    AsyncTask.status == "timeout",
                )
                .count(),
            },
            "success_rate": (completed_tasks / total_tasks * 100)
            if total_tasks > 0
            else 0,
            "average_execution_time_seconds": 0,  # Can be calculated if needed
            "active_tasks": running_tasks,
            "pending_tasks": db.query(AsyncTask)
            .filter(
                AsyncTask.task_type == "visualization_generation",
                AsyncTask.status == "pending",
            )
            .count(),
        },
    }


async def _process_visualization_generation(task_id: str, request: GenerateRequest, user_id: int):
    """Process visualization generation in background."""
    db = next(get_db())
    start_time = time.time()  # Track generation time
    try:
        start_task_stage(
            db, task_id, "initialization", "Starting visualization generation"
        )

        logger.info(f"[{task_id}] Starting visualization generation")
        logger.info(f"[{task_id}] Request type: {type(request)}")
        logger.info(f"[{task_id}] Request config type: {type(request.config) if request.config else 'None'}")
        if request.config:
            logger.info(f"[{task_id}] Request config has components: {hasattr(request.config, 'components')}")
            logger.info(f"[{task_id}] Request config components: {getattr(request.config, 'components', 'NOT_FOUND')}")
        update_task_stage(db, task_id, "initialization", 25, "Initializing services")

        # Initialize services
        update_task_stage(db, task_id, "initialization", 50, "Services initialized")
        complete_task_stage(db, task_id, "initialization")

        # Stage 1: Context Retrieval
        start_task_stage(
            db, task_id, "context_retrieval", "Retrieving similar visualizations"
        )

        try:
            vector_store = get_vector_store()

            # Build rich embedding text with fallback strategies
            embedding_input = None
            embedding_strategy = "unknown"

            if request.config:
                try:
                    config_dict = request.config.model_dump()
                    embedding_input = build_embedding_text_from_config(config_dict)
                    embedding_strategy = "rich_config"
                    logger.info(
                        f"Built rich embedding text from config: {len(embedding_input)} characters"
                    )
                except Exception as config_error:
                    logger.warning(
                        f"Failed to build embedding from config: {config_error}"
                    )
                    # Fallback to topic_name from config if available
                    if (
                        hasattr(request.config, "topic_name")
                        and request.config.topic_name
                    ):
                        embedding_input = request.config.topic_name
                        embedding_strategy = "config_topic_name"
                        logger.info(
                            f"Using config topic_name as fallback: {embedding_input}"
                        )

            # Final fallback to request topic
            if not embedding_input:
                embedding_input = request.topic
                embedding_strategy = "request_topic"
                logger.info(
                    f"Using request topic as embedding input: {embedding_input}"
                )

            update_task_stage(
                db,
                task_id,
                "context_retrieval",
                30,
                f"Generating embeddings using {embedding_strategy} strategy",
            )

            try:
                embedding = EmbeddingService.generate_embedding(embedding_input)
                logger.debug(
                    f"Generated embedding with shape: {getattr(embedding, 'shape', 'unknown')}"
                )
            except Exception as embedding_error:
                logger.error(f"Failed to generate embedding: {embedding_error}")
                # Log embedding input for debugging (truncated for safety)
                input_preview = (
                    embedding_input[:200] + "..."
                    if len(embedding_input) > 200
                    else embedding_input
                )
                logger.debug(f"Embedding input preview: {input_preview}")
                raise Exception(f"Embedding generation failed: {embedding_error}")

            update_task_stage(
                db, task_id, "context_retrieval", 60, "Searching for similar content"
            )

            similar_results = vector_store.similarity_search_with_score(
                embedding, k=settings.SIMILAR_VIS_LIMIT
            )

            # Filter results by quality score if enabled
            filtered_similar = []
            for item in similar_results:
                if not settings.ENABLE_QUALITY_FILTERING:
                    filtered_similar.append(item)
                elif (
                    isinstance(item, tuple)
                    and len(item) > 1
                    and isinstance(item[0], dict)
                    and "quality_score" in item[0]
                    and item[0]["quality_score"] >= settings.CONTEXT_FILTER_MIN_QUALITY
                ):
                    filtered_similar.append(item)

            complete_task_stage(
                db,
                task_id,
                "context_retrieval",
                f"Retrieved {len(filtered_similar)} similar examples",
                {
                    "similar_count": len(filtered_similar),
                    "embedding_strategy": embedding_strategy,
                    "embedding_input_length": len(embedding_input),
                    "total_results_found": len(similar_results),
                    "quality_filtering_enabled": settings.ENABLE_QUALITY_FILTERING,
                },
            )

        except Exception as e:
            fail_task_stage(
                db, task_id, "context_retrieval", f"Context retrieval failed: {str(e)}"
            )
            return

        # Stage 2: Prompt Generation
        start_task_stage(
            db, task_id, "prompt_generation", "Building context and prompt"
        )

        try:
            # Build context
            context_items = []
            if filtered_similar:
                for result in filtered_similar:
                    context_items.append(
                        {
                            "topic": getattr(result, "topic", ""),
                            "html_content": getattr(result, "html_content", ""),
                            "score": getattr(result, "score", 0),
                        }
                    )

            # Generate context text
            context_text = ""
            if context_items:
                context_text = "Here are some similar visualizations for reference:\n\n"
                for i, item in enumerate(context_items[:3]):  # Limit to top 3
                    context_text += f"Example {i + 1}: {item['topic']}\n"
                    context_text += f"HTML: {item['html_content'][:500]}...\n\n"

            update_task_stage(db, task_id, "prompt_generation", 50, "Generating prompt")

            # Generate prompt using generate_from_topic method
            if request.config:
                # Convert PromptConfig to dict for generate_prompt
                config_dict = request.config.model_dump()
                prompt_content = prompt_generator.generate_prompt(config_dict)
            else:
                # Use the generate_from_topic method for simple cases
                prompt_content = prompt_generator.generate_from_topic(
                    topic=request.topic,
                    subject=request.subject or "physics",
                    education_level="High School",
                )

            # Combine context and prompt
            if context_text:
                prompt_content = f"{context_text}\n\n---\n\n{prompt_content}"

            complete_task_stage(
                db,
                task_id,
                "prompt_generation",
                f"Generated prompt ({len(prompt_content)} characters)",
                {"prompt_length": len(prompt_content)},
            )

        except Exception as e:
            fail_task_stage(
                db, task_id, "prompt_generation", f"Prompt generation failed: {str(e)}"
            )
            return

        # Stage 3: LLM Generation
        start_task_stage(
            db, task_id, "llm_generation", f"Generating content with {request.provider}"
        )

        try:
            html_content = await _generate_with_provider(
                prompt_content, request.provider
            )
            if not html_content:
                raise Exception("No content generated by LLM")

            complete_task_stage(
                db,
                task_id,
                "llm_generation",
                "LLM generation completed",
                {"content_length": len(html_content), "provider": request.provider},
            )

        except Exception as e:
            fail_task_stage(
                db, task_id, "llm_generation", f"LLM generation failed: {str(e)}"
            )
            return

        # Validation attempts with HTML error fixing
        best_quality_score = 0
        best_html_content = html_content
        validation_results = []
        current_html_content = html_content
        quality_enhancement_attempts = 0
        max_quality_enhancement_attempts = settings.QUALITY_ENHANCEMENT_MAX_ATTEMPTS

        for attempt in range(1, settings.MAX_VALIDATION_ATTEMPTS + 1):  # Configurable validation attempts
            stage_name = f"validation_attempt_{attempt}"
            start_task_stage(db, task_id, stage_name, f"Validation attempt {attempt}")

            try:
                # For attempts after the first one, fix HTML errors from previous validation
                if attempt > 1 and settings.ENABLE_ERROR_FIXING:
                    update_task_stage(
                        db,
                        task_id,
                        stage_name,
                        10,
                        f"Fixing HTML errors from previous validation (attempt {attempt})",
                    )

                    # Get errors from previous validation attempt
                    if validation_results:
                        previous_validation = validation_results[-1]
                        previous_errors = previous_validation.get("real_errors", [])  # Use real errors
                    else:
                        previous_errors = []
                    
                    if previous_errors:
                        logger.info(
                            f"[{task_id}] Fixing HTML errors for attempt {attempt}",
                            extra={
                                "attempt": attempt,
                                "previous_quality_score": previous_validation.get("quality_score", 0) if 'previous_validation' in locals() else 0,
                                "errors_to_fix": len(previous_errors),
                            },
                        )
                        
                        # Fix HTML errors using the enhanced error fixing service
                        fixing_result = await enhanced_error_fixing_service.fix_html_errors(
                            current_html_content,
                            previous_errors,
                            request.provider,
                        )
                        
                        if fixing_result.get("success") and fixing_result.get("fixed_html"):
                            current_html_content = fixing_result["fixed_html"]
                            logger.info(
                                f"[{task_id}] Successfully fixed HTML for attempt {attempt}",
                                extra={
                                    "attempt": attempt,
                                    "errors_addressed": fixing_result.get("errors_addressed", 0),
                                    "new_content_length": len(current_html_content),
                                },
                            )
                        else:
                            logger.warning(
                                f"[{task_id}] Failed to fix HTML for attempt {attempt}: {fixing_result.get('error', 'Unknown error')}"
                            )
                    else:
                        logger.info(f"[{task_id}] No errors to fix for attempt {attempt}")

                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    25,
                    f"Validating content (attempt {attempt})",
                )

                # Perform validation on current HTML content
                validation_result = await validation_orchestrator.validate_content(
                    html_content=current_html_content,
                    title="3D Visualization",
                    subject=request.subject,
                    education_level="high school"
                )

                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    50,
                    f"Processing validation results (attempt {attempt})",
                )

                # Try to get quality score from different possible locations
                current_quality_score = validation_result.get(
                    "overall_quality_score", 0
                )
                
                if current_quality_score == 0:
                    # Try from overall_result
                    overall_result = validation_result.get("overall_result", {})
                    current_quality_score = overall_result.get("overall_score", 0)
                    
                    # Try from quality_assessment
                    if current_quality_score == 0:
                        quality_assessment = validation_result.get("quality_assessment", {})
                        if quality_assessment and "metrics" in quality_assessment:
                            metrics = quality_assessment["metrics"]
                            current_quality_score = metrics.get("overall_quality_score", 0)

                # Extract errors from validation result structure
                validation_errors = []
                
                # Check for errors in phase results
                phase_results = validation_result.get("phase_results", {})
                for phase_name, phase_result in phase_results.items():
                    if phase_result and not phase_result.get("error"):
                        # Check for issues in each phase
                        issues = phase_result.get("issues", [])
                        for issue in issues:
                            validation_errors.append({
                                "phase": phase_name,
                                "type": issue.get("type", "unknown"),
                                "message": issue.get("message", "Unknown error"),
                                "severity": issue.get("severity", 1)
                            })
                
                # Check quality assessment for critical issues
                quality_assessment = validation_result.get("quality_assessment", {})
                if quality_assessment and "metrics" in quality_assessment:
                    metrics = quality_assessment["metrics"]
                    critical_issues = metrics.get("critical_issues", 0)
                    major_issues = metrics.get("major_issues", 0)
                    
                    if critical_issues > 0:
                        validation_errors.append({
                            "phase": "quality",
                            "type": "critical",
                            "message": f"{critical_issues} critical quality issues detected",
                            "severity": 5
                        })
                    
                    if major_issues > 0:
                        validation_errors.append({
                            "phase": "quality", 
                            "type": "major",
                            "message": f"{major_issues} major quality issues detected",
                            "severity": 3
                        })
                
                # Check overall result for failures
                overall_result = validation_result.get("overall_result", {})
                if overall_result and not overall_result.get("success", True):
                    validation_errors.append({
                        "phase": "overall",
                        "type": "validation_failure",
                        "message": "Overall validation failed",
                        "severity": 4
                    })

                # Filter out false positive errors (like JavaScript keywords flagged as units)
                real_errors = []
                for error in validation_errors:
                    # Skip false positive unit errors from scientific validator
                    if (error.get("phase") == "scientific" and 
                        error.get("type") == "error" and 
                        "Invalid or inappropriate unit" in error.get("message", "") and
                        any(keyword in error.get("message", "").lower() for keyword in 
                            ["const", "material", "value", "pos", "d", "bands", "standard", "color"])):
                        continue
                    real_errors.append(error)

                # Store validation result with improvement info
                validation_result_data = {
                    "attempt": attempt,
                    "quality_score": current_quality_score,
                    "errors_count": len(real_errors),  # Use real errors count
                    "total_errors_detected": len(validation_errors),  # Keep track of total detected
                    "errors": validation_errors,  # Keep all errors for debugging
                    "real_errors": real_errors,  # Store filtered real errors
                    "overall_quality_score": current_quality_score,  # For compatibility
                }

                # Add error fixing information for attempts after the first
                if attempt > 1 and settings.ENABLE_ERROR_FIXING:
                    validation_result_data["error_fixing_applied"] = True
                    validation_result_data["previous_errors_count"] = len(previous_errors) if 'previous_errors' in locals() else 0
                    validation_result_data["errors_fixed"] = fixing_result.get("errors_addressed", 0) if 'fixing_result' in locals() else 0
                    validation_result_data["real_errors_fixed"] = len(real_errors) if real_errors else 0
                else:
                    validation_result_data["error_fixing_applied"] = False
                
                # Add quality enhancement information
                validation_result_data["quality_enhancement_attempts"] = quality_enhancement_attempts
                validation_result_data["max_quality_enhancement_attempts"] = max_quality_enhancement_attempts
                validation_result_data["quality_enhancement_applied"] = 'enhancement_result' in locals()
                if 'enhancement_result' in locals():
                    validation_result_data["quality_improvement"] = enhancement_result.quality_improvement
                    validation_result_data["enhancement_strategy"] = enhancement_result.strategy_used.category.value if enhancement_result.strategy_used else None

                validation_results.append(validation_result_data)

                # Log detailed validation information
                logger.info(
                    f"[{task_id}] Validation attempt {attempt} completed: "
                    f"quality_score={current_quality_score:.2f}, "
                    f"real_errors_count={len(real_errors)}, "
                    f"total_errors_detected={len(validation_errors)}, "
                    f"quality_threshold={settings.QUALITY_SCORE_THRESHOLD}, "
                    f"enable_error_fixing={settings.ENABLE_ERROR_FIXING}, "
                    f"enable_quality_enhancement={settings.ENABLE_QUALITY_ENHANCEMENT}"
                )
                
                if validation_errors:
                    logger.info(f"[{task_id}] Total validation errors detected: {[e.get('message', 'Unknown') for e in validation_errors]}")
                
                if real_errors:
                    logger.info(f"[{task_id}] Real validation errors (after filtering): {[e.get('message', 'Unknown') for e in real_errors]}")
                else:
                    logger.info(f"[{task_id}] No real validation errors found after filtering false positives")

                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    75,
                    f"Quality score: {current_quality_score:.1f} (attempt {attempt})",
                )

                # Check if we should attempt error fixing or quality enhancement
                if real_errors and settings.ENABLE_ERROR_FIXING:
                    logger.info(
                        f"[{task_id}] Error fixing conditions met: "
                        f"real errors found ({len(real_errors)} out of {len(validation_errors)} total), "
                        f"error fixing enabled ({settings.ENABLE_ERROR_FIXING})"
                    )
                    update_task_stage(
                        db,
                        task_id,
                        stage_name,
                        90,
                        f"Attempting error fixing (attempt {attempt})",
                    )

                    # Attempt error fixing with real errors only
                    fixing_result = await enhanced_error_fixing_service.fix_html_errors(
                        current_html_content, real_errors[:10], request.provider
                    )

                    if fixing_result.get("fixed_html"):
                        # Re-validate the fixed content
                        fixed_validation = (
                            await validation_orchestrator.validate_content(
                                html_content=fixing_result["fixed_html"],
                                title="3D Visualization",
                                subject=request.subject,
                                education_level="high school"
                            )
                        )
                        fixed_quality_score = fixed_validation.get(
                            "overall_quality_score", 0
                        )

                        # Use fixed version if it's better
                        if fixed_quality_score > current_quality_score:
                            current_html_content = fixing_result["fixed_html"]
                            current_quality_score = fixed_quality_score
                            # Extract errors from fixed validation result
                            fixed_errors = []
                            fixed_phase_results = fixed_validation.get("phase_results", {})
                            for phase_name, phase_result in fixed_phase_results.items():
                                if phase_result and not phase_result.get("error"):
                                    issues = phase_result.get("issues", [])
                                    for issue in issues:
                                        fixed_errors.append({
                                            "phase": phase_name,
                                            "type": issue.get("type", "unknown"),
                                            "message": issue.get("message", "Unknown error"),
                                            "severity": issue.get("severity", 1)
                                        })
                            validation_errors = fixed_errors
                
                # Check if we should attempt quality enhancement (when few real errors and low quality)
                elif (len(real_errors) < 5 and 
                      current_quality_score < settings.QUALITY_SCORE_THRESHOLD and
                      settings.ENABLE_QUALITY_ENHANCEMENT and
                      quality_enhancement_attempts < max_quality_enhancement_attempts):
                    
                    quality_enhancement_attempts += 1
                    
                    logger.info(
                        f"[{task_id}] Quality enhancement conditions met: "
                        f"few real errors ({len(real_errors)}), "
                        f"low quality ({current_quality_score:.2f} < {settings.QUALITY_SCORE_THRESHOLD}), "
                        f"enhancement enabled ({settings.ENABLE_QUALITY_ENHANCEMENT}), "
                        f"attempt {quality_enhancement_attempts}/{max_quality_enhancement_attempts}"
                    )
                    
                    update_task_stage(
                        db,
                        task_id,
                        stage_name,
                        90,
                        f"Attempting quality enhancement (attempt {quality_enhancement_attempts}/{max_quality_enhancement_attempts})",
                    )

                    # Attempt quality enhancement
                    from app.services.quality_enhancement import QualityEnhancementService
                    quality_enhancement_service = QualityEnhancementService()
                    
                    enhancement_result = await quality_enhancement_service.enhance_html_quality(
                        html_content=current_html_content,
                        current_quality_score=current_quality_score,
                        target_quality_score=settings.QUALITY_SCORE_THRESHOLD,
                        attempt_number=quality_enhancement_attempts,
                        provider=request.provider
                    )

                    if enhancement_result.success and enhancement_result.quality_improvement > 0:
                        # Re-validate the enhanced content
                        enhanced_validation = (
                            await validation_orchestrator.validate_content(
                                html_content=enhancement_result.enhanced_html,
                                title="3D Visualization",
                                subject=request.subject,
                                education_level="high school"
                            )
                        )
                        enhanced_quality_score = enhanced_validation.get(
                            "overall_quality_score", 0
                        )

                        # Use enhanced version if it's better
                        if enhanced_quality_score > current_quality_score:
                            current_html_content = enhancement_result.enhanced_html
                            current_quality_score = enhanced_quality_score
                            # Extract errors from enhanced validation result
                            enhanced_errors = []
                            enhanced_phase_results = enhanced_validation.get("phase_results", {})
                            for phase_name, phase_result in enhanced_phase_results.items():
                                if phase_result and not phase_result.get("error"):
                                    issues = phase_result.get("issues", [])
                                    for issue in issues:
                                        enhanced_errors.append({
                                            "phase": phase_name,
                                            "type": issue.get("type", "unknown"),
                                            "message": issue.get("message", "Unknown error"),
                                            "severity": issue.get("severity", 1)
                                        })
                            validation_errors = enhanced_errors
                            
                            logger.info(
                                f"[{task_id}] Quality enhancement successful: "
                                f"{enhancement_result.quality_improvement:.2f} point improvement "
                                f"using {enhancement_result.strategy_used.category.value if enhancement_result.strategy_used else 'unknown'} strategy"
                            )
                        else:
                            logger.warning(
                                f"[{task_id}] Quality enhancement did not improve score: "
                                f"expected {enhancement_result.new_quality_score:.2f}, "
                                f"got {enhanced_quality_score:.2f}"
                            )
                    else:
                        logger.warning(
                            f"[{task_id}] Quality enhancement failed: {enhancement_result.error_message}"
                        )
                
                # Log when neither error fixing nor quality enhancement is attempted
                if len(real_errors) >= 5 and current_quality_score < settings.QUALITY_SCORE_THRESHOLD:
                    logger.info(
                        f"[{task_id}] Neither error fixing nor quality enhancement attempted: "
                        f"too many real errors ({len(real_errors)} >= 5), "
                        f"low quality ({current_quality_score:.2f} < {settings.QUALITY_SCORE_THRESHOLD}), "
                        f"error fixing enabled ({settings.ENABLE_ERROR_FIXING}), "
                        f"quality enhancement enabled ({settings.ENABLE_QUALITY_ENHANCEMENT})"
                    )
                elif len(real_errors) < 5 and current_quality_score < settings.QUALITY_SCORE_THRESHOLD and quality_enhancement_attempts >= max_quality_enhancement_attempts:
                    logger.info(
                        f"[{task_id}] Quality enhancement max attempts reached: "
                        f"few real errors ({len(real_errors)} < 5), "
                        f"low quality ({current_quality_score:.2f} < {settings.QUALITY_SCORE_THRESHOLD}), "
                        f"quality enhancement attempts exhausted ({quality_enhancement_attempts}/{max_quality_enhancement_attempts})"
                    )
                elif real_errors:
                    logger.info(
                        f"[{task_id}] Error fixing attempted but quality enhancement not triggered: "
                        f"real errors found ({len(real_errors)}), "
                        f"quality score ({current_quality_score:.2f})"
                    )
                elif current_quality_score >= settings.QUALITY_SCORE_THRESHOLD:
                    logger.info(
                        f"[{task_id}] Quality threshold met, no enhancement needed: "
                        f"quality score ({current_quality_score:.2f} >= {settings.QUALITY_SCORE_THRESHOLD})"
                    )

                # Update best version if this is better
                if current_quality_score > best_quality_score:
                    best_quality_score = current_quality_score
                    best_html_content = current_html_content

                complete_task_stage(
                    db,
                    task_id,
                    stage_name,
                    f"Validation complete - Quality: {current_quality_score:.1f}",
                    {
                        "quality_score": current_quality_score,
                        "real_errors_count": len(real_errors),
                        "total_errors_detected": len(validation_errors),
                        "best_so_far": current_quality_score == best_quality_score,
                    },
                )

                # If quality is good enough, break early
                if current_quality_score >= settings.QUALITY_SCORE_THRESHOLD:
                    break

            except Exception as e:
                fail_task_stage(
                    db,
                    task_id,
                    stage_name,
                    f"Validation attempt {attempt} failed: {str(e)}",
                )
                # Continue to next attempt

        # NEW: Post-Validation Quality Enhancement Stage
        if (best_quality_score < settings.QUALITY_SCORE_THRESHOLD and 
            settings.ENABLE_QUALITY_ENHANCEMENT and
            settings.ENABLE_POST_VALIDATION_ENHANCEMENT):
            
            start_task_stage(
                db, 
                task_id, 
                "post_validation_enhancement", 
                "Post-validation quality enhancement"
            )
            
            try:
                logger.info(
                    f"[{task_id}] Starting post-validation quality enhancement: "
                    f"best quality score ({best_quality_score:.2f} < {settings.QUALITY_SCORE_THRESHOLD}), "
                    f"enhancement enabled ({settings.ENABLE_QUALITY_ENHANCEMENT})"
                )
                
                update_task_stage(
                    db,
                    task_id,
                    "post_validation_enhancement",
                    25,
                    "Analyzing content for quality improvement opportunities",
                )

                # Attempt quality enhancement with the best content so far
                from app.services.quality_enhancement import QualityEnhancementService
                quality_enhancement_service = QualityEnhancementService()
                
                # Double-check that enhancement is actually needed
                if best_quality_score >= settings.QUALITY_ENHANCEMENT_SKIP_THRESHOLD:
                    logger.warning(
                        f"[{task_id}] Quality enhancement skipped - score already above skip threshold: "
                        f"{best_quality_score:.2f} >= {settings.QUALITY_ENHANCEMENT_SKIP_THRESHOLD}"
                    )
                    complete_task_stage(
                        db,
                        task_id,
                        "post_validation_enhancement",
                        f"Quality enhancement skipped - score already quite good",
                        {
                            "quality_score": best_quality_score,
                            "enhancement_successful": False,
                            "reason": "Quality score already above skip threshold",
                        },
                    )
                    # Skip to next stage instead of breaking
                    pass
                else:
                    # Proceed with quality enhancement
                    enhancement_result = await quality_enhancement_service.enhance_html_quality(
                        html_content=best_html_content,
                        current_quality_score=best_quality_score,
                        target_quality_score=settings.QUALITY_SCORE_THRESHOLD,
                        attempt_number=1,  # First post-validation attempt
                        provider=request.provider
                    )

                    if enhancement_result.success and enhancement_result.quality_improvement > 0:
                        update_task_stage(
                            db,
                            task_id,
                            "post_validation_enhancement",
                            75,
                            f"Quality enhancement successful: +{enhancement_result.quality_improvement:.2f} points",
                        )

                        # Re-validate the enhanced content
                        enhanced_validation = (
                            await validation_orchestrator.validate_content(
                                html_content=enhancement_result.enhanced_html,
                                title="3D Visualization",
                                subject=request.subject,
                                education_level="high school"
                            )
                        )
                        enhanced_quality_score = enhanced_validation.get(
                            "overall_quality_score", 0
                        )

                        # Use enhanced version if it's better (with minimum improvement threshold)
                        if enhanced_quality_score > (best_quality_score + settings.QUALITY_ENHANCEMENT_MIN_IMPROVEMENT):
                            best_html_content = enhancement_result.enhanced_html
                            best_quality_score = enhanced_quality_score
                            
                            logger.info(
                                f"[{task_id}] Post-validation quality enhancement successful: "
                                f"{enhancement_result.quality_improvement:.2f} point improvement "
                                f"using {enhancement_result.strategy_used.category.value if enhancement_result.strategy_used else 'unknown'} strategy"
                            )
                            
                            complete_task_stage(
                                db,
                                task_id,
                                "post_validation_enhancement",
                                f"Quality enhanced: {best_quality_score:.1f} (+{enhancement_result.quality_improvement:.2f})",
                                {
                                    "quality_score": best_quality_score,
                                    "quality_improvement": enhancement_result.quality_improvement,
                                    "enhancement_strategy": enhancement_result.strategy_used.category.value if enhancement_result.strategy_used else None,
                                    "enhancement_successful": True,
                                },
                            )
                        else:
                            logger.warning(
                                f"[{task_id}] Post-validation quality enhancement did not improve score: "
                                f"expected {enhancement_result.new_quality_score:.2f}, "
                                f"got {enhanced_quality_score:.2f}"
                            )
                            complete_task_stage(
                                db,
                                task_id,
                                "post_validation_enhancement",
                                f"Quality enhancement attempted but no improvement",
                                {
                                    "quality_score": best_quality_score,
                                    "enhancement_successful": False,
                                    "reason": "No score improvement after enhancement",
                                },
                            )
                    else:
                        logger.warning(
                            f"[{task_id}] Post-validation quality enhancement failed: {enhancement_result.error_message}"
                        )
                        complete_task_stage(
                            db,
                            task_id,
                            "post_validation_enhancement",
                            f"Quality enhancement failed",
                            {
                                "quality_score": best_quality_score,
                                "enhancement_successful": False,
                                "error": enhancement_result.error_message,
                            },
                        )
                    
            except Exception as e:
                logger.error(f"[{task_id}] Post-validation quality enhancement failed: {str(e)}")
                fail_task_stage(
                    db,
                    task_id,
                    "post_validation_enhancement",
                    f"Post-validation quality enhancement failed: {str(e)}",
                )
        else:
            logger.info(
                f"[{task_id}] Post-validation quality enhancement skipped: "
                f"quality threshold met ({best_quality_score:.2f} >= {settings.QUALITY_SCORE_THRESHOLD}) "
                f"or enhancement disabled ({not settings.ENABLE_QUALITY_ENHANCEMENT}) "
                f"or post-validation enhancement disabled ({not settings.ENABLE_POST_VALIDATION_ENHANCEMENT})"
            )

        # Stage: Result Preparation
        start_task_stage(db, task_id, "result_preparation", "Preparing final result")

        try:
            # Prepare final result
            result = {
                "html_content": best_html_content,
                "quality_score": best_quality_score,
                "validation_attempts": len(validation_results),
                "validation_results": validation_results,
                "provider": request.provider,
                "topic": request.topic,
                "subject": request.subject,
                "generation_time": time.time(),  # Can be calculated properly
                "total_stages_completed": len(
                    [s for s in VISUALIZATION_STAGES if s != "finalization"]
                ),
            }

            update_task_stage(db, task_id, "result_preparation", 50, "Storing result")

            # Store result in task
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if task:
                task.result = result  # type: ignore
                db.commit()

            complete_task_stage(
                db, task_id, "result_preparation", "Result prepared successfully"
            )

        except Exception as e:
            fail_task_stage(
                db,
                task_id,
                "result_preparation",
                f"Result preparation failed: {str(e)}",
            )
            return

        # Stage: Finalization
        start_task_stage(db, task_id, "finalization", "Finalizing task")

        try:
            # Complete the entire task
            complete_task(db, task_id, result)

            # Create history entry for successful generation
            try:
                generation_time = time.time() - start_time

                # Create prompt entry if needed (optional)
                prompt_id = _create_prompt_entry(db, request.model_dump(), user_id)

                # Create comprehensive history entry using helper function
                history_entry = _create_history_entry_data(
                    request=request,
                    html_content=best_html_content,
                    quality_score=best_quality_score,
                    generation_time=generation_time,
                    prompt_id=prompt_id,
                    user_id=user_id,
                )

                created_entry = create_history_entry(db, history_entry)
                logger.info(f"[{task_id}] Created history entry: {created_entry.id}")

                # Add history entry ID to task result metadata
                if "metadata" not in result:
                    result["metadata"] = {}
                result["metadata"]["history_entry_id"] = created_entry.id

            except Exception as history_error:
                logger.warning(
                    f"[{task_id}] Failed to create history entry: {history_error}"
                )
                # Rollback the session to handle any database errors
                try:
                    db.rollback()
                except Exception as rollback_error:
                    logger.error(f"[{task_id}] Failed to rollback session: {rollback_error}")
                # Don't fail the entire task for history creation issues

            complete_task_stage(
                db, task_id, "finalization", "Task completed successfully"
            )

            logger.info(f"[{task_id}] Visualization generation completed successfully")

        except Exception as e:
            fail_task_stage(
                db, task_id, "finalization", f"Finalization failed: {str(e)}"
            )

    except Exception as e:
        logger.error(f"[{task_id}] Unexpected error in task processing: {str(e)}")
        # Rollback the session before updating task status
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"[{task_id}] Failed to rollback session: {rollback_error}")
        
        try:
            update_task_status(db, task_id, "failed", f"Unexpected error: {str(e)}")
        except Exception as status_error:
            logger.error(f"[{task_id}] Failed to update task status: {status_error}")
    finally:
        db.close()


async def _generate_with_provider(prompt: str, provider: str) -> str:
    """Generate visualization with specified provider."""
    from app.utils.llm_utils import generate_with_provider
    
    result = await generate_with_provider(prompt, provider)
    if not result:
        raise ValueError(f"No response from {provider}")
    return result


def _extract_validation_errors(
    validation_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Extract validation errors from validation result."""
    errors = []

    # Extract different types of errors
    html_errors = validation_result.get("html_validation", {}).get("errors", [])
    scientific_errors = validation_result.get("scientific_validation", {}).get(
        "errors", []
    )
    realism_errors = validation_result.get("realism_validation", {}).get("errors", [])
    runtime_errors = validation_result.get("runtime_validation", {}).get("errors", [])

    # Combine all errors
    all_error_lists = [html_errors, scientific_errors, realism_errors, runtime_errors]
    error_types = ["html", "scientific", "realism", "runtime"]

    for error_list, error_type in zip(all_error_lists, error_types):
        for error in error_list:
            if isinstance(error, dict):
                errors.append(
                    {
                        "type": error_type,
                        "severity": error.get("severity", "medium"),
                        "message": error.get("message", str(error)),
                        "location": error.get("location", ""),
                        "suggestion": error.get("suggestion", ""),
                    }
                )
            else:
                errors.append(
                    {
                        "type": error_type,
                        "severity": "medium",
                        "message": str(error),
                        "location": "",
                        "suggestion": "",
                    }
                )

    return errors


def _create_prompt_entry(db: Session, request_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[int]:
    """Create a prompt entry in the database."""
    try:
        # Extract config data if available
        config = request_data.get("config", {})
        
        prompt = create_prompt(
            db=db,
            subject=request_data.get("subject", "physics"),
            topic=request_data.get("topic", ""),
            content=json.dumps(request_data),
            key_concepts=config.get("key_concepts") if config else None,
            education_level=config.get("education_level") if config else None,
            learning_objectives=config.get("learning_objectives") if config else None,
            interactive_features=config.get("interactive_features") if config else None,
            user_id=user_id,
        )
        # Ensure we return the integer ID, not the Prompt object
        if hasattr(prompt, 'id'):
            return int(prompt.id)
        else:
            logger.error(f"Prompt object has no id attribute: {type(prompt)}")
            return None
    except Exception as e:
        logger.error(f"Error creating prompt entry: {e}")
        return None


def _create_history_entry_data(
    request: GenerateRequest,
    html_content: str,
    quality_score: float,
    generation_time: float,
    prompt_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create comprehensive history entry data with safe config extraction."""

    def safe_json_dumps(data, default="[]"):
        """Safely serialize data to JSON."""
        try:
            if data is None:
                return default
            # If data is already a string that looks like JSON, return it as is
            if isinstance(data, str):
                # Check if it's already a JSON string
                try:
                    json.loads(data)
                    return data  # Already valid JSON, return as is
                except json.JSONDecodeError:
                    # Not JSON, continue with normal processing
                    pass
            if hasattr(data, "model_dump"):
                return json.dumps(data.model_dump())
            elif isinstance(data, list):
                return json.dumps(
                    [
                        item.model_dump() if hasattr(item, "model_dump") else item
                        for item in data
                    ]
                )
            elif isinstance(data, dict):
                return json.dumps(data)
            else:
                return json.dumps(data)
        except Exception as e:
            logger.warning(f"Failed to serialize data to JSON: {e}, data type: {type(data)}")
            return default

    history_entry = {
        "id": str(uuid.uuid4()),
        "prompt_id": prompt_id,
        "user_id": user_id,
        "user_query": request.topic,
        "response": html_content,
        "provider_id": None,  # TODO: Map provider string to provider_id
        "generation_time": generation_time,
        "created_at": datetime.utcnow(),
    }

    # Safely extract config data if available
    if request.config:
        try:
            config = request.config
            logger.info(f"Extracting config data for history: config type={type(config)}")
            
            # Debug: Log the actual values being extracted
            # Handle both Pydantic models and dictionaries
            if hasattr(config, "components"):
                # Pydantic model
                components = getattr(config, "components", None)
                materials = getattr(config, "materials", None)
                lights = getattr(config, "lights", None)
                intro_narration = getattr(config, "intro_narration_texts", None)
                supporting_narration = getattr(config, "supporting_narration_texts", None)
            else:
                # Dictionary
                components = config.get("components", None)
                materials = config.get("materials", None)
                lights = config.get("lights", None)
                intro_narration = config.get("intro_narration_texts", None)
                supporting_narration = config.get("supporting_narration_texts", None)
            
            logger.info(f"Config data extracted: components={type(components)}, materials={type(materials)}, lights={type(lights)}, intro_narration={type(intro_narration)}")
            logger.info(f"Components value: {components}")
            logger.info(f"Materials value: {materials}")
            logger.info(f"Lights value: {lights}")
            logger.info(f"Intro narration value: {intro_narration}")
            logger.info(f"Supporting narration value: {supporting_narration}")
            
            # Test safe_json_dumps directly
            components_json = safe_json_dumps(components, "[]")
            materials_json = safe_json_dumps(materials, "[]")
            lights_json = safe_json_dumps(lights, "[]")
            intro_narration_json = safe_json_dumps(intro_narration, "[]")
            supporting_narration_json = safe_json_dumps(supporting_narration, "[]")
            
            logger.info(f"JSON serialized: components={components_json[:100]}..., materials={materials_json[:100]}..., lights={lights_json[:100]}...")
            logger.info(f"JSON serialized: intro_narration={intro_narration_json[:100]}..., supporting_narration={supporting_narration_json[:100]}...")
            
            history_entry.update(
                {
                    # Component and material fields
                    "components": components_json,
                    "materials": materials_json,
                    "lights": lights_json,
                    
                    # Renderer and animation settings
                    "render_settings": safe_json_dumps(
                        config.renderer if hasattr(config, "renderer") else config.get("renderer", None), "{}"
                    ),
                    "animation_speed": config.animation_speed if hasattr(config, "animation_speed") else config.get("animation_speed", 1.0),
                    
                    # Narration texts
                    "intro_narration_texts": intro_narration_json,
                    "supporting_narration_texts": supporting_narration_json,
                    
                    # Scene description
                    "scene_description": config.scene_description if hasattr(config, "scene_description") else config.get("scene_description", None),
                }
            )
            
            logger.info(f"History entry updated with config data: components={history_entry.get('components')[:100]}...")
        except Exception as e:
            logger.warning(f"Failed to extract config data for history: {e}")
            import traceback
            logger.warning(f"Traceback: {traceback.format_exc()}")
    else:
        logger.warning("No config found in request for history entry")

    return history_entry
