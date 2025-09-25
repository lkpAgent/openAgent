"""Role management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...core.simple_permissions import require_super_admin
from ...db.database import get_db
from ...models.user import User
from ...models.permission import Role, UserRole
from ...services.auth import AuthService
from ...utils.logger import get_logger
from ...schemas.permission import (
    RoleCreate, RoleUpdate, RoleResponse,
    UserRoleAssign
)

logger = get_logger(__name__)
router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleResponse])
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin),
):
    """获取角色列表."""
    try:
        query = db.query(Role)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    Role.name.ilike(f"%{search}%"),
                    Role.code.ilike(f"%{search}%"),
                    Role.description.ilike(f"%{search}%")
                )
            )
        
        # 状态筛选
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        # 分页
        roles = query.offset(skip).limit(limit).all()
        
        return [role.to_dict() for role in roles]
        
    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色列表失败"
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """获取角色详情."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        return role.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色详情失败"
        )


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """创建角色."""
    try:
        # 检查角色代码是否已存在
        existing_role = db.query(Role).filter(
            Role.code == role_data.code
        ).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色代码已存在"
            )
        
        # 创建角色
        role = Role(
            name=role_data.name,
            code=role_data.code,
            description=role_data.description,
            is_active=role_data.is_active
        )
        role.set_audit_fields(current_user.id)
        
        db.add(role)
        db.commit()
        db.refresh(role)
        
        logger.info(f"Role created: {role.name} by user {current_user.username}")
        return role.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建角色失败"
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """更新角色."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 超级管理员角色不能被编辑
        if role.code == "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="超级管理员角色不能被编辑"
            )
        
        # 检查角色编码是否已存在（排除当前角色）
        if role_data.code and role_data.code != role.code:
            existing_role = db.query(Role).filter(
                and_(
                    Role.code == role_data.code,
                    Role.id != role_id
                )
            ).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色代码已存在"
                )
        
        # 更新字段
        update_data = role_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)
        
        role.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(role)
        
        logger.info(f"Role updated: {role.name} by user {current_user.username}")
        return role.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新角色失败"
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """删除角色."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 超级管理员角色不能被删除
        if role.code == "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="超级管理员角色不能被删除"
            )
        
        # 检查是否有用户使用该角色
        user_count = db.query(UserRole).filter(
            UserRole.role_id == role_id
        ).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法删除角色，还有 {user_count} 个用户关联此角色"
            )
        
        # 删除角色
        db.delete(role)
        db.commit()
        
        logger.info(f"Role deleted: {role.name} by user {current_user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除角色失败"
        )


# 用户角色管理路由
user_role_router = APIRouter(prefix="/user-roles", tags=["user-roles"])


@user_role_router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_user_roles(
    assignment_data: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """为用户分配角色."""
    try:
        # 验证用户是否存在
        user = db.query(User).filter(User.id == assignment_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证角色是否存在
        roles = db.query(Role).filter(
            Role.id.in_(assignment_data.role_ids)
        ).all()
        if len(roles) != len(assignment_data.role_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分角色不存在"
            )
        
        # 删除现有角色关联
        db.query(UserRole).filter(
            UserRole.user_id == assignment_data.user_id
        ).delete()
        
        # 添加新的角色关联
        for role_id in assignment_data.role_ids:
            user_role = UserRole(
                user_id=assignment_data.user_id,
                role_id=role_id
            )
            db.add(user_role)
        
        db.commit()
        
        logger.info(f"User roles assigned: user {user.username}, roles {assignment_data.role_ids} by user {current_user.username}")
        
        return {"message": "角色分配成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning roles to user {assignment_data.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="角色分配失败"
        )


@user_role_router.get("/user/{user_id}", response_model=List[RoleResponse])
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_active_user)
):
    """获取用户角色列表."""
    try:
        # 检查权限：用户只能查看自己的角色，或者是超级管理员
        if current_user.id != user_id and not current_user.is_superuser():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限查看其他用户的角色"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        roles = db.query(Role).join(
            UserRole, Role.id == UserRole.role_id
        ).filter(
            UserRole.user_id == user_id
        ).all()
        
        return [role.to_dict() for role in roles]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user roles {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户角色失败"
        )


# 将子路由添加到主路由
router.include_router(user_role_router)