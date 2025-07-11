from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models import (
    SystemConfig, AdminUser, AuditLog, MaintenanceMode, User, 
    BusinessProfile, Delivery, Transaction, Report
)
from schemas.admin import (
    SystemConfigCreate, SystemConfigUpdate, AdminUserCreate, 
    AdminUserUpdate, AuditLogCreate, MaintenanceModeCreate,
    MaintenanceModeUpdate, AdminRole
)
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import time

class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.start_time = time.time()

    def create_system_config(
        self,
        config_data: SystemConfigCreate
    ) -> SystemConfig:
        """Crear una nueva configuración del sistema"""
        # Verificar que la clave no existe
        existing_config = self.db.query(SystemConfig).filter(
            SystemConfig.key == config_data.key
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una configuración con esta clave"
            )

        config = SystemConfig(**config_data.dict())
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_system_config(self, key: str) -> Optional[SystemConfig]:
        """Obtener una configuración específica"""
        return self.db.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_public_configs(self) -> List[SystemConfig]:
        """Obtener configuraciones públicas"""
        return self.db.query(SystemConfig).filter(SystemConfig.is_public == True).all()

    def update_system_config(
        self,
        key: str,
        config_update: SystemConfigUpdate
    ) -> SystemConfig:
        """Actualizar una configuración del sistema"""
        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración no encontrada"
            )

        for key, value in config_update.dict(exclude_unset=True).items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_system_config(self, key: str) -> bool:
        """Eliminar una configuración del sistema"""
        config = self.db.query(SystemConfig).filter(SystemConfig.key == key).first()
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración no encontrada"
            )

        self.db.delete(config)
        self.db.commit()
        return True

    def create_admin_user(
        self,
        admin_data: AdminUserCreate
    ) -> AdminUser:
        """Crear un nuevo administrador"""
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == admin_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Verificar que no es ya administrador
        existing_admin = self.db.query(AdminUser).filter(
            AdminUser.user_id == admin_data.user_id
        ).first()
        
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya es administrador"
            )

        admin_user = AdminUser(**admin_data.dict())
        self.db.add(admin_user)
        self.db.commit()
        self.db.refresh(admin_user)
        return admin_user

    def get_admin_users(self) -> List[AdminUser]:
        """Obtener todos los administradores"""
        return self.db.query(AdminUser).all()

    def update_admin_user(
        self,
        admin_id: int,
        admin_update: AdminUserUpdate
    ) -> AdminUser:
        """Actualizar un administrador"""
        admin_user = self.db.query(AdminUser).filter(AdminUser.id == admin_id).first()
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador no encontrado"
            )

        for key, value in admin_update.dict(exclude_unset=True).items():
            setattr(admin_user, key, value)

        admin_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(admin_user)
        return admin_user

    def delete_admin_user(self, admin_id: int) -> bool:
        """Eliminar un administrador"""
        admin_user = self.db.query(AdminUser).filter(AdminUser.id == admin_id).first()
        
        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Administrador no encontrado"
            )

        self.db.delete(admin_user)
        self.db.commit()
        return True

    def check_admin_permissions(
        self,
        user_id: int,
        resource: str,
        action: str
    ) -> bool:
        """Verificar permisos de administrador"""
        admin_user = self.db.query(AdminUser).filter(
            AdminUser.user_id == user_id,
            AdminUser.is_active == True
        ).first()

        if not admin_user:
            return False

        # Super admin tiene todos los permisos
        if admin_user.role == AdminRole.SUPER_ADMIN:
            return True

        # Verificar permisos específicos
        if admin_user.permissions:
            resource_permissions = admin_user.permissions.get(resource, [])
            return action in resource_permissions

        return False

    def create_audit_log(
        self,
        audit_data: AuditLogCreate,
        request: Request
    ) -> AuditLog:
        """Crear un registro de auditoría"""
        # Obtener IP y User Agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        audit_log = AuditLog(
            **audit_data.dict(),
            ip_address=client_ip,
            user_agent=user_agent
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        admin_user_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[AuditLog]:
        """Obtener registros de auditoría con filtros"""
        query = self.db.query(AuditLog)

        if admin_user_id:
            query = query.filter(AuditLog.admin_user_id == admin_user_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_maintenance_mode(self) -> Optional[MaintenanceMode]:
        """Obtener configuración de modo mantenimiento"""
        return self.db.query(MaintenanceMode).first()

    def update_maintenance_mode(
        self,
        maintenance_data: MaintenanceModeUpdate
    ) -> MaintenanceMode:
        """Actualizar modo mantenimiento"""
        maintenance = self.db.query(MaintenanceMode).first()
        
        if not maintenance:
            maintenance = MaintenanceMode()
            self.db.add(maintenance)

        for key, value in maintenance_data.dict(exclude_unset=True).items():
            setattr(maintenance, key, value)

        maintenance.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(maintenance)
        return maintenance

    def is_maintenance_mode(self, client_ip: Optional[str] = None) -> bool:
        """Verificar si el sistema está en modo mantenimiento"""
        maintenance = self.get_maintenance_mode()
        
        if not maintenance or not maintenance.is_active:
            return False

        # Verificar si la IP está permitida
        if client_ip and maintenance.allowed_ips:
            return client_ip not in maintenance.allowed_ips

        return True

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        # Total de usuarios
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        
        # Total de negocios
        total_businesses = self.db.query(func.count(BusinessProfile.id)).scalar() or 0
        
        # Total de entregas
        total_deliveries = self.db.query(func.count(Delivery.id)).scalar() or 0
        
        # Total de ingresos
        total_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.status == "completed"
        ).scalar() or 0.0
        
        # Tiempo de actividad del sistema
        system_uptime = time.time() - self.start_time
        
        # Modo mantenimiento activo
        maintenance = self.get_maintenance_mode()
        active_maintenance = maintenance.is_active if maintenance else False
        
        # Reportes pendientes
        pending_reports = self.db.query(func.count(Report.id)).filter(
            Report.status == "pending"
        ).scalar() or 0

        return {
            "total_users": total_users,
            "total_businesses": total_businesses,
            "total_deliveries": total_deliveries,
            "total_revenue": total_revenue,
            "system_uptime": round(system_uptime, 2),
            "active_maintenance": active_maintenance,
            "pending_reports": pending_reports
        }

    def get_admin_dashboard(self) -> Dict[str, Any]:
        """Obtener dashboard de administración"""
        # Actividades recientes
        recent_activities = self.get_audit_logs(skip=0, limit=10)
        
        # Estado del sistema
        system_status = self.get_system_status()
        
        # Configuraciones del sistema
        system_configs = self.db.query(SystemConfig).limit(5).all()
        
        # Usuarios activos (últimas 24 horas)
        active_users = self.db.query(func.count(User.id)).filter(
            User.updated_at >= datetime.utcnow() - timedelta(hours=24)
        ).scalar() or 0

        return {
            "recent_activities": recent_activities,
            "system_status": system_status,
            "active_users": active_users,
            "system_configs": system_configs
        }

    def backup_system_data(self) -> Dict[str, Any]:
        """Crear backup de datos del sistema"""
        # Esta es una implementación básica
        # En producción, deberías usar herramientas específicas de backup
        
        backup_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "users_count": self.db.query(func.count(User.id)).scalar(),
            "businesses_count": self.db.query(func.count(BusinessProfile.id)).scalar(),
            "deliveries_count": self.db.query(func.count(Delivery.id)).scalar(),
            "configs_count": self.db.query(func.count(SystemConfig.id)).scalar()
        }
        
        return backup_data 