"""Proiezione 2025/26-2034/35 per scuola e per NIL (scenario, non previsione).

Uso: python -I -X utf8 03_proietta.py <percorso assoluto milano-in-dati> <percorso assoluto scuole-domani>
Legge anche out/backtest_bande_errore.csv (da 02_backtest.py).
Scrive in out/: proiezione_scuole.csv, proiezione_nil.csv, proiezione_citta.csv, proiezione_residenti_nil.csv,
scuole_sotto_70.csv, sensibilita_scenari.csv
"""
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
idx = {i: k for k, i in enumerate(ids)}
T0 = 2024
ANNI = list(range(2025, 2035))          # a.s. 2025/26 ... 2034/35
SOGLIA = 0.70
RIF = 2015                              # anno di riferimento per la soglia (a.s. 2015/16)
nomi_nil = pd.read_csv(lib.percorsi(base)["nil"]).set_index("id_nil").nil.to_dict()

# --- elenco delle scuole attive nel 2024/25
anag = pd.read_csv(Path(base) / "scuole" / "pulito" / "comune_scuole_anagrafica.csv", sep=";")
anag["codice"] = "C" + anag.codice_comune.astype(str)
anag = anag.set_index("codice")
a24 = S[(S.anno_inizio == T0) & (S.iscritti > 0)].copy()
a15 = S[(S.anno_inizio == RIF) & (S.iscritti > 0)].set_index("codice").iscritti
a19 = S[(S.anno_inizio == 2019) & (S.iscritti > 0)].set_index("codice").iscritti
a24["iscritti_2015"] = a24.codice.map(a15)
a24["iscritti_2019"] = a24.codice.map(a19)
a24 = a24.rename(columns={"iscritti": "iscritti_2024"})

# --- scenari e varianti
COMBO = {   # nome -> (variante, scenario nascite)
    "centrale": ("centrale", "stabili"),
    "nati_in_calo": ("centrale", "calo"),
    "nati_in_risalita": ("centrale", "risalita"),
    "solo_citta": ("solo_citta", "stabili"),
    "solo_nil": ("solo_nil", "stabili"),
    "con_migrazione": ("con_migrazione", "stabili"),
}
F = {k: lib.fattori_variante(R, ADJ, T0, ANNI, v, scenario=sc)[0] for k, (v, sc) in COMBO.items()}
r_nati = lib.tasso_nascite_citta(R, T0 + 1, 5)
print("variazione media annua dei residenti di eta' 0 (citta', 2020-2025):", round(100 * r_nati, 2), "%")

bande = pd.read_csv(out / "backtest_bande_errore.csv", sep=";")


def proj(o, combo):
    sub = a24[a24.ordine == o]
    ii = sub.id_nil.map(idx).values
    f = F[combo][o][ii, :]
    f = np.where(np.isnan(f), F["solo_citta"][o][ii, :], f)
    return sub.iscritti_2024.values[:, None] * f


rows = []
for o in lib.ORDINI:
    sub = a24[a24.ordine == o].copy().reset_index(drop=True)
    P = {c: proj(o, c) for c in COMBO}
    for k, y in enumerate(ANNI):
        sub[f"p{y}"] = P["centrale"][:, k]
    for c in ["nati_in_calo", "nati_in_risalita", "solo_citta", "solo_nil", "con_migrazione"]:
        sub[f"p2034_{c}"] = P[c][:, -1]
        sub[f"p2029_{c}"] = P[c][:, 4]
    rows.append(sub)
sc = pd.concat(rows, ignore_index=True)

# fascia di errore dal back-test (rapporto reale/proiettato, 10° e 90° percentile, per ordine e orizzonte)
for y in (2029, 2034):
    h = y - T0
    lo = bande[bande.h == h].set_index("ordine").q10
    hi = bande[bande.h == h].set_index("ordine").q90
    sc[f"fascia_bassa_{y}"] = sc[f"p{y}"] * sc.ordine.map(lo)
    sc[f"fascia_alta_{y}"] = sc[f"p{y}"] * sc.ordine.map(hi)

