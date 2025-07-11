from database.database import engine, Base
from models_simple import User, ServiceProfile

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Base de datos inicializada correctamente")

if __name__ == "__main__":
    init_db() 