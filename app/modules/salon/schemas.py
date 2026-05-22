from pydantic import BaseModel
from typing import Optional

class SalonBase(BaseModel):
    grado: int
    grupo: int
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None

class SalonCreate(SalonBase):
    pass

class SalonUpdate(BaseModel):
    grado: Optional[int] = None
    grupo: Optional[int] = None
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None

class SalonResponse(SalonBase):
    id_salon: int
    
    class Config:
        from_attributes = True