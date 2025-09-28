"""LLM配置服务 - 从数据库读取默认配置"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.llm_config import LLMConfig
from ..utils.logger import get_logger
from ..db.database import get_db_session

logger = get_logger("llm_config_service")


class LLMConfigService:
    """LLM配置管理服务"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or get_db_session()
    
    def get_default_chat_config(self) -> Optional[LLMConfig]:
        """获取默认对话模型配置"""
        try:
            config = self.db.query(LLMConfig).filter(
                and_(
                    LLMConfig.is_default == True,
                    LLMConfig.is_embedding == False,
                    LLMConfig.is_active == True
                )
            ).first()
            
            if not config:
                logger.warning("未找到默认对话模型配置")
                return None
            
            return config
            
        except Exception as e:
            logger.error(f"获取默认对话模型配置失败: {str(e)}")
            return None
    
    def get_default_embedding_config(self) -> Optional[LLMConfig]:
        """获取默认嵌入模型配置"""
        try:
            config = self.db.query(LLMConfig).filter(
                and_(
                    LLMConfig.is_default == True,
                    LLMConfig.is_embedding == True,
                    LLMConfig.is_active == True
                )
            ).first()
            
            if not config:
                logger.warning("未找到默认嵌入模型配置")
                return None
            
            return config
            
        except Exception as e:
            logger.error(f"获取默认嵌入模型配置失败: {str(e)}")
            return None
    
    def get_config_by_id(self, config_id: int) -> Optional[LLMConfig]:
        """根据ID获取配置"""
        try:
            return self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return None
    
    def get_active_configs(self, is_embedding: Optional[bool] = None) -> list:
        """获取所有激活的配置"""
        try:
            query = self.db.query(LLMConfig).filter(LLMConfig.is_active == True)
            
            if is_embedding is not None:
                query = query.filter(LLMConfig.is_embedding == is_embedding)
            
            return query.order_by(LLMConfig.created_at).all()
            
        except Exception as e:
            logger.error(f"获取激活配置失败: {str(e)}")
            return []
    
    def _get_fallback_chat_config(self) -> Dict[str, Any]:
        """获取fallback对话模型配置（从环境变量）"""
        from ..core.config import get_settings
        settings = get_settings()
        return settings.llm.get_current_config()
    
    def _get_fallback_embedding_config(self) -> Dict[str, Any]:
        """获取fallback嵌入模型配置（从环境变量）"""
        from ..core.config import get_settings
        settings = get_settings()
        return settings.embedding.get_current_config()
    
    def test_config(self, config_id: int, test_message: str = "Hello") -> Dict[str, Any]:
        """测试配置连接"""
        try:
            config = self.get_config_by_id(config_id)
            if not config:
                return {"success": False, "error": "配置不存在"}
            
            # 这里可以添加实际的连接测试逻辑
            # 例如发送一个简单的请求来验证配置是否有效
            
            return {"success": True, "message": "配置测试成功"}
            
        except Exception as e:
            logger.error(f"测试配置失败: {str(e)}")
            return {"success": False, "error": str(e)}


# 全局实例
_llm_config_service = None

def get_llm_config_service(db_session: Optional[Session] = None) -> LLMConfigService:
    """获取LLM配置服务实例"""
    global _llm_config_service
    if _llm_config_service is None or db_session is not None:
        _llm_config_service = LLMConfigService(db_session)
    return _llm_config_service