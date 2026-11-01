"""Fase 2 - dati AGGREGATI per la pagina docs/biblioteche/ (Comune di Milano, CC BY). Nessuna riga di prestito, nessun dato personale.
Uso: python -I -X utf8 pagina.py <biblioteche_abs> <docs_biblioteche_abs>
Legge pulito/ (prodotto dai programmi di fase 1) e scrive <docs_biblioteche>/data/: riepilogo.json (tutti i numeri della pagina) e csv scaricabili.
Rilanciabile: sovrascrive i file."""
import sys, os, json
import numpy as np, pandas as pd
B, DOCS = sys.argv[1], sys.argv[2]
O = os.path.join(B, "pulito"); D = os.path.join(DOCS, "data")
os.makedirs(D, exist_ok=True)
rc = lambda n, **k: pd.read_csv(os.path.join(O, n), sep=";", **k)
R = json.load(open(os.path.join(O, "riepilogo.json"), encoding="utf-8"))
I = lambda x: int(x)
out = {"scaricato": "2026-11-01"}

# ---- totali annui (ds2986) e per abitante
out["totali"] = {k: I(v) for k, v in R["totali_anno_ds2986"].items()}
out["per_abitante"] = R["prestiti_per_abitante"]
out["rapporto_2019"] = R["rapporto_a_2019"]
for k in ["calo_2013_2018_pct", "var_2019_su_2018_pct", "calo_2020_su_2019_pct", "var_2025_su_2019_pct", "var_2025_su_2013_pct", "gen_apr_2026", "gen_apr_2019", "gen_apr_2026_su_2019_pct", "maggio_2026_parziale", "mesi_piu_bassi_2020"]:
    out[k] = R[k]
out["mesi_sopra_2019"] = len(R["anni_sopra_2019_mesi"])

# ---- libri contro non libri (dettaglio, prestiti validi)
for k in ["libri_audiolibri_per_anno", "non_book_dvd_cd_per_anno", "prestiti_validi_dettaglio_per_anno", "quota_libri_pct", "libri_2023_su_2019_pct", "libri_2023_su_2013_pct", "non_book_2023_su_2013_pct",
          "calo_totale_2013_2023", "calo_non_book_2013_2023", "calo_libri_2013_2023", "libri_gen_giu", "non_book_gen_giu", "libri_gen_giu_2024_su_2023_pct", "libri_gen_giu_2024_su_2019_pct",
          "libri_gen_giu_2024_su_2013_pct", "non_book_gen_giu_2024_su_2013_pct"]:
    out[k] = R[k]
out["quota_non_book_perdita_pct"] = round(100 * R["calo_non_book_2013_2023"] / R["calo_totale_2013_2023"], 1)

# ---- serie mensile: totale (ds2986), libri e non libri (dettaglio fino a giugno 2024)
s = rc("prestiti_mese_punto_eta.csv")
tot = s.groupby(["anno", "mese"]).prestiti.sum()
cubo = pd.read_parquet(os.path.join(O, "cubo_prestiti_completo.parquet"))
cv = cubo[(cubo.stato != "Annullato") & (cubo.tipo != "Consultazione")]
dm = cv.groupby(["mese_inizio", "media"]).n.sum().unstack().fillna(0)
rows = []
for (a, m), v in tot.items():
    ym = f"{a}-{m:02d}"
    lb = I(dm.loc[ym, "LIBRI E AUDIOLIBRI"]) if ym in dm.index else None
    nb = I(dm.loc[ym, "NBN - NON BOOK MATERIAL"]) if ym in dm.index else None
    rows.append(dict(mese=ym, totale=I(v), libri_audiolibri=lb, non_libri=nb, parziale=(ym == "2026-05")))
mens = pd.DataFrame(rows)
mens.to_csv(os.path.join(D, "mensile.csv"), sep=";", index=False)
out["mensile"] = [[r["mese"], r["totale"], r["libri_audiolibri"], r["non_libri"]] for r in rows]

# ---- titoli e autori (primi 10 per anno e fascia)
tt = rc("top_titoli_anno.csv"); tt = tt[tt.rango <= 10]
tt.to_csv(os.path.join(D, "top_titoli_anno.csv"), sep=";", index=False)
au = rc("top_autori_anno.csv"); au = au[au.rango <= 10]
au.to_csv(os.path.join(D, "top_autori_anno.csv"), sep=";", index=False)
def lst(df, cols):
    o = {}
    for (a, f), g in df.groupby(["anno", "fascia_utente"]):
        o.setdefault(str(a), {})[f] = [[("" if (isinstance(r[c], float) and np.isnan(r[c])) else r[c]) if c != "prestiti" else I(r[c]) for c in cols] for _, r in g.sort_values("rango").iterrows()]
    return o
out["titoli"] = lst(tt, ["titolo", "autore", "prestiti"])
out["autori"] = lst(au, ["autore", "prestiti"])
c = rc("concentrazione_titoli_anno.csv"); trd = rc("traduzioni_anno.csv"); fr = rc("freschezza_libri_anno.csv")
conc = c[["anno", "prestiti_libri", "titoli_distinti", "quota_primi_10", "quota_primi_100", "prestiti_primo", "prestiti_decimo", "prestiti_centesimo"]].merge(
    trd[["anno", "quota_prestiti_tradotti", "tradotti_tra_i_primi_100"]], on="anno").merge(fr[["anno", "quota_uscito_nell_anno_o_precedente", "mediana_eta_libro"]], on="anno")
