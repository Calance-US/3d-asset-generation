from sqlalchemy import Column, Integer, String, ForeignKey, Table, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from .database.db_config import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from typing import Dict, Any, Optional

# Association table for many-to-many relationship between prompts and tags
prompt_tags = Table(
    'prompt_tags',
    Base.metadata,
    Column('prompt_id', Integer, ForeignKey('prompts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

# Association table for many-to-many relationship between visualizations and tags
visualization_tags = Table(
    'visualization_tags',
    Base.metadata,
    Column('visualization_id', Integer, ForeignKey('visualizations.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    subject = Column(String, index=True)
    content = Column(Text)
    embedding = Column(JSON)  # Store embeddings as JSON
    category = Column(String, nullable=True)
    key_concepts = Column(Text, nullable=True)
    education_level = Column(String(50), nullable=True)
    learning_objectives = Column(Text, nullable=True)
    interactive_features = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = relationship("Tag", secondary=prompt_tags, back_populates="prompts")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prompts = relationship("Prompt", secondary=prompt_tags, back_populates="tags")
    visualizations = relationship("Visualization", secondary=visualization_tags, back_populates="tags")

class HistoryEntry(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    user_query = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    provider = Column(String(50), nullable=True)
    components = Column(JSON, nullable=True, default=list)
    materials = Column(JSON, nullable=True, default=list)
    lights = Column(JSON, nullable=True, default=list)
    render_settings = Column(JSON, nullable=True, default=dict)
    animation_speed = Column(Float, nullable=True)
    intro_narration_texts = Column(JSON, nullable=True, default=list)
    supporting_narration_texts = Column(JSON, nullable=True, default=list)
    scene_description = Column(String)
    generation_time = Column(Float)
    
    # Relationships
    prompt = relationship("Prompt")

class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    subject = Column(String, index=True)
    html_content = Column(Text)
    config = Column(JSON)
    embedding = Column(JSON)  # Store embeddings as JSON for similarity search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = relationship("Tag", secondary=visualization_tags, back_populates="visualizations")

class GoldStandardUploadStatus(Base):
    __tablename__ = "gold_standard_upload_status"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="pending")  # pending, processing, completed, error
    result = Column(Text, nullable=True)  # Store JSON as text in SQLite
    error_message = Column(Text, nullable=True)

    def set_result(self, result: Dict[str, Any]):
        """Set the result field, converting dict to JSON string."""
        self.result = json.dumps(result) if result else None

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the result field, converting JSON string to dict."""
        return json.loads(self.result) if self.result else None

class SnippetMetadata(Base):
    """SQLAlchemy model for snippet metadata."""
    __tablename__ = "snippet_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snippet_hash = Column(String, unique=True, index=True)
    snippet_type = Column(String)
    summary = Column(String)
    embedding_text = Column(String)
    html_snippet = Column(String)
    filename = Column(String)
    upload_id = Column(String(36))
    llm_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validation_status = Column(String)
    validation_errors = Column(JSON)
    retry_count = Column(Integer, default=0)
    topic = Column(String)
    key_concepts = Column(String)
    education_level = Column(String)
    learning_objectives = Column(String)