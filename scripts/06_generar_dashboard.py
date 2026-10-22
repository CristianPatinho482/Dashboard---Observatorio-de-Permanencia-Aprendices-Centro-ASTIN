# -*- coding: utf-8 -*-
"""
FASE 6 - Dashboard HTML autocontenido (sin internet, sin PII).
Salidas:
  dashboard/index.html
  dashboard/datos_dashboard.json
  dashboard/README.md
  data/restricted/lista_priorizada.csv  (PII; no publicar)
"""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
DASH = ROOT / "dashboard"
DASH.mkdir(parents=True, exist_ok=True)
RESTRICTED = ROOT / "data" / "restricted"


def read_csv(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sha(text, n=12):
    return hashlib.sha1(text.encode("utf-8")).hexdigest().upper()[:n]


def domain_group(domain):
    d = (domain or "").lower()
    if d == "gmail.com":
        return "Gmail"
    if d in ("hotmail.com", "outlook.com", "outlook.es", "hotmail.es", "live.com"):
        return "Hotmail/Outlook"
    if d.endswith(".edu.co") or d.endswith(".edu"):
        return "Educativo"
    if not d:
        return "Sin correo"
    return "Otro"


def main():
    fact = read_csv("FactMatricula.csv")
    fichas = read_csv("DimFicha.csv")
    programas = read_csv("DimPrograma.csv")
    generaciones = read_csv("DimGeneracion.csv")
    estados = read_csv("DimEstado.csv")
    aprendices = {a["AprendizID"]: a for a in read_csv("DimAprendiz.csv")}
    proj = read_csv("FactProyeccionMatricula.csv")
    stats = json.loads((OUT / "03_analisis_estadistico.json").read_text(encoding="utf-8"))
    model = json.loads((OUT / "04_modelo_predictivo.json").read_text(encoding="utf-8"))

    ficha_by = {f["FichaID"]: f for f in fichas}
    prog_by = {p["ProgramaID"]: p for p in programas}
    estado_by = {e["EstadoID"]: e for e in estados}
    gen_by = {g["GeneracionID"]: g for g in generaciones}
    gen_order = {g["GeneracionID"]: int(num(g["GeneracionOrden"])) for g in generaciones}

    rows = []
    for r in fact:
        a = aprendices[r["AprendizID"]]
        f = ficha_by[r["FichaID"]]
        e = estado_by[r["EstadoID"]]
        rows.append({
            "id": r["AprendizID"],
            "ficha": r["FichaID"],
            "prog": r["ProgramaID"],
            "jorn": "DIURNA" if r["JornadaID"] == "J01" else "NOCTURNA",
            "gen": r["GeneracionID"],
            "genOrden": gen_order.get(r["GeneracionID"], 0),
            "estado": e["Estado"],
            "categoria": e["Categoria"],
            "perdida": int(num(r["EsPerdida"])),
            "activo": int(num(r["EsActivo"])),
            "contacto": int(num(r["ContactoCompleto"])),
            "tipo": a["TipoDocumento"],
            "edadProxy": a["GrupoEdadProxy"],
            "dominio": domain_group(a["EmailDominio"]),
            "prob": round(num(r["ProbPerdidaEstimada"]), 4),
            "alerta": r["NivelAlertaAprendiz"],
            "prioridad": r["PrioridadAtencion"],
            "motivo": r["MotivoPrioridad"],
            "rankFicha": int(num(r["RankingRiesgoFicha"])),
            "percentil": round(num(r["PercentilProbabilidad"]), 1),
            "riesgoFicha": f["NivelRiesgo"],
            "contactoIncFicha": round(num(f["TasaContactoIncompleto"]), 4),
        })

    ficha_rows = []
    for f in fichas:
        ficha_rows.append({
            "id": f["FichaID"],
            "prog": f["ProgramaID"],
            "jorn": f["Jornada"],
            "gen": f["GeneracionID"],
            "genOrden": gen_order.get(f["GeneracionID"], 0),
            "n": int(num(f["TotalMatriculas"])),
            "perdidas": int(num(f["Cancelados"])) + int(num(f["Retiros"])),
            "activos": int(num(f["AprendicesActivos"])),
            "vinculados": int(num(f["AprendicesVinculados"])),
            "tasa": round(num(f["TasaPerdida"]), 4),
            "tasaAj": round(num(f["TasaPerdidaAjustada"]), 4),
            "indice": round(num(f["IndiceRiesgo"]), 1),
            "percentil": round(num(f["PercentilRiesgo"]), 1),
            "nivel": f["NivelRiesgo"],
            "ranking": int(num(f["RankingRiesgo"])),
            "conf": f["Confiabilidad"],
            "alerta": f["AlertaPrincipal"],
            "alertaSec": f["AlertaSecundaria"],
            "contactoInc": round(num(f["TasaContactoIncompleto"]), 4),
            "prob": round(num(f["ProbDesercionFicha"]), 4),
            "icInf": round(num(f["ProbDesercionICInf"]), 4),
            "icSup": round(num(f["ProbDesercionICSup"]), 4),
            "prob30": round(num(f["ProbSupera30"]), 4),
            "prob40": round(num(f["ProbSupera40"]), 4),
            "prioridad": f["Prioridad"],
        })

    prog_rows = []
    for p in stats["programas"]["detalle"]:
        d = prog_by[p["programa_id"]]
        prog_rows.append({
            "id": p["programa_id"],
            "nombre": p["programa"],
            "corto": p["corto"],
            "linea": p["linea"],
            "nivel": p["nivel"],
            "fichas": p["fichas"],
            "n": p["matriculas"],
            "perdidas": p["perdidas"],
            "activos": p["activos"],
            "tasa": p["tasa_perdida"],
            "icInf": p["ic95_inf"],
            "icSup": p["ic95_sup"],
            "eb": p["tasa_ajustada_eb"],
            "rank": p["ranking_tasa"],
            "participacion": p["participacion"],
        })

    gen_rows = []
    for g in stats["tendencia_generaciones"]["detalle"]:
        gen_rows.append({
            "id": g["generacion_id"],
            "nombre": g["generacion"].replace("Generación ", "G"),
            "orden": g["orden"],
            "fichas": g["fichas"],
            "n": g["n"],
            "perdidas": g["perdidas"],
            "tasa": g["tasa_perdida"],
        })

    estado_rows = []
    counts = Counter(r["EstadoID"] for r in fact)
    for e in estados:
        estado_rows.append({
            "id": e["EstadoID"], "estado": e["Estado"], "categoria": e["Categoria"],
            "n": counts.get(e["EstadoID"], 0), "color": e["ColorHex"],
        })

    proj_summary = model["proyeccion"]["resumen_escenarios"]
    proj_prog = model["proyeccion"]["por_programa_base"]
    proj_gen = model["proyeccion"]["por_generacion_base"]

    data = {
        "meta": {
            "fecha": "2026-10-19",
            "matriculas": len(fact),
            "aprendices": len(aprendices),
            "fichas": len(fichas),
            "programas": len(programas),
            "generaciones": len(generaciones),
            "perdidas": sum(r["perdida"] for r in rows),
            "tasa": round(sum(r["perdida"] for r in rows) / len(rows), 4),
            "activos": sum(r["activo"] for r in rows),
            "contactoIncompleto": sum(1 for r in rows if not r["contacto"]),
            "fichasCriticas": sum(1 for f in ficha_rows if f["nivel"] == "Crítico"),
            "alertasAltas": sum(1 for r in rows if r["alerta"] == "Alto"),
            "prioridadInmediata": sum(1 for r in rows if r["prioridad"] == "Inmediata"),
            "nota": "Snapshot único. Sin PII: identificadores hasheados.",
        },
        "programas": prog_rows,
        "fichas": ficha_rows,
        "generaciones": gen_rows,
        "estados": estado_rows,
        "rows": rows,
        "stats": {
            "jornadas": stats["jornadas"],
            "programasContraste": stats["programas"]["contraste"],
            "contacto": stats["contacto"],
            "fichasDist": stats["fichas_distribucion"],
            "correlaciones": stats["correlaciones"],
            "tendencia": stats["tendencia_generaciones"],
            "validacionRiesgo": stats["validacion_riesgo"],
            "calidad": stats["calidad_datos"],
            "poder": stats["poder_estadistico"],
            "concentracion": stats["programas"]["concentracion"],
            "recomendaciones": stats["recomendaciones_metodologicas"],
        },
        "modelo": {
            "principal": model["modelo_principal"],
            "individual": model["modelo_individual"],
            "estructural": model["modelo_estructural"],
            "distribucion": model["distribucion_probabilidad"],
            "coeficientes": model["coeficientes"],
            "proyeccion": model["proyeccion"],
            "pronostico": model["pronostico_nueva_matricula"],
            "limitaciones": model["limitaciones"],
        },
        "proyeccion": {
            "resumen": proj_summary,
            "porPrograma": proj_prog,
            "porGeneracion": proj_gen,
        },
    }

    (DASH / "datos_dashboard.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    # Lista nominal restringida (PII) para coordinacion; NO se publica.
    raw = json.loads((RESTRICTED / "aprendices_crudos.json").read_text(encoding="utf-8"))
    meta_by_mat = {}
    for r in fact:
        meta_by_mat[(r["FichaID"], r["AprendizID"])] = r
    restricted = []
    for r in raw:
        tipo = str(r["tipo_documento"]).strip().upper()
        doc = re.sub(r"\D", "", str(r["documento"]))
        aid = "APR-" + sha(f"{tipo}|{doc}", 10)
        ficha = str(r["ficha"])
        m = meta_by_mat.get((ficha, aid))
        if not m:
            continue
        restricted.append({
            "AprendizID": aid,
            "NombreCompleto": f"{r['nombres']} {r['apellidos']}".strip(),
            "Documento": doc,
            "TipoDocumento": tipo,
            "FichaID": ficha,
            "ProgramaID": m["ProgramaID"],
            "Jornada": "DIURNA" if m["JornadaID"] == "J01" else "NOCTURNA",
            "Estado": estado_by[m["EstadoID"]]["Estado"],
            "ProbPerdida": m["ProbPerdidaEstimada"],
            "NivelAlerta": m["NivelAlertaAprendiz"],
            "Prioridad": m["PrioridadAtencion"],
            "Motivo": m["MotivoPrioridad"],
            "Celular": r["celular"],
            "Correo": r["correo"],
        })
    restricted.sort(key=lambda x: (x["Prioridad"] != "Inmediata", -float(x["ProbPerdida"] or 0)))
    with (RESTRICTED / "lista_priorizada.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(restricted[0].keys()))
        w.writeheader()
        w.writerows(restricted)

    chart_js = (DASH / "chart.umd.min.js").read_text(encoding="utf-8")
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    html = html.replace("__CHARTJS__", chart_js.replace("</", "<\\/"))
    (DASH / "index.html").write_text(html, encoding="utf-8")

    (DASH / "README.md").write_text(
        "# Observatorio de Permanencia Aprendices Centro ASTIN\n\n"
        "Abrir `index.html` con doble clic. No requiere internet ni servidor: Chart.js y los datos están embebidos.\n\n"
        "- Datos: snapshot 2026-10-19, 56 fichas, 1.592 matrículas.\n"
        "- Identidad: tipografías Work Sans / Calibri y paleta del Manual de Identidad Corporativa SENA 2024. Los logos no se incluyen; se insertan manualmente.\n"
        "- Privacidad: el HTML no incluye nombres, documentos, celulares ni correos. Usa `AprendizID` hasheado.\n"
        "- Lista nominal: `../data/restricted/lista_priorizada.csv` (PII, uso interno; no publicar).\n"
        "- Actualización: ejecutar `scripts/01` a `04` y luego `06_generar_dashboard.py`.\n\n"
        "## Pestañas\n\n"
        "1. Resumen ejecutivo\n2. Demografía y calidad (con brechas de datos)\n"
        "3. Programas\n4. Fichas\n5. Temporal / cohortes (proxy por prefijo de ficha)\n"
        "6. Riesgos\n7. Predictivo y proyección de permanencia\n",
        encoding="utf-8",
    )

    print("Dashboard:", DASH / "index.html", f"({(DASH / 'index.html').stat().st_size/1024:.0f} KB)")
    print("Datos:", DASH / "datos_dashboard.json")
    print("Lista restringida:", RESTRICTED / "lista_priorizada.csv", f"({len(restricted)} filas, PII)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Caracterización de Aprendices · Centro ASTIN</title>
<style>
:root{
  /* Manual de Identidad Corporativa SENA 2024 */
  --green:#39A900; --green-dark:#007832; --dark:#00304D; --dark-2:#007832;
  --violet:#71277A; --sky:#50E5F9; --brand-yellow:#FDC300;
  --ink:#17313F; --muted:#5D7480; --line:#DDE7EC; --bg:#F6F6F6; --card:#FFFFFF;
  --red:#C62828; --orange:#EF6C00; --yellow:#FDC300; --teal:#007832;
  --font-main:"Work Sans",Calibri,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --shadow:0 6px 22px rgba(0,48,77,.08);
  --radius:14px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-main);font-size:14px;line-height:1.45}
a{color:var(--dark-2)}
.topbar{background:linear-gradient(118deg,#00304D 0%,#00304D 62%,#007832 100%);color:#fff;padding:22px 30px 20px;display:flex;justify-content:space-between;gap:20px;align-items:center;flex-wrap:wrap;border-bottom:4px solid var(--green)}
.brand{display:flex;gap:16px;align-items:center}
.brand img{height:54px;width:auto;display:block}
.topbar h1{margin:0;font-size:27px;line-height:1.12;letter-spacing:-.2px;font-weight:700}
.topbar p{margin:5px 0 0;color:#C9DCE6;font-size:12.5px}
.meta{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.pill{background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);padding:6px 10px;border-radius:999px;font-size:11.5px;color:#EAF4F8;white-space:nowrap}
.pill.privacy{background:rgba(57,169,0,.22);border-color:rgba(57,169,0,.45)}
nav.tabs{display:flex;gap:4px;overflow-x:auto;background:#fff;padding:0 22px;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:40;box-shadow:0 2px 10px rgba(0,50,77,.04)}
.tab{border:0;background:transparent;padding:14px 14px 12px;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap}
.tab:hover{color:var(--dark);background:#F7FAFB}
.tab.active{color:var(--dark);border-bottom-color:var(--green)}
main{max-width:1480px;margin:0 auto;padding:20px 24px 40px}
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:end;background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px;box-shadow:var(--shadow);margin-bottom:14px}
.field{display:flex;flex-direction:column;gap:3px;min-width:150px}
.field label{font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);font-weight:700}
select,input[type=search]{border:1px solid #C9D7DF;border-radius:8px;padding:8px 10px;background:#fff;color:var(--ink);font-size:12.5px;outline:none;min-height:36px}
select:focus,input:focus{border-color:var(--green);box-shadow:0 0 0 3px rgba(57,169,0,.12)}
.btn{border:0;border-radius:8px;padding:9px 13px;font-size:12px;font-weight:700;cursor:pointer;background:var(--dark);color:#fff}
.btn:hover{background:var(--dark-2)}
.btn.ghost{background:#EDF3F6;color:var(--dark)}
.btn.green{background:var(--green)}
.btn.small{padding:6px 9px;font-size:11px}
.banner{display:flex;gap:12px;align-items:flex-start;background:#FFF8E1;border:1px solid #F3D48A;color:#5D4300;border-radius:12px;padding:11px 14px;margin-bottom:16px;font-size:12.5px}
.banner strong{color:#4A3500}
.banner .close{margin-left:auto;background:transparent;border:0;font-size:18px;cursor:pointer;color:#8A6A00;line-height:1}
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 15px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.kpi:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--green)}
.kpi.red:before{background:var(--red)} .kpi.orange:before{background:var(--orange)} .kpi.yellow:before{background:var(--yellow)} .kpi.teal:before{background:var(--teal)}
.kpi .label{font-size:10.5px;text-transform:uppercase;letter-spacing:.55px;color:var(--muted);font-weight:700}
.kpi .value{font-size:27px;font-weight:800;letter-spacing:-.5px;margin:3px 0 1px;color:var(--dark)}
.kpi .sub{font-size:11px;color:var(--muted)}
.section-title{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:22px 0 10px}
.section-title h2{margin:0;font-size:17px;color:var(--dark)}
.section-title p{margin:0;color:var(--muted);font-size:12px}
.grid{display:grid;gap:14px}
.grid-2{grid-template-columns:1.05fr .95fr}
.grid-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:15px 16px;min-width:0}
.card h3{margin:0 0 2px;font-size:13.5px;color:var(--dark)}
.card .hint{color:var(--muted);font-size:11.5px;margin-bottom:8px}
.chart-wrap{position:relative;height:300px}
.chart-wrap.tall{height:360px}
.chart-wrap.short{height:230px}
.table-wrap{overflow:auto;max-height:520px;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:12px}
th{position:sticky;top:0;background:#F2F7F9;color:var(--dark);text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);font-size:10.5px;text-transform:uppercase;letter-spacing:.4px;z-index:2}
td{padding:8px;border-bottom:1px solid #EDF2F4;vertical-align:middle}
tr:hover td{background:#FAFCFD}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;padding:3px 8px;border-radius:999px;font-size:10.5px;font-weight:800;white-space:nowrap}
.badge.Bajo{background:#E4F4DC;color:#246B00}.badge.Medio{background:#FFF1C6;color:#7A5600}
.badge.Alto{background:#FFE0C2;color:#A33E00}.badge.Crítico{background:#FBDCDC;color:#9B1C1C}
.badge.Inmediata{background:#FBDCDC;color:#9B1C1C}.badge.Seguimiento{background:#FFF1C6;color:#7A5600}.badge.Rutinaria{background:#E7F0F5;color:#35525F}
.badge.P1{background:#FBDCDC;color:#9B1C1C}.badge.P2{background:#FFE0C2;color:#A33E00}.badge.P3{background:#FFF1C6;color:#7A5600}.badge.P4{background:#E7F0F5;color:#35525F}
.mini{display:flex;align-items:center;gap:7px;min-width:90px}
.mini-bar{height:7px;background:#E8EFF3;border-radius:999px;flex:1;overflow:hidden}
.mini-bar span{display:block;height:100%;background:var(--green);border-radius:999px}
.mini-bar span.warn{background:var(--orange)}.mini-bar span.danger{background:var(--red)}
.insight{display:flex;gap:10px;align-items:flex-start;padding:11px 12px;border-radius:11px;background:#F7FAFB;border:1px solid var(--line);margin-bottom:8px}
.insight .ico{width:26px;height:26px;border-radius:8px;background:var(--green);color:#fff;display:grid;place-items:center;font-weight:800;font-size:12px;flex:none}
.insight.red .ico{background:var(--red)}.insight.orange .ico{background:var(--orange)}.insight.teal .ico{background:var(--teal)}
.insight b{color:var(--dark)} .insight p{margin:1px 0 0;color:var(--muted);font-size:12px}
.critical-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.critical{border:1px solid #F3C6C6;background:linear-gradient(180deg,#FFF9F9,#fff);border-radius:12px;padding:12px 13px}
.critical h4{margin:0;font-size:15px;color:#9B1C1C}
.critical .prog{font-size:11px;color:var(--muted);min-height:30px}
.critical .rate{font-size:24px;font-weight:800;color:var(--red)}
.critical .meta{font-size:11px;color:var(--muted);justify-content:flex-start}
.notice{border-left:4px solid var(--orange);background:#FFF9F2;padding:11px 13px;border-radius:9px;font-size:12px;color:#5B3A12;margin:10px 0}
.notice.blue{border-left-color:var(--dark-2);background:#F3F8FB;color:#23495C}
.notice.red{border-left-color:var(--red);background:#FFF5F5;color:#6B1B1B}
.small{font-size:11px;color:var(--muted)}
.two-col-list{display:grid;grid-template-columns:1fr 1fr;gap:8px 18px}
.two-col-list div{padding:6px 0;border-bottom:1px dashed #E2EAEE;font-size:12px}
.two-col-list b{color:var(--dark)}
.tab-panel{display:none}
.tab-panel.active{display:block}
.footer{margin-top:30px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:11px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
.tag{display:inline-block;background:#EDF3F6;color:#35525F;border-radius:6px;padding:2px 6px;font-size:10px;font-weight:700;margin-left:4px}
.nowrap{white-space:nowrap}
@media(max-width:1100px){.kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-2,.grid-3{grid-template-columns:1fr}.critical-grid{grid-template-columns:1fr 1fr}}
@media(max-width:700px){main{padding:14px 12px 30px}.topbar{padding:15px 14px}.topbar h1{font-size:18px}.kpi-grid{grid-template-columns:1fr}.critical-grid{grid-template-columns:1fr}.filters{padding:10px}.field{min-width:135px;flex:1}.chart-wrap{height:260px}nav.tabs{padding:0 8px}.tab{padding:12px 9px;font-size:12px}}
@media print{nav.tabs,.filters,.btn{display:none!important}.tab-panel{display:block!important;page-break-before:always}.card{box-shadow:none}.topbar{background:#00304D!important;-webkit-print-color-adjust:exact}}
</style>
</head>
<body>
<header class="topbar">
  <!-- LOGO SENA: insertar aquí el logosímbolo oficial. No se recrea en este archivo. -->
  <div class="brand">
    <div>
      <h1>Observatorio de Permanencia Aprendices Centro ASTIN</h1>
      <p>Centro de Formación ASTIN · Snapshot 19 de octubre de 2026 · 56 fichas · 15 programas</p>
    </div>
  </div>
  <div class="meta">
    <span class="pill" id="pill-matriculas">1.592 matrículas</span>
    <span class="pill" id="pill-perdida">27,6% pérdida</span>
    <span class="pill privacy">Sin PII · IDs hasheados</span>
  </div>
</header>

<nav class="tabs" role="tablist">
  <button class="tab active" data-tab="resumen" role="tab">Resumen</button>
  <button class="tab" data-tab="demografia" role="tab">Demografía y calidad</button>
  <button class="tab" data-tab="programas" role="tab">Programas</button>
  <button class="tab" data-tab="fichas" role="tab">Fichas</button>
  <button class="tab" data-tab="temporal" role="tab">Temporal / cohortes</button>
  <button class="tab" data-tab="riesgos" role="tab">Riesgos</button>
  <button class="tab" data-tab="predictivo" role="tab">Predictivo</button>
</nav>

<main>
  <section class="filters" aria-label="Filtros globales">
    <div class="field">
      <label for="f-prog">Programa</label>
      <select id="f-prog"><option value="">Todos los programas</option></select>
    </div>
    <div class="field">
      <label for="f-jorn">Jornada</label>
      <select id="f-jorn"><option value="">Todas</option><option>DIURNA</option><option>NOCTURNA</option></select>
    </div>
    <div class="field">
      <label for="f-risk">Riesgo de ficha</label>
      <select id="f-risk"><option value="">Todos</option><option>Crítico</option><option>Alto</option><option>Medio</option><option>Bajo</option></select>
    </div>
    <div class="field">
      <label for="f-q">Buscar ficha</label>
      <input id="f-q" type="search" placeholder="Ej. 3181464" autocomplete="off">
    </div>
    <button class="btn ghost" id="btn-reset">Limpiar</button>
    <button class="btn green" id="btn-print">Imprimir / PDF</button>
    <span class="small" id="filter-count" style="margin-left:auto"></span>
  </section>

  <div class="banner" id="gap-banner">
    <span style="font-size:18px;line-height:1">⚠️</span>
    <div><strong>Brecha de datos:</strong> la fuente solo trae documento, nombres, celular, correo y estado. No hay género, edad, municipio, departamento, fechas de matrícula/egreso ni certificación. Las dimensiones demográficas se muestran como “No informado” y no se inventan distribuciones. <a href="#" data-goto="demografia">Ver detalle</a>.</div>
    <button class="close" aria-label="Cerrar" onclick="document.getElementById('gap-banner').style.display='none'">×</button>
  </div>

  <!-- RESUMEN -->
  <section class="tab-panel active" id="tab-resumen">
    <div class="kpi-grid" id="kpis"></div>
    <div class="grid grid-2">
      <div class="card">
        <h3>Matrículas por estado</h3>
        <div class="hint">Snapshot 19-oct-2026 · todos los estados de la fuente</div>
        <div class="chart-wrap"><canvas id="ch-estados"></canvas></div>
      </div>
      <div class="card">
        <h3>Fichas por nivel de riesgo</h3>
        <div class="hint">Nivel = percentil de la tasa de pérdida ajustada (empirical Bayes)</div>
        <div class="chart-wrap"><canvas id="ch-riesgo"></canvas></div>
      </div>
    </div>
    <div class="section-title"><h2>Hallazgos que requieren atención</h2><p>Lectura ejecutiva, no causal</p></div>
    <div class="grid grid-2">
      <div>
        <div class="insight red"><div class="ico">!</div><div><b>439 matrículas perdidas (27,6%)</b><p>IC 95%: 25,4%–29,8%. El 97,5% de las pérdidas son cancelaciones; solo 11 son retiros voluntarios.</p></div></div>
        <div class="insight orange"><div class="ico">N</div><div><b>La jornada nocturna concentra el mayor riesgo</b><p>36,0% de pérdida vs 23,0% en diurna (OR diurna/nocturna 0,53; p &lt; 0,001). Es asociación, no efecto causal aislado.</p></div></div>
        <div class="insight red"><div class="ico">6</div><div><b>6 fichas críticas</b><p>206 matrículas y 116 pérdidas (56,3% de pérdida). Prioridad P1 para comité académico.</p></div></div>
      </div>
      <div>
        <div class="insight teal"><div class="ico">C</div><div><b>Contacto incompleto: 228 (14,3%)</b><p>Se concentra en cohortes nuevas con 0% de pérdida. No es factor de riesgo; es una brecha de contactabilidad y actualización de datos.</p></div></div>
        <div class="insight"><div class="ico">↗</div><div><b>La pérdida cae con el prefijo de ficha</b><p>Spearman -0,92 entre orden de generación y tasa. El prefijo es un proxy de antigüedad, no un año calendario.</p></div></div>
        <div class="insight orange"><div class="ico">?</div><div><b>La señal individual es débil</b><p>AUC del modelo con variables individuales: 0,47. El modelo completo (0,73) prioriza fichas/estructuras, no personas.</p></div></div>
      </div>
    </div>
    <div class="section-title"><h2>Fichas críticas</h2><p>Ordenadas por probabilidad posterior de pérdida</p></div>
    <div class="critical-grid" id="critical-cards"></div>
  </section>

  <!-- DEMOGRAFIA -->
  <section class="tab-panel" id="tab-demografia">
    <div class="notice red">
      <strong>No disponible en la fuente.</strong> El reporte de ficha no contiene género, edad, municipio, departamento, estrato, discapacidad ni fecha de nacimiento. No se imputan valores: se crean dimensiones “No informado” y se documenta la ruta de integración (SOFIA Plus / matrícula / caracterización).
    </div>
    <div class="grid grid-2">
      <div class="card">
        <h3>Tipo de documento como proxy etario</h3>
        <div class="hint">TI ≈ menor de edad; CC ≈ adulto; PPT/CE ≈ extranjero. Es un proxy, no edad exacta.</div>
        <div class="chart-wrap"><canvas id="ch-documentos"></canvas></div>
      </div>
      <div class="card">
        <h3>Calidad de contacto</h3>
        <div class="hint">Celular válido (10 dígitos, inicia en 3) y correo con formato válido</div>
        <div class="two-col-list" id="contacto-kpis"></div>
        <div class="notice blue">El correo tiene 0 errores de formato, pero 208 matrículas no tienen celular y 20 tienen celular inválido. 228 quedan sin contacto completo.</div>
      </div>
    </div>
    <div class="grid grid-2" style="margin-top:14px">
      <div class="card">
        <h3>Contacto incompleto por programa</h3>
        <div class="hint">% de matrículas sin celular válido o correo válido</div>
        <div class="chart-wrap tall"><canvas id="ch-contacto-prog"></canvas></div>
      </div>
      <div class="card">
        <h3>Dominios de correo más frecuentes</h3>
        <div class="hint">Solo se usa el dominio; no se publica el correo completo</div>
        <div class="table-wrap" style="max-height:330px"><table id="tb-dominios"></table></div>
      </div>
    </div>
    <div class="section-title"><h2>Ruta de integración de dimensiones faltantes</h2><p>Qué pedir y para qué</p></div>
    <div class="table-wrap" style="max-height:none">
      <table>
        <thead><tr><th>Dimensión</th><th>Estado actual</th><th>Fuente sugerida</th><th>Uso analítico</th></tr></thead>
        <tbody>
          <tr><td>Género</td><td><span class="badge Medio">No informado</span></td><td>SOFIA Plus / caracterización</td><td>Brechas de permanencia y focalización</td></tr>
          <tr><td>Edad / fecha de nacimiento</td><td><span class="badge Medio">Proxy TI/CC</span></td><td>SOFIA Plus / registro de matrícula</td><td>Riesgo por ciclo de vida; validar proxy</td></tr>
          <tr><td>Municipio / departamento</td><td><span class="badge Medio">No informado</span></td><td>SOFIA Plus / dirección</td><td>Movilidad, ruralidad, distancia al centro</td></tr>
          <tr><td>Fecha de matrícula / periodo</td><td><span class="badge Crítico">Ausente</span></td><td>Matrícula / calendario académico</td><td>Series de tiempo, cohortes reales, pronóstico</td></tr>
          <tr><td>Fecha y motivo de retiro</td><td><span class="badge Crítico">Ausente</span></td><td>Novedades / SOFIA Plus</td><td>Supervivencia, causas, alerta temprana</td></tr>
          <tr><td>Certificación / egreso</td><td><span class="badge Crítico">Ausente</span></td><td>Certificación / SOFIA Plus</td><td>Tasa de titulación y eficiencia</td></tr>
          <tr><td>Centro / regional</td><td><span class="badge Medio">No informado</span></td><td>Ficha / SOFIA Plus</td><td>Comparación entre centros y regionales</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- PROGRAMAS -->
  <section class="tab-panel" id="tab-programas">
    <div class="grid grid-2">
      <div class="card">
        <h3>Participación y concentración</h3>
        <div class="hint">Pareto de matrícula por programa</div>
        <div class="chart-wrap"><canvas id="ch-pareto"></canvas></div>
      </div>
      <div class="card">
        <h3>Tasa de pérdida por programa</h3>
        <div class="hint">Barras: tasa observada. La tabla incluye IC 95% y tasa ajustada EB.</div>
        <div class="chart-wrap"><canvas id="ch-prog-rate"></canvas></div>
      </div>
    </div>
    <div class="section-title"><h2>Ranking de programas</h2><p>Ordenado por tasa ajustada empirical Bayes; los tamaños pequeños se contraen hacia la media</p></div>
    <div class="table-wrap"><table id="tb-programas"></table></div>
    <div class="notice blue" style="margin-top:12px">
      <strong>Lectura correcta:</strong> un programa con 0% de pérdida y 14–26 matrículas no es “el mejor” de forma concluyente: su IC 95% llega a 13–18%. Los programas grandes tienen estimaciones más estables. No ordenar por tasa puntual sin mirar el intervalo y el tamaño.
    </div>
  </section>

  <!-- FICHAS -->
  <section class="tab-panel" id="tab-fichas">
    <div class="grid grid-2">
      <div class="card">
        <h3>Mapa de fichas: tamaño vs pérdida</h3>
        <div class="hint">Cada punto es una ficha. Color = nivel de riesgo. Línea = tasa global.</div>
        <div class="chart-wrap tall"><canvas id="ch-fichas-scatter"></canvas></div>
      </div>
      <div class="card">
        <h3>Distribución de tasas por ficha</h3>
        <div class="hint">Media 27,3% · mediana 26,8% · desviación 19,7 pp · rango 0–62,1%</div>
        <div class="chart-wrap tall"><canvas id="ch-fichas-hist"></canvas></div>
      </div>
    </div>
    <div class="section-title"><h2>Detalle de fichas</h2><p>Filtros globales aplicados · orden por ranking de riesgo</p></div>
    <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
      <button class="btn ghost small" id="btn-fichas-csv">Descargar CSV de fichas</button>
      <span class="small" id="fichas-count"></span>
    </div>
    <div class="table-wrap"><table id="tb-fichas"></table></div>
  </section>

  <!-- TEMPORAL -->
  <section class="tab-panel" id="tab-temporal">
    <div class="notice">
      <strong>El prefijo de ficha NO es un año calendario.</strong> La fuente no tiene fecha de matrícula, inicio de ficha ni periodo. Se usa el prefijo (314, 317, …, 358) como proxy de generación/antigüedad. La tendencia es descriptiva y no permite afirmar que “la deserción bajó en 2025” ni proyectar por calendario.
    </div>
    <div class="card">
      <h3>Volumen y tasa de pérdida por generación (proxy)</h3>
      <div class="hint">Barras = matrículas; línea = tasa de pérdida. Orden = prefijo de ficha.</div>
      <div class="chart-wrap tall"><canvas id="ch-generaciones"></canvas></div>
    </div>
    <div class="grid grid-2" style="margin-top:14px">
      <div class="card">
        <h3>Evidencia de tendencia</h3>
        <div class="two-col-list" id="tendencia-stats"></div>
        <div class="notice blue" style="margin-bottom:0">Cochran-Armitage y Spearman usan el orden del prefijo, no fechas. La caída es compatible con cohortes más jóvenes que aún no acumulan pérdidas; también podría reflejar cambios de matrícula. No hay identificación causal.</div>
      </div>
      <div class="card">
        <h3>Lectura de cohortes</h3>
        <p class="small" style="margin-top:0">Las generaciones 314–340 son las más maduras (43,2% de pérdida agregada). Las generaciones 345–358 tienen 0% observado, consistente con cohortes recién iniciadas. La proyección de permanencia lleva a las cohortes jóvenes hacia un plateau, no a una fecha futura.</p>
        <div class="two-col-list" id="cohorte-stats"></div>
      </div>
    </div>
    <div class="section-title"><h2>Tabla de generaciones</h2><p>Agregación por prefijo de ficha</p></div>
    <div class="table-wrap"><table id="tb-generaciones"></table></div>
  </section>

  <!-- RIESGOS -->
  <section class="tab-panel" id="tab-riesgos">
    <div class="grid grid-2">
      <div class="card">
        <h3>Cómo se calcula el semáforo</h3>
        <p class="small" style="margin-top:0">El índice es el <b>percentil de la tasa de pérdida ajustada por empirical Bayes</b> (prior k=10). No suma contacto incompleto: esa variable está confundida con cohortes nuevas y se reporta aparte como alerta de contactabilidad.</p>
        <div class="two-col-list">
          <div><b>Bajo</b><br>Percentil &lt; 50 · monitoreo rutinario</div>
          <div><b>Medio</b><br>Percentil 50–75 · seguimiento mensual</div>
          <div><b>Alto</b><br>Percentil 75–90 · plan de acción 30 días</div>
          <div><b>Crítico</b><br>Percentil ≥ 90 · comité académico 8 días</div>
        </div>
        <div class="notice blue">La probabilidad por ficha es la media posterior beta-binomial con IC 95% creíble. No es una probabilidad frecuentista ni un pronóstico validado temporalmente.</div>
      </div>
      <div class="card">
        <h3>Validación descriptiva del semáforo</h3>
        <div class="hint">Tasa de pérdida observada por banda (todas las fichas)</div>
        <div class="chart-wrap"><canvas id="ch-validacion"></canvas></div>
        <div class="table-wrap" style="max-height:none;margin-top:8px"><table id="tb-validacion"></table></div>
      </div>
    </div>
    <div class="section-title"><h2>Fichas críticas: intervención inmediata</h2><p>6 fichas · 206 matrículas · 116 pérdidas</p></div>
    <div class="critical-grid" id="critical-cards-2"></div>
    <div class="section-title"><h2>Todas las fichas</h2><p>Ordenadas por ranking de riesgo · incluye probabilidad posterior e IC</p></div>
    <div class="table-wrap"><table id="tb-fichas-riesgo"></table></div>
  </section>

  <!-- PREDICTIVO -->
  <section class="tab-panel" id="tab-predictivo">
    <div class="notice red">
      <strong>Uso responsable.</strong> Este modelo se entrenó con un solo snapshot y sin etiquetas históricas. Aprende diferencias estructurales entre fichas/programas; <b>no predice el comportamiento individual</b> (AUC individual 0,47). No usar para negar cupos, sancionar ni estigmatizar. Es apoyo de priorización para coordinación académica.
    </div>
    <div class="kpi-grid" id="model-kpis"></div>
    <div class="grid grid-2">
      <div class="card">
        <h3>Calibración del modelo</h3>
        <div class="hint">Predicciones out-of-fold, validación agrupada por ficha (5 folds)</div>
        <div class="chart-wrap"><canvas id="ch-calibracion"></canvas></div>
      </div>
      <div class="card">
        <h3>Distribución de scores</h3>
        <div class="hint">Score estructural de pérdida (filtro actual). Corte de alerta alta: percentil 90.</div>
        <div class="chart-wrap"><canvas id="ch-hist-prob"></canvas></div>
      </div>
    </div>
    <div class="section-title"><h2>Probabilidad de pérdida por ficha</h2><p>Media posterior beta-binomial e IC 95% · top 15</p></div>
    <div class="grid grid-2">
      <div class="card"><div class="chart-wrap tall"><canvas id="ch-prob-fichas"></canvas></div></div>
      <div class="card"><div class="table-wrap" style="max-height:430px"><table id="tb-prob-fichas"></table></div></div>
    </div>
    <div class="section-title"><h2>Proyección de permanencia por escenarios</h2><p>No es pronóstico calendario ni de nueva matrícula</p></div>
    <div class="grid grid-2">
      <div class="card">
        <div class="chart-wrap"><canvas id="ch-proyeccion"></canvas></div>
        <div class="notice" style="margin-bottom:0">Supuesto base: las cohortes maduras (prefijos 314–340) alcanzan 43,2% de pérdida; cada programa se suaviza con k=50. Optimista = −7 pp; pesimista = +7 pp. La población vinculada actual es 1.144.</div>
      </div>
      <div class="card">
        <h3>Pronóstico de nueva matrícula</h3>
        <div class="notice red" style="margin-top:0"><strong>No estimable con la fuente actual.</strong> No hay serie temporal, fecha/periodo de matrícula ni cupos. Cualquier cifra de “matrícula futura” sería inventada.</div>
        <p class="small"><b>Para habilitarlo se requiere:</b></p>
        <ul class="small" style="margin-top:0;padding-left:18px">
          <li>Fecha o periodo de matrícula</li>
          <li>Fecha de inicio/fin de ficha</li>
          <li>Cupos ofertados y matriculados por periodo</li>
          <li>Meta de admisión y capacidad instalada</li>
          <li>Fecha y motivo de retiro/cancelación</li>
        </ul>
        <div class="table-wrap" style="max-height:none"><table id="tb-proy-prog"></table></div>
      </div>
    </div>
    <div class="section-title"><h2>Lista de priorización individual</h2><p>Score estructural + ficha + contacto · sin nombres ni documentos · top 100</p></div>
    <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
      <button class="btn ghost small" id="btn-alertas-csv">Descargar CSV de alertas</button>
      <span class="small" id="alertas-count"></span>
    </div>
    <div class="table-wrap"><table id="tb-alertas"></table></div>
    <div class="section-title"><h2>Variables del modelo</h2><p>Odds ratios interpretables con IC 95% · el programa tiene categorías inestables por tamaños pequeños</p></div>
    <div class="table-wrap" style="max-height:420px"><table id="tb-coeficientes"></table></div>
    <div class="notice blue" style="margin-top:12px">
      <strong>Limitaciones:</strong> un solo snapshot; 56 fichas; sin validación temporal; AUC 0,73 (IC 0,67–0,78) pero calibración imperfecta (ECE 0,048; pendiente 0,72); variables individuales sin señal. La proyección supone convergencia al plateau de cohortes maduras. Ver <code>docs/05_metodologia_predictiva.md</code>.
    </div>
  </section>

  <div class="footer">
    <div>Fuente: 56 reportes de ficha `.xls` · Centro ASTIN · snapshot 2026-10-19 · 1.592 matrículas · 1.583 aprendices únicos.</div>
    <div>Diseño basado en el Manual de Identidad Corporativa SENA 2024 · Work Sans / Calibri · logos no incluidos.</div>
  </div>
</main>

<script>__CHARTJS__</script>
<script>
const DATA = __DATA__;
const COLORS = {green:"#39A900", dark:"#00304D", red:"#C62828", orange:"#EF6C00", yellow:"#FDC300", teal:"#007832", violet:"#71277A", sky:"#50E5F9", grey:"#78909C", line:"#DDE7EC"};
const RISK_COLOR = {"Bajo":"#39A900","Medio":"#FDC300","Alto":"#EF6C00","Crítico":"#C62828"};
const charts = {};
Chart.defaults.font.family = '"Work Sans",Calibri,"Segoe UI",Roboto,Helvetica,Arial,sans-serif';
Chart.defaults.color = "#4A5C68";
Chart.defaults.borderColor = "#E6EEF2";

const state = {tab:"resumen", programa:"", jornada:"", riesgo:"", q:""};
const fmtNum = n => new Intl.NumberFormat("es-CO").format(Math.round(n));
const fmtPct = (x,d=1) => (Number(x)*100).toLocaleString("es-CO",{minimumFractionDigits:d,maximumFractionDigits:d})+"%";
const fmtPP = (x,d=1) => (Number(x)*100).toLocaleString("es-CO",{minimumFractionDigits:d,maximumFractionDigits:d})+" pp";
const esc = s => String(s??"").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const shortProg = id => (DATA.programas.find(p=>p.id===id)||{}).corto || id;
const progName = id => (DATA.programas.find(p=>p.id===id)||{}).nombre || id;
const fichaById = id => DATA.fichas.find(f=>f.id===id);
const pctColor = x => x>=0.5?"danger":x>=0.3?"warn":"";
const badge = x => `<span class="badge ${esc(x)}">${esc(x)}</span>`;
const probBar = x => `<div class="mini"><div class="mini-bar"><span class="${pctColor(x)}" style="width:${Math.min(100,x*100)}%"></span></div><b class="num">${fmtPct(x,1)}</b></div>`;

function destroy(id){ if(charts[id]){ charts[id].destroy(); delete charts[id]; } }
function make(id, cfg){ destroy(id); const el=document.getElementById(id); if(!el) return; charts[id]=new Chart(el.getContext("2d"), cfg); }

function filteredRows(){
  return DATA.rows.filter(r =>
    (!state.programa || r.prog===state.programa) &&
    (!state.jornada || r.jorn===state.jornada) &&
    (!state.riesgo || r.riesgoFicha===state.riesgo) &&
    (!state.q || r.ficha.includes(state.q))
  );
}
function uniqueFichas(rows){
  const m = new Map();
  rows.forEach(r=>{ if(!m.has(r.ficha)) m.set(r.ficha, fichaById(r.ficha)); });
  return [...m.values()].filter(Boolean);
}
function aggregate(rows){
  const n=rows.length, perd=rows.reduce((a,r)=>a+r.perdida,0), act=rows.reduce((a,r)=>a+r.activo,0);
  const cont=rows.filter(r=>!r.contacto).length;
  const fs=uniqueFichas(rows);
  return {n,perd,act,cont,tasa:n?perd/n:0,fichas:fs.length,criticas:fs.filter(f=>f.nivel==="Crítico").length,
          altas:rows.filter(r=>r.alerta==="Alto").length, inmediatas:rows.filter(r=>r.prioridad==="Inmediata").length};
}
function wilson(k,n,z=1.96){
  if(!n) return [0,0];
  const p=k/n, den=1+z*z/n, c=(p+z*z/(2*n))/den;
  const m=z*Math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;
  return [Math.max(0,c-m),Math.min(1,c+m)];
}
function groupBy(rows,key){
  const m=new Map();
  rows.forEach(r=>{ if(!m.has(r[key])) m.set(r[key],[]); m.get(r[key]).push(r); });
  return m;
}

function renderKpis(){
  const a=aggregate(filteredRows());
  const items=[
    ["Matrículas",fmtNum(a.n),"Registros en el filtro actual",""],
    ["Pérdidas",fmtNum(a.perd),fmtPct(a.n?a.perd/a.n:0)+" del filtro","red"],
    ["Tasa de pérdida",fmtPct(a.tasa),"IC 95% global: 25,4%–29,8%","red"],
    ["Fichas críticas",fmtNum(a.criticas),"De "+fmtNum(a.fichas)+" fichas en el filtro","orange"],
    ["Aprendices activos",fmtNum(a.act),fmtPct(a.n?a.act/a.n:0)+" de las matrículas",""],
    ["Contacto incompleto",fmtNum(a.cont),fmtPct(a.n?a.cont/a.n:0)+" sin celular/correo válido","yellow"],
    ["Alertas altas",fmtNum(a.altas),"Score estructural ≥ percentil 90","teal"],
    ["Prioridad inmediata",fmtNum(a.inmediatas),"Ficha crítica + señal/contacto","red"]
  ];
  document.getElementById("kpis").innerHTML=items.map(([l,v,s,c])=>`<div class="kpi ${c}"><div class="label">${l}</div><div class="value">${v}</div><div class="sub">${s}</div></div>`).join("");
  document.getElementById("filter-count").textContent=`${fmtNum(a.n)} matrículas · ${fmtNum(a.fichas)} fichas`;
  document.getElementById("pill-matriculas").textContent=`${fmtNum(a.n)} matrículas`;
  document.getElementById("pill-perdida").textContent=`${fmtPct(a.tasa)} pérdida`;
}

function renderResumen(){
  const rows=filteredRows(); const a=aggregate(rows);
  // Estados
  const byEstado=new Map(); rows.forEach(r=>byEstado.set(r.estado,(byEstado.get(r.estado)||0)+1));
  const estOrder=DATA.estados.map(e=>e.estado).filter(e=>byEstado.has(e));
  make("ch-estados",{type:"doughnut",data:{labels:estOrder,datasets:[{data:estOrder.map(e=>byEstado.get(e)),backgroundColor:estOrder.map(e=>(DATA.estados.find(x=>x.estado===e)||{}).color||COLORS.grey),borderWidth:2,borderColor:"#fff"}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:"62%",plugins:{legend:{position:"bottom",labels:{boxWidth:11,font:{size:10.5}}},tooltip:{callbacks:{label:c=>` ${c.label}: ${fmtNum(c.raw)} (${fmtPct(c.raw/rows.length)})`}}}}});
  // Riesgo fichas
  const fs=uniqueFichas(rows); const levels=["Bajo","Medio","Alto","Crítico"];
  const counts=levels.map(l=>fs.filter(f=>f.nivel===l).length);
  make("ch-riesgo",{type:"bar",data:{labels:levels,datasets:[{data:counts,backgroundColor:levels.map(l=>RISK_COLOR[l]),borderRadius:6,barPercentage:.62}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fmtNum(c.raw)} fichas`}}},scales:{y:{beginAtZero:true,ticks:{precision:0},grid:{color:"#EDF2F4"}},x:{grid:{display:false}}}}});
  // Criticas
  const crit=fs.filter(f=>f.nivel==="Crítico").sort((a,b)=>b.prob-a.prob);
  document.getElementById("critical-cards").innerHTML=crit.map(f=>`
    <div class="critical"><h4>Ficha ${esc(f.id)}</h4><div class="prog">${esc(shortProg(f.prog))} · ${esc(f.jorn)} · ${esc(f.gen)}</div>
    <div class="rate">${fmtPct(f.tasa)}</div><div class="meta">${f.perdidas}/${f.n} pérdidas · prob. posterior ${fmtPct(f.prob)} [${fmtPct(f.icInf)}–${fmtPct(f.icSup)}]</div>
    <div style="margin-top:7px">${badge(f.nivel)} <span class="tag">${esc(f.prioridad)}</span> ${f.alertaSec?`<span class="tag">${esc(f.alertaSec)}</span>`:""}</div></div>`).join("") || `<div class="card">Sin fichas críticas en el filtro.</div>`;
}

function renderDemografia(){
  const rows=filteredRows();
  const byTipo=new Map(); rows.forEach(r=>byTipo.set(r.tipo,(byTipo.get(r.tipo)||0)+1));
  const labels=[...byTipo.keys()].sort((a,b)=>byTipo.get(b)-byTipo.get(a));
  const colors={"CC":"#00304D","TI":"#39A900","PPT":"#EF6C00","CE":"#78909C"};
  make("ch-documentos",{type:"doughnut",data:{labels:labels.map(x=>x==="CC"?"CC (adulto)":x==="TI"?"TI (menor)":x),datasets:[{data:labels.map(x=>byTipo.get(x)),backgroundColor:labels.map(x=>colors[x]||COLORS.grey),borderWidth:2,borderColor:"#fff"}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:"58%",plugins:{legend:{position:"bottom",labels:{boxWidth:11}},tooltip:{callbacks:{label:c=>` ${fmtNum(c.raw)} (${fmtPct(c.raw/rows.length)})`}}}}});
  const q=DATA.stats.calidad;
  document.getElementById("contacto-kpis").innerHTML=[
    ["Sin celular",`${fmtNum(q.sin_celular)} (${fmtPct(q.sin_celular_pct)})`],
    ["Celular inválido",`${fmtNum(q.celular_invalido)} (${fmtPct(q.celular_invalido_pct)})`],
    ["Correo inválido",`${fmtNum(q.email_invalido)} (0,0%)`],
    ["Contacto incompleto",`${fmtNum(q.contacto_incompleto)} (${fmtPct(q.contacto_incompleto_pct)})`],
    ["Aprendices únicos",fmtNum(q.aprendices_unicos)],
    ["Multi-ficha",`${fmtNum(q.aprendices_multi_ficha)} (${fmtNum(q.matriculas_multi_ficha)} matrículas)`]
  ].map(([k,v])=>`<div><b>${k}</b><br>${v}</div>`).join("");
  // Contacto por programa
  const byProg=groupBy(rows,"prog");
  const arr=[...byProg.entries()].map(([id,rs])=>({id,n:rs.length,inc:rs.filter(r=>!r.contacto).length/rs.length})).sort((a,b)=>b.inc-a.inc);
  make("ch-contacto-prog",{type:"bar",data:{labels:arr.map(x=>shortProg(x.id)),datasets:[{data:arr.map(x=>x.inc*100),backgroundColor:arr.map(x=>x.inc>=0.3?COLORS.orange:x.inc>=0.15?COLORS.yellow:COLORS.green),borderRadius:5,barPercentage:.72}]},
    options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw.toFixed(1)}% (${fmtNum(arr[c.dataIndex].inc*arr[c.dataIndex].n)} de ${fmtNum(arr[c.dataIndex].n)})`}}},
      scales:{x:{beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
  // Dominios
  const dom=new Map(); rows.forEach(r=>dom.set(r.dominio,(dom.get(r.dominio)||0)+1));
  const domArr=[...dom.entries()].sort((a,b)=>b[1]-a[1]);
  document.getElementById("tb-dominios").innerHTML=`<thead><tr><th>Dominio</th><th class="num">Matrículas</th><th class="num">%</th></tr></thead><tbody>${domArr.map(([d,n])=>`<tr><td>${esc(d)}</td><td class="num">${fmtNum(n)}</td><td class="num">${fmtPct(n/rows.length)}</td></tr>`).join("")}</tbody>`;
}

function renderProgramas(){
  const rows=filteredRows(); const by=groupBy(rows,"prog");
  const arr=[...by.entries()].map(([id,rs])=>{
    const n=rs.length, perd=rs.reduce((a,r)=>a+r.perdida,0), act=rs.reduce((a,r)=>a+r.activo,0);
    const [lo,hi]=wilson(perd,n);
    return {id,n,perd,act,tasa:n?perd/n:0,lo,hi,fichas:new Set(rs.map(r=>r.ficha)).size};
  });
  // Pareto
  const par=[...arr].sort((a,b)=>b.n-a.n); let cum=0; const cumArr=par.map(x=>{cum+=x.n; return cum/rows.length*100;});
  make("ch-pareto",{type:"bar",data:{labels:par.map(x=>shortProg(x.id)),datasets:[
      {type:"bar",data:par.map(x=>x.n),backgroundColor:"#B9DDA8",borderRadius:4,order:2,label:"Matrículas"},
      {type:"line",data:cumArr,borderColor:COLORS.dark,backgroundColor:COLORS.dark,pointRadius:2.5,borderWidth:2,tension:.15,yAxisID:"y1",order:1,label:"% acumulado"}
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:11}},tooltip:{callbacks:{label:c=>c.dataset.type==="line"?` Acumulado: ${c.raw.toFixed(1)}%`:` ${fmtNum(c.raw)} matrículas`}}},
    scales:{x:{ticks:{font:{size:9},maxRotation:50,minRotation:30},grid:{display:false}},y:{beginAtZero:true,title:{display:true,text:"Matrículas"},grid:{color:"#EDF2F4"}},y1:{position:"right",beginAtZero:true,max:105,ticks:{callback:v=>v+"%"},grid:{display:false}}}}});
  // Rate
  const rateArr=[...arr].sort((a,b)=>a.tasa-b.tasa);
  make("ch-prog-rate",{type:"bar",data:{labels:rateArr.map(x=>shortProg(x.id)),datasets:[{data:rateArr.map(x=>x.tasa*100),backgroundColor:rateArr.map(x=>x.tasa>=DATA.meta.tasa?COLORS.red:COLORS.green),borderRadius:5,barPercentage:.72}]},
    options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw.toFixed(1)}% (${fmtNum(rateArr[c.dataIndex].perd)}/${fmtNum(rateArr[c.dataIndex].n)})`}}},
      scales:{x:{beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}},y:{grid:{display:false},ticks:{font:{size:9.5}}}}}});
  // Tabla
  const order=[...arr].sort((a,b)=>b.tasa-a.tasa);
  document.getElementById("tb-programas").innerHTML=`<thead><tr><th>#</th><th>Programa</th><th>Línea</th><th>Nivel</th><th class="num">Fichas</th><th class="num">Matrículas</th><th class="num">Pérdidas</th><th class="num">Tasa</th><th>IC 95%</th><th class="num">Activos</th></tr></thead><tbody>${order.map((x,i)=>`<tr><td class="num">${i+1}</td><td><b>${esc(progName(x.id))}</b></td><td>${esc((DATA.programas.find(p=>p.id===x.id)||{}).linea||"")}</td><td>${esc((DATA.programas.find(p=>p.id===x.id)||{}).nivel||"")}</td><td class="num">${x.fichas}</td><td class="num">${fmtNum(x.n)}</td><td class="num">${fmtNum(x.perd)}</td><td class="num"><b>${fmtPct(x.tasa)}</b></td><td class="small nowrap">${fmtPct(x.lo)}–${fmtPct(x.hi)}</td><td class="num">${fmtNum(x.act)}</td></tr>`).join("")}</tbody>`;
}

function renderFichas(){
  const rows=filteredRows(); const fs=uniqueFichas(rows).sort((a,b)=>a.ranking-b.ranking);
  const scatter=fs.map(f=>({x:f.n,y:f.tasa*100,f}));
  make("ch-fichas-scatter",{type:"scatter",data:{datasets:["Bajo","Medio","Alto","Crítico"].map(l=>({label:l,data:scatter.filter(p=>p.f.nivel===l),backgroundColor:RISK_COLOR[l],borderColor:"#fff",borderWidth:.8,pointRadius:6,pointHoverRadius:8}))},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:10}},tooltip:{callbacks:{label:c=>{const f=c.raw.f; return [`Ficha ${f.id} · ${shortProg(f.prog)}`,`${f.n} matrículas · ${fmtPct(f.tasa)} pérdida · prob. ${fmtPct(f.prob)}`,f.nivel];}}}},
      scales:{x:{title:{display:true,text:"Matrículas en la ficha"},grid:{color:"#EDF2F4"}},y:{title:{display:true,text:"Tasa de pérdida (%)"},beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}}}}});
  // Histograma
  const bins=[0,10,20,30,40,50,60,70]; const hist=Array(bins.length-1).fill(0);
  fs.forEach(f=>{const v=f.tasa*100; for(let i=0;i<bins.length-1;i++){if(v>=bins[i]&&v<bins[i+1]){hist[i]++;break;} if(i===bins.length-2&&v>=bins[i])hist[i]++;}});
  make("ch-fichas-hist",{type:"bar",data:{labels:bins.slice(0,-1).map((b,i)=>`${b}–${bins[i+1]}%`),datasets:[{data:hist,backgroundColor:COLORS.dark,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw} fichas`}}},scales:{y:{beginAtZero:true,ticks:{precision:0},grid:{color:"#EDF2F4"}},x:{grid:{display:false}}}}});
  // Tabla
  document.getElementById("tb-fichas").innerHTML=`<thead><tr><th>Rank</th><th>Ficha</th><th>Programa</th><th>Jornada</th><th>Gen.</th><th class="num">n</th><th class="num">Pérdidas</th><th class="num">Tasa</th><th class="num">Prob.</th><th>Nivel</th><th>Prioridad</th><th>Alerta</th></tr></thead><tbody>${fs.map(f=>`<tr><td class="num">${f.ranking}</td><td><b>${esc(f.id)}</b></td><td>${esc(shortProg(f.prog))}</td><td>${esc(f.jorn)}</td><td>${esc(f.gen)}</td><td class="num">${f.n}</td><td class="num">${f.perdidas}</td><td class="num"><b>${fmtPct(f.tasa)}</b></td><td class="num">${fmtPct(f.prob)}</td><td>${badge(f.nivel)}</td><td>${badge(f.prioridad)}</td><td class="small">${esc(f.alerta)}${f.alertaSec?` · ${esc(f.alertaSec)}`:""}</td></tr>`).join("")}</tbody>`;
  document.getElementById("fichas-count").textContent=`${fs.length} fichas · ${fmtNum(rows.length)} matrículas`;
  window._fichasCsv=fs;
}

function renderTemporal(){
  const rows=filteredRows(); const by=groupBy(rows,"gen");
  const arr=DATA.generaciones.filter(g=>by.has(g.id)).map(g=>{
    const rs=by.get(g.id); return {...g,fichas:new Set(rs.map(r=>r.ficha)).size,n:rs.length,perdidas:rs.reduce((a,r)=>a+r.perdida,0),tasa:rs.length?rs.reduce((a,r)=>a+r.perdida,0)/rs.length:0};
  }).sort((a,b)=>a.orden-b.orden);
  make("ch-generaciones",{data:{labels:arr.map(g=>g.nombre),datasets:[
    {type:"bar",label:"Matrículas",data:arr.map(g=>g.n),backgroundColor:"#CFE8C6",borderRadius:4,yAxisID:"y"},
    {type:"line",label:"Tasa de pérdida",data:arr.map(g=>g.tasa*100),borderColor:COLORS.red,backgroundColor:COLORS.red,pointRadius:3,borderWidth:2.2,tension:.18,yAxisID:"y1"}
  ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:11}},tooltip:{callbacks:{label:c=>c.dataset.type==="line"?` ${c.raw.toFixed(1)}% pérdida`:` ${fmtNum(c.raw)} matrículas`}}},
    scales:{x:{grid:{display:false},ticks:{font:{size:9}}},y:{beginAtZero:true,title:{display:true,text:"Matrículas"},grid:{color:"#EDF2F4"}},y1:{position:"right",beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{display:false}}}}});
  const t=DATA.stats.tendencia;
  document.getElementById("tendencia-stats").innerHTML=[
    ["Spearman orden vs tasa",`${t.spearman_orden_vs_tasa.rho.toFixed(3)} (p ${t.spearman_orden_vs_tasa.p<0.001?"< 0,001":t.spearman_orden_vs_tasa.p.toFixed(3)})`],
    ["Cochran-Armitage",`z = ${t.cochran_armitage.z.toFixed(2)} · p ${t.cochran_armitage.p_texto}`],
    ["Pendiente lineal",`${t.cochran_armitage.pendiente_pp_por_generacion.toFixed(1)} pp por prefijo`],
    ["Generaciones",`${DATA.generaciones.length} prefijos distintos`]
  ].map(([k,v])=>`<div><b>${k}</b><br>${v}</div>`).join("");
  document.getElementById("cohorte-stats").innerHTML=[
    ["Cohortes maduras","314–340 (8 prefijos)"],
    ["Pérdida agregada madura",fmtPct(DATA.modelo.proyeccion.supuestos.plateau_global)],
    ["Matrículas maduras",fmtNum(DATA.modelo.proyeccion.supuestos.plateau_global_n)],
    ["Cohortes jóvenes","345–358 (0% observado)"]
  ].map(([k,v])=>`<div><b>${k}</b><br>${v}</div>`).join("");
  document.getElementById("tb-generaciones").innerHTML=`<thead><tr><th>Generación</th><th class="num">Fichas</th><th class="num">Matrículas</th><th class="num">Pérdidas</th><th class="num">Tasa</th><th class="num">Proyección base</th></tr></thead><tbody>${arr.map(g=>{
    const p=DATA.proyeccion.porGeneracion.find(x=>x.GeneracionID===g.id);
    return `<tr><td><b>${esc(g.nombre)}</b></td><td class="num">${g.fichas}</td><td class="num">${fmtNum(g.n)}</td><td class="num">${fmtNum(g.perdidas)}</td><td class="num"><b>${fmtPct(g.tasa)}</b></td><td class="num">${p?fmtPct(p.tasa_proyectada):"—"}</td></tr>`;
  }).join("")}</tbody>`;
}

function renderRiesgos(){
  const rows=filteredRows(); const fs=uniqueFichas(rows);
  const bands=["Bajo","Medio","Alto","Crítico"];
  const val=bands.map(l=>{const rs=rows.filter(r=>r.riesgoFicha===l); const n=rs.length, p=rs.reduce((a,r)=>a+r.perdida,0); return {l,n,p,tasa:n?p/n:0,fichas:fs.filter(f=>f.nivel===l).length};});
  make("ch-validacion",{type:"bar",data:{labels:bands,datasets:[{data:val.map(x=>x.tasa*100),backgroundColor:bands.map(l=>RISK_COLOR[l]),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.raw.toFixed(1)}% · ${fmtNum(val[c.dataIndex].p)}/${fmtNum(val[c.dataIndex].n)}`}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}},x:{grid:{display:false}}}}});
  document.getElementById("tb-validacion").innerHTML=`<thead><tr><th>Banda</th><th class="num">Fichas</th><th class="num">n</th><th class="num">Pérdidas</th><th class="num">Tasa</th></tr></thead><tbody>${val.map(x=>`<tr><td>${badge(x.l)}</td><td class="num">${x.fichas}</td><td class="num">${fmtNum(x.n)}</td><td class="num">${fmtNum(x.p)}</td><td class="num"><b>${fmtPct(x.tasa)}</b></td></tr>`).join("")}</tbody>`;
  const crit=fs.filter(f=>f.nivel==="Crítico").sort((a,b)=>b.prob-a.prob);
  document.getElementById("critical-cards-2").innerHTML=crit.map(f=>`
    <div class="critical"><h4>Ficha ${esc(f.id)}</h4><div class="prog">${esc(shortProg(f.prog))} · ${esc(f.jorn)} · ${esc(f.gen)}</div>
    <div class="rate">${fmtPct(f.tasa)}</div><div class="meta">${f.perdidas}/${f.n} pérdidas · prob. ${fmtPct(f.prob)} [${fmtPct(f.icInf)}–${fmtPct(f.icSup)}]</div>
    <div style="margin-top:7px">${badge(f.nivel)} <span class="tag">${esc(f.prioridad)}</span> ${f.alertaSec?`<span class="tag">${esc(f.alertaSec)}</span>`:""}</div></div>`).join("");
  const all=fs.sort((a,b)=>a.ranking-b.ranking);
  document.getElementById("tb-fichas-riesgo").innerHTML=`<thead><tr><th>Rank</th><th>Ficha</th><th>Programa</th><th>Jornada</th><th class="num">n</th><th class="num">Tasa</th><th class="num">Prob.</th><th>IC 95%</th><th class="num">P(&gt;30%)</th><th>Nivel</th><th>Confiab.</th></tr></thead><tbody>${all.map(f=>`<tr><td class="num">${f.ranking}</td><td><b>${esc(f.id)}</b></td><td>${esc(shortProg(f.prog))}</td><td>${esc(f.jorn)}</td><td class="num">${f.n}</td><td class="num"><b>${fmtPct(f.tasa)}</b></td><td class="num">${fmtPct(f.prob)}</td><td class="small nowrap">${fmtPct(f.icInf)}–${fmtPct(f.icSup)}</td><td class="num">${fmtPct(f.prob30)}</td><td>${badge(f.nivel)}</td><td class="small">${esc(f.conf)}</td></tr>`).join("")}</tbody>`;
}

function renderPredictivo(){
  const m=DATA.modelo.principal, ind=DATA.modelo.individual, d=DATA.modelo.distribucion;
  document.getElementById("model-kpis").innerHTML=[
    ["AUC agrupado",m.auc.toFixed(3),"IC 95% "+m.auc_ic95_bootstrap_ficha.ic95_inf.toFixed(2)+"–"+m.auc_ic95_bootstrap_ficha.ic95_sup.toFixed(2),""],
    ["Brier",m.brier.toFixed(3),"Baseline "+m.brier_base.toFixed(3)+" (tasa base)","teal"],
    ["ECE",m.ece.toFixed(3),"Error de calibración (0=perfecto)","yellow"],
    ["AUC individual",ind.auc.toFixed(3),"Sin señal personal: ~azar","red"]
  ].map(([l,v,s,c])=>`<div class="kpi ${c}"><div class="label">${l}</div><div class="value">${v}</div><div class="sub">${s}</div></div>`).join("");
  // Calibracion
  const cal=m.calibracion_deciles;
  make("ch-calibracion",{type:"line",data:{labels:cal.map((_,i)=>`D${i+1}`),datasets:[
    {label:"Modelo",data:cal.map(c=>c.tasa_observada*100),borderColor:COLORS.dark,backgroundColor:COLORS.dark,pointRadius:3,tension:.15},
    {label:"Predicción media",data:cal.map(c=>c.prob_media*100),borderColor:COLORS.green,backgroundColor:COLORS.green,pointRadius:3,borderDash:[5,4],tension:.15}
  ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom",labels:{boxWidth:11}},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${c.raw.toFixed(1)}%`}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}},x:{grid:{display:false}}}}});
  // Histograma scores
  const rows=filteredRows(); const bins=Array(10).fill(0);
  rows.forEach(r=>{const i=Math.min(9,Math.floor(r.prob*10)); bins[i]++;});
  make("ch-hist-prob",{type:"bar",data:{labels:bins.map((_,i)=>`${i*10}–${i*10+10}%`),datasets:[{data:bins,backgroundColor:bins.map((_,i)=>i>=9?COLORS.red:i>=5?COLORS.orange:COLORS.green),borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${fmtNum(c.raw)} matrículas`}}},scales:{y:{beginAtZero:true,ticks:{precision:0},grid:{color:"#EDF2F4"}},x:{grid:{display:false},ticks:{font:{size:9}}}}}});
  // Prob fichas top 15
  const fs=uniqueFichas(rows).sort((a,b)=>b.prob-a.prob).slice(0,15);
  make("ch-prob-fichas",{type:"bar",data:{labels:fs.map(f=>f.id),datasets:[{data:fs.map(f=>f.prob*100),backgroundColor:fs.map(f=>RISK_COLOR[f.nivel]),borderRadius:4}]},
    options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const f=fs[c.dataIndex];return ` ${fmtPct(f.prob)} [${fmtPct(f.icInf)}–${fmtPct(f.icSup)}] · n=${f.n}`;}}}},
      scales:{x:{beginAtZero:true,ticks:{callback:v=>v+"%"},grid:{color:"#EDF2F4"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});
  document.getElementById("tb-prob-fichas").innerHTML=`<thead><tr><th>Ficha</th><th class="num">n</th><th class="num">Tasa</th><th class="num">Prob.</th><th>IC 95%</th><th>Nivel</th></tr></thead><tbody>${fs.map(f=>`<tr><td><b>${esc(f.id)}</b><br><span class="small">${esc(shortProg(f.prog))}</span></td><td class="num">${f.n}</td><td class="num">${fmtPct(f.tasa)}</td><td class="num"><b>${fmtPct(f.prob)}</b></td><td class="small nowrap">${fmtPct(f.icInf)}–${fmtPct(f.icSup)}</td><td>${badge(f.nivel)}</td></tr>`).join("")}</tbody>`;
  // Proyeccion
  const ps=DATA.proyeccion.resumen; const names=ps.map(x=>x.escenario);
  make("ch-proyeccion",{type:"bar",data:{labels:names,datasets:[{data:ps.map(x=>x.poblacion_proyectada),backgroundColor:[COLORS.green,COLORS.dark,COLORS.orange],borderRadius:6}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${fmtNum(c.raw)} vinculados · −${fmtNum(ps[c.dataIndex].perdida_adicional_esperada)} pérdidas adicionales`}}},scales:{y:{beginAtZero:true,max:1200,title:{display:true,text:"Población proyectada"},grid:{color:"#EDF2F4"}},x:{grid:{display:false}}}}});
  const pp=DATA.proyeccion.porPrograma.filter(x=>!state.programa||x.ProgramaID===state.programa);
  document.getElementById("tb-proy-prog").innerHTML=`<thead><tr><th>Programa</th><th class="num">Vinc.</th><th class="num">Pérd. adic.</th><th class="num">Proy.</th><th class="num">Tasa proy.</th></tr></thead><tbody>${pp.map(x=>`<tr><td>${esc(x.programa)}</td><td class="num">${fmtNum(x.poblacion_vinculada)}</td><td class="num">${fmtNum(x.perdida_adicional)}</td><td class="num">${fmtNum(x.poblacion_proyectada)}</td><td class="num"><b>${fmtPct(x.tasa_proyectada)}</b></td></tr>`).join("")}</tbody>`;
  // Alertas
  const alerts=rows.filter(r=>r.prioridad!=="Rutinaria").sort((a,b)=>b.prob-a.prob).slice(0,100);
  document.getElementById("tb-alertas").innerHTML=`<thead><tr><th>ID</th><th>Ficha</th><th>Programa</th><th>Jornada</th><th>Estado</th><th class="num">Prob.</th><th>Alerta</th><th>Prioridad</th><th>Motivo</th></tr></thead><tbody>${alerts.map(r=>`<tr><td class="small">${esc(r.id)}</td><td><b>${esc(r.ficha)}</b></td><td>${esc(shortProg(r.prog))}</td><td>${esc(r.jorn)}</td><td class="small">${esc(r.estado)}</td><td class="num">${fmtPct(r.prob)}</td><td>${badge(r.alerta)}</td><td>${badge(r.prioridad)}</td><td class="small">${esc(r.motivo)}</td></tr>`).join("")}</tbody>`;
  document.getElementById("alertas-count").textContent=`${alerts.length} mostradas · ${fmtNum(rows.filter(r=>r.prioridad!=="Rutinaria").length)} con prioridad en el filtro`;
  window._alertasCsv=rows.filter(r=>r.prioridad!=="Rutinaria").sort((a,b)=>b.prob-a.prob);
  // Coeficientes interpretables
  const sel=["num__GeneracionOrden","num__ContactoCompleto","num__TieneMultiplesFichas","num__TamanoFicha","num__TasaContactoIncompletoFicha","cat__Jornada_NOCTURNA","cat__TipoDocumento_TI","cat__TipoDocumento_PPT","cat__DominioGrupo_Gmail","cat__DominioGrupo_Hotmail/Outlook"];
  const cs=DATA.modelo.coeficientes.filter(c=>sel.includes(c.raw));
  document.getElementById("tb-coeficientes").innerHTML=`<thead><tr><th>Variable</th><th class="num">OR</th><th>IC 95%</th><th>Lectura</th></tr></thead><tbody>${cs.map(c=>`<tr><td>${esc(c.variable)}</td><td class="num"><b>${c.or.toFixed(2)}</b></td><td class="small nowrap">${c.or_ic95_inf.toFixed(2)}–${c.or_ic95_sup.toFixed(2)}</td><td class="small">${c.or>1?"Mayor odds de pérdida":"Menor odds de pérdida"} (asociación)</td></tr>`).join("")}</tbody>`;
}

function renderTab(tab){
  if(tab==="resumen") renderResumen();
  else if(tab==="demografia") renderDemografia();
  else if(tab==="programas") renderProgramas();
  else if(tab==="fichas") renderFichas();
  else if(tab==="temporal") renderTemporal();
  else if(tab==="riesgos") renderRiesgos();
  else if(tab==="predictivo") renderPredictivo();
}
function refresh(){
  renderKpis();
  renderTab(state.tab);
}

function downloadCSV(filename, rows, headers){
  const csv=[headers.join(",")].concat(rows.map(r=>headers.map(h=>{
    let v=r[h]??""; v=String(v).replace(/"/g,'""'); return `"${v}"`;
  }).join(","))).join("\n");
  const blob=new Blob(["\ufeff"+csv],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=filename; a.click(); URL.revokeObjectURL(a.href);
}

function init(){
  const progSel=document.getElementById("f-prog");
  DATA.programas.slice().sort((a,b)=>a.nombre.localeCompare(b.nombre)).forEach(p=>{
    const o=document.createElement("option"); o.value=p.id; o.textContent=p.nombre; progSel.appendChild(o);
  });
  progSel.addEventListener("change",e=>{state.programa=e.target.value;refresh();});
  document.getElementById("f-jorn").addEventListener("change",e=>{state.jornada=e.target.value;refresh();});
  document.getElementById("f-risk").addEventListener("change",e=>{state.riesgo=e.target.value;refresh();});
  document.getElementById("f-q").addEventListener("input",e=>{state.q=e.target.value.trim();refresh();});
  document.getElementById("btn-reset").addEventListener("click",()=>{
    state.programa="";state.jornada="";state.riesgo="";state.q="";
    progSel.value="";document.getElementById("f-jorn").value="";document.getElementById("f-risk").value="";document.getElementById("f-q").value="";
    refresh();
  });
  document.getElementById("btn-print").addEventListener("click",()=>window.print());
  document.getElementById("btn-fichas-csv").addEventListener("click",()=>{
    const rows=(window._fichasCsv||[]).map(f=>({FichaID:f.id,Programa:shortProg(f.prog),Jornada:f.jorn,NivelRiesgo:f.nivel,Matriculas:f.n,Perdidas:f.perdidas,TasaPerdida:f.tasa,ProbDesercion:f.prob,IC95Inf:f.icInf,IC95Sup:f.icSup,Prioridad:f.prioridad}));
    downloadCSV("fichas_riesgo.csv",rows,["FichaID","Programa","Jornada","NivelRiesgo","Matriculas","Perdidas","TasaPerdida","ProbDesercion","IC95Inf","IC95Sup","Prioridad"]);
  });
  document.getElementById("btn-alertas-csv").addEventListener("click",()=>{
    const rows=(window._alertasCsv||[]).map(r=>({AprendizID:r.id,FichaID:r.ficha,Programa:shortProg(r.prog),Jornada:r.jorn,Estado:r.estado,ProbPerdida:r.prob,NivelAlerta:r.alerta,Prioridad:r.prioridad,Motivo:r.motivo}));
    downloadCSV("alertas_priorizadas_sin_pii.csv",rows,["AprendizID","FichaID","Programa","Jornada","Estado","ProbPerdida","NivelAlerta","Prioridad","Motivo"]);
  });
  document.querySelectorAll(".tab").forEach(btn=>btn.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p=>p.classList.remove("active"));
    btn.classList.add("active");
    state.tab=btn.dataset.tab;
    document.getElementById("tab-"+state.tab).classList.add("active");
    renderTab(state.tab);
    window.scrollTo({top:0,behavior:"smooth"});
  }));
  document.querySelectorAll("[data-goto]").forEach(a=>a.addEventListener("click",e=>{
    e.preventDefault(); const t=a.dataset.goto;
    document.querySelector(`.tab[data-tab="${t}"]`)?.click();
  }));
  refresh();
}
document.addEventListener("DOMContentLoaded",init);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
