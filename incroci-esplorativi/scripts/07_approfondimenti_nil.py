"""Approfondimenti sui candidati di quartiere: gare tra predittori, definizioni alternative, controlli specifici.
Stampa tutto in out/log_07.txt (lanciare con redirezione) e salva le tabelle in out/app_*.csv."""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import adjusted_rand_score

from comune import OUT, SEED, path, rd
from robusta import A, CTRL, FORTI, Wm, moran, msr, parz, qmat, scheda

pd.set_option("display.width", 230, "display.max_rows", 300, "display.max_colwidth", 70)
rng = np.random.default_rng(SEED)
ix = json.load(open(path("docs", "elezioni", "data", "index.json"), encoding="utf8"))
EL = {e["id"]: e for e in ix["elezioni"]}


def voto(eid):
    d = json.load(open(path("docs", "elezioni", "data", "nil", eid + ".json"), encoding="utf8"))
    e = EL[eid]
    fam = e.get("fam") or []
    rows = {}
    for k, v in d["p"].items():
        if v.get("e", 0) < 1000:
            continue
        r = {"aff": v["vt"] / v["e"] * 100}
        if "v" in v and e.get("par"):
            tot = sum(v["v"]) or 1
            acc = {}
            for (nome, fi), n in zip(e["par"], v["v"]):
                acc[fam[fi]] = acc.get(fam[fi], 0) + n
            for f_, n in acc.items():
                r[f_] = n / tot * 100
        rows[int(k)] = r
    return pd.DataFrame(rows).T.reindex(A.index)


ELS = ["referendum_2016-04-17_ds1369", "comunali_consiglio_2016-06-05", "referendum_2016-12-04_ds1370", "referendum_2017-10-22_ds1371", "camera_2018-03-04", "regionali_consiglio_2018-03-04", "europee_2019-05-26", "referendum_2020-09-20_ds1461", "comunali_consiglio_2021-10-03", "referendum_2022-06-12_ds1889", "camera_2022-09-25", "regionali_consiglio_2023-02-12", "europee_2024-06-08", "referendum_2025-06-08_ds2930", "referendum_2026-03-22_ds2975"]
VT = {e: voto(e) for e in ELS}

# --------------------------------------- 1. affluenza e mortalità
print("=== 1. AFFLUENZA E MORTALITA'")
sm = rd("speranza-vita/pulito/nil_smr_e0.csv")
def smr(fin, sex):
    return sm[(sm.finestra == fin) & (sm.sesso == sex)].set_index("id_nil").smr.reindex(A.index).values
rig = []
for e in ELS:
    a_ = VT[e].aff.values
    for fin in ["2012-2015", "2016-2019", "2022-2024"]:
        y = smr(fin, "T")
        ok = ~np.isnan(a_)
        r0 = stats.spearmanr(a_[ok], y[ok])[0]
        r, p, n, ex, ey, okk = parz(a_, y, CTRL)
        r2 = parz(a_, y, [c for c in CTRL + FORTI])[0]
        rig.append(dict(elezione=e, finestra=fin, n=n, rho=r0, rho_parz=r, p=p, rho_forti=r2))
T1 = pd.DataFrame(rig)
T1.to_csv(os.path.join(OUT, "app_affluenza_smr_tutte_elezioni.csv"), index=False, encoding="utf-8-sig")
print(T1.pivot(index="elezione", columns="finestra", values="rho_parz").round(2).to_string())
print(T1.pivot(index="elezione", columns="finestra", values="rho_forti").round(2).to_string())
print("mediana rho_parz per finestra", T1.groupby("finestra").rho_parz.median().round(2).to_dict(), "quante negative", (T1.rho_parz < 0).sum(), "su", len(T1))
for sex in "MF":
    y = smr("2022-2024", sex)
    x = A.aff_cam_2022.values
    print("sesso", sex, "rho parz camera 2022 vs SMR 2022-24", round(parz(x, y, CTRL)[0], 3), "vs SMR 2012-19", round(parz(x, smr("2012-2019", sex), CTRL)[0], 3))
