from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.salon.models import Salon

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).offset(skip).limit(limit).all()

def get_by_id(db: Session, salon_id: int) -> Optional[Salon]:
    return db.query(Salon).filter(Salon.id_salon == salon_id).first()

def get_by_grado_grupo(db: Session, grado: int, grupo: int) -> List[Salon]:
    return db.query(Salon).filter(Salon.grado == grado, Salon.grupo == grupo).all()

def create(db: Session, data: dict) -> Salon:
    nuevo = Salon(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update(db: Session, salon_id: int, data: dict) -> Optional[Salon]:
    salon = get_by_id(db, salon_id)
    if not salon:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(salon, key, value)
    db.commit()
    db.refresh(salon)
    return salon

def delete(db: Session, salon_id: int) -> bool:
    salon = get_by_id(db, salon_id)
    if not salon:
        return False
    db.delete(salon)
    db.commit()
    return True