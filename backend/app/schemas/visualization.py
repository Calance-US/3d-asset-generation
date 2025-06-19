from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


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
