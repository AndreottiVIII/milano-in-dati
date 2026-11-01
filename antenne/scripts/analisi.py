"""Riepiloghi CASTEL Milano. Uso: python -I -X utf8 analisi.py <antenne_dir> <milano_in_dati_dir>
Legge pulito/impianti.csv, pulito/snapshot_impianti.csv, scuole/pulito/*anagrafica.csv, citta-15-minuti (ds205 abitanti, civici). Scrive pulito/*.csv e riepilogo.json"""
import sys, os, json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

A, P = sys.argv[1], sys.argv[2]
OUT = os.path.join(A, "pulito")
R = {}
t = pd.read_csv(os.path.join(OUT, "impianti.csv"), sep=";", dtype={"cap": str, "id_nil": "Int64", "id_nil_file": str})
S = pd.read_csv(os.path.join(OUT, "snapshot_impianti.csv"), sep=";", dtype=str, keep_default_na=False)
S["lon"] = pd.to_numeric(S.lon, errors="coerce"); S["lat"] = pd.to_numeric(S.lat, errors="coerce")
S["acceso"] = S.acceso == "True"
S["previsto"] = S.previsto == "True"
S["procedura_scia"] = S.procedura_scia == "True"
for c in ("acceso", "previsto", "procedura_scia"):
    t[c] = t[c].astype(bool)

# ---------------- 1. quadro generale (file attuale)
R["impianti_totali"] = len(t)
R["stato"] = t.stato.value_counts().to_dict()
R["acceso"] = int(t.acceso.sum()); R["previsto"] = int(t.previsto.sum())
R["siti_unici_coordinate_tutti"] = int(t.sito_id.nunique())
R["siti_unici_coordinate_accesi"] = int(t[t.acceso].sito_id.nunique())
R["senza_coordinate"] = int(t.lon.isna().sum())
R["categoria"] = t.categoria.value_counts().to_dict()
R["categoria_accesi"] = t[t.acceso].categoria.value_counts().to_dict()
R["tipo"] = t.tipo.value_counts().to_dict()
R["tipo_per_categoria"] = pd.crosstab(t.categoria, t.tipo).to_dict("index")
R["procedura_scia"] = int(t.procedura_scia.sum())
R["segnalazioni_parere"] = t[t.segnalazione_parere != ""].segnalazione_parere.value_counts().to_dict()
R["segnalazioni_parere_elenco"] = t[t.segnalazione_parere.isin(["ultimo parere: non rispetto limiti", "ultimo parere negativo"])][
    ["id_impianto", "gruppo_gestore", "tipo", "stato", "indirizzo", "nil"]].fillna("").to_dict("records")
g = t.groupby("gruppo_gestore").agg(impianti=("id_impianto", "size"), accesi=("acceso", "sum"), previsti=("previsto", "sum"), scia=("procedura_scia", "sum"),
                                     siti=("sito_id", "nunique"), categoria=("categoria", "first")).sort_values("impianti", ascending=False)
g["quota_pct"] = (100 * g.impianti / len(t)).round(2)
g.to_csv(os.path.join(OUT, "gestori.csv"), sep=";", encoding="utf-8")
tp = pd.crosstab(t.gruppo_gestore.where(t.gruppo_gestore.isin(g.index[:9]), "altri"), t.tipo)
tp.to_csv(os.path.join(OUT, "gestori_per_tipo.csv"), sep=";", encoding="utf-8")
pw = pd.crosstab(t.tipo, t.potenza_classe_W.fillna("n.d."))
pw.to_csv(os.path.join(OUT, "tipo_per_potenza.csv"), sep=";", encoding="utf-8")
R["potenza_classi_telefonia"] = t[t.tipo == "Telefonia"].potenza_classe_W.fillna("n.d.").value_counts().to_dict()

