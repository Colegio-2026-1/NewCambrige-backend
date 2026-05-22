from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    TIMESTAMP
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# ==========================================
# SESIONES DE USUARIO
# ==========================================

class SesionUsuario(Base):

    __tablename__ = "sesion_usuario"

    # ==============================
    # ID
    # ==============================

    id_sesion = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ==============================
    # USUARIO
    # ==============================

    id_usuario = Column(
        Integer,
        ForeignKey(
            "usuario.id_usuario",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # ==============================
    # TOKEN JWT
    # ==============================

    token = Column(
        String(500),
        nullable=False,
        unique=True
    )

    # ==============================
    # FECHA LOGIN
    # ==============================

    fecha_inicio = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    # ==============================
    # EXPIRACIÓN TOTAL
    # ==============================

    fecha_expiracion = Column(
        TIMESTAMP,
        nullable=False
    )

    # ==============================
    # ÚLTIMA ACTIVIDAD
    # ==============================

    ultima_actividad = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    # ==============================
    # SESIÓN ACTIVA
    # ==============================

    activa = Column(
        Boolean,
        default=True,
        nullable=False
    )

    # ==============================
    # RELACIÓN
    # ==============================

    usuario = relationship(
        "Usuario",
        back_populates="sesiones"
    )


# ==========================================
# INTENTOS DE LOGIN
# ==========================================

class LoginAttempt(Base):

    __tablename__ = "login_attempt"

    # ==============================
    # ID
    # ==============================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ==============================
    # USUARIO
    # ==============================

    username = Column(
        String(100),
        nullable=False,
        unique=True
    )

    # ==============================
    # INTENTOS FALLIDOS
    # ==============================

    intentos = Column(
        Integer,
        default=0,
        nullable=False
    )

    # ==============================
    # BLOQUEO TEMPORAL
    # ==============================

    bloqueado_hasta = Column(
        TIMESTAMP,
        nullable=True
    )

    # ==============================
    # ÚLTIMO INTENTO
    # ==============================

    ultimo_intento = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )