from sqlalchemy.orm import Session
from typing import List, Optional


from fastapi import HTTPException, status
from app.shared.models import PeriodoAcademico, Auditoria
from app.modules.usuarios.models import Usuario, RolUsuario, Rol 
from app.modules.salon.models import TipoPrueba, Salon  
from app.core.database import SessionLocal
from datetime import datetime
from .schemas import AnioEscolarCreate, AnioEscolarUpdate


#PERIODO ACADEMICO
# ============ LECTURA ============
def get_anios_all(db: Session) -> List[PeriodoAcademico]:
    return db.query(PeriodoAcademico).order_by(PeriodoAcademico.nombre.desc()).all()

def get_anio_by_id(db: Session, id_periodo: int) -> Optional[PeriodoAcademico]:
    return db.query(PeriodoAcademico).filter(PeriodoAcademico.id_periodo == id_periodo).first()

# ============ CREACIÓN ============
def crear_anio_escolar(db: Session, data_in: AnioEscolarCreate, usuario_nombre: str, forzar: bool = False):
    nombre_str = str(data_in.anio_inicio) 
    anio_existente = db.query(PeriodoAcademico).filter(PeriodoAcademico.nombre == nombre_str).first()
    if anio_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El año escolar {nombre_str} ya está registrado en el sistema."
        )

    if data_in.activo:
        anio_activo_actual = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        if anio_activo_actual and not forzar:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail=f"Ya existe un año activo ({anio_activo_actual.nombre})."
            )
        if anio_activo_actual and forzar:
            anio_activo_actual.activo = False

    nuevo_periodo = PeriodoAcademico(
        nombre=nombre_str,
        fecha_inicio=data_in.fecha_inicio,
        fecha_fin=data_in.fecha_fin,
        activo=data_in.activo
    )
    db.add(nuevo_periodo)
    db.flush()

    db.add(Auditoria(
        tabla="periodo_academico", 
        id_registro=nuevo_periodo.id_periodo, 
        accion="CREAR", 
        usuario=usuario_nombre
    ))
    
    db.commit()
    db.refresh(nuevo_periodo)
    return nuevo_periodo

# ============ CAMBIO AÑO (UPDATE) ============

def update_anio_escolar(db: Session, id_periodo: int, datos_actualizar: dict, usuario_nombre: str, forzar: bool = False):
    anio_obj = get_anio_by_id(db, id_periodo)
    if not anio_obj:
        return None

    nuevo_estado_activo = datos_actualizar.get("activo")
    if nuevo_estado_activo is True and anio_obj.activo is False:
        anio_activo_otro = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True, 
            PeriodoAcademico.id_periodo != id_periodo
        ).first()
        
        if anio_activo_otro:
            if not forzar:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"No puedes activar este año porque {anio_activo_otro.nombre} ya está activo."
                )
            else:
                anio_activo_otro.activo = False

    for llave, valor in datos_actualizar.items():
        if hasattr(anio_obj, llave):
            setattr(anio_obj, llave, valor)

    db.add(Auditoria(
        tabla="periodo_academico", 
        id_registro=id_periodo, 
        accion="ACTUALIZAR_PARAMETROS_ANIO", 
        usuario=usuario_nombre
    ))
    
    db.commit()
    db.refresh(anio_obj)
    return anio_obj

# ============ CIERRE AUTOMÁTICO (31 DICIEMBRE) ============
def verificar_y_ejecutar_cierre_automatico():
    """
    Se ejecuta periódicamente (ej: cada hora).
    Comprueba si el AÑO, MES y DÍA de hoy coinciden exactamente con la fecha_fin.
    """
    db = SessionLocal()
    try:
        hoy = datetime.now().date()

        periodo_activo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
        
        if periodo_activo:
            fecha_fin_solo_dia = periodo_activo.fecha_fin.date()
            
            
            if hoy == fecha_fin_solo_dia:
                nombre_periodo_cerrado = periodo_activo.nombre
                id_periodo_cerrado = periodo_activo.id_periodo
                
                periodo_activo.activo = False
                
                db.add(Auditoria(
                    tabla="periodo_academico",
                    id_registro=id_periodo_cerrado,
                    accion="CIERRE_AUTOMATICO_FIN_DE_ANIO",
                    usuario="SISTEMA_AUTOMATICO"
                ))
                
                usuarios_afectados = db.query(Usuario).filter(Usuario.estado == True).update(
                    {Usuario.estado: False}, 
                    synchronize_session=False
                )
                
                db.add(Auditoria(
                    tabla="usuario",
                    id_registro=0,
                    accion=f"DESACTIVACION_MASIVA_ANUAL_{nombre_periodo_cerrado}",
                    usuario="SISTEMA_AUTOMATICO"
                ))
                
                db.commit()
                print(f" LOG: ¡Cierre anual ejecutado hoy ({hoy})! Periodo '{nombre_periodo_cerrado}' cerrado. {usuarios_afectados} usuarios desactivados.")
            else:
                pass
                
    except Exception as e:
        print(f" ERROR en verificación de cierre automático: {e}")
        db.rollback()
    finally:
        db.close()

