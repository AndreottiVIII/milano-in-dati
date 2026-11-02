"""Fase 1 - Nascite a Milano: pulizia e tabelle in pulito/.
Uso: python -I -X utf8 01_pulisci.py <nascite_dir> <milano_in_dati_dir>      (percorsi assoluti, si puo' rilanciare)

Legge (raw/comune/): ds141 (nati vivi RESIDENTI per quartiere 2003-2020), ds1943 (idem 2021-2024), ds1944 (residenti per eta' della madre
2021-2024), ds1945 (nati AVVENUTI a Milano per eta' della madre 2021-2024), ds1495 (nati vivi residenti dal 1880), ds289 (nascite avvenute a Milano).
Legge dal filone popolazione/: ds27 (zip) per donne 15-49 e residenti per NIL e per cittadinanza; nil_2021_anagrafica per i nomi dei NIL.
Legge raw/istat/: TFR e eta' media delle madri (FECONDITA1_5/6, province).
Scrive pulito/: nascite_nil_anno.csv, denominatori_nil_anno.csv, tassi_nil_anno.csv, citta_anno.csv, eta_madre_citta.csv, tfr_citta_2021_2024.csv,
istat_tfr_eta_madre.csv, controlli.json
"""
import sys, os, json, zipfile, re, unicodedata
import numpy as np, pandas as pd

N, M = sys.argv[1], sys.argv[2]
RAW = os.path.join(N, "raw", "comune")
OUT = os.path.join(N, "pulito")
os.makedirs(OUT, exist_ok=True)
CHK = {}

