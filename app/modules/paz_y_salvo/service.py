from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.shared.models import PeriodoAcademico, Auditoria
from app.modules.estudiantes.models import Estudiante, EstudianteBanda
from app.modules.paz_y_salvo.models import FirmasPazYSalvo, TipoFirma, DetalleFirmaPazYSalvo, ResponsableFirma
from app.modules.uniformes.models import PrestamoObjeto
from app.modules.paz_y_salvo.schemas import SemaforoEstado, DetalleFirma
from app.modules.salon.models import Salon, Prueba, Pupitre, PrestamoLibro
from app.modules.banda.models import PrestamoInstrumento
from app.modules.tesoreria.models import Matricula, DetalleMatricula
from app.modules.usuarios.models import Usuario, RolUsuario, Rol
from app.shared.pdf_generator import generar_pdf_paz_salvo
from datetime import datetime
from app.core.config import settings
import hashlib, os, hmac

FIRMA_DIR = "app/modules/paz_y_salvo/firmas"
SELLO_PATH = f"{FIRMA_DIR}/Sello.png"

FIRMA_PATH_MAP = {
    "banda":        f"{FIRMA_DIR}/Firma_Banda.png",
    "coordinadora": f"{FIRMA_DIR}/Firma_Coordinadora.png",
    "uniforme":     f"{FIRMA_DIR}/Firma_Uniformes.png",
    "titular":      f"{FIRMA_DIR}/Firma_Titular.png",
    "secretaria":   f"{FIRMA_DIR}/Firma_Secretaría.png",
    "rectoria":     f"{FIRMA_DIR}/Firma_Rectoría.png",
}

_firma_hmacs: dict = {}

def _compute_file_hmac(path: str) -> str:
    with open(path, "rb") as f:
        content = f.read()
    return hmac.new(settings.SECRET_KEY.encode(), content, hashlib.sha256).hexdigest()

def _init_firma_hmacs():
    hmacs = {}
    for path in FIRMA_PATH_MAP.values():
        if os.path.exists(path):
            hmacs[path] = _compute_file_hmac(path)
    if os.path.exists(SELLO_PATH):
        hmacs[SELLO_PATH] = _compute_file_hmac(SELLO_PATH)
    return hmacs

_firma_hmacs = _init_firma_hmacs()

def _verify_firma_integrity(path: str) -> bool:
    if not os.path.exists(path):
        return False
    expected = _firma_hmacs.get(path)
    if expected is None:
        _firma_hmacs[path] = _compute_file_hmac(path)
        return True
    current = _compute_file_hmac(path)
    return current == expected

CAMPOS_FIRMAS = ["banda", "coordinadora", "uniforme", "salon", "secretaria", "rectoria"]

CAMPO_TIPO_MAP = {
    "banda": "banda",
    "coordinadora": "coordinadora",
    "uniforme": "uniforme",
    "salon": "titular",
    "secretaria": "secretaria",
    "rectoria": "rectoria",
}

DETALLE_FIRMAS_CONFIG = [
    {"campo": "rectoria",     "nombre": "rectoria",     "rol": "rectoria"},
    {"campo": "coordinadora", "nombre": "coordinadora", "rol": "coordinadora"},
    {"campo": "salon",        "nombre": "titular",      "rol": "titular"},
    {"campo": "banda",        "nombre": "banda",        "rol": "banda"},
    {"campo": "uniforme",     "nombre": "uniforme",     "rol": "uniformes"},
    {"campo": "secretaria",   "nombre": "secretaria",   "rol": "secretaria"},
]
 

def _get_periodo_activo(db: Session) -> Optional[PeriodoAcademico]:
    return db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()

def _get_detalle(firma, tipo_nombre):
    for d in firma.detalles:
        if d.tipo_firma.nombre == tipo_nombre:
            return d
    return None

def _get_valor_campo(firma, campo):
    tipo_nombre = CAMPO_TIPO_MAP.get(campo)
    if not tipo_nombre:
        return False
    d = _get_detalle(firma, tipo_nombre)
    return d.estado if d else False

