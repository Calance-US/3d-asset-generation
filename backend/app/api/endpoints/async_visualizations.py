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

from app.config.settings import settings
from app.database.database import create_history_entry, create_prompt, get_db
from app.models import AsyncTask, AsyncTaskStage
from app.schemas.schemas import GenerateRequest
from app.services.error_fixing.enhanced_error_fixing_service import (
    enhanced_error_fixing_service,
)
from app.services.error_fixing.error_fixing_service import ErrorFixingService
from app.services.prompt_generator import PromptGenerator
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.services.validation.simple_orchestrator import SimpleValidationOrchestrator
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


# Define stage names for visualization generation
VISUALIZATION_STAGES = [
    "initialization",
    "context_retrieval",
    "prompt_generation",
    "llm_generation",
    "validation_attempt_1",
    "validation_attempt_2",
    "validation_attempt_3",
    "validation_attempt_4",
    "result_preparation",
    "finalization",
]


router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
prompt_generator = PromptGenerator()
validation_orchestrator = SimpleValidationOrchestrator()
error_fixing_service = ErrorFixingService()


# Database-backed task management functions
def create_async_task(
    db: Session,
    task_type: str,
    request_data: Dict[str, Any],
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
        request_data=request_data,
        progress_percentage=0,
        total_stages=len(VISUALIZATION_STAGES),
        expires_at=datetime.utcnow() + timedelta(minutes=timeout_minutes),
    )

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
            metadata={
                "provider": request.provider,
                "topic": request.topic,
                "subject": request.subject,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

        # Start background processing
        background_tasks.add_task(_process_visualization_generation, task_id, request)

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


async def _process_visualization_generation(task_id: str, request: GenerateRequest):
    """Process visualization generation in background."""
    db = next(get_db())
    start_time = time.time()  # Track generation time
    try:
        start_task_stage(
            db, task_id, "initialization", "Starting visualization generation"
        )

        logger.info(f"[{task_id}] Starting visualization generation")
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

        # Validation attempts
        best_quality_score = 0
        best_html_content = html_content
        validation_results = []

        for attempt in range(1, 5):  # 4 validation attempts
            stage_name = f"validation_attempt_{attempt}"
            start_task_stage(db, task_id, stage_name, f"Validation attempt {attempt}")

            try:
                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    25,
                    f"Validating content (attempt {attempt})",
                )

                # Perform validation
                validation_result = await validation_orchestrator.validate_html_content(
                    html_content
                )

                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    50,
                    f"Processing validation results (attempt {attempt})",
                )

                current_quality_score = validation_result.get(
                    "overall_quality_score", 0
                )
                validation_errors = validation_result.get("errors", [])

                # Store validation result
                validation_results.append(
                    {
                        "attempt": attempt,
                        "quality_score": current_quality_score,
                        "errors_count": len(validation_errors),
                        "errors": validation_errors,
                    }
                )

                update_task_stage(
                    db,
                    task_id,
                    stage_name,
                    75,
                    f"Quality score: {current_quality_score:.1f} (attempt {attempt})",
                )

                # Check if we should attempt error fixing
                if validation_errors and settings.ENABLE_ERROR_FIXING:
                    update_task_stage(
                        db,
                        task_id,
                        stage_name,
                        90,
                        f"Attempting error fixing (attempt {attempt})",
                    )

                    # Attempt error fixing
                    fixing_result = enhanced_error_fixing_service.fix_html_errors(
                        html_content, validation_errors[:10], request.provider
                    )

                    if fixing_result.get("fixed_html"):
                        # Re-validate the fixed content
                        fixed_validation = (
                            await validation_orchestrator.validate_html_content(
                                fixing_result["fixed_html"]
                            )
                        )
                        fixed_quality_score = fixed_validation.get(
                            "overall_quality_score", 0
                        )

                        # Use fixed version if it's better
                        if fixed_quality_score > current_quality_score:
                            html_content = fixing_result["fixed_html"]
                            current_quality_score = fixed_quality_score
                            validation_errors = fixed_validation.get("errors", [])

                # Update best version if this is better
                if current_quality_score > best_quality_score:
                    best_quality_score = current_quality_score
                    best_html_content = html_content

                complete_task_stage(
                    db,
                    task_id,
                    stage_name,
                    f"Validation complete - Quality: {current_quality_score:.1f}",
                    {
                        "quality_score": current_quality_score,
                        "errors_count": len(validation_errors),
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
                prompt_id = _create_prompt_entry(db, request.model_dump())

                # Create comprehensive history entry using helper function
                history_entry = _create_history_entry_data(
                    request=request,
                    html_content=best_html_content,
                    quality_score=best_quality_score,
                    generation_time=generation_time,
                    prompt_id=prompt_id,
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
        update_task_status(db, task_id, "failed", f"Unexpected error: {str(e)}")
    finally:
        db.close()


async def _generate_with_provider(prompt: str, provider: str) -> str:
    """Generate visualization with specified provider."""
    try:
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            generated_text = response.choices[0].message.content
            if not generated_text:
                raise ValueError("No response from OpenAI")
            return generated_text
        elif provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API key not configured")
            import google.generativeai as genai

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            response = await model.generate_content_async(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
            if not response.text:
                raise ValueError("No response from Gemini")
            return response.text
        elif provider == "ollama":
            # For now, fallback to OpenAI if Ollama is requested but not implemented
            logger.warning("Ollama provider not implemented, falling back to OpenAI")
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured for Ollama fallback")
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            generated_text = response.choices[0].message.content
            if not generated_text:
                raise ValueError("No response from OpenAI (Ollama fallback)")
            return generated_text
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        logger.error(f"Error generating with provider {provider}: {e}")
        raise


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


def _create_prompt_entry(db: Session, request_data: Dict[str, Any]) -> Optional[int]:
    """Create a prompt entry in the database."""
    try:
        prompt_id = create_prompt(
            db=db,
            subject=request_data.get("subject", "physics"),
            topic=request_data.get("topic", ""),
            content=json.dumps(request_data),
        )
        return prompt_id
    except Exception as e:
        logger.error(f"Error creating prompt entry: {e}")
        return None


def _create_history_entry_data(
    request: GenerateRequest,
    html_content: str,
    quality_score: float,
    generation_time: float,
    prompt_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create comprehensive history entry data with safe config extraction."""

    def safe_json_dumps(data, default=None):
        """Safely serialize data to JSON."""
        try:
            if data is None:
                return default
            if hasattr(data, "model_dump"):
                return json.dumps(data.model_dump())
            elif isinstance(data, list):
                return json.dumps(
                    [
                        item.model_dump() if hasattr(item, "model_dump") else item
                        for item in data
                    ]
                )
            else:
                return json.dumps(data)
        except Exception:
            return default

    history_entry = {
        "id": str(uuid.uuid4()),
        "prompt_id": prompt_id,
        "user_query": request.topic,
        "response": html_content,
        "provider": request.provider,
        "generation_time": generation_time,
        "created_at": datetime.utcnow(),
    }

    # Safely extract config data if available
    if request.config:
        try:
            config = request.config
            history_entry.update(
                {
                    "components": safe_json_dumps(getattr(config, "components", None)),
                    "materials": safe_json_dumps(getattr(config, "materials", None)),
                    "lights": safe_json_dumps(getattr(config, "lights", None)),
                    "render_settings": safe_json_dumps(
                        getattr(config, "renderer", None)
                    ),
                    "animation_speed": getattr(config, "animation_speed", 1.0),
                    "intro_narration_texts": safe_json_dumps(
                        getattr(config, "intro_narration_texts", None)
                    ),
                    "supporting_narration_texts": safe_json_dumps(
                        getattr(config, "supporting_narration_texts", None)
                    ),
                    "scene_description": getattr(config, "scene_description", None),
                }
            )
        except Exception as e:
            logger.warning(f"Failed to extract config data for history: {e}")

    return history_entry
