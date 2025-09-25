"""User schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..utils.schemas import BaseResponse


class UserBase(BaseModel):
    """User base schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")


class ResetPasswordRequest(BaseModel):
    """Admin reset password request schema."""
    new_password: str = Field(..., min_length=6, description="New password")


class UserResponse(BaseResponse, UserBase):
    """User response schema."""
    is_active: bool
    is_superuser: Optional[bool] = Field(default=False, description="是否为超级管理员")
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应模型，正确处理is_superuser方法"""
        data = obj.__dict__.copy()
        # 调用is_superuser方法获取布尔值
        if hasattr(obj, 'is_superuser') and callable(obj.is_superuser):
            data['is_superuser'] = obj.is_superuser()
        return cls(**data)