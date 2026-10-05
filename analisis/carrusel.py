"""Análisis y carrusel LinkedIn (1080x1350): urgencias de la red pública de Chile, 2019-2026.
Fuente: DEIS-Minsal, Atenciones de urgencia (DAU). Todas las cifras se calculan acá a partir de data/raw.
Uso: python analisis/carrusel.py  ->  docs/img/slide_XX.png, docs/Carrusel_Urgencias_Chile.pdf, analisis/kpis.json
"""
import json
import os

import img2pdf
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

FD = "/usr/share/fonts/truetype/google-fonts/"
for f in ["Poppins-Regular.ttf", "Poppins-Medium.ttf", "Poppins-Bold.ttf"]:
    if os.path.exists(FD + f):
        fm.fontManager.addfont(FD + f)
plt.rcParams["font.family"] = "Poppins"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "docs", "img")
os.makedirs(OUT, exist_ok=True)

BG, NAVY, INK2, MUTED, GRID = "#F6F4EF", "#0B2545", "#4A5568", "#8A94A6", "#E3E0D8"
BLUE, ORANGE, PALEBLUE, PALEORANGE, RED = "#1F5FA8", "#D9731A", "#C9D8EC", "#F2C9A5", "#C0392B"
AUTHOR = "Emiliano Pérez Alaniz"
SOURCE = "Fuente: DEIS-Minsal Chile, atenciones de urgencia 2019-2026 · Cálculo propio"
N = 12

# ------------------------------------------------------------------ datos
d = pd.read_csv(os.path.join(RAW, "urg_chile_hospital_dia.csv"), dtype={"id_establecimiento": str})
d["id"] = d.id_establecimiento.str.strip()
d["fecha"] = pd.to_datetime(d.fecha)
d = d.groupby(["id", "fecha"], as_index=False)[["atenciones", "resp", "hosp", "cirugias"]].sum()
d["anio"] = d.fecha.dt.year
edad = pd.read_csv(os.path.join(RAW, "hospital_edad_ene_sep.csv")).set_index(["anio", "seccion"])
red = pd.read_csv(os.path.join(RAW, "red_urgencia_anual_tipo.csv"))

# Línea base comparable: enero a septiembre
es = d[d.fecha.dt.month <= 9].groupby("anio").agg(atenciones=("atenciones", "sum"), hosp=("hosp", "sum"),
                                                   cirugias=("cirugias", "sum"), resp=("resp", "sum"),
                                                   dias=("fecha", "nunique"))
es["aten_dia"] = es.atenciones / es.dias
es["hosp_dia"] = es.hosp / es.dias
es["tasa"] = 100 * es.hosp / es.atenciones
YRS = list(es.index)

# Validación cruzada: dos extracciones independientes deben coincidir
assert es.loc[2019, "atenciones"] == edad.loc[(2019, "atenciones"), "total"] == 5700840
assert es.loc[2026, "hosp"] == edad.loc[(2026, "hospitalizaciones"), "total"]

ch = lambda col: 100 * (es.loc[2026, col] / es.loc[2019, col] - 1)
K = {
    "atenciones_total": int(d.atenciones.sum()),
    "hosp_total": int(d.hosp.sum()),
    "hospitales": int(d.id.nunique()),
    "aten_dia_19": es.loc[2019, "aten_dia"], "aten_dia_26": es.loc[2026, "aten_dia"],
    "hosp_dia_19": es.loc[2019, "hosp_dia"], "hosp_dia_26": es.loc[2026, "hosp_dia"],
    "chg_aten": ch("aten_dia"), "chg_hosp": ch("hosp_dia"), "chg_cir": ch("cirugias"),
    "tasa_19": es.loc[2019, "tasa"], "tasa_26": es.loc[2026, "tasa"],
}

