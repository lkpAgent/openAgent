"""Resource management schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ResourceBase(BaseModel):
    """资源基础模型."""
    name: str = Field(..., description="资源名称")
    code: str = Field(..., description="资源编码")
    type: str = Field(..., description="资源类型: menu|page|button|api")
    path: Optional[str] = Field(None, description="资源路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    description: Optional[str] = Field(None, description="描述")
    parent_id: Optional[int] = Field(None, description="父级资源ID")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")
    requires_auth: bool = Field(True, description="是否需要认证")
    requires_admin: bool = Field(False, description="是否需要管理员权限")
    meta: Optional[dict] = Field(None, description="元数据")


class ResourceCreate(ResourceBase):
    """创建资源模型."""
    pass


class ResourceUpdate(BaseModel):
    """更新资源模型."""
    name: Optional[str] = Field(None, description="资源名称")
    code: Optional[str] = Field(None, description="资源编码")
    type: Optional[str] = Field(None, description="资源类型")
    path: Optional[str] = Field(None, description="资源路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    description: Optional[str] = Field(None, description="描述")
    parent_id: Optional[int] = Field(None, description="父级资源ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否启用")
    requires_auth: Optional[bool] = Field(None, description="是否需要认证")
    requires_admin: Optional[bool] = Field(None, description="是否需要管理员权限")
    meta: Optional[dict] = Field(None, description="元数据")


class ResourceResponse(ResourceBase):
    """资源响应模型."""
    id: int
    created_at: datetime
    updated_at: datetime
    children: Optional[List['ResourceResponse']] = Field(None, description="子资源")

    class Config:
        from_attributes = True


class ResourceTreeNode(BaseModel):
    """资源树节点模型."""
    id: int
    name: str
    code: str
    type: str
    path: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    children: Optional[List['ResourceTreeNode']] = None


class RoleResourceAssign(BaseModel):
    """角色资源分配模型."""
    role_id: int = Field(..., description="角色ID")
    resource_ids: List[int] = Field(..., description="资源ID列表")


# 更新前向引用
ResourceResponse.model_rebuild()
ResourceTreeNode.model_rebuild()