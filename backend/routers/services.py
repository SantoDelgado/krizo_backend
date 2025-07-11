from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import random
import math

from database.database import get_db
from models_simple import User as UserModel, ServiceProfile
from auth.jwt import get_current_active_user

router = APIRouter(prefix="/services", tags=["services"])

class KrizoWorkerResponse(BaseModel):
    id: int
    name: str
    rating: float
    review_count: int
    services: List[str]
    experience: int
    distance: float
    is_online: bool
    response_time: int
    hourly_rate: float
    location: dict
    description: str
    specializations: List[str]
    available_hours: dict

class ServiceProfileRequest(BaseModel):
    services: List[str]
    experience: str
    professional_description: str
    available_hours: dict
    state: str
    municipality: str
    parish: str
    location: dict
    vehicle_data: Optional[dict] = None

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcular distancia entre dos puntos usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en kilómetros
    
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@router.get("/marketplace", response_model=List[KrizoWorkerResponse])
async def get_krizoworkers(
    lat: Optional[float] = Query(None, description="Latitud del usuario"),
    lng: Optional[float] = Query(None, description="Longitud del usuario"),
    max_distance: Optional[float] = Query(50, description="Distancia máxima en km"),
    services: Optional[str] = Query(None, description="Servicios separados por coma"),
    min_rating: Optional[float] = Query(0, description="Rating mínimo"),
    online_only: Optional[bool] = Query(False, description="Solo trabajadores en línea"),
    sort_by: Optional[str] = Query("distance", description="Ordenar por: distance, rating, price, experience"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de KrizoWorkers disponibles ordenados por proximidad
    """
    try:
        # Obtener todos los KrizoWorkers con sus perfiles de servicio
        workers_query = db.query(UserModel, ServiceProfile).join(
            ServiceProfile, UserModel.id == ServiceProfile.user_id
        ).filter(
            UserModel.user_type == "SERVICE_PROVIDER",
            UserModel.is_active == True
        )

        # Filtrar por estado online si se solicita
        if online_only:
            workers_query = workers_query.filter(ServiceProfile.is_online == True)

        workers_data = workers_query.all()

        # Convertir a formato de respuesta
        workers_response = []
        for user, profile in workers_data:
            # Calcular distancia si se proporcionan coordenadas
            distance = 0.0
            if lat and lng and profile.location_lat and profile.location_lng:
                distance = calculate_distance(
                    lat, lng, 
                    profile.location_lat, profile.location_lng
                )
            else:
                # Distancia simulada si no hay coordenadas
                distance = random.uniform(1.0, 20.0)

            # Filtrar por distancia
            if max_distance and distance > max_distance:
                continue

            # Filtrar por rating
            if min_rating and profile.average_rating < min_rating:
                continue

            # Filtrar por servicios
            if services:
                requested_services = [s.strip() for s in services.split(',')]
                if not any(service in profile.services for service in requested_services):
                    continue

            # Crear respuesta
            worker_response = KrizoWorkerResponse(
                id=user.id,
                name=f"{user.first_name} {user.last_name}",
                rating=profile.average_rating or 4.0,
                review_count=profile.total_reviews or 0,
                services=profile.services or [],
                experience=profile.experience_years or 1,
                distance=distance,
                is_online=profile.is_online,
                response_time=random.randint(5, 30),  # Simulado por ahora
                hourly_rate=random.uniform(25, 100),  # Simulado por ahora
                location={
                    "lat": profile.location_lat or 10.4806,
                    "lng": profile.location_lng or -66.9036,
                    "address": profile.location_address or "Caracas, Venezuela"
                },
                description=profile.professional_description or f"Profesional con {profile.experience_years or 1} años de experiencia.",
                specializations=profile.services or [],
                available_hours=profile.available_hours or {"start": "07:00", "end": "19:00"}
            )
            workers_response.append(worker_response)

        # Ordenar resultados
        if sort_by == "distance":
            workers_response.sort(key=lambda x: x.distance)
        elif sort_by == "rating":
            workers_response.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "price":
            workers_response.sort(key=lambda x: x.hourly_rate)
        elif sort_by == "experience":
            workers_response.sort(key=lambda x: x.experience, reverse=True)

        return workers_response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener KrizoWorkers: {str(e)}"
        )

@router.get("/marketplace/{worker_id}")
async def get_krizoworker_details(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Obtener detalles específicos de un KrizoWorker
    """
    try:
        worker = db.query(UserModel).filter(
            UserModel.id == worker_id,
            UserModel.user_type == "SERVICE_PROVIDER",
            UserModel.is_active == True
        ).first()

        if not worker:
            raise HTTPException(
                status_code=404,
                detail="KrizoWorker no encontrado"
            )

        # Aquí agregarías más detalles del perfil del trabajador
        return {
            "id": worker.id,
            "name": f"{worker.first_name} {worker.last_name}",
            "email": worker.email,
            "phone": worker.phone,
            "address": worker.address,
            "user_type": worker.user_type,
            "created_at": worker.created_at
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalles del KrizoWorker: {str(e)}"
        )

@router.post("/profile")
async def save_service_profile(
    profile_data: ServiceProfileRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Guardar perfil de servicios del KrizoWorker
    """
    try:
        # Actualizar el usuario con los datos del perfil
        current_user.user_type = "SERVICE_PROVIDER"
        current_user.address = f"{profile_data.state}, {profile_data.municipality}, {profile_data.parish}"
        
        # Verificar si ya existe un perfil de servicio
        existing_profile = db.query(ServiceProfile).filter(
            ServiceProfile.user_id == current_user.id
        ).first()
        
        if existing_profile:
            # Actualizar perfil existente
            existing_profile.services = profile_data.services
            existing_profile.experience_years = int(profile_data.experience)
            existing_profile.professional_description = profile_data.professional_description
            existing_profile.available_hours = profile_data.available_hours
            existing_profile.location_lat = profile_data.location.get('lat')
            existing_profile.location_lng = profile_data.location.get('lng')
            existing_profile.location_address = profile_data.location.get('address', '')
            existing_profile.state = profile_data.state
            existing_profile.municipality = profile_data.municipality
            existing_profile.parish = profile_data.parish
            
            # Datos del vehículo si se proporcionan
            if profile_data.vehicle_data:
                existing_profile.vehicle_type = profile_data.vehicle_data.get('vehicleType')
                existing_profile.vehicle_model = profile_data.vehicle_data.get('vehicleModel')
                existing_profile.vehicle_year = profile_data.vehicle_data.get('vehicleYear')
                existing_profile.vehicle_color = profile_data.vehicle_data.get('vehicleColor')
                existing_profile.vehicle_plate = profile_data.vehicle_data.get('vehiclePlate')
            
            profile = existing_profile
        else:
            # Crear nuevo perfil
            profile = ServiceProfile(
                user_id=current_user.id,
                services=profile_data.services,
                experience_years=int(profile_data.experience),
                professional_description=profile_data.professional_description,
                available_hours=profile_data.available_hours,
                location_lat=profile_data.location.get('lat'),
                location_lng=profile_data.location.get('lng'),
                location_address=profile_data.location.get('address', ''),
                state=profile_data.state,
                municipality=profile_data.municipality,
                parish=profile_data.parish,
                is_online=True,  # Por defecto online al crear perfil
                last_online=datetime.utcnow()
            )
            
            # Datos del vehículo si se proporcionan
            if profile_data.vehicle_data:
                profile.vehicle_type = profile_data.vehicle_data.get('vehicleType')
                profile.vehicle_model = profile_data.vehicle_data.get('vehicleModel')
                profile.vehicle_year = profile_data.vehicle_data.get('vehicleYear')
                profile.vehicle_color = profile_data.vehicle_data.get('vehicleColor')
                profile.vehicle_plate = profile_data.vehicle_data.get('vehiclePlate')
            
            db.add(profile)
        
        db.commit()
        
        return {
            "message": "Perfil de servicios guardado exitosamente",
            "user_id": current_user.id,
            "services": profile_data.services,
            "status": "active"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar perfil de servicios: {str(e)}"
        )

@router.get("/profile/status")
async def get_profile_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Obtener estado del perfil de servicios
    """
    try:
        # Verificar si existe un perfil de servicios
        profile = db.query(ServiceProfile).filter(
            ServiceProfile.user_id == current_user.id
        ).first()
        
        is_service_provider = current_user.user_type == "SERVICE_PROVIDER" and profile is not None
        
        return {
            "is_service_provider": is_service_provider,
            "user_id": current_user.id,
            "status": "active" if is_service_provider else "inactive",
            "has_profile": profile is not None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estado del perfil: {str(e)}"
        )

@router.post("/profile/online-status")
async def toggle_online_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Cambiar estado online/offline del KrizoWorker
    """
    try:
        # Verificar que el usuario sea SERVICE_PROVIDER
        if current_user.user_type != "SERVICE_PROVIDER":
            raise HTTPException(
                status_code=400,
                detail="Solo los KrizoWorkers pueden cambiar su estado online"
            )
        
        # Obtener el perfil de servicio
        profile = db.query(ServiceProfile).filter(
            ServiceProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Perfil de servicios no encontrado"
            )
        
        # Cambiar el estado
        profile.is_online = not profile.is_online
        profile.last_online = datetime.utcnow()
        
        db.commit()
        
        return {
            "user_id": current_user.id,
            "is_online": profile.is_online,
            "message": f"Estado cambiado a {'En Línea' if profile.is_online else 'Fuera de Línea'}"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al cambiar estado online: {str(e)}"
        )

@router.get("/profile/online-status")
async def get_online_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Obtener estado online/offline del KrizoWorker
    """
    try:
        # Verificar que el usuario sea SERVICE_PROVIDER
        if current_user.user_type != "SERVICE_PROVIDER":
            raise HTTPException(
                status_code=400,
                detail="Solo los KrizoWorkers pueden consultar su estado online"
            )
        
        # Obtener el perfil de servicio
        profile = db.query(ServiceProfile).filter(
            ServiceProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Perfil de servicios no encontrado"
            )
        
        return {
            "user_id": current_user.id,
            "is_online": profile.is_online
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estado online: {str(e)}"
        ) 