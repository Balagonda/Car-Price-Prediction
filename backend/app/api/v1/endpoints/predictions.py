"""
AutoWorth AI — Prediction Endpoints

User-facing API for vehicle price predictions and history.

Layer: API Layer
Auth: Verified users only (JWT)
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response

from app.api.v1.dependencies import DBSession, VerifiedUser, ActiveUser
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.prediction import (
    PredictionListItem,
    PredictionRequest,
    PredictionResponse,
    MarketplaceListing,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ──────────────────────────────────────────────
# POST /predictions — Create Prediction
# ──────────────────────────────────────────────
@router.post(
    "",
    response_model=APIResponse[PredictionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Vehicle Price Prediction",
    description=(
        "Submit vehicle specifications and receive an AI-powered price estimate, "
        "SHAP feature explanations, 5 similar historical vehicles, and actionable "
        "recommendations. Response time target: < 3 seconds."
    ),
)
async def create_prediction(
    data: PredictionRequest,
    current_user: VerifiedUser,
    db: DBSession,
) -> APIResponse[PredictionResponse]:
    """
    Create a new prediction for the authenticated user.

    - Requires a verified user account.
    - Returns estimated price, confidence score (0–100%), SHAP breakdown,
      5 nearest comparable vehicles, and AI recommendations.
    - If confidence < 60%, a `confidence_warning` string is included.
    """
    service = PredictionService(db)

    try:
        result = await service.create_prediction(
            user_id=current_user.id,
            data=data,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "message": str(exc),
                "error_code": "MODEL_UNAVAILABLE",
            },
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Invalid reference IDs provided. Please ensure the selected brand, model, variant, and city are valid.",
                "error_code": "INVALID_REFERENCE",
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Prediction failed due to an internal error. Please try again. Details: {str(exc)}",
                "error_code": "PREDICTION_FAILED",
            },
        )

    return APIResponse(
        success=True,
        message="Vehicle price prediction generated successfully.",
        data=result,
    )


# ──────────────────────────────────────────────
# GET /predictions — User History
# ──────────────────────────────────────────────
@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[PredictionListItem]],
    summary="Get Prediction History",
    description="Return a paginated list of the authenticated user's past predictions.",
)
async def get_prediction_history(
    current_user: ActiveUser,
    db: DBSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="Items per page")] = 20,
) -> APIResponse[PaginatedResponse[PredictionListItem]]:
    """
    Retrieve paginated prediction history for the authenticated user.
    """
    skip = (page - 1) * page_size
    service = PredictionService(db)
    items = await service.get_user_history(
        user_id=current_user.id, skip=skip, limit=page_size
    )

    # Count total for pagination metadata
    from app.repositories.prediction_repository import PredictionRepository
    count = await PredictionRepository(db).count_by_user(current_user.id)
    total_pages = max(1, -(-count // page_size))  # Ceiling division

    return APIResponse(
        success=True,
        message="Prediction history retrieved.",
        data=PaginatedResponse(
            items=items,
            total=count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


# ──────────────────────────────────────────────
# GET /predictions/marketplace/listings
# ──────────────────────────────────────────────
@router.get(
    "/marketplace/listings",
    response_model=APIResponse[list[MarketplaceListing]],
    summary="Get Marketplace Listings",
    description="Return all predictions that have been listed on the marketplace.",
)
async def get_marketplace_listings(
    db: DBSession,
) -> APIResponse[list[MarketplaceListing]]:
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.models.prediction import Prediction
    from app.models.vehicle import Vehicle
    from app.models.brand import Brand
    from app.models.car_model import CarModel
    from app.models.variant import Variant
    
    query = (
        select(Prediction)
        .where(Prediction.is_listed == True)
        .options(
            joinedload(Prediction.vehicle).joinedload(Vehicle.brand),
            joinedload(Prediction.vehicle).joinedload(Vehicle.car_model),
            joinedload(Prediction.vehicle).joinedload(Vehicle.variant),
            joinedload(Prediction.vehicle).joinedload(Vehicle.city),
            joinedload(Prediction.images)
        )
        .order_by(Prediction.created_at.desc())
        .limit(200)
    )
    result = await db.execute(query)
    predictions = result.unique().scalars().all()
    
    listings = []
    seen_models = set()
    
    # Categorized fallback images by body type (expanded with more realistic, full-body car shots)
    fallback_images_map = {
        "Hatchback": [
            "https://images.unsplash.com/photo-1619682817481-e994891cd1f5?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1511919884226-fd3cad34687c?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1532581140115-3e355d1ed1de?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1609521263047-f8f205293f24?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1580274455191-1c62238fa333?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1590362891991-f776e747a588?auto=format&fit=crop&w=640&q=80"
        ],
        "Sedan": [
            "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1580273916550-e323be2ae537?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1617531653332-bd46c24f2068?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1506015391300-415214844111?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1542282088-fe8426682b8f?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1553440569-bcc63803a83d?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1535958636474-b021ee887b13?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=640&q=80"
        ],
        "SUV": [
            "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1532980400857-e8d9d275d858?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1566008885218-90abf9200ddb?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1606016159991-dfe4f2746ad5?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fd?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1540066019607-e5f6f4870bd8?auto=format&fit=crop&w=640&q=80"
        ],
        "MUV": [
            "https://images.unsplash.com/photo-1517524008697-84bbe3c3fd98?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1623910309100-c9f5ddf53051?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1551042777-27b372f85419?auto=format&fit=crop&w=640&q=80",
            "https://images.unsplash.com/photo-1610647752706-3bb12232b3ab?auto=format&fit=crop&w=640&q=80"
        ]
    }
    
    import hashlib

    for p in predictions:
        v = p.vehicle
        model_name = v.car_model.name.lower()
        title = f"{v.manufacturing_year} {v.brand.name} {v.car_model.name}"
        if v.variant:
            title += f" {v.variant.name}"
            
        # Remove duplicates permanently by car model so each image/detail looks highly unique
        if model_name in seen_models:
            continue
        seen_models.add(model_name)
        
        # Determine logical body type from model name
        if any(x in model_name for x in ["creta", "nexon", "thar", "safari", "xuv", "harrier", "brezza", "venue", "punch", "seltos", "hector", "fortuner", "br-v", "ecosport", "bolero", "scorpio", "s cross", "duster", "magnite", "kiger", "sonet", "taigun", "kushaq"]):
            body_type = "SUV"
        elif any(x in model_name for x in ["swift", "baleno", "alto", "i20", "i10", "tiago", "kwid", "celerio", "wagon", "presso", "polo", "go", "figo", "beat", "brio", "ignis", "glanza"]):
            body_type = "Hatchback"
        elif any(x in model_name for x in ["innova", "ertiga", "triber", "carens", "marazzo", "lodgy", "mobilio", "enjoy"]):
            body_type = "MUV"
        else:
            body_type = "Sedan"
            
        # Determine unique image based on body type and MD5 hash to ensure uniform distribution
        cat_images = fallback_images_map.get(body_type, fallback_images_map["Sedan"])
        # Mix the prediction ID into the hash so images are completely distinct across different listings
        hash_seed = f"{title}_{p.id}"
        title_hash = int(hashlib.md5(hash_seed.encode()).hexdigest(), 16)
        fallback_idx = title_hash % len(cat_images)
        image_url = cat_images[fallback_idx]
        
        if p.images:
            primary_img = next((img for img in p.images if img.is_primary), p.images[0])
            image_url = primary_img.image_url
            
        listings.append(MarketplaceListing(
            id=str(p.id),
            title=title,
            year=v.manufacturing_year,
            brand=v.brand.name,
            bodyType=body_type,
            fuelType=v.fuel_type,
            transmission=v.transmission,
            km=v.kilometers_driven,
            priceLakh=round(float(p.estimated_price) / 100000.0, 2),
            location=v.city.name if hasattr(v, 'city') and v.city else "Delhi",
            certified=True,
            owner=v.owner_type,
            image=image_url,
            color="blue"
        ))

    # Limit to 50 unique listings
    listings = listings[:50]

    return APIResponse(
        success=True,
        message="Marketplace listings retrieved.",
        data=listings,
    )


# ──────────────────────────────────────────────
# POST /predictions/{prediction_id}/list
# ──────────────────────────────────────────────
@router.post(
    "/{prediction_id}/list",
    response_model=APIResponse[dict],
    summary="List Prediction on Marketplace",
    description="Sets is_listed to True for a specific prediction.",
)
async def list_prediction(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
) -> APIResponse[dict]:
    from sqlalchemy import update
    from app.models.prediction import Prediction
    
    stmt = (
        update(Prediction)
        .where(Prediction.id == prediction_id, Prediction.user_id == current_user.id)
        .values(is_listed=True)
    )
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found or not authorized.",
        )
        
    await db.commit()
    
    return APIResponse(
        success=True,
        message="Vehicle posted to marketplace.",
        data={"id": str(prediction_id), "is_listed": True},
    )


# ──────────────────────────────────────────────
# GET /predictions/{prediction_id} — Detail
# ──────────────────────────────────────────────
@router.get(
    "/{prediction_id}",
    response_model=APIResponse[PredictionResponse],
    summary="Get Prediction Detail",
    description=(
        "Retrieve the full details of a specific prediction, including SHAP breakdown, "
        "similar vehicles, and recommendations."
    ),
)
async def get_prediction_detail(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
) -> APIResponse[PredictionResponse]:
    """
    Retrieve full prediction details for the authenticated user.

    Returns 404 if the prediction does not belong to the requesting user.
    """
    service = PredictionService(db)
    result = await service.get_prediction_detail(prediction_id, current_user.id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Prediction not found.",
                "error_code": "PREDICTION_NOT_FOUND",
            },
        )

    return APIResponse(
        success=True,
        message="Prediction details retrieved.",
        data=result,
    )


# ──────────────────────────────────────────────
# GET /predictions/{prediction_id}/report — Download PDF
# ──────────────────────────────────────────────
@router.get(
    "/{prediction_id}/report",
    summary="Download PDF Report",
    description="Generates and returns a PDF valuation report for the prediction.",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the PDF file.",
        },
    },
)
async def download_prediction_report(
    prediction_id: uuid.UUID,
    current_user: ActiveUser,
    db: DBSession,
):
    from fastapi import Response
    from app.services.report_service import ReportService
    
    service = ReportService(db)
    pdf_bytes = await service.generate_prediction_report(prediction_id, current_user.id)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="autoworth_report_{prediction_id}.pdf"'
        }
    )

