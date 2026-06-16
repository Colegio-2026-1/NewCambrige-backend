from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.importacion.schemas import (
    CargaMasivaRequest, 
    CargaIndividualRequest, 
    EjecucionBotResponse, 
    SincronizarRequest,
    CredencialesResponse,
    CredencialesUpdate
)
from app.modules.importacion.service import ImportacionService
from app.modules.auth.deps import get_current_user, require_roles
from app.modules.usuarios.models import Usuario
from app.modules.secretaria.models import CredencialesLogin
from app.core.security import encriptar_texto

router = APIRouter()

def get_importacion_service(db: Session = Depends(get_db)):
    return ImportacionService(db)

@router.get("/credenciales", response_model=CredencialesResponse, summary="Obtiene las credenciales del robot scraper")
def obtener_credenciales(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    credencial = db.query(CredencialesLogin).first()
    if not credencial:
        raise HTTPException(status_code=404, detail="No hay credenciales configuradas")
    return credencial

@router.put("/credenciales", response_model=CredencialesResponse, summary="Actualiza las credenciales del robot scraper")
def actualizar_credenciales(
    datos: CredencialesUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    credencial = db.query(CredencialesLogin).first()
    if not credencial:
        credencial = CredencialesLogin()
        db.add(credencial)
    
    credencial.url = datos.url
    credencial.nombre_usuario = datos.nombre_usuario
    credencial.password_hash = encriptar_texto(datos.password)
    db.commit()
    db.refresh(credencial)
    return credencial

@router.post("/scraping", summary="Inicia el scraping desde WebColegios")
def iniciar_scraping(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping(usuario_id=current_user.id_usuario)

@router.post("/scraping/estudiantes", summary="Inicia el scraping solo de estudiantes")
def iniciar_scraping_estudiantes(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping_estudiantes(usuario_id=current_user.id_usuario)

@router.post("/scraping/docentes", summary="Inicia el scraping solo de docentes")
def iniciar_scraping_docentes(
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.iniciar_scraping_docentes(usuario_id=current_user.id_usuario)

@router.post("/carga-masiva", summary="Procesa un array de registros y los inserta en staging")
def carga_masiva(
    request: CargaMasivaRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.ejecutar_carga_masiva(request, usuario_id=current_user.id_usuario)

@router.post("/carga-individual", summary="Inserta un registro individual en staging")
def carga_individual(
    request: CargaIndividualRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.ejecutar_carga_individual(request, usuario_id=current_user.id_usuario)

@router.get("/ejecuciones", response_model=List[EjecucionBotResponse], summary="Obtiene el historial de ejecuciones")
def listar_ejecuciones(
    limit: int = 100, 
    skip: int = 0, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.obtener_ejecuciones(limit=limit, skip=skip)

@router.get("/ejecuciones/{id}", response_model=EjecucionBotResponse, summary="Obtiene una ejecucion especifica")
def obtener_ejecucion(
    id: int, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    ej = service.obtener_ejecucion(id)
    if not ej:
        raise HTTPException(status_code=404, detail="Ejecucion no encontrada")
    return ej


@router.post("/sincronizar-estudiantes", summary="Sincroniza estudiantes desde staging hacia la tabla oficial")
def sincronizar_estudiantes(
    request: SincronizarRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.sincronizar_estudiantes(ejecucion_id=request.ejecucion_id)

@router.post("/sincronizar-docentes", summary="Sincroniza docentes desde staging hacia la tabla oficial")
def sincronizar_docentes(
    request: SincronizarRequest, 
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    return service.sincronizar_docentes(ejecucion_id=request.ejecucion_id)

@router.delete("/scraping/cancelar/{ejecucion_id}", summary="Cancela la importación y limpia los datos temporales")
def cancelar_scraping(
    ejecucion_id: int,
    tipo: str,
    service: ImportacionService = Depends(get_importacion_service),
    current_user: Usuario = Depends(require_roles(["admin"]))
):
    if tipo not in ["estudiante", "docente"]:
        raise HTTPException(status_code=400, detail="El tipo debe ser 'estudiante' o 'docente'")
    return service.cancelar_sincronizacion(ejecucion_id=ejecucion_id, tipo=tipo)
