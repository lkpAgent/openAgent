"""Resource management models."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base


class Resource(Base):
    """资源模型."""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="资源名称")
    code = Column(String(100), unique=True, nullable=False, index=True, comment="资源编码")
    type = Column(String(20), nullable=False, comment="资源类型: menu|page|button|api")
    path = Column(String(255), comment="资源路径")
    component = Column(String(255), comment="组件路径")
    icon = Column(String(50), comment="图标")
    description = Column(Text, comment="描述")
    parent_id = Column(Integer, ForeignKey("resources.id"), comment="父级资源ID")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    requires_auth = Column(Boolean, default=True, comment="是否需要认证")
    requires_admin = Column(Boolean, default=False, comment="是否需要管理员权限")
    meta = Column(JSON, comment="元数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    parent = relationship("Resource", remote_side=[id], back_populates="children")
    children = relationship("Resource", back_populates="parent", cascade="all, delete-orphan")
    role_resources = relationship("RoleResource", back_populates="resource", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "type": self.type,
            "path": self.path,
            "component": self.component,
            "icon": self.icon,
            "description": self.description,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "requires_auth": self.requires_auth,
            "requires_admin": self.requires_admin,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_tree_node(self):
        """转换为树节点."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "type": self.type,
            "path": self.path,
            "icon": self.icon,
            "is_active": self.is_active,
            "children": [child.to_tree_node() for child in self.children if child.is_active]
        }


class RoleResource(Base):
    """角色资源关联模型."""
    __tablename__ = "role_resources"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True, comment="角色ID")
    resource_id = Column(Integer, ForeignKey("resources.id"), primary_key=True, comment="资源ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关系
    role = relationship("Role", back_populates="role_resources")
    resource = relationship("Resource", back_populates="role_resources")

    def to_dict(self):
        """转换为字典."""
        return {
            "role_id": self.role_id,
            "resource_id": self.resource_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }