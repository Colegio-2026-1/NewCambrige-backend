from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Rol(Base):
    __tablename__ = "rol"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)
    usuarios = relationship("RolUsuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    documento = Column(String(10), nullable=False)
    #correo = Column(String(150), nullable=False, unique=True)
    estado = Column(Boolean, default=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    roles = relationship("RolUsuario", back_populates="usuario")
    sesiones = relationship("SesionUsuario", back_populates="usuario")


class RolUsuario(Base):
    __tablename__ = "rol_usuario"
    id_rol = Column(Integer, ForeignKey("rol.id_rol"), primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), primary_key=True)
    rol = relationship("Rol", back_populates="usuarios")
    usuario = relationship("Usuario", back_populates="roles")
