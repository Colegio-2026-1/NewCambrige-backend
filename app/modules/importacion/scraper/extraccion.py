# =============================================================================
# modules/extraccion.py — Extracción de datos del listado
# =============================================================================

import os
import re
import json
import time
import glob
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import Page
import pdfplumber
import pandas as pd
from .logger import get_logger
from .config import DOWNLOAD_DIR, DOWNLOAD_TIMEOUT

logger = get_logger("extraccion")

PATRON_PERSONA = re.compile(
    r'^\s*(\d+)\s+(\d{5,15})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)(?:\s+([A-Z0-9]{2})\s+([A-Z0-9]{2}))?\s*$',
    re.IGNORECASE | re.MULTILINE
)

MAPA_GRADOS = {
    "00": "Transicion", "01": "Primero", "02": "Segundo", "03": "Tercero",
    "04": "Cuarto", "05": "Quinto", "06": "Sexto", "07": "Septimo",
    "08": "Octavo", "09": "Noveno", "10": "Decimo", "11": "Once",
    "JA": "Jardin", "PA": "Parvulos", "PJ": "Prejardin"
}

def _mapear_curso(codigo: str) -> str:
    try:
        n = int(codigo)
        if 1 <= n <= 26:
            return chr(ord('A') + n - 1)
    except ValueError:
        pass
    return codigo if codigo else ""


# =============================================================================
#  EXTRACCIÓN DESDE HTML / PDF
# =============================================================================

def extraer_desde_html(page: Page, tipo: str = "estudiantes") -> Optional[List[Dict]]:
    logger.info(f" Extrayendo {tipo} desde HTML...")
    try:
        tablas = page.locator("//table")
        count = tablas.count()
        if count > 0:
            texto_total = ""
            for i in range(count):
                texto_total += tablas.nth(i).inner_text() + "\n"
            resultados = _parsear_texto(texto_total, tipo)
            if resultados:
                logger.info(f" {len(resultados)} registros extraídos desde tablas HTML")
                return resultados

        body = page.inner_text("body")
        resultados = _parsear_texto(body, tipo)
        if resultados:
            logger.info(f" {len(resultados)} registros extraídos desde body HTML")
            return resultados
    except Exception as e:
        logger.warning(f"️  Error leyendo HTML: {e}")

    logger.warning("️  No se encontraron registros en el HTML")
    return None


def extraer_desde_pdf(pdf_path: str, tipo: str = "estudiantes") -> Optional[List[Dict]]:
    if not os.path.exists(pdf_path):
        return None
    logger.info(f" Leyendo PDF: {pdf_path}")
    paginas = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    paginas.append(texto)
    except Exception as e:
        logger.error(f" Error leyendo PDF: {e}")
        return None

    todos = "\n".join(paginas)
    resultados = _parsear_texto(todos, tipo)
    if resultados:
        logger.info(f" {len(resultados)} registros extraídos del PDF")
    return resultados or None


def esperar_pdf_descargado() -> Optional[str]:
    logger.info(f"⏳ Esperando PDF en: {DOWNLOAD_DIR}")
    inicio = time.time()
    while time.time() - inicio < DOWNLOAD_TIMEOUT:
        pdfs = [f for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*.pdf"))
                if not f.endswith(".crdownload") and "titulares" not in f]
        if pdfs:
            pdf_reciente = max(pdfs, key=os.path.getmtime)
            logger.info(f" PDF listo: {pdf_reciente}")
            return pdf_reciente
        time.sleep(2)
    logger.error(" Tiempo agotado esperando PDF")
    return None


# =============================================================================
#  ORQUESTADORES
# =============================================================================

def extraer_estudiantes(page: Page) -> List[Dict]:
    """Extrae estudiantes desde el HTML de resultado o PDF."""
    resultados = extraer_desde_html(page, "estudiantes")
    if resultados:
        return resultados
    context = page.context
    if context:
        for p in context.pages:
            resultados = extraer_desde_html(p, "estudiantes")
            if resultados:
                return resultados
    pdf_path = esperar_pdf_descargado()
    if pdf_path:
        resultados = extraer_desde_pdf(pdf_path)
        if resultados:
            return resultados
    return []