def norm(s):
    s = unicodedata.normalize("NFD", str(s).strip().lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")      # accenti
    s = s.replace("’", "").replace("'", "").replace("`", "")
    return re.sub(r"\s+", " ", s)

# ------------------------------------------------------------ NIL
ana = pd.read_csv(os.path.join(M, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
ana = ana.rename(columns={"nil": "id_nil", "nil_nome": "nome"})
assert len(ana) == 88
KEY = {norm(n): int(i) for i, n in zip(ana.id_nil, ana.nome)}

def nil_id(name):
    k = norm(name)
    if k == "":
        return -1                       # nascite senza quartiere
    if k in KEY:
        return KEY[k]
    c = [i for kk, i in KEY.items() if kk.startswith(k)]   # nomi troncati in ds1943
    assert len(c) == 1, ("quartiere non agganciato", name)
    return c[0]

# ------------------------------------------------------------ nati per NIL (ds141 + ds1943)
a = pd.read_csv(os.path.join(RAW, "ds141-popolazione-nascite-quartiere.csv"), sep=";", keep_default_na=False)
b = pd.read_csv(os.path.join(RAW, "ds1943_popolazione-nascite-residenti-quartiere.csv"), sep=";", keep_default_na=False)
a.columns = b.columns = ["anno", "quartiere", "genere", "madre", "padre", "n"]
a["fonte"] = "ds141"
b["fonte"] = "ds1943"
x = pd.concat([a, b], ignore_index=True)
x["id_nil"] = x.quartiere.map(nil_id)
assert x.n.ge(1).all()
x["madre"] = x.madre.replace({"n.d.": "nd"})
x["padre"] = x.padre.replace({"n.d.": "nd"})

g = x.groupby(["anno", "id_nil"])
nasc = pd.DataFrame({
    "nati": g.n.sum(),
    "madre_straniera": x[x.madre == "Straniera"].groupby(["anno", "id_nil"]).n.sum(),
    "madre_italiana": x[x.madre == "Italiana"].groupby(["anno", "id_nil"]).n.sum(),
    "madre_nd": x[x.madre == "nd"].groupby(["anno", "id_nil"]).n.sum(),
    "entrambi_stranieri": x[(x.madre == "Straniera") & (x.padre == "Straniera")].groupby(["anno", "id_nil"]).n.sum(),
    "femmine": x[x.genere == "Femmine"].groupby(["anno", "id_nil"]).n.sum(),
    "maschi": x[x.genere == "Maschi"].groupby(["anno", "id_nil"]).n.sum(),
}).fillna(0).astype(int).reset_index()
nasc.to_csv(os.path.join(OUT, "nascite_nil_anno.csv"), index=False)

# controllo: totale annuo = ds1495 (nati vivi residenti, serie storica del Comune)
s1495 = pd.read_csv(os.path.join(RAW, "ds1495_nati_vivi_residenti_anno-1880.csv"), sep=";")
s1495.columns = ["anno", "nati"]
s1495 = s1495.set_index("anno").nati
tot = nasc.groupby("anno").nati.sum()
diff = {int(y): int(tot[y] - s1495[y]) for y in tot.index}
CHK["totale_nil_meno_ds1495"] = diff
assert all(v == 0 for v in diff.values()), diff
CHK["nati_senza_quartiere"] = {int(y): int(v) for y, v in nasc[nasc.id_nil == -1].set_index("anno").nati.items()}
CHK["nati_totali"] = {int(y): int(v) for y, v in tot.items()}

# ------------------------------------------------------------ ds27: donne 15-49, residenti, per NIL e per cittadinanza
z = zipfile.ZipFile(os.path.join(M, "popolazione", "raw", "comune_ds27", "ds27_pop_sto_quartiere.zip"))
d = pd.read_csv(z.open("ds27_pop_sto_quartiere.csv"), sep=";", dtype={"Eta": str, "Cittadinanza": str, "Nil": str}, keep_default_na=False)
d["eta"] = d.Eta.str.extract(r"(\d+)")[0].astype(int)       # "100 e piu'" -> 100
d["it"] = d.Cittadinanza.eq("Italia")
CHK["ds27_righe"] = int(len(d))
# controllo: id e nome dei NIL in ds27 coincidono con l'anagrafica usata per agganciare i nati
for i_, n_ in d[["IdNil", "Nil"]].drop_duplicates().itertuples(index=False):
    assert nil_id(n_) == int(i_), ("id/nome NIL diversi", i_, n_)
CHK["ds27_id_nome_nil_coerenti"] = True
CHK["ds27_cittadinanze_senza_italia_ma_n.d."] = int(d.Cittadinanza.str.contains("n.d", case=False).sum())
d["f1549"] = d.eta.between(15, 49) & d.Genere.eq("Femmine")
den = d.groupby(["Anno", "IdNil"]).Residenti.sum().rename("residenti").to_frame()
den["donne_15_49"] = d[d.f1549].groupby(["Anno", "IdNil"]).Residenti.sum()
den = den.fillna(0).astype(int).reset_index().rename(columns={"Anno": "anno", "IdNil": "id_nil"})
den.to_csv(os.path.join(OUT, "denominatori_nil_anno.csv"), index=False)
CHK["ds27_residenti_citta"] = {int(y): int(v) for y, v in den.groupby("anno").residenti.sum().items() if y in (1999, 2003, 2012, 2020, 2024, 2025)}

# citta': donne 15-49 italiane / straniere, e per classe di 5 anni
cit = d[d.f1549].copy()
cit["classe"] = (cit.eta // 5) * 5
cc = cit.groupby(["Anno", "classe", "it"]).Residenti.sum().unstack("it").rename(columns={True: "italiane", False: "straniere"}).fillna(0).astype(int)
cc["tutte"] = cc.italiane + cc.straniere
cc = cc.reset_index().rename(columns={"Anno": "anno"})
cc.to_csv(os.path.join(OUT, "donne_citta_anno_classe.csv"), index=False)

# ------------------------------------------------------------ tassi per NIL
# esposizione = media delle donne 15-49 (e dei residenti) al 31/12 dell'anno prima e dell'anno
den2 = den.set_index(["id_nil", "anno"]).sort_index()
nasc_idx = nasc[nasc.id_nil > 0].set_index(["id_nil", "anno"])
rows = []
for i in sorted(ana.id_nil):
    for y in range(2003, 2025):
        k, k0 = (i, y), (i, y - 1)
        if k not in den2.index or k0 not in den2.index:
            continue
        w = (den2.loc[k, "donne_15_49"] + den2.loc[k0, "donne_15_49"]) / 2
        p = (den2.loc[k, "residenti"] + den2.loc[k0, "residenti"]) / 2
        n = int(nasc_idx.loc[k, "nati"]) if k in nasc_idx.index else 0
        ms = int(nasc_idx.loc[k, "madre_straniera"]) if k in nasc_idx.index else 0
        mi = int(nasc_idx.loc[k, "madre_italiana"]) if k in nasc_idx.index else 0
        rows.append({"anno": y, "id_nil": int(i), "nati": n, "donne_15_49_medie": round(w, 1), "residenti_medi": round(p, 1),
                     "nati_per_1000_donne_15_49": round(1000 * n / w, 2) if w > 0 else None,
                     "nati_per_1000_residenti": round(1000 * n / p, 2) if p > 0 else None,
                     "madre_straniera": ms, "madre_italiana": mi,
                     "quota_madre_straniera_pct": round(100 * ms / (ms + mi), 1) if (ms + mi) > 0 else None})
tassi = pd.DataFrame(rows)
tassi.to_csv(os.path.join(OUT, "tassi_nil_anno.csv"), index=False)

# ------------------------------------------------------------ citta' per anno
nc = nasc.groupby("anno")[["nati", "madre_straniera", "madre_italiana", "madre_nd", "entrambi_stranieri"]].sum()
cdn = den.groupby("anno")[["residenti", "donne_15_49"]].sum()
cit_rows = []
for y in range(2003, 2025):
    w = (cdn.loc[y, "donne_15_49"] + cdn.loc[y - 1, "donne_15_49"]) / 2
    p = (cdn.loc[y, "residenti"] + cdn.loc[y - 1, "residenti"]) / 2
    fy, fy0 = cc[cc.anno == y], cc[cc.anno == y - 1]
    wi = (fy.italiane.sum() + fy0.italiane.sum()) / 2
    ws = (fy.straniere.sum() + fy0.straniere.sum()) / 2
    n = nc.loc[y]
    cit_rows.append({"anno": y, "nati_residenti": int(n.nati), "nati_ds1495": int(s1495[y]),
                     "residenti_medi": round(p), "donne_15_49_medie": round(w),
                     "nati_per_1000_residenti": round(1000 * n.nati / p, 2),
                     "nati_per_1000_donne_15_49": round(1000 * n.nati / w, 2),
                     "madre_straniera": int(n.madre_straniera), "madre_italiana": int(n.madre_italiana), "madre_nd": int(n.madre_nd),
                     "quota_madre_straniera_pct": round(100 * n.madre_straniera / (n.madre_straniera + n.madre_italiana), 1),
                     "donne_15_49_straniere_medie": round(ws), "donne_15_49_italiane_medie": round(wi),
                     "quota_donne_15_49_straniere_pct": round(100 * ws / w, 1),
                     "nati_per_1000_donne_straniere": round(1000 * n.madre_straniera / ws, 2),
                     "nati_per_1000_donne_italiane": round(1000 * n.madre_italiana / wi, 2)})
citta = pd.DataFrame(cit_rows)
# nati avvenuti a Milano (ds289 2003-2020 + ds1945 2021-2024) come confronto, tutti i luoghi di residenza dei genitori
d289 = pd.read_csv(os.path.join(RAW, "ds289-popolazione-nascite.csv"), sep=";", keep_default_na=False)
d289.columns = ["anno", "genere", "madre", "padre", "luogo", "n"]
av = d289.groupby("anno").n.sum()
d1945 = pd.read_csv(os.path.join(RAW, "ds1945_popolazione-nascite-milano-eta.csv"), sep=";", keep_default_na=False)
d1945.columns = ["anno", "padre_eta", "madre_eta", "parto", "filiazione", "n"]
av = pd.concat([av, d1945.groupby("anno").n.sum()])
citta["nati_avvenuti_a_milano"] = citta.anno.map(av)
# nati a Milano da madre residente a Milano (ds289): quota
res = d289[d289.luogo == "Milano"].groupby("anno").n.sum()
d1946 = pd.read_csv(os.path.join(RAW, "ds1946_popolazione-nascite-milano-cit.csv"), sep=";", keep_default_na=False)
d1946.columns = ["anno", "genere", "madre", "padre", "luogo", "n"]
res = pd.concat([res, d1946[d1946.luogo == "Milano"].groupby("anno").n.sum()])
CHK["ds1946_totale_avvenuti"] = {int(k): int(v) for k, v in d1946.groupby("anno").n.sum().items()}
citta["nati_in_citta_da_genitori_residenti"] = citta.anno.map(res)
citta["nati_in_citta_da_genitori_residenti_pct"] = citta.anno.map(lambda y: round(100 * res[y] / av[y], 1))
citta["residenti_nati_altrove_stima"] = citta.nati_residenti - citta.nati_in_citta_da_genitori_residenti
citta.to_csv(os.path.join(OUT, "citta_anno.csv"), index=False)

# ------------------------------------------------------------ eta' della madre, citta' 2021-2024 (ds1944 residenti)
e = pd.read_csv(os.path.join(RAW, "ds1944_popolazione-nascite-residenti-eta.csv"), sep=";", keep_default_na=False)
e.columns = ["anno", "padre_eta", "madre_eta", "parto", "filiazione", "n"]
CHK["ds1944_senza_eta_madre"] = {int(k): int(v) for k, v in e[e.madre_eta == ""].groupby("anno").n.sum().items()}
CHK["ds1944_totale"] = {int(k): int(v) for k, v in e.groupby("anno").n.sum().items()}
em = e[e.madre_eta != ""].groupby(["anno", "madre_eta"]).n.sum().reset_index()
em["classe"] = em.madre_eta.str.extract(r"(\d+)")[0].astype(int)
em["medio"] = em.classe + 2.5          # centro della classe (15-19 -> 17,5 ecc.)
em = em.sort_values(["anno", "classe"])
em.to_csv(os.path.join(OUT, "eta_madre_citta.csv"), index=False)
# nati avvenuti a Milano (ds1945) - stesse classi
e2 = d1945[d1945.madre_eta != ""].groupby(["anno", "madre_eta"]).n.sum().reset_index()
e2.to_csv(os.path.join(OUT, "eta_madre_avvenuti_a_milano.csv"), index=False)
CHK["ds1945_senza_eta_madre"] = {int(k): int(v) for k, v in d1945[d1945.madre_eta == ""].groupby("anno").n.sum().items()}

# TFR della citta' 2021-2024 (mio calcolo): sum_classi 5 * nati/donne della classe (donne = media 31/12 anno prima e anno)
ds27w = d[d.Genere.eq("Femmine") & d.eta.between(10, 59)].copy()
ds27w["classe"] = (ds27w.eta // 5) * 5
W = ds27w.groupby(["Anno", "classe"]).Residenti.sum()
tfr = []
for y in range(2021, 2025):
    t, ages = 0.0, {}
    for _, r in em[em.anno == y].iterrows():
        c = int(r.classe)
        w = (W[(y, c)] + W[(y - 1, c)]) / 2
        t += 5 * r.n / w
        ages[c] = (r.n, w)
    # nati con classi 10-14 o 50-59 non separati: si assegnano alle classi estreme come fa ISTAT (<=14 -> 15, >=50 -> 49)
    ex = em[(em.anno == y)]
    mean_age = float((ex.n * ex.medio).sum() / ex.n.sum())
    tfr.append({"anno": y, "tfr_mio_calcolo": round(t, 3), "eta_media_madre_approx": round(mean_age, 2),
                "nati_con_eta_madre": int(ex.n.sum()), "nati_totale": CHK["ds1944_totale"][y],
                "quota_madre_35_piu_pct": round(100 * ex[ex.classe >= 35].n.sum() / ex.n.sum(), 1),
                "quota_madre_40_piu_pct": round(100 * ex[ex.classe >= 40].n.sum() / ex.n.sum(), 1),
                "quota_madre_sotto_25_pct": round(100 * ex[ex.classe < 25].n.sum() / ex.n.sum(), 1)})
pd.DataFrame(tfr).to_csv(os.path.join(OUT, "tfr_citta_2021_2024.csv"), index=False)

# ------------------------------------------------------------ ISTAT: TFR e eta' media delle madri (Italia, Milano provincia ITC45, Lombardia)
def ist(fn, nome):
    t = pd.read_csv(os.path.join(N, "raw", "istat", fn), dtype=str)
    t = t[t.REF_AREA.isin(["IT", "ITC45", "ITC4"]) & t.MOTHER_AGE.eq("TOTAL")]
    t = t.assign(area=t.REF_AREA.map({"IT": "Italia", "ITC45": "Provincia di Milano", "ITC4": "Lombardia"}),
                 cittadinanza=t.CITIZENSHIP.map({"TOTAL": "tutte", "ITL": "italiana", "FRG": "straniera"}),
                 anno=t.TIME_PERIOD.astype(int), valore=t.OBS_VALUE.astype(float))
    return t.pivot_table(index=["area", "cittadinanza", "anno"], values="valore", aggfunc="first").rename(columns={"valore": nome})
ist_t = ist("istat_FECONDITA1_5_TFR_province.csv", "tfr").join(ist("istat_FECONDITA1_6_eta_media_madri_province.csv", "eta_media_madre")).reset_index()
ist_t.to_csv(os.path.join(OUT, "istat_tfr_eta_madre.csv"), index=False)
CHK["istat_anni"] = [int(ist_t.anno.min()), int(ist_t.anno.max())]
for k in ("tfr", "eta_media_madre"):
    CHK["istat_" + k + "_2024_milano_italia"] = [float(ist_t[(ist_t.area == "Provincia di Milano") & (ist_t.cittadinanza == "tutte") & (ist_t.anno == 2024)][k].iloc[0]),
                                                float(ist_t[(ist_t.area == "Italia") & (ist_t.cittadinanza == "tutte") & (ist_t.anno == 2024)][k].iloc[0])]

# ------------------------------------------------------------ ISTAT bilancio demografico: nati del Comune (controllo)
ib = pd.read_csv(os.path.join(M, "popolazione", "pulito", "istat_bilancio_milano_2001_2018.csv"))
ib = ib[(ib.Sesso == "Maschi e femmine") & (ib.Cittadinanza == "Tutte")][["Anno", "Nati"]].rename(columns={"Anno": "anno", "Nati": "nati_istat"})
ib2 = pd.read_csv(os.path.join(M, "popolazione", "pulito", "istat_bilancio_milano_2019_2024_annuale.csv"))[["Anno", "Nati vivi"]].rename(columns={"Anno": "anno", "Nati vivi": "nati_istat"})
ist_n = pd.concat([ib, ib2]).drop_duplicates("anno").set_index("anno").nati_istat
citta["nati_istat_bilancio"] = citta.anno.map(ist_n)
citta.to_csv(os.path.join(OUT, "citta_anno.csv"), index=False)
CHK["nati_istat_bilancio"] = {int(k): int(v) for k, v in ist_n.items() if k in (2003, 2010, 2015, 2019, 2020, 2024)}

json.dump(CHK, open(os.path.join(OUT, "controlli.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(CHK, ensure_ascii=False)[:3000])
