"""Role and permission management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ...core.permissions import require_superuser
from ...db.database import get_db
from ...models.user import User
from ...models.permission import Role, Permission, RolePermission, UserRole
from ...core.permissions import (
    require_role_read, require_role_manage, require_admin,
    require_permission_read, require_permission_manage,
    Permissions
)
from ...services.auth import AuthService
from ...utils.logger import get_logger
from ...schemas.permission import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse, 
    UserRoleAssign, RolePermissionAssign
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
    current_user = Depends(require_superuser),
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
    current_user: User = Depends(require_role_read)
):
    """获取角色详情."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        return role.to_dict(include_permissions=True)
        
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
    current_user: User = Depends(require_role_manage)
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
    current_user: User = Depends(require_role_manage)
):
    """更新角色."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查角色代码是否已存在（排除自己）
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
    current_user: User = Depends(require_role_manage)
):
    """删除角色."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查是否有用户使用该角色
        user_count = db.query(UserRole).filter(
            UserRole.role_id == role_id
        ).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该角色还有用户在使用，无法删除"
            )
        
        # 删除角色权限关联
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id
        ).delete()
        
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


@router.post("/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_role_permissions(
    role_id: int,
    permission_data: RolePermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_manage)
):
    """为角色分配权限."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 验证权限是否存在
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_data.permission_ids)
        ).all()
        if len(permissions) != len(permission_data.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分权限不存在"
            )
        
        # 删除现有权限关联
        db.query(RolePermission).filter(
            RolePermission.role_id == role_id
        ).delete()
        
        # 添加新的权限关联
        for permission_id in permission_data.permission_ids:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            db.add(role_permission)
        
        db.commit()
        
        logger.info(f"Role permissions assigned: role {role.name}, permissions {permission_data.permission_ids} by user {current_user.username}")
        
        return {"message": "权限分配成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning permissions to role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="权限分配失败"
        )


@router.get("/{role_id}/permissions", response_model=List[PermissionResponse])
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_read)
):
    """获取角色权限列表."""
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        permissions = db.query(Permission).join(
            RolePermission, Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id == role_id
        ).all()

        return [permission.to_dict() for permission in permissions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role permissions {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色权限失败"
        )


# 权限管理路由
permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permission_router.get("/")
async def get_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_superuser)
):
    """获取权限列表."""
    try:
        query = db.query(Permission)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    Permission.name.ilike(f"%{search}%"),
                    Permission.code.ilike(f"%{search}%"),
                    Permission.description.ilike(f"%{search}%")
                )
            )
        
        # 资源筛选
        if resource:
            query = query.filter(Permission.resource == resource)
            
        # 操作筛选
        if action:
            query = query.filter(Permission.action == action)

        # 获取总数
        total = query.count()
        
        # 分页
        skip = (page - 1) * page_size
        permissions = query.offset(skip).limit(page_size).all()
        
        return {
            "items": [permission.to_dict() for permission in permissions],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限列表失败"
        )


@permission_router.get("/categories")
async def get_permission_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_read)
):
    """获取权限分类列表."""
    try:
        categories = db.query(Permission.category).distinct().all()
        return [category[0] for category in categories if category[0]]
        
    except Exception as e:
        logger.error(f"Error getting permission categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限分类失败"
        )


@permission_router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_manage)
):
    """创建权限."""
    try:
        # 检查权限代码是否已存在
        existing_permission = db.query(Permission).filter(
            Permission.code == permission_data.code
        ).first()
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限代码已存在"
            )
        
        # 创建权限
        permission = Permission(**permission_data.dict())
        permission.set_audit_fields(current_user.id)
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        logger.info(f"Permission created: {permission.name} ({permission.code}) by user {current_user.username}")
        
        return permission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建权限失败"
        )


@permission_router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_read)
):
    """获取权限详情."""
    try:
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        return permission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限详情失败"
        )


@permission_router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_manage)
):
    """更新权限."""
    try:
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 检查权限代码是否与其他权限冲突
        if permission_data.code and permission_data.code != permission.code:
            existing_permission = db.query(Permission).filter(
                and_(
                    Permission.code == permission_data.code,
                    Permission.id != permission_id
                )
            ).first()
            if existing_permission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="权限代码已存在"
                )
        
        # 更新权限信息
        update_data = permission_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        permission.set_audit_fields(current_user.id, is_update=True)
        db.commit()
        db.refresh(permission)
        
        logger.info(f"Permission updated: {permission.name} ({permission.code}) by user {current_user.username}")
        
        return permission.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新权限失败"
        )


@permission_router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission_manage)
):
    """删除权限."""
    try:
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="权限不存在"
            )
        
        # 检查权限是否被角色使用
        role_permissions = db.query(RolePermission).filter(
            RolePermission.permission_id == permission_id
        ).first()
        if role_permissions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限正在被角色使用，无法删除"
            )
        
        db.delete(permission)
        db.commit()
        
        logger.info(f"Permission deleted: {permission.name} ({permission.code}) by user {current_user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting permission {permission_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除权限失败"
        )


# 用户角色管理路由
user_role_router = APIRouter(prefix="/user-roles", tags=["user-roles"])


@user_role_router.post("/assign", status_code=status.HTTP_201_CREATED)
async def assign_user_roles(
    assignment_data: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_manage)
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
    # current_user: User = Depends(require_role_read)
):
    """获取用户角色列表."""
    try:
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
router.include_router(permission_router)
router.include_router(user_role_router)