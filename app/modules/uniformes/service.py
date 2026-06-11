from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date

from app.modules.uniformes.models import (
    InventarioObjeto,
    PrestamoObjeto
)
from app.modules.estudiantes.models import (
    Estudiante
)
from app.modules.salon.models import (
    Salon
)
from app.shared.models import Auditoria


# =========================================
# AUDITORIA
# =========================================

def registrar_auditoria(
    db: Session,
    tabla: str,
    id_registro: int,
    accion: str,
    usuario: str
):
    auditoria = Auditoria(
        tabla=tabla,
        id_registro=id_registro,
        accion=accion,
        usuario=usuario
    )

    db.add(auditoria)

# =========================================
# INVENTARIO
# =========================================
def obtener_inventario_service(db: Session):
    print("SERVICIO INVENTARIO NUEVO EJECUTANDO")

    inventario = db.query(InventarioObjeto).all()
    resultado = []

    for item in inventario:
        # CONTAR PRESTAMOS ACTIVOS
        cantidad_prestadas = (
            db.query(PrestamoObjeto)
            .filter(
                PrestamoObjeto.id_objeto == item.id_objeto,
                PrestamoObjeto.estado_prestamo == "prestado"
            )
            .count()
        )
        
        resultado.append({
            "id_objeto": item.id_objeto,
            "nombre": item.nombre,
            "tipo": item.tipo,
            "estado_fisico": item.estado_fisico,
            "talla": item.talla,
            "observacion": item.observacion,
            "fecha_registro": item.fecha_registro,
            "cantidad_total": item.cantidad_total,
            "cantidad_disponible": item.cantidad_disponible,
            "prestadas": cantidad_prestadas
        })

    return resultado


