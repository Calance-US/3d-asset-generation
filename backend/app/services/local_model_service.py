import os
import hashlib
import json
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import Local3DModel
from ..config.settings import get_settings
from ..services.rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


class LocalModelService:
    """Service for managing locally stored 3D models."""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_dir = Path(settings.MODEL_STORAGE_BASE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_and_index_models(self) -> Dict[str, Any]:
        """Scan the models directory and index all GLTF files."""
        indexed_count = 0
        errors = []
        
        logger.info(f"Scanning models directory: {self.base_dir}")
        
        for model_file in self.base_dir.rglob("*.glb"):
            try:
                # Check if model already exists
                file_hash = self._calculate_file_hash(model_file)
                existing_model = self.db.query(Local3DModel).filter(
                    Local3DModel.file_hash == file_hash
                ).first()
                
                if existing_model:
                    logger.debug(f"Model already exists: {model_file}")
                    continue
                
                # Extract metadata from filename and path
                metadata = self._extract_metadata_from_path(model_file)
                
                # Create model record
                model = Local3DModel(
                    model_name=metadata.get("name", model_file.stem),
                    filename=model_file.name,
                    file_path=str(model_file.absolute()),
                    file_size=model_file.stat().st_size,
                    file_hash=file_hash,
                    category=metadata.get("category"),
                    subject=metadata.get("subject"),
                    tags=metadata.get("tags", []),
                    description=metadata.get("description"),
                    model_type="glb"
                )
                
                self.db.add(model)
                indexed_count += 1
                logger.info(f"Indexed new model: {model_file}")
                
            except Exception as e:
                error_msg = f"Error indexing {model_file}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        try:
            self.db.commit()
            logger.info(f"Successfully indexed {indexed_count} new models")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Database error during indexing: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {
            "indexed_count": indexed_count,
            "errors": errors
        }
    
    def search_models(
        self,
        query: str,
        category: Optional[str] = None,
        subject: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Local3DModel]:
        """Search for models using semantic similarity and metadata filters."""
        
        # Start with metadata filters
        db_query = self.db.query(Local3DModel).filter(Local3DModel.is_active == True)
        
        if category:
            db_query = db_query.filter(Local3DModel.category == category)
        
        if subject:
            db_query = db_query.filter(Local3DModel.subject == subject)
        
        if tags:
            for tag in tags:
                db_query = db_query.filter(Local3DModel.tags.contains([tag]))
        
        # Get all matching models
        models = db_query.all()
        
        if not query or not models:
            return models[:limit]
        
        # Perform hybrid search (semantic + keyword)
        try:
            query_embedding = EmbeddingService.generate_embedding(query)
            query_lower = query.lower()
            
            # Calculate similarities and keyword matches
            model_scores = []
            for model in models:
                # Create search text from model metadata
                search_text = f"{model.model_name} {model.description or ''} {' '.join(model.tags or [])}"
                model_embedding = EmbeddingService.generate_embedding(search_text)
                
                # Calculate cosine similarity
                similarity = self._calculate_cosine_similarity(query_embedding, model_embedding)
                
                # Check for keyword matches
                keyword_match = False
                if query_lower in model.model_name.lower():
                    keyword_match = True
                    similarity = max(similarity, 0.6)  # Boost similarity for keyword matches
                
                # Check if query appears in tags
                if model.tags:
                    for tag in model.tags:
                        if query_lower in tag.lower():
                            keyword_match = True
                            similarity = max(similarity, 0.5)  # Boost similarity for tag matches
                
                # Accept models that meet semantic threshold OR have keyword matches
                if similarity >= settings.MODEL_SEARCH_SIMILARITY_THRESHOLD or keyword_match:
                    model_scores.append((model, similarity))
            
            # Sort by similarity and return top results
            model_scores.sort(key=lambda x: x[1], reverse=True)
            return [model for model, score in model_scores[:limit]]
            
        except Exception as e:
            logger.warning(f"Hybrid search failed, falling back to metadata search: {e}")
            return models[:limit]
    
    def get_models_for_visualization(
        self,
        topic: str,
        subject: str,
        components: List[Dict[str, str]]
    ) -> List[Local3DModel]:
        """Get relevant models for a specific visualization topic."""
        
        # Create search queries based on components
        search_queries = []
        
        # Add topic-based search
        search_queries.append(topic)
        
        # Add component-based searches
        for component in components:
            component_name = component.get("component_name", "")
            component_desc = component.get("component_description", "")
            search_queries.append(f"{component_name} {component_desc}")
        
        # Search for models
        all_models = []
        for query in search_queries:
            models = self.search_models(query, subject=subject, limit=5)
            all_models.extend(models)
        
        # Remove duplicates and return top results
        unique_models = list({model.id: model for model in all_models}.values())
        return unique_models[:10]  # Return top 10 relevant models
    
    def get_model_by_id(self, model_id: int) -> Optional[Local3DModel]:
        """Get a model by its ID."""
        return self.db.query(Local3DModel).filter(
            and_(
                Local3DModel.id == model_id,
                Local3DModel.is_active == True
            )
        ).first()
    
    def update_usage_count(self, model_id: int):
        """Update usage count for a model."""
        model = self.get_model_by_id(model_id)
        if model:
            model.usage_count += 1
            model.last_used_at = datetime.utcnow()
            try:
                self.db.commit()
                logger.debug(f"Updated usage count for model {model_id}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to update usage count for model {model_id}: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _calculate_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.warning(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    def _extract_metadata_from_path(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path structure."""
        metadata = {
            "name": file_path.stem,
            "category": None,
            "subject": None,
            "tags": [],
            "description": None
        }
        
        # Parse path structure: models/subject/subject/filename.glb
        try:
            path_parts = file_path.relative_to(self.base_dir).parts
            
            if len(path_parts) >= 1:
                metadata["subject"] = path_parts[0]
            
            if len(path_parts) >= 2:
                metadata["category"] = path_parts[1]
            
            # Extract tags from filename (e.g., "resistor_electronic_circuit.glb")
            filename_parts = file_path.stem.split("_")
            if len(filename_parts) > 1:
                metadata["tags"] = filename_parts[1:]
            
            # Create description from metadata
            desc_parts = []
            if metadata["category"]:
                desc_parts.append(f"Category: {metadata['category']}")
            if metadata["subject"]:
                desc_parts.append(f"Subject: {metadata['subject']}")
            if metadata["tags"]:
                desc_parts.append(f"Tags: {', '.join(metadata['tags'])}")
            
            if desc_parts:
                metadata["description"] = f"3D model for {metadata['name']} - {' | '.join(desc_parts)}"
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from path {file_path}: {e}")
        
        return metadata
    
    def get_categories(self) -> List[str]:
        """Get list of all available categories."""
        categories = self.db.query(Local3DModel.category).filter(
            and_(
                Local3DModel.category.isnot(None),
                Local3DModel.is_active == True
            )
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]
    
    def get_subjects(self) -> List[str]:
        """Get list of all available subjects."""
        subjects = self.db.query(Local3DModel.subject).filter(
            and_(
                Local3DModel.subject.isnot(None),
                Local3DModel.is_active == True
            )
        ).distinct().all()
        
        return [subj[0] for subj in subjects if subj[0]]
    
    def get_tags(self) -> List[str]:
        """Get list of all available tags."""
        all_tags = []
        models = self.db.query(Local3DModel.tags).filter(
            and_(
                Local3DModel.tags.isnot(None),
                Local3DModel.is_active == True
            )
        ).all()
        
        for model in models:
            if model.tags:
                all_tags.extend(model.tags)
        
        # Return unique tags
        return list(set(all_tags)) 