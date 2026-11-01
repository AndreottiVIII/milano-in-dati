"""Fase 1 - tabelle ordinate (tidy) dai dati grezzi. Nessun valore viene corretto: le stranezze restano segnalate.
Uso: python -I -X utf8 build_tabelle.py <biblioteche_abs> <milano_in_dati_abs>
Scrive in pulito/: punti_prestito.csv, prestiti_mese_punto_eta.csv, prestiti_anno_punto.csv, prestiti_anno_totale.csv, prestiti_anno_eta.csv,
 statistiche_annuali_biblioteca.csv, controlli_tabelle.json"""
import sys, os, json, re
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, Point
from shapely import STRtree
from pyproj import Transformer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import rd, canon, kind_of
B, P = sys.argv[1], sys.argv[2]
RAW, OUT = os.path.join(B, "raw"), os.path.join(B, "pulito")
log = {}

# ---------- 1. punti di prestito (ds3012) + NIL per punto in poligono (ds964 NIL vigenti)
pt = rd(os.path.join(RAW, "comune_ds3012", "ds3012_biblioteche_punti_prestito.csv"))
nil = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in nil["features"]]
props = [f["properties"] for f in nil["features"]]
tree = STRtree(polys)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def to_m(g):
    return shapely.transform(g, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
polys_m = [to_m(p) for p in polys]
rows = []
for _, r in pt.iterrows():
    if pd.isna(r["LONG_X_4326"]) or pd.isna(r["LAT_Y_4326"]):   # punti non attivi: nessuna coordinata nel file, tengo il NIL del file
        rows.append((r["ID_NIL"], r["NIL"], np.nan, "dal file (senza coordinate)")); continue
    p = Point(r["LONG_X_4326"], r["LAT_Y_4326"])
    hit = [i for i in tree.query(p) if polys[i].contains(p)]
    pm = Point(*tr.transform(r["LONG_X_4326"], r["LAT_Y_4326"]))
    if hit:
        i, dist, how = hit[0], 0.0, "dentro"
    else:
        ds = [pg.distance(pm) for pg in polys_m]
        i = int(np.argmin(ds)); dist = float(ds[i]); how = "vicinanza"
    rows.append((props[i]["ID_NIL"], props[i]["NIL"], round(dist, 1), how))
pt[["id_nil", "nil", "dist_nil_m", "nil_come"]] = pd.DataFrame(rows, index=pt.index)
pt["biblioteca"] = pt["Denominazione"].map(canon)
pt["tipo_punto"] = [kind_of(t, n) for t, n in zip(pt["Tipo"], pt["Denominazione"])]
pt["nil_file_ds3012"] = pt["NIL"]; pt["id_nil_file_ds3012"] = pt["ID_NIL"]
pt["accordo_id_nil"] = pt["id_nil"] == pt["id_nil_file_ds3012"]
log["punti_ds3012"] = int(len(pt)); log["punti_nil_dentro"] = int((pt.nil_come == "dentro").sum()); log["punti_nil_vicinanza"] = int((pt.nil_come == "vicinanza").sum()); log["punti_senza_coordinate"] = int(pt.LONG_X_4326.isna().sum())
log["punti_id_nil_accordo_con_file"] = int(pt.accordo_id_nil.sum())
dis = pt.loc[~pt.accordo_id_nil, ["Denominazione", "nil", "nil_file_ds3012"]]
log["punti_id_nil_in_disaccordo"] = dis.values.tolist()
out = pt.rename(columns={"library_id": "id_punto", "Denominazione": "denominazione", "Indirizzo": "indirizzo", "Tipo": "tipo_file", "Stato": "stato",
                         "library_code": "codice", "Codice ISIL": "isil", "MUNICIPIO": "municipio_file", "LONG_X_4326": "lon", "LAT_Y_4326": "lat"})
out[["id_punto", "denominazione", "biblioteca", "tipo_punto", "tipo_file", "stato", "codice", "isil", "indirizzo", "lon", "lat", "id_nil", "nil", "dist_nil_m", "nil_come",
     "municipio_file", "id_nil_file_ds3012", "nil_file_ds3012"]].to_csv(os.path.join(OUT, "punti_prestito.csv"), sep=";", index=False)

# ---------- 2. ds2986: prestiti per mese, punto di prestito, classe di eta'
s = rd(os.path.join(RAW, "comune_ds2986", "ds2986-biblioteche-prestiti-per-mese.csv"))
s.columns = ["anno", "mese", "punto", "id_punto_file", "id_nil_file", "nil_file", "municipio_file", "tipologia_file", "eta_classe", "prestiti"]
s["biblioteca"] = s["punto"].map(canon)
s["tipo_punto"] = [kind_of(None, n) for n in s["punto"]]
s.loc[s.tipologia_file.eq("Smartlocker"), "tipo_punto"] = "smartlocker"
log["ds2986_righe"] = int(len(s)); log["ds2986_prestiti_totali"] = int(s.prestiti.sum())
log["ds2986_ultimo_mese"] = f"{s.anno.max()}-{s[s.anno==s.anno.max()].mese.max():02d}"
log["ds2986_prestiti_nulli_o_negativi"] = int((s.prestiti <= 0).sum())
m = s[["punto", "id_nil_file"]].drop_duplicates().merge(pt[["Denominazione", "id_nil"]].assign(punto=lambda d: d.Denominazione.str.upper()), on="punto", how="left")
m = m[m.id_nil_file.notna() & m.id_nil.notna()]
log["ds2986_punti_con_nil_confrontabile"] = int(len(m)); log["ds2986_punti_nil_uguale"] = int((m.id_nil_file.astype(float) == m.id_nil.astype(float)).sum())
s.to_csv(os.path.join(OUT, "prestiti_mese_punto_eta.csv"), sep=";", index=False)
ap = s.groupby(["anno", "biblioteca", "tipo_punto"], as_index=False).agg(prestiti=("prestiti", "sum"), mesi_con_prestiti=("mese", "nunique"))
ap.to_csv(os.path.join(OUT, "prestiti_anno_punto.csv"), sep=";", index=False)
at = s.groupby("anno", as_index=False).agg(prestiti=("prestiti", "sum"), mesi_con_dati=("mese", "nunique"))
at["anno_parziale"] = at.mesi_con_dati < 12
at.to_csv(os.path.join(OUT, "prestiti_anno_totale.csv"), sep=";", index=False)
s.groupby(["anno", "eta_classe"], as_index=False).prestiti.sum().to_csv(os.path.join(OUT, "prestiti_anno_eta.csv"), sep=";", index=False)

# ---------- 3. statistiche annuali per biblioteca (iscritti, patrimonio, prestiti) 2013-2023
def num(x):
    return pd.to_numeric(x.astype(str).str.strip().replace({"-": np.nan, "N.D.": np.nan, "nan": np.nan, "": np.nan}), errors="coerce")
rows = []
d = rd(os.path.join(RAW, "comune_ds336", "ds336_cultura_bilioteche-rionali-patrimonio-prestiti_2013-2015.csv"))
for _, r in d.iterrows():
    rows.append(dict(anno=r["Anno"], biblioteca=canon(r["Biblioteca"]), fonte="ds336", iscritti_adulti=r["Iscritti-Adulti"], iscritti_ragazzi=r["Iscritti-Ragazzi"],
        patrimonio_stampati=r["Patrimonio-Libri"], prestiti_stampati=(r["Prestiti-Libri Adulti"] + r["Prestiti-Libri ragazzi"]), prestiti_multimediali=r["Prestiti-Audiovisivi"],
        prestiti_periodici=np.nan, interprestiti_uscita=r["Prestiti intersistema-Ad altre Biblioteche"], interprestiti_entrata=r["Prestiti intersistema-Da altre Biblioteche"]))
d = rd(os.path.join(RAW, "comune_ds286", "ds286_cultura_bilioteche_sormani_prestiti_utenti_2013-2015.csv"))
for _, r in d.iterrows():
    def f(c):  # 2015: il file scrive 60.455 per 60455 (punto come separatore delle migliaia)
        v = str(r[c]).strip()
        if re.fullmatch(r"\d{1,3}\.\d{3}", v): v = v.replace(".", "")
        return pd.to_numeric(v.replace("N.D.", "nan"), errors="coerce")
    rows.append(dict(anno=r["Anno"], biblioteca="Sormani", fonte="ds286", iscritti_adulti=f("Iscritti-Adulti"), iscritti_ragazzi=f("Iscritti-Ragazzi"),
        patrimonio_stampati=f("Patrimonio-Libri"), prestiti_stampati=f("Prestiti-Libri Adulti") + f("Prestiti-Libri ragazzi"), prestiti_multimediali=f("Prestiti-Audiovisivi"),
        prestiti_periodici=np.nan, interprestiti_uscita=f("Prestiti intersistema-Ad altre Biblioteche"), interprestiti_entrata=f("Prestiti intersistema-Da altre Biblioteche")))
log["sormani_2015_separatore_migliaia_corretto_in_lettura"] = True
d = rd(os.path.join(RAW, "comune_ds909", "cultura_biblioteche-rionali-caratteristiche.csv"))
d = d[d.Anno == 2016]   # 2017 e 2018: colonne sfalsate, non utilizzabili (vedi NOTE)
for _, r in d.iterrows():
    g = lambda c: num(pd.Series([r[c]])).iloc[0]
    rows.append(dict(anno=2016, biblioteca=canon(r["Biblioteche"]), fonte="ds909", iscritti_adulti=g("Iscritti Adulti >15 anni"), iscritti_ragazzi=g("Iscritti Ragazzi <= 14 anni"),
        patrimonio_stampati=np.nan, prestiti_stampati=np.nan, prestiti_multimediali=g("Prestiti Multimediali"), prestiti_periodici=np.nan,
        interprestiti_uscita=g("Prestiti ad altre Biblioteche"), interprestiti_entrata=g("Prestiti da altre biblioteche"),
        prestiti_totale_locale_file=g("Prestiti Adulti") + g("Prestiti Ragazzi")))
for ds, f, y in [("ds928", "ds928_biblio_comunali_2019.csv", 2019), ("ds1641", "ds1641_biblio_comunali_2020.csv", 2020), ("ds2166", "ds2166_biblio_comunali_2021.csv", 2021),
                 ("ds2928", "ds2928_biblio_comunali_2022.csv", 2022), ("ds2929", "ds2929_ds2929_biblio_comunali_2023.csv", 2023)]:
    d = rd(os.path.join(RAW, "comune_" + ds, f))
    stamp = [c for c in d.columns if c.startswith("Prestiti-Prestito locale-Stampati")]
    mult = [c for c in d.columns if c.startswith("Prestiti-Prestito locale-Multimediali")]
    per = [c for c in d.columns if c.startswith("Prestiti-Periodici")]
    usc = [c for c in d.columns if "usc" in c and c.startswith("Prestiti")]
    ent = [c for c in d.columns if "entr" in c and c.startswith("Prestiti")]
    pat = [c for c in d.columns if c.startswith("Patrimonio-Stampati")]
    sm = lambda cs: sum(num(d[c]).fillna(0) for c in cs)
    s_stamp, s_mult, s_per, s_usc, s_ent = sm(stamp), sm(mult), sm(per), sm(usc), sm(ent)
    for i in range(len(d)):
        rows.append(dict(anno=y, biblioteca=canon(d["Biblioteca"].iloc[i]), fonte=ds,
            iscritti_adulti=num(d["Iscritti-Adulti>15 anni"]).iloc[i], iscritti_ragazzi=num(d["Iscritti-Ragazzi<=14 anni"]).iloc[i],
            patrimonio_stampati=num(d[pat[0]]).iloc[i], prestiti_stampati=s_stamp.iloc[i], prestiti_multimediali=s_mult.iloc[i], prestiti_periodici=s_per.iloc[i],
            interprestiti_uscita=s_usc.iloc[i], interprestiti_entrata=s_ent.iloc[i]))
st = pd.DataFrame(rows)
st["iscritti_totale"] = st.iscritti_adulti.fillna(0) + st.iscritti_ragazzi.fillna(0)
st.loc[st.iscritti_adulti.isna() & st.iscritti_ragazzi.isna(), "iscritti_totale"] = np.nan
st["prestiti_locali"] = st.prestiti_stampati.fillna(0) + st.prestiti_multimediali.fillna(0)
msk = st.fonte == "ds909"
st.loc[msk, "prestiti_locali"] = st.loc[msk, "prestiti_totale_locale_file"]
st = st.drop(columns=["prestiti_totale_locale_file"])
st.to_csv(os.path.join(OUT, "statistiche_annuali_biblioteca.csv"), sep=";", index=False)
log["statistiche_annuali_righe"] = int(len(st)); log["statistiche_annuali_anni"] = sorted(st.anno.unique().astype(int).tolist())
json.dump(log, open(os.path.join(OUT, "controlli_tabelle.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, ensure_ascii=False, indent=1, default=str))
