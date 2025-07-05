# app/api/treatments.py
"""
Endpoints básicos de tratamientos
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_treatments():
    return {"message": "Lista de tratamientos - Por implementar"}