# Edad
g = ["menores_1", "de_1_a_4", "de_5_a_14", "de_15_a_64", "de_65_y_mas"]
at = {y: edad.loc[(y, "atenciones"), g] for y in (2019, 2026)}
ho = {y: edad.loc[(y, "hospitalizaciones"), g] for y in (2019, 2026)}
K["share65_19"] = 100 * at[2019].de_65_y_mas / at[2019].sum()
K["share65_26"] = 100 * at[2026].de_65_y_mas / at[2026].sum()
K["chg_65"] = 100 * (at[2026].de_65_y_mas / at[2019].de_65_y_mas - 1)
K["chg_u5"] = 100 * ((at[2026].menores_1 + at[2026].de_1_a_4) / (at[2019].menores_1 + at[2019].de_1_a_4) - 1)
K["chg_hosp65"] = 100 * (ho[2026].de_65_y_mas / ho[2019].de_65_y_mas - 1)
r19, r26 = ho[2019] / at[2019], ho[2026] / at[2026]
mix_only = 100 * (r19 * at[2026]).sum() / at[2026].sum()
K["pct_por_edad"] = 100 * (mix_only - K["tasa_19"]) / (K["tasa_26"] - K["tasa_19"])
K["tasa_1564_19"], K["tasa_1564_26"] = 100 * r19.de_15_a_64, 100 * r26.de_15_a_64
K["tasa_65_19"], K["tasa_65_26"] = 100 * r19.de_65_y_mas, 100 * r26.de_65_y_mas

# Día de la semana (2023 en adelante)
nd = d[(d.fecha >= "2023-01-01") & (d.fecha <= "2026-09-27")].groupby("fecha")[["atenciones", "hosp"]].sum()
dow = nd.groupby(nd.index.dayofweek).mean() / nd.mean()
K["lunes"] = 100 * (dow.atenciones[0] - 1)
K["finde"] = 100 * (dow.atenciones[[5, 6]].mean() - 1)

# Semanal 2024-2026 (semanas completas) y cartas de control I-MR
n = d.groupby("fecha")[["atenciones", "resp", "hosp"]].sum()
wk = n.resample("W-SUN").agg(["sum", "count"])
wk = wk[wk[("atenciones", "count")] == 7]
wk = pd.DataFrame({c: wk[(c, "sum")] for c in ["atenciones", "resp", "hosp"]})["2024-01-01":"2026-09-27"]
# Corte en la última semana completa: los últimos días publicados tienen rezago de carga (menos hospitales informando)


def imr(x):
    mrb = x.diff().abs().mean()
    m = x.mean()
    ucl, lcl = m + 2.66 * mrb, m - 2.66 * mrb
    return m, ucl, lcl, int(((x > ucl) | (x < lcl)).sum())


A = imr(wk.atenciones)
H = imr(wk.hosp)
hi = wk.hosp[wk.hosp > H[1]]
lo = wk.hosp[wk.hosp < H[2]]
K.update(fuera_hosp_alto=len(hi), fuera_hosp_alto_2026=int((hi.index.year == 2026).sum()), fuera_hosp_bajo=len(lo),
         ultima_semana=str(wk.index[-1].date()))
print("semanas altas", list(hi.index.date), "bajas", list(lo.index.date))
K.update(semanas=len(wk), fuera_aten=A[3], fuera_hosp=H[3],
         cv_aten=100 * wk.atenciones.std() / wk.atenciones.mean(), cv_hosp=100 * wk.hosp.std() / wk.hosp.mean())

# Red: SAR vs SAPU vs hospitales
rp = red.pivot(index="anio", columns="tipo", values="atenciones")
K["sar_19"], K["sar_25"] = rp.loc[2019, "SAR"], rp.loc[2025, "SAR"]

# Pareto 2025
h25 = d[d.anio == 2025].groupby("id").atenciones.sum().sort_values(ascending=False)
cum = h25.cumsum() / h25.sum()
K["hosp_50"], K["hosp_n25"] = int((cum <= 0.5).sum()), len(h25)

# Regiones 2025: tasa de internación
hd = pd.read_csv(os.path.join(RAW, "hospitales.csv"), dtype={"id_establecimiento": str})
hd["id"] = hd.id_establecimiento.str.strip()
reg = d[d.anio == 2025].join(hd.drop_duplicates("id").set_index("id")[["region"]], on="id")
assert reg.region.notna().all()
reg = reg.groupby("region")[["atenciones", "hosp"]].sum()
reg["tasa"] = 100 * reg.hosp / reg.atenciones
reg = reg.sort_values("tasa")
K["reg_max"], K["reg_min"] = reg.tasa.max(), reg.tasa.min()

