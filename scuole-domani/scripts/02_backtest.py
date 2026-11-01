"""Prova all'indietro: si "dimentica" il futuro, si proietta, si confronta con il vero.

Uso: python -I -X utf8 02_backtest.py <percorso assoluto milano-in-dati> <percorso assoluto scuole-domani>

Per ogni anno di partenza T0 (ultimo a.s. noto: 2010..2023) e orizzonte h (1..10 anni, con T0+h <= 2024)
usa solo dati fino a T0 per gli alunni e fino a T0+1 per i residenti (come nel caso reale: alunni fino al 2024/25,
residenti fino al 31/12/2025). Confronta: "fermo" (nessun cambio), le varianti di lib.VARIANTI, e la variante
centrale con i nati veri al posto dello scenario (per separare l'errore dei nati dal resto).
Scrive in out/: backtest_scuole.csv, backtest_riepilogo.csv, backtest_nil.csv, backtest_bande_errore.csv,
backtest_citta.csv, backtest_casi.csv (2014->2019, 2019->2024, 2014->2024).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402

base, out = sys.argv[1], Path(sys.argv[2]) / "out"
out.mkdir(exist_ok=True)
R, ids = lib.carica_residenti(base)
S = lib.carica_scuole(base)
ADJ = lib.adiacenze(base, ids)
idx = {i: k for k, i in enumerate(ids)}
ULTIMO = 2024

METODI = ["fermo", "centrale", "solo_citta", "solo_nil", "con_migrazione", "centrale_nati_veri"]
righe = []
for T0 in range(2010, ULTIMO):
    for h in range(1, 11):
        tgt = T0 + h
        if tgt > ULTIMO:
            continue
        Fm = {}
        for m in METODI:
            if m == "fermo":
                Fm[m] = {o: np.ones((len(ids), 1)) for o in lib.ORDINI}
            elif m == "centrale_nati_veri":
                Fm[m] = lib.fattori_variante(R, ADJ, T0, [tgt], "centrale", oracolo=True)[0]
            else:
                Fm[m] = lib.fattori_variante(R, ADJ, T0, [tgt], m)[0]
        for o in lib.ORDINI:
            s0 = S[(S.ordine == o) & (S.anno_inizio == T0) & (S.iscritti > 0)]
            s1 = S[(S.ordine == o) & (S.anno_inizio == tgt) & (S.iscritti > 0)].set_index("codice")
            ii = s0.id_nil.map(idx).values
            for m in METODI:
                f = Fm[m][o][ii, 0]
                f = np.where(np.isnan(f), 1.0, f)
                d = pd.DataFrame({"codice": s0.codice.values, "id_nil": s0.id_nil.values,
                                  "iscritti_t0": s0.iscritti.values, "proiettati": s0.iscritti.values * f})
                d["reali"] = d.codice.map(s1.iscritti)
                d["metodo"], d["ordine"], d["T0"], d["h"] = m, o, T0, h
                righe.append(d)
bt = pd.concat(righe, ignore_index=True)
bt["esiste_dopo"] = bt.reali.notna()
bt[bt.metodo.isin(["fermo", "centrale", "solo_citta"])].to_csv(out / "backtest_scuole.csv", index=False, sep=";", float_format="%.3f")


def riepiloga(g):
    c = g[g.esiste_dopo]
    err = (c.proiettati - c.reali) / c.reali
    ass = err.abs()
    wape = (c.proiettati - c.reali).abs().sum() / c.reali.sum()
    bias = (c.proiettati.sum() - c.reali.sum()) / c.reali.sum()
    pred = (c.proiettati / c.iscritti_t0) < 0.85
    vero = (c.reali / c.iscritti_t0) < 0.85
    tp = (pred & vero).sum()
    return pd.Series({"n_scuole": len(c), "WAPE_scuola": wape, "mediana_err_ass": ass.median(),
                      "entro10": (ass <= .10).mean(), "entro20": (ass <= .20).mean(), "bias_somma": bias,
                      "allarme_prec": tp / pred.sum() if pred.sum() else np.nan,
                      "allarme_rec": tp / vero.sum() if vero.sum() else np.nan,
                      "n_allarmi": int(pred.sum()), "n_veri": int(vero.sum())})


riep = bt.groupby(["metodo", "ordine", "h"]).apply(riepiloga, include_groups=False).reset_index()
riep.to_csv(out / "backtest_riepilogo.csv", index=False, sep=";", float_format="%.4f")

# --- bande di errore (rapporto reale/proiettato per scuola) per il metodo centrale
c = bt[(bt.metodo == "centrale") & bt.esiste_dopo].copy()
c["rapporto"] = c.reali / c.proiettati
bande = c.groupby(["ordine", "h"]).rapporto.quantile([.1, .25, .5, .75, .9]).unstack().reset_index()
bande.columns = ["ordine", "h", "q10", "q25", "q50", "q75", "q90"]
bande.to_csv(out / "backtest_bande_errore.csv", index=False, sep=";", float_format="%.4f")

# --- per NIL della sede e per citta'
nil_rows, citta_rows = [], []
for (m, o, T0, h), g in bt.groupby(["metodo", "ordine", "T0", "h"]):
    tgt = T0 + h
    reali = S[(S.ordine == o) & (S.anno_inizio == tgt)].groupby("id_nil").iscritti.sum()
    pr = g.groupby("id_nil").proiettati.sum()
    d = pd.DataFrame({"proiettati": pr, "reali": reali}).fillna(0)
    d2 = d[d.reali >= 200]
    nil_rows.append({"metodo": m, "ordine": o, "T0": T0, "h": h, "n_nil": len(d2),
                     "WAPE_nil": (d2.proiettati - d2.reali).abs().sum() / d2.reali.sum(),
                     "mediana_err_ass_nil": ((d2.proiettati - d2.reali).abs() / d2.reali).median()})
    citta_rows.append({"metodo": m, "ordine": o, "T0": T0, "h": h, "alunni_T0": g.iscritti_t0.sum(),
                       "proiettati": pr.sum(), "reali": reali.sum(), "err_citta": pr.sum() / reali.sum() - 1})
pd.DataFrame(nil_rows).to_csv(out / "backtest_nil.csv", index=False, sep=";", float_format="%.4f")
cit = pd.DataFrame(citta_rows)
cit.to_csv(out / "backtest_citta.csv", index=False, sep=";", float_format="%.4f")

# --- i tre casi richiesti
casi = []
nilb = pd.DataFrame(nil_rows)
for T0, h in [(2014, 5), (2019, 5), (2014, 10)]:
    for m in METODI:
        for o in lib.ORDINI:
            r1 = riep[(riep.metodo == m) & (riep.ordine == o) & (riep.h == h)]
            # riepilogo solo per questa partenza:
            g = bt[(bt.metodo == m) & (bt.ordine == o) & (bt.T0 == T0) & (bt.h == h)]
            rr = riepiloga(g)
            n_ = nilb[(nilb.metodo == m) & (nilb.ordine == o) & (nilb.T0 == T0) & (nilb.h == h)].iloc[0]
            c_ = cit[(cit.metodo == m) & (cit.ordine == o) & (cit.T0 == T0) & (cit.h == h)].iloc[0]
            casi.append({"partenza": T0, "arrivo": T0 + h, "metodo": m, "ordine": o,
                         "alunni_partenza": int(c_.alunni_T0), "alunni_proiettati": round(c_.proiettati),
                         "alunni_reali": int(c_.reali), "errore_citta_pct": 100 * c_.err_citta,
                         "WAPE_nil_pct": 100 * n_.WAPE_nil, "WAPE_scuola_pct": 100 * rr.WAPE_scuola,
                         "mediana_err_scuola_pct": 100 * rr.mediana_err_ass, "scuole_entro10_pct": 100 * rr.entro10,
                         "scuole_entro20_pct": 100 * rr.entro20, "n_scuole": int(rr.n_scuole)})
pd.DataFrame(casi).to_csv(out / "backtest_casi.csv", index=False, sep=";", float_format="%.2f")
print("fatto", len(bt))

# --- prova della soglia: "sotto il 70% del livello di riferimento" (riferimento = T0-5, bersaglio = T0+5)
sog = []
for T0 in range(2014, 2020):
    ref_y, tgt = T0 - 5, T0 + 5
    for o in lib.ORDINI:
        ref = S[(S.ordine == o) & (S.anno_inizio == ref_y) & (S.iscritti > 0)].set_index("codice").iscritti
        for m in ["fermo", "centrale", "solo_citta"]:
            g = bt[(bt.metodo == m) & (bt.ordine == o) & (bt.T0 == T0) & (bt.h == 5)].copy()
            g["ref"] = g.codice.map(ref)
            g = g[g.ref.notna() & g.esiste_dopo]
            for t in (0.7, 0.8):
                pred = (g.proiettati / g.ref) < t
                vero = (g.reali / g.ref) < t
                tp = int((pred & vero).sum())
                sog.append({"T0": T0, "ordine": o, "metodo": m, "soglia": t, "n": len(g), "previste": int(pred.sum()),
                            "vere": int(vero.sum()), "azzeccate": tp,
                            "accordo_totale": float((pred == vero).mean())})
sog = pd.DataFrame(sog)
sog.to_csv(out / "backtest_soglia.csv", index=False, sep=";", float_format="%.3f")
tot = sog.groupby(["ordine", "metodo", "soglia"])[["n", "previste", "vere", "azzeccate"]].sum().reset_index()
tot["precisione"] = tot.azzeccate / tot.previste
tot["richiamo"] = tot.azzeccate / tot.vere
tot["F1"] = 2 * tot.precisione * tot.richiamo / (tot.precisione + tot.richiamo)
tot.to_csv(out / "backtest_soglia_riepilogo.csv", index=False, sep=";", float_format="%.3f")
print(tot.round(3).to_string(index=False))
