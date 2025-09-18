"""User Department schemas for API serialization."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserDepartmentBase(BaseModel):
    """Base schema for user department association."""
    user_id: int = Field(..., description="User ID")
    department_id: int = Field(..., description="Department ID")
    is_primary: bool = Field(default=True, description="Whether this is the primary department")
    is_active: bool = Field(default=True, description="Whether the association is active")


class UserDepartmentCreate(UserDepartmentBase):
    """Schema for creating user department association."""
    pass


class UserDepartmentUpdate(BaseModel):
    """Schema for updating user department association."""
    is_primary: Optional[bool] = Field(None, description="Whether this is the primary department")
    is_active: Optional[bool] = Field(None, description="Whether the association is active")


class UserDepartmentResponse(UserDepartmentBase):
    """Schema for user department association response."""
    id: int = Field(..., description="Association ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class UserDepartmentWithDetails(UserDepartmentResponse):
    """Schema for user department association with related details."""
    user_name: Optional[str] = Field(None, description="User name")
    user_email: Optional[str] = Field(None, description="User email")
    department_name: Optional[str] = Field(None, description="Department name")
    department_code: Optional[str] = Field(None, description="Department code")
    
    class Config:
        from_attributes = True


class DepartmentUserList(BaseModel):
    """Schema for listing users in a department."""
    department_id: int = Field(..., description="Department ID")
    department_name: str = Field(..., description="Department name")
    department_code: str = Field(..., description="Department code")
    users: list[UserDepartmentWithDetails] = Field(default=[], description="Users in department")
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")


class UserDepartmentList(BaseModel):
    """Schema for listing user's departments."""
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    user_email: str = Field(..., description="User email")
    departments: list[UserDepartmentWithDetails] = Field(default=[], description="User's departments")
    primary_department: Optional[UserDepartmentWithDetails] = Field(None, description="Primary department")
    total_departments: int = Field(..., description="Total number of departments")


class SetPrimaryDepartmentRequest(BaseModel):
    """Schema for setting primary department."""
    department_id: int = Field(..., description="Department ID to set as primary")


class BulkUserDepartmentCreate(BaseModel):
    """Schema for bulk creating user department associations."""
    user_ids: list[int] = Field(..., description="List of user IDs")
    department_id: int = Field(..., description="Department ID")
    is_primary: bool = Field(default=False, description="Whether this should be the primary department")
    is_active: bool = Field(default=True, description="Whether the associations should be active")


class BulkUserDepartmentResponse(BaseModel):
    """Schema for bulk operation response."""
    success_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    errors: list[str] = Field(default=[], description="List of error messages")
    created_associations: list[UserDepartmentResponse] = Field(default=[], description="Successfully created associations")