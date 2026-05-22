# 🏫 Sistema de Paz y Salvo — NCS
# Backend · API REST

Backend del sistema de gestión de **Paz y Salvo** para el colegio *New Cambridge School*.  
Permite administrar el estado académico y administrativo de estudiantes y docentes de forma digital mediante una API REST.

---

## 🛠️ Stack Tecnológico

- Lenguaje: Python 3.12
- Framework: FastAPI 0.136.1
- Base de datos: postgreSQL 16
- ORM: SQLAlchemy 2.0.40
- Migraciones: Alembic 1.15.2
- Autenticación: python-jose + passlib
- Validación: Pydantic 2.11.1
- Generación de PDF: WeasyPrint 68.1

---

## ✅ Requisitos
```bash
python --version  # 3.12.x
git --version
```
> PostgreSQL debe estar instalado y corriendo antes de continuar.

---

## 🚀 Instalación y ejecución

## 1. Clonar repositorio
```bash
git clone https://github.com/Software262/NewCambrige-backend.git
cd NewCambrige-backend
```

## 2. Crear entorno virtual
```bash
py -3.12 -m venv venv        # Windows
python3.12 -m venv venv      # Linux/Mac
```

## 3. Activar entorno virtual

```bash
# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

## 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 5. Configurar variables de entorno
```bash
cp .env.example .env
```
## 6. Crear la base de datos
Antes de migrar, crea la base de datos en PostgreSQL. Puedes hacerlo desde pgAdmin o desde la terminal:
```bash
psql -U postgres -c "CREATE DATABASE newcambridge;"
```

## 7. Ejecutar migraciones (primera vez)
```bash
alembic upgrade head
```
Esto creará todas las tablas automáticamente en la base de datos.  
Al terminar verás algo como:

```bash
INFO  [alembic.runtime.migration] Running upgrade  -> xxxxxxxx, initial_schema
```
## 8. Iniciar servidor
```bash
uvicorn app.main:app --reload --port 8000

# API disponible en:
http://localhost:8000

# Documentación automática:
http://localhost:8000/docs
```
---

> ⚠️ RECUERQUE QUE: Para crear un usuario de prueba (desarrollo) se debe hacer desde BD (query) y la clave debe guardarse hasheada

```bash
#Ejemplo de como generar una clave hasheada (python)

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash = pwd_context.hash("admin") #entre "" la contraseña que quiere hashea
print(hash)   # copia este valor
exit()
```
```bash
/* query para agregar al usuario en BD */ 
/* pegar la clave hasheada del codigo anterior */

INSERT INTO usuario (nombre, contrasena, created_at)
VALUES ('admin', '$2b$12$kfR2nz....', NOW());
```

# 🗄️ Migraciones con Alembic

## Primera vez (instalación inicial)
Si acabas de clonar el repositorio, simplemente corre:
```bash
alembic upgrade head
```
Alembic aplicará todas las migraciones existentes en orden y dejará la base de datos lista.

## Cuando realizas un cambio en los modelos
Cada vez que modifiques un `models.py` (nueva columna, nueva tabla, cambio de tipo), sigue este flujo:

```bash
# 1. Genera el archivo de migración automáticamente
alembic revision --autogenerate -m "descripcion_del_cambio"

# 2. Revisa el archivo generado en alembic/versions/
#    Verifica que los cambios detectados sean correctos

# 3. Aplica la migración
alembic upgrade head
```

> ⚠️ Siempre revisa el archivo generado antes de aplicarlo. Alembic detecta la mayoría de cambios correctamente, pero es bueno confirmar.

## Cuando haces git pull y hay migraciones nuevas
Si un compañero generó una migración y la subió al repositorio, solo necesitas:
```bash
git pull
alembic upgrade head
```

---

## 📁 Estructura del Proyecto
```bash
paz-salvo-backend/
├── app/
│   ├── main.py              # Punto de entrada de la API
│   ├── models.py            # Modelos ORM
│   ├── core/                # Configuración central (seguridad, DB, etc.)
│   ├── modules/
│   │   ├── auth/            # Autenticación y autorización
│   │   ├── usuarios/        # Gestión de usuarios
│   │   ├── estudiantes/     # Gestión de estudiantes
│   │   ├── parametrizacion/ # Configuración del sistema
│   │   ├── salon/           # Módulo salón
│   │   ├── banda/           # Módulo banda
│   │   ├── uniformes/       # Gestión de uniformes
│   │   ├── tesoreria/       # Pagos y finanzas
│   │   ├── secretaria/      # Papeleria y gestion a bajo nivel
│   │   ├── rectoria/        # Panel administrativo
│   │   └── paz_y_salvo/     # Lógica principal del sistema
│   └── shared/              # Utilidades y componentes compartidos
├── alembic/                 # Migraciones de base de datos
├── tests/                   # Pruebas
├── .env.example             # Variables de entorno de ejemplo
├── requirements.txt         # Dependencias
└── README.md
```
---

## ⚙️ Comandos útiles
```bash
# Ejecutar servidor
uvicorn app.main:app --reload --port 8000

# Crear nueva migración
alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial de migraciones
alembic history
```
---

## 🔐 Autenticación

- Basada en JWT
- Manejo de contraseñas con hash seguro (passlib)
- Protección de endpoints mediante dependencias de FastAPI

---

## 📌 Buenas prácticas

- Arquitectura modular escalable
- Separación por dominios
- Uso de variables de entorno
- Migraciones versionadas con Alembic

---

## ⚠️ Flujo de trabajo

- No trabajar directamente sobre la rama `main`
- Crear ramas por feature o fix:
  - feature/nombre-funcionalidad
  - fix/nombre-error
- Usar pull requests para integración

---

## 🚧 Mejoras futuras

- Integración con PostgreSQL
- Implementación de tests automatizados
- Dockerización del proyecto
- CI/CD
- Roles y permisos más granulares

---

