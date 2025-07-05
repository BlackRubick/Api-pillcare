"""
Archivo principal de la aplicación FastAPI - PillCare 360
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import create_tables, test_connection, get_db_info
from app.api import api_router
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando PillCare 360 API...")
    logger.info(f"🌍 Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"🔑 Debug: {settings.DEBUG}")

    # Verificar conexión a la base de datos
    if test_connection():
        logger.info("✅ Conexión a MySQL exitosa")

        # Mostrar información de la base de datos
        db_info = get_db_info()
        if db_info:
            logger.info(f"📊 MySQL {db_info['mysql_version']} - DB: {db_info['database_name']}")

        # Crear tablas si no existen
        try:
            create_tables()
            logger.info("✅ Esquema de base de datos verificado")
        except Exception as e:
            logger.error(f"❌ Error al verificar esquema: {e}")
    else:
        logger.error("❌ Error de conexión a MySQL")
        logger.warning("⚠️ La aplicación continuará pero sin base de datos")

    logger.info("🎯 PillCare 360 API lista para recibir requests")
    yield

    # Shutdown
    logger.info("🛑 Cerrando PillCare 360 API...")


def create_application() -> FastAPI:
    """Factory function para crear la aplicación FastAPI"""

    # Configuración de la aplicación
    app_config = {
        "title": settings.PROJECT_NAME,
        "description": """
## PillCare 360 API

API REST para la gestión inteligente de medicamentos y tratamientos médicos.

### Características principales:
- 👥 Gestión de pacientes y cuidadores
- 💊 Catálogo de medicamentos
- 📋 Tratamientos personalizados
- ⏰ Alarmas y recordatorios
- 📊 Monitoreo de cumplimiento
- 🚨 Sistema de alertas
- 📈 Reportes y analíticas

### Seguridad:
- Autenticación JWT
- Control de acceso basado en roles
- Encriptación de datos sensibles
        """,
        "version": "1.0.0",
        "contact": {
            "name": "PillCare 360 Support",
            "email": "support@pillcare360.com",
        },
        "license_info": {
            "name": "MIT License",
        },
        "lifespan": lifespan,
    }

    # En producción, ocultar documentación
    if settings.is_production:
        app_config.update({
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None
        })

    app = FastAPI(**app_config)

    # Configurar middlewares
    setup_middlewares(app)

    # Configurar rutas
    setup_routes(app)

    return app


def setup_middlewares(app: FastAPI):
    """Configurar middlewares de la aplicación"""

    # CORS - Configuración para desarrollo y producción
    cors_config = {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["*"]
    }

    if settings.DEBUG:
        # En desarrollo, permitir más orígenes
        cors_config["allow_origins"] = ["*"]
        cors_config["allow_credentials"] = False

    app.add_middleware(CORSMiddleware, **cors_config)

    # Trusted hosts middleware (solo en producción)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.pillcare360.com", "pillcare360.com", "localhost"]
        )


def setup_routes(app: FastAPI):
    """Configurar rutas de la aplicación"""

    # Endpoint raíz
    @app.get("/")
    async def root():
        return {
            "message": "🏥 PillCare 360 API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "documentation": "/docs" if not settings.is_production else "Contact support for API documentation",
            "health": "/health",
            "api": "/api"
        }

    # Health check general
    @app.get("/health")
    async def health_check():
        """Health check completo de la aplicación"""
        db_status = "connected" if test_connection() else "disconnected"

        health_status = {
            "status": "healthy" if db_status == "connected" else "degraded",
            "service": "PillCare 360 API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "database": {
                "status": db_status,
                "type": "MySQL"
            },
            "timestamp": "2025-01-01T00:00:00Z"  # En implementación real, usar datetime.utcnow()
        }

        # Información adicional en desarrollo
        if settings.DEBUG:
            db_info = get_db_info()
            if db_info:
                health_status["database"].update(db_info)

        return health_status

    # Incluir router principal de la API
    app.include_router(
        api_router,
        prefix="/api"
    )


# Crear la aplicación
app = create_application()


# Solo para desarrollo con uvicorn run
if __name__ == "__main__":
    import uvicorn

    # Configuración para desarrollo
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.HOST,
        "port": settings.PORT,
        "reload": settings.DEBUG,
        "log_level": settings.LOG_LEVEL.lower(),
        "access_log": settings.DEBUG,
    }

    logger.info("🚀 Iniciando servidor de desarrollo...")
    logger.info(f"🌐 URL: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🔍 Redoc: http://{settings.HOST}:{settings.PORT}/redoc")
    logger.info(f"💡 Health: http://{settings.HOST}:{settings.PORT}/health")

    uvicorn.run(**uvicorn_config)