with open(os.path.join(ROOT, "analisis", "kpis.json"), "w") as f:
    json.dump({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else (v if isinstance(v, str) else int(v))) for k, v in K.items()}, f,
              indent=1, ensure_ascii=False)
for k, v in K.items():
    print(f"{k}: {v:.2f}" if isinstance(v, (float, np.floating)) else f"{k}: {v}")


# ------------------------------------------------------------------ helpers
def f1(v, dec=1):
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def miles(v):
    return f"{v:,.0f}".replace(",", ".")


def canvas(bg=BG):
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor(bg)
    return fig


def header(fig, kicker, title):
    fig.text(0.07, 0.935, kicker.upper(), fontsize=17, color=ORANGE, weight="bold")
    fig.text(0.07, 0.905, title, fontsize=36, color=NAVY, weight="bold", va="top", linespacing=1.15)


def footer(fig, n, dark=False):
    c = "#9FB3CC" if dark else MUTED
    fig.text(0.07, 0.035, f"{AUTHOR}  ·  {SOURCE}", fontsize=11, color=c)
    fig.text(0.93, 0.035, f"{n}/{N}", fontsize=13, color=c, ha="right")
    if n < N:
        fig.text(0.93, 0.065, "desliza  ›", fontsize=13, color="#F2A65A" if dark else ORANGE, ha="right", weight="medium")


def style_ax(ax, pct=False):
    ax.set_facecolor(BG)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=14, length=0)
    ax.grid(axis="y", color=GRID, lw=1)
    ax.set_axisbelow(True)
    fmt = (lambda v, _: f1(v, 0) + "%") if pct else (lambda v, _: miles(v))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(fmt))


def subtitle(fig, text, y=0.765):
    fig.text(0.10, y, text, fontsize=15, color=INK2)


def takeaway(fig, text, y=0.14):
    fig.patches.append(FancyBboxPatch((0.07, y - 0.04), 0.86, 0.095, boxstyle="round,pad=0.008,rounding_size=0.015",
                                      transform=fig.transFigure, fc="white", ec=GRID, lw=1.2))
    fig.patches.append(FancyBboxPatch((0.07, y - 0.04), 0.010, 0.095, boxstyle="square,pad=0",
                                      transform=fig.transFigure, fc=ORANGE, ec="none"))
    fig.text(0.10, y + 0.008, text, fontsize=16.5, color=NAVY, va="center", linespacing=1.45)


paths = []