sc["var_pct_2034_su_2024"] = 100 * (sc.p2034 / sc.iscritti_2024 - 1)
sc["var_pct_2024_su_2015"] = 100 * (sc.iscritti_2024 / sc.iscritti_2015 - 1)
sc["rapporto_2034_su_2015"] = sc.p2034 / sc.iscritti_2015
sc["rapporto_2024_su_2015"] = sc.iscritti_2024 / sc.iscritti_2015
sc["gia_sotto_70_nel_2024"] = sc.rapporto_2024_su_2015 < SOGLIA
sc["sotto_70_nel_2034"] = sc.rapporto_2034_su_2015 < SOGLIA
nuovi = [c for c in ["nati_in_calo", "nati_in_risalita", "solo_citta", "solo_nil", "con_migrazione"]]
cols = ["p2034"] + [f"p2034_{c}" for c in nuovi]
sotto = np.column_stack([(sc[c] / sc.iscritti_2015) < SOGLIA for c in cols])
sc["n_varianti_sotto_70"] = np.where(sc.iscritti_2015.notna(), sotto.sum(axis=1), np.nan)
sc["tenuta_del_risultato"] = np.select(
    [sc.iscritti_2015.isna(), sc.n_varianti_sotto_70 == len(cols), sc.n_varianti_sotto_70 == 0],
    ["senza riferimento 2015", "sotto 70% in tutte e 6 le varianti", "sopra 70% in tutte e 6 le varianti"],
    default="dipende dalla variante")
# anno in cui, nello scenario centrale, scende sotto il 70% del 2015
def primo_anno(r):
    if pd.isna(r.iscritti_2015):
        return np.nan
    for y in ANNI:
        if r[f"p{y}"] / r.iscritti_2015 < SOGLIA:
            return y
    return np.nan
sc["primo_anno_sotto_70"] = sc.apply(primo_anno, axis=1)
sc["nome_nil"] = sc.id_nil.map(nomi_nil)
sc["piccola_meno_50_alunni_2024"] = sc.iscritti_2024 < 50
sc["ultima_localizzazione_incerta"] = sc.codice.map(anag.metodo_nil).fillna("") != "poligono"

keep = ["ordine", "codice", "denominazione", "indirizzo", "gestione", "id_nil", "nome_nil", "classi", "iscritti_2015", "iscritti_2019",
        "iscritti_2024"] + [f"p{y}" for y in ANNI] + ["fascia_bassa_2029", "fascia_alta_2029", "fascia_bassa_2034", "fascia_alta_2034",
        "var_pct_2034_su_2024", "var_pct_2024_su_2015", "rapporto_2024_su_2015", "rapporto_2034_su_2015", "gia_sotto_70_nel_2024",
        "sotto_70_nel_2034", "primo_anno_sotto_70", "n_varianti_sotto_70", "tenuta_del_risultato",
        "p2034_nati_in_calo", "p2034_nati_in_risalita", "p2034_solo_citta", "p2034_solo_nil", "p2034_con_migrazione",
        "piccola_meno_50_alunni_2024", "ultima_localizzazione_incerta"]
sc[keep].rename(columns={"classi": "classi_2024"}).to_csv(out / "proiezione_scuole.csv", sep=";", index=False, float_format="%.3f")

# --- soglia 70%: elenco ordinato
lista = sc[sc.sotto_70_nel_2034 & sc.iscritti_2015.notna()].sort_values(["ordine", "rapporto_2034_su_2015"])
lista[["ordine", "codice", "denominazione", "indirizzo", "gestione", "nome_nil", "iscritti_2015", "iscritti_2024", "p2034",
       "rapporto_2024_su_2015", "rapporto_2034_su_2015", "gia_sotto_70_nel_2024", "primo_anno_sotto_70", "tenuta_del_risultato",
       "piccola_meno_50_alunni_2024"]].to_csv(out / "scuole_sotto_70.csv", sep=";", index=False, float_format="%.3f")

# --- per NIL (sede delle scuole)
g = sc.groupby(["ordine", "id_nil"])
agg = g.agg(n_scuole=("codice", "count"), iscritti_2015=("iscritti_2015", "sum"), iscritti_2024=("iscritti_2024", "sum"),
            **{f"p{y}": (f"p{y}", "sum") for y in ANNI}, p2034_nati_in_calo=("p2034_nati_in_calo", "sum"),
            p2034_nati_in_risalita=("p2034_nati_in_risalita", "sum"), p2034_solo_citta=("p2034_solo_citta", "sum"),
            p2034_solo_nil=("p2034_solo_nil", "sum"), p2034_con_migrazione=("p2034_con_migrazione", "sum"),
            n_scuole_sotto_70_2034=("sotto_70_nel_2034", "sum"), n_scuole_con_rif_2015=("iscritti_2015", "count")).reset_index()