def _hash_sello() -> str:
    if os.path.exists(SELLO_PATH):
        with open(SELLO_PATH, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    return ""

def obtener_firma_modulo(nombre_modulo: str, db: Session, usuario_id: Optional[int] = None) -> dict:
    tipo = db.query(TipoFirma).filter(TipoFirma.nombre == nombre_modulo).first()
    if tipo and usuario_id:
        resp = db.query(ResponsableFirma).filter(
            ResponsableFirma.id_tipo_firma == tipo.id_tipo_firma,
            ResponsableFirma.id_usuario == usuario_id,
            ResponsableFirma.ruta_firma.isnot(None)
        ).first()
        if resp and os.path.exists(resp.ruta_firma) and _verify_firma_integrity(resp.ruta_firma):
            return {"ruta": resp.ruta_firma}
    ruta = FIRMA_PATH_MAP.get(nombre_modulo)
    if ruta and os.path.exists(ruta) and _verify_firma_integrity(ruta):
        return {"ruta": ruta}
    return {"error": f"Firma no encontrada para {nombre_modulo}"}

def _get_no_aplica(db: Session, estudiante_id: int) -> set:
    no_aplica = set()

    en_banda = db.query(EstudianteBanda).filter(
        EstudianteBanda.id_estudiante == estudiante_id,
        EstudianteBanda.activo == True
    ).first()
    if not en_banda:
        no_aplica.add("banda")
    
    return no_aplica

def _calcular_semaforo(firmas_dict: dict, no_aplica: set) -> str:
    campos_que_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
    if not campos_que_aplican:
        return SemaforoEstado.VERDE
    valores = [firmas_dict[c] for c in campos_que_aplican]
    total_true = sum(v for v in valores if v)
    if total_true == len(campos_que_aplican):
        return SemaforoEstado.VERDE
    elif total_true > 0:
        return SemaforoEstado.AMARILLO
    else:
        return SemaforoEstado.ROJO

def _construir_detalle_firmas(firmas_dict: dict, no_aplica: set, firmas_obj=None) -> list:
    result = []
    for config in DETALLE_FIRMAS_CONFIG:
        tipo_nombre = config["nombre"]
        id_usuario_firmante = None
        if firmas_obj:
            d = _get_detalle(firmas_obj, tipo_nombre)
            if d:
                id_usuario_firmante = d.id_usuario_firmante
        result.append(
            DetalleFirma(
                nombre=tipo_nombre,
                firmado=config["campo"] in no_aplica or firmas_dict.get(config["campo"], False),
                rol_responsable=config["rol"],
                no_aplica=config["campo"] in no_aplica,
                id_usuario_firmante=id_usuario_firmante,
            )
        )
    return result

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
    
    firmas = db.query(FirmasPazYSalvo).options(
        joinedload(FirmasPazYSalvo.detalles).joinedload(DetalleFirmaPazYSalvo.tipo_firma)
    ).filter(
        FirmasPazYSalvo.id_estudiante == estudiante_id,
        FirmasPazYSalvo.id_periodo == periodo_id
    ).first()
    
    if firmas:
        tipos = db.query(TipoFirma).all()
        tipos_existentes = {d.id_tipo_firma for d in firmas.detalles}
        nuevos = [t for t in tipos if t.id_tipo_firma not in tipos_existentes]
        for t in nuevos:
            db.add(DetalleFirmaPazYSalvo(id_firma=firmas.id_firma, id_tipo_firma=t.id_tipo_firma, estado=False))
        if nuevos:
            db.commit()
            firmas = db.query(FirmasPazYSalvo).options(
                joinedload(FirmasPazYSalvo.detalles).joinedload(DetalleFirmaPazYSalvo.tipo_firma)
            ).filter(FirmasPazYSalvo.id_firma == firmas.id_firma).first()

    if not firmas:
        firmas = FirmasPazYSalvo(
            id_estudiante=estudiante_id,
            id_periodo=periodo_id
        )
        db.add(firmas)
        db.flush()
        tipos = db.query(TipoFirma).all()
        for t in tipos:
            db.add(DetalleFirmaPazYSalvo(id_firma=firmas.id_firma, id_tipo_firma=t.id_tipo_firma, estado=False))
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
    no_aplica = _get_no_aplica(db, estudiante_id)
    
    firmas_dict = {
        c: _get_valor_auto(firmas, c, db, estudiante_id, periodo_id) for c in CAMPOS_FIRMAS
    }
    
    campos_que_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
    completadas = sum(1 for c in campos_que_aplican if firmas_dict[c])
    todas_firmadas = completadas == len(campos_que_aplican)

    
    return {
        "id_estudiante": estudiante_id,
        "nombre": estudiante.nombre,
        "documento": estudiante.documento,
        "id_periodo": periodo_id,
        "periodo_nombre": periodo_nombre,
        "firmas": firmas_dict,
        "todas_firmadas": todas_firmadas,
        "puede_retirarse": todas_firmadas,
        "semaforo":          _calcular_semaforo(firmas_dict, no_aplica),
        "detalle_firmas":    _construir_detalle_firmas(firmas_dict, no_aplica, firmas),
        "firmas_completadas": completadas,
        "total_firmas":      len(campos_que_aplican),
    }

def firmar_rectoria(db: Session, estudiante_id: int, usuario_nombre: str, periodo_id: Optional[int] = None, usuario_id: int = None) -> dict:
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    if not estudiante:
        return {"error": "Estudiante no encontrado", "codigo": 404}

    if not periodo_id:
        periodo = _get_periodo_activo(db)
        if not periodo:
            return {"error": "No hay periodo académico activo", "codigo": 400}
        periodo_id = periodo.id_periodo

    firmas = get_firmas(db, estudiante_id, periodo_id)
    no_aplica = _get_no_aplica(db, estudiante_id)

    firmas_previas = ["banda", "coordinadora", "uniforme", "salon", "secretaria"]
    modulos_autocompletados = []
    for campo in firmas_previas:
        tipo_nombre = CAMPO_TIPO_MAP.get(campo)
        d = _get_detalle(firmas, tipo_nombre)
        if d and not d.estado:
            d.estado = True
            if usuario_id:
                d.id_usuario_firmante = usuario_id
            modulos_autocompletados.append(campo)

    if modulos_autocompletados:
        _registrar_auditoria(
            db=db, usuario=usuario_nombre,
            accion="FIRMA_RECTORIA_AUTOCOMPLETE",
            tabla="firmas_paz_y_salvo",
            id_registro=firmas.id_firma,
        )

    d_rect = _get_detalle(firmas, "rectoria")
    if not d_rect:
        return {"error": "Error interno", "codigo": 500}
    if d_rect.estado:
        return {"error": "Este estudiante ya tiene la firma de Rectoría.", "codigo": 400}
    d_rect.estado = True
    if usuario_id:
        d_rect.id_usuario_firmante = usuario_id

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

def obtener_sello() -> dict:
    if not os.path.exists(SELLO_PATH):
        return {"error": "Sello no encontrado"}
    if not _verify_firma_integrity(SELLO_PATH):
        return {"error": "Sello manipulado"}
    return {"ruta": SELLO_PATH, "hash": _hash_sello()}

def _auto_banda(db: Session, estudiante_id: int) -> Optional[bool]:
    asociado = db.query(EstudianteBanda).filter(
        EstudianteBanda.id_estudiante == estudiante_id,
        EstudianteBanda.activo == True
    ).first()
    if not asociado:
        return None 
    
    pendiente = db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante == estudiante_id,
        PrestamoInstrumento.estado_entrega == "prestado"
    ).first()
    return pendiente is None

