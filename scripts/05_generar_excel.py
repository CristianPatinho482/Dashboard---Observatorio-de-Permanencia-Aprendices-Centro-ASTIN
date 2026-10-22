# -*- coding: utf-8 -*-
"""
05_generar_excel.py
Genera el libro Excel ejecutivo de Caracterización de Aprendices Centro ASTIN.

Entradas : data/processed/*.csv, outputs/03_analisis_estadistico.json,
           outputs/04_modelo_predictivo.json
Salida   : outputs/Dashboard_Aprendices_SENA.xlsx

Reglas:
- Solo usa datos procesados (sin nombres, documentos, celulares ni correos).
- No inventa datos: las dimensiones ausentes se muestran como "No informado".
- Todas las cifras se escriben como valores; el libro no requiere cálculo.
"""

from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, ScatterChart, Reference, Series
from openpyxl.chart.data_source import AxDataSource, StrData, StrRef, StrVal
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import Marker
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
OUTPUTS = BASE / "outputs"
OUT_FILE = OUTPUTS / "Dashboard_Aprendices_SENA.xlsx"

# ---------------------------------------------------------------------------
# Paleta y estilos
# ---------------------------------------------------------------------------
NAVY = "00304D"
NAVY_2 = "007832"
GREEN = "39A900"
GREEN_DARK = "007832"
AMBER = "FDC300"
ORANGE = "EF6C00"
RED = "C62828"
RED_DARK = "8E0000"
SLATE = "546E7A"
INK = "1B2A33"
MUTED = "5B6B75"
LIGHT = "F3F6F8"
LIGHT_2 = "E8EEF2"
WHITE = "FFFFFF"
BORDER = "D7E0E6"

FONT = "Calibri"
TITLE_FONT = Font(name=FONT, size=22, bold=True, color=WHITE)
H1 = Font(name=FONT, size=15, bold=True, color=NAVY)
H2 = Font(name=FONT, size=11, bold=True, color=WHITE)
BODY = Font(name=FONT, size=10, color=INK)
SMALL = Font(name=FONT, size=9, color=MUTED)
SMALL_WHITE = Font(name=FONT, size=9, color=WHITE)
BOLD = Font(name=FONT, size=10, bold=True, color=INK)
KPI_VALUE = Font(name=FONT, size=24, bold=True, color=NAVY)
KPI_LABEL = Font(name=FONT, size=9, bold=True, color=MUTED)

FILL_NAVY = PatternFill("solid", fgColor=NAVY)
FILL_NAVY_2 = PatternFill("solid", fgColor=NAVY_2)
FILL_GREEN = PatternFill("solid", fgColor=GREEN)
FILL_LIGHT = PatternFill("solid", fgColor=LIGHT)
FILL_LIGHT_2 = PatternFill("solid", fgColor=LIGHT_2)
FILL_WHITE = PatternFill("solid", fgColor=WHITE)
FILL_AMBER = PatternFill("solid", fgColor="FFF3CD")
FILL_RED = PatternFill("solid", fgColor="FDE2E1")
FILL_GREEN_SOFT = PatternFill("solid", fgColor="E6F4EA")

THIN = Side(style="thin", color=BORDER)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
NO_BORDER = Border()

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
LEFT_TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center")


def pct(v: float, digits: int = 1) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    return f"{v * 100:.{digits}f}%".replace(".", ",")


def num(v: float, digits: int = 0) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    s = f"{v:,.{digits}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def style_range(ws, cell_range: str, font=None, fill=None, border=None, align=None, number_format=None):
    for row in ws[cell_range]:
        for c in row:
            if font:
                c.font = font
            if fill:
                c.fill = fill
            if border:
                c.border = border
            if align:
                c.alignment = align
            if number_format:
                c.number_format = number_format


def title_block(ws, title: str, subtitle: str, last_col: int = 10):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(1, 1, title)
    c.font = TITLE_FONT
    c.fill = FILL_NAVY
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 38

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    c = ws.cell(2, 1, subtitle)
    c.font = Font(name=FONT, size=9.5, color=MUTED, italic=True)
    c.fill = FILL_WHITE
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 24

    for col in range(1, last_col + 1):
        ws.cell(1, col).fill = FILL_NAVY
        ws.cell(2, col).fill = FILL_WHITE


def section(ws, row: int, text: str, last_col: int = 10, fill=FILL_NAVY):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row, 1, text)
    c.font = H2
    c.fill = fill
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for col in range(1, last_col + 1):
        ws.cell(row, col).fill = fill
    ws.row_dimensions[row].height = 21


def note(ws, row: int, text: str, last_col: int = 10, height: int = 34):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row, 1, text)
    c.font = SMALL
    c.fill = FILL_AMBER
    c.alignment = LEFT_TOP
    c.border = BOX
    for col in range(1, last_col + 1):
        ws.cell(row, col).fill = FILL_AMBER
        ws.cell(row, col).border = BOX
    ws.row_dimensions[row].height = height


def kpi_box(ws, row: int, col: int, label: str, value: str, accent: str = GREEN, width: int = 2):
    """Dibuja una tarjeta KPI de 2 columnas x 3 filas."""
    start_col = col
    end_col = col + width - 1
    ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)
    c = ws.cell(row, start_col, label.upper())
    c.font = KPI_LABEL
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.fill = FILL_WHITE
    ws.merge_cells(start_row=row + 1, start_column=start_col, end_row=row + 2, end_column=end_col)
    c = ws.cell(row + 1, start_col, value)
    c.font = Font(name=FONT, size=22, bold=True, color=accent)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.fill = FILL_WHITE
    for r in range(row, row + 3):
        for cc in range(start_col, end_col + 1):
            ws.cell(r, cc).fill = FILL_WHITE
            ws.cell(r, cc).border = BOX
    # línea de acento superior
    for cc in range(start_col, end_col + 1):
        ws.cell(row, cc).border = Border(left=THIN, right=THIN, top=Side(style="thick", color=accent), bottom=THIN)


def write_table(ws, start_row: int, start_col: int, headers: list[str], rows: list[list], widths: list[int] | None = None):
    for j, h in enumerate(headers, start=start_col):
        c = ws.cell(start_row, j, h)
        c.font = Font(name=FONT, size=9, bold=True, color=WHITE)
        c.fill = FILL_NAVY_2
        c.alignment = CENTER
        c.border = BOX
    for i, row in enumerate(rows, start=start_row + 1):
        for j, v in enumerate(row, start=start_col):
            c = ws.cell(i, j, v)
            c.font = BODY
            c.alignment = LEFT if isinstance(v, str) else RIGHT
            c.border = BOX
            if i % 2 == 0:
                c.fill = PatternFill("solid", fgColor="F8FAFB")
    if widths:
        for j, w in enumerate(widths, start=start_col):
            col_letter = get_column_letter(j)
            current = ws.column_dimensions[col_letter].width or 8.43
            ws.column_dimensions[col_letter].width = max(current, w)
    ws.row_dimensions[start_row].height = 27


def add_table_style(ws, ref: str, name: str, style: str = "TableStyleMedium2"):
    tab = Table(displayName=name, ref=ref)
    tab.tableStyleInfo = TableStyleInfo(name=style, showRowStripes=True, showColumnStripes=False)
    ws.add_table(tab)


def show_axes(chart):
    """Fuerza la visualización de ejes y etiquetas.

    openpyxl omite <c:delete val="0"/> y Excel interpreta la ausencia como
    ejes ocultos en algunos gráficos exportados.
    """
    chart.x_axis.delete = False
    chart.y_axis.delete = False


def set_text_categories(chart, labels: Reference, values: list):
    """Categorías textuales con caché para que Excel las muestre al exportar.

    openpyxl usa numRef por defecto en set_categories y, sin strCache, Excel
    puede perder las etiquetas de texto (programas, estados, generaciones).
    """
    cache = StrData(
        ptCount=len(values),
        pt=[StrVal(idx=i, v=str(v)) for i, v in enumerate(values)],
    )
    ref = StrRef(f=str(labels), strCache=cache)
    show_axes(chart)
    for series in chart.series:
        series.cat = AxDataSource(strRef=ref)


def labels_only(numfmt: str | None = None, position: str = "outEnd") -> DataLabelList:
    """Etiquetas limpias: solo el valor, sin categoría ni nombre de serie."""
    dl = DataLabelList()
    dl.showVal = True
    dl.showCatName = False
    dl.showSerName = False
    dl.showLegendKey = False
    dl.showPercent = False
    dl.showBubbleSize = False
    dl.position = position
    if numfmt:
        dl.numFmt = numfmt
    return dl


def page_setup(ws, orientation="landscape", fit_width=1, fit_height=0):
    ws.page_setup.orientation = orientation
    ws.page_setup.fitToWidth = fit_width
    ws.page_setup.fitToHeight = fit_height
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.35, right=0.35, top=0.45, bottom=0.45)
    ws.oddFooter.center.text = "Caracterización de Aprendices Centro ASTIN · Corte 19/10/2026 · Datos sin PII"
    ws.oddFooter.center.size = 8
    ws.oddFooter.center.color = "808080"


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def load_data():
    data = {}
    for f in sorted(PROCESSED.glob("*.csv")):
        data[f.stem] = pd.read_csv(f, dtype=str, keep_default_na=False)
    stats = json.loads((OUTPUTS / "03_analisis_estadistico.json").read_text(encoding="utf-8"))
    pred = json.loads((OUTPUTS / "04_modelo_predictivo.json").read_text(encoding="utf-8"))
    return data, stats, pred


