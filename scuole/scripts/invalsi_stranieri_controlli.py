"""Controlli sul modello principale: ESCS di classe fornito contro ricalcolato, coefficienti di ESCS,
forma della relazione, confronto con le medie ufficiali.

Uso: python -I -X utf8 invalsi_stranieri_controlli.py <scripts> <raw/invalsi_campione> <output>
"""
import runpy
import sys

import numpy as np
import pandas as pd

SCR, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = ["x", RAW, OUT]
m = runpy.run_path(SCR + "/invalsi_stranieri.py", run_name="lib")
d, conta = m["tutto"]()
conta["ok"] = (conta.noti >= 10) & (conta.quota_mancante <= 0.25)
d = d.merge(conta[["id_classe", "ok"]], on="id_classe", how="left")
d["quota_ok"] = d.ok
d = d[d.punteggio.notna() & d.peso.notna()]
wls, GEO, dummies = m["wls_cl"], m["GEO"], m["dummies"]

print("=== ESCS di classe: fornito contro media ricalcolata")
u = d.drop_duplicates(["id_classe", "studente"])
c = u.groupby("id_classe").agg(mia=("escs", "mean"), forn=("escs_classe", "first"), gr=("grado", "first"), n=("escs", "count"))
print(c.groupby("gr")[["mia", "forn"]].corr().round(3).to_string())
print("scarto assoluto medio:", (c.mia - c.forn).abs().groupby(c.gr).mean().round(3).to_dict())

print("\n=== coefficienti ESCS nel modello C (nativi); + ricalcolo con ESCS dei SOLI compagni")
for gr in (5, 8):
    for mat in ("ita", "mat"):
        for geo in ("Lombardia", "Nord"):
            s = d[(d.grado == gr) & (d.materia == mat) & GEO[geo](d) & (d.origine == 1) & d.quota_ok].copy()
            ya = dummies(s, "anno")
            ra = dummies(s, "cod_reg") if geo != "Lombardia" else []
            r = wls(s, "punteggio", ["quota10", "escs", "escs_classe"] + ya + ra)
            print(f"G{gr} {mat} {geo}: quota {r['b'][0]:.2f} ({r['se_id_scuola'][0]:.2f}) | escs ind {r['b'][1]:.2f} ({r['se_id_scuola'][1]:.2f}) | escs classe {r['b'][2]:.2f} ({r['se_id_scuola'][2]:.2f}) | n {r['n']}")
            # quota al quadrato
            s["q2"] = s.quota_comp ** 2 * 100
            r2 = wls(s, "punteggio", ["quota10", "q2", "escs", "escs_classe"] + ya + ra)
            print(f"   con termine quadratico: lineare {r2['b'][0]:.2f} ({r2['se_id_scuola'][0]:.2f}) | quadr {r2['b'][1]:.2f} ({r2['se_id_scuola'][1]:.2f})")

print("\n=== SD dei punteggi (per tradurre i punti) e divario nativi-stranieri (modello con ESCS individuale)")
for gr in (5, 8):
    for mat in ("ita", "mat"):
        for geo in ("Lombardia", "Nord"):
            s = d[(d.grado == gr) & (d.materia == mat) & GEO[geo](d) & d.origine.isin([1, 2, 3]) & d.quota_ok].copy()
            mu = np.average(s.punteggio, weights=s.peso)
            sd = np.sqrt(np.average((s.punteggio - mu) ** 2, weights=s.peso))
            s["st"] = s.origine.isin([2, 3]).astype(float)
            ya = dummies(s, "anno")
            r0 = wls(s, "punteggio", ["st"] + ya)
            r1 = wls(s, "punteggio", ["st", "escs"] + ya)
            r2 = wls(s, "punteggio", ["st", "escs", "quota10", "escs_classe"] + ya)
            print(f"G{gr} {mat} {geo}: media {mu:.1f} sd {sd:.1f} | divario stranieri-nativi grezzo {r0['b'][0]:.1f} ({r0['se_id_scuola'][0]:.1f}) | a parita' ESCS ind {r1['b'][0]:.1f} ({r1['se_id_scuola'][0]:.1f}) | + quota e ESCS classe {r2['b'][0]:.1f} ({r2['se_id_scuola'][0]:.1f})")

print("\n=== ANNO PER ANNO, nativi G5 italiano, modello C (Lombardia e Nord)")
for geo in ("Lombardia", "Nord"):
    for a in m["ANNI"][5]:
        s = d[(d.grado == 5) & (d.materia == "ita") & GEO[geo](d) & (d.origine == 1) & d.quota_ok & (d.anno == a)].copy()
        ra = dummies(s, "cod_reg") if geo != "Lombardia" else []
        r = wls(s, "punteggio", ["quota10", "escs", "escs_classe"] + ra)
        print(f"{geo} {a}: {r['b'][0]:.2f} ({r['se_id_scuola'][0]:.2f}), classi {r['G_id_classe']}")

print("\n=== ANNO 2025-26 da solo (G5) e 2024-25 da solo (G8), Lombardia: nativi, modelli grezzo e C")
for gr, a in ((5, "2025-26"), (8, "2024-25")):
    for mat in ("ita", "mat"):
        s = d[(d.grado == gr) & (d.materia == mat) & (d.cod_reg == 4) & (d.origine == 1) & d.quota_ok & (d.anno == a)].copy()
        ra0 = wls(s, "punteggio", ["quota10"])
        rc = wls(s, "punteggio", ["quota10", "escs", "escs_classe"])
        print(f"G{gr} {mat} {a}: grezzo {ra0['b'][0]:.2f} ({ra0['se_id_scuola'][0]:.2f}) | C {rc['b'][0]:.2f} ({rc['se_id_scuola'][0]:.2f}) | classi {rc['G_id_classe']} scuole {rc['G_id_scuola']} nativi {rc['n']}")

print("\n=== SOLO quota I generazione contro II generazione tra i compagni (nativi, Nord, G5, modello C)")
for mat in ("ita", "mat"):
    s = d[(d.grado == 5) & (d.materia == mat) & GEO["Nord"](d) & (d.origine == 1) & d.quota_ok].copy()
    s["qg1"] = s.g1_x if "g1_x" in s else 0
    n = (s.noti - 1).where(s.noti > 1)
    conta2 = conta.set_index("id_classe")
    s["q1"] = s.id_classe.map(conta2.g1) / n * 10
    s["q2"] = s.id_classe.map(conta2.g2) / n * 10
    ya = dummies(s, "anno")
    ra = dummies(s, "cod_reg")
    r = wls(s, "punteggio", ["q1", "q2", "escs", "escs_classe"] + ya + ra)
    print(f"{mat}: per +10 punti di I gen. {r['b'][0]:.2f} ({r['se_id_scuola'][0]:.2f}); per +10 punti di II gen. {r['b'][1]:.2f} ({r['se_id_scuola'][1]:.2f}); classi {r['G_id_classe']}")

print("\n=== NATIVI: ESCS medio per fascia di classe, Lombardia G5 (selezione)")
s = d[(d.grado == 5) & (d.materia == "ita") & (d.cod_reg == 4) & (d.origine == 1) & d.quota_ok]
print(s.groupby("bin", observed=True).apply(lambda q: pd.Series(dict(escs=np.average(q.escs.fillna(q.escs.mean()), weights=q.peso), p=np.average(q.punteggio, weights=q.peso), n=len(q), cl=q.id_classe.nunique()))).round(2).to_string())
