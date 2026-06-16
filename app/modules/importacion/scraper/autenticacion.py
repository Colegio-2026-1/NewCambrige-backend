# =============================================================================
# modules/autenticacion.py — Login en WebColegios con resolución de captcha (Requests)
# =============================================================================

import os
import re
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from functools import wraps
from .logger import get_logger

logger = get_logger("autenticacion")

# Excepción personalizada
class WebcolegiosAuthError(Exception):
    pass

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
def autenticar(url: str = None, usuario: str = None,
               password: str = None, tipo_usuario: str = None) -> requests.Session | None:
    """
    Flujo completo de autenticación en WebColegios usando `requests.Session`.
    Las credenciales se reciben como parámetros (provenientes de la tabla login).
    Si no se proporcionan, se intentan cargar desde las variables de entorno como fallback.

    Retorna un objeto `requests.Session` autenticado si el login fue exitoso, None en caso contrario.
    """
    url = url or os.getenv("WEB_URL", "")
    usuario = usuario or os.getenv("WEB_USUARIO", "")
    password = password or os.getenv("WEB_PASSWORD", "")
    tipo_usuario = tipo_usuario or os.getenv("WEB_TIPO_USUARIO", "Administrativo")

    if not url or not usuario or not password:
        logger.error(" Faltan credenciales de autenticación (url, usuario o password).")
        return None
        
    os.makedirs("logs", exist_ok=True)
    
    session = requests.Session()
    # Configurar User-Agent estándar para evitar bloqueos
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    })

    try:
        # ── Paso 1: Obtener la página de login ────────────────────────────────
        logger.info(f"Abriendo: {url}")
        r1 = session.get(url)
        r1.raise_for_status()
        logger.debug(f"Página cargada. Cookies obtenidas: {session.cookies.get_dict()}")
        
        soup = BeautifulSoup(r1.text, 'html.parser')

        # Buscar el formulario de login principal
        login_form = None
        for form in soup.find_all('form'):
            action = form.get('action', '').lower()
            if 'index.php' in action or 'login' in action:
                login_form = form
                break

        if not login_form:
            raise WebcolegiosAuthError("No se encontró el formulario de login en la página principal.")

        action_url = urllib.parse.urljoin(url, login_form.get('action', 'index.php'))
        
        # Extraer parámetros ocultos por defecto
        data = {}
        for input_tag in login_form.find_all('input'):
            name = input_tag.get('name')
            if name:
                data[name] = input_tag.get('value', '')

        # ── Paso 2: Extraer y resolver captcha matemático ────────────────────
        captcha_span = soup.find('span', id='captcha_pregunta')
        if not captcha_span:
            # Fallback a body text
            match = re.search(r'\d+\s*[\+\-\*\/]\s*\d+', r1.text)
            if match:
                texto_captcha = match.group(0)
            else:
                raise WebcolegiosAuthError("No se encontró el captcha matemático en el HTML.")
        else:
            texto_captcha = captcha_span.text.strip()
            
        logger.info(f"Captcha encontrado: '{texto_captcha}'")
        respuesta_captcha = _resolver_captcha_matematico(texto_captcha)

        # ── Paso 3: Rellenar credenciales y construir POST ───────────────────
        data['identidad'] = usuario
        data['clave'] = password
        data['nivel'] = tipo_usuario
        data['captcha_respuesta'] = respuesta_captcha
        
        # Asegurar token y request (están en inputs ocultos, pero forzamos porsia)
        captcha_token = data.get('captcha_token')
        if not captcha_token:
            raise WebcolegiosAuthError("No se encontró 'captcha_token' oculto.")
            
        data['wc_login_request'] = '1'

        logger.debug("Enviando credenciales POST...")
        r2 = session.post(action_url, data=data)
        r2.raise_for_status()

        if "Acceso Denegado" in r2.text or "Contraseña Incorrecta" in r2.text or "Captcha Incorrecto" in r2.text:
            raise WebcolegiosAuthError("Login fallido. Verifica credenciales o captcha.")

        logger.info("Login exitoso aparente.")

        # ── Paso 4: Confirmar sesión (Segundo POST a administrativo/index.php) ───
        modal_soup = BeautifulSoup(r2.text, 'html.parser')
        modal_form = modal_soup.find('form', id='form1')
        
        if modal_form:
            url_segundo_acceder = urllib.parse.urljoin(url, modal_form.get('action'))
            logger.info(f"Confirmando sesión con segundo POST a {url_segundo_acceder}...")
            r3 = session.post(url_segundo_acceder)
            r3.raise_for_status()
        else:
            logger.warning("No se encontró modal_form en la respuesta del login. Continuando de todos modos...")
            # Fallback en caso de que no aparezca el modal pero haya iniciado
            session.post(urllib.parse.urljoin(url, "../administrativo/index.php"))

        logger.info("✅ Autenticación completada.")
        return session

    except Exception as e:
        logger.error(f"Error en el proceso de autenticación HTTP: {e}")
        raise
