"""Riepiloghi sugli alberi di Milano: specie, diversita' (10-20-30), per NIL, cambiamenti tra edizioni, confronto col reddito per CAP.

Uso (percorsi assoluti):
  python -I -X utf8 analisi.py <alberi_dir> <progetto_milano_in_dati_dir>
Legge pulito/alberi.csv (da build.py). Scrive tabelle in pulito/ e pulito/riepilogo.json
"""
import sys, os, json, re
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from shapely.geometry import shape
from pyproj import Transformer
import shapely

A, P = sys.argv[1], sys.argv[2]
PU = os.path.join(A, "pulito")
R = {}
t = pd.read_csv(os.path.join(PU, "alberi.csv"), sep=";", low_memory=False, keep_default_na=False,
                na_values=[""], dtype={"id": str, "id_area": str, "localita": str})
EDS = sorted(t.edizione.unique())
LAST = EDS[-1]

# ================= 1. citta' intera, per edizione
rows, topsp, topgen, topfam = [], [], [], []
for ed in EDS:
    e = t[t.edizione == ed]
    n = len(e)
    nd = (e.genere.isna()).sum()
    sp = e.specie_binomio_normalizzata.value_counts()
    sp_raw = e.specie_binomio.value_counts()
    gen = e.genere.value_counts()
    fam = e.famiglia.value_counts()
    sp_known = sp.drop(labels=[i for i in sp.index if i == "n.d." or i.endswith(" spp")], errors="ignore")
    # caso peggiore: la specie piu' frequente di un genere + tutti i "spp" di quel genere (la specie non e' indicata)
    spp_by_genus = e[e.epiteto == "spp"].genere.value_counts()
    worst = max(((sp_known[s] + spp_by_genus.get(s.split()[0], 0)), s) for s in sp_known.index[:10])
    top_sp_name = sp_known.index[0]
    rows.append({
        "edizione": ed, "alberi": n, "generi": int(gen.size), "specie_binomio_distinte": int(sp_raw.size),
        "specie_normalizzate_distinte": int(sp.size), "famiglie": int(fam.size),
        "senza_genere": int(nd), "con_epiteto_spp": int((e.epiteto == "spp").sum()),
        "specie_piu_frequente": top_sp_name, "quota_specie_piu_frequente_pct": round(100 * sp_known.iloc[0] / n, 2),
        "quota_specie_top_caso_peggiore_pct(spp_incluse)": round(100 * worst[0] / n, 2), "specie_top_caso_peggiore": worst[1],
        "genere_piu_frequente": gen.index[0], "quota_genere_piu_frequente_pct": round(100 * gen.iloc[0] / n, 2),
        "famiglia_piu_frequente": fam.index[0], "quota_famiglia_piu_frequente_pct": round(100 * fam.iloc[0] / n, 2),
        "regola_10_20_30_rispettata": bool(sp_known.iloc[0] / n < .10 and gen.iloc[0] / n < .20 and fam.iloc[0] / n < .30),
        "specie_oltre_10pct": int((sp_known / n >= .10).sum()), "generi_oltre_20pct": int((gen / n >= .20).sum()),
        "famiglie_oltre_30pct": int((fam / n >= .30).sum()),
    })
    for tab, ser, key in [(topsp, sp, "specie"), (topgen, gen, "genere"), (topfam, fam, "famiglia")]:
        s = ser.head(25).reset_index()
        s.columns = [key, "alberi"]
        s["quota_pct"] = (100 * s.alberi / n).round(2)
        s.insert(0, "edizione", ed)
        tab.append(s)
pd.DataFrame(rows).to_csv(os.path.join(PU, "citta_per_edizione.csv"), index=False, sep=";")
pd.concat(topsp).to_csv(os.path.join(PU, "top_specie.csv"), index=False, sep=";")
pd.concat(topgen).to_csv(os.path.join(PU, "top_generi.csv"), index=False, sep=";")
pd.concat(topfam).to_csv(os.path.join(PU, "top_famiglie.csv"), index=False, sep=";")
R["citta_per_edizione"] = rows

# nome comune delle specie top (ultima edizione)
e = t[t.edizione == LAST]
nc = e.groupby("specie_binomio_normalizzata").nome_comune.agg(lambda s: s.mode().iat[0])
ts = pd.concat(topsp)
ts["nome_comune"] = ts.specie.map(nc)
ts.to_csv(os.path.join(PU, "top_specie.csv"), index=False, sep=";")

