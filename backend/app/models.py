from sqlalchemy import Column, Integer, String, ForeignKey, Table, Float, DateTime, Text
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
    category = Column(String, nullable=True)
    tags = relationship("Tag", secondary=prompt_tags, back_populates="prompts")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    prompts = relationship("Prompt", secondary=prompt_tags, back_populates="tags")

class HistoryEntry(Base):
    __tablename__ = "history"

    id = Column(String, primary_key=True, index=True)
    prompt = Column(Text)
    provider = Column(String)
    subject = Column(String, nullable=True)
    html = Column(Text)
    timestamp = Column(DateTime) 