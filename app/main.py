import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date
import json

# ===== CONFIGURACIÓN =====
DATABASE_URL = f"mysql+pymysql://pillcare360_user:12345@localhost:3306/pillcare360?charset=utf8mb4"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===== MODELOS SQLALCHEMY =====
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    address = Column(Text, nullable=False)
    emergency_contact = Column(JSON, nullable=False)
    medical_history = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dosage = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    instructions = Column(Text, nullable=True)
    side_effects = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False)
    medication_id = Column(Integer, nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ===== CREAR TABLAS =====
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")

# ===== ESQUEMAS PYDANTIC =====
class PatientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    date_of_birth: date
    gender: str
    address: str
    emergency_contact: dict
    medical_history: List[str] = []
    allergies: List[str] = []

class PatientResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    date_of_birth: date
    gender: str
    address: str
    emergency_contact: dict
    medical_history: List[str]
    allergies: List[str]
    created_at: str

    class Config:
        from_attributes = True

class MedicationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dosage: str
    unit: str
    instructions: Optional[str] = None
    side_effects: List[str] = []

class TreatmentCreate(BaseModel):
    patient_id: int
    medication_id: int
    dosage: str
    frequency: int
    duration_days: int
    start_date: date
    end_date: date
    instructions: Optional[str] = None

# ===== DEPENDENCIAS =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== FASTAPI APP =====
app = FastAPI(
    title="PillCare 360 API - REAL",
    description="API real con MySQL para gestión de medicamentos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== ENDPOINTS =====

@app.get("/")
async def root():
    return {
        "message": "🏥 PillCare 360 API - VERSIÓN REAL",
        "version": "1.0.0",
        "database": "MySQL conectado",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Probar conexión
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "service": "PillCare 360 API"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}",
            "service": "PillCare 360 API"
        }

# ===== PACIENTES =====
@app.get("/api/patients", response_model=List[PatientResponse])
async def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return patients

@app.post("/api/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    # Verificar si el email ya existe
    existing = db.query(Patient).filter(Patient.email == patient.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return patient

@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, patient_update: PatientCreate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    for field, value in patient_update.dict().items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient

@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    db.delete(patient)
    db.commit()
    return {"message": "Paciente eliminado exitosamente"}

# ===== MEDICAMENTOS =====
@app.get("/api/medications")
async def list_medications(db: Session = Depends(get_db)):
    medications = db.query(Medication).all()
    return medications

@app.post("/api/medications", status_code=status.HTTP_201_CREATED)
async def create_medication(medication: MedicationCreate, db: Session = Depends(get_db)):
    db_medication = Medication(**medication.dict())
    db.add(db_medication)
    db.commit()
    db.refresh(db_medication)
    return db_medication

# ===== TRATAMIENTOS =====
@app.get("/api/treatments")
async def list_treatments(db: Session = Depends(get_db)):
    treatments = db.query(Treatment).all()
    return treatments

@app.post("/api/treatments", status_code=status.HTTP_201_CREATED)
async def create_treatment(treatment: TreatmentCreate, db: Session = Depends(get_db)):
    # Verificar que el paciente existe
    patient = db.query(Patient).filter(Patient.id == treatment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # Verificar que el medicamento existe
    medication = db.query(Medication).filter(Medication.id == treatment.medication_id).first()
    if not medication:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")

    db_treatment = Treatment(**treatment.dict())
    db.add(db_treatment)
    db.commit()
    db.refresh(db_treatment)
    return db_treatment


if __name__ == "__main__":
    import uvicorn

    print("🚀 Iniciando PillCare 360 API REAL...")
    print("🗄️ Conectando a MySQL...")
    print("🔗 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")

    uvicorn.run(
        "main",
        host="0.0.0.0",
        port=8000,
        reload=True
    )