def extraer_docentes(page, titulares: Dict[str, Dict] = None, registros_raw: List[Dict] = None) -> List[Dict]:
    """
    Extrae docentes y los enriquece con información de titulares.
    
    Si `registros_raw` se provee, lo usa directamente (ya extraído del PDF).
    En caso contrario intenta extraer desde `page` (HTML o PDF interceptado).
    """
    resultados = registros_raw or []

    if not resultados:
        ruta_impresion = os.path.join(DOWNLOAD_DIR, "docentes_listado.pdf")
        if os.path.exists(ruta_impresion):
            logger.info(" PDF 'docentes_listado.pdf' encontrado, extrayendo desde PDF...")
            resultados = extraer_desde_pdf(ruta_impresion, "docentes") or []

    if not resultados and page is not None:
        resultados = extraer_desde_html(page, "docentes") or []
        if not resultados:
            context = getattr(page, "context", None)
            if context:
                for p in context.pages:
                    resultados = extraer_desde_html(p, "docentes") or []
                    if resultados:
                        break

    if not resultados and page is None:
        logger.warning("️  No hay registros ni page disponible para extraer docentes")

    if not resultados:
        return []

    # Enriquecer con titulares
    titulares = titulares or {}
    titulares_norm = {
        re.sub(r'\s+', '', k).lower(): v
        for k, v in titulares.items()
    }

    docentes_finales = []
    for r in resultados:
        nombre_norm = re.sub(r'\s+', '', r["nombre"]).lower()
        datos_titular = titulares_norm.get(nombre_norm, {})
        
        grado_titular = datos_titular.get("grado_titular", None)
        curso_titular = datos_titular.get("curso_titular", None)
        
        # Filtramos para retornar únicamente los docentes que son titulares
        if grado_titular and curso_titular:
            docentes_finales.append({
                "consecutivo":   r["consecutivo"],
                "documento":     r["documento"],
                "nombre":        r["nombre"],
                "grado_titular": grado_titular,
                "curso_titular": curso_titular,
            })

    return docentes_finales