# ================= 2. misure: valori "di default"
m = e.copy()
tri = ((m.diam_tronc_cm == 8) & (m.altezza_m == 5) & (m.diam_chioma_m == 2))
R["misure_ultima_edizione"] = {
    "tronco_esattamente_8cm_pct": round(100 * (m.diam_tronc_cm == 8).mean(), 1),
    "altezza_esattamente_5m_pct": round(100 * (m.altezza_m == 5).mean(), 1),
    "chioma_esattamente_2m_pct": round(100 * (m.diam_chioma_m == 2).mean(), 1),
    "tripletta_8cm_5m_2m_pct": round(100 * tri.mean(), 1), "tripletta_n": int(tri.sum()),
    "mediana_tronco_cm": float(m.diam_tronc_cm.median()), "mediana_altezza_m": float(m.altezza_m.median()),
    "tronco_oltre_50cm_pct": round(100 * (m.diam_tronc_cm >= 50).mean(), 1),
    "tronco_oltre_100cm_pct": round(100 * (m.diam_tronc_cm >= 100).mean(), 2),
}
# data_inizio_scheda: 21 ottobre
dm = m.data_inizio_scheda.str[5:]
R["data_inizio_scheda"] = {"quota_21_ottobre_pct": round(100 * (dm == "10-21").mean(), 1),
                           "quota_31_dicembre_pct": round(100 * (dm == "12-31").mean(), 1),
                           "date_distinte": int(m.data_inizio_scheda.nunique())}
anno = m.data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce")
R["senza_data_scheda_ultima_edizione"] = int(anno.isna().sum())
yy = anno.value_counts().sort_index()
yy.rename("alberi").reset_index().rename(columns={"data_inizio_scheda": "anno"}).to_csv(
    os.path.join(PU, "alberi_per_anno_scheda_" + LAST + ".csv"), index=False, sep=";")
R["anni_scheda"] = {"prima_del_2000_pct": round(100 * (anno < 2000).mean(), 1), "dal_2015_pct": round(100 * (anno >= 2015).mean(), 1),
                    "dal_2020_pct": round(100 * (anno >= 2020).mean(), 1)}

# strada o area verde (prima parola di 'localita')
w = m.localita.fillna("").str.split().str[0].str.lower()
tipo = np.select([w.isin(["via", "vie", "viale", "viali", "corso", "piazza", "piazzale", "largo", "bastioni", "cavalcavia", "foro", "alzaia", "svincolo", "interscambio", "collegamento", "strada", "ponte", "galleria"]),
                  w.isin(["parco", "giardino", "giardini", "bosco", "villa", "area", "orto", "parchetto", "cascina", "quartiere"]), w == "cimitero"],
                 ["strada/piazza", "parco/giardino/area verde", "cimitero"], "altro")
R["tipo_localita"] = pd.Series(tipo).value_counts().to_dict()
R["tipo_localita_pct"] = (100 * pd.Series(tipo).value_counts(normalize=True)).round(1).to_dict()

# ================= 3. NIL
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
tr = Transformer.from_crs(4326, 32632, always_xy=True)
nil = []
for f in g["features"]:
    pg = shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
    nil.append({"id_nil": int(f["properties"]["ID_NIL"]), "nil": f["properties"]["NIL"], "area_km2": pg.area / 1e6})
nil = pd.DataFrame(nil)
d205 = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"),
                   sep=None, engine="python")
d205 = d205[d205.NIL.notna()].copy()
d205["id_nil"] = d205.NIL.astype(int)
d205["area_ds205_km2"] = d205["Area (metri quadrati)"].astype(str).str.replace(",", ".").astype(float) / 1e6
for yr in (2023, 2024):
    x = d205[d205.Anno == yr][["id_nil", "Totale"]].rename(columns={"Totale": f"abitanti_{yr}"})
    nil = nil.merge(x, on="id_nil", how="left")
nil = nil.merge(d205[d205.Anno == 2024][["id_nil", "area_ds205_km2"]], on="id_nil", how="left")
R["nil_area_totale_km2_poligoni"] = round(nil.area_km2.sum(), 2)
R["nil_area_totale_km2_ds205"] = round(nil.area_ds205_km2.sum(), 2)
R["nil_abitanti_2024"] = int(nil.abitanti_2024.sum()); R["nil_abitanti_2023"] = int(nil.abitanti_2023.sum())
nil["diff_area_pct"] = 100 * (nil.area_km2 / nil.area_ds205_km2 - 1)
R["nil_con_area_ds205_incoerente_oltre_5pct"] = nil[nil.diff_area_pct.abs() > 5][["nil", "area_km2", "area_ds205_km2"]].round(3).to_dict("records")
R["controllo_area_poligono_vs_ds205_max_diff_pct"] = round(float((100 * (nil.area_km2 / nil.area_ds205_km2 - 1)).abs().max()), 2)
ED_POP = {"2023-03-31": "abitanti_2023", "2024-03-31": "abitanti_2024", "2025-03-31": "abitanti_2024"}

