"""Italia, Lombardia (e 'senza Milano'): distribuzione per classi di reddito complessivo, serie definitiva 2000-2024.
PROBLEMA: nei file comunali il MEF oscura le celle con pochi contribuenti (comuni piccoli). Nel 2023-2024 le celle oscurate
sono molte di piu' (circa il 31% dei contribuenti sta in comuni senza la classe >120k): sommando i comuni si perde ~2,4% del
reddito nazionale e la quota dei redditi alti risulta sottostimata. Fino al 2022 l'errore e' trascurabile (controllo 2016-2022).
SOLUZIONE: per 2016-2024 si usano i file MEF per regione 'REG_calcolo_irpef_<anno+1>.csv' (classi fini, complete) riaggregati
nelle 8 classi grandi (soglie 10, 15, 26, 55, 75, 120 mila: coincidono). Nel file finale: 2000-2022 dalla somma dei comuni
(validata su 2016-2022), 2023-2024 dai file regionali.  'senza Milano' = totale - Milano (Milano ha tutte le celle).
Uso: python -I -X utf8 nazionale.py <percorso assoluto redditi> <percorso assoluto milano-in-dati>
Scrive pulito/benchmark_reg_2016_2024.csv, pulito/benchmark_controllo_somma_comuni.csv, pulito/italia_lombardia_serie_definitiva.csv"""
import sys, os, csv, re
import numpy as np, pandas as pd

base, root = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito"); R = os.path.join(base, "raw", "mef_nazionale")
foi = pd.read_csv(os.path.join(root, "prezzi-case", "pulito", "foi_annuale.csv")).set_index("anno")["indice_raccordato_2025_100"]
defl = (100.0 / foi).to_dict()
CL = ["cl0_le0", "cl1_0_10k", "cl2_10_15k", "cl3_15_26k", "cl4_26_55k", "cl5_55_75k", "cl6_75_120k", "cl7_oltre120k"]
BOUNDS = [0, 10000, 15000, 26000, 55000, 75000, 120000]


def it(s):
    s = s.strip()
    return np.nan if s == "" else float(s.replace(".", "").replace(",", "."))


def gini(n, y):
    n = np.asarray(n, float); y = np.asarray(y, float); N, Y = n.sum(), y.sum()
    p = np.concatenate([[0], np.cumsum(n) / N]); L = np.concatenate([[0], np.cumsum(y) / Y])
    return float(1 - np.sum((p[1:] - p[:-1]) * (L[1:] + L[:-1])))


def riga(unita, ai, metodo, nc, n8, y8, extra=None):
    Y = y8.sum(); o = {"unita": unita, "anno_imposta": ai, "fonte_dato": metodo, "contribuenti": nc, "contribuenti_con_classe": n8.sum(),
                       "reddito_complessivo_eur": Y, "media_nominale": Y / nc, "media_euro2025": Y / nc * defl[ai],
                       "gini_classi_grandi": gini(n8[1:], y8[1:]),
                       "quota_contr_sotto_15k": n8[:3].sum() / n8.sum(), "quota_contr_sotto_10k": n8[:2].sum() / n8.sum(),
                       "quota_contr_sopra_120k": n8[7] / n8.sum(), "quota_reddito_sopra_120k": y8[7] / Y}
    if extra: o.update(extra)
    return o


# ---- 1) file regionali (esatti) ----
reg = {}
for ai in range(2016, 2025):
    rows = list(csv.reader(open(os.path.join(R, f"REG_calcolo_irpef_{ai + 1}.csv"), encoding="utf8", errors="replace"), delimiter=";"))
    hdr = rows[0]
    assert hdr[2].startswith("Numero contribuenti") and hdr[3].startswith("Reddito complessivo - Frequenza") and hdr[4].startswith("Reddito complessivo - Ammontare"), hdr[:5]
    for unita, sel in (("Italia", lambda r: True), ("Lombardia", lambda r: r[1].lower().startswith("lombard"))):
        nc = 0.0; zero_n = 0.0; n8 = np.zeros(8); y8 = np.zeros(8); fine = {}
        for r in rows[1:]:
            if not sel(r): continue
            lab = r[0].strip(); ctr = np.nan_to_num(it(r[2])); nfreq = np.nan_to_num(it(r[3])); amt = np.nan_to_num(it(r[4]))
            nc += ctr
            if lab == "zero":
                zero_n += ctr; continue
            m = re.match(r"da ([\-\d\.]+) a ([\-\d\.]+)", lab)
            if lab.startswith("minore di"): lo = -1e9
            elif lab.startswith("oltre"): lo = 300000.0
            elif m: lo = float(m.group(1).replace(".", ""))
            else: raise ValueError(lab)
            k = 0 if lo < 0 else max(i for i, b in enumerate(BOUNDS) if lo >= b) + 1
            n8[k] += nfreq; y8[k] += amt; a_ = fine.setdefault(lo, [0.0, 0.0]); a_[0] += nfreq; a_[1] += amt
        ks = [k for k in sorted(fine) if k >= 0]
        extra = {"contribuenti_reddito_zero": zero_n,
                 "gini_classi_fini": gini([fine[k][0] for k in ks], [fine[k][1] for k in ks]),
                 "quota_contr_sopra_300k": fine[300000.0][0] / n8.sum(), "quota_reddito_sopra_300k": fine[300000.0][1] / y8.sum()}
        reg[(unita, ai)] = (nc, n8, y8, extra)

