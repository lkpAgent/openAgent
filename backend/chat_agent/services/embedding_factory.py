"""Embedding factory for different providers."""

from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from .zhipu_embeddings import ZhipuOpenAIEmbeddings
from ..core.config import settings
from ..utils.logger import get_logger

logger = get_logger("embedding_factory")


class EmbeddingFactory:
    """Factory class for creating embedding instances based on provider."""
    
    @staticmethod
    def create_embeddings(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None
    ) -> Embeddings:
        """Create embeddings instance based on provider.
        
        Args:
            provider: Embedding provider (openai, zhipu, deepseek, doubao, moonshot, sentence-transformers)
            model: Model name
            dimensions: Embedding dimensions
            
        Returns:
            Embeddings instance
        """
        # 使用新的embedding配置
        embedding_config = settings.embedding.get_current_config()
        provider = provider or settings.embedding.provider
        model = model or embedding_config.get("model")
        dimensions = dimensions or settings.vector_db.embedding_dimension
        
        logger.info(f"Creating embeddings with provider: {provider}, model: {model}")
        
        if provider == "openai":
            return EmbeddingFactory._create_openai_embeddings(embedding_config, model, dimensions)
        elif provider in ["zhipu", "deepseek", "doubao", "moonshot"]:
            return EmbeddingFactory._create_openai_compatible_embeddings(embedding_config, model, dimensions, provider)
        elif provider == "sentence-transformers":
            return EmbeddingFactory._create_huggingface_embeddings(model)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    @staticmethod
    def _create_openai_embeddings(embedding_config: dict, model: str, dimensions: int) -> OpenAIEmbeddings:
        """Create OpenAI embeddings."""
        return OpenAIEmbeddings(
            api_key=embedding_config["api_key"],
            base_url=embedding_config["base_url"],
            model=model if model.startswith("text-embedding") else "text-embedding-ada-002",
            dimensions=dimensions if model.startswith("text-embedding-3") else None
        )
    

    
    @staticmethod
    def _create_openai_compatible_embeddings(embedding_config: dict, model: str, dimensions: int, provider: str) -> Embeddings:
        """Create OpenAI-compatible embeddings for ZhipuAI, DeepSeek, Doubao, Moonshot."""
        if provider == "zhipu":
            return ZhipuOpenAIEmbeddings(
                api_key=embedding_config["api_key"],
                base_url=embedding_config["base_url"],
                model=model if model.startswith("embedding") else "embedding-3",
                dimensions=dimensions
            )
        else:
            return OpenAIEmbeddings(
                api_key=embedding_config["api_key"],
                base_url=embedding_config["base_url"],
                model=model,
                dimensions=dimensions
            )
    
    @staticmethod
    def _create_huggingface_embeddings(model: str) -> HuggingFaceEmbeddings:
        """Create HuggingFace embeddings."""
        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )