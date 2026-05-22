from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.modules.uniformes.models import InventarioObjeto, PrestamoObjeto

def get_objetos_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(InventarioObjeto).offset(skip).limit(limit).all()

def get_objetos_disponibles(db: Session):
    return db.query(InventarioObjeto).filter(InventarioObjeto.cantidad_disponible > 0).all()

def get_objeto_by_id(db: Session, objeto_id: int):
    return db.query(InventarioObjeto).filter(InventarioObjeto.id_objeto == objeto_id).first()

def create_objeto(db: Session, data: dict):
    nuevo = InventarioObjeto(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update_objeto(db: Session, objeto_id: int, data: dict):
    objeto = get_objeto_by_id(db, objeto_id)
    if not objeto:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(objeto, key, value)
    db.commit()
    db.refresh(objeto)
    return objeto

def delete_objeto(db: Session, objeto_id: int):
    objeto = get_objeto_by_id(db, objeto_id)
    if not objeto:
        return False
    db.delete(objeto)
    db.commit()
    return True

def registrar_prestamo(db: Session, data: dict):
    objeto = get_objeto_by_id(db, data["id_objeto"])
    if not objeto or objeto.cantidad_disponible < data["cantidad_prestada"]:
        return None
    
    objeto.cantidad_disponible -= data["cantidad_prestada"]
    
    prestamo = PrestamoObjeto(**data, estado_entrega="prestado")
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return prestamo

def devolver_prestamo(db: Session, prestamo_id: int):
    prestamo = db.query(PrestamoObjeto).filter(PrestamoObjeto.id_prestamo == prestamo_id).first()
    if not prestamo or prestamo.estado_entrega != "prestado":
        return None
    
    objeto = get_objeto_by_id(db, prestamo.id_objeto)
    if objeto:
        objeto.cantidad_disponible += prestamo.cantidad_prestada
    
    prestamo.estado_entrega = "devuelto"
    prestamo.fecha_devolucion = date.today()
    db.commit()
    db.refresh(prestamo)
    return prestamo

def get_prestamos_activos(db: Session):
    return db.query(PrestamoObjeto).filter(PrestamoObjeto.estado_entrega == "prestado").all()