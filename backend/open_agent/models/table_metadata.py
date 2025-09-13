"""表元数据模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.base import BaseModel


class TableMetadata(BaseModel):
    """表元数据表"""
    __tablename__ = "table_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    # database_config_id = Column(Integer, ForeignKey('database_configs.id'), nullable=False)
    table_name = Column(String(100), nullable=False, index=True)
    table_schema = Column(String(50), default='public')
    table_type = Column(String(20), default='BASE TABLE')
    table_comment = Column(Text, nullable=True)  # 表描述
    database_config_id = Column(Integer, nullable=True) #数据库配置ID
    # 表结构信息
    columns_info = Column(JSON, nullable=False)  # 列信息：名称、类型、注释等
    primary_keys = Column(JSON, nullable=True)   # 主键列表
    foreign_keys = Column(JSON, nullable=True)   # 外键信息
    indexes = Column(JSON, nullable=True)        # 索引信息
    
    # 示例数据
    sample_data = Column(JSON, nullable=True)    # 前5条示例数据
    row_count = Column(Integer, default=0)       # 总行数
    
    # 问答相关
    is_enabled_for_qa = Column(Boolean, default=True)  # 是否启用问答
    qa_description = Column(Text, nullable=True)       # 问答描述
    business_context = Column(Text, nullable=True)     # 业务上下文

    last_synced_at = Column(DateTime(timezone=True), nullable=True)  # 最后同步时间
    
    # 关系
    # database_config = relationship("DatabaseConfig", back_populates="table_metadata")
    
    def to_dict(self):
        return {
            "id": self.id,
            "created_by": self.created_by,  # 改为created_by
            "database_config_id": self.database_config_id,
            "table_name": self.table_name,
            "table_schema": self.table_schema,
            "table_type": self.table_type,
            "table_comment": self.table_comment,
            "columns_info": self.columns_info,
            "primary_keys": self.primary_keys,
            # "foreign_keys": self.foreign_keys,
            "indexes": self.indexes,
            "sample_data": self.sample_data,
            "row_count": self.row_count,
            "is_enabled_for_qa": self.is_enabled_for_qa,
            "qa_description": self.qa_description,
            "business_context": self.business_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None
        }