# iscritti_2015 NIL: tutte le scuole del NIL nel 2015 (anche chiuse dopo), per un confronto onesto a livello di NIL
tot15 = S[(S.anno_inizio == RIF)].groupby(["ordine", "id_nil"]).iscritti.sum().rename("iscritti_2015_nil_tutte_le_scuole").reset_index()
agg = agg.merge(tot15, on=["ordine", "id_nil"], how="left")
agg["nome_nil"] = agg.id_nil.map(nomi_nil)
agg["var_pct_2034_su_2024"] = 100 * (agg.p2034 / agg.iscritti_2024 - 1)
agg["var_pct_2024_su_2015_tutte"] = 100 * (agg.iscritti_2024 / agg.iscritti_2015_nil_tutte_le_scuole - 1)
agg["rapporto_2034_su_2015_tutte"] = agg.p2034 / agg.iscritti_2015_nil_tutte_le_scuole
agg["quota_alunni_in_scuole_sotto_70_2034_pct"] = 100 * sc[sc.sotto_70_nel_2034 & sc.iscritti_2015.notna()].groupby(["ordine", "id_nil"]).iscritti_2024.sum().reindex(
    pd.MultiIndex.from_frame(agg[["ordine", "id_nil"]])).fillna(0).values / agg.iscritti_2024
agg.to_csv(out / "proiezione_nil.csv", sep=";", index=False, float_format="%.2f")

# --- bambini residenti nel NIL (dato di partenza e proiezione, solo nel NIL, nascite stabili): quanti bambini ci sono dove sta la scuola
_, Pn = lib.fattori_area(R, ADJ["nil"], T0, ANNI, 5, "stabili", mig="nessuna")
_, Pn_calo = lib.fattori_area(R, ADJ["nil"], T0, ANNI, 5, "calo", mig="nessuna")
resrows = []
for o, (lo, hi) in lib.BANDE.items():
    for k, i in enumerate(ids):
        d = {"ordine": o, "id_nil": i, "nome_nil": nomi_nil.get(i),
             "residenti_fascia_2015": R[k, 2015 - 1999, lo:hi + 1].sum(), "residenti_fascia_2024": R[k, 2024 - 1999, lo:hi + 1].sum(),
             "residenti_fascia_2025": R[k, 2025 - 1999, lo:hi + 1].sum()}
        for j, y in enumerate(ANNI):
            d[f"res{y}"] = Pn[k, j, lo:hi + 1].sum()
        d["res2034_nati_in_calo"] = Pn_calo[k, -1, lo:hi + 1].sum()
        resrows.append(d)
res = pd.DataFrame(resrows)
res["var_pct_2034_su_2025"] = 100 * (res.res2034 / res.residenti_fascia_2025 - 1)
res.to_csv(out / "proiezione_residenti_nil.csv", sep=";", index=False, float_format="%.2f")

# --- citta'
cr = []
cls = a24.groupby("ordine").classi.sum()
for o in lib.ORDINI:
    sub = sc[sc.ordine == o]
    for c, (v, scn) in COMBO.items():
        P = proj(o, c).sum(axis=0)
        for y, val in zip(ANNI, P):
            cr.append({"ordine": o, "combinazione": c, "anno": y, "alunni_proiettati": val})
    cr.append({"ordine": o, "combinazione": "reale", "anno": 2024, "alunni_proiettati": sub.iscritti_2024.sum()})
    cr.append({"ordine": o, "combinazione": "reale", "anno": 2015, "alunni_proiettati": S[(S.ordine == o) & (S.anno_inizio == 2015)].iscritti.sum()})
citta = pd.DataFrame(cr)
citta["alunni_per_classe_2024"] = citta.ordine.map(a24.groupby("ordine").iscritti_2024.sum() / cls)
citta["classi_equivalenti"] = citta.alunni_proiettati / citta.alunni_per_classe_2024
citta.to_csv(out / "proiezione_citta.csv", sep=";", index=False, float_format="%.1f")

# --- sensibilita' sintetica
sens = []
for o in lib.ORDINI:
    sub = sc[sc.ordine == o]
    for c in ["p2034", "p2034_nati_in_calo", "p2034_nati_in_risalita", "p2034_solo_citta", "p2034_solo_nil", "p2034_con_migrazione"]:
        ref = sub.iscritti_2015.notna()
        sens.append({"ordine": o, "scenario": c, "alunni_2024": sub.iscritti_2024.sum(), "alunni_2034": sub[c].sum(),
                     "var_pct": 100 * (sub[c].sum() / sub.iscritti_2024.sum() - 1),
                     "scuole": len(sub), "scuole_sotto_70_del_2015": int(((sub[c] / sub.iscritti_2015) < SOGLIA)[ref].sum()),
                     "scuole_con_riferimento_2015": int(ref.sum())})
pd.DataFrame(sens).to_csv(out / "sensibilita_scenari.csv", sep=";", index=False, float_format="%.2f")
print(pd.DataFrame(sens).round(1).to_string(index=False))
print(sc.groupby("ordine").agg(n=("codice", "count"), gia70=("gia_sotto_70_nel_2024", "sum"), sotto34=("sotto_70_nel_2034", "sum")))
print(sc.groupby(["ordine", "tenuta_del_risultato"]).size())
