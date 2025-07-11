from database.database import SessionLocal
from models_simple import User, ServiceProfile
from datetime import datetime
import json

def insert_test_data():
    db = SessionLocal()
    
    try:
        # Crear usuarios KrizoWorker de ejemplo
        test_workers = [
            {
                "email": "carlos.mendez@krizo.com",
                "phone": "0412-123-4567",
                "cedula": "V-12345678",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO",  # password123
                "user_type": "SERVICE_PROVIDER",
                "first_name": "Carlos",
                "last_name": "Méndez",
                "address": "Chacao, Caracas",
                "is_active": True
            },
            {
                "email": "maria.gonzalez@krizo.com",
                "phone": "0414-987-6543",
                "cedula": "V-87654321",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO",  # password123
                "user_type": "SERVICE_PROVIDER",
                "first_name": "María",
                "last_name": "González",
                "address": "Baruta, Caracas",
                "is_active": True
            },
            {
                "email": "roberto.silva@krizo.com",
                "phone": "0424-555-1234",
                "cedula": "V-11223344",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO",  # password123
                "user_type": "SERVICE_PROVIDER",
                "first_name": "Roberto",
                "last_name": "Silva",
                "address": "Libertador, Caracas",
                "is_active": True
            }
        ]
        
        # Insertar usuarios
        created_users = []
        for worker_data in test_workers:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(User.email == worker_data["email"]).first()
            if not existing_user:
                user = User(**worker_data)
                db.add(user)
                db.commit()
                db.refresh(user)
                created_users.append(user)
                print(f"✅ Usuario creado: {user.first_name} {user.last_name}")
            else:
                created_users.append(existing_user)
                print(f"ℹ️ Usuario ya existe: {existing_user.first_name} {existing_user.last_name}")
        
        # Crear perfiles de servicio
        service_profiles = [
            {
                "user_id": created_users[0].id,
                "services": ["mecanico", "electricista"],
                "experience_years": 8,
                "professional_description": "Mecánico especializado en vehículos japoneses y europeos. Servicio a domicilio con garantía.",
                "available_hours": {"start": "07:00", "end": "19:00"},
                "location_lat": 10.4806,
                "location_lng": -66.9036,
                "location_address": "Chacao, Caracas",
                "state": "Distrito Capital",
                "municipality": "Chacao",
                "parish": "Chacao",
                "is_online": True,
                "last_online": datetime.utcnow(),
                "average_rating": 4.8,
                "total_reviews": 127,
                "total_services": 45,
                "total_earnings": 2025.50
            },
            {
                "user_id": created_users[1].id,
                "services": ["plomero", "electricista"],
                "experience_years": 12,
                "professional_description": "Plomera profesional con amplia experiencia en instalaciones residenciales y comerciales.",
                "available_hours": {"start": "08:00", "end": "18:00"},
                "location_lat": 10.4861,
                "location_lng": -66.9017,
                "location_address": "Baruta, Caracas",
                "state": "Miranda",
                "municipality": "Baruta",
                "parish": "Baruta",
                "is_online": True,
                "last_online": datetime.utcnow(),
                "average_rating": 4.9,
                "total_reviews": 89,
                "total_services": 32,
                "total_earnings": 1760.00
            },
            {
                "user_id": created_users[2].id,
                "services": ["grua", "mecanico"],
                "experience_years": 15,
                "professional_description": "Servicio de grúa 24/7 y mecánica especializada en emergencias viales.",
                "available_hours": {"start": "00:00", "end": "23:59"},
                "location_lat": 10.4731,
                "location_lng": -66.9086,
                "location_address": "Libertador, Caracas",
                "state": "Distrito Capital",
                "municipality": "Libertador",
                "parish": "San Pedro",
                "is_online": False,
                "last_online": datetime.utcnow(),
                "average_rating": 4.6,
                "total_reviews": 203,
                "total_services": 78,
                "total_earnings": 5850.00,
                "vehicle_type": "Grúa",
                "vehicle_model": "Ford F-350",
                "vehicle_year": "2020",
                "vehicle_color": "Amarillo",
                "vehicle_plate": "ABC-1234"
            }
        ]
        
        # Insertar perfiles de servicio
        for profile_data in service_profiles:
            # Verificar si el perfil ya existe
            existing_profile = db.query(ServiceProfile).filter(
                ServiceProfile.user_id == profile_data["user_id"]
            ).first()
            
            if not existing_profile:
                profile = ServiceProfile(**profile_data)
                db.add(profile)
                db.commit()
                print(f"✅ Perfil de servicio creado para: {profile_data['user_id']}")
            else:
                print(f"ℹ️ Perfil de servicio ya existe para: {profile_data['user_id']}")
        
        print("\n🎉 Datos de prueba insertados correctamente!")
        print("📊 Resumen:")
        print(f"   - Usuarios KrizoWorker: {len(created_users)}")
        print(f"   - Perfiles de servicio: {len(service_profiles)}")
        
    except Exception as e:
        print(f"❌ Error al insertar datos: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_data() 