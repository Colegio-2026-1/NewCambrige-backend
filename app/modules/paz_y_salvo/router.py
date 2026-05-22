from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.modules.paz_y_salvo import service
from app.modules.paz_y_salvo.schemas import FirmasResponse, FirmasUpdate, EstadoPazSalvoResponse, RectoriaFirmaRequest, RectoriaFirmaResponse, EstudiantePendienteResponse
from app.modules.auth.deps import require_roles
from app.modules.usuarios.models import Usuario

router = APIRouter()

@router.get("/estudiante/{estudiante_id}", response_model=EstadoPazSalvoResponse)
def obtener_estado_paz_salvo(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria", "rectoria"]))
):
    resultado = service.get_estado_completo(db, estudiante_id, periodo_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Estudiante o periodo no encontrado")
    return resultado

@router.get("/sin-firmar/periodo/{periodo_id}")
def estudiantes_sin_firmas(
    periodo_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "rectoria"]))
):
    return service.get_sin_firmas(db, periodo_id)

@router.get("/firmas/{estudiante_id}", response_model=FirmasResponse)
def obtener_firmas(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria"]))
):
    firmas = service.get_firmas(db, estudiante_id, periodo_id)
    if not firmas:
        raise HTTPException(status_code=404, detail="No se encontraron firmas")
    return firmas

@router.put("/firmas/{estudiante_id}", response_model=FirmasResponse)
def actualizar_firmas(
    estudiante_id: int,
    data: FirmasUpdate,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "secretaria", "tesoreria", "rectoria"]))
):
    
    data_dict = data.model_dump(exclude_unset=True)
    if data_dict.get("rectoria") is True:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La firma de Rectoría debe hacerse desde POST /api/paz-salvo/rectoria/{estudiante_id}")

    firmas = service.update_firmas(db, estudiante_id, periodo_id, data.model_dump(exclude_unset=True))
    if not firmas:
        raise HTTPException(status_code=404, detail="Estudiante o periodo no encontrado")
    return firmas

@router.post("/rectoria/{estudiante_id}", response_model=RectoriaFirmaResponse, summary="Firma final de Rectoría")
def firmar_rectoria(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    body: Optional[RectoriaFirmaRequest] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    resultado = service.firmar_rectoria(
        db=db,
        estudiante_id=estudiante_id,
        usuario_nombre=current_user.nombre,
        periodo_id=periodo_id,
    )

    if "error" in resultado:
        raise HTTPException(status_code=resultado.get("codigo", 400), detail=resultado["error"])

    return resultado

@router.get("/pendientes", response_model=List[EstudiantePendienteResponse], summary="Estudiantes con paz y salvo pendiente")
def listar_pendientes(
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "secretaria", "rectoria"])),
):
    return service.get_pendientes(db, periodo_id)