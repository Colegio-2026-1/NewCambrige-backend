from sqlalchemy.orm import Session
from typing import Optional, List

from app.modules.estudiantes.models import Estudiante
from app.modules.estudiantes.schemas import EstudianteCreate, EstudianteUpdate

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Estudiante]:
    return db.query(Estudiante).offset(skip).limit(limit).all()

def get_by_id(db: Session, estudiante_id: int) -> Optional[Estudiante]:
    return db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()

def create(db: Session, data: EstudianteCreate) -> Estudiante:
    nuevo = Estudiante(
        nombre=data.nombre,
        telefono_acudiente=data.telefono_acudiente,
        id_salon=data.id_salon
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update(db: Session, estudiante_id: int, data: EstudianteUpdate) -> Optional[Estudiante]:
    estudiante = get_by_id(db, estudiante_id)
    if not estudiante:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(estudiante, field, value)
    
    db.commit()
    db.refresh(estudiante)
    return estudiante

def delete(db: Session, estudiante_id: int) -> bool:
    estudiante = get_by_id(db, estudiante_id)
    if not estudiante:
        return False
    
    db.delete(estudiante)
    db.commit()
    return True