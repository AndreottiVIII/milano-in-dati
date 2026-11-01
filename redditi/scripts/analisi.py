"""Analisi redditi (MEF, dichiarazioni IRPEF, anni d'imposta 2000-2024).
Uso: python -I -X utf8 analisi.py <percorso assoluto redditi> <percorso assoluto milano-in-dati>
Legge pulito/mef_comuni_2000_2024.csv, pulito/mef_cap_2011_2024.csv, pulito/popolazione_1gen.csv,
l'indice FOI di prezzi-case/pulito/foi_annuale.csv e la popolazione Milano di bilancio-comune/pulito.
Scrive in pulito/: serie_unita_anno.csv, tipi_reddito.csv, soglie_reali.csv, cap_*.csv, riepilogo.json.
METODO (riassunto, completo in NOTE.md):
 - reddito complessivo = somma degli importi delle 8 classi (<=0, 0-10k, 10-15k, 15-26k, 26-55k, 55-75k, 75-120k, >120k);
   dal 2023 coincide col campo 'Reddito complessivo - Ammontare' (controllo per Milano).
 - media per contribuente = reddito complessivo / 'Numero contribuenti' (come i riepiloghi MEF).
 - euro 2025 = nominale x 100 / indice FOI annuale (2025=100) dell'anno d'imposta.
 - Gini da classi (esclusa la classe <=0, che nel 2017 ha un valore anomalo a livello nazionale): curva di Lorenz con i punti alle soglie (n e importo di ogni classe) uniti da segmenti: SOTTOSTIMA la
   disuguaglianza (ignora quella dentro ogni classe); serve per confronti nel tempo e tra citta', non come valore assoluto."""
import sys, os, json, math
import numpy as np, pandas as pd

base, root = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito")
foi = pd.read_csv(os.path.join(root, "prezzi-case", "pulito", "foi_annuale.csv")).set_index("anno")["indice_raccordato_2025_100"]
defl = (100.0 / foi).to_dict()   # da moltiplicare per il nominale dell'anno t

d = pd.read_csv(os.path.join(P, "mef_comuni_2000_2024.csv"), dtype={"catastale": str, "istat": str, "cap": str})
CL = ["cl0_le0", "cl1_0_10k", "cl2_10_15k", "cl3_15_26k", "cl4_26_55k", "cl5_55_75k", "cl6_75_120k", "cl7_oltre120k"]
UP = [0, 10000, 15000, 26000, 55000, 75000, 120000, np.inf]
LO = [-np.inf, 0, 10000, 15000, 26000, 55000, 75000, 120000]
reg = d["regione"].str.upper().str.replace(r"[^A-Z]", "", regex=True)
d["is_lomb"] = reg.eq("LOMBARDIA")
UNITA = {"Milano": d.catastale.eq("F205"), "Roma": d.catastale.eq("H501"), "Torino": d.catastale.eq("L219"),
         "Napoli": d.catastale.eq("F839"), "Bologna": d.catastale.eq("A944"), "Lombardia": d.is_lomb,
         "Lombardia senza Milano": d.is_lomb & ~d.catastale.eq("F205"),
         "Italia": pd.Series(True, index=d.index), "Italia senza Milano": ~d.catastale.eq("F205")}


def gini_classi(n, y):
    n = np.asarray(n, float); y = np.asarray(y, float)
    N, Y = n.sum(), y.sum()
    p = np.concatenate([[0], np.cumsum(n) / N]); L = np.concatenate([[0], np.cumsum(y) / Y])
    return float(1 - np.sum((p[1:] - p[:-1]) * (L[1:] + L[:-1])))


def quota_sopra(n, soglia):
    """Quota (0-1) di contribuenti sopra 'soglia' euro, con densita' uniforme dentro la classe. Valida per 0 < soglia < 120000."""
    n = np.asarray(n, float); N = n.sum(); acc = 0.0
    for k in range(len(n)):
        if UP[k] <= soglia:
            continue
        if LO[k] >= soglia:
            acc += n[k]
        else:
            acc += n[k] * (UP[k] - soglia) / (UP[k] - LO[k])
    return acc / N


def mediana(n):
    n = np.asarray(n, float); N = n.sum(); c = 0.0
    for k in range(len(n)):
        if c + n[k] >= N / 2 and np.isfinite(LO[k]) and np.isfinite(UP[k]):
            return LO[k] + (N / 2 - c) / n[k] * (UP[k] - LO[k])
        c += n[k]
    return float("nan")


