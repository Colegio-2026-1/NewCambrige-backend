# =============================================================================
# modules/autenticacion.py — Login en WebColegios con resolución de captcha
# =============================================================================

import os
import re
import time
from functools import wraps
from playwright.sync_api import Page
from .logger import get_logger
from .config import ELEMENT_TIMEOUT

logger = get_logger("autenticacion")


# =============================================================================
#  HELPERS
# =============================================================================

def retry_with_backoff(retries=3, backoff_in_seconds=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f" Falló tras {retries} reintentos. Excepción: {e}")
                        raise
                    sleep_time = backoff_in_seconds * (2 ** x)
                    logger.warning(f"️ Error: {e}. Reintentando en {sleep_time}s... (Intento {x+1}/{retries})")
                    time.sleep(sleep_time)
                    x += 1
        return wrapper
    return decorator

def _resolver_captcha_matematico(texto: str) -> str:
    """
    Recibe un string como '5 + 6' o '8-3' y devuelve el resultado como string.
    Operaciones soportadas: suma (+), resta (-), multiplicación (*), división (/).
    """
    texto = texto.strip()
    match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', texto)
    if not match:
        raise ValueError(f"No se pudo interpretar el captcha: '{texto}'")

    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))

    if op == '+':
        resultado = a + b
    elif op == '-':
        resultado = a - b
    elif op == '*':
        resultado = a * b
    elif op == '/':
        resultado = a // b
    else:
        raise ValueError(f"Operador no reconocido: '{op}'")

    logger.debug(f"Captcha resuelto: {texto} = {resultado}")
    return str(resultado)


# =============================================================================
#  FUNCIÓN PRINCIPAL
# =============================================================================

