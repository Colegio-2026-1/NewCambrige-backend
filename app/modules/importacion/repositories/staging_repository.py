from sqlalchemy.orm import Session
from app.modules.importacion.models import EjecucionBot, StagingEstudiante, StagingDocente
from app.modules.importacion.scraper.logger import get_logger

logger = get_logger("importacion_repo")

class StagingRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_ejecucion(self, tipo_ejecucion: str, usuario_id: int = None) -> EjecucionBot:
        ejecucion = EjecucionBot(estado="iniciado", tipo_ejecucion=tipo_ejecucion, usuario_id=usuario_id)
        self.db.add(ejecucion)
        self.db.commit()
        self.db.refresh(ejecucion)
        return ejecucion

    def finalizar_ejecucion(self, ejecucion_id: int, estado: str, reg_est: int, reg_doc: int, errores: int):
        ejecucion = self.db.query(EjecucionBot).filter(EjecucionBot.id == ejecucion_id).first()
        if ejecucion:
            ejecucion.estado = estado
            from sqlalchemy.sql import func
            ejecucion.fecha_fin = func.now()
            ejecucion.registros_estudiantes = reg_est
            ejecucion.registros_docentes = reg_doc
            ejecucion.errores = errores
            self.db.commit()
            self.db.refresh(ejecucion)

    def registrar_error(self, ejecucion_id: int, tipo_origen: str, mensaje: str, registro_referencia: str = None):
        logger.error(f"Ejecucion [{ejecucion_id}] | {tipo_origen} | Ref: {registro_referencia or 'N/A'} | {mensaje}")

    def insertar_staging_estudiante(self, ejecucion_id: int, datos: dict):
        st = StagingEstudiante(
            ejecucion_id=ejecucion_id,
            documento=datos.get("documento"),
            nombre=datos.get("nombre"),
            grado=datos.get("grado"),
            curso=datos.get("curso"),
            jornada=datos.get("jornada")
        )
        self.db.add(st)
        self.db.commit()

    def insertar_staging_docente(self, ejecucion_id: int, datos: dict):
        st = StagingDocente(
            ejecucion_id=ejecucion_id,
            documento=datos.get("documento"),
            nombre=datos.get("nombre"),
            grado_titular=datos.get("grado_titular") or datos.get("grado"),
            curso_titular=datos.get("curso_titular") or datos.get("curso")
        )
        self.db.add(st)
        self.db.commit()

    def obtener_ejecuciones(self, limit: int = 100, skip: int = 0):
        return self.db.query(EjecucionBot).order_by(EjecucionBot.id.desc()).offset(skip).limit(limit).all()
        
    def obtener_ejecucion(self, ejecucion_id: int):
        return self.db.query(EjecucionBot).filter(EjecucionBot.id == ejecucion_id).first()
