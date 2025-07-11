#!/usr/bin/env python3

# Test simple para identificar el problema de recursión
print("Iniciando test...")

try:
    print("1. Importando FastAPI...")
    from fastapi import FastAPI
    print("✓ FastAPI importado correctamente")
    
    print("2. Importando routers...")
    from routers import auth
    print("✓ Router auth importado correctamente")
    
    print("3. Importando schemas...")
    from schemas import user
    print("✓ Schema user importado correctamente")
    
    print("4. Importando database...")
    from database import database, models
    print("✓ Database y models importados correctamente")
    
    print("5. Creando app...")
    app = FastAPI()
    print("✓ App creada correctamente")
    
    print("6. Incluyendo routers...")
    app.include_router(auth.router, prefix="/api/v1")
    print("✓ Router incluido correctamente")
    
    print("✅ ¡Todo funciona correctamente!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 