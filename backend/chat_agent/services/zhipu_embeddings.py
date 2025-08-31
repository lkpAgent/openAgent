"""Custom ZhipuAI Embeddings using OpenAI compatible API."""

import asyncio
from typing import List, Optional
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from ..core.config import settings
from ..utils.logger import get_logger

logger = get_logger("zhipu_embeddings")


class ZhipuOpenAIEmbeddings(Embeddings):
    """ZhipuAI Embeddings using OpenAI compatible API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "embedding-3",
        dimensions: int = 1024
    ):
        self.api_key = api_key or settings.embedding.zhipu_api_key
        self.base_url = base_url
        self.model = model
        self.dimensions = dimensions
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"ZhipuOpenAI Embeddings initialized with model: {self.model}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        try:
            embeddings = []
            for text in texts:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    dimensions=self.dimensions,
                    encoding_format="float"
                )
                embeddings.append(response.data[0].embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Async embed search docs."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """Async embed query text."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, text)