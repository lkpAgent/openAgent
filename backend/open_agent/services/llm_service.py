"""LLM service for workflow execution."""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..models.llm_config import LLMConfig
from ..utils.logger import get_logger

logger = get_logger("llm_service")


class LLMService:
    """LLM服务，用于工作流中的大模型调用"""
    
    def __init__(self):
        pass
    
    async def chat_completion(
        self,
        model_config: LLMConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """调用大模型进行对话完成"""
        try:
            # 创建LangChain ChatOpenAI实例
            llm = ChatOpenAI(
                model=model_config.model_name,
                api_key=model_config.api_key,
                base_url=model_config.base_url,
                temperature=temperature or model_config.temperature,
                max_tokens=max_tokens or model_config.max_tokens,
                streaming=False
            )
            
            # 转换消息格式
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # 调用LLM
            response = await llm.ainvoke(langchain_messages)
            
            # 返回响应内容
            return response.content
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise Exception(f"LLM调用失败: {str(e)}")
    
    async def chat_completion_stream(
        self,
        model_config: LLMConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """调用大模型进行流式对话完成"""
        try:
            # 创建LangChain ChatOpenAI实例（流式）
            llm = ChatOpenAI(
                model=model_config.model_name,
                api_key=model_config.api_key,
                base_url=model_config.base_url,
                temperature=temperature or model_config.temperature,
                max_tokens=max_tokens or model_config.max_tokens,
                streaming=True
            )
            
            # 转换消息格式
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # 流式调用LLM
            async for chunk in llm.astream(langchain_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
            
        except Exception as e:
            logger.error(f"LLM流式调用失败: {str(e)}")
            raise Exception(f"LLM流式调用失败: {str(e)}")
    
    def get_model_info(self, model_config: LLMConfig) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "id": model_config.id,
            "name": model_config.model_name,
            "provider": model_config.provider,
            "base_url": model_config.base_url,
            "temperature": model_config.temperature,
            "max_tokens": model_config.max_tokens,
            "is_active": model_config.is_active
        }