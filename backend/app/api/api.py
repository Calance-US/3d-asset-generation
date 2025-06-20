from app.api.endpoints import (
    admin,
    async_visualizations,
    auth,
    gold_standards,
    history,
    models,
    prompt,
    rag,
    visualizations,
)
from fastapi import APIRouter

api_router = APIRouter()

# Include available routers
api_router.include_router(
    visualizations.router, prefix="/visualizations", tags=["visualizations"]
)
api_router.include_router(
    gold_standards.router, prefix="/gold-standards", tags=["gold-standards"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(prompt.router, prefix="/prompt", tags=["prompt"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(
    async_visualizations.router,
    prefix="/async-visualizations",
    tags=["async-visualizations"],
)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
