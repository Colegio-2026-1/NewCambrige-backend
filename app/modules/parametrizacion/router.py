
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from .schemas import AnioEscolarCreate, AnioEscolarRead, AnioEscolarUpdate, TipoPruebaUpdate, TipoPruebaRead, TipoPruebaCreate
from .service import crear_anio_escolar, get_anios_all, update_anio_escolar, get_tipos_prueba, update_tipo_prueba, create_tipo_prueba, get_tipo_prueba_by_id, get_tipo_prueba_by_nombre, get_tipos_prueba_por_grado
from app.modules.parametrizacion import service, schemas
from app.modules.auth.deps import require_roles


router = APIRouter(tags=["Parametrización"])

#PERIDO ACADEMICO
@router.post("/anio-escolar", response_model=AnioEscolarRead, status_code=status.HTTP_201_CREATED)
def registrar_anio(
    payload: AnioEscolarCreate, 
    forzar: bool = Query(False, description="Forzar la desactivación del año anterior"),
    db: Session = Depends(get_db)
):
    return crear_anio_escolar(db, payload, "USUARIO_PRUEBA", forzar)

@router.get("/anio-escolar", response_model=List[AnioEscolarRead])
def listar_anios(db: Session = Depends(get_db)):
    return get_anios_all(db)


@router.patch("/anio-escolar/{id_periodo}", response_model=AnioEscolarRead)
def actualizar_anio(
    id_periodo: int,
    payload: AnioEscolarUpdate,
    forzar: bool = Query(False, description="Forzar la desactivación del año actual para activar este"),
    db: Session = Depends(get_db)
):
   
    datos_filtrados = payload.dict(exclude_unset=True)
    
    actualizado = update_anio_escolar(db, id_periodo, datos_filtrados, "USUARIO_PRUEBA", forzar)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Año escolar no encontrado")
        
    return actualizado

#TIPOS DE PRUEBA

@router.get("/tipos-prueba", response_model=List[TipoPruebaRead])
def listar_tipos_prueba(db: Session = Depends(get_db)):
    return get_tipos_prueba(db)

@router.get("/tipos-prueba/{id_tipo_prueba}", response_model=TipoPruebaRead)
def obtener_tipo_prueba(id_tipo_prueba: int, db: Session = Depends(get_db)):
    """Obtiene los detalles de un tipo de prueba específico por su ID."""
    prueba = get_tipo_prueba_by_id(db, id_tipo_prueba)
    if not prueba:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de prueba no encontrado")
    return prueba

@router.get("/tipos-prueba/grado/{grado}", response_model=List[TipoPruebaRead])
def listar_tipos_prueba_por_grado(grado: int, db: Session = Depends(get_db)):
    """Obtiene los tipos de prueba que aplican a un grado escolar específico."""
    if not (1 <= grado <= 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grado inválido (debe ser de 1 a 12)")
    return get_tipos_prueba_por_grado(db, grado)

@router.post("/tipos-prueba", response_model=TipoPruebaRead, status_code=status.HTTP_201_CREATED)
def crear_nuevo_tipo_prueba(
    payload: TipoPruebaCreate, 
    db: Session = Depends(get_db)
):
    """Permite registrar un nuevo tipo de prueba en el sistema."""
    try:
        return create_tipo_prueba(db, payload.model_dump())
        
    except ValueError as e:
        errores = e.errors() if hasattr(e, 'errors') else [{"msg": str(e)}]
        mensaje_limpio = errores[0]['msg'] if errores else str(e)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=mensaje_limpio
        )

@router.patch("/tipos-prueba/{id_tipo_prueba}", response_model=TipoPruebaRead)
def editar_rangos_prueba(
    id_tipo_prueba: int, 
    payload: TipoPruebaUpdate, 
    db: Session = Depends(get_db)
):
    """Permite editar los rangos de grados (min y max) y la descripción de la prueba."""
    try:
        actualizado = update_tipo_prueba(db, id_tipo_prueba, payload.model_dump())
        if not actualizado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de prueba no encontrado")
        return actualizado
    except ValueError as e:
        errores = e.errors() if hasattr(e, 'errors') else [{"msg": str(e)}]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errores[0]['msg'] if errores else str(e))
    


# ASIGNACIÓN DE TITULARES

@router.get(
    "/titulares", 
    response_model=List[schemas.TitularResponse]
)
def listar_titulares(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "parametrizacion"]))
):
    """Devuelve la lista de todos los usuarios activos que tienen el rol de titular."""
    return service.get_titulares_activos(db)


@router.get(
    "/salones/periodo/{id_periodo}", 
    response_model=List[schemas.SalonAsignacionResponse]
)
def listar_salones_por_periodo(
    id_periodo: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "parametrizacion"]))
):
    """Devuelve los salones de un periodo para armar los combos de Grado y Grupo."""
    return service.get_salones_para_asignacion(db, id_periodo)


@router.put(
    "/salones/{id_salon}/asignar-titular", 
    response_model=schemas.SalonAsignacionResponse
)
def asignar_titular(
    id_salon: int,
    data: schemas.AsignarTitularRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "parametrizacion"]))
):
    """Actualiza el id_usuario (titular) de un salón específico."""
    salon_actualizado = service.asignar_titular_a_salon(db, id_salon, data.id_usuario)
    
    if not salon_actualizado:
        raise HTTPException(
            status_code=404, 
            detail="Salón no encontrado"
        )
        
    return salon_actualizado

@router.post(
    "/salones", 
    response_model=schemas.SalonAsignacionResponse, 
    status_code=status.HTTP_201_CREATED
)
def crear_salon_desde_parametrizacion(
    data: schemas.SalonCreateParam,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "parametrizacion"]))
):
    from app.modules.salon.models import Salon  

    salon_existente = db.query(Salon).filter(
        Salon.grado == data.grado,
        Salon.grupo == data.grupo,
        Salon.id_periodo == data.id_periodo
    ).first()

    if salon_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"El salón {data.grado} - {data.grupo} ya existe en este periodo escolar."
        )

    nuevo_salon = service.crear_salon_parametrizacion(db, data.model_dump())
    
    return nuevo_salon