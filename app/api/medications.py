# app/api/medications.py
"""
Endpoints básicos de medicamentos
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_medications():
    return {"message": "Lista de medicamentos - Por implementar"}