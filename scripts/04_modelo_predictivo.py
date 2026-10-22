# -*- coding: utf-8 -*-
"""
FASE 4 - Capa predictiva y de priorizacion.
- Probabilidad de perdida por ficha (beta-binomial empirical Bayes + IC creible)
- Modelo logistico regularizado con validacion agrupada por ficha
- Alertas estructurales por aprendiz y priorizacion operativa
- Proyeccion de permanencia por escenarios (NO es pronostico calendario)
Salidas:
  data/processed/DimFicha.csv (actualizado)
  data/processed/FactMatricula.csv (actualizado)
  data/processed/DimAprendiz.csv (actualizado)
  data/processed/FactProyeccionMatricula.csv
  outputs/04_modelo_predictivo.json
  outputs/charts/08..12*.png
"""
import csv
import json
import math
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (brier_score_loss, log_loss, roc_auc_score,
                             roc_curve, confusion_matrix)
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.edgecolor": "#B8C4CC", "axes.labelcolor": "#243B4A",
    "text.color": "#243B4A", "xtick.color": "#4A5C68", "ytick.color": "#4A5C68",
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "savefig.dpi": 180,
})
SENA_GREEN = "#39A900"
SENA_DARK = "#00324D"
ORANGE = "#EF6C00"
RED = "#C62828"
YELLOW = "#F9A825"
GREY = "#78909C"

warnings.filterwarnings("ignore", category=UserWarning)


def read_csv(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(name, rows, columns):
    with (DATA / name).open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(value, digits=4):
    return round(float(value), digits)


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


def make_pipeline(categorical, numeric):
    ct = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False), categorical),
        ("num", StandardScaler(), numeric),
    ], remainder="drop")
    return Pipeline([("ct", ct), ("lr", LogisticRegression(max_iter=5000, C=1.0))])


def fit_metrics(X, y, groups, categorical, numeric):
    pipe = make_pipeline(categorical, numeric)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261019)
    prob = cross_val_predict(pipe, X, y, groups=groups, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]
    auc = roc_auc_score(y, prob)
    brier = brier_score_loss(y, prob)
    ll = log_loss(y, prob, labels=[0, 1])
    base = float(np.mean(y))
    brier_base = brier_score_loss(y, np.full_like(y, base, dtype=float))
    return pipe, prob, {
        "auc": round(float(auc), 4),
        "brier": round(float(brier), 4),
        "brier_base": round(float(brier_base), 4),
        "log_loss": round(float(ll), 4),
        "auc_ganancia_sobre_azar": round(float(auc - 0.5), 4),
    }


def calibration_table(y, prob, bins=10):
    order = np.argsort(prob)
    y = np.asarray(y)[order]
    prob = np.asarray(prob)[order]
    chunks = np.array_split(np.arange(len(y)), bins)
    table = []
    ece = 0.0
    for idx in chunks:
        if len(idx) == 0:
            continue
        mp = float(prob[idx].mean())
        obs = float(y[idx].mean())
        table.append({"n": int(len(idx)), "prob_media": round(mp, 4), "tasa_observada": round(obs, 4),
                      "brecha": round(obs - mp, 4)})
        ece += len(idx) / len(y) * abs(obs - mp)
    return table, round(float(ece), 4)


def bootstrap_auc_by_ficha(y, prob, fichas, reps=1000, seed=20261019):
    rng = np.random.default_rng(seed)
    unique = np.array(sorted(set(fichas)))
    by = defaultdict(list)
    for yy, pp, ff in zip(y, prob, fichas):
        by[ff].append((yy, pp))
    vals = []
    for _ in range(reps):
        sample = rng.choice(unique, size=len(unique), replace=True)
        ys, ps = [], []
        for f in sample:
            for yy, pp in by[f]:
                ys.append(yy)
                ps.append(pp)
        ys = np.array(ys)
        if ys.min() == ys.max():
            continue
        vals.append(roc_auc_score(ys, ps))
    return {"ic95_inf": round(float(np.percentile(vals, 2.5)), 4),
            "ic95_sup": round(float(np.percentile(vals, 97.5)), 4),
            "replicas_validas": len(vals)}


