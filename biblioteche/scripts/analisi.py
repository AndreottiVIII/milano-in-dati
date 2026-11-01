"""Fase 1 - riepiloghi (numeri citati nella NOTE.md). Legge le tabelle di pulito/ e scrive riepilogo.json + nil_biblioteche.csv, catchment_biblioteche.csv,
mesi_chiusi_biblioteca_anno.csv, prestiti_biblioteca_anno_ranking.csv, ripresa_mensile_vs_2019.csv.
Uso: python -I -X utf8 analisi.py <biblioteche_abs> <milano_in_dati_abs>"""
import sys, os, json
import numpy as np, pandas as pd
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import rd
B, P = sys.argv[1], sys.argv[2]; O = os.path.join(B, "pulito")
R = {}
rc = lambda name, **kw: pd.read_csv(os.path.join(O, name), sep=";", **kw)

# ---- popolazione (ds205 Comune di Milano, campo Totale)
pop = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"), sep=None, engine="python")
pop_anno = pop.groupby("Anno").Totale.sum()
R["abitanti_ds205_totale"] = {int(k): int(v) for k, v in pop_anno.items()}

# ---- 1. totali per anno (ds2986)
at = rc("prestiti_anno_totale.csv")
at = at.set_index("anno")
tot = at.prestiti
ab = pop_anno.reindex(at.index).ffill()      # 2025 e 2026: uso 2024 (ultimo dato)
R["totali_anno_ds2986"] = {int(k): int(v) for k, v in tot.items()}
R["prestiti_per_abitante"] = {int(k): round(float(tot[k] / ab[k]), 3) for k in tot.index if k <= 2025}
R["abitanti_usati_per_2025"] = "2024 (ultimo anno ds205)"
R["rapporto_a_2019"] = {int(k): round(float(tot[k] / tot[2019]), 4) for k in tot.index if k <= 2025}
R["calo_2013_2018_pct"] = round(float((tot[2018] / tot[2013] - 1) * 100), 1)
R["calo_2013_2019_pct"] = round(float((tot[2019] / tot[2013] - 1) * 100), 1)
R["var_2019_su_2018_pct"] = round(float((tot[2019] / tot[2018] - 1) * 100), 1)
R["calo_2020_su_2019_pct"] = round(float((tot[2020] / tot[2019] - 1) * 100), 1)
R["var_2025_su_2019_pct"] = round(float((tot[2025] / tot[2019] - 1) * 100), 1)
R["var_2025_su_2013_pct"] = round(float((tot[2025] / tot[2013] - 1) * 100), 1)
s = rc("prestiti_mese_punto_eta.csv")
m = s.groupby(["anno", "mese"]).prestiti.sum().unstack(0)
rip = (m.div(m[2019], axis=0) * 100).round(1)
rip.to_csv(os.path.join(O, "ripresa_mensile_vs_2019.csv"), sep=";")
R["mesi_piu_bassi_2020"] = {int(mm): int(m.loc[mm, 2020]) for mm in [3, 4, 5, 11]}
R["gen_apr_2026"] = int(m.loc[1:4, 2026].sum()); R["gen_apr_2025"] = int(m.loc[1:4, 2025].sum()); R["gen_apr_2019"] = int(m.loc[1:4, 2019].sum())
R["gen_apr_2026_su_2019_pct"] = round(float((R["gen_apr_2026"] / R["gen_apr_2019"] - 1) * 100), 1)
R["maggio_2026_parziale"] = int(m.loc[5, 2026])
R["anni_sopra_2019_mesi"] = [f"{a}-{mm:02d}" for a in range(2021, 2026) for mm in range(1, 13) if m.loc[mm, a] >= m.loc[mm, 2019]]
R["tipologie_punti_totale_ds2986"] = s.groupby("tipo_punto").prestiti.sum().astype(int).to_dict()

