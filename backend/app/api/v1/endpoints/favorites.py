import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.api.v1.dependencies import ActiveUser, DBSession
from app.models.favorite import Favorite
from app.models.prediction import Prediction
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.favorite import FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get(
    "",
    summary="Get user favorites",
    response_model=APIResponse[PaginatedResponse[FavoriteResponse]],
)
async def get_favorites(
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> APIResponse[PaginatedResponse[FavoriteResponse]]:
    """Get the paginated list of favorites for the authenticated user."""
    skip = (page - 1) * page_size
    
    # Query favorites with joined prediction
    stmt = (
        select(Favorite)
        .where(Favorite.user_id == current_user.id)
        .options(selectinload(Favorite.prediction))
        .order_by(Favorite.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    # Count total
    count_stmt = select(Favorite).where(Favorite.user_id == current_user.id)
    count_res = await db.execute(count_stmt)
    total = len(count_res.scalars().all())
    
    total_pages = max(1, -(-total // page_size))
    
    return APIResponse(
        success=True,
        message="Favorites retrieved.",
        data=PaginatedResponse(
            items=[FavoriteResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )

@router.post(
    "/{prediction_id}",
    summary="Add prediction to favorites",
    response_model=APIResponse[FavoriteResponse],
)
async def add_favorite(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
) -> APIResponse[FavoriteResponse]:
    """Add a prediction to the authenticated user's favorites."""
    # Ensure prediction exists
    pred = await db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Prediction not found.", "error_code": "NOT_FOUND"},
        )
        
    fav = Favorite(user_id=current_user.id, prediction_id=prediction_id)
    db.add(fav)
    
    try:
        await db.commit()
        await db.refresh(fav, ["prediction"])
    except IntegrityError:
        await db.rollback()
        # Already favorited, just fetch it
        stmt = select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.prediction_id == prediction_id)
        ).options(selectinload(Favorite.prediction))
        res = await db.execute(stmt)
        fav = res.scalar_one()

    return APIResponse(
        success=True,
        message="Prediction added to favorites.",
        data=FavoriteResponse.model_validate(fav),
    )

@router.delete(
    "/{prediction_id}",
    summary="Remove prediction from favorites",
    response_model=APIResponse,
)
async def remove_favorite(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
) -> APIResponse:
    """Remove a prediction from favorites."""
    stmt = delete(Favorite).where(
        and_(Favorite.user_id == current_user.id, Favorite.prediction_id == prediction_id)
    )
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Favorite not found.", "error_code": "NOT_FOUND"},
        )
        
    return APIResponse(success=True, message="Prediction removed from favorites.")
