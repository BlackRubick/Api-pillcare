"""
Router principal de la API
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

# Importar todos los routers
from . import auth, patients, medications, treatments
# Crear el archivo alarms.py con el código que te proporcioné
from . import alarms  # AGREGAR ESTA LÍNEA

# Router principal de la API
api_router = APIRouter()

from . import auth, patients, medications, treatments, alarms

# Agregar después de los otros routers:
api_router.include_router(
    alarms.router,
    prefix="",
    tags=["alarms"],
    dependencies=[Depends(get_current_user)]
)
# Incluir routers que YA ESTÁN IMPLEMENTADOS
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["patients"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    medications.router,
    prefix="/medications",
    tags=["medications"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    treatments.router,
    prefix="/treatments",
    tags=["treatments"],
    dependencies=[Depends(get_current_user)]
)

# AGREGAR EL ROUTER DE ALARMAS
api_router.include_router(
    alarms.router,
    prefix="",  # Sin prefix porque ya incluye /treatments/{id}/alarms en las rutas
    tags=["alarms"],
    dependencies=[Depends(get_current_user)]
)

# Endpoints adicionales de la API
@api_router.get("/health")
async def api_health():
    """Health check específico de la API"""
    return {
        "status": "healthy",
        "service": "PillCare 360 API",
        "version": "1.0.0"
    }


@api_router.get("/info")
async def api_info(current_user: User = Depends(get_current_user)):
    """Información de la API para el usuario actual"""
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "role": current_user.role,
            "is_admin": current_user.is_admin
        },
        "api": {
            "version": "1.0.0",
            "available_endpoints": [
                "/auth",
                "/patients",
                "/medications",
                "/treatments",
                "/treatments/{id}/alarms"  # AGREGAR ESTA LÍNEA
            ],
            "coming_soon": [
                "/alerts",
                "/monitoring",
                "/reports",
                "/settings"
            ]
        }
    }

