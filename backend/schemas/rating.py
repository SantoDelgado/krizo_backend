from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RatingBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5 estrellas")
    review: Optional[str] = Field(None, description="Reseña escrita")
    is_anonymous: bool = Field(False, description="Indica si la reseña es anónima")

class RatingCreate(RatingBase):
    business_id: int = Field(..., description="ID del negocio")
    service_id: Optional[int] = Field(None, description="ID del servicio (opcional)")
    delivery_id: Optional[int] = Field(None, description="ID de la entrega (opcional)")

class RatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None
    is_anonymous: Optional[bool] = None

class Rating(RatingBase):
    id: int
    user_id: int
    business_id: int
    service_id: Optional[int] = None
    delivery_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReviewImageBase(BaseModel):
    image_url: str = Field(..., description="URL de la imagen")

class ReviewImageCreate(ReviewImageBase):
    pass

class ReviewImage(ReviewImageBase):
    id: int
    rating_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class RatingResponseBase(BaseModel):
    response: str = Field(..., description="Respuesta del negocio a la reseña")

class RatingResponseCreate(RatingResponseBase):
    pass

class RatingResponse(RatingResponseBase):
    id: int
    rating_id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RatingWithDetails(Rating):
    images: List[ReviewImage] = []
    responses: List[RatingResponse] = []
    user_name: Optional[str] = None
    business_name: Optional[str] = None

    class Config:
        orm_mode = True

class BusinessRatingSummary(BaseModel):
    business_id: int
    average_rating: float
    total_ratings: int
    rating_distribution: dict  # {1: count, 2: count, 3: count, 4: count, 5: count}
    recent_ratings: List[RatingWithDetails]

class RatingFilter(BaseModel):
    business_id: Optional[int] = None
    service_id: Optional[int] = None
    min_rating: Optional[int] = Field(None, ge=1, le=5)
    max_rating: Optional[int] = Field(None, ge=1, le=5)
    has_review: Optional[bool] = None
    is_anonymous: Optional[bool] = None 