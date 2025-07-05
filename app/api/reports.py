# app/api/reports.py
"""
Endpoints básicos de reportes
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_reports():
    return {"message": "Lista de reportes - Por implementar"}