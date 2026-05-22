from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.usuarios import service
from app.modules.usuarios.schemas import (
    UsuarioResponse, UsuarioCreate, UsuarioUpdate,
    RolResponse, RolCreate, AsignarRolesRequest,
    SesionResponse
)
from app.modules.auth.deps import require_roles

router = APIRouter()

# ============ USUARIOS ============
@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Listar todos los usuarios - Solo admin"""
    usuarios = service.get_usuarios_all(db, skip, limit)
    resultado = []
    for u in usuarios:
        roles = service.get_roles_de_usuario(db, u.id_usuario)
        resultado.append({
            "id_usuario": u.id_usuario,
            "nombre": u.nombre,
            "created_at": u.created_at,
            "roles": roles
        })
    return resultado

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Obtener usuario por ID - Solo admin"""
    usuario = service.get_usuario_con_roles(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Crear nuevo usuario - Solo admin"""
    existente = service.get_usuario_by_nombre(db, data.nombre)
    if existente:
        raise HTTPException(status_code=400, detail="El nombre ya está registrado")
    
    usuario = service.create_usuario(db, data.model_dump())
    roles = service.get_roles_de_usuario(db, usuario.id_usuario)
    
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "created_at": usuario.created_at,
        "roles": roles
    }

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Actualizar usuario - Solo admin"""
    usuario = service.update_usuario(db, usuario_id, data.model_dump(exclude_unset=True))
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    roles = service.get_roles_de_usuario(db, usuario.id_usuario)
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "created_at": usuario.created_at,
        "roles": roles
    }

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Eliminar usuario - Solo admin"""
    if not service.delete_usuario(db, usuario_id):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

# ============ ROLES ============
@router.get("/roles", response_model=List[RolResponse])
def listar_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Listar todos los roles - Solo admin"""
    return service.get_roles_all(db)

@router.post("/roles", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def crear_rol(
    data: RolCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Crear nuevo rol - Solo admin"""
    existente = service.get_rol_by_nombre(db, data.nombre)
    if existente:
        raise HTTPException(status_code=400, detail="El rol ya existe")
    return service.create_rol(db, data.nombre)

@router.get("/{usuario_id}/roles", response_model=List[str])
def obtener_roles_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Obtener roles de un usuario - Solo admin"""
    usuario = service.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return service.get_roles_de_usuario(db, usuario_id)

@router.put("/{usuario_id}/roles", response_model=UsuarioResponse)
def asignar_roles_usuario(
    usuario_id: int,
    data: AsignarRolesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Asignar roles a un usuario - Solo admin"""
    usuario = service.asignar_roles(db, usuario_id, data.roles)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    roles = service.get_roles_de_usuario(db, usuario.id_usuario)
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "created_at": usuario.created_at,
        "roles": roles
    }

# ============ SESIONES ============
@router.get("/{usuario_id}/sesiones", response_model=List[SesionResponse])
def obtener_sesiones_activas(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Obtener sesiones activas de un usuario - Solo admin"""
    usuario = service.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return service.get_sesiones_activas(db, usuario_id)

@router.delete("/sesiones/{sesion_id}", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion_especifica(
    sesion_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Cerrar una sesión específica - Solo admin"""
    if not service.cerrar_sesion(db, sesion_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

@router.post("/{usuario_id}/cerrar-todas-sesiones")
def cerrar_todas_sesiones_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    """Cerrar todas las sesiones de un usuario - Solo admin"""
    usuario = service.get_usuario_by_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    cantidad = service.cerrar_todas_sesiones(db, usuario_id)
    return {"message": f"Se cerraron {cantidad} sesiones", "usuario": usuario.nombre}