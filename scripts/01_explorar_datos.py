# -*- coding: utf-8 -*-
"""
FASE 1 - Auditoria y exploracion de los reportes de aprendices SENA.
Genera outputs/01_exploracion.json con evidencia verificable.
"""
import collections
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

import xlrd

RAW_DIR = Path(r"C:\Users\capatino\Desktop\Base de datos aprendices centro")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DOC_RE = re.compile(r"Aprendices_(\d+)_([^_]+)_(.+)\.xls$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def clean(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", " ", str(value)).strip()


def norm_key(value):
    text = clean(value).upper()
    text = text.replace("Á", "A").replace("É", "E").replace("Í", "I")
    text = text.replace("Ó", "O").replace("Ú", "U").replace("Ü", "U")
    text = text.replace("Ñ", "N")
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def main():
    files = sorted(RAW_DIR.glob("*.xls"))
    rows = []
    fichas = []
    errors = []

    for path in files:
        match = DOC_RE.match(path.name)
        if not match:
            errors.append({"archivo": path.name, "error": "Nombre no cumple patron"})
            continue
        ficha_name, jornada, programa_slug = match.groups()
        try:
            wb = xlrd.open_workbook(str(path))
            sh = wb.sheet_by_index(0)
        except Exception as exc:  # pragma: no cover
            errors.append({"archivo": path.name, "error": repr(exc)})
            continue

        title = clean(sh.cell_value(1, 2)) if sh.nrows > 1 else ""
        ficha_title = title.split(" - ")[0].strip()
        programa_title = title.split(" - ", 1)[1].strip() if " - " in title else ""
        estado_ficha = clean(sh.cell_value(2, 2)) if sh.nrows > 2 else ""
        fecha_raw = sh.cell_value(3, 2) if sh.nrows > 3 else ""
        try:
            fecha = xlrd.xldate_as_datetime(fecha_raw, wb.datemode).date().isoformat()
        except Exception:
            fecha = clean(fecha_raw)

        header_row = None
        for r in range(min(12, sh.nrows)):
            if norm_key(sh.cell_value(r, 0)).startswith("TIPO DE DOCUMENTO"):
                header_row = r
                break
        if header_row is None:
            errors.append({"archivo": path.name, "error": "No se encontro encabezado"})
            continue

        headers = [clean(sh.cell_value(header_row, c)) for c in range(sh.ncols)]
        n_rows = 0
        for r in range(header_row + 1, sh.nrows):
            values = [sh.cell_value(r, c) for c in range(sh.ncols)]
            if not any(clean(v) for v in values):
                continue
            record = dict(zip(headers, values))
            # Acceso por posicion para no depender de la codificacion de tildes.
            tipo_doc = clean(values[0])
            num_doc = clean(values[1])
            nombres = clean(values[2])
            apellidos = clean(values[3])
            celular = clean(values[4])
            correo = clean(values[5]).lower()
            estado = clean(values[6]).upper()
            rows.append({
                "archivo": path.name,
                "ficha": ficha_name,
                "ficha_titulo": ficha_title,
                "jornada": jornada.upper(),
                "programa_slug": programa_slug,
                "programa_titulo": programa_title,
                "estado_ficha": estado_ficha,
                "fecha_reporte": fecha,
                "tipo_documento": tipo_doc,
                "documento": num_doc,
                "nombres": nombres,
                "apellidos": apellidos,
                "celular": celular,
                "correo": correo,
                "estado": estado,
            })
            n_rows += 1
        fichas.append({
            "archivo": path.name,
            "ficha": ficha_name,
            "ficha_titulo": ficha_title,
            "jornada": jornada.upper(),
            "programa_titulo": programa_title,
            "programa_slug": programa_slug,
            "estado_ficha": estado_ficha,
            "fecha_reporte": fecha,
            "filas": n_rows,
            "columnas": sh.ncols,
            "encabezado_fila": header_row,
        })

    # Duplicados
    doc_counts = collections.Counter(r["documento"] for r in rows if r["documento"])
    dup_docs = {d: n for d, n in doc_counts.items() if n > 1}
    same_ficha_dups = []
    seen = collections.Counter((r["ficha"], r["documento"]) for r in rows if r["documento"])
    for (ficha, doc), n in seen.items():
        if n > 1:
            same_ficha_dups.append({"ficha": ficha, "documento": doc, "n": n})
    cross_ficha = {}
    for doc, n in dup_docs.items():
        fs = sorted({r["ficha"] for r in rows if r["documento"] == doc})
        if len(fs) > 1:
            cross_ficha[doc] = fs

    # Calidad
    email_valid = [r for r in rows if EMAIL_RE.match(r["correo"])]
    email_counts = collections.Counter(r["correo"] for r in rows if r["correo"])
    email_dups = {e: n for e, n in email_counts.items() if n > 1}
    phone_digits = [re.sub(r"\D", "", r["celular"]) for r in rows if r["celular"]]
    phone_valid = [p for p in phone_digits if len(p) == 10 and p.startswith("3")]
    doc_lengths = collections.Counter(len(re.sub(r"\D", "", r["documento"])) for r in rows)
    names_norm = collections.Counter(norm_key(r["nombres"] + " " + r["apellidos"]) for r in rows)
    name_repeats = {k: v for k, v in names_norm.items() if v > 1}

    summary = {
        "fuente": str(RAW_DIR),
        "archivos": len(files),
        "filas": len(rows),
        "fichas": len(fichas),
        "fichas_unicas": len({f["ficha"] for f in fichas}),
        "programas": len({f["programa_titulo"] for f in fichas}),
        "jornadas": dict(collections.Counter(f["jornada"] for f in fichas)),
        "estados_ficha": dict(collections.Counter(f["estado_ficha"] for f in fichas)),
        "fechas_reporte": dict(collections.Counter(f["fecha_reporte"] for f in fichas)),
        "tamano_ficha": {
            "min": min(f["filas"] for f in fichas),
            "max": max(f["filas"] for f in fichas),
            "total": sum(f["filas"] for f in fichas),
        },
        "columnas": sorted({h for h in [
            "Tipo de Documento", "Número de Documento", "Nombre", "Apellidos",
            "Celular", "Correo Electrónico", "Estado"
        ]}),
        "estados_aprendiz": dict(collections.Counter(r["estado"] for r in rows)),
        "tipos_documento": dict(collections.Counter(r["tipo_documento"] for r in rows)),
        "documentos": {
            "distintos": len(doc_counts),
            "duplicados": len(dup_docs),
            "filas_duplicadas": sum(dup_docs.values()),
            "duplicados_misma_ficha": len(same_ficha_dups),
            "duplicados_entre_fichas": len(cross_ficha),
            "longitudes": dict(doc_lengths),
            "vacios": sum(1 for r in rows if not r["documento"]),
        },
        "contacto": {
            "celular_vacio": sum(1 for r in rows if not r["celular"]),
            "celular_valido": len(phone_valid),
            "celular_longitudes": dict(collections.Counter(len(p) for p in phone_digits)),
            "correo_vacio": sum(1 for r in rows if not r["correo"]),
            "correo_valido": len(email_valid),
            "correo_duplicado": len(email_dups),
            "dominios": dict(collections.Counter(r["correo"].split("@")[-1] for r in rows if "@" in r["correo"]).most_common(12)),
            "nombres_repetidos": len(name_repeats),
        },
        "programas_detalle": sorted(
            [{"programa": k, "fichas": sum(1 for f in fichas if f["programa_titulo"] == k),
              "aprendices": sum(f["filas"] for f in fichas if f["programa_titulo"] == k)}
             for k in {f["programa_titulo"] for f in fichas}],
            key=lambda x: x["aprendices"], reverse=True),
        "fichas_detalle": sorted(fichas, key=lambda f: f["ficha"]),
        "duplicados_misma_ficha": same_ficha_dups[:20],
        "duplicados_entre_fichas": [
            {"documento": d, "fichas": fs} for d, fs in list(cross_ficha.items())[:20]
        ],
        "errores": errors,
        "filas_muestra": rows[:5],
    }
    (OUT_DIR / "01_exploracion.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # Respaldo de filas para las siguientes fases (sin publicar)
    restricted = Path(__file__).resolve().parents[1] / "data" / "restricted"
    restricted.mkdir(parents=True, exist_ok=True)
    (restricted / "aprendices_crudos.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("Archivos:", summary["archivos"])
    print("Filas:", summary["filas"], "| Fichas:", summary["fichas"], "| Programas:", summary["programas"])
    print("Estados:", summary["estados_aprendiz"])
    print("Documentos distintos:", summary["documentos"]["distintos"],
          "| dup misma ficha:", summary["documentos"]["duplicados_misma_ficha"],
          "| dup entre fichas:", summary["documentos"]["duplicados_entre_fichas"])
    print("Celular vacio:", summary["contacto"]["celular_vacio"],
          "| Correo invalido:", summary["filas"] - summary["contacto"]["correo_valido"])
    print("JSON ->", OUT_DIR / "01_exploracion.json")


if __name__ == "__main__":
    main()
