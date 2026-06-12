from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db

from app.modules.uniformes import service

from app.modules.uniformes.service import (
    obtener_inventario_service,
    devolver_prestamo as devolver_prestamo_service,
    get_historial_devoluciones
)

from app.modules.uniformes.models import (
    PrestamoObjeto
)

from app.modules.uniformes.schemas import (

    ObjetoResponse,
    ObjetoCreate,
    ObjetoUpdate,

    PrestamoObjetoResponse,
    PrestamoObjetoCreate,

    AsignacionResponse

)

from app.modules.auth.deps import (
    require_roles
)

from app.modules.auth.deps import (
    get_current_user
)

router = APIRouter()

# =========================================
# OBJETOS
# =========================================

@router.get(
    "/objetos",
    response_model=List[ObjetoResponse]
)
def listar_objetos(

    skip: int = Query(0, ge=0),

    limit: int = Query(
        100,
        ge=1,
        le=500
    ),

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    return service.get_objetos_all(
        db,
        skip,
        limit
    )


@router.get(
    "/inventario",
    response_model=List[ObjetoResponse]
)
def obtener_inventario(

    db: Session = Depends(get_db)

):

    return obtener_inventario_service(db)


@router.get(
    "/objetos/disponibles",
    response_model=List[ObjetoResponse]
)
def objetos_disponibles(

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    return service.get_objetos_disponibles(db)


@router.post(
    "/objetos",
    response_model=ObjetoResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_objeto(

    data: ObjetoCreate,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    return service.create_objeto(
        db,
        data.model_dump(),
        current_user.nombre
    )


@router.put(
    "/objetos/{objeto_id}",
    response_model=ObjetoResponse
)
def actualizar_objeto(

    objeto_id: int,

    data: ObjetoUpdate,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    objeto = service.update_objeto(

        db,
        objeto_id,

        data.model_dump(
            exclude_unset=True
        ),

        current_user.nombre

        

    )
    
    if objeto == "cantidad_invalida":
        raise HTTPException(
            status_code=400,
            detail="La cantidad total no puede ser menor a las prendas actualmente prestadas"
    )

    if not objeto:

        raise HTTPException(

            status_code=404,

            detail=
            "Objeto no encontrado"

        )

    return objeto


# =========================================
# PRESTAMOS
# =========================================

@router.get(
    "/prestamos",
    response_model=List[PrestamoObjetoResponse]
)
def listar_prestamos(

    skip: int = Query(0, ge=0),

    limit: int = Query(
        100,
        ge=1,
        le=500
    ),

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    return (

        db.query(PrestamoObjeto)

        .offset(skip)

        .limit(limit)

        .all()

    )


@router.get(
    "/prestamos/activos",
    response_model=List[PrestamoObjetoResponse]
)
def prestamos_activos(

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    return service.get_prestamos_activos(db)


@router.post(
    "/prestamos",
    response_model=PrestamoObjetoResponse,
    status_code=status.HTTP_201_CREATED
)
def registrar_prestamo(

    data: PrestamoObjetoCreate,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    prestamo = service.registrar_prestamo(

        db,

        data.model_dump(),
        current_user.nombre

    )

    # =====================================
    # YA TIENE PRESTAMO ACTIVO
    # =====================================

    if prestamo == "ya_tiene_prestamo":

        raise HTTPException(

            status_code=400,

            detail=
            "El estudiante ya tiene una asignación activa"

        )

    # =====================================
    # STOCK
    # =====================================

    if not prestamo:

        raise HTTPException(

            status_code=400,

            detail=
            "Stock insuficiente o objeto no encontrado"

        )

    return prestamo


@router.put(
    "/prestamos/{prestamo_id}/devolver",
    response_model=PrestamoObjetoResponse
)
def devolver_prestamo_old(

    prestamo_id: int,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    prestamo = service.devolver_prestamo(

        db,
        prestamo_id

    )

    if not prestamo:

        raise HTTPException(

            status_code=404,

            detail=
            "Préstamo no encontrado o ya devuelto"

        )

    return prestamo


# =========================================
# ASIGNACIONES
# =========================================

@router.get(
    "/asignaciones",
    response_model=List[AsignacionResponse]
)
def listar_asignaciones(

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    # =====================================
    # CONVERTIR ROLES A STRING
    # =====================================

    roles = []

    for r in current_user.roles:

        if hasattr(r, "rol") and r.rol:

            roles.append(
                r.rol.nombre.lower()
            )

    # =====================================
    # DEBUG
    # =====================================

    print("USUARIO:", current_user)
    print("ROLES:", roles)
    print("ID USER:", current_user.id_usuario)

    # =====================================
    # OBTENER ASIGNACIONES
    # =====================================

    return service.get_asignaciones(

        db,

        current_user.id_usuario,

        roles

    )


# =========================================
# DEVOLVER PRESTAMO NUEVO
# =========================================

@router.put("/devolver/{id_prestamo}")

def devolver_uniforme(

    id_prestamo: int,

    data: dict,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )

):

    prestamo = devolver_prestamo_service(

        db,
        id_prestamo,
        data,
        current_user.nombre

    )
    if prestamo == "observacion_requerida":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar una observación cuando la prenda se devuelve en mal estado"
        )

    if not prestamo:

        raise HTTPException(

            status_code=404,

            detail=
            "Préstamo no encontrado"

        )

    return prestamo



# =========================================
# ELIMINAR OBJETO
# =========================================

@router.delete(
    "/objetos/{objeto_id}"
)
def eliminar_objeto(

    objeto_id: int,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    try:

        eliminado = service.delete_objeto(

            db,
            objeto_id,
            current_user.nombre

        )

        # ==========================
        # NO EXISTE
        # ==========================

        if eliminado == "no_existe":

            raise HTTPException(

                status_code=404,

                detail=
                "Prenda no encontrada"

            )

        # ==========================
        # TIENE PRÉSTAMOS
        # ==========================

        if eliminado == "tiene_prestamos":

            raise HTTPException(

                status_code=400,

                detail=
                "No se puede eliminar porque la prenda tiene historial de préstamos"

            )

        return {

            "message":
            "Prenda eliminada correctamente"

        }

    except HTTPException:

        raise

    except Exception as e:

        print("ERROR ELIMINANDO PRENDA:", e)

        raise HTTPException(

            status_code=500,

            detail=
            f"Error interno eliminando prenda: {str(e)}"

        )
    

# =========================================
# ELIMINAR PRESTAMO
# =========================================

@router.delete("/prestamos/{prestamo_id}")
def eliminar_prestamo(

    prestamo_id: int,

    db: Session = Depends(get_db),

    current_user = Depends(
        require_roles([
            "admin",
            "uniformes"
        ])
    )
):

    eliminado = service.eliminar_prestamo(
        db,
        prestamo_id
    )

    if not eliminado:

        raise HTTPException(
            status_code=404,
            detail="Préstamo no encontrado"
        )

    return {
        "message": "Préstamo eliminado correctamente"
    }

    # =====================================
    # CONVERTIR ROLES
    # =====================================

    roles = []

    for r in current_user.roles:

        if hasattr(r, "rol") and r.rol:

            roles.append(
                r.rol.nombre.lower()
            )