def logistic_se(X, y, coef, intercept):
    """Errores estandar de Wald a partir del Hessiano (no clusterizados)."""
    X1 = np.column_stack([np.ones(len(X)), X])
    beta = np.concatenate([[intercept], coef])
    eta = X1 @ beta
    p = 1 / (1 + np.exp(-eta))
    w = p * (1 - p)
    H = X1.T @ (X1 * w[:, None])
    cov = np.linalg.pinv(H)
    return np.sqrt(np.diag(cov))[1:]


def main():
    fact = read_csv("FactMatricula.csv")
    fichas = read_csv("DimFicha.csv")
    programas = {p["ProgramaID"]: p for p in read_csv("DimPrograma.csv")}
    aprendices = {a["AprendizID"]: a for a in read_csv("DimAprendiz.csv")}
    generaciones = {g["GeneracionID"]: g for g in read_csv("DimGeneracion.csv")}

    n = len(fact)
    y = np.array([int(num(r["EsPerdida"])) for r in fact], dtype=int)
    base_rate = float(y.mean())
    ficha_by_id = {f["FichaID"]: f for f in fichas}
    gen_order = {gid: int(num(g["GeneracionOrden"])) for gid, g in generaciones.items()}

    # ---------- Dataset de modelado ----------
    rows = []
    for r in fact:
        a = aprendices[r["AprendizID"]]
        f = ficha_by_id[r["FichaID"]]
        rows.append({
            "MatriculaID": r["MatriculaID"],
            "AprendizID": r["AprendizID"],
            "FichaID": r["FichaID"],
            "ProgramaID": r["ProgramaID"],
            "Jornada": "DIURNA" if r["JornadaID"] == "J01" else "NOCTURNA",
            "TipoDocumento": a["TipoDocumento"],
            "ContactoCompleto": int(num(r["ContactoCompleto"])),
            "TieneMultiplesFichas": int(num(a["TieneMultiplesFichas"])),
            "DominioGrupo": domain_group(a["EmailDominio"]),
            "TamanoFicha": int(num(f["TotalMatriculas"])),
            "GeneracionOrden": gen_order.get(f["GeneracionID"], 0),
            "TasaContactoIncompletoFicha": num(f["TasaContactoIncompleto"]),
            "EstadoID": r["EstadoID"],
            "NivelRiesgoFicha": f["NivelRiesgo"],
        })
    df = pd.DataFrame(rows)
    df["y"] = y
    groups = df["FichaID"].values

    cat_full = ["ProgramaID", "Jornada", "TipoDocumento", "DominioGrupo"]
    num_full = ["ContactoCompleto", "TieneMultiplesFichas", "TamanoFicha",
                "GeneracionOrden", "TasaContactoIncompletoFicha"]
    cat_ind = ["TipoDocumento", "DominioGrupo"]
    num_ind = ["ContactoCompleto", "TieneMultiplesFichas"]
    cat_struct = ["ProgramaID", "Jornada"]
    num_struct = ["TamanoFicha", "GeneracionOrden", "TasaContactoIncompletoFicha"]

    # Modelo completo
    pipe_full, prob_oof, metrics_full = fit_metrics(df[cat_full + num_full], y, groups, cat_full, num_full)
    # Modelo solo individual (para diagnosticar si hay senal personal)
    _, prob_ind, metrics_ind = fit_metrics(df[cat_ind + num_ind], y, groups, cat_ind, num_ind)
    # Modelo estructural
    _, prob_struct, metrics_struct = fit_metrics(df[cat_struct + num_struct], y, groups, cat_struct, num_struct)

    auc_ci = bootstrap_auc_by_ficha(y, prob_oof, df["FichaID"].values, reps=1000)

    # Calibracion
    cal_table, ece = calibration_table(y, prob_oof)
    logit = np.log(np.clip(prob_oof, 1e-6, 1 - 1e-6) / (1 - np.clip(prob_oof, 1e-6, 1 - 1e-6)))
    calib = LogisticRegression(C=1e6, max_iter=5000).fit(logit.reshape(-1, 1), y)
    cal_slope = float(calib.coef_[0][0])
    cal_intercept = float(calib.intercept_[0])

    # Umbral por indice de Youden
    fpr, tpr, thr = roc_curve(y, prob_oof)
    youden = tpr - fpr
    best_idx = int(np.argmax(youden))
    best_thr = float(thr[best_idx])
    tn, fp, fn, tp = confusion_matrix(y, (prob_oof >= best_thr).astype(int)).ravel()
    sens = tp / (tp + fn) if (tp + fn) else 0
    spec = tn / (tn + fp) if (tn + fp) else 0

    # Coeficientes del modelo completo (ajustado en toda la muestra, solo interpretacion)
    pipe_full.fit(df[cat_full + num_full], y)
    ct = pipe_full.named_steps["ct"]
    lr = pipe_full.named_steps["lr"]
    Xt = ct.transform(df[cat_full + num_full])
    if hasattr(Xt, "toarray"):
        Xt = Xt.toarray()
    se = logistic_se(Xt, y, lr.coef_[0], float(lr.intercept_[0]))
    names = ct.get_feature_names_out()
    coefs = []
    for name, coef, err in zip(names, lr.coef_[0], se):
        coefs.append({
            "raw": str(name),
            "variable": str(name).replace("cat__", "").replace("num__", ""),
            "coeficiente": round(float(coef), 4),
            "or": round(float(math.exp(coef)), 3),
            "or_ic95_inf": round(float(math.exp(coef - 1.96 * err)), 3),
            "or_ic95_sup": round(float(math.exp(coef + 1.96 * err)), 3),
        })
    coefs.sort(key=lambda x: -abs(x["coeficiente"]))
    for c in coefs:
        c["nota"] = "OR por 1 DE en variables numericas; categoria vs referencia en categoricas."
    # Referencias
    refs = {}
    for col in cat_full:
        vals = sorted(df[col].astype(str).unique())
        refs[col] = vals[0] if vals else ""
    # Corregir nombres de categoria (OneHotEncoder usa el valor tal cual)
    for c in coefs:
        for col in cat_full:
            prefix = col + "_"
            if c["variable"].startswith(prefix):
                c["variable"] = f"{col}={c['variable'][len(prefix):]} (ref. {refs[col]})"
                break

    # ---------- Probabilidad por ficha (beta-binomial) ----------
    prior_k = 10
    alpha0 = base_rate * prior_k
    beta0 = (1 - base_rate) * prior_k
    ficha_prob = []
    for f in fichas:
        nf = int(num(f["TotalMatriculas"]))
        yf = int(num(f["Cancelados"])) + int(num(f["Retiros"]))
        a = alpha0 + yf
        b = beta0 + (nf - yf)
        mean = a / (a + b)
        low = float(stats.beta.ppf(0.025, a, b))
        high = float(stats.beta.ppf(0.975, a, b))
        p30 = float(1 - stats.beta.cdf(0.30, a, b))
        p40 = float(1 - stats.beta.cdf(0.40, a, b))
        ficha_prob.append({
            "FichaID": f["FichaID"],
            "ProgramaID": f["ProgramaID"],
            "Jornada": f["Jornada"],
            "GeneracionID": f["GeneracionID"],
            "n": nf,
            "perdidas": yf,
            "tasa_observada": pct(yf / nf if nf else 0),
            "prob_desercion": pct(mean),
            "ic95_inf": pct(low),
            "ic95_sup": pct(high),
            "prob_supera_30": pct(p30),
            "prob_supera_40": pct(p40),
            "nivel_riesgo": f["NivelRiesgo"],
            "ranking": int(num(f["RankingRiesgo"])),
        })
    ficha_prob.sort(key=lambda x: x["ranking"])
    for fp in ficha_prob:
        ficha_by_id[fp["FichaID"]]["ProbDesercionFicha"] = f"{fp['prob_desercion']:.4f}"
        ficha_by_id[fp["FichaID"]]["Prioridad"] = {"Crítico": "P1", "Alto": "P2", "Medio": "P3", "Bajo": "P4"}.get(fp["nivel_riesgo"], "P4")

    # ---------- Alertas por aprendiz (OOF) ----------
    q = np.quantile(prob_oof, [0.25, 0.50, 0.75, 0.90])
    # Bandas absolutas, con ajuste si la distribucion es muy extrema
    thr_alto = max(0.40, float(q[3]))
    thr_medio = max(0.28, float(q[1]))
    if thr_medio >= thr_alto:
        thr_medio = thr_alto - 0.05

    alert_rows = []
    for i, r in enumerate(rows):
        p = float(prob_oof[i])
        if p >= thr_alto:
            nivel = "Alto"
        elif p >= thr_medio:
            nivel = "Medio"
        else:
            nivel = "Bajo"
        nivel_ficha = r["NivelRiesgoFicha"]
        motivos = []
        if nivel_ficha == "Crítico":
            motivos.append("Ficha crítica")
        elif nivel_ficha == "Alto":
            motivos.append("Ficha de alto riesgo")
        if p >= thr_alto:
            motivos.append("Probabilidad estructural alta")
        if not r["ContactoCompleto"]:
            motivos.append("Contacto incompleto")
        if r["EstadoID"] in ("E03", "E04"):
            motivos.append("Estado condicionado/aplazado")
        if nivel_ficha == "Crítico" and (p >= thr_alto or not r["ContactoCompleto"]):
            prioridad = "Inmediata"
        elif nivel_ficha in ("Crítico", "Alto") or p >= thr_alto or not r["ContactoCompleto"]:
            prioridad = "Seguimiento"
        else:
            prioridad = "Rutinaria"
        alert_rows.append({
            "prob": p, "nivel": nivel, "prioridad": prioridad,
            "motivo": "; ".join(motivos) if motivos else "Sin señales de alerta",
            "requiere": 1 if prioridad == "Inmediata" else 0,
        })
    # Ranking dentro de ficha
    by_ficha = defaultdict(list)
    for i, r in enumerate(rows):
        by_ficha[r["FichaID"]].append(i)
    rank_in_ficha = {}
    for f, idxs in by_ficha.items():
        for rank, i in enumerate(sorted(idxs, key=lambda k: (-alert_rows[k]["prob"], rows[k]["MatriculaID"])), start=1):
            rank_in_ficha[i] = rank
    pctl = stats.rankdata([a["prob"] for a in alert_rows], method="average") / len(alert_rows) * 100

    for i, r in enumerate(fact):
        r["ProbPerdidaEstimada"] = f"{alert_rows[i]['prob']:.4f}"
        r["NivelAlertaAprendiz"] = alert_rows[i]["nivel"]
        r["RankingRiesgoFicha"] = rank_in_ficha[i]
        r["PercentilProbabilidad"] = f"{pctl[i]:.1f}"
        r["PrioridadAtencion"] = alert_rows[i]["prioridad"]
        r["MotivoPrioridad"] = alert_rows[i]["motivo"]
        r["RequiereIntervencion"] = alert_rows[i]["requiere"]

    # Agregar a DimAprendiz
    by_ap = defaultdict(list)
    for i, r in enumerate(rows):
        by_ap[r["AprendizID"]].append(i)
    order_nivel = {"Bajo": 1, "Medio": 2, "Alto": 3}
    for aid, a in aprendices.items():
        idxs = by_ap.get(aid, [])
        if not idxs:
            continue
        pmax = max(alert_rows[i]["prob"] for i in idxs)
        nivel = max((alert_rows[i]["nivel"] for i in idxs), key=lambda x: order_nivel[x])
        req = max(alert_rows[i]["requiere"] for i in idxs)
        motivos = []
        for i in idxs:
            for m in alert_rows[i]["motivo"].split("; "):
                if m and m != "Sin señales de alerta" and m not in motivos:
                    motivos.append(m)
        fichas_riesgo = len({rows[i]["FichaID"] for i in idxs if rows[i]["NivelRiesgoFicha"] in ("Alto", "Crítico")})
        a["ProbPerdidaMax"] = f"{pmax:.4f}"
        a["NivelAlertaAprendiz"] = nivel
        a["RequiereIntervencion"] = req
        a["FichasRiesgoAlto"] = fichas_riesgo
        a["MotivoPrioridad"] = "; ".join(motivos) if motivos else "Sin señales de alerta"

    # ---------- Proyeccion de permanencia por escenarios ----------
    # Plateaus: cohortes maduras = orden <= 8 (prefijos 314 a 340)
    mature_gens = {gid for gid, o in gen_order.items() if o <= 8}
    mature = [r for r in fact if r["GeneracionID"] in mature_gens]
    mature_n = len(mature)
    mature_loss = sum(int(num(r["EsPerdida"])) for r in mature)
    global_plateau = mature_loss / mature_n if mature_n else base_rate

    # Plateau por programa, suavizado hacia el global con k=50 aprendices
    prog_mature = defaultdict(lambda: [0, 0])
    for r in mature:
        prog_mature[r["ProgramaID"]][0] += 1
        prog_mature[r["ProgramaID"]][1] += int(num(r["EsPerdida"]))
    plateau_prog = {}
    for pid in programas:
        nn, yy = prog_mature.get(pid, [0, 0])
        plateau_prog[pid] = (yy + 50 * global_plateau) / (nn + 50)

    scenarios = {
        "Optimista": lambda p: max(0.25, p - 0.07),
        "Base": lambda p: p,
        "Pesimista": lambda p: min(0.65, p + 0.07),
    }
    proj_rows = []
    for esc, fn in scenarios.items():
        for f in fichas:
            fid = f["FichaID"]
            nn = int(num(f["TotalMatriculas"]))
            perd = int(num(f["Cancelados"])) + int(num(f["Retiros"]))
            vinc = int(num(f["AprendicesVinculados"]))
            p_obs = perd / nn if nn else 0
            plateau = fn(plateau_prog[f["ProgramaID"]])
            q_add = max(0.0, (plateau - p_obs) / (1 - p_obs)) if p_obs < 1 else 0.0
            add = vinc * q_add
            proj_rows.append({
                "Escenario": esc,
                "FichaID": fid,
                "ProgramaID": f["ProgramaID"],
                "GeneracionID": f["GeneracionID"],
                "Jornada": f["Jornada"],
                "NivelRiesgo": f["NivelRiesgo"],
                "Matriculas": nn,
                "PerdidasObservadas": perd,
                "TasaObservada": f"{p_obs:.4f}",
                "PoblacionVinculada": vinc,
                "TasaFinalSupuesta": f"{plateau:.4f}",
                "PerdidaAdicionalEsperada": f"{add:.1f}",
                "PoblacionProyectada": f"{vinc - add:.1f}",
                "TasaProyectada": f"{(perd + add) / nn if nn else 0:.4f}",
                "Nota": "Escenario de permanencia; no es pronostico calendario ni de nueva matricula.",
            })

    def summarize(scenario):
        sel = [r for r in proj_rows if r["Escenario"] == scenario]
        vinc = sum(int(num(r["PoblacionVinculada"])) for r in sel)
        add = sum(num(r["PerdidaAdicionalEsperada"]) for r in sel)
        perd = sum(int(num(r["PerdidasObservadas"])) for r in sel)
        mat = sum(int(num(r["Matriculas"])) for r in sel)
        return {
            "escenario": scenario,
            "poblacion_vinculada": vinc,
            "perdida_adicional_esperada": round(add, 1),
            "poblacion_proyectada": round(vinc - add, 1),
            "tasa_proyectada": pct((perd + add) / mat if mat else 0),
        }

    summary_scenarios = [summarize(e) for e in ["Optimista", "Base", "Pesimista"]]
    by_program = []
    for pid, p in programas.items():
        sel = [r for r in proj_rows if r["Escenario"] == "Base" and r["ProgramaID"] == pid]
        if not sel:
            continue
        vinc = sum(int(num(r["PoblacionVinculada"])) for r in sel)
        add = sum(num(r["PerdidaAdicionalEsperada"]) for r in sel)
        perd = sum(int(num(r["PerdidasObservadas"])) for r in sel)
        mat = sum(int(num(r["Matriculas"])) for r in sel)
        by_program.append({
            "ProgramaID": pid, "programa": p["ProgramaNombre"],
            "matriculas": mat, "perdidas_observadas": perd,
            "poblacion_vinculada": vinc, "perdida_adicional": round(add, 1),
            "poblacion_proyectada": round(vinc - add, 1),
            "tasa_observada": pct(perd / mat if mat else 0),
            "tasa_proyectada": pct((perd + add) / mat if mat else 0),
            "plateau_base": pct(plateau_prog[pid]),
        })
    by_program.sort(key=lambda x: -x["poblacion_vinculada"])

    by_generation = []
    for gid, g in generaciones.items():
        sel = [r for r in proj_rows if r["Escenario"] == "Base" and r["GeneracionID"] == gid]
        if not sel:
            continue
        vinc = sum(int(num(r["PoblacionVinculada"])) for r in sel)
        add = sum(num(r["PerdidaAdicionalEsperada"]) for r in sel)
        perd = sum(int(num(r["PerdidasObservadas"])) for r in sel)
        mat = sum(int(num(r["Matriculas"])) for r in sel)
        by_generation.append({
            "GeneracionID": gid, "generacion": g["GeneracionNombre"],
            "orden": int(num(g["GeneracionOrden"])),
            "matriculas": mat, "perdidas_observadas": perd,
            "poblacion_vinculada": vinc, "perdida_adicional": round(add, 1),
            "poblacion_proyectada": round(vinc - add, 1),
            "tasa_observada": pct(perd / mat if mat else 0),
            "tasa_proyectada": pct((perd + add) / mat if mat else 0),
        })
    by_generation.sort(key=lambda x: x["orden"])

    # ---------- Escritura de CSV ----------
    write_csv("FactProyeccionMatricula.csv", proj_rows, list(proj_rows[0].keys()))

    ficha_cols = list(fichas[0].keys())
    for col in ["ProbDesercionICInf", "ProbDesercionICSup", "ProbSupera30", "ProbSupera40"]:
        if col not in ficha_cols:
            ficha_cols.append(col)
    fp_by = {x["FichaID"]: x for x in ficha_prob}
    for f in fichas:
        x = fp_by[f["FichaID"]]
        f["ProbDesercionICInf"] = f"{x['ic95_inf']:.4f}"
        f["ProbDesercionICSup"] = f"{x['ic95_sup']:.4f}"
        f["ProbSupera30"] = f"{x['prob_supera_30']:.4f}"
        f["ProbSupera40"] = f"{x['prob_supera_40']:.4f}"
    write_csv("DimFicha.csv", fichas, ficha_cols)

    fact_cols = list(fact[0].keys())
    for col in ["ProbPerdidaEstimada", "NivelAlertaAprendiz", "RankingRiesgoFicha",
                "PercentilProbabilidad", "PrioridadAtencion", "MotivoPrioridad", "RequiereIntervencion"]:
        if col not in fact_cols:
            fact_cols.append(col)
    write_csv("FactMatricula.csv", fact, fact_cols)

    ap_cols = list(aprendices[list(aprendices)[0]].keys())
    for col in ["ProbPerdidaMax", "NivelAlertaAprendiz", "RequiereIntervencion",
                "FichasRiesgoAlto", "MotivoPrioridad"]:
        if col not in ap_cols:
            ap_cols.append(col)
    write_csv("DimAprendiz.csv", list(aprendices.values()), ap_cols)

    # ---------- JSON ----------
    alert_counts = Counter(a["nivel"] for a in alert_rows)
    priority_counts = Counter(a["prioridad"] for a in alert_rows)
    conf = confusion_matrix(y, (prob_oof >= best_thr).astype(int)).ravel()
    result = {
        "metadata": {
            "fecha_reporte": "2026-10-19",
            "filas": n,
            "eventos": int(y.sum()),
            "tasa_base": pct(base_rate),
            "validacion": "StratifiedGroupKFold(5) agrupado por FichaID; predicciones out-of-fold.",
            "advertencia": ("Un solo snapshot sin etiquetas historicas. El modelo aprende diferencias "
                            "estructurales entre fichas/programas, no trayectorias individuales. "
                            "No usar para negar cupos, certificar ni sancionar."),
        },
        "modelo_principal": {
            **metrics_full,
            "auc_ic95_bootstrap_ficha": auc_ci,
            "ece": ece,
            "calibracion_slope": round(cal_slope, 3),
            "calibracion_intercepto": round(cal_intercept, 3),
            "umbral_youden": round(best_thr, 4),
            "sensibilidad_youden": round(float(sens), 3),
            "especificidad_youden": round(float(spec), 3),
            "matriz_confusion_youden": {"tn": int(conf[0]), "fp": int(conf[1]),
                                        "fn": int(conf[2]), "tp": int(conf[3])},
            "calibracion_deciles": cal_table,
            "variables": cat_full + num_full,
            "referencias_categoricas": refs,
        },
        "modelo_individual": {
            **metrics_ind,
            "variables": cat_ind + num_ind,
            "conclusion": ("AUC cercano a 0.5: las variables individuales disponibles (tipo de documento, "
                           "contacto, multiples fichas, dominio de correo) no discriminan la perdida. "
                           "La senal predictiva es estructural (programa/jornada/cohorte)."),
        },
        "modelo_estructural": {
            **metrics_struct,
            "variables": cat_struct + num_struct,
            "conclusion": ("Modelo sin variables individuales; sirve para priorizar fichas, no personas."),
        },
        "coeficientes": coefs,
        "distribucion_probabilidad": {
            "min": round(float(prob_oof.min()), 4),
            "p25": round(float(q[0]), 4),
            "mediana": round(float(q[1]), 4),
            "p75": round(float(q[2]), 4),
            "p90": round(float(q[3]), 4),
            "max": round(float(prob_oof.max()), 4),
            "umbral_alerta_alto": round(thr_alto, 4),
            "umbral_alerta_medio": round(thr_medio, 4),
            "conteo_bandas": dict(alert_counts),
            "conteo_prioridad": dict(priority_counts),
        },
        "ficha_probabilidades": ficha_prob,
        "prior_parametros": {"k_prior": prior_k, "alpha0": round(alpha0, 3),
                             "beta0": round(beta0, 3), "tasa_global": pct(base_rate)},
        "proyeccion": {
            "supuestos": {
                "plateau_global": pct(global_plateau),
                "plateau_global_n": mature_n,
                "plateau_global_perdidas": mature_loss,
                "cohortes_maduras": sorted(mature_gens, key=lambda x: gen_order[x]),
                "k_suavizado_programa": 50,
                "escenarios": {"Optimista": "plateau - 7 pp", "Base": "plateau por programa",
                               "Pesimista": "plateau + 7 pp"},
                "nota": ("Proyeccion de permanencia de la poblacion ya vinculada. No proyecta nueva "
                         "matricula ni fechas de cierre: la fuente no tiene fecha de matricula, "
                         "fecha de retiro ni periodo academico."),
            },
            "resumen_escenarios": summary_scenarios,
            "por_programa_base": by_program,
            "por_generacion_base": by_generation,
            "plateau_por_programa": {pid: pct(v) for pid, v in plateau_prog.items()},
        },
        "pronostico_nueva_matricula": {
            "estimable": False,
            "motivo": ("No hay serie temporal ni fecha/periodo de matricula. Con un solo snapshot no se "
                       "puede identificar la tendencia de ingreso ni la estacionalidad."),
            "variables_requeridas": [
                "Fecha de matricula o periodo academico",
                "Fecha de inicio y fin de ficha",
                "Cupos ofertados y matriculados por periodo",
                "Meta de admision y capacidad instalada",
                "Fecha y motivo de retiro/cancelacion",
            ],
            "alternativa_entregada": "Proyeccion de permanencia por escenarios (FactProyeccionMatricula).",
        },
        "limitaciones": [
            "Snapshot unico: no hay validacion temporal ni etiquetas historicas independientes.",
            "La validacion agrupada por ficha evita fuga de informacion, pero solo hay 56 fichas.",
            "El AUC mide ordenamiento, no causalidad; el modelo no prueba que intervenir reduzca la desercion.",
            "Las variables individuales disponibles no discriminan; el score es estructural.",
            "La proyeccion supone que las cohortes jovenes convergen al plateau de las maduras; es un escenario.",
            "La fuente no tiene genero, edad, municipio, fecha de matricula ni certificacion.",
        ],
    }
    (OUT / "04_modelo_predictivo.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---------- Graficos ----------
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(CHARTS / name, bbox_inches="tight")
        plt.close(fig)

    # ROC
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    ax.plot(fpr, tpr, color=SENA_GREEN, lw=2.2, label=f"Modelo (AUC={metrics_full['auc']:.3f})")
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", lw=1, label="Azar (AUC=0.500)")
    ax.set_xlabel("Tasa de falsos positivos")
    ax.set_ylabel("Tasa de verdaderos positivos")
    ax.set_title("Curva ROC - validacion agrupada por ficha")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "08_modelo_roc.png")

    # Calibracion
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    mp = [c["prob_media"] for c in cal_table]
    ob = [c["tasa_observada"] for c in cal_table]
    ax.plot([0, 0.7], [0, 0.7], color=GREY, ls="--", lw=1, label="Calibracion perfecta")
    ax.plot(mp, ob, color=SENA_DARK, marker="o", lw=2, label=f"Modelo (ECE={ece:.3f})")
    ax.set_xlabel("Probabilidad predicha")
    ax.set_ylabel("Tasa observada")
    ax.set_title("Calibracion por deciles (out-of-fold)")
    ax.legend(frameon=False, loc="upper left")
    ax.set_xlim(0, max(0.7, max(mp) * 1.1))
    ax.set_ylim(0, max(0.7, max(ob) * 1.1))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "09_modelo_calibracion.png")

    # Top fichas: probabilidad + IC
    top = ficha_prob[:15]
    fig, ax = plt.subplots(figsize=(8.6, 5.8))
    labels = [f"{x['FichaID']} ({x['n']})" for x in top][::-1]
    vals = [x["prob_desercion"] * 100 for x in top][::-1]
    lows = [(x["prob_desercion"] - x["ic95_inf"]) * 100 for x in top][::-1]
    highs = [(x["ic95_sup"] - x["prob_desercion"]) * 100 for x in top][::-1]
    colors = [RED if x["nivel_riesgo"] == "Crítico" else ORANGE for x in top][::-1]
    ax.barh(labels, vals, color=colors, alpha=0.9)
    ax.errorbar(vals, labels, xerr=[lows, highs], fmt="none", ecolor=SENA_DARK, capsize=3, lw=1)
    ax.axvline(base_rate * 100, color=SENA_DARK, ls="--", lw=1, label=f"Global {base_rate*100:.1f}%")
    ax.set_xlabel("Probabilidad posterior de pérdida (%)")
    ax.set_title("Fichas prioritarias: probabilidad de pérdida e IC 95%")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "10_fichas_probabilidad.png")

    # Escenarios
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    labels = [s["escenario"] for s in summary_scenarios]
    vals = [s["poblacion_proyectada"] for s in summary_scenarios]
    bars = ax.bar(labels, vals, color=[SENA_GREEN, SENA_DARK, ORANGE])
    for b, s in zip(bars, summary_scenarios):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 8,
                f"{s['poblacion_proyectada']:,.0f}\n(-{s['perdida_adicional_esperada']:.0f})".replace(",", "."),
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_ylabel("Población vinculada proyectada")
    ax.set_title("Proyección de permanencia por escenario")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "11_proyeccion_escenarios.png")

    # Coeficientes interpretables (odds ratios con IC)
    selected = ["num__GeneracionOrden", "num__ContactoCompleto", "num__TieneMultiplesFichas",
                "num__TamanoFicha", "num__TasaContactoIncompletoFicha",
                "cat__Jornada_NOCTURNA", "cat__TipoDocumento_TI", "cat__TipoDocumento_PPT",
                "cat__DominioGrupo_Gmail", "cat__DominioGrupo_Hotmail/Outlook"]
    topc = [c for c in coefs if c["raw"] in selected]
    if topc:
        topc = sorted(topc, key=lambda c: c["or"])
        fig, ax = plt.subplots(figsize=(8.8, 5.4))
        vals = [c["or"] for c in topc]
        lows = [c["or_ic95_inf"] for c in topc]
        highs = [c["or_ic95_sup"] for c in topc]
        labels = [c["variable"] for c in topc]
        colors = [RED if v > 1 else SENA_GREEN for v in vals]
        ax.errorbar(vals, labels, xerr=[np.array(vals) - np.array(lows), np.array(highs) - np.array(vals)],
                    fmt="o", color=SENA_DARK, ecolor=GREY, capsize=3, ms=7, lw=1.4)
        for y, (v, c) in enumerate(zip(vals, topc)):
            ax.plot([v], [y], "o", color=RED if v > 1 else SENA_GREEN, ms=8, zorder=3)
        ax.axvline(1, color=SENA_DARK, ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_xlabel("Odds ratio (escala logarítmica)")
        ax.set_title("Variables interpretables asociadas a la pérdida (IC 95%)")
        ax.spines[["top", "right"]].set_visible(False)
        save(fig, "12_coeficientes.png")

    print("Modelo escrito en", OUT / "04_modelo_predictivo.json")
    print("AUC:", metrics_full["auc"], "| IC bootstrap:", auc_ci, "| Brier:", metrics_full["brier"],
          "| base:", metrics_full["brier_base"])
    print("Modelo individual AUC:", metrics_ind["auc"], "| estructural AUC:", metrics_struct["auc"])
    print("Bandas:", dict(alert_counts), "| Prioridad:", dict(priority_counts))
    print("Proyeccion base:", summary_scenarios[1])


if __name__ == "__main__":
    main()
