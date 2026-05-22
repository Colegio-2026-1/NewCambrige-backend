from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ============ USUARIOS ============
class UsuarioBase(BaseModel):
    nombre: str

class UsuarioCreate(UsuarioBase):
    password: str
    roles: Optional[List[str]] = None
    estado: Optional[bool] = True

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    password: Optional[str] = None
    estado: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    estado: bool
    created_at: Optional[datetime] = None
    roles: List[str] = []
    
    class Config:
        from_attributes = True

# ============ ROLES ============
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class RolResponse(RolBase):
    id_rol: int
    
    class Config:
        from_attributes = True

# ============ ASIGNAR ROLES ============
class AsignarRolesRequest(BaseModel):
    roles: List[str]

# ============ SESIONES ============
class SesionResponse(BaseModel):
    id_sesion: int
    fecha_inicio: Optional[datetime] = None
    fecha_expiracion: Optional[datetime] = None
    activa: bool
    
    class Config:
        from_attributes = True