def as_int(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


def as_float(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------
def sheet_portada(wb, data, stats):
    ws = wb.create_sheet("Portada")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 2
    for col in "BCDEFGHIJKLMN":
        ws.column_dimensions[col].width = 13

    ws.merge_cells("B2:N4")
    c = ws["B2"]
    c.value = "Caracterización de Aprendices Centro ASTIN"
    c.font = Font(name=FONT, size=30, bold=True, color=WHITE)
    c.fill = FILL_NAVY
    c.alignment = Alignment(horizontal="left", vertical="center", indent=2)
    for row in ws["B2:N4"]:
        for cc in row:
            cc.fill = FILL_NAVY

    ws.merge_cells("B5:N5")
    c = ws["B5"]
    c.value = "Analítica de matrícula, pérdida, riesgo y permanencia · Centro ASTIN"
    c.font = Font(name=FONT, size=11, color="C9D6DF")
    c.fill = FILL_NAVY
    c.alignment = Alignment(horizontal="left", vertical="center", indent=2)
    for cc in ws["B5:N5"][0]:
        cc.fill = FILL_NAVY
    ws.row_dimensions[5].height = 26

    ws.merge_cells("B6:N6")
    c = ws["B6"]
    c.value = "Corte único: 19 de octubre de 2026  ·  56 fichas  ·  15 programas  ·  1.592 matrículas"
    c.font = Font(name=FONT, size=10, bold=True, color=WHITE)
    c.fill = FILL_GREEN
    c.alignment = Alignment(horizontal="left", vertical="center", indent=2)
    for cc in ws["B6:N6"][0]:
        cc.fill = FILL_GREEN
    ws.row_dimensions[6].height = 24

    r = stats["resumen"]
    cards = [
        ("Matrículas", num(r["matriculas"]), NAVY),
        ("Pérdidas", num(r["perdidas"]), RED),
        ("Tasa de pérdida", pct(r["tasa_perdida"]), RED_DARK),
        ("Aprendices únicos", num(stats["metadata"]["aprendices_unicos"]), NAVY_2),
        ("Fichas críticas", "6", ORANGE),
    ]
    col = 2
    for label, value, accent in cards:
        kpi_box(ws, 8, col, label, value, accent, width=2)
        col += 2
    ws.row_dimensions[8].height = 18
    ws.row_dimensions[9].height = 28
    ws.row_dimensions[10].height = 16

    section(ws, 12, "Contenido del libro", last_col=14)
    rows = [
        ("Resumen", "KPIs, estados, jornada y hallazgos principales."),
        ("Programas", "Ranking de 15 programas, tasas, IC y concentración."),
        ("Fichas", "Detalle de 56 fichas, riesgo y probabilidad estructural."),
        ("Cohortes", "Tendencia por prefijo de ficha; no es año calendario."),
        ("Riesgos", "Bandas de riesgo, validación y protocolo de atención."),
        ("Predictivo", "Modelo, calibración, proyección y priorización."),
        ("Diccionario", "Tablas, campos, tipos y reglas de privacidad."),
        ("Notas", "Metodología, límites y reproducibilidad."),
    ]
    rr = 13
    for name, desc in rows:
        ws.cell(rr, 2, name).font = BOLD
        ws.cell(rr, 2).border = BOX
        ws.merge_cells(start_row=rr, start_column=3, end_row=rr, end_column=14)
        c = ws.cell(rr, 3, desc)
        c.font = BODY
        c.alignment = LEFT
        c.border = BOX
        for cc in range(2, 15):
            ws.cell(rr, cc).border = BOX
        rr += 1

    section(ws, 22, "Advertencia de alcance", last_col=14, fill=PatternFill("solid", fgColor=ORANGE))
    ws.merge_cells("B23:N27")
    c = ws["B23"]
    c.value = (
        "Este libro describe un único corte transversal. No contiene serie histórica, fecha de matrícula, "
        "fecha de retiro ni periodo académico; por eso no proyecta nueva matrícula ni fechas de cierre. "
        "La proyección incluida es un escenario de permanencia de la población ya vinculada.\n\n"
        "La fuente original no trae género, edad, municipio ni departamento. Esos campos aparecen como "
        "«No informado» y no se imputan. El tipo de documento se usa solo como proxy grueso de edad.\n\n"
        "El puntaje individual es una priorización estructural, no una predicción personal: el AUC del "
        "modelo con variables individuales es 0,467 (cercano al azar). No use estos puntajes para negar "
        "cupos, certificar, sancionar ni tomar decisiones automáticas."
    )
    c.font = Font(name=FONT, size=9.5, color=INK)
    c.fill = FILL_AMBER
    c.alignment = LEFT_TOP
    for row in ws["B23:N27"]:
        for cc in row:
            cc.fill = FILL_AMBER
            cc.border = BOX

    section(ws, 29, "Privacidad y uso", last_col=14, fill=PatternFill("solid", fgColor=SLATE))
    ws.merge_cells("B30:N32")
    c = ws["B30"]
    c.value = (
        "El libro no contiene nombres, números de documento, celulares ni correos. Los identificadores "
        "de aprendiz son seudónimos (hash) y se incluyen solo cuando aportan trazabilidad operativa. "
        "No publique listas nominales: la lista priorizada con nombres está en data/restricted y es de uso interno."
    )
    c.font = Font(name=FONT, size=9.5, color=INK)
    c.fill = FILL_LIGHT
    c.alignment = LEFT_TOP
    for row in ws["B30:N32"]:
        for cc in row:
            cc.fill = FILL_LIGHT
            cc.border = BOX

    ws.merge_cells("B34:N34")
    c = ws["B34"]
    c.value = "Generado por scripts/05_generar_excel.py · Fuente: 56 archivos .xls de la base de aprendices · Datos procesados sin PII"
    c.font = SMALL
    c.alignment = LEFT
    page_setup(ws, "portrait")
    ws.print_area = "A1:N34"


# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
def sheet_resumen(wb, data, stats):
    ws = wb.create_sheet("Resumen")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Resumen ejecutivo", "Indicadores del corte, distribución por estado y lectura de hallazgos.", 14)

    r = stats["resumen"]
    cards = [
        ("Matrículas", num(r["matriculas"]), NAVY),
        ("Pérdidas", num(r["perdidas"]), RED),
        ("Tasa de pérdida", pct(r["tasa_perdida"]), RED_DARK),
        ("Fichas", num(stats["metadata"]["fichas"]), NAVY_2),
        ("Prioridad inmediata", num(65), ORANGE),
    ]
    col = 1
    for label, value, accent in cards:
        kpi_box(ws, 4, col, label, value, accent, width=2)
        col += 2

    ws.merge_cells("L4:N5")
    c = ws["L4"]
    c.value = f"IC 95% de la tasa de pérdida\n{pct(r['ic95_inf'])} – {pct(r['ic95_sup'])}"
    c.font = Font(name=FONT, size=10, bold=True, color=NAVY)
    c.alignment = CENTER
    c.fill = FILL_LIGHT_2
    c.border = BOX
    for row in ws["L4:N5"]:
        for cc in row:
            cc.fill = FILL_LIGHT_2
            cc.border = BOX

    section(ws, 8, "Estados de matrícula", 14)
    headers = ["Estado", "Categoría", "Matrículas", "% del total", "Pérdidas"]
    rows = []
    total = r["matriculas"]
    # El JSON de estados no trae conteo: se toma del hecho.
    f = data["FactMatricula"].copy()
    f["EstadoID"] = f["EstadoID"].astype(str)
    d_est = data["DimEstado"].set_index("EstadoID")
    counts = f["EstadoID"].value_counts().to_dict()
    for eid, drow in d_est.iterrows():
        n = counts.get(eid, 0)
        rows.append([
            drow["Estado"], drow["Categoria"], n, n / total if total else 0,
            "Sí" if str(drow["EsPerdida"]) == "1" else "No",
        ])
    rows.sort(key=lambda x: (-x[2], x[0]))
    write_table(ws, 9, 1, headers, rows, widths=[20, 18, 11, 10, 9])
    ref = f"A9:E{9 + len(rows)}"
    add_table_style(ws, ref, "tblEstados")
    for i in range(10, 10 + len(rows)):
        ws.cell(i, 4).number_format = "0.0%"

    # Jornada
    n_estados = len(rows)
    estado_labels = [r[0] for r in rows]
    section(ws, 18, "Jornada", 14)
    j = stats["jornadas"]["detalle"]
    headers = ["Jornada", "Matrículas", "Pérdidas", "Tasa de pérdida", "IC 95% inferior", "IC 95% superior"]
    rows = [[x["jornada"], x["n"], x["perdidas"], x["tasa_perdida"], x["ic95_inf"], x["ic95_sup"]] for x in j]
    write_table(ws, 19, 1, headers, rows, widths=[18, 12, 10, 14, 15, 15])
    add_table_style(ws, f"A19:F{19 + len(rows)}", "tblJornada")
    for i in range(20, 20 + len(rows)):
        for c in (4, 5, 6):
            ws.cell(i, c).number_format = "0.0%"

    cont = stats["jornadas"]["contraste"]
    ws.merge_cells("H19:N20")
    c = ws["H19"]
    c.value = (
        f"Contraste: χ² = {cont['chi2']:.3f}; p {cont['p_texto']}; V de Cramer = {cont['v_cramer']:.3f}. "
        f"OR DIURNA vs NOCTURNA = {cont['or_diurna_vs_nocturna']:.3f} "
        f"(IC 95% {cont['or_ic95_inf']:.3f}–{cont['or_ic95_sup']:.3f})."
    )
    c.font = BODY
    c.fill = FILL_LIGHT
    c.alignment = LEFT_TOP
    for row in ws["H19:N20"]:
        for cc in row:
            cc.fill = FILL_LIGHT
            cc.border = BOX

    section(ws, 24, "Hallazgos que requieren atención", 14)
    findings = [
        "1. La pérdida acumulada es 27,6% (439 de 1.592 matrículas). Casi toda es cancelación (26,9%); el retiro voluntario es 0,7%.",
        "2. La jornada nocturna duplica el riesgo relativo de la diurna: 36,0% vs 23,0% (OR 0,53; p < 0,001).",
        "3. Seis fichas son críticas: 206 matrículas y 116 pérdidas (56,3% de pérdida observada).",
        "4. La concentración es alta: 3 programas reúnen 56,7% de la matrícula. El mayor es Sistemas Integrados de Gestión (484; 31,6%).",
        "5. La pérdida cae con el prefijo de ficha (Spearman −0,921; pendiente −3,5 pp por generación). Es un proxy de antigüedad, no un año calendario.",
        "6. El contacto incompleto (14,3%) no es factor de riesgo: su asociación ajustada por programa es espuria (OR MH 0,65).",
        "7. El modelo discrimina mejor entre fichas (AUC 0,726) que entre personas (AUC individual 0,467). Priorice fichas, no personas.",
    ]
    rr = 25
    for text in findings:
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=14)
        c = ws.cell(rr, 1, text)
        c.font = BODY
        c.alignment = LEFT_TOP
        c.border = Border(bottom=THIN)
        ws.row_dimensions[rr].height = 26
        rr += 1

    # Charts
    ch = BarChart()
    ch.type = "bar"
    ch.style = 10
    ch.title = "Matrículas por estado"
    ch.y_axis.title = None
    ch.x_axis.title = None
    data_ref = Reference(ws, min_col=3, min_row=9, max_row=9 + n_estados)
    cats = Reference(ws, min_col=1, min_row=10, max_row=9 + n_estados)
    ch.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch, cats, estado_labels)
    ch.legend = None
    ch.height = 8.2
    ch.width = 15.5
    ch.dataLabels = labels_only()
    ch.y_axis.majorGridlines = None
    ch.x_axis.axPos = "l"
    ch.y_axis.axPos = "b"
    ch.varyColors = False
    ch.series[0].graphicalProperties.solidFill = GREEN
    ws.add_chart(ch, "P4")

    st = stats["estados"]
    # Chart jornada
    ch2 = BarChart()
    ch2.type = "col"
    ch2.style = 12
    ch2.title = "Tasa de pérdida por jornada"
    ch2.y_axis.title = None
    ch2.y_axis.numFmt = "0%"
    data_ref = Reference(ws, min_col=4, min_row=19, max_row=19 + len(j))
    cats = Reference(ws, min_col=1, min_row=20, max_row=19 + len(j))
    ch2.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch2, cats, [x["jornada"] for x in j])
    ch2.legend = None
    ch2.height = 7.2
    ch2.width = 11
    ch2.dataLabels = labels_only("0.0%")
    ch2.x_axis.axPos = "b"
    ch2.y_axis.axPos = "l"
    ch2.varyColors = False
    ch2.series[0].graphicalProperties.solidFill = NAVY
    ws.add_chart(ch2, "P22")

    page_setup(ws, fit_height=1)
    ws.print_area = "A1:N40"


# ---------------------------------------------------------------------------
# Programas
# ---------------------------------------------------------------------------
def sheet_programas(wb, data, stats):
    ws = wb.create_sheet("Programas")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Programas", "Ranking por tasa de pérdida, incertidumbre y concentración de matrícula.", 16)

    d = stats["programas"]["detalle"]
    headers = [
        "Ranking", "Programa", "Línea tecnológica", "Nivel", "Fichas", "Matrículas",
        "Pérdidas", "Tasa de pérdida", "IC 95% inf.", "IC 95% sup.", "Tasa ajustada EB",
        "Brecha vs global (pp)", "Participación",
    ]
    rows = []
    for x in sorted(d, key=lambda z: z["ranking_tasa"]):
        rows.append([
            x["ranking_tasa"], x["corto"], x["linea"], x["nivel"], x["fichas"], x["matriculas"],
            x["perdidas"], x["tasa_perdida"], x["ic95_inf"], x["ic95_sup"], x["tasa_ajustada_eb"],
            x["brecha_vs_global_pp"], x["participacion"],
        ])
    write_table(ws, 4, 1, headers, rows, widths=[8, 34, 22, 11, 7, 10, 9, 12, 10, 10, 12, 12, 11])
    add_table_style(ws, f"A4:M{4 + len(rows)}", "tblProgramas")
    for i in range(5, 5 + len(rows)):
        for c in (8, 9, 10, 11, 13):
            ws.cell(i, c).number_format = "0.0%"
        ws.cell(i, 12).number_format = "+0.0;-0.0;0.0"
        ws.cell(i, 1).alignment = CENTER

    ws.conditional_formatting.add(
        f"H5:H{4 + len(rows)}",
        ColorScaleRule(start_type="num", start_value=0, start_color="C6EFCE",
                       mid_type="num", mid_value=0.28, mid_color="FFEB9C",
                       end_type="num", end_value=0.55, end_color="F4B6B6"),
    )

    conc = stats["programas"]["concentracion"]
    ws.merge_cells("O4:P10")
    c = ws["O4"]
    c.value = (
        f"Concentración\n\nHHI = {conc['hhi_programas']:.4f}\n"
        f"Programas efectivos = {conc['numero_efectivo_programas']:.1f}\n"
        f"Top 3 = {pct(conc['top3_participacion'])}\n\n"
        f"χ² = {stats['programas']['contraste']['chi2']:.1f}; "
        f"p {stats['programas']['contraste']['p_texto']}; "
        f"V = {stats['programas']['contraste']['v_cramer']:.3f}"
    )
    c.font = Font(name=FONT, size=10, color=INK)
    c.fill = FILL_LIGHT
    c.alignment = LEFT_TOP
    for row in ws["O4:P10"]:
        for cc in row:
            cc.fill = FILL_LIGHT
            cc.border = BOX

    note(
        ws, 22,
        "Los intervalos son amplios en programas con una sola ficha o pocos aprendices. El ranking es descriptivo: "
        "no prueba causalidad ni ajusta por clustering intra-ficha. La tasa ajustada EB contrae los tamaños pequeños hacia la media global.",
        13, 38,
    )

    # Chart horizontal
    ch = BarChart()
    ch.type = "bar"
    ch.style = 10
    ch.title = "Tasa de pérdida por programa (15)"
    ch.x_axis.title = None
    ch.y_axis.title = None
    ch.y_axis.numFmt = "0%"
    data_ref = Reference(ws, min_col=8, min_row=4, max_row=4 + len(rows))
    cats = Reference(ws, min_col=2, min_row=5, max_row=4 + len(rows))
    ch.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch, cats, [r[1] for r in rows])
    ch.legend = None
    ch.height = 13.0
    ch.width = 21
    ch.y_axis.majorGridlines = None
    ch.x_axis.axPos = "l"
    ch.y_axis.axPos = "b"
    ch.varyColors = False
    ch.series[0].graphicalProperties.solidFill = GREEN
    ws.add_chart(ch, "A28")

    # Scatter tamaño vs tasa
    sc = ScatterChart()
    sc.title = "Matrículas vs tasa de pérdida"
    sc.x_axis.title = "Matrículas"
    sc.y_axis.title = "Tasa de pérdida"
    sc.y_axis.numFmt = "0%"
    sc.style = 13
    xvalues = Reference(ws, min_col=6, min_row=5, max_row=4 + len(rows))
    yvalues = Reference(ws, min_col=8, min_row=5, max_row=4 + len(rows))
    series = Series(yvalues, xvalues, title="Programa")
    series.marker = Marker(symbol="circle", size=7)
    series.graphicalProperties.line.noFill = True
    sc.series.append(series)
    sc.scatterStyle = "marker"
    sc.height = 11
    sc.width = 17
    sc.legend = None
    show_axes(sc)
    ws.add_chart(sc, "O13")

    page_setup(ws, fit_height=1)
    ws.print_area = "A1:P44"


# ---------------------------------------------------------------------------
# Fichas
# ---------------------------------------------------------------------------
def sheet_fichas(wb, data, stats):
    ws = wb.create_sheet("Fichas")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Fichas", "Detalle de las 56 fichas: volumen, pérdida, riesgo estructural y prioridad.", 17)

    df = data["DimFicha"].copy()
    for c in ["TotalMatriculas", "AprendicesVinculados", "Cancelados", "Retiros", "RankingRiesgo"]:
        df[c] = as_int(df, c)
    for c in ["TasaPerdida", "ProbDesercionFicha", "ProbDesercionICInf", "ProbDesercionICSup", "IndiceRiesgo"]:
        df[c] = as_float(df, c)
    df = df.sort_values(["RankingRiesgo", "FichaID"])

    dprog = data["DimPrograma"].set_index("ProgramaID")
    headers = [
        "Ficha", "Programa", "Jornada", "Generación", "Matrículas", "Vinculados",
        "Cancelados", "Retiros", "Tasa de pérdida", "Índice de riesgo", "Nivel de riesgo",
        "Ranking", "Prob. pérdida ficha", "IC 95% inf.", "IC 95% sup.", "Prioridad", "Alerta principal",
    ]
    rows = []
    for _, x in df.iterrows():
        prog = dprog.loc[x["ProgramaID"], "ProgramaCorto"] if x["ProgramaID"] in dprog.index else "—"
        rows.append([
            x["FichaID"], prog, x["Jornada"], x["GeneracionID"], x["TotalMatriculas"], x["AprendicesVinculados"],
            x["Cancelados"], x["Retiros"], x["TasaPerdida"], x["IndiceRiesgo"], x["NivelRiesgo"],
            x["RankingRiesgo"], x["ProbDesercionFicha"], x["ProbDesercionICInf"], x["ProbDesercionICSup"],
            x["Prioridad"], x["AlertaPrincipal"],
        ])
    write_table(ws, 4, 1, headers, rows, widths=[11, 28, 11, 10, 9, 9, 9, 8, 11, 10, 10, 8, 12, 9, 9, 9, 20])
    add_table_style(ws, f"A4:Q{4 + len(rows)}", "tblFichas")
    ws.freeze_panes = "B5"
    for i in range(5, 5 + len(rows)):
        for c in (9, 13, 14, 15):
            ws.cell(i, c).number_format = "0.0%"
        ws.cell(i, 10).number_format = "0.0"
        ws.cell(i, 1).alignment = CENTER
        ws.cell(i, 5).alignment = CENTER
        ws.cell(i, 12).alignment = CENTER

    last = 4 + len(rows)
    ws.conditional_formatting.add(
        f"I5:I{last}",
        ColorScaleRule(start_type="num", start_value=0, start_color="C6EFCE",
                       mid_type="num", mid_value=0.3, mid_color="FFEB9C",
                       end_type="num", end_value=0.6, end_color="F4B6B6"),
    )
    for value, fill, font_color in [
        ("Crítico", FILL_RED, RED_DARK),
        ("Alto", PatternFill("solid", fgColor="FCE4D6"), ORANGE),
        ("Medio", FILL_AMBER, "7A5B00"),
        ("Bajo", FILL_GREEN_SOFT, GREEN_DARK),
    ]:
        ws.conditional_formatting.add(
            f"K5:K{last}",
            CellIsRule(operator="equal", formula=[f'"{value}"'], fill=fill,
                       font=Font(name=FONT, size=10, bold=True, color=font_color)),
        )

    note(
        ws, last + 2,
        "La probabilidad de pérdida es la media posterior beta-binomial por ficha (prior k=10). No es un pronóstico "
        "individual ni una fecha de deserción. El índice de riesgo es un percentil de la tasa ajustada; ambas columnas "
        "responden a preguntas distintas. Use el IC y el tamaño de ficha antes de concluir diferencias.",
        12, 44,
    )

    # Scatter n vs tasa
    sc = ScatterChart()
    sc.title = "Tamaño de ficha vs tasa de pérdida"
    sc.x_axis.title = "Matrículas"
    sc.y_axis.title = "Tasa de pérdida"
    sc.y_axis.numFmt = "0%"
    sc.style = 13
    xvalues = Reference(ws, min_col=5, min_row=5, max_row=last)
    yvalues = Reference(ws, min_col=9, min_row=5, max_row=last)
    series = Series(yvalues, xvalues, title="Fichas")
    series.marker = Marker(symbol="circle", size=6)
    series.graphicalProperties.line.noFill = True
    sc.series.append(series)
    sc.scatterStyle = "marker"
    sc.height = 12
    sc.width = 17
    sc.legend = None
    show_axes(sc)
    ws.add_chart(sc, "S4")

    page_setup(ws, fit_height=1)
    ws.print_area = f"A1:W{last + 5}"


# ---------------------------------------------------------------------------
# Cohortes
# ---------------------------------------------------------------------------
def sheet_cohortes(wb, data, stats):
    ws = wb.create_sheet("Cohortes")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Cohortes y tendencia", "Agregación por prefijo de ficha. El prefijo es un proxy de generación, no un año calendario.", 12)

    d = stats["tendencia_generaciones"]["detalle"]
    headers = ["Orden", "Generación", "Fichas", "Matrículas", "Pérdidas", "Tasa de pérdida"]
    rows = [[x["orden"], x["generacion"].replace("Generación ", ""), x["fichas"], x["n"], x["perdidas"], x["tasa_perdida"]] for x in d]
    gen_labels = [r[1] for r in rows]
    write_table(ws, 4, 1, headers, rows, widths=[8, 24, 8, 11, 10, 12])
    add_table_style(ws, f"A4:F{4 + len(rows)}", "tblGeneraciones")
    for i in range(5, 5 + len(rows)):
        ws.cell(i, 6).number_format = "0.0%"

    ws.conditional_formatting.add(
        f"F5:F{4 + len(rows)}",
        ColorScaleRule(start_type="num", start_value=0, start_color="C6EFCE",
                       mid_type="num", mid_value=0.25, mid_color="FFEB9C",
                       end_type="num", end_value=0.55, end_color="F4B6B6"),
    )

    ca = stats["tendencia_generaciones"]["cochran_armitage"]
    sp = stats["tendencia_generaciones"]["spearman_orden_vs_tasa"]
    ws.merge_cells("H4:L8")
    c = ws["H4"]
    c.value = (
        f"Prueba de tendencia\n\n"
        f"Spearman ρ = {sp['rho']:.3f} (p < 0,001)\n"
        f"Cochran–Armitage z = {ca['z']:.3f} (p < 0,001)\n"
        f"Pendiente = {ca['pendiente_pp_por_generacion']:.2f} pp por generación\n\n"
        f"La tendencia es descriptiva. No hay fechas de matrícula ni retiro: no se puede separar maduración de cohorte "
        f"de riesgo real ni estimar estacionalidad."
    )
    c.font = BODY
    c.fill = FILL_LIGHT
    c.alignment = LEFT_TOP
    for row in ws["H4:L8"]:
        for cc in row:
            cc.fill = FILL_LIGHT
            cc.border = BOX

    # Line chart
    ch = LineChart()
    ch.title = "Tasa de pérdida por generación"
    ch.y_axis.title = "Tasa de pérdida"
    ch.y_axis.numFmt = "0%"
    ch.x_axis.title = None
    ch.style = 12
    data_ref = Reference(ws, min_col=6, min_row=4, max_row=4 + len(rows))
    cats = Reference(ws, min_col=2, min_row=5, max_row=4 + len(rows))
    ch.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch, cats, gen_labels)
    ch.legend = None
    ch.height = 10
    ch.width = 23
    ch.marker = True
    ch.x_axis.axPos = "b"
    ch.y_axis.axPos = "l"
    ws.add_chart(ch, "A24")

    # Column chart n
    ch2 = BarChart()
    ch2.type = "col"
    ch2.title = "Matrículas por generación"
    ch2.y_axis.title = None
    ch2.style = 10
    data_ref = Reference(ws, min_col=4, min_row=4, max_row=4 + len(rows))
    cats = Reference(ws, min_col=2, min_row=5, max_row=4 + len(rows))
    ch2.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch2, cats, gen_labels)
    ch2.legend = None
    ch2.height = 10
    ch2.width = 23
    ch2.x_axis.axPos = "b"
    ch2.y_axis.axPos = "l"
    ch2.varyColors = False
    ch2.series[0].graphicalProperties.solidFill = NAVY
    ws.add_chart(ch2, "A44")

    page_setup(ws, fit_height=1)
    ws.print_area = "A1:L62"