# gara tra predittori (ranghi)
PRED = ["aff_cam_2022", "aff_eur_2024", "aff_com_2021", "disocc_2011", "tasso_occ", "laureati", "laureati_1991", "reddito", "quota_bassi", "prezzo", "aler_x_abitazione", "gap_occ_mf", "case_non_occ", "famiglia_media", "dist_duomo_km"]
for yy in ["smr_12_19", "smr_22_24"]:
    rr = {p_: stats.spearmanr(A[p_], A[yy], nan_policy="omit")[0] for p_ in PRED}
    print(yy, "rho semplice:", {k: round(v, 2) for k, v in sorted(rr.items(), key=lambda t: -abs(t[1]))})


def beta(y, xs, mask=None):
    """Regressione sui ranghi standardizzati: restituisce beta, t, R2."""
    ok = np.array(A[[y] + xs].notna().all(axis=1).values)
    if mask is not None:
        ok = ok & mask
    Y = A.loc[ok, y].rank()
    Y = (Y - Y.mean()) / Y.std()
    X = A.loc[ok, xs].rank()
    X = ((X - X.mean()) / X.std()).values
    X1 = np.column_stack([np.ones(ok.sum()), X])
    b, *_ = np.linalg.lstsq(X1, Y.values, rcond=None)
    e = Y.values - X1 @ b
    s2 = e @ e / (ok.sum() - X1.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X1.T @ X1)))
    return {x: (round(b[i + 1], 2), round(b[i + 1] / se[i + 1], 1)) for i, x in enumerate(xs)}, round(1 - e @ e / (Y.values @ Y.values), 3), int(ok.sum())


print("gara SMR 22-24:", beta("smr_22_24", ["aff_cam_2022", "reddito", "laureati", "disocc_2011", "aler_x_abitazione", "eta_media", "q80"]))
print("gara SMR 12-19:", beta("smr_12_19", ["aff_cam_2022", "reddito", "laureati", "disocc_2011", "aler_x_abitazione", "eta_media", "q80"]))
print("senza affluenza SMR 22-24:", beta("smr_22_24", ["reddito", "laureati", "disocc_2011", "aler_x_abitazione", "eta_media", "q80"]))
print("senza disocc SMR 22-24:", beta("smr_22_24", ["aff_cam_2022", "reddito", "laureati", "aler_x_abitazione", "eta_media", "q80"]))
# togli i NIL con molte residenze per anziani segnalati dal filone
ba = rd("speranza-vita/pulito/nil_bandiere_residenze.csv").set_index("id_nil").reindex(A.index)
molti = ba.molti_85piu.astype(str).str.lower().isin(["true", "1"]).values
print("NIL segnati molti 85+:", list(A.nil[molti]))
for nome, m in [("senza molti 85+", ~molti), ("senza Morivione", (A.nil != "Morivione").values), ("senza Muggiano, San Siro", ~A.nil.isin(["Muggiano", "San Siro"]).values)]:
    print(nome, "rho parz:", round(parz(A.aff_cam_2022.values, A.smr_22_24.values, CTRL, m)[0], 3), "con 12-19:", round(parz(A.aff_cam_2022.values, A.smr_12_19.values, CTRL, m)[0], 3))
s1 = scheda("aff_cam_2022", "smr_22_24")
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in s1.items()})
# terzili di affluenza a parità di reddito: dentro i terzili di reddito
d = A[["reddito", "aff_cam_2022", "smr_22_24", "smr_12_19", "residenti_2024"]].dropna()
d["tr"] = pd.qcut(d.reddito, 3, labels=["reddito basso", "reddito medio", "reddito alto"])
d["ta"] = d.groupby("tr").aff_cam_2022.transform(lambda s: pd.qcut(s, 2, labels=["affl. bassa", "affl. alta"]))
print(d.groupby(["tr", "ta"]).agg(n=("smr_22_24", "size"), smr2224=("smr_22_24", "mean"), smr1219=("smr_12_19", "mean"), aff=("aff_cam_2022", "mean"), red=("reddito", "mean")).round(3).to_string())

