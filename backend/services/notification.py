from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from database.models import (
    User, Notification, NotificationPreference, DeviceToken,
    NotificationType, NotificationPriority
)
from schemas.notification import NotificationCreate
from datetime import datetime
import os
from typing import List, Optional
import aiohttp
import json

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.firebase_server_key = os.getenv("FIREBASE_SERVER_KEY")
        self.sms_api_key = os.getenv("SMS_API_KEY")
        self.email_api_key = os.getenv("EMAIL_API_KEY")

    async def create_notification(
        self,
        user_id: int,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[dict] = None
    ) -> Notification:
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Obtener preferencias de notificación
        preferences = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()

        # Verificar si el usuario quiere recibir este tipo de notificación
        if not self._should_send_notification(preferences, type):
            return None

        # Crear la notificación
        notification = Notification(
            user_id=user_id,
            type=type,
            priority=priority,
            title=title,
            message=message,
            data=data
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Enviar notificaciones según las preferencias
        await self._send_notifications(notification, user, preferences)

        return notification

    def _should_send_notification(
        self,
        preferences: NotificationPreference,
        type: NotificationType
    ) -> bool:
        if type == NotificationType.ORDER_STATUS:
            return preferences.order_updates
        elif type == NotificationType.PAYMENT:
            return preferences.payment_updates
        elif type == NotificationType.PROMOTION:
            return preferences.promotion_updates
        elif type == NotificationType.LOYALTY:
            return preferences.loyalty_updates
        elif type == NotificationType.SYSTEM:
            return preferences.system_updates
        return True

    async def _send_notifications(
        self,
        notification: Notification,
        user: User,
        preferences: NotificationPreference
    ):
        tasks = []
        
        # Enviar notificación push si está habilitado
        if preferences.push_enabled:
            tasks.append(self._send_push_notification(notification, user))
        
        # Enviar email si está habilitado
        if preferences.email_enabled:
            tasks.append(self._send_email_notification(notification, user))
        
        # Enviar SMS si está habilitado
        if preferences.sms_enabled:
            tasks.append(self._send_sms_notification(notification, user))
        
        # Ejecutar todas las tareas de envío
        await asyncio.gather(*tasks)

    async def _send_push_notification(self, notification: Notification, user: User):
        # Obtener tokens de dispositivos activos
        device_tokens = self.db.query(DeviceToken).filter(
            DeviceToken.user_id == user.id,
            DeviceToken.is_active == True
        ).all()

        if not device_tokens:
            return

        # Preparar el mensaje para Firebase Cloud Messaging
        message = {
            "notification": {
                "title": notification.title,
                "body": notification.message
            },
            "data": notification.data or {},
            "registration_ids": [dt.token for dt in device_tokens]
        }

        # Enviar a Firebase
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"key={self.firebase_server_key}",
                "Content-Type": "application/json"
            }
            async with session.post(
                "https://fcm.googleapis.com/fcm/send",
                headers=headers,
                json=message
            ) as response:
                if response.status != 200:
                    print(f"Error sending push notification: {await response.text()}")

    async def _send_email_notification(self, notification: Notification, user: User):
        # Implementar envío de email usando el servicio de email configurado
        # Por ejemplo, usando SendGrid, Mailgun, etc.
        pass

    async def _send_sms_notification(self, notification: Notification, user: User):
        # Implementar envío de SMS usando el servicio de SMS configurado
        # Por ejemplo, usando Twilio, MessageBird, etc.
        pass

    def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def mark_notification_as_read(self, notification_id: int, user_id: int) -> Notification:
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada"
            )

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, user_id: int):
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        self.db.commit()

    def get_unread_count(self, user_id: int) -> int:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    def update_notification_preferences(
        self,
        user_id: int,
        preferences: dict
    ) -> NotificationPreference:
        db_preferences = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not db_preferences:
            db_preferences = NotificationPreference(user_id=user_id)
            self.db.add(db_preferences)

        for key, value in preferences.items():
            if hasattr(db_preferences, key):
                setattr(db_preferences, key, value)

        self.db.commit()
        self.db.refresh(db_preferences)
        return db_preferences

    def register_device_token(
        self,
        user_id: int,
        token: str,
        device_type: str
    ) -> DeviceToken:
        # Verificar si el token ya existe
        existing_token = self.db.query(DeviceToken).filter(
            DeviceToken.token == token
        ).first()

        if existing_token:
            if existing_token.user_id != user_id:
                # El token pertenece a otro usuario, desactivarlo
                existing_token.is_active = False
                self.db.commit()

        # Crear nuevo token
        device_token = DeviceToken(
            user_id=user_id,
            token=token,
            device_type=device_type
        )
        self.db.add(device_token)
        self.db.commit()
        self.db.refresh(device_token)
        return device_token

    def unregister_device_token(self, token: str):
        self.db.query(DeviceToken).filter(
            DeviceToken.token == token
        ).update({"is_active": False})
        self.db.commit() 