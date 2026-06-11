# =============================================================================
# modules/navegacion.py — Navegación de menús y generación del listado
# =============================================================================

import os
import time
from playwright.sync_api import Page, BrowserContext
from .logger import get_logger
from .config import ELEMENT_TIMEOUT, WEB_URL, DOWNLOAD_DIR

logger = get_logger("navegacion")


# =============================================================================
#  HELPERS
# =============================================================================

def _click_por_texto(page: Page, texto: str, tag: str = "*") -> bool:
    texto_lower = texto.lower()
    xpath = (
        f"//{tag}[contains("
        f"translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ',"
        f"'abcdefghijklmnopqrstuvwxyzáéíóúñ'),'{texto_lower}')]"
    )
    # 1. Buscar en la página principal
    try:
        locator = page.locator(xpath).first
        if locator.is_visible(timeout=2000):
            locator.click()
            logger.debug(f" Click en: '{texto}' (página principal)")
            return True
    except Exception:
        pass

    # 2. Buscar en frames
    for frame in page.frames:
        try:
            locator = frame.locator(xpath).first
            if locator.is_visible(timeout=1000):
                locator.click()
                logger.debug(f" Click en: '{texto}' (en frame '{frame.name}')")
                return True
        except Exception:
            continue

    logger.warning(f" No se encontró elemento con texto: '{texto}'")
    return False


def _marcar_checkbox_por_id(page: Page, checkbox_id: str) -> bool:
    try:
        cb = page.locator(f"id={checkbox_id}")
        cb.wait_for(state="attached", timeout=ELEMENT_TIMEOUT * 1000)
        if not cb.is_checked():
            cb.scroll_into_view_if_needed()
            time.sleep(0.3)
            cb.check()
            logger.debug(f"️  Checkbox '{checkbox_id}' marcado")
        return True
    except Exception:
        logger.warning(f"️  No se encontró checkbox id='{checkbox_id}'")
        return False


def _marcar_checkbox_no_retirados(page: Page) -> bool:
    # Estrategia 1: Label con texto "retirados"
    try:
        label_xpath = (
            "//label[contains("
            "translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ',"
            "'abcdefghijklmnopqrstuvwxyzáéíóúñ'),'retirados')]"
        )
        label = page.locator(label_xpath).first
        label.wait_for(state="attached", timeout=3000)
        for_attr = label.get_attribute("for")
        if for_attr:
            cb = page.locator(f"id={for_attr}")
        else:
            cb = label.locator("//input[@type='checkbox']").first
        if not cb.is_checked():
            cb.check()
        logger.info("️  'No incluir retirados ni desertores' marcado")
        return True
    except Exception:
        pass

    # Estrategia 2: Checkbox precedente al input de retirados
    try:
        cb = page.locator("//input[@id='soloretirados']/preceding::input[@type='checkbox'][1]").first
        if not cb.is_checked():
            cb.check()
        logger.info("️  'No incluir retirados ni desertores' marcado (estrategia preceding)")
        return True
    except Exception:
        pass

    return False


def _seleccionar_tomar_datos_de(page: Page, tipo: str) -> bool:
    """
    Selecciona de qué tabla se tomarán los datos ('Estudiantes' o 'Docentes').
    El selector de 'Docentes' aparece MÁS ARRIBA que el checkbox de 'No retirados'.
    Prueba múltiples estrategias: radio button, label, select dropdown.
    """
    logger.info(f" Seleccionando tomar datos de: '{tipo}'")
    tipo_lower = tipo.lower()

    # Estrategia 1: Radio dentro de label con ese texto
    try:
        xpath_radio = (
            f"//label[contains("
            f"translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ',"
            f"'abcdefghijklmnopqrstuvwxyzáéíóúñ'),'{tipo_lower}')]"
            f"//input[@type='radio']"
        )
        radio = page.locator(xpath_radio).first
        radio.wait_for(state="attached", timeout=3000)
        radio.check()
        logger.info(f" Radio '{tipo}' seleccionado (estrategia label>radio)")
        return True
    except Exception:
        pass

    # Estrategia 2: Radio seguido de texto hermano
    try:
        xpath_radio2 = (
            f"//input[@type='radio' and "
            f"following-sibling::text()[contains("
            f"translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ',"
            f"'abcdefghijklmnopqrstuvwxyzáéíóúñ'),'{tipo_lower}'"
            f")]]"
        )
        radio2 = page.locator(xpath_radio2).first
        radio2.wait_for(state="attached", timeout=2000)
        radio2.check()
        logger.info(f" Radio '{tipo}' seleccionado (estrategia radio+sibling)")
        return True
    except Exception:
        pass

    # Estrategia 3: Select dropdown con opción coincidente
    try:
        selects = page.locator("select")
        count = selects.count()
        for i in range(count):
            s = selects.nth(i)
            opts = s.locator(f"option:has-text('{tipo}')")
            if opts.count() > 0:
                s.select_option(label=tipo)
                logger.info(f" Select '{tipo}' seleccionado (estrategia dropdown)")
                return True
    except Exception:
        pass

    logger.warning(f"️  No se pudo seleccionar tipo de datos '{tipo}'")
    return False