for ed in EDS:
    s = t[t.edizione == ed]
    c = s.groupby("id_nil").size().rename(f"alberi_{ed[:4]}")
    nil = nil.merge(c, left_on="id_nil", right_index=True, how="left")
    nil[f"alberi_{ed[:4]}"] = nil[f"alberi_{ed[:4]}"].fillna(0).astype(int)
nil["alberi_per_1000ab_2025"] = 1000 * nil.alberi_2025 / nil.abitanti_2024.replace(0, np.nan)
nil["alberi_per_1000ab_2023"] = 1000 * nil.alberi_2023 / nil.abitanti_2023
nil["alberi_per_km2_2025"] = nil.alberi_2025 / nil.area_km2
nil["variazione_2023_2025"] = nil.alberi_2025 - nil.alberi_2023
nil["variazione_pct"] = 100 * nil.variazione_2023_2025 / nil.alberi_2023.replace(0, np.nan)
nil["abitanti_per_albero_2025"] = nil.abitanti_2024 / nil.alberi_2025
# diversita' per NIL (ultima edizione)
def div(df):
    n = len(df)
    sp = df.specie_binomio_normalizzata.value_counts()
    sp = sp[[i for i in sp.index if i != "n.d." and not i.endswith(" spp")]]
    gen = df.genere.value_counts()
    p = gen / gen.sum()
    return pd.Series({"generi_nil": gen.size, "genere_top": gen.index[0], "genere_top_pct": 100 * gen.iloc[0] / n,
                      "specie_top": sp.index[0] if len(sp) else "", "specie_top_pct": 100 * sp.iloc[0] / n if len(sp) else np.nan,
                      "simpson_generi": 1 - (p ** 2).sum(),
                      "diam_mediano_cm": df.diam_tronc_cm.median(), "quota_tronco_ge50_pct": 100 * (df.diam_tronc_cm >= 50).mean()})
dv = t[t.edizione == LAST].groupby("id_nil").apply(div, include_groups=False).reset_index()
nil = nil.merge(dv, on="id_nil", how="left")
# alberi senza NIL (fuori dai 88 poligoni)
sn = t[(t.edizione == LAST) & t.id_nil.isna()]
R["alberi_senza_NIL_ultima_edizione"] = len(sn)
nil.round(4).to_csv(os.path.join(PU, "nil_alberi.csv"), index=False, sep=";")

big = nil[nil.abitanti_2024 >= 5000].copy()
R["nil_con_meno_di_5000_abitanti_fuori_classifica"] = nil[nil.abitanti_2024 < 5000][["nil", "abitanti_2024", "alberi_2025"]].to_dict("records")
cols = ["nil", "abitanti_2024", "area_km2", "alberi_2025", "alberi_per_1000ab_2025", "alberi_per_km2_2025"]
R["nil_top_per_abitante"] = big.sort_values("alberi_per_1000ab_2025", ascending=False).head(10)[cols].round(2).to_dict("records")
R["nil_bottom_per_abitante"] = big.sort_values("alberi_per_1000ab_2025").head(10)[cols].round(2).to_dict("records")
R["nil_top_per_km2"] = nil.sort_values("alberi_per_km2_2025", ascending=False).head(8)[cols].round(2).to_dict("records")
R["nil_bottom_per_km2"] = nil.sort_values("alberi_per_km2_2025").head(8)[cols].round(2).to_dict("records")
R["nil_in_classifica_n"] = len(big)
R["nil_rapporto_max_min_per_abitante"] = round(float(big.alberi_per_1000ab_2025.max() / big.alberi_per_1000ab_2025.min()), 1)
R["citta_alberi_per_1000ab_2025"] = round(1000 * len(e) / nil.abitanti_2024.sum(), 1)
R["citta_alberi_per_km2_2025"] = round(len(e) / nil.area_km2.sum(), 1)
R["nil_mediana_alberi_per_1000ab"] = round(float(big.alberi_per_1000ab_2025.median()), 1)
R["nil_con_specie_top_oltre_10pct"] = int((nil.specie_top_pct >= 10).sum())
R["nil_con_genere_top_oltre_20pct"] = int((nil.genere_top_pct >= 20).sum())
R["nil_genere_top_oltre_50pct"] = nil[nil.genere_top_pct >= 50][["nil", "genere_top", "genere_top_pct", "alberi_2025"]].round(1).to_dict("records")

