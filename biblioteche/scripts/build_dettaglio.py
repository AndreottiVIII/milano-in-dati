"""Fase 1 - tabelle dal dettaglio prestito per prestito (aggregati mensili gia' fatti da build_mensili.py / build_extra.py) e dai dati 2007-2011.
Uso: python -I -X utf8 build_dettaglio.py <biblioteche_abs>
Scrive in pulito/: dettaglio_anno_tipo.csv, dettaglio_anno_eta_genere.csv, dettaglio_anno_supporto.csv, dettaglio_anno_ritiro_proprietaria.csv,
 top_titoli_anno.csv, top_autori_anno.csv, top_non_libri_anno.csv, concentrazione_titoli_anno.csv, traduzioni_anno.csv, freschezza_libri_anno.csv, top_editori_anno.csv,
 serie_lunga_rionali_2007_2011.csv, narrativa_saggistica.csv, controlli_dettaglio.json
Definizione 'prestito valido': stato diverso da Annullato e tipo diverso da Consultazione (include prestiti in corso)."""
import sys, os, glob, json, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import rd, canon, titolo_chiave, autore_chiave
B = sys.argv[1]; RAW, OUT = os.path.join(B, "raw"), os.path.join(B, "pulito")
log = {}
c = pd.read_parquet(os.path.join(OUT, "cubo_prestiti_completo.parquet"))
c["anno"] = c.mese_inizio.str[:4].astype(int)
log["cubo_righe_prestiti_totali"] = int(c.n.sum())
log["righe_con_anno_inizio_diverso_da_file"] = int(c.loc[c.mese_inizio != c.mese_file, "n"].sum())
c.groupby(["anno", "tipo", "stato"], as_index=False).n.sum().to_csv(os.path.join(OUT, "dettaglio_anno_tipo.csv"), sep=";", index=False)
v = c[(c.stato != "Annullato") & (c.tipo != "Consultazione")].copy()
log["prestiti_validi"] = int(v.n.sum())
v.groupby(["anno", "eta_fascia", "eta", "genere"], as_index=False).n.sum().to_csv(os.path.join(OUT, "dettaglio_anno_eta_genere.csv"), sep=";", index=False)
v.groupby(["anno", "media", "supporto"], as_index=False).n.sum().to_csv(os.path.join(OUT, "dettaglio_anno_supporto.csv"), sep=";", index=False)
v["ritiro"] = v.a_bib.map(canon); v["proprietaria"] = v.da_bib.map(canon)
v.groupby(["anno", "ritiro", "proprietaria", "tipo"], as_index=False).n.sum().to_csv(os.path.join(OUT, "dettaglio_anno_ritiro_proprietaria.csv"), sep=";", index=False)

# ---- titoli
t = pd.read_parquet(os.path.join(OUT, "titoli_anno_completo.parquet"))   # prestiti validi bibliotecario/interbibliotecario, non annullati
t["anno"] = t["anno"].astype(int)
t["tradotto"] = t.titolo.fillna("").str.contains(r"traduzion|traduz\.|tradotto|translated|trad\. ", case=False, regex=True)
libri = t[(t.media == "LIBRI E AUDIOLIBRI") & (t.supporto == "MATERIALE A STAMPA")].copy()
log["libri_stampati_prestiti"] = int(libri.n.sum())
libri["tk"], libri["td"] = titolo_chiave(libri.titolo.fillna(""))
libri["ak"], libri["ad"] = autore_chiave(libri.autore.replace("(vuoto)", ""))
# record senza titolo vero (solo numero di volume, es. "1", "2", senza autore): non sono libri classificabili, restano nei totali ma non nelle classifiche
bad = libri.tk.str.fullmatch(r"\d{1,3}") | (libri.tk == "")
log["libri_record_con_titolo_solo_numero_prestiti"] = int(libri.loc[bad, "n"].sum())
log["libri_record_con_titolo_solo_numero_quota"] = round(float(libri.loc[bad, "n"].sum() / libri.n.sum()), 4)
pd.DataFrame({"anno": libri.anno, "n": libri.n, "bad": bad}).groupby("anno").apply(lambda g: pd.Series({"prestiti_libri": g.n.sum(), "prestiti_titolo_solo_numero": g.loc[g.bad, "n"].sum()})).reset_index().assign(quota=lambda d: (d.prestiti_titolo_solo_numero / d.prestiti_libri).round(4)).to_csv(os.path.join(OUT, "libri_titolo_solo_numero_anno.csv"), sep=";", index=False)
libri_all = libri
libri = libri[~bad]
def top(df, keycols, disp, scope, k=25):
    out = []
    for a, g in df.groupby("anno"):
        gg = g.groupby(keycols, as_index=False).n.sum()
        # nome visualizzato = la forma piu' frequente
        dm = g.sort_values("n", ascending=False).drop_duplicates(keycols)[keycols + disp]
        gg = gg.merge(dm, on=keycols).nlargest(k, "n")
        gg["anno"] = a; gg["rango"] = range(1, len(gg) + 1); gg["scope"] = scope
        out.append(gg)
    return pd.concat(out)
