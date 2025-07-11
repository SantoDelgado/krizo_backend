from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class ReportType(str, Enum):
    DELIVERY = "delivery"
    SERVICE = "service"
    BUSINESS = "business"
    USER = "user"

class ReportReason(str, Enum):
    INAPPROPRIATE = "inappropriate"
    FRAUD = "fraud"
    QUALITY = "quality"
    OTHER = "other"

class ReportStatus(str, Enum):
    PENDING = "pending"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class ReportBase(BaseModel):
    report_type: ReportType = Field(..., description="Tipo de reporte")
    reason: ReportReason = Field(..., description="Razón del reporte")
    description: Optional[str] = Field(None, description="Descripción detallada")

class ReportCreate(ReportBase):
    business_id: Optional[int] = Field(None, description="ID del negocio reportado")
    service_id: Optional[int] = Field(None, description="ID del servicio reportado")
    delivery_id: Optional[int] = Field(None, description="ID de la entrega reportada")

class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    admin_notes: Optional[str] = None

class Report(ReportBase):
    id: int
    user_id: int
    business_id: Optional[int] = None
    service_id: Optional[int] = None
    delivery_id: Optional[int] = None
    status: ReportStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AnalyticsBase(BaseModel):
    metric_type: str = Field(..., description="Tipo de métrica")
    metric_value: float = Field(..., description="Valor de la métrica")
    period: str = Field(..., description="Período de tiempo")
    date: date = Field(..., description="Fecha de la métrica")

class AnalyticsCreate(AnalyticsBase):
    business_id: Optional[int] = Field(None, description="ID del negocio")
    user_id: Optional[int] = Field(None, description="ID del usuario")

class Analytics(AnalyticsBase):
    id: int
    business_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True

class DashboardBase(BaseModel):
    name: str = Field(..., description="Nombre del dashboard")
    description: Optional[str] = Field(None, description="Descripción del dashboard")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuración del dashboard")
    is_default: bool = Field(False, description="Indica si es el dashboard por defecto")

class DashboardCreate(DashboardBase):
    business_id: Optional[int] = Field(None, description="ID del negocio")

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class Dashboard(DashboardBase):
    id: int
    user_id: int
    business_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BusinessMetrics(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    average_rating: float
    total_deliveries: int
    active_promotions: int
    loyalty_members: int

class RevenueMetrics(BaseModel):
    daily_revenue: List[Dict[str, Any]]
    weekly_revenue: List[Dict[str, Any]]
    monthly_revenue: List[Dict[str, Any]]
    total_revenue: float
    growth_rate: float

class OrderMetrics(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    cancelled_orders: int
    average_order_value: float
    orders_by_status: Dict[str, int]

class CustomerMetrics(BaseModel):
    total_customers: int
    new_customers: int
    active_customers: int
    customer_retention_rate: float
    top_customers: List[Dict[str, Any]]

class DeliveryMetrics(BaseModel):
    total_deliveries: int
    completed_deliveries: int
    average_delivery_time: float
    delivery_success_rate: float
    deliveries_by_status: Dict[str, int]

class AnalyticsFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metric_type: Optional[str] = None
    period: Optional[str] = None
    business_id: Optional[int] = None
    user_id: Optional[int] = None

class ReportFilter(BaseModel):
    report_type: Optional[ReportType] = None
    reason: Optional[ReportReason] = None
    status: Optional[ReportStatus] = None
    business_id: Optional[int] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 