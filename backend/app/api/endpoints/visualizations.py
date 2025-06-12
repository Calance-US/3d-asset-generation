from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database.database import get_db
from ...models import Visualization
from ...schemas.visualization import VisualizationCreate, VisualizationResponse
from ...services.prompt_selector import PromptSelector

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