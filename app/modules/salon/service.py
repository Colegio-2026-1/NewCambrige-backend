from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.shared.models import Auditoria
from typing import List, Optional
from datetime import date
from app.modules.salon.models import (
    Salon, Prueba, TipoPrueba, Pupitre, InventarioLibro, PrestamoLibro
)
from app.modules.estudiantes.models import Estudiante

# ======================
# 🏫 SALONES
# ======================
def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).offset(skip).limit(limit).all()

def get_salon_all_by_periodo(db: Session, id_periodo: int, skip: int = 0, limit: int = 100) -> List[Salon]:
    return db.query(Salon).filter(Salon.id_periodo == id_periodo).offset(skip).limit(limit).all()


def get_by_id(db: Session, salon_id: int) -> Optional[Salon]:
    return db.query(Salon).filter(Salon.id_salon == salon_id).first()

def get_by_grado_grupo(db: Session, grado: int, grupo: int) -> List[Salon]:
    return db.query(Salon).filter(Salon.grado == grado, Salon.grupo == grupo).all()

def get_by_titular(db: Session, current_user) -> List[Salon]:
    return db.query(Salon).filter(Salon.id_usuario == current_user.id_usuario).all()

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


# ======================
# 🧪 PRUEBAS
# ======================
def get_all_pruebas(db: Session) -> list:
    pruebas = (
        db.query(Prueba)
        .options(
            joinedload(Prueba.estudiante).joinedload(Estudiante.salon),
            joinedload(Prueba.tipo_prueba)
        )
        .all()
    )

    resultado = []

    for p in pruebas:
        e = p.estudiante
        salon = e.salon if e else None

        resultado.append({
            "id": p.id_prueba,
            "id_prueba": p.id_prueba,
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "tipo_prueba": (
                p.tipo_prueba.nombre
                if p.tipo_prueba else None
            ),
            "estado": p.estado,

            # SOLO mostrar fecha si está pagado
            "fecha_pago": (
                p.fecha_pago.strftime("%d/%m/%Y")
                if p.estado == "visto" and p.fecha_pago
                else None
            ),
        })

    return resultado


def create_prueba(db: Session, data: dict) -> Prueba:
    nueva = Prueba(**data)

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    return nueva


def update_estado_prueba(
    db: Session,
    prueba_id: int,
    estado: str
) -> Optional[Prueba]:

    prueba = db.query(Prueba).filter(
        Prueba.id_prueba == prueba_id
    ).first()

    if not prueba:
        return None

    prueba.estado = estado

    # FECHA AUTOMÁTICA
    if estado == "visto":
        prueba.fecha_pago = date.today()

    db.commit()
    db.refresh(prueba)

    return prueba

# ======================
# 🪑 PUPITRES
# ======================
def get_all_pupitres(db: Session) -> list:
    pupitres = (
        db.query(Pupitre)
        .options(
            joinedload(Pupitre.estudiante).joinedload(Estudiante.salon),
        )
        .all()
    )

    resultado = []

    for p in pupitres:
        e = p.estudiante
        salon = e.salon if e else None

        resultado.append({
            "id_mantenimiento": p.id_mantenimiento,
            "id_estudiante": p.id_estudiante,
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "estado": p.estado,
            "fecha_pago": (
                p.fecha_pago.strftime("%d/%m/%Y")
                if p.estado == "visto" and p.fecha_pago  #  Cambio: "visto" en lugar de "PAGADO"
                else None
            ),
        })

    return resultado


def update_pupitre(db: Session, pupitre_id: int, estado: str, fecha_pago: Optional[date] = None) -> Optional[Pupitre]:
    pupitre = db.query(Pupitre).filter(
        Pupitre.id_mantenimiento == pupitre_id
    ).first()

    if not pupitre:
        return None

    pupitre.estado = estado
    
    if fecha_pago:  # Ahora recibe el parámetro
        pupitre.fecha_pago = fecha_pago

    db.commit()
    db.refresh(pupitre)
    return pupitre


# ======================
# 📚 BIBLIOTECA
# ======================
def get_all_libros(db: Session):
    libros = db.query(InventarioLibro).all()

    return [
        {
            "id_libro": l.id_libro,
            "nombre": l.nombre,
            "autor": l.autor,
            "id_salon": l.id_salon,
            "disponible": l.disponible,
            "edicion": l.edicion,
            "estado_fisico": l.estado_fisico,
        }
        for l in libros
    ]