def extraer_titulares_de_pdfs(rutas_pdfs: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Lee los PDFs individuales por grado descargados desde la Página 2 del formulario.
    Cada PDF de grado tiene un header con campos como:
        Grado: Primero    Curso: A    Titular: VARGAS MONCADA ERLY MARIA

    Estrategias de extracción (en orden de prioridad):
    1. Regex sobre el texto del PDF buscando "Titular:" seguido del nombre.
    2. Campo 'titular' ya parseado por _parsear_texto() si hay registros en el PDF.
    3. Patrón literal alternativo: "es titular del grado X curso Y".

    Retorna dict: { "VARGAS MONCADA ERLY MARIA": { "grado_titular": "Primero", "curso_titular": "A" } }
    """
    titulares = {}

    # Patrón 1 (principal): "Titular: NOMBRE APELLIDO APELLIDO"
    patron_titular_header = re.compile(
        r'Titular\s*:\s*([A-ZÁÉÍÓÚÑ][a-zA-ZÁÉÍÓÚñÑ\s]{3,}?)(?=\s+Fecha:|$)',
        re.IGNORECASE
    )
    # Patrón de grado y curso en header
    patron_grado = re.compile(r'Grado\s*:\s*([A-Za-záéíóúÁÉÍÓÚñÑ0-9\s]+?)(?=\s+Curso:|$)', re.IGNORECASE)
    patron_curso  = re.compile(r'Curso\s*:\s*([A-Za-z0-9]+)', re.IGNORECASE)

    # Patrón 2 (fallback): "X es titular del grado Y curso Z"
    patron_titular_frase = re.compile(
        r'([a-záéíóúÁÉÍÓÚñÑ\s]+?)\s+es\s+titular\s+del\s+grado\s+([a-záéíóúÁÉÍÓÚñÑ0-9]+)\s+curso\s+([a-záéíóúÁÉÍÓÚñÑ0-9]+)',
        re.IGNORECASE
    )

    for pdf_path in rutas_pdfs:
        if not os.path.exists(pdf_path):
            continue

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if not texto_pagina or not texto_pagina.strip():
                        continue

                    nombre_titular = None
                    grado = None
                    curso = None

                    # ── Estrategia 1: Buscar "Titular: NOMBRE" en el header ─────────
                    m_titular = patron_titular_header.search(texto_pagina)
                    if m_titular:
                        nombre_titular = _limpiar_nombre(m_titular.group(1))

                    m_grado = patron_grado.search(texto_pagina)
                    if m_grado:
                        grado = m_grado.group(1).strip().capitalize()

                    m_curso = patron_curso.search(texto_pagina)
                    if m_curso:
                        curso = m_curso.group(1).strip().upper()

                    # ── Estrategia 2: Usar _parsear_texto() que ya extrae el campo 'titular' ──
                    if not nombre_titular:
                        registros = _parsear_texto(texto_pagina)
                        if registros and registros[0].get("titular"):
                            nombre_titular = _limpiar_nombre(registros[0]["titular"])
                        if registros and not grado:
                            grado = registros[0].get("grado", "")
                        if registros and not curso:
                            curso = registros[0].get("curso", "")

                    # ── Estrategia 3: Frase literal alternativa ──────────────────────
                    if not nombre_titular:
                        m_frase = patron_titular_frase.search(texto_pagina)
                        if m_frase:
                            nombre_titular = _limpiar_nombre(m_frase.group(1))
                            grado = m_frase.group(2).strip().capitalize()
                            curso = m_frase.group(3).strip().upper()

                    if nombre_titular:
                        titulares[nombre_titular] = {
                            "grado_titular": grado,
                            "curso_titular": _mapear_curso(curso),
                        }
                        logger.info(
                            f"‍ Titular: {nombre_titular} → "
                            f"Grado: {grado or '?'} / Curso: {_mapear_curso(curso) or '?'} "
                            f"[{os.path.basename(pdf_path)}]"
                        )
                    else:
                        logger.warning(
                            f"️  No se encontró titular en una página de: {os.path.basename(pdf_path)}"
                        )

        except Exception as e:
            logger.warning(f"️  Error procesando {os.path.basename(pdf_path)}: {e}")

    logger.info(f" Total titulares extraídos: {len(titulares)}")
    return titulares


# =============================================================================
#  PARSEO DE TEXTO
# =============================================================================

def _parsear_texto(texto: str, tipo: str = "estudiantes") -> List[Dict]:
    if not texto:
        return []

    def extract_header(pattern):
        m = re.search(pattern, texto, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    jornada     = extract_header(r"Jornada:\s*([^\n\r]+?)(?=\s+Grado:|$)")
    grado_texto = extract_header(r"Grado:\s*([^\n\r]+?)(?=\s+Curso:|$)")
    curso       = extract_header(r"Curso:\s*([^\n\r]+?)(?=\s+Sede:|$)")
    sede        = extract_header(r"Sede:\s*([^\n\r]+)")
    
    # Extraer Jornada si viene embebida dentro del campo Sede
    if not jornada and "Jornada:" in sede:
        m_jornada = re.search(r"Jornada:\s*([a-zA-Z0-9_]+)", sede, re.IGNORECASE)
        if m_jornada:
            jornada = m_jornada.group(1).strip()
        sede = re.sub(r"\s*Jornada:\s*[a-zA-Z0-9_]+", "", sede, flags=re.IGNORECASE).strip()
        
    titular     = extract_header(r"Titular:\s*([^\n\r]+?)(?=\s+Fecha:|$)")

    resultados = []

    if tipo == "docentes":
        PATRON_DOCENTE = re.compile(
            r'^\s*(?:(\d+)\s+)?(\d{5,15})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s*$',
            re.IGNORECASE | re.MULTILINE
        )
        encontrados = PATRON_DOCENTE.findall(texto)
        for match in encontrados:
            consecutivo = match[0] if match[0] else "0"
            documento = match[1]
            nombre = match[2]
            
            nombre_limpio = _limpiar_nombre(nombre)
            documento_limpio = documento.strip()
            
            if nombre_limpio and documento_limpio:
                resultados.append({
                    "consecutivo": int(consecutivo),
                    "documento":   documento_limpio,
                    "nombre":      nombre_limpio,
                    "jornada":     jornada,
                    "grado":       grado_texto,
                    "curso":       curso,
                    "sede":        sede,
                    "titular":     titular,
                })
    else:
        encontrados = PATRON_PERSONA.findall(texto)
        for consecutivo, documento, nombre, cod_grado, cod_curso in encontrados:
            nombre_limpio = _limpiar_nombre(nombre)
            documento_limpio = documento.strip()
            grado_asignado = MAPA_GRADOS.get(cod_grado, cod_grado) if cod_grado else grado_texto
            curso_asignado = _mapear_curso(cod_curso) if cod_curso else _mapear_curso(curso)

            if nombre_limpio and documento_limpio:
                resultados.append({
                    "consecutivo": int(consecutivo),
                    "documento":   documento_limpio,
                    "nombre":      nombre_limpio,
                    "jornada":     jornada,
                    "grado":       grado_asignado,
                    "curso":       curso_asignado,
                    "sede":        sede,
                    "titular":     titular,
                })
    return resultados


def _limpiar_nombre(nombre: str) -> str:
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    nombre = re.sub(r'[^A-Za-záéíóúÁÉÍÓÚñÑ\s]', '', nombre).strip()
    return nombre[:100] if len(nombre) > 100 else nombre


# =============================================================================
#  SERIALIZACIÓN
# =============================================================================

def guardar_json(datos: List[Dict], path: str = None) -> str:
    if not datos:
        return ""
    if path is None:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        path = os.path.join(DOWNLOAD_DIR, "extraccion.json")

    payload = {
        "metadata": {
            "total": len(datos),
            "fecha_extraccion": datetime.now().isoformat(),
        },
        "datos": datos,
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def guardar_csv_respaldo(datos: List[Dict], path: str = None) -> str:
    if not datos:
        return ""
    if path is None:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        path = os.path.join(DOWNLOAD_DIR, "respaldo.csv")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    df = pd.DataFrame(datos)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def cargar_json(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("datos", [])
