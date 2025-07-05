# app/api/monitoring.py
"""
Endpoints básicos de monitoreo
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard")
async def dashboard():
    return {"message": "Dashboard de monitoreo - Por implementar"}