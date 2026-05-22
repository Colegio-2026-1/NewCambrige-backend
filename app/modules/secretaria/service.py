from sqlalchemy.orm import Session
from typing import Optional, List
from app.modules.tesoreria.models import Matricula, DetalleMatricula,TipoConcepto

# ============ MATRÍCULAS ============
def get_matriculas_all(db: Session, skip: int = 0, limit: int = 100) -> List[Matricula]:
    return db.query(Matricula).offset(skip).limit(limit).all()

def get_matricula_by_id(db: Session, matricula_id: int) -> Optional[Matricula]:
    return db.query(Matricula).filter(Matricula.id_matricula == matricula_id).first()

def get_matriculas_por_estudiante(db: Session, estudiante_id: int) -> List[Matricula]:
    return db.query(Matricula).filter(Matricula.id_estudiante == estudiante_id).all()

def get_matriculas_por_periodo(db: Session, periodo_id: int) -> List[Matricula]:
    return db.query(Matricula).filter(Matricula.id_periodo == periodo_id).all()

def get_matriculas_pendientes(db: Session) -> List[Matricula]:
    return db.query(Matricula).filter(Matricula.estado == "pendiente").all()

def create_matricula(db: Session, data: dict) -> Matricula:
    matricula = Matricula(**data)
    db.add(matricula)
    db.commit()
    db.refresh(matricula)
    return matricula

def update_matricula(db: Session, matricula_id: int, data: dict) -> Optional[Matricula]:
    matricula = get_matricula_by_id(db, matricula_id)
    if not matricula:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(matricula, key, value)
    db.commit()
    db.refresh(matricula)
    return matricula

def cancelar_matricula(db: Session, matricula_id: int) -> Optional[Matricula]:
    return update_matricula(db, matricula_id, {"estado": "cancelada"})

# ============ DETALLES DE MATRÍCULA ============
def get_detalles_by_matricula(db: Session, matricula_id: int) -> List[DetalleMatricula]:
    return db.query(DetalleMatricula).filter(DetalleMatricula.id_matricula == matricula_id).all()

def get_detalle_by_id(db: Session, detalle_id: int) -> Optional[DetalleMatricula]:
    return db.query(DetalleMatricula).filter(DetalleMatricula.id_detalle == detalle_id).first()

def create_detalle(db: Session, data: dict) -> DetalleMatricula:
    detalle = DetalleMatricula(**data)
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return detalle

def update_detalle(db: Session, detalle_id: int, data: dict) -> Optional[DetalleMatricula]:
    detalle = get_detalle_by_id(db, detalle_id)
    if not detalle:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(detalle, key, value)
    db.commit()
    db.refresh(detalle)
    return detalle

def delete_detalle(db: Session, detalle_id: int) -> bool:
    detalle = get_detalle_by_id(db, detalle_id)
    if not detalle:
        return False
    db.delete(detalle)
    db.commit()
    return True

# ============ TIPOS DE CONCEPTO ============
def get_tipos_all(db: Session, skip: int = 0, limit: int = 100) -> List[TipoConcepto]:
    return db.query(TipoConcepto).offset(skip).limit(limit).all()

def get_tipo_by_id(db: Session, tipo_id: int) -> Optional[TipoConcepto]:
    return db.query(TipoConcepto).filter(TipoConcepto.id_tipo == tipo_id).first()

def create_tipo(db: Session, data: dict) -> TipoConcepto:
    tipo = TipoConcepto(**data)
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo

def update_tipo(db: Session, tipo_id: int, data: dict) -> Optional[TipoConcepto]:
    tipo = get_tipo_by_id(db, tipo_id)
    if not tipo:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(tipo, key, value)
    db.commit()
    db.refresh(tipo)
    return tipo

def delete_tipo(db: Session, tipo_id: int) -> bool:
    tipo = get_tipo_by_id(db, tipo_id)
    if not tipo:
        return False
    db.delete(tipo)
    db.commit()
    return True