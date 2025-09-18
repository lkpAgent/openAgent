"""Department model for organizational structure."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from typing import List, Optional

from ..db.base import BaseModel


class Department(BaseModel):
    """Department model for organizational hierarchy."""
    
    __tablename__ = "departments"
    
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # 部门编码
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    level = Column(Integer, default=1, nullable=False)  # 部门层级
    sort_order = Column(Integer, default=0, nullable=False)  # 排序
    is_active = Column(Boolean, default=True, nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 部门负责人
    
    # 关系
    parent = relationship("Department", remote_side="Department.id", back_populates="children")
    children = relationship("Department", back_populates="parent", cascade="all, delete-orphan")
    manager = relationship("User", foreign_keys=[manager_id], back_populates="managed_departments")
    user_departments = relationship("UserDepartment", back_populates="department", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    def to_dict(self, include_children=False, include_users=False):
        """Convert to dictionary with optional nested data."""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id,
            'level': self.level,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None
        })
        
        if include_children and self.children:
            data['children'] = [child.to_dict() for child in self.children if child.is_active]
            
        if include_users and self.users:
            data['users'] = [{
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'is_active': user.is_active
            } for user in self.users if user.is_active]
            
        return data
    
    def get_all_children_ids(self) -> List[int]:
        """递归获取所有子部门ID."""
        children_ids = []
        for child in self.children:
            if child.is_active:
                children_ids.append(child.id)
                children_ids.extend(child.get_all_children_ids())
        return children_ids
    
    def get_path(self) -> List['Department']:
        """获取从根部门到当前部门的路径."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path
    
    def get_path_names(self) -> str:
        """获取部门路径名称，用/分隔."""
        path = self.get_path()
        return ' / '.join([dept.name for dept in path])