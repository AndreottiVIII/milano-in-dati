"""Prepara i dati aggregati per la pagina docs/redditi/ (solo valori aggregati, nessun dato personale).
Uso: python -I -X utf8 pagina.py <percorso assoluto redditi> <percorso assoluto milano-in-dati>
Legge redditi/pulito/*.csv (prodotti da analisi.py, nazionale.py, riepilogo.py) e scrive in milano-in-dati/docs/redditi/data/:
 riepilogo.json (tutto cio' che usa la pagina, con l'origine dei numeri), serie_citta.csv, classi_milano.csv, tipi_reddito.csv,
 soglie_reali.csv, cap_milano.csv, cap_divario_per_citta.csv, cap_gruppi_milano.csv, italia_lombardia_serie_definitiva.csv.
Rilanciabile: sovrascrive i file."""
import sys, os, json, shutil
import numpy as np, pandas as pd

base, root = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito"); OUT = os.path.join(root, "docs", "redditi", "data")
os.makedirs(OUT, exist_ok=True)
foi = pd.read_csv(os.path.join(root, "prezzi-case", "pulito", "foi_annuale.csv")).set_index("anno")["indice_raccordato_2025_100"]
defl = (100.0 / foi).to_dict()
S = pd.read_csv(os.path.join(P, "serie_unita_anno.csv")); F = pd.read_csv(os.path.join(P, "italia_lombardia_serie_definitiva.csv"))
T = pd.read_csv(os.path.join(P, "tipi_reddito.csv")); SR = pd.read_csv(os.path.join(P, "soglie_reali.csv"))
G = pd.read_csv(os.path.join(P, "cap_divario_per_citta.csv")); C = pd.read_csv(os.path.join(P, "cap_redditi_tutte_le_citta.csv"), dtype={"cap": str})
ANNI = list(range(2000, 2025))
CITTA = ["Milano", "Roma", "Torino", "Napoli", "Bologna"]
UNITA = CITTA + ["Lombardia", "Italia"]


