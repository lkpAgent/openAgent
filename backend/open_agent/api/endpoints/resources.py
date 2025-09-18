"""Resource management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...db.database import get_db
from ...models.user import User
from ...models.resource import Resource, RoleResource
from ...models.permission import Role
from ...core.permissions import (
    require_admin, require_system_admin,
    Permissions
)
from ...services.auth import AuthService
from ...utils.logger import get_logger
from ...schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceTreeNode,
    RoleResourceAssign
)

logger = get_logger(__name__)
router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/", response_model=List[ResourceResponse])
async def get_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取资源列表."""
    try:
        query = db.query(Resource)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    Resource.name.ilike(f"%{search}%"),
                    Resource.code.ilike(f"%{search}%"),
                    Resource.description.ilike(f"%{search}%")
                )
            )
        
        # 类型筛选
        if type:
            query = query.filter(Resource.type == type)
            
        # 父级筛选
        if parent_id is not None:
            query = query.filter(Resource.parent_id == parent_id)
        
        # 排序
        query = query.order_by(Resource.sort_order, Resource.id)
        
        # 分页
        resources = query.offset(skip).limit(limit).all()
        
        return [resource.to_dict() for resource in resources]
        
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源列表失败"
        )


@router.get("/tree", response_model=List[ResourceTreeNode])
async def get_resource_tree(
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取资源树."""
    try:
        query = db.query(Resource).filter(Resource.parent_id.is_(None))
        
        # 类型筛选
        if type:
            query = query.filter(Resource.type == type)
            
        # 排序
        query = query.order_by(Resource.sort_order, Resource.id)
        
        root_resources = query.all()
        
        return [resource.to_tree_node() for resource in root_resources]
        
    except Exception as e:
        logger.error(f"Error getting resource tree: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源树失败"
        )


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取资源详情."""
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        return resource.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resource {resource_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源详情失败"
        )


@router.post("/", response_model=ResourceResponse)
async def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin)
):
    """创建资源."""
    try:
        # 检查编码是否已存在
        existing = db.query(Resource).filter(Resource.code == resource_data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="资源编码已存在"
            )
        
        # 检查父级资源是否存在
        if resource_data.parent_id:
            parent = db.query(Resource).filter(Resource.id == resource_data.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父级资源不存在"
                )
        
        # 创建资源
        resource = Resource(**resource_data.model_dump())
        db.add(resource)
        db.commit()
        db.refresh(resource)
        
        logger.info(f"Resource created: {resource.code} by user {current_user.username}")
        return resource.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建资源失败"
        )


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin)
):
    """更新资源."""
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        # 检查编码是否已被其他资源使用
        if resource_data.code and resource_data.code != resource.code:
            existing = db.query(Resource).filter(
                and_(Resource.code == resource_data.code, Resource.id != resource_id)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="资源编码已存在"
                )
        
        # 检查父级资源
        if resource_data.parent_id is not None:
            if resource_data.parent_id == resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能将自己设为父级资源"
                )
            if resource_data.parent_id > 0:
                parent = db.query(Resource).filter(Resource.id == resource_data.parent_id).first()
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="父级资源不存在"
                    )
        
        # 更新资源
        update_data = resource_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(resource, field, value)
        
        db.commit()
        db.refresh(resource)
        
        logger.info(f"Resource updated: {resource.code} by user {current_user.username}")
        return resource.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating resource {resource_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新资源失败"
        )


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin)
):
    """删除资源."""
    try:
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        # 检查是否有子资源
        children_count = db.query(Resource).filter(Resource.parent_id == resource_id).count()
        if children_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="存在子资源，无法删除"
            )
        
        # 删除资源
        db.delete(resource)
        db.commit()
        
        logger.info(f"Resource deleted: {resource.code} by user {current_user.username}")
        return {"message": "资源删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting resource {resource_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除资源失败"
        )


@router.post("/roles/assign")
async def assign_role_resources(
    assignment: RoleResourceAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin)
):
    """分配角色资源."""
    try:
        # 检查角色是否存在
        role = db.query(Role).filter(Role.id == assignment.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查资源是否存在
        resources = db.query(Resource).filter(Resource.id.in_(assignment.resource_ids)).all()
        if len(resources) != len(assignment.resource_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分资源不存在"
            )
        
        # 删除现有的角色资源关联
        db.query(RoleResource).filter(RoleResource.role_id == assignment.role_id).delete()
        
        # 创建新的角色资源关联
        for resource_id in assignment.resource_ids:
            role_resource = RoleResource(
                role_id=assignment.role_id,
                resource_id=resource_id
            )
            db.add(role_resource)
        
        db.commit()
        
        logger.info(f"Role resources assigned: role_id={assignment.role_id}, resources={assignment.resource_ids} by user {current_user.username}")
        return {"message": "角色资源分配成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning role resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配角色资源失败"
        )


@router.get("/roles/{role_id}", response_model=List[ResourceResponse])
async def get_role_resources(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取角色的资源列表."""
    try:
        # 检查角色是否存在
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 获取角色的资源
        resources = db.query(Resource).join(
            RoleResource, Resource.id == RoleResource.resource_id
        ).filter(RoleResource.role_id == role_id).order_by(
            Resource.sort_order, Resource.id
        ).all()
        
        return [resource.to_dict() for resource in resources]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role resources for role {role_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取角色资源失败"
        )