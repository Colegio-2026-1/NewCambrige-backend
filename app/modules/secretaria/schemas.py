from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ============ MATRÍCULAS ============
class MatriculaBase(BaseModel):
    id_estudiante: int
    id_periodo: int
    estado: str = "activa"

class MatriculaCreate(MatriculaBase):
    pass

class MatriculaUpdate(BaseModel):
    estado: Optional[str] = None

class MatriculaResponse(MatriculaBase):
    id_matricula: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ DETALLES DE MATRÍCULA ============
class DetalleMatriculaBase(BaseModel):
    id_matricula: int
    id_tipo: int
    descripcion: Optional[str] = None
    estado: str = "pendiente"

class DetalleMatriculaCreate(DetalleMatriculaBase):
    pass

class DetalleMatriculaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

class DetalleMatriculaResponse(DetalleMatriculaBase):
    id_detalle: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ TIPOS DE CONCEPTO ============
class TipoConceptoBase(BaseModel):
    nombre: str

class TipoConceptoCreate(TipoConceptoBase):
    pass

class TipoConceptoResponse(TipoConceptoBase):
    id_tipo: int
    
    class Config:
        from_attributes = True