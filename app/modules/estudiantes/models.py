from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Estudiante(Base):
    __tablename__ = "estudiante"
    id_estudiante = Column(Integer, primary_key=True, index=True)
    documento = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    telefono_acudiente = Column(String(20))
    id_salon = Column(Integer, ForeignKey("salon.id_salon"), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    salon = relationship("Salon", back_populates="estudiantes")


class EstudianteBanda(Base):
    __tablename__ = "estudiante_banda"
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"), primary_key=True)
    activo = Column(Boolean, default=True)
    estudiante = relationship("Estudiante")