# --------------------------------------- 2. voto: reddito contro laureati
print("\n=== 2. VOTO: LAUREATI E REDDITO")
GR = {"sinistra_csx": ["Sinistra", "Centrosinistra"], "destra_cdx": ["Centrodestra", "Lega", "Destra"], "m5s": ["M5S"], "centro": ["Centro"]}
rig = []
for e in ["comunali_consiglio_2016-06-05", "camera_2018-03-04", "regionali_consiglio_2018-03-04", "europee_2019-05-26", "comunali_consiglio_2021-10-03", "camera_2022-09-25", "regionali_consiglio_2023-02-12", "europee_2024-06-08"]:
    v = VT[e]
    for g, fam in GR.items():
        cols = [f for f in fam if f in v.columns]
        if not cols:
            continue
        y = v[cols].sum(axis=1)
        A["_y"] = y
        ok = A[["_y", "laureati", "reddito"]].notna().all(axis=1).values
        b, r2, n = beta("_y", ["laureati", "reddito", "eta_media", "dist_duomo_km"])
        # effetto in punti: OLS sui valori
        X = np.column_stack([np.ones(ok.sum()), A.laureati.values[ok] / 10, A.reddito.values[ok] / 10000, A.eta_media.values[ok], A.dist_duomo_km.values[ok]])
        bb, *_ = np.linalg.lstsq(X, y.values[ok], rcond=None)
        rig.append(dict(elezione=e, gruppo=g, n=n, rho_laureati=stats.spearmanr(A.laureati.values[ok], y.values[ok])[0], rho_reddito=stats.spearmanr(A.reddito.values[ok], y.values[ok])[0], beta_laureati=b["laureati"][0], t_laureati=b["laureati"][1], beta_reddito=b["reddito"][0], t_reddito=b["reddito"][1], r2=r2, punti_per_10pp_laureati=bb[1], punti_per_10mila_euro=bb[2]))
T2 = pd.DataFrame(rig)
T2.to_csv(os.path.join(OUT, "app_voto_laureati_reddito.csv"), index=False, encoding="utf-8-sig")
print(T2.round(2).to_string())
print("laureati 1991 contro 2023 come predittori (rho semplice):")
for y_ in ["m5s_cam18", "lega_eur19", "dx_cam22", "destra_cam22", "sx_com21", "aff_cam_2022"]:
    print(y_, "1991:", round(stats.spearmanr(A.laureati_1991, A[y_], nan_policy="omit")[0], 3), "2023:", round(stats.spearmanr(A.laureati, A[y_], nan_policy="omit")[0], 3), "reddito:", round(stats.spearmanr(A.reddito, A[y_], nan_policy="omit")[0], 3), "prezzo:", round(stats.spearmanr(A.prezzo, A[y_], nan_policy="omit")[0], 3), "disocc11:", round(stats.spearmanr(A.disocc_2011, A[y_], nan_policy="omit")[0], 3))
print("rho laureati 1991 e 2023:", round(stats.spearmanr(A.laureati_1991, A.laureati)[0], 3))
for y_ in ["dx_cam22", "lega_eur19", "m5s_cam18", "sx_com21"]:
    print(y_, scheda("laureati", y_, ctrl=["dist_duomo_km", "reddito", "eta_media", "densita_kmq"])["rho_parz"].round(3), "senza 5:", scheda("laureati", y_)["rho_senza5"].round(3), "forti:", scheda("laureati", y_)["rho_forti"].round(3))
# senza centro: i NIL del tipo 3 tolti
cen = (A.dist_duomo_km > 2.5).values
print("gara senza il centro (oltre 2,5 km):")
A["_dx"] = A.dx_cam22
print(beta("_dx", ["laureati", "reddito", "eta_media", "dist_duomo_km"], cen))
print(beta("sx_com21", ["laureati", "reddito", "eta_media", "dist_duomo_km"], cen))
print("escludo i 4 NIL con CAP instabile:", beta("_dx", ["laureati", "reddito", "eta_media", "dist_duomo_km"], ~A.nil.isin(["Duomo", "Brera", "Guastalla", "Porta Vigentina - Porta Lodovica"]).values))
# reddito misurato meglio? con prezzo come ricchezza
print("con prezzo come misura di ricchezza:", beta("_dx", ["laureati", "prezzo", "eta_media", "dist_duomo_km"]))

