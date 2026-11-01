"""Scrive i file dati della pagina "Alberi della citta'" (docs/alberi/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <alberi_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): alberi/pulito/alberi.csv, nil_alberi.csv, riepilogo.json, cap_alberi_reddito.csv, forestami_piantagioni.csv,
alberi/raw/comune_ds2489/*.csv (alberi monumentali), alberi/scripts/taxonomia_genere.csv, il file dei poligoni NIL di citta-15-minuti e
censimenti/pulito/nil_2021_anagrafica.csv (nomi dei NIL).
Scrive in <docs_dir>/alberi/data/: riepilogo.json, nil.geojson, esagoni.json, nil.csv, specie_2025.csv, generi_2025.csv,
cambiamenti_per_genere_2023_2025.csv, cap_alberi_reddito.csv, monumentali.csv.
Dati aggregati (per quartiere, per esagono di circa 250 m, per citta'): nessun albero singolo (251.165 punti) viene ripubblicato.
Nessun contenuto di Forestami: solo i totali (numeri) in riepilogo.json.
"""
import sys, os, json, csv
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from pyproj import Transformer
from scipy.stats import spearmanr

A, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(A, "pulito")
OUT = os.path.join(DOCS, "alberi", "data")
os.makedirs(OUT, exist_ok=True)
assert int(shapely.__version__.split(".")[0]) >= 2

AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))

# ---------------------------------------------------------------- dati
cols = ["id", "edizione", "specie_binomio_normalizzata", "genere", "famiglia", "nome_comune", "lon", "lat",
        "diam_tronc_cm", "data_inizio_scheda", "localita", "id_nil"]
t = pd.read_csv(os.path.join(PU, "alberi.csv"), sep=";", usecols=cols, low_memory=False, keep_default_na=False,
                na_values=[""], dtype={"id": str, "localita": str})
EDS = sorted(t.edizione.unique())
assert EDS == ["2023-03-31", "2024-03-31", "2025-03-31"], EDS
E23, E24, E25 = (t[t.edizione == e].copy() for e in EDS)
t = None
N23, N24, N25 = len(E23), len(E24), len(E25)
print("alberi", N23, N24, N25)

tax = pd.read_csv(os.path.join(A, "scripts", "taxonomia_genere.csv"), sep=";")
GEN_IT = dict(zip(tax.genere, tax.nome_comune))

# ---------------------------------------------------------------- NIL: base, nomi, poligoni
nil = pd.read_csv(os.path.join(PU, "nil_alberi.csv"), sep=";")
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
nil["nome"] = [nomi.get(int(i)) or str(n).title() for i, n in zip(nil.id_nil, nil.nil)]
assert len(nil) == 88 and nil.nome.notna().all()
nil["abitanti_per_km2"] = nil.abitanti_2024 / nil.area_km2
nil["in_classifica"] = nil.abitanti_2024 >= 5000

nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
assert set(geom) == set(int(i) for i in nil.id_nil)

# specie, genere, famiglia per NIL (edizione 2025) - stessa regola di analisi.py: le specie "spp" e "n.d." non entrano nella classifica delle specie
def determinata(s):
    return ~(s.eq("n.d.") | s.str.endswith(" spp"))
per_nil = {}
for i, g in E25[E25.id_nil.notna()].groupby("id_nil"):
    n = len(g)
    sp = g.specie_binomio_normalizzata.value_counts()
    sp = sp[determinata(sp.index.to_series()).values]
    nome_comune = g.dropna(subset=["nome_comune"]).groupby("specie_binomio_normalizzata").nome_comune.agg(lambda s: s.mode().iloc[0])
    top3 = [[nome_comune.get(b, ""), b, int(c)] for b, c in sp.head(3).items()]
    gen = g.genere.value_counts()
    fam = g.famiglia.value_counts()
    spp = int((~determinata(g.specie_binomio_normalizzata)).sum())
    per_nil[int(i)] = {
        "_sp": 100 * sp.iloc[0] / n if len(sp) else 0.0, "_g": 100 * gen.iloc[0] / n, "_f": 100 * fam.iloc[0] / n,
        "s": top3, "sp": round(100 * sp.iloc[0] / n, 1) if len(sp) else None,
        "g": gen.index[0], "gi": GEN_IT.get(gen.index[0], ""), "gp": round(100 * gen.iloc[0] / n, 1),
        "f": fam.index[0], "fp": round(100 * fam.iloc[0] / n, 1), "nsp": round(100 * spp / n, 1)}