# telefonia mobile = operatori mobili + societa infrastrutture, tipi Telefonia/Microcella (stima: il file non dice la tecnologia)
mob = t[(t.acceso) & (t.categoria.isin(["operatore mobile", "societa infrastrutture"])) & (t.tipo.isin(["Telefonia", "Microcella"]))].copy()
R["telefonia_mobile_accesi_impianti"] = len(mob)
R["telefonia_mobile_accesi_macro_Telefonia"] = int((mob.tipo == "Telefonia").sum())
R["telefonia_mobile_accesi_Microcella"] = int((mob.tipo == "Microcella").sum())
R["telefonia_mobile_siti_unici"] = int(mob.sito_id.nunique())
R["telefonia_mobile_macro_siti_unici"] = int(mob[mob.tipo == "Telefonia"].sito_id.nunique())
R["quota_microcelle_gestite_da_societa_infrastrutture_pct"] = round(100 * float(((mob.tipo == "Microcella") & (mob.categoria == "societa infrastrutture")).sum() / max(1, (mob.tipo == "Microcella").sum())), 1)
R["mobile_per_gestore_accesi"] = mob.gruppo_gestore.value_counts().to_dict()
# colocazione
c = t.dropna(subset=["sito_id"]).groupby("sito_id").size()
R["colocazione_distribuzione_impianti_per_sito"] = {"1": int((c == 1).sum()), "2": int((c == 2).sum()), "3-5": int(c.between(3, 5).sum()), "6-20": int(c.between(6, 20).sum()), ">20": int((c > 20).sum())}
R["colocazione_massimo"] = int(c.max())
top = t.dropna(subset=["sito_id"]).groupby("sito_id").agg(impianti=("id_impianto", "size"), indirizzo=("indirizzo", "first"), nil=("nil", "first"),
                                                         radio_tv=("categoria", lambda s: int((s == "radio e TV").sum())), mobile_infra=("categoria", lambda s: int(s.isin(["operatore mobile", "societa infrastrutture"]).sum())))
top = top.sort_values("impianti", ascending=False).head(25)
top.to_csv(os.path.join(OUT, "siti_piu_affollati.csv"), sep=";", encoding="utf-8")
macro = mob[mob.tipo == "Telefonia"].groupby("sito_id").size()
R["siti_macro_telefonia_con_n_operatori"] = macro.value_counts().sort_index().to_dict()

# ---------------- 2. per NIL
polys, ids, names = load_nil(P)
_, _, _, areas = assegna_nil([9.19], [45.46], polys, ids, names)
nil = pd.DataFrame({"id_nil": ids, "nil": names, "area_km2": areas})
d205 = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"), sep=None, engine="python")
d205 = d205[d205.NIL.notna()].copy(); d205["id_nil"] = d205.NIL.astype(int)
nil = nil.merge(d205[d205.Anno == 2024][["id_nil", "Totale"]].rename(columns={"Totale": "abitanti_2024"}), on="id_nil", how="left")
R["nil_area_totale_km2"] = round(nil.area_km2.sum(), 2); R["abitanti_2024"] = int(nil.abitanti_2024.sum())
a = t[t.acceso].dropna(subset=["id_nil"])
nil = nil.merge(a.groupby("id_nil").size().rename("impianti_accesi"), on="id_nil", how="left")
nil = nil.merge(a.groupby("id_nil").sito_id.nunique().rename("siti_accesi"), on="id_nil", how="left")
nil = nil.merge(mob.dropna(subset=["id_nil"]).groupby("id_nil").size().rename("mobile_impianti"), on="id_nil", how="left")
nil = nil.merge(mob[mob.tipo == "Telefonia"].dropna(subset=["id_nil"]).groupby("id_nil").sito_id.nunique().rename("mobile_macro_siti"), on="id_nil", how="left")
nil = nil.merge(mob[mob.tipo == "Microcella"].dropna(subset=["id_nil"]).groupby("id_nil").size().rename("microcelle"), on="id_nil", how="left")
nil = nil.merge(a[a.categoria == "radio e TV"].groupby("id_nil").size().rename("radio_tv_impianti"), on="id_nil", how="left")
nil = nil.merge(t[t.previsto].dropna(subset=["id_nil"]).groupby("id_nil").size().rename("previsti"), on="id_nil", how="left")
for c_ in ["impianti_accesi", "siti_accesi", "mobile_impianti", "mobile_macro_siti", "microcelle", "radio_tv_impianti", "previsti"]:
    nil[c_] = nil[c_].fillna(0).astype(int)
