from sqlalchemy import Column, Integer, String, Date, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class InventarioObjeto(Base):
    __tablename__ = "inventario_objeto"
    id_objeto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(20))   # uniforme | balon | otro
    cantidad_total = Column(Integer)
    cantidad_disponible = Column(Integer)


class PrestamoObjeto(Base):
    __tablename__ = "prestamo_objeto"
    id_prestamo = Column(Integer, primary_key=True, index=True)
    id_objeto = Column(Integer, ForeignKey("inventario_objeto.id_objeto"))
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    fecha_prestamo = Column(Date)
    fecha_devolucion = Column(Date)
    estado_entrega = Column(String(20))
    talla = Column(String(10))
    cantidad_prestada = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    objeto = relationship("InventarioObjeto")
    estudiante = relationship("Estudiante")