# Prova equa: la stessa grana per tutti. Porto laureati e affluenza sui CAP e di nuovo sui NIL: così hanno lo stesso "sfocato" del reddito.
cl = rd("quartieri-che-cambiano/out/collegamento_cap_nil.csv")
cl = cl[cl.ID_NIL.isin(A.index)]


def sfoca(col):
    d_ = cl.merge(A[[col, "residenti_2024"]], left_on="ID_NIL", right_index=True).dropna(subset=[col])
    d_["peso"] = d_.quota_nil * d_.residenti_2024
    cap_v = d_.groupby("CAP").apply(lambda g: np.average(g[col], weights=g.peso))
    d_["vcap"] = d_.CAP.map(cap_v)
    return d_.groupby("ID_NIL").apply(lambda g: np.average(g.vcap, weights=g.quota_nil)).reindex(A.index)


A["laureati_sfocati"] = sfoca("laureati")
A["aff22_sfocata"] = sfoca("aff_cam_2022")
A["reddito_sfocato2"] = sfoca("reddito")
print("controllo sfocatura: rho laureati e laureati sfocati", round(stats.spearmanr(A.laureati, A.laureati_sfocati)[0], 3), "| valori distinti sfocati", A.laureati_sfocati.nunique())
for y_ in ["_dx", "sx_com21", "lega_eur19", "m5s_cam18"]:
    print(y_, "laureati veri:", beta(y_, ["laureati", "reddito", "eta_media", "dist_duomo_km"])[0], "| laureati sfocati come il reddito:", beta(y_, ["laureati_sfocati", "reddito", "eta_media", "dist_duomo_km"])[0])
print("mortalità con affluenza sfocata:", beta("smr_22_24", ["aff22_sfocata", "reddito", "laureati", "eta_media"])[0], "| contro affluenza vera:", beta("smr_22_24", ["aff_cam_2022", "reddito", "laureati", "eta_media"])[0])
print("parziale affluenza sfocata e SMR 22-24:", parz(A.aff22_sfocata.values, A.smr_22_24.values, CTRL)[:3], "| SMR 12-19:", parz(A.aff22_sfocata.values, A.smr_12_19.values, CTRL)[:3])

# --------------------------------------- 3. famiglie piccole e voto
print("\n=== 3. FAMIGLIE PICCOLE E VOTO")
rig = []
for e in ["comunali_consiglio_2016-06-05", "camera_2018-03-04", "europee_2019-05-26", "comunali_consiglio_2021-10-03", "camera_2022-09-25", "regionali_consiglio_2023-02-12", "europee_2024-06-08"]:
    v = VT[e]
    y = v[[f for f in ["Sinistra", "Centrosinistra"] if f in v.columns]].sum(axis=1).values
    y2 = v[[f for f in ["Centrodestra", "Lega", "Destra"] if f in v.columns]].sum(axis=1).values
    rig.append(dict(elezione=e, sx_parz=parz(A.famiglia_media.values, y, CTRL)[0], sx_forti=parz(A.famiglia_media.values, y, CTRL + FORTI)[0], dx_parz=parz(A.famiglia_media.values, y2, CTRL)[0], dx_forti=parz(A.famiglia_media.values, y2, CTRL + FORTI)[0], sx_sole_forti=parz(A.famiglie_sole.values, y, CTRL + FORTI)[0]))
print(pd.DataFrame(rig).round(2).to_string())
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in scheda("famiglia_media", "sx_eur24").items()})

# --------------------------------------- 4. affluenza e lavoro
print("\n=== 4. AFFLUENZA, LAVORO")
for y_ in ["aff_cam_2022", "aff_com_2021", "aff_ref_2025", "aff_eur_2024"]:
    print(y_, beta(y_, ["tasso_occ", "gap_occ_mf", "disocc_2011", "laureati", "reddito", "eta_media", "q_stranieri"]))
    rr = {p_: stats.spearmanr(A[p_], A[y_], nan_policy="omit")[0] for p_ in ["disocc_2011", "tasso_occ", "gap_occ_mf", "laureati", "reddito", "prezzo", "q_stranieri", "eta_media", "aler_x_abitazione"]}
    print("   rho:", {k: round(v, 2) for k, v in sorted(rr.items(), key=lambda t: -abs(t[1]))})
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in scheda("disocc_2011", "aff_cam_2022").items()})