nil["impianti_accesi_per_km2"] = (nil.impianti_accesi / nil.area_km2).round(2)
nil["mobile_per_km2"] = (nil.mobile_impianti / nil.area_km2).round(2)
nil["mobile_per_1000_ab"] = (1000 * nil.mobile_impianti / nil.abitanti_2024.where(nil.abitanti_2024 > 0)).round(3)
nil["abitanti_sotto_1000"] = nil.abitanti_2024 < 1000
nil["macro_siti_per_km2"] = (nil.mobile_macro_siti / nil.area_km2).round(2)
nil["macro_siti_per_1000_ab"] = (1000 * nil.mobile_macro_siti / nil.abitanti_2024.where(nil.abitanti_2024 > 0)).round(3)
nil["abitanti_per_km2"] = (nil.abitanti_2024 / nil.area_km2).round(0)
nil.to_csv(os.path.join(OUT, "nil_antenne.csv"), sep=";", index=False, encoding="utf-8")
R["nil_con_zero_impianti_accesi"] = nil[nil.impianti_accesi == 0].nil.tolist()
R["citta_mobile_per_km2"] = round(len(mob.dropna(subset=["id_nil"])) / nil.area_km2.sum(), 2)
R["citta_mobile_per_1000_ab"] = round(1000 * len(mob.dropna(subset=["id_nil"])) / nil.abitanti_2024.sum(), 3)
R["citta_macro_siti_per_km2"] = round(mob[mob.tipo == "Telefonia"].dropna(subset=["id_nil"]).sito_id.nunique() / nil.area_km2.sum(), 2)
R["citta_macro_siti_per_1000_ab"] = round(1000 * mob[mob.tipo == "Telefonia"].dropna(subset=["id_nil"]).sito_id.nunique() / nil.abitanti_2024.sum(), 3)
R["nil_top10_mobile_per_km2"] = nil.sort_values("mobile_per_km2", ascending=False).head(10)[["nil", "mobile_impianti", "mobile_per_km2", "abitanti_2024"]].to_dict("records")
R["nil_bottom10_mobile_per_km2"] = nil[nil.mobile_impianti > 0].sort_values("mobile_per_km2").head(10)[["nil", "mobile_impianti", "mobile_per_km2", "abitanti_2024"]].to_dict("records")
big = nil[nil.abitanti_2024 >= 1000]
R["nil_con_meno_di_1000_abitanti"] = nil[nil.abitanti_2024 < 1000][["nil", "abitanti_2024", "mobile_impianti"]].to_dict("records")
R["nil_top10_mobile_per_1000_ab_(>=1000 ab)"] = big.sort_values("mobile_per_1000_ab", ascending=False).head(10)[["nil", "mobile_impianti", "mobile_per_1000_ab", "abitanti_2024"]].to_dict("records")
R["nil_bottom10_mobile_per_1000_ab_(>=1000 ab)"] = big.sort_values("mobile_per_1000_ab").head(10)[["nil", "mobile_impianti", "mobile_per_1000_ab", "abitanti_2024"]].to_dict("records")
R["nil_top10_radio_tv"] = nil.sort_values("radio_tv_impianti", ascending=False).head(6)[["nil", "radio_tv_impianti"]].to_dict("records")
R["nil_correlazione_mobile_vs_densita_abitanti_spearman"] = round(float(nil[["mobile_per_km2", "abitanti_per_km2"]].corr(method="spearman").iloc[0, 1]), 3)
R["nil_mediana_mobile_per_1000_ab"] = round(float(nil.mobile_per_1000_ab.median()), 3)
bz = big[big.mobile_per_1000_ab > 0]
R["nil_ratio_max_min_per_1000_ab_(>=1000 ab, esclusi_zero)"] = round(float(bz.mobile_per_1000_ab.max() / bz.mobile_per_1000_ab.min()), 1)
R["nil_mediana_mobile_per_km2"] = round(float(nil.mobile_per_km2.median()), 2)
# per gestore x NIL (accesi, mobile)
mn = mob.dropna(subset=["id_nil"]).groupby(["nil", "gruppo_gestore"]).size().unstack(fill_value=0)
mn.to_csv(os.path.join(OUT, "nil_per_gestore.csv"), sep=";", encoding="utf-8")
# per municipio (dal NIL)
R["per_municipio_mobile_accesi"] = mob.groupby("municipio_file").size().to_dict()