def _auto_uniforme(db: Session, estudiante_id: int) -> bool:
    pendiente = db.query(PrestamoObjeto).filter(
        PrestamoObjeto.id_estudiante == estudiante_id,
        PrestamoObjeto.estado_prestamo == "prestado"
    ).first()
    return pendiente is None

def _auto_salon(db: Session, estudiante_id: int) -> bool:
    if not db.query(Prueba).filter(
        Prueba.id_estudiante == estudiante_id,
        Prueba.estado == "visto"
    ).first():
        return False
    if not db.query(Pupitre).filter(
        Pupitre.id_estudiante == estudiante_id,
        Pupitre.estado == "visto"
    ).first():
        return False
    if db.query(PrestamoLibro).filter(
        PrestamoLibro.id_estudiante == estudiante_id,
        PrestamoLibro.estado == "Prestado"
    ).first():
        return False
    return True
    
def _auto_secretaria(db: Session, estudiante_id: int, periodo_id: int) -> bool:
    matricula = db.query(Matricula).filter(
        Matricula.id_estudiante == estudiante_id,
        Matricula.id_periodo == periodo_id
    ).first()
    if not matricula:
        return False
    pendiente = db.query(DetalleMatricula).filter(
        DetalleMatricula.id_matricula == matricula.id_matricula,
        DetalleMatricula.estado.in_(["pendiente", "activa"])
    ).first()
    return pendiente is None

