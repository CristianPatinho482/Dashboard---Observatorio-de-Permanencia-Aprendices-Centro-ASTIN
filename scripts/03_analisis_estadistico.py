# -*- coding: utf-8 -*-
"""
FASE 3 - Analisis estadistico del snapshot 2026-10-19.
Salidas:
  outputs/03_analisis_estadistico.json
  outputs/charts/*.png
"""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#B8C4CC",
    "axes.labelcolor": "#243B4A",
    "text.color": "#243B4A",
    "xtick.color": "#4A5C68",
    "ytick.color": "#4A5C68",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 180,
})
SENA_GREEN = "#39A900"
SENA_DARK = "#00324D"
ORANGE = "#EF6C00"
RED = "#C62828"
YELLOW = "#F9A825"
GREY = "#78909C"


def read_csv(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(value, digits=4):
    return round(float(value), digits)


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def beta_binomial(k, n, prior_rate, prior_n=10):
    a = prior_rate * prior_n + k
    b = (1 - prior_rate) * prior_n + (n - k)
    mean = a / (a + b)
    low = stats.beta.ppf(0.025, a, b)
    high = stats.beta.ppf(0.975, a, b)
    return mean, low, high


def chi2_table(table, correction=False):
    table = np.asarray(table, dtype=float)
    chi2, p, dof, expected = stats.chi2_contingency(table, correction=correction)
    n = table.sum()
    v = math.sqrt(chi2 / (n * (min(table.shape) - 1))) if n and min(table.shape) > 1 else 0.0
    return {
        "chi2": round(float(chi2), 3),
        "gl": int(dof),
        "p": float(p),
        "p_texto": "< 0.001" if p < 0.001 else f"{p:.3f}",
        "v_cramer": round(float(v), 3),
        "n": int(n),
        "esperados_menores_5": int((expected < 5).sum()),
        "esperados_menores_5_pct": round(float((expected < 5).mean()), 3),
    }


def odds_ratio_2x2(table):
    a, b = table[0]
    c, d = table[1]
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return (a * d) / (b * c)


def mh_or_stratified(rows, strat_key, exposure_key, outcome_key):
    """Mantel-Haenszel OR y CI 95% (Greenland-Robins) para exposicion binaria."""
    strata = defaultdict(lambda: [0, 0, 0, 0])  # a exp+out+, b exp+out-, c exp-out+, d exp-out-
    for r in rows:
        s = strata[r[strat_key]]
        exp = int(r[exposure_key])
        out = int(r[outcome_key])
        if exp and out:
            s[0] += 1
        elif exp and not out:
            s[1] += 1
        elif not exp and out:
            s[2] += 1
        else:
            s[3] += 1
    num_r = 0.0
    den_r = 0.0
    sum_pr = 0.0
    sum_ps_qr = 0.0
    sum_qs = 0.0
    valid = 0
    for a, b, c, d in strata.values():
        n = a + b + c + d
        if n < 2:
            continue
        valid += 1
        # Correccion de Haldane solo para celdas vacias del estrato
        aa, bb, cc, dd = a, b, c, d
        if 0 in (aa, bb, cc, dd):
            aa, bb, cc, dd = aa + 0.5, bb + 0.5, cc + 0.5, dd + 0.5
            n = aa + bb + cc + dd
        num_r += aa * dd / n
        den_r += bb * cc / n
        p = (aa + dd) / n
        q = (bb + cc) / n
        sum_pr += p * (aa * dd) / n
        sum_ps_qr += p * (aa * dd) / n + q * (bb * cc) / n
        sum_qs += q * (bb * cc) / n
    if den_r == 0:
        return None
    or_mh = num_r / den_r
    se = math.sqrt(sum_pr / (2 * num_r * num_r) + sum_ps_qr / (2 * num_r * den_r) + sum_qs / (2 * den_r * den_r))
    low = math.exp(math.log(or_mh) - 1.96 * se)
    high = math.exp(math.log(or_mh) + 1.96 * se)
    return {"or_mh": round(or_mh, 3), "ic95_inf": round(low, 3), "ic95_sup": round(high, 3),
            "estratos_validos": valid}


def cochran_armitage(groups):
    """groups: lista de (score, n, eventos). Tendencia lineal en proporciones."""
    total_n = sum(n for _, n, _ in groups)
    total_y = sum(y for _, _, y in groups)
    if total_n == 0 or total_y in (0, total_n):
        return {"z": 0.0, "p": 1.0, "pendiente_pp_por_generacion": 0.0}
    p = total_y / total_n
    scores = np.array([g[0] for g in groups], dtype=float)
    ns = np.array([g[1] for g in groups], dtype=float)
    ys = np.array([g[2] for g in groups], dtype=float)
    t = float(np.sum(scores * (ys - ns * p)))
    var = p * (1 - p) * (float(np.sum(ns * scores ** 2)) - float(np.sum(ns * scores)) ** 2 / total_n)
    z = t / math.sqrt(var) if var > 0 else 0.0
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    # Pendiente aproximada de la proporcion por unidad de score (minimos cuadrados ponderados)
    w = ns
    xbar = np.average(scores, weights=w)
    ybar = np.average(ys / ns, weights=w)
    slope = np.sum(w * (scores - xbar) * (ys / ns - ybar)) / np.sum(w * (scores - xbar) ** 2)
    return {"z": round(z, 3), "p": float(pval),
            "p_texto": "< 0.001" if pval < 0.001 else f"{pval:.3f}",
            "pendiente_pp_por_generacion": round(float(slope) * 100, 3)}


def gini(values):
    values = np.sort(np.asarray(values, dtype=float))
    n = len(values)
    if n == 0 or values.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * values) / (n * values.sum())) - (n + 1) / n)


