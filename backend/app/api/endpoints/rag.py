from typing import Any, Dict, List

from app.config.settings import settings
from app.database.database import get_db
from app.schemas.schemas import GenerateRequest, RetrieveSimilarResponse
from app.services.rag import RAGService, get_rag_service
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.utils.embedding_utils import build_embedding_text_from_config
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/similar", response_model=List[Dict[str, Any]])
async def get_similar_visualizations(
    query: str, limit: int = 5, rag_service: RAGService = Depends(get_rag_service)
):
    """Get similar visualizations based on the query text."""
    try:
        return await rag_service.get_similar_visualizations(query, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diverse-examples", response_model=List[Dict[str, Any]])
async def get_diverse_examples(
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db),
):
    """Get one example of each visualization type from the vector store."""
    try:
        return await rag_service.get_diverse_examples(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve-similar", response_model=RetrieveSimilarResponse)
async def retrieve_similar_visualizations(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    top_k: int = Query(
        settings.SIMILAR_VIS_LIMIT, description="Number of similar results to return"
    ),
) -> RetrieveSimilarResponse:
    """Retrieve similar visualizations/snippets based on user prompt and config."""
    try:
        # Prepare embedding input using the same utility as /generate
        if request.config:
            embedding_input = build_embedding_text_from_config(
                request.config.model_dump()
            )
        else:
            embedding_input = request.topic
        embedding = EmbeddingService.generate_embedding(embedding_input)
        vector_store = get_vector_store()
        similar = await vector_store.get_similar_visualizations(
            embedding, db, limit=top_k
        )
        # Optionally, add similarity scores if available
        results = []
        for item in similar:
            meta = item.get("metadata", {})
            score = item.get("similarity") if "similarity" in item else None
            results.append({"metadata": meta, "score": score})
        return RetrieveSimilarResponse(results=results)
    except Exception as e:
        import logging

        logger = logging.getLogger("retrieve_similar_visualizations")
        logger.error(
            "Error retrieving similar visualizations",
            extra={
                "action": "retrieve_similar_visualizations",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))