conc.to_csv(os.path.join(D, "concentrazione_titoli_anno.csv"), sep=";", index=False)
out["concentrazione"] = {str(r.anno): dict(primo=I(r.prestiti_primo), distinti=I(r.titoli_distinti), q100=round(r.quota_primi_100 * 100, 2), tradotti=round(r.quota_prestiti_tradotti * 100, 1),
                                           trad100=I(r.tradotti_tra_i_primi_100), recenti=round(r.quota_uscito_nell_anno_o_precedente * 100, 1)) for r in conc.itertuples()}

# ---- biblioteche: prestiti per anno, mesi quasi senza prestiti
pt = rc("punti_prestito.csv")
ph = pt[(pt.tipo_punto == "biblioteca") & (pt.stato == "Attivo") & pt.lon.notna() & ~pt.denominazione.str.contains("FONDAZIONE|Gianni Mura", case=False)].drop_duplicates("biblioteca")
ap = rc("prestiti_anno_punto.csv"); ap = ap[ap.tipo_punto == "biblioteca"]
py = ap.pivot_table(index="biblioteca", columns="anno", values="prestiti", aggfunc="sum")
cl = rc("mesi_chiusi_biblioteca_anno.csv", index_col=0); cl.columns = [int(x) for x in cl.columns]
bl, rows = [], []
for r in ph.itertuples():
    b = r.biblioteca
    if b not in py.index: continue
    y = {str(a): I(py.loc[b, a]) for a in py.columns if not np.isnan(py.loc[b, a])}
    cc = {str(a): I(cl.loc[b, a]) for a in cl.columns}
    bl.append(dict(n=b, ind=r.indirizzo, lat=round(r.lat, 5), lon=round(r.lon, 5), nil=r.nil, y=y, c=cc))
    for a in y: rows.append(dict(biblioteca=b, anno=int(a), prestiti=y[a], mesi_quasi_senza_prestiti=cc.get(a)))
out["biblioteche"] = bl
pd.DataFrame(rows).to_csv(os.path.join(D, "biblioteche_anno.csv"), sep=";", index=False)
ph[["biblioteca", "denominazione", "indirizzo", "lon", "lat", "id_nil", "nil"]].to_csv(os.path.join(D, "biblioteche_posizione.csv"), sep=";", index=False)
out["mesi_chiusi_totale_per_anno"] = R["mesi_biblioteca_a_meno_del_25pct_del_normale_per_anno"]
out["classifica_2025"] = R["classifica_2025"]
out["nil_con_biblioteca"] = R["nil_totale"] - R["nil_senza_biblioteca"]; out["nil_totale"] = R["nil_totale"]

# ---- chi prende in prestito
ut = pd.DataFrame({"anno": sorted(int(k) for k in R["quota_65piu_pct"])})
ut["quota_65piu_pct"] = ut.anno.map(lambda a: R["quota_65piu_pct"][str(a)])
ut["quota_0_17_pct"] = ut.anno.map(lambda a: R["quota_0_17_pct"][str(a)])
ut["quota_donne_pct"] = ut.anno.map(lambda a: R["quota_donne_pct"].get(str(a)))
ut["prestiti_0_17"] = ut.anno.map(lambda a: R["prestiti_0_17"][str(a)])
ut["prestiti_65piu"] = ut.anno.map(lambda a: R["prestiti_65piu"][str(a)])
ut.to_csv(os.path.join(D, "utenti_anno.csv"), sep=";", index=False)
out["utenti"] = {str(r.anno): dict(p65=r.quota_65piu_pct, m=r.quota_0_17_pct, f=(None if pd.isna(r.quota_donne_pct) else r.quota_donne_pct)) for r in ut.itertuples()}

# ---- rete e punti di ritiro
rete = pd.DataFrame([dict(anno=int(k), quota_prestiti_di_altra_biblioteca_pct=v) for k, v in R["quota_prestiti_di_altra_biblioteca_pct"].items()])
rete.to_csv(os.path.join(D, "rete_anno.csv"), sep=";", index=False)
out["rete"] = {str(r.anno): r.quota_prestiti_di_altra_biblioteca_pct for r in rete.itertuples()}
allp = rc("prestiti_anno_punto.csv")
pr = allp[allp.tipo_punto.isin(["bibliobus", "smartlocker", "edicola", "libreria", "altro"])].pivot_table(index="anno", columns="tipo_punto", values="prestiti", aggfunc="sum").fillna(0).astype(int).reset_index()
pr.to_csv(os.path.join(D, "punti_ritiro_anno.csv"), sep=";", index=False)
out["ritiro"] = {str(r["anno"]): {k: I(r[k]) for k in pr.columns if k != "anno"} for _, r in pr.iterrows()}
out["biblioteche_totale_anno"] = {str(a): I(v) for a, v in ap.groupby("anno").prestiti.sum().items()}
out["covid"] = rc("ripresa_mensile_vs_2019.csv", index_col=0).loc[:, ["2020", "2021"]].round(0).astype(int).to_dict()
out["sormani_2011_fuori_milano_pct"] = R["sormani_2011_quota_fuori_milano_pct"]
out["ascolto"] = "Dati aggregati dal Comune di Milano (CC BY)."
json.dump(out, open(os.path.join(D, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
tot_b = sum(os.path.getsize(os.path.join(D, f)) for f in os.listdir(D))
print("scritti", len(os.listdir(D)), "file,", tot_b, "byte in", D)