def _auto_coordinadora(db: Session, estudiante_id: int, periodo_id: int, firma: FirmasPazYSalvo) -> bool:
    campos_requeridos = ["banda", "uniforme", "secretaria", "salon"]
    for c in campos_requeridos:
        if not _get_valor_auto(firma, c, db, estudiante_id, periodo_id):
            return False
    return True

def _get_valor_auto(firma: FirmasPazYSalvo, campo: str, db: Session, estudiante_id: int, periodo_id: int) -> bool:
    if _get_valor_campo(firma, campo):
        return True
    if campo == "banda":
        auto = _auto_banda(db, estudiante_id)
        return auto if auto is not None else False
    elif campo == "uniforme":
        return _auto_uniforme(db, estudiante_id)
    elif campo == "coordinadora":
        return _auto_coordinadora(db, estudiante_id, periodo_id, firma)
    elif campo == "salon":
        return _auto_salon(db, estudiante_id)
    elif campo == "secretaria":
        return _auto_secretaria(db, estudiante_id, periodo_id)
    return False

def listar_estudiantes_para_rectoria(db: Session, periodo_id: int, grado: Optional[str] = None, semaforo: Optional[str] = None, nombre: Optional[str] = None, documento: Optional[str] = None, grupo: Optional[str] = None,) -> list:
    query = db.query(Estudiante).options(joinedload(Estudiante.salon)).filter(
        Estudiante.id_estudiante.in_(
            db.query(Matricula.id_estudiante).filter(
                Matricula.id_periodo == periodo_id
            )
        )
    )
    
    if nombre:
        query = query.filter(Estudiante.nombre.ilike(f"%{nombre}%"))
    if documento:
        query = query.filter(Estudiante.documento.ilike(f"%{documento}%"))
    
    estudiantes = query.all()
    if not estudiantes:
        return []

    ids = [e.id_estudiante for e in estudiantes]

    firmas_list = db.query(FirmasPazYSalvo).options(
        joinedload(FirmasPazYSalvo.detalles).joinedload(DetalleFirmaPazYSalvo.tipo_firma)
    ).filter(
        FirmasPazYSalvo.id_estudiante.in_(ids),
        FirmasPazYSalvo.id_periodo == periodo_id
    ).all()
    firmas_map = {f.id_estudiante: f for f in firmas_list}

    ids_banda = set(r.id_estudiante for r in db.query(EstudianteBanda).filter(
        EstudianteBanda.id_estudiante.in_(ids), EstudianteBanda.activo == True
    ).all())

    prestamos_banda = set(r.id_estudiante for r in db.query(PrestamoInstrumento).filter(
        PrestamoInstrumento.id_estudiante.in_(ids),
        PrestamoInstrumento.estado_entrega == "prestado"
    ).all())

    prestamos_uniforme = set(r.id_estudiante for r in db.query(PrestamoObjeto).filter(
        PrestamoObjeto.id_estudiante.in_(ids),
        PrestamoObjeto.estado_prestamo == "prestado"
    ).all())

    matriculas = db.query(Matricula).filter(
        Matricula.id_estudiante.in_(ids),
        Matricula.id_periodo == periodo_id
    ).all()
    ids_matriculados = {m.id_estudiante for m in matriculas}
    ids_matricula_map = {m.id_estudiante: m.id_matricula for m in matriculas}
    ids_matricula_pagada = {m.id_estudiante for m in matriculas}

    pendientes_tesoreria = set()
    if ids_matricula_map:
        detalles = db.query(DetalleMatricula).filter(
            DetalleMatricula.id_matricula.in_(ids_matricula_map.values()),
            DetalleMatricula.estado.in_(["pendiente", "activa"])
        ).all()
        id_matriculas_pendientes = {d.id_matricula for d in detalles}
        for est_id, mat_id in ids_matricula_map.items():
            if mat_id in id_matriculas_pendientes:
                pendientes_tesoreria.add(est_id)

    ids_pruebas = set(r.id_estudiante for r in db.query(Prueba).filter(
        Prueba.id_estudiante.in_(ids), Prueba.estado == "visto"
    ).all())
    ids_pupitres = set(r.id_estudiante for r in db.query(Pupitre).filter(
        Pupitre.id_estudiante.in_(ids), Pupitre.estado == "visto"
    ).all())
    ids_libros = set(r.id_estudiante for r in db.query(PrestamoLibro).filter(
        PrestamoLibro.id_estudiante.in_(ids), PrestamoLibro.estado == "Prestado"
    ).all())

    resultado = []
    
    for e in estudiantes:
        salon_obj = e.salon
        salon_grado = str(salon_obj.grado) if salon_obj else None
        salon_grupo = str(salon_obj.grupo) if salon_obj else None
        
        if grado and salon_grado != grado:
            continue
        if grupo and salon_grupo != grupo:
            continue

        firma = firmas_map.get(e.id_estudiante)
        detalle_map = {}
        if firma and firma.detalles:
            for d in firma.detalles:
                detalle_map[d.tipo_firma.nombre] = d.estado

        no_aplica = set()
        if e.id_estudiante not in ids_banda:
            no_aplica.add("banda")

        def valor_firma(campo):
            tipo = CAMPO_TIPO_MAP.get(campo)
            if tipo and detalle_map.get(tipo):
                return True
            if campo == "banda":
                return e.id_estudiante not in prestamos_banda if e.id_estudiante in ids_banda else False
            if campo == "uniforme":
                return e.id_estudiante not in prestamos_uniforme
            if campo == "coordinadora":
                for c in ["banda", "uniforme", "secretaria", "salon"]:
                    if not valor_firma(c):
                        return False
                return True
            if campo == "salon":
                return e.id_estudiante in ids_pruebas and e.id_estudiante in ids_pupitres and e.id_estudiante not in ids_libros
            if campo == "secretaria":
                if e.id_estudiante not in ids_matriculados:
                    return False
                if e.id_estudiante not in ids_matricula_pagada:
                    return False
                return e.id_estudiante not in pendientes_tesoreria
            return False
        
        firmas_dict = {c: valor_firma(c) for c in CAMPOS_FIRMAS}
        campos_aplican = [c for c in CAMPOS_FIRMAS if c not in no_aplica]
        completadas = sum(1 for c in campos_aplican if firmas_dict[c])
        todas_firmadas = completadas == len(campos_aplican)

        if semaforo:
            calc = _calcular_semaforo(firmas_dict, no_aplica)
            if calc != semaforo:
                continue
        
        resultado.append({
            "id_estudiante": e.id_estudiante,
            "nombre": e.nombre,
            "documento": e.documento,
            "grado": salon_grado,
            "grupo": salon_grupo,
            "salon": f"{salon_grado}-{salon_grupo}" if salon_obj else "Sin salón",
            "semaforo": _calcular_semaforo(firmas_dict, no_aplica),
            "firmas_completadas": completadas,
            "total_firmas": len(campos_aplican),
            "todas_firmadas": todas_firmadas,
            "puede_retirarse": todas_firmadas,
        })
    
    return resultado


