from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Float, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from database.database import Base

class UserType(str, enum.Enum):
    PERSONAL = "PERSONAL"
    BUSINESS = "BUSINESS"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    cedula = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    user_type = Column(Enum(UserType))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Información personal
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(DateTime)
    address = Column(String)
    face_photo_url = Column(String)
    id_card_photo_url = Column(String)
    
    # Verificación
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_documents = Column(String)  # JSON como string
    
    # Wallet
    wallet_balance = Column(String, default="0.0")  # Float como string para evitar problemas

class ServiceProfile(Base):
    __tablename__ = "service_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    
    # Servicios ofrecidos
    services = Column(JSON)  # Lista de servicios como JSON
    
    # Experiencia y descripción
    experience_years = Column(Integer)
    professional_description = Column(Text)
    
    # Horarios de trabajo
    available_hours = Column(JSON)  # {"start": "07:00", "end": "19:00"}
    
    # Ubicación
    location_lat = Column(Float)
    location_lng = Column(Float)
    location_address = Column(String)
    state = Column(String)
    municipality = Column(String)
    parish = Column(String)
    
    # Estado online
    is_online = Column(Boolean, default=False)
    last_online = Column(DateTime(timezone=True))
    
    # Datos del vehículo (para servicios que lo requieren)
    vehicle_type = Column(String)
    vehicle_model = Column(String)
    vehicle_year = Column(String)
    vehicle_color = Column(String)
    vehicle_plate = Column(String)
    vehicle_photo_url = Column(String)
    
    # Documentación
    id_document_url = Column(String)
    driver_license_url = Column(String)
    commercial_permit_url = Column(String)
    
    # Estadísticas
    total_services = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 