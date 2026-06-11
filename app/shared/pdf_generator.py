from fpdf import FPDF
from datetime import datetime
from typing import Optional
import os


def _build_pdf(data: dict, tipo: str, sello_path: Optional[str] = None, firma_map: Optional[dict] = None) -> FPDF:
    nombre = data.get("nombre", "")
    documento = data.get("documento", "")
    periodo = data.get("periodo_nombre", "")
    detalle = data.get("detalle_firmas", [])

    if tipo == "estudiante":
        grado = data.get("grado", "")
        grupo = data.get("grupo", "")
    else:
        grado = ""
        grupo = ""

    grupo_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
    grupo = grupo_map.get(str(grupo), grupo)
    grado_map = {
        "1": "PRIMERO", "2": "SEGUNDO", "3": "TERCERO", "4": "CUARTO",
        "5": "QUINTO", "6": "SEXTO", "7": "SEPTIMO", "8": "OCTAVO",
        "9": "NOVENO", "10": "DECIMO", "11": "ONCE",
        "12": "JARDIN", "13": "PARVULOS", "14": "PREJARDIN",
        "15": "PREESCOLAR", "16": "TRANSICION", "17": "NURSERY",
    }
    grado = grado_map.get(str(grado), grado)

    pdf = FPDF(orientation="L", format="A4")
    pdf.add_page()

    # Header azul
    pdf.set_fill_color(208, 225, 255)
    pdf.rect(0, 0, 297, 18, "F")

    # Título
    pdf.set_xy(0, 3)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(297, 10, "PAZ Y SALVO", align="C")

    # Cuerpo
    pdf.set_y(25)

    # Info: Nombre
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(16, 6, "Nombre:", align="L")
    pdf.line(48, pdf.get_y() + 4, 140, pdf.get_y() + 4)

    pdf.set_xy(48, pdf.get_y() - 1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(80, 6, nombre, align="L")

    # Info: Código
    pdf.set_xy(165, 25)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(14, 6, "Código:", align="L")
    pdf.line(196, 29, 265, 29)

    pdf.set_xy(196, 24)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(60, 6, documento, align="L")

    # Info: Grado/Grupo (solo estudiantes)
    y_actual = 34
    if tipo == "estudiante" and (grado or grupo):
        pdf.set_xy(15, y_actual)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(80, 5, f"Grado: {grado}  |  Grupo: {grupo}", align="L")
        pdf.set_text_color(0, 0, 0)
        y_actual += 7
    else:
        y_actual += 2

    # Periodo
    pdf.set_xy(15, y_actual)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(80, 5, f"Periodo: {periodo}", align="L")
    pdf.set_text_color(0, 0, 0)

    # Grid de módulos
    cant = len(detalle)
    if cant == 0:
        pass
    elif tipo == "docente":
        # 1 módulo centrado
        x_centro = 148
        y_mod = 85
        pdf.line(x_centro - 40, y_mod, x_centro + 40, y_mod)
        if detalle[0].get("firmado") and firma_map:
            img_path = firma_map.get(detalle[0]["nombre"])
            if img_path and os.path.exists(img_path):
                pdf.image(img_path, x=x_centro - 15, y=y_mod - 30, w=30, h=30)
        pdf.set_xy(x_centro - 20, y_mod + 3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 5, detalle[0]["nombre"], align="C")
    else:
        ancho_modulo = 60
        margen_izquierdo = 20
        espacio_col = 38.5 

        cols = [
            margen_izquierdo + (ancho_modulo / 2),                             # Columna 1
            margen_izquierdo + ancho_modulo + espacio_col + (ancho_modulo / 2), # Columna 2
            margen_izquierdo + (ancho_modulo * 2) + (espacio_col * 2) + (ancho_modulo / 2) # Columna 3
        ]
        
        filas_y = [85, 135]

        for idx, m in enumerate(detalle):
            col = idx % 3
            fila = idx // 3
            cx = cols[col]
            cy = filas_y[fila]

            es_dict = isinstance(m, dict)
            firmado = m.get("firmado") if es_dict else getattr(m, "firmado", False)
            nombre_modulo = m.get("nombre", "") if es_dict else getattr(m, "nombre", "")
            no_aplica = m.get("no_aplica") if es_dict else getattr(m, "no_aplica", False)

            pdf.line(cx - ancho_modulo / 2, cy, cx + ancho_modulo / 2, cy)

            if no_aplica and sello_path and os.path.exists(sello_path):
                pdf.image(sello_path, x=cx - 12, y=cy - 26, w=24, h=24)
            elif firmado and firma_map:
                img_path = firma_map.get(nombre_modulo)
                if img_path and os.path.exists(img_path):
                    pdf.image(img_path, x=cx - 12, y=cy - 26, w=24, h=24)

            # Texto del módulo debajo de la línea
            pdf.set_xy(cx - ancho_modulo / 2, cy + 3)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(ancho_modulo, 5, nombre_modulo, align="C")

    # Footer
    pdf.set_y(180)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C")
    pdf.set_text_color(0, 0, 0)

    return pdf


def generar_pdf_paz_salvo(data: dict, tipo: str, sello_path: Optional[str] = None, firma_map: Optional[dict] = None) -> bytes:
    pdf = _build_pdf(data, tipo, sello_path, firma_map)
    return bytes(pdf.output())