def listar_docentes_para_rectoria(db: Session, periodo_id: int, nombre: Optional[str] = None, documento: Optional[str] = None) -> list:
    docentes = db.query(Usuario).join(RolUsuario).join(Rol).filter(
        Rol.nombre == "titular",
        Usuario.estado == True,
        Usuario.id_usuario.in_(
            db.query(Salon.id_usuario).filter(
                Salon.id_usuario.isnot(None),
                Salon.id_periodo == periodo_id
            ).subquery()
        )
    )
    if nombre:
        docentes = docentes.filter(Usuario.nombre.ilike(f"%{nombre}%"))
    if documento:
        docentes = docentes.filter(Usuario.documento.ilike(f"%{documento}%"))
    docentes = docentes.all()
    if not docentes:
        return []

    ids = [d.id_usuario for d in docentes]

    accion = f"FIRMAR_PERIODO_{periodo_id}"
    auditorias = db.query(Auditoria).filter(
        Auditoria.tabla == "firma_docente_rectoria",
        Auditoria.id_registro.in_(ids),
        Auditoria.accion == accion,
    ).all()
    firmados = {a.id_registro: a for a in auditorias}
    nombres_firmantes = list(set(a.usuario for a in auditorias))
    usuarios_por_nombre = {}
    if nombres_firmantes:
        for u in db.query(Usuario).filter(Usuario.nombre.in_(nombres_firmantes)).all():
            usuarios_por_nombre[u.nombre] = u.id_usuario

    salones = db.query(Salon).filter(
        Salon.id_usuario.in_(ids),
        Salon.id_periodo == periodo_id
    ).all()
    salon_map = {}
    for s in salones:
        salon_map.setdefault(s.id_usuario, []).append(f"{s.grado}-{s.grupo}")

    resultado = []
    for d in docentes:
        salones_docente = salon_map.get(d.id_usuario, [])
        if salones_docente:
            partes = salones_docente[0].split("-")
            grado = partes[0] if len(partes) > 0 else None
            grupo = partes[1] if len(partes) > 1 else None
        else:
            grado = None
            grupo = None
        id_usuario_firmante = None
        if d.id_usuario in firmados:
            audit_entry = firmados[d.id_usuario]
            id_usuario_firmante = usuarios_por_nombre.get(audit_entry.usuario)
        resultado.append({
            "id_docente": d.id_usuario,
            "nombre": d.nombre,
            "documento": d.documento,
            "grado": grado,
            "grupo": grupo,
            "salon": ", ".join(salones_docente),
            "firmado": d.id_usuario in firmados,
            "fecha_firma": firmados[d.id_usuario].fecha if d.id_usuario in firmados else None,
            "id_usuario_firmante": id_usuario_firmante,
        })
    return resultado

