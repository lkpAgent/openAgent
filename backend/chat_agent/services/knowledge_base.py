"""Knowledge base service."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.knowledge_base import KnowledgeBase
from ..utils.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate
from ..core.config import get_settings
from .document_processor import document_processor

logger = logging.getLogger(__name__)
settings = get_settings()


class KnowledgeBaseService:
    """Knowledge base service for managing knowledge bases."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_knowledge_base(self, kb_data: KnowledgeBaseCreate) -> KnowledgeBase:
        """Create a new knowledge base."""
        try:
            # Generate collection name for vector database
            collection_name = f"kb_{kb_data.name.lower().replace(' ', '_').replace('-', '_')}"
            
            kb = KnowledgeBase(
                name=kb_data.name,
                description=kb_data.description,
                embedding_model=kb_data.embedding_model,
                chunk_size=kb_data.chunk_size,
                chunk_overlap=kb_data.chunk_overlap,
                vector_db_type=settings.vector_db.type,
                collection_name=collection_name
            )
            
            self.db.add(kb)
            self.db.commit()
            self.db.refresh(kb)
            
            logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
            return kb
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create knowledge base: {e}")
            raise
    
    def get_knowledge_base(self, kb_id: int) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID."""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    def get_knowledge_base_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """Get knowledge base by name."""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.name == name).first()
    
    def get_knowledge_bases(self, skip: int = 0, limit: int = 50, active_only: bool = True) -> List[KnowledgeBase]:
        """Get list of knowledge bases."""
        query = self.db.query(KnowledgeBase)
        
        if active_only:
            query = query.filter(KnowledgeBase.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def update_knowledge_base(self, kb_id: int, kb_update: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
        """Update knowledge base."""
        try:
            kb = self.get_knowledge_base(kb_id)
            if not kb:
                return None
            
            # Update fields
            update_data = kb_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(kb, field, value)
            
            self.db.commit()
            self.db.refresh(kb)
            
            logger.info(f"Updated knowledge base: {kb.name} (ID: {kb.id})")
            return kb
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update knowledge base {kb_id}: {e}")
            raise
    
    def delete_knowledge_base(self, kb_id: int) -> bool:
        """Delete knowledge base."""
        try:
            kb = self.get_knowledge_base(kb_id)
            if not kb:
                return False
            
            # TODO: Clean up vector database collection
            # This should be implemented when vector database service is ready
            
            self.db.delete(kb)
            self.db.commit()
            
            logger.info(f"Deleted knowledge base: {kb.name} (ID: {kb.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete knowledge base {kb_id}: {e}")
            raise
    
    def search_knowledge_bases(self, query: str, skip: int = 0, limit: int = 50) -> List[KnowledgeBase]:
        """Search knowledge bases by name or description."""
        search_filter = or_(
            KnowledgeBase.name.ilike(f"%{query}%"),
            KnowledgeBase.description.ilike(f"%{query}%")
        )
        
        return (
            self.db.query(KnowledgeBase)
            .filter(and_(KnowledgeBase.is_active == True, search_filter))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    async def search(self, kb_id: int, query: str, top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search in knowledge base using vector similarity."""
        try:
            logger.info(f"Searching in knowledge base {kb_id} for: {query}")
            
            # 使用document_processor进行向量搜索
            search_results = document_processor.search_similar_documents(
                knowledge_base_id=kb_id,
                query=query,
                k=top_k
            )
            
            # 过滤相似度阈值
            filtered_results = []
            for result in search_results:
                # 使用已经归一化的相似度分数
                normalized_score = result.get('normalized_score', 0)
                
                if normalized_score >= similarity_threshold:
                    filtered_results.append({
                        "content": result.get('content', ''),
                        "source": result.get('source', 'unknown'),
                        "score": normalized_score,
                        "metadata": result.get('metadata', {}),
                        "document_id": result.get('document_id', 'unknown'),
                        "chunk_id": result.get('chunk_id', 'unknown')
                    })
            
            logger.info(f"Found {len(filtered_results)} relevant documents (threshold: {similarity_threshold})")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed for knowledge base {kb_id}: {str(e)}")
            return []