# --------------------------------------- 5. Airbnb e aree gioco
print("\n=== 5. AIRBNB E AREE GIOCO")
ve = rd("docs/verde/data/nil_verde.csv").set_index("id_nil").reindex(A.index)
A["gioco_n"] = ve.gioco_n
A["gioco_x_kmq"] = ve.gioco_n / A.area_km2
A["gioco_x1000bimbi"] = ve.gioco_n / (A.residenti_2024 * A.q0_14 / 100) * 1000
A["log_annunci"] = np.log(A.airbnb_x100.clip(lower=0.01))
print(scheda("airbnb_x100", "gioco_x10k"))
for y_ in ["gioco_x_kmq", "gioco_x1000bimbi", "c15_giochi"]:
    print(y_, round(parz(A.airbnb_x100.values, A[y_].values, CTRL)[0], 3), "p", round(parz(A.airbnb_x100.values, A[y_].values, CTRL)[1], 4), "forti", round(parz(A.airbnb_x100.values, A[y_].values, CTRL + FORTI)[0], 3))
for extra in ["verde_a_pct", "edifici_pre1946", "edifici_46_70", "aler_x_abitazione", "suolo_pct", "alberi_x_kmq", "c15_parchi", "q0_14"]:
    print("con controllo", extra, round(parz(A.airbnb_x100.values, A.gioco_x10k.values, CTRL + [extra])[0], 3), "p", round(parz(A.airbnb_x100.values, A.gioco_x10k.values, CTRL + [extra])[1], 4))
print("rho gioco_x10k e gli altri: ", {k: round(stats.spearmanr(A[k], A.gioco_x10k, nan_policy="omit")[0], 2) for k in ["airbnb_x100", "locali_x1000", "edifici_pre1946", "edifici_46_70", "aler_x_abitazione", "q65", "q0_14", "reddito", "dist_duomo_km", "verde_a_pct", "sport_comunali_x10k"]})
print("rho parz gioco_x10k con locali, stesso denominatore:", round(parz(A.locali_x1000.values, A.gioco_x10k.values, CTRL)[0], 3), "airbnb|locali:", round(parz(A.airbnb_x100.values, A.gioco_x10k.values, CTRL + ["locali_x1000"])[0], 3))

# --------------------------------------- 6. antenne
print("\n=== 6. ANTENNE: DOVE?")
print("rho antenne per km2:", {k: round(stats.spearmanr(A[k], A.antenne_x_kmq, nan_policy="omit")[0], 2) for k in ["densita_kmq", "locali_x_kmq", "wiki_views_x_kmq", "incidenti_x_kmq", "c15_metro", "dist_duomo_km", "bikemi_x_kmq", "airbnb_x100", "reddito"]})
print(beta("antenne_x_kmq", ["densita_kmq", "locali_x_kmq", "wiki_views_x_kmq", "c15_metro", "dist_duomo_km"]))
for y_ in ["wiki_quota_estero", "wiki_views_x_kmq", "airbnb_x100", "locali_x_kmq", "c15_metro", "incidenti_x_kmq"]:
    r = parz(A[y_].values, A.antenne_x_kmq.values, ["dist_duomo_km", "densita_kmq", "reddito", "eta_media"])
    print("antenne_x_kmq vs", y_, round(r[0], 3), "p", round(r[1], 4))
print(scheda("wiki_quota_estero", "antenne_x1000"))

