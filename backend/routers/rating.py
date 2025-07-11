from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from schemas.rating import (
    Rating, RatingCreate, RatingUpdate, RatingWithDetails,
    BusinessRatingSummary, RatingFilter, ReviewImage, RatingResponse,
    ReviewImageCreate, RatingResponseCreate
)
from services.rating import RatingService
from auth.jwt import get_current_user
from database.models import User, UserType

router = APIRouter(
    prefix="/ratings",
    tags=["ratings"]
)

@router.post("/", response_model=Rating)
async def create_rating(
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva calificación"""
    rating_service = RatingService(db)
    return rating_service.create_rating(current_user.id, rating_data)

@router.get("/", response_model=List[Rating])
async def get_ratings(
    business_id: Optional[int] = Query(None, description="Filtrar por negocio"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    has_review: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener calificaciones con filtros"""
    rating_service = RatingService(db)
    
    if business_id:
        filters = RatingFilter(
            business_id=business_id,
            min_rating=min_rating,
            max_rating=max_rating,
            has_review=has_review
        )
        return rating_service.get_business_ratings(
            business_id,
            skip=skip,
            limit=limit,
            filters=filters
        )
    else:
        return rating_service.get_user_ratings(
            current_user.id,
            skip=skip,
            limit=limit
        )

@router.get("/my-ratings", response_model=List[Rating])
async def get_my_ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener las calificaciones del usuario actual"""
    rating_service = RatingService(db)
    return rating_service.get_user_ratings(
        current_user.id,
        skip=skip,
        limit=limit
    )

@router.get("/{rating_id}", response_model=RatingWithDetails)
async def get_rating(
    rating_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener una calificación específica con detalles"""
    rating_service = RatingService(db)
    rating_details = rating_service.get_rating_with_details(rating_id)
    
    if not rating_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calificación no encontrada"
        )
    
    return rating_details

@router.put("/{rating_id}", response_model=Rating)
async def update_rating(
    rating_id: int,
    rating_update: RatingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar una calificación"""
    rating_service = RatingService(db)
    return rating_service.update_rating(
        rating_id,
        current_user.id,
        rating_update
    )

@router.delete("/{rating_id}")
async def delete_rating(
    rating_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una calificación"""
    rating_service = RatingService(db)
    rating_service.delete_rating(rating_id, current_user.id)
    return {"message": "Calificación eliminada exitosamente"}

@router.get("/business/{business_id}/summary", response_model=BusinessRatingSummary)
async def get_business_rating_summary(
    business_id: int,
    db: Session = Depends(get_db)
):
    """Obtener resumen de calificaciones de un negocio"""
    rating_service = RatingService(db)
    summary = rating_service.get_business_rating_summary(business_id)
    
    # Obtener calificaciones recientes
    recent_ratings = rating_service.get_business_ratings(
        business_id,
        skip=0,
        limit=5
    )
    
    return BusinessRatingSummary(
        **summary,
        recent_ratings=recent_ratings
    )

@router.post("/{rating_id}/images", response_model=ReviewImage)
async def add_review_image(
    rating_id: int,
    image_data: ReviewImageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agregar imagen a una reseña"""
    rating_service = RatingService(db)
    return rating_service.add_review_image(
        rating_id,
        current_user.id,
        image_data.image_url
    )

@router.post("/{rating_id}/response", response_model=RatingResponse)
async def create_rating_response(
    rating_id: int,
    response_data: RatingResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear respuesta del negocio a una calificación"""
    # Verificar que el usuario es un negocio
    if current_user.user_type != UserType.BUSINESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden responder a calificaciones"
        )
    
    rating_service = RatingService(db)
    return rating_service.create_rating_response(
        rating_id,
        current_user.business_profile.id,
        response_data.response
    )

@router.get("/business/{business_id}/reviews", response_model=List[RatingWithDetails])
async def get_business_reviews(
    business_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """Obtener todas las reseñas de un negocio"""
    rating_service = RatingService(db)
    filters = RatingFilter(
        business_id=business_id,
        min_rating=min_rating,
        max_rating=max_rating
    )
    
    ratings = rating_service.get_business_ratings(
        business_id,
        skip=skip,
        limit=limit,
        filters=filters
    )
    
    # Obtener detalles completos para cada calificación
    detailed_ratings = []
    for rating in ratings:
        details = rating_service.get_rating_with_details(rating.id)
        if details:
            detailed_ratings.append(details)
    
    return detailed_ratings 