from app.config.logging_config import logger
from app.schemas.schemas import ModelsResponse
from app.services.model_repository import ModelRepository
from fastapi import APIRouter, HTTPException

router = APIRouter()

model_repository = ModelRepository()


@router.get("/models/{subject}", response_model=ModelsResponse)
async def get_available_models(subject: str) -> ModelsResponse:
    """Get available models for a subject."""
    try:
        models = model_repository.get_models(subject)
        return ModelsResponse(models=models)
    except Exception as e:
        logger.error(
            "Error getting models",
            extra={
                "action": "get_models",
                "subject": subject,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))
