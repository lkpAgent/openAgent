"""Permission and Role Pydantic schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PermissionBase(BaseModel):
    """权限基础模式."""
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    category: Optional[str] = Field(None, max_length=50, description="权限分类")
    sort_order: Optional[int] = Field(0, ge=0, description="排序")


class PermissionCreate(PermissionBase):
    """创建权限模式."""
    
    @validator('code')
    def validate_code(cls, v):
        if ':' not in v:
            raise ValueError('权限代码应包含冒号分隔符，格式如: module:action')
        return v.lower()


class PermissionUpdate(BaseModel):
    """更新权限模式."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="权限名称")
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="权限代码")
    description: Optional[str] = Field(None, max_length=500, description="权限描述")
    category: Optional[str] = Field(None, max_length=50, description="权限分类")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None and ':' not in v:
            raise ValueError('权限代码应包含冒号分隔符，格式如: module:action')
        return v.lower() if v else v


class PermissionResponse(PermissionBase):
    """权限响应模式."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """角色基础模式."""
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    sort_order: Optional[int] = Field(0, ge=0, description="排序")
    is_active: bool = Field(True, description="是否激活")


class RoleCreate(RoleBase):
    """创建角色模式."""
    
    @validator('code')
    def validate_code(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('角色代码只能包含字母、数字、下划线和连字符')
        return v.upper()


class RoleUpdate(BaseModel):
    """更新角色模式."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="角色名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="角色代码")
    description: Optional[str] = Field(None, max_length=500, description="角色描述")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('角色代码只能包含字母、数字、下划线和连字符')
        return v.upper() if v else v


class RoleResponse(RoleBase):
    """角色响应模式."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # 关联信息
    permissions: Optional[List[PermissionResponse]] = []
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class UserRoleAssign(BaseModel):
    """用户角色分配模式."""
    user_id: int = Field(..., description="用户ID")
    role_ids: List[int] = Field(..., description="角色ID列表")
    
    @validator('role_ids')
    def validate_role_ids(cls, v):
        if not v:
            raise ValueError('角色ID列表不能为空')
        if len(v) != len(set(v)):
            raise ValueError('角色ID列表不能包含重复项')
        return v


class RolePermissionAssign(BaseModel):
    """角色权限分配模式."""
    permission_ids: List[int] = Field(..., description="权限ID列表")
    
    @validator('permission_ids')
    def validate_permission_ids(cls, v):
        if not v:
            raise ValueError('权限ID列表不能为空')
        if len(v) != len(set(v)):
            raise ValueError('权限ID列表不能包含重复项')
        return v


class UserPermissionResponse(BaseModel):
    """用户权限响应模式."""
    user_id: int
    username: str
    roles: List[RoleResponse] = []
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True