# controllo municipio dichiarato nel file vs municipio prevalente del NIL
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
x = t[(t.edizione == LAST) & t.id_nil.notna()].merge(ana[["nil", "municipio_prevalente"]], left_on="id_nil", right_on="nil", how="left")
R["controllo_municipio_file_vs_NIL_prevalente_pct_uguali"] = round(100 * float((x.municipio_file == x.municipio_prevalente).mean()), 1)

# ================= 4. cambiamenti tra edizioni (per id)
def ids(ed):
    s = t[t.edizione == ed].set_index("id")
    return s
a, b, c = (ids(ed) for ed in EDS)
ch = []
for (e1, s1), (e2, s2) in [((EDS[0], a), (EDS[1], b)), ((EDS[1], b), (EDS[2], c)), ((EDS[0], a), (EDS[2], c))]:
    common = s1.index.intersection(s2.index)
    removed = s1.index.difference(s2.index)
    added = s2.index.difference(s1.index)
    x1, y1 = tr.transform(s1.loc[common].lon.values, s1.loc[common].lat.values)
    x2, y2 = tr.transform(s2.loc[common].lon.values, s2.loc[common].lat.values)
    dist = np.hypot(x1 - x2, y1 - y2)
    sp_diff = (s1.loc[common].specie_binomio.values != s2.loc[common].specie_binomio.values)
    gr = (s2.loc[common].diam_tronc_cm.values - s1.loc[common].diam_tronc_cm.values)
    yrs = (pd.Timestamp(e2) - pd.Timestamp(e1)).days / 365.25
    added_year = s2.loc[added].data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce")
    rem_year = s1.loc[removed].data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce")
    ch.append({"da": e1, "a": e2, "alberi_da": len(s1), "alberi_a": len(s2), "in_comune": len(common), "rimossi": len(removed), "aggiunti": len(added),
               "saldo": len(s2) - len(s1), "saldo_pct": round(100 * (len(s2) - len(s1)) / len(s1), 2),
               "in_comune_spostati_oltre_5m": int((dist > 5).sum()), "in_comune_spostati_oltre_50m": int((dist > 50).sum()),
               "in_comune_specie_cambiata": int(sp_diff.sum()),
               "aggiunti_con_anno_scheda_nel_periodo_pct": round(100 * float((added_year.dropna() >= int(e1[:4])).mean()), 1),
               "aggiunti_con_anno_scheda_precedente_pct": round(100 * float((added_year.dropna() < int(e1[:4])).mean()), 1),
               "rimossi_con_scheda_ante_2000_pct": round(100 * float((rem_year.dropna() < 2000).mean()), 1),
               "diametro_mediano_rimossi_cm": float(s1.loc[removed].diam_tronc_cm.median()),
               "diametro_mediano_aggiunti_cm": float(s2.loc[added].diam_tronc_cm.median()),
               "crescita_tronco_mediana_cm_anno": round(float(np.nanmedian(gr)) / yrs, 3),
               "in_comune_tronco_invariato_pct": round(100 * float(np.nanmean(gr == 0)), 1)})
pd.DataFrame(ch).to_csv(os.path.join(PU, "cambiamenti_edizioni.csv"), index=False, sep=";")
R["cambiamenti"] = ch

