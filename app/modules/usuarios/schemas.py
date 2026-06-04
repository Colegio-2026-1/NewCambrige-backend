from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, Optional

# ============ USUARIOS ============
class UsuarioBase(BaseModel):
    nombre: str

class UsuarioCreate(UsuarioBase):
    password: str
    roles: Optional[List[str]] = None
    estado: Optional[bool] = True
    documento: Optional[str] = None    

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    password: Optional[str] = None
    estado: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    estado: bool
    documento: Optional[str] = None
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
    roles: Optional[List[str]] = None

    @validator('roles', pre=True, each_item=False)
    def limpiar_roles(cls, v):
        if v is None:
            return []
        # Filtrar valores que no sean string (None, números, etc.)
        return [r for r in v if isinstance(r, str) and r.strip()]

# ============ SESIONES ============
class SesionResponse(BaseModel):
    id_sesion: int
    fecha_inicio: Optional[datetime] = None
    fecha_expiracion: Optional[datetime] = None
    activa: bool
    
    class Config:
        from_attributes = True