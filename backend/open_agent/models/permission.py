"""Permission and Role models for RBAC system."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from typing import List, Dict, Any

from ..db.base import BaseModel, Base


# Note: Association tables are now defined as model classes below


class Permission(BaseModel):
    """Permission model for RBAC system."""
    
    __tablename__ = "permissions"
    
    name = Column(String(100), nullable=False, unique=True, index=True)  # 权限名称
    code = Column(String(100), nullable=False, unique=True, index=True)  # 权限编码
    description = Column(Text, nullable=True)  # 权限描述
    resource = Column(String(100), nullable=False, index=True)  # 资源类型
    action = Column(String(50), nullable=False, index=True)  # 操作类型
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关系
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, code='{self.code}', resource='{self.resource}', action='{self.action}')>"
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'resource': self.resource,
            'action': self.action,
            'is_active': self.is_active
        })
        return data


class Role(BaseModel):
    """Role model for RBAC system."""
    
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False, unique=True, index=True)  # 角色名称
    code = Column(String(100), nullable=False, unique=True, index=True)  # 角色编码
    description = Column(Text, nullable=True)  # 角色描述
    is_system = Column(Boolean, default=False, nullable=False)  # 是否系统角色
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关系
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    users = relationship("User", secondary="user_roles", back_populates="roles")
    role_resources = relationship("RoleResource", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    def to_dict(self, include_permissions=False, include_users=False):
        """Convert to dictionary with optional nested data."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'is_system': self.is_system,
            'is_active': self.is_active
        })
        
        if include_permissions:
            data['permissions'] = [perm.to_dict() for perm in self.permissions if perm.is_active]
            
        if include_users:
            data['users'] = [{
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email
            } for user in self.users if user.is_active]
            
        return data
    
    def has_permission(self, permission_code: str) -> bool:
        """检查角色是否拥有指定权限."""
        return any(
            perm.code == permission_code and perm.is_active 
            for perm in self.permissions
        )
    
    def get_permission_codes(self) -> List[str]:
        """获取角色的所有权限编码."""
        return [perm.code for perm in self.permissions if perm.is_active]


class RolePermission(Base):
    """Role permission association model."""
    
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), primary_key=True)
    
    # 关系
    role = relationship("Role")
    permission = relationship("Permission")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """User role association model."""
    
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    
    # 关系
    user = relationship("User")
    role = relationship("Role")
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class UserPermission(Base):
    """User permission model for direct permission assignment."""
    
    __tablename__ = "user_permissions"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True,primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), nullable=False, index=True,primary_key=True)
    granted = Column(Boolean, default=True, nullable=False)  # True=授予，False=拒绝
    
    # 关系
    user = relationship("User", back_populates="direct_permissions")
    permission = relationship("Permission")
    
    def __repr__(self):
        return f"<UserPermission(user_id={self.user_id}, permission_id={self.permission_id}, granted={self.granted})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'permission_id': self.permission_id,
            'granted': self.granted,
            'permission': self.permission.to_dict() if self.permission else None
        })
        return data