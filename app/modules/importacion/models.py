from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class EjecucionBot(Base):
    __tablename__ = "ejecuciones_bot"
    id = Column(Integer, primary_key=True, index=True)
    fecha_inicio = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fecha_fin = Column(TIMESTAMP(timezone=True), nullable=True)
    estado = Column(String(50), nullable=False) # iniciado, completado, error, interrumpido
    registros_estudiantes = Column(Integer, default=0)
    registros_docentes = Column(Integer, default=0)
    errores = Column(Integer, default=0)
    usuario_id = Column(Integer, nullable=True)
    tipo_ejecucion = Column(String(50), nullable=False) # scraping, masiva, individual

    staging_estudiantes = relationship("StagingEstudiante", back_populates="ejecucion")
    staging_docentes = relationship("StagingDocente", back_populates="ejecucion")


class StagingEstudiante(Base):
    __tablename__ = "staging_estudiantes"
    id = Column(Integer, primary_key=True, index=True)
    ejecucion_id = Column(Integer, ForeignKey("ejecuciones_bot.id"), nullable=False)
    documento = Column(String(100), nullable=True, index=True)
    nombre = Column(String(255), nullable=True)
    grado = Column(String(100), nullable=True)
    curso = Column(String(100), nullable=True)
    jornada = Column(String(100), nullable=True)
    estado_validacion = Column(String(50), default="Pendiente")
    observaciones = Column(String, nullable=True)
    fecha_carga = Column(TIMESTAMP(timezone=True), server_default=func.now())
    id_salon = Column(Integer, ForeignKey("salon.id_salon"), nullable=True)

    ejecucion = relationship("EjecucionBot", back_populates="staging_estudiantes")


class StagingDocente(Base):
    __tablename__ = "staging_docentes"
    id = Column(Integer, primary_key=True, index=True)
    ejecucion_id = Column(Integer, ForeignKey("ejecuciones_bot.id"), nullable=False)
    documento = Column(String(100), nullable=True, index=True)
    nombre = Column(String(255), nullable=True)
    grado_titular = Column(String(100), nullable=True)
    curso_titular = Column(String(100), nullable=True)
    estado_validacion = Column(String(50), default="Pendiente")
    observaciones = Column(String, nullable=True)
    fecha_carga = Column(TIMESTAMP(timezone=True), server_default=func.now())

    ejecucion = relationship("EjecucionBot", back_populates="staging_docentes")

