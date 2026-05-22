from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.database import get_db
from app.core.security import verificar_token
from app.modules.auth.models import SesionUsuario
from app.modules.usuarios.models import Usuario, RolUsuario, Rol
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=True)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Obtiene el usuario actual desde el token JWT"""
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar sesión activa en BD
    sesion = db.query(SesionUsuario).filter(
        SesionUsuario.token == token,
        SesionUsuario.activa == True
    ).first()
    
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no válida o cerrada",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == int(payload["sub"])).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return usuario

def require_roles(roles_permitidos: list):
    """
    Factory que retorna una dependencia para verificar roles.
    Uso: current_user = Depends(require_roles(["admin", "titular"]))
    """
    async def role_checker(
        current_user: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Obtener roles del usuario desde BD
        roles_usuario = db.query(Rol.nombre).join(
            RolUsuario, Rol.id_rol == RolUsuario.id_rol
        ).filter(RolUsuario.id_usuario == current_user.id_usuario).all()
        
        roles = [r[0] for r in roles_usuario]
        
        if not any(rol in roles_permitidos for rol in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles requeridos: {roles_permitidos}. Tus roles: {roles}"
            )
        return current_user
    
    return role_checker