@retry_with_backoff(retries=3, backoff_in_seconds=2)
def autenticar(page: Page, url: str = None, usuario: str = None,
               password: str = None, tipo_usuario: str = None) -> bool:
    """
    Flujo completo de autenticación en WebColegios.
    Las credenciales se reciben como parámetros (provenientes de la tabla login).
    Si no se proporcionan, se intentan cargar desde las variables de entorno como fallback.

    Retorna True si el login fue exitoso, False en caso contrario.
    """
    # Fallback a variables de entorno si no se pasan parámetros
    import os
    url = url or os.getenv("WEB_URL", "")
    usuario = usuario or os.getenv("WEB_USUARIO", "")
    password = password or os.getenv("WEB_PASSWORD", "")
    tipo_usuario = tipo_usuario or os.getenv("WEB_TIPO_USUARIO", "Administrativo")

    if not url or not usuario or not password:
        logger.error(" Faltan credenciales de autenticación (url, usuario o password).")
        return False
    os.makedirs("logs", exist_ok=True)

    try:
        # ── Paso 1: Abrir URL ────────────────────────────────────────────────
        logger.info(f"Abriendo: {url}")
        page.goto(url)
        time.sleep(2)

        # ── Paso 2: Usuario  (id=identidad1) ─────────────────────────────────
        selector_usuario = (
            "//input[@id='identidad1' or @name='identidad1' "
            "or (@type='text' and (@name='usuario' or contains(@placeholder,'usu')))]"
        )
        page.wait_for_selector(selector_usuario, timeout=ELEMENT_TIMEOUT * 1000)
        page.fill(selector_usuario, usuario)
        logger.debug(f"Usuario ingresado: {usuario}")

        # ── Paso 3: Contraseña ────────────────────────────────────────────────
        selector_pass = "//input[@type='password']"
        page.wait_for_selector(selector_pass, timeout=ELEMENT_TIMEOUT * 1000)
        page.fill(selector_pass, password)
        logger.debug("Contraseña ingresada")

        # ── Paso 4: Tipo de usuario  (id=nivel1) ─────────────────────────────
        selector_tipo = (
            "//select[@id='nivel1' or @name='nivel1' "
            "or contains(@name,'tipo') or contains(@id,'tipo') "
            "or contains(@name,'perfil') or contains(@id,'perfil')]"
        )
        try:
            page.wait_for_selector(selector_tipo, timeout=3000)
            page.select_option(selector_tipo, label=tipo_usuario)
            logger.debug(f"Tipo de usuario seleccionado: {tipo_usuario}")
        except Exception:
            logger.warning("No se encontró <select> de tipo usuario; continuando...")

        # ── Paso 5: Leer captcha matemático ──────────────────────────────────
        selectores_captcha = [
            "//label[contains(text(),'=') and (contains(text(),'+') or "
            "contains(text(),'-') or contains(text(),'*') or contains(text(),'/'))]",
            "//td[contains(text(),'=') and (contains(text(),'+') or contains(text(),'-'))]",
            "//span[contains(@id,'captcha')]",
            "//div[contains(@id,'captcha')]",
            "//label[contains(@for,'captcha')]",
            "//*[contains(@class,'captcha') or contains(@class,'operacion')]",
            "//td[contains(text(),'+') or contains(text(),'-')]",
        ]
        texto_captcha = None
        for sel in selectores_captcha:
            try:
                locator = page.locator(sel)
                if locator.is_visible(timeout=1000):
                    text = locator.inner_text().strip()
                    if text:
                        texto_captcha = text
                        logger.info(f"Captcha detectado: '{texto_captcha}'")
                        break
            except Exception:
                continue

        if not texto_captcha:
            try:
                body_text = page.inner_text("body")
                match = re.search(r'\d+\s*[\+\-\*\/]\s*\d+', body_text)
                if match:
                    texto_captcha = match.group(0)
                    logger.info(f"Captcha extraído del body: '{texto_captcha}'")
            except Exception:
                pass

        if not texto_captcha:
            raise RuntimeError(
                "No se pudo localizar el captcha matemático. "
                "Inspecciona el HTML y actualiza los selectores."
            )

        # ── Paso 6: Resolver e ingresar captcha  (id=captcha_respuesta) ──────
        respuesta = _resolver_captcha_matematico(texto_captcha)
        selector_captcha = (
            "//input[@id='captcha_respuesta' or @name='captcha_respuesta' "
            "or contains(@name,'captcha') or contains(@id,'captcha') "
            "or contains(@placeholder,'resultado') or contains(@placeholder,'=')]"
        )
        page.wait_for_selector(selector_captcha, timeout=ELEMENT_TIMEOUT * 1000)
        page.fill(selector_captcha, respuesta)
        logger.debug(f"Respuesta captcha ingresada: {respuesta}")

        # ── Paso 7: Clic en Acceder  (id=boton) ──────────────────────────────
        selector_btn_acceder = (
            "//button[@id='boton'] | //input[@id='boton'] | "
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'acceder')] | "
            "//input[@type='submit']"
        )
        page.wait_for_selector(selector_btn_acceder, timeout=ELEMENT_TIMEOUT * 1000)
        page.click(selector_btn_acceder)
        logger.info("Botón 'Acceder' presionado")

        # ── Paso 8: Presionar segundo botón 'Acceder' del modal ───────────────
        logger.info("⏳ Esperando modal de bienvenida...")
        timeout_end = time.time() + 20
        boton_presionado = False
        while time.time() < timeout_end:
            try:
                segundo_boton = page.locator("//input[@type='submit' and @value='Acceder']")
                if segundo_boton.is_visible(timeout=500) and segundo_boton.is_enabled():
                    segundo_boton.click()
                    logger.info(" Segundo botón 'Acceder' presionado")
                    boton_presionado = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not boton_presionado:
            logger.warning("️ Modal no detectado")

        # ── Paso 9: Verificar login exitoso ───────────────────────────────────
        time.sleep(2)
        if _verificar_login_exitoso(page):
            logger.info("Autenticación exitosa — dashboard cargado")
            return True
        else:
            logger.error("Login fallido — verifica credenciales o captcha")
            page.screenshot(path="logs/screenshot_login_fallido.png")
            return False

    except Exception as e:
        logger.error(f"Error inesperado durante autenticación: {e}")
        try:
            page.screenshot(path="logs/screenshot_error.png")
        except Exception:
            pass
        raise


def _verificar_login_exitoso(page: Page) -> bool:
    """
    Heurística para detectar si el login fue exitoso.
    Criterios positivos: URL cambia, aparece un menú, desaparece el formulario.
    """
    url_actual = page.url.lower()

    # Si la URL cambió (ya no está en la página de login)
    if "login" not in url_actual:
        return True

    # Busca elementos típicos de sesión iniciada
    indicadores = [
        "//div[contains(@class,'menu')]",
        "//nav",
        "//a[contains(text(),'Cerrar') or contains(text(),'Salir')]",
        "//span[contains(text(),'Bienvenido') or contains(text(),'bienvenido')]",
    ]
    for sel in indicadores:
        try:
            if page.locator(sel).is_visible(timeout=1000):
                return True
        except Exception:
            continue

    # Busca mensajes de error típicos de login fallido
    errores = [
        "//span[contains(text(),'incorrecto') or contains(text(),'invalido')]",
        "//div[contains(@class,'error') or contains(@class,'alert-danger')]",
    ]
    for sel in errores:
        try:
            if page.locator(sel).is_visible(timeout=1000):
                return False
        except Exception:
            continue

    # No se pudo determinar — asume éxito si no hay error explícito
    return True
