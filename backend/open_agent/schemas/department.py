"""Department Pydantic schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DepartmentBase(BaseModel):
    """部门基础模式."""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=50, description="部门代码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: Optional[int] = Field(0, ge=0, description="排序")
    is_active: bool = Field(True, description="是否激活")


class DepartmentCreate(DepartmentBase):
    """创建部门模式."""
    
    @validator('code')
    def validate_code(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('部门代码只能包含字母、数字、下划线和连字符')
        return v.upper()


class DepartmentUpdate(BaseModel):
    """更新部门模式."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="部门代码")
    description: Optional[str] = Field(None, max_length=500, description="部门描述")
    parent_id: Optional[int] = Field(None, description="父部门ID")
    sort_order: Optional[int] = Field(None, ge=0, description="排序")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('code')
    def validate_code(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('部门代码只能包含字母、数字、下划线和连字符')
        return v.upper() if v else v


class DepartmentResponse(DepartmentBase):
    """部门响应模式."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # 关联信息
    parent_name: Optional[str] = None
    children_count: Optional[int] = 0
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class DepartmentTreeResponse(DepartmentResponse):
    """部门树形响应模式."""
    children: Optional[List['DepartmentTreeResponse']] = []
    
    class Config:
        from_attributes = True


# 解决前向引用问题
DepartmentTreeResponse.model_rebuild()