import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ValidationErrorService:
    """Service for managing validation errors in the database."""

    @staticmethod
    def save_validation_errors(
        db: Session, errors: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> List:
        """
        Save validation errors to the database.

        Args:
            db: Database session
            errors: List of validation error dictionaries
            metadata: Additional metadata (visualization_id, prompt_id, etc.)

        Returns:
            List of created ValidationError instances
        """
        # Import here to avoid circular import
        from app.models import ValidationError

        saved_errors = []

        try:
            for error_data in errors:
                validation_error = ValidationError(
                    visualization_id=metadata.get("visualization_id"),
                    prompt_id=metadata.get("prompt_id"),
                    phase=error_data.get("phase", "unknown"),
                    severity=error_data.get("severity", "unknown"),
                    error_type=error_data.get("error_type", "unknown"),
                    message=error_data.get("message", ""),
                    location=error_data.get("location"),
                    suggestion=error_data.get("suggestion"),
                    context=error_data.get("context"),
                    attempt_number=metadata.get("attempt_number", 1),
                    quality_score=metadata.get("quality_score"),
                    # Use provider_id, not provider string
                    provider_id=metadata.get("provider_id"),
                )

                db.add(validation_error)
                saved_errors.append(validation_error)

            db.commit()
            logger.info(f"Saved {len(saved_errors)} validation errors to database")
            return saved_errors

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save validation errors: {e}")
            raise

    @staticmethod
    def get_validation_errors_by_visualization(
        db: Session, visualization_id: int
    ) -> List:
        """Get all validation errors for a specific visualization."""
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            return (
                db.query(ValidationError)
                .filter(ValidationError.visualization_id == visualization_id)
                .order_by(ValidationError.created_at.desc())
                .all()
            )
        except Exception as e:
            logger.error(
                f"Failed to get validation errors for visualization {visualization_id}: {e}"
            )
            return []

    @staticmethod
    def get_validation_errors_by_prompt(db: Session, prompt_id: int) -> List:
        """Get all validation errors for a specific prompt."""
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            return (
                db.query(ValidationError)
                .filter(ValidationError.prompt_id == prompt_id)
                .order_by(ValidationError.created_at.desc())
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get validation errors for prompt {prompt_id}: {e}")
            return []

    @staticmethod
    def get_error_statistics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get validation error statistics for the last N days."""
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Get error breakdown by phase and type
            error_breakdown = (
                db.query(
                    ValidationError.phase,
                    ValidationError.error_type,
                    func.count(ValidationError.id).label("count"),
                    func.avg(ValidationError.quality_score).label("avg_quality"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(ValidationError.phase, ValidationError.error_type)
                .all()
            )

            # Get total error counts
            total_errors = (
                db.query(func.count(ValidationError.id))
                .filter(ValidationError.created_at >= since_date)
                .scalar()
            )

            # Get error counts by severity
            severity_breakdown = (
                db.query(
                    ValidationError.severity,
                    func.count(ValidationError.id).label("count"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(ValidationError.severity)
                .all()
            )

            # Get error counts by provider
            provider_breakdown = (
                db.query(
                    ValidationError.provider,
                    func.count(ValidationError.id).label("count"),
                    func.avg(ValidationError.quality_score).label("avg_quality"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(ValidationError.provider)
                .all()
            )

            # Get daily error trends
            daily_trends = (
                db.query(
                    func.date(ValidationError.created_at).label("date"),
                    func.count(ValidationError.id).label("count"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(func.date(ValidationError.created_at))
                .order_by("date")
                .all()
            )

            return {
                "period_days": days,
                "total_errors": total_errors,
                "error_breakdown": [
                    {
                        "phase": stat.phase,
                        "error_type": stat.error_type,
                        "count": stat.count,
                        "avg_quality_score": (
                            float(stat.avg_quality) if stat.avg_quality else None
                        ),
                    }
                    for stat in error_breakdown
                ],
                "severity_breakdown": [
                    {"severity": stat.severity, "count": stat.count}
                    for stat in severity_breakdown
                ],
                "provider_breakdown": [
                    {
                        "provider": stat.provider,
                        "count": stat.count,
                        "avg_quality_score": (
                            float(stat.avg_quality) if stat.avg_quality else None
                        ),
                    }
                    for stat in provider_breakdown
                ],
                "daily_trends": [
                    {"date": str(trend.date), "count": trend.count}
                    for trend in daily_trends
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {
                "period_days": days,
                "total_errors": 0,
                "error_breakdown": [],
                "severity_breakdown": [],
                "provider_breakdown": [],
                "daily_trends": [],
                "error": str(e),
            }

    @staticmethod
    def get_most_common_errors(
        db: Session, limit: int = 10, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get the most common validation errors in the last N days."""
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            results = (
                db.query(
                    ValidationError.error_type,
                    ValidationError.message,
                    func.count(ValidationError.id).label("count"),
                    func.avg(ValidationError.quality_score).label("avg_quality"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(ValidationError.error_type, ValidationError.message)
                .order_by(func.count(ValidationError.id).desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "error_type": result.error_type,
                    "message": result.message,
                    "count": result.count,
                    "avg_quality_score": (
                        float(result.avg_quality) if result.avg_quality else None
                    ),
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Failed to get most common errors: {e}")
            return []

    @staticmethod
    def get_retry_success_metrics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get retry success metrics for the last N days."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            # Get visualizations with retry attempts
            from app.models import Visualization

            retry_metrics = (
                db.query(
                    func.avg(Visualization.generation_attempts).label("avg_attempts"),
                    func.max(Visualization.generation_attempts).label("max_attempts"),
                    func.count(Visualization.id)
                    .filter(Visualization.generation_attempts > 1)
                    .label("retry_count"),
                    func.count(Visualization.id).label("total_count"),
                )
                .filter(Visualization.created_at >= since_date)
                .first()
            )

            # Get success rate by attempt number
            attempt_success_rates = (
                db.query(
                    ValidationError.attempt_number,
                    func.count(ValidationError.id).label("error_count"),
                )
                .filter(ValidationError.created_at >= since_date)
                .group_by(ValidationError.attempt_number)
                .order_by(ValidationError.attempt_number)
                .all()
            )

            return {
                "period_days": days,
                "average_attempts": (
                    float(retry_metrics.avg_attempts)
                    if retry_metrics.avg_attempts
                    else 1.0
                ),
                "max_attempts": retry_metrics.max_attempts or 1,
                "retry_rate": (
                    (retry_metrics.retry_count / retry_metrics.total_count * 100)
                    if retry_metrics.total_count > 0
                    else 0
                ),
                "total_generations": retry_metrics.total_count,
                "attempt_distribution": [
                    {"attempt": stat.attempt_number, "error_count": stat.error_count}
                    for stat in attempt_success_rates
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get retry success metrics: {e}")
            return {
                "period_days": days,
                "average_attempts": 1.0,
                "max_attempts": 1,
                "retry_rate": 0,
                "total_generations": 0,
                "attempt_distribution": [],
                "error": str(e),
            }

    @staticmethod
    def cleanup_old_errors(db: Session, days: int = 90) -> int:
        """
        Clean up old validation errors to manage database size.

        Args:
            db: Database session
            days: Keep errors from last N days

        Returns:
            Number of deleted records
        """
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = (
                db.query(ValidationError)
                .filter(ValidationError.created_at < cutoff_date)
                .delete()
            )

            db.commit()
            logger.info(f"Cleaned up {deleted_count} old validation errors")
            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old errors: {e}")
            return 0

    @staticmethod
    def get_error_details(db: Session, error_id: int) -> Optional:
        """Get detailed information about a specific validation error."""
        # Import here to avoid circular import
        from app.models import ValidationError

        try:
            return (
                db.query(ValidationError).filter(ValidationError.id == error_id).first()
            )
        except Exception as e:
            logger.error(f"Failed to get error details for ID {error_id}: {e}")
            return None


# Create singleton instance
validation_error_service = ValidationErrorService()