# ---------------- 3. serie storica (snapshot)
rows = []
for s, x in S.groupby("snapshot"):
    xa = x[x.acceso]
    xm = x[x.acceso & x.categoria.isin(["operatore mobile", "societa infrastrutture"]) & x.tipo.isin(["Telefonia", "Microcella"])]
    rows.append({"snapshot": s, "data_copia": x.data_copia.iloc[0], "righe": len(x), "accesi": len(xa), "previsti": int(x.previsto.sum()), "scia": int(x.procedura_scia.sum()),
                 "scia_su_accesi_pct": round(100 * xa.procedura_scia.mean(), 1),
                 "telefonia_mobile_accesi": len(xm), "macro_Telefonia": int((xm.tipo == "Telefonia").sum()), "Microcella": int((xm.tipo == "Microcella").sum()),
                 "Ponte": int((xa.tipo == "Ponte").sum()), "radio_tv": int((xa.categoria == "radio e TV").sum()),
                 "siti_unici_mobile": xm.assign(k=xm.lon.astype(str) + xm.lat.astype(str)).k.nunique()})
ser = pd.DataFrame(rows)
ser.to_csv(os.path.join(OUT, "serie_snapshot.csv"), sep=";", index=False, encoding="utf-8")
gs = S[S.acceso & S.categoria.isin(["operatore mobile", "societa infrastrutture"]) & S.tipo.isin(["Telefonia", "Microcella"])].groupby(["snapshot", "gruppo_gestore"]).size().unstack(fill_value=0)
gs.to_csv(os.path.join(OUT, "serie_snapshot_gestori_mobile.csv"), sep=";", encoding="utf-8")
R["serie_snapshot"] = ser.to_dict("records")
R["serie_gestori_mobile"] = gs.to_dict("index")

# flussi tra snapshot consecutivi con codice impianto (2023-01 -> 2024-05 -> 2024-06 -> 2025-06)
fl = []
order = ["2023-01", "2024-05", "2024-06", "2025-06"]
for a_, b_ in zip(order[:-1], order[1:]):
    xa_, xb_ = S[S.snapshot == a_].set_index("id_impianto"), S[S.snapshot == b_].set_index("id_impianto")
    nuovi = xb_.index.difference(xa_.index); persi = xa_.index.difference(xb_.index); comuni = xa_.index.intersection(xb_.index)
    cambi_stato = int((xa_.loc[comuni].stato != xb_.loc[comuni].stato).sum())
    nb = xb_.loc[nuovi]
    fl.append({"da": a_, "a": b_, "nuovi_id": len(nuovi), "id_spariti": len(persi), "id_in_comune": len(comuni), "cambi_di_stato": cambi_stato,
               "nuovi_per_categoria": nb.categoria.value_counts().to_dict(), "nuovi_per_tipo": nb.tipo.value_counts().to_dict(), "nuovi_per_gestore": nb.gruppo_gestore.value_counts().head(8).to_dict(),
               "spariti_per_gestore": xa_.loc[persi].gruppo_gestore.value_counts().head(8).to_dict()})
R["flussi_con_id"] = fl
# transizione stato Previsto -> Acceso
xa_, xb_ = S[S.snapshot == "2023-01"].set_index("id_impianto"), S[S.snapshot == "2025-06"].set_index("id_impianto")
cm = xa_.index.intersection(xb_.index)
R["prev2023_nel_2025"] = pd.crosstab(xa_.loc[cm].stato.str.slice(0, 18), xb_.loc[cm].stato.str.slice(0, 18)).to_dict("index")
R["id_2023_ancora_nel_2025"] = int(len(cm)); R["id_2023_totale"] = int(len(xa_)); R["id_2023_non_piu_nel_2025"] = int(len(xa_.index.difference(xb_.index)))
# confronto approssimato 2020-21 -> 2023-01 (senza codice): chiave gruppo+tipo+coordinate a 4 decimali (~10 m), conteggio per multiinsieme
def key(x):
    return (x.gruppo_gestore + "|" + x.tipo + "|" + x.lon.astype(float).round(4).astype(str) + "|" + x.lat.astype(float).round(4).astype(str))
k0 = key(S[S.snapshot == "2020-21"]).value_counts(); k1 = key(S[S.snapshot == "2023-01"]).value_counts()
com = pd.concat([k0, k1], axis=1, keys=["a", "b"]).fillna(0)
R["approx_2020_2023"] = {"righe_2020": int(com.a.sum()), "righe_2023": int(com.b.sum()), "corrispondenti": int(np.minimum(com.a, com.b).sum()),
                         "nuove_in_2023": int((com.b - np.minimum(com.a, com.b)).sum()), "sparite_dal_2020": int((com.a - np.minimum(com.a, com.b)).sum())}
