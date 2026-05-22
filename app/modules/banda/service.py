from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime, timedelta

from app.modules.banda.models import (
    Categoria, Ubicacion, InventarioInstrumento, PrestamoInstrumento
)
from app.modules.estudiantes.models import Estudiante

# ============ CATEGORÍAS ============
def get_categorias_all(db: Session, skip: int = 0, limit: int = 100) -> List[Categoria]:
    return db.query(Categoria).offset(skip).limit(limit).all()

def get_categoria_by_id(db: Session, categoria_id: int) -> Optional[Categoria]:
    return db.query(Categoria).filter(Categoria.id_categoria == categoria_id).first()

def get_categoria_by_nombre(db: Session, nombre: str) -> Optional[Categoria]:
    return db.query(Categoria).filter(Categoria.nombre == nombre).first()

def create_categoria(db: Session, data: dict) -> Categoria:
    nueva = Categoria(**data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def update_categoria(db: Session, categoria_id: int, data: dict) -> Optional[Categoria]:
    categoria = get_categoria_by_id(db, categoria_id)
    if not categoria:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(categoria, key, value)
    db.commit()
    db.refresh(categoria)
    return categoria

def delete_categoria(db: Session, categoria_id: int) -> bool:
    categoria = get_categoria_by_id(db, categoria_id)
    if not categoria:
        return False
    db.delete(categoria)
    db.commit()
    return True

# ============ UBICACIONES ============
def get_ubicaciones_all(db: Session, skip: int = 0, limit: int = 100) -> List[Ubicacion]:
    return db.query(Ubicacion).offset(skip).limit(limit).all()

def get_ubicacion_by_id(db: Session, ubicacion_id: int) -> Optional[Ubicacion]:
    return db.query(Ubicacion).filter(Ubicacion.id_ubicacion == ubicacion_id).first()

def create_ubicacion(db: Session, data: dict) -> Ubicacion:
    nueva = Ubicacion(**data)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def update_ubicacion(db: Session, ubicacion_id: int, data: dict) -> Optional[Ubicacion]:
    ubicacion = get_ubicacion_by_id(db, ubicacion_id)
    if not ubicacion:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(ubicacion, key, value)
    db.commit()
    db.refresh(ubicacion)
    return ubicacion

def delete_ubicacion(db: Session, ubicacion_id: int) -> bool:
    ubicacion = get_ubicacion_by_id(db, ubicacion_id)
    if not ubicacion:
        return False
    db.delete(ubicacion)
    db.commit()
    return True

# ============ INSTRUMENTOS ============
def get_instrumentos_all(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    solo_disponibles: bool = False,
    categoria_id: Optional[int] = None
) -> List[InventarioInstrumento]:
    query = db.query(InventarioInstrumento).options(
        joinedload(InventarioInstrumento.categoria),
        joinedload(InventarioInstrumento.ubicacion)
    )
    
    if solo_disponibles:
        query = query.filter(InventarioInstrumento.disponible == True)
    
    if categoria_id:
        query = query.filter(InventarioInstrumento.id_categoria == categoria_id)
    
    return query.offset(skip).limit(limit).all()

def get_instrumento_by_id(db: Session, instrumento_id: int) -> Optional[InventarioInstrumento]:
    return db.query(InventarioInstrumento).options(
        joinedload(InventarioInstrumento.categoria),
        joinedload(InventarioInstrumento.ubicacion)
    ).filter(InventarioInstrumento.id_instrumento == instrumento_id).first()

def create_instrumento(db: Session, data: dict) -> InventarioInstrumento:
    nuevo = InventarioInstrumento(**data)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update_instrumento(db: Session, instrumento_id: int, data: dict) -> Optional[InventarioInstrumento]:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(instrumento, key, value)
    db.commit()
    db.refresh(instrumento)
    return instrumento

def delete_instrumento(db: Session, instrumento_id: int) -> bool:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return False
    
    # Verificar si tiene préstamos activos
    prestamo_activo = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_instrumento == instrumento_id,
        PrestamoInstrumento.estado_entrega == "prestado"
    ).first()
    
    if prestamo_activo:
        raise ValueError("No se puede eliminar un instrumento con préstamos activos")
    
    db.delete(instrumento)
    db.commit()
    return True

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
def get_prestamos_all(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    solo_activos: bool = False,
    estudiante_id: Optional[int] = None
) -> List[PrestamoInstrumento]:
    query = db.query(PrestamoInstrumento).options(
        joinedload(PrestamoInstrumento.instrumento),
        joinedload(PrestamoInstrumento.estudiante)
    )
    
    if solo_activos:
        query = query.filter(PrestamoInstrumento.estado_entrega == "prestado")
    
    if estudiante_id:
        query = query.filter(PrestamoInstrumento.id_estudiante == estudiante_id)
    
    return query.order_by(PrestamoInstrumento.fecha_prestamo.desc()).offset(skip).limit(limit).all()

