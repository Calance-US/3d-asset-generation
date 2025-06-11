from sqlalchemy import Column, Integer, String, ForeignKey, Table, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from .database.db_config import Base
from datetime import datetime

# Association table for many-to-many relationship between prompts and tags
prompt_tags = Table(
    'prompt_tags',
    Base.metadata,
    Column('prompt_id', Integer, ForeignKey('prompts.id')),
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

class HistoryEntry(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"))
    user_query = Column(Text)
    response = Column(Text)
    provider = Column(String(50), nullable=True)
    components = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)
    lights = Column(Text, nullable=True)
    render_settings = Column(Text, nullable=True)
    animation_speed = Column(Float, nullable=True)
    intro_narration_texts = Column(Text, nullable=True)
    supporting_narration_texts = Column(Text, nullable=True)
    scene_description = Column(Text, nullable=True)
    generation_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    prompt = relationship("Prompt") 