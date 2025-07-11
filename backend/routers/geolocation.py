from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from schemas.geolocation import (
    Location, LocationCreate, DistanceResponse, GeocodingResponse
)
from services.geolocation import GeolocationService
from auth.jwt import get_current_user
from database.models import User, Location as LocationModel

router = APIRouter(
    prefix="/geolocation",
    tags=["geolocation"]
)

@router.post("/locations", response_model=Location)
async def create_location(
    location: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva ubicación para el usuario"""
    db_location = LocationModel(
        user_id=current_user.id,
        **location.dict()
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.get("/locations", response_model=List[Location])
async def get_user_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las ubicaciones del usuario"""
    return db.query(LocationModel).filter(
        LocationModel.user_id == current_user.id
    ).all()

@router.get("/locations/{location_id}", response_model=Location)
async def get_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener una ubicación específica"""
    location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no encontrada"
        )
    
    return location

@router.put("/locations/{location_id}", response_model=Location)
async def update_location(
    location_id: int,
    location_update: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar una ubicación"""
    db_location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.user_id == current_user.id
    ).first()
    
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no encontrada"
        )
    
    for key, value in location_update.dict().items():
        setattr(db_location, key, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una ubicación"""
    db_location = db.query(LocationModel).filter(
        LocationModel.id == location_id,
        LocationModel.user_id == current_user.id
    ).first()
    
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ubicación no encontrada"
        )
    
    db.delete(db_location)
    db.commit()
    return {"message": "Ubicación eliminada exitosamente"}

@router.post("/calculate-distance", response_model=DistanceResponse)
async def calculate_distance(
    origin: LocationCreate,
    destination: LocationCreate,
    db: Session = Depends(get_db)
):
    """Calcular distancia y costo de envío entre dos ubicaciones"""
    geolocation_service = GeolocationService()
    
    # Crear objetos Location para el cálculo
    origin_location = LocationModel(**origin.dict())
    destination_location = LocationModel(**destination.dict())
    
    # Calcular distancia y tiempo
    distance_km, duration_minutes = await geolocation_service.calculate_distance(
        origin_location,
        destination_location
    )
    
    # Calcular costo de envío
    delivery_fee = geolocation_service.calculate_delivery_fee(distance_km)
    
    # Verificar si está dentro del radio de entrega
    is_within_radius = geolocation_service.is_within_delivery_radius(
        origin_location,
        destination_location
    )
    
    return DistanceResponse(
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        delivery_fee=delivery_fee,
        is_within_radius=is_within_radius
    )

@router.get("/geocode", response_model=GeocodingResponse)
async def geocode_address(
    address: str,
    db: Session = Depends(get_db)
):
    """Obtener coordenadas a partir de una dirección"""
    geolocation_service = GeolocationService()
    coordinates = await geolocation_service.get_coordinates_from_address(address)
    
    if not coordinates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo geocodificar la dirección"
        )
    
    # Obtener dirección formateada
    formatted_address = await geolocation_service.get_address_from_coordinates(
        coordinates[0],
        coordinates[1]
    )
    
    return GeocodingResponse(
        address=formatted_address or address,
        coordinates=coordinates
    )

@router.get("/reverse-geocode", response_model=GeocodingResponse)
async def reverse_geocode(
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    """Obtener dirección a partir de coordenadas"""
    geolocation_service = GeolocationService()
    address = await geolocation_service.get_address_from_coordinates(
        latitude,
        longitude
    )
    
    if not address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener la dirección para las coordenadas dadas"
        )
    
    return GeocodingResponse(
        address=address,
        coordinates=(latitude, longitude)
    ) 