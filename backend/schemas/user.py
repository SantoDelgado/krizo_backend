from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re

# Enums puros para Pydantic (no usar los de SQLAlchemy)
class UserTypeEnum(str, Enum):
    PERSONAL = "PERSONAL"
    BUSINESS = "BUSINESS"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"

class VerificationStatusEnum(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[constr(min_length=10, max_length=15)] = None
    cedula: Optional[constr(min_length=7, max_length=10)] = None
    user_type: UserTypeEnum

    @validator('cedula')
    def validate_cedula(cls, v):
        if v is not None:
            # Validar que solo contenga números
            if not re.match(r'^\d+$', v):
                raise ValueError('La cédula debe contener solo números')
            # Validar longitud (7-10 dígitos)
            if len(v) < 7 or len(v) > 10:
                raise ValueError('La cédula debe tener entre 7 y 10 dígitos')
        return v

class UserCreate(UserBase):
    password: constr(min_length=8)
    first_name: str
    last_name: str
    birth_date: datetime
    address: str
    cedula: constr(min_length=7, max_length=10)  # Cédula obligatoria en creación

class UserVerification(BaseModel):
    face_photo_url: str
    id_card_photo_url: str

class BusinessVerification(BaseModel):
    business_name: str
    rif_number: str
    rif_document_url: str
    business_address: str
    permits: list[str]

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[datetime] = None
    cedula: Optional[str] = None

    @validator('cedula')
    def validate_cedula(cls, v):
        if v is not None:
            # Validar que solo contenga números
            if not re.match(r'^\d+$', v):
                raise ValueError('La cédula debe contener solo números')
            # Validar longitud (7-10 dígitos)
            if len(v) < 7 or len(v) > 10:
                raise ValueError('La cédula debe tener entre 7 y 10 dígitos')
        return v

class UserRegisterResponse(BaseModel):
    id: int
    email: str
    phone: str
    cedula: str
    user_type: UserTypeEnum
    first_name: str
    last_name: str
    birth_date: datetime
    address: str
    created_at: datetime

class User(BaseModel):
    id: int
    email: str
    phone: str
    cedula: str
    user_type: UserTypeEnum
    first_name: str
    last_name: str
    birth_date: datetime
    address: str
    created_at: datetime

class UserInDB(User):
    hashed_password: str

class UserMe(BaseModel):
    id: int
    email: str
    phone: str
    cedula: str
    user_type: UserTypeEnum
    first_name: str
    last_name: str
    birth_date: datetime
    address: str
    created_at: datetime
    updated_at: datetime 