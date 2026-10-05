"""Datos para el tablero ejecutivo (docs/tablero.html).
Recalcula las series desde data/raw con las mismas reglas que analisis/carrusel.py
y escribe analisis/tablero.json. Uso: python analisis/tablero_datos.py
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
CORTE = "2026-09-27"  # última semana completa; los días siguientes tienen rezago de carga

d = pd.read_csv(os.path.join(RAW, "urg_chile_hospital_dia.csv"), dtype={"id_establecimiento": str})
d["id"] = d.id_establecimiento.str.strip()
d["fecha"] = pd.to_datetime(d.fecha)
d = d.groupby(["id", "fecha"], as_index=False)[["atenciones", "resp", "hosp", "cirugias"]].sum()
d["anio"] = d.fecha.dt.year
hd = pd.read_csv(os.path.join(RAW, "hospitales.csv"), dtype={"id_establecimiento": str})
hd["id"] = hd.id_establecimiento.str.strip()
hd = hd.drop_duplicates("id").set_index("id")
edad = pd.read_csv(os.path.join(RAW, "hospital_edad_ene_sep.csv")).set_index(["anio", "seccion"])
red = pd.read_csv(os.path.join(RAW, "red_urgencia_anual_tipo.csv"))

out = {}

# 1. Línea base enero-septiembre por año
es = d[d.fecha.dt.month <= 9].groupby("anio").agg(aten=("atenciones", "sum"), ho=("hosp", "sum"),
                                                 ci=("cirugias", "sum"), dias=("fecha", "nunique"))
out["anual"] = [{"anio": int(y), "aten_dia": round(r.aten / r.dias), "hosp_dia": round(r.ho / r.dias),
                 "tasa": round(100 * r.ho / r.aten, 2), "cirugias": int(r.ci)} for y, r in es.iterrows()]
assert es.loc[2019, "aten"] == 5700840

# 2. Semanal con carta I-MR
n = d.groupby("fecha")[["atenciones", "resp", "hosp"]].sum()
wk = n.resample("W-SUN").agg(["sum", "count"])
wk = wk[wk[("atenciones", "count")] == 7]
wk = pd.DataFrame({c: wk[(c, "sum")] for c in ["atenciones", "resp", "hosp"]})["2024-01-01":CORTE]


def imr(x):
    mrb = x.diff().abs().mean()
    m = x.mean()
    return {"media": round(m), "lcs": round(m + 2.66 * mrb), "lci": round(m - 2.66 * mrb)}


out["limites"] = {"hosp": imr(wk.hosp), "aten": imr(wk.atenciones)}
out["semanas"] = [{"s": str(i.date()), "a": int(r.atenciones), "h": int(r.hosp), "r": int(r.resp)} for i, r in wk.iterrows()]
assert len(wk) == 143

# 3. Día de la semana (índice vs promedio)
nd = d[(d.fecha >= "2023-01-01") & (d.fecha <= CORTE)].groupby("fecha")[["atenciones", "hosp"]].sum()
dow = nd.groupby(nd.index.dayofweek).mean() / nd.mean()
out["dow"] = [{"d": i, "a": round(100 * (r.atenciones - 1), 1), "h": round(100 * (r.hosp - 1), 1)} for i, r in dow.iterrows()]

# 4. Edad: consultas y tasa de internación por grupo
g = ["menores_1", "de_1_a_4", "de_5_a_14", "de_15_a_64", "de_65_y_mas"]
out["edad"] = []
for c in g:
    row = {"grupo": c}
    for y in (2019, 2026):
        a, h = edad.loc[(y, "atenciones"), c], edad.loc[(y, "hospitalizaciones"), c]
        row[f"at{y}"], row[f"ho{y}"], row[f"tasa{y}"] = int(a), int(h), round(100 * h / a, 2)
    out["edad"].append(row)

# 5. Regiones 2025: consultas y tasa de internación
d25 = d[d.anio == 2025].join(hd[["region"]], on="id")
rg = d25.groupby("region")[["atenciones", "hosp"]].sum()
rg["tasa"] = 100 * rg.hosp / rg.atenciones
out["regiones"] = [{"region": k, "at": int(r.atenciones), "tasa": round(r.tasa, 2)}
                   for k, r in rg.sort_values("tasa", ascending=False).iterrows()]
assert d25.region.notna().all()

# 6. Pareto y top hospitales 2025
h25 = d25.groupby("id")[["atenciones", "hosp"]].sum().sort_values("atenciones", ascending=False)
cum = (h25.atenciones.cumsum() / h25.atenciones.sum()).round(4)
out["pareto"] = cum.tolist()
top = h25.head(12).join(hd[["nombre", "region"]])
out["top"] = [{"nombre": r.nombre, "region": r.region, "at": int(r.atenciones),
               "tasa": round(100 * r.hosp / r.atenciones, 2)} for _, r in top.iterrows()]

# 7. Red completa por tipo de establecimiento
out["red"] = red.to_dict(orient="records")

with open(os.path.join(ROOT, "analisis", "tablero.json"), "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print({k: (len(v) if isinstance(v, list) else v) for k, v in out.items()})

# Render del tablero: inserta los datos y el estado del monitor de Make
estado = {"__CHEQUEO__": "05/10/2026 11:03 (Chile)", "__VERSION__": "05/10/2026 · 42 MB"}
tpl = open(os.path.join(ROOT, "docs", "tablero_template.html"), encoding="utf-8").read()
html = tpl.replace("__DATA__", json.dumps(out, ensure_ascii=False, separators=(",", ":")))
for k, v in estado.items():
    html = html.replace(k, v)
with open(os.path.join(ROOT, "docs", "tablero.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("docs/tablero.html", len(html))
