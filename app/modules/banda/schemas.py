from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# ============ CATEGORÍAS ============
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None

class CategoriaResponse(CategoriaBase):
    id_categoria: int
    
    class Config:
        from_attributes = True

# ============ INSTRUMENTOS ============
class InstrumentoBase(BaseModel):
    nombre: str
    id_categoria: Optional[int] = None
    cantidad_total:int = Field(ge=0)
    estado:str = "activo"
    
class InstrumentoCreate(InstrumentoBase):
    pass

class InstrumentoUpdate(BaseModel):
    nombre: Optional[str] = None
    id_categoria: Optional[int] = None
    cantidad_total: Optional[int] = Field(None, ge=0)
    estado: Optional[str] = None

class InstrumentoResponse(InstrumentoBase):
    id_instrumento: int
    cantidad_disponible: int
    categoria_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ DEVOLUCIONES DE INSTRUMENTOS ============
class DevolucionCreate(BaseModel):
    estado_al_devolver: str 
    observaciones: Optional[str] = None

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
class PrestamoInstrumentoBase(BaseModel):
    id_instrumento: int
    id_estudiante: int
    observacion: Optional[str] = None

class PrestamoInstrumentoCreate(PrestamoInstrumentoBase):
    pass

class PrestamoInstrumentoUpdate(BaseModel):
    fecha_devolucion: Optional[date] = None
    estado_entrega: Optional[str] = None
    observacion: Optional[str] = None

class PrestamoInstrumentoResponse(PrestamoInstrumentoBase):
    id_prestamo: int
    id_instrumento: int
    id_estudiante: int
    fecha_prestamo: date
    fecha_devolucion: Optional[date] = None
    estado_entrega: str
    estado_al_devolver: Optional[str] = None
    observacion: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    instrumento_nombre: Optional[str] = None
    estudiante_nombre: Optional[str] = None
    
    estudiante_documento: Optional[str] = None
    estudiante_grado: Optional[str] = None
    estudiante_grupo: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============ REPORTES ============
class InstrumentoDisponibleResponse(BaseModel):
    id_instrumento: int
    codigo: int
    nombre: str
    cantidad_disponible: int
    categoria: Optional[str] = None

class PrestamoActivoResponse(BaseModel):
    id_prestamo: int
    instrumento: str
    estudiante: str
    fecha_prestamo: datetime
    dias_prestado: int
    
class AuditoriaBandaResponse(BaseModel):
    id_auditoria: int
    fecha: date
    hora: datetime
    nombre_usuario: str
    tabla: str
    accion: str
    entidad_afectada: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    resultado: str
    descripcion: str

    class Config:
        from_attributes = True
        
#============ esquemas para grado y grupo ============

class SalonSimple(BaseModel):
    grado: str
    grupo: str
    class Config:
        from_attributes = True

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
    salon: Optional[SalonSimple] = None
    
    class Config:
        from_attributes = True