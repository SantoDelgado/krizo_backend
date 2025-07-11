from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from schemas.admin import (
    SystemConfig, SystemConfigCreate, SystemConfigUpdate,
    AdminUser, AdminUserCreate, AdminUserUpdate,
    AuditLog, AuditLogCreate, MaintenanceMode, MaintenanceModeUpdate,
    SystemStatus, AdminDashboard, PermissionCheck, AdminRole
)
from services.admin import AdminService
from auth.jwt import get_current_user
from database.models import User, AdminUser as AdminUserModel
from fastapi import Depends

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

def require_admin(current_user: User = Depends(get_current_user)):
    """Verificar que el usuario es administrador"""
    if not current_user.admin_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user

def require_super_admin(current_user: User = Depends(get_current_user)):
    """Verificar que el usuario es super administrador"""
    if not current_user.admin_profile or current_user.admin_profile.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de super administrador"
        )
    return current_user

@router.get("/dashboard", response_model=AdminDashboard)
async def get_admin_dashboard(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener dashboard de administración"""
    admin_service = AdminService(db)
    return admin_service.get_admin_dashboard()

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener estado del sistema"""
    admin_service = AdminService(db)
    status_data = admin_service.get_system_status()
    return SystemStatus(**status_data)

# Rutas de configuración del sistema
@router.post("/config", response_model=SystemConfig)
async def create_system_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Crear una nueva configuración del sistema"""
    admin_service = AdminService(db)
    return admin_service.create_system_config(config_data)

@router.get("/config", response_model=List[SystemConfig])
async def get_system_configs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener todas las configuraciones del sistema"""
    admin_service = AdminService(db)
    return admin_service.get_public_configs()

@router.get("/config/{key}", response_model=SystemConfig)
async def get_system_config(
    key: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener una configuración específica"""
    admin_service = AdminService(db)
    config = admin_service.get_system_config(key)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    return config

@router.put("/config/{key}", response_model=SystemConfig)
async def update_system_config(
    key: str,
    config_update: SystemConfigUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Actualizar una configuración del sistema"""
    admin_service = AdminService(db)
    return admin_service.update_system_config(key, config_update)

@router.delete("/config/{key}")
async def delete_system_config(
    key: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Eliminar una configuración del sistema"""
    admin_service = AdminService(db)
    admin_service.delete_system_config(key)
    return {"message": "Configuración eliminada exitosamente"}

# Rutas de administradores
@router.post("/users", response_model=AdminUser)
async def create_admin_user(
    admin_data: AdminUserCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Crear un nuevo administrador (solo super admin)"""
    admin_service = AdminService(db)
    return admin_service.create_admin_user(admin_data)

@router.get("/users", response_model=List[AdminUser])
async def get_admin_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener todos los administradores"""
    admin_service = AdminService(db)
    return admin_service.get_admin_users()

@router.put("/users/{admin_id}", response_model=AdminUser)
async def update_admin_user(
    admin_id: int,
    admin_update: AdminUserUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Actualizar un administrador (solo super admin)"""
    admin_service = AdminService(db)
    return admin_service.update_admin_user(admin_id, admin_update)

@router.delete("/users/{admin_id}")
async def delete_admin_user(
    admin_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Eliminar un administrador (solo super admin)"""
    admin_service = AdminService(db)
    admin_service.delete_admin_user(admin_id)
    return {"message": "Administrador eliminado exitosamente"}

# Rutas de auditoría
@router.post("/audit", response_model=AuditLog)
async def create_audit_log(
    audit_data: AuditLogCreate,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Crear un registro de auditoría"""
    admin_service = AdminService(db)
    return admin_service.create_audit_log(audit_data, request)

@router.get("/audit", response_model=List[AuditLog])
async def get_audit_logs(
    admin_user_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener registros de auditoría con filtros"""
    admin_service = AdminService(db)
    return admin_service.get_audit_logs(
        skip=skip,
        limit=limit,
        admin_user_id=admin_user_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type
    )

# Rutas de modo mantenimiento
@router.get("/maintenance", response_model=MaintenanceMode)
async def get_maintenance_mode(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Obtener configuración de modo mantenimiento"""
    admin_service = AdminService(db)
    maintenance = admin_service.get_maintenance_mode()
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de mantenimiento no encontrada"
        )
    return maintenance

@router.put("/maintenance", response_model=MaintenanceMode)
async def update_maintenance_mode(
    maintenance_update: MaintenanceModeUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Actualizar modo mantenimiento (solo super admin)"""
    admin_service = AdminService(db)
    return admin_service.update_maintenance_mode(maintenance_update)

@router.get("/maintenance/check")
async def check_maintenance_mode(
    request: Request,
    db: Session = Depends(get_db)
):
    """Verificar si el sistema está en modo mantenimiento"""
    admin_service = AdminService(db)
    client_ip = request.client.host if request.client else None
    is_maintenance = admin_service.is_maintenance_mode(client_ip)
    
    if is_maintenance:
        maintenance = admin_service.get_maintenance_mode()
        return {
            "maintenance_mode": True,
            "message": maintenance.message if maintenance else "Sistema en mantenimiento"
        }
    
    return {"maintenance_mode": False}

# Rutas de permisos
@router.post("/permissions/check", response_model=PermissionCheck)
async def check_permissions(
    resource: str,
    action: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verificar permisos de administrador"""
    admin_service = AdminService(db)
    has_permission = admin_service.check_admin_permissions(
        current_user.id,
        resource,
        action
    )
    return PermissionCheck(
        resource=resource,
        action=action,
        has_permission=has_permission
    )

# Rutas de backup
@router.post("/backup")
async def create_backup(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Crear backup del sistema (solo super admin)"""
    admin_service = AdminService(db)
    backup_data = admin_service.backup_system_data()
    return {
        "message": "Backup creado exitosamente",
        "backup_data": backup_data
    }

# Rutas públicas
@router.get("/public/config", response_model=List[SystemConfig])
async def get_public_configs(
    db: Session = Depends(get_db)
):
    """Obtener configuraciones públicas del sistema"""
    admin_service = AdminService(db)
    return admin_service.get_public_configs()

@router.get("/public/status")
async def get_public_status(
    db: Session = Depends(get_db)
):
    """Obtener estado público del sistema"""
    admin_service = AdminService(db)
    status_data = admin_service.get_system_status()
    return {
        "total_users": status_data["total_users"],
        "total_businesses": status_data["total_businesses"],
        "total_deliveries": status_data["total_deliveries"],
        "system_uptime": status_data["system_uptime"]
    } 