# ---- 2. biblioteche: ranking, mesi chiusi
ap = rc("prestiti_anno_punto.csv")
bib = s[s.tipo_punto == "biblioteca"].copy()
bib["ym"] = bib.anno * 100 + bib.mese
mm = bib.groupby(["biblioteca", "ym"]).prestiti.sum().unstack(0).fillna(0)
ref = mm.loc[(mm.index >= 202401) & (mm.index <= 202512)].median()            # livello 'normale' di ogni biblioteca: mediana mensile 2024-2025
closed = (mm < 0.25 * ref)
cl = closed.groupby(mm.index // 100).sum().T
cl.index.name = "biblioteca"
cl.to_csv(os.path.join(O, "mesi_chiusi_biblioteca_anno.csv"), sep=";")
cm_year = closed.groupby(mm.index // 100).sum().sum(axis=1)
R["mesi_biblioteca_a_meno_del_25pct_del_normale_per_anno"] = {int(k): int(v) for k, v in cm_year.items()}   # 25 biblioteche x 12 = 300 al massimo (2026: 5 mesi)
R["definizione_mesi_chiusi"] = "mese-biblioteca con prestiti < 25% della mediana mensile 2024-2025 della stessa biblioteca (include chiusure per lavori, Covid, orari ridotti)"
rk = ap[ap.tipo_punto == "biblioteca"].pivot_table(index="biblioteca", columns="anno", values="prestiti", aggfunc="sum")
rk["var_2025_su_2019_pct"] = (rk[2025] / rk[2019] - 1) * 100
rk["var_2019_su_2013_pct"] = (rk[2019] / rk[2013] - 1) * 100
rk["mesi_chiusi_2019"] = cl[2019]; rk["mesi_chiusi_2025"] = cl[2025]
rk["quota_2025_pct"] = rk[2025] / rk[2025].sum() * 100
rk.round(1).sort_values(2025, ascending=False).to_csv(os.path.join(O, "prestiti_biblioteca_anno_ranking.csv"), sep=";")
R["classifica_2025"] = rk[2025].sort_values(ascending=False).astype(int).to_dict()
R["prime_3_quota_2025_pct"] = round(float(rk[2025].nlargest(3).sum() / rk[2025].sum() * 100), 1)
R["ultime_3_2025"] = rk[2025].nsmallest(3).astype(int).to_dict()
R["rapporto_prima_ultima_2025"] = round(float(rk[2025].max() / rk[2025].min()), 1)
R["bibliobus"] = ap[ap.tipo_punto == "bibliobus"].set_index("anno").prestiti.astype(int).to_dict()
R["smartlocker_edicole_librerie_altro"] = ap[ap.tipo_punto.isin(["smartlocker", "edicola", "libreria", "altro"])].groupby(["anno", "tipo_punto"]).prestiti.sum().unstack().fillna(0).astype(int).to_dict()

# ---- 3. classi di eta' e genere
e = rc("prestiti_anno_eta.csv").pivot_table(index="anno", columns="eta_classe", values="prestiti", aggfunc="sum")
e["65+"] = e[["65-84", "85+"]].sum(axis=1); e["0-17"] = e[["0-2", "3-5", "6-10", "11-13", "14-17"]].sum(axis=1); e["tot"] = e.drop(columns=["65+", "0-17"]).sum(axis=1)
R["quota_65piu_pct"] = {int(k): round(float(v), 1) for k, v in (e["65+"] / e.tot * 100).items()}
R["quota_0_17_pct"] = {int(k): round(float(v), 1) for k, v in (e["0-17"] / e.tot * 100).items()}
R["prestiti_0_17"] = {int(k): int(v) for k, v in e["0-17"].items()}
R["prestiti_65piu"] = {int(k): int(v) for k, v in e["65+"].items()}
g = rc("dettaglio_anno_eta_genere.csv")
gp = g.groupby(["anno", "genere"]).n.sum().unstack()
R["quota_donne_pct"] = {int(k): round(float(v), 1) for k, v in (gp["F"] / gp.sum(axis=1) * 100).items()}

# ---- 4. libri contro non-libri (campo media del dettaglio; 'LIBRI E AUDIOLIBRI' esclude i periodici, contati dal 2018) 
cubo = pd.read_parquet(os.path.join(O, "cubo_prestiti_completo.parquet"))
cv = cubo[(cubo.stato != "Annullato") & (cubo.tipo != "Consultazione")].copy()
cv["anno"] = cv.mese_inizio.str[:4].astype(int); cv["mese"] = cv.mese_inizio.str[5:7].astype(int)
x = cv.groupby(["anno", "media"]).n.sum().unstack().fillna(0)
nb = x["NBN - NON BOOK MATERIAL"]; lb = x["LIBRI E AUDIOLIBRI"]; tv = x.sum(axis=1)
R["libri_audiolibri_per_anno"] = {int(k): int(v) for k, v in lb.items()}
R["non_book_dvd_cd_per_anno"] = {int(k): int(v) for k, v in nb.items()}
R["prestiti_validi_dettaglio_per_anno"] = {int(k): int(v) for k, v in tv.items()}
R["quota_libri_pct"] = {int(k): round(float(v), 1) for k, v in (lb / tv * 100).items()}
R["libri_2023_su_2019_pct"] = round(float((lb[2023] / lb[2019] - 1) * 100), 1); R["libri_2023_su_2013_pct"] = round(float((lb[2023] / lb[2013] - 1) * 100), 1)
R["non_book_2023_su_2013_pct"] = round(float((nb[2023] / nb[2013] - 1) * 100), 1)
R["calo_totale_2013_2023"] = int(tv[2013] - tv[2023]); R["calo_non_book_2013_2023"] = int(nb[2013] - nb[2023]); R["calo_libri_2013_2023"] = int(lb[2013] - lb[2023])
R["calo_totale_2013_2019"] = int(tv[2013] - tv[2019]); R["calo_non_book_2013_2019"] = int(nb[2013] - nb[2019]); R["calo_libri_2013_2019"] = int(lb[2013] - lb[2019])
h1 = cv[cv.mese <= 6].groupby(["anno", "media"]).n.sum().unstack().fillna(0)
R["libri_gen_giu"] = {int(k): int(v) for k, v in h1["LIBRI E AUDIOLIBRI"].items()}
R["non_book_gen_giu"] = {int(k): int(v) for k, v in h1["NBN - NON BOOK MATERIAL"].items()}
R["libri_gen_giu_2024_su_2023_pct"] = round(float((h1.loc[2024, "LIBRI E AUDIOLIBRI"] / h1.loc[2023, "LIBRI E AUDIOLIBRI"] - 1) * 100), 1)
R["libri_gen_giu_2024_su_2019_pct"] = round(float((h1.loc[2024, "LIBRI E AUDIOLIBRI"] / h1.loc[2019, "LIBRI E AUDIOLIBRI"] - 1) * 100), 1)
R["libri_gen_giu_2024_su_2013_pct"] = round(float((h1.loc[2024, "LIBRI E AUDIOLIBRI"] / h1.loc[2013, "LIBRI E AUDIOLIBRI"] - 1) * 100), 1)
R["non_book_gen_giu_2024_su_2013_pct"] = round(float((h1.loc[2024, "NBN - NON BOOK MATERIAL"] / h1.loc[2013, "NBN - NON BOOK MATERIAL"] - 1) * 100), 1)
R["totale_dettaglio_gen_giu_2024_su_2013_pct"] = round(float((h1.loc[2024].sum() / h1.loc[2013].sum() - 1) * 100), 1)
R["nota_periodici"] = "i periodici compaiono nel dettaglio solo dal 2018 (media PERIODICO): per confronti nel tempo uso LIBRI E AUDIOLIBRI e NON BOOK"

# ---- 5. prestiti di libri di altre biblioteche (proprietaria != ritiro), da 2017
t = rc("dettaglio_anno_ritiro_proprietaria.csv")
t["diversa"] = t.ritiro != t.proprietaria
z = t.groupby(["anno", "diversa"]).n.sum().unstack().fillna(0)
R["quota_prestiti_di_altra_biblioteca_pct"] = {int(k): round(float(v), 1) for k, v in (z[True] / z.sum(axis=1) * 100).items()}
# 2023: quanto sono 'locali' i prestiti di ogni biblioteca (quota di volumi propri)
t23 = t[t.anno == 2023].groupby(["ritiro"]).apply(lambda d: pd.Series({"prestiti": d.n.sum(), "quota_volumi_propri": d.loc[~d.diversa, "n"].sum() / d.n.sum()}), include_groups=False)
t23[t23.prestiti > 5000].round(3).to_csv(os.path.join(O, "quota_volumi_propri_2023.csv"), sep=";")

# ---- 6. dati annuali Comune (iscritti): confronto con prestiti
st = rc("statistiche_annuali_biblioteca.csv")
isc = st[~st.biblioteca.isin(["Deposito Interbibliotecario", "Fondo Storico Ragazzi", "Bibliotecainattesa", "Deposito Boifava", "Deposito Deledda", "Centro Servizi", "Servizi Locali",
                              "Remote Library", "Ledha", "Mudec", "Edicole", "Librerie"]) & ~st.biblioteca.str.contains("Smartlocker")].groupby("anno").iscritti_totale.sum()
R["iscritti_totale_somma_biblioteche_stat_annuali"] = {int(k): int(v) for k, v in isc.items()}
R["nota_iscritti"] = "somma di 'iscritti' (adulti+ragazzi) delle biblioteche nei file annuali del Comune: 2013-2016 e 2019-2023; 2017-2018 inutilizzabili (colonne sfalsate in ds909)"

# ---- 7. NIL: biblioteche per NIL, prestiti 2025, abitanti; catchment per vicinanza
pt = rc("punti_prestito.csv")
phys = pt[(pt.tipo_punto == "biblioteca") & (pt.stato == "Attivo") & ~pt.denominazione.str.contains("FONDAZIONE|Gianni Mura|WOW|LEDHA|CLUSTER", case=False)]
phys = phys[phys.biblioteca.isin(rk.index)].drop_duplicates("biblioteca")
nilp = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm_4326.csv"), sep=";")
pa = pop[pop.Anno == 2024].groupby("NIL").Totale.sum(); pb = pop[pop.Anno == 2019].groupby("NIL").Totale.sum()
nilp["abitanti_2024"] = nilp.ID_NIL.map(pa); nilp["abitanti_2019"] = nilp.ID_NIL.map(pb)
nilp = nilp.rename(columns={"NIL": "nil"})
pr25 = rk[2025]; pr19 = rk[2019]
out = nilp[["ID_NIL", "nil", "abitanti_2019", "abitanti_2024", "LONG_X_4326_CENTROID", "LAT_Y_4326_CENTROID"]].copy()
grp = phys.groupby("id_nil")
out["n_biblioteche"] = out.ID_NIL.map(grp.size()).fillna(0).astype(int)
out["biblioteche"] = out.ID_NIL.map(grp.biblioteca.apply(lambda v: ", ".join(v))).fillna("")
out["prestiti_2025_biblioteche_nel_nil"] = out.ID_NIL.map(grp.biblioteca.apply(lambda v: pr25[list(v)].sum())).fillna(0).astype(int)
out["prestiti_2019_biblioteche_nel_nil"] = out.ID_NIL.map(grp.biblioteca.apply(lambda v: pr19[list(v)].sum())).fillna(0).astype(int)
out["prestiti_per_1000_ab_2025_nil_ospitante"] = np.where(out.abitanti_2024 >= 5000, out.prestiti_2025_biblioteche_nel_nil / out.abitanti_2024 * 1000, np.nan).round(0)
# catchment: ogni NIL assegnato alla biblioteca piu' vicina (distanza centroide NIL - biblioteca, UTM 32N); esclusi Sormani/Lambrate? no: incluse tutte le biblioteche di quartiere + Sormani
tr = Transformer.from_crs(4326, 32632, always_xy=True)
bx, by = tr.transform(phys.lon.values, phys.lat.values); nx, ny = tr.transform(out.LONG_X_4326_CENTROID.values, out.LAT_Y_4326_CENTROID.values)
d = np.sqrt((np.array(nx)[:, None] - np.array(bx)[None, :]) ** 2 + (np.array(ny)[:, None] - np.array(by)[None, :]) ** 2)
j = d.argmin(axis=1)
out["biblioteca_piu_vicina"] = phys.biblioteca.values[j]; out["distanza_centroide_m"] = d.min(axis=1).round(0)
out.drop(columns=["LONG_X_4326_CENTROID", "LAT_Y_4326_CENTROID"]).to_csv(os.path.join(O, "nil_biblioteche.csv"), sep=";", index=False)
cat = out.groupby("biblioteca_piu_vicina").agg(nil_assegnati=("nil", lambda v: "; ".join(v)), n_nil=("nil", "size"), abitanti_2024=("abitanti_2024", "sum"), abitanti_2019=("abitanti_2019", "sum")).reset_index().rename(columns={"biblioteca_piu_vicina": "biblioteca"})
cat["prestiti_2025"] = cat.biblioteca.map(pr25); cat["prestiti_2019"] = cat.biblioteca.map(pr19)
cat["prestiti_per_1000_ab_2025"] = (cat.prestiti_2025 / cat.abitanti_2024 * 1000).round(0)
cat["prestiti_per_1000_ab_2019"] = (cat.prestiti_2019 / cat.abitanti_2019 * 1000).round(0)
cat = cat.sort_values("prestiti_per_1000_ab_2025", ascending=False)
cat.to_csv(os.path.join(O, "catchment_biblioteche.csv"), sep=";", index=False)
R["biblioteche_senza_nil_assegnati"] = [b for b in phys.biblioteca if b not in set(cat.biblioteca)]
R["catchment_prestiti_per_1000_ab_2025"] = cat.set_index("biblioteca").prestiti_per_1000_ab_2025.to_dict()
R["nil_senza_biblioteca"] = int((out.n_biblioteche == 0).sum()); R["nil_totale"] = int(len(out))
R["nil_con_piu_biblioteche"] = out[out.n_biblioteche > 1][["nil", "n_biblioteche"]].values.tolist()
v = out[out.prestiti_per_1000_ab_2025_nil_ospitante.notna() & (out.n_biblioteche > 0)]
R["nil_ospitante_prestiti_per_1000_ab_2025_max"] = v.nlargest(5, "prestiti_per_1000_ab_2025_nil_ospitante")[["nil", "prestiti_per_1000_ab_2025_nil_ospitante"]].values.tolist()
R["nil_ospitante_prestiti_per_1000_ab_2025_min"] = v.nsmallest(5, "prestiti_per_1000_ab_2025_nil_ospitante")[["nil", "prestiti_per_1000_ab_2025_nil_ospitante"]].values.tolist()
R["totale_prestiti_biblioteche_2025_in_nil"] = int(out.prestiti_2025_biblioteche_nel_nil.sum())
from scipy.stats import spearmanr
rho = spearmanr(cat.prestiti_per_1000_ab_2025, cat.abitanti_2024)
R["catchment_spearman_prestiti_per_ab_vs_abitanti"] = [round(float(rho.statistic), 2), round(float(rho.pvalue), 3)]

# ---- 8. serie lunga 2007-2011 (solo biblioteche rionali, Sormani escluso)
sl = rc("serie_lunga_rionali_2007_2011.csv")
R["rionali_2007_2008_2011_prestiti"] = sl.groupby("Anno").NumPrestiti.sum().astype(int).to_dict()
R["rionali_2007_2008_2011_quota_libri_pct"] = (sl[sl.Materiale == "Libri"].groupby("Anno").NumPrestiti.sum() / sl.groupby("Anno").NumPrestiti.sum() * 100).round(1).to_dict()
ns = rc("narrativa_saggistica.csv")
q = ns.groupby(["Anno", "Genere"]).prestiti.sum().unstack().fillna(0)
R["narrativa_saggistica_2011_2016"] = {int(a): {k: int(v) for k, v in r.items()} for a, r in q.iterrows()}

# ---- 8b. Sormani 2011: dove abitano gli utenti (ds101, solo libri)
so = rd(os.path.join(B, "raw", "comune_ds101", "ds101_cultura_bilioteche_sormani_prestiti_utenti_2011.csv"))
gr = so.groupby("Residenza").PrestitiLibri.sum()
R["sormani_2011_prestiti_libri_per_residenza"] = {k: int(v) for k, v in gr.items()}
R["sormani_2011_quota_fuori_milano_pct"] = round(float(gr["Fuori Milano"] / gr.sum() * 100), 1)
zz = so[so.Residenza == "Milano"].groupby("ZonaDec_Res").PrestitiLibri.sum()
R["sormani_2011_quota_per_municipio_residenza_pct"] = {int(k): round(float(v), 1) for k, v in (zz / zz.sum() * 100).items()}
so.groupby(["Residenza", "ZonaDec_Res"], dropna=False).PrestitiLibri.sum().reset_index().to_csv(os.path.join(O, "sormani_2011_residenza_utenti.csv"), sep=";", index=False)

# ---- 9. libri: sintesi
c = rc("concentrazione_titoli_anno.csv").set_index("anno"); tr_ = rc("traduzioni_anno.csv").set_index("anno"); fr = rc("freschezza_libri_anno.csv").set_index("anno")
R["libri_titoli_distinti"] = c.titoli_distinti.to_dict(); R["libri_quota_primi_100_titoli_pct"] = (c.quota_primi_100 * 100).round(1).to_dict()
R["libri_prestiti_primo_titolo"] = c.prestiti_primo.to_dict(); R["libri_quota_tradotti_pct"] = (tr_.quota_prestiti_tradotti * 100).round(1).to_dict()
R["libri_tradotti_tra_primi_100"] = tr_.tradotti_tra_i_primi_100.to_dict()
R["libri_quota_ultimi_2_anni_pct"] = (fr.quota_uscito_nell_anno_o_precedente * 100).round(1).to_dict(); R["libri_mediana_eta"] = fr.mediana_eta_libro.to_dict()
json.dump(R, open(os.path.join(O, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str)[:12000])
