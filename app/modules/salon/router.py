from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.modules.auth.deps import get_current_user, require_roles
from app.modules.usuarios.models import RolUsuario, Rol
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.salon import service
from app.modules.salon.schemas import (
    DevolucionSchema, SalonResponse, SalonCreate, SalonUpdate,
    PruebaResponse, PruebaCreate,
    PupitreResponse, PupitreUpdate,
    LibroResponse, LibroCreate, LibroUpdate,
    PrestamoResponse, PrestamoCreate,
)

router = APIRouter()

# ======================
#  SALONES
# ======================
@router.get("/", response_model=List[SalonResponse])
def listar_salones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    return service.get_all(db, skip, limit)


@router.get("/periodo/{id_periodo}", response_model=List[SalonResponse])
def listar_salones_por_periodo(
    id_periodo: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    return service.get_salon_all_by_periodo(db, id_periodo, skip, limit)


@router.get("/grado/{grado}/grupo/{grupo}", response_model=List[SalonResponse])
def salones_por_grado_grupo(
    grado: int, grupo: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    return service.get_by_grado_grupo(db, grado, grupo)


@router.post("/", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
def crear_salon(
    data: SalonCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    return service.create(db, data.model_dump())


@router.put("/{salon_id}", response_model=SalonResponse)
def actualizar_salon(
    salon_id: int, data: SalonUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    salon = service.update(db, salon_id, data.model_dump(exclude_unset=True))
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    return salon


@router.delete("/{salon_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_salon(
    salon_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if not service.delete(db, salon_id):
        raise HTTPException(status_code=404, detail="Salón no encontrado")


# ======================
#  PRUEBAS
# ======================
@router.get("/pruebas", response_model=List[dict])
def listar_pruebas(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.get_all_pruebas(db)


@router.post("/pruebas", response_model=PruebaResponse, status_code=status.HTTP_201_CREATED)
def crear_prueba(
    data: PruebaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.create_prueba(db, data.model_dump())


@router.put("/pruebas/{prueba_id}/estado")
def actualizar_estado_prueba(
    prueba_id: int, estado: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    prueba = service.update_estado_prueba(db, prueba_id, estado, current_user.nombre)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return prueba


# ======================
#  PUPITRES
# ======================
@router.get("/pupitres", response_model=List[dict])
def listar_pupitres(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.get_all_pupitres(db)


@router.put("/pupitres/{pupitre_id}", response_model=PupitreResponse)
def actualizar_pupitre(
    pupitre_id: int, data: PupitreUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    pupitre = service.update_pupitre(db, pupitre_id, data.estado, data.fecha_pago, current_user.nombre)
    if not pupitre:
        raise HTTPException(status_code=404, detail="Pupitre no encontrado")
    return pupitre


# ======================
#  BIBLIOTECA
# ======================
@router.get("/libros", response_model=List[LibroResponse])
def listar_libros(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.get_all_libros(db)


@router.post("/libros", response_model=LibroResponse, status_code=status.HTTP_201_CREATED)
def crear_libro(
    data: LibroCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.create_libro(db, data.model_dump(), current_user.nombre)


@router.put("/libros/{libro_id}", response_model=LibroResponse)
def actualizar_libro(
    libro_id: int, data: LibroUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    libro = service.update_libro(db, libro_id, data.model_dump(exclude_unset=True), current_user.nombre)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return libro


@router.delete("/libros/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(
    libro_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    if not service.delete_libro(db, libro_id, current_user.nombre):
        raise HTTPException(status_code=404, detail="Libro no encontrado")


@router.get("/prestamos", response_model=List[PrestamoResponse])
def listar_prestamos(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    return service.get_all_prestamos(db)


@router.post("/prestamos", response_model=PrestamoResponse, status_code=status.HTTP_201_CREATED)
def crear_prestamo(
    data: PrestamoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    try:
        return service.create_prestamo(db, data.model_dump(), current_user.nombre)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/prestamos/{prestamo_id}/devolver", response_model=PrestamoResponse)
def devolver_libro_prestado(
    prestamo_id: int,
    data: DevolucionSchema,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular"]))
):
    prestamo = service.registrar_devolucion(db, prestamo_id, data.model_dump(), current_user.nombre)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Registro de préstamo no encontrado")
    return prestamo


# ← GET /{salon_id} SIEMPRE AL FINAL
@router.get("/{salon_id}", response_model=SalonResponse)
def obtener_salon(
    salon_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    salon = service.get_by_id(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    return salon