# --------------------------------------- 7. beni confiscati, definizioni alternative
print("\n=== 7. BENI CONFISCATI")
pn = rd("beni-confiscati/pulito/per_nil.csv").set_index("id_nil").reindex(A.index).fillna(0)
uc = rd("docs/beni-confiscati/data/unita_comune.csv")
print(uc.columns.tolist()[:8], uc.quartiere.head(2).tolist())
nome2id = {v.lower(): k for k, v in A.nil.items()}
uc["id"] = uc.quartiere.astype(str).str.lower().map(nome2id)
A["conf_indirizzi"] = uc.groupby("id").indirizzo.nunique().reindex(A.index).fillna(0)
A["conf_ds147"] = pn.ds147_unita
A["conf_anbsc"] = pn.anbsc_destinati
A["conf_ds147_x10k"] = A.conf_ds147 / A.residenti_2024 * 1e4
A["conf_anbsc_x10k"] = A.conf_anbsc / A.residenti_2024 * 1e4
A["conf_ind_x10k"] = A.conf_indirizzi / A.residenti_2024 * 1e4
A["conf_ind_x_kmq"] = A.conf_indirizzi / A.area_km2
A["log_locali_n"] = np.log(A.locali_x1000 * A.residenti_2024 / 1000 + 1)
A["log_conf_ind"] = np.log(A.conf_indirizzi + 1)
for y_ in ["confiscati_x10k", "conf_ds147_x10k", "conf_anbsc_x10k", "conf_ind_x10k", "conf_ind_x_kmq"]:
    for x_ in ["locali_x1000", "locali_x_kmq", "airbnb_x100", "var_reddito", "ricambio_15_19"]:
        r = parz(A[x_].values, A[y_].values, CTRL)
        print(y_, x_, "rho parz", round(r[0], 3), "p", round(r[1], 4), "n", r[2], "| forti", round(parz(A[x_].values, A[y_].values, CTRL + FORTI)[0], 3))
print("conteggi con log residenti tra i controlli (toglie il denominatore comune):", parz(A.log_locali_n.values, A.log_conf_ind.values, CTRL + ["log_residenti"])[:3])
print("rho semplice confiscati:", {k: round(stats.spearmanr(A[k], A.conf_ind_x_kmq, nan_policy="omit")[0], 2) for k in ["locali_x_kmq", "dist_duomo_km", "reddito", "densita_kmq", "edifici_pre1946", "airbnb_x100"]})
print(A.sort_values("conf_ind_x10k", ascending=False)[["nil", "conf_ds147", "conf_indirizzi", "conf_anbsc", "conf_ind_x10k", "locali_x1000"]].head(10).round(2).to_string())

# --------------------------------------- 8. reddito per CAP: dove sbaglia di più?
print("\n=== 8. DOVE IL REDDITO PER CAP NON RACCONTA IL QUARTIERE")
SES = ["laureati", "tasso_occ", "disocc_2011", "aff_cam_2022", "aler_x_abitazione", "smr_12_19", "prezzo", "famiglia_media"]
Zr = A[SES].rank()
Zr = (Zr - Zr.mean()) / Zr.std()
Zr["disocc_2011"] *= -1
Zr["aler_x_abitazione"] *= -1
Zr["smr_12_19"] *= -1
ind = Zr.drop(columns=["famiglia_media"]).mean(axis=1)
print("alfa di coerenza (media delle correlazioni tra indicatori):", round(np.nanmean(np.corrcoef(Zr.drop(columns=["famiglia_media"]).T.values)[np.triu_indices(7, 1)]), 3))
print("rho indice con reddito CAP:", round(stats.spearmanr(ind, A.reddito)[0], 3))
gap = pd.DataFrame({"nil": A.nil, "reddito": A.reddito, "rango_reddito": A.reddito.rank(ascending=False), "rango_indice": ind.rank(ascending=False), "residenti": A.residenti_2024})
gap["differenza"] = gap.rango_reddito - gap.rango_indice
gap = gap.sort_values("differenza")
gap.to_csv(os.path.join(OUT, "app_reddito_cap_vs_indice.csv"), encoding="utf-8-sig")
print("Reddito CAP molto più alto dell'indice sociale:"); print(gap.head(8).round(1).to_string())
print("Reddito CAP molto più basso dell'indice sociale:"); print(gap.tail(8).round(1).to_string())
# confronto con ogni variabile: quanto spiega di più il reddito CAP o l'indice?
ca = rd("quartieri-che-cambiano/out/collegamento_cap_nil.csv")
mx = ca.groupby("ID_NIL").quota_nil.max().reindex(A.index)
print("NIL ricchi nel CAP ma con quota alta di CAP dominante:", gap.head(5).nil.tolist(), mx.reindex(gap.head(5).index).round(2).tolist())

