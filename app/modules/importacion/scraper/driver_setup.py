# =============================================================================
# modules/driver_setup.py — Inicialización de Playwright Chromium
# =============================================================================

import os
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from .logger import get_logger
from .config import HEADLESS, DOWNLOAD_DIR, PAGE_TIMEOUT

logger = get_logger("driver_setup")


def crear_driver(p) -> tuple[Browser, BrowserContext, Page]:
    """
    Configura y devuelve las instancias de Playwright: Browser, BrowserContext y Page.

    Opciones aplicadas:
      - Modo headless opcional (configurable en settings.py)
      - Directorio de descarga automática (manejado por el contexto de Playwright)
      - Sin sandbox (necesario en algunos entornos Linux/Docker)
      - Deshabilita GPU (mejora estabilidad headless)
      - Acepta descargas automáticamente
      - Configura el tamaño de la ventana (1920x1080)
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    logger.info(" Configurando Playwright Chromium...")

    # Lanzar el navegador
    browser = p.chromium.launch(
        headless=HEADLESS,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )

    # Crear contexto con opciones específicas de descarga y viewport
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        accept_downloads=True
    )

    # Crear página y configurar el timeout por defecto
    page = context.new_page()
    page.set_default_navigation_timeout(PAGE_TIMEOUT * 1000)
    page.set_default_timeout(PAGE_TIMEOUT * 1000)

    logger.info(" Playwright Chromium iniciado correctamente")
    return browser, context, page
