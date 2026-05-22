from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.shared.models
from app.routers import routers
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Paz y Salvo API",
    swagger_ui_parameters={"persistAuthorization": True}
)

"""def custom_openapi(): #Dado el caso no usemos OAuth2 UI en Swagger
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Paz y Salvo API",
        version="1.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [
                {"BearerAuth": []}
            ]

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi"""

@app.get("/")
def read_root():
    return {"mensaje": "Hola mundo con FastAPI 🚀"}

for router, prefix, tag in routers:
    app.include_router(router, prefix=prefix, tags=[tag])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # puerto por defecto de Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)