from database.database import SessionLocal
from models_simple import User, ServiceProfile
from datetime import datetime

def create_armando_delgado():
    db = SessionLocal()
    try:
        # Verificar si ya existe
        existing_user = db.query(User).filter(
            User.first_name == "Armando",
            User.last_name == "Delgado"
        ).first()
        
        if existing_user:
            print("✅ Armando Delgado ya existe en la base de datos")
            return existing_user
        
        # Crear usuario Armando Delgado
        armando = User(
            email="armando.delgado@krizo.com",
            phone="0412-555-1234",
            cedula="V-12345678",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.i8eO",  # password123
            user_type="SERVICE_PROVIDER",
            first_name="Armando",
            last_name="Delgado",
            address="Caracas, Venezuela",
            is_active=True
        )
        
        db.add(armando)
        db.commit()
        db.refresh(armando)
        
        # Crear perfil de servicio para Armando
        service_profile = ServiceProfile(
            user_id=armando.id,
            services=["mecanico", "electricista", "grua"],
            experience_years=10,
            professional_description="Mecánico profesional con amplia experiencia en vehículos de todas las marcas. Servicio a domicilio 24/7.",
            available_hours={"start": "06:00", "end": "22:00"},
            location_lat=10.4806,
            location_lng=-66.9036,
            location_address="Caracas, Venezuela",
            state="Distrito Capital",
            municipality="Libertador",
            parish="San Pedro",
            is_online=True,
            last_online=datetime.utcnow(),
            average_rating=4.9,
            total_reviews=156,
            total_services=89,
            total_earnings=4450.00
        )
        
        db.add(service_profile)
        db.commit()
        
        print("✅ Armando Delgado creado exitosamente como KrizoWorker")
        print(f"   - ID: {armando.id}")
        print(f"   - Email: {armando.email}")
        print(f"   - Servicios: {service_profile.services}")
        print(f"   - Rating: {service_profile.average_rating}")
        
        return armando
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_armando_delgado() 