# spariti / nuovi 2023-2025 per NIL
s23, s25 = E23.set_index("id"), E25.set_index("id")
rim_ids = s23.index.difference(s25.index)
agg_ids = s25.index.difference(s23.index)
com_ids = s23.index.intersection(s25.index)
check("alberi spariti 2023-2025", len(rim_ids), RIEP["rimossi_2023_2025_totale"])
check("alberi nuovi 2023-2025", len(agg_ids), 17905)
check("alberi in comune 2023-2025", len(com_ids), 233260)
check("saldo 2023-2025", N25 - N23, -3910)
rim = s23.loc[rim_ids]
agg = s25.loc[agg_ids]
tr_pct = round(100 * float((rim.diam_tronc_cm <= 12).mean()), 1)
check("spariti con tronco <= 12 cm (%)", tr_pct, RIEP["rimossi_2023_2025_con_tronco_fino_a_12cm_pct"], 0.05)
anno_rim = rim.data_inizio_scheda.str[:4].astype(float)
n_rim_2019 = int((anno_rim >= 2019).sum())
check("spariti con scheda dal 2019 (n)", n_rim_2019, RIEP["rimossi_2023_2025_con_anno_scheda_dal_2019"])
# confronto: com'e' l'insieme di tutti gli alberi del 2023 (per capire se i spariti sono diversi dagli altri)
anno_23 = E23.data_inizio_scheda.str[:4].astype(float)
base_tr = round(100 * float((E23.diam_tronc_cm <= 12).mean()), 1)
base_2019 = round(100 * float((anno_23 >= 2019).mean()), 1)
com23 = s23.loc[com_ids]
rimasti_tr = round(100 * float((com23.diam_tronc_cm <= 12).mean()), 1)
rimasti_2019 = round(100 * float((com23.data_inizio_scheda.str[:4].astype(float) >= 2019).mean()), 1)
print("confronto 2023: tutti tronco<=12", base_tr, "rimasti", rimasti_tr, "| tutti scheda>=2019", base_2019, "rimasti", rimasti_2019)
rim_nil = rim.id_nil.value_counts()
agg_nil = agg.id_nil.value_counts()

# ---------------------------------------------------------------- NIL: geojson per la pagina
def R1(x, d=1):
    return None if pd.isna(x) else round(float(x), d)