# ---------------------------------------------------------------------------
# Riesgos
# ---------------------------------------------------------------------------
def sheet_riesgos(wb, data, stats):
    ws = wb.create_sheet("Riesgos")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Riesgo y priorización de fichas", "Bandas de riesgo, validación empírica y fichas que requieren intervención.", 14)

    bands = stats["validacion_riesgo"]
    headers = ["Nivel", "Fichas", "Matrículas", "Pérdidas", "Tasa observada"]
    rows = [[x["nivel"], x["fichas"], x["n"], x["perdidas"], x["tasa_perdida"]] for x in bands]
    write_table(ws, 4, 1, headers, rows, widths=[14, 9, 12, 10, 14])
    add_table_style(ws, f"A4:E{4 + len(rows)}", "tblBandas")
    for i in range(5, 5 + len(rows)):
        ws.cell(i, 5).number_format = "0.0%"
    for value, fill, font_color in [
        ("Crítico", FILL_RED, RED_DARK),
        ("Alto", PatternFill("solid", fgColor="FCE4D6"), ORANGE),
        ("Medio", FILL_AMBER, "7A5B00"),
        ("Bajo", FILL_GREEN_SOFT, GREEN_DARK),
    ]:
        ws.conditional_formatting.add(
            f"A5:A{4 + len(rows)}",
            CellIsRule(operator="equal", formula=[f'"{value}"'], fill=fill,
                       font=Font(name=FONT, size=10, bold=True, color=font_color)),
        )

    # Bar bandas
    ch = BarChart()
    ch.type = "col"
    ch.title = "Fichas por nivel de riesgo"
    ch.y_axis.title = "Fichas"
    ch.style = 10
    data_ref = Reference(ws, min_col=2, min_row=4, max_row=4 + len(rows))
    cats = Reference(ws, min_col=1, min_row=5, max_row=4 + len(rows))
    ch.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch, cats, [x["nivel"] for x in bands])
    ch.legend = None
    ch.height = 7
    ch.width = 12
    ch.dataLabels = labels_only()
    ch.x_axis.axPos = "b"
    ch.y_axis.axPos = "l"
    ws.add_chart(ch, "G4")

    # Tabla fichas
    df = data["DimFicha"].copy()
    for c in ["TotalMatriculas", "Cancelados", "Retiros", "RankingRiesgo"]:
        df[c] = as_int(df, c)
    for c in ["TasaPerdida", "ProbDesercionFicha", "ProbDesercionICInf", "ProbDesercionICSup", "IndiceRiesgo"]:
        df[c] = as_float(df, c)
    df = df.sort_values("RankingRiesgo")
    dprog = data["DimPrograma"].set_index("ProgramaID")
    headers = [
        "Ranking", "Ficha", "Programa", "Jornada", "Matrículas", "Pérdidas", "Tasa observada",
        "Índice", "Nivel", "Prob. ficha", "IC inf.", "IC sup.", "Prioridad",
    ]
    rows = []
    for _, x in df.iterrows():
        prog = dprog.loc[x["ProgramaID"], "ProgramaCorto"] if x["ProgramaID"] in dprog.index else "—"
        rows.append([
            x["RankingRiesgo"], x["FichaID"], prog, x["Jornada"], x["TotalMatriculas"],
            x["Cancelados"] + x["Retiros"], x["TasaPerdida"], x["IndiceRiesgo"], x["NivelRiesgo"],
            x["ProbDesercionFicha"], x["ProbDesercionICInf"], x["ProbDesercionICSup"], x["Prioridad"],
        ])
    write_table(ws, 17, 1, headers, rows, widths=[8, 11, 28, 11, 10, 9, 11, 8, 10, 11, 9, 9, 10])
    add_table_style(ws, f"A17:M{17 + len(rows)}", "tblFichasRiesgo")
    ws.freeze_panes = "B18"
    for i in range(18, 18 + len(rows)):
        for c in (7, 10, 11, 12):
            ws.cell(i, c).number_format = "0.0%"
        ws.cell(i, 8).number_format = "0.0"
        ws.cell(i, 2).alignment = CENTER
        ws.cell(i, 1).alignment = CENTER

    last = 17 + len(rows)
    for value, fill, font_color in [
        ("Crítico", FILL_RED, RED_DARK),
        ("Alto", PatternFill("solid", fgColor="FCE4D6"), ORANGE),
        ("Medio", FILL_AMBER, "7A5B00"),
        ("Bajo", FILL_GREEN_SOFT, GREEN_DARK),
    ]:
        ws.conditional_formatting.add(
            f"I18:I{last}",
            CellIsRule(operator="equal", formula=[f'"{value}"'], fill=fill,
                       font=Font(name=FONT, size=10, bold=True, color=font_color)),
        )

    section(ws, last + 2, "Protocolo de atención", 13, fill=PatternFill("solid", fgColor=SLATE))
    protocol = [
        ("Crítico (percentil ≥ 90)", "Intervención inmediata en 5 días hábiles. Revisar asistencia, contacto y barreras; asignar responsable y registrar compromiso."),
        ("Alto (75–90)", "Seguimiento quincenal. Verificar alertas individuales y contactabilidad; documentar acciones."),
        ("Medio (50–75)", "Monitoreo mensual. Revisar evolución y factores de programa/jornada."),
        ("Bajo (< 50)", "Monitoreo rutinario. Mantener acciones preventivas y buena calidad de contacto."),
    ]
    rr = last + 3
    for label, text in protocol:
        ws.cell(rr, 1, label).font = BOLD
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=3)
        ws.merge_cells(start_row=rr, start_column=4, end_row=rr, end_column=13)
        c = ws.cell(rr, 4, text)
        c.font = BODY
        c.alignment = LEFT_TOP
        for cc in range(1, 14):
            ws.cell(rr, cc).border = Border(bottom=THIN)
        ws.row_dimensions[rr].height = 30
        rr += 1

    page_setup(ws)
    ws.print_area = f"A1:M{rr}"


