from pydantic import BaseModel, constr
from typing import Optional, List, Dict
from datetime import datetime
from database.models import UserType

class ServiceProfileBase(BaseModel):
    service_type: UserType
    base_price: float
    price_per_km: Optional[float] = None
    service_radius: Optional[float] = None
    working_hours: dict

class ServiceProfileCreate(ServiceProfileBase):
    pass

class ServiceProfileUpdate(ServiceProfileBase):
    is_available: Optional[bool] = None

class ServiceProfile(ServiceProfileBase):
    id: int
    user_id: int
    is_available: bool

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    images: List[str]

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    is_available: Optional[bool] = None

class Product(ProductBase):
    id: int
    business_id: int
    is_available: bool

    class Config:
        orm_mode = True

class ServiceBase(BaseModel):
    name: str
    description: str
    price: float

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(ServiceBase):
    is_available: Optional[bool] = None
    promotion_status: Optional[bool] = None
    promotion_end_date: Optional[datetime] = None

class Service(ServiceBase):
    id: int
    business_id: int
    service_profile_id: int
    is_available: bool
    promotion_status: bool
    promotion_end_date: Optional[datetime]

    class Config:
        orm_mode = True

class Location(BaseModel):
    lat: float
    lng: float
    address: str

class DeliveryCreate(BaseModel):
    service_id: int
    pickup_location: Location
    delivery_location: Location
    notes: Optional[str] = None

class Delivery(BaseModel):
    id: int
    user_id: int
    service_id: int
    status: str
    pickup_location: Location
    delivery_location: Location
    total_price: float
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True 