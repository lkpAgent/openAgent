"""Role models for simplified RBAC system."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from typing import List, Dict, Any

from ..db.base import BaseModel, Base


class Role(BaseModel):
    """Role model for simplified RBAC system."""
    
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False, unique=True, index=True)  # 角色名称
    code = Column(String(100), nullable=False, unique=True, index=True)  # 角色编码
    description = Column(Text, nullable=True)  # 角色描述
    is_system = Column(Boolean, default=False, nullable=False)  # 是否系统角色
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关系 - 只保留用户关系
    users = relationship("User", secondary="user_roles", back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_system': self.is_system,
            'is_active': self.is_active
        })
        return data


class UserRole(Base):
    """User role association model."""
    
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    
    # 关系 - 用于直接操作关联表的场景
    user = relationship("User", viewonly=True)
    role = relationship("Role", viewonly=True)
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"