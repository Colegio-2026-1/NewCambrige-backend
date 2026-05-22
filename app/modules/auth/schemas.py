from pydantic import BaseModel
from typing import List, Optional
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre: str

class UsuarioCreate(BaseModel):
    nombre: str
    password: str
    roles: Optional[List[str]] = None
    class Config:
        from_attributes = True