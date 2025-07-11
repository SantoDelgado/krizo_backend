from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"

class SystemConfigBase(BaseModel):
    key: str = Field(..., description="Clave de configuración")
    value: Dict[str, Any] = Field(..., description="Valor de configuración")
    description: Optional[str] = Field(None, description="Descripción de la configuración")
    is_public: bool = Field(False, description="Indica si es visible para usuarios")

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class SystemConfig(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AdminUserBase(BaseModel):
    role: AdminRole = Field(..., description="Rol del administrador")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Permisos específicos")
    is_active: bool = Field(True, description="Indica si el administrador está activo")

class AdminUserCreate(AdminUserBase):
    user_id: int = Field(..., description="ID del usuario")

class AdminUserUpdate(BaseModel):
    role: Optional[AdminRole] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AdminUser(AdminUserBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AuditLogBase(BaseModel):
    action: str = Field(..., description="Acción realizada")
    resource_type: str = Field(..., description="Tipo de recurso")
    resource_id: Optional[int] = Field(None, description="ID del recurso")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles de la acción")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User Agent")

class AuditLogCreate(AuditLogBase):
    admin_user_id: Optional[int] = Field(None, description="ID del administrador")
    user_id: Optional[int] = Field(None, description="ID del usuario")

class AuditLog(AuditLogBase):
    id: int
    admin_user_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True

class MaintenanceModeBase(BaseModel):
    is_active: bool = Field(False, description="Indica si el modo mantenimiento está activo")
    message: Optional[str] = Field(None, description="Mensaje de mantenimiento")
    allowed_ips: Optional[List[str]] = Field(None, description="IPs permitidas")
    start_time: Optional[datetime] = Field(None, description="Hora de inicio")
    end_time: Optional[datetime] = Field(None, description="Hora de fin")

class MaintenanceModeCreate(MaintenanceModeBase):
    pass

class MaintenanceModeUpdate(BaseModel):
    is_active: Optional[bool] = None
    message: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class MaintenanceMode(MaintenanceModeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SystemStatus(BaseModel):
    total_users: int
    total_businesses: int
    total_deliveries: int
    total_revenue: float
    system_uptime: float
    active_maintenance: bool
    last_backup: Optional[datetime] = None

class AdminDashboard(BaseModel):
    recent_activities: List[AuditLog]
    system_status: SystemStatus
    pending_reports: int
    active_users: int
    system_configs: List[SystemConfig]

class PermissionCheck(BaseModel):
    resource: str = Field(..., description="Recurso a verificar")
    action: str = Field(..., description="Acción a verificar")
    has_permission: bool = Field(..., description="Indica si tiene permiso")

class AdminFilter(BaseModel):
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 