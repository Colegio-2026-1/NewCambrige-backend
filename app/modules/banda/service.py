from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime

from app.shared.models import Auditoria
from app.modules.banda.models import (
    Categoria, InventarioInstrumento, PrestamoInstrumento
)
from app.modules.estudiantes.models import Estudiante, EstudianteBanda

# ============ AUDITORÍA ============
def registrar_auditoria_central(db: Session, current_user, tabla: str, id_reg: int, accion_msg: str):
    """
    Registra en la tabla 'auditoria' central del proyecto.
    """
    nom_usr = getattr(current_user, 'nombre', 'Sistema')
    
    mensaje_seguro = str(accion_msg)[:50]
    
    log = Auditoria(
        tabla=tabla,
        id_registro=id_reg,
        accion=mensaje_seguro,
        usuario=nom_usr
    )
    db.add(log)
    
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

#======= estudiantes salon ========

def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Estudiante).options(
        joinedload(Estudiante.salon)
    ).offset(skip).limit(limit).all()
    
def get_estudiantes_banda(db: Session):
    """
    Obtiene todos los estudiantes que pertenecen a la banda y están activos.
    """
    return (
        db.query(Estudiante)
        .join(EstudianteBanda, Estudiante.id_estudiante == EstudianteBanda.id_estudiante)
        .filter(EstudianteBanda.activo == True)
        .all()
    )

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
    )
    
    if solo_disponibles:
        query = query.filter(InventarioInstrumento.cantidad_disponible > 0, InventarioInstrumento.estado == "Activo")
    
    if categoria_id:
        query = query.filter(InventarioInstrumento.id_categoria == categoria_id)
    
    return query.offset(skip).limit(limit).all()

def get_instrumento_by_id(db: Session, instrumento_id: int) -> Optional[InventarioInstrumento]:
    return db.query(InventarioInstrumento).options(
        joinedload(InventarioInstrumento.categoria),
    ).filter(InventarioInstrumento.id_instrumento == instrumento_id).first() 

def create_instrumento(db: Session, data: dict, current_user) -> InventarioInstrumento:
    data["cantidad_disponible"] = data["cantidad_total"]
    nuevo = InventarioInstrumento(**data)
    db.add(nuevo)
    db.flush() 
    
    registrar_auditoria_central(
        db, current_user, "inventario_instrumento", nuevo.id_instrumento,
        f"REGISTRO: {nuevo.nombre}")
    db.commit()
    db.refresh(nuevo)
    return nuevo

def update_instrumento(db: Session, instrumento_id: int, data: dict, current_user) -> Optional[InventarioInstrumento]:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return None

    if "cantidad_total" in data and data["cantidad_total"] is not None:
        nuevo_total = int(data["cantidad_total"])
        prestados = (
            instrumento.cantidad_total
            - instrumento.cantidad_disponible
        )
        if nuevo_total < prestados:
            raise ValueError(
                f"No puede reducir la cantidad total a {nuevo_total}. "
                f"Actualmente hay {prestados} instrumentos prestados."
            )
        instrumento.cantidad_disponible = (
            nuevo_total - prestados
        )
        instrumento.cantidad_total = nuevo_total
        
        if "estado" in data:
            nuevo_estado = data["estado"]
            if (
                nuevo_estado == "Activo"
                and instrumento.estado == "En mantenimiento"
                ):
                if instrumento.cantidad_disponible < instrumento.cantidad_total:
                    instrumento.cantidad_disponible += 1
        elif (
            nuevo_estado == "En mantenimiento"
            and instrumento.estado == "Activo"
        ):
            if instrumento.cantidad_disponible > 0:
                instrumento.cantidad_disponible -= 1
                
    for key, value in data.items():
        if key == "cantidad_total":
            continue
        if value is not None and key not in [
            "id_instrumento",
            "id_inventario"
        ]:
            setattr(instrumento, key, value)
    registrar_auditoria_central(
        db,
        current_user,
        "inventario_instrumento",
        instrumento.id_instrumento,
        f"EDIT: {instrumento.nombre}"
    )
    db.commit()
    db.refresh(instrumento)
    return instrumento

