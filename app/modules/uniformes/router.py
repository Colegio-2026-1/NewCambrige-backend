from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.modules.uniformes import service
from app.modules.uniformes.schemas import (
    ObjetoResponse, ObjetoCreate, ObjetoUpdate,
    PrestamoObjetoResponse, PrestamoObjetoCreate
)
from app.modules.auth.deps import require_roles

router = APIRouter()

# ============ OBJETOS ============
@router.get("/objetos", response_model=List[ObjetoResponse])
def listar_objetos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes", "secretaria"]))
):
    return service.get_objetos_all(db, skip, limit)

@router.get("/objetos/disponibles", response_model=List[ObjetoResponse])
def objetos_disponibles(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes", "secretaria"]))
):
    return service.get_objetos_disponibles(db)

@router.post("/objetos", response_model=ObjetoResponse, status_code=status.HTTP_201_CREATED)
def crear_objeto(
    data: ObjetoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes"]))
):
    return service.create_objeto(db, data.model_dump())

@router.put("/objetos/{objeto_id}", response_model=ObjetoResponse)
def actualizar_objeto(
    objeto_id: int,
    data: ObjetoUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes"]))
):
    objeto = service.update_objeto(db, objeto_id, data.model_dump(exclude_unset=True))
    if not objeto:
        raise HTTPException(status_code=404, detail="Objeto no encontrado")
    return objeto

# ============ PRÉSTAMOS ============
@router.get("/prestamos", response_model=List[PrestamoObjetoResponse])
def listar_prestamos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes", "secretaria"]))
):
    return db.query(PrestamoObjeto).offset(skip).limit(limit).all()

@router.get("/prestamos/activos", response_model=List[PrestamoObjetoResponse])
def prestamos_activos(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes"]))
):
    return service.get_prestamos_activos(db)

@router.post("/prestamos", response_model=PrestamoObjetoResponse, status_code=status.HTTP_201_CREATED)
def registrar_prestamo(
    data: PrestamoObjetoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes"]))
):
    prestamo = service.registrar_prestamo(db, data.model_dump())
    if not prestamo:
        raise HTTPException(status_code=400, detail="Stock insuficiente o objeto no encontrado")
    return prestamo

@router.put("/prestamos/{prestamo_id}/devolver", response_model=PrestamoObjetoResponse)
def devolver_prestamo(
    prestamo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "uniformes"]))
):
    prestamo = service.devolver_prestamo(db, prestamo_id)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado o ya devuelto")
    return prestamo