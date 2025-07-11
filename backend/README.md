# AutoAssist API Backend

Backend completo para el sistema de servicios y entregas AutoAssist, construido con FastAPI y PostgreSQL.

## 🚀 Características

- **Autenticación JWT** con roles y permisos
- **Gestión de usuarios** (personal, negocios, proveedores de servicios)
- **Sistema de servicios** y productos
- **Sistema de entregas** con geolocalización
- **Sistema de pagos** (PayPal, Stripe, wallet interno)
- **Promociones y programa de lealtad**
- **Sistema de notificaciones** (push, email, SMS)
- **Calificaciones y reseñas**
- **Analytics y reportes**
- **Panel de administración** completo
- **Modo mantenimiento**
- **Auditoría completa**
- **Integración con Binance Pay** 🆕

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Redis (opcional, para caché)

## 🛠️ Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd autoassist/backend
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Configurar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb autoassist_db

# Ejecutar migraciones (si usas Alembic)
alembic upgrade head
```

6. **Ejecutar la aplicación**
```bash
python main.py
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Base de datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=autoassist_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# PayPal
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your-client-id
PAYPAL_CLIENT_SECRET=your-client-secret

# Google Maps
GOOGLE_MAPS_API_KEY=your-google-maps-key

# Firebase (notificaciones push)
FIREBASE_SERVER_KEY=your-firebase-key

# Email (SendGrid)
EMAIL_API_KEY=your-sendgrid-key
EMAIL_FROM=noreply@tuapp.com

# SMS (Twilio)
SMS_API_KEY=your-twilio-key
SMS_ACCOUNT_SID=your-account-sid
SMS_AUTH_TOKEN=your-auth-token
SMS_FROM=+1234567890

# Servidor
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Binance Pay 🆕
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
BINANCE_TESTNET=true  # false para producción
```

## 📚 Documentación de la API

Una vez ejecutada la aplicación, la documentación estará disponible en:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Estructura del Proyecto

```
backend/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias
├── .env                   # Variables de entorno
├── database/
│   ├── database.py        # Configuración de base de datos
│   ├── models.py          # Modelos SQLAlchemy
│   └── scripts/
│       └── init_db.py     # Script de inicialización
├── auth/
│   └── jwt.py            # Autenticación JWT
├── schemas/              # Esquemas Pydantic
│   ├── user.py
│   ├── service.py
│   ├── delivery.py
│   ├── payment.py
│   ├── promotion.py
│   ├── notification.py
│   ├── geolocation.py
│   ├── rating.py
│   ├── report.py
│   └── admin.py
├── services/             # Lógica de negocio
│   ├── payment.py
│   ├── notification.py
│   ├── geolocation.py
│   ├── rating.py
│   ├── analytics.py
│   └── admin.py
├── routers/              # Rutas de la API
│   ├── auth.py
│   ├── services.py
│   ├── delivery.py
│   ├── payment.py
│   ├── promotion.py
│   ├── notification.py
│   ├── geolocation.py
│   ├── rating.py
│   ├── analytics.py
│   └── admin.py
└── tests/                # Tests unitarios
```

## 🔐 Autenticación

La API usa JWT para autenticación. Para usar endpoints protegidos:

1. **Registrarse**: `POST /api/v1/auth/register`
2. **Iniciar sesión**: `POST /api/v1/auth/login`
3. **Usar el token**: Incluir en header `Authorization: Bearer <token>`

## 👥 Roles de Usuario

- **PERSONAL**: Usuarios regulares
- **BUSINESS**: Negocios y empresas
- **SERVICE_PROVIDER**: Proveedores de servicios
- **ADMIN**: Administradores del sistema
- **SUPER_ADMIN**: Super administradores

## 💳 Sistema de Pagos

Soporte para múltiples métodos de pago:

- **PayPal**: Integración completa
- **Stripe**: Preparado para integración
- **Wallet interno**: Sistema de billetera
- **Métodos tradicionales**: Tarjetas, transferencias
- **Binance Pay**: Integración con Binance Pay 🆕

## 📍 Geolocalización

- **Google Maps API**: Cálculo de distancias y rutas
- **Geocodificación**: Direcciones a coordenadas
- **Radio de entrega**: Verificación de cobertura

## 🔔 Notificaciones

- **Push notifications**: Firebase Cloud Messaging
- **Email**: SendGrid
- **SMS**: Twilio
- **Preferencias personalizables**

## 📊 Analytics

- **Métricas de negocio**: Ingresos, entregas, usuarios
- **Reportes personalizados**: Dashboards configurables
- **Exportación de datos**: Múltiples formatos

## 🛡️ Seguridad

- **JWT tokens** con expiración
- **Encriptación de contraseñas** (bcrypt)
- **Validación de datos** (Pydantic)
- **Auditoría completa** de acciones
- **Modo mantenimiento** con IPs permitidas
- **CORS configurado**
- **Rate limiting** (preparado)

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=.

# Tests específicos
pytest tests/test_auth.py
```

## 🚀 Despliegue

### Docker

```bash
# Construir imagen
docker build -t autoassist-backend .

# Ejecutar contenedor
docker run -p 8000:8000 autoassist-backend
```

### Producción

1. **Configurar variables de entorno de producción**
2. **Usar Gunicorn**:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```
3. **Configurar proxy reverso** (Nginx)
4. **Configurar SSL/TLS**
5. **Configurar monitoreo** (Prometheus, Grafana)

## 📝 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/register` - Registro
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Usuario actual

### Servicios
- `GET /api/v1/services/` - Listar servicios
- `POST /api/v1/services/` - Crear servicio
- `GET /api/v1/services/{id}` - Obtener servicio

### Entregas
- `POST /api/v1/delivery/` - Crear entrega
- `GET /api/v1/delivery/` - Listar entregas
- `PUT /api/v1/delivery/{id}/status` - Actualizar estado

### Pagos
- `POST /api/v1/payment/process` - Procesar pago
- `GET /api/v1/wallet/balance` - Saldo de wallet
- `POST /api/v1/wallet/deposit` - Depositar fondos

### Administración
- `GET /api/v1/admin/dashboard` - Dashboard admin
- `GET /api/v1/admin/system/status` - Estado del sistema
- `PUT /api/v1/admin/maintenance` - Modo mantenimiento

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico:
- Email: soporte@autoassist.com
- Documentación: https://docs.autoassist.com
- Issues: https://github.com/autoassist/backend/issues

## 🔄 Changelog

### v1.0.0
- ✅ Sistema completo de autenticación
- ✅ Gestión de usuarios y roles
- ✅ Sistema de servicios y entregas
- ✅ Integración de pagos
- ✅ Sistema de notificaciones
- ✅ Analytics y reportes
- ✅ Panel de administración
- ✅ Documentación completa 