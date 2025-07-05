#app/api/patients.py
"""
Endpoints básicos de pacientes
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_patients():
    return {"message": "Lista de pacientes - Por implementar"}

@router.post("/")
async def create_patient():
    return {"message": "Crear paciente - Por implementar"}