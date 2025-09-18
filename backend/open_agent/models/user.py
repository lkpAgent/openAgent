"""User model."""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from typing import List, Set, Optional

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
    
    # 关系
    user_departments = relationship("UserDepartment", back_populates="user", cascade="all, delete-orphan")
    managed_departments = relationship("Department", foreign_keys="Department.manager_id", back_populates="manager")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    direct_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def department_id(self) -> Optional[int]:
        """获取用户的主要部门ID."""
        for user_dept in self.user_departments:
            if user_dept.is_primary and user_dept.is_active:
                return user_dept.department_id
        return None
    
    @property
    def is_admin(self) -> bool:
        """检查用户是否为管理员."""
        return any(
            role.code in ['ADMIN', 'SUPER_ADMIN'] 
            for role in self.roles 
            if role.is_active
        )
    
    def to_dict(self, include_sensitive=False, include_permissions=False, include_department=False):
        """Convert to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()
        data.update({
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,

            'avatar_url': self.avatar_url,
            'bio': self.bio
        })
        
        if not include_sensitive:
            data.pop('hashed_password', None)
            
        if include_department:
            # 获取用户的主要部门
            primary_dept = None
            for user_dept in self.user_departments:
                if user_dept.is_primary and user_dept.is_active:
                    primary_dept = user_dept.department
                    break
            
            if primary_dept:
                data['department'] = {
                    'id': primary_dept.id,
                    'name': primary_dept.name,
                    'code': primary_dept.code
                }
            
        if include_permissions:
            data['roles'] = [role.to_dict() for role in self.roles if role.is_active]
            data['permissions'] = self.get_all_permissions()
            
        return data
    
    def has_permission(self, permission_code: str) -> bool:
        """检查用户是否拥有指定权限."""
        # 检查角色权限
        for role in self.roles:
            if role.is_active and role.has_permission(permission_code):
                return True
                
        # 检查直接权限
        for user_perm in self.direct_permissions:
            if (user_perm.permission.code == permission_code and 
                user_perm.permission.is_active):
                return user_perm.granted
                
        return False
    
    def get_all_permissions(self) -> List[str]:
        """获取用户的所有权限编码."""
        permissions = set()
        
        # 从角色获取权限
        for role in self.roles:
            if role.is_active:
                permissions.update(role.get_permission_codes())
                
        # 处理直接权限（可能覆盖角色权限）
        for user_perm in self.direct_permissions:
            if user_perm.permission.is_active:
                if user_perm.granted:
                    permissions.add(user_perm.permission.code)
                else:
                    permissions.discard(user_perm.permission.code)
                    
        return list(permissions)
    
    def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色."""
        return any(role.code == role_code and role.is_active for role in self.roles)
    
    def is_admin(self) -> bool:
        """检查用户是否为管理员."""
        return self.has_role('ADMIN') or self.has_role('SUPER_ADMIN')
    
    def can_manage_department(self, department_id: int) -> bool:
        """检查用户是否可以管理指定部门."""
        # 超级管理员可以管理所有部门
        if self.has_role('SUPER_ADMIN'):
            return True
            
        # 检查是否为部门负责人
        for dept in self.managed_departments:
            if dept.id == department_id or department_id in dept.get_all_children_ids():
                return True
                
        return False