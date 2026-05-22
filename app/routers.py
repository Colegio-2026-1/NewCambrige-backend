"""Centraliza todos los routers de la aplicación"""

from app.modules.auth.router import router as auth_router
from app.modules.usuarios.router import router as usuarios_router
from app.modules.estudiantes.router import router as estudiantes_router
from app.modules.salon.router import router as salon_router
from app.modules.banda.router import router as banda_router
from app.modules.tesoreria.router import router as tesoreria_router
from app.modules.uniformes.router import router as uniformes_router
from app.modules.paz_y_salvo.router import router as paz_salvo_router
from app.modules.secretaria.router import router as secretaria_router
#from app.modules.rectoria.router import router as rectoria_router
#from app.modules.parametrizacion.router import router as parametrizacion_router

# Lista de routers para registrar fácilmente
routers = [
    (auth_router, "/api/auth", "Auth"),
    (usuarios_router, "/api/usuarios", "Usuarios"),
    (estudiantes_router, "/api/estudiantes", "Estudiantes"),
    (salon_router, "/api/salones", "Salones"),
    (banda_router, "/api/banda", "Banda"),
    (tesoreria_router, "/api/tesoreria", "Tesoreria"),
    (uniformes_router, "/api/uniformes", "Uniformes"),
    (paz_salvo_router, "/api/paz-salvo", "Paz y Salvo"),
    (secretaria_router, "/api/secretaria", "Secretaria"),
    #(rectoria_router, "/api/rectoria", "Rectoria"),
    #(parametrizacion_router, "/api/parametros", "Parametrizacion"),
]