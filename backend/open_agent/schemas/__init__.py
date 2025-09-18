"""Schemas for API serialization."""

# Import only existing schema modules
from .department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentTreeResponse
)
from .user_department import (
    UserDepartmentCreate, UserDepartmentUpdate, UserDepartmentResponse,
    UserDepartmentWithDetails, DepartmentUserList, UserDepartmentList,
    SetPrimaryDepartmentRequest, BulkUserDepartmentCreate, BulkUserDepartmentResponse
)
from .permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    UserRoleAssign, RolePermissionAssign, UserPermissionResponse
)
from .llm_config import LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse

__all__ = [
    # Department schemas
    "DepartmentCreate", "DepartmentUpdate", "DepartmentResponse",
    "DepartmentTreeResponse",
    
    # User department schemas
    "UserDepartmentCreate", "UserDepartmentUpdate", "UserDepartmentResponse",
    "UserDepartmentWithDetails", "DepartmentUserList", "UserDepartmentList",
    "SetPrimaryDepartmentRequest", "BulkUserDepartmentCreate", "BulkUserDepartmentResponse",
    
    # Permission schemas
    "PermissionCreate", "PermissionUpdate", "PermissionResponse",
    "RoleCreate", "RoleUpdate", "RoleResponse",
    "UserRoleAssign", "RolePermissionAssign", "UserPermissionResponse",
    
    # LLM config schemas
    "LLMConfigCreate", "LLMConfigUpdate", "LLMConfigResponse"
]