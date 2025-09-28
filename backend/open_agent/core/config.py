"""Configuration management for openAgent."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(..., alias="database_url")  # Must be provided via environment variable
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    
    model_config = {
        "env_file": ".env",
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
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

class ToolSetings(BaseSettings):
    # Tavily搜索配置
    tavily_api_key: Optional[str] = Field(default=None)
    weather_api_key: Optional[str] = Field(default=None)
    model_config = {
        "env_file": ".env",
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
    zhipu_embedding_model: str = Field(default="embedding-3")
    
    # 月之暗面配置
    moonshot_api_key: Optional[str] = Field(default=None)
    moonshot_base_url: str = Field(default="https://api.moonshot.cn/v1")
    moonshot_model: str = Field(default="moonshot-v1-8k")
    
    # 通用配置
    max_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def get_current_config(self) -> dict:
        """获取当前选择的提供商配置 - 优先从数据库读取默认配置."""
        try:
            # 尝试从数据库读取默认聊天模型配置
            from open_agent.services.llm_config_service import LLMConfigService
            llm_service = LLMConfigService()
            db_config = llm_service.get_default_chat_config()
            
            if db_config:
                # 如果数据库中有默认配置，使用数据库配置
                config = {
                    "api_key": db_config.api_key,
                    "base_url": db_config.base_url,
                    "model": db_config.model_name,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
                return config
        except Exception as e:
            # 如果数据库读取失败，记录错误并回退到环境变量
            import logging
            logging.warning(f"Failed to read LLM config from database, falling back to env vars: {e}")
        
        # 回退到原有的环境变量配置
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


class EmbeddingSettings(BaseSettings):
    """Embedding模型配置 - 支持多种提供商."""
    provider: str = Field(default="zhipu", alias="embedding_provider")  # openai, deepseek, doubao, zhipu, moonshot
    
    # OpenAI配置
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_embedding_model: str = Field(default="text-embedding-ada-002")
    
    # DeepSeek配置
    deepseek_api_key: Optional[str] = Field(default=None)
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
    deepseek_embedding_model: str = Field(default="deepseek-embedding")
    
    # 豆包配置
    doubao_api_key: Optional[str] = Field(default=None)
    doubao_base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    doubao_embedding_model: str = Field(default="doubao-embedding")
    
    # 智谱AI配置
    zhipu_api_key: Optional[str] = Field(default=None)
    zhipu_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    zhipu_embedding_model: str = Field(default="embedding-3")
    
    # 月之暗面配置
    moonshot_api_key: Optional[str] = Field(default=None)
    moonshot_base_url: str = Field(default="https://api.moonshot.cn/v1")
    moonshot_embedding_model: str = Field(default="moonshot-embedding")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def get_current_config(self) -> dict:
        """获取当前选择的embedding提供商配置 - 优先从数据库读取默认配置."""
        try:
            # 尝试从数据库读取默认嵌入模型配置
            from open_agent.services.llm_config_service import LLMConfigService
            llm_service = LLMConfigService()
            db_config = llm_service.get_default_embedding_config()
            
            if db_config:
                # 如果数据库中有默认配置，使用数据库配置
                config = {
                    "api_key": db_config.api_key,
                    "base_url": db_config.base_url,
                    "model": db_config.model_name
                }
                return config
        except Exception as e:
            # 如果数据库读取失败，记录错误并回退到环境变量
            import logging
            logging.warning(f"Failed to read embedding config from database, falling back to env vars: {e}")
        
        # 回退到原有的环境变量配置
        provider_configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": self.openai_embedding_model
            },
            "deepseek": {
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": self.deepseek_embedding_model
            },
            "doubao": {
                "api_key": self.doubao_api_key,
                "base_url": self.doubao_base_url,
                "model": self.doubao_embedding_model
            },
            "zhipu": {
                "api_key": self.zhipu_api_key,
                "base_url": self.zhipu_base_url,
                "model": self.zhipu_embedding_model
            },
            "moonshot": {
                "api_key": self.moonshot_api_key,
                "base_url": self.moonshot_base_url,
                "model": self.moonshot_embedding_model
            }
        }
        
        return provider_configs.get(self.provider, provider_configs["zhipu"])


class VectorDBSettings(BaseSettings):
    """Vector database configuration."""
    type: str = Field(default="pgvector", alias="vector_db_type")
    persist_directory: str = Field(default="./data/chroma")
    collection_name: str = Field(default="documents")
    embedding_dimension: int = Field(default=2048)  # 智谱AI embedding-3模型的维度
    
    # PostgreSQL pgvector configuration
    pgvector_host: str = Field(default="localhost")
    pgvector_port: int = Field(default=5432)
    pgvector_database: str = Field(default="vectordb")
    pgvector_user: str = Field(default="postgres")
    pgvector_password: str = Field(default="")
    pgvector_table_name: str = Field(default="embeddings")
    pgvector_vector_dimension: int = Field(default=1024)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class FileSettings(BaseSettings):
    """File processing configuration."""
    upload_dir: str = Field(default="./data/uploads")
    max_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: Union[str, List[str]] = Field(default=[".txt", ".pdf", ".docx", ".md"])
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    semantic_splitter_enabled: bool = Field(default=False)  # 是否启用语义分割器
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Parse comma-separated string to list of extensions."""
        if isinstance(v, str):
            # Split by comma and add dots if not present
            extensions = [ext.strip() for ext in v.split(',')]
            return [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        elif isinstance(v, list):
            # Ensure all extensions start with dot
            return [ext if ext.startswith('.') else f'.{ext}' for ext in v]
        return v
    
    def get_allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list."""
        if isinstance(self.allowed_extensions, list):
            return self.allowed_extensions
        elif isinstance(self.allowed_extensions, str):
            # Split by comma and add dots if not present
            extensions = [ext.strip() for ext in self.allowed_extensions.split(',')]
            return [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        return []
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class StorageSettings(BaseSettings):
    """Storage configuration."""
    storage_type: str = Field(default="local")  # local or s3
    upload_directory: str = Field(default="./data/uploads")
    
    # S3 settings
    s3_bucket_name: str = Field(default="chat-agent-files")
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: str = Field(default="us-east-1")
    s3_endpoint_url: Optional[str] = Field(default=None)  # For S3-compatible services
    
    model_config = {
        "env_file": ".env",
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
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


class CORSSettings(BaseSettings):
    """CORS configuration."""
    allowed_origins: List[str] = Field(default=["*"])
    allowed_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allowed_headers: List[str] = Field(default=["*"])
    
    model_config = {
        "env_file": ".env",
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
    app_name: str = Field(default="openAgent")
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
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    file: FileSettings = Field(default_factory=FileSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
    tool: ToolSetings = Field(default_factory=ToolSetings)
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
        
    @classmethod
    def load_from_yaml(cls, config_path: str = "../configs/settings.yaml") -> "Settings":
        """Load settings from YAML file."""
        config_file = Path(config_path)
        
        # 如果配置文件不存在，尝试从backend目录查找
        if not config_file.exists():
            # 获取当前文件所在目录（backend/open_agent/core）
            current_dir = Path(__file__).parent
            # 向上两级到backend目录，然后找configs/settings.yaml
            backend_config_path = current_dir.parent.parent / "configs" / "settings.yaml"
            if backend_config_path.exists():
                config_file = backend_config_path
            else:
                return cls()
            
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
            
        # 处理环境变量替换
        config_data = cls._resolve_env_vars_nested(config_data)
        
        # 为每个子设置类创建实例，确保它们能正确加载环境变量
        # 如果YAML中没有对应配置，则使用默认的BaseSettings加载（会自动读取.env文件）
        settings_kwargs = {}
        
        # 显式处理各个子设置，以解决debug等情况因为环境的变化没有自动加载.env配置的问题
        settings_kwargs['database'] = DatabaseSettings(**(config_data.get('database', {})))
        settings_kwargs['security'] = SecuritySettings(**(config_data.get('security', {})))
        settings_kwargs['llm'] = LLMSettings(**(config_data.get('llm', {})))
        settings_kwargs['embedding'] = EmbeddingSettings(**(config_data.get('embedding', {})))
        settings_kwargs['vector_db'] = VectorDBSettings(**(config_data.get('vector_db', {})))
        settings_kwargs['file'] = FileSettings(**(config_data.get('file', {})))
        settings_kwargs['storage'] = StorageSettings(**(config_data.get('storage', {})))
        settings_kwargs['logging'] = LoggingSettings(**(config_data.get('logging', {})))
        settings_kwargs['cors'] = CORSSettings(**(config_data.get('cors', {})))
        settings_kwargs['chat'] = ChatSettings(**(config_data.get('chat', {})))
        settings_kwargs['tool'] = ToolSetings(**(config_data.get('tool', {})))
        
        # 添加顶级配置
        for key, value in config_data.items():
            if key not in settings_kwargs:
                settings_kwargs[key] = value
        
        return cls(**settings_kwargs)
    
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
    def _resolve_env_vars_nested(config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in nested configuration."""
        if isinstance(config, dict):
            return {key: Settings._resolve_env_vars_nested(value) for key, value in config.items()}
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            return os.getenv(env_var, config)
        else:
            return config
    
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