def save(fig, n):
    p = os.path.join(OUT, f"slide_{n:02d}.png")
    fig.savefig(p, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    paths.append(p)


# 1 PORTADA ------------------------------------------------------------------
fig = canvas(NAVY)
fig.text(0.07, 0.87, "LEAN SIX SIGMA · SALUD · CHILE", fontsize=18, color="#F2A65A", weight="bold")
fig.text(0.07, 0.83, "Las urgencias de\nChile no están\nmás llenas.\nEstán más graves.", fontsize=58,
         color="white", weight="bold", va="top", linespacing=1.04)
fig.text(0.07, 0.47, "Analicé 8 años de datos oficiales de las urgencias\nde los hospitales públicos de Chile.",
         fontsize=22, color=PALEBLUE, va="top", linespacing=1.35)
big = [(f"{f1(K['atenciones_total'] / 1e6, 0)} M", "atenciones de\nurgencia analizadas"),
       (f"+{f1(K['chg_hosp'], 0)}%", "hospitalizaciones\ndiarias vs. 2019"),
       (f"{f1(K['chg_aten'], 0)}%", "consultas diarias\nvs. 2019")]
for i, (v, l) in enumerate(big):
    x = 0.07 + i * 0.30
    fig.text(x, 0.30, v, fontsize=40, color="white", weight="bold")
    fig.text(x, 0.285, l, fontsize=15, color="#9FB3CC", va="top", linespacing=1.3)
fig.text(0.07, 0.17, "SQL (PostgreSQL)  ·  Python  ·  DMAIC  ·  Monitor automático en Make", fontsize=16, color="#9FB3CC")
fig.text(0.07, 0.11, AUTHOR, fontsize=22, color="white", weight="bold")
fig.text(0.07, 0.085, "Enfermero · Salud ocupacional y emergencias · Datos", fontsize=15, color="#9FB3CC")
fig.text(0.93, 0.065, "desliza  ›", fontsize=15, color="#F2A65A", ha="right", weight="medium")
save(fig, 1)

# 2 MÉTODO -------------------------------------------------------------------
fig = canvas()
header(fig, "Método", "Lean Six Sigma\naplicado a datos públicos")
steps = [("D", "Definir", "Pregunta: ¿qué presiona hoy a la urgencia hospitalaria\npública de Chile? Alcance: 186 hospitales, 2019-2026."),
         ("M", "Medir", f"{miles(K['atenciones_total'])} atenciones y {miles(K['hosp_total'])} hospitalizaciones,\n"
                        "día por día. Línea base comparable: enero a septiembre."),
         ("A", "Analizar", "Edad, día de la semana, estacionalidad y cartas de\ncontrol I-MR para separar ruido de cambio real."),
         ("✓", "Validar", "Dos extracciones independientes coinciden al número:\n5.700.840 atenciones en enero-septiembre de 2019.")]
for i, (num, t, desc) in enumerate(steps):
    y = 0.70 - i * 0.145
    fig.patches.append(FancyBboxPatch((0.07, y - 0.055), 0.86, 0.12, boxstyle="round,pad=0.006,rounding_size=0.015",
                                      transform=fig.transFigure, fc="white", ec=GRID, lw=1.2))
    fig.text(0.115, y + 0.005, num, fontsize=40, color=ORANGE, weight="bold", va="center", ha="center",
             family="DejaVu Sans" if num == "✓" else "Poppins")
    fig.text(0.19, y + 0.035, t, fontsize=22, color=NAVY, weight="bold", va="center")
    fig.text(0.19, y - 0.013, desc, fontsize=14.5, color=INK2, va="center", linespacing=1.35)
footer(fig, 2)
save(fig, 2)

# 3 MENOS CONSULTAS, MÁS INTERNACIONES ---------------------------------------
fig = canvas()
header(fig, "Hallazgo 1", "Menos consultas,\nmás internaciones")
ax = fig.add_axes([0.10, 0.28, 0.74, 0.46])
style_ax(ax)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f1(v, 0)))
idx = lambda c: 100 * es[c] / es.loc[2019, c]
ax.axvspan(2019.6, 2021.5, color=GRID, alpha=0.5, lw=0)
ax.text(2020.55, 116, "pandemia", ha="center", fontsize=13, color=MUTED)
ax.axhline(100, color=MUTED, lw=1, ls=(0, (2, 2)))
ax.plot(YRS, idx("hosp_dia"), color=ORANGE, lw=3.5, marker="o", ms=7, mec=BG, mew=2)
ax.plot(YRS, idx("aten_dia"), color=BLUE, lw=3.5, marker="o", ms=7, mec=BG, mew=2)
ax.text(2026.15, idx("hosp_dia")[2026], f"Hospitalizaciones\n+{f1(K['chg_hosp'])}%", color=ORANGE, fontsize=14,
        weight="bold", va="center")
ax.text(2026.15, idx("aten_dia")[2026], f"Consultas\n{f1(K['chg_aten'])}%", color=BLUE, fontsize=14, weight="bold",
        va="center")
ax.set_xlim(2018.7, 2027.6)
ax.set_ylim(55, 120)
ax.set_xticks(YRS)
ax.set_xticklabels([f"'{str(y)[2:]}" for y in YRS])
subtitle(fig, "Promedio diario en hospitales públicos, enero a septiembre (2019 = 100)")
takeaway(fig, f"De {miles(K['aten_dia_19'])} a {miles(K['aten_dia_26'])} consultas por día, pero de {miles(K['hosp_dia_19'])} "
              f"a {miles(K['hosp_dia_26'])}\nhospitalizaciones. Las cirugías de urgencia subieron {f1(K['chg_cir'])}%.")
