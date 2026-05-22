from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PagoBase(BaseModel):
    id_estudiante: int
    id_periodo: int
    concepto: str
    monto: float
    referencia: Optional[str] = None

class PagoCreate(PagoBase):
    pass

class PagoResponse(PagoBase):
    id_pago: int
    fecha_pago: datetime
    estado: str
    
    class Config:
        from_attributes = True