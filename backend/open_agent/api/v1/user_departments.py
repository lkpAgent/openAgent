"""User Department API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...services.user_department_service import UserDepartmentService
from ...schemas.user_department import (
    UserDepartmentCreate, UserDepartmentUpdate, UserDepartmentResponse,
    UserDepartmentWithDetails, DepartmentUserList, UserDepartmentList,
    SetPrimaryDepartmentRequest, BulkUserDepartmentCreate, BulkUserDepartmentResponse
)
from ...core.exceptions import NotFoundError, ValidationError
from ...services.auth import AuthService
from ...models.user import User

router = APIRouter(prefix="/user-departments", tags=["user-departments"])


@router.post("/", response_model=UserDepartmentResponse)
async def create_user_department(
    user_department_data: UserDepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a new user-department association."""
    try:
        service = UserDepartmentService(db)
        user_department = service.create_user_department(user_department_data)
        return user_department
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}", response_model=UserDepartmentList)
async def get_user_departments(
    user_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all departments for a user."""
    try:
        service = UserDepartmentService(db)
        user_departments = service.get_user_departments(user_id, active_only)
        
        # 获取用户信息
        from ...models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # 获取主要部门
        primary_department = service.get_user_primary_department(user_id)
        
        # 构建响应数据
        departments_with_details = []
        for ud in user_departments:
            dept_detail = UserDepartmentWithDetails(
                id=ud.id,
                user_id=ud.user_id,
                department_id=ud.department_id,
                is_primary=ud.is_primary,
                is_active=ud.is_active,
                created_at=ud.created_at,
                updated_at=ud.updated_at,
                user_name=user.full_name,
                user_email=user.email,
                department_name=ud.department.name,
                department_code=ud.department.code
            )
            departments_with_details.append(dept_detail)
        
        primary_dept_detail = None
        if primary_department:
            primary_dept_detail = UserDepartmentWithDetails(
                id=primary_department.id,
                user_id=primary_department.user_id,
                department_id=primary_department.department_id,
                is_primary=primary_department.is_primary,
                is_active=primary_department.is_active,
                created_at=primary_department.created_at,
                updated_at=primary_department.updated_at,
                user_name=user.full_name,
                user_email=user.email,
                department_name=primary_department.department.name,
                department_code=primary_department.department.code
            )
        
        return UserDepartmentList(
            user_id=user_id,
            user_name=user.full_name,
            user_email=user.email,
            departments=departments_with_details,
            primary_department=primary_dept_detail,
            total_departments=len(departments_with_details)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/department/{department_id}", response_model=DepartmentUserList)
async def get_department_users(
    department_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all users in a department."""
    try:
        service = UserDepartmentService(db)
        department_users = service.get_department_users(department_id, active_only)
        
        # 获取部门信息
        from ...models.department import Department
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        
        # 构建响应数据
        users_with_details = []
        active_count = 0
        for ud in department_users:
            if ud.is_active:
                active_count += 1
            
            user_detail = UserDepartmentWithDetails(
                id=ud.id,
                user_id=ud.user_id,
                department_id=ud.department_id,
                is_primary=ud.is_primary,
                is_active=ud.is_active,
                created_at=ud.created_at,
                updated_at=ud.updated_at,
                user_name=ud.user.full_name,
                user_email=ud.user.email,
                department_name=department.name,
                department_code=department.code
            )
            users_with_details.append(user_detail)
        
        return DepartmentUserList(
            department_id=department_id,
            department_name=department.name,
            department_code=department.code,
            users=users_with_details,
            total_users=len(users_with_details),
            active_users=active_count
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/user/{user_id}/department/{department_id}", response_model=UserDepartmentResponse)
async def update_user_department(
    user_id: int,
    department_id: int,
    update_data: UserDepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Update a user-department association."""
    try:
        service = UserDepartmentService(db)
        user_department = service.update_user_department(user_id, department_id, update_data)
        return user_department
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/user/{user_id}/department/{department_id}")
async def remove_user_from_department(
    user_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Remove user from department."""
    try:
        service = UserDepartmentService(db)
        service.remove_user_from_department(user_id, department_id)
        return {"message": "User removed from department successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/user/{user_id}/primary-department", response_model=UserDepartmentResponse)
async def set_primary_department(
    user_id: int,
    request: SetPrimaryDepartmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Set a department as user's primary department."""
    try:
        service = UserDepartmentService(db)
        user_department = service.set_user_primary_department(user_id, request.department_id)
        return user_department
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}/primary-department", response_model=UserDepartmentResponse)
async def get_user_primary_department(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get user's primary department."""
    try:
        service = UserDepartmentService(db)
        primary_department = service.get_user_primary_department(user_id)
        if not primary_department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No primary department found")
        return primary_department
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/bulk", response_model=BulkUserDepartmentResponse)
async def bulk_create_user_departments(
    bulk_data: BulkUserDepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Bulk create user-department associations."""
    try:
        service = UserDepartmentService(db)
        
        success_count = 0
        failed_count = 0
        errors = []
        created_associations = []
        
        for user_id in bulk_data.user_ids:
            try:
                user_dept_data = UserDepartmentCreate(
                    user_id=user_id,
                    department_id=bulk_data.department_id,
                    is_primary=bulk_data.is_primary,
                    is_active=bulk_data.is_active
                )
                
                user_department = service.create_user_department(user_dept_data)
                created_associations.append(user_department)
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"User {user_id}: {str(e)}")
        
        return BulkUserDepartmentResponse(
            success_count=success_count,
            failed_count=failed_count,
            errors=errors,
            created_associations=created_associations
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users-with-departments")
async def get_users_with_departments(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get all user IDs that have department associations."""
    try:
        service = UserDepartmentService(db)
        user_ids = service.get_users_with_departments(active_only)
        return {"user_ids": user_ids}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user/{user_id}/tree")
async def get_user_department_tree(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get user's department hierarchy tree."""
    try:
        service = UserDepartmentService(db)
        tree = service.get_user_department_tree(user_id)
        return {"user_id": user_id, "department_tree": tree}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))