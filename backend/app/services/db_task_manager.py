"""
Database-backed Task Manager Service

This module provides a database-backed task management system to replace the in-memory
task manager. Tasks and their stages are persisted to the database, allowing for
server restarts without losing task information.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from ..database.database import get_db
from ..models import AsyncTask, AsyncTaskStage

logger = logging.getLogger(__name__)


class DatabaseTaskManager:
    """Database-backed task manager for async operations."""

    def __init__(self, cleanup_interval: int = 3600, max_task_age_hours: int = 168):
        """
        Initialize the database task manager.

        Args:
            cleanup_interval: Seconds between cleanup operations (default: 1 hour)
            max_task_age_hours: Maximum age of completed tasks in hours (default: 7 days)
        """
        self.cleanup_interval = cleanup_interval
        self.max_task_age_hours = max_task_age_hours
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the task manager and cleanup loop."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Database task manager started")

    async def stop(self):
        """Stop the task manager and cleanup loop."""
        if not self._running:
            return

        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Database task manager stopped")

    def create_task(
        self,
        task_type: str,
        request_data: Dict[str, Any],
        stages: List[str],
        expires_hours: int = 24,
    ) -> str:
        """
        Create a new task in the database.

        Args:
            task_type: Type of task (e.g., 'visualization_generation')
            request_data: Original request parameters
            stages: List of stage names for this task
            expires_hours: Hours until task expires (default: 24)

        Returns:
            Task ID (UUID string)
        """
        db = next(get_db())
        try:
            task_id = str(uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            # Create the main task
            task = AsyncTask(
                id=task_id,
                task_type=task_type,
                status="pending",
                request_data=request_data,
                total_stages=len(stages),
                expires_at=expires_at,
            )

            db.add(task)
            db.flush()  # Get the task ID before creating stages

            # Create stages
            for i, stage_name in enumerate(stages):
                stage = AsyncTaskStage(
                    task_id=task_id,
                    name=stage_name,
                    status="pending",
                    order_index=i,
                )
                db.add(stage)

            db.commit()
            logger.info(f"Created task {task_id} with {len(stages)} stages")
            return task_id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create task: {e}")
            raise
        finally:
            db.close()

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        """
        Get a task by ID with all its stages.

        Args:
            task_id: Task ID

        Returns:
            AsyncTask object or None if not found
        """
        db = next(get_db())
        try:
            task = (
                db.query(AsyncTask)
                .options(joinedload(AsyncTask.stages))
                .filter(AsyncTask.id == task_id)
                .first()
            )
            return task
        finally:
            db.close()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status information.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with task status information or None if not found
        """
        task = self.get_task(task_id)
        if not task:
            return None

        # Get current stage info
        current_stage_info = None
        if task.current_stage:
            current_stage = next(
                (s for s in task.stages if s.name == task.current_stage), None
            )
            if current_stage:
                current_stage_info = {
                    "name": current_stage.name,
                    "status": current_stage.status,
                    "start_time": current_stage.started_at.isoformat()
                    if current_stage.started_at
                    else None,
                    "end_time": current_stage.completed_at.isoformat()
                    if current_stage.completed_at
                    else None,
                    "progress_percentage": current_stage.progress_percentage,
                    "message": current_stage.message,
                    "details": current_stage.get_details(),
                    "error": current_stage.error_message,
                }

        return {
            "task_id": task.id,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
            "progress": {
                "overall_percentage": task.progress_percentage,
                "current_stage": task.current_stage,
                "total_stages": task.total_stages,
                "completed_stages": len(
                    [s for s in task.stages if s.status == "completed"]
                ),
            },
            "current_stage": current_stage_info,
            "error": task.error_message,
        }

    def update_task_status(
        self, task_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status
            error_message: Error message if status is 'failed'

        Returns:
            True if successful, False if task not found
        """
        db = next(get_db())
        try:
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if not task:
                return False

            task.status = status
            task.updated_at = datetime.utcnow()

            if status == "running" and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled", "timeout"]:
                task.completed_at = datetime.utcnow()

            if error_message:
                task.error_message = error_message

            db.commit()
            logger.debug(f"Updated task {task_id} status to {status}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update task {task_id} status: {e}")
            return False
        finally:
            db.close()

    def start_stage(
        self, task_id: str, stage_name: str, message: Optional[str] = None
    ) -> bool:
        """
        Start a task stage.

        Args:
            task_id: Task ID
            stage_name: Name of the stage to start
            message: Optional status message

        Returns:
            True if successful, False if task/stage not found
        """
        db = next(get_db())
        try:
            # Update task current stage and status
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if not task:
                return False

            task.current_stage = stage_name
            task.status = "running"
            task.updated_at = datetime.utcnow()

            if not task.started_at:
                task.started_at = datetime.utcnow()

            # Update stage status
            stage = (
                db.query(AsyncTaskStage)
                .filter(
                    and_(
                        AsyncTaskStage.task_id == task_id,
                        AsyncTaskStage.name == stage_name,
                    )
                )
                .first()
            )

            if stage:
                stage.status = "running"
                stage.started_at = datetime.utcnow()
                if message:
                    stage.message = message

            db.commit()
            logger.debug(f"Started stage {stage_name} for task {task_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to start stage {stage_name} for task {task_id}: {e}")
            return False
        finally:
            db.close()

    def update_stage_progress(
        self,
        task_id: str,
        stage_name: str,
        progress: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update stage progress.

        Args:
            task_id: Task ID
            stage_name: Name of the stage
            progress: Progress percentage (0-100)
            message: Optional status message
            details: Optional details dictionary

        Returns:
            True if successful, False if task/stage not found
        """
        db = next(get_db())
        try:
            stage = (
                db.query(AsyncTaskStage)
                .filter(
                    and_(
                        AsyncTaskStage.task_id == task_id,
                        AsyncTaskStage.name == stage_name,
                    )
                )
                .first()
            )

            if not stage:
                return False

            stage.progress_percentage = max(0, min(100, progress))
            if message:
                stage.message = message
            if details:
                stage.set_details(details)

            # Update overall task progress
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if task:
                # Calculate overall progress based on stage completion
                total_progress = sum(s.progress_percentage for s in task.stages)
                task.progress_percentage = min(100, total_progress // len(task.stages))
                task.updated_at = datetime.utcnow()

            db.commit()
            logger.debug(
                f"Updated progress for stage {stage_name} of task {task_id}: {progress}%"
            )
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update stage progress for task {task_id}: {e}")
            return False
        finally:
            db.close()

    def complete_stage(
        self,
        task_id: str,
        stage_name: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Complete a task stage.

        Args:
            task_id: Task ID
            stage_name: Name of the stage to complete
            message: Optional completion message
            details: Optional details dictionary

        Returns:
            True if successful, False if task/stage not found
        """
        db = next(get_db())
        try:
            stage = (
                db.query(AsyncTaskStage)
                .filter(
                    and_(
                        AsyncTaskStage.task_id == task_id,
                        AsyncTaskStage.name == stage_name,
                    )
                )
                .first()
            )

            if not stage:
                return False

            stage.status = "completed"
            stage.completed_at = datetime.utcnow()
            stage.progress_percentage = 100

            if message:
                stage.message = message
            if details:
                stage.set_details(details)

            # Update overall task progress
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if task:
                completed_stages = len(
                    [s for s in task.stages if s.status == "completed"]
                )
                task.progress_percentage = (completed_stages * 100) // task.total_stages
                task.updated_at = datetime.utcnow()

            db.commit()
            logger.debug(f"Completed stage {stage_name} for task {task_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to complete stage {stage_name} for task {task_id}: {e}"
            )
            return False
        finally:
            db.close()

    def fail_stage(
        self,
        task_id: str,
        stage_name: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Fail a task stage.

        Args:
            task_id: Task ID
            stage_name: Name of the stage that failed
            error_message: Error message
            details: Optional details dictionary

        Returns:
            True if successful, False if task/stage not found
        """
        db = next(get_db())
        try:
            stage = (
                db.query(AsyncTaskStage)
                .filter(
                    and_(
                        AsyncTaskStage.task_id == task_id,
                        AsyncTaskStage.name == stage_name,
                    )
                )
                .first()
            )

            if not stage:
                return False

            stage.status = "failed"
            stage.completed_at = datetime.utcnow()
            stage.error_message = error_message

            if details:
                stage.set_details(details)

            db.commit()
            logger.debug(
                f"Failed stage {stage_name} for task {task_id}: {error_message}"
            )
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to fail stage {stage_name} for task {task_id}: {e}")
            return False
        finally:
            db.close()

    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> bool:
        """
        Complete a task.

        Args:
            task_id: Task ID
            result: Task result data
            message: Optional completion message

        Returns:
            True if successful, False if task not found
        """
        db = next(get_db())
        try:
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if not task:
                return False

            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100

            if result:
                task.set_result(result)
            if message:
                task.error_message = (
                    message  # Using error_message field for completion message
                )

            db.commit()
            logger.info(f"Completed task {task_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False
        finally:
            db.close()

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """
        Fail a task.

        Args:
            task_id: Task ID
            error_message: Error message

        Returns:
            True if successful, False if task not found
        """
        db = next(get_db())
        try:
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if not task:
                return False

            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = error_message

            db.commit()
            logger.info(f"Failed task {task_id}: {error_message}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to fail task {task_id}: {e}")
            return False
        finally:
            db.close()

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID

        Returns:
            True if successful, False if task not found
        """
        db = next(get_db())
        try:
            task = db.query(AsyncTask).filter(AsyncTask.id == task_id).first()
            if not task:
                return False

            # Only cancel if not already finished
            if task.is_finished():
                return False

            task.status = "cancelled"
            task.completed_at = datetime.utcnow()

            # Cancel any running stages
            for stage in task.stages:
                if stage.status == "running":
                    stage.status = "cancelled"
                    stage.completed_at = datetime.utcnow()

            db.commit()
            logger.info(f"Cancelled task {task_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
        finally:
            db.close()

    def get_tasks_by_status(self, status: str, limit: int = 100) -> List[AsyncTask]:
        """
        Get tasks by status.

        Args:
            status: Task status to filter by
            limit: Maximum number of tasks to return

        Returns:
            List of AsyncTask objects
        """
        db = next(get_db())
        try:
            tasks = (
                db.query(AsyncTask)
                .filter(AsyncTask.status == status)
                .order_by(AsyncTask.created_at.desc())
                .limit(limit)
                .all()
            )
            return tasks
        finally:
            db.close()

    def get_recent_tasks(self, limit: int = 50) -> List[AsyncTask]:
        """
        Get recent tasks ordered by creation time.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of AsyncTask objects
        """
        db = next(get_db())
        try:
            tasks = (
                db.query(AsyncTask)
                .order_by(AsyncTask.created_at.desc())
                .limit(limit)
                .all()
            )
            return tasks
        finally:
            db.close()

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get task statistics.

        Returns:
            Dictionary with task statistics
        """
        db = next(get_db())
        try:
            # Count tasks by status
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

            # Count tasks by type
            type_counts = {}
            task_types = db.query(AsyncTask.task_type).distinct().all()
            for (task_type,) in task_types:
                count = (
                    db.query(AsyncTask).filter(AsyncTask.task_type == task_type).count()
                )
                type_counts[task_type] = count

            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_count = (
                db.query(AsyncTask)
                .filter(AsyncTask.created_at >= recent_cutoff)
                .count()
            )

            return {
                "total_tasks": sum(status_counts.values()),
                "status_counts": status_counts,
                "type_counts": type_counts,
                "recent_tasks_24h": recent_count,
                "active_tasks": status_counts.get("pending", 0)
                + status_counts.get("running", 0),
            }
        finally:
            db.close()

    async def _cleanup_loop(self):
        """Periodic cleanup of old tasks."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                if self._running:
                    await self._cleanup_old_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks."""
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.max_task_age_hours)

            # Delete old completed tasks and their stages
            deleted_count = (
                db.query(AsyncTask)
                .filter(
                    and_(
                        AsyncTask.completed_at < cutoff_time,
                        AsyncTask.status.in_(["completed", "failed", "cancelled"]),
                    )
                )
                .count()
            )

            if deleted_count > 0:
                # Delete stages first (foreign key constraint)
                old_task_ids = (
                    db.query(AsyncTask.id)
                    .filter(
                        and_(
                            AsyncTask.completed_at < cutoff_time,
                            AsyncTask.status.in_(["completed", "failed", "cancelled"]),
                        )
                    )
                    .subquery()
                )

                db.query(AsyncTaskStage).filter(
                    AsyncTaskStage.task_id.in_(old_task_ids)
                ).delete(synchronize_session=False)

                # Delete tasks
                db.query(AsyncTask).filter(
                    and_(
                        AsyncTask.completed_at < cutoff_time,
                        AsyncTask.status.in_(["completed", "failed", "cancelled"]),
                    )
                ).delete(synchronize_session=False)

                db.commit()
                logger.info(f"Cleaned up {deleted_count} old tasks")

            # Mark expired tasks
            expired_count = (
                db.query(AsyncTask)
                .filter(
                    and_(
                        AsyncTask.expires_at < datetime.utcnow(),
                        AsyncTask.status.in_(["pending", "running"]),
                    )
                )
                .update({"status": "timeout", "completed_at": datetime.utcnow()})
            )

            if expired_count > 0:
                db.commit()
                logger.info(f"Marked {expired_count} tasks as expired")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old tasks: {e}")
        finally:
            db.close()


# Global instance
db_task_manager = DatabaseTaskManager()
