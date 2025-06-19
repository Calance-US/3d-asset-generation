"""Utility functions for the application."""

import asyncio
import hashlib
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, UploadFile

from app.config.settings import settings
from app.database.db_config import SessionLocal
from app.models import SnippetMetadata
from app.schemas.schemas import EnhancedConfigSchema, HtmlAnalysisRequest
from app.services.rag import get_metadata_service, get_vector_store
from app.services.rag.embedding_service import EmbeddingService
from app.utils.coerce_utils import coerce_to_schema
from app.utils.datetime_utils import serialize_datetimes
from app.utils.embedding_utils import (
    build_embedding_text_from_config,
    create_embedding_text,
)
from app.utils.html_utils import analyze_html, parse_html_content
from app.utils.snippet_utils import normalize_snippet_types

__all__ = ["create_embedding_text", "parse_html_content", "serialize_datetimes"]


async def process_with_retry(
    file: UploadFile, upload_id: str, max_retries: int = 3
) -> Dict[str, Any]:
    """Process a file with retry logic."""
    for attempt in range(max_retries):
        try:
            return await process_file(file, upload_id)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logging.warning(
                f"Retry {attempt + 1}/{max_retries} for file {file.filename}: {str(e)}"
            )
            await asyncio.sleep(2**attempt)  # Exponential backoff
    return {}  # This line should never be reached, but added for type safety


async def process_file(file: UploadFile, upload_id: str) -> Dict[str, Any]:
    """Process a single file."""
    file_result = {
        "filename": file.filename,
        "status": "pending",
        "snippets": [],
        "error": None,
    }
    db = SessionLocal()
    try:
        html = (await file.read()).decode("utf-8")

        request_obj = HtmlAnalysisRequest(html=html, provider="openai")

        try:
            # Get enhanced config from LLM
            enhanced_config = await analyze_html(request_obj)
            # Convert to plain dict (bulletproof) if it's a Pydantic model
            enhanced_config_dict = enhanced_config.model_dump(
                mode="python", by_alias=True
            )
            # Normalize snippet types before coercion/validation
            if "snippets" in enhanced_config_dict:
                enhanced_config_dict["snippets"] = normalize_snippet_types(
                    enhanced_config_dict["snippets"]
                )
            # Coerce and validate all fields using the schema
            enhanced_config_dict = coerce_to_schema(
                enhanced_config_dict, EnhancedConfigSchema
            )
            # Validate against schema
            try:
                validated_config = EnhancedConfigSchema(**enhanced_config_dict)
            except Exception as e:
                raise ValueError(f"Invalid config schema: {str(e)}")
            file_result["status"] = "success"
            file_result["config"] = validated_config.dict()
            # Initialize vector_store at the start
            vector_store = get_vector_store()
            # Process snippets
            embedding_text = build_embedding_text_from_config(validated_config.dict())
            embedding = EmbeddingService.generate_embedding(embedding_text)
            snippet_results = []
            for snippet in validated_config.snippets:
                snippet_result = {
                    "snippet_type": snippet.snippet_type,
                    "summary": snippet.summary,
                    "status": "pending",
                    "error": None,
                }
                try:
                    # Generate hash for deduplication
                    snippet_hash = hashlib.sha256(
                        snippet.html_snippet.encode()
                    ).hexdigest()
                    # Check for duplicates
                    metadata_service = get_metadata_service()
                    existing = await metadata_service.get_by_hash(snippet_hash)
                    # Patch: Also check vector store for snippet_hash
                    in_vector_store = vector_store.has_snippet_hash(snippet_hash, db)
                    if existing or in_vector_store:
                        # Update existing snippet in metadata store if present
                        if existing:
                            await metadata_service.update_snippet(
                                snippet_hash,
                                {
                                    "updated_at": datetime.utcnow(),
                                    "retry_count": existing.retry_count + 1,
                                },
                            )
                        snippet_result["status"] = "duplicate"
                        snippet_result["message"] = "Snippet already exists"
                        snippet_results.append(snippet_result)
                        continue
                    # Store snippet metadata
                    snippet_metadata = {
                        "id": str(uuid.uuid4()),  # Ensure id is a string
                        "snippet_hash": snippet_hash,
                        "snippet_type": snippet.snippet_type.value
                        if hasattr(snippet.snippet_type, "value")
                        else str(snippet.snippet_type),
                        "summary": snippet.summary,
                        "embedding_text": embedding_text,
                        "html_snippet": snippet.html_snippet,
                        "filename": file.filename,
                        "upload_id": str(upload_id),  # Ensure upload_id is a string
                        "llm_version": settings.OPENAI_MODEL,
                        "validation_status": "pending",
                        "validation_errors": [],
                        "retry_count": 0,
                        "topic": validated_config.topic_name,
                        "key_concepts": validated_config.key_concepts,
                        "education_level": validated_config.education_level.value
                        if hasattr(validated_config.education_level, "value")
                        else str(validated_config.education_level),
                        "learning_objectives": validated_config.learning_objectives,
                    }
                    # Generate a new unique faiss_id (max+1 for demo, use sequence in prod)
                    # TODO: Fix SnippetMetadata import issue
                    # max_faiss_id = (
                    #     db.query(SnippetMetadata.faiss_id)
                    #     .order_by(SnippetMetadata.faiss_id.desc())
                    #     .first()
                    # )
                    # faiss_id = (
                    #     max_faiss_id[0]
                    #     if max_faiss_id and max_faiss_id[0] is not None
                    #     else 0
                    # ) + 1
                    faiss_id = 1  # Temporary fallback
                    # Add to metadata store with faiss_id
                    await metadata_service.add_snippet(
                        snippet_metadata, faiss_id=faiss_id
                    )
                    # Add to vector store
                    vector_store.add_visualization(embedding, faiss_id)
                    snippet_result["status"] = "success"
                except Exception as e:
                    snippet_result["status"] = "error"
                    snippet_result["error"] = str(e)
                snippet_results.append(snippet_result)
            file_result["snippets"] = snippet_results
        except Exception as e:
            file_result["status"] = "error"
            if isinstance(e, HTTPException):
                file_result["error"] = f"HTTPException: {getattr(e, 'detail', '')}"
            else:
                file_result["error"] = f"{type(e).__name__}: {str(e)}"
            logging.error(
                f"Error processing file {file.filename}: {e}\n{traceback.format_exc()}"
            )
    except Exception as e:
        file_result["status"] = "error"
        if isinstance(e, HTTPException):
            file_result["error"] = f"HTTPException: {getattr(e, 'detail', '')}"
        else:
            file_result["error"] = f"{type(e).__name__}: {str(e)}"
        logging.error(
            f"Error reading file {file.filename}: {e}\n{traceback.format_exc()}"
        )
    finally:
        db.close()
    return file_result
