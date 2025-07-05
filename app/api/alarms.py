# app/api/alarms.py
"""
Endpoints básicos de alarmas
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_alarms():
    return {"message": "Lista de alarmas - Por implementar"}