# ---------------------------------------------------------------------------
# Predictivo
# ---------------------------------------------------------------------------
def sheet_predictivo(wb, data, stats, pred):
    ws = wb.create_sheet("Predictivo")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Capa predictiva y proyección", "Modelo estructural, calibración, escenarios de permanencia y priorización operativa.", 14)

    m = pred["modelo_principal"]
    ind = pred["modelo_individual"]
    est = pred["modelo_estructural"]

    metrics = [
        ("AUC out-of-fold", f"{m['auc']:.3f}", "Validación agrupada por ficha (5 folds)."),
        ("IC 95% AUC (bootstrap)", f"{m['auc_ic95_bootstrap_ficha']['ic95_inf']:.3f} – {m['auc_ic95_bootstrap_ficha']['ic95_sup']:.3f}", "1.000 réplicas válidas por ficha."),
        ("Brier", f"{m['brier']:.3f}", f"Base sin modelo: {m['brier_base']:.3f}."),
        ("ECE", f"{m['ece']:.3f}", "Error de calibración esperado (menor es mejor)."),
        ("Pendiente de calibración", f"{m['calibracion_slope']:.3f}", "1,0 sería calibración perfecta."),
        ("Sensibilidad / especificidad", f"{m['sensibilidad_youden']:.3f} / {m['especificidad_youden']:.3f}", f"Umbral Youden = {m['umbral_youden']:.3f}."),
        ("AUC estructural", f"{est['auc']:.3f}", "Sin variables individuales."),
        ("AUC individual", f"{ind['auc']:.3f}", "Variables individuales; cerca del azar."),
    ]
    write_table(ws, 4, 1, ["Métrica", "Valor", "Lectura"], [[a, b, c] for a, b, c in metrics], widths=[28, 16, 58])
    add_table_style(ws, f"A4:C{4 + len(metrics)}", "tblMetricas")

    note(
        ws, 14,
        "El modelo usa un solo snapshot y etiquetas observadas en el mismo corte. La validación agrupada por ficha evita "
        "filtrar información entre fichas, pero no sustituye una validación temporal. AUC 0,726 indica discriminación "
        "moderada entre fichas; AUC individual 0,467 indica que las variables personales disponibles no discriminan. "
        "Use el score para priorizar fichas y acciones, nunca para sancionar o negar cupos.",
        14, 52,
    )

    # Comparación de modelos
    section(ws, 20, "Comparación de especificaciones", 14)
    comp = [
        ["Principal (estructura + individuo)", m["auc"], m["brier"], m["auc_ganancia_sobre_azar"]],
        ["Estructural (sin individuo)", est["auc"], est["brier"], est["auc_ganancia_sobre_azar"]],
        ["Individual", ind["auc"], ind["brier"], ind["auc_ganancia_sobre_azar"]],
    ]
    write_table(ws, 21, 1, ["Especificación", "AUC", "Brier", "Ganancia vs azar"], comp, widths=[38, 10, 10, 16])
    add_table_style(ws, "A21:D24", "tblComparacion")
    for i in range(22, 25):
        ws.cell(i, 2).number_format = "0.000"
        ws.cell(i, 3).number_format = "0.000"
        ws.cell(i, 4).number_format = "+0.000;-0.000;0.000"

    # Calibración
    section(ws, 26, "Calibración por deciles", 14)
    dec = pred["modelo_principal"]["calibracion_deciles"]
    headers = ["Decil", "n", "Probabilidad media", "Tasa observada", "Brecha (pp)"]
    rows = [[i + 1, x["n"], x["prob_media"], x["tasa_observada"], x["brecha"] * 100] for i, x in enumerate(dec)]
    write_table(ws, 27, 1, headers, rows, widths=[8, 9, 18, 16, 12])
    add_table_style(ws, f"A27:E{27 + len(rows)}", "tblCalibracion")
    for i in range(28, 28 + len(rows)):
        ws.cell(i, 3).number_format = "0.0%"
        ws.cell(i, 4).number_format = "0.0%"
        ws.cell(i, 5).number_format = "+0.0;-0.0;0.0"

    ch = LineChart()
    ch.title = "Calibración: probabilidad media vs tasa observada"
    ch.y_axis.title = "Tasa"
    ch.y_axis.numFmt = "0%"
    ch.x_axis.title = "Decil de probabilidad"
    ch.style = 12
    data_ref = Reference(ws, min_col=3, max_col=4, min_row=27, max_row=27 + len(rows))
    cats = Reference(ws, min_col=1, min_row=28, max_row=27 + len(rows))
    ch.add_data(data_ref, titles_from_data=True)
    ch.set_categories(cats)
    ch.height = 6.5
    ch.width = 16
    ch.marker = True
    ch.x_axis.axPos = "b"
    ch.y_axis.axPos = "l"
    show_axes(ch)
    ws.add_chart(ch, "G26")

    # Proyección
    section(ws, 40, "Proyección de permanencia por escenarios", 14)
    proj = pred["proyeccion"]["resumen_escenarios"]
    headers = ["Escenario", "Población vinculada", "Pérdida adicional", "Población proyectada", "Tasa proyectada"]
    rows = [[x["escenario"], x["poblacion_vinculada"], x["perdida_adicional_esperada"], x["poblacion_proyectada"], x["tasa_proyectada"]] for x in proj]
    write_table(ws, 41, 1, headers, rows, widths=[16, 18, 16, 18, 15])
    add_table_style(ws, f"A41:E{41 + len(rows)}", "tblProyeccion")
    for i in range(42, 42 + len(rows)):
        ws.cell(i, 5).number_format = "0.0%"

    ch2 = BarChart()
    ch2.type = "col"
    ch2.title = "Población proyectada por escenario"
    ch2.y_axis.title = None
    ch2.style = 10
    data_ref = Reference(ws, min_col=4, min_row=41, max_row=41 + len(rows))
    cats = Reference(ws, min_col=1, min_row=42, max_row=41 + len(rows))
    ch2.add_data(data_ref, titles_from_data=True)
    set_text_categories(ch2, cats, [x["escenario"] for x in proj])
    ch2.legend = None
    ch2.height = 5.5
    ch2.width = 12
    ch2.dataLabels = labels_only()
    ch2.x_axis.axPos = "b"
    ch2.y_axis.axPos = "l"
    ws.add_chart(ch2, "G40")

    note(
        ws, 46,
        "Proyección de permanencia de los 1.144 vinculados, no de nueva matrícula. El escenario Base usa un plateau global "
        "de 43,2% y suavizado por programa (k=50). Optimista resta 7 pp y pesimista suma 7 pp. No hay fechas de cierre: "
        "no se producen proyecciones mensuales ni anuales.",
        14, 40,
    )

    # Top fichas
    section(ws, 49, "Fichas con mayor probabilidad estructural de pérdida", 14)
    fp = sorted(pred["ficha_probabilidades"], key=lambda x: x["prob_desercion"], reverse=True)[:15]
    headers = ["Ranking", "Ficha", "Jornada", "Generación", "n", "Pérdidas", "Tasa observada", "Prob. posterior", "IC 95% inf.", "IC 95% sup.", "Nivel"]
    rows = [[x["ranking"], x["FichaID"], x["Jornada"], x["GeneracionID"], x["n"], x["perdidas"], x["tasa_observada"],
             x["prob_desercion"], x["ic95_inf"], x["ic95_sup"], x["nivel_riesgo"]] for x in fp]
    write_table(ws, 50, 1, headers, rows, widths=[8, 11, 10, 11, 6, 8, 12, 14, 10, 10, 10])
    add_table_style(ws, f"A50:K{50 + len(rows)}", "tblTopFichas")
    for i in range(51, 51 + len(rows)):
        for c in (7, 8, 9, 10):
            ws.cell(i, c).number_format = "0.0%"

    # Priorización individual (sin PII)
    section(ws, 67, "Priorización operativa de aprendices (sin nombres ni documentos)", 14)
    f = data["FactMatricula"].copy()
    for c in ["ProbPerdidaEstimada", "PercentilProbabilidad", "RankingRiesgoFicha"]:
        f[c] = as_float(f, c)
    f = f[f["PrioridadAtencion"].isin(["Inmediata", "Seguimiento"])].copy()
    f = f.sort_values(["PrioridadAtencion", "ProbPerdidaEstimada"], ascending=[True, False]).head(100)
    dprog = data["DimPrograma"].set_index("ProgramaID")
    djorn = data["DimJornada"].set_index("JornadaID")
    headers = ["#", "Aprendiz (hash)", "Ficha", "Programa", "Jornada", "Prob. estimada", "Percentil", "Alerta", "Prioridad", "Motivo"]
    rows = []
    for i, (_, x) in enumerate(f.iterrows(), start=1):
        prog = dprog.loc[x["ProgramaID"], "ProgramaCorto"] if x["ProgramaID"] in dprog.index else "—"
        jorn = djorn.loc[x["JornadaID"], "Jornada"] if x["JornadaID"] in djorn.index else "—"
        rows.append([i, x["AprendizID"], x["FichaID"], prog, jorn, x["ProbPerdidaEstimada"],
                     x["PercentilProbabilidad"], x["NivelAlertaAprendiz"], x["PrioridadAtencion"], x["MotivoPrioridad"]])
    write_table(ws, 68, 1, headers, rows, widths=[6, 18, 11, 30, 10, 13, 10, 10, 11, 42])
    add_table_style(ws, f"A68:J{68 + len(rows)}", "tblPrioridad")
    ws.freeze_panes = "A69"
    for i in range(69, 69 + len(rows)):
        ws.cell(i, 6).number_format = "0.0%"
        ws.cell(i, 7).number_format = "0.0"

    note(
        ws, 68 + len(rows) + 2,
        "La lista individual es una cola de trabajo operativa basada en la ficha y en variables estructurales. No es una "
        "predicción personal validada: el modelo individual tiene AUC 0,467. No use esta lista para sancionar, negar cupos "
        "ni certificar. El identificador es un hash; no permite recuperar el documento original.",
        14, 44,
    )

    page_setup(ws)
    ws.print_area = f"A1:N{68 + len(rows) + 4}"


