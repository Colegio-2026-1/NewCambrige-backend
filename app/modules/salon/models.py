from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,Date, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Salon(Base):
    __tablename__ = "salon"
    id_salon = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"))
    grado = Column(Integer, nullable=False)
    grupo = Column(Integer, nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodo_academico.id_periodo"))
    periodo = relationship("PeriodoAcademico")
    estudiantes = relationship("Estudiante", back_populates="salon")

class TipoPrueba(Base):
    __tablename__ = "tipo_prueba"
    id_tipo_prueba = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    grado_min = Column(Integer)
    grado_max = Column(Integer)


class Prueba(Base):
    __tablename__ = "prueba"
    id_prueba = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    id_tipo_prueba = Column(Integer, ForeignKey("tipo_prueba.id_tipo_prueba"))
    estado = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    estudiante = relationship("Estudiante")
    tipo_prueba = relationship("TipoPrueba")


class Pupitre(Base):
    __tablename__ = "pupitres"
    id_mantenimiento = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    estado = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class InventarioLibro(Base):
    __tablename__ = "inventario_libro"
    id_libro = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    autor = Column(String(100), nullable=False)
    id_salon = Column(Integer, ForeignKey("salon.id_salon"))
    disponible = Column(Boolean, default=True)


class PrestamoLibro(Base):
    __tablename__ = "prestamo_libro"
    id_prestamo = Column(Integer, primary_key=True, index=True)
    id_libro = Column(Integer, ForeignKey("inventario_libro.id_libro"))
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    fecha_prestamo = Column(Date)
    fecha_devolucion = Column(Date)
    estado = Column(Boolean)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
