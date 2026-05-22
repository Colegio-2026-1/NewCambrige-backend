from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class TipoConcepto(Base):
    __tablename__ = "tipo_concepto"
    id_tipo = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)


class Matricula(Base):
    __tablename__ = "matricula"
    id_matricula = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    id_periodo = Column(Integer, ForeignKey("periodo_academico.id_periodo"), index=True)
    estado = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    detalles = relationship("DetalleMatricula", back_populates="matricula")


class DetalleMatricula(Base):
    __tablename__ = "detalle_matricula"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_matricula = Column(Integer, ForeignKey("matricula.id_matricula"))
    id_tipo = Column(Integer, ForeignKey("tipo_concepto.id_tipo"))
    #descripcion = Column(String(100))
    mes = Column(String(12))
    estado = Column(String(20), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    matricula = relationship("Matricula", back_populates="detalles")
    tipo = relationship("TipoConcepto")