def get_all_prestamos(db: Session) -> list:
    prestamos = (
        db.query(PrestamoLibro)
        .options(
            joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
            joinedload(PrestamoLibro.libro)
        )
        .all()
    )

    resultado = []

    for p in prestamos:
        e = p.estudiante
        salon = e.salon if e else None

        resultado.append({
            "id_prestamo": p.id_prestamo,
            "codigo": e.documento if e else None,
            "nombre": e.nombre if e else None,
            "grado": str(salon.grado) if salon else None,
            "grupo": str(salon.grupo) if salon else None,
            "libro": p.libro.nombre if p.libro else None,
            "fecha_prestamo": str(p.fecha_prestamo) if p.fecha_prestamo else None,
            "fecha_devolucion": str(p.fecha_devolucion) if p.fecha_devolucion else None,
            "estado": p.estado,
        })

    return resultado


def create_libro(db: Session, data: dict) -> InventarioLibro:
    libro = InventarioLibro(**data)
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return libro


def update_libro(db: Session, libro_id: int, data: dict) -> Optional[InventarioLibro]:
    libro = db.query(InventarioLibro).filter(
        InventarioLibro.id_libro == libro_id
    ).first()

    if not libro:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(libro, key, value)

    db.commit()
    db.refresh(libro)
    return libro


def delete_libro(db: Session, libro_id: int) -> bool:

    libro = db.query(InventarioLibro).filter(
        InventarioLibro.id_libro == libro_id
    ).first()

    if not libro:
        return False

    # VALIDAR SI ESTÁ PRESTADO
    if libro.disponible == False:
        raise Exception(
            "No es posible eliminar un libro con préstamo activo."
        )

    # BORRADO LÓGICO
    if "(Eliminado del Inventario)" not in libro.nombre:
        libro.nombre = (
            f"{libro.nombre} (Eliminado del Inventario)"
        )

    db.commit()

    return True

def create_prestamo(db: Session, data: dict) -> dict:
    # 1. Buscar estudiante por código
    estudiante = db.query(Estudiante).filter(
        Estudiante.documento == str(data.get("codigo"))
    ).first()
    if not estudiante:
        raise Exception(f"Estudiante con código {data.get('codigo')} no encontrado.")

    # 2. Buscar libro por nombre
    libro = db.query(InventarioLibro).filter(
        InventarioLibro.nombre.ilike(data.get("libro"))
    ).first()
    if not libro:
        raise Exception(f"Libro '{data.get('libro')}' no encontrado en inventario.")
    if not libro.disponible:
        raise Exception(f"El libro '{libro.nombre}' no está disponible.")

    # ✅ VALIDACIÓN 1: libro en mal estado no se puede prestar
    if libro.estado_fisico == "Malo":
        raise Exception(f"El libro '{libro.nombre}' está en mal estado y no puede prestarse hasta ser revisado.")

    # ✅ VALIDACIÓN 2: límite de 3 libros prestados por estudiante
    prestamos_activos = db.query(PrestamoLibro).filter(
        PrestamoLibro.id_estudiante == estudiante.id_estudiante,
        PrestamoLibro.estado == "Prestado"
    ).count()
    if prestamos_activos >= 3:
        raise Exception(f"El estudiante ya tiene 3 libros prestados. Debe devolver uno antes de solicitar otro.")

    # 3. Actualizar libro
    libro.disponible    = False
    libro.estado_fisico = data.get("estado_fisico", "Excelente")

    # 4. Crear el préstamo
    prestamo = PrestamoLibro(
        id_estudiante    = estudiante.id_estudiante,
        id_libro         = libro.id_libro,
        fecha_prestamo   = date.today(),
        fecha_devolucion = data.get("fecha_devolucion"),
        estado           = "Prestado",
    )
    db.add(prestamo)
    db.commit()

    # 5. Re-query con relaciones
    prestamo = db.query(PrestamoLibro).options(
        joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
        joinedload(PrestamoLibro.libro)
    ).filter(PrestamoLibro.id_prestamo == prestamo.id_prestamo).first()

    e     = prestamo.estudiante
    salon = e.salon if e else None
    return {
        "id_prestamo":      prestamo.id_prestamo,
        "codigo":           e.documento if e else None,
        "nombre":           e.nombre if e else None,
        "grado":            str(salon.grado) if salon else None,
        "grupo":            str(salon.grupo) if salon else None,
        "libro":            prestamo.libro.nombre if prestamo.libro else None,
        "fecha_prestamo":   str(prestamo.fecha_prestamo) if prestamo.fecha_prestamo else None,
        "fecha_devolucion": str(prestamo.fecha_devolucion) if prestamo.fecha_devolucion else None,
        "estado":           prestamo.estado,
    }