# nuove 2023 per gruppo/tipo (approssimato)
nuove = (com.b - np.minimum(com.a, com.b)); nuove = nuove[nuove > 0]
nn_ = pd.DataFrame({"k": nuove.index, "n": nuove.values}); nn_["gruppo"] = nn_.k.str.split("|").str[0]; nn_["tipo"] = nn_.k.str.split("|").str[1]
R["approx_nuove_2023_per_gruppo"] = nn_.groupby("gruppo").n.sum().sort_values(ascending=False).head(8).astype(int).to_dict()
R["approx_nuove_2023_per_tipo"] = nn_.groupby("tipo").n.sum().astype(int).to_dict()
sp = (com.a - np.minimum(com.a, com.b)); sp = sp[sp > 0]
ss_ = pd.DataFrame({"k": sp.index, "n": sp.values}); ss_["gruppo"] = ss_.k.str.split("|").str[0]
R["approx_sparite_2020_per_gruppo"] = ss_.groupby("gruppo").n.sum().sort_values(ascending=False).head(8).astype(int).to_dict()
# NIL: crescita 2020-21 vs 2025 (impianti mobili accesi) -- usa NIL da coordinate
def nil_of(x):
    xx = x.dropna(subset=["lon", "lat"]).copy()
    xx["lon"] = xx.lon.astype(float); xx["lat"] = xx.lat.astype(float)
    ni, nn2, _, _ = assegna_nil(xx.lon.values, xx.lat.values, polys, ids, names)
    xx["id_nil"] = ni
    return xx
def mobq(x):
    return x[x.acceso & x.categoria.isin(["operatore mobile", "societa infrastrutture"]) & x.tipo.isin(["Telefonia", "Microcella"])]
x20 = mobq(nil_of(S[S.snapshot == "2020-21"])); x25 = mobq(nil_of(S[S.snapshot == "2025-06"]))
cr = pd.DataFrame({"mobile_2020_21": x20.groupby("id_nil").size(), "mobile_2025": x25.groupby("id_nil").size()}).fillna(0).astype(int)
cr = cr.reset_index().merge(nil[["id_nil", "nil", "area_km2", "abitanti_2024"]], on="id_nil", how="right").fillna(0)
cr["variazione"] = cr.mobile_2025 - cr.mobile_2020_21
cr["variazione_pct"] = np.where(cr.mobile_2020_21 > 0, (100 * cr.variazione / cr.mobile_2020_21).round(1), np.nan)
cr.to_csv(os.path.join(OUT, "nil_crescita_2020_2025.csv"), sep=";", index=False, encoding="utf-8")
R["crescita_nil_top5_assoluta"] = cr.sort_values("variazione", ascending=False).head(5)[["nil", "mobile_2020_21", "mobile_2025", "variazione"]].to_dict("records")
R["crescita_nil_con_calo"] = int((cr.variazione < 0).sum())
R["crescita_nil_bottom5"] = cr.sort_values("variazione").head(5)[["nil", "mobile_2020_21", "mobile_2025", "variazione"]].to_dict("records")

# ---------------- 4. scuole (solo confronto di posizione)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def xy(lon, lat):
    X, Y = tr.transform(np.asarray(lon, float), np.asarray(lat, float)); return np.column_stack([X, Y])
cs = pd.read_csv(os.path.join(P, "scuole", "pulito", "comune_scuole_anagrafica.csv"), sep=";", dtype=str)
cs = cs[cs.ultimo_anno == "2024"].dropna(subset=["lon", "lat"])
cs = cs.assign(fonte="Comune ANASCO 2024/25", denominazione=cs.denominazione)[["ordine", "gestione", "denominazione", "indirizzo", "lon", "lat", "nil", "fonte"]]
ms = pd.read_csv(os.path.join(P, "scuole", "pulito", "miur_scuole_anagrafica.csv"), sep=";", dtype=str)
ms = ms[(ms.ordine == "sec2")].dropna(subset=["lon", "lat"])
ms = pd.DataFrame({"ordine": "sec2", "gestione": ms.tipo, "denominazione": ms.codice_mecc, "indirizzo": ms.indirizzo, "lon": ms.lon, "lat": ms.lat, "nil": ms.nil, "fonte": "MIM anagrafe (coordinate dal filone scuole)"})
sc = pd.concat([cs, ms], ignore_index=True)
sc["lon"] = sc.lon.astype(float); sc["lat"] = sc.lat.astype(float)
R["scuole_con_coordinate"] = len(sc); R["scuole_per_ordine"] = sc.ordine.value_counts().to_dict()
M = mob.dropna(subset=["lon", "lat"])
M_macro = M[M.tipo == "Telefonia"]
def dist_stats(pts_xy, ants):
    tree = cKDTree(xy(ants.lon, ants.lat))
    dmin, _ = tree.query(pts_xy)
    n100 = np.array([len(x) for x in tree.query_ball_point(pts_xy, 100)])
    n200 = np.array([len(x) for x in tree.query_ball_point(pts_xy, 200)])
    return dmin, n100, n200
