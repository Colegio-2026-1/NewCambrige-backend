from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.salon import service
from app.modules.salon.schemas import SalonResponse, SalonCreate, SalonUpdate
from app.modules.auth.deps import require_roles

router = APIRouter()

@router.get("/", response_model=List[SalonResponse])
def listar_salones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular", "secretaria"]))
):
    return service.get_all(db, skip, limit)

@router.get("/{salon_id}", response_model=SalonResponse)
def obtener_salon(
    salon_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular", "secretaria"]))
):
    salon = service.get_by_id(db, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    return salon

@router.get("/grado/{grado}/grupo/{grupo}", response_model=List[SalonResponse])
def salones_por_grado_grupo(
    grado: int,
    grupo: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular", "secretaria"]))
):
    return service.get_by_grado_grupo(db, grado, grupo)

@router.post("/", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
def crear_salon(
    data: SalonCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.create(db, data.model_dump())

@router.put("/{salon_id}", response_model=SalonResponse)
def actualizar_salon(
    salon_id: int,
    data: SalonUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
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