footer(fig, 3)
save(fig, 3)

# 4 TASA DE HOSPITALIZACIÓN --------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 2", "1 de cada 11 consultas\ntermina en internación")
ax = fig.add_axes([0.10, 0.28, 0.83, 0.46])
style_ax(ax, pct=True)
cols = [MUTED if y in (2020, 2021) else (ORANGE if y >= 2023 else PALEBLUE) for y in YRS]
ax.bar(YRS, es.tasa, color=cols, width=0.62)
for y in YRS:
    v = es.loc[y, "tasa"]
    ax.text(y, v + 0.15, f1(v), ha="center", fontsize=15, color=NAVY, weight="bold" if y in (2019, 2026) else "normal")
ax.set_ylim(0, 12)
ax.set_xticks(YRS)
ax.set_xticklabels([str(y) if y != 2026 else "2026*" for y in YRS], fontsize=13)
subtitle(fig, "% de atenciones de urgencia que terminan en hospitalización (enero a septiembre)")
fig.text(0.10, 0.235, "En gris, pandemia: muchas menos consultas, solo las graves. *2026 hasta el 30/09.", fontsize=12.5,
         color=MUTED)
takeaway(fig, f"De {f1(K['tasa_19'])}% en 2019 a {f1(K['tasa_26'])}% en 2026. Con ~7,2 millones de consultas al año,\n"
              f"cada punto de tasa son unas {miles(round(rp.loc[2025, 'Hospital'] / 100, -3))} hospitalizaciones más.")
footer(fig, 4)
save(fig, 4)

# 5 EDAD -------------------------------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 3", "Cambió el paciente:\nmenos niños, más mayores")
ax = fig.add_axes([0.10, 0.30, 0.83, 0.42])
style_ax(ax)
labels = ["Menores de 5", "5 a 14", "15 a 64", "65 y más"]
v19 = [at[2019].menores_1 + at[2019].de_1_a_4, at[2019].de_5_a_14, at[2019].de_15_a_64, at[2019].de_65_y_mas]
v26 = [at[2026].menores_1 + at[2026].de_1_a_4, at[2026].de_5_a_14, at[2026].de_15_a_64, at[2026].de_65_y_mas]
x = np.arange(4)
ax.bar(x - 0.2, np.array(v19) / 1e3, 0.38, color=PALEBLUE, label="2019")
ax.bar(x + 0.2, np.array(v26) / 1e3, 0.38, color=ORANGE, label="2026")
for i in range(4):
    c = 100 * (v26[i] / v19[i] - 1)
    ax.text(i + 0.2, v26[i] / 1e3 + 40, ("+" if c > 0 else "") + f1(c, 0) + "%", ha="center", fontsize=16,
            color=NAVY, weight="bold")
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=14.5)
ax.set_ylim(0, 3300)
ax.legend(frameon=False, fontsize=15, loc="upper left")
subtitle(fig, "Atenciones de urgencia en hospitales por edad, enero a septiembre (miles)")
takeaway(fig, f"Los mayores de 65 pasaron del {f1(K['share65_19'])}% al {f1(K['share65_26'])}% de las consultas y se internan "
              f"en\n{f1(K['tasa_65_26'], 0)}% de los casos. Pero la edad explica solo el {f1(K['pct_por_edad'], 0)}% de la suba de la tasa.")
footer(fig, 5)
save(fig, 5)

# 6 DÍA DE LA SEMANA ----------------------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 4", "El lunes llega 14% más\ngente que el promedio")
ax = fig.add_axes([0.10, 0.28, 0.83, 0.46])
style_ax(ax, pct=True)
dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
vals = 100 * (dow.atenciones.values - 1)
ax.bar(dias, vals, color=[ORANGE if v > 0 else PALEBLUE for v in vals], width=0.6)
ax.axhline(0, color=NAVY, lw=1.2)
for i, v in enumerate(vals):
    ax.text(i, v + (0.8 if v > 0 else -1.8), ("+" if v > 0 else "") + f1(v, 0) + "%", ha="center", fontsize=17,
            color=NAVY, weight="bold")
