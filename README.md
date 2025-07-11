# Sistema Web con React, FastAPI y PostgreSQL

Este proyecto es una aplicación web moderna construida con las siguientes tecnologías:

## Frontend
- React
- TypeScript
- Material-UI (para componentes de interfaz)

## Backend
- Python
- FastAPI
- SQLAlchemy (ORM)

## Base de Datos
- PostgreSQL

## Estructura del Proyecto
```
.
├── frontend/           # Aplicación React
├── backend/           # API FastAPI
└── docs/             # Documentación
```

## Requisitos Previos
- Node.js (v16 o superior)
- Python (v3.8 o superior)
- PostgreSQL (v13 o superior)

## Instalación

### Frontend
```bash
cd frontend
npm install
npm start
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Desarrollo
El frontend se ejecutará en http://localhost:3000
El backend se ejecutará en http://localhost:8000 