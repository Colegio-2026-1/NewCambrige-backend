from sqlalchemy.orm import Session
from typing import Optional, List
from app.modules.estudiantes.models import Estudiante
from app.modules.rectoria.models import FirmasPazYSalvo
from app.shared.models import PeriodoAcademico

def registrar_pago(db: Session, estudiante_id: int, periodo_id: Optional[int] = None) -> Optional[dict]:
    if not periodo_id:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
    
    firmas = db.query(FirmasPazYSalvo).filter(
        FirmasPazYSalvo.id_estudiante == estudiante_id,
        FirmasPazYSalvo.id_periodo == periodo_id
    ).first()
    
    if not firmas:
        firmas = FirmasPazYSalvo(
            id_estudiante=estudiante_id,
            id_periodo=periodo_id,
            tesoreria=True
        )
        db.add(firmas)
    else:
        firmas.tesoreria = True
    
    db.commit()
    
    return {
        "id_estudiante": estudiante_id,
        "id_periodo": periodo_id,
        "tesoreria_firmada": True,
        "fecha": firmas.updated_at
    }

def obtener_pagos_pendientes(db: Session, periodo_id: Optional[int] = None) -> List[dict]:
    if not periodo_id:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if not periodo:
            return []
        periodo_id = periodo.id_periodo
    
    estudiantes = db.query(Estudiante).all()
    pendientes = []
    
    for e in estudiantes:
        firmas = db.query(FirmasPazYSalvo).filter(
            FirmasPazYSalvo.id_estudiante == e.id_estudiante,
            FirmasPazYSalvo.id_periodo == periodo_id
        ).first()
        
        if not firmas or not firmas.tesoreria:
            pendientes.append({
                "id_estudiante": e.id_estudiante,
                "nombre": e.nombre,
                "telefono_acudiente": e.telefono_acudiente
            })
    
    return pendientes