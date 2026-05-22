from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.estudiantes import service
from app.modules.estudiantes.schemas import EstudianteResponse, EstudianteCreate, EstudianteUpdate
from app.modules.auth.deps import require_roles

router = APIRouter()

@router.get("/", response_model=List[EstudianteResponse])
def listar_estudiantes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular", "secretaria", "banda"]))
):
    return service.get_all(db, skip, limit)

@router.get("/{estudiante_id}", response_model=EstudianteResponse)
def obtener_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "titular", "secretaria"]))
):
    estudiante = service.get_by_id(db, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante

@router.post("/", response_model=EstudianteResponse, status_code=status.HTTP_201_CREATED)
def crear_estudiante(
    data: EstudianteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.create(db, data)

@router.put("/{estudiante_id}", response_model=EstudianteResponse)
def actualizar_estudiante(
    estudiante_id: int,
    data: EstudianteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    estudiante = service.update(db, estudiante_id, data)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return estudiante

@router.delete("/{estudiante_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if not service.delete(db, estudiante_id):
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return None