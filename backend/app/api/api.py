from fastapi import APIRouter
from app.api.endpoints import gold_standards, visualizations, admin

api_router = APIRouter()

# Include available routers
api_router.include_router(visualizations.router, prefix="/visualizations", tags=["visualizations"])
api_router.include_router(gold_standards.router, prefix="/gold-standards", tags=["gold-standards"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 