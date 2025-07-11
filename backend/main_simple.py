from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

# Importar configuración
from config import HOST, PORT, RELOAD

# Importar routers necesarios
from auth_simple import router as auth_router
from routers.services import router as services_router

# Importar servicios básicos
from database.database import engine, Base
from models_simple import User  # Importar el modelo para crear las tablas

# Configuración de la aplicación
app_config = {
    "title": "Krizo API",
    "description": "API para sistema de servicios automotrices",
    "version": "1.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicio y cierre de la aplicación"""
    # Crear tablas al inicio
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")
    print("🚀 Krizo API iniciada")
    yield
    print("🛑 Krizo API detenida")

# Crear aplicación FastAPI
app = FastAPI(**app_config, lifespan=lifespan)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")

# Rutas de salud y estado
@app.get("/")
async def root():
    """Ruta raíz"""
    return {
        "message": "Krizo API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Verificación de salud del sistema"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/api/v1/status")
async def api_status():
    """Estado de la API"""
    return {
        "api_version": "v1",
        "status": "active",
        "services": [
            "authentication"
        ]
    }

if __name__ == "__main__":
    print(f"🌐 Iniciando servidor en {HOST}:{PORT}")
    print(f"📚 Documentación disponible en http://{HOST}:{PORT}/docs")
    
    uvicorn.run(
        "main_simple:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="info"
    ) 