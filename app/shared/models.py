from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Auditoria(Base):
    __tablename__ = "auditoria"
    id_auditoria = Column(Integer, primary_key=True, index=True)
    tabla = Column(String(100))
    id_registro = Column(Integer)
    accion = Column(String(50))
    usuario = Column(String(100))
    fecha = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class PeriodoAcademico(Base):
    __tablename__ = "periodo_academico"
    id_periodo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(4), nullable=False)
    fecha_inicio = Column(TIMESTAMP, nullable=False)
    fecha_fin = Column(TIMESTAMP, nullable=False)
    activo = Column(Boolean, default=True)

