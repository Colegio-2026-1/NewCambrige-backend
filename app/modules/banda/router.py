from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.banda import service
from app.modules.banda.schemas import (
    CategoriaResponse, CategoriaCreate, CategoriaUpdate,
    UbicacionResponse, UbicacionCreate, UbicacionUpdate,
    InstrumentoResponse, InstrumentoCreate, InstrumentoUpdate,
    PrestamoInstrumentoResponse, PrestamoInstrumentoCreate, PrestamoInstrumentoUpdate,
    InstrumentoDisponibleResponse, PrestamoActivoResponse
)
from app.modules.auth.deps import require_roles

router = APIRouter()

# ============ CATEGORÍAS ============
@router.get("/categorias", response_model=List[CategoriaResponse])
def listar_categorias(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    return service.get_categorias_all(db, skip, limit)

@router.get("/categorias/{categoria_id}", response_model=CategoriaResponse)
def obtener_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    categoria = service.get_categoria_by_id(db, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    data: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    existente = service.get_categoria_by_nombre(db, data.nombre)
    if existente:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    return service.create_categoria(db, data.model_dump())

@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
def actualizar_categoria(
    categoria_id: int,
    data: CategoriaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    categoria = service.update_categoria(db, categoria_id, data.model_dump(exclude_unset=True))
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@router.delete("/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if not service.delete_categoria(db, categoria_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

# ============ UBICACIONES ============
@router.get("/ubicaciones", response_model=List[UbicacionResponse])
def listar_ubicaciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    return service.get_ubicaciones_all(db, skip, limit)

@router.post("/ubicaciones", response_model=UbicacionResponse, status_code=status.HTTP_201_CREATED)
def crear_ubicacion(
    data: UbicacionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    return service.create_ubicacion(db, data.model_dump())

@router.put("/ubicaciones/{ubicacion_id}", response_model=UbicacionResponse)
def actualizar_ubicacion(
    ubicacion_id: int,
    data: UbicacionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    ubicacion = service.update_ubicacion(db, ubicacion_id, data.model_dump(exclude_unset=True))
    if not ubicacion:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    return ubicacion

@router.delete("/ubicaciones/{ubicacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ubicacion(
    ubicacion_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if not service.delete_ubicacion(db, ubicacion_id):
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")

# ============ INSTRUMENTOS ============
@router.get("/instrumentos", response_model=List[InstrumentoResponse])
def listar_instrumentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_disponibles: bool = Query(False),
    categoria_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria", "titular"]))
):
    instrumentos = service.get_instrumentos_all(db, skip, limit, solo_disponibles, categoria_id)
    resultado = []
    for i in instrumentos:
        resultado.append({
            "id_instrumento": i.id_instrumento,
            "nombre": i.nombre,
            "id_categoria": i.id_categoria,
            "id_ubicacion": i.id_ubicacion,
            "disponible": i.disponible,
            "categoria_nombre": i.categoria.nombre if i.categoria else None,
            "ubicacion_nombre": i.ubicacion.nombre if i.ubicacion else None
        })
    return resultado

@router.get("/instrumentos/disponibles", response_model=List[InstrumentoDisponibleResponse])
def instrumentos_disponibles(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    instrumentos = service.get_instrumentos_all(db, solo_disponibles=True)
    return [
        {
            "id_instrumento": i.id_instrumento,
            "nombre": i.nombre,
            "categoria": i.categoria.nombre if i.categoria else None,
            "ubicacion": i.ubicacion.nombre if i.ubicacion else None
        }
        for i in instrumentos
    ]

@router.get("/instrumentos/{instrumento_id}", response_model=InstrumentoResponse)
def obtener_instrumento(
    instrumento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    instrumento = service.get_instrumento_by_id(db, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento no encontrado")
    return {
        "id_instrumento": instrumento.id_instrumento,
        "nombre": instrumento.nombre,
        "id_categoria": instrumento.id_categoria,
        "id_ubicacion": instrumento.id_ubicacion,
        "disponible": instrumento.disponible,
        "categoria_nombre": instrumento.categoria.nombre if instrumento.categoria else None,
        "ubicacion_nombre": instrumento.ubicacion.nombre if instrumento.ubicacion else None
    }

@router.post("/instrumentos", response_model=InstrumentoResponse, status_code=status.HTTP_201_CREATED)
def crear_instrumento(
    data: InstrumentoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    return service.create_instrumento(db, data.model_dump())

@router.put("/instrumentos/{instrumento_id}", response_model=InstrumentoResponse)
def actualizar_instrumento(
    instrumento_id: int,
    data: InstrumentoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    instrumento = service.update_instrumento(db, instrumento_id, data.model_dump(exclude_unset=True))
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento no encontrado")
    return instrumento

@router.delete("/instrumentos/{instrumento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_instrumento(
    instrumento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    try:
        if not service.delete_instrumento(db, instrumento_id):
            raise HTTPException(status_code=404, detail="Instrumento no encontrado")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ PRÉSTAMOS DE INSTRUMENTOS ============
@router.get("/prestamos", response_model=List[PrestamoInstrumentoResponse])
def listar_prestamos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(False),
    estudiante_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    prestamos = service.get_prestamos_all(db, skip, limit, solo_activos, estudiante_id)
    resultado = []
    for p in prestamos:
        resultado.append({
            "id_prestamo": p.id_prestamo,
            "id_instrumento": p.id_instrumento,
            "id_estudiante": p.id_estudiante,
            "fecha_prestamo": p.fecha_prestamo,
            "fecha_devolucion": p.fecha_devolucion,
            "estado_entrega": p.estado_entrega,
            "observacion": p.observacion,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "instrumento_nombre": p.instrumento.nombre if p.instrumento else None,
            "estudiante_nombre": p.estudiante.nombre if p.estudiante else None
        })
    return resultado

@router.get("/prestamos/activos", response_model=List[PrestamoActivoResponse])
def prestamos_activos(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    prestamos = service.get_prestamos_all(db, solo_activos=True)
    return [
        {
            "id_prestamo": p.id_prestamo,
            "instrumento": p.instrumento.nombre if p.instrumento else "N/A",
            "estudiante": p.estudiante.nombre if p.estudiante else "N/A",
            "fecha_prestamo": p.fecha_prestamo,
            "dias_prestado": (date.today() - p.fecha_prestamo).days
        }
        for p in prestamos
    ]

@router.get("/prestamos/{prestamo_id}", response_model=PrestamoInstrumentoResponse)
def obtener_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    prestamo = service.get_prestamo_by_id(db, prestamo_id)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return {
        "id_prestamo": prestamo.id_prestamo,
        "id_instrumento": prestamo.id_instrumento,
        "id_estudiante": prestamo.id_estudiante,
        "fecha_prestamo": prestamo.fecha_prestamo,
        "fecha_devolucion": prestamo.fecha_devolucion,
        "estado_entrega": prestamo.estado_entrega,
        "observacion": prestamo.observacion,
        "created_at": prestamo.created_at,
        "updated_at": prestamo.updated_at,
        "instrumento_nombre": prestamo.instrumento.nombre if prestamo.instrumento else None,
        "estudiante_nombre": prestamo.estudiante.nombre if prestamo.estudiante else None
    }

@router.post("/prestamos", response_model=PrestamoInstrumentoResponse, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    data: PrestamoInstrumentoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    try:
        prestamo = service.create_prestamo(db, data.model_dump())
        if not prestamo:
            raise HTTPException(status_code=404, detail="Instrumento o estudiante no encontrado")
        return prestamo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/prestamos/{prestamo_id}/devolver", response_model=PrestamoInstrumentoResponse)
def devolver_instrumento(
    prestamo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    try:
        prestamo = service.devolver_instrumento(db, prestamo_id)
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        return prestamo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/prestamos/{prestamo_id}", response_model=PrestamoInstrumentoResponse)
def actualizar_prestamo(
    prestamo_id: int,
    data: PrestamoInstrumentoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    prestamo = service.update_prestamo(db, prestamo_id, data.model_dump(exclude_unset=True))
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return prestamo

@router.get("/instrumentos/{instrumento_id}/historial", response_model=List[PrestamoInstrumentoResponse])
def historial_instrumento(
    instrumento_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda", "secretaria"]))
):
    prestamos = service.get_historial_instrumento(db, instrumento_id)
    return [
        {
            "id_prestamo": p.id_prestamo,
            "id_instrumento": p.id_instrumento,
            "id_estudiante": p.id_estudiante,
            "fecha_prestamo": p.fecha_prestamo,
            "fecha_devolucion": p.fecha_devolucion,
            "estado_entrega": p.estado_entrega,
            "observacion": p.observacion,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "instrumento_nombre": p.instrumento.nombre if p.instrumento else None,
            "estudiante_nombre": p.estudiante.nombre if p.estudiante else None
        }
        for p in prestamos
    ]

# ============ ESTADÍSTICAS ============
@router.get("/estadisticas")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "banda"]))
):
    return service.get_estadisticas(db)