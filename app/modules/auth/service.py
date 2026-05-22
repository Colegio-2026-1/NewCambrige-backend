from sqlalchemy.orm import Session
from passlib.context import CryptContext

from fastapi import HTTPException

from datetime import (
    datetime,
    timedelta
)

from app.modules.usuarios.models import (
    Usuario,
    RolUsuario,
    Rol
)

from app.modules.auth.models import (
    SesionUsuario,
    LoginAttempt
)

from app.core.security import crear_token
from app.core.config import settings

# ==========================================
# PASSWORD HASH
# ==========================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ==========================================
# HASH PASSWORD
# ==========================================

def hash_contra(contra: str):

    return pwd_context.hash(
        contra
    )

# ==========================================
# VERIFICAR BLOQUEO
# ==========================================

def verificar_bloqueo(
    db: Session,
    username: str
):

    intento = db.query(
        LoginAttempt
    ).filter(
        LoginAttempt.username == username
    ).first()

    if not intento:
        return

    # usuario bloqueado
    if (
        intento.bloqueado_hasta and
        intento.bloqueado_hasta >
        datetime.utcnow()
    ):

        raise HTTPException(
            status_code=429,
            detail=(
                "Demasiados intentos. "
                "Intenta nuevamente en 1 minuto."
            )
        )

# ==========================================
# REGISTRAR INTENTO FALLIDO
# ==========================================

def registrar_intento_fallido(
    db: Session,
    username: str
):

    intento = db.query(
        LoginAttempt
    ).filter(
        LoginAttempt.username == username
    ).first()

    # crear registro
    if not intento:

        intento = LoginAttempt(
            username=username,
            intentos=1
        )

        db.add(intento)

    else:

        intento.intentos += 1

        # bloquear al llegar a 5
        if intento.intentos >= 5:

            intento.bloqueado_hasta = (
                datetime.utcnow() +
                timedelta(minutes=1)
            )

            # reiniciar contador
            intento.intentos = 0

    db.commit()

# ==========================================
# LIMPIAR INTENTOS
# ==========================================

def limpiar_intentos(
    db: Session,
    username: str
):

    intento = db.query(
        LoginAttempt
    ).filter(
        LoginAttempt.username == username
    ).first()

    if intento:

        intento.intentos = 0

        intento.bloqueado_hasta = None

        db.commit()

# ==========================================
# AUTENTICAR USUARIO
# ==========================================

def autenticar_usuario(
    db: Session,
    nombre: str,
    password: str
):

    # verificar bloqueo
    verificar_bloqueo(
        db,
        nombre
    )

    usuario = db.query(
        Usuario
    ).filter(
        Usuario.nombre == nombre
    ).first()

    # credenciales incorrectas
    if (
        not usuario or
        not pwd_context.verify(
            password,
            usuario.contrasena
        )
    ):

        registrar_intento_fallido(
            db,
            nombre
        )

        return None

    # login exitoso
    limpiar_intentos(
        db,
        nombre
    )

    return usuario

# ==========================================
# CREAR USUARIO
# ==========================================

def crear_usuario(
    db: Session,
    nombre: str,
    contra: str,
    roles: list = None
):

    existente = db.query(
        Usuario
    ).filter(
        Usuario.nombre == nombre
    ).first()

    if existente:
        return None

    nuevo = Usuario(
        nombre=nombre,
        contrasena=hash_contra(contra)
    )

    db.add(nuevo)

    db.commit()

    db.refresh(nuevo)

    if not roles:
        roles = ["none"]

    for rol_nombre in roles:

        rol = db.query(
            Rol
        ).filter(
            Rol.nombre == rol_nombre
        ).first()

        if rol:

            db.add(
                RolUsuario(
                    id_usuario=nuevo.id_usuario,
                    id_rol=rol.id_rol
                )
            )

    db.commit()

    return nuevo

# ==========================================
# GENERAR TOKEN
# ==========================================

def generar_token(
    db: Session,
    usuario: Usuario
) -> dict:

    roles_db = (
        db.query(Rol.nombre)
        .join(
            RolUsuario,
            Rol.id_rol == RolUsuario.id_rol
        )
        .filter(
            RolUsuario.id_usuario ==
            usuario.id_usuario
        )
        .all()
    )

    roles = [r[0] for r in roles_db]

    token = crear_token({

        "sub":
            str(usuario.id_usuario),

        "roles":
            roles
    })

    # buscar sesión activa
    sesion = db.query(
        SesionUsuario
    ).filter(

        SesionUsuario.id_usuario ==
        usuario.id_usuario,

        SesionUsuario.activa == True

    ).first()

    ahora = datetime.utcnow()

    expiracion = (
        ahora +
        timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    # ======================================
    # ACTUALIZAR SESIÓN
    # ======================================

    if sesion:

        sesion.token = token

        sesion.fecha_inicio = ahora

        sesion.fecha_expiracion = expiracion

        sesion.ultima_actividad = ahora

        sesion.activa = True

    # ======================================
    # CREAR SESIÓN
    # ======================================

    else:

        sesion = SesionUsuario(

            id_usuario=usuario.id_usuario,

            token=token,

            fecha_inicio=ahora,

            fecha_expiracion=expiracion,

            ultima_actividad=ahora,

            activa=True
        )

        db.add(sesion)

    db.commit()

    # ======================================
    # RESPONSE
    # ======================================

    return {

        "access_token":
            token,

        "token_type":
            "bearer"
    }