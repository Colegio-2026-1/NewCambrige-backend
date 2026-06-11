# =============================================================================
# config/settings.py — Configuración central del proyecto
# =============================================================================
# Todas las credenciales se leen exclusivamente desde variables de entorno.
# Copia .env.example a .env y completa los valores antes de ejecutar.
# =============================================================================

import os
from dotenv import load_dotenv

# Cargar variables desde .env (si existe) al inicio
load_dotenv()

# ---------------------------------------------------------------------------
# Plataforma WebColegios (valores por defecto solo estructurales, NO claves)
# ---------------------------------------------------------------------------
WEB_URL          = os.getenv("WEB_URL", "https://www.webcolegios.com/clararincon/")
WEB_TIPO_USUARIO = os.getenv("WEB_TIPO_USUARIO", "Administrativo")

# ---------------------------------------------------------------------------
# Base de datos PostgreSQL
# ---------------------------------------------------------------------------
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME",     "paz_y_salvo")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ---------------------------------------------------------------------------
# Clave maestra de cifrado para la tabla login (Fernet)
# ---------------------------------------------------------------------------
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# ---------------------------------------------------------------------------
# Playwright / Chromium
# ---------------------------------------------------------------------------
HEADLESS          = os.getenv("HEADLESS", "True").lower() in ("true", "1", "yes")
PAGE_TIMEOUT      = int(os.getenv("PAGE_TIMEOUT", "30"))      # segundos
ELEMENT_TIMEOUT   = int(os.getenv("ELEMENT_TIMEOUT", "20"))   # segundos
DOWNLOAD_DIR      = os.path.join(os.path.dirname(__file__), "..", "downloads")
DOWNLOAD_TIMEOUT  = int(os.getenv("DOWNLOAD_TIMEOUT", "60"))  # segundos

# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------
GRADO_ID_DEFAULT = int(os.getenv("GRADO_ID_DEFAULT", "1"))
LOG_LEVEL        = os.getenv("LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Seguridad API
# ---------------------------------------------------------------------------
API_KEY          = os.getenv("API_KEY", "")
