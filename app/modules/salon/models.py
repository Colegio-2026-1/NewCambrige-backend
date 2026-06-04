from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# ======================
#  SALON
# ======================
class Salon(Base):
    __tablename__ = "salon"

    id_salon = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"))
    grado = Column(String(10), nullable=False)
    grupo = Column(String(2), nullable=False)
    id_periodo = Column(Integer, ForeignKey("periodo_academico.id_periodo"))

    periodo = relationship("PeriodoAcademico")
    estudiantes = relationship("Estudiante", back_populates="salon")


# ======================
#  TIPO PRUEBA
# ======================
class TipoPrueba(Base):
    __tablename__ = "tipo_prueba"

    id_tipo_prueba = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    grado_min = Column(Integer)
    grado_max = Column(Integer)
    descripcion = Column(String(150))


# ======================
#  PRUEBA (PAGO)
# ======================
class Prueba(Base):
    __tablename__ = "prueba"

    id_prueba = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    id_tipo_prueba = Column(Integer, ForeignKey("tipo_prueba.id_tipo_prueba"))

   
    estado = Column(String(20), nullable=True)

    fecha_pago = Column(Date, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    estudiante = relationship("Estudiante")
    tipo_prueba = relationship("TipoPrueba")


# ======================
#  PUPITRE (APROBADO / NO APROBADO)
# ======================
class Pupitre(Base):
    __tablename__ = "pupitres"

    id_mantenimiento = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))

    # BOOLEAN CORRECTO
    estado = Column(String(20), nullable=True)
    fecha_pago = Column(Date, nullable=True)  #  NUEVO CAMPO
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    estudiante = relationship("Estudiante")


# ======================
#  INVENTARIO LIBRO
# ======================
class InventarioLibro(Base):
    __tablename__ = "inventario_libro"

    id_libro = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    autor = Column(String(100), nullable=False)
    edicion = Column(String(50))
    estado_fisico = Column(String(100))

    id_salon = Column(Integer, ForeignKey("salon.id_salon"))

    # BOOLEAN OK
    disponible = Column(Boolean, default=True, nullable=False)


# ======================
# PRESTAMO LIBRO
# ======================
class PrestamoLibro(Base):
    __tablename__ = "prestamo_libro"

    id_prestamo = Column(Integer, primary_key=True, index=True)
    id_libro = Column(Integer, ForeignKey("inventario_libro.id_libro"))
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))

    fecha_prestamo = Column(Date)
    fecha_devolucion = Column(Date)

    # STRING CORRECTO (BUENO/MALO/REGULAR o ACTIVO/DEVUELTO)
    estado = Column(String(20), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    estudiante = relationship("Estudiante")
    libro = relationship("InventarioLibro")