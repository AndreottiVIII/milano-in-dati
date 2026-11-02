"""Ultimi controlli di quartiere: laureati vecchi e nuovi, gara affluenza-disoccupazione su più elezioni, rumore dell'eccesso 2020, scheda finale dei candidati.
Uscite: out/candidati_finali_nil.csv; stampare in out/log_07b.txt"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, path, rd
from robusta import A, CTRL, FORTI, parz, scheda

pd.set_option("display.width", 230, "display.max_rows", 200, "display.max_colwidth", 60)
ix = json.load(open(path("docs", "elezioni", "data", "index.json"), encoding="utf8"))
EL = {e["id"]: e for e in ix["elezioni"]}


def voto(eid, fam_):
    d = json.load(open(path("docs", "elezioni", "data", "nil", eid + ".json"), encoding="utf8"))
    e = EL[eid]
    fam = e.get("fam") or []
    rows = {}
    for k, v in d["p"].items():
        if v.get("e", 0) < 1000:
            continue
        rr = {"aff": v["vt"] / v["e"] * 100, "quota": np.nan}
        if "v" in v and e.get("par"):
            tot = sum(v["v"]) or 1
            rr["quota"] = sum(n for (nm, fi), n in zip(e["par"], v["v"]) if fam[fi] in fam_) / tot * 100
        rows[int(k)] = rr
    return pd.DataFrame(rows).T.reindex(A.index)


print("=== laureati vecchi e nuovi")
ce = rd("censimenti/pulito/indicatori_NIL.csv")
L = ce.pivot(index="nil", columns="anno", values="quota_laureati_su_residenti").reindex(A.index)
print(L.median().round(1).to_dict())
A["lau91_r"] = L[1991]
A["lau23_r"] = L[2023]
A["lau11_r"] = L[2011]
A["nuovi_laureati"] = L[2023] - L[1991]
A["nuovi_11_23"] = L[2023] - L[2011]
A["nuovi_91_11"] = L[2011] - L[1991]
rb = rd("censimenti/pulito/variazioni_NIL_1991_2023.csv").set_index("nil").robusto.reindex(A.index).astype(str).str.lower().isin(["true", "1"]).values
print("NIL a confini robusti:", rb.sum())
SX, DX, CE = ["Sinistra", "Centrosinistra"], ["Centrodestra", "Lega", "Destra"], ["Centro"]
out = []
for e in ["comunali_consiglio_2016-06-05", "camera_2018-03-04", "europee_2019-05-26", "comunali_consiglio_2021-10-03", "camera_2022-09-25", "regionali_consiglio_2023-02-12", "europee_2024-06-08"]:
    for nome, fam in [("sx", SX), ("centro", CE), ("dx", DX)]:
        y = voto(e, fam).quota.values
        if np.nanstd(y) == 0:
            continue
        ok = ~np.isnan(y)
        # a parità di laureati di oggi (e di controlli): pesa di più l'arrivo recente o la presenza antica?
        c2 = CTRL + ["lau23_r"]
        r_old = parz(A.lau91_r.values, y, c2)
        r_rb = parz(A.lau91_r.values, y, c2, rb)
        out.append(dict(elezione=e, gruppo=nome, rho_lau91=stats.spearmanr(A.lau91_r[ok], y[ok])[0], rho_lau23=stats.spearmanr(A.lau23_r[ok], y[ok])[0], rho_nuovi=stats.spearmanr(A.nuovi_laureati[ok], y[ok])[0], parz_lau91_dati_lau23=r_old[0], p=r_old[1], parz_solo_robusti=r_rb[0], n_rob=r_rb[2]))
O = pd.DataFrame(out)
O.to_csv(os.path.join(OUT, "app_laureati_vecchi_nuovi.csv"), index=False, encoding="utf-8-sig")
print(O.round(2).to_string())
for nome, fam, e in [("sx_cam22", SX, "camera_2022-09-25"), ("centro_cam22", CE, "camera_2022-09-25"), ("sx_eur24", SX, "europee_2024-06-08")]:
    A["_y"] = voto(e, fam).quota
    s = scheda("nuovi_laureati", "_y")
    print(nome, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items() if k in ("rho_grezzo", "rho_parz", "p_msr", "moran_res", "rho_senza5", "rho_loo_min", "rho_loo_max", "rho_forti", "rho_mem", "rho_ge7000", "ic95_lo", "ic95_hi", "effetto_iqr", "x_q1", "x_q3", "y_terzo_basso", "y_terzo_alto")})
    print("   solo robusti:", round(parz(A.nuovi_laureati.values, A._y.values, CTRL, rb)[0], 3), "| con 1991-2011:", round(parz(A.nuovi_91_11.values, A._y.values, CTRL)[0], 3), "| con 2011-2023:", round(parz(A.nuovi_11_23.values, A._y.values, CTRL)[0], 3))
    print("   eta 20-34 come controllo:", round(parz(A.nuovi_laureati.values, A._y.values, CTRL + ["q20_34"])[0], 3), " famiglia_media:", round(parz(A.nuovi_laureati.values, A._y.values, CTRL + ["famiglia_media"])[0], 3), " ricambio:", round(parz(A.nuovi_laureati.values, A._y.values, CTRL + ["ricambio_15_19"])[0], 3))

print("\n=== gara affluenza contro disoccupazione: stessa grana (sezioni), più elezioni")


def beta(y, xs):
    ok = np.array(A[[y] + xs].notna().all(axis=1).values)
    Y = A.loc[ok, y].rank()
    Y = (Y - Y.mean()) / Y.std()
    X = A.loc[ok, xs].rank()
    X = ((X - X.mean()) / X.std()).values
    X1 = np.column_stack([np.ones(ok.sum()), X])
    b, *_ = np.linalg.lstsq(X1, Y.values, rcond=None)
    e = Y.values - X1 @ b
    se = np.sqrt(np.diag(e @ e / (ok.sum() - X1.shape[1]) * np.linalg.inv(X1.T @ X1)))
    return {x: f"{b[i+1]:+.2f} (t {b[i+1]/se[i+1]:+.1f})" for i, x in enumerate(xs)}, round(1 - e @ e / (Y.values @ Y.values), 2)


for e in ["camera_2018-03-04", "europee_2019-05-26", "comunali_consiglio_2021-10-03", "camera_2022-09-25", "europee_2024-06-08", "referendum_2016-12-04_ds1370", "referendum_2026-03-22_ds2975"]:
    A["_a"] = voto(e, []).aff
    print(e, beta("smr_12_19", ["_a", "disocc_2011", "laureati", "reddito", "eta_media"]))
# chi spiega l'SMR se la classifica dipende dalla lista? un indice di disagio senza affluenza
print("Affluenza da sola R2 rank:", round(stats.spearmanr(A.aff_cam_2022, A.smr_22_24)[0] ** 2, 2), "Reddito da solo:", round(stats.spearmanr(A.reddito, A.smr_22_24)[0] ** 2, 2), "Disocc:", round(stats.spearmanr(A.disocc_2011, A.smr_22_24)[0] ** 2, 2), "Laureati:", round(stats.spearmanr(A.laureati, A.smr_22_24)[0] ** 2, 2))
# in valori: quante morti in più
sm = rd("speranza-vita/pulito/nil_smr_e0.csv")
t = sm[(sm.finestra == "2022-2024") & (sm.sesso == "T")].set_index("id_nil").reindex(A.index)
t["aff"] = A.aff_cam_2022
t["ter"] = pd.qcut(t.aff, 3, labels=["bassa", "media", "alta"])
g = t.groupby("ter").agg(n=("smr", "size"), osservati=("osservati", "sum"), attesi=("attesi", "sum"), aff=("aff", "mean"))
g["smr_gruppo"] = g.osservati / g.attesi
print(g.round(3).to_string())
print("NIL estremi: ", A.sort_values("aff_cam_2022")[["nil", "aff_cam_2022", "smr_22_24", "reddito"]].round(2).iloc[[0, 1, 2, 3, -4, -3, -2, -1]].to_string())
# anomali: chi sta lontano dalla retta affluenza-SMR
x = A.aff_cam_2022.rank()
y = A.smr_22_24.rank()
b = np.polyfit(x, y, 1)
res = y - np.polyval(b, x)
print("Fuori retta SMR più alto del previsto:", A.nil[res.sort_values().index[-5:]].tolist(), "| più basso:", A.nil[res.sort_values().index[:5]].tolist())

print("\n=== rumore nell'eccesso 2020")
s = sm[sm.sesso == "T"]
a20 = s[s.finestra == "2020"].set_index("id_nil").reindex(A.index)
a16 = s[s.finestra == "2016-2019"].set_index("id_nil").reindex(A.index)
var_oss = np.log(a20.smr / a16.smr).var()
rumore = (1 / a20.osservati + 1 / a16.osservati).mean()
print("varianza osservata log(SMR2020/SMR16-19):", round(var_oss, 4), "attesa solo per caso (Poisson):", round(rumore, 4), "quota segnale:", round(max(var_oss - rumore, 0) / var_oss, 3))
print("rho SMR 2020 con SMR 2016-19:", round(stats.spearmanr(a20.smr, a16.smr)[0], 3), "| SMR 2021 con SMR 16-19:", round(stats.spearmanr(s[s.finestra == "2021"].set_index("id_nil").reindex(A.index).smr, a16.smr)[0], 3))
# potenza: quale rho vero si potrebbe vedere con questo rumore? attenuazione = radice della quota segnale
print("attenuazione massima di qualsiasi correlazione con l'eccesso:", round(np.sqrt(max(var_oss - rumore, 0) / var_oss), 3))
var2 = np.log(s[s.finestra == "2022-2024"].set_index("id_nil").reindex(A.index).smr)
print("affidabilità SMR 22-24: quota segnale:", round(1 - (1 / t.osservati).mean() / var2.var(), 3))

print("\n=== schede finali")
FIN = [("aff_cam_2022", "smr_22_24"), ("aff_cam_2022", "smr_12_19"), ("laureati", "dx_cam22"), ("reddito", "dx_cam22"), ("laureati", "lega_eur19"), ("famiglia_media", "sx_eur24"), ("famiglia_media", "dx_cam22"), ("gap_occ_mf", "aff_com_2021"), ("gap_occ_mf", "aff_eur_2024"), ("airbnb_x100", "gioco_x10k"), ("locali_x_kmq", "antenne_x_kmq"), ("densita_kmq", "antenne_x_kmq"), ("wiki_quota_estero", "antenne_x1000"), ("locali_x1000", "confiscati_x10k"), ("var_reddito", "confiscati_x10k"), ("nidi_x1000", "gap_occ_mf"), ("aler_x_abitazione", "smr_22_24"), ("edifici_pre1946", "opere_x_kmq"), ("disocc_2011", "aff_cam_2022"), ("var_antenne", "var_sx_18_22"), ("incid_q_moto", "var_bambini"), ("q0_14", "c15_medici"), ("airbnb_crescita", "sx_com21"), ("artigianato_x1000", "cuc_pizza"), ("cuc_veg_insalate_poke", "bikemi_x_kmq"), ("cuc_italiana", "wiki_quota_estero")]
rs = []
for a, b in FIN:
    # controllo: se la variabile è un controllo, si toglie dai controlli
    rs.append(scheda(a, b))
F = pd.DataFrame(rs)
F.to_csv(os.path.join(OUT, "candidati_finali_nil.csv"), index=False, encoding="utf-8-sig")
print(F[["a", "b", "n", "rho_grezzo", "rho_parz", "ic95_lo", "ic95_hi", "p_msr", "moran_res", "rho_senza5", "rho_loo_min", "rho_loo_max", "rho_entro_municipio", "rho_forti", "rho_mem", "rho_ge7000"]].round(2).to_string())
print(F[["a", "b", "x_q1", "x_q3", "effetto_iqr", "y_mediana", "y_terzo_basso", "y_terzo_alto"]].round(2).to_string())
