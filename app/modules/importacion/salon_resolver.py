import unicodedata
from sqlalchemy.orm import Session
from app.modules.salon.models import Salon
from app.modules.importacion.models import StagingEstudiante
from app.shared.models import PeriodoAcademico

class SalonResolverError(Exception):
    pass

class SalonResolverService:

    @staticmethod
    def normalizar_grado(grado_str: str) -> str:
        if not grado_str:
            raise SalonResolverError("Grado vacío")
        grado_str = str(grado_str).strip()
        # Eliminar tildes
        grado_str = ''.join(c for c in unicodedata.normalize('NFD', grado_str) if unicodedata.category(c) != 'Mn')
        # Eliminar espacios sobrantes y convertir a Title Case
        grado_str = ' '.join(grado_str.split())
        return grado_str.title()

    @staticmethod
    def normalizar_grupo(grupo_str: str) -> str:
        if not grupo_str:
            raise SalonResolverError("Grupo vacío")
        grupo_str = str(grupo_str)
        # Eliminar todos los espacios y convertir a mayúsculas
        grupo_str = "".join(grupo_str.split())
        return grupo_str.upper()

    @staticmethod
    def obtener_periodo_activo(db: Session) -> PeriodoAcademico:
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if not periodo:
            raise SalonResolverError("No existe un periodo acad\u00e9mico activo")
        return periodo

    @staticmethod
    def resolver_o_crear_salon(db: Session, grado_str: str, grupo_str: str, id_periodo: int, cache: dict) -> int:
        key = (grado_str, grupo_str, id_periodo)
        
        # 1. Buscar en cach\u00e9 local (evita duplicidad concurrente/en el mismo lote)
        if key in cache:
            return cache[key]
        
        # 2. Buscar en base de datos
        salon = db.query(Salon).filter(
            Salon.grado == grado_str,
            Salon.grupo == grupo_str,
            Salon.id_periodo == id_periodo
        ).first()

        if salon:
            cache[key] = salon.id_salon
            return salon.id_salon

        # 3. Crear el sal\u00f3n si no existe
        nuevo_salon = Salon(
            grado=grado_str,
            grupo=grupo_str,
            id_periodo=id_periodo
        )
        db.add(nuevo_salon)
        db.commit() # Important: commit to get the ID and avoid race conditions if used elsewhere
        db.refresh(nuevo_salon)
        
        cache[key] = nuevo_salon.id_salon
        return nuevo_salon.id_salon

    @staticmethod
    def procesar_staging_estudiantes(db: Session, ejecucion_id: int) -> dict:
        """
        Resuelve y asocia un id_salon a todos los registros de staging_estudiantes para la ejecuci\u00f3n dada.
        Retorna estad\u00edsticas.
        """
        try:
            periodo = SalonResolverService.obtener_periodo_activo(db)
        except SalonResolverError as e:
            return {"estado": "error", "mensaje": str(e)}

        estudiantes = db.query(StagingEstudiante).filter(
            StagingEstudiante.ejecucion_id == ejecucion_id,
            StagingEstudiante.id_salon == None
        ).all()

        if not estudiantes:
            return {"estado": "completado", "mensaje": "No hay estudiantes pendientes de resolver sal\u00f3n en esta ejecuci\u00f3n.", "procesados": 0}

        cache_salones = {}
        procesados = 0
        errores_mapeo = []

        for est in estudiantes:
            try:
                grado_str = SalonResolverService.normalizar_grado(est.grado)
                grupo_str = SalonResolverService.normalizar_grupo(est.curso)
                
                id_salon = SalonResolverService.resolver_o_crear_salon(
                    db, 
                    grado_str, 
                    grupo_str, 
                    periodo.id_periodo, 
                    cache_salones
                )
                
                est.id_salon = id_salon
                procesados += 1
            except SalonResolverError as e:
                errores_mapeo.append({"documento": est.documento, "grado": est.grado, "curso": est.curso, "error": str(e)})
        
        db.commit()
        
        return {
            "estado": "completado",
            "mensaje": f"Se resolvieron salones para {procesados} estudiantes.",
            "procesados": procesados,
            "salones_en_cache": len(cache_salones),
            "errores_mapeo": errores_mapeo
        }
