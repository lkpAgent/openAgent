"""Configuration management for ChatAgent."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(default="sqlite:///./data/chat_agent.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class SecuritySettings(BaseSettings):
    """Security configuration."""
    secret_key: str = Field(default="your-secret-key-here-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=300)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class LLMSettings(BaseSettings):
    """大模型配置 - 支持多种OpenAI协议兼容的服务商."""
    provider: str = Field(default="openai", alias="llm_provider")  # openai, deepseek, doubao, zhipu, moonshot
    
    # OpenAI配置
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_model: str = Field(default="gpt-3.5-turbo")
    
    # DeepSeek配置
    deepseek_api_key: Optional[str] = Field(default=None)
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
    deepseek_model: str = Field(default="deepseek-chat")
    
    # 豆包配置
    doubao_api_key: Optional[str] = Field(default=None)
    doubao_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    doubao_model: str = Field(default="doubao-lite-4k")
    
    # 智谱AI配置
    zhipu_api_key: Optional[str] = Field(default=None)
    zhipu_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    zhipu_model: str = Field(default="glm-4")
    
    # 月之暗面配置
    moonshot_api_key: Optional[str] = Field(default=None)
    moonshot_base_url: str = Field(default="https://api.moonshot.cn/v1")
    moonshot_model: str = Field(default="moonshot-v1-8k")
    
    # 通用配置
    max_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def get_current_config(self) -> dict:
        """获取当前选择的提供商配置."""
        provider_configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": self.openai_model
            },
            "deepseek": {
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": self.deepseek_model
            },
            "doubao": {
                "api_key": self.doubao_api_key,
                "base_url": self.doubao_base_url,
                "model": self.doubao_model
            },
            "zhipu": {
                "api_key": self.zhipu_api_key,
                "base_url": self.zhipu_base_url,
                "model": self.zhipu_model
            },
            "moonshot": {
                "api_key": self.moonshot_api_key,
                "base_url": self.moonshot_base_url,
                "model": self.moonshot_model
            }
        }
        
        config = provider_configs.get(self.provider, provider_configs["openai"])
        config.update({
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        })
        return config


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""
    type: str = Field(default="chroma")
    persist_directory: str = Field(default="./data/chroma")
    collection_name: str = Field(default="documents")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class FileSettings(BaseSettings):
    """File processing configuration."""
    upload_dir: str = Field(default="./data/uploads")
    max_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: List[str] = Field(default=[".txt", ".pdf", ".docx", ".md"])
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    level: str = Field(default="INFO")
    file: str = Field(default="./data/logs/app.log")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    max_bytes: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class CORSSettings(BaseSettings):
    """CORS configuration."""
    allowed_origins: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"])
    allowed_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allowed_headers: List[str] = Field(default=["*"])
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class ChatSettings(BaseSettings):
    """Chat configuration."""
    max_history_length: int = Field(default=10)
    system_prompt: str = Field(default="你是一个有用的AI助手，请根据提供的上下文信息回答用户的问题。")
    max_response_tokens: int = Field(default=1000)


class Settings(BaseSettings):
    """Main application settings."""
    
    # App info
    app_name: str = Field(default="ChatAgent")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=True)
    environment: str = Field(default="development")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Configuration sections
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    file: FileSettings = Field(default_factory=FileSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
    
    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
        
    @classmethod
    def load_from_yaml(cls, config_path: str = "configs/settings.yaml") -> "Settings":
        """Load settings from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            return cls()
            
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            
        # 展平嵌套配置
        flat_config = cls._flatten_config(config_data)
        
        # 处理环境变量替换
        flat_config = cls._resolve_env_vars(flat_config)
        
        return cls(**flat_config)
    
    @staticmethod
    def _flatten_config(config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested configuration dictionary."""
        flat = {}
        for key, value in config.items():
            new_key = f"{prefix}_{key}" if prefix else key
            if isinstance(value, dict):
                flat.update(Settings._flatten_config(value, new_key))
            else:
                flat[new_key] = value
        return flat
    
    @staticmethod
    def _resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in configuration values."""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, value)
            else:
                resolved[key] = value
        return resolved


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.load_from_yaml()


# Global settings instance
settings = get_settings()