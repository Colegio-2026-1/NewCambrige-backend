# =============================================================================
# modules/navegacion.py — Navegación de menús y generación del listado (Requests)
# =============================================================================

import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from .logger import get_logger
from .config import DOWNLOAD_DIR

logger = get_logger("navegacion")

# =============================================================================
#  FUNCIONES PRINCIPALES
# =============================================================================

def navegar_y_generar_listado(session: requests.Session, url_base: str, tipo_datos: str = "Estudiantes") -> str | None:
    """
    Descarga el PDF de estudiantes (o tipo_datos general) usando requests.
    Retorna la ruta al archivo descargado, o None si falló.
    """
    logger.info(f"Navegando y generando listado para: {tipo_datos}")
    
    # 1. Ir al formulario
    url_formulario = urllib.parse.urljoin(url_base, "/admin_lista_uso_general.php")
    r1 = session.get(url_formulario)
    r1.raise_for_status()
    
    soup = BeautifulSoup(r1.text, 'html.parser')
    form1 = soup.find('form', attrs={'name': 'form1'})
    if not form1:
        logger.error("No se encontró form1 en admin_lista_uso_general.php")
        return None
        
    action1 = urllib.parse.urljoin(r1.url, form1.get('action'))
    
    # Recoger todos los inputs ocultos del form1
    data_form1 = {}
    for i in form1.find_all('input'):
        name = i.get('name')
        if name:
            data_form1[name] = i.get('value', '')
            
    # Configurar filtros según tipo
    if tipo_datos.lower() == "docentes":
        data_form1['destino'] = 'DO'
    else:
        data_form1['destino'] = 'ES'
    data_form1['noretirados'] = '1'
    
    # 2. Enviar formulario principal
    r2 = session.post(action1, data=data_form1)
    r2.raise_for_status()
    
    # 3. Buscar el formulario final (donde está el botón Imprimir)
    html_res = r2.text
    idx_btn = html_res.find('btn-dark')
    if idx_btn == -1:
        logger.error("No se encontró el botón Imprimir (btn-dark) en el formulario secundario.")
        return None
        
    form_start = html_res.rfind('<form', 0, idx_btn)
    form_end = html_res.find('</form>', idx_btn)
    form_html = html_res[form_start:form_end+7]
    
    action_match = re.search(r'action="([^"]+)"', form_html)
    if not action_match:
        logger.error("No se pudo encontrar el action en el form secundario.")
        return None
        
    action_pdf = urllib.parse.urljoin(r2.url, action_match.group(1))
    
    # Extraer todos los campos (inputs y selects)
    data_pdf = {}
    for m in re.finditer(r'(?i)<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', form_html):
        data_pdf[m.group(1)] = m.group(2)
    for m in re.finditer(r'(?i)<select[^>]*name="([^"]+)"[^>]*>.*?<option[^>]*value="([^"]*)"', form_html, re.DOTALL):
        data_pdf[m.group(1)] = m.group(2)
        
    data_pdf['boton'] = 'Imprimir'
    if 'escuela_nueva' in data_pdf:
        del data_pdf['escuela_nueva']  # Nos aseguramos de que NUNCA vaya este check para obtener titulares
        
    if tipo_datos.lower() != "docentes" and 'condocumento' in data_pdf:
        del data_pdf['condocumento']  # Usar el código interno COD solo para estudiantes
        
    if tipo_datos.lower() == "docentes":
        data_pdf['boton'] = 'Imprimir Todos'
        
    # 4. Descargar el PDF
    logger.info(f"Descargando PDF desde: {action_pdf}")
    r_pdf = session.post(action_pdf, data=data_pdf)
    r_pdf.raise_for_status()
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    nombre_archivo = f"{tipo_datos.lower()}_listado.pdf"
    ruta_pdf = os.path.join(DOWNLOAD_DIR, nombre_archivo)
    
    with open(ruta_pdf, "wb") as f:
        f.write(r_pdf.content)
        
    logger.info(f"PDF {tipo_datos} guardado exitosamente en: {ruta_pdf}")
    return ruta_pdf

def navegar_pagina2_y_descargar_pdfs(session: requests.Session, url_base: str) -> list[str]:
    """
    Descarga el 'PDF maestro de titulares' para extraer
    a los titulares de cada grado. Es el mismo listado de estudiantes, pero SIN
    marcar la casilla 'escuela_nueva'.
    """
    logger.info("=" * 50)
    logger.info("FASE A — Descarga de PDF Maestro de Titulares")
    logger.info("=" * 50)
    
    url_formulario = urllib.parse.urljoin(url_base, "/admin_lista_uso_general.php")
    r1 = session.get(url_formulario)
    soup = BeautifulSoup(r1.text, 'html.parser')
    form1 = soup.find('form', attrs={'name': 'form1'})
    if not form1:
        return []
        
    action1 = urllib.parse.urljoin(r1.url, form1.get('action'))
    data_form1 = {i.get('name'): i.get('value', '') for i in form1.find_all('input') if i.get('name')}
    data_form1['destino'] = 'ES' # Esudiantes
    data_form1['noretirados'] = '1'
    
    r2 = session.post(action1, data=data_form1)
    html_res = r2.text
    idx_btn = html_res.find('btn-dark')
    if idx_btn == -1:
        return []
        
    form_start = html_res.rfind('<form', 0, idx_btn)
    form_end = html_res.find('</form>', idx_btn)
    form_html = html_res[form_start:form_end+7]
    
    action_match = re.search(r'action="([^"]+)"', form_html)
    if not action_match:
        return []
        
    action_pdf = urllib.parse.urljoin(r2.url, action_match.group(1))
    
    data_pdf = {}
    for m in re.finditer(r'(?i)<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', form_html):
        data_pdf[m.group(1)] = m.group(2)
    for m in re.finditer(r'(?i)<select[^>]*name="([^"]+)"[^>]*>.*?<option[^>]*value="([^"]*)"', form_html, re.DOTALL):
        data_pdf[m.group(1)] = m.group(2)
        
    data_pdf['boton'] = 'Imprimir'
    # IMPORTANTE: No enviamos escuela_nueva para obtener el PDF maestro.
    if 'escuela_nueva' in data_pdf:
        del data_pdf['escuela_nueva']
    if 'condocumento' in data_pdf:
        del data_pdf['condocumento']
        
    r_pdf = session.post(action_pdf, data=data_pdf)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ruta_pdf = os.path.join(DOWNLOAD_DIR, "titulares_maestro.pdf")
    with open(ruta_pdf, "wb") as f:
        f.write(r_pdf.content)
        
    logger.info(f"PDF Maestro de Titulares guardado: {ruta_pdf}")
    return [ruta_pdf]

def navegar_y_descargar_docentes(session: requests.Session, url_base: str) -> str | None:
    """
    Descarga el PDF del listado de docentes.
    """
    return navegar_y_generar_listado(session, url_base, "Docentes")
