from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from database.models import NotificationType, NotificationPriority

class NotificationBase(BaseModel):
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    data: Optional[Dict] = None

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        orm_mode = True

class NotificationPreferenceBase(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    order_updates: bool = True
    payment_updates: bool = True
    promotion_updates: bool = True
    loyalty_updates: bool = True
    system_updates: bool = True

class NotificationPreferenceCreate(NotificationPreferenceBase):
    pass

class NotificationPreference(NotificationPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class DeviceTokenBase(BaseModel):
    token: str
    device_type: str

class DeviceTokenCreate(DeviceTokenBase):
    pass

class DeviceToken(DeviceTokenBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class NotificationResponse(BaseModel):
    notifications: List[Notification]
    unread_count: int

class NotificationUpdate(BaseModel):
    is_read: bool = True 