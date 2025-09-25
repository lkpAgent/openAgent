"""User model."""

from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from typing import List, Optional

from ..db.base import BaseModel


class User(BaseModel):
    """User model."""
    
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 关系 - 只保留角色关系
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self, include_sensitive=False, include_roles=False):
        """Convert to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_superuser': self.is_superuser()
        })
        
        if not include_sensitive:
            data.pop('hashed_password', None)
            
        if include_roles:
            data['roles'] = [role.to_dict() for role in self.roles if role.is_active]
            
        return data
    
    def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色."""
        try:
            return any(role.code == role_code and role.is_active for role in self.roles)
        except Exception:
            # 如果对象已分离，使用数据库查询
            from sqlalchemy.orm import object_session
            from .permission import Role, UserRole
            
            session = object_session(self)
            if session is None:
                # 如果没有会话，创建新的会话
                from ..db.database import SessionLocal
                session = SessionLocal()
                try:
                    user_role = session.query(UserRole).join(Role).filter(
                        UserRole.user_id == self.id,
                        Role.code == role_code,
                        Role.is_active == True
                    ).first()
                    return user_role is not None
                finally:
                    session.close()
            else:
                user_role = session.query(UserRole).join(Role).filter(
                    UserRole.user_id == self.id,
                    Role.code == role_code,
                    Role.is_active == True
                ).first()
                return user_role is not None
    
    def is_superuser(self) -> bool:
        """检查用户是否为超级管理员."""
        return self.has_role('SUPER_ADMIN')
    
    def is_admin_user(self) -> bool:
        """检查用户是否为管理员（兼容性方法）."""
        return self.is_superuser()
    
    @property
    def is_admin(self) -> bool:
        """检查用户是否为管理员（属性方式）."""
        return self.is_superuser()