def R(x, d=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


# ---------- serie per unita' ----------
rows = []
for u in UNITA:
    for t in ANNI:
        if u in CITTA:
            r = S[(S.unita == u) & (S.anno_imposta == t)].iloc[0]
            g, q120r, q120c, s15, s10 = r.gini_classi, r.quota_reddito_sopra_120k, r.quota_contr_sopra_120k, r.quota_contr_sotto_15k, r.quota_contr_sotto_10k
            fonte = "somma_comuni_MEF"
        else:
            r = F[(F.unita == u) & (F.anno_imposta == t)].iloc[0]
            g, q120r, q120c, s15, s10 = r.gini_classi_grandi, r.quota_reddito_sopra_120k, r.quota_contr_sopra_120k, r.quota_contr_sotto_15k, r.quota_contr_sotto_10k
            fonte = r.fonte_dato
        sr = SR[(SR.unita == u) & (SR.anno_imposta == t)].iloc[0]
        a55, a26 = sr.quota_sopra_55k_euro2000, sr.quota_sopra_26k_euro2000
        if u in ("Italia", "Lombardia") and t >= 2023:   # celle oscurate nei file comunali: soglie reali non affidabili
            a55 = a26 = np.nan
        rows.append({"unita": u, "anno_imposta": t, "contribuenti": r.contribuenti, "media_nominale": r.media_nominale, "media_euro2025": r.media_euro2025,
                     "gini_classi": g, "quota_reddito_sopra_120k": q120r, "quota_contr_sopra_120k": q120c, "quota_contr_sotto_15k": s15, "quota_contr_sotto_10k": s10,
                     "quota_contr_sopra_55k_euro2000": a55, "quota_contr_sopra_26k_euro2000": a26, "fonte_dato": fonte})
SC = pd.DataFrame(rows)
SC.to_csv(os.path.join(OUT, "serie_citta.csv"), index=False, float_format="%.6g")
serie = {}
for u in UNITA:
    x = SC[SC.unita == u].sort_values("anno_imposta")
    serie[u] = {k: [R(v, 4 if k.startswith(("gini", "quota")) else 0) for v in x[k]] for k in
                ["media_nominale", "media_euro2025", "gini_classi", "quota_reddito_sopra_120k", "quota_contr_sopra_120k", "quota_contr_sotto_15k",
                 "quota_contr_sotto_10k", "quota_contr_sopra_55k_euro2000", "quota_contr_sopra_26k_euro2000"]}
    serie[u]["fonte_dato"] = list(x.fonte_dato)

# ---------- classi Milano ----------
CL = ["cl0_le0", "cl1_0_10k", "cl2_10_15k", "cl3_15_26k", "cl4_26_55k", "cl5_55_75k", "cl6_75_120k", "cl7_oltre120k"]
ETI = ["fino a 0", "0-10.000", "10.000-15.000", "15.000-26.000", "26.000-55.000", "55.000-75.000", "75.000-120.000", "oltre 120.000"]
M = S[S.unita == "Milano"].sort_values("anno_imposta")
cm = {"etichette": ETI, "anni": ANNI,
      "quota_contribuenti": {int(r.anno_imposta): [R(r["quota_contribuenti_" + c] * 100, 2) for c in CL] for _, r in M.iterrows()},
      "quota_reddito": {int(r.anno_imposta): [R(r["quota_reddito_" + c] * 100, 2) for c in CL] for _, r in M.iterrows()}}
pd.DataFrame([{"anno_imposta": int(r.anno_imposta), **{"quota_contribuenti_" + c: r["quota_contribuenti_" + c] for c in CL}, **{"quota_reddito_" + c: r["quota_reddito_" + c] for c in CL}} for _, r in M.iterrows()]).to_csv(os.path.join(OUT, "classi_milano.csv"), index=False, float_format="%.6g")
SR.to_csv(os.path.join(OUT, "soglie_reali.csv"), index=False, float_format="%.6g")

# ---------- tipi ----------
TIPI = ["dipendente", "pensione", "autonomo", "impresa"]
tipi = {}
for u in ("Milano", "Italia"):
    x = T[(T.unita == u) & (T.anno_imposta >= 2002)].sort_values("anno_imposta")
    tipi[u] = {"anni": [int(a) for a in x.anno_imposta]}
    for k in TIPI:
        tipi[u][k + "_quota_contribuenti"] = [R(v * 100, 2) for v in x[k + "_quota_contribuenti"]]
        tipi[u][k + "_per_percettore_euro2025"] = [R(v, 0) for v in x[k + "_per_percettore_euro2025"]]
        tipi[u][k + "_quota_reddito"] = [R(v * 100, 2) for v in x[k + "_quota_del_reddito_complessivo"]]
        tipi[u][k + "_percettori"] = [R(v, 0) for v in x[k + "_n"]]
T[T.unita.isin(["Milano", "Italia"])].to_csv(os.path.join(OUT, "tipi_reddito.csv"), index=False, float_format="%.6g")

# ---------- CAP ----------
mil = C[C.comune.str.upper() == "MILANO"].copy()
anni_cap = sorted(mil.anno.unique())
caps = sorted(mil.cap.unique())
cap = {"anni": [int(a) for a in anni_cap], "cap": {}}
for cp in caps:
    x = mil[mil.cap == cp].sort_values("anno")
    cap["cap"][cp] = {"contribuenti": [int(v) for v in x.contribuenti], "media_euro2025": [R(v, 0) for v in x.media_euro2025], "media_nominale": [R(v, 0) for v in x.media_nominale]}
mil[["cap", "anno", "contribuenti", "media_nominale", "media_euro2025", "reddito_eur"]].rename(columns={"anno": "anno_imposta", "reddito_eur": "reddito_complessivo_eur"}).sort_values(["cap", "anno_imposta"]).to_csv(os.path.join(OUT, "cap_milano.csv"), index=False, float_format="%.6g")
# cambi di assegnazione: variazione dei contribuenti > 15% tra un anno e l'altro
flags = []
pv = mil.pivot(index="cap", columns="anno", values="contribuenti"); ys = list(pv.columns)
for i in range(1, len(ys)):
    ch = pv[ys[i]] / pv[ys[i - 1]] - 1
    for cp, v in ch[ch.abs() > 0.15].items():
        flags.append({"cap": cp, "da": int(ys[i - 1]), "a": int(ys[i]), "contribuenti_da": int(pv.loc[cp, ys[i - 1]]), "contribuenti_a": int(pv.loc[cp, ys[i]]), "variazione_pct": R(v * 100, 0)})
cap["cambi_assegnazione"] = flags
# gruppi di CAP per reddito 2011
a = mil[mil.anno == 2011].set_index("cap"); b = mil[mil.anno == 2024].set_index("cap")
a = a.assign(q=pd.qcut(a.media_euro2025, 4, labels=["1", "2", "3", "4"]))
gr = []
for q, g_ in a.groupby("q", observed=True):
    ix = g_.index
    m11 = a.loc[ix, "reddito_eur"].sum() / a.loc[ix, "contribuenti"].sum() * defl[2011]
    m24 = b.loc[ix, "reddito_eur"].sum() / b.loc[ix, "contribuenti"].sum() * defl[2024]
    gr.append({"gruppo": int(q), "n_cap": len(ix), "cap": sorted(ix), "contribuenti_2011": int(a.loc[ix, "contribuenti"].sum()), "contribuenti_2024": int(b.loc[ix, "contribuenti"].sum()),
               "media_2011_euro2025": R(m11, 0), "media_2024_euro2025": R(m24, 0), "variazione_reale_pct": R((m24 / m11 - 1) * 100, 1)})
pd.DataFrame(gr).drop(columns=["cap"]).to_csv(os.path.join(OUT, "cap_gruppi_milano.csv"), index=False)
cap["gruppi"] = gr
# divario tra CAP, citta'
nomi = {"MILANO": "Milano", "ROMA": "Roma", "TORINO": "Torino", "NAPOLI": "Napoli", "BOLOGNA": "Bologna"}
gd = G[G.comune.isin(nomi)].copy(); gd["unita"] = gd.comune.map(nomi)
gd[["unita", "anno_imposta", "n_cap", "p90_su_p10", "gini_tra_cap", "rapporto_max_min", "min_cap", "max_cap"]].sort_values(["unita", "anno_imposta"]).to_csv(os.path.join(OUT, "cap_divario_per_citta.csv"), index=False, float_format="%.6g")
cap["divario"] = {u: {"anni": [int(v) for v in x.anno_imposta], "p90_su_p10": [R(v, 3) for v in x.p90_su_p10], "gini_tra_cap": [R(v, 4) for v in x.gini_tra_cap], "n_cap": int(x.n_cap.iloc[0])}
                  for u, x in ((u, gd[gd.unita == u].sort_values("anno_imposta")) for u in nomi.values())}
gu = G[G.comune == "MILANO (20121+20122 uniti)"].sort_values("anno_imposta")
cap["milano_20121_20122_uniti_p90_su_p10"] = [R(v, 3) for v in gu.p90_su_p10]

# ---------- numeri citati nel testo (con l'origine) ----------
sm = S[S.unita == "Milano"].set_index("anno_imposta"); si = F[F.unita == "Italia"].set_index("anno_imposta")
tm = T[T.unita == "Milano"].set_index("anno_imposta"); ti = T[T.unita == "Italia"].set_index("anno_imposta")
pop = sm.contribuenti_per_100_abitanti
sn = S[S.unita == "Napoli"].set_index("anno_imposta")
f = defl[2024] / defl[2000]
num = {
    "milano_media_euro2025": {"2000": R(sm.media_euro2025[2000], 0), "2006": R(sm.media_euro2025[2006], 0), "2011": R(sm.media_euro2025[2011], 0), "2024": R(sm.media_euro2025[2024], 0)},
    "milano_media_nominale": {"2000": R(sm.media_nominale[2000], 0), "2024": R(sm.media_nominale[2024], 0)},
    "milano_nominale_var_pct_2000_2024": R((sm.media_nominale[2024] / sm.media_nominale[2000] - 1) * 100, 1),
    "milano_reale_var_pct_2000_2024": R((sm.media_euro2025[2024] / sm.media_euro2025[2000] - 1) * 100, 1),
    "milano_reale_var_pct_2006_2024": R((sm.media_euro2025[2024] / sm.media_euro2025[2006] - 1) * 100, 1),
    "milano_reale_var_pct_2011_2024": R((sm.media_euro2025[2024] / sm.media_euro2025[2011] - 1) * 100, 1),
    "var_reale_pct_2006_2024": {u: R((SC[(SC.unita == u) & (SC.anno_imposta == 2024)].media_euro2025.iloc[0] / SC[(SC.unita == u) & (SC.anno_imposta == 2006)].media_euro2025.iloc[0] - 1) * 100, 1) for u in UNITA},
    "var_reale_pct_2000_2024": {u: R((SC[(SC.unita == u) & (SC.anno_imposta == 2024)].media_euro2025.iloc[0] / SC[(SC.unita == u) & (SC.anno_imposta == 2000)].media_euro2025.iloc[0] - 1) * 100, 1) for u in UNITA},
    "milano_su_italia_nominale": {"2000": R(sm.media_nominale[2000] / si.media_nominale[2000], 2), "2006": R(sm.media_nominale[2006] / si.media_nominale[2006], 2), "2024": R(sm.media_nominale[2024] / si.media_nominale[2024], 2)},
    "gruppi_cap_var_reale_pct_2011_2024": [g_["variazione_reale_pct"] for g_ in gr],
    "pensione_per_pensionato_milano_euro2025": {"2002": R(tm.pensione_per_percettore_euro2025[2002], 0), "2010": R(tm.pensione_per_percettore_euro2025[2010], 0), "2024": R(tm.pensione_per_percettore_euro2025[2024], 0)},
    "dipendente_per_dipendente_milano_euro2025": {"2002": R(tm.dipendente_per_percettore_euro2025[2002], 0), "2010": R(tm.dipendente_per_percettore_euro2025[2010], 0), "2024": R(tm.dipendente_per_percettore_euro2025[2024], 0)},
    "pensione_per_pensionato_italia_euro2025": {"2002": R(ti.pensione_per_percettore_euro2025[2002], 0), "2010": R(ti.pensione_per_percettore_euro2025[2010], 0), "2024": R(ti.pensione_per_percettore_euro2025[2024], 0)},
    "dipendente_per_dipendente_italia_euro2025": {"2002": R(ti.dipendente_per_percettore_euro2025[2002], 0), "2010": R(ti.dipendente_per_percettore_euro2025[2010], 0), "2024": R(ti.dipendente_per_percettore_euro2025[2024], 0)},
    "pensione_milano_var_pct_2002_2024": R((tm.pensione_per_percettore_euro2025[2024] / tm.pensione_per_percettore_euro2025[2002] - 1) * 100, 1),
    "dipendente_milano_var_pct_2002_2024": R((tm.dipendente_per_percettore_euro2025[2024] / tm.dipendente_per_percettore_euro2025[2002] - 1) * 100, 1),
    "pensione_milano_var_pct_2010_2024": R((tm.pensione_per_percettore_euro2025[2024] / tm.pensione_per_percettore_euro2025[2010] - 1) * 100, 1),
    "dipendente_milano_var_pct_2010_2024": R((tm.dipendente_per_percettore_euro2025[2024] / tm.dipendente_per_percettore_euro2025[2010] - 1) * 100, 1),
    "pensione_italia_var_pct_2010_2024": R((ti.pensione_per_percettore_euro2025[2024] / ti.pensione_per_percettore_euro2025[2010] - 1) * 100, 1),
    "dipendente_italia_var_pct_2010_2024": R((ti.dipendente_per_percettore_euro2025[2024] / ti.dipendente_per_percettore_euro2025[2010] - 1) * 100, 1),
    "autonomi_milano_percettori": {"2018": R(tm.autonomo_n[2018], 0), "2019": R(tm.autonomo_n[2019], 0)},
    "autonomo_milano_per_percettore_euro2025": {"2018": R(tm.autonomo_per_percettore_euro2025[2018], 0), "2019": R(tm.autonomo_per_percettore_euro2025[2019], 0)},
    "milano_sotto_10k_2024_pct": R(sm.quota_contr_sotto_10k[2024] * 100, 1), "milano_sotto_10k_2000_pct": R(sm.quota_contr_sotto_10k[2000] * 100, 1),
    "milano_gini": {"2000": R(sm.gini_classi[2000], 3), "2022": R(sm.gini_classi[2022], 3), "2024": R(sm.gini_classi[2024], 3)},
    "milano_quota_reddito_sopra_120k_pct": {"2000": R(sm.quota_reddito_sopra_120k[2000] * 100, 1), "2024": R(sm.quota_reddito_sopra_120k[2024] * 100, 1)},
    "milano_quota_contr_sopra_120k_pct": {"2000": R(sm.quota_contr_sopra_120k[2000] * 100, 2), "2024": R(sm.quota_contr_sopra_120k[2024] * 100, 2)},
    "soglia_55k_euro2000_in_nominale_2024": R(SR[(SR.unita == "Milano") & (SR.anno_imposta == 2024)].soglia_55k_euro2000_in_nominale.iloc[0], 0),
    "soglia_26k_euro2000_in_nominale_2024": R(26000 / f, 0),
    "120k_euro2000_in_euro2025": R(120000 * defl[2000], 0), "120k_euro2000_in_nominale_2024": R(120000 / f, 0),
    "inflazione_2000_2024_pct": R((1 / f - 1) * 100, 1),
    "contribuenti_per_100_abitanti_2024": {"Milano": R(pop[2024], 1), "Napoli": R(sn.contribuenti_per_100_abitanti[2024], 1)},
    "milano_contribuenti_2024": R(sm.contribuenti[2024], 0), "milano_senza_classe_2024": R(sm.senza_classe[2024], 0),
    "milano_reddito_da_fabbricati_miliardi": {"2010": R(T[(T.unita == "Milano") & (T.anno_imposta == 2010)].fabbricati_eur.iloc[0] / 1e9, 2), "2012": R(T[(T.unita == "Milano") & (T.anno_imposta == 2012)].fabbricati_eur.iloc[0] / 1e9, 2)},
    "italia_somma_comuni_vs_file_regionali_media_2024_pct": R((S[(S.unita == "Italia") & (S.anno_imposta == 2024)].media_nominale.iloc[0] / F[(F.unita == "Italia") & (F.anno_imposta == 2024)].media_nominale.iloc[0] - 1) * 100, 1),
}
fonti = {
    "mef": {"nome": "Ministero dell'Economia e delle Finanze, Dipartimento delle Finanze, Open data \"Redditi e principali variabili IRPEF\" (base comunale 2000-2024; base sub-comunale per CAP 2011, 2015, 2019-2024; file per regione e classe 2016-2024)",
            "licenza": "Creative Commons Attribution 3.0 (CC BY 3.0), dichiarata nei metadati RDF dei file; la pagina web del MEF lascia vuoto il campo Tipo licenza",
            "url": "https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes", "scaricato": "2026-11-01"},
    "istat_popolazione": {"nome": "ISTAT, demo.istat.it, popolazione residente al 1 gennaio (ricostruzione 2002-2019 e POSAS 2020-2026)", "licenza": "CC BY 4.0", "url": "https://demo.istat.it/", "scaricato": "2026-11-01"},
    "istat_foi": {"nome": "ISTAT, indice FOI (senza tabacchi), medie annue raccordate a 2025 = 100 (dalla pagina prezzi-case)", "licenza": "CC BY 4.0", "url": "https://esploradati.istat.it/", "scaricato": "2026-10"},
    "comune_pop_2000_01": {"nome": "Comune di Milano, ds71 popolazione calcolata ISTAT 31/12 (solo per il rapporto contribuenti/abitanti 2000-2001, non usato nella pagina)", "licenza": "CC BY"},
}
J = {"meta": {"titolo": "Redditi dei milanesi dal 2000", "anni_imposta": [2000, 2024], "generato_da": "redditi/scripts/pagina.py", "deflatore": "euro 2025 = euro correnti x 100 / FOI annuale (2025 = 100), anno d'imposta"},
     "anni": ANNI, "serie": serie, "classi_milano": cm, "tipi": tipi, "cap": cap, "numeri": num, "fonti": fonti}
json.dump(J, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
shutil.copy(os.path.join(P, "italia_lombardia_serie_definitiva.csv"), os.path.join(OUT, "italia_lombardia_serie_definitiva.csv"))
print("ok", os.path.getsize(os.path.join(OUT, "riepilogo.json")), "byte")
print(json.dumps(num, ensure_ascii=False)[:3500])