def get_prestamo_by_id(db: Session, prestamo_id: int) -> Optional[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).options(
        joinedload(PrestamoInstrumento.instrumento),
        joinedload(PrestamoInstrumento.estudiante)
    ).filter(PrestamoInstrumento.id_prestamo == prestamo_id).first()

def get_prestamos_activos_por_estudiante(db: Session, estudiante_id: int) -> List[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == estudiante_id,
        PrestamoInstrumento.estado_entrega == "prestado"
    ).all()

def create_prestamo(db: Session, data: dict) -> Optional[PrestamoInstrumento]:
    # Verificar que el instrumento existe y está disponible
    instrumento = get_instrumento_by_id(db, data["id_instrumento"])
    if not instrumento:
        return None
    
    if not instrumento.disponible:
        raise ValueError("El instrumento no está disponible para préstamo")
    
    # Verificar que el estudiante existe
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == data["id_estudiante"]).first()
    if not estudiante:
        return None
    
    # Crear préstamo
    prestamo = PrestamoInstrumento(
        id_instrumento=data["id_instrumento"],
        id_estudiante=data["id_estudiante"],
        fecha_prestamo=data["fecha_prestamo"],
        observacion=data.get("observacion"),
        estado_entrega="prestado"
    )
    
    # Marcar instrumento como no disponible
    instrumento.disponible = False
    
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return prestamo

def devolver_instrumento(db: Session, prestamo_id: int) -> Optional[PrestamoInstrumento]:
    prestamo = get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        return None
    
    if prestamo.estado_entrega != "prestado":
        raise ValueError("El instrumento ya fue devuelto")
    
    # Actualizar préstamo
    prestamo.estado_entrega = "devuelto"
    prestamo.fecha_devolucion = date.today()
    
    # Marcar instrumento como disponible nuevamente
    instrumento = get_instrumento_by_id(db, prestamo.id_instrumento)
    if instrumento:
        instrumento.disponible = True
    
    db.commit()
    db.refresh(prestamo)
    return prestamo

def update_prestamo(db: Session, prestamo_id: int, data: dict) -> Optional[PrestamoInstrumento]:
    prestamo = get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        return None
    
    for key, value in data.items():
        if value is not None:
            setattr(prestamo, key, value)
    
    db.commit()
    db.refresh(prestamo)
    return prestamo

def get_historial_instrumento(db: Session, instrumento_id: int) -> List[PrestamoInstrumento]:
    return db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_instrumento == instrumento_id
    ).order_by(PrestamoInstrumento.fecha_prestamo.desc()).all()

def get_estadisticas(db: Session) -> dict:
    total_instrumentos = db.query(InventarioInstrumento).count()
    disponibles = db.query(InventarioInstrumento).filter(InventarioInstrumento.disponible == True).count()
    prestamos_activos = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.estado_entrega == "prestado"
    ).count()
    
    prestamos_mes = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.fecha_prestamo >= date.today().replace(day=1)
    ).count()
    
    return {
        "total_instrumentos": total_instrumentos,
        "instrumentos_disponibles": disponibles,
        "instrumentos_prestados": total_instrumentos - disponibles,
        "prestamos_activos": prestamos_activos,
        "prestamos_este_mes": prestamos_mes
    }