# -*- coding: utf-8 -*-
"""
FASE 2 - Construccion del modelo estrella (snapshot 2026-10-19).
Salidas: data/processed/*.csv y outputs/02_etl_resumen.json
"""
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "restricted" / "aprendices_crudos.json"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)
OUTPUTS = ROOT / "outputs"
REPORT_DATE = date(2026, 10, 19)


def read_rows():
    return json.loads(RAW.read_text(encoding="utf-8"))


def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def norm(value):
    text = clean(value).upper()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"),
                 ("Ü", "U"), ("Ñ", "N")]:
        text = text.replace(a, b)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def sha(text, n=12):
    return hashlib.sha1(text.encode("utf-8")).hexdigest().upper()[:n]


def write_csv(name, rows, columns):
    path = OUT / name
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
    return path


def pct(value, digits=4):
    return round(float(value), digits)


def percentile_rank(values):
    """Percentil 0-100 con promedio de rangos para empates."""
    n = len(values)
    if n <= 1:
        return {i: 50.0 for i in range(n)}
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return {i: 100.0 * ranks[i] / (n - 1) for i in range(n)}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


PROGRAMS = {
    "ALISTAMIENTO DE LABORATORIOS DE ANALISIS Y ENSAYOS PARA LA INDUSTRIA": {
        "id": "P01", "nombre": "Alistamiento de Laboratorios de Análisis y Ensayos para la Industria",
        "corto": "Alistamiento de Laboratorios", "linea": "Química y Laboratorio",
        "nivel": "Técnico", "nivel_fuente": "Inferido por nombre de programa"},
    "ANALISIS DE MATERIALES PARA LA INDUSTRIA": {
        "id": "P02", "nombre": "Análisis de Materiales para la Industria",
        "corto": "Análisis de Materiales", "linea": "Química y Laboratorio",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "APLICACION DE PROCEDIMIENTOS DE LABORATORIO QUIMICO": {
        "id": "P03", "nombre": "Aplicación de Procedimientos de Laboratorio Químico",
        "corto": "Procedimientos de Laboratorio", "linea": "Química y Laboratorio",
        "nivel": "Técnico", "nivel_fuente": "Inferido por nombre de programa"},
    "COORDINACION EN SISTEMAS INTEGRADOS DE GESTION": {
        "id": "P04", "nombre": "Coordinación en Sistemas Integrados de Gestión",
        "corto": "Sistemas Integrados de Gestión", "linea": "Gestión y Sistemas",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "DESARROLLO DE COMPONENTES MECANICOS": {
        "id": "P05", "nombre": "Desarrollo de Componentes Mecánicos",
        "corto": "Componentes Mecánicos", "linea": "Metalmecánica y Materiales",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "DESARROLLO Y MODELADO DE PRODUCTOS INDUSTRIALES": {
        "id": "P06", "nombre": "Desarrollo y Modelado de Productos Industriales",
        "corto": "Modelado de Productos", "linea": "Diseño y Manufactura",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "FABRICACION DE MOLDES Y TROQUELES": {
        "id": "P07", "nombre": "Fabricación de Moldes y Troqueles",
        "corto": "Moldes y Troqueles", "linea": "Metalmecánica y Materiales",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "FABRICACION DE PRODUCTOS PLASTICOS POR INYECCION Y SOPLADO": {
        "id": "P08", "nombre": "Fabricación de Productos Plásticos por Inyección y Soplado",
        "corto": "Productos Plásticos", "linea": "Plásticos y Polímeros",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "GESTION DE PROYECTOS DE DESARROLLO ECONOMICO Y SOCIAL": {
        "id": "P09", "nombre": "Gestión de Proyectos de Desarrollo Económico y Social",
        "corto": "Gestión de Proyectos", "linea": "Gestión y Sistemas",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "GESTION DE LA PRODUCCION INDUSTRIAL": {
        "id": "P10", "nombre": "Gestión de la Producción Industrial",
        "corto": "Producción Industrial", "linea": "Producción Industrial",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "MODELADO 3D PARA LA INDUSTRIA": {
        "id": "P11", "nombre": "Modelado 3D para la Industria",
        "corto": "Modelado 3D", "linea": "Diseño y Manufactura",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "MONITOREO AMBIENTAL": {
        "id": "P12", "nombre": "Monitoreo Ambiental",
        "corto": "Monitoreo Ambiental", "linea": "Ambiental",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "PROCESOS DE MANUFACTURA": {
        "id": "P13", "nombre": "Procesos de Manufactura (Baxter)",
        "corto": "Manufactura Baxter", "linea": "Metalmecánica y Materiales",
        "nivel": "Técnico", "nivel_fuente": "Explícito en nombre de archivo"},
    "QUIMICA APLICADA A LA INDUSTRIA": {
        "id": "P14", "nombre": "Química Aplicada a la Industria",
        "corto": "Química Aplicada", "linea": "Química y Laboratorio",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
    "TRANSFORMACION DE POLIMEROS POR INYECCION": {
        "id": "P15", "nombre": "Transformación de Polímeros por Inyección",
        "corto": "Transformación de Polímeros", "linea": "Plásticos y Polímeros",
        "nivel": "Tecnólogo", "nivel_fuente": "Inferido por nombre de programa"},
}

STATES = {
    "EN FORMACION": dict(id="E01", categoria="Activo", vinculado=1, activo=1, perdida=0,
                         cancelado=0, retirado=0, trasladado=0, suspendido=0, riesgo=0,
                         certificado=0, orden=1, color="#2E7D32",
                         definicion="Aprendiz con matrícula vigente y formación en curso."),
    "INDUCCION": dict(id="E02", categoria="Activo", vinculado=1, activo=1, perdida=0,
                      cancelado=0, retirado=0, trasladado=0, suspendido=0, riesgo=0,
                      certificado=0, orden=2, color="#00897B",
                      definicion="Aprendiz en etapa de inducción, matrícula vigente."),
    "CONDICIONADO": dict(id="E03", categoria="Activo en riesgo", vinculado=1, activo=1, perdida=0,
                         cancelado=0, retirado=0, trasladado=0, suspendido=0, riesgo=1,
                         certificado=0, orden=3, color="#F9A825",
                         definicion="Aprendiz con novedad académica o disciplinaria; requiere seguimiento."),
    "APLAZADO": dict(id="E04", categoria="Suspendido", vinculado=1, activo=0, perdida=0,
                     cancelado=0, retirado=0, trasladado=0, suspendido=1, riesgo=1,
                     certificado=0, orden=4, color="#EF6C00",
                     definicion="Aprendiz con matrícula aplazada; no está en formación activa."),
    "CANCELADO": dict(id="E05", categoria="Desertor", vinculado=0, activo=0, perdida=1,
                      cancelado=1, retirado=0, trasladado=0, suspendido=0, riesgo=0,
                      certificado=0, orden=5, color="#C62828",
                      definicion="Matrícula cancelada. Se contabiliza como deserción."),
    "RETIRO VOLUNTARIO": dict(id="E06", categoria="Desertor", vinculado=0, activo=0, perdida=1,
                              cancelado=0, retirado=1, trasladado=0, suspendido=0, riesgo=0,
                              certificado=0, orden=6, color="#8E0000",
                              definicion="Retiro solicitado por el aprendiz. Se contabiliza como deserción."),
    "TRASLADADO": dict(id="E07", categoria="Egreso por traslado", vinculado=0, activo=0, perdida=0,
                       cancelado=0, retirado=0, trasladado=1, suspendido=0, riesgo=0,
                       certificado=0, orden=7, color="#546E7A",
                       definicion="Traslado a otra ficha o centro; no se contabiliza como deserción."),
}


def main():
    raw = read_rows()
    # Normalizacion y llaves
    rows = []
    for r in raw:
        prog_key = norm(r["programa_titulo"]).replace(" .", "").strip()
        # Quitar punto final y espacios residuales
        prog_key = re.sub(r"\s+", " ", prog_key).strip()
        if prog_key not in PROGRAMS:
            raise KeyError(f"Programa no mapeado: {r['programa_titulo']!r} -> {prog_key!r}")
        p = PROGRAMS[prog_key]
        tipo = r["tipo_documento"].upper()
        doc = re.sub(r"\D", "", r["documento"])
        estado = r["estado"].upper()
        if estado not in STATES:
            raise KeyError(f"Estado no mapeado: {estado}")
        ficha = str(r["ficha"])
        jornada = r["jornada"].upper()
        generacion = ficha[:3]
        email = r["correo"].lower()
        email_ok = bool(re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$", email))
        phone = re.sub(r"\D", "", r["celular"])
        phone_ok = len(phone) == 10 and phone.startswith("3")
        aprendiz_id = "APR-" + sha(f"{tipo}|{doc}", 10)
        matricula_id = "MAT-" + sha(f"{ficha}|{tipo}|{doc}", 12)
        nombre = clean(r["nombres"]).upper()
        apellidos = clean(r["apellidos"]).upper()
        nombre_abrev = ""
        if nombre:
            nombre_abrev = nombre.split()[0][0] + "."
        if apellidos:
            parts = apellidos.split()
            nombre_abrev += " " + parts[0]
            if len(parts) > 1:
                nombre_abrev += " " + parts[1][0] + "."
        nombre_abrev = nombre_abrev.strip()
        grupo_edad = {
            "TI": "Menor de 18 (proxy TI)",
            "CC": "Adulto (proxy CC)",
            "PPT": "Extranjero (proxy PPT)",
            "CE": "Extranjero (proxy CE)",
        }.get(tipo, "No informado")
        rows.append({
            **r,
            "programa_key": prog_key,
            "programa_id": p["id"],
            "programa_nombre": p["nombre"],
            "programa_corto": p["corto"],
            "linea": p["linea"],
            "nivel": p["nivel"],
            "nivel_fuente": p["nivel_fuente"],
            "tipo_documento": tipo,
            "documento": doc,
            "estado": estado,
            "estado_id": STATES[estado]["id"],
            "ficha": ficha,
            "jornada": jornada,
            "generacion": generacion,
            "aprendiz_id": aprendiz_id,
            "matricula_id": matricula_id,
            "nombre_abreviado": nombre_abrev,
            "email_dominio": email.split("@")[-1] if "@" in email else "",
            "email_valido": 1 if email_ok else 0,
            "celular_valido": 1 if phone_ok else 0,
            "tiene_celular": 1 if phone else 0,
            "contacto_completo": 1 if (phone_ok and email_ok) else 0,
            "grupo_edad_proxy": grupo_edad,
            "genero": "No informado",
        })

    # Deduplicar solo duplicados exactos dentro de la misma ficha (no hay en la fuente)
    dedup = {}
    for r in rows:
        dedup[(r["ficha"], r["documento"])] = r
    rows = list(dedup.values())
    rows.sort(key=lambda r: (r["ficha"], r["apellidos"], r["nombres"]))

    # Dimension Tiempo
    dim_tiempo = []
    start = date(2025, 1, 1)
    end = date(2027, 12, 31)
    d = start
    while d <= end:
        iso = d.isocalendar()
        dim_tiempo.append({
            "FechaID": int(d.strftime("%Y%m%d")),
            "Fecha": d.isoformat(),
            "Anio": d.year,
            "Trimestre": f"T{(d.month - 1)//3 + 1}",
            "TrimestreNum": (d.month - 1)//3 + 1,
            "Mes": d.month,
            "NombreMes": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][d.month - 1],
            "MesCorto": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago",
                         "Sep", "Oct", "Nov", "Dic"][d.month - 1],
            "AnioMes": d.strftime("%Y-%m"),
            "SemanaISO": iso.week,
            "Dia": d.day,
            "DiaSemana": iso.weekday,
            "NombreDia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][iso.weekday - 1],
            "EsFinSemana": 1 if iso.weekday >= 6 else 0,
            "InicioMes": d.replace(day=1).isoformat(),
            "FinMes": (d.replace(day=28) + timedelta(days=4)).replace(day=1).__sub__(timedelta(days=1)).isoformat(),
        })
        d += timedelta(days=1)

    # Dimensiones simples
    dim_jornada = [
        {"JornadaID": "J01", "Jornada": "DIURNA", "Descripcion": "Jornada diurna"},
        {"JornadaID": "J02", "Jornada": "NOCTURNA", "Descripcion": "Jornada nocturna"},
        {"JornadaID": "J03", "Jornada": "NO INFORMADA", "Descripcion": "Sin dato en la fuente"},
    ]
    dim_nivel = [
        {"NivelID": "N01", "NivelFormacion": "Técnico", "Orden": 1,
         "Definicion": "Programa de formación técnica. Nivel inferido; validar en SOFIA Plus."},
        {"NivelID": "N02", "NivelFormacion": "Tecnólogo", "Orden": 2,
         "Definicion": "Programa de formación tecnológica. Nivel inferido; validar en SOFIA Plus."},
        {"NivelID": "N03", "NivelFormacion": "No informado", "Orden": 3,
         "Definicion": "Nivel no disponible en la fuente."},
    ]
    dim_centro = [{
        "CentroID": "CF-000",
        "CentroNombre": "Centro ASTIN",
        "Regional": "No informado",
        "Ciudad": "No informado",
        "CodigoCentro": "No informado",
        "Nota": "Nombre del centro indicado por el usuario. El código, la regional y la ciudad no vienen en los reportes de ficha; completar desde SOFIA Plus.",
    }]
    dim_departamento = [{
        "DepartamentoID": "DEP-000", "Departamento": "No informado",
        "CodigoDANE": "No informado",
        "Nota": "Campo no disponible en la fuente. Diseñado para integración futura.",
    }]
    dim_municipio = [{
        "MunicipioID": "MUN-000", "Municipio": "No informado",
        "DepartamentoID": "DEP-000", "CodigoDANE": "No informado",
        "Nota": "Campo no disponible en la fuente. Diseñado para integración futura.",
    }]
    dim_riesgo = [
        {"NivelRiesgo": "Bajo", "Orden": 1, "PercentilMin": 0, "PercentilMax": 49.999,
         "ColorHex": "#39A900", "Criterio": "Percentil de la tasa de pérdida ajustada < 50",
         "Accion": "Monitoreo rutinario."},
        {"NivelRiesgo": "Medio", "Orden": 2, "PercentilMin": 50, "PercentilMax": 74.999,
         "ColorHex": "#FDC300", "Criterio": "Percentil de la tasa de pérdida ajustada entre 50 y 75",
         "Accion": "Seguimiento mensual y refuerzo preventivo."},
        {"NivelRiesgo": "Alto", "Orden": 3, "PercentilMin": 75, "PercentilMax": 89.999,
         "ColorHex": "#EF6C00", "Criterio": "Percentil de la tasa de pérdida ajustada entre 75 y 90",
         "Accion": "Plan de acción en 30 días; alerta a coordinación."},
        {"NivelRiesgo": "Crítico", "Orden": 4, "PercentilMin": 90, "PercentilMax": 100,
         "ColorHex": "#C62828", "Criterio": "Percentil de la tasa de pérdida ajustada ≥ 90 (decil superior)",
         "Accion": "Intervención inmediata; comité académico en 8 días."},
    ]
    dim_estado = []
    for estado, s in sorted(STATES.items(), key=lambda kv: kv[1]["orden"]):
        dim_estado.append({
            "EstadoID": s["id"], "Estado": estado, "Categoria": s["categoria"],
            "EsVinculado": s["vinculado"], "EsActivo": s["activo"], "EsPerdida": s["perdida"],
            "EsCancelado": s["cancelado"], "EsRetirado": s["retirado"],
            "EsTrasladado": s["trasladado"], "EsSuspendido": s["suspendido"],
            "EsRiesgo": s["riesgo"], "EsCertificado": s["certificado"],
            "Orden": s["orden"], "ColorHex": s["color"], "Definicion": s["definicion"],
        })

    # Programas
    dim_programa = []
    for key, p in sorted(PROGRAMS.items(), key=lambda kv: kv[1]["id"]):
        n = sum(1 for r in rows if r["programa_id"] == p["id"])
        f = len({r["ficha"] for r in rows if r["programa_id"] == p["id"]})
        dim_programa.append({
            "ProgramaID": p["id"], "ProgramaNombre": p["nombre"], "ProgramaCorto": p["corto"],
            "LineaTecnologica": p["linea"], "NivelFormacion": p["nivel"],
            "NivelFuente": p["nivel_fuente"], "TotalFichas": f, "TotalMatriculas": n,
            "Activo": "Sí", "NotaNivel": "Nivel inferido a partir del nombre; validar contra SOFIA Plus.",
        })

    # Aprendices
    by_student = defaultdict(list)
    for r in rows:
        by_student[r["aprendiz_id"]].append(r)
    dim_aprendiz = []
    for aid, rs in by_student.items():
        r0 = sorted(rs, key=lambda x: x["ficha"])[0]
        # Peor estado del aprendiz entre sus fichas
        worst = sorted(rs, key=lambda x: STATES[x["estado"]]["orden"], reverse=True)[0]
        fichas = sorted({x["ficha"] for x in rs})
        dim_aprendiz.append({
            "AprendizID": aid,
            "TipoDocumento": r0["tipo_documento"],
            "Genero": "No informado",
            "GeneroFuente": "No disponible en la fuente",
            "GrupoEdadProxy": r0["grupo_edad_proxy"],
            "Edad": "",
            "MunicipioID": "MUN-000",
            "DepartamentoID": "DEP-000",
            "EmailDominio": r0["email_dominio"],
            "TieneCelular": max(x["tiene_celular"] for x in rs),
            "CelularValido": max(x["celular_valido"] for x in rs),
            "EmailValido": max(x["email_valido"] for x in rs),
            "ContactoCompleto": max(x["contacto_completo"] for x in rs),
            "TotalMatriculas": len(rs),
            "TotalFichas": len(fichas),
            "PrimeraFicha": fichas[0],
            "UltimaFicha": fichas[-1],
            "EstadoActual": worst["estado"],
            "TieneMultiplesFichas": 1 if len(fichas) > 1 else 0,
        })

    # Fichas + riesgo
    fichas = sorted({r["ficha"] for r in rows})
    ficha_base = {}
    for f in fichas:
        rs = [r for r in rows if r["ficha"] == f]
        r0 = rs[0]
        counts = Counter(r["estado"] for r in rs)
        n = len(rs)
        perdidas = counts["CANCELADO"] + counts["RETIRO VOLUNTARIO"]
        cancelados = counts["CANCELADO"]
        retiros = counts["RETIRO VOLUNTARIO"]
        trasladados = counts["TRASLADADO"]
        activos = counts["EN FORMACION"] + counts["INDUCCION"] + counts["CONDICIONADO"]
        vinculados = activos + counts["APLAZADO"]
        contacto_incompleto = sum(1 for r in rs if not r["contacto_completo"])
        ficha_base[f] = {
            "ficha": f, "n": n, "perdidas": perdidas, "cancelados": cancelados,
            "retiros": retiros, "trasladados": trasladados, "activos": activos,
            "vinculados": vinculados, "contacto_incompleto": contacto_incompleto,
            "programa_id": r0["programa_id"], "jornada": r0["jornada"],
            "generacion": r0["generacion"], "estado_ficha": r0["estado_ficha"],
            "counts": counts,
        }

    total_n = sum(v["n"] for v in ficha_base.values())
    total_perdidas = sum(v["perdidas"] for v in ficha_base.values())
    global_rate = total_perdidas / total_n if total_n else 0
    k_prior = 10
    for v in ficha_base.values():
        v["tasa_perdida"] = v["perdidas"] / v["n"] if v["n"] else 0
        v["tasa_cancelacion"] = v["cancelados"] / v["n"] if v["n"] else 0
        v["tasa_retiro"] = v["retiros"] / v["n"] if v["n"] else 0
        v["tasa_activos"] = v["activos"] / v["n"] if v["n"] else 0
        v["tasa_contacto_incompleto"] = v["contacto_incompleto"] / v["n"] if v["n"] else 0
        v["tasa_perdida_ajustada"] = (v["perdidas"] + k_prior * global_rate) / (v["n"] + k_prior)
        v["wilson_low"], v["wilson_high"] = wilson(v["perdidas"], v["n"])

    p_loss = percentile_rank([v["tasa_perdida_ajustada"] for v in ficha_base.values()])
    for i, f in enumerate(ficha_base):
        v = ficha_base[f]
        v["p_loss"] = p_loss[i]
        # El indice es el percentil de la tasa de perdida ajustada (empirical Bayes).
        # El contacto incompleto NO suma riesgo: esta concentrado en cohortes nuevas
        # y se reporta como bandera de calidad/operacion.
        v["indice_riesgo"] = v["p_loss"]

    ranking = sorted(ficha_base, key=lambda f: ficha_base[f]["indice_riesgo"], reverse=True)
    n_fichas = len(ranking)
    for rank, f in enumerate(ranking, start=1):
        v = ficha_base[f]
        v["ranking"] = rank
        # Percentil de posicion (0-100). El indice es comparativo, no una probabilidad.
        v["percentil_riesgo"] = 100.0 * (n_fichas - rank + 0.5) / n_fichas
        idx = v["percentil_riesgo"]
        if idx >= 90:
            v["nivel"] = "Crítico"
        elif idx >= 75:
            v["nivel"] = "Alto"
        elif idx >= 50:
            v["nivel"] = "Medio"
        else:
            v["nivel"] = "Bajo"
        v["confiabilidad"] = "Alta" if v["n"] >= 30 else ("Media" if v["n"] >= 20 else "Baja")
        contrib = {
            "Tasa de pérdida": 1.0 * v["p_loss"],
        }
        v["alerta_principal"] = max(contrib, key=contrib.get)
        v["alerta_secundaria"] = "Calidad de contacto" if v["tasa_contacto_incompleto"] >= 0.25 else ""

    dim_ficha = []
    for f in sorted(ficha_base, key=lambda x: x):
        v = ficha_base[f]
        c = v["counts"]
        dim_ficha.append({
            "FichaID": f,
            "FichaNombre": f"Ficha {f}",
            "ProgramaID": v["programa_id"],
            "Jornada": v["jornada"],
            "GeneracionID": f"GEN-{v['generacion']}",
            "CentroID": "CF-000",
            "EstadoFicha": v["estado_ficha"],
            "FechaReporte": REPORT_DATE.isoformat(),
            "TotalMatriculas": v["n"],
            "AprendicesActivos": v["activos"],
            "AprendicesVinculados": v["vinculados"],
            "EnFormacion": c["EN FORMACION"],
            "Induccion": c["INDUCCION"],
            "Condicionados": c["CONDICIONADO"],
            "Aplazados": c["APLAZADO"],
            "Cancelados": v["cancelados"],
            "Retiros": v["retiros"],
            "Trasladados": v["trasladados"],
            "Certificados": 0,
            "TasaPerdida": pct(v["tasa_perdida"]),
            "TasaPerdidaAjustada": pct(v["tasa_perdida_ajustada"]),
            "TasaCancelacion": pct(v["tasa_cancelacion"]),
            "TasaRetiro": pct(v["tasa_retiro"]),
            "TasaActivos": pct(v["tasa_activos"]),
            "TasaContactoIncompleto": pct(v["tasa_contacto_incompleto"]),
            "IC95Inferior": pct(v["wilson_low"]),
            "IC95Superior": pct(v["wilson_high"]),
            "IndiceRiesgo": round(v["indice_riesgo"], 1),
            "PercentilRiesgo": round(v["percentil_riesgo"], 1),
            "NivelRiesgo": v["nivel"],
            "RankingRiesgo": v["ranking"],
            "Confiabilidad": v["confiabilidad"],
            "AlertaPrincipal": v["alerta_principal"],
            "AlertaSecundaria": v["alerta_secundaria"],
            "ProbDesercionFicha": "",
            "Prioridad": "",
        })

    # Generaciones (prefijo de ficha)
    gen_groups = defaultdict(list)
    for f, v in ficha_base.items():
        gen_groups[v["generacion"]].append(v)
    dim_generacion = []
    for i, gen in enumerate(sorted(gen_groups), start=1):
        vs = gen_groups[gen]
        n = sum(v["n"] for v in vs)
        perd = sum(v["perdidas"] for v in vs)
        dim_generacion.append({
            "GeneracionID": f"GEN-{gen}",
            "GeneracionNombre": f"Generación {gen}",
            "GeneracionOrden": i,
            "RangoFicha": f"{gen}0000 - {gen}9999",
            "Fichas": len(vs),
            "Matriculas": n,
            "Perdidas": perd,
            "TasaPerdida": pct(perd / n if n else 0),
            "Nota": "Agrupación por prefijo de ficha. No equivale a año calendario.",
        })

    # Hechos
    nivel_by_program = {"P01": "N01", "P02": "N02", "P03": "N01", "P04": "N02",
                        "P05": "N02", "P06": "N02", "P07": "N02", "P08": "N02",
                        "P09": "N02", "P10": "N02", "P11": "N02", "P12": "N02",
                        "P13": "N01", "P14": "N02", "P15": "N02"}
    fact = []
    for r in rows:
        s = STATES[r["estado"]]
        fv = ficha_base[r["ficha"]]
        fact.append({
            "MatriculaID": r["matricula_id"],
            "AprendizID": r["aprendiz_id"],
            "FichaID": r["ficha"],
            "ProgramaID": r["programa_id"],
            "JornadaID": "J01" if r["jornada"] == "DIURNA" else "J02",
            "EstadoID": s["id"],
            "CentroID": "CF-000",
            "NivelID": nivel_by_program[r["programa_id"]],
            "MunicipioID": "MUN-000",
            "DepartamentoID": "DEP-000",
            "GeneracionID": f"GEN-{r['generacion']}",
            "FechaReporteID": int(REPORT_DATE.strftime("%Y%m%d")),
            "FechaReporte": REPORT_DATE.isoformat(),
            "EsVinculado": s["vinculado"],
            "EsActivo": s["activo"],
            "EsPerdida": s["perdida"],
            "EsCancelado": s["cancelado"],
            "EsRetirado": s["retirado"],
            "EsTrasladado": s["trasladado"],
            "EsSuspendido": s["suspendido"],
            "EsRiesgo": s["riesgo"],
            "EsCertificado": 0,
            "ContactoCompleto": r["contacto_completo"],
            "TieneCelular": r["tiene_celular"],
            "CelularValido": r["celular_valido"],
            "EmailValido": r["email_valido"],
            "NivelRiesgoFicha": fv["nivel"],
            "IndiceRiesgoFicha": round(fv["indice_riesgo"], 1),
            "Peso": 1,
        })

    # Escribir dimensiones
    write_csv("DimTiempo.csv", dim_tiempo, list(dim_tiempo[0].keys()))
    write_csv("DimJornada.csv", dim_jornada, list(dim_jornada[0].keys()))
    write_csv("DimNivelFormacion.csv", dim_nivel, list(dim_nivel[0].keys()))
    write_csv("DimCentroFormacion.csv", dim_centro, list(dim_centro[0].keys()))
    write_csv("DimDepartamento.csv", dim_departamento, list(dim_departamento[0].keys()))
    write_csv("DimMunicipio.csv", dim_municipio, list(dim_municipio[0].keys()))
    write_csv("DimRiesgo.csv", dim_riesgo, list(dim_riesgo[0].keys()))
    write_csv("DimEstado.csv", dim_estado, list(dim_estado[0].keys()))
    write_csv("DimPrograma.csv", dim_programa, list(dim_programa[0].keys()))
    write_csv("DimAprendiz.csv", dim_aprendiz, list(dim_aprendiz[0].keys()))
    write_csv("DimFicha.csv", dim_ficha, list(dim_ficha[0].keys()))
    write_csv("DimGeneracion.csv", dim_generacion, list(dim_generacion[0].keys()))
    write_csv("FactMatricula.csv", fact, list(fact[0].keys()))

    # Resumen para auditoria y documentos
    estados = Counter(r["estado"] for r in rows)
    total = len(rows)
    perdidas = estados["CANCELADO"] + estados["RETIRO VOLUNTARIO"]
    summary = {
        "fecha_reporte": REPORT_DATE.isoformat(),
        "filas": total,
        "aprendices_unicos": len({r["aprendiz_id"] for r in rows}),
        "fichas": len(fichas),
        "programas": len(PROGRAMS),
        "matriculas_multiples": sum(1 for _, rs in by_student.items() if len(rs) > 1),
        "estados": dict(estados),
        "perdidas": perdidas,
        "tasa_perdida": pct(perdidas / total),
        "tasa_cancelacion": pct(estados["CANCELADO"] / total),
        "tasa_retiro": pct(estados["RETIRO VOLUNTARIO"] / total),
        "tasa_traslado": pct(estados["TRASLADADO"] / total),
        "tasa_activos": pct((estados["EN FORMACION"] + estados["INDUCCION"] + estados["CONDICIONADO"]) / total),
        "tasa_vinculados": pct((estados["EN FORMACION"] + estados["INDUCCION"] + estados["CONDICIONADO"] + estados["APLAZADO"]) / total),
        "contacto_incompleto": sum(1 for r in rows if not r["contacto_completo"]),
        "contacto_incompleto_pct": pct(sum(1 for r in rows if not r["contacto_completo"]) / total),
        "fichas_riesgo": {
            k: sum(1 for v in ficha_base.values() if v["nivel"] == k)
            for k in ["Bajo", "Medio", "Alto", "Crítico"]
        },
        "fichas_detalle": [
            {k: v[k] for k in ["ficha", "n", "perdidas", "cancelados", "retiros", "trasladados",
                               "activos", "tasa_perdida", "tasa_perdida_ajustada",
                               "indice_riesgo", "percentil_riesgo", "nivel", "ranking",
                               "alerta_principal", "alerta_secundaria", "confiabilidad",
                               "programa_id", "jornada", "generacion"]}
            for v in sorted(ficha_base.values(), key=lambda x: x["ranking"])
        ],
        "programas_detalle": [],
        "generaciones_detalle": dim_generacion,
    }
    for p in dim_programa:
        rs = [r for r in rows if r["programa_id"] == p["ProgramaID"]]
        n = len(rs)
        perd = sum(1 for r in rs if r["estado"] in ("CANCELADO", "RETIRO VOLUNTARIO"))
        canc = sum(1 for r in rs if r["estado"] == "CANCELADO")
        act = sum(1 for r in rs if r["estado"] in ("EN FORMACION", "INDUCCION", "CONDICIONADO"))
        low, high = wilson(perd, n)
        summary["programas_detalle"].append({
            "programa_id": p["ProgramaID"], "programa": p["ProgramaNombre"],
            "linea": p["LineaTecnologica"], "nivel": p["NivelFormacion"],
            "fichas": p["TotalFichas"], "matriculas": n, "perdidas": perd,
            "cancelados": canc, "activos": act,
            "tasa_perdida": pct(perd / n if n else 0),
            "tasa_cancelacion": pct(canc / n if n else 0),
            "tasa_activos": pct(act / n if n else 0),
            "ic95_inf": pct(low), "ic95_sup": pct(high),
        })
    summary["programas_detalle"].sort(key=lambda x: x["matriculas"], reverse=True)
    (OUTPUTS / "02_etl_resumen.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Tablas escritas en", OUT)
    print("Filas:", total, "| Aprendices unicos:", summary["aprendices_unicos"],
          "| Fichas:", len(fichas), "| Programas:", len(PROGRAMS))
    print("Tasa de perdida:", f"{summary['tasa_perdida']*100:.2f}%",
          "| Cancelacion:", f"{summary['tasa_cancelacion']*100:.2f}%",
          "| Retiro:", f"{summary['tasa_retiro']*100:.2f}%")
    print("Riesgo fichas:", summary["fichas_riesgo"])
    print("Contacto incompleto:", summary["contacto_incompleto"], f"({summary['contacto_incompleto_pct']*100:.2f}%)")


if __name__ == "__main__":
    main()
