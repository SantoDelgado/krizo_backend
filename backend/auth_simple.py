from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from pydantic import BaseModel
from typing import Optional

from database.database import get_db
from models_simple import User as UserModel
from auth.jwt import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Schemas simplificados
class RegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    cedula: str
    password: str
    address: str
    userType: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    phone: str
    cedula: str
    user_type: str
    first_name: str
    last_name: str
    address: str
    created_at: datetime

@router.post("/register")
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    db_user = db.query(UserModel).filter(
        (UserModel.email == user_data.email) | 
        (UserModel.phone == user_data.phone) | 
        (UserModel.cedula == user_data.cedula)
    ).first()
    
    if db_user:
        if db_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        elif db_user.phone == user_data.phone:
            raise HTTPException(status_code=400, detail="El teléfono ya está registrado")
        elif db_user.cedula == user_data.cedula:
            raise HTTPException(status_code=400, detail="La cédula ya está registrada")
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        email=user_data.email,
        phone=user_data.phone,
        cedula=user_data.cedula,
        hashed_password=hashed_password,
        user_type=user_data.userType,
        first_name=user_data.firstName,
        last_name=user_data.lastName,
        birth_date=datetime.now(),
        address=user_data.address
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "id": db_user.id,
        "email": db_user.email,
        "phone": db_user.phone,
        "cedula": db_user.cedula,
        "user_type": db_user.user_type,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "address": db_user.address,
        "created_at": db_user.created_at
    }

@router.post("/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    # Buscar usuario por email
    user = db.query(UserModel).filter(UserModel.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "cedula": user.cedula,
            "user_type": user.user_type,
            "address": user.address,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    }

@router.get("/me")
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "phone": current_user.phone,
        "cedula": current_user.cedula,
        "user_type": current_user.user_type,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "address": current_user.address,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at or current_user.created_at
    }

@router.post("/logout")
async def logout():
    return {
        "message": "Logout exitoso",
        "status": "success"
    } 