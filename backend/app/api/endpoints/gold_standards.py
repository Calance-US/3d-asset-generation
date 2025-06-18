from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.rag import get_rag_service, get_vector_store, get_metadata_service
from app.config.settings import settings
from app.schemas.schemas import EnhancedPromptResponse, EnhancedConfigSchema, SnippetSchema, SnippetType
from app.utils import create_embedding_text, coerce_to_schema
from openai import AsyncOpenAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import aiohttp
import json
import logging
import asyncio
from app.models import GoldStandardUploadStatus
from app.database.db_config import SessionLocal, get_db
from sqlalchemy.orm import Session
import uuid
import re
import hashlib
from datetime import datetime
import traceback
from app.services.rag.embedding_service import EmbeddingService
from app.utils.embedding_utils import build_embedding_text_from_config
from app.models import SnippetMetadata

router = APIRouter()

class GoldStandardCreate(BaseModel):
    html: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None

class GoldStandardUpdate(BaseModel):
    html: str = ""
    metadata: Dict[str, Any]

class GoldStandardResponse(BaseModel):
    id: int
    metadata: Dict[str, Any]
    distance: float = None
    html: str = None

class HtmlAnalysisRequest(BaseModel):
    html: str
    provider: str = "openai"  # Default to OpenAI

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

def build_gold_standard_prompt(html_content: str) -> str:
    schema_json = json.dumps(EnhancedConfigSchema.model_json_schema(), indent=2)
    prompt = settings.GOLD_STANDARD_ANALYSIS_PROMPT.format(
        json_schema=schema_json,
        html_content=html_content
    )
    return prompt

def normalize_snippet_types(snippets):
    """Ensure all snippets are dicts and snippet_type is valid, else set to 'miscellaneous'."""
    allowed_types = {e.value for e in SnippetType}
    normalized = []
    for snippet in snippets:
        # Convert to dict if it's a Pydantic model
        if hasattr(snippet, 'model_dump'):
            snippet = snippet.model_dump(mode='python', by_alias=True)
        # Map invalid snippet_type to 'miscellaneous'
        if 'snippet_type' in snippet and snippet['snippet_type'] not in allowed_types:
            snippet['snippet_type'] = 'miscellaneous'
        normalized.append(snippet)
    return normalized