tt = []
for scope, df in [("tutti", libri), ("Minori", libri[libri.eta_fascia == "Minori"]), ("Adulti", libri[libri.eta_fascia == "Adulti"]), ("Anziani", libri[libri.eta_fascia == "Anziani"])]:
    tt.append(top(df, ["tk", "ak"], ["td", "ad"], scope))
tt = pd.concat(tt).rename(columns={"td": "titolo", "ad": "autore", "n": "prestiti", "scope": "fascia_utente"})
tt[["anno", "fascia_utente", "rango", "titolo", "autore", "prestiti"]].to_csv(os.path.join(OUT, "top_titoli_anno.csv"), sep=";", index=False)
aa = []
la = libri[libri.ak != ""]
for scope, df in [("tutti", la), ("Minori", la[la.eta_fascia == "Minori"]), ("Adulti", la[la.eta_fascia == "Adulti"]), ("Anziani", la[la.eta_fascia == "Anziani"])]:
    aa.append(top(df, ["ak"], ["ad"], scope, 25))
aa = pd.concat(aa).rename(columns={"ad": "autore", "n": "prestiti", "scope": "fascia_utente"})
aa[["anno", "fascia_utente", "rango", "autore", "prestiti"]].to_csv(os.path.join(OUT, "top_autori_anno.csv"), sep=";", index=False)
# non-libri (DVD ecc.)
nb = t[t.media == "NBN - NON BOOK MATERIAL"].copy()
nb["tk"], nb["td"] = titolo_chiave(nb.titolo.fillna(""))
nb["ak"] = ""; nb["ad"] = ""
nbt = top(nb, ["tk"], ["td"], "tutti", 15).rename(columns={"td": "titolo", "n": "prestiti"})
nbt[["anno", "rango", "titolo", "prestiti"]].to_csv(os.path.join(OUT, "top_non_libri_anno.csv"), sep=";", index=False)
# concentrazione
rows = []
for a, g in libri.groupby("anno"):
    gg = g.groupby(["tk", "ak"]).n.sum().sort_values(ascending=False)
    tot = gg.sum()
    rows.append(dict(anno=a, prestiti_libri=int(tot), titoli_distinti=int(len(gg)), prestiti_per_titolo=round(tot / len(gg), 2), titoli_con_1_prestito=int((gg == 1).sum()),
        quota_primi_10=round(gg.iloc[:10].sum() / tot, 5), quota_primi_100=round(gg.iloc[:100].sum() / tot, 5), quota_primi_1000=round(gg.iloc[:1000].sum() / tot, 5),
        prestiti_primo=int(gg.iloc[0]), prestiti_decimo=int(gg.iloc[9]), prestiti_centesimo=int(gg.iloc[99])))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "concentrazione_titoli_anno.csv"), sep=";", index=False)
# traduzioni: quota dei prestiti con 'traduzione' nel titolo; nei primi 100 titoli
rows = []
for a, g in libri.groupby("anno"):
    gg = g.groupby(["tk", "ak"]).agg(n=("n", "sum"), trad=("tradotto", "max")).sort_values("n", ascending=False)
    top100 = gg.iloc[:100]
    rows.append(dict(anno=a, quota_prestiti_tradotti=round(g.loc[g.tradotto, "n"].sum() / g.n.sum(), 4), quota_tradotti_nei_primi_100_titoli=round(top100.loc[top100.trad, "n"].sum() / top100.n.sum(), 4),
                     tradotti_tra_i_primi_100=int(top100.trad.sum())))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "traduzioni_anno.csv"), sep=";", index=False)
# lingua dell'edizione
lg = libri_all.assign(lingua2=np.where(libri_all.lingua == "ita", "ita", np.where(libri_all.lingua == "eng", "eng", "altre"))).groupby(["anno", "lingua2"], as_index=False).n.sum()
lg.to_csv(os.path.join(OUT, "lingua_edizione_anno.csv"), sep=";", index=False)

