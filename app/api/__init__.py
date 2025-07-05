"""
Router principal de la API
"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User

# Importar solo los routers que YA EXISTEN y están completos
from . import auth, patients, medications, treatments

# TODO: Importar cuando estén implementados
# from . import alarms, alerts, monitoring, reports, settings

# Router principal de la API
api_router = APIRouter()

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

# TODO: Descomentar cuando implementes estos módulos
"""
api_router.include_router(
    alarms.router,
    prefix="/alarms",
    tags=["alarms"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(get_current_user)]
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)]
)
"""

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
                "/treatments"
            ],
            "coming_soon": [
                "/alarms",
                "/alerts",
                "/monitoring",
                "/reports",
                "/settings"
            ]
        }
    }