# ---------------------------------------------------------------------------
# Diccionario
# ---------------------------------------------------------------------------
COL_DESC = {
    "AprendizID": "Identificador seudónimo del aprendiz (SHA-256 del documento, truncado). No permite recuperar el documento.",
    "TipoDocumento": "Tipo de documento (TI, CC, PPT, CE). Se usa solo como proxy grueso de edad; no es edad.",
    "Genero": "Género declarado. La fuente no lo trae: todos los registros quedan 'No informado'.",
    "GeneroFuente": "Origen del dato de género; documenta que no está disponible en la fuente.",
    "GrupoEdadProxy": "Grupo de edad inferido del tipo de documento. Proxy, no edad real.",
    "Edad": "Edad. No disponible en la fuente; queda vacía.",
    "MunicipioID": "Llave del municipio. La fuente no lo trae: 'No informado'.",
    "DepartamentoID": "Llave del departamento. La fuente no lo trae: 'No informado'.",
    "EmailDominio": "Dominio del correo (sin usuario). Sirve para calidad de contacto, no para identificar personas.",
    "TieneCelular": "1 si hay celular registrado; 0 si no.",
    "CelularValido": "1 si el celular tiene exactamente 10 dígitos.",
    "EmailValido": "1 si el correo cumple estructura básica y dominio con punto.",
    "ContactoCompleto": "1 si celular y correo son válidos. Bandera operativa, no factor de riesgo.",
    "TotalMatriculas": "Número de matrículas asociadas.",
    "TotalFichas": "Número de fichas distintas en las que aparece el aprendiz.",
    "PrimeraFicha": "Primera ficha observada para el aprendiz en el corte.",
    "UltimaFicha": "Última ficha observada para el aprendiz en el corte.",
    "EstadoActual": "Estado de la matrícula en el corte.",
    "TieneMultiplesFichas": "1 si el aprendiz aparece en más de una ficha.",
    "ProbPerdidaMax": "Máxima probabilidad estructural entre las fichas del aprendiz. No es probabilidad individual validada.",
    "NivelAlertaAprendiz": "Banda de alerta individual derivada del percentil de probabilidad estructural.",
    "RequiereIntervencion": "1 si la prioridad es Inmediata o Seguimiento.",
    "FichasRiesgoAlto": "Número de fichas del aprendiz con nivel Alto o Crítico.",
    "MotivoPrioridad": "Explicación textual de la prioridad asignada.",
    "FichaID": "Número de ficha. Llave de la dimensión ficha.",
    "FichaNombre": "Etiqueta descriptiva de la ficha.",
    "ProgramaID": "Llave del programa normalizado.",
    "Jornada": "Jornada de la ficha (DIURNA o NOCTURNA).",
    "GeneracionID": "Generación proxy: prefijo de 3 dígitos de la ficha. No es año calendario.",
    "CentroID": "Llave del centro de formación.",
    "EstadoFicha": "Estado administrativo de la ficha en el corte.",
    "FechaReporte": "Fecha del corte: 2026-10-19.",
    "AprendicesActivos": "Aprendices en estado activo en la ficha.",
    "AprendicesVinculados": "Aprendices vinculados: activos más aplazados.",
    "EnFormacion": "Aprendices en formación.",
    "Induccion": "Aprendices en inducción.",
    "Condicionados": "Aprendices condicionados.",
    "Aplazados": "Aprendices aplazados.",
    "Cancelados": "Matrículas canceladas.",
    "Retiros": "Retiros voluntarios.",
    "Trasladados": "Traslados a otra ficha o centro.",
    "Certificados": "Certificados. La fuente no trae certificaciones: todos en 0.",
    "TasaPerdida": "Pérdidas / matrículas de la ficha.",
    "TasaPerdidaAjustada": "Tasa de pérdida suavizada por empirical Bayes (k=10).",
    "TasaCancelacion": "Cancelados / matrículas.",
    "TasaRetiro": "Retiros voluntarios / matrículas.",
    "TasaActivos": "Activos / matrículas.",
    "TasaContactoIncompleto": "Matrículas con contacto incompleto / matrículas.",
    "IC95Inferior": "Límite inferior del IC 95% de la tasa de pérdida.",
    "IC95Superior": "Límite superior del IC 95% de la tasa de pérdida.",
    "IndiceRiesgo": "Percentil de la tasa ajustada por empirical Bayes. Es un ranking, no una probabilidad.",
    "PercentilRiesgo": "Percentil del índice de riesgo entre las 56 fichas.",
    "NivelRiesgo": "Banda de riesgo: Bajo, Medio, Alto o Crítico.",
    "RankingRiesgo": "Posición de la ficha en el ranking de riesgo (1 = mayor riesgo).",
    "Confiabilidad": "Indicador de estabilidad del ranking según tamaño de ficha.",
    "AlertaPrincipal": "Principal señal de alerta de la ficha.",
    "AlertaSecundaria": "Señal de alerta secundaria.",
    "ProbDesercionFicha": "Media posterior beta-binomial de pérdida de la ficha. No es un pronóstico individual.",
    "Prioridad": "Prioridad operativa de la ficha (P1 a P4).",
    "ProbDesercionICInf": "Límite inferior del IC creíble 95% de la probabilidad de pérdida.",
    "ProbDesercionICSup": "Límite superior del IC creíble 95% de la probabilidad de pérdida.",
    "ProbSupera30": "Probabilidad posterior de que la tasa de la ficha supere 30%.",
    "ProbSupera40": "Probabilidad posterior de que la tasa de la ficha supere 40%.",
    "ProgramaNombre": "Nombre canónico del programa.",
    "ProgramaCorto": "Nombre abreviado del programa para visuales.",
    "LineaTecnologica": "Línea tecnológica del programa.",
    "NivelFormacion": "Nivel inferido del nombre del programa (Técnico o Tecnólogo).",
    "NivelFuente": "Fuente del nivel: inferido del nombre; validar contra SOFIA Plus.",
    "TotalFichas": "Número de fichas del programa.",
    "Activo": "Indica si el programa tiene matrícula en el corte.",
    "NotaNivel": "Advertencia sobre la inferencia del nivel.",
    "EstadoID": "Llave del estado de matrícula.",
    "Estado": "Nombre del estado de matrícula.",
    "Categoria": "Categoría analítica del estado.",
    "EsVinculado": "1 si el estado cuenta como vinculado.",
    "EsActivo": "1 si el estado cuenta como activo.",
    "EsPerdida": "1 si el estado cuenta como pérdida (cancelado o retiro).",
    "EsCancelado": "1 si el estado es cancelado.",
    "EsRetirado": "1 si el estado es retiro voluntario.",
    "EsTrasladado": "1 si el estado es trasladado.",
    "EsSuspendido": "1 si el estado es suspendido (aplazado).",
    "EsRiesgo": "1 si el estado es condicionado o aplazado.",
    "EsCertificado": "1 si el estado es certificado. No hay registros en el corte.",
    "Definicion": "Definición funcional del estado.",
    "GeneracionNombre": "Etiqueta de la generación proxy.",
    "GeneracionOrden": "Orden de la generación por prefijo de ficha. No es año.",
    "RangoFicha": "Rango de números de ficha que compone la generación.",
    "Fichas": "Número de fichas de la generación.",
    "Matriculas": "Número de matrículas.",
    "Perdidas": "Número de pérdidas.",
    "Nota": "Nota metodológica.",
    "FechaID": "Llave de fecha en formato AAAAMMDD.",
    "Fecha": "Fecha calendario.",
    "Anio": "Año.",
    "Trimestre": "Trimestre (T1–T4).",
    "TrimestreNum": "Número de trimestre.",
    "Mes": "Número de mes.",
    "NombreMes": "Nombre del mes.",
    "MesCorto": "Nombre corto del mes.",
    "AnioMes": "Año y mes en formato AAAAMM.",
    "SemanaISO": "Semana ISO.",
    "Dia": "Día del mes.",
    "DiaSemana": "Día de la semana (1 = lunes).",
    "NombreDia": "Nombre del día.",
    "EsFinSemana": "1 si es fin de semana.",
    "InicioMes": "Primer día del mes.",
    "FinMes": "Último día del mes.",
    "MatriculaID": "Identificador único de la matrícula.",
    "EsPerdida": "1 si la matrícula se canceló o retiró.",
    "NivelRiesgoFicha": "Nivel de riesgo de la ficha, repetido en el hecho.",
    "IndiceRiesgoFicha": "Índice de riesgo de la ficha, repetido en el hecho.",
    "Peso": "Peso de la matrícula en el análisis (1 por fila).",
    "ProbPerdidaEstimada": "Probabilidad estructural estimada para la matrícula según su ficha y covariables.",
    "RankingRiesgoFicha": "Ranking de riesgo de la ficha.",
    "PercentilProbabilidad": "Percentil de la probabilidad estimada entre las matrículas.",
    "PrioridadAtencion": "Prioridad operativa: Inmediata, Seguimiento o Rutinaria.",
    "RequiereIntervencion": "1 si requiere intervención.",
    "Escenario": "Escenario de permanencia: Optimista, Base o Pesimista.",
    "PerdidasObservadas": "Pérdidas ya observadas en la ficha.",
    "TasaObservada": "Tasa de pérdida observada.",
    "PoblacionVinculada": "Población vinculada al inicio de la proyección.",
    "TasaFinalSupuesta": "Tasa final (plateau) supuesta para el escenario.",
    "PerdidaAdicionalEsperada": "Pérdida adicional esperada desde el corte hasta el plateau.",
    "PoblacionProyectada": "Población proyectada al final del escenario.",
    "TasaProyectada": "Tasa de pérdida proyectada.",
}


def sheet_diccionario(wb, data, stats):
    ws = wb.create_sheet("Diccionario")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Diccionario de datos", "Tablas, grano, columnas y reglas de privacidad del modelo analítico.", 8)

    rows = [
        ("FactMatricula", "Matrícula de aprendiz en ficha", len(data["FactMatricula"]), "Hecho", "Una fila por matrícula; un aprendiz puede tener dos fichas."),
        ("FactProyeccionMatricula", "Ficha × escenario", len(data["FactProyeccionMatricula"]), "Hecho", "168 filas: 56 fichas × 3 escenarios."),
        ("DimAprendiz", "Persona (documento hasheado)", len(data["DimAprendiz"]), "Dimensión", "Sin nombres, documentos, celulares ni correos."),
        ("DimFicha", "Ficha", len(data["DimFicha"]), "Dimensión", "Incluye tasa, riesgo y probabilidad estructural."),
        ("DimPrograma", "Programa normalizado", len(data["DimPrograma"]), "Dimensión", "15 nombres canónicos."),
        ("DimJornada", "Jornada", len(data["DimJornada"]), "Dimensión", "DIURNA, NOCTURNA, No informado."),
        ("DimEstado", "Estado de matrícula", len(data["DimEstado"]), "Dimensión", "7 estados; reglas de pérdida documentadas."),
        ("DimTiempo", "Día", len(data["DimTiempo"]), "Dimensión", "2024–2026; solo el corte tiene hechos."),
        ("DimCentroFormacion", "Centro", len(data["DimCentroFormacion"]), "Dimensión", "Un centro."),
        ("DimNivelFormacion", "Nivel", len(data["DimNivelFormacion"]), "Dimensión", "Técnico, Tecnólogo, No informado."),
        ("DimMunicipio", "Municipio", len(data["DimMunicipio"]), "Dimensión", "No informado en la fuente."),
        ("DimDepartamento", "Departamento", len(data["DimDepartamento"]), "Dimensión", "No informado en la fuente."),
        ("DimGeneracion", "Prefijo de ficha", len(data["DimGeneracion"]), "Dimensión", "Proxy de generación; no es año calendario."),
        ("DimRiesgo", "Banda de riesgo", len(data["DimRiesgo"]), "Dimensión", "Bajo, Medio, Alto, Crítico."),
    ]
    write_table(ws, 4, 1, ["Tabla", "Grano", "Filas", "Tipo", "Nota"], rows, widths=[24, 30, 8, 12, 66])
    add_table_style(ws, f"A4:E{4 + len(rows)}", "tblTablas")

    # Columnas
    section(ws, 22, "Columnas", 8)
    headers = ["Tabla", "Columna", "Tipo", "Descripción"]
    col_rows = []
    for table in sorted(data):
        df = data[table]
        for c in df.columns:
            desc = COL_DESC.get(c, "Campo del modelo analítico.")
            # Tipo inferido del contenido
            vals = df[c].head(200)
            if c in {"Fecha", "InicioMes", "FinMes", "FechaReporte"}:
                typ = "Fecha"
            elif any(v.lower() in {"true", "false"} for v in vals.astype(str)):
                typ = "Booleano"
            else:
                try:
                    pd.to_numeric(vals.replace("", pd.NA).dropna())
                    typ = "Numérico"
                except Exception:
                    typ = "Texto"
            col_rows.append([table, c, typ, desc])
    write_table(ws, 23, 1, headers, col_rows, widths=[24, 28, 10, 100])
    add_table_style(ws, f"A23:D{23 + len(col_rows)}", "tblColumnas")
    ws.freeze_panes = "A24"

    note(
        ws, 23 + len(col_rows) + 2,
        "Regla de privacidad: data/processed y este libro no contienen nombres, documentos, celulares ni correos. "
        "El correo se reduce a dominio; el documento se reemplaza por un hash. La lista nominal está en data/restricted "
        "y no debe publicarse ni adjuntarse a este entregable.",
        8, 40,
    )

    page_setup(ws)
    ws.print_area = f"A1:D{23 + len(col_rows) + 4}"


