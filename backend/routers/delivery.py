from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import User, Delivery, Service
from schemas.service import DeliveryCreate, Delivery as DeliverySchema
from auth.jwt import get_current_active_user
import math
from datetime import datetime

router = APIRouter(prefix="/delivery", tags=["delivery"])

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia entre dos puntos usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en kilómetros

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    return distance

@router.post("/", response_model=DeliverySchema)
async def create_delivery(
    delivery_data: DeliveryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar si el servicio existe y está disponible
    service = db.query(Service).filter(
        Service.id == delivery_data.service_id,
        Service.is_available == True
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado o no disponible"
        )
    
    # Calcular la distancia y el precio
    distance = calculate_distance(
        delivery_data.pickup_location["lat"],
        delivery_data.pickup_location["lng"],
        delivery_data.delivery_location["lat"],
        delivery_data.delivery_location["lng"]
    )
    
    # Obtener el perfil de servicio para calcular el precio
    service_profile = service.service_profile
    if not service_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El servicio no tiene un perfil de servicio configurado"
        )
    
    # Calcular el precio total
    total_price = service_profile.base_price
    if service_profile.price_per_km:
        total_price += distance * service_profile.price_per_km
    
    # Verificar si el servicio está dentro del radio de cobertura
    if service_profile.service_radius and distance > service_profile.service_radius:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La ubicación está fuera del radio de cobertura del servicio"
        )
    
    # Crear el delivery
    db_delivery = Delivery(
        user_id=current_user.id,
        service_id=delivery_data.service_id,
        status="pending",
        pickup_location=delivery_data.pickup_location,
        delivery_location=delivery_data.delivery_location,
        total_price=total_price
    )
    
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

@router.get("/", response_model=List[DeliverySchema])
async def list_deliveries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Si es un usuario normal, ver sus deliveries
    if current_user.user_type == "personal":
        deliveries = db.query(Delivery).filter(
            Delivery.user_id == current_user.id
        ).all()
    # Si es un prestador de servicios, ver los deliveries asignados a sus servicios
    else:
        service_ids = db.query(Service.id).filter(
            Service.service_profile_id.in_(
                db.query(ServiceProfile.id).filter(
                    ServiceProfile.user_id == current_user.id
                )
            )
        ).all()
        deliveries = db.query(Delivery).filter(
            Delivery.service_id.in_([s[0] for s in service_ids])
        ).all()
    
    return deliveries

@router.get("/{delivery_id}", response_model=DeliverySchema)
async def get_delivery(
    delivery_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery no encontrado"
        )
    
    # Verificar permisos
    if current_user.user_type == "personal" and delivery.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este delivery"
        )
    
    return delivery

@router.put("/{delivery_id}/status")
async def update_delivery_status(
    delivery_id: int,
    status: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery no encontrado"
        )
    
    # Verificar si el usuario es el prestador del servicio
    service = db.query(Service).filter(Service.id == delivery.service_id).first()
    if not service or service.service_profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este delivery"
        )
    
    # Actualizar el estado
    delivery.status = status
    if status == "completed":
        delivery.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(delivery)
    return delivery 