from pydantic import BaseModel
from typing import Optional
from datetime import date
# ======================
# 🏫 SALONES
# ======================
class SalonBase(BaseModel):
    grado: str
    grupo: str
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None


class SalonCreate(SalonBase):
    pass


class SalonUpdate(BaseModel):
    grado: Optional[str] = None
    grupo: Optional[str] = None
    id_usuario: Optional[int] = None
    id_periodo: Optional[int] = None


class SalonResponse(SalonBase):
    id_salon: int

    class Config:
        from_attributes = True

# ======================
# 🧪 PRUEBAS
# ======================
class PruebaResponse(BaseModel):
    id_prueba: int
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[str] = None
    grupo: Optional[str] = None
    tipo_prueba: Optional[str] = None
    estado: Optional[str] = None   # CAMBIO AQUÍ
    fecha_pago: Optional[date] = None

    class Config:
        from_attributes = True


class PruebaCreate(BaseModel):
    id_estudiante: int
    id_tipo_prueba: int
    estado: Optional[str] = "Pendiente"
    fecha_pago: Optional[date] = None

# ======================
# 🪑 PUPITRES
# ======================
class PupitreResponse(BaseModel):
    id_mantenimiento: int
    id_estudiante: int
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None  
    fecha_pago: Optional[date] # CAMBIO AQUÍ

    class Config:
        from_attributes = True


class PupitreUpdate(BaseModel):
    estado: str   # 🔥 CAMBIO AQUÍ
    fecha_pago: Optional[date] = None


# ======================
# 📚 BIBLIOTECA
# ======================
class LibroResponse(BaseModel):
    id_libro: int
    nombre: str
    autor: str
    id_salon: Optional[int] = None
    disponible: Optional[bool] = True
    edicion: Optional[str] = None
    estado_fisico: Optional[str] = None

    class Config:
        from_attributes = True


class LibroCreate(BaseModel):
    nombre: str
    autor: str
    edicion : str
    id_salon: Optional[int] = None
    disponible: Optional[bool] = True
    estado_fisico: Optional[str] = None

class LibroUpdate(BaseModel):
    nombre: Optional[str] = None
    autor: Optional[str] = None
    edicion:      Optional[str]  = None   # 
    estado_fisico: Optional[str] = None   # 
    id_salon: Optional[int] = None
    disponible: Optional[bool] = None


class PrestamoResponse(BaseModel):
    id_prestamo: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    grado: Optional[str] = None
    grupo: Optional[str] = None
    libro: Optional[str] = None
    fecha_prestamo: Optional[str] = None
    fecha_devolucion: Optional[str] = None
    estado: Optional[str] = None   #  CAMBIO AQUÍ


class PrestamoCreate(BaseModel):
    codigo:           int
    libro:            str
    fecha_devolucion: Optional[date] = None
    estado:           Optional[str]  = "Prestado"
    estado_fisico:    Optional[str]  = "Excelente"

class DevolucionSchema(BaseModel):
    fecha_devolucion: Optional[date] = None
    estado_de_devolucion: Optional[str] = None
    observacion: Optional[str] = None