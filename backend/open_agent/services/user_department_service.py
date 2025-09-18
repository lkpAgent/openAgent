"""User Department service for managing user-department associations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.user_department import UserDepartment
from ..models.user import User
from ..models.department import Department
from ..schemas.user_department import UserDepartmentCreate, UserDepartmentUpdate
from ..core.exceptions import NotFoundError, ValidationError


class UserDepartmentService:
    """Service for managing user-department associations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user_department(self, user_department_data: UserDepartmentCreate) -> UserDepartment:
        """Create a new user-department association."""
        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == user_department_data.user_id).first()
        if not user:
            raise NotFoundError(f"User with id {user_department_data.user_id} not found")
        
        # 检查部门是否存在
        department = self.db.query(Department).filter(Department.id == user_department_data.department_id).first()
        if not department:
            raise NotFoundError(f"Department with id {user_department_data.department_id} not found")
        
        # 检查是否已存在关联
        existing = self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_department_data.user_id,
                UserDepartment.department_id == user_department_data.department_id
            )
        ).first()
        
        if existing:
            raise ValidationError(f"User {user_department_data.user_id} is already associated with department {user_department_data.department_id}")
        
        # 如果设置为主要部门，需要将其他主要部门设置为非主要
        if user_department_data.is_primary:
            self.db.query(UserDepartment).filter(
                and_(
                    UserDepartment.user_id == user_department_data.user_id,
                    UserDepartment.is_primary == True
                )
            ).update({"is_primary": False})
        
        # 创建新的关联
        user_department = UserDepartment(**user_department_data.model_dump())
        self.db.add(user_department)
        self.db.commit()
        self.db.refresh(user_department)
        
        return user_department
    
    def get_user_departments(self, user_id: int, active_only: bool = True) -> List[UserDepartment]:
        """Get all departments for a user."""
        query = self.db.query(UserDepartment).filter(UserDepartment.user_id == user_id)
        
        if active_only:
            query = query.filter(UserDepartment.is_active == True)
        
        return query.all()
    
    def get_department_users(self, department_id: int, active_only: bool = True) -> List[UserDepartment]:
        """Get all users in a department."""
        query = self.db.query(UserDepartment).filter(UserDepartment.department_id == department_id)
        
        if active_only:
            query = query.filter(UserDepartment.is_active == True)
        
        return query.all()
    
    def get_user_primary_department(self, user_id: int) -> Optional[UserDepartment]:
        """Get user's primary department."""
        return self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_id,
                UserDepartment.is_primary == True,
                UserDepartment.is_active == True
            )
        ).first()
    
    def update_user_department(self, user_id: int, department_id: int, update_data: UserDepartmentUpdate) -> UserDepartment:
        """Update a user-department association."""
        user_department = self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_id,
                UserDepartment.department_id == department_id
            )
        ).first()
        
        if not user_department:
            raise NotFoundError(f"User-department association not found")
        
        # 如果设置为主要部门，需要将其他主要部门设置为非主要
        if update_data.is_primary and not user_department.is_primary:
            self.db.query(UserDepartment).filter(
                and_(
                    UserDepartment.user_id == user_id,
                    UserDepartment.is_primary == True,
                    UserDepartment.id != user_department.id
                )
            ).update({"is_primary": False})
        
        # 更新字段
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(user_department, field, value)
        
        self.db.commit()
        self.db.refresh(user_department)
        
        return user_department
    
    def remove_user_from_department(self, user_id: int, department_id: int) -> bool:
        """Remove user from department."""
        user_department = self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_id,
                UserDepartment.department_id == department_id
            )
        ).first()
        
        if not user_department:
            raise NotFoundError(f"User-department association not found")
        
        self.db.delete(user_department)
        self.db.commit()
        
        return True
    
    def set_user_primary_department(self, user_id: int, department_id: int) -> UserDepartment:
        """Set a department as user's primary department."""
        # 检查关联是否存在
        user_department = self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_id,
                UserDepartment.department_id == department_id,
                UserDepartment.is_active == True
            )
        ).first()
        
        if not user_department:
            raise NotFoundError(f"User-department association not found or inactive")
        
        # 将其他主要部门设置为非主要
        self.db.query(UserDepartment).filter(
            and_(
                UserDepartment.user_id == user_id,
                UserDepartment.is_primary == True,
                UserDepartment.id != user_department.id
            )
        ).update({"is_primary": False})
        
        # 设置为主要部门
        user_department.is_primary = True
        self.db.commit()
        self.db.refresh(user_department)
        
        return user_department
    
    def get_user_department_tree(self, user_id: int) -> List[dict]:
        """Get user's department hierarchy tree."""
        user_departments = self.get_user_departments(user_id)
        
        result = []
        for ud in user_departments:
            department_data = ud.department.to_dict()
            department_data.update({
                'is_primary': ud.is_primary,
                'is_active': ud.is_active,
                'association_created_at': ud.created_at
            })
            result.append(department_data)
        
        return result
    
    def get_users_with_departments(self, active_only: bool = True) -> List[int]:
        """Get all user IDs that have department associations."""
        query = self.db.query(UserDepartment.user_id).distinct()
        
        if active_only:
            query = query.filter(UserDepartment.is_active == True)
        
        result = query.all()
        return [row[0] for row in result]