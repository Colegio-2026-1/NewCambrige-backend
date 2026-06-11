from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class FirmasPazYSalvo(Base):
    __tablename__ = "firmas_paz_y_salvo"
    id_firma = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"), nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodo_academico.id_periodo"), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    estudiante = relationship("Estudiante")
    periodo = relationship("PeriodoAcademico")
    detalles = relationship("DetalleFirmaPazYSalvo", back_populates="firma", cascade="all, delete-orphan")


class TipoFirma(Base):
    __tablename__ = "tipo_firma"
    id_tipo_firma = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    #descripcion = Column(String(255), nullable=True) #no se necesita por ahora :v


class DetalleFirmaPazYSalvo(Base):
    __tablename__ = "detalle_firma_paz_y_salvo"
    id_detalle = Column(Integer, primary_key=True, index=True)
    id_firma = Column(Integer, ForeignKey("firmas_paz_y_salvo.id_firma"), nullable=False)
    id_tipo_firma = Column(Integer, ForeignKey("tipo_firma.id_tipo_firma"), nullable=False)
    id_usuario_firmante = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    estado = Column(Boolean, default=False)
    observacion = Column(String(255), nullable=True)
    fecha_firma = Column(TIMESTAMP(timezone=True), server_default=func.now())
    firma = relationship("FirmasPazYSalvo", back_populates="detalles")
    tipo_firma = relationship("TipoFirma")
    usuario_firmante = relationship("Usuario")

class ResponsableFirma(Base):
    __tablename__ = "responsable_firma"
    id_responsable = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_tipo_firma = Column(Integer, ForeignKey("tipo_firma.id_tipo_firma"), nullable=False)
    ruta_firma = Column(String(255), nullable=True)
    #activo = Column(Boolean, default=True)
    #updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    usuario = relationship("Usuario")
    tipo_firma = relationship("TipoFirma")