def obtener_id_anio_vigente(db: Session) -> int:
  
    periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.activo == True).first()
    if not periodo:
        raise HTTPException(
            status_code=400, 
            detail="Operación no permitida: El sistema se encuentra en 'año sin definir'."
        )
    return periodo.id_periodo



#TIPOS DE PRUEBA
def get_tipos_prueba(db: Session):
    return db.query(TipoPrueba).order_by(TipoPrueba.id_tipo_prueba.asc()).all()

def get_tipo_prueba_by_id(db: Session, id_tipo_prueba: int):
    return db.query(TipoPrueba).filter(TipoPrueba.id_tipo_prueba == id_tipo_prueba).first()

def get_tipo_prueba_by_nombre(db: Session, nombre: str):
    return db.query(TipoPrueba).filter(TipoPrueba.nombre.ilike(nombre)).first()

def get_tipos_prueba_por_grado(db: Session, grado: int):
    return db.query(TipoPrueba).filter(
        TipoPrueba.grado_min <= grado,
        TipoPrueba.grado_max >= grado
    ).all()

def create_tipo_prueba(db: Session, datos_in: dict):
    nuevo_min = datos_in["grado_min"]
    nuevo_max = datos_in["grado_max"]
    nuevo_nombre = datos_in["nombre"]

    solapamiento = db.query(TipoPrueba).filter(
        TipoPrueba.nombre == nuevo_nombre,
        TipoPrueba.grado_min <= nuevo_max,
        TipoPrueba.grado_max >= nuevo_min
    ).first()

    if solapamiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"¡Rango Solapado detectado con la prueba existente: {solapamiento.nombre}!"
        )

    nueva_prueba = TipoPrueba(
        nombre=nuevo_nombre,
        grado_min=nuevo_min,
        grado_max=nuevo_max,
        descripcion=datos_in.get("descripcion")
    )

    db.add(nueva_prueba)
    db.commit()
    db.refresh(nueva_prueba)
    return nueva_prueba

def update_tipo_prueba(db: Session, id_tipo_prueba: int, datos_in: dict):
    prueba_obj = db.query(TipoPrueba).filter(TipoPrueba.id_tipo_prueba == id_tipo_prueba).first()
    if not prueba_obj:
        return None

    nuevo_min = datos_in.get("grado_min", prueba_obj.grado_min)
    nuevo_max = datos_in.get("grado_max", prueba_obj.grado_max)
    nuevo_nombre = datos_in.get("nombre", prueba_obj.nombre)

    solapamiento = db.query(TipoPrueba).filter(
        TipoPrueba.id_tipo_prueba != id_tipo_prueba, 
        TipoPrueba.nombre == nuevo_nombre,
        TipoPrueba.grado_min <= nuevo_max,
        TipoPrueba.grado_max >= nuevo_min
    ).first()

    if solapamiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="¡Rango Solapado detectado con el mismo nombre!"
        )

    prueba_obj.nombre = nuevo_nombre
    prueba_obj.grado_min = nuevo_min
    prueba_obj.grado_max = nuevo_max

    if "descripcion" in datos_in:
        prueba_obj.descripcion = datos_in["descripcion"]

    db.commit()
    db.refresh(prueba_obj)
    return prueba_obj


#ASIGNAR TITULARES

def get_titulares_activos(db: Session):
    return (
        db.query(Usuario)
        .join(RolUsuario, Usuario.id_usuario == RolUsuario.id_usuario)
        .join(Rol, RolUsuario.id_rol == Rol.id_rol)
        .filter(
            Rol.nombre.ilike("%titular%"), 
            Usuario.estado == True         
        )
        .all()
    )

def get_salones_para_asignacion(db: Session, id_periodo: int):
    return (
        db.query(Salon)
        .filter(Salon.id_periodo == id_periodo)
        .all()
    )

def asignar_titular_a_salon(db: Session, id_salon: int, id_usuario: int):
    salon = db.query(Salon).filter(Salon.id_salon == id_salon).first()
    
    if not salon:
        return None
        
    salon.id_usuario = id_usuario
    db.commit()
    db.refresh(salon)
    
    return salon

def crear_salon_parametrizacion(db: Session, data: dict):
    nuevo_salon = Salon(
        grado=data["grado"],
        grupo=data["grupo"],
        id_periodo=data["id_periodo"],
        id_usuario=data.get("id_usuario") 
    )
    
    db.add(nuevo_salon)
    db.commit()
    db.refresh(nuevo_salon)
    
    return nuevo_salon