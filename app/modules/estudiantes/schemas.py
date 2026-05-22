from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EstudianteBase(BaseModel):
    nombre: str
    telefono_acudiente: Optional[str] = None
    id_salon: Optional[int] = None
    documento: Optional[str] = None

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono_acudiente: Optional[str] = None
    id_salon: Optional[int] = None

class EstudianteResponse(EstudianteBase):
    id_estudiante: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True