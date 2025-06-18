import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import SnippetMetadata, HistoryEntry
from app.services.rag import get_vector_store

router = APIRouter()

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

@router.get("/admin/generation-stats", response_model=dict)
async def get_generation_stats(db: Session = Depends(get_db)) -> dict:
    """Get statistics about visualization generation times."""
    try:
        # Get all generation times
        generation_times = db.query(HistoryEntry.generation_time).filter(
            HistoryEntry.generation_time.isnot(None)
        ).all()
        if not generation_times:
            return {
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "total_generations": 0
            }
        # Convert to numpy array for calculations
        import numpy as np
        times = np.array([t[0] for t in generation_times])
        return {
            "mean": float(np.mean(times)),
            "median": float(np.median(times)),
            "p95": float(np.percentile(times, 95)),
            "p99": float(np.percentile(times, 99)),
            "total_generations": len(times)
        }
    except Exception as e:
        logger = logging.getLogger("generation_stats")
        logger.error("Error getting generation stats", extra={
            "action": "get_generation_stats",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e)) 