def firmar_rectoria_docente(db: Session, docente_id: int, usuario_nombre: str, usuario_id: int, periodo_id: int) -> dict:
    docente = db.query(Usuario).filter(
        Usuario.id_usuario == docente_id, Usuario.estado == True
    ).first()
    if not docente:
        return {"error": "Docente no encontrado", "codigo": 404}

    accion = f"FIRMAR_PERIODO_{periodo_id}"
    ya_firmado = db.query(Auditoria).filter(
        Auditoria.tabla == "firma_docente_rectoria",
        Auditoria.id_registro == docente_id,
        Auditoria.accion == accion,
    ).first()
    if ya_firmado:
        return {"error": "Este docente ya tiene la firma de Rectoría.", "codigo": 400}

    _registrar_auditoria(
        db=db, usuario=usuario_nombre,
        accion=accion, tabla="firma_docente_rectoria",
        id_registro=docente_id,
    )
    db.commit()

    return {
        "mensaje": f"Paz y salvo de {docente.nombre} firmado correctamente por Rectoría.",
        "id_docente": docente_id, "nombre_docente": docente.nombre,
        "firmado": True, "fecha_firma": datetime.utcnow(),
    }

def descargar_pdf_estudiante(db: Session, estudiante_id: int, periodo_id: int) -> bytes:
    estado = get_estado_completo(db, estudiante_id, periodo_id)
    if not estado:
        raise ValueError("Estudiante no encontrado")
    if not estado.get("todas_firmadas"):
        raise ValueError("El estudiante no ha completado el paz y salvo")
    estudiante = db.query(Estudiante).filter(Estudiante.id_estudiante == estudiante_id).first()
    salon = db.query(Salon).filter(Salon.id_salon == estudiante.id_salon).first() if estudiante.id_salon else None
    estado["grado"] = str(salon.grado) if salon else ""
    estado["grupo"] = str(salon.grupo) if salon else ""
    firma_map = {}
    for detalle in (estado.get("detalle_firmas") or []):
        if detalle.firmado:
            r = obtener_firma_modulo(detalle.nombre, db, detalle.id_usuario_firmante)
            if "ruta" in r:
                firma_map[detalle.nombre] = r["ruta"]
    return generar_pdf_paz_salvo(estado, "estudiante", sello_path=SELLO_PATH, firma_map=firma_map)