def delete_instrumento(db: Session, instrumento_id: int, current_user) -> bool:
    instrumento = get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        return False
    
    tiene_historial = db.query(PrestamoInstrumento).filter(PrestamoInstrumento.id_instrumento == instrumento_id).first()
    if tiene_historial:
        raise ValueError("No es posible eliminar este instrumento. Tiene historial de préstamos vincuados.")
    
    if instrumento.cantidad_disponible < instrumento.cantidad_total:
        raise ValueError("No es posible eliminar este instrumento. Tiene asignaciones activas.")
    
    registrar_auditoria_central(db, current_user, "inventario_instrumento", instrumento_id,
                                f"ELIMINACIÓN: {instrumento.nombre}")
    
    db.delete(instrumento)
    db.commit()
    return True

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
def get_prestamos_all(db: Session, skip: int = 0, limit: int = 100, solo_activos: bool = False, estudiante_id: Optional[int] = None) -> List[dict]:
    query = db.query(PrestamoInstrumento).options(
        joinedload(PrestamoInstrumento.instrumento),
        joinedload(PrestamoInstrumento.estudiante).joinedload(Estudiante.salon) 
    )
    
    if solo_activos:
        query = query.filter(PrestamoInstrumento.estado_entrega == "prestado")
    
    prestamos = query.order_by(PrestamoInstrumento.fecha_prestamo.desc()).offset(skip).limit(limit).all()
    
    resultado = []
    for p in prestamos:
        resultado.append({
            "id_prestamo": p.id_prestamo,
            "id_instrumento": p.id_instrumento,
            "id_estudiante": p.id_estudiante,
            "fecha_prestamo": p.fecha_prestamo,
            "fecha_devolucion": p.fecha_devolucion,
            "estado_entrega": p.estado_entrega,
            "estado_al_devolver": p.estado_al_devolver,
            "observacion": p.observacion,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "instrumento_nombre": p.instrumento.nombre if p.instrumento else "N/A",
            "estudiante_nombre": p.estudiante.nombre if p.estudiante else "N/A",
            "estudiante_documento": p.estudiante.documento if p.estudiante else "N/A",
            "estudiante_grado": p.estudiante.salon.grado if p.estudiante and p.estudiante.salon else "N/A",
            "estudiante_grupo": p.estudiante.salon.grupo if p.estudiante and p.estudiante.salon else "N/A",
        })
    return resultado

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

def create_prestamo(db: Session, data: dict, current_user) -> Optional[PrestamoInstrumento]:
    instrumento = get_instrumento_by_id(db, data["id_instrumento"])
    if not instrumento:
        return None
    
    if instrumento.cantidad_disponible <= 0 or instrumento.estado != "Activo":
        raise ValueError("No hay instrumentos disponibles para asignar.")
    
    prestamo_activo = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == data["id_estudiante"],
        PrestamoInstrumento.estado_entrega == "prestado"
    ).first()
    
    if prestamo_activo:
        raise ValueError("El estudiante ya tiene un instrumento asignado. Debe registrar la devolución antes de asignar uno nuevo.")
    
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == data["id_estudiante"]).first()
    if not estudiante:
        return None
    
    prestamo = PrestamoInstrumento(
        id_instrumento=data["id_instrumento"],
        id_estudiante=data["id_estudiante"],
        fecha_prestamo=datetime.now(),
        observacion=data.get("observacion"),
        estado_entrega="prestado"
    )
    
    instrumento.cantidad_disponible -= 1
    
    db.add(prestamo)
    db.flush()
    registrar_auditoria_central(db, current_user, "prestamo_instrumento", prestamo.id_prestamo,
                                f"ASIGNACIÓN: {instrumento.nombre}")
    db.commit()
    db.refresh(prestamo)
    return prestamo

def devolver_instrumento(db: Session, prestamo_id: int, data: dict, current_user) -> Optional[PrestamoInstrumento]:
    prestamo = get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        return None
    
    if prestamo.estado_entrega == "devuelto":
        return prestamo
        
    estado_devolucion = data.get("estado_al_devolver")
    observaciones = data.get("observaciones")
    
    if estado_devolucion == "Malo" and not observaciones:
        raise ValueError("Debe describir el daño del instrumento en las observaciones.")
    
    estado_recibido = str(data.get("estado_al_devolver", "Bueno")).strip().capitalize()

    prestamo.estado_entrega = "devuelto"
    prestamo.estado_al_devolver = data.get("estado_al_devolver")
    prestamo.observacion = data.get("observaciones") or prestamo.observacion
    prestamo.fecha_devolucion = datetime.now() 
    
    instrumento = get_instrumento_by_id(db, prestamo.id_instrumento)
    if instrumento:
        if estado_devolucion == "Bueno":
            instrumento.cantidad_disponible += 1
        else:
            instrumento.estado = "En mantenimiento"
            
              
    registrar_auditoria_central(db, current_user, "prestamo_instrumento", prestamo_id,
                                f"DEVOLUCIÓN: {instrumento.nombre}")
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
    total_instrumentos = db.query(func.sum(InventarioInstrumento.cantidad_total)).scalar() or 0
    disponibles = db.query(func.sum(InventarioInstrumento.cantidad_disponible)).scalar() or 0
    prestamos_activos = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.estado_entrega == "prestado"
    ).count()
    
    return {
        "total_instrumentos": total_instrumentos,
        "instrumentos_disponibles": disponibles,
        "instrumentos_prestados": total_instrumentos - disponibles,
        "prestamos_activos": prestamos_activos
    }