from sqlalchemy.orm import Session
from typing import Optional, List
from passlib.context import CryptContext
from app.modules.usuarios.models import Usuario, Rol, RolUsuario
from app.modules.auth.models import SesionUsuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ============ USUARIOS ============
def get_usuarios_all(db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
    return db.query(Usuario).offset(skip).limit(limit).all()

def get_usuario_by_id(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()

def get_usuario_by_nombre(db: Session, nombre: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.nombre == nombre).first()

def get_usuario_con_roles(db: Session, usuario_id: int) -> Optional[dict]:
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        return None
    
    roles = db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == usuario_id).all()
    
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "estado": usuario.estado,
        "created_at": usuario.created_at,
        "roles": [r[0] for r in roles]
    }

def create_usuario(db: Session, data: dict) -> Usuario:
    nuevo = Usuario(
        nombre=data["nombre"],
        contrasena=hash_password(data["password"]),
        estado=data.get("estado", True)
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    # Asignar roles si vienen
    roles_asignados = data.get("roles", ["none"])
    for rol_nombre in roles_asignados:
        rol = db.query(Rol).filter(Rol.nombre == rol_nombre).first()
        if rol:
            db.add(RolUsuario(id_usuario=nuevo.id_usuario, id_rol=rol.id_rol))
    
    db.commit()
    return nuevo

def update_usuario(db: Session, usuario_id: int, data: dict) -> Optional[Usuario]:
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        return None
    
    if "nombre" in data and data["nombre"]:
        usuario.nombre = data["nombre"]
    if "password" in data and data["password"]:
        usuario.contrasena = hash_password(data["password"])
        
    if "estado" in data and data["estado"] is not None:
        usuario.estado = data["estado"]
    db.commit()
    db.refresh(usuario)
    return usuario

def delete_usuario(db: Session, usuario_id: int) -> bool:
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        return False
    db.delete(usuario)
    db.commit()
    return True

# ============ ROLES ============
def get_roles_all(db: Session) -> List[Rol]:
    return db.query(Rol).all()

def get_rol_by_id(db: Session, rol_id: int) -> Optional[Rol]:
    return db.query(Rol).filter(Rol.id_rol == rol_id).first()

def get_rol_by_nombre(db: Session, nombre: str) -> Optional[Rol]:
    return db.query(Rol).filter(Rol.nombre == nombre).first()

def create_rol(db: Session, nombre: str) -> Rol:
    nuevo = Rol(nombre=nombre)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def asignar_roles(db: Session, usuario_id: int, roles: List[str]) -> Optional[Usuario]:
    usuario = get_usuario_by_id(db, usuario_id)
    if not usuario:
        return None
    
    # Eliminar roles actuales
    db.query(RolUsuario).filter(RolUsuario.id_usuario == usuario_id).delete()
    
    # Asignar nuevos roles
    for rol_nombre in roles:
        rol = get_rol_by_nombre(db, rol_nombre)
        if rol:
            db.add(RolUsuario(id_usuario=usuario_id, id_rol=rol.id_rol))
    
    db.commit()
    return usuario

def get_roles_de_usuario(db: Session, usuario_id: int) -> List[str]:
    roles = db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == usuario_id).all()
    return [r[0] for r in roles]

# ============ SESIONES ============
def get_sesiones_activas(db: Session, usuario_id: int) -> List[SesionUsuario]:
    return db.query(SesionUsuario).filter(
        SesionUsuario.id_usuario == usuario_id,
        SesionUsuario.activa == True
    ).all()

def cerrar_sesion(db: Session, sesion_id: int) -> bool:
    sesion = db.query(SesionUsuario).filter(SesionUsuario.id_sesion == sesion_id).first()
    if not sesion:
        return False
    sesion.activa = False
    db.commit()
    return True

def cerrar_todas_sesiones(db: Session, usuario_id: int) -> int:
    resultado = db.query(SesionUsuario).filter(
        SesionUsuario.id_usuario == usuario_id,
        SesionUsuario.activa == True
    ).update({SesionUsuario.activa: False})
    db.commit()
    return resultado