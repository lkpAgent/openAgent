"""User management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...core.permissions import require_superuser
from ...services.auth import AuthService
from ...services.user import UserService
from ...utils.schemas import UserResponse, UserUpdate, UserCreate

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user = Depends(AuthService.get_current_user)
):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    user_service = UserService(db)
    
    # Check if email is being changed and is already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = user_service.get_user_by_email(user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user
    updated_user = user_service.update_user(current_user.id, user_update)
    return UserResponse.from_orm(updated_user)


@router.delete("/profile")
async def delete_user_account(
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account."""
    user_service = UserService(db)
    user_service.delete_user(current_user.id)
    return {"message": "Account deleted successfully"}


# Admin endpoints
@router.post("/", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    current_user = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    user_service = UserService(db)
    
    # Check if username already exists
    existing_user = user_service.get_user_by_username(user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_user = user_service.get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = user_service.create_user(user_create)
    return UserResponse.from_orm(new_user)


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    role_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """List all users with pagination and filters (admin only)."""
    user_service = UserService(db)
    skip = (page - 1) * size
    users, total = user_service.get_users_with_filters(
        skip=skip, 
        limit=size, 
        search=search,
        department_id=department_id,
        role_id=role_id,
        is_active=is_active
    )
    result = {
        "users": [UserResponse.from_orm(user) for user in users],
        "total": total,
        "page": page,
        "page_size": size
    }
    return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(AuthService.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)."""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user = Depends(AuthService.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user by ID (admin only)."""
    user_service = UserService(db)
    
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_service.update_user(user_id, user_update)
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(AuthService.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user by ID (admin only)."""
    user_service = UserService(db)
    
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}