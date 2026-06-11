from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# =========================================
# SCHEMAS - INVENTARIO OBJETO
# =========================================
class ObjetoBase(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    estado_fisico: Optional[str] = None
    talla: Optional[str] = None
    observacion: Optional[str] = None
    fecha_registro: Optional[date] = None
    cantidad_total: int = 0
    cantidad_disponible: int = 0

class ObjetoCreate(ObjetoBase):
    pass

class ObjetoUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    estado_fisico: Optional[str] = None
    talla: Optional[str] = None
    observacion: Optional[str] = None
    fecha_registro: Optional[date] = None
    cantidad_total: Optional[int] = None
    cantidad_disponible: Optional[int] = None

class ObjetoResponse(ObjetoBase):
    id_objeto: int
    prestadas: int = 0

    class Config:
        from_attributes = True


# =========================================
# SCHEMAS - PRESTAMO OBJETO
# =========================================
class PrestamoObjetoBase(BaseModel):
    id_objeto: int
    id_estudiante: int
    talla: Optional[str] = None
    cantidad_prestada: int = 1

class PrestamoObjetoCreate(PrestamoObjetoBase):
    estado: str

class PrestamoObjetoResponse(PrestamoObjetoBase):
    id_prestamo: int
    fecha_prestamo: Optional[datetime] = None  # Cambiado para acoplarse con datetime.now() de tu servicio
    fecha_devolucion: Optional[datetime] = None  # Cambiado a datetime por consistencia con datetime.today()
    estado_prestamo: Optional[str] = None
    estado_entrega: str
    observacion: Optional[str] = None
    created_at: Optional[datetime] = None  # Se vuelve opcional para prevenir fallos si el ORM no lo implementa

    class Config:
        from_attributes = True


# =========================================
# SCHEMAS - VISTAS / RESPUESTAS DE TABLAS
# =========================================
class AsignacionResponse(BaseModel):
    id_prestamo: Optional[int] = None
    id_estudiante: int
    codigo: str
    nombre_completo: str
    grado: Optional[str] = None
    grupo: Optional[str] = None
    anio: Optional[str] = None
    prenda: Optional[str] = None
    fecha_entrega: Optional[datetime] = None  # Solución al Bug: Ahora acepta datetime con hora sin romper la serialización
    estado: Optional[str] = None
    estado_original: Optional[str] = None
    talla: Optional[str] = None  # Se añade explícitamente ya que tu servicio lo incluye en el diccionario de salida
    estado_entrega: Optional[str] = None

    class Config:
        from_attributes = True