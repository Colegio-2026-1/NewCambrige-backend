
# app/modules/parametrizacion/schemas.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime

#PERIODO ACADEMICO

class AnioEscolarCreate(BaseModel):
    anio_inicio: int = Field(..., gt=2000, lt=2100, example=2025)
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool = Field(True, description="Estado del año escolar")

class AnioEscolarUpdate(BaseModel):
    # Todos los campos son opcionales para permitir actualizaciones parciales
    activo: Optional[bool] = Field(None, description="Nuevo estado de activación")
    fecha_inicio: Optional[datetime] = Field(None, description="Nueva fecha de inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Nueva fecha de fin")

class AnioEscolarRead(BaseModel):
    id_periodo: int
    nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool

    class Config:
        from_attributes = True

#TIPO PRUEBA

class TipoPruebaCreate(BaseModel):
    nombre: str = Field(..., max_length=100) # Obligatorio al crear
    grado_min: int
    grado_max: int
    descripcion: Optional[str] = Field(default=None, max_length=150)

    @field_validator('grado_min', 'grado_max')
    @classmethod
    def validar_rango_grados(cls, v):
        if not (1 <= v <= 12):
            raise ValueError('Ingrese un número entero válido para el grado escolar')
        return v

    @model_validator(mode='after')
    def validar_br249(self) -> 'TipoPruebaCreate':
        if self.grado_min > self.grado_max:
            raise ValueError('El grado inicial debe ser menor o igual al grado final')
        return self

class TipoPruebaUpdate(BaseModel):
    grado_min: int
    grado_max: int
    descripcion: Optional[str] = Field(default=None, max_length=150)

    @field_validator('grado_min', 'grado_max')
    @classmethod
    def validar_rango_grados(cls, v):
        if not (1 <= v <= 12):
            raise ValueError('Ingrese un número entero válido para el grado escolar')
        return v


    @model_validator(mode='after')
    def validar_br249(self) -> 'TipoPruebaUpdate':
        if self.grado_min > self.grado_max:
            raise ValueError('El grado inicial debe ser menor o igual al grado final')
        return self

class TipoPruebaRead(BaseModel):
    id_tipo_prueba: int
    nombre: str
    grado_min: int
    grado_max: int
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True
