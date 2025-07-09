import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    Boolean,
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


class AIProvider(Base):
    """SQLAlchemy model for AI provider configurations."""

    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)  # openai/google/anthropic
    description = Column(String, nullable=True)
    config = Column(JSON, nullable=True)  # API settings
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    history_entries = relationship("HistoryEntry", back_populates="ai_provider")
    validation_errors = relationship("ValidationError", back_populates="ai_provider")

    def __repr__(self):
        return f"<AIProvider(id={self.id}, name='{self.name}', is_active={self.is_active})>"


class TagCategory(Base):
    """SQLAlchemy model for hierarchical tag categories."""

    __tablename__ = "tag_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)  # Subject/Grade/Difficulty
    description = Column(String, nullable=True)
    parent_category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Self-referential relationship for hierarchy
    parent = relationship("TagCategory", remote_side=[id], back_populates="children")
    children = relationship("TagCategory", back_populates="parent")

    # Relationship with tags
    tags = relationship("Tag", back_populates="category")

    def __repr__(self):
        return f"<TagCategory(id={self.id}, name='{self.name}', parent_id={self.parent_category_id})>"


class User(Base):
    """SQLAlchemy model for users with Keycloak SSO integration."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(
        String, unique=True, index=True, nullable=False
    )  # Keycloak UUID
    provider = Column(
        String, nullable=False, default="keycloak"
    )  # keycloak/google/github
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role = Column(String, nullable=False, default="student")  # cached from Keycloak
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_deleted = Column(Boolean, nullable=False, default=False)

    # Relationships
    prompts = relationship("Prompt", back_populates="user")
    visualizations = relationship("Visualization", back_populates="user")
    history_entries = relationship("HistoryEntry", back_populates="user")
    shared_content_owned = relationship(
        "SharedContent",
        foreign_keys="SharedContent.owner_user_id",
        back_populates="owner",
    )
    shared_content_received = relationship(
        "SharedContent",
        foreign_keys="SharedContent.target_user_id",
        back_populates="target",
    )
    async_tasks = relationship("AsyncTask", back_populates="user")

    def is_admin_user(self) -> bool:
        """Check if user has admin role."""
        return self.role in ["admin", "super_admin"]

    def is_active_user(self) -> bool:
        """Check if user is active (not deleted)."""
        return not self.is_deleted

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"


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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="prompts")
    tags = relationship("Tag", secondary=prompt_tags, back_populates="prompts")
    validation_errors = relationship("ValidationError", back_populates="prompt")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    # Relationships
    category = relationship("TagCategory", back_populates="tags")
    prompts = relationship("Prompt", secondary=prompt_tags, back_populates="tags")
    visualizations = relationship(
        "Visualization", secondary=visualization_tags, back_populates="tags"
    )


class HistoryEntry(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    visualization_id = Column(Integer, ForeignKey("visualizations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_query = Column(Text)
    response = Column(Text)
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=True)
    scene_description = Column(Text, nullable=True)
    components = Column(JSON, nullable=True, default=list)
    materials = Column(JSON, nullable=True, default=list)
    lights = Column(JSON, nullable=True, default=list)
    render_settings = Column(JSON, nullable=True, default=dict)
    intro_narration_texts = Column(JSON, nullable=True, default=list)
    supporting_narration_texts = Column(JSON, nullable=True, default=list)
    animation_speed = Column(Float, nullable=True)
    generation_time = Column(Float, nullable=True)
    visibility = Column(String, nullable=False, default="private")  # private/public
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prompt = relationship("Prompt")
    visualization = relationship("Visualization")
    user = relationship("User", back_populates="history_entries")
    ai_provider = relationship("AIProvider", back_populates="history_entries")


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    subject = Column(String, index=True)
    html_content = Column(Text)
    config = Column(JSON)
    embedding = Column(JSON)  # Store embeddings as JSON for similarity search
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Enhanced error tracking fields
    generation_attempts = Column(Integer, default=1)
    final_quality_score = Column(Numeric(3, 1), nullable=True)
    validation_errors_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="visualizations")
    tags = relationship(
        "Tag", secondary=visualization_tags, back_populates="visualizations"
    )
    validation_errors = relationship("ValidationError", back_populates="visualization")


class SharedContent(Base):
    """SQLAlchemy model for content sharing between users."""

    __tablename__ = "shared_content"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String, nullable=False)  # prompt/visualization
    content_id = Column(Integer, nullable=False)
    permission_level = Column(String, nullable=False, default="view")  # view/edit
    shared_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship(
        "User", foreign_keys=[owner_user_id], back_populates="shared_content_owned"
    )
    target = relationship(
        "User", foreign_keys=[target_user_id], back_populates="shared_content_received"
    )

    def __repr__(self):
        return f"<SharedContent(id={self.id}, content_type='{self.content_type}', content_id={self.content_id})>"


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
    # snippet_id = Column(Integer, ForeignKey("snippet_metadata.id"), nullable=True)  # Temporarily disabled - DB column doesn't exist
    phase = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    error_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    location = Column(String(200), nullable=True)
    context = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    quality_score = Column(Numeric(3, 1), nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    visualization = relationship("Visualization", back_populates="validation_errors")
    prompt = relationship("Prompt", back_populates="validation_errors")
    # snippet = relationship("SnippetMetadata", back_populates="validation_error_records")  # Temporarily disabled - DB column doesn't exist
    ai_provider = relationship("AIProvider", back_populates="validation_errors")


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

    # Relationships
    # validation_error_records = relationship("ValidationError", back_populates="snippet")  # Temporarily disabled - DB column doesn't exist


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
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User who created the task

    # Relationships
    stages = relationship(
        "AsyncTaskStage", back_populates="task", cascade="all, delete-orphan"
    )
    user = relationship("User", back_populates="async_tasks")

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


class Local3DModel(Base):
    """SQLAlchemy model for locally stored 3D models."""
    
    __tablename__ = "local_3d_models"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # File information
    model_name = Column(String(100), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Absolute path to model file
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    
    # Metadata for search
    category = Column(String(50), nullable=True, index=True)
    subject = Column(String(50), nullable=True, index=True)
    tags = Column(JSON, nullable=True, default=list)
    description = Column(Text, nullable=True)
    
    # Technical metadata
    model_type = Column(String(20), nullable=False, default="gltf")
    has_animations = Column(Boolean, default=False)
    has_textures = Column(Boolean, default=False)
    has_materials = Column(Boolean, default=False)
    triangle_count = Column(Integer, nullable=True)
    vertex_count = Column(Integer, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Local3DModel(id={self.id}, name='{self.model_name}', path='{self.file_path}')>"
    
    def get_api_url(self) -> str:
        """Get the API URL to serve this model."""
        from ..config.settings import get_settings
        settings = get_settings()
        return f"{settings.MODEL_API_BASE_URL}/api/v1/local-models/{self.id}/file"
    
    def get_relative_path(self) -> str:
        """Get relative path for use in generated HTML."""
        from ..config.settings import get_settings
        settings = get_settings()
        return f"{settings.MODEL_API_BASE_URL}/api/v1/local-models/{self.id}/file"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    history_entry_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, history_entry_id={self.history_entry_id}, user_id={self.user_id})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True)
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    timestamp = Column(DateTime, default=datetime.utcnow)

    chat_session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, type={self.message_type})>"
