from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class VisualizationBase(BaseModel):
    topic: str
    subject: str
    html_content: str
    config: Dict[str, Any]

class VisualizationCreate(VisualizationBase):
    pass

class VisualizationResponse(VisualizationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    embedding: Optional[list] = None

    class Config:
        from_attributes = True 