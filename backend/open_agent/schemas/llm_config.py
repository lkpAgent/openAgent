"""LLM Configuration Pydantic schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class LLMConfigBase(BaseModel):
    """大模型配置基础模式."""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    provider: str = Field(..., min_length=1, max_length=50, description="服务商")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    api_key: str = Field(..., min_length=1, description="API密钥")
    api_base: Optional[str] = Field(None, description="API基础URL")
    api_version: Optional[str] = Field(None, description="API版本")
    max_tokens: Optional[int] = Field(4096, ge=1, le=32000, description="最大令牌数")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: Optional[int] = Field(60, ge=1, le=300, description="超时时间（秒）")
    max_retries: Optional[int] = Field(3, ge=0, le=10, description="最大重试次数")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sort_order: Optional[int] = Field(0, ge=0, description="排序")
    is_active: bool = Field(True, description="是否激活")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class LLMConfigCreate(LLMConfigBase):
    """创建大模型配置模式."""
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = [
            'openai', 'azure', 'anthropic', 'google', 'baidu', 
            'alibaba', 'tencent', 'zhipu', 'moonshot', 'deepseek',
            'ollama', 'custom'
        ]
        if v.lower() not in allowed_providers:
            raise ValueError(f'不支持的服务商: {v}，支持的服务商: {", ".join(allowed_providers)}')
        return v.lower()
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('API密钥长度不能少于10个字符')
        return v.strip()


class LLMConfigUpdate(BaseModel):
    """更新大模型配置模式."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="配置名称")
    provider: Optional[str] = Field(None, min_length=1, max_length=50, description="服务商")
    model_name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    api_key: Optional[str] = Field(None, min_length=1, description="API密钥")
    api_base: Optional[str] = Field(None, description="API基础URL")
    api_version: Optional[str] = Field(None, description="API版本")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="最大令牌数")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p参数")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="存在惩罚")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="超时时间（秒）")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    description: Optional[str] = Field(None, max_length=500, description="配置描述")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")
    
    @validator('provider')
    def validate_provider(cls, v):
        if v is not None:
            allowed_providers = [
                'openai', 'azure', 'anthropic', 'google', 'baidu', 
                'alibaba', 'tencent', 'zhipu', 'moonshot', 'deepseek',
                'ollama', 'custom'
            ]
            if v.lower() not in allowed_providers:
                raise ValueError(f'不支持的服务商: {v}，支持的服务商: {", ".join(allowed_providers)}')
            return v.lower()
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('API密钥长度不能少于10个字符')
        return v.strip() if v else v


class LLMConfigResponse(BaseModel):
    """大模型配置响应模式."""
    id: int
    name: str
    provider: str
    model_name: str
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: bool
    extra_params: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # 敏感信息处理
    api_key_masked: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @validator('api_key_masked', pre=True, always=True)
    def mask_api_key(cls, v, values):
        # 在响应中隐藏API密钥，只显示前4位和后4位
        if 'api_key' in values and values['api_key']:
            key = values['api_key']
            if len(key) > 8:
                return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"
            else:
                return '*' * len(key)
        return None


class LLMConfigTest(BaseModel):
    """大模型配置测试模式."""
    message: Optional[str] = Field(
        "Hello, this is a test message.", 
        max_length=1000, 
        description="测试消息"
    )


class LLMConfigClientResponse(BaseModel):
    """大模型配置客户端响应模式（用于前端）."""
    id: int
    name: str
    provider: str
    model_name: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    is_active: bool
    description: Optional[str] = None
    
    class Config:
        from_attributes = True