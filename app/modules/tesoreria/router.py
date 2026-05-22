from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.modules.tesoreria import service
from app.modules.auth.deps import require_roles
from app.modules.rectoria.models import FirmasPazYSalvo
router = APIRouter()

@router.post("/registrar-pago")
def registrar_pago(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "tesoreria"]))
):
    resultado = service.registrar_pago(db, estudiante_id, periodo_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Estudiante o periodo no encontrado")
    return resultado

@router.get("/pagos-pendientes")
def pagos_pendientes(
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "tesoreria", "secretaria"]))
):
    return service.obtener_pagos_pendientes(db, periodo_id)

@router.get("/estudiante/{estudiante_id}/pagos")
def pagos_estudiante(
    estudiante_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "tesoreria", "secretaria"]))
):
    firmas = db.query(FirmasPazYSalvo).filter(
        FirmasPazYSalvo.id_estudiante == estudiante_id
    ).all()
    return [
        {
            "id_periodo": f.id_periodo,
            "pagado": f.tesoreria,
            "fecha": f.updated_at
        }
        for f in firmas
    ]