def descargar_pdf_docente(db: Session, docente_id: int, periodo_id: int, usuario_id: Optional[int]=None) -> bytes:
    docente = db.query(Usuario).filter(Usuario.id_usuario == docente_id).first()
    if not docente:
        raise ValueError("Docente no encontrado")
    accion = f"FIRMAR_PERIODO_{periodo_id}"
    auditoria = db.query(Auditoria).filter(
        Auditoria.tabla == "firma_docente_rectoria",
        Auditoria.id_registro == docente_id,
        Auditoria.accion == accion,
    ).first()
    if not auditoria:
        raise ValueError("El docente no ha completado el paz y salvo")

    periodo = db.query(PeriodoAcademico).filter(
        PeriodoAcademico.id_periodo == periodo_id
    ).first()
    salon = db.query(Salon).filter(Salon.id_usuario == docente_id).first()
    data = {
        "nombre": docente.nombre,
        "documento": docente.documento,
        "periodo_nombre": periodo.nombre if periodo else str(periodo_id),
        "grado": str(salon.grado) if salon else "",
        "grupo": str(salon.grupo) if salon else "",
        "detalle_firmas": [
            {"nombre": "rectoria", "firmado": auditoria is not None, "no_aplica": False}
        ],
    }
    firma_map = {}
    if auditoria:
        r = obtener_firma_modulo("rectoria", db, usuario_id)
        if "ruta" in r:
            firma_map["rectoria"] = r["ruta"]
    return generar_pdf_paz_salvo(data, "docente", sello_path=SELLO_PATH, firma_map=firma_map)

def descargar_pdf_estudiantes_batch(db: Session, periodo_id: int, grado: Optional[str] = None, grupo: Optional[str] = None) -> bytes:
    import io, zipfile

    estudiantes = listar_estudiantes_para_rectoria(db, periodo_id, grado=grado, grupo=grupo)

    estudiantes = [e for e in estudiantes if e.get("todas_firmadas")]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for est in estudiantes:
            try:
                pdf_bytes = descargar_pdf_estudiante(db, est["id_estudiante"], periodo_id)
                filename = f"paz_y_salvo_{est['documento'] or est['id_estudiante']}.pdf"
                zf.writestr(filename, pdf_bytes)
            except ValueError:
                continue

    return buf.getvalue()

def descargar_pdf_docentes_batch(db: Session, periodo_id: int, grado: Optional[str] = None, grupo: Optional[str] = None) -> bytes:
    import io, zipfile
    docentes = listar_docentes_para_rectoria(db, periodo_id)
    if grado:
        docentes = [d for d in docentes if d.get("grado") == grado]
    if grupo:
        docentes = [d for d in docentes if d.get("grupo") == grupo]
    docentes = [d for d in docentes if d.get("firmado")]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docentes:
            try:
                pdf_bytes = descargar_pdf_docente(db, doc["id_docente"], periodo_id)
                filename = f"paz_y_salvo_{doc['documento'] or doc['id_docente']}.pdf"
                zf.writestr(filename, pdf_bytes)
            except ValueError:
                continue
    return buf.getvalue()