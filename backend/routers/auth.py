from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from database.database import get_db
from database.models import User as UserModel
from schemas.user import UserCreate, User, UserRegisterResponse, UserTypeEnum, VerificationStatusEnum, UserMe
from pydantic import BaseModel
from auth.jwt import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    cedula: str
    password: str
    address: str
    userType: str

@router.post("/register", response_model=UserRegisterResponse)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe por email, teléfono o cédula
    db_user = db.query(UserModel).filter(
        (UserModel.email == user_data.email) | 
        (UserModel.phone == user_data.phone) | 
        (UserModel.cedula == user_data.cedula)
    ).first()
    
    if db_user:
        # Determinar qué campo está duplicado
        if db_user.email == user_data.email:
            raise HTTPException(
                status_code=400,
                detail="El email ya está registrado"
            )
        elif db_user.phone == user_data.phone:
            raise HTTPException(
                status_code=400,
                detail="El teléfono ya está registrado"
            )
        elif db_user.cedula == user_data.cedula:
            raise HTTPException(
                status_code=400,
                detail="La cédula ya está registrada"
            )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        email=user_data.email,
        phone=user_data.phone,
        cedula=user_data.cedula,
        hashed_password=hashed_password,
        user_type=user_data.userType,  # Usar el valor directo
        first_name=user_data.firstName,
        last_name=user_data.lastName,
        birth_date=datetime.now(),  # Usar fecha actual como placeholder
        address=user_data.address
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Construir respuesta manualmente para evitar recursión
    return UserRegisterResponse(
        id=db_user.id,
        email=db_user.email,
        phone=db_user.phone,
        cedula=db_user.cedula,
        user_type=UserTypeEnum(db_user.user_type),
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        birth_date=db_user.birth_date,
        address=db_user.address,
        created_at=db_user.created_at
    )

@router.post("/login")
async def login(
    credentials: dict,
    db: Session = Depends(get_db)
):
    # Buscar usuario por email
    user = db.query(UserModel).filter(UserModel.email == credentials.get("email")).first()
    
    if not user or not verify_password(credentials.get("password"), user.hashed_password):
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

@router.post("/token")
async def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Buscar usuario por email, teléfono o cédula
    user = db.query(UserModel).filter(
        (UserModel.email == form_data.username) | 
        (UserModel.phone == form_data.username) | 
        (UserModel.cedula == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
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
            "email": user.email,
            "phone": user.phone,
            "cedula": user.cedula,
            "user_type": user.user_type,
        }
    }

@router.get("/me", response_model=UserMe)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    # Construir respuesta manualmente para manejar campos None
    return UserMe(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        cedula=current_user.cedula,
        user_type=UserTypeEnum(current_user.user_type),
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        birth_date=current_user.birth_date,
        address=current_user.address,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at or current_user.created_at  # Usar created_at si updated_at es None
    )

@router.post("/logout")
async def logout():
    """
    Endpoint de logout - En una implementación real, aquí invalidarías el token
    """
    return {
        "message": "Logout exitoso",
        "status": "success"
    } 