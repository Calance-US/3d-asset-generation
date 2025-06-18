import logging
import json
import hashlib
import uuid
from datetime import datetime
import traceback
import asyncio
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.models import GoldStandardUploadStatus, SnippetMetadata
from app.database.db_config import SessionLocal, get_db
from app.config.settings import settings
from app.schemas.schemas import (
    EnhancedPromptResponse, EnhancedConfigSchema, SnippetSchema, SnippetType,
    GoldStandardCreate, GoldStandardUpdate, GoldStandardResponse, HtmlAnalysisRequest
)
from app.services.rag import get_rag_service, get_vector_store, get_metadata_service
from app.services.rag.embedding_service import EmbeddingService
from app.utils import (
    create_embedding_text, coerce_to_schema, build_gold_standard_prompt,
    normalize_snippet_types, process_with_retry, process_file
)
from app.utils.embedding_utils import build_embedding_text_from_config
from app.utils.html_utils import analyze_html
from app.utils.coerce_utils import coerce_to_schema

router = APIRouter()

@router.post("/")
async def create_gold_standards(
    files: List[UploadFile] = File(..., description="One or more HTML files to analyze and ingest as gold standards"),
    background_tasks: BackgroundTasks = None,
    rag_service = Depends(get_rag_service)
) -> Dict[str, Any]:
    """Create gold standards from HTML files."""
    db: Session = SessionLocal()
    upload_id = str(uuid.uuid4())
    status_row = GoldStandardUploadStatus(
        id=upload_id,
        status="processing",
        result=None,
        error_message=None
    )
    db.add(status_row)
    db.commit()
    db.refresh(status_row)

    try:
        # Process files concurrently with retry logic
        file_tasks = [process_with_retry(file, upload_id) for file in files]
        results = await asyncio.gather(*file_tasks)
        
        status_row.status = "completed"
        status_row.set_result(results)
        status_row.error_message = None
        
    except Exception as e:
        status_row.status = "error"
        status_row.set_result(None)
        status_row.error_message = str(e)
        
    finally:
        current_status = status_row.status
        db.add(status_row)
        db.commit()
        db.close()

    return {"upload_id": upload_id, "status": current_status}

@router.get("/status/{upload_id}")
def get_gold_standard_upload_status(upload_id: str):
    db: Session = SessionLocal()
    status_row = db.query(GoldStandardUploadStatus).filter_by(id=upload_id).first()
    if not status_row:
        db.close()
        raise HTTPException(status_code=404, detail="Upload status not found")
    result = {
        "upload_id": status_row.id,
        "status": status_row.status,
        "result": status_row.get_result(),
        "error_message": status_row.error_message,
        "created_at": status_row.created_at,
        "updated_at": status_row.updated_at,
    }
    db.close()
    return result

@router.get("/search", response_model=List[GoldStandardResponse])
async def search_gold_standards(
    query: str,
    top_k: int = 2,
    rag_service = Depends(get_rag_service)
):
    """Search for similar gold standard visualizations."""
    try:
        db = next(get_db())
        # Create embedding text for the query using the same function
        query_embedding_text = create_embedding_text(
            llm_embedding_text=query,  # Use the query as the primary semantic content
            snippet_type="",  # We don't know the type for the query
            topic="",  # We don't know the topic for the query
            concepts=""  # We don't know the concepts for the query
        )
        # Get similar visualizations using the query embedding text
        results = await rag_service.get_similar_visualizations(query_embedding_text, db, limit=top_k)
        return [
            GoldStandardResponse(
                id=i,
                metadata=result['metadata'],
                distance=result['similarity']
            )
            for i, result in enumerate(results)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[GoldStandardResponse])
async def list_gold_standards(
    rag_service = Depends(get_rag_service)
):
    """List all gold standard visualizations."""
    db = next(get_db())
    try:
        all_metadata = db.query(SnippetMetadata).all()
        return [
            GoldStandardResponse(
                id=m.faiss_id,
                metadata={
                    "id": m.id,
                    "snippet_hash": m.snippet_hash,
                    "snippet_type": m.snippet_type,
                    "summary": m.summary,
                    "embedding_text": m.embedding_text,
                    "html_snippet": m.html_snippet,
                    "filename": m.filename,
                    "upload_id": m.upload_id,
                    "llm_version": m.llm_version,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                    "validation_status": m.validation_status,
                    "validation_errors": m.validation_errors,
                    "retry_count": m.retry_count,
                    "topic": m.topic,
                    "key_concepts": m.key_concepts,
                    "education_level": m.education_level,
                    "learning_objectives": m.learning_objectives,
                    "faiss_id": m.faiss_id
                },
                html=m.html_snippet
            )
            for m in all_metadata
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.put("/{index}", response_model=GoldStandardResponse)
async def update_gold_standard(
    index: int,
    gold_standard: GoldStandardUpdate,
    db: Session = Depends(get_db),
    rag_service = Depends(get_rag_service)
):
    """Update a gold standard visualization in the vector store."""
    try:
        # Get the existing visualization from database
        existing_metadata = db.query(SnippetMetadata).filter(SnippetMetadata.faiss_id == index).first()
        
        if not existing_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Gold standard at index {index} not found"
            )
            
        # Update the visualization metadata
        if gold_standard.metadata:
            existing_metadata.metadata.update(gold_standard.metadata)
        if gold_standard.html:
            existing_metadata.metadata['html'] = gold_standard.html
            
        # Save the updated metadata
        db.commit()
        
        logging.info("Successfully updated gold standard", extra={
            "action": "update_gold_standard",
            "index": index
        })
        
        return GoldStandardResponse(
            id=index,
            metadata=existing_metadata.metadata,
            html=existing_metadata.metadata.get('html', '')
        )
            
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logging.error("Error updating gold standard", extra={
            "action": "update_gold_standard",
            "error": str(e),
            "error_type": type(e).__name__,
            "index": index
        })
        raise HTTPException(
            status_code=500,
            detail=f"Error updating gold standard: {str(e)}"
        )

@router.delete("/{index}")
async def delete_gold_standard(
    index: int,
    db: Session = Depends(get_db),
    rag_service = Depends(get_rag_service)
):
    """Delete a gold standard visualization from the vector store."""
    try:
        # Get the existing visualization from database
        existing_metadata = db.query(SnippetMetadata).filter(SnippetMetadata.faiss_id == index).first()
        
        if not existing_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Gold standard at index {index} not found"
            )
            
        # Delete from database
        db.delete(existing_metadata)
        db.commit()
        
        # Note: FAISS doesn't have a simple way to remove by ID, so the vector store
        # will need to be rebuilt or the index will become inconsistent
        # For now, we'll just log a warning
        logging.warning(f"Deleted metadata for faiss_id {index}, but FAISS index may be inconsistent")
        
        logging.info("Successfully deleted gold standard", extra={
            "action": "delete_gold_standard",
            "index": index
        })
        
        return {"message": f"Successfully deleted gold standard at index {index}"}
            
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logging.error("Error deleting gold standard", extra={
            "action": "delete_gold_standard",
            "error": str(e),
            "error_type": type(e).__name__,
            "index": index
        })
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting gold standard: {str(e)}"
        ) 