# ---------- popolazione (1 gennaio dell'anno successivo a quello d'imposta) ----------
pop = pd.read_csv(os.path.join(P, "popolazione_1gen.csv"))
popm = pop.pivot(index="anno_1_gennaio", columns="unita", values="popolazione")
m71 = pd.read_csv(os.path.join(root, "bilancio-comune", "pulito", "popolazione_milano.csv"), sep=";", encoding="utf-8-sig").set_index("anno")["pop_calcolata_istat_fine_anno"]


def popolazione(u, t):
    if u in popm.columns and (t + 1) in popm.index:
        return float(popm.loc[t + 1, u]), "ISTAT popolazione al 1/1/%d" % (t + 1)
    if u == "Milano" and t in m71.index:
        return float(m71[t]), "ds71 Comune di Milano, 31/12/%d (prima del censimento 2001: sovrastima)" % t
    return float("nan"), ""


# ---------- serie per unita' e anno ----------
rows = []
for u, mask in UNITA.items():
    for t, g in d[mask].groupby("anno"):
        n = np.array([g[c + "_n"].sum() for c in CL]); y = np.array([g[c + "_eur"].sum() for c in CL])
        N_ctr = g["contribuenti"].sum(); Ncl = n.sum(); Y = y.sum(); f = defl[t]
        r = {"unita": u, "anno_imposta": t, "n_comuni": len(g), "contribuenti": N_ctr, "contribuenti_con_classe": Ncl,
             "senza_classe": N_ctr - Ncl, "reddito_complessivo_eur": Y,
             "media_nominale": Y / N_ctr, "media_su_classificati": Y / Ncl, "media_euro2025": Y / N_ctr * f,
             "mediana_stimata_nominale": mediana(n), "mediana_stimata_euro2025": mediana(n) * f,
             "deflatore_a_euro2025": f, "gini_classi": gini_classi(n[1:], y[1:])}
        if t >= 2023:
            r["controllo_campo_reddito_complessivo_eur"] = g["reddito_complessivo_eur"].sum()
        pp, fonte = popolazione(u, t)
        r["popolazione"] = pp; r["fonte_popolazione"] = fonte
        r["contribuenti_per_100_abitanti"] = N_ctr / pp * 100 if pp == pp else float("nan")
        for k, c in enumerate(CL):
            r["quota_contribuenti_" + c] = n[k] / Ncl; r["quota_reddito_" + c] = y[k] / Y
        r["quota_contr_sotto_10k"] = (n[0] + n[1]) / Ncl; r["quota_contr_sotto_15k"] = (n[0] + n[1] + n[2]) / Ncl
        r["quota_contr_sopra_75k"] = (n[6] + n[7]) / Ncl; r["quota_contr_sopra_120k"] = n[7] / Ncl
        r["quota_reddito_sopra_120k"] = y[7] / Y; r["quota_reddito_sopra_75k"] = (y[6] + y[7]) / Y
        r["quota_reddito_sotto_15k"] = (y[0] + y[1] + y[2]) / Y
        r["media_classe_oltre120k_nominale"] = y[7] / n[7]
        r["rapporto_media_oltre120k_su_media_generale"] = (y[7] / n[7]) / (Y / Ncl)
        rows.append(r)
S = pd.DataFrame(rows).sort_values(["unita", "anno_imposta"])
S.to_csv(os.path.join(P, "serie_unita_anno.csv"), index=False, float_format="%.6g")

# ---------- soglie costanti in euro reali (euro del 2000) ----------
rr = []
for u in ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Lombardia", "Italia"]:
    for t, g in d[UNITA[u]].groupby("anno"):
        n = np.array([g[c + "_n"].sum() for c in CL]); f = defl[t] / defl[2000]
        rr.append({"unita": u, "anno_imposta": t, "inflazione_da_2000": 1 / f,
                   "quota_sopra_26k_euro2000": quota_sopra(n, 26000 / f), "quota_sopra_55k_euro2000": quota_sopra(n, 55000 / f),
                   "quota_sopra_10k_euro2000": quota_sopra(n, 10000 / f), "quota_sotto_15k_euro2000": 1 - quota_sopra(n, 15000 / f),
                   "soglia_55k_euro2000_in_nominale": 55000 / f})
