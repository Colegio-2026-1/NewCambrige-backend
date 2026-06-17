from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SemaforoEstado:
    VERDE = "VERDE"        
    AMARILLO = "AMARILLO" 
    ROJO = "ROJO"          

class FirmasBase(BaseModel):
    banda: bool = False
    coordinadora: bool = False
    uniforme: bool = False
    salon: bool = False
    secretaria: bool = False
    rectoria: bool = False

class DetalleFirma(BaseModel):
    nombre: str
    firmado: bool
    rol_responsable: str
    no_aplica: bool = False
    id_usuario_firmante: Optional[int] = None 

class EstadoPazSalvoResponse(BaseModel):
    id_estudiante: int
    nombre: str
    documento: Optional[str] = None
    id_periodo: int
    periodo_nombre: Optional[str] = None
    firmas: FirmasBase
    todas_firmadas: bool
    puede_retirarse: bool
    semaforo: Optional [str] = None
    detalle_firmas: Optional[list[DetalleFirma]] = None
    firmas_completadas: Optional [int] = 0
    total_firmas: Optional [int] = 0

class RectoriaFirmaResponse(BaseModel):
    mensaje: str
    id_estudiante: int
    nombre_estudiante: str
    paz_y_salvo_completo: bool
    fecha_firma: datetime

class RectoriaFirmaRequest(BaseModel):
    observacion: Optional[str] = None


class EstudianteRectoriaItem(BaseModel):
    id_estudiante: int
    nombre: str
    documento: str
    grado: Optional[str]
    grupo: Optional[str]
    salon: str
    semaforo: str
    firmas_completadas: int
    total_firmas: int
    todas_firmadas: bool
    puede_retirarse: bool

class DocenteRectoriaItem(BaseModel):
    id_docente: int
    nombre: str
    documento: str
    grado: Optional[str] = None
    grupo: Optional[str] = None
    salon: Optional[str] = None
    firmado: bool = False
    fecha_firma: Optional[datetime] = None
    id_usuario_firmante: Optional[int] = None

class DocenteRectoriaFirmaResponse(BaseModel):
    mensaje: str
    id_docente: int
    nombre_docente: str
    firmado: bool
    fecha_firma: datetime