from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EstudianteImportBase(BaseModel):
    documento: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=255)
    grado: Optional[str] = Field(None, max_length=100)
    curso: Optional[str] = Field(None, max_length=100)
    jornada: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = Field(None)

class DocenteImportBase(BaseModel):
    documento: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=255)
    grado_titular: Optional[str] = Field(None, max_length=100)
    curso_titular: Optional[str] = Field(None, max_length=100)

class CargaMasivaRequest(BaseModel):
    tipo: str # "estudiante" o "docente"
    datos: List[dict] # Se puede hacer un list de BaseModel para validacion mas estricta luego

class CargaIndividualRequest(BaseModel):
    tipo: str
    datos: dict

class EjecucionBotResponse(BaseModel):
    id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: str
    registros_estudiantes: int
    registros_docentes: int
    errores: int
    tipo_ejecucion: str
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

class SincronizarRequest(BaseModel):
    ejecucion_id: int

class CredencialesResponse(BaseModel):
    url: str
    nombre_usuario: str
    password_hash: str
    
    class Config:
        from_attributes = True

class CredencialesUpdate(BaseModel):
    url: str
    nombre_usuario: str
    password: str
