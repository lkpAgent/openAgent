"""User management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...services.auth import AuthService
from ...services.user import UserService
from ...utils.schemas import UserResponse, UserUpdate

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
@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(AuthService.get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    return [UserResponse.from_orm(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(AuthService.get_current_active_superuser),
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
    current_user = Depends(AuthService.get_current_active_superuser),
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
    current_user = Depends(AuthService.get_current_active_superuser),
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