def _pagina_formulario_valida(page: Page) -> bool:
    """Verifica que la página sea válida y contenga elementos de formulario reales."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass
        
    url_actual = page.url
    if "admin_lista_uso_general" not in url_actual:
        logger.info(f"_pagina_formulario_valida: URL invalida: {url_actual}")
        return False

    try:
        if page.locator("text='Acceso Denegado'").count() > 0:
            logger.info("_pagina_formulario_valida: 'Acceso Denegado' encontrado")
            return False
            
        try:
            page.locator("input[type='radio'], select").first.wait_for(state="attached", timeout=5000)
        except Exception:
            pass
            
        hay_radios = page.locator("input[type='radio']").count() > 0
        hay_selects = page.locator("select").count() > 0
        if not (hay_radios or hay_selects):
            html_content = page.content()[:500]
            logger.info(f"_pagina_formulario_valida: No hay radios ni selects. HTML snippet: {html_content}")
            return False
    except Exception as e:
        logger.info(f"_pagina_formulario_valida: Excepcion: {e}")
        return False
        
    return True


def _retornar_a_dashboard(page: Page):
    """Retorna al dashboard principal navegando a la página principal y pasando el modal si es necesario."""
    page.goto(WEB_URL)
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
        
    try:
        btn_acceder_modal = page.locator("input.btn-primary[value='Acceder'], button:has-text('Acceder')").first
        if btn_acceder_modal.is_visible(timeout=3000):
            btn_acceder_modal.click()
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
    except Exception:
        pass

def _ir_a_pagina_formulario(page: Page) -> bool:
    """Navega a la página del formulario de listas de uso general con estrategia de fallback robusta."""
    base = WEB_URL.rstrip('/')
    if '/' in base.split('//')[-1]:
        base = base.rsplit('/', 1)[0]
    url_pagina1 = base + "/admin_lista_uso_general.php"

    logger.info(f" Navegando a: {url_pagina1}")
    try:
        page.goto(url_pagina1)
        time.sleep(2.5)
    except Exception as e:
        logger.warning(f"Excepción al navegar directo: {e}")

    if not _pagina_formulario_valida(page):
        logger.warning(f" Acceso directo bloqueado o página inválida. Retornando al panel y usando menú...")
        _retornar_a_dashboard(page)
        time.sleep(2)
        
        _click_por_texto(page, "administrativo", tag="a")
        time.sleep(1.5)
        _click_por_texto(page, "listas")
        time.sleep(1.5)
        if not _click_por_texto(page, "uso general", tag="a"):
            _click_por_texto(page, "uso general")
        time.sleep(2.5)
        
        if not _pagina_formulario_valida(page):
            raise Exception("No se pudo alcanzar la página del formulario ni usando acceso directo ni menú.")

    return True


def _click_siguiente(page: Page) -> bool:
    """Presiona el botón 'Siguiente' del formulario."""
    logger.info("▶️  Presionando 'Siguiente'")
    siguiente_xpath = (
        "//button[@id='button'] | //input[@id='button'] | "
        "//input[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'siguiente')] | "
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'siguiente')]"
    )
    try:
        btn_sig = page.locator(siguiente_xpath).first
        btn_sig.wait_for(state="visible", timeout=5000)
        btn_sig.scroll_into_view_if_needed()
        time.sleep(0.3)
        btn_sig.click()
        time.sleep(2.5)
        return True
    except Exception:
        if _click_por_texto(page, "siguiente"):
            time.sleep(2.5)
            return True
    logger.error(" No se encontró el botón 'Siguiente'")
    return False


def _click_imprimir(context: BrowserContext, page: Page) -> Page | None:
    """Presiona 'Imprimir' y retorna la nueva página/pestaña resultante."""
    logger.info("️  Presionando 'Imprimir'")
    
    ruta_pdf_impresion = os.path.join(DOWNLOAD_DIR, "impresion.pdf")
    if os.path.exists(ruta_pdf_impresion):
        try:
            os.remove(ruta_pdf_impresion)
        except Exception:
            pass

    imprimir_xpath = (
        "//input[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'imprimir') "
        "or contains(@class,'btn-dark')] | "
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'imprimir')]"
    )
    
    # Interceptar PDFs generados inline (ej: listas de estudiantes que ahora son PDF)
    pdf_interceptado = []
    
    def handle_route(route):
        try:
            if route.request.resource_type in ["document", "fetch", "xhr"]:
                response = route.fetch()
                ctype = response.headers.get("content-type", "").lower()
                if "application/pdf" in ctype:
                    logger.info(f" PDF interceptado vía route: {route.request.url}")
                    with open(ruta_pdf_impresion, "wb") as f:
                        f.write(response.body())
                    pdf_interceptado.append(True)
                route.fulfill(response=response)
            else:
                route.continue_()
        except Exception as e:
            logger.error(f" Error en route fetch (PDF): {e}")
            try:
                route.continue_()
            except:
                pass

    context.route("**/*", handle_route)

    try:
        with context.expect_page(timeout=15000) as new_page_info:
            btn_imp = page.locator(imprimir_xpath).first
            btn_imp.wait_for(state="visible", timeout=ELEMENT_TIMEOUT * 1000)
            btn_imp.scroll_into_view_if_needed()
            time.sleep(0.3)
            btn_imp.click()
        new_page = new_page_info.value
        try:
            new_page.wait_for_load_state(timeout=5000)
        except Exception:
            pass
            
        time.sleep(2) # Esperar a que el route termine de escribir el PDF
        context.unroute("**/*", handle_route)
        
        if pdf_interceptado:
            logger.info(f" PDF guardado exitosamente en {ruta_pdf_impresion}")
            
        logger.info(f" Nueva pestaña: {new_page.url}")
        return new_page
    except Exception as e:
        context.unroute("**/*", handle_route)
        logger.warning(f"️  expect_page falló: {e}")
        
        if pdf_interceptado:
            logger.info(f" PDF guardado tras timeout en {ruta_pdf_impresion}")
            
        pages = context.pages
        if len(pages) > 1:
            logger.info(f" Usando última pestaña de {len(pages)} disponibles")
            return pages[-1]
        return None


# =============================================================================
#  DESCARGA DEL PDF DEL LISTADO DE DOCENTES (Fase B)
# =============================================================================

def descargar_pdf_docentes(page: Page) -> str | None:
    """
    Estando en la Página 2 del formulario (con 'Docentes' ya seleccionado),
    hace click en 'Imprimir Todos' y captura la descarga del PDF.
    Retorna la ruta al archivo guardado, o None si falló.
    """
    logger.info("️  Descargando PDF del listado de docentes...")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ruta_pdf = os.path.join(DOWNLOAD_DIR, "docentes_listado.pdf")

    # Limpiar archivo previo
    if os.path.exists(ruta_pdf):
        try:
            os.remove(ruta_pdf)
        except Exception:
            pass

    # Estrategia 1: Botón "Imprimir Todos" con expect_download
    try:
        btn_xpath = (
            "//input[contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'imprimir todos')] | "
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'imprimir todos')]"
        )
        btn = page.locator(btn_xpath).first
        btn.wait_for(state="visible", timeout=5000)
        with page.expect_download(timeout=20000) as dl_info:
            btn.click()
        dl = dl_info.value
        dl.save_as(ruta_pdf)
        logger.info(f" PDF de docentes guardado: {ruta_pdf}")
        return ruta_pdf
    except Exception as e:
        logger.warning(f"️  'Imprimir Todos' falló: {e}")

    # Estrategia 2: Primer botón de imagen (print_p) de la tabla de filas
    try:
        btn2 = page.locator("input[type='image'][src*='print_p']").first
        btn2.wait_for(state="visible", timeout=3000)
        with page.expect_download(timeout=20000) as dl_info:
            btn2.click()
        dl = dl_info.value
        dl.save_as(ruta_pdf)
        logger.info(f" PDF de docentes guardado (estrategia 2): {ruta_pdf}")
        return ruta_pdf
    except Exception as e:
        logger.warning(f"️  Botón imagen falló: {e}")

    logger.error(" No se pudo descargar el PDF del listado de docentes")
    return None


# =============================================================================
#  DESCARGA DE PDFs DE TITULARES (Página 2 del formulario)
# =============================================================================

def descargar_pdfs_grados(context: BrowserContext, page: Page) -> list[str]:
    """
    En la Página 2 del formulario (después de 'Siguiente'), hace click en el
    botón 'Imprimir' general, descargando un solo PDF maestro de todas
    las páginas, el cual contiene a todos los titulares en la cabecera.
    """
    logger.info(" Buscando PDF maestro de titulares en Página 2...")
    rutas_pdfs = []
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    try:
        time.sleep(2)
        new_page = _click_imprimir(context, page)
        if new_page:
            try:
                new_page.close()
            except:
                pass
            
        ruta_impresion = os.path.join(DOWNLOAD_DIR, "impresion.pdf")
        if os.path.exists(ruta_impresion):
            ruta_final = os.path.join(DOWNLOAD_DIR, "titulares_maestro.pdf")
            if os.path.exists(ruta_final):
                os.remove(ruta_final)
            os.rename(ruta_impresion, ruta_final)
            logger.info(f" PDF maestro guardado: {ruta_final}")
            rutas_pdfs.append(ruta_final)
        else:
            logger.error(" No se encontró el PDF impreso maestro.")

    except Exception as e:
        logger.error(f" Error general buscando PDF maestro de grados: {e}")

    logger.info(f" Total PDFs maestros descargados: {len(rutas_pdfs)}")
    return rutas_pdfs


# =============================================================================
#  FUNCIÓN: Navegar a Página 2 y descargar PDFs de titulares
#  (Solo para el flujo de Docentes — Fase A)
# =============================================================================

def navegar_pagina2_y_descargar_pdfs(context: BrowserContext, page: Page) -> list[str]:
    """
    Flujo exclusivo para la Fase A del scraping de Docentes:
    1. Va a la página del formulario (modo Estudiantes, que es el default)
    2. Marca "No incluir retirados"
    3. Presiona "Siguiente" → llega a Página 2 con lista de grados + PDFs
    4. Descarga TODOS los PDFs de cada grado (contienen el docente titular)
    5. Retorna la lista de rutas de PDFs descargados

    NO presiona "Imprimir todos los alumnos (escuela nueva)" — eso es solo para estudiantes.
    """
    logger.info("=" * 50)
    logger.info("FASE A — Descarga de PDFs de titulares por grado")
    logger.info("=" * 50)

    try:
        # Paso 1: Ir al formulario
        _ir_a_pagina_formulario(page)

        # Paso 2: Marcar "No incluir retirados"
        logger.info("️  Marcando 'No incluir retirados ni desertores'")
        _marcar_checkbox_no_retirados(page)

        # Paso 3: Click "Siguiente" → Página 2
        if not _click_siguiente(page):
            logger.error(" No se pudo avanzar a Página 2 para descargar PDFs")
            return []

        # Paso 4: Descargar PDFs (estamos en Página 2)
        rutas = descargar_pdfs_grados(context, page)

        return rutas

    except Exception as e:
        logger.error(f" Error en navegar_pagina2_y_descargar_pdfs: {e}", exc_info=True)
        try:
            page.screenshot(path="logs/screenshot_fase_a_error.png")
        except Exception:
            pass
        return []


# =============================================================================
#  FUNCIÓN: Descargar PDF del listado de docentes (Fase B completa)
# =============================================================================

def navegar_y_descargar_docentes(page: Page) -> str | None:
    """
    Flujo completo de la Fase B para Docentes:
    1. Va al formulario, selecciona 'Docentes', presiona 'Siguiente'
    2. En Página 2, descarga el PDF del listado de docentes
    Retorna la ruta al PDF guardado, o None si falló.
    """
    logger.info("=" * 50)
    logger.info("FASE B — Descarga del PDF del listado de docentes")
    logger.info("=" * 50)
    try:
        _ir_a_pagina_formulario(page)
        _seleccionar_tomar_datos_de(page, "Docentes")
        time.sleep(1)
        if not _click_siguiente(page):
            logger.error(" No se pudo presionar 'Siguiente' en Fase B")
            return None
        return descargar_pdf_docentes(page)
    except Exception as e:
        logger.error(f" Error en navegar_y_descargar_docentes: {e}", exc_info=True)
        return None


# =============================================================================
#  FUNCIÓN PRINCIPAL — Genera el listado (Estudiantes)
# =============================================================================

def navegar_y_generar_listado(
    context: BrowserContext,
    page: Page,
    tipo_datos: str = "Estudiantes",
    descargar_titulares: bool = False  # Parámetro legacy, ignorado
) -> Page | None:
    """
    Ejecuta el flujo completo del formulario para generar el listado final.

    Para Estudiantes:
      Pág1 [Estudiantes, No retirados] → Siguiente → [Escuela Nueva] → Imprimir → nueva pestaña HTML

    Para Docentes:
      Pág1 [Docentes, No retirados] → Siguiente → Imprimir → nueva pestaña HTML

    El parámetro `descargar_titulares` está deprecado. La descarga de PDFs de
    titulares se maneja con `navegar_pagina2_y_descargar_pdfs()` en Fase A.
    """
    if descargar_titulares:
        logger.warning(
            "️  navegar_y_generar_listado() llamado con descargar_titulares=True. "
            "Este parámetro está deprecado. Usa navegar_pagina2_y_descargar_pdfs() para Fase A."
        )

    try:
        # ── Paso 1: Ir al formulario ────────────────────────────────────────
        _ir_a_pagina_formulario(page)

        # ── Paso 1.5: Seleccionar tomar datos de (Estudiantes o Docentes) ───
        _seleccionar_tomar_datos_de(page, tipo_datos)

        # ── Paso 2: Marcar "No incluir retirados ni desertores" ─────────────
        logger.info("️  Marcando 'No incluir retirados ni desertores'")
        _marcar_checkbox_no_retirados(page)

        # ── Paso 3: Click "Siguiente" ────────────────────────────────────────
        if not _click_siguiente(page):
            raise Exception("No se pudo presionar 'Siguiente'")

        # ── Paso 4: Marcar "Escuela Nueva" (solo Estudiantes) ───────────────
        logger.info("️  Marcando 'Imprimir todos los alumnos (tipo escuela nueva)'")
        if not _marcar_checkbox_por_id(page, "escuela_nueva"):
            try:
                label = page.locator(
                    "//label[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ',"
                    "'abcdefghijklmnopqrstuvwxyzáéíóúñ'),'escuela nueva')]"
                ).first
                cb = label.locator("//input[@type='checkbox']").first
                if not cb.is_checked():
                    cb.check()
                logger.info("️  'Escuela Nueva' marcado por label")
            except Exception:
                logger.warning("️  No se encontró checkbox 'escuela nueva'")

        # ── Paso 5: Click "Imprimir" → nueva pestaña ────────────────────────
        new_page = _click_imprimir(context, page)
        if not new_page:
            raise Exception("No se obtuvo pestaña de resultados")
        return new_page

    except Exception as e:
        logger.error(f" Error durante navegación (Estudiantes): {e}", exc_info=True)
        try:
            page.screenshot(path="logs/screenshot_navegacion_error.png")
        except Exception:
            pass
        return None