def registrar_devolucion(db: Session, prestamo_id: int, data: dict) -> Optional[dict]:
    prestamo = db.query(PrestamoLibro).filter(
        PrestamoLibro.id_prestamo == prestamo_id
    ).first()
    if not prestamo:
        return None

    prestamo.estado = "Devuelto"

    fecha = data.get("fecha_devolucion")
    if isinstance(fecha, date):
        prestamo.fecha_devolucion = fecha
    elif isinstance(fecha, str) and fecha:
        prestamo.fecha_devolucion = date.fromisoformat(fecha)
    else:
        prestamo.fecha_devolucion = date.today()

    if data.get("observacion"):
        prestamo.observacion = data["observacion"]

    libro = db.query(InventarioLibro).filter(
        InventarioLibro.id_libro == prestamo.id_libro
    ).first()
    if libro:
        libro.disponible = True
        if data.get("estado_de_devolucion"):
            libro.estado_fisico = data["estado_de_devolucion"]

    db.commit()

    # Re-query con relaciones cargadas, igual que get_all_prestamos
    prestamo = db.query(PrestamoLibro).options(
        joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
        joinedload(PrestamoLibro.libro)
    ).filter(PrestamoLibro.id_prestamo == prestamo_id).first()

    e = prestamo.estudiante
    salon = e.salon if e else None
    return {
        "id_prestamo":      prestamo.id_prestamo,
        "codigo":           e.documento if e else None,
        "nombre":           e.nombre if e else None,
        "grado":            str(salon.grado) if salon else None,
        "grupo":            str(salon.grupo) if salon else None,
        "libro":            prestamo.libro.nombre if prestamo.libro else None,
        "fecha_prestamo":   str(prestamo.fecha_prestamo) if prestamo.fecha_prestamo else None,
        "fecha_devolucion": str(prestamo.fecha_devolucion) if prestamo.fecha_devolucion else None,
        "estado":           prestamo.estado,

    }

#logs de auditoria
def update_estado_prueba(
    db: Session, 
    prueba_id: int, 
    estado: str, 
    current_user_name: str
) -> Optional[Prueba]:
    prueba = db.query(Prueba).filter(Prueba.id_prueba == prueba_id).first()
    if not prueba:
        return None

    prueba.estado = estado
    if estado == "visto":
        prueba.fecha_pago = date.today()

    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="prueba",
            id_registro=prueba.id_prueba,
            accion="Update" if estado != "visto" else "Registrar Pago",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
        db.refresh(prueba)
        return prueba
    except Exception as e:
        db.rollback()
        raise e
    
def update_pupitre(
    db: Session, 
    pupitre_id: int, 
    estado: str, 
    fecha_pago: Optional[date] = None, 
    current_user_name: str = None
) -> Optional[Pupitre]:
    pupitre = db.query(Pupitre).filter(Pupitre.id_mantenimiento == pupitre_id).first()
    if not pupitre:
        return None

    pupitre.estado = estado
    if fecha_pago:  
        pupitre.fecha_pago = fecha_pago

    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="pupitre",
            id_registro=pupitre.id_mantenimiento,
            accion="Registrar Pago",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
        db.refresh(pupitre)
        return pupitre
    except Exception as e:
        db.rollback()
        raise e
    
def create_libro(db: Session, data: dict, current_user_name: str) -> InventarioLibro:
    libro = InventarioLibro(**data)
    db.add(libro)
    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="inventario_libro",
            id_registro=libro.id_libro,
            accion="Insert",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
        db.refresh(libro)
        return libro
    except Exception as e:
        db.rollback()
        raise e
    

def update_libro(db: Session, libro_id: int, data: dict, current_user_name: str) -> Optional[InventarioLibro]:
    libro = db.query(InventarioLibro).filter(InventarioLibro.id_libro == libro_id).first()
    if not libro:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(libro, key, value)

    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="inventario_libro",
            id_registro=libro.id_libro,
            accion="Update",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
        db.refresh(libro)
        return libro
    except Exception as e:
        db.rollback()
        raise e
    
def delete_libro(db: Session, libro_id: int, current_user_name: str) -> bool:
    libro = db.query(InventarioLibro).filter(InventarioLibro.id_libro == libro_id).first()
    if not libro:
        return False

    if libro.disponible == False:
        raise Exception("No es posible eliminar un libro con préstamo activo.")

    # Borrado lógico
    if "(Eliminado del Inventario)" not in libro.nombre:
        libro.nombre = f"{libro.nombre} (Eliminado del Inventario)"

    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="inventario_libro",
            id_registro=libro.id_libro,
            accion="Delete (Logico)",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    
