import sys
import traceback
import logging
from sqlalchemy.orm import Session
from app.core.security import desencriptar_texto
from app.modules.importacion.repositories.staging_repository import StagingRepository
from app.modules.importacion.schemas import CargaMasivaRequest, CargaIndividualRequest
from app.modules.secretaria.models import CredencialesLogin
from app.modules.importacion.scraper.autenticacion import autenticar
from app.modules.importacion.scraper.navegacion import navegar_y_generar_listado, navegar_pagina2_y_descargar_pdfs, navegar_y_descargar_docentes
from app.modules.importacion.scraper.extraccion import extraer_estudiantes, extraer_docentes, extraer_titulares_de_pdfs
from app.modules.importacion.salon_resolver import SalonResolverService

logger = logging.getLogger(__name__)

class ImportacionService:
    def __init__(self, db: Session):
        self.repo = StagingRepository(db)

    def ejecutar_carga_masiva(self, request: CargaMasivaRequest, usuario_id: int = None):
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="masiva", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        for idx, datos in enumerate(request.datos):
            try:
                if request.tipo == "estudiante":
                    self.repo.insertar_staging_estudiante(ejecucion.id, datos)
                    reg_est += 1
                elif request.tipo == "docente":
                    self.repo.insertar_staging_docente(ejecucion.id, datos)
                    reg_doc += 1
                else:
                    raise ValueError(f"Tipo desconocido: {request.tipo}")
            except Exception as e:
                errores += 1
                doc_ref = datos.get("documento") or f"Fila {idx}"
                self.repo.registrar_error(ejecucion.id, request.tipo, str(e), str(doc_ref))

        self.repo.finalizar_ejecucion(
            ejecucion_id=ejecucion.id,
            estado="completado" if errores == 0 else "completado_con_errores",
            reg_est=reg_est,
            reg_doc=reg_doc,
            errores=errores
        )

        if request.tipo == "estudiante" and reg_est > 0:
            SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

        return {"ejecucion_id": ejecucion.id, "estado": "completado", "insertados": reg_est + reg_doc, "errores": errores}

    def ejecutar_carga_individual(self, request: CargaIndividualRequest, usuario_id: int = None):
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="individual", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            if request.tipo == "estudiante":
                self.repo.insertar_staging_estudiante(ejecucion.id, request.datos)
                reg_est += 1
            elif request.tipo == "docente":
                self.repo.insertar_staging_docente(ejecucion.id, request.datos)
                reg_doc += 1
            else:
                raise ValueError(f"Tipo desconocido: {request.tipo}")
        except Exception as e:
            errores += 1
            doc_ref = request.datos.get("documento") or "Registro individual"
            self.repo.registrar_error(ejecucion.id, request.tipo, str(e), str(doc_ref))

        self.repo.finalizar_ejecucion(
            ejecucion_id=ejecucion.id,
            estado="completado" if errores == 0 else "error",
            reg_est=reg_est,
            reg_doc=reg_doc,
            errores=errores
        )

        if request.tipo == "estudiante" and reg_est > 0:
            SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

        return {"ejecucion_id": ejecucion.id, "estado": "completado" if errores == 0 else "error", "errores": errores}

    def _obtener_credenciales(self):
        credencial = self.repo.db.query(CredencialesLogin).first()
        if not credencial:
            raise ValueError("No hay credenciales configuradas en la base de datos para WebColegios. Por favor configúrelas primero.")
        return credencial

    def _procesar_estudiantes(self, ejecucion_id, url, usuario, password):
        reg_est = 0
        errores = 0
        
        logger.info("INICIO autenticar (estudiantes)")
        session = autenticar(url=url, usuario=usuario, password=password, tipo_usuario="Administrativo")
        if not session:
            raise Exception("Fallo la autenticacion en WebColegios")
        logger.info("FIN autenticar")

        logger.info("INICIO navegar_y_generar_listado")
        ruta_estudiantes_pdf = navegar_y_generar_listado(session, url, tipo_datos="Estudiantes")
        logger.info("FIN navegar_y_generar_listado")
        if not ruta_estudiantes_pdf:
            raise Exception("No se pudo obtener el listado de estudiantes")
        
        logger.info("INICIO extraer_estudiantes")
        estudiantes_extraidos = extraer_estudiantes(ruta_estudiantes_pdf)
        logger.info("FIN extraer_estudiantes")
        
        logger.info("INICIO insercion staging_estudiantes")
        for est in estudiantes_extraidos:
            try:
                self.repo.insertar_staging_estudiante(ejecucion_id, est)
                reg_est += 1
            except Exception as e:
                errores += 1
                self.repo.registrar_error(ejecucion_id, "estudiante", f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}", est.get("documento", ""))
        logger.info("FIN insercion staging_estudiantes")

        return reg_est, errores

    def _procesar_docentes(self, ejecucion_id, url, usuario, password):
        reg_doc = 0
        errores = 0

        logger.info("INICIO autenticar para FASE B (Titulares)")
        session = autenticar(url=url, usuario=usuario, password=password, tipo_usuario="Administrativo")
        if not session:
            raise Exception("Fallo la autenticacion en WebColegios para FASE B")
        logger.info("FIN autenticar para FASE B")
        
        logger.info("INICIO navegar_pagina2_y_descargar_pdfs")
        rutas_titulares = navegar_pagina2_y_descargar_pdfs(session, url)
        logger.info("FIN navegar_pagina2_y_descargar_pdfs")
        
        logger.info("INICIO extraer_titulares_de_pdfs")
        titulares = extraer_titulares_de_pdfs(rutas_titulares)
        logger.info("FIN extraer_titulares_de_pdfs")

        logger.info("INICIO navegar_y_descargar_docentes")
        ruta_docentes = navegar_y_descargar_docentes(session, url)
        logger.info("FIN navegar_y_descargar_docentes")
        if not ruta_docentes:
            raise Exception("No se pudo descargar listado de docentes")

        logger.info("INICIO extraer_docentes")
        docentes_extraidos = extraer_docentes(pdf_path=ruta_docentes, titulares=titulares)
        logger.info("FIN extraer_docentes")
        
        logger.info("INICIO insercion staging_docentes")
        for doc in docentes_extraidos:
            try:
                self.repo.insertar_staging_docente(ejecucion_id, doc)
                reg_doc += 1
            except Exception as e:
                errores += 1
                self.repo.registrar_error(ejecucion_id, "docente", f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}", doc.get("documento", ""))
        logger.info("FIN insercion staging_docentes")

        return reg_doc, errores

    def iniciar_scraping_estudiantes(self, usuario_id: int = None):
        import time
        inicio_perf = time.perf_counter()
        
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping_estudiantes", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            try:
                r_est, err = self._procesar_estudiantes(ejecucion.id, credencial.url, credencial.nombre_usuario, desencriptar_texto(credencial.password_hash))
                reg_est += r_est
                errores += err
                if r_est > 0:
                    SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)
            except Exception as ex_inner:
                logger.error(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}")
                raise ex_inner

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            logger.error(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}")
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        fin_perf = time.perf_counter()
        duracion = round(fin_perf - inicio_perf, 2)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores,
            "duracion_segundos": duracion
        }

    def iniciar_scraping_docentes(self, usuario_id: int = None):
        import time
        inicio_perf = time.perf_counter()
        
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping_docentes", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            try:
                r_doc, err = self._procesar_docentes(ejecucion.id, credencial.url, credencial.nombre_usuario, desencriptar_texto(credencial.password_hash))
                reg_doc += r_doc
                errores += err
            except Exception as ex_inner:
                logger.error(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}")
                raise ex_inner

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            logger.error(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}")
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        fin_perf = time.perf_counter()
        duracion = round(fin_perf - inicio_perf, 2)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores,
            "duracion_segundos": duracion
        }

    def iniciar_scraping(self, usuario_id: int = None):
        credencial = self._obtener_credenciales()
        ejecucion = self.repo.crear_ejecucion(tipo_ejecucion="scraping", usuario_id=usuario_id)
        
        reg_est = 0
        reg_doc = 0
        errores = 0

        try:
            try:
                # Estudiantes
                r_est, err1 = self._procesar_estudiantes(ejecucion.id, credencial.url, credencial.nombre_usuario, desencriptar_texto(credencial.password_hash))
                reg_est += r_est
                errores += err1
                if r_est > 0:
                    SalonResolverService.procesar_staging_estudiantes(self.repo.db, ejecucion.id)

                # Docentes
                r_doc, err2 = self._procesar_docentes(ejecucion.id, credencial.url, credencial.nombre_usuario, desencriptar_texto(credencial.password_hash))
                reg_doc += r_doc
                errores += err2

            except Exception as ex_inner:
                print(f"EXCEPCION INTERNA CAPTURADA: {type(ex_inner).__name__} - {str(ex_inner)}\n{traceback.format_exc()}", flush=True)
                raise ex_inner

            estado_final = "completado" if errores == 0 else "completado_con_errores"
        except Exception as ex:
            print(f"EXCEPCION EXTERNA CAPTURADA: {type(ex).__name__} - {str(ex)}\n{traceback.format_exc()}", flush=True)
            self.repo.registrar_error(ejecucion.id, "sistema", f"{type(ex).__name__}: {str(ex)}\n{traceback.format_exc()}")
            errores += 1
            estado_final = "error"

        self.repo.finalizar_ejecucion(ejecucion.id, estado_final, reg_est, reg_doc, errores)
        
        return {
            "ejecucion_id": ejecucion.id,
            "estado": estado_final,
            "registros_estudiantes": reg_est,
            "registros_docentes": reg_doc,
            "errores": errores
        }

    def obtener_ejecuciones(self, limit: int = 100, skip: int = 0):
        return self.repo.obtener_ejecuciones(limit, skip)

    def obtener_ejecucion(self, id: int):
        return self.repo.obtener_ejecucion(id)
        


    def sincronizar_estudiantes(self, ejecucion_id: int):
        from app.modules.estudiantes.models import Estudiante
        from app.modules.importacion.models import StagingEstudiante

        estudiantes_staging = self.repo.db.query(StagingEstudiante).filter(
            StagingEstudiante.ejecucion_id == ejecucion_id
        ).all()

        procesados = 0
        insertados = 0
        actualizados = 0
        rechazados = 0

        for stg in estudiantes_staging:
            procesados += 1
            try:
                # Validacion 1: id_salon NO puede ser NULL
                if stg.id_salon is None:
                    raise ValueError("id_salon es NULL")

                # Validacion 2: documento NO puede ser NULL
                if not stg.documento or str(stg.documento).strip() == "":
                    raise ValueError("documento es NULL o vacio")

                doc_str = str(stg.documento).strip()
                
                # Validacion 3: documento NO debe exceder 10 caracteres (sin truncar silenciosamente)
                if len(doc_str) > 10:
                    raise ValueError(f"documento excede 10 caracteres: '{doc_str}'")

                # Validacion 4: nombre puede truncarse a 100 caracteres
                nom_str = str(stg.nombre).strip() if stg.nombre else ""
                if len(nom_str) > 100:
                    nom_str = nom_str[:100]

                # Logica de Sincronizacion
                est_existente = self.repo.db.query(Estudiante).filter(Estudiante.documento == doc_str).first()
                if est_existente:
                    est_existente.nombre = nom_str
                    est_existente.id_salon = stg.id_salon
                    if stg.observaciones:
                        est_existente.telefono_acudiente = str(stg.observaciones)[:20]
                    actualizados += 1
                else:
                    nuevo_est = Estudiante(
                        documento=doc_str,
                        nombre=nom_str,
                        id_salon=stg.id_salon,
                        telefono_acudiente=str(stg.observaciones)[:20] if stg.observaciones else None
                    )
                    self.repo.db.add(nuevo_est)
                    insertados += 1
                
                # Commit individual para evitar que un fallo (FK o unique) afecte al lote completo
                self.repo.db.commit()

            except Exception as e:
                self.repo.db.rollback()
                rechazados += 1
                self.repo.registrar_error(
                    ejecucion_id=ejecucion_id,
                    tipo_origen="sincronizacion_estudiante",
                    mensaje=str(e),
                    registro_referencia=stg.documento
                )

        # Confirmar que el commit de inserciones fue exitoso (al procesarse individualmente ya est\u00e1 en BD).
        # Ahora procedemos con la limpieza de los registros temporales.
        try:
            self.repo.db.query(StagingEstudiante).filter(
                StagingEstudiante.ejecucion_id == ejecucion_id
            ).delete(synchronize_session=False)
            self.repo.db.commit()
        except Exception as e:
            self.repo.db.rollback()
            self.repo.registrar_error(ejecucion_id, "limpieza_staging", f"Fallo al limpiar staging: {str(e)}")

        return {
            "procesados": procesados,
            "insertados": insertados,
            "actualizados": actualizados,
            "rechazados": rechazados
        }

    def sincronizar_docentes(self, ejecucion_id: int):
        from app.modules.usuarios.models import Usuario, Rol, RolUsuario
        from app.modules.importacion.models import StagingDocente
        from app.modules.salon.models import Salon
        from app.modules.auth.service import hash_contra
        from app.modules.importacion.salon_resolver import SalonResolverService
        from app.shared.models import PeriodoAcademico

        # Paso 1: Verificacion de Rol Base "Titular"
        rol_titular = self.repo.db.query(Rol).filter(Rol.nombre == "Titular").first()
        if not rol_titular:
            rol_titular = Rol(nombre="Titular")
            self.repo.db.add(rol_titular)
            self.repo.db.commit()
            self.repo.db.refresh(rol_titular)

        # Pre-validacion de periodo activo
        periodo_activo = self.repo.db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()

        docentes_staging = self.repo.db.query(StagingDocente).filter(
            StagingDocente.ejecucion_id == ejecucion_id
        ).all()

        # Pre-escanear conflictos de titularidad en el lote
        # dict map: salon_key -> list of staging docs
        asignaciones_lote = {}
        for stg in docentes_staging:
            if stg.grado_titular and stg.curso_titular:
                try:
                    g_str = SalonResolverService.normalizar_grado(stg.grado_titular)
                    c_str = SalonResolverService.normalizar_grupo(stg.curso_titular)
                    s_key = f"{g_str}_{c_str}"
                    if s_key not in asignaciones_lote:
                        asignaciones_lote[s_key] = []
                    asignaciones_lote[s_key].append(stg)
                except Exception:
                    pass

        # Marcar conflictos
        for s_key, docs in asignaciones_lote.items():
            if len(docs) > 1:
                for doc in docs:
                    doc._has_conflict = True

        procesados = 0
        insertados = 0
        actualizados = 0
        roles_asignados = 0
        titularidades_asignadas = 0
        rechazados = 0

        for stg in docentes_staging:
            procesados += 1
            try:
                # Validacion de documento
                if not stg.documento or str(stg.documento).strip() == "":
                    raise ValueError("documento es NULL o vacio")

                doc_str = str(stg.documento).strip()
                if len(doc_str) > 10:
                    raise ValueError(f"documento excede 10 caracteres: '{doc_str}'")

                nom_str = str(stg.nombre).strip() if stg.nombre else ""
                if not nom_str:
                    raise ValueError("nombre es NULL o vacio")
                if len(nom_str) > 100:
                    nom_str = nom_str[:100]

                # Conflicto previo detectado en lote
                if getattr(stg, '_has_conflict', False):
                    raise ValueError("Conflicto de titularidad detectado en el mismo lote para el salon")

                # Paso 3: Resolver Usuario
                usuario = self.repo.db.query(Usuario).filter(Usuario.documento == doc_str).first()
                if usuario:
                    if usuario.nombre != nom_str:
                        usuario.nombre = nom_str
                    actualizados += 1
                else:
                    usuario = Usuario(
                        nombre=nom_str,
                        documento=doc_str,
                        estado=True,
                        contrasena=hash_contra(doc_str)
                    )
                    self.repo.db.add(usuario)
                    self.repo.db.flush() # flush to get id_usuario
                    insertados += 1

                # Paso 4: Asignar Rol Titular
                if usuario.id_usuario:
                    rol_exists = self.repo.db.query(RolUsuario).filter(
                        RolUsuario.id_usuario == usuario.id_usuario,
                        RolUsuario.id_rol == rol_titular.id_rol
                    ).first()
                    
                    if not rol_exists:
                        self.repo.db.add(RolUsuario(id_usuario=usuario.id_usuario, id_rol=rol_titular.id_rol))
                        roles_asignados += 1

                # Paso 5 & 6: Resolver Titularidad
                if stg.grado_titular and stg.curso_titular:
                    if not periodo_activo:
                        raise ValueError("No existe periodo academico activo para asignar titularidad")
                    
                    grado_str = SalonResolverService.normalizar_grado(stg.grado_titular)
                    grupo_str = SalonResolverService.normalizar_grupo(stg.curso_titular)
                    
                    # Buscar salon
                    salon = self.repo.db.query(Salon).filter(
                        Salon.grado == grado_str,
                        Salon.grupo == grupo_str,
                        Salon.id_periodo == periodo_activo.id_periodo
                    ).first()
                    
                    if not salon:
                        salon = Salon(
                            grado=grado_str,
                            grupo=grupo_str,
                            id_periodo=periodo_activo.id_periodo
                        )
                        self.repo.db.add(salon)
                        self.repo.db.flush()
                    
                    salon.id_usuario = usuario.id_usuario
                    titularidades_asignadas += 1

                stg.estado_validacion = "Sincronizado"
                self.repo.db.commit()

            except Exception as e:
                self.repo.db.rollback()
                rechazados += 1
                stg.estado_validacion = "Error"
                self.repo.registrar_error(
                    ejecucion_id=ejecucion_id,
                    tipo_origen="sincronizacion_docente",
                    mensaje=str(e),
                    registro_referencia=stg.documento
                )
                self.repo.db.commit() # commit the error state and error log

        # Paso 10: Limpieza de Staging
        try:
            self.repo.db.query(StagingDocente).filter(
                StagingDocente.ejecucion_id == ejecucion_id
            ).delete(synchronize_session=False)
            self.repo.db.commit()
        except Exception as e:
            self.repo.db.rollback()
            self.repo.registrar_error(ejecucion_id, "limpieza_staging_docente", f"Fallo al limpiar staging: {str(e)}")

        return {
            "procesados": procesados,
            "insertados": insertados,
            "actualizados": actualizados,
            "roles_asignados": roles_asignados,
            "titularidades_asignadas": titularidades_asignadas,
            "rechazados": rechazados
        }

    def cancelar_sincronizacion(self, ejecucion_id: int, tipo: str):
        from app.modules.importacion.models import StagingEstudiante, StagingDocente, EjecucionBot
        
        try:
            if tipo == "estudiante":
                self.repo.db.query(StagingEstudiante).filter(StagingEstudiante.ejecucion_id == ejecucion_id).delete(synchronize_session=False)
            elif tipo == "docente":
                self.repo.db.query(StagingDocente).filter(StagingDocente.ejecucion_id == ejecucion_id).delete(synchronize_session=False)
            
            # Cambiar estado de ejecucion a cancelado
            ejecucion = self.repo.db.query(EjecucionBot).filter(EjecucionBot.id == ejecucion_id).first()
            if ejecucion:
                ejecucion.estado = "cancelado"
                
            self.repo.db.commit()
            return {"mensaje": f"Importación cancelada exitosamente. Se han descartado los registros temporales de {tipo}."}
        except Exception as e:
            self.repo.db.rollback()
            raise Exception(f"Error al cancelar sincronización: {str(e)}")
