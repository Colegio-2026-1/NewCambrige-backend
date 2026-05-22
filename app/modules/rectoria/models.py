from sqlalchemy import Column, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class FirmasPazYSalvo(Base):
    __tablename__ = "firmas_paz_y_salvo"
    id_firma = Column(Integer, primary_key=True, index=True)
    id_estudiante = Column(Integer, ForeignKey("estudiante.id_estudiante"))
    id_periodo = Column(Integer, ForeignKey("periodo_academico.id_periodo"))
    biblioteca = Column(Boolean, default=False)
    prueba = Column(Boolean, default=False)
    pupitre = Column(Boolean, default=False)
    tesoreria = Column(Boolean, default=False)
    inventario = Column(Boolean, default=False)
    uniforme = Column(Boolean, default=False) #se llama uniforme pero es OTROS
    rectoria = Column(Boolean, default=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    estudiante = relationship("Estudiante")
    periodo = relationship("PeriodoAcademico")
