from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ...database.database import get_db
from ...models import Visualization
from ...schemas.visualization import VisualizationCreate, VisualizationResponse
from ...services.prompt_selector import PromptSelector
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.vector_store import get_vector_store
from app.utils.embedding_utils import build_embedding_text_from_config
import json
from pydantic import BaseModel

router = APIRouter()
prompt_selector = PromptSelector()

@router.post("/save", response_model=VisualizationResponse)
def save_visualization(visualization: VisualizationCreate, db: Session = Depends(get_db)):
    """Save a visualization to the database."""
    try:
        # Generate embedding for the visualization
        embedding = prompt_selector.model.encode(
            f"{visualization.topic} {visualization.subject}",
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Create new visualization
        db_visualization = Visualization(
            topic=visualization.topic,
            subject=visualization.subject,
            html_content=visualization.html_content,
            config=visualization.config,
            embedding=embedding.tolist()
        )

        db.add(db_visualization)
        db.commit()
        db.refresh(db_visualization)

        return db_visualization
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[VisualizationResponse])
def get_visualizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all visualizations."""
    visualizations = db.query(Visualization).offset(skip).limit(limit).all()
    return visualizations

@router.get("/{visualization_id}", response_model=VisualizationResponse)
def get_visualization(visualization_id: int, db: Session = Depends(get_db)):
    """Get a specific visualization by ID."""
    visualization = db.query(Visualization).filter(Visualization.id == visualization_id).first()
    if visualization is None:
        raise HTTPException(status_code=404, detail="Visualization not found")
    return visualization

class SimilarVisualizationRequest(BaseModel):
    prompt: str
    config: Optional[Dict[str, Any]] = None
    top_k: int = 5

@router.post("/retrieve_similar", response_model=List[VisualizationResponse])
async def retrieve_similar_visualizations(
    request: SimilarVisualizationRequest,
    db: Session = Depends(get_db)
):
    """Retrieve similar visualizations based on user prompt and/or config for context injection."""
    # Combine prompt and config for embedding if config is provided
    if request.config:
        embedding_input = build_embedding_text_from_config(request.config)
    else:
        embedding_input = request.prompt
    embedding = EmbeddingService.generate_embedding(embedding_input)
    vector_store = get_vector_store()
    # Retrieve top_k similar visualizations from the vector store
    similar = await vector_store.get_similar_visualizations(embedding, limit=request.top_k)
    # Optionally, fetch full visualization details from the DB using metadata (e.g., by id)
    results = []
    for item in similar:
        meta = item['metadata']
        # If you store visualization id in metadata, fetch from DB for full details
        viz_id = meta.get('id')
        if viz_id:
            db_viz = db.query(Visualization).filter_by(id=viz_id).first()
            if db_viz:
                results.append(db_viz)
            else:
                # Fallback: return metadata as VisualizationResponse
                results.append(VisualizationResponse(**meta))
        else:
            # Fallback: return metadata as VisualizationResponse
            results.append(VisualizationResponse(**meta))
    return results 