pd.DataFrame(rr).to_csv(os.path.join(P, "soglie_reali.csv"), index=False, float_format="%.6g")

# ---------- tipi di reddito ----------
TIPI = {"dipendente": ["dipendente"], "pensione": ["pensione"], "dip_e_pens_2000_01": ["dip_e_pens"],
        "autonomo": ["autonomo", "autonomo_eia", "autonomo_eib", "autonomo_eii"],
        "impresa": ["imp_ordinaria", "imp_semplificata"], "partecipazione": ["partecipazione"], "fabbricati": ["fabbricati"]}
tr = []
for u, mask in UNITA.items():
    for t, g in d[mask].groupby("anno"):
        N_ctr = g["contribuenti"].sum(); Y = sum(g[c + "_eur"].sum() for c in CL); f = defl[t]
        r = {"unita": u, "anno_imposta": t, "contribuenti": N_ctr, "reddito_complessivo_eur": Y}
        for k, cols in TIPI.items():
            e = sum(g[c + "_eur"].sum() for c in cols if c + "_eur" in g and g[c + "_eur"].notna().any())
            nn = sum(g[c + "_n"].sum() for c in cols if c + "_n" in g and g[c + "_n"].notna().any())
            if e == 0 and nn == 0:
                e = nn = float("nan")
            r[k + "_eur"] = e; r[k + "_n"] = nn
            r[k + "_per_contribuente_euro2025"] = e / N_ctr * f if e == e else float("nan")
            r[k + "_per_percettore_euro2025"] = e / nn * f if (nn == nn and nn > 0) else float("nan")
            r[k + "_quota_contribuenti"] = nn / N_ctr if nn == nn else float("nan")
            r[k + "_quota_del_reddito_complessivo"] = e / Y if e == e else float("nan")
        tr.append(r)
T = pd.DataFrame(tr).sort_values(["unita", "anno_imposta"])
T.to_csv(os.path.join(P, "tipi_reddito.csv"), index=False, float_format="%.6g")

# ---------- CAP ----------
c = pd.read_csv(os.path.join(P, "mef_cap_2011_2024.csv"), dtype={"catastale": str, "cap": str})
# Dal 2023 il campo 'Reddito complessivo' e' completo, mentre nei CAP molte celle di classe sono oscurate (es. >120k):
# se c'e' il campo si usa quello, altrimenti la somma delle classi (2011-2022: celle oscurate solo in pochi CAP, vedi NOTE.md).
c["reddito_somma_classi_eur"] = c[[x + "_eur" for x in CL]].sum(axis=1)
c["reddito_eur"] = c["reddito_complessivo_eur"].fillna(c["reddito_somma_classi_eur"]) if "reddito_complessivo_eur" in c else c["reddito_somma_classi_eur"]
c["n_classi"] = c[[x + "_n" for x in CL]].sum(axis=1)
c["classi_complete"] = c[[x + "_n" for x in CL[1:]] + [x + "_eur" for x in CL[1:]]].notna().all(axis=1)
c["media_nominale"] = c.reddito_eur / c.contribuenti; c["media_euro2025"] = c.media_nominale * c.anno.map(defl)
c["quota_sopra_120k"] = (c.cl7_oltre120k_n / c.n_classi).where(c.classi_complete)
c["quota_sotto_15k"] = ((c.cl0_le0_n.fillna(0) + c.cl1_0_10k_n + c.cl2_10_15k_n) / c.n_classi).where(c.classi_complete)
c["quota_reddito_sopra_120k"] = (c.cl7_oltre120k_eur / c.reddito_eur).where(c.classi_complete)
c.to_csv(os.path.join(P, "cap_redditi_tutte_le_citta.csv"), index=False, float_format="%.6g")


def wq(x, w, q):
    o = np.argsort(x); x = np.asarray(x)[o]; w = np.asarray(w, float)[o]; cw = np.cumsum(w) / w.sum()
    return float(np.interp(q, cw - w / w.sum() / 2, x))


