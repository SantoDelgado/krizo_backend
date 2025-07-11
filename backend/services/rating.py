from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database.models import (
    Rating, ReviewImage, RatingResponse, User, BusinessProfile, Service, Delivery
)
from schemas.rating import RatingCreate, RatingUpdate, RatingFilter
from typing import List, Optional
from datetime import datetime

class RatingService:
    def __init__(self, db: Session):
        self.db = db

    def create_rating(
        self,
        user_id: int,
        rating_data: RatingCreate
    ) -> Rating:
        """Crear una nueva calificación"""
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que el negocio existe
        business = self.db.query(BusinessProfile).filter(
            BusinessProfile.id == rating_data.business_id
        ).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Negocio no encontrado"
            )

        # Verificar que no existe una calificación previa para la misma entrega
        if rating_data.delivery_id:
            existing_rating = self.db.query(Rating).filter(
                Rating.delivery_id == rating_data.delivery_id,
                Rating.user_id == user_id
            ).first()
            if existing_rating:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una calificación para esta entrega"
                )

        # Crear la calificación
        rating = Rating(
            user_id=user_id,
            **rating_data.dict()
        )
        self.db.add(rating)
        self.db.commit()
        self.db.refresh(rating)
        return rating

    def get_rating(self, rating_id: int) -> Optional[Rating]:
        """Obtener una calificación específica"""
        return self.db.query(Rating).filter(Rating.id == rating_id).first()

    def get_user_ratings(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Rating]:
        """Obtener las calificaciones de un usuario"""
        return self.db.query(Rating).filter(
            Rating.user_id == user_id
        ).order_by(Rating.created_at.desc()).offset(skip).limit(limit).all()

    def get_business_ratings(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[RatingFilter] = None
    ) -> List[Rating]:
        """Obtener las calificaciones de un negocio"""
        query = self.db.query(Rating).filter(Rating.business_id == business_id)

        if filters:
            if filters.min_rating:
                query = query.filter(Rating.rating >= filters.min_rating)
            if filters.max_rating:
                query = query.filter(Rating.rating <= filters.max_rating)
            if filters.has_review is not None:
                if filters.has_review:
                    query = query.filter(Rating.review.isnot(None))
                else:
                    query = query.filter(Rating.review.is_(None))
            if filters.is_anonymous is not None:
                query = query.filter(Rating.is_anonymous == filters.is_anonymous)

        return query.order_by(Rating.created_at.desc()).offset(skip).limit(limit).all()

    def update_rating(
        self,
        rating_id: int,
        user_id: int,
        rating_update: RatingUpdate
    ) -> Rating:
        """Actualizar una calificación"""
        rating = self.db.query(Rating).filter(
            Rating.id == rating_id,
            Rating.user_id == user_id
        ).first()

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calificación no encontrada"
            )

        # Solo permitir actualización dentro de las primeras 24 horas
        time_diff = datetime.utcnow() - rating.created_at
        if time_diff.total_seconds() > 86400:  # 24 horas
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden editar calificaciones dentro de las primeras 24 horas"
            )

        for key, value in rating_update.dict(exclude_unset=True).items():
            setattr(rating, key, value)

        rating.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rating)
        return rating

    def delete_rating(self, rating_id: int, user_id: int) -> bool:
        """Eliminar una calificación"""
        rating = self.db.query(Rating).filter(
            Rating.id == rating_id,
            Rating.user_id == user_id
        ).first()

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calificación no encontrada"
            )

        self.db.delete(rating)
        self.db.commit()
        return True

    def get_business_rating_summary(self, business_id: int) -> dict:
        """Obtener resumen de calificaciones de un negocio"""
        # Calcular promedio y total
        result = self.db.query(
            func.avg(Rating.rating).label('average_rating'),
            func.count(Rating.id).label('total_ratings')
        ).filter(Rating.business_id == business_id).first()

        # Calcular distribución de calificaciones
        distribution = {}
        for i in range(1, 6):
            count = self.db.query(Rating).filter(
                Rating.business_id == business_id,
                Rating.rating == i
            ).count()
            distribution[i] = count

        return {
            "business_id": business_id,
            "average_rating": float(result.average_rating) if result.average_rating else 0.0,
            "total_ratings": result.total_ratings,
            "rating_distribution": distribution
        }

    def add_review_image(
        self,
        rating_id: int,
        user_id: int,
        image_url: str
    ) -> ReviewImage:
        """Agregar imagen a una reseña"""
        rating = self.db.query(Rating).filter(
            Rating.id == rating_id,
            Rating.user_id == user_id
        ).first()

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calificación no encontrada"
            )

        review_image = ReviewImage(
            rating_id=rating_id,
            image_url=image_url
        )
        self.db.add(review_image)
        self.db.commit()
        self.db.refresh(review_image)
        return review_image

    def create_rating_response(
        self,
        rating_id: int,
        business_id: int,
        response: str
    ) -> RatingResponse:
        """Crear respuesta del negocio a una calificación"""
        rating = self.db.query(Rating).filter(
            Rating.id == rating_id,
            Rating.business_id == business_id
        ).first()

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calificación no encontrada"
            )

        # Verificar que no existe una respuesta previa
        existing_response = self.db.query(RatingResponse).filter(
            RatingResponse.rating_id == rating_id
        ).first()

        if existing_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una respuesta para esta calificación"
            )

        rating_response = RatingResponse(
            rating_id=rating_id,
            business_id=business_id,
            response=response
        )
        self.db.add(rating_response)
        self.db.commit()
        self.db.refresh(rating_response)
        return rating_response

    def get_rating_with_details(self, rating_id: int) -> Optional[dict]:
        """Obtener calificación con detalles completos"""
        rating = self.db.query(Rating).filter(Rating.id == rating_id).first()
        if not rating:
            return None

        # Obtener imágenes
        images = self.db.query(ReviewImage).filter(
            ReviewImage.rating_id == rating_id
        ).all()

        # Obtener respuestas
        responses = self.db.query(RatingResponse).filter(
            RatingResponse.rating_id == rating_id
        ).all()

        # Obtener nombres
        user_name = None
        if not rating.is_anonymous:
            user = self.db.query(User).filter(User.id == rating.user_id).first()
            user_name = f"{user.first_name} {user.last_name}" if user else None

        business = self.db.query(BusinessProfile).filter(
            BusinessProfile.id == rating.business_id
        ).first()
        business_name = business.business_name if business else None

        return {
            **rating.__dict__,
            "images": [img.__dict__ for img in images],
            "responses": [resp.__dict__ for resp in responses],
            "user_name": user_name,
            "business_name": business_name
        } 