from sqlalchemy.orm import Session
from typing import Optional, List
from app.shared.models import PeriodoAcademico, Auditoria
from app.modules.estudiantes.models import Estudiante
from app.modules.rectoria.models import FirmasPazYSalvo
from datetime import datetime
from app.modules.paz_y_salvo.schemas import (
    SemaforoEstado,
    DetalleFirma,
    EstadoPazSalvoResponse,
    EstudiantePendienteResponse,
    FirmasBase,
)

CAMPOS_FIRMAS = ["biblioteca", "tesoreria", "uniforme", "salon", "rectoria"]

DETALLE_FIRMAS_CONFIG = [
    {"campo": "biblioteca", "nombre": "Biblioteca", "rol": "titular"},
    {"campo": "tesoreria",  "nombre": "Tesorería",  "rol": "tesoreria"},
    {"campo": "uniforme",   "nombre": "Uniforme",   "rol": "titular"},
    {"campo": "salon",      "nombre": "Salón",      "rol": "titular"},
    {"campo": "rectoria",   "nombre": "Rectoría",   "rol": "rectoria"},
]
 

def _get_periodo_activo(db: Session) -> Optional[PeriodoAcademico]:
    return db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()

def _calcular_semaforo(firmas: FirmasPazYSalvo) -> str:
    valores = [getattr(firmas, c) for c in CAMPOS_FIRMAS]
    total_true = sum(valores)
    if total_true == len(CAMPOS_FIRMAS):
        return SemaforoEstado.VERDE
    elif total_true > 0:
        return SemaforoEstado.AMARILLO
    else:
        return SemaforoEstado.ROJO

def _construir_detalle_firmas(firmas: FirmasPazYSalvo) -> list:
    return [
        DetalleFirma(
            nombre=config["nombre"],
            firmado=getattr(firmas, config["campo"]),
            rol_responsable=config["rol"],
        )
        for config in DETALLE_FIRMAS_CONFIG
    ]

def _registrar_auditoria(db: Session, usuario: str, accion: str, tabla: str, id_registro: int) -> None:
    entrada = Auditoria(
        tabla=tabla,
        id_registro=id_registro,
        accion=accion,
        usuario=usuario,
        fecha=datetime.utcnow(),
    )
    db.add(entrada)



def get_firmas(db: Session, estudiante_id: int, periodo_id: Optional[int] = None) -> Optional[FirmasPazYSalvo]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
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
            id_periodo=periodo_id
        )
        db.add(firmas)
        db.commit()
        db.refresh(firmas)
    
    return firmas

def get_estado_completo(db: Session, estudiante_id: int, periodo_id: Optional[int] = None) -> Optional[dict]:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return None
    
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
        periodo_nombre = periodo.nombre
    else:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == periodo_id).first()
        periodo_nombre = periodo.nombre if periodo else None
    
    firmas = get_firmas(db, estudiante_id, periodo_id)
    
    firmas_dict = {
        "biblioteca": firmas.biblioteca,
        "tesoreria": firmas.tesoreria,
        "uniforme": firmas.uniforme,
        "salon": firmas.salon,
        "rectoria": firmas.rectoria
    }
    
    todas_firmadas = all(firmas_dict.values())
    completadas    = sum(firmas_dict.values())
    
    return {
        "id_estudiante": estudiante_id,
        "nombre": estudiante.nombre,
        "id_periodo": periodo_id,
        "periodo_nombre": periodo_nombre,
        "firmas": firmas_dict,
        "todas_firmadas": todas_firmadas,
        "puede_retirarse": todas_firmadas,
        "semaforo":          _calcular_semaforo(firmas),
        "detalle_firmas":    _construir_detalle_firmas(firmas),
        "firmas_completadas": completadas,
        "total_firmas":      len(CAMPOS_FIRMAS),
    }

def update_firmas(db: Session, estudiante_id: int, periodo_id: Optional[int], data: dict) -> Optional[FirmasPazYSalvo]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo
    
    firmas = get_firmas(db, estudiante_id, periodo_id)
    
    for key, value in data.items():
        if value is not None:
            setattr(firmas, key, value)
    
    db.commit()
    db.refresh(firmas)
    return firmas


