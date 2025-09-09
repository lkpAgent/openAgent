"""数据库配置模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from ..db.base import BaseModel


# 在现有的DatabaseConfig类中添加关系
from sqlalchemy.orm import relationship

class DatabaseConfig(BaseModel):
    """数据库配置表"""
    __tablename__ = "database_configs"
    
    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String(100), nullable=False)  # 配置名称
    db_type = Column(String(20), nullable=False, unique=True)  # 数据库类型：postgresql, mysql等
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(Text, nullable=False)  # 加密存储
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    connection_params = Column(JSON, nullable=True)  # 额外连接参数 
    
    def to_dict(self, include_password=False, decrypt_service=None):
        result = {
            "id": self.id,
            "created_by": self.created_by,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "connection_params": self.connection_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # 如果需要包含密码且提供了解密服务
        if include_password and decrypt_service:
            result["password"] = decrypt_service._decrypt_password(self.password)
        
        return result
    
    # 添加关系
    # table_metadata = relationship("TableMetadata", back_populates="database_config")