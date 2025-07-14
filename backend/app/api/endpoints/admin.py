import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from app.auth.dependencies import get_admin_user, get_current_user
from app.database.database import get_db
from app.models import (
    AsyncTask,
    AsyncTaskStage,
    HistoryEntry,
    SnippetMetadata,
    User,
    ValidationError,
    Visualization,
    ChatSession,
    ChatMessage,
)
from app.services.error_fixing.validation_error_service import validation_error_service
from app.services.rag import get_vector_store
from app.services.validation.simple_orchestrator import SimpleValidationOrchestrator
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.schemas.schemas import ChatFixRequest, ChatFixResponse, ChatMessageRequest, ChatMessageResponse, ChatSessionSchema, ChatMessageSchema
import uuid
from app.utils.llm_utils import generate_with_provider
from app.api.endpoints.async_visualizations import _extract_validation_errors
from app.services.error_fixing.enhanced_error_fixing_service import enhanced_error_fixing_service
from app.services.validation.validation_orchestrator import ValidationOrchestrator

router = APIRouter()

# Initialize validation system components for metrics
validation_orchestrator = ValidationOrchestrator()

def validate_html(html):
    # Simulate validation
    return {"html_validation": {"errors": []}}


@router.get("/vector-store-stats", response_model=Dict[str, Any])
async def get_vector_store_stats(
    admin_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """Get statistics about the vector store (Qdrant or other)."""
    vector_store = get_vector_store()
    db = next(get_db())
    logger = logging.getLogger("vector_store_stats")
    try:
        stats: Dict[str, Any] = {
            "total_vectors": 0,
            "dimension": 0,
            "index_type": "Qdrant",
            "snippet_types": {},
            "topics": {},
            "education_levels": {},
        }
        # Use Qdrant count API for total vectors
        try:
            logger.info(f"Qdrant collection name: {vector_store.collection_name}")
            logger.info(
                f"Qdrant client host: {getattr(vector_store.client, 'host', 'unknown')}, port: {getattr(vector_store.client, 'port', 'unknown')}"
            )
            info = vector_store.client.get_collection(vector_store.collection_name)
            logger.info(f"Qdrant get_collection result: {info}")
            count_result = vector_store.client.count(
                collection_name=vector_store.collection_name, exact=True
            )
            logger.info(f"Qdrant count result: {count_result}")
            stats["total_vectors"] = count_result.count
            stats["dimension"] = info.config.params.vectors.size
        except Exception as e:
            logger.error(f"Error querying Qdrant: {e}")
        # Get all metadata from DB
        all_metadata = db.query(SnippetMetadata).all()
        for metadata in all_metadata:
            snippet_type = getattr(metadata, "snippet_type", "unknown") or "unknown"
            stats["snippet_types"][snippet_type] = (
                stats["snippet_types"].get(snippet_type, 0) + 1
            )
            topic = getattr(metadata, "topic", "unknown") or "unknown"
            stats["topics"][topic] = stats["topics"].get(topic, 0) + 1
            level = getattr(metadata, "education_level", "unknown") or "unknown"
            stats["education_levels"][level] = (
                stats["education_levels"].get(level, 0) + 1
            )
        return stats
    finally:
        db.close()


@router.get("/vector-store-vectors", response_model=List[Dict[str, Any]])
async def get_vector_store_vectors(
    skip: int = 0,
    limit: int = 100,
    snippet_type: Optional[str] = None,
    topic: Optional[str] = None,
    education_level: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
) -> List[Dict[str, Any]]:
    """Get paginated vectors from the vector store with optional filtering."""
    vector_store = get_vector_store()
    db = next(get_db())
    try:
        # Build query
        query = db.query(SnippetMetadata)
        if snippet_type:
            query = query.filter(SnippetMetadata.snippet_type == snippet_type)
        if topic:
            query = query.filter(SnippetMetadata.topic == topic)
        if education_level:
            query = query.filter(SnippetMetadata.education_level == education_level)
        # Apply pagination
        paginated_metadata = query.offset(skip).limit(limit).all()
        # Format response
        return [
            {
                "id": m.id,
                "faiss_id": m.faiss_id,
                "snippet_type": m.snippet_type,
                "topic": m.topic,
                "education_level": m.education_level,
                "summary": m.summary,
                "filename": m.filename,
            }
            for m in paginated_metadata
        ]
    finally:
        db.close()


@router.get("/admin/generation-stats", response_model=Dict[str, Any])
async def get_generation_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """Get statistics about visualization generation times."""
    try:
        # Get all generation times
        generation_times = (
            db.query(HistoryEntry.generation_time)
            .filter(HistoryEntry.generation_time.isnot(None))
            .all()
        )
        if not generation_times:
            return {"mean": 0, "median": 0, "p95": 0, "p99": 0, "total_generations": 0}
        # Convert to numpy array for calculations
        times = np.array([t[0] for t in generation_times])
        return {
            "mean": float(np.mean(times)),
            "median": float(np.median(times)),
            "p95": float(np.percentile(times, 95)),
            "p99": float(np.percentile(times, 99)),
            "total_generations": len(times),
        }
    except Exception as e:
        logger = logging.getLogger("generation_stats")
        logger.error(
            "Error getting generation stats",
            extra={
                "action": "get_generation_stats",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation-metrics")
async def get_validation_metrics(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """Get comprehensive validation system metrics from real database data."""
    try:
        # Get real validation error statistics from database
        from sqlalchemy import text

        # Basic validation metrics
        total_errors_query = text("SELECT COUNT(*) FROM validation_errors")
        total_errors = db.execute(total_errors_query).scalar()

        # Quality score distribution
        quality_stats_query = text("""
            SELECT
                AVG(quality_score::numeric) as avg_quality,
                MIN(quality_score::numeric) as min_quality,
                MAX(quality_score::numeric) as max_quality,
                COUNT(DISTINCT prompt_id) as total_prompts
            FROM validation_errors
            WHERE quality_score IS NOT NULL
        """)
        quality_stats = db.execute(quality_stats_query).fetchone()

        # Attempt success metrics
        attempt_success_query = text("""
            SELECT
                attempt_number,
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_errors,
                AVG(quality_score::numeric) as avg_quality_score
            FROM validation_errors
            GROUP BY attempt_number
            ORDER BY attempt_number
        """)
        attempt_stats = db.execute(attempt_success_query).fetchall()

        # Provider performance
        provider_stats_query = text("""
            SELECT
                provider,
                COUNT(*) as total_errors,
                AVG(quality_score::numeric) as avg_quality,
                COUNT(DISTINCT prompt_id) as unique_prompts
            FROM validation_errors
            GROUP BY provider
        """)
        provider_stats = db.execute(provider_stats_query).fetchall()

        # Phase error distribution
        phase_stats_query = text("""
            SELECT
                phase,
                COUNT(*) as error_count,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_count
            FROM validation_errors
            GROUP BY phase
            ORDER BY error_count DESC
        """)
        phase_stats = db.execute(phase_stats_query).fetchall()

        # Recent activity (last 24 hours)
        recent_activity_query = text("""
            SELECT
                COUNT(*) as recent_errors,
                COUNT(DISTINCT prompt_id) as recent_prompts,
                AVG(quality_score::numeric) as recent_avg_quality
            FROM validation_errors
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        recent_activity = db.execute(recent_activity_query).fetchone()

        # Calculate improvement rates
        improvement_data = []
        for row in attempt_stats:
            improvement_data.append(
                {
                    "attempt": row[0],
                    "total_attempts": row[1],
                    "critical_errors": row[2],
                    "avg_quality_score": float(row[3]) if row[3] else 0.0,
                }
            )

        # Calculate overall success rate
        max_attempts = max([row[0] for row in attempt_stats]) if attempt_stats else 1
        prompts_with_max_attempts = sum(
            1 for row in attempt_stats if row[0] == max_attempts
        )
        total_unique_prompts = quality_stats[3] if quality_stats else 1
        success_rate = (
            (
                (total_unique_prompts - prompts_with_max_attempts)
                / total_unique_prompts
                * 100
            )
            if total_unique_prompts > 0
            else 0
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "validation_performance": {
                "total_validation_errors": total_errors,
                "unique_prompts_validated": quality_stats[3] if quality_stats else 0,
                "success_rate": round(success_rate, 2),
                "avg_attempts_per_prompt": round(total_errors / quality_stats[3], 2)
                if quality_stats and quality_stats[3] > 0
                else 0,
                "attempt_breakdown": improvement_data,
            },
            "quality_distribution": {
                "average_score": round(float(quality_stats[0]), 2)
                if quality_stats and quality_stats[0]
                else 0.0,
                "min_score": round(float(quality_stats[1]), 2)
                if quality_stats and quality_stats[1]
                else 0.0,
                "max_score": round(float(quality_stats[2]), 2)
                if quality_stats and quality_stats[2]
                else 0.0,
                "score_improvement_trend": [
                    {"attempt": row["attempt"], "avg_score": row["avg_quality_score"]}
                    for row in improvement_data
                ],
            },
            "provider_performance": [
                {
                    "provider": row[0],
                    "total_errors": row[1],
                    "avg_quality": round(float(row[2]), 2) if row[2] else 0.0,
                    "unique_prompts": row[3],
                }
                for row in provider_stats
            ],
            "phase_error_distribution": [
                {
                    "phase": row[0],
                    "total_errors": row[1],
                    "critical_errors": row[2],
                    "error_rate": round(row[2] / row[1] * 100, 2) if row[1] > 0 else 0,
                }
                for row in phase_stats
            ],
            "recent_activity_24h": {
                "recent_errors": recent_activity[0] if recent_activity else 0,
                "recent_prompts": recent_activity[1] if recent_activity else 0,
                "recent_avg_quality": round(float(recent_activity[2]), 2)
                if recent_activity and recent_activity[2]
                else 0.0,
            },
            "system_health": {
                "overall_success_rate": round(success_rate, 2),
                "average_quality_score": round(float(quality_stats[0]), 2)
                if quality_stats and quality_stats[0]
                else 0.0,
                "improvement_rate": round(
                    improvement_data[-1]["avg_quality_score"]
                    - improvement_data[0]["avg_quality_score"],
                    2,
                )
                if len(improvement_data) > 1
                else 0.0,
                "total_validations": total_errors,
                "active_validation_enabled": True,
            },
        }

    except Exception as e:
        logger = logging.getLogger("validation_metrics")
        logger.error(f"Error getting validation metrics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get validation metrics: {str(e)}"
        )


@router.get("/validation-error-stats")
async def get_validation_error_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """Get validation error statistics and retry metrics."""
    try:
        # Get comprehensive error statistics
        error_stats = validation_error_service.get_error_statistics(db, days)

        # Get retry success metrics
        retry_metrics = validation_error_service.get_retry_success_metrics(db, days)

        # Get most common errors
        common_errors = validation_error_service.get_most_common_errors(
            db, limit=10, days=days
        )

        return {
            "period_days": days,
            "error_statistics": error_stats,
            "retry_metrics": retry_metrics,
            "most_common_errors": common_errors,
            "summary": {
                "total_errors": error_stats.get("total_errors", 0),
                "retry_success_rate": retry_metrics.get("retry_rate", 0),
                "average_attempts": retry_metrics.get("average_attempts", 1.0),
                "quality_improvement": "Available in error_statistics",
            },
        }

    except Exception as e:
        logger = logging.getLogger("validation_error_stats")
        logger.error(f"Error getting validation error stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get validation error statistics"
        )


@router.get("/error-fixing-performance")
async def get_error_fixing_performance(
    days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)
):
    """Get detailed error fixing performance metrics."""
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import func

        since_date = datetime.utcnow() - timedelta(days=days)

        # Get visualization success rates with retry information
        visualization_metrics = (
            db.query(
                func.count(Visualization.id).label("total_visualizations"),
                func.avg(Visualization.generation_attempts).label("avg_attempts"),
                func.count(Visualization.id)
                .filter(Visualization.generation_attempts > 1)
                .label("retry_count"),
                func.avg(Visualization.final_quality_score).label("avg_quality_score"),
            )
            .filter(Visualization.created_at >= since_date)
            .first()
        )

        # Get error distribution by phase
        phase_distribution = (
            db.query(
                ValidationError.phase,
                func.count(ValidationError.id).label("count"),
                func.avg(ValidationError.quality_score).label("avg_quality"),
            )
            .filter(ValidationError.created_at >= since_date)
            .group_by(ValidationError.phase)
            .all()
        )

        # Get success rate by provider
        provider_performance = (
            db.query(
                ValidationError.provider,
                func.count(ValidationError.id).label("error_count"),
                func.avg(ValidationError.quality_score).label("avg_quality"),
            )
            .filter(ValidationError.created_at >= since_date)
            .group_by(ValidationError.provider)
            .all()
        )

        return {
            "period_days": days,
            "overall_metrics": {
                "total_visualizations": visualization_metrics.total_visualizations or 0,
                "average_attempts": float(visualization_metrics.avg_attempts)
                if visualization_metrics.avg_attempts
                else 1.0,
                "retry_rate": (
                    visualization_metrics.retry_count
                    / visualization_metrics.total_visualizations
                    * 100
                )
                if visualization_metrics.total_visualizations > 0
                else 0,
                "average_quality_score": float(visualization_metrics.avg_quality_score)
                if visualization_metrics.avg_quality_score
                else 0.0,
            },
            "phase_distribution": [
                {
                    "phase": phase.phase,
                    "error_count": phase.count,
                    "avg_quality_score": float(phase.avg_quality)
                    if phase.avg_quality
                    else None,
                }
                for phase in phase_distribution
            ],
            "provider_performance": [
                {
                    "provider": provider.provider,
                    "error_count": provider.error_count,
                    "avg_quality_score": float(provider.avg_quality)
                    if provider.avg_quality
                    else None,
                }
                for provider in provider_performance
            ],
        }

    except Exception as e:
        logger = logging.getLogger("error_fixing_performance")
        logger.error(f"Error getting error fixing performance: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get error fixing performance metrics"
        )


@router.post("/cleanup-old-errors")
async def cleanup_old_validation_errors(
    days: int = Query(default=90, ge=30, le=365), db: Session = Depends(get_db)
):
    """Clean up old validation errors to manage database size."""
    try:
        deleted_count = validation_error_service.cleanup_old_errors(db, days)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "retention_days": days,
            "message": f"Successfully cleaned up {deleted_count} validation errors older than {days} days",
        }

    except Exception as e:
        logger = logging.getLogger("cleanup_errors")
        logger.error(f"Error cleaning up old errors: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to cleanup old validation errors"
        )


@router.get("/error-statistics")
async def get_error_statistics(
    days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)
):
    """Get error statistics for the specified time period."""
    try:
        stats = validation_error_service.get_error_statistics(db, days)
        return stats
    except Exception as e:
        logger = logging.getLogger("error_statistics")
        logger.error(f"Error getting error statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get error statistics")


@router.get("/common-errors")
async def get_common_errors(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get the most common validation errors."""
    try:
        errors = validation_error_service.get_most_common_errors(db, limit, days)
        return errors
    except Exception as e:
        logger = logging.getLogger("common_errors")
        logger.error(f"Error getting common errors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get common errors")


@router.get("/retry-metrics")
async def get_retry_metrics(
    days: int = Query(default=30, ge=1, le=365), db: Session = Depends(get_db)
):
    """Get retry success metrics."""
    try:
        metrics = validation_error_service.get_retry_success_metrics(db, days)
        return metrics
    except Exception as e:
        logger = logging.getLogger("retry_metrics")
        logger.error(f"Error getting retry metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get retry metrics")


# Task Manager API Endpoints


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of tasks to return"
    ),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get list of async tasks with optional filtering."""
    logger = logging.getLogger("get_tasks")

    try:
        # Build query
        query = db.query(AsyncTask)

        # Apply filters
        if status:
            query = query.filter(AsyncTask.status == status)
        if task_type:
            query = query.filter(AsyncTask.task_type == task_type)

        # Order by creation date (newest first) and limit
        tasks = query.order_by(AsyncTask.created_at.desc()).limit(limit).all()

        # Format response
        result = []
        for task in tasks:
            result.append(
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "progress_percentage": task.progress_percentage or 0,
                    "current_stage": task.current_stage,
                    "created_at": task.created_at.isoformat()
                    if task.created_at
                    else None,
                    "started_at": task.started_at.isoformat()
                    if task.started_at
                    else None,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                    "expires_at": task.expires_at.isoformat()
                    if task.expires_at
                    else None,
                }
            )

        logger.info(f"Retrieved {len(result)} tasks")
        return result

    except Exception as e:
        logger.error(f"Error retrieving tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task_details(
    task_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information about a specific task."""
    logger = logging.getLogger("get_task_details")

    try:
        # Get task
        task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get task stages
        stages = (
            db.query(AsyncTaskStage)
            .filter(AsyncTaskStage.task_id == task_id)
            .order_by(AsyncTaskStage.order_index)
            .all()
        )

        # Format stages
        formatted_stages = []
        for stage in stages:
            stage_data = {
                "name": stage.name,
                "status": stage.status,
                "order_index": stage.order_index,
                "progress_percentage": stage.progress_percentage or 0,
                "message": stage.message,
                "started_at": stage.started_at.isoformat()
                if stage.started_at
                else None,
                "completed_at": stage.completed_at.isoformat()
                if stage.completed_at
                else None,
                "error_message": stage.error_message,
            }

            # Include details if available
            if stage.details:
                stage_data["details"] = stage.get_details()

            formatted_stages.append(stage_data)

        # Format response
        result = {
            "id": task.id,
            "task_type": task.task_type,
            "status": task.status,
            "progress_percentage": task.progress_percentage or 0,
            "current_stage": task.current_stage,
            "total_stages": task.total_stages or 1,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
            "expires_at": task.expires_at.isoformat() if task.expires_at else None,
            "error_message": task.error_message,
            "stages": formatted_stages,
        }

        # Include request data if available
        if task.request_data:
            result["request_data"] = task.get_request_data()

        # Include result if available
        if task.result:
            result["result"] = task.get_result()

        logger.info(f"Retrieved details for task {task_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task details for {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task details")


@router.get("/tasks/{task_id}/stages", response_model=List[Dict[str, Any]])
async def get_task_stages(
    task_id: str, db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all stages for a specific task."""
    logger = logging.getLogger("get_task_stages")

    try:
        # Verify task exists
        task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get stages
        stages = (
            db.query(AsyncTaskStage)
            .filter(AsyncTaskStage.task_id == task_id)
            .order_by(AsyncTaskStage.order_index)
            .all()
        )

        # Format response
        result = []
        for stage in stages:
            stage_data = {
                "id": stage.id,
                "name": stage.name,
                "status": stage.status,
                "order_index": stage.order_index,
                "progress_percentage": stage.progress_percentage or 0,
                "message": stage.message,
                "started_at": stage.started_at.isoformat()
                if stage.started_at
                else None,
                "completed_at": stage.completed_at.isoformat()
                if stage.completed_at
                else None,
                "error_message": stage.error_message,
            }

            # Include details if available
            if stage.details:
                stage_data["details"] = stage.get_details()

            result.append(stage_data)

        logger.info(f"Retrieved {len(result)} stages for task {task_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stages for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task stages")


@router.get("/tasks/stats/summary", response_model=Dict[str, Any])
async def get_task_stats_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get summary statistics for all tasks."""
    logger = logging.getLogger("get_task_stats")

    try:
        # Get task counts by status
        status_counts = {}
        for status in [
            "pending",
            "running",
            "completed",
            "failed",
            "cancelled",
            "timeout",
        ]:
            count = db.query(AsyncTask).filter(AsyncTask.status == status).count()
            status_counts[status] = count

        # Get task counts by type
        type_counts = {}
        types = db.query(AsyncTask.task_type).distinct().all()
        for (task_type,) in types:
            if task_type:
                count = (
                    db.query(AsyncTask).filter(AsyncTask.task_type == task_type).count()
                )
                type_counts[task_type] = count

        # Get total tasks
        total_tasks = db.query(AsyncTask).count()

        # Get recently completed tasks (last 24 hours)
        from datetime import datetime, timedelta

        recent_completed = (
            db.query(AsyncTask)
            .filter(
                AsyncTask.status == "completed",
                AsyncTask.completed_at >= datetime.utcnow() - timedelta(hours=24),
            )
            .count()
        )

        # Get currently running tasks
        running_tasks = (
            db.query(AsyncTask).filter(AsyncTask.status == "running").count()
        )

        result = {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "recent_completed": recent_completed,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "last_updated": datetime.utcnow().isoformat(),
        }

        logger.info("Retrieved task statistics summary")
        return result

    except Exception as e:
        logger.error(f"Error retrieving task statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve task statistics"
        )

@router.post("/fix", response_model=ChatFixResponse)
async def chat_fix(request: ChatFixRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get or create chat session for this history entry and user
    history_entry = db.query(HistoryEntry).filter_by(id=request.history_entry_id).first()
    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    # Compose prompt for LLM: include user message and current HTML, instruct to return ONLY HTML
    prompt = (
        f"User request: {request.user_message}\n"
        f"Current HTML:\n{history_entry.response}\n"
        "\n---\n"
        "Return ONLY the corrected HTML. Do not include any markdown, explanation, or commentary."
    )
    # Call the real LLM
    updated_html = await generate_with_provider(prompt, request.provider)
    if not updated_html:
        raise HTTPException(status_code=500, detail="LLM did not return any HTML.")

    # Validate the updated HTML using the orchestrator
    validation_result = await validation_orchestrator.validate_content(
        html_content=updated_html,
        title="3D Visualization",
        subject=getattr(history_entry, "subject", "physics"),
        education_level="high school"
    )
    real_errors = _extract_validation_errors(validation_result)

    # If there are real errors, try to fix them using the enhanced error fixing service
    if real_errors:
        fixing_result = await enhanced_error_fixing_service.fix_html_errors(
            updated_html, real_errors, request.provider, db=db, chat_session_id=None
        )
        if fixing_result.get("fixed_html"):
            updated_html = fixing_result["fixed_html"]
            # Optionally, re-validate (not strictly required for parity)
            validation_result = await validation_orchestrator.validate_content(
                html_content=updated_html,
                title="3D Visualization",
                subject=getattr(history_entry, "subject", "physics"),
                education_level="high school"
            )
            real_errors = _extract_validation_errors(validation_result)

    # Update the HistoryEntry with the best HTML
    history_entry.response = updated_html
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    # Find or create a ChatSession for this user and history entry
    session = db.query(ChatSession).filter_by(history_entry_id=history_entry.id, user_id=current_user.id, is_active=True).first()
    if not session:
        session = ChatSession(
            id=str(uuid.uuid4()),
            history_entry_id=history_entry.id,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Create user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        chat_session_id=session.id,
        role="user",
        content=request.user_message,
        message_type="text",
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Create assistant message
    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        chat_session_id=session.id,
        role="assistant",
        content="Visualization updated. See new HTML.",
        message_type="text",
        timestamp=datetime.utcnow()
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatFixResponse(
        success=True,
        updated_html=updated_html,
        assistant_message="Visualization updated. See new HTML.",
        chat_session_id=session.id,
        message_id=assistant_msg.id,
        updated_history_entry_id=history_entry.id,
        validation_results=validation_result,
        error=None,
    )

@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(request: ChatMessageRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get chat session and history entry
    session = db.query(ChatSession).filter_by(id=request.chat_session_id, user_id=current_user.id, is_active=True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    history_entry = db.query(HistoryEntry).filter_by(id=session.history_entry_id).first()
    if not history_entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    # Compose prompt for LLM: include user message and current HTML, instruct to return ONLY HTML
    prompt = (
        f"User request: {request.user_message}\n"
        f"Current HTML:\n{history_entry.response}\n"
        "\n---\n"
        "Return ONLY the corrected HTML. Do not include any markdown, explanation, or commentary."
    )
    # Call the real LLM
    updated_html = await generate_with_provider(prompt, request.provider)
    if not updated_html:
        raise HTTPException(status_code=500, detail="LLM did not return any HTML.")

    # Update the HistoryEntry with the new HTML
    history_entry.response = updated_html
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    # Add user message
    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        chat_session_id=session.id,
        role="user",
        content=request.user_message,
        message_type="text",
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Add assistant message
    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        chat_session_id=session.id,
        role="assistant",
        content="Visualization updated. See new HTML.",
        message_type="text",
        timestamp=datetime.utcnow()
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageResponse(
        success=True,
        updated_html=updated_html,
        assistant_message="Visualization updated. See new HTML.",
        chat_session_id=session.id,
        message_id=assistant_msg.id,
        updated_history_entry_id=history_entry.id,
        validation_results={},
        error=None,
    )

@router.get("/session/{session_id}", response_model=ChatSessionSchema)
async def get_chat_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = db.query(ChatMessage).filter_by(chat_session_id=session.id).order_by(ChatMessage.timestamp).all()
    return ChatSessionSchema(
        id=session.id,
        history_entry_id=session.history_entry_id,
        user_id=session.user_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        messages=[ChatMessageSchema(
            id=m.id,
            role=m.role,
            content=m.content,
            timestamp=m.timestamp,
            message_type=m.message_type
        ) for m in messages]
        )
