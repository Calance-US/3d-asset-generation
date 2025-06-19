import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from .database.db_config import Base

# Association table for many-to-many relationship between prompts and tags
prompt_tags = Table(
    "prompt_tags",
    Base.metadata,
    Column("prompt_id", Integer, ForeignKey("prompts.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

# Association table for many-to-many relationship between visualizations and tags
visualization_tags = Table(
    "visualization_tags",
    Base.metadata,
    Column("visualization_id", Integer, ForeignKey("visualizations.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
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

    # Relationships
    tags = relationship("Tag", secondary=prompt_tags, back_populates="prompts")
    validation_errors = relationship("ValidationError", back_populates="prompt")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prompts = relationship("Prompt", secondary=prompt_tags, back_populates="tags")
    visualizations = relationship(
        "Visualization", secondary=visualization_tags, back_populates="tags"
    )


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

    # Enhanced error tracking fields
    generation_attempts = Column(Integer, default=1)
    final_quality_score = Column(Numeric(3, 1), nullable=True)
    validation_errors_count = Column(Integer, default=0)

    # Relationships
    tags = relationship(
        "Tag", secondary=visualization_tags, back_populates="visualizations"
    )
    validation_errors = relationship("ValidationError", back_populates="visualization")


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


class ValidationError(Base):
    """SQLAlchemy model for validation errors."""

    __tablename__ = "validation_errors"

    id = Column(Integer, primary_key=True, index=True)
    visualization_id = Column(Integer, ForeignKey("visualizations.id"), nullable=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=True)
    phase = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    error_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    location = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    quality_score = Column(Numeric(3, 1), nullable=True)
    provider = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    visualization = relationship("Visualization", back_populates="validation_errors")
    prompt = relationship("Prompt", back_populates="validation_errors")


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
    faiss_id = Column(sa.BigInteger, unique=True, nullable=True)


class AsyncTask(Base):
    """SQLAlchemy model for async task management."""

    __tablename__ = "async_tasks"

    id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    task_type = Column(
        String(50), nullable=False, index=True
    )  # visualization_generation, batch_validation, etc.
    status = Column(
        String(20), nullable=False, index=True, default="pending"
    )  # pending, running, completed, failed, cancelled, timeout
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    request_data = Column(JSON, nullable=False)  # Original request parameters
    result = Column(JSON, nullable=True)  # Final task result
    error_message = Column(Text, nullable=True)  # Error details if task failed
    progress_percentage = Column(Integer, default=0)  # Overall progress (0-100)
    current_stage = Column(String(50), nullable=True)  # Current stage name
    total_stages = Column(Integer, default=1)  # Total number of stages
    expires_at = Column(DateTime, nullable=True)  # When task should be cleaned up

    # Relationships
    stages = relationship(
        "AsyncTaskStage", back_populates="task", cascade="all, delete-orphan"
    )

    def set_request_data(self, data: Dict[str, Any]):
        """Set the request_data field, converting dict to JSON."""
        self.request_data = data

    def get_request_data(self) -> Dict[str, Any]:
        """Get the request_data field."""
        return self.request_data or {}

    def set_result(self, result: Dict[str, Any]):
        """Set the result field, converting dict to JSON."""
        self.result = result

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the result field."""
        return self.result

    def is_finished(self) -> bool:
        """Check if task is in a finished state."""
        return self.status in ["completed", "failed", "cancelled", "timeout"]

    def is_expired(self) -> bool:
        """Check if task has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class AsyncTaskStage(Base):
    """SQLAlchemy model for async task stages."""

    __tablename__ = "async_task_stages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("async_tasks.id"), nullable=False)
    name = Column(
        String(50), nullable=False
    )  # llm_generation, validation_attempt_1, etc.
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, running, completed, failed
    order_index = Column(Integer, nullable=False)  # Order of stage execution
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0)  # Stage progress (0-100)
    message = Column(Text, nullable=True)  # Status message
    details = Column(JSON, nullable=True)  # Additional stage details
    error_message = Column(Text, nullable=True)  # Error details if stage failed

    # Relationships
    task = relationship("AsyncTask", back_populates="stages")

    def set_details(self, details: Dict[str, Any]):
        """Set the details field, converting dict to JSON."""
        self.details = details

    def get_details(self) -> Dict[str, Any]:
        """Get the details field."""
        return self.details or {}

    def is_finished(self) -> bool:
        """Check if stage is in a finished state."""
        return self.status in ["completed", "failed"]
