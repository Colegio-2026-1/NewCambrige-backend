from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ObjetoBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    cantidad_total: int = 0
    cantidad_disponible: int = 0

class ObjetoCreate(ObjetoBase):
    pass

class ObjetoUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    cantidad_total: Optional[int] = None
    cantidad_disponible: Optional[int] = None

class ObjetoResponse(ObjetoBase):
    id_objeto: int
    
    class Config:
        from_attributes = True

class PrestamoObjetoBase(BaseModel):
    id_objeto: int
    id_estudiante: int
    fecha_prestamo: date
    talla: Optional[str] = None
    cantidad_prestada: int = 1

class PrestamoObjetoCreate(PrestamoObjetoBase):
    pass

class PrestamoObjetoResponse(PrestamoObjetoBase):
    id_prestamo: int
    fecha_devolucion: Optional[date] = None
    estado_entrega: str
    created_at: datetime
    
    class Config:
        from_attributes = True