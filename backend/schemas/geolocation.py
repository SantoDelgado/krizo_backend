from pydantic import BaseModel, Field
from typing import Optional, Tuple

class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitud en grados decimales")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud en grados decimales")
    address: Optional[str] = Field(None, description="Dirección formateada")
    city: Optional[str] = Field(None, description="Ciudad")
    state: Optional[str] = Field(None, description="Estado/Provincia")
    country: Optional[str] = Field(None, description="País")
    postal_code: Optional[str] = Field(None, description="Código postal")

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    user_id: Optional[int] = None
    business_id: Optional[int] = None
    is_default: bool = False

    class Config:
        orm_mode = True

class DistanceResponse(BaseModel):
    distance_km: float = Field(..., description="Distancia en kilómetros")
    duration_minutes: float = Field(..., description="Duración estimada en minutos")
    delivery_fee: float = Field(..., description="Costo de envío calculado")
    is_within_radius: bool = Field(..., description="Indica si está dentro del radio de entrega")

class GeocodingResponse(BaseModel):
    address: str = Field(..., description="Dirección formateada")
    coordinates: Tuple[float, float] = Field(..., description="Tupla de (latitud, longitud)")
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None 