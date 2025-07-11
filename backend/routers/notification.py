from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from schemas.notification import (
    Notification, NotificationCreate, NotificationPreference,
    DeviceTokenCreate, NotificationResponse
)
from services.notification import NotificationService
from auth.jwt import get_current_user
from database.models import User

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener las notificaciones del usuario"""
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return notifications

@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el número de notificaciones no leídas"""
    notification_service = NotificationService(db)
    count = notification_service.get_unread_count(current_user.id)
    return {"count": count}

@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar una notificación como leída"""
    notification_service = NotificationService(db)
    notification = notification_service.mark_notification_as_read(
        notification_id,
        current_user.id
    )
    return notification

@router.post("/read/all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar todas las notificaciones como leídas"""
    notification_service = NotificationService(db)
    notification_service.mark_all_as_read(current_user.id)
    return {"message": "Todas las notificaciones han sido marcadas como leídas"}

@router.get("/preferences", response_model=NotificationPreference)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener las preferencias de notificación del usuario"""
    notification_service = NotificationService(db)
    preferences = notification_service.get_notification_preferences(current_user.id)
    return preferences

@router.put("/preferences", response_model=NotificationPreference)
async def update_notification_preferences(
    preferences: NotificationPreference,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar las preferencias de notificación del usuario"""
    notification_service = NotificationService(db)
    updated_preferences = notification_service.update_notification_preferences(
        current_user.id,
        preferences.dict()
    )
    return updated_preferences

@router.post("/device-token", response_model=DeviceTokenCreate)
async def register_device_token(
    device_token: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar un token de dispositivo para notificaciones push"""
    notification_service = NotificationService(db)
    token = notification_service.register_device_token(
        current_user.id,
        device_token.token,
        device_token.device_type
    )
    return token

@router.delete("/device-token/{token}")
async def unregister_device_token(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un token de dispositivo"""
    notification_service = NotificationService(db)
    notification_service.unregister_device_token(token)
    return {"message": "Token de dispositivo eliminado exitosamente"} 