def main():
    fact = read_csv("FactMatricula.csv")
    fichas = read_csv("DimFicha.csv")
    programas = read_csv("DimPrograma.csv")
    generaciones = read_csv("DimGeneracion.csv")
    estados = read_csv("DimEstado.csv")
    aprendices = read_csv("DimAprendiz.csv")
    tipo_doc = {a["AprendizID"]: a["TipoDocumento"] for a in aprendices}
    for r in fact:
        r["TipoDocumento"] = tipo_doc.get(r["AprendizID"], "No informado")

    for r in fact:
        for c in ["EsPerdida", "EsCancelado", "EsActivo", "EsVinculado", "EsTrasladado",
                  "EsSuspendido", "EsRiesgo", "ContactoCompleto", "TieneCelular",
                  "CelularValido", "EmailValido"]:
            r[c] = int(num(r[c]))
        r["TieneDocumento"] = 1
        r["Perdida"] = r["EsPerdida"]

    n = len(fact)
    perdidas = sum(r["EsPerdida"] for r in fact)
    cancelados = sum(r["EsCancelado"] for r in fact)
    activos = sum(r["EsActivo"] for r in fact)
    vinculados = sum(r["EsVinculado"] for r in fact)
    trasladados = sum(r["EsTrasladado"] for r in fact)
    contacto_incompleto = sum(1 for r in fact if not r["ContactoCompleto"])
    tasa = perdidas / n
    low, high = wilson(perdidas, n)

    prog_by_id = {p["ProgramaID"]: p for p in programas}
    ficha_by_id = {f["FichaID"]: f for f in fichas}

    # ---------- Programas ----------
    prog_rows = []
    total_perd = perdidas
    for p in programas:
        rs = [r for r in fact if r["ProgramaID"] == p["ProgramaID"]]
        nn = len(rs)
        yy = sum(r["EsPerdida"] for r in rs)
        cc = sum(r["EsCancelado"] for r in rs)
        aa = sum(r["EsActivo"] for r in rs)
        lo, hi = wilson(yy, nn)
        eb, eb_lo, eb_hi = beta_binomial(yy, nn, tasa, 10)
        prog_rows.append({
            "programa_id": p["ProgramaID"],
            "programa": p["ProgramaNombre"],
            "corto": p["ProgramaCorto"],
            "linea": p["LineaTecnologica"],
            "nivel": p["NivelFormacion"],
            "fichas": int(num(p["TotalFichas"])),
            "matriculas": nn,
            "perdidas": yy,
            "cancelados": cc,
            "activos": aa,
            "tasa_perdida": pct(yy / nn if nn else 0),
            "ic95_inf": pct(lo),
            "ic95_sup": pct(hi),
            "tasa_ajustada_eb": pct(eb),
            "eb_ic95_inf": pct(eb_lo),
            "eb_ic95_sup": pct(eb_hi),
            "participacion": pct(nn / n if n else 0),
        })
    prog_rows.sort(key=lambda x: (-x["matriculas"], x["programa"]))
    acum = 0.0
    for p in prog_rows:
        acum += p["participacion"]
        p["participacion_acumulada"] = pct(acum)
    for p in prog_rows:
        p["ranking_tasa"] = 1 + sum(1 for q in prog_rows if q["tasa_ajustada_eb"] > p["tasa_ajustada_eb"])
        p["brecha_vs_global_pp"] = round((p["tasa_perdida"] - tasa) * 100, 2)

    hhi = sum(p["participacion"] ** 2 for p in prog_rows)
    top3 = sum(p["participacion"] for p in sorted(prog_rows, key=lambda x: -x["participacion"])[:3])
    concentracion = {
        "hhi_programas": round(hhi, 4),
        "numero_efectivo_programas": round(1 / hhi, 2) if hhi else 0,
        "top3_participacion": pct(top3),
        "gini_tamano_fichas": round(gini([int(num(f["TotalMatriculas"])) for f in fichas]), 4),
        "ficha_mas_grande": max(int(num(f["TotalMatriculas"])) for f in fichas),
        "ficha_mas_pequena": min(int(num(f["TotalMatriculas"])) for f in fichas),
        "nota": "HHI sobre participacion de matricula por programa. Gini sobre tamano de ficha.",
    }

    # ---------- Jornadas ----------
    jornadas = []
    for jid, nombre in [("J01", "DIURNA"), ("J02", "NOCTURNA")]:
        rs = [r for r in fact if r["JornadaID"] == jid]
        nn = len(rs)
        yy = sum(r["EsPerdida"] for r in rs)
        lo, hi = wilson(yy, nn)
        jornadas.append({"jornada_id": jid, "jornada": nombre, "n": nn, "perdidas": yy,
                         "tasa_perdida": pct(yy / nn if nn else 0),
                         "ic95_inf": pct(lo), "ic95_sup": pct(hi)})
    tabla_j = [[j["perdidas"], j["n"] - j["perdidas"]] for j in jornadas]
    chi_j = chi2_table(tabla_j, correction=True)
    or_j = odds_ratio_2x2(tabla_j)
    # IC del OR por Woolf
    a, b = tabla_j[0]
    c, d = tabla_j[1]
    se_or = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d) if min(a, b, c, d) > 0 else float("nan")
    chi_j.update({"or_diurna_vs_nocturna": round(or_j, 3),
                  "or_ic95_inf": round(math.exp(math.log(or_j) - 1.96 * se_or), 3),
                  "or_ic95_sup": round(math.exp(math.log(or_j) + 1.96 * se_or), 3)})
    try:
        _, fisher_p = stats.fisher_exact(tabla_j)
        chi_j["fisher_p"] = float(fisher_p)
    except Exception:
        chi_j["fisher_p"] = None

    # ---------- Documento (proxy etario) ----------
    docs = []
    for tipo in sorted({r["TipoDocumento"] for r in fact}):
        rs = [r for r in fact if r["TipoDocumento"] == tipo]
        nn = len(rs)
        yy = sum(r["EsPerdida"] for r in rs)
        lo, hi = wilson(yy, nn)
        docs.append({"tipo_documento": tipo, "n": nn, "perdidas": yy,
                     "tasa_perdida": pct(yy / nn if nn else 0),
                     "ic95_inf": pct(lo), "ic95_sup": pct(hi)})
    tabla_doc = [[d["perdidas"], d["n"] - d["perdidas"]] for d in docs]
    chi_doc = chi2_table(tabla_doc)

    # ---------- Contacto ----------
    tabla_c = []
    for val in (0, 1):
        rs = [r for r in fact if r["ContactoCompleto"] == val]
        yy = sum(r["EsPerdida"] for r in rs)
        tabla_c.append([yy, len(rs) - yy])
    chi_c = chi2_table(tabla_c, correction=True)
    or_c = odds_ratio_2x2(tabla_c)
    a, b = tabla_c[0]
    c, d = tabla_c[1]
    se_c = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d) if min(a, b, c, d) > 0 else float("nan")
    chi_c.update({"or_incompleto_vs_completo": round(or_c, 3),
                  "or_ic95_inf": round(math.exp(math.log(or_c) - 1.96 * se_c), 3),
                  "or_ic95_sup": round(math.exp(math.log(or_c) + 1.96 * se_c), 3)})
    chi_c["or_ajustado_por_programa"] = mh_or_stratified(fact, "ProgramaID", "ContactoCompleto", "Perdida")
    chi_c["nota"] = ("El contacto incompleto se concentra en cohortes nuevas (0% de perdida) y en programas "
                     "con menor perdida; por eso la asociacion cruda es nula y la ajustada por programa "
                     "invierte el signo. No debe usarse como factor de riesgo de desercion: es un "
                     "indicador de calidad/contactabilidad y de actualizacion de datos.")

    # ---------- Distribucion de tasas por ficha ----------
    fr = np.array([num(f["TasaPerdida"]) for f in fichas], dtype=float)
    q1, med, q3 = np.percentile(fr, [25, 50, 75])
    iqr = q3 - q1
    out_alto = [f for f in fichas if num(f["TasaPerdida"]) > q3 + 1.5 * iqr]
    out_bajo = [f for f in fichas if num(f["TasaPerdida"]) < q1 - 1.5 * iqr]
    dist = {
        "n_fichas": len(fichas),
        "media": pct(fr.mean()),
        "mediana": pct(med),
        "desv_estandar": pct(fr.std(ddof=1)),
        "min": pct(fr.min()),
        "q1": pct(q1),
        "q3": pct(q3),
        "max": pct(fr.max()),
        "iqr": pct(iqr),
        "coef_variacion": pct(fr.std(ddof=1) / fr.mean() if fr.mean() else 0),
        "asimetria": pct(stats.skew(fr, bias=False)),
        "curtosis": pct(stats.kurtosis(fr, bias=False)),
        "outliers_alto": [{"ficha": f["FichaID"], "tasa": num(f["TasaPerdida"]), "n": int(num(f["TotalMatriculas"]))}
                          for f in out_alto],
        "outliers_bajo": [{"ficha": f["FichaID"], "tasa": num(f["TasaPerdida"]), "n": int(num(f["TotalMatriculas"]))}
                          for f in out_bajo],
    }

    # ---------- Asociaciones a nivel ficha ----------
    tam = np.array([num(f["TotalMatriculas"]) for f in fichas])
    contacto_f = np.array([num(f["TasaContactoIncompleto"]) for f in fichas])
    indice = np.array([num(f["IndiceRiesgo"]) for f in fichas])
    pearson_size = stats.pearsonr(tam, fr)
    spearman_size = stats.spearmanr(tam, fr)
    pearson_contact = stats.pearsonr(contacto_f, fr)
    spearman_contact = stats.spearmanr(contacto_f, fr)
    spearman_risk = stats.spearmanr(indice, fr)

    # ---------- Test de homogeneidad entre programas (Monte Carlo) ----------
    prog_codes = sorted({r["ProgramaID"] for r in fact})
    code_idx = {c: i for i, c in enumerate(prog_codes)}
    prog_arr = np.array([code_idx[r["ProgramaID"]] for r in fact])
    loss_arr = np.array([r["EsPerdida"] for r in fact])
    obs_table = np.zeros((len(prog_codes), 2), dtype=int)
    for p_i, y in zip(prog_arr, loss_arr):
        obs_table[p_i, 0] += int(y)
        obs_table[p_i, 1] += int(1 - y)
    chi_prog_asym = chi2_table(obs_table)
    rng = np.random.default_rng(20261019)
    sims = 5000
    ge = 0
    for _ in range(sims):
        shuffled = rng.permutation(loss_arr)
        tab = np.zeros_like(obs_table)
        for p_i, y in zip(prog_arr, shuffled):
            tab[p_i, 0] += int(y)
            tab[p_i, 1] += int(1 - y)
        stat = stats.chi2_contingency(tab, correction=False)[0]
        if stat >= chi_prog_asym["chi2"]:
            ge += 1
    chi_prog_asym["p_montecarlo"] = (ge + 1) / (sims + 1)
    chi_prog_asym["simulaciones"] = sims

    # ---------- Tendencia por generaciones ----------
    gen_rows = []
    for g in sorted(generaciones, key=lambda x: int(num(x["GeneracionOrden"]))):
        gen_rows.append({
            "generacion_id": g["GeneracionID"],
            "generacion": g["GeneracionNombre"],
            "orden": int(num(g["GeneracionOrden"])),
            "fichas": int(num(g["Fichas"])),
            "n": int(num(g["Matriculas"])),
            "perdidas": int(num(g["Perdidas"])),
            "tasa_perdida": pct(num(g["TasaPerdida"])),
        })
    ca = cochran_armitage([(g["orden"], g["n"], g["perdidas"]) for g in gen_rows])
    # Correlaciones generacion vs tasa (no ponderada y ponderada por n)
    gx = np.array([g["orden"] for g in gen_rows], dtype=float)
    gy = np.array([g["tasa_perdida"] for g in gen_rows], dtype=float)
    gw = np.array([g["n"] for g in gen_rows], dtype=float)
    spear_gen = stats.spearmanr(gx, gy)
    pearson_gen = stats.pearsonr(gx, gy)
    pearson_gen_w = np.corrcoef(gx, gy)[0, 1]  # se reporta sin ponderar; el CA ya pondera por n
    # Bandas de tamano de ficha
    bandas = []
    for label, lo, hi in [("< 20", 0, 19), ("20-29", 20, 29), ("30-39", 30, 39), ("40+", 40, 999)]:
        sel = [f for f in fichas if lo <= int(num(f["TotalMatriculas"])) <= hi]
        if not sel:
            continue
        nn = sum(int(num(f["TotalMatriculas"])) for f in sel)
        yy = sum(int(num(f["Cancelados"])) + int(num(f["Retiros"])) for f in sel)
        bandas.append({"banda": label, "fichas": len(sel), "n": nn, "perdidas": yy,
                       "tasa_perdida": pct(yy / nn if nn else 0)})

    # ---------- Validacion descriptiva del indice de riesgo ----------
    bandas_riesgo = []
    for nivel in ["Bajo", "Medio", "Alto", "Crítico"]:
        sel = [f for f in fichas if f["NivelRiesgo"] == nivel]
        if not sel:
            bandas_riesgo.append({"nivel": nivel, "fichas": 0, "n": 0, "perdidas": 0, "tasa_perdida": 0})
            continue
        nn = sum(int(num(f["TotalMatriculas"])) for f in sel)
        yy = sum(int(num(f["Cancelados"])) + int(num(f["Retiros"])) for f in sel)
        bandas_riesgo.append({"nivel": nivel, "fichas": len(sel), "n": nn, "perdidas": yy,
                             "tasa_perdida": pct(yy / nn if nn else 0),
                             "indice_promedio": round(float(np.mean([num(f["IndiceRiesgo"]) for f in sel])), 1)})

    # ---------- Calidad de datos ----------
    docs_counter = Counter(r["TipoDocumento"] for r in fact)
    dominios = Counter(a["EmailDominio"] for a in aprendices if a["EmailDominio"])
    multi = [a for a in aprendices if int(num(a["TotalFichas"])) > 1]
    calidad = {
        "sin_celular": sum(1 for r in fact if not r["TieneCelular"]),
        "sin_celular_pct": pct(sum(1 for r in fact if not r["TieneCelular"]) / n),
        "celular_invalido": sum(1 for r in fact if not r["CelularValido"]),
        "celular_invalido_pct": pct(sum(1 for r in fact if not r["CelularValido"]) / n),
        "email_invalido": sum(1 for r in fact if not r["EmailValido"]),
        "contacto_incompleto": contacto_incompleto,
        "contacto_incompleto_pct": pct(contacto_incompleto / n),
        "aprendices_unicos": len(aprendices),
        "aprendices_multi_ficha": len(multi),
        "matriculas_multi_ficha": sum(int(num(a["TotalFichas"])) for a in multi),
        "documentos": dict(docs_counter),
        "dominios_email_top": dominios.most_common(10),
        "sin_genero": sum(1 for a in aprendices if a["Genero"] == "No informado"),
        "sin_municipio": sum(1 for a in aprendices if a["MunicipioID"] == "MUN-000"),
    }

    # ---------- Poder estadistico ----------
    p0 = tasa
    z_alpha = 1.959963984540054
    z_beta = 0.8416212335729143
    # Diferencia detectable entre dos grupos iguales (aprox. normal)
    mde = (z_alpha + z_beta) * math.sqrt(2 * p0 * (1 - p0) / (n / 2)) if n else 0
    poder = {
        "tasa_base": pct(p0),
        "n": n,
        "mde_dos_grupos_iguales_pp_80pct": round(mde * 100, 2),
        "nota": ("Diferencia minima detectable entre dos grupos de igual tamano, prueba bilateral "
                 "alpha=0.05, poder=80%, aproximacion normal. Con 56 fichas y clusters, los "
                 "contrastes por ficha tienen baja potencia."),
    }

    # ---------- Consolidado ----------
    result = {
        "metadata": {
            "fecha_reporte": "2026-10-19",
            "fuente": "56 reportes .xls de ficha (snapshot unico)",
            "filas": n,
            "aprendices_unicos": len(aprendices),
            "fichas": len(fichas),
            "programas": len(programas),
            "generaciones": len(generaciones),
            "advertencia": ("Snapshot transversal sin fechas de matricula, egreso ni certificacion. "
                            "Los contrastes son exploratorios y no implican causalidad. Las fichas son "
                            "clusters; los p-valores no corrigen por dependencia intra-ficha."),
        },
        "resumen": {
            "matriculas": n,
            "perdidas": perdidas,
            "cancelados": cancelados,
            "retiros": perdidas - cancelados,
            "activos": activos,
            "vinculados": vinculados,
            "trasladados": trasladados,
            "tasa_perdida": pct(tasa),
            "ic95_inf": pct(low),
            "ic95_sup": pct(high),
            "tasa_cancelacion": pct(cancelados / n),
            "tasa_retiro": pct((perdidas - cancelados) / n),
            "tasa_activos": pct(activos / n),
            "tasa_vinculados": pct(vinculados / n),
            "contacto_incompleto": contacto_incompleto,
            "contacto_incompleto_pct": pct(contacto_incompleto / n),
        },
        "estados": estados,
        "jornadas": {"detalle": jornadas, "contraste": chi_j},
        "programas": {"detalle": prog_rows, "contraste": chi_prog_asym, "concentracion": concentracion},
        "documentos": {"detalle": docs, "contraste": chi_doc},
        "contacto": {"contraste": chi_c},
        "fichas_distribucion": dist,
        "correlaciones": {
            "tamano_ficha_vs_tasa_perdida": {"pearson_r": round(float(pearson_size.statistic), 3),
                                            "pearson_p": float(pearson_size.pvalue),
                                            "spearman_rho": round(float(spearman_size.statistic), 3),
                                            "spearman_p": float(spearman_size.pvalue)},
            "contacto_incompleto_vs_tasa_perdida": {"pearson_r": round(float(pearson_contact.statistic), 3),
                                                    "pearson_p": float(pearson_contact.pvalue),
                                                    "spearman_rho": round(float(spearman_contact.statistic), 3),
                                                    "spearman_p": float(spearman_contact.pvalue),
                                                    "nota": ("Asociacion negativa: las fichas con mas contacto incompleto "
                                                             "son cohortes nuevas con menor perdida. Confusion por cohorte; "
                                                             "no interpretar como protector.")},
            "indice_riesgo_vs_tasa_perdida": {"spearman_rho": round(float(spearman_risk.statistic), 3),
                                              "spearman_p": float(spearman_risk.pvalue),
                                              "nota": "Diagnostico interno: el indice incorpora la tasa de perdida."},
        },
        "tendencia_generaciones": {
            "detalle": gen_rows,
            "cochran_armitage": ca,
            "spearman_orden_vs_tasa": {"rho": round(float(spear_gen.statistic), 3),
                                       "p": float(spear_gen.pvalue)},
            "pearson_orden_vs_tasa": {"r": round(float(pearson_gen.statistic), 3),
                                      "p": float(pearson_gen.pvalue)},
            "nota": ("El prefijo de ficha se usa como proxy de generacion/antiguedad. No equivale a ano "
                     "calendario ni a fecha de matricula; la tendencia es descriptiva."),
        },
        "bandas_tamano_ficha": bandas,
        "validacion_riesgo": bandas_riesgo,
        "calidad_datos": calidad,
        "poder_estadistico": poder,
        "recomendaciones_metodologicas": [
            "Reportar intervalos de confianza junto con las tasas; evitar rankings por tasa puntual en fichas pequenas.",
            "No comparar programas o jornadas como si hubiera asignacion aleatoria: hay autoseleccion y confusion por ficha.",
            "Los contrastes por ficha y por generacion son exploratorios; validar con datos longitudinales.",
            "Para inferencia causal se requiere fecha de matricula, fecha de retiro, motivo y variables socioeconomicas.",
            "El contacto incompleto no es factor de riesgo: esta confundido con la antiguedad de la cohorte. Usarlo solo para gestion de contactabilidad.",
        ],
    }
    (OUT / "03_analisis_estadistico.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---------- Graficos ----------
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(CHARTS / name, bbox_inches="tight")
        plt.close(fig)

    # Estados
    est_labels = [e["Estado"] for e in estados]
    est_vals = [int(num(e["Total"])) if "Total" in e else 0 for e in estados]
    # DimEstado no trae Total: calcular desde fact
    est_counts = Counter(r["EstadoID"] for r in fact)
    est_vals = [est_counts.get(e["EstadoID"], 0) for e in estados]
    colors = [e["ColorHex"] for e in estados]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    bars = ax.bar(est_labels, est_vals, color=colors)
    for b, v in zip(bars, est_vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 8, f"{v:,}".replace(",", "."),
                ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_title("Matrículas por estado (snapshot 19-oct-2026)")
    ax.set_ylabel("Matrículas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", rotation=25)
    save(fig, "01_estados.png")

    # Programas: tasa con IC
    p_sorted = sorted(prog_rows, key=lambda x: x["tasa_ajustada_eb"])
    labels = [p["corto"] for p in p_sorted]
    vals = [p["tasa_perdida"] * 100 for p in p_sorted]
    err_low = [(p["tasa_perdida"] - p["ic95_inf"]) * 100 for p in p_sorted]
    err_high = [(p["ic95_sup"] - p["tasa_perdida"]) * 100 for p in p_sorted]
    fig, ax = plt.subplots(figsize=(9.2, 6.0))
    ax.barh(labels, vals, color=[RED if v >= tasa * 100 else SENA_GREEN for v in vals], alpha=0.88)
    ax.errorbar(vals, labels, xerr=[err_low, err_high], fmt="none", ecolor=SENA_DARK, capsize=3, lw=1)
    ax.axvline(tasa * 100, color=SENA_DARK, ls="--", lw=1.2, label=f"Global {tasa*100:.1f}%")
    ax.set_title("Tasa de pérdida por programa, con IC 95%")
    ax.set_xlabel("Tasa de pérdida (%)")
    ax.legend(loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "02_programas_tasa.png")

    # Dispersion fichas
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    color_map = {"Bajo": SENA_GREEN, "Medio": YELLOW, "Alto": ORANGE, "Crítico": RED}
    for nivel, color in color_map.items():
        sel = [f for f in fichas if f["NivelRiesgo"] == nivel]
        ax.scatter([num(f["TotalMatriculas"]) for f in sel], [num(f["TasaPerdida"]) * 100 for f in sel],
                   s=55, color=color, edgecolor="white", linewidth=0.6, label=nivel, alpha=0.9, zorder=3)
    ax.axhline(tasa * 100, color=SENA_DARK, ls="--", lw=1.1)
    ax.set_title("Fichas: tamaño vs tasa de pérdida")
    ax.set_xlabel("Matrículas en la ficha")
    ax.set_ylabel("Tasa de pérdida (%)")
    ax.legend(title="Nivel de riesgo", frameon=False, loc="upper left")
    ax.grid(axis="y", color="#E6ECEF", lw=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "03_fichas_dispersion.png")

    # Generaciones
    fig, ax1 = plt.subplots(figsize=(9.6, 4.8))
    gx_lab = [g["generacion"].replace("Generación ", "G") for g in gen_rows]
    g_n = [g["n"] for g in gen_rows]
    g_tasa = [g["tasa_perdida"] * 100 for g in gen_rows]
    ax1.bar(gx_lab, g_n, color="#CFE8C6", edgecolor="white", label="Matrículas")
    ax1.set_ylabel("Matrículas")
    ax1.tick_params(axis="x", rotation=0, labelsize=8)
    ax2 = ax1.twinx()
    ax2.plot(gx_lab, g_tasa, color=RED, marker="o", lw=2, label="Tasa de pérdida")
    ax2.set_ylabel("Tasa de pérdida (%)")
    ax2.set_ylim(0, max(g_tasa) * 1.25 if max(g_tasa) else 100)
    ax1.set_title("Generaciones por prefijo de ficha: volumen y pérdida")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=False, fontsize=9)
    ax1.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    save(fig, "04_generaciones.png")

    # Riesgo vs tasa observada
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    labels = [b["nivel"] for b in bandas_riesgo]
    vals = [b["tasa_perdida"] * 100 for b in bandas_riesgo]
    bars = ax.bar(labels, vals, color=[color_map.get(x, GREY) for x in labels])
    for b, v, meta in zip(bars, vals, bandas_riesgo):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.0,
                f"{v:.1f}%\n(n={meta['n']})", ha="center", va="bottom", fontsize=9)
    ax.set_title("Tasa de pérdida observada por banda de riesgo de ficha")
    ax.set_ylabel("Tasa de pérdida (%)")
    ax.set_ylim(0, max(vals) * 1.35 if max(vals) else 100)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "05_riesgo_bandas.png")

    # Contacto por programa
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    p_contact = sorted(prog_rows, key=lambda x: -sum(1 for r in fact if r["ProgramaID"] == x["programa_id"] and not r["ContactoCompleto"]) / x["matriculas"])
    vals = [sum(1 for r in fact if r["ProgramaID"] == p["programa_id"] and not r["ContactoCompleto"]) / p["matriculas"] * 100 for p in p_contact]
    ax.barh([p["corto"] for p in p_contact], vals, color=ORANGE, alpha=0.85)
    ax.set_title("Contacto incompleto por programa")
    ax.set_xlabel("% de matrículas sin celular válido o correo válido")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "06_calidad_contacto.png")

    # Pareto
    fig, ax1 = plt.subplots(figsize=(8.8, 4.6))
    pp = sorted(prog_rows, key=lambda x: -x["matriculas"])
    xs = [p["corto"] for p in pp]
    ys = [p["matriculas"] for p in pp]
    cum = np.cumsum(ys) / n * 100
    ax1.bar(xs, ys, color=SENA_GREEN, alpha=0.85)
    ax1.set_ylabel("Matrículas")
    ax1.tick_params(axis="x", rotation=35, labelsize=8)
    ax2 = ax1.twinx()
    ax2.plot(xs, cum, color=SENA_DARK, marker="o", lw=1.8)
    ax2.axhline(80, color=GREY, ls=":", lw=1)
    ax2.set_ylabel("% acumulado")
    ax2.set_ylim(0, 105)
    ax1.set_title("Concentración de la matrícula por programa (Pareto)")
    ax1.spines[["top"]].set_visible(False)
    ax2.spines[["top"]].set_visible(False)
    save(fig, "07_pareto_programas.png")

    print("Analisis escrito en", OUT / "03_analisis_estadistico.json")
    print("Tasa global:", f"{tasa*100:.2f}%", f"IC95 [{low*100:.2f}, {high*100:.2f}]")
    print("Chi2 programa p:", chi_prog_asym["p_texto"], "| Monte Carlo p:", round(chi_prog_asym["p_montecarlo"], 4))
    print("Jornada OR:", chi_j["or_diurna_vs_nocturna"], "p:", chi_j["p_texto"])
    print("Contacto OR:", chi_c["or_incompleto_vs_completo"], "p:", chi_c["p_texto"])
    print("Tendencia generaciones p:", ca["p_texto"], "| rho:", round(float(spear_gen.statistic), 3))


if __name__ == "__main__":
    main()
