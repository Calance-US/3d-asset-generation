import datetime
import json
import logging

from app.auth.dependencies import get_current_user_optional
from app.database.database import (
    get_all_history,
    get_db,
    get_history_entry_by_id,
    remove_history_entry,
)
from app.models import User
from app.schemas.schemas import HistoryEntryResponse, HistoryResponse, SuccessResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=HistoryResponse)
async def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
) -> HistoryResponse:
    """Get the history of generated visualizations."""
    try:
        history = get_all_history(db)
        return HistoryResponse(
            entries=[
                HistoryEntryResponse(
                    id=entry.id,
                    prompt=entry.user_query or "",
                    provider=entry.ai_provider.name if entry.ai_provider else "Unknown",
                    subject=entry.prompt.subject if entry.prompt else "Unknown",
                    html=entry.response or "",
                    timestamp=entry.created_at.isoformat() if entry.created_at else datetime.datetime.now().isoformat(),
                    config={
                        "topic_name": entry.prompt.topic if entry.prompt else "",
                        "key_concepts": entry.prompt.key_concepts if entry.prompt else "",
                        "education_level": entry.prompt.education_level if entry.prompt else "High School",
                        "learning_objectives": entry.prompt.learning_objectives if entry.prompt else "",
                        "interactive_features": entry.prompt.interactive_features if entry.prompt else "",
                        "components": json.loads(entry.components) if entry.components else [],
                        "materials": json.loads(entry.materials) if entry.materials else [],
                        "lights": json.loads(entry.lights) if entry.lights else [],
                        "render_settings": json.loads(entry.render_settings) if entry.render_settings else {},
                        "animation_speed": entry.animation_speed or 1.0,
                        "intro_narration_texts": json.loads(entry.intro_narration_texts) if entry.intro_narration_texts else [],
                        "supporting_narration_texts": json.loads(entry.supporting_narration_texts) if entry.supporting_narration_texts else [],
                        "interactive_description": entry.prompt.interactive_features if entry.prompt else "",
                        "scene_description": entry.scene_description if entry.scene_description else "",
                    },
                )
                for entry in history
            ]
        )
    except Exception as e:
        logger.error(
            "Error getting history",
            extra={
                "action": "get_history",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entry_id}", response_model=HistoryEntryResponse)
async def get_history_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
) -> HistoryEntryResponse:
    """Get a specific history entry by ID."""
    try:
        entry = get_history_entry_by_id(db, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found")
        return HistoryEntryResponse(
            id=entry.id,
            prompt=entry.user_query or "",
            provider=entry.ai_provider.name if entry.ai_provider else "Unknown",
            subject=entry.prompt.subject if entry.prompt else "Unknown",
            html=entry.response or "",
            timestamp=entry.created_at.isoformat()
            if entry.created_at
            else datetime.datetime.now().isoformat(),
            config={
                "topic_name": entry.prompt.topic if entry.prompt else "",
                "key_concepts": entry.prompt.key_concepts if entry.prompt else "",
                "education_level": entry.prompt.education_level
                if entry.prompt
                else "High School",
                "learning_objectives": entry.prompt.learning_objectives
                if entry.prompt
                else "",
                "interactive_features": entry.prompt.interactive_features
                if entry.prompt
                else "",
                "components": json.loads(entry.components) if entry.components else [],
                "materials": json.loads(entry.materials) if entry.materials else [],
                "lights": json.loads(entry.lights) if entry.lights else [],
                "render_settings": json.loads(entry.render_settings)
                if entry.render_settings
                else {},
                "animation_speed": entry.animation_speed or 1.0,
                "intro_narration_texts": json.loads(entry.intro_narration_texts)
                if entry.intro_narration_texts
                else [],
                "supporting_narration_texts": json.loads(
                    entry.supporting_narration_texts
                )
                if entry.supporting_narration_texts
                else [],
                "interactive_description": entry.prompt.interactive_features
                if entry.prompt
                else "",
                "animated_elements": entry.prompt.interactive_features
                if entry.prompt
                else "",
                "three_js_url": "https://esm.sh/three@0.155.0",
                "orbit_controls_url": "https://esm.sh/three@0.155.0/examples/jsm/controls/OrbitControls",
                "camera_controls": "OrbitControls",
                "curve_points": [{"x": 0, "y": 0, "z": 0}],
                "tts_language": "en-US",
                "tts_rate": 1.0,
                "tts_pitch": 1.0,
                "scene_description": entry.scene_description
                if entry.scene_description
                else "",
            },
        )
    except Exception as e:
        logger.error(
            "Error getting history entry",
            extra={
                "action": "get_history_entry",
                "entry_id": entry_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_history_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
) -> SuccessResponse:
    """Delete a history entry."""
    try:
        remove_history_entry(db, entry_id)
        return SuccessResponse(status="success")
    except Exception as e:
        logger.error(
            "Error deleting history entry",
            extra={
                "action": "delete_history_entry",
                "entry_id": entry_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))