@router.post("/analyze", response_model=EnhancedPromptResponse)
async def analyze_html(request: HtmlAnalysisRequest):
    """Analyze HTML content and extract configuration and topic."""
    try:
        # Create a prompt for the LLM to analyze the HTML
        analysis_prompt = build_gold_standard_prompt(request.html)

        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            client = None
            logging.warning("OpenAI API key not found")

        # Initialize Google Gemini client if API key is available
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            gemini_model = None
            logging.warning("Google API key not found")

        generated_text = None

        if request.provider == "openai":
            if not client:
                raise HTTPException(status_code=400, detail="OpenAI API key not configured")

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7
            )

            generated_text = response.choices[0].message.content

        elif request.provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": analysis_prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=500, detail="Failed to generate with Ollama")

                    result = await response.json()
                    generated_text = result.get("response", "")

        elif request.provider == "gemini":
            if not gemini_model:
                raise HTTPException(status_code=400, detail="Google API key not configured")

            response = gemini_model.generate_content(
                analysis_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            generated_text = response.text

        else:
            raise HTTPException(status_code=400, detail="Invalid provider specified")

        if not generated_text:
            raise HTTPException(status_code=500, detail="No response from LLM")

        # Log the raw LLM response
        logging.info("Raw LLM response:", extra={
            "action": "analyze_html",
            "provider": request.provider,
            "response": generated_text
        })

        # Clean the response to ensure it's valid JSON
        try:
            # Remove any markdown code block markers
            cleaned_text = generated_text.replace("```json", "").replace("```", "").strip()
            # Try to find the first { and last }
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx]

            # Log the cleaned response
            logging.info("Cleaned LLM response:", extra={
                "action": "analyze_html",
                "provider": request.provider,
                "response": cleaned_text
            })

            # Validate JSON structure
            enhanced_config = json.loads(cleaned_text)
            # Normalize snippet types before any validation
            if 'snippets' in enhanced_config:
                enhanced_config['snippets'] = normalize_snippet_types(enhanced_config['snippets'])
            
            # Log the parsed configuration
            logging.info("Parsed configuration:", extra={
                "action": "analyze_html",
                "provider": request.provider,
                "config": json.dumps(enhanced_config, indent=2)
            })

            # Validate required fields
            required_fields = [
                "topic_name", "key_concepts", "education_level", "learning_objectives",
                "interactive_features", "components", "materials", "lights",
                "interactive_description", "animated_elements", "intro_narration_texts", 
                "supporting_narration_texts", "scene_description", "snippets"
            ]
            missing_fields = [field for field in required_fields if field not in enhanced_config]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

            # Validate snippets structure
            if not enhanced_config.get("snippets"):
                raise ValueError("Response must include at least one snippet")
                
            for snippet in enhanced_config.get("snippets", []):
                snippet_fields = ["snippet_type", "summary", "embedding_text", "html_snippet"]
                missing_snippet_fields = [field for field in snippet_fields if field not in snippet]
                if missing_snippet_fields:
                    raise ValueError(f"Missing required snippet fields: {', '.join(missing_snippet_fields)}")
                
                # No need to raise error for invalid snippet_type, as normalization guarantees validity

            # Clamp light intensity values to 1.0 before schema validation
            if 'lights' in enhanced_config:
                for light in enhanced_config['lights']:
                    if 'intensity' in light and isinstance(light['intensity'], (int, float)):
                        if light['intensity'] > 1.0:
                            light['intensity'] = 1.0

            return EnhancedPromptResponse(**enhanced_config)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logging.error(f"Raw response: {generated_text}")
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM response as JSON: {str(e)}")

    except Exception as e:
        logging.error("Error analyzing HTML", extra={
            "action": "analyze_html",
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=str(e))

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

async def process_with_retry(file: UploadFile, upload_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """Process a file with retry logic."""
    for attempt in range(max_retries):
        try:
            return await process_file(file, upload_id)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logging.warning(f"Retry {attempt + 1}/{max_retries} for file {file.filename}: {str(e)}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def process_file(file: UploadFile, upload_id: str) -> Dict[str, Any]:
    """Process a single file."""
    file_result = {"filename": file.filename, "status": "pending", "snippets": [], "error": None}
    db = SessionLocal()
    try:
        html = (await file.read()).decode("utf-8")
        class DummyRequest:
            def __init__(self, html):
                self.html = html
                self.provider = "openai"
        try:
            # Get enhanced config from LLM
            enhanced_config = await analyze_html(DummyRequest(html))
            # Convert to plain dict (bulletproof) if it's a Pydantic model
            import json as _json
            if hasattr(enhanced_config, 'model_dump_json'):
                enhanced_config_dict = _json.loads(enhanced_config.model_dump_json())
            elif hasattr(enhanced_config, 'model_dump'):
                enhanced_config_dict = enhanced_config.model_dump(mode='python', by_alias=True)
            else:
                enhanced_config_dict = enhanced_config
            # Normalize snippet types before coercion/validation
            if 'snippets' in enhanced_config_dict:
                enhanced_config_dict['snippets'] = normalize_snippet_types(enhanced_config_dict['snippets'])
            # Coerce and validate all fields using the schema
            enhanced_config_dict = coerce_to_schema(enhanced_config_dict, EnhancedConfigSchema)
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
                    "error": None
                }
                try:
                    # Generate hash for deduplication
                    snippet_hash = hashlib.sha256(snippet.html_snippet.encode()).hexdigest()
                    # Check for duplicates
                    metadata_service = get_metadata_service()
                    existing = await metadata_service.get_by_hash(snippet_hash)
                    # Patch: Also check vector store for snippet_hash
                    in_vector_store = vector_store.has_snippet_hash(snippet_hash, db)
                    if existing or in_vector_store:
                        # Update existing snippet in metadata store if present
                        if existing:
                            await metadata_service.update_snippet(snippet_hash, {
                                "updated_at": datetime.utcnow(),
                                "retry_count": existing.retry_count + 1
                            })
                        snippet_result["status"] = "duplicate"
                        snippet_result["message"] = "Snippet already exists"
                        snippet_results.append(snippet_result)
                        continue
                    # Store snippet metadata
                    snippet_metadata = {
                        "id": str(uuid.uuid4()),  # Ensure id is a string
                        "snippet_hash": snippet_hash,
                        "snippet_type": snippet.snippet_type.value if hasattr(snippet.snippet_type, "value") else str(snippet.snippet_type),
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
                        "education_level": validated_config.education_level.value if hasattr(validated_config.education_level, "value") else str(validated_config.education_level),
                        "learning_objectives": validated_config.learning_objectives
                    }
                    # Generate a new unique faiss_id (max+1 for demo, use sequence in prod)
                    max_faiss_id = db.query(SnippetMetadata.faiss_id).order_by(SnippetMetadata.faiss_id.desc()).first()
                    faiss_id = (max_faiss_id[0] if max_faiss_id and max_faiss_id[0] is not None else 0) + 1
                    # Add to metadata store with faiss_id
                    snippet_obj = await metadata_service.add_snippet(snippet_metadata, faiss_id=faiss_id)
                    # Add to vector store
                    vector_store.add_visualization(embedding, faiss_id)
                    snippet_result["status"] = "success"
                except Exception as e:
                    snippet_result["status"] = "error"
                    snippet_result["error"] = str(e)
                snippet_results.append(snippet_result)
            file_result["snippets"] = snippet_results
            # Save vector store
            vector_store.save(settings.VECTOR_STORE_PATH)
        except Exception as e:
            file_result["status"] = "error"
            if isinstance(e, HTTPException):
                file_result["error"] = f"HTTPException: {getattr(e, 'detail', '')}"
            else:
                file_result["error"] = f"{type(e).__name__}: {str(e)}"
            logging.error(f"Error processing file {file.filename}: {e}\n{traceback.format_exc()}")
    except Exception as e:
        file_result["status"] = "error"
        if isinstance(e, HTTPException):
            file_result["error"] = f"HTTPException: {getattr(e, 'detail', '')}"
        else:
            file_result["error"] = f"{type(e).__name__}: {str(e)}"
        logging.error(f"Error reading file {file.filename}: {e}\n{traceback.format_exc()}")
    finally:
        db.close()
    return file_result 