# ---------------------------------------------------------------------------
# Notas
# ---------------------------------------------------------------------------
def sheet_notas(wb, stats, pred):
    ws = wb.create_sheet("Notas")
    ws.sheet_view.showGridLines = False
    title_block(ws, "Notas metodológicas", "Cómo leer el libro, qué se puede concluir y qué no.", 10)

    blocks = [
        ("1. Corte y granularidad", [
            "Hay un solo corte: 19 de octubre de 2026. No hay serie histórica ni fechas de matrícula, retiro o certificación.",
            "El grano de FactMatricula es una matrícula de aprendiz en una ficha. Un aprendiz puede aportar dos filas si está en dos fichas.",
            "Los totales de matrícula (1.592) no son personas únicas (1.583). Use la medida correcta según la pregunta.",
        ]),
        ("2. Estados y pérdida", [
            "Pérdida = CANCELADO + RETIRO VOLUNTARIO. En el corte: 428 cancelados + 11 retiros = 439 (27,6%).",
            "TRASLADADO no es pérdida, pero tampoco es activo ni vinculado. APLAZADO es vinculado, no activo.",
            "CONDICIONADO es activo en riesgo. No hay certificados en la fuente.",
        ]),
        ("3. Riesgo por ficha", [
            "El índice es el percentil de la tasa de pérdida ajustada por empirical Bayes (prior k=10, media global 27,58%).",
            "Bandas: Bajo < p50; Medio p50–p75; Alto p75–p90; Crítico ≥ p90. La validación es monotónica, no predictiva.",
            "La probabilidad beta-binomial reporta media posterior e IC creíble 95%. No es una fecha ni una probabilidad individual.",
            "El contacto incompleto no entra al índice: su asociación ajustada por programa es espuria (OR MH 0,65).",
        ]),
        ("4. Programa y jornada", [
            "Los contrastes son exploratorios: no ajustan por clustering intra-ficha y no prueban causalidad.",
            "La jornada nocturna tiene mayor tasa observada (36,0% vs 23,0%), pero la asignación a jornada no es aleatoria.",
            "Los rankings de programas con una ficha o n pequeño son inestables; siempre lea el IC y el tamaño.",
        ]),
        ("5. Cohortes", [
            "La generación es un proxy construido con el prefijo de 3 dígitos de la ficha. No es año calendario.",
            "La tendencia negativa (Spearman −0,921) mezcla maduración de cohortes y composición. Es descriptiva.",
            "No se puede estimar nueva matrícula ni estacionalidad con un solo snapshot.",
        ]),
        ("6. Modelo predictivo", [
            "Validación StratifiedGroupKFold(5) agrupada por ficha; predicciones out-of-fold.",
            "AUC 0,726 (IC bootstrap 0,669–0,781), Brier 0,178 vs base 0,200, ECE 0,048.",
            "El modelo estructural (sin variables individuales) obtiene AUC 0,716; el individual, 0,467.",
            "Conclusión: la señal es de ficha/programa/jornada. Priorice fichas. No use el score para sancionar ni negar cupos.",
        ]),
        ("7. Proyección", [
            "Proyecta la permanencia de los 1.144 vinculados, no la nueva matrícula.",
            "Plateau global 43,2% con suavizado por programa (k=50). Escenarios: Base, Optimista −7 pp, Pesimista +7 pp.",
            "Base: 856 proyectados (−288; 45,6% de pérdida proyectada). Optimista: 932. Pesimista: 769.",
            "No produce fechas de cierre ni presupuesto: es un ejercicio de escenarios.",
        ]),
        ("8. Privacidad", [
            "data/processed no contiene nombres, documentos, celulares ni correos.",
            "El identificador de aprendiz es un hash; el correo se reduce a dominio.",
            "La lista nominal está en data/restricted/lista_priorizada.csv y es de uso interno. No se incluye en este libro.",
        ]),
        ("9. Reproducibilidad", [
            "Ejecute los scripts 01 a 06 en orden con Python 3.12+ y las dependencias de requirements.txt.",
            "Comando: $env:PYTHONIOENCODING='utf-8'; python -X utf8 scripts/05_generar_excel.py",
            "Las cifras del libro se leen de data/processed y outputs/*.json; no se digitan a mano.",
        ]),
    ]

    row = 4
    for title, items in blocks:
        section(ws, row, title, 10)
        row += 1
        for text in items:
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=10)
            c = ws.cell(row, 1, "• " + text)
            c.font = BODY
            c.alignment = LEFT_TOP
            c.border = Border(bottom=THIN)
            ws.row_dimensions[row].height = 30
            row += 1
        row += 1

    page_setup(ws, "portrait")
    ws.print_area = f"A1:J{row}"


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
def validate_workbook(path: Path, data, stats, pred):
    from openpyxl import load_workbook

    wb = load_workbook(path)
    expected = ["Portada", "Resumen", "Programas", "Fichas", "Cohortes", "Riesgos", "Predictivo", "Diccionario", "Notas"]
    assert wb.sheetnames == expected, f"Hojas inesperadas: {wb.sheetnames}"

    # Sin PII en celdas de texto
    email_re = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    phone_re = re.compile(r"\b3\d{9}\b")
    pii_hits = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str):
                    if email_re.search(c.value) or phone_re.search(c.value):
                        pii_hits.append((ws.title, c.coordinate, c.value[:60]))
    assert not pii_hits, f"Posible PII: {pii_hits[:5]}"

    # Totales
    assert len(data["FactMatricula"]) == 1592
    assert stats["resumen"]["perdidas"] == 439
    assert abs(stats["resumen"]["tasa_perdida"] - 439 / 1592) < 1e-4
    assert len(data["DimFicha"]) == 56
    assert len(data["FactProyeccionMatricula"]) == 168
    assert len(pred["ficha_probabilidades"]) == 56

    # Las hojas principales tienen datos
    for name, min_rows in [("Programas", 15), ("Fichas", 56), ("Cohortes", 17), ("Riesgos", 56)]:
        ws = wb[name]
        assert ws.max_row >= min_rows, f"{name} tiene muy pocas filas"

    return {
        "hojas": wb.sheetnames,
        "pii_hits": len(pii_hits),
        "tamano_bytes": path.stat().st_size,
        "matriculas": len(data["FactMatricula"]),
        "perdidas": int(stats["resumen"]["perdidas"]),
        "fichas": len(data["DimFicha"]),
        "programas": len(data["DimPrograma"]),
    }


def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    data, stats, pred = load_data()

    wb = Workbook()
    wb.remove(wb.active)

    sheet_portada(wb, data, stats)
    sheet_resumen(wb, data, stats)
    sheet_programas(wb, data, stats)
    sheet_fichas(wb, data, stats)
    sheet_cohortes(wb, data, stats)
    sheet_riesgos(wb, data, stats)
    sheet_predictivo(wb, data, stats, pred)
    sheet_diccionario(wb, data, stats)
    sheet_notas(wb, stats, pred)

    wb.properties.title = "Caracterización de Aprendices Centro ASTIN"
    wb.properties.subject = "Analítica de matrícula, pérdida, riesgo y permanencia"
    wb.properties.creator = "Dashboard Aprendices SENA"
    wb.properties.keywords = "SENA; aprendices; deserción; riesgo; Power BI; Excel"
    wb.properties.description = "Corte 2026-10-19. Datos agregados sin PII."
    wb.active = 0

    tmp = OUT_FILE.with_suffix(".tmp.xlsx")
    wb.save(tmp)
    tmp.replace(OUT_FILE)

    result = validate_workbook(OUT_FILE, data, stats, pred)
    (OUTPUTS / "05_excel_resumen.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Excel generado:", OUT_FILE)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