# --------------------------------------- 9. municipi contro tipi
print("\n=== 9. MUNICIPI CONTRO TIPI")
T = pd.read_csv(os.path.join(OUT, "nil_tipi.csv"), index_col=0)
D = pd.read_csv(os.path.join(OUT, "dizionario.csv")).fillna("")
V = [v for v in D.variabile if D.set_index("variabile").loc[v, "controllo"] == 0 and A[v].notna().sum() >= 55 and A[v].nunique() >= 8 and v not in ("q_stranieri", "var_q_stranieri", "n_eff_cittadinanze", "scuola_gap_cit")]


def eta2(lab, Y):
    out = []
    for v in Y.columns:
        y = Y[v].rank()
        ok = y.notna()
        gm = y[ok].groupby(np.asarray(lab)[ok.values]).transform("mean")
        out.append(((gm - y[ok].mean()) ** 2).sum() / ((y[ok] - y[ok].mean()) ** 2).sum())
    return np.array(out)


em = eta2(A.municipio.fillna(0).values, A[V])
et = eta2(T.tipo.values, A[V])
fasce = pd.qcut(A.dist_duomo_km, 4, labels=False).values
ed = eta2(fasce, A[V])
print("quota di varianza spiegata (mediana sugli indicatori): municipio", round(np.median(em), 3), "fasce di distanza (4)", round(np.median(ed), 3), "tipi (4)", round(np.median(et), 3), "su", len(V))
# atteso col caso: etichette mescolate con gli stessi gruppi
sim_m = [np.median(eta2(rng.permutation(A.municipio.fillna(0).values), A[V])) for _ in range(100)]
print("municipio col caso (9 gruppi mescolati):", round(np.mean(sim_m), 3), "max", round(np.max(sim_m), 3))
print(A.groupby(T.tipo).municipio.apply(lambda s: s.value_counts().sort_index().to_dict()).to_string() if False else pd.crosstab(T.tipo, A.municipio).to_string())
print("Vicini di casa con tipo diverso: quota di confini tra tipi diversi:", round(np.mean([T.tipo[a] != T.tipo[b] for a, b in pd.read_csv(os.path.join(OUT, 'nil_vicini.csv')).values if a in T.index and b in T.index]), 3))

# --------------------------------------- 10. Covid 2020: cosa spiega l'eccesso?
print("\n=== 10. COVID 2020")
R = pd.read_csv(os.path.join(OUT, "nil_coppie_tutte.csv"))
e = R[(R.a == "eccesso_2020") | (R.b == "eccesso_2020")].copy()
print("coppie con eccesso_2020:", len(e), "min q parz:", round(e.q_parz.min(), 3), " migliori:")
print(e.sort_values("p_parz").head(8)[["a", "b", "rho", "rho_parz", "p_parz", "q_parz", "meccanica"]].round(3).to_string())
print("eccesso vs q80 / aff / reddito rho semplice", {k: round(stats.spearmanr(A[k], A.eccesso_2020, nan_policy="omit")[0], 2) for k in ["q80", "q65", "aff_cam_2022", "reddito", "densita_kmq", "famiglia_media", "smr_12_19"]})
print(A.sort_values("eccesso_2020")[["nil", "eccesso_2020"]].round(1).iloc[[0, 1, 2, -3, -2, -1]].to_string())

# --------------------------------------- 11. nidi e divario, tasso occ. cucine e comunità (parole neutre)
print("\n=== 11. ALTRI")
print(scheda("nidi_x1000", "gap_occ_mf"))
ct = rd("divisa/out/cittadinanza_nil.csv")
ct = ct[ct.anno == 2025].set_index("id_nil").reindex(A.index)
for c_, k in [("c_Cina", "cuc_cinese"), ("c_Bangladesh", "cuc_indiana_sudasiatica"), ("c_Sri Lanka", "cuc_indiana_sudasiatica"), ("c_Egitto", "cuc_kebab_medio_oriente")]:
    x = ct[c_] / ct.residenti * 100
    ok = x.notna().values & A[k].notna().values
    print("cucina", k, "e quota residenti", c_, "rho", round(stats.spearmanr(x[ok], A[k].values[ok])[0], 2), "parz", round(parz(x.values, A[k].values, CTRL)[0], 2), "n", ok.sum())
