"""
AutoWorth AI — Users Admin Endpoints

Admin-only routes for user management.

Routes:
  GET    /users              — Paginated user list (Admin only)
  GET    /users/{user_id}    — Single user detail (Admin only)
  PATCH  /users/{user_id}/deactivate  — Deactivate a user (Admin only)
  PATCH  /users/{user_id}/activate    — Reactivate a user (Admin only)
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.dependencies import AdminUser, DBSession
from app.repositories.user_repository import UserRepository
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users (Admin)"])


# ──────────────────────────────────────────────
# List Users
# ──────────────────────────────────────────────
@router.get(
    "",
    summary="List all users (Admin)",
    response_model=APIResponse[PaginatedResponse[UserResponse]],
)
async def list_users(
    _current_admin: AdminUser,
    db: DBSession,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(default=False, description="Filter to active users only"),
) -> APIResponse[PaginatedResponse[UserResponse]]:
    """
    Return a paginated list of all users. Admin access required.
    """
    skip = (page - 1) * page_size
    user_repo = UserRepository(db)
    users = await user_repo.get_all_paginated(
        skip=skip, limit=page_size, active_only=active_only
    )
    total = await user_repo.count()

    import math
    total_pages = math.ceil(total / page_size) if total else 1

    paginated = PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    return APIResponse(success=True, message="OK", data=paginated)


# ──────────────────────────────────────────────
# Get Single User
# ──────────────────────────────────────────────
@router.get(
    "/{user_id}",
    summary="Get a single user by ID (Admin)",
    response_model=APIResponse[UserResponse],
)
async def get_user(
    user_id: uuid.UUID,
    _current_admin: AdminUser,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Fetch a single user's profile by UUID. Admin access required.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_role(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "User not found.",
                "error_code": "USER_NOT_FOUND",
            },
        )
    return APIResponse(
        success=True, message="OK", data=UserResponse.model_validate(user)
    )


# ──────────────────────────────────────────────
# Deactivate User
# ──────────────────────────────────────────────
@router.patch(
    "/{user_id}/deactivate",
    summary="Deactivate a user account (Admin)",
    response_model=APIResponse[UserResponse],
)
async def deactivate_user(
    user_id: uuid.UUID,
    current_admin: AdminUser,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Deactivate a user account. Admin access required.
    Admins cannot deactivate their own account.
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "You cannot deactivate your own account.",
                "error_code": "CANNOT_SELF_DEACTIVATE",
            },
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_role(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "User not found.",
                "error_code": "USER_NOT_FOUND",
            },
        )

    updated = await user_repo.update(user, is_active=False)
    await db.commit()
    return APIResponse(
        success=True,
        message="User account deactivated.",
        data=UserResponse.model_validate(updated),
    )


# ──────────────────────────────────────────────
# Reactivate User
# ──────────────────────────────────────────────
@router.patch(
    "/{user_id}/activate",
    summary="Reactivate a user account (Admin)",
    response_model=APIResponse[UserResponse],
)
async def activate_user(
    user_id: uuid.UUID,
    _current_admin: AdminUser,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Reactivate a previously deactivated user. Admin access required.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_role(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "User not found.",
                "error_code": "USER_NOT_FOUND",
            },
        )

    updated = await user_repo.update(user, is_active=True)
    await db.commit()
    return APIResponse(
        success=True,
        message="User account reactivated.",
        data=UserResponse.model_validate(updated),
    )