feats = []
nil_rows = []
for _, r in nil.sort_values("nome").iterrows():
    i = int(r.id_nil)
    pn = per_nil[i]
    p = {"i": i, "n": r.nome, "ab": int(r.abitanti_2024), "km2": R1(r.area_km2, 2), "abkm2": R1(r.abitanti_per_km2, 0),
         "t23": int(r.alberi_2023), "t24": int(r.alberi_2024), "t25": int(r.alberi_2025),
         "p1000": R1(r.alberi_per_1000ab_2025, 1) if r.abitanti_2024 > 0 else None,
         "pkm2": R1(r.alberi_per_km2_2025, 0), "v": int(r.variazione_2023_2025), "vp": R1(r.variazione_pct, 1),
         "rm": int(rim_nil.get(i, 0)), "ag": int(agg_nil.get(i, 0)),
         "cl": 1 if r.in_classifica else 0}
    p.update({k: v for k, v in pn.items() if not k.startswith("_")})
    g = geom[i].simplify(0.00003, preserve_topology=True)
    gj = mapping(g)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    gj = {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}
    feats.append({"type": "Feature", "properties": p, "geometry": gj})
    nil_rows.append({
        "id_nil": i, "nil": r.nome, "area_km2": R1(r.area_km2, 3), "abitanti_2024": int(r.abitanti_2024), "abitanti_per_km2": R1(r.abitanti_per_km2, 0),
        "alberi_2023": int(r.alberi_2023), "alberi_2024": int(r.alberi_2024), "alberi_2025": int(r.alberi_2025),
        "alberi_per_1000_abitanti_2025": p["p1000"], "alberi_per_km2_2025": p["pkm2"],
        "variazione_2023_2025": p["v"], "variazione_pct_2023_2025": p["vp"], "spariti_2023_2025": p["rm"], "nuovi_2023_2025": p["ag"],
        "specie_piu_frequente": (pn["s"][0][1] if pn["s"] else ""), "specie_piu_frequente_pct": pn["sp"],
        "genere_piu_frequente": pn["g"], "genere_piu_frequente_pct": pn["gp"], "famiglia_piu_frequente": pn["f"], "famiglia_piu_frequente_pct": pn["fp"],
        "in_classifica_almeno_5000_abitanti": int(r.in_classifica)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(nil_rows).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";")
check("somma alberi NIL 2025 + senza NIL", int(nil.alberi_2025.sum()) + int(E25.id_nil.isna().sum()), N25)

# regola 10-20-30 per NIL
sp_pct = np.array([v["_sp"] for v in per_nil.values()])
g_pct = np.array([v["_g"] for v in per_nil.values()])
f_pct = np.array([v["_f"] for v in per_nil.values()])
n_sp10, n_g20, n_f30 = int((sp_pct >= 10).sum()), int((g_pct >= 20).sum()), int((f_pct >= 30).sum())
check("NIL con specie sopra 10%", n_sp10, RIEP["nil_con_specie_top_oltre_10pct"])
check("NIL con genere sopra 20%", n_g20, RIEP["nil_con_genere_top_oltre_20pct"])
print("NIL con famiglia sopra 30%:", n_f30)

# cimiteri: il caso del Calocedrus
w = E25.localita.fillna("").str.split().str[0].str.lower()
E25["cimitero"] = w.eq("cimitero")
cal = E25[E25.genere == "Calocedrus"]
cal_tot, cal_cim = len(cal), int(cal.cimitero.sum())
mag = nil[nil.nil.str.startswith("MAGGIORE")].iloc[0]
cal_mag = int((cal.id_nil == mag.id_nil).sum())
cal_mag_cim = int(((cal.id_nil == mag.id_nil) & cal.cimitero).sum())
print("calocedri", cal_tot, "in cimiteri", cal_cim, "in Maggiore", cal_mag, "di cui cimiteri", cal_mag_cim)
cimiteri_alberi = int(E25.cimitero.sum())

# ---------------------------------------------------------------- esagoni (UTM 32N, esagoni "punta in su", larghezza 250 m)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
tri = Transformer.from_crs(32632, 4326, always_xy=True)
LARG = 250.0
Rh = LARG / np.sqrt(3)
x, y = tr.transform(E25.lon.values, E25.lat.values)
x, y = np.asarray(x), np.asarray(y)
qf = (np.sqrt(3) / 3 * x - y / 3) / Rh
rf = (2 / 3 * y) / Rh
# arrotondamento cubico
xc, zc = qf, rf
yc = -xc - zc
rx, ry, rz = np.round(xc), np.round(yc), np.round(zc)
dx, dy, dz = abs(rx - xc), abs(ry - yc), abs(rz - zc)
m1 = (dx > dy) & (dx > dz)
m2 = ~m1 & (dy > dz)
rx = np.where(m1, -ry - rz, rx)
rz = np.where(~m1 & ~m2, -rx - ry, rz)
E25["hq"], E25["hr"] = rx.astype(int), rz.astype(int)
cnt = E25.groupby(["hq", "hr"]).size().rename("n").reset_index()
gg = E25.dropna(subset=["genere"]).groupby(["hq", "hr", "genere"]).size().rename("c").reset_index()
gg = gg.sort_values(["hq", "hr", "c", "genere"], ascending=[True, True, False, True]).drop_duplicates(["hq", "hr"])
cnt = cnt.merge(gg, on=["hq", "hr"], how="left")
cx = Rh * np.sqrt(3) * (cnt.hq + cnt.hr / 2)
cy = Rh * 1.5 * cnt.hr
clon, clat = tri.transform(cx.values, cy.values)
cnt["lon"], cnt["lat"] = np.round(clon, 5), np.round(clat, 5)
# NIL del centro dell'esagono
cnt["nil"] = -1
for i, g in geom.items():
    inside = shapely.contains_xy(g, cnt.lon.values, cnt.lat.values)
    cnt.loc[inside & (cnt.nil == -1), "nil"] = i
generi_usati = sorted(cnt.genere.dropna().unique())
gidx = {g: k for k, g in enumerate(generi_usati)}
cells = []
for r in cnt.itertuples():
    gi = gidx.get(r.genere, -1)
    gp = int(round(100 * r.c / r.n)) if gi >= 0 else 0
    cells.append([float(r.lon), float(r.lat), int(r.n), gi, gp, int(r.nil)])
check("somma alberi negli esagoni", int(sum(c[2] for c in cells)), N25)
ns = np.array([c[2] for c in cells])
print("esagoni", len(cells), "mediana alberi", np.median(ns), "percentili 10/25/50/75/90/99", np.percentile(ns, [10, 25, 50, 75, 90, 99]).round(1), "max", ns.max())
area_ha = 3 * np.sqrt(3) / 2 * Rh ** 2 / 10000
breaks = [10, 30, 70, 130, 250]
esagoni = {"larghezza_m": LARG, "raggio_m": round(Rh, 2), "area_ha": round(float(area_ha), 2), "edizione": "2025-03-31",
           "classi": breaks, "generi": [[g, GEN_IT.get(g, "")] for g in generi_usati],
           "campi": ["lon_centro", "lat_centro", "alberi", "indice_genere_principale", "quota_genere_principale_pct", "id_nil_del_centro"],
           "celle": cells}
json.dump(esagoni, open(os.path.join(OUT, "esagoni.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------- specie, generi, famiglie (2025)
nc = E25.dropna(subset=["nome_comune"]).groupby("specie_binomio_normalizzata").nome_comune.agg(lambda s: s.mode().iloc[0])
fam_of = E25.dropna(subset=["famiglia"]).groupby("genere").famiglia.agg(lambda s: s.mode().iloc[0])
sp = E25.specie_binomio_normalizzata.value_counts()
spdf = pd.DataFrame({"specie": sp.index, "nome_comune": [nc.get(s, "") for s in sp.index], "alberi": sp.values,
                     "quota_pct": (100 * sp.values / N25).round(2)})
spdf["genere"] = spdf.specie.str.split().str[0]
spdf["famiglia"] = [fam_of.get(g, "") for g in spdf.genere]
spdf.to_csv(os.path.join(OUT, "specie_2025.csv"), index=False, sep=";")
gen = E25.genere.value_counts()
gdf = pd.DataFrame({"genere": gen.index, "nome": [GEN_IT.get(g, "") for g in gen.index], "alberi": gen.values,
                    "quota_pct": (100 * gen.values / N25).round(2), "famiglia": [fam_of.get(g, "") for g in gen.index]})
gdf.to_csv(os.path.join(OUT, "generi_2025.csv"), index=False, sep=";")
fam = E25.famiglia.value_counts()

det = spdf[determinata(spdf.specie)]
top_sp = [[r.nome_comune, r.specie, int(r.alberi), float(r.quota_pct)] for r in det.head(15).itertuples()]
top_gen = [[r.genere, r.nome, int(r.alberi), float(r.quota_pct)] for r in gdf.head(15).itertuples()]
top_fam = [[f, int(c), round(100 * c / N25, 2)] for f, c in fam.head(5).items()]
check("platano comune (alberi)", top_sp[0][2], 16618)
check("Acer (alberi)", top_gen[0][2], 27613)
senza_specie = int(E25.specie_binomio_normalizzata.str.endswith(" spp").sum())
check("alberi con specie non indicata (spp) 2025", senza_specie, RIEP["citta_per_edizione"][2]["con_epiteto_spp"])

# cambiamenti per genere (dal file di fase 1, gia' calcolato per id)
cg = pd.read_csv(os.path.join(PU, "cambiamenti_per_genere_2023_2025.csv"), sep=";")
cg["nome"] = [GEN_IT.get(g, "") for g in cg.genere]
cg.to_csv(os.path.join(OUT, "cambiamenti_per_genere_2023_2025.csv"), index=False, sep=";")
cgtop = cg.sort_values("saldo")
cambi_gen = [[r.genere, r.nome, int(r.tot_2023), int(r.rimossi), int(r.aggiunti), int(r.saldo)] for r in cgtop.itertuples()]

# ---------------------------------------------------------------- CAP e reddito
cap = pd.read_csv(os.path.join(PU, "cap_alberi_reddito.csv"), sep=";")
rho, _ = spearmanr(cap.alberi_per_1000ab, cap.imponibile_medio_2024)
check("Spearman CAP alberi/1000 ab vs imponibile", round(float(rho), 3), RIEP["cap_spearman_alberi_per_1000ab_vs_imponibile_2024"][0], 0.0006)
big = nil[nil.in_classifica]
rho2, _ = spearmanr(big.alberi_per_1000ab_2025, big.abitanti_per_km2)
check("Spearman NIL alberi/1000 ab vs abitanti/km2", round(float(rho2), 3), RIEP["nil_spearman_alberi_per_1000ab_vs_abitanti_per_km2"][0], 0.0006)
capo = pd.DataFrame({"cap": cap.CAP.astype(int), "zona_piu_frequente": [str(z).title().replace("Q.Re", "Q.re").replace("P.Ta", "P.ta").replace("S.", "S.") for z in cap.NIL_piu_frequente],
                     "residenti_stimati": cap.residenti_stimati.round(0).astype(int), "imponibile_medio_2024_euro": cap.imponibile_medio_2024.round(0).astype(int),
                     "alberi_2025": cap.alberi_2025.astype(int), "alberi_per_1000_abitanti": cap.alberi_per_1000ab.round(1)})
capo.to_csv(os.path.join(OUT, "cap_alberi_reddito.csv"), index=False, sep=";")
cap_pts = [[int(r.cap), r.zona_piu_frequente, int(r.imponibile_medio_2024_euro), float(r.alberi_per_1000_abitanti), int(r.alberi_2025)] for r in capo.itertuples()]

# ---------------------------------------------------------------- alberi monumentali
mo = pd.read_csv(os.path.join(A, "raw", "comune_ds2489", "alberi_monumentali_031123_final.csv"), sep=";", dtype=str)
assert len(mo) == 13
mon = []
for r in mo.itertuples(index=False):
    d = r._asdict() if hasattr(r, "_asdict") else None
mo.columns = [c.strip() for c in mo.columns]
for _, r in mo.iterrows():
    mon.append({"id": r["ID"], "luogo": r["LOCALITÀ"].strip(), "specie": r["SPECIE - NOME SCIENTIFICO"].strip(), "nome": r["SPECIE - NOME VOLGARE"].strip(),
                "circonferenza_cm": r["CIRCONFERENZA FUSTO (cm)"].strip(), "altezza_m": r["ALTEZZA (m)"].strip(),
                "nil": nomi.get(int(r["ID_NIL"]), r["NIL"].title()), "lon": round(float(r["LONG_X_4326"]), 6), "lat": round(float(r["LAT_Y_4326"]), 6),
                "scheda_del_comune": r["Link"].strip()})
pd.DataFrame(mon).to_csv(os.path.join(OUT, "monumentali.csv"), index=False, sep=";")

# ---------------------------------------------------------------- Forestami: solo i totali (numeri) con link
fo = pd.read_csv(os.path.join(PU, "forestami_piantagioni.csv"), sep=";")
tot_fo = int(fo.numero_piante.sum())
check("Forestami: totale piante delle 52 piantagioni", tot_fo, 72571)
forestami = {"piantagioni": int(len(fo)), "piante_totali": tot_fo, "siti_in_citta": 8, "piante_in_citta": 5760,
             "nota": "Totali contati dalle pagine pubbliche delle piantagioni (campo 'Numero di piante'): comprendono alberi e arbusti, non sono nel censimento del Comune e non si possono confrontare. Nessun altro contenuto del sito e' ripubblicato.",
             "link": "https://forestami.org/"}
assert len(fo) == 52

# ---------------------------------------------------------------- riepilogo per la pagina
ce = RIEP["citta_per_edizione"]
cam = [c for c in RIEP["cambiamenti"] if c["da"] == "2023-03-31" and c["a"] == "2025-03-31"][0]
cam1 = [c for c in RIEP["cambiamenti"] if c["da"] == "2023-03-31" and c["a"] == "2024-03-31"][0]
cam2 = [c for c in RIEP["cambiamenti"] if c["da"] == "2024-03-31" and c["a"] == "2025-03-31"][0]
ab24 = int(RIEP["nil_abitanti_2024"])
area = float(RIEP["nil_area_totale_km2_poligoni"])
mis = RIEP["misure_ultima_edizione"]
riep = {
    "meta": {"edizioni": EDS, "ultima": "2025-03-31", "scaricato": "2026-11-01", "pagina_generata_da": "alberi/scripts/pagina.py",
             "abitanti_anno": 2024, "nil": 88, "nil_in_classifica": int(nil.in_classifica.sum()), "soglia_abitanti": 5000},
    "citta": {"alberi": {"2023": N23, "2024": N24, "2025": N25}, "abitanti_2024": ab24, "area_km2": area,
              "per_1000_abitanti": RIEP["citta_alberi_per_1000ab_2025"], "per_km2": RIEP["citta_alberi_per_km2_2025"],
              "abitanti_per_albero": round(ab24 / N25, 1), "senza_nil_2025": int(E25.id_nil.isna().sum()),
              "tipo_localita_pct": RIEP["tipo_localita_pct"], "cimiteri_alberi": cimiteri_alberi,
              "mediana_nil_per_1000_abitanti": RIEP["nil_mediana_alberi_per_1000ab"], "rapporto_max_min_nil": RIEP["nil_rapporto_max_min_per_abitante"]},
    "cambi": {"da": "2023-03-31", "a": "2025-03-31", "saldo": cam["saldo"], "saldo_pct": cam["saldo_pct"], "spariti": cam["rimossi"], "nuovi": cam["aggiunti"],
              "in_comune": cam["in_comune"], "saldo_2023_2024": cam1["saldo"], "saldo_2023_2024_pct": cam1["saldo_pct"],
              "saldo_2024_2025": cam2["saldo"], "saldo_2024_2025_pct": cam2["saldo_pct"],
              "spariti_tronco_max12_pct": tr_pct, "spariti_scheda_dal_2019": n_rim_2019, "spariti_scheda_dal_2019_pct": round(100 * n_rim_2019 / len(rim), 2),
              "confronto_2023_tutti_tronco_max12_pct": base_tr, "confronto_2023_tutti_scheda_dal_2019_pct": base_2019,
              "confronto_2023_rimasti_tronco_max12_pct": rimasti_tr, "confronto_2023_rimasti_scheda_dal_2019_pct": rimasti_2019,
              "nuovi_scheda_nel_periodo_pct": cam["aggiunti_con_anno_scheda_nel_periodo_pct"], "nuovi_scheda_precedente_pct": cam["aggiunti_con_anno_scheda_precedente_pct"],
              "nuovi_per_anno_scheda": RIEP["aggiunti_2023_2025_per_anno_scheda"],
              "tronco_invariato_pct": cam["in_comune_tronco_invariato_pct"], "specie_cambiata": cam["in_comune_specie_cambiata"],
              "nil_con_meno": int((nil.variazione_2023_2025 < 0).sum()), "nil_con_piu": int((nil.variazione_2023_2025 > 0).sum())},
    "regola": {"edizioni": [{"ed": c["edizione"], "specie_pct": c["quota_specie_piu_frequente_pct"], "genere_pct": c["quota_genere_piu_frequente_pct"],
                             "famiglia_pct": c["quota_famiglia_piu_frequente_pct"], "rispettata": bool(c["regola_10_20_30_rispettata"])} for c in ce],
               "specie_top": top_sp[0][1], "specie_top_nome": top_sp[0][0], "genere_top": "Acer", "famiglia_top": top_fam[0][0],
               "caso_peggiore_specie_pct": ce[2]["quota_specie_top_caso_peggiore_pct(spp_incluse)"], "specie_non_indicata": senza_specie,
               "nil_specie_oltre10": n_sp10, "nil_genere_oltre20": n_g20, "nil_famiglia_oltre30": n_f30, "nil_totale": 88,
               "calocedri_citta": cal_tot, "calocedri_nei_cimiteri": cal_cim, "calocedri_nil_maggiore": cal_mag, "calocedri_nil_maggiore_cimiteri": cal_mag_cim,
               "alberi_nil_maggiore": int(mag.alberi_2025)},
    "top_specie": top_sp, "top_generi": top_gen, "top_famiglie": top_fam,
    "specie_distinte_2025": int(det.shape[0]), "generi_2025": int(gen.size), "famiglie_2025": int(fam.size),
    "cambi_genere": cambi_gen,
    "misure": {"tronco_8cm_pct": mis["tronco_esattamente_8cm_pct"], "altezza_5m_pct": mis["altezza_esattamente_5m_pct"], "chioma_2m_pct": mis["chioma_esattamente_2m_pct"],
               "tripletta_pct": mis["tripletta_8cm_5m_2m_pct"], "tripletta_n": mis["tripletta_n"], "tronco_invariato_pct": cam["in_comune_tronco_invariato_pct"],
               "data_21_ottobre_pct": RIEP["data_inizio_scheda"]["quota_21_ottobre_pct"]},
    "confronti": {"cap_n": int(len(cap)), "cap_spearman": RIEP["cap_spearman_alberi_per_1000ab_vs_imponibile_2024"], "cap_spearman_assoluti": RIEP["cap_spearman_alberi_totali_vs_imponibile_2024"],
                  "cap_punti": cap_pts, "nil_spearman_densita": RIEP["nil_spearman_alberi_per_1000ab_vs_abitanti_per_km2"],
                  "nil_spearman_verde_satellite": RIEP["nil_spearman_alberi_per_km2_vs_indice_verde_SPOTTED"]},
    "forestami": forestami,
    "monumentali": mon,
    "origine": {
        "citta.alberi": "alberi/pulito/alberi.csv (3 edizioni), righe per edizione; riepilogo.json > citta_per_edizione[].alberi",
        "citta.per_1000_abitanti e per_km2": "alberi/pulito/riepilogo.json > citta_alberi_per_1000ab_2025, citta_alberi_per_km2_2025 (abitanti ds205 2024, area dai poligoni NIL)",
        "cambi": "alberi/pulito/riepilogo.json > cambiamenti[2023->2025] e rimossi_2023_2025_*; ricalcolati per id da alberi.csv in pagina.py (controllo OK)",
        "cambi.confronto_2023": "calcolato in pagina.py da alberi.csv (edizione 2023): quota di tutti gli alberi e dei soli alberi che restano nel 2025 con tronco <= 12 cm / scheda dal 2019",
        "regola": "alberi/pulito/citta_per_edizione.csv (quote massime) e riepilogo.json; NIL sopra soglia: ricalcolati da alberi.csv (analisi.py: nil_alberi.csv)",
        "top_specie/top_generi/top_famiglie": "alberi.csv edizione 2025; specie_binomio_normalizzata, genere, famiglia; nome comune e famiglia scritti a mano (scripts/nomi_specie.csv, taxonomia_genere.csv)",
        "confronti.cap": "alberi/pulito/cap_alberi_reddito.csv: alberi_per_1000ab, imponibile_medio_2024 (ds3009 Comune di Milano, CC BY; CAP degli alberi stimato)",
        "confronti.nil": "alberi/pulito/riepilogo.json > nil_spearman_*",
        "monumentali": "alberi/raw/comune_ds2489/alberi_monumentali_031123_final.csv",
        "forestami": "alberi/pulito/forestami_piantagioni.csv: solo somma di numero_piante",
        "metodo (331 punti entro 100 m, 87 oltre, 41 alberi senza NIL, 91% degli identificativi 2023 ritrovati)": "alberi/pulito/controlli_pulizia.json (punti_fuori_da_ogni_NIL, fuori_NIL_*), NOTE.md 2.1 e 3",
        "esagoni": "alberi.csv edizione 2025, lon/lat, griglia esagonale in UTM 32N (EPSG:32632), larghezza 250 m"
    }
}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

print()
print("FILE:")
tot = 0
for f in sorted(os.listdir(OUT)):
    s = os.path.getsize(os.path.join(OUT, f)); tot += s
    print(f"  {f:45s} {s/1024:8.1f} KB")
print(f"  totale {tot/1024:.1f} KB")
if AVVISI:
    print("\nATTENZIONE:")
    for a in AVVISI:
        print("  ", a)
    sys.exit(1)
print("controlli tutti ok")
