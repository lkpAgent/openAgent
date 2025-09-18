"""LLM Configuration model for managing multiple AI models."""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, JSON
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional
import json

from ..db.base import BaseModel


class LLMConfig(BaseModel):
    """LLM Configuration model for managing AI model settings."""
    
    __tablename__ = "llm_configs"
    
    name = Column(String(100), nullable=False, index=True)  # 配置名称
    provider = Column(String(50), nullable=False, index=True)  # 服务商：openai, deepseek, doubao, zhipu, moonshot
    model_name = Column(String(100), nullable=False)  # 模型名称
    api_key = Column(String(500), nullable=False)  # API密钥（加密存储）
    base_url = Column(String(200), nullable=True)  # API基础URL
    
    # 模型参数
    max_tokens = Column(Integer, default=2048, nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=1.0, nullable=False)
    frequency_penalty = Column(Float, default=0.0, nullable=False)
    presence_penalty = Column(Float, default=0.0, nullable=False)
    
    # 配置信息
    description = Column(Text, nullable=True)  # 配置描述
    is_active = Column(Boolean, default=True, nullable=False)  # 是否启用
    is_default = Column(Boolean, default=False, nullable=False)  # 是否为默认配置
    is_embedding = Column(Boolean, default=False, nullable=False)  # 是否为嵌入模型
    
    # 扩展配置（JSON格式）
    extra_config = Column(JSON, nullable=True)  # 额外配置参数
    
    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False)  # 使用次数
    last_used_at = Column(String(50), nullable=True)  # 最后使用时间
    
    def __repr__(self):
        return f"<LLMConfig(id={self.id}, name='{self.name}', provider='{self.provider}', model='{self.model_name}')>"
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'provider': self.provider,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'description': self.description,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_embedding': self.is_embedding,
            'extra_config': self.extra_config,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at
        })
        
        if include_sensitive:
            data['api_key'] = self.api_key
        else:
            # 只显示API密钥的前几位和后几位
            if self.api_key:
                key_len = len(self.api_key)
                if key_len > 8:
                    data['api_key_masked'] = f"{self.api_key[:4]}...{self.api_key[-4:]}"
                else:
                    data['api_key_masked'] = "***"
            else:
                data['api_key_masked'] = None
                
        return data
    
    def get_client_config(self) -> Dict[str, Any]:
        """获取用于创建客户端的配置."""
        config = {
            'api_key': self.api_key,
            'base_url': self.base_url,
            'model': self.model_name,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty
        }
        
        # 添加额外配置
        if self.extra_config:
            config.update(self.extra_config)
            
        return config
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """验证配置是否有效."""
        if not self.name or not self.name.strip():
            return False, "配置名称不能为空"
            
        if not self.provider or self.provider not in ['openai', 'deepseek', 'doubao', 'zhipu', 'moonshot']:
            return False, "不支持的服务商"
            
        if not self.model_name or not self.model_name.strip():
            return False, "模型名称不能为空"
            
        if not self.api_key or not self.api_key.strip():
            return False, "API密钥不能为空"
            
        if self.max_tokens <= 0 or self.max_tokens > 32000:
            return False, "最大令牌数必须在1-32000之间"
            
        if self.temperature < 0 or self.temperature > 2:
            return False, "温度参数必须在0-2之间"
            
        return True, None
    
    def increment_usage(self):
        """增加使用次数."""
        from datetime import datetime
        self.usage_count += 1
        self.last_used_at = datetime.now().isoformat()
    
    @classmethod
    def get_default_config(cls, provider: str, is_embedding: bool = False):
        """获取服务商的默认配置模板."""
        templates = {
            'openai': {
                'base_url': 'https://api.openai.com/v1',
                'model_name': 'gpt-3.5-turbo' if not is_embedding else 'text-embedding-ada-002',
                'max_tokens': 2048,
                'temperature': 0.7
            },
            'deepseek': {
                'base_url': 'https://api.deepseek.com/v1',
                'model_name': 'deepseek-chat' if not is_embedding else 'deepseek-embedding',
                'max_tokens': 2048,
                'temperature': 0.7
            },
            'doubao': {
                'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                'model_name': 'doubao-lite-4k' if not is_embedding else 'doubao-embedding',
                'max_tokens': 2048,
                'temperature': 0.7
            },
            'zhipu': {
                'base_url': 'https://open.bigmodel.cn/api/paas/v4',
                'model_name': 'glm-4' if not is_embedding else 'embedding-3',
                'max_tokens': 2048,
                'temperature': 0.7
            },
            'moonshot': {
                'base_url': 'https://api.moonshot.cn/v1',
                'model_name': 'moonshot-v1-8k' if not is_embedding else 'moonshot-embedding',
                'max_tokens': 2048,
                'temperature': 0.7
            }
        }
        
        return templates.get(provider, {})