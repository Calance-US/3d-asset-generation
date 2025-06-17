from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from backend.services.rag import RAGService

router = APIRouter()

@router.get("/similar", response_model=List[Dict[str, Any]])
async def get_similar_visualizations(
    query: str,
    limit: int = 5,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get similar visualizations based on the query text."""
    try:
        return await rag_service.get_similar_visualizations(query, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diverse-examples", response_model=List[Dict[str, Any]])
async def get_diverse_examples(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get one example of each visualization type from the vector store."""
    try:
        return await rag_service.get_diverse_examples()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 