# alberi aggiunti e rimossi 2023->2025 per genere e per NIL
common = a.index.intersection(c.index)
rem = a.loc[a.index.difference(c.index)]
add = c.loc[c.index.difference(a.index)]
gg = pd.DataFrame({"rimossi": rem.genere.value_counts(), "aggiunti": add.genere.value_counts(), "tot_2023": a.genere.value_counts()}).fillna(0).astype(int)
gg["saldo"] = gg.aggiunti - gg.rimossi
gg.sort_values("tot_2023", ascending=False).head(30).to_csv(os.path.join(PU, "cambiamenti_per_genere_2023_2025.csv"), sep=";")
R["cambiamenti_generi_top"] = gg.sort_values("tot_2023", ascending=False).head(12).to_dict("index")
R["aggiunti_2023_2025_per_anno_scheda"] = add.data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce").dropna().astype(int).value_counts().sort_index().tail(8).to_dict()
R["rimossi_2023_2025_totale"] = len(rem)
R["rimossi_2023_2025_con_anno_scheda_dal_2019"] = int((rem.data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce") >= 2019).sum())
R["rimossi_2023_2025_con_tronco_fino_a_12cm_pct"] = round(100*float((rem.diam_tronc_cm <= 12).mean()),1)
R["rimossi_2023_2025_per_anno_scheda_top"] = rem.data_inizio_scheda.str[:4].pipe(pd.to_numeric, errors="coerce").dropna().astype(int).value_counts().head(8).to_dict()
# nuovi tipi / nuove specie nel 2025
R["generi_piu_frequenti_tra_gli_aggiunti_2023_2025"] = add.genere.value_counts().head(8).to_dict()
# NIL: saldo
nsa = nil.sort_values("variazione_2023_2025")[["nil", "alberi_2023", "alberi_2025", "variazione_2023_2025", "variazione_pct"]].round(1)
R["nil_peggiori_saldi_2023_2025"] = nsa.head(8).to_dict("records")
R["nil_migliori_saldi_2023_2025"] = nsa.tail(8).to_dict("records")

# ================= 5. confronto col reddito per CAP (38 CAP, stima)
cap = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "cap_redditi_servizi.csv"),
                  usecols=["CAP", "residenti_stimati", "imponibile_medio_2024", "complessivo_per_contribuente", "contribuenti_2024", "NIL_piu_frequente"])
cc = t[t.edizione == LAST].groupby("cap_stimato").size().rename("alberi_2025").reset_index().rename(columns={"cap_stimato": "CAP"})
cap = cap.merge(cc, on="CAP", how="left")
cap["alberi_per_1000ab"] = 1000 * cap.alberi_2025 / cap.residenti_stimati
cap.round(3).to_csv(os.path.join(PU, "cap_alberi_reddito.csv"), index=False, sep=";")
rng = np.random.default_rng(7)
def sp_ci(x, y, n=4000):
    r = spearmanr(x, y).statistic
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        bs.append(spearmanr(x[i], y[i]).statistic)
    return round(float(r), 3), [round(float(v), 3) for v in np.nanpercentile(bs, [2.5, 97.5])]
xs = cap.dropna(subset=["alberi_per_1000ab", "imponibile_medio_2024"])
R["cap_n"] = len(xs)
R["cap_spearman_alberi_per_1000ab_vs_imponibile_2024"] = sp_ci(xs.imponibile_medio_2024.values, xs.alberi_per_1000ab.values)
R["cap_spearman_alberi_totali_vs_imponibile_2024"] = sp_ci(xs.imponibile_medio_2024.values, xs.alberi_2025.values)
dens = None
R["cap_top_alberi_per_1000ab"] = cap.sort_values("alberi_per_1000ab", ascending=False).head(5)[["CAP", "NIL_piu_frequente", "alberi_per_1000ab", "imponibile_medio_2024"]].round(1).to_dict("records")
R["cap_bottom_alberi_per_1000ab"] = cap.sort_values("alberi_per_1000ab").head(5)[["CAP", "NIL_piu_frequente", "alberi_per_1000ab", "imponibile_medio_2024"]].round(1).to_dict("records")
# stesso confronto a livello NIL con indice di verde SPOTTED (luglio 2024)
iv = pd.read_csv(os.path.join(A, "raw", "comune_ds2813", "ds2813_spotted-milan-urbangreenindex-nil-01072024_31072024.csv"), sep=";", decimal=".")
iv = iv.rename(columns={"ID_NIL": "id_nil", "value": "indice_verde"})[["id_nil", "indice_verde"]]
nil = nil.merge(iv, on="id_nil", how="left")
nil.round(4).to_csv(os.path.join(PU, "nil_alberi.csv"), index=False, sep=";")
bb = nil[nil.abitanti_2024 >= 5000].dropna(subset=["indice_verde"])
R["nil_spearman_alberi_per_km2_vs_indice_verde_SPOTTED"] = sp_ci(bb.indice_verde.values, bb.alberi_per_km2_2025.values)
R["nil_spearman_alberi_per_1000ab_vs_abitanti_per_km2"] = sp_ci((bb.abitanti_2024 / bb.area_km2).values, bb.alberi_per_1000ab_2025.values)

json.dump(R, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