ax.set_ylim(-20, 20)
ax.tick_params(axis="x", labelsize=16)
subtitle(fig, "Consultas diarias vs. el promedio semanal, hospitales públicos 2023-2026")
takeaway(fig, "La demanda es previsible: el lunes es el pico y el fin de semana el valle.\n"
              "Lean propone ajustar turnos y box a esa curva, no a un promedio plano.")
footer(fig, 6)
save(fig, 6)

# 7 INVIERNO: CONSULTAS VS CAMAS ----------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 5", "El invierno llena la sala\nde espera. Las camas, siempre")
ax = fig.add_axes([0.10, 0.28, 0.74, 0.46])
style_ax(ax)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f1(v, 0)))
ia = 100 * wk.atenciones / wk.atenciones.mean()
ih = 100 * wk.hosp / wk.hosp.mean()
ax.plot(wk.index, ia, color=BLUE, lw=2.2)
ax.plot(wk.index, ih, color=ORANGE, lw=2.8)
ax.axhline(100, color=MUTED, lw=1, ls=(0, (2, 2)))
ax.text(wk.index[-1] + pd.Timedelta(days=12), ia.iloc[-1] + 4, "Consultas", color=BLUE, fontsize=14, weight="bold", va="center")
ax.text(wk.index[-1] + pd.Timedelta(days=12), ih.iloc[-1] - 4, "Hospitali-\nzaciones", color=ORANGE, fontsize=14,
        weight="bold", va="center")
ax.set_xlim(wk.index[0] - pd.Timedelta(days=10), wk.index[-1] + pd.Timedelta(days=130))
ax.set_ylim(75, 120)
ax.set_yticks([80, 90, 100, 110, 120])
ax.set_xticks(pd.to_datetime(["2024-01-01", "2025-01-01", "2026-01-01"]))
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
subtitle(fig, "Total semanal vs. su promedio (=100), semanas completas 2024 a septiembre 2026")
takeaway(fig, f"Las consultas varían {f1(K['cv_aten'])}% (picos respiratorios). Las hospitalizaciones solo {f1(K['cv_hosp'])}%:\n"
              "la presión sobre camas no es estacional, es estructural.")
footer(fig, 7)
save(fig, 7)

# 8 CARTA DE CONTROL ---------------------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 6", "Carta de control: 5 semanas\nseguidas sobre el techo")
ax = fig.add_axes([0.10, 0.28, 0.83, 0.46])
style_ax(ax)
m, ucl, lcl, _ = H
out = (wk.hosp > ucl) | (wk.hosp < lcl)
ax.plot(wk.index, wk.hosp, color=BLUE, lw=1.8, marker="o", ms=4, mec=BG, mew=1)
ax.scatter(wk.index[out], wk.hosp[out], color=RED, s=60, zorder=5, edgecolor=BG, lw=1.5)
for v, lab, c in [(m, "Media", NAVY), (ucl, "LCS", RED), (lcl, "LCI", RED)]:
    ax.axhline(v, color=c, lw=1.4, ls="-" if lab == "Media" else (0, (4, 3)))
    ax.text(wk.index[-1] + pd.Timedelta(days=14), v + 40, f"{lab} {miles(v)}", color=c, fontsize=12.5, va="bottom",
            weight="bold")
ax.set_xlim(wk.index[0] - pd.Timedelta(days=10), wk.index[-1] + pd.Timedelta(days=120))
ax.set_ylim(10500, 14500)
ax.set_yticks([11000, 12000, 13000, 14000])
ax.set_xticks(pd.to_datetime(["2024-01-01", "2025-01-01", "2026-01-01"]))
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
subtitle(fig, "Carta I-MR: hospitalizaciones semanales desde urgencia, red pública de Chile")
takeaway(fig, f"{K['fuera_hosp']} de {K['semanas']} semanas fuera de límites (en consultas, {K['fuera_aten']}). Pero {K['fuera_hosp_alto_2026']} de\n"
              f"las {K['fuera_hosp_alto']} que superan el techo son de 2026, seguidas, entre agosto y septiembre.")
