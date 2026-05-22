from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.modules.secretaria import service
from app.modules.secretaria.schemas import (
    MatriculaResponse, MatriculaCreate, MatriculaUpdate,
    DetalleMatriculaResponse, DetalleMatriculaCreate, DetalleMatriculaUpdate,
    TipoConceptoResponse, TipoConceptoCreate
)
from app.modules.auth.deps import require_roles

router = APIRouter()

# ============ MATRÍCULAS ============
@router.get("/matriculas", response_model=List[MatriculaResponse])
def listar_matriculas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "titular"]))
):
    return service.get_matriculas_all(db, skip, limit)

@router.get("/matriculas/estudiante/{estudiante_id}", response_model=List[MatriculaResponse])
def matriculas_por_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "titular"]))
):
    return service.get_matriculas_por_estudiante(db, estudiante_id)

@router.get("/matriculas/periodo/{periodo_id}", response_model=List[MatriculaResponse])
def matriculas_por_periodo(
    periodo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "titular"]))
):
    return service.get_matriculas_por_periodo(db, periodo_id)

@router.get("/matriculas/pendientes", response_model=List[MatriculaResponse])
def matriculas_pendientes(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.get_matriculas_pendientes(db)

@router.get("/matriculas/{matricula_id}", response_model=MatriculaResponse)
def obtener_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "titular"]))
):
    matricula = service.get_matricula_by_id(db, matricula_id)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula

@router.post("/matriculas", response_model=MatriculaResponse, status_code=status.HTTP_201_CREATED)
def crear_matricula(
    data: MatriculaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.create_matricula(db, data.model_dump())

@router.put("/matriculas/{matricula_id}", response_model=MatriculaResponse)
def actualizar_matricula(
    matricula_id: int,
    data: MatriculaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    matricula = service.update_matricula(db, matricula_id, data.model_dump(exclude_unset=True))
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula

@router.delete("/matriculas/{matricula_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    matricula = service.cancelar_matricula(db, matricula_id)
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

# ============ DETALLES DE MATRÍCULA ============
@router.get("/detalles-matricula/matricula/{matricula_id}", response_model=List[DetalleMatriculaResponse])
def detalles_por_matricula(
    matricula_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "titular"]))
):
    return service.get_detalles_by_matricula(db, matricula_id)

@router.get("/detalles-matricula/{detalle_id}", response_model=DetalleMatriculaResponse)
def obtener_detalle(
    detalle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    detalle = service.get_detalle_by_id(db, detalle_id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    return detalle

@router.post("/detalles-matricula", response_model=DetalleMatriculaResponse, status_code=status.HTTP_201_CREATED)
def crear_detalle(
    data: DetalleMatriculaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.create_detalle(db, data.model_dump())

@router.put("/detalles-matricula/{detalle_id}", response_model=DetalleMatriculaResponse)
def actualizar_detalle(
    detalle_id: int,
    data: DetalleMatriculaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    detalle = service.update_detalle(db, detalle_id, data.model_dump(exclude_unset=True))
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
    return detalle

@router.delete("/detalles-matricula/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_detalle(
    detalle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    if not service.delete_detalle(db, detalle_id):
        raise HTTPException(status_code=404, detail="Detalle no encontrado")

# ============ TIPOS DE CONCEPTO ============
@router.get("/tipos-concepto", response_model=List[TipoConceptoResponse])
def listar_tipos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria"]))
):
    return service.get_tipos_all(db, skip, limit)

@router.post("/tipos-concepto", response_model=TipoConceptoResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo(
    data: TipoConceptoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    return service.create_tipo(db, data.model_dump())

@router.put("/tipos-concepto/{tipo_id}", response_model=TipoConceptoResponse)
def actualizar_tipo(
    tipo_id: int,
    data: TipoConceptoCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    tipo = service.update_tipo(db, tipo_id, data.model_dump(exclude_unset=True))
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    return tipo

@router.delete("/tipos-concepto/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo(
    tipo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    if not service.delete_tipo(db, tipo_id):
        raise HTTPException(status_code=404, detail="Tipo no encontrado")