pxy = xy(sc.lon, sc.lat)
sc["dist_min_m_telefonia_mobile"], sc["n_entro_100m"], sc["n_entro_200m"] = dist_stats(pxy, M)
sc["dist_min_m_macro"], sc["macro_entro_100m"], sc["macro_entro_200m"] = dist_stats(pxy, M_macro)
sc.round(1).to_csv(os.path.join(OUT, "scuole_vicinanza_antenne.csv"), sep=";", index=False, encoding="utf-8")
civ = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["RESIDENZIALE", "lon", "lat"])
civ = civ[civ.RESIDENZIALE == 1.0].dropna()
cxy = xy(civ.lon, civ.lat)
cd, c100, c200 = dist_stats(cxy, M)
cdm, c100m, c200m = dist_stats(cxy, M_macro)
def summ(dmin, n100, n200):
    return {"n": int(len(dmin)), "mediana_dist_m": round(float(np.median(dmin)), 0), "entro_50m_pct": round(100 * float((dmin <= 50).mean()), 1),
            "entro_100m_pct": round(100 * float((dmin <= 100).mean()), 1), "entro_200m_pct": round(100 * float((dmin <= 200).mean()), 1),
            "media_antenne_entro_100m": round(float(n100.mean()), 2), "media_antenne_entro_200m": round(float(n200.mean()), 2)}
R["scuole_vs_civici_residenziali_telefonia_mobile"] = {"scuole": summ(sc.dist_min_m_telefonia_mobile.values, sc.n_entro_100m.values, sc.n_entro_200m.values), "civici_residenziali": summ(cd, c100, c200)}
R["scuole_vs_civici_residenziali_solo_macro"] = {"scuole": summ(sc.dist_min_m_macro.values, sc.macro_entro_100m.values, sc.macro_entro_200m.values), "civici_residenziali": summ(cdm, c100m, c200m)}
R["scuole_per_ordine_entro_100m_pct"] = (sc.groupby("ordine").apply(lambda x: round(100 * float((x.dist_min_m_telefonia_mobile <= 100).mean()), 1))).to_dict()
R["scuole_entro_50m_n"] = int((sc.dist_min_m_telefonia_mobile <= 50).sum())
R["scuole_entro_100m_n"] = int((sc.dist_min_m_telefonia_mobile <= 100).sum())
R["scuole_entro_20m_n"] = int((sc.dist_min_m_telefonia_mobile <= 20).sum())
# per NIL: quota scuole entro 100 m
scn = sc.dropna(subset=["nil"]).groupby("nil").apply(lambda x: pd.Series({"scuole": len(x), "entro100_n": int((x.dist_min_m_telefonia_mobile <= 100).sum())}))
scn["entro100_pct"] = (100 * scn.entro100_n / scn.scuole).round(1)
scn.to_csv(os.path.join(OUT, "scuole_antenne_per_nil.csv"), sep=";", encoding="utf-8")
# test di casualita': spostamento casuale dei punti scuola entro l'edificato residenziale (stesse dimensioni) - distribuzioni
rng = np.random.default_rng(42)
sel = rng.choice(len(civ), size=(1000, len(sc)))
quota100 = []
tree_m = cKDTree(xy(M.lon, M.lat))
dd_all, _ = tree_m.query(cxy)
for k in range(1000):
    quota100.append((dd_all[sel[k]] <= 100).mean() * 100)
R["scuole_entro_100m_pct_osservato"] = round(100 * float((sc.dist_min_m_telefonia_mobile <= 100).mean()), 1)
R["campioni_casuali_di_civici_entro_100m_pct"] = {"p2.5": round(float(np.percentile(quota100, 2.5)), 1), "mediana": round(float(np.percentile(quota100, 50)), 1), "p97.5": round(float(np.percentile(quota100, 97.5)), 1)}

json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
