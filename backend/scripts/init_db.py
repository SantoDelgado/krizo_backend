#!/usr/bin/env python3
"""
Script para inicializar la base de datos de Krizo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import engine, Base
from database.models import User, BusinessProfile, ServiceProfile, Product, Service, Delivery, Wallet, Transaction, Payment, PaymentMethod, Promotion, PromotionRedemption, LoyaltyProgram, LoyaltyMember, LoyaltyTransaction, Notification, NotificationPreference, DeviceToken, Rating, ReviewImage, RatingResponse, Report, Analytics, Dashboard, SystemConfig, AdminUser, AuditLog, MaintenanceMode, Location

def init_database():
    """Inicializar la base de datos creando todas las tablas"""
    try:
        print("🗄️  Inicializando base de datos...")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Base de datos inicializada correctamente")
        print("📋 Tablas creadas:")
        
        # Listar las tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"   - {table}")
            
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎉 Base de datos lista para usar")
    else:
        print("\n💥 Error al inicializar la base de datos")
        sys.exit(1) 