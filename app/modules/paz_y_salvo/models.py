from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DirFirmas(Base):
    __tablename__ = "dir_firmas"

    id_dir_firma = Column(Integer, primary_key=True, index=True)
    #dir_secretaria = Column(String(255), nullable=True)
    #dir_rectoria   = Column(String(255), nullable=True)
    #dir_titular    = Column(String(255), nullable=True)
    #dir_banda      = Column(String(255), nullable=True)
    #dir_banda_pred = Column(String(255), nullable=True)
    #dir_tesoreria  = Column(String(255), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"))
    dir_user = Column(String(255), nullable=True)
    relationship("Usuario", back_populates="roles")