footer(fig, 8)
save(fig, 8)

# 9 REGIONES -------------------------------------------------------------------------
fig = canvas()
header(fig, "Hallazgo 7", "Según la región, la tasa\nde internación se duplica")
ax = fig.add_axes([0.30, 0.25, 0.60, 0.50])
ax.set_facecolor(BG)
for sp in ["top", "right", "left"]:
    ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.tick_params(colors=INK2, labelsize=13, length=0)
ax.grid(axis="x", color=GRID, lw=1)
ax.set_axisbelow(True)
nat = 100 * es.loc[2025, "hosp"] / es.loc[2025, "atenciones"]
cl = [ORANGE if v > 11 else (MUTED if v < 6 else PALEBLUE) for v in reg.tasa]
ax.barh(reg.index, reg.tasa, color=cl, height=0.68)
for i, v in enumerate(reg.tasa):
    ax.text(v + 0.15, i, f1(v), va="center", fontsize=12.5, color=NAVY, weight="bold" if v > 11 or v < 6 else "normal")
ax.set_xlim(0, 13.5)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f1(v, 0) + "%"))
subtitle(fig, "% de consultas de urgencia que terminan en internación, hospitales públicos, 2025", y=0.775)
takeaway(fig, f"De {f1(K['reg_min'])}% en Aysén a {f1(K['reg_max'])}% en el Maule. Puede ser complejidad, camas\n"
              "o forma de registrar: hay que auditarlo antes de comparar desempeño.", y=0.13)
footer(fig, 9)
save(fig, 9)

# 10 AUTOMATIZACIÓN CON MAKE --------------------------------------------------------
fig = canvas(NAVY)
fig.text(0.07, 0.935, "CONTROLAR", fontsize=17, color="#F2A65A", weight="bold")
fig.text(0.07, 0.905, "Un análisis que se\nactualiza solo", fontsize=40, color="white", weight="bold", va="top",
         linespacing=1.1)
fig.text(0.07, 0.77, "Todos los lunes a las 9:00, Make revisa la fuente del Minsal.", fontsize=17, color=PALEBLUE)
flujo = [("1", "Chequea el archivo", "Pide solo el encabezado: fecha y tamaño.", "Make · HTTP"),
         ("2", "Compara versiones", "Si no cambió, se detiene ahí.", "Make · Data store"),
         ("3", "Deja registro", "Cada chequeo queda anotado en una planilla.", "Make · Google Sheets"),
         ("4", "Avisa", "Si hay datos nuevos, llega un mail con el resumen.", "Make · Gmail"),
         ("5", "Recalcula", "ETL, KPIs, carta de control, tablero y carrusel.", "SQL · Python")]
for i, (n_, t, desc, tool) in enumerate(flujo):
    y = 0.68 - i * 0.105
    fig.patches.append(FancyBboxPatch((0.07, y - 0.04), 0.86, 0.083, boxstyle="round,pad=0.004,rounding_size=0.012",
                                      transform=fig.transFigure, fc="#13335C", ec="none"))
    fig.text(0.115, y, n_, fontsize=30, color="#F2A65A", weight="bold", va="center", ha="center")
    fig.text(0.17, y + 0.014, t, fontsize=19, color="white", weight="bold", va="center")
    fig.text(0.17, y - 0.018, desc, fontsize=14, color=PALEBLUE, va="center")
    fig.text(0.91, y + 0.014, tool, fontsize=12, color="#9FB3CC", va="center", ha="right")
fig.text(0.07, 0.15, "Make no procesa 1,5 GB: vigila, registra y avisa. El cálculo queda en\n"
                     "SQL y Python. Cada herramienta en lo que mejor hace.", fontsize=15.5, color="white",
         va="top", linespacing=1.4)
footer(fig, 10, dark=True)
save(fig, 10)