def gap(g, col="media_nominale"):
    g = g.sort_values(col); x = g[col].values; w = g.contribuenti.values.astype(float)
    mu = np.average(x, weights=w); sd = math.sqrt(np.average((x - mu) ** 2, weights=w))
    p = np.concatenate([[0], np.cumsum(w) / w.sum()]); L = np.concatenate([[0], np.cumsum(x * w) / (x * w).sum()])
    gi = 1 - np.sum((p[1:] - p[:-1]) * (L[1:] + L[:-1]))
    return {"n_cap": len(g), "min_cap": g.cap.iloc[0], "min_media": x[0], "max_cap": g.cap.iloc[-1], "max_media": x[-1],
            "rapporto_max_min": x[-1] / x[0], "p90_su_p10": wq(x, w, .9) / wq(x, w, .1), "cv_pesato": sd / mu,
            "gini_tra_cap": float(gi), "media_pesata": mu}


gr = []
for (com, t), g in c.groupby(["comune", "anno"]):
    r = {"comune": com, "anno_imposta": t}; r.update(gap(g)); gr.append(r)
G = pd.DataFrame(gr)
gm = []   # Milano con 20121 e 20122 uniti (i contribuenti si spostano tra i due CAP)
for t, g in c[c.comune.str.upper() == "MILANO"].groupby("anno"):
    mk = g.cap.isin(["20121", "20122"]); a = g[mk]
    agg = {"cap": "20121+20122", "contribuenti": a.contribuenti.sum(), "reddito_eur": a.reddito_eur.sum()}
    agg["media_nominale"] = agg["reddito_eur"] / agg["contribuenti"]
    h2 = pd.concat([g[~mk][["cap", "contribuenti", "reddito_eur", "media_nominale"]], pd.DataFrame([agg])])
    r = {"comune": "MILANO (20121+20122 uniti)", "anno_imposta": t}; r.update(gap(h2)); gm.append(r)
G = pd.concat([G, pd.DataFrame(gm)]); G["fattore_euro2025"] = G.anno_imposta.map(defl)
G.sort_values(["comune", "anno_imposta"]).to_csv(os.path.join(P, "cap_divario_per_citta.csv"), index=False, float_format="%.6g")

mil = c[c.comune.str.upper() == "MILANO"].copy()
piv = mil.pivot(index="cap", columns="anno", values="media_euro2025"); piv["var_2011_2024_pct"] = (piv[2024] / piv[2011] - 1) * 100
piv.round(1).to_csv(os.path.join(P, "cap_milano_media_euro2025.csv"))
mil.pivot(index="cap", columns="anno", values="media_nominale").round(0).to_csv(os.path.join(P, "cap_milano_media_nominale.csv"))
mil.pivot(index="cap", columns="anno", values="contribuenti").to_csv(os.path.join(P, "cap_milano_contribuenti.csv"))
mil.pivot(index="cap", columns="anno", values="quota_sopra_120k").round(4).to_csv(os.path.join(P, "cap_milano_quota_sopra_120k.csv"))
mil.pivot(index="cap", columns="anno", values="quota_sotto_15k").round(4).to_csv(os.path.join(P, "cap_milano_quota_sotto_15k.csv"))


# ---------- riepilogo ----------
def get(u, t, col):
    return float(S[(S.unita == u) & (S.anno_imposta == t)][col].iloc[0])


R = {"anni_imposta": "2000-2024", "ultimo_anno": 2024}
ANNI = (2000, 2005, 2010, 2015, 2019, 2024)
for u in ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Lombardia", "Italia"]:
    R[u] = {"media_nominale": {t: round(get(u, t, "media_nominale")) for t in ANNI},
            "media_euro2025": {t: round(get(u, t, "media_euro2025")) for t in ANNI},
            "var_reale_2000_2024_pct": round((get(u, 2024, "media_euro2025") / get(u, 2000, "media_euro2025") - 1) * 100, 1),
            "gini_classi": {t: round(get(u, t, "gini_classi"), 3) for t in ANNI},
            "quota_reddito_sopra_120k_pct": {t: round(get(u, t, "quota_reddito_sopra_120k") * 100, 1) for t in ANNI},
            "quota_contr_sopra_120k_pct": {t: round(get(u, t, "quota_contr_sopra_120k") * 100, 2) for t in ANNI},
            "quota_contr_sotto_15k_pct": {t: round(get(u, t, "quota_contr_sotto_15k") * 100, 1) for t in ANNI}}
json.dump(R, open(os.path.join(P, "riepilogo.json"), "w"), indent=1, ensure_ascii=False)
print("ok")
