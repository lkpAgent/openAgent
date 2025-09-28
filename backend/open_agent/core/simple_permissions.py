"""简化的权限检查系统."""

from functools import wraps
from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.user import User
from ..models.permission import Role
from ..services.auth import AuthService


def is_super_admin(user: User, db: Session) -> bool:
    """检查用户是否为超级管理员."""
    if not user or not user.is_active:
        return False
    
    # 检查用户是否有超级管理员角色
    for role in user.roles:
        if role.code == "SUPER_ADMIN":
            return True
    return False


def require_super_admin(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """要求超级管理员权限的依赖项."""
    if not is_super_admin(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="需要超级管理员权限"
        )
    return current_user


def require_authenticated_user(
    current_user: User = Depends(AuthService.get_current_user)
) -> User:
    """要求已认证用户的依赖项."""
    if not current_user or not current_user.is_active:
        raise HTTPException(
            status_code=401,
            detail="需要登录"
        )
    return current_user


class SimplePermissionChecker:
    """简化的权限检查器."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_super_admin(self, user: User) -> bool:
        """检查是否为超级管理员."""
        return is_super_admin(user, self.db)
    
    def check_user_access(self, user: User, target_user_id: int) -> bool:
        """检查用户访问权限（自己或超级管理员）."""
        if not user or not user.is_active:
            return False
        
        # 超级管理员可以访问所有用户
        if self.check_super_admin(user):
            return True
        
        # 用户只能访问自己的信息
        return user.id == target_user_id


# 权限装饰器
def super_admin_required(func):
    """超级管理员权限装饰器."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 这个装饰器主要用于服务层，实际的FastAPI依赖项检查在路由层
        return func(*args, **kwargs)
    return wrapper


def authenticated_required(func):
    """认证用户权限装饰器."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 这个装饰器主要用于服务层，实际的FastAPI依赖项检查在路由层
        return func(*args, **kwargs)
    return wrapper