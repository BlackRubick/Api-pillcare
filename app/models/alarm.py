# app/models/alarm.py
"""
Modelo de Alarma
"""
from sqlalchemy import Column, Integer, String, Boolean, Time, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Alarm(Base):
    """Modelo de Alarma"""
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    treatment_id = Column(Integer, ForeignKey("treatments.id"), nullable=False)
    time = Column(String(5), nullable=False)  # HH:MM format
    is_active = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    visual_enabled = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    # Relaciones
    treatment = relationship("Treatment", back_populates="alarms")