# 11 QUÉ HARÍA -----------------------------------------------------------------------
fig = canvas()
header(fig, "Mejorar y controlar", "Qué haría con\nestos datos")
recs = [("Turnos según la curva semanal", "Reforzar lunes y martes; el fin de semana llega 14% menos\ngente. Misma dotación, mejor distribuida."),
        ("Gestión de altas, no solo de urgencia", "Si la presión es de camas, la espera se resuelve arriba:\naltas antes del mediodía y planificación de egresos."),
        ("Ruta rápida para mayores de 65", "Más de un tercio de las hospitalizaciones son de mayores.\nEvaluación geriátrica temprana desde el triage."),
        ("Publicar el tiempo de espera de cama", "El registro DAU tiene el campo de espera menor a 12 horas,\npero llega vacío. Sin ese dato no hay control posible.")]
for i, (t, desc) in enumerate(recs):
    y = 0.70 - i * 0.145
    fig.patches.append(FancyBboxPatch((0.07, y - 0.055), 0.86, 0.12, boxstyle="round,pad=0.006,rounding_size=0.015",
                                      transform=fig.transFigure, fc="white", ec=GRID, lw=1.2))
    fig.patches.append(FancyBboxPatch((0.07, y - 0.055), 0.012, 0.12, boxstyle="square,pad=0",
                                      transform=fig.transFigure, fc=ORANGE, ec="none"))
    fig.text(0.11, y + 0.03, t, fontsize=20, color=NAVY, weight="bold", va="center")
    fig.text(0.11, y - 0.016, desc, fontsize=14.5, color=INK2, va="center", linespacing=1.35)
footer(fig, 11)
save(fig, 11)

# 12 CIERRE ---------------------------------------------------------------------------
fig = canvas(NAVY)
fig.text(0.07, 0.90, "CONCLUSIÓN", fontsize=18, color="#F2A65A", weight="bold")
fig.text(0.07, 0.87, "Para que la urgencia\natienda más rápido,\nhay que mirar las camas.", fontsize=40,
         color="white", weight="bold", va="top", linespacing=1.12)
items = [f"Hay {f1(-K['chg_aten'], 0)}% menos consultas por día que en 2019, pero {f1(K['chg_hosp'], 0)}% más internaciones.",
         f"Los mayores de 65 crecen y los niños menores de 5 bajan {f1(-K['chg_u5'], 0)}%.",
         "La demanda tiene patrón: lunes y semanas de invierno se pueden planificar.",
         "Las camas trabajan al límite todo el año, y en 2026 pasaron el techo.",
         "El monitor en Make avisa cada vez que el Minsal publica datos nuevos."]
for i, t in enumerate(items):
    y = 0.655 - i * 0.062
    fig.text(0.07, y, "›", fontsize=24, color="#F2A65A", weight="bold", va="center")
    fig.text(0.11, y, t, fontsize=16.5, color=PALEBLUE, va="center")
fig.text(0.07, 0.31, "Limitaciones: datos agregados por día y hospital, sin triage ni tiempos de espera\n"
                     "(los campos existen pero se publican vacíos). La causa de la suba en la tasa de\n"
                     "internación más allá de la edad es una hipótesis, no un resultado probado.",
         fontsize=13, color="#9FB3CC", va="top", linespacing=1.45)
fig.text(0.07, 0.19, "Fui enfermero de emergencias. ¿Lo ves igual\ndesde tu guardia? Te leo en comentarios.",
         fontsize=21, color="white", weight="medium", va="top", linespacing=1.3)
fig.text(0.07, 0.085, AUTHOR, fontsize=19, color="white", weight="bold")
fig.text(0.07, 0.062, "Código, datos y tablero interactivo: github.com/mperezalaniz/urgencias-chile-lean-six-sigma", fontsize=12.5, color="#9FB3CC")
fig.text(0.93, 0.035, f"{N}/{N}", fontsize=13, color="#9FB3CC", ha="right")
save(fig, 12)

pdf = os.path.join(ROOT, "docs", "Carrusel_Urgencias_Chile.pdf")
with open(pdf, "wb") as f:
    f.write(img2pdf.convert(paths))
print(pdf)
