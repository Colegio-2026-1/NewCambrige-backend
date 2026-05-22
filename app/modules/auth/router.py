from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verificar_token
from app.modules.usuarios.models import Usuario
from app.modules.auth.models import SesionUsuario
from app.modules.auth import service
from app.modules.auth.schemas import TokenResponse, UsuarioResponse, UsuarioCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
""" si vamos a usar OAuth2 en Swagger
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    scopes={
        "admin": "Acceso total",
        "docente": "Acceso docente",
        "estudiante": "Acceso estudiante"
    }
)")
"""

@router.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = service.autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return service.generar_token(db, usuario)

@router.get("/me", response_model=UsuarioResponse)
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    # valideishon en BD la sesion
    sesion = db.query(SesionUsuario).filter(
        SesionUsuario.token == token,
        SesionUsuario.activa == True
    ).first()

    if not sesion:
        raise HTTPException(status_code=401, detail="Sesión inválida o cerrada")

    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == int(payload["sub"])
    ).first()

    return usuario

@router.post("/register", response_model=UsuarioResponse)
def register(data: UsuarioCreate, db: Session = Depends(get_db)):

    usuario = service.crear_usuario(
        db,
        data.nombre,
        data.password,
        data.roles if hasattr(data, "roles") else None
    )

    if not usuario:
        raise HTTPException(status_code=400, detail="El nombre ya está registrado")

    return usuario

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    sesion = db.query(SesionUsuario).filter(
        SesionUsuario.token == token,
        SesionUsuario.activa == True
    ).first()

    if not sesion:
        raise HTTPException(status_code=401, detail="sesion no encontrada")

    sesion.activa = False
    db.commit()

    return {"message": "sesion cerrada correctamente"}

@router.get("/check-session")
def check_session(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verificar_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    sesion = db.query(SesionUsuario).filter(
        SesionUsuario.token == token,
        SesionUsuario.activa == True
    ).first()

    if not sesion:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida"
        )

    ahora = datetime.utcnow()

    #cambiar fuera de fase de producción
    limite = ahora - timedelta(minutes=1)

    # VERIFICAR INACTIVIDAD
    if sesion.ultima_actividad < limite:

        sesion.activa = False
        db.commit()

        raise HTTPException(
            status_code=401,
            detail="Sesión expirada por inactividad"
        )

    # IMPORTANTE:
    # NO actualizar ultima_actividad

    print("AHORA:", ahora)
    print("ULTIMA:", sesion.ultima_actividad)
    print("LIMITE:", limite)

    return {
        "ok": True
    }