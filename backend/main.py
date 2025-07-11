from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

# Importar routers
from routers import auth, payment, analytics

# Importar servicios básicos
from database.database import engine, Base

# Cargar variables de entorno
load_dotenv()

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

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
            "authentication",
            "payments"
        ]
    }

if __name__ == "__main__":
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🌐 Iniciando servidor en {host}:{port}")
    print(f"📚 Documentación disponible en http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 