B = [riga(u, ai, "REG_esatto", nc, n8, y8, ex) for (u, ai), (nc, n8, y8, ex) in sorted(reg.items())]
pd.DataFrame(B).to_csv(os.path.join(P, "benchmark_reg_2016_2024.csv"), index=False, float_format="%.6g")

# ---- 2) controllo somma comuni vs file regionali ----
S = pd.read_csv(os.path.join(P, "serie_unita_anno.csv"))
rg = pd.DataFrame(B).set_index(["unita", "anno_imposta"]); sc = S.set_index(["unita", "anno_imposta"])
ctl = []
for (u, ai) in rg.index:
    a = rg.loc[(u, ai)]; b = sc.loc[(u, ai)]
    ctl.append({"unita": u, "anno_imposta": ai, "media_REG": a.media_nominale, "media_somma_comuni": b.media_nominale,
                "diff_media_pct": (b.media_nominale / a.media_nominale - 1) * 100,
                "gini_REG": a.gini_classi_grandi, "gini_somma_comuni": b.gini_classi,
                "quota_reddito_120k_REG": a.quota_reddito_sopra_120k, "quota_reddito_120k_somma_comuni": b.quota_reddito_sopra_120k,
                "quota_contr_sotto15k_REG": a.quota_contr_sotto_15k, "quota_contr_sotto15k_somma_comuni": b.quota_contr_sotto_15k})
ctl = pd.DataFrame(ctl); ctl.to_csv(os.path.join(P, "benchmark_controllo_somma_comuni.csv"), index=False, float_format="%.6g")
print(ctl.round(4).to_string())

# ---- 3) serie definitiva ----
d = pd.read_csv(os.path.join(P, "mef_comuni_2000_2024.csv"), dtype={"catastale": str})


def da_somma(u, ai):
    r = S[(S.unita == u) & (S.anno_imposta == ai)].iloc[0]
    return {"unita": u, "anno_imposta": ai, "fonte_dato": "somma_comuni_MEF", "contribuenti": r.contribuenti,
            "reddito_complessivo_eur": r.reddito_complessivo_eur, "media_nominale": r.media_nominale, "media_euro2025": r.media_euro2025,
            "gini_classi_grandi": r.gini_classi, "quota_contr_sotto_15k": r.quota_contr_sotto_15k, "quota_contr_sotto_10k": r.quota_contr_sotto_10k,
            "quota_contr_sopra_120k": r.quota_contr_sopra_120k, "quota_reddito_sopra_120k": r.quota_reddito_sopra_120k}


fin = []
for u in ["Italia", "Lombardia"]:
    for ai in range(2000, 2025):
        if ai <= 2022:
            fin.append(da_somma(u, ai)); fin.append(da_somma(u + " senza Milano", ai))
        else:
            nc, n8, y8, ex = reg[(u, ai)]
            fin.append(riga(u, ai, "REG_esatto", nc, n8, y8))
            m = d[(d.catastale == "F205") & (d.anno == ai)].iloc[0]
            mn = np.array([m[c + "_n"] for c in CL], float); my = np.array([m[c + "_eur"] for c in CL], float)
            fin.append(riga(u + " senza Milano", ai, "REG_esatto_meno_Milano", nc - m.contribuenti, n8 - mn, y8 - my))
F = pd.DataFrame(fin).sort_values(["unita", "anno_imposta"])
F.to_csv(os.path.join(P, "italia_lombardia_serie_definitiva.csv"), index=False, float_format="%.6g")
print(F[F.anno_imposta.isin([2000, 2010, 2022, 2023, 2024])][["unita", "anno_imposta", "fonte_dato", "media_nominale", "media_euro2025", "gini_classi_grandi", "quota_reddito_sopra_120k"]].round(3).to_string())
