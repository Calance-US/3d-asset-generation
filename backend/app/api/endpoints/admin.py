from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import (
    get_db,
    get_prompts,
    create_prompt,
    update_prompt,
    delete_prompt,
    duplicate_prompt,
    batch_delete_prompts,
    export_prompts,
    import_prompts
)
from app.schemas.schemas import (
    UpdatePromptRequest,
    CreatePromptRequest,
    BatchDeleteRequest,
    ImportPromptsRequest,
    PromptResponse,
    PromptsResponse,
    SuccessResponse
)
from app.services.prompt_selector import PromptSelector
from typing import List, Dict, Any, Optional
import numpy as np
from app.services.rag import get_vector_store
from app.models import SnippetMetadata
from app.database.db_config import get_db
import logging

router = APIRouter()
prompt_selector = PromptSelector()

@router.get("/vector-store-stats", response_model=Dict[str, Any])
async def get_vector_store_stats():
    """Get statistics about the vector store (Qdrant or other)."""
    vector_store = get_vector_store()
    db = next(get_db())
    logger = logging.getLogger("vector_store_stats")
    try:
        stats = {
            "total_vectors": 0,
            "dimension": 0,
            "index_type": "Qdrant",
            "snippet_types": {},
            "topics": {},
            "education_levels": {}
        }
        # Use Qdrant count API for total vectors
        try:
            logger.info(f"Qdrant collection name: {vector_store.collection_name}")
            logger.info(f"Qdrant client host: {getattr(vector_store.client, 'host', 'unknown')}, port: {getattr(vector_store.client, 'port', 'unknown')}")
            info = vector_store.client.get_collection(vector_store.collection_name)
            logger.info(f"Qdrant get_collection result: {info}")
            count_result = vector_store.client.count(collection_name=vector_store.collection_name, exact=True)
            logger.info(f"Qdrant count result: {count_result}")
            stats["total_vectors"] = count_result.count
            stats["dimension"] = info.config.params.vectors.size
        except Exception as e:
            logger.error(f"Error querying Qdrant: {e}")
        # Get all metadata from DB
        all_metadata = db.query(SnippetMetadata).all()
        for metadata in all_metadata:
            snippet_type = getattr(metadata, 'snippet_type', 'unknown') or 'unknown'
            stats['snippet_types'][snippet_type] = stats['snippet_types'].get(snippet_type, 0) + 1
            topic = getattr(metadata, 'topic', 'unknown') or 'unknown'
            stats['topics'][topic] = stats['topics'].get(topic, 0) + 1
            level = getattr(metadata, 'education_level', 'unknown') or 'unknown'
            stats['education_levels'][level] = stats['education_levels'].get(level, 0) + 1
        return stats
    finally:
        db.close()

@router.get("/vector-store-vectors", response_model=List[Dict[str, Any]])
async def get_vector_store_vectors(
    skip: int = 0,
    limit: int = 100,
    snippet_type: Optional[str] = None,
    topic: Optional[str] = None,
    education_level: Optional[str] = None
):
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

@router.get("/prompts", response_model=PromptsResponse)
async def get_all_prompts(
    subject: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> PromptsResponse:
    """Get all prompts from the database with optional filtering."""
    try:
        prompts = get_prompts(db, subject, category, tag, search)
        return PromptsResponse(prompts=[
            PromptResponse(
                id=prompt.id,
                subject=prompt.subject,
                topic=prompt.topic,
                content=prompt.content,
                category=prompt.category,
                tags=[tag.name for tag in prompt.tags]
            )
            for prompt in prompts
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts", response_model=PromptResponse)
async def create_prompt_endpoint(
    prompt_data: CreatePromptRequest,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Create a new prompt in the database."""
    try:
        new_prompt = create_prompt(
            db,
            subject=prompt_data.subject,
            topic=prompt_data.topic,
            content=prompt_data.content,
            category=prompt_data.category,
            tags=",".join(prompt_data.tags) if prompt_data.tags else ""
        )
        prompt_selector.initialize_index()
        return PromptResponse(
            id=new_prompt.id,
            subject=new_prompt.subject,
            topic=new_prompt.topic,
            content=new_prompt.content,
            category=new_prompt.category,
            tags=[tag.name for tag in new_prompt.tags]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt_endpoint(
    prompt_id: int,
    prompt_data: UpdatePromptRequest,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Update a prompt in the database."""
    try:
        update_data = {k: v for k, v in prompt_data.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")
        updated_prompt = update_prompt(db, prompt_id, update_data)
        if not updated_prompt:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")
        prompt_selector.initialize_index()
        return PromptResponse(
            id=updated_prompt.id,
            subject=updated_prompt.subject,
            topic=updated_prompt.topic,
            content=updated_prompt.content,
            category=updated_prompt.category,
            tags=[tag.name for tag in updated_prompt.tags]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/prompts/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete a prompt from the database."""
    try:
        success = delete_prompt(db, prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")
        prompt_selector.initialize_index()
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts/{prompt_id}/duplicate", response_model=PromptResponse)
async def duplicate_prompt_endpoint(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> PromptResponse:
    """Duplicate a prompt."""
    try:
        duplicated = duplicate_prompt(db, prompt_id)
        if not duplicated:
            raise HTTPException(status_code=404, detail=f"Prompt with ID {prompt_id} not found")
        return PromptResponse(
            id=duplicated.id,
            subject=duplicated.subject,
            topic=duplicated.topic,
            content=duplicated.content,
            category=duplicated.category,
            tags=[tag.name for tag in duplicated.tags]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts/batch-delete", response_model=SuccessResponse)
async def batch_delete_prompts_endpoint(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Delete multiple prompts."""
    try:
        success = batch_delete_prompts(db, request.prompt_ids)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete prompts")
        prompt_selector.initialize_index()
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts/export", response_model=PromptsResponse)
async def export_prompts_endpoint(db: Session = Depends(get_db)) -> PromptsResponse:
    """Export all prompts."""
    try:
        prompts_data = export_prompts(db)
        return PromptsResponse(prompts=[
            PromptResponse(
                id=prompt["id"],
                subject=prompt["subject"],
                topic=prompt["topic"],
                content=prompt["content"],
                category=prompt["category"],
                tags=prompt["tags"]
            )
            for prompt in prompts_data
        ])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts/import", response_model=SuccessResponse)
async def import_prompts_endpoint(
    request: ImportPromptsRequest,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """Import prompts."""
    try:
        success = import_prompts(db, request.prompts)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import prompts")
        return SuccessResponse(status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 