def create_prestamo(db: Session, data: dict, current_user_name: str) -> dict:
    codigo_raw = str(data.get("codigo", "")).strip()
    codigo_padded = codigo_raw.zfill(10)
    

    estudiante = db.query(Estudiante).filter(
        or_(
            Estudiante.documento == codigo_raw,
            Estudiante.documento == codigo_padded,
        )
    ).first()
    if not estudiante:
        raise Exception(f"Estudiante con código {codigo_raw} no encontrado.")

    libro = db.query(InventarioLibro).filter(InventarioLibro.nombre.ilike(data.get("libro"))).first()
    if not libro:
        raise Exception(f"Libro '{data.get('libro')}' no encontrado en inventario.")
    if not libro.disponible:
        raise Exception(f"El libro '{libro.nombre}' no está disponible.")

    if libro.estado_fisico == "Malo":
        raise Exception(f"El libro '{libro.nombre}' está en mal estado y no puede prestarse.")

    prestamos_activos = db.query(PrestamoLibro).filter(
        PrestamoLibro.id_estudiante == estudiante.id_estudiante,
        PrestamoLibro.estado == "Prestado"
    ).count()
    if prestamos_activos >= 3:
        raise Exception(f"El estudiante ya tiene 3 libros prestados.")

    libro.disponible = False
    libro.estado_fisico = data.get("estado_fisico", "Excelente")

    prestamo = PrestamoLibro(
        id_estudiante=estudiante.id_estudiante,
        id_libro=libro.id_libro,
        fecha_prestamo=date.today(),
        fecha_devolucion=data.get("fecha_devolucion"),
        estado="Prestado",
    )
    db.add(prestamo)
    
    try:
        db.commit()
        auditoria = Auditoria(
            tabla="prestamo_libro",
            id_registro=prestamo.id_prestamo,
            accion="Insert (Prestamo)",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    # Re-query con relaciones para armar el diccionario de respuesta
    prestamo = db.query(PrestamoLibro).options(
        joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
        joinedload(PrestamoLibro.libro)
    ).filter(PrestamoLibro.id_prestamo == prestamo.id_prestamo).first()

    e = prestamo.estudiante
    salon = e.salon if e else None
    return {
        "id_prestamo": prestamo.id_prestamo,
        "codigo": e.documento if e else None,
        "nombre": e.nombre if e else None,
        "grado": str(salon.grado) if salon else None,
        "grupo": str(salon.grupo) if salon else None,
        "libro": prestamo.libro.nombre if prestamo.libro else None,
        "fecha_prestamo": str(prestamo.fecha_prestamo) if prestamo.fecha_prestamo else None,
        "fecha_devolucion": str(prestamo.fecha_devolucion) if prestamo.fecha_devolucion else None,
        "estado": prestamo.estado,
    }

def registrar_devolucion(db: Session, prestamo_id: int, data: dict, current_user_name: str) -> Optional[dict]:
    prestamo = db.query(PrestamoLibro).filter(PrestamoLibro.id_prestamo == prestamo_id).first()
    if not prestamo:
        return None

    prestamo.estado = "Devuelto"

    fecha = data.get("fecha_devolucion")
    if isinstance(fecha, date):
        prestamo.fecha_devolucion = fecha
    elif isinstance(fecha, str) and fecha:
        prestamo.fecha_devolucion = date.fromisoformat(fecha)
    else:
        prestamo.fecha_devolucion = date.today()

    if data.get("observacion"):
        prestamo.observacion = data["observacion"]

    libro = db.query(InventarioLibro).filter(InventarioLibro.id_libro == prestamo.id_libro).first()
    if libro:
        libro.disponible = True
        if data.get("estado_de_devolucion"):
            libro.estado_fisico = data["estado_de_devolucion"]

    try:
        db.commit()
        
        auditoria = Auditoria(
            tabla="prestamo_libro",
            id_registro=prestamo.id_prestamo,
            accion="Update (Devolucion)",
            usuario=current_user_name
        )
        db.add(auditoria)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    # Re-query con relaciones para la respuesta
    prestamo = db.query(PrestamoLibro).options(
        joinedload(PrestamoLibro.estudiante).joinedload(Estudiante.salon),
        joinedload(PrestamoLibro.libro)
    ).filter(PrestamoLibro.id_prestamo == prestamo_id).first()

    e = prestamo.estudiante
    salon = e.salon if e else None
    return {
        "id_prestamo": prestamo.id_prestamo,
        "codigo": e.documento if e else None,
        "nombre": e.nombre if e else None,
        "grado": str(salon.grado) if salon else None,
        "grupo": str(salon.grupo) if salon else None,
        "libro": prestamo.libro.nombre if prestamo.libro else None,
        "fecha_prestamo": str(prestamo.fecha_prestamo) if prestamo.fecha_prestamo else None,
        "fecha_devolucion": str(prestamo.fecha_devolucion) if prestamo.fecha_devolucion else None,
        "estado": prestamo.estado,
    }
