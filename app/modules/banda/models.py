from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base

class Categoria(Base):
    __tablename__ = "categoria"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)

class Ubicacion(Base):
    __tablename__ = "ubicacion"
    id_ubicacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)

class InventarioInstrumento(Base):
    __tablename__ = "inventario_instrumento"
    id_instrumento = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"))
    id_ubicacion = Column(Integer, ForeignKey("ubicacion.id_ubicacion"))
    cantidad_total = Column(Integer, nullable=False, default=1)
    cantidad_disponible = Column(Integer, nullable=False, default=1)
    estado = Column(String(50), nullable=False, default="Activo")
    
    categoria = relationship("Categoria")
    ubicacion = relationship("Ubicacion")

class PrestamoInstrumento(Base):
    __tablename__ = "prestamo_instrumento"
    id_prestamo = Column(Integer, primary_key=True, index=True)
    id_instrumento = Column(Integer, ForeignKey("inventario_instrumento.id_instrumento"))
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    fecha_prestamo = Column(Date)
    fecha_devolucion = Column(Date, nullable=True)
    estado_entrega = Column(String(20))
    estado_al_devolver = Column(String(50), nullable=True)
    observacion = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    instrumento = relationship("InventarioInstrumento")
    estudiante = relationship("Estudiante")