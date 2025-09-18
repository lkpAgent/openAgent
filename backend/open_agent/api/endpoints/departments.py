"""Department management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...db.database import get_db
from ...models.user import User
from ...models.department import Department
from ...core.permissions import (
    require_dept_read, require_dept_manage, require_admin,
    DepartmentChecker, Permissions
)
from ...services.auth import AuthService
from ...utils.logger import get_logger
from ...schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentTreeResponse
)

logger = get_logger(__name__)
router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dept_read)
):
    """获取部门列表."""
    try:
        query = db.query(Department)
        
        # 如果不是超级管理员，只能查看自己部门及子部门
        # if not current_user.is_superuser:
        #     if current_user.department_id:
        #         # 获取用户部门及其所有子部门ID
        #         user_dept = db.query(Department).filter(
        #             Department.id == current_user.department_id
        #         ).first()
        #         if user_dept:
        #             allowed_dept_ids = [current_user.department_id] + user_dept.get_all_children_ids()
        #             query = query.filter(Department.id.in_(allowed_dept_ids))
        #         else:
        #             # 用户没有部门，返回空列表
        #             return []
        #     else:
        #         # 用户没有部门，返回空列表
        #         return []
        
        # 按父部门筛选
        if parent_id is not None:
            query = query.filter(Department.parent_id == parent_id)
        
        # 搜索
        if search:
            query = query.filter(
                or_(
                    Department.name.ilike(f"%{search}%"),
                    Department.code.ilike(f"%{search}%"),
                    Department.description.ilike(f"%{search}%")
                )
            )
        
        # 排序
        query = query.order_by(Department.sort_order, Department.name)
        
        # 分页
        departments = query.offset(skip).limit(limit).all()
        
        return [dept.to_dict() for dept in departments]
        
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门列表失败"
        )


@router.get("/tree", response_model=List[DepartmentTreeResponse])
async def get_department_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dept_read)
):
    """获取部门树形结构."""
    try:
        # 获取所有部门
        query = db.query(Department)
        
        # 如果不是超级管理员，只能查看自己部门及子部门
        # if not current_user.is_superuser:
        #     if current_user.department_id:
        #         user_dept = db.query(Department).filter(
        #             Department.id == current_user.department_id
        #         ).first()
        #         if user_dept:
        #             allowed_dept_ids = [current_user.department_id] + user_dept.get_all_children_ids()
        #             query = query.filter(Department.id.in_(allowed_dept_ids))
        #         else:
        #             return []
        #     else:
        #         return []
        
        departments = query.order_by(Department.sort_order, Department.name).all()
        
        # 构建树形结构
        dept_dict = {dept.id: dept.to_dict(include_children=False) for dept in departments}
        tree = []
        
        # 为每个部门初始化children数组
        for dept_data in dept_dict.values():
            dept_data['children'] = []
        
        # 构建父子关系
        for dept in departments:
            dept_data = dept_dict[dept.id]
            if dept.parent_id is None:
                tree.append(dept_data)
            else:
                parent = dept_dict.get(dept.parent_id)
                if parent:
                    parent['children'].append(dept_data)
        
        return tree
        
    except Exception as e:
        logger.error(f"Error getting department tree: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门树失败"
        )


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(DepartmentChecker(allow_self_department=True, allow_sub_departments=True))
):
    """获取部门详情."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部门不存在"
            )
        
        return department.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门详情失败"
        )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dept_manage)
):
    """创建部门."""
    try:
        # 检查部门代码是否已存在
        existing_dept = db.query(Department).filter(
            Department.code == department_data.code
        ).first()
        if existing_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部门代码已存在"
            )
        
        # 检查父部门是否存在
        if department_data.parent_id:
            parent_dept = db.query(Department).filter(
                Department.id == department_data.parent_id
            ).first()
            if not parent_dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="父部门不存在"
                )
            
            # 检查权限：只能在自己管理的部门下创建子部门
            if not current_user.is_superuser and not current_user.can_manage_department(department_data.parent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权在该部门下创建子部门"
                )
        
        # 创建部门
        department = Department(
            name=department_data.name,
            code=department_data.code,
            description=department_data.description,
            parent_id=department_data.parent_id,
            sort_order=department_data.sort_order or 0,
            is_active=department_data.is_active
        )
        department.set_audit_fields(current_user.id)
        
        db.add(department)
        db.commit()
        db.refresh(department)
        
        logger.info(f"Department created: {department.name} by user {current_user.username}")
        return department.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating department: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建部门失败"
        )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dept_manage)
):
    """更新部门."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部门不存在"
            )
        
        # 检查权限
        if not current_user.is_superuser and not current_user.can_manage_department(department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改该部门"
            )
        
        # 检查部门代码是否已存在（排除自己）
        if department_data.code and department_data.code != department.code:
            existing_dept = db.query(Department).filter(
                and_(
                    Department.code == department_data.code,
                    Department.id != department_id
                )
            ).first()
            if existing_dept:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部门代码已存在"
                )
        
        # 检查父部门变更
        if department_data.parent_id is not None and department_data.parent_id != department.parent_id:
            if department_data.parent_id == department_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部门不能设置自己为父部门"
                )
            
            # 检查是否会形成循环引用
            if department_data.parent_id in department.get_all_children_ids():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能将子部门设置为父部门"
                )
            
            # 检查新父部门是否存在
            if department_data.parent_id:
                parent_dept = db.query(Department).filter(
                    Department.id == department_data.parent_id
                ).first()
                if not parent_dept:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="父部门不存在"
                    )
        
        # 更新字段
        update_data = department_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(department, field, value)
        
        department.set_audit_fields(current_user.id, is_update=True)
        
        db.commit()
        db.refresh(department)
        
        logger.info(f"Department updated: {department.name} by user {current_user.username}")
        return department.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新部门失败"
        )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dept_manage)
):
    """删除部门."""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部门不存在"
            )
        
        # 检查权限
        if not current_user.is_superuser and not current_user.can_manage_department(department_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除该部门"
            )
        
        # 检查是否有子部门
        child_count = db.query(Department).filter(
            Department.parent_id == department_id
        ).count()
        if child_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该部门下还有子部门，无法删除"
            )
        
        # 检查是否有用户
        from ...models.user_department import UserDepartment
        user_count = db.query(UserDepartment).filter(
            UserDepartment.department_id == department_id
        ).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该部门下还有用户，无法删除"
            )
        
        db.delete(department)
        db.commit()
        
        logger.info(f"Department deleted: {department.name} by user {current_user.username}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting department {department_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除部门失败"
        )