#!/usr/bin/env python3
"""
Script para insertar datos de prueba para KrizoWorkers
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, engine
from database.models import (
    User, Delivery, Rating, Transaction, Payment, 
    UserType, PaymentStatus, TransactionType
)
from auth.jwt import create_access_token

def create_test_krizoworker_data():
    """Crear datos de prueba para un KrizoWorker"""
    db = SessionLocal()
    
    try:
        # Crear un usuario KrizoWorker de prueba
        krizoworker = User(
            email="krizoworker@test.com",
            phone="+1234567891",
            cedula="87654321",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2",  # password123
            user_type=UserType.SERVICE_PROVIDER,
            first_name="Juan",
            last_name="Mecánico",
            address="Calle Principal 123, Ciudad",
            is_active=True
        )
        
        db.add(krizoworker)
        db.commit()
        db.refresh(krizoworker)
        
        print(f"✅ KrizoWorker creado: {krizoworker.email} (ID: {krizoworker.id})")
        
        # Crear entregas de prueba
        delivery_statuses = ["completed", "pending", "accepted", "in_progress"]
        services = ["Cambio de Aceite", "Revisión de Frenos", "Diagnóstico Eléctrico", "Mantenimiento General"]
        
        for i in range(25):  # 25 entregas totales
            # Fecha aleatoria en los últimos 3 meses
            days_ago = random.randint(0, 90)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            status = random.choice(delivery_statuses)
            service_name = random.choice(services)
            price = random.uniform(30.0, 150.0)
            
            delivery = Delivery(
                user_id=krizoworker.id,
                service_id=1,  # ID de servicio ficticio
                status=status,
                pickup_location={
                    "lat": 19.4326 + random.uniform(-0.01, 0.01),
                    "lng": -99.1332 + random.uniform(-0.01, 0.01),
                    "address": f"Ubicación de recogida {i+1}"
                },
                delivery_location={
                    "lat": 19.4326 + random.uniform(-0.01, 0.01),
                    "lng": -99.1332 + random.uniform(-0.01, 0.01),
                    "address": f"Ubicación de entrega {i+1}"
                },
                total_price=round(price, 2),
                notes=f"Servicio: {service_name}",
                created_at=created_at
            )
            
            if status == "completed":
                delivery.completed_at = created_at + timedelta(hours=random.randint(1, 4))
            
            db.add(delivery)
            db.commit()
            db.refresh(delivery)
            
            # Crear transacción para entregas completadas
            if status == "completed":
                transaction = Transaction(
                    user_id=krizoworker.id,
                    wallet_id=1,  # ID de wallet ficticio
                    amount=delivery.total_price,
                    type=TransactionType.PAYMENT,
                    status=PaymentStatus.COMPLETED,
                    description=f"Pago por servicio: {service_name}",
                    meta_data={"delivery_id": delivery.id},
                    created_at=delivery.completed_at
                )
                db.add(transaction)
                db.commit()
        
        print(f"✅ 25 entregas creadas para el KrizoWorker")
        
        # Crear calificaciones de prueba
        for i in range(18):  # 18 reseñas
            rating = Rating(
                user_id=krizoworker.id,
                business_id=1,  # ID de negocio ficticio
                service_id=1,   # ID de servicio ficticio
                delivery_id=random.randint(1, 25),
                rating=random.randint(4, 5),  # Mayormente buenas calificaciones
                review=f"Excelente servicio, muy profesional. Reseña #{i+1}",
                is_anonymous=False,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(rating)
        
        db.commit()
        print(f"✅ 18 calificaciones creadas para el KrizoWorker")
        
        print("\n🎯 Datos de prueba creados exitosamente!")
        print(f"📊 Estadísticas esperadas:")
        print(f"   - Ganancias totales: ~$1,500-2,500")
        print(f"   - Servicios completados: ~15-20")
        print(f"   - Calificación promedio: ~4.5-5.0")
        print(f"   - Tasa de aceptación: ~80-100%")
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creando datos de prueba para KrizoWorker...")
    create_test_krizoworker_data()
    print("✅ Script completado!") 