def get_sin_firmas(db: Session, periodo_id: Optional[int] = None) -> List[dict]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return []
        periodo_id = periodo.id_periodo
    
    estudiantes = db.query(Estudiante).all()
    resultado = []
    
    for e in estudiantes:
        firmas = db.query(FirmasPazYSalvo).filter(
            FirmasPazYSalvo.id_estudiante == e.id_estudiante,
            FirmasPazYSalvo.id_periodo == periodo_id
        ).first()
        
        if not firmas:
            resultado.append({"id_estudiante": e.id_estudiante, "nombre": e.nombre, "faltan": "todas"})
        else:
            faltantes = []
            if not firmas.biblioteca: faltantes.append("biblioteca")
            if not firmas.tesoreria: faltantes.append("tesoreria")
            if not firmas.uniforme: faltantes.append("uniforme")
            if not firmas.salon: faltantes.append("salon")
            if not firmas.rectoria: faltantes.append("rectoria")
            if faltantes:
                resultado.append({"id_estudiante": e.id_estudiante, "nombre": e.nombre, "faltan": faltantes})
    
    return resultado


def actualizar_firma(db: Session, estudiante_id: int, data: dict, usuario_nombre: str, periodo_id: Optional[int] = None) -> Optional[FirmasPazYSalvo]:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return None

    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return None
        periodo_id = periodo.id_periodo

    firmas = get_firmas(db, estudiante_id, periodo_id)

    campos_actualizados = []
    for campo, valor in data.items():
        if valor is not None and hasattr(firmas, campo):
            setattr(firmas, campo, valor)
            campos_actualizados.append(f"{campo}={valor}")

    _registrar_auditoria(
        db=db,
        usuario=usuario_nombre,
        accion=f"FIRMA: {', '.join(campos_actualizados)}"[:50],
        tabla="firmas_paz_y_salvo",
        id_registro=firmas.id_firma,
    )

    db.commit()
    db.refresh(firmas)
    return firmas


def firmar_rectoria(db: Session, estudiante_id: int, usuario_nombre: str, periodo_id: Optional[int] = None) -> dict:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return {"error": "Estudiante no encontrado", "codigo": 404}

    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return {"error": "No hay periodo académico activo", "codigo": 400}
        periodo_id = periodo.id_periodo

    firmas = get_firmas(db, estudiante_id, periodo_id)

    firmas_previas = ["biblioteca", "tesoreria", "uniforme", "salon"]
    nombres_display = {
        "biblioteca": "Biblioteca",
        "tesoreria":  "Tesorería",
        "uniforme":   "Uniforme",
        "salon":      "Salón",
    }
    faltantes = [c for c in firmas_previas if not getattr(firmas, c)]

    if faltantes:
        return {
            "error": f"No se puede firmar. Hay módulos pendientes: {', '.join(nombres_display[f] for f in faltantes)}",
            "codigo": 400,
        }

    if firmas.rectoria:
        return {"error": "Este estudiante ya tiene la firma de Rectoría.", "codigo": 400}

    firmas.rectoria = True

    _registrar_auditoria(
        db=db,
        usuario=usuario_nombre,
        accion="FIRMA_RECTORIA",
        tabla="firmas_paz_y_salvo",
        id_registro=firmas.id_firma,
    )

    db.commit()
    db.refresh(firmas)

    return {
        "mensaje": f"Paz y salvo de {estudiante.nombre} firmado correctamente por Rectoría.",
        "id_estudiante": estudiante_id,
        "nombre_estudiante": estudiante.nombre,
        "paz_y_salvo_completo": True,
        "fecha_firma": datetime.utcnow(),
    }

def get_pendientes(db: Session, periodo_id: Optional[int] = None) -> List[dict]:
    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return []
        periodo_id = periodo.id_periodo

    estudiantes = db.query(Estudiante).all()
    resultado = []

    for estudiante in estudiantes:
        firmas = get_firmas(db, estudiante.id_estudiante, periodo_id)
        faltantes = [c for c in CAMPOS_FIRMAS if not getattr(firmas, c)]

        if faltantes:
            completadas = len(CAMPOS_FIRMAS) - len(faltantes)
            resultado.append(EstudiantePendienteResponse(
                id_estudiante=estudiante.id_estudiante,
                nombre=estudiante.nombre,
                semaforo=_calcular_semaforo(firmas),
                firmas_faltantes=faltantes,
                firmas_completadas=completadas,
                total_firmas=len(CAMPOS_FIRMAS),
            ))

    return resultado