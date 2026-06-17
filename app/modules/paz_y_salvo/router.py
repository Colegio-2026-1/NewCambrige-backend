from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.shared.models import PeriodoAcademico
from app.modules.paz_y_salvo import service
from app.modules.paz_y_salvo.schemas import EstadoPazSalvoResponse, RectoriaFirmaRequest, RectoriaFirmaResponse, EstudianteRectoriaItem, DocenteRectoriaItem, DocenteRectoriaFirmaResponse
from app.modules.auth.deps import require_roles
from app.modules.usuarios.models import Usuario, RolUsuario, Rol
from fastapi.responses import FileResponse, StreamingResponse

router = APIRouter()

def _validar_acceso_periodo(periodo_id: Optional[int], current_user: Usuario, db: Session) -> int:
    roles = [r[0] for r in db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == current_user.id_usuario).all()]

    if periodo_id is None:
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True
        ).first()
        if not periodo:
            raise HTTPException(status_code=404, detail="No hay un periodo académico activo")
        return periodo.id_periodo
    
    periodo = db.query(PeriodoAcademico).filter(
        PeriodoAcademico.id_periodo == periodo_id
    ).first()
    if not periodo:
        raise HTTPException(status_code=404, detail=f"Periodo {periodo_id} no encontrado")
    
    if not periodo.activo and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Solo el administrador puede acceder a periodos inactivos")
    
    return periodo_id
    

@router.get("/estudiante/{estudiante_id}", response_model=EstadoPazSalvoResponse)
def obtener_estado_paz_salvo(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin",  "rectoria"]))
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    resultado = service.get_estado_completo(db, estudiante_id, periodo_id_valido)
    if not resultado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return resultado

@router.post("/rectoria/{estudiante_id}", response_model=RectoriaFirmaResponse, summary="Firma final de Rectoría")
def firmar_rectoria(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    body: Optional[RectoriaFirmaRequest] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_validado = _validar_acceso_periodo(periodo_id, current_user, db)
    resultado = service.firmar_rectoria(
        db=db,
        estudiante_id=estudiante_id,
        usuario_nombre=current_user.nombre,
        usuario_id=current_user.id_usuario,
        periodo_id=periodo_id_validado,
    )

    if "error" in resultado:
        raise HTTPException(status_code=resultado.get("codigo", 400), detail=resultado["error"])

    return resultado

@router.get("/periodos", summary="Listar periodos académicos")
def listar_periodos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"]))
):
    roles_usuario = db.query(Rol.nombre).join(
        RolUsuario, Rol.id_rol == RolUsuario.id_rol
    ).filter(RolUsuario.id_usuario == current_user.id_usuario).all()
    roles = [r[0] for r in roles_usuario]

    if "admin" in roles:
        periodos = db.query(PeriodoAcademico).order_by(
            PeriodoAcademico.id_periodo.desc()
        ).all()
    else:
        periodos = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.activo == True
        ).all()
    
    return [
        {
            "id_periodo": p.id_periodo,
            "nombre": p.nombre,
            "fecha_inicio": p.fecha_inicio,
            "fecha_fin": p.fecha_fin,
            "activo": p.activo,
        }
        for p in periodos
    ]

@router.get("/sello")
def obtener_sello(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"]))
):
    resultado = service.obtener_sello()
    if "error" in resultado:
        raise HTTPException(404, resultado["error"])
    return FileResponse(resultado["ruta"], media_type="image/jpeg", headers={"X-Hash-SHA256": resultado["hash"]})

@router.get("/firma/modulo/{nombre_modulo}")
def obtener_firma_modulo(
    nombre_modulo: str,
    usuario_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    resultado = service.obtener_firma_modulo(nombre_modulo, db, usuario_id)
    if "error" in resultado:
        raise HTTPException(404, resultado["error"])
    return FileResponse(resultado["ruta"], media_type="image/png")

@router.get("/estudiantes-rectoria", response_model=List[EstudianteRectoriaItem])
def listar_estudiantes_para_rectoria(
    periodo_id: Optional[int] = Query(None),
    grado: Optional[str] = Query(None),
    semaforo: Optional[str] = Query(None),
    nombre: Optional[str] = Query(None),
    documento: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    return service.listar_estudiantes_para_rectoria(db, periodo_id_valido, grado, semaforo, nombre, documento, grupo)

@router.get("/docentes-rectoria", response_model=List[DocenteRectoriaItem])
def listar_docentes_para_rectoria_endpoint(
    periodo_id: Optional[int] = Query(None),
    nombre: Optional[str] = Query(None),
    documento: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    return service.listar_docentes_para_rectoria(
        db, periodo_id_valido, nombre, documento
    )

@router.post("/rectoria/docente/{docente_id}", response_model=DocenteRectoriaFirmaResponse)
def firmar_rectoria_docente_endpoint(
    docente_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    resultado = service.firmar_rectoria_docente(
        db, docente_id, current_user.nombre, current_user.id_usuario, periodo_id
    )
    if "error" in resultado:
        raise HTTPException(resultado["codigo"], resultado["error"])
    return resultado

@router.get("/descargar-pdf/estudiante/{estudiante_id}")
def descargar_pdf_estudiante_endpoint(
    estudiante_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    try:
        pdf_bytes = service.descargar_pdf_estudiante(db, estudiante_id, periodo_id_valido)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    nombre_archivo = f"paz_y_salvo_estudiante_{estudiante_id}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


@router.get("/descargar-pdf/docente/{docente_id}")
def descargar_pdf_docente_endpoint(
    docente_id: int,
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    try:
        pdf_bytes = service.descargar_pdf_docente(db, docente_id, periodo_id_valido, current_user.id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    nombre_archivo = f"paz_y_salvo_docente_{docente_id}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )

@router.get("/descargar-pdf/estudiantes/batch")
def descargar_pdf_estudiantes_batch_endpoint(
    periodo_id: int = Query(None),
    grado: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    zip_bytes = service.descargar_pdf_estudiantes_batch(
        db, periodo_id_valido, grado, grupo
    )
    sufijo = []
    if grado:
        sufijo.append(f"grado_{grado}")
    if grupo:
        sufijo.append(f"grupo_{grupo}")
    nombre = f"paz_y_salvo_{'_'.join(sufijo) if sufijo else 'todos'}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )

@router.get("/descargar-pdf/docentes/batch")
def descargar_pdf_docentes_batch_endpoint(
    periodo_id: Optional[int] = Query(None),
    grado: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin", "rectoria"])),
):
    periodo_id_valido = _validar_acceso_periodo(periodo_id, current_user, db)
    zip_bytes = service.descargar_pdf_docentes_batch(db, periodo_id_valido, grado, grupo)
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=paz_y_salvo_docentes.zip"},
    )