# ---- freschezza (anno di edizione) ed editori, dal secondo passaggio
e = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "mensili_parquet", "ed_*.parquet")))])
e["anno"] = e.mese_inizio.str[:4].astype(int)
e["ed"] = pd.to_numeric(e.anno_edizione, errors="coerce")
e.loc[(e.ed < 1000) | (e.ed > e.anno + 1), "ed"] = np.nan
e["eta_libro"] = e.anno - e.ed
rows = []
for a, g in e.groupby("anno"):
    gd = g[g.eta_libro.notna()]
    w = gd.n.values; x = gd.eta_libro.values
    o = np.argsort(x); cw = np.cumsum(w[o]); med = x[o][np.searchsorted(cw, cw[-1] / 2)]
    rows.append(dict(anno=a, prestiti_libri=int(g.n.sum()), con_anno_edizione=int(w.sum()), quota_senza_anno=round(1 - w.sum() / g.n.sum(), 4),
        quota_uscito_nell_anno_o_precedente=round(w[x <= 1].sum() / w.sum(), 4), quota_entro_3_anni=round(w[x <= 3].sum() / w.sum(), 4),
        quota_oltre_10_anni=round(w[x > 10].sum() / w.sum(), 4), mediana_eta_libro=float(med)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "freschezza_libri_anno.csv"), sep=";", index=False)
ed = e[e.editore != "(vuoto)"].copy()
ed["editore_k"] = ed.editore.str.lower().str.replace(r"[^\w ]+", "", regex=True).str.strip()
rows = []
for a, g in ed.groupby("anno"):
    gg = g.groupby("editore_k").agg(n=("n", "sum"), editore=("editore", "first")).nlargest(10, "n")
    for i, (k, r) in enumerate(gg.iterrows(), 1): rows.append(dict(anno=a, rango=i, editore=r.editore, prestiti=int(r.n), quota=round(r.n / g.n.sum(), 4)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "top_editori_anno.csv"), sep=";", index=False)

# ---- 2007-2011 (solo rionali) e narrativa/saggistica
a = rd(os.path.join(RAW, "comune_ds161", "ds161_cultura_biblioteche_rionali_prestiti_opera_2007-2008.csv"))
b = rd(os.path.join(RAW, "comune_ds99", "ds99_cultura_biblioteche_rionali_prestiti_opera_2011.csv")).rename(columns={"TipoPrestito": "Materiale"})
sl = pd.concat([a[["Anno", "Materiale", "NumPrestiti"]], b[["Anno", "Materiale", "NumPrestiti"]]]).groupby(["Anno", "Materiale"], as_index=False).NumPrestiti.sum()
sl["fonte"] = np.where(sl.Anno < 2011, "ds161", "ds99")
sl.to_csv(os.path.join(OUT, "serie_lunga_rionali_2007_2011.csv"), sep=";", index=False)
c163 = rd(os.path.join(RAW, "comune_ds163", "ds163_cultura_biblioteche_rionali_prestiti_opera_mese_2011.csv"))
ns = c163.groupby(["Anno", "Genere", "FasciaEta"], as_index=False).NumPrestiti.sum().rename(columns={"NumPrestiti": "prestiti"})
ns["fonte"] = "ds163 (libri e altro, rionali, 2011)"
d909 = rd(os.path.join(RAW, "comune_ds909", "cultura_biblioteche-rionali-caratteristiche.csv"))
d909 = d909[(d909.Anno == 2016) & ~d909.Biblioteche.isin(["Biblioteca Sormani", "Bibliobus", "Fondo storico ragazzi", "Deposito interbibliotecario"])]
nn = {k: pd.to_numeric(d909[k].replace("-", np.nan), errors="coerce").sum() for k in ["Prestiti Narrativa", "Prestiti Saggistica", "Prestiti Multimediali"]}
ns2 = pd.DataFrame([dict(Anno=2016, Genere=k.replace("Prestiti ", ""), FasciaEta="tutte", prestiti=int(v_), fonte="ds909 (24 biblioteche rionali con dati; Accursio e Gallaratese senza)") for k, v_ in nn.items()])
pd.concat([ns, ns2]).to_csv(os.path.join(OUT, "narrativa_saggistica.csv"), sep=";", index=False)
json.dump(log, open(os.path.join(OUT, "controlli_dettaglio.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, indent=1))