# =========================================
# GET ALL OBJETOS
# =========================================
def get_objetos_all(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(InventarioObjeto)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================================
# DISPONIBLES
# =========================================
def get_objetos_disponibles(db: Session):
    return (
        db.query(InventarioObjeto)
        .filter(InventarioObjeto.cantidad_disponible > 0)
        .all()
    )


# =========================================
# GET BY ID
# =========================================
def get_objeto_by_id(db: Session, objeto_id: int):
    return (
        db.query(InventarioObjeto)
        .filter(InventarioObjeto.id_objeto == objeto_id)
        .first()
    )


# =========================================
# CREAR OBJETO
# =========================================
def create_objeto(db: Session, data: dict, usuario: str):
    print("DATA RECIBIDA:", data)
    nuevo = InventarioObjeto(
        nombre=data["nombre"],
        tipo=data["tipo"],
        estado_fisico=data.get("estado_fisico"),
        talla=data.get("talla"),
        observacion=data.get("observacion"),
        fecha_registro=data.get("fecha_registro"),
        cantidad_total=data["cantidad_total"],
        cantidad_disponible=data["cantidad_total"]
    )

    db.add(nuevo)
    db.flush()

    registrar_auditoria(
        db,
        "inventario_objeto",
        nuevo.id_objeto,
        "CREAR",
        usuario
    )
    db.commit()
    db.refresh(nuevo)
    return nuevo


# =========================================
# EDITAR OBJETO
# =========================================
def update_objeto(db: Session, objeto_id: int, data: dict,usuario: str):
    print("DATA UPDATE:", data)
    objeto = get_objeto_by_id(db, objeto_id)
    if not objeto:
        return None

    # CALCULAR PRESTADAS
    cantidad_prestadas = (
        db.query(func.count(PrestamoObjeto.id_prestamo))
        .filter(
            PrestamoObjeto.id_objeto == objeto.id_objeto,
            PrestamoObjeto.estado_prestamo == "prestado"
        )
        .scalar() or 0
    )

    nueva_total = data.get("cantidad_total", objeto.cantidad_total)

    # NO PUEDE SER MENOR
    if nueva_total < cantidad_prestadas:
        return "cantidad_invalida"

    # ACTUALIZAR
    objeto.nombre = data.get("nombre", objeto.nombre)
    objeto.tipo = data.get("tipo", objeto.tipo)
    objeto.estado_fisico = data.get("estado_fisico",objeto.estado_fisico)
    objeto.talla = data.get("talla", objeto.talla)
    objeto.observacion = data.get("observacion",objeto.observacion)
    objeto.fecha_registro = date.today()
    
    objeto.cantidad_total = nueva_total

    # RECALCULAR DISPONIBLE
    objeto.cantidad_disponible = nueva_total - cantidad_prestadas

    registrar_auditoria(
        db,
        "inventario_objeto",
        objeto.id_objeto,
        "EDITAR",
        usuario
    )

    db.commit()
    db.refresh(objeto)
    return objeto


# =========================================
# ELIMINAR OBJETO
# =========================================
def delete_objeto(db: Session, objeto_id: int,  usuario: str):
    objeto = get_objeto_by_id(db, objeto_id)
    if not objeto:
        return False

    # VALIDAR HISTORIAL RELACIONADO (Uso de scalar() optimizado)
    prestamos_relacionados = (
        db.query(func.count(PrestamoObjeto.id_prestamo))
        .filter(PrestamoObjeto.id_objeto == objeto_id)
        .scalar() or 0
    )

    if prestamos_relacionados > 0:
        return "tiene_prestamos"

    registrar_auditoria(
        db,
        "inventario_objeto",
        objeto.id_objeto,
        "ELIMINAR",
        usuario
    )

    db.delete(objeto)
    db.commit()
    return True


# =========================================
# REGISTRAR PRESTAMO
# =========================================
def registrar_prestamo(db: Session, data: dict, usuario: str):
    # VALIDAR PRESTAMO ACTIVO
    prestamo_activo = (
        db.query(PrestamoObjeto)
        .filter(
            PrestamoObjeto.id_estudiante == data["id_estudiante"],
            PrestamoObjeto.estado_prestamo == "prestado"
        )
        .first()
    )

    if prestamo_activo:
        return "ya_tiene_prestamo"

    objeto = get_objeto_by_id(db, data["id_objeto"])

    # STOCK
    if not objeto or objeto.cantidad_disponible < data["cantidad_prestada"]:
        return None

    # DESCONTAR
    objeto.cantidad_disponible -= data["cantidad_prestada"]

    # CREAR PRESTAMO
    prestamo = PrestamoObjeto(
        id_objeto=data["id_objeto"],
        id_estudiante=data["id_estudiante"],
        talla=data["talla"],
        cantidad_prestada=data["cantidad_prestada"],
        fecha_prestamo=datetime.now(),
        estado_prestamo="prestado",
        estado_entrega=data["estado"].lower(),
        
    )

    db.add(prestamo)

    db.flush()

    registrar_auditoria(
        db,
        "prestamo_objeto",
        prestamo.id_prestamo,
        "CREAR",
        usuario
    )

    db.commit()
    db.refresh(prestamo)
    return prestamo


# =========================================
# DEVOLVER PRESTAMO
# =========================================
def devolver_prestamo(db: Session, prestamo_id: int, data: dict = None,usuario: str = ""):
    prestamo = (
        db.query(PrestamoObjeto)
        .filter(PrestamoObjeto.id_prestamo == prestamo_id)
        .first()
    )

    if not prestamo or prestamo.estado_prestamo == "devuelto":
        return None

    objeto = get_objeto_by_id(db, prestamo.id_objeto)

    estado_devolucion = "bueno"
    if data and data.get("estado_devolucion"):
        estado_devolucion = data.get("estado_devolucion").lower()

    # VALIDAR OBSERVACION SI ESTA MALO
    if estado_devolucion == "malo":
        observacion = data.get("observacion", "").strip()

        if not observacion:
            return "observacion_requerida"

    # REINTEGRAR
    if objeto and estado_devolucion in ["bueno", "regular"]:
        objeto.cantidad_disponible += prestamo.cantidad_prestada

    # ACTUALIZAR
    prestamo.estado_entrega = estado_devolucion
    prestamo.estado_prestamo = "devuelto"
    prestamo.fecha_devolucion = datetime.today()
    prestamo.observacion = data.get("observacion")

    registrar_auditoria(
        db,
        "prestamo_objeto",
        prestamo.id_prestamo,
        "DEVOLUCION",
        usuario
    )

    db.commit()
    db.refresh(prestamo)
    return prestamo


# =========================================
# PRESTAMOS ACTIVOS
# =========================================
def get_prestamos_activos(db: Session):
    return (
        db.query(PrestamoObjeto)
        .filter( PrestamoObjeto.estado_prestamo == "prestado")
        .all()
    )


# =========================================
# ASIGNACIONES (OPTIMIZADO CON EAGER LOADING)
# =========================================
def get_asignaciones(db: Session, id_usuario: int, roles: list):
    # Traemos estudiantes junto con su salón de forma eficiente
    estudiantes_query = (
        db.query(Estudiante)
        .outerjoin(Estudiante.salon)
        .options(joinedload(Estudiante.salon))
    )

    if "admin" not in roles and "administrador" not in roles:
        estudiantes_query = estudiantes_query.filter(Salon.id_usuario == id_usuario)

    estudiantes = estudiantes_query.all()
    print("ESTUDIANTES:", len(estudiantes))
    estudiante_ids = [e.id_estudiante for e in estudiantes]

    prestamos = (
        db.query(PrestamoObjeto)
        .filter(
            PrestamoObjeto.id_estudiante.in_(estudiante_ids)
            if estudiante_ids else False,
            PrestamoObjeto.estado_prestamo == "prestado"
        )
        .all()
    )

    prestamos_map = {}

    for p in prestamos:
        prestamos_map[p.id_estudiante] = p

    objetos_inventario = db.query(
        InventarioObjeto
    ).all()
    
    objetos_map = {obj.id_objeto: obj for obj in objetos_inventario}

    resultado = []
    for estudiante in estudiantes:
        prestamo = prestamos_map.get(estudiante.id_estudiante)
        objeto = objetos_map.get(prestamo.id_objeto) if prestamo else None

        resultado.append({
            "id_prestamo": prestamo.id_prestamo if prestamo else None,
            "id_estudiante": estudiante.id_estudiante,

            "codigo": estudiante.documento,

            "nombre_completo": estudiante.nombre,

            "grado": estudiante.salon.grado if estudiante.salon else None,

            "grupo": estudiante.salon.grupo if estudiante.salon else None,

            "anio": estudiante.salon.periodo.nombre
                if estudiante.salon and estudiante.salon.periodo
                else None,

            "prenda": objeto.nombre if objeto else "Sin asignar",

            "fecha_entrega":
                prestamo.fecha_prestamo
                if prestamo
                else None,

            "estado":
                prestamo.estado_prestamo
                if prestamo
                else "Sin asignar",

            "talla":
                prestamo.talla if prestamo else "",

            "estado_entrega":
                prestamo.estado_entrega if prestamo else ""
        })
        

    return resultado


# =========================================
# HISTORIAL DEVOLUCIONES (OPTIMIZADO)
# =========================================
def get_historial_devoluciones(db: Session, id_usuario: int, roles: list):
    estudiantes_query = (
        db.query(Estudiante)
        .outerjoin(Estudiante.salon)
        .options(joinedload(Estudiante.salon))
    )

    if "admin" not in roles and "administrador" not in roles:
        estudiantes_query = estudiantes_query.filter(Salon.id_usuario == id_usuario)

    estudiantes = estudiantes_query.all()
    estudiante_ids = [e.id_estudiante for e in estudiantes]

    # Traemos todos los préstamos devueltos en una única consulta
    prestamos_devueltos = (
        db.query(PrestamoObjeto)
        .filter(
            PrestamoObjeto.id_estudiante.in_(estudiante_ids) if estudiante_ids else False,
            PrestamoObjeto.estado_prestamo == "devuelto"
        )
        .order_by(func.coalesce(PrestamoObjeto.fecha_devolucion, PrestamoObjeto.fecha_prestamo).desc())
        .all()
    )

    # Agrupamos los préstamos por estudiante
    prestamos_por_estudiante = {}
    for p in prestamos_devueltos:
        if p.id_estudiante not in prestamos_por_estudiante:
            prestamos_por_estudiante[p.id_estudiante] = []
        prestamos_por_estudiante[p.id_estudiante].append(p)

    objeto_ids = [p.id_objeto for p in prestamos_devueltos]
    objetos_inventario = (
        db.query(InventarioObjeto)
        .filter(InventarioObjeto.id_objeto.in_(objeto_ids) if objeto_ids else False)
        .all()
    )
    objetos_map = {obj.id_objeto: obj for obj in objetos_inventario}

    resultado = []
    for estudiante in estudiantes:
        prestamos = prestamos_por_estudiante.get(estudiante.id_estudiante, [])
        for prestamo in prestamos:
            objeto = objetos_map.get(prestamo.id_objeto)

            resultado.append({
                "id_prestamo": prestamo.id_prestamo,
                "codigo": str(estudiante.id_estudiante),
                "nombre_completo": estudiante.nombre,
                "grado": estudiante.salon.grado if estudiante.salon else None,
                "grupo": estudiante.salon.grupo if estudiante.salon else None,
                "prenda": objeto.nombre if objeto else "—",
                "fecha_entrega": prestamo.fecha_prestamo,
                "fecha_devolucion": prestamo.fecha_devolucion,
                "estado_final": prestamo.estado_entrega,
                "talla": prestamo.talla
            })

    return resultado


# =========================================
# ELIMINAR PRESTAMO
# =========================================
def eliminar_prestamo(db: Session, prestamo_id: int):
    prestamo = (
        db.query(PrestamoObjeto)
        .filter(PrestamoObjeto.id_prestamo == prestamo_id)
        .first()
    )

    if not prestamo:
        return False

    # DEVOLVER INVENTARIO
    if prestamo.estado_prestamo == "prestado":
        objeto = (
            db.query(InventarioObjeto)
            .filter(InventarioObjeto.id_objeto == prestamo.id_objeto)
            .first()
        )

        if objeto:
            objeto.cantidad_disponible += prestamo.cantidad_prestada

        registrar_auditoria(
            db,
            "prestamo_objeto",
            prestamo.id_prestamo,
            "ELIMINAR",
            "admin"

        )

        db.delete(prestamo)
        db.commit()
        return True