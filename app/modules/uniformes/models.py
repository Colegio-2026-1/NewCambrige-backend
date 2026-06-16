from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TIMESTAMP,Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class InventarioObjeto(Base):
    __tablename__ = "inventario_objeto"

    id_objeto = Column(Integer, primary_key=True)

    nombre = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=True)

    cantidad_total = Column(Integer, default=0)
    cantidad_disponible = Column(Integer, default=0)

    estado_fisico = Column(String(20), nullable=True)

    talla = Column(String(10), nullable=True)
    observacion = Column(String, nullable=True)
    fecha_registro = Column(Date, nullable=True)


    prestamos = relationship(
        "PrestamoObjeto",
        back_populates="objeto"
    )


class PrestamoObjeto(Base):
    __tablename__ = "prestamo_objeto"

    id_prestamo = Column(Integer, primary_key=True, index=True)
    id_objeto = Column(
        Integer,
        ForeignKey("inventario_objeto.id_objeto"),
        nullable=False
    )
    id_estudiante = Column(
        Integer,
        ForeignKey("estudiante.id_estudiante"),
        nullable=False
    )

    
    fecha_prestamo = Column(DateTime, nullable=True)
    fecha_devolucion = Column(DateTime, nullable=True)
    estado_prestamo = Column(
        String(20),
        nullable=False,
        default="prestado")

    estado_entrega = Column(String(20), nullable=True)
    estado_devolucion = Column(String(20), nullable=True)
    observacion = Column(String, nullable=True)
    talla = Column(String(10), nullable=True)
    cantidad_prestada = Column(Integer, default=1)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    
    objeto = relationship("InventarioObjeto", back_populates="prestamos")
    estudiante = relationship("Estudiante")