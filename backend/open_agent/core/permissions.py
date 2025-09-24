"""Permission decorators and dependencies for API endpoints."""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services.auth import AuthService
from ..models.user import User
from ..models.permission import Permission, Role
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PermissionChecker:
    """权限检查器类."""
    
    def __init__(self, required_permissions: List[str], require_all: bool = True):
        """
        初始化权限检查器.
        
        Args:
            required_permissions: 需要的权限列表
            require_all: 是否需要所有权限（True）还是任一权限（False）
        """
        self.required_permissions = required_permissions
        self.require_all = require_all
    
    def __call__(
        self,
        current_user: User = Depends(AuthService.get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """检查用户权限."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证的用户"
            )
        
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        # 超级管理员拥有所有权限
        if current_user.has_role('SUPER_ADMIN'):
            return current_user
        
        # 检查权限
        if self.require_all:
            # 需要所有权限
            for permission in self.required_permissions:
                if not current_user.has_permission(permission):
                    logger.warning(
                        f"User {current_user.username} lacks permission: {permission}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {permission}"
                    )
        else:
            # 需要任一权限
            has_any_permission = any(
                current_user.has_permission(permission) 
                for permission in self.required_permissions
            )
            if not has_any_permission:
                logger.warning(
                    f"User {current_user.username} lacks any of permissions: {self.required_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少以下任一权限: {', '.join(self.required_permissions)}"
                )
        
        return current_user


class RoleChecker:
    """角色检查器类."""
    
    def __init__(self, required_roles: List[str], require_all: bool = False):
        """
        初始化角色检查器.
        
        Args:
            required_roles: 需要的角色列表
            require_all: 是否需要所有角色（True）还是任一角色（False）
        """
        self.required_roles = required_roles
        self.require_all = require_all
    
    def __call__(
        self,
        current_user: User = Depends(AuthService.get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """检查用户角色."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证的用户"
            )
        
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        # 超级管理员拥有所有角色
        if current_user.has_role('SUPER_ADMIN'):
            return current_user
        
        # 检查角色
        if self.require_all:
            # 需要所有角色
            for role in self.required_roles:
                if not current_user.has_role(role):
                    logger.warning(
                        f"User {current_user.username} lacks role: {role}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少角色: {role}"
                    )
        else:
            # 需要任一角色
            has_any_role = any(
                current_user.has_role(role) 
                for role in self.required_roles
            )
            if not has_any_role:
                logger.warning(
                    f"User {current_user.username} lacks any of roles: {self.required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少以下任一角色: {', '.join(self.required_roles)}"
                )
        
        return current_user


class DepartmentChecker:
    """部门权限检查器类."""
    
    def __init__(self, allow_self_department: bool = True, allow_sub_departments: bool = False):
        """
        初始化部门权限检查器.
        
        Args:
            allow_self_department: 是否允许访问自己部门的数据
            allow_sub_departments: 是否允许访问子部门的数据
        """
        self.allow_self_department = allow_self_department
        self.allow_sub_departments = allow_sub_departments
    
    def __call__(
        self,
        target_department_id: int,
        current_user: User = Depends(AuthService.get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """检查部门访问权限."""
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证的用户"
            )
        
        # 超级管理员可以访问所有部门
        if current_user.has_role('SUPER_ADMIN'):
            return current_user
        
        # 检查是否可以管理该部门
        if current_user.can_manage_department(target_department_id):
            return current_user
        
        # 检查是否为同一部门
        if self.allow_self_department and current_user.department_id == target_department_id:
            return current_user
        
        # 检查是否为子部门
        if self.allow_sub_departments and current_user.department:
            allowed_dept_ids = current_user.department.get_all_children_ids()
            if target_department_id in allowed_dept_ids:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该部门的数据"
        )


# 常用权限依赖项
def require_admin() -> User:
    """要求管理员权限."""
    from .context import UserContext
    current_user = UserContext.require_current_user()
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_superuser() -> User:
    """要求超级管理员权限."""
    from .context import UserContext
    current_user = UserContext.require_current_user()
    # 检查用户是否为超级管理员
    if not current_user.has_role('SUPER_ADMIN'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


# 权限常量
class Permissions:
    """权限常量定义."""
    
    # 系统管理
    SYSTEM_ADMIN = "system:admin"
    
    # 用户管理
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_MANAGE = "user:manage"
    
    # 部门管理
    DEPT_CREATE = "department:create"
    DEPT_READ = "department:read"
    DEPT_UPDATE = "department:update"
    DEPT_DELETE = "department:delete"
    DEPT_MANAGE = "department:manage"
    
    # 角色权限管理
    ROLE_CREATE = "role:create"
    ROLE_READ = "role:read"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_MANAGE = "role:manage"
    
    PERMISSION_READ = "permission:read"
    PERMISSION_CREATE = "permission:create"
    PERMISSION_UPDATE = "permission:update"
    PERMISSION_DELETE = "permission:delete"
    PERMISSION_MANAGE = "permission:manage"
    PERMISSION_ASSIGN = "permission:assign"
    
    # 大模型管理
    LLM_CONFIG_CREATE = "llm_config:create"
    LLM_CONFIG_READ = "llm_config:read"
    LLM_CONFIG_UPDATE = "llm_config:update"
    LLM_CONFIG_DELETE = "llm_config:delete"
    LLM_CONFIG_MANAGE = "llm_config:manage"
    
    # 对话管理
    CHAT_CREATE = "chat:create"
    CHAT_READ = "chat:read"
    CHAT_UPDATE = "chat:update"
    CHAT_DELETE = "chat:delete"
    
    # 知识库管理
    KNOWLEDGE_CREATE = "knowledge:create"
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_UPDATE = "knowledge:update"
    KNOWLEDGE_DELETE = "knowledge:delete"
    KNOWLEDGE_MANAGE = "knowledge:manage"
    
    # 智能查询
    SMART_QUERY_USE = "smart_query:use"
    SMART_QUERY_MANAGE = "smart_query:manage"


# 常用权限检查器实例
require_user_read = PermissionChecker([Permissions.USER_READ])
require_user_manage = PermissionChecker([Permissions.USER_MANAGE])
require_dept_read = PermissionChecker([Permissions.DEPT_READ])
require_dept_manage = PermissionChecker([Permissions.DEPT_MANAGE])
require_role_read = PermissionChecker([Permissions.ROLE_READ])
require_role_manage = PermissionChecker([Permissions.ROLE_MANAGE])
require_llm_config_read = PermissionChecker([Permissions.LLM_CONFIG_READ])
require_llm_config_manage = PermissionChecker([Permissions.LLM_CONFIG_MANAGE])
require_permission_read = PermissionChecker([Permissions.PERMISSION_READ])
require_permission_manage = PermissionChecker([Permissions.PERMISSION_MANAGE])
require_system_admin = PermissionChecker([Permissions.SYSTEM_ADMIN])