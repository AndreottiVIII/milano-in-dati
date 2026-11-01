"""Cosa c'e' di piu' sorprendente: numeri di appoggio.

Uso: python -I -X utf8 04_sorpresa.py <percorso assoluto milano-in-dati> <percorso assoluto scuole-domani>
Scrive in out/: sorpresa_quartiere_vs_scuola.csv, sorpresa_nil_rapporto_alunni_residenti.csv, sorpresa_gia_nati.csv,
sorpresa_soglie.csv, sorpresa_riepilogo.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

base, out = sys.argv[1], Path(sys.argv[2]) / "out"
R, ids = lib.carica_residenti(base)
S = lib.carica_scuole(base)
ADJ = lib.adiacenze(base, ids)
nomi = pd.read_csv(lib.percorsi(base)["nil"]).set_index("id_nil").nil.to_dict()
res = {}

# A. Il quartiere spiega la scuola? Variazione 2015->2024 degli alunni nelle scuole del NIL contro quella dei bambini residenti
rows = []
for o, (lo, hi) in lib.BANDE.items():
    pup = S[S.ordine == o].pivot_table(index="id_nil", columns="anno_inizio", values="iscritti", aggfunc="sum").fillna(0)
    for area in ["nil", "anello1"]:
        Ra = np.einsum("ij,jta->ita", ADJ[area], R)[:, :, lo:hi + 1].sum(axis=2)
        r15, r24 = Ra[:, 2015 - 1999], Ra[:, 2024 - 1999]
        d = pd.DataFrame({"id_nil": ids, "res15": r15, "res24": r24}).set_index("id_nil")
        d["p15"], d["p24"] = pup[2015].reindex(d.index).fillna(0), pup[2024].reindex(d.index).fillna(0)
        dd = d[(d.p15 >= 200) & (d.p24 >= 200) & (d.res15 >= 200)].copy()
        dd["var_alunni"] = dd.p24 / dd.p15 - 1
        dd["var_residenti"] = dd.res24 / dd.res15 - 1
        rows.append({"ordine": o, "area": area, "n_nil": len(dd),
                     "corr_pearson": dd.var_alunni.corr(dd.var_residenti),
                     "corr_spearman": dd.var_alunni.corr(dd.var_residenti, method="spearman"),
                     "mediana_var_alunni_pct": 100 * dd.var_alunni.median(), "mediana_var_residenti_pct": 100 * dd.var_residenti.median(),
                     "nil_dove_calano_bambini_e_crescono_alunni": int(((dd.var_residenti < 0) & (dd.var_alunni > 0)).sum())})
        if area == "nil":
            dd.reset_index().assign(nome=lambda x: x.id_nil.map(nomi), ordine=o).to_csv(
                out / f"sorpresa_quartiere_vs_scuola_{o}.csv", sep=";", index=False, float_format="%.3f")
qs = pd.DataFrame(rows)
qs.to_csv(out / "sorpresa_quartiere_vs_scuola.csv", sep=";", index=False, float_format="%.3f")
res["quartiere_vs_scuola"] = qs.round(3).to_dict("records")

# B. Rapporto alunni nelle scuole del NIL / bambini residenti nel NIL (2024)
rr = []
for o, (lo, hi) in lib.BANDE.items():
    pup = S[(S.ordine == o) & (S.anno_inizio == 2024)].groupby("id_nil").iscritti.sum()
    for k, i in enumerate(ids):
        r = R[k, 2024 - 1999, lo:hi + 1].sum()
        rr.append({"ordine": o, "id_nil": i, "nome": nomi[i], "alunni_nelle_scuole_2024": pup.get(i, 0), "bambini_residenti_2024": r,
                   "rapporto": pup.get(i, 0) / r if r > 0 else np.nan})
rr = pd.DataFrame(rr)
rr.to_csv(out / "sorpresa_nil_rapporto_alunni_residenti.csv", sep=";", index=False, float_format="%.3f")
sel = rr[(rr.bambini_residenti_2024 >= 300) & (rr.alunni_nelle_scuole_2024 > 0)]
res["rapporto_alunni_residenti"] = {o: {"mediana": float(sel[sel.ordine == o].rapporto.median()),
                                         "min": float(sel[sel.ordine == o].rapporto.min()), "max": float(sel[sel.ordine == o].rapporto.max()),
                                         "n_nil_sotto_0_5": int((sel[sel.ordine == o].rapporto < 0.5).sum()),
                                         "n_nil_sopra_1_5": int((sel[sel.ordine == o].rapporto > 1.5).sum()),
                                         "n": int((sel.ordine == o).sum())} for o in lib.ORDINI}

# C. Quanto del calo 2024 -> 2034 e' gia' "scritto": bambini gia' nati al 31/12/2025
pr = pd.read_csv(out / "proiezione_citta.csv", sep=";")
c = pr[pr.combinazione == "centrale"].pivot(index="anno", columns="ordine", values="alunni_proiettati")
reale24 = pr[(pr.combinazione == "reale") & (pr.anno == 2024)].set_index("ordine").alunni_proiettati
first_free = {"infanzia": 2029, "primaria": 2032, "sec1": 2037}   # primo a.s. con bambini non ancora nati al 31/12/2025
gn = []
for o in lib.ORDINI:
    ultimo_noto = min(first_free[o] - 1, 2034)
    gn.append({"ordine": o, "alunni_2024": reale24[o], "ultimo_anno_con_tutti_i_bambini_gia_nati": ultimo_noto,
               "alunni_proiettati_quell_anno": c.loc[ultimo_noto, o], "var_pct": 100 * (c.loc[ultimo_noto, o] / reale24[o] - 1),
               "alunni_proiettati_2034": c.loc[2034, o], "var_pct_2034": 100 * (c.loc[2034, o] / reale24[o] - 1),
               "quota_del_calo_2034_gia_scritta_pct": 100 * (c.loc[ultimo_noto, o] - reale24[o]) / (c.loc[2034, o] - reale24[o])})
gn = pd.DataFrame(gn)
gn.to_csv(out / "sorpresa_gia_nati.csv", sep=";", index=False, float_format="%.1f")
res["gia_nati"] = gn.round(1).to_dict("records")

# D. Soglie diverse (60/70/80% del 2015) e quante scuole le passano nel 2034 (scenario centrale)
sc = pd.read_csv(out / "proiezione_scuole.csv", sep=";")
sg = []
for o in lib.ORDINI:
    s = sc[(sc.ordine == o) & sc.iscritti_2015.notna()]
    for t in (0.6, 0.7, 0.8):
        sg.append({"ordine": o, "soglia": t, "scuole_con_rif_2015": len(s), "gia_sotto_nel_2024": int(((s.iscritti_2024 / s.iscritti_2015) < t).sum()),
                   "sotto_nel_2034": int(((s.p2034 / s.iscritti_2015) < t).sum()),
                   "alunni_2024_in_quelle_scuole": int(s[(s.p2034 / s.iscritti_2015) < t].iscritti_2024.sum())})
sg = pd.DataFrame(sg)
sg.to_csv(out / "sorpresa_soglie.csv", sep=";", index=False)
res["soglie"] = sg.to_dict("records")

# E. Quanto cambia con la gestione (soglia 70%): quante scuole statali / comunali / paritarie
gs = sc[sc.iscritti_2015.notna()].groupby(["ordine", "gestione"]).agg(
    scuole=("codice", "count"), gia_sotto_70=("gia_sotto_70_nel_2024", "sum"), sotto_70_2034=("sotto_70_nel_2034", "sum"),
    iscritti_2024=("iscritti_2024", "sum"), p2034=("p2034", "sum")).reset_index()
gs["var_pct_2034"] = 100 * (gs.p2034 / gs.iscritti_2024 - 1)
gs.to_csv(out / "sorpresa_per_gestione.csv", sep=";", index=False, float_format="%.1f")
res["per_gestione"] = gs.round(1).to_dict("records")

json.dump(res, open(out / "sorpresa_riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
pd.set_option("display.width", 250)
print(qs.round(3).to_string(index=False))
print(json.dumps(res["rapporto_alunni_residenti"], indent=1))
print(gn.round(1).to_string(index=False))
print(sg.to_string(index=False))
print(gs.round(1).to_string(index=False))
