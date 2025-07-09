import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ...database.database import get_db
from ...models import Local3DModel
from ...services.local_model_service import LocalModelService
from ...config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=List[dict])
async def list_local_models(
    search: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List local 3D models with optional filtering."""
    
    service = LocalModelService(db)
    
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
    
    models = service.search_models(
        query=search or "",
        category=category,
        subject=subject,
        tags=tag_list,
        limit=limit
    )
    
    # Convert to response format
    response_models = []
    for model in models:
        response_models.append({
            "id": model.id,
            "model_name": model.model_name,
            "filename": model.filename,
            "file_size": model.file_size,
            "category": model.category,
            "subject": model.subject,
            "tags": model.tags or [],
            "description": model.description,
            "model_type": model.model_type,
            "has_animations": model.has_animations,
            "has_textures": model.has_textures,
            "has_materials": model.has_materials,
            "triangle_count": model.triangle_count,
            "vertex_count": model.vertex_count,
            "usage_count": model.usage_count,
            "last_used_at": model.last_used_at.isoformat() if model.last_used_at else None,
            "is_active": model.is_active,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
            "api_url": model.get_api_url()
        })
    
    return response_models


@router.get("/{model_id}", response_model=dict)
async def get_local_model(
    model_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific local 3D model."""
    
    service = LocalModelService(db)
    model = service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return {
        "id": model.id,
        "model_name": model.model_name,
        "filename": model.filename,
        "file_size": model.file_size,
        "category": model.category,
        "subject": model.subject,
        "tags": model.tags or [],
        "description": model.description,
        "model_type": model.model_type,
        "has_animations": model.has_animations,
        "has_textures": model.has_textures,
        "has_materials": model.has_materials,
        "triangle_count": model.triangle_count,
        "vertex_count": model.vertex_count,
        "usage_count": model.usage_count,
        "last_used_at": model.last_used_at.isoformat() if model.last_used_at else None,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat(),
        "api_url": model.get_api_url()
    }


@router.get("/{model_id}/file")
async def serve_model_file(
    model_id: int,
    db: Session = Depends(get_db),
):
    """Serve a 3D model file."""
    
    service = LocalModelService(db)
    model = service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    file_path = Path(model.file_path)
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model file not found"
        )
    
    # Update usage count
    service.update_usage_count(model_id)
    
    response = FileResponse(
        path=file_path,
        filename=model.filename,
        media_type="model/gltf+json"
    )
    
    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


@router.options("/{model_id}/file")
async def options_model_file():
    """Handle OPTIONS request for CORS preflight."""
    return Response(headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    })


@router.post("/scan")
async def scan_models(
    db: Session = Depends(get_db),
):
    """Scan and index all models in the models directory."""
    
    service = LocalModelService(db)
    result = service.scan_and_index_models()
    
    return {
        "message": f"Indexed {result['indexed_count']} new models",
        "indexed_count": result["indexed_count"],
        "errors": result["errors"]
    }


@router.get("/categories/list")
async def list_categories(
    db: Session = Depends(get_db),
):
    """Get list of all available categories."""
    
    service = LocalModelService(db)
    return service.get_categories()


@router.get("/subjects/list")
async def list_subjects(
    db: Session = Depends(get_db),
):
    """Get list of all available subjects."""
    
    service = LocalModelService(db)
    return service.get_subjects()


@router.get("/tags/list")
async def list_tags(
    db: Session = Depends(get_db),
):
    """Get list of all available tags."""
    
    service = LocalModelService(db)
    return service.get_tags()


@router.get("/search/visualization")
async def search_models_for_visualization(
    topic: str = Query(..., description="Visualization topic"),
    subject: str = Query(..., description="Subject area"),
    components: Optional[str] = Query(None, description="JSON string of components"),
    db: Session = Depends(get_db),
):
    """Search for models relevant to a specific visualization."""
    
    service = LocalModelService(db)
    
    # Parse components if provided
    component_list = []
    if components:
        try:
            import json
            component_list = json.loads(components)
            if not isinstance(component_list, list):
                component_list = []
        except json.JSONDecodeError:
            component_list = []
    
    models = service.get_models_for_visualization(
        topic=topic,
        subject=subject,
        components=component_list
    )
    
    # Convert to response format
    response_models = []
    for model in models:
        response_models.append({
            "id": model.id,
            "model_name": model.model_name,
            "filename": model.filename,
            "category": model.category,
            "subject": model.subject,
            "tags": model.tags or [],
            "description": model.description,
            "api_url": model.get_api_url(),
            "relevance_score": 0.8  # Placeholder - could be calculated based on similarity
        })
    
    return {
        "topic": topic,
        "subject": subject,
        "models": response_models,
        "total_count": len(response_models)
    } 