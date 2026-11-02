"""Pulizia e riepiloghi (fase 1): ambiti dei piani approvati/adottati del PGT Milano 2030 (Tavola R02, CC BY 4.0).
Uso (percorsi assoluti): python -I -X utf8 build.py <rigenerazione_dir> <milano_in_dati_dir>
Legge: rigenerazione/raw/pgt/*.geojson; i quartieri (NIL) di citta-15-minuti; i raster ISPRA del consumo di suolo (suolo/raw/raster);
       docs/quartieri-che-cambiano/data/nil.csv (variazione prezzi OMI), docs/costruzioni/data/nil.csv, docs/suolo/data/nil_suolo.csv.
Scrive in rigenerazione/pulito/: ambiti_progetti.csv, nil_rigenerazione.csv, tipi.csv, riepilogo.json, build_log.txt.
Non usa il servizio "Mappa dei progetti di Rigenerazione urbana" (Atlante): licenza "Solo consultazione autorizzata"."""
import sys, os, json, collections
import numpy as np, pandas as pd, pyproj, shapely, rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import unary_union
from scipy.stats import spearmanr

R, P = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(R, "raw", "pgt"), os.path.join(R, "pulito")
os.makedirs(PU, exist_ok=True)
LOG = open(os.path.join(PU, "build_log.txt"), "w", encoding="utf8")
def say(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.write(s + "\n"); LOG.flush()

t4326_32632 = pyproj.Transformer.from_crs(4326, 32632, always_xy=True)
t4326_7794 = pyproj.Transformer.from_crs(4326, 7794, always_xy=True)
def tr(t):
    return lambda g: shapely.transform(g, lambda a: np.column_stack(t.transform(a[:, 0], a[:, 1])))
utm, rdn = tr(t4326_32632), tr(t4326_7794)

# ------------------------------------------------------------------ NIL
nf = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
NOME = dict(zip(ana.nil, ana.nil_nome))
NIL = {}
for f in nf["features"]:
    i = int(f["properties"]["ID_NIL"]); g = shape(f["geometry"])
    NIL[i] = {"nome": NOME.get(i) or f["properties"]["NIL"].title(), "g4326": g, "gutm": utm(g), "grdn": rdn(g)}
assert len(NIL) == 88
for i, v in NIL.items(): v["area_ha"] = v["gutm"].area / 1e4
CITTA_HA = sum(v["area_ha"] for v in NIL.values())
say("NIL", len(NIL), "area totale NIL ha", round(CITTA_HA, 1))

# ------------------------------------------------------------------ ambiti (R02 livello 10)
feats = json.load(open(os.path.join(RAW, "r02_provvedimenti_in_itinere.geojson"), encoding="utf8"))["features"]
assert len(feats) == 405
vuoti = [f["properties"]["objectid"] for f in feats if not f["geometry"] or not f["geometry"].get("coordinates")]
say("record senza geometria (scartati):", vuoti)  # objectid 444, 'Fiera - CityLife': 1 record su 405
feats = [f for f in feats if f["geometry"] and f["geometry"].get("coordinates")]
GRUPPO = {
    "Accordi di Programma": "Accordi di programma e intese", "Accordi di Programma/PII": "Accordi di programma e intese",
    "Accordo di Programma Scali": "Accordi di programma e intese", "Accordo Quadro": "Accordi di programma e intese",
    "Protocollo di Intesa": "Accordi di programma e intese",
    "PII": "Programmi integrati e di recupero (PII, PRU, PIR, Zona C)", "PRU": "Programmi integrati e di recupero (PII, PRU, PIR, Zona C)",
    "PIR": "Programmi integrati e di recupero (PII, PRU, PIR, Zona C)", "Zona C": "Programmi integrati e di recupero (PII, PRU, PIR, Zona C)",
    "PA": "Piani attuativi (PA)", "Variante": "Piani attuativi (PA)",
    "PII (Opera esterna)": "Opere esterne di PII e PA", "PA (Opera esterna)": "Opere esterne di PII e PA",
    "Convenzione": "Piccoli lotti: convenzioni, istanze, bandi", "Istanza": "Piccoli lotti: convenzioni, istanze, bandi", "Bando": "Piccoli lotti: convenzioni, istanze, bandi",
    "Fondo Comune Milano 1": "Lotti dei fondi del Comune", "Fondo Comune Milano 2": "Lotti dei fondi del Comune",
}
assert set(f["properties"]["tipopianif"] for f in feats) <= set(GRUPPO), set(f["properties"]["tipopianif"] for f in feats) - set(GRUPPO)
STATO = {"Ambito attuato": "attuato", "Ambito attuato in parte": "attuato in parte", "Ambito non attuato": "non attuato", "Area non attuata": "area non attuata"}
rows = []
for f in feats:
    p = f["properties"]; g = shape(f["geometry"])
    assert g.is_valid or True
    gu = utm(g); gu = gu if gu.is_valid else gu.buffer(0)
    rows.append({"oid": p["objectid"], "tipo": p["tipopianif"], "gruppo": GRUPPO[p["tipopianif"]], "nome": (p["nome"] or "").strip(),
                 "stato": STATO[p["tipoarea"]], "stato_file": p["statoattuazione"], "gutm": gu, "grdn": rdn(g if g.is_valid else g.buffer(0))})
poly = pd.DataFrame(rows)
poly["area_ha"] = [g.area / 1e4 for g in poly.gutm]
say("poligoni", len(poly), "somma aree ha", round(poly.area_ha.sum(), 1), "senza nome:", int((poly.nome == "").sum()))
# controllo area: attributo del file vs mia
att = np.array([f["properties"]["st_area(shape)"] or np.nan for f in feats]) / 1e4
say("controllo area: rapporto mediano attributo/calcolata", round(float(np.nanmedian(att / poly.area_ha.values)), 4))

# sovrapposizioni: area dell'unione contro somma
U = unary_union(list(poly.gutm)); say("unione di tutti gli ambiti ha", round(U.area / 1e4, 1), "contro somma", round(poly.area_ha.sum(), 1))
dup_share = 1 - (U.area / 1e4) / poly.area_ha.sum()
by_g = {}
for gname, d in poly.groupby("gruppo"):
    u = unary_union(list(d.gutm)); by_g[gname] = u
    say("  gruppo", gname, "poligoni", len(d), "somma", round(d.area_ha.sum(), 1), "unione", round(u.area / 1e4, 1))

# ------------------------------------------------------------------ progetti = (tipo, nome)
prog = []
for (tipo, nome), d in poly.groupby(["tipo", "nome"], sort=False):
    u = unary_union(list(d.gutm)); ur = unary_union(list(d.grdn))
    st = sorted(set(d.stato))
    if len(st) == 1: stato = st[0]
    elif "attuato" in st or "attuato in parte" in st: stato = "attuato in parte"
    else: stato = "non attuato"
    c = shapely.transform(u.centroid, lambda a: np.column_stack(pyproj.Transformer.from_crs(32632, 4326, always_xy=True).transform(a[:, 0], a[:, 1])))
    # NIL: quello con la maggiore intersezione
    inter = {i: u.intersection(v["gutm"]).area / 1e4 for i, v in NIL.items() if u.intersects(v["gutm"])}
    nil_p = max(inter, key=inter.get) if inter else None
    prog.append({"tipo": tipo, "gruppo": GRUPPO[tipo], "nome": nome or "(senza nome)", "stato": stato, "n_poligoni": len(d), "area_ha": u.area / 1e4,
                 "lon": c.x, "lat": c.y, "id_nil": nil_p, "nil": NIL[nil_p]["nome"] if nil_p else None, "_u": u, "_ur": ur,
                 "nil_tutti": ";".join(NIL[i]["nome"] for i in sorted(inter, key=inter.get, reverse=True))})
prog = pd.DataFrame(prog)
say("progetti (tipo+nome)", len(prog), "nomi distinti", prog.nome.nunique())

# ------------------------------------------------------------------ raster: consumo di suolo dentro gli ambiti
RASTER = os.path.join(P, "suolo", "raw", "raster")
bnd = U.bounds  # utm, serve solo per la finestra: uso rdn
Urdn = unary_union(list(poly.grdn))
bnd = unary_union([v["grdn"] for v in NIL.values()]).bounds
cons = lambda a: (a == 1) | (a == 11) | (a == 12) | ((a >= 111) & (a <= 126))
C, org = {}, {}
for y, fn in {2006: "SC_2006_RDN_v6.tif", 2012: "SC_2012_RDN_v6.tif", 2025: "SC_2025_RDN_v8.tif"}.items():
    with rasterio.open(os.path.join(RASTER, fn)) as r:
        w = from_bounds(*bnd, transform=r.transform).round_offsets().round_lengths()
        a = r.read(1, window=w); t = r.window_transform(w)
    C[y] = cons(a); org[y] = (t.c, t.f); trf = t; shp = a.shape
assert len(set(org.values())) == 1
nid = rasterize([(v["grdn"], i) for i, v in NIL.items()], out_shape=shp, transform=trf, fill=0, dtype="int32")
inside = nid > 0
NEW = (~C[2012]) & C[2025] & inside
REST = C[2012] & (~C[2025]) & inside
mask_all = rasterize([(Urdn, 1)], out_shape=shp, transform=trf, fill=0, dtype="uint8").astype(bool) & inside
say("raster pixel", shp, "ambiti pixel ha", mask_all.sum() / 100)
def zs(mask):
    return {"ha": mask.sum() / 100, "cons2012": (C[2012] & mask).sum() / 100, "cons2025": (C[2025] & mask).sum() / 100,
            "nuovo": (NEW & mask).sum() / 100, "ripristino": (REST & mask).sum() / 100}
Z_all = zs(mask_all)
say("ambiti (tutti):", Z_all)
Z_city = zs(inside)
say("citta:", Z_city)
prog["nuovo_2012_2025_ha"] = 0.0; prog["consumato_2012_pct"] = np.nan; prog["consumato_2025_pct"] = np.nan; prog["ripristino_2012_2025_ha"] = 0.0
for k, r in prog.iterrows():
    m = rasterize([(r._ur, 1)], out_shape=shp, transform=trf, fill=0, dtype="uint8").astype(bool) & inside
    z = zs(m)
    if z["ha"] > 0:
        prog.at[k, "nuovo_2012_2025_ha"] = z["nuovo"]; prog.at[k, "ripristino_2012_2025_ha"] = z["ripristino"]
        prog.at[k, "consumato_2012_pct"] = 100 * z["cons2012"] / z["ha"]; prog.at[k, "consumato_2025_pct"] = 100 * z["cons2025"] / z["ha"]
# per gruppo e per stato (maschera unione)
Z_gruppo, Z_stato = {}, {}
for gname, u in by_g.items():
    m = rasterize([(rdn(shapely.transform(u, lambda a: np.column_stack(pyproj.Transformer.from_crs(32632, 4326, always_xy=True).transform(a[:, 0], a[:, 1])))), 1)], out_shape=shp, transform=trf, fill=0, dtype="uint8").astype(bool) & inside
    Z_gruppo[gname] = zs(m)
for s, d in poly.groupby("stato"):
    m = rasterize([(g, 1) for g in d.grdn], out_shape=shp, transform=trf, fill=0, dtype="uint8").astype(bool) & inside
    Z_stato[s] = zs(m)
say("per gruppo:", {k: round(v["nuovo"], 1) for k, v in Z_gruppo.items()})

# per NIL
nil_rows = []
for i, v in NIL.items():
    inter = U.intersection(v["gutm"]).area / 1e4
    mi = (nid == i)
    r = {"id_nil": i, "nil": v["nome"], "area_ha": v["area_ha"], "ambiti_ha": inter, "ambiti_pct": 100 * inter / v["area_ha"],
         "nuovo_nil_ha": (NEW & mi).sum() / 100, "nuovo_in_ambiti_ha": (NEW & mi & mask_all).sum() / 100,
         "consumato_2012_ambiti_pct": 100 * (C[2012] & mi & mask_all).sum() / max(1, (mi & mask_all).sum()) if (mi & mask_all).sum() else np.nan}
    for gname, u in by_g.items():
        r["ha_" + gname.split(" (")[0].split(":")[0].replace(" ", "_").lower()] = u.intersection(v["gutm"]).area / 1e4
    for s, d in poly.groupby("stato"):
        r["ha_stato_" + s.replace(" ", "_")] = unary_union(list(d.gutm)).intersection(v["gutm"]).area / 1e4
    r["n_progetti"] = int(sum(1 for _, p in prog.iterrows() if p.id_nil == i))
    nil_rows.append(r)
nil = pd.DataFrame(nil_rows)

# ------------------------------------------------------------------ incroci con altri filoni
qc = pd.read_csv(os.path.join(P, "docs", "quartieri-che-cambiano", "data", "nil.csv"))[["id_nil", "residenti_2024", "in_classifica", "prezzo_var", "costruzioni_100"]]
co = pd.read_csv(os.path.join(P, "docs", "costruzioni", "data", "nil.csv"), sep=";")[["id_nil", "nuove_abitazioni_2014_2024", "nuove_abitazioni_ogni_1000_abitanti_2024"]]
su = pd.read_csv(os.path.join(P, "docs", "suolo", "data", "nil_suolo.csv"), sep=";")[["id_nil", "nuovo_2012_2025_ha", "pct_2025"]]
cp = pd.read_csv(os.path.join(P, "docs", "case-popolari", "data", "nil.csv"), sep=";")[["id_nil", "quota_canone_ALER_2016_pct", "edifici_ALER_2016", "abitazioni_2023"]]
for d in (qc, co, su, cp): d["id_nil"] = d.id_nil.astype(int)
nil = nil.merge(qc, on="id_nil", how="left").merge(co, on="id_nil", how="left").merge(su, on="id_nil", how="left").merge(cp, on="id_nil", how="left")
# controllo: il mio nuovo consumo per NIL coincide con quello della pagina suolo
diff = (nil.nuovo_nil_ha - nil.nuovo_2012_2025_ha).abs().max()
say("controllo nuovo consumo per NIL, scarto massimo rispetto a docs/suolo (ha):", round(float(diff), 3))
assert diff < 0.1

ok = nil[nil.in_classifica == 1].copy()
def sp(x, y, d):
    d = d.dropna(subset=[x, y]); r = spearmanr(d[x], d[y])
    rng = np.random.default_rng(1); n = len(d); bs = []
    for _ in range(2000):
        ix = rng.integers(0, n, n); bs.append(spearmanr(d[x].values[ix], d[y].values[ix])[0])
    return {"rho": float(r[0]), "p": float(r[1]), "n": int(n), "ic": [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]}
corr = {
    "ambiti_pct_vs_prezzo_var": sp("ambiti_pct", "prezzo_var", ok),
    "ambiti_pct_vs_nuove_abitazioni_1000": sp("ambiti_pct", "nuove_abitazioni_ogni_1000_abitanti_2024", ok),
    "ambiti_pct_vs_nuovo_suolo_ha": sp("ambiti_pct", "nuovo_nil_ha", nil),
    "ambiti_pct_vs_quota_aler": sp("ambiti_pct", "quota_canone_ALER_2016_pct", ok),
}
say("correlazioni", json.dumps(corr))
# confronto tra gruppi di NIL: 'molto coperti' (>= 10%) e gli altri
ok["gr"] = np.where(ok.ambiti_pct >= 10, "alta", "bassa")
conf = ok.groupby("gr").agg(n=("id_nil", "count"), prezzo_var_med=("prezzo_var", "median"), abit_1000_med=("nuove_abitazioni_ogni_1000_abitanti_2024", "median"),
                            aler_med=("quota_canone_ALER_2016_pct", "median")).reset_index()
say(conf.to_string())

# ------------------------------------------------------------------ altri strati del PGT
def L(n): return json.load(open(os.path.join(RAW, n + ".geojson"), encoding="utf8"))["features"]
def proj_area(fs):
    return [(f["properties"], utm(shape(f["geometry"])).area / 1e4) for f in fs]
pa = proj_area(L("r02_piani_attuativi_obbligatori"))
pa_g = collections.defaultdict(float)
for p, a in pa: pa_g[p["nome"]] += a
ers = proj_area(L("r02_ers")); gfu = proj_area(L("r02_grandi_funzioni_urbane")); ra = proj_area(L("r02_rigenerazione_ambientale"))
say("PA obbligatori: poligoni", len(pa), "nomi", len(pa_g), "ha", round(sum(pa_g.values()), 1))
say("ERS aree", len(ers), "ha", round(sum(a for _, a in ers), 2)); say("Grandi funzioni urbane", len(gfu), round(sum(a for _, a in gfu), 1))
say("Ambiti di rigenerazione ambientale", len(ra), round(sum(a for _, a in ra), 1))
ru = unary_union([utm(shape(f["geometry"])).buffer(0) for f in L("r02_rigenerazione_ambientale")])
say("rigenerazione ambientale: unione ha", round(ru.area / 1e4, 1), " intersezione con ambiti ha", round(ru.intersection(U).area / 1e4, 1))
r10 = L("r10_rigenerazione")
ur10 = unary_union([utm(shape(f["geometry"])).buffer(0) for f in r10])
say("R10 'Ambiti di Rigenerazione' (1601 poligoni): unione ha", round(ur10.area / 1e4, 1), "; intersezione con ambiti R02 liv.10 ha", round(ur10.intersection(U).area / 1e4, 1))

# ------------------------------------------------------------------ scrittura
prog_out = prog.drop(columns=["_u", "_ur"]).sort_values("area_ha", ascending=False)
prog_out.round(4).to_csv(os.path.join(PU, "ambiti_progetti.csv"), sep=";", index=False)
nil.round(4).to_csv(os.path.join(PU, "nil_rigenerazione.csv"), sep=";", index=False)
tipi = poly.groupby(["gruppo", "tipo"]).agg(poligoni=("oid", "count"), somma_ha=("area_ha", "sum")).reset_index()
tipi = tipi.merge(prog.groupby("tipo").agg(progetti=("nome", "count")).reset_index(), on="tipo")
tipi.round(3).to_csv(os.path.join(PU, "tipi.csv"), sep=";", index=False)
stati = poly.groupby("stato").agg(poligoni=("oid", "count"), somma_ha=("area_ha", "sum")).reset_index()
RIEP = {
    "data_download": "2026-11-01", "nil_ha_totali": CITTA_HA, "n_poligoni": len(poly), "n_record_file": 405, "senza_geometria": len(vuoti), "n_progetti": len(prog), "n_nomi": int(prog.nome.nunique()),
    "somma_ha": float(poly.area_ha.sum()), "unione_ha": float(U.area / 1e4), "quota_sovrapposta_pct": float(100 * dup_share), "ambiti_pct_citta": float(100 * U.area / 1e4 / CITTA_HA),
    "gruppi": {g: {"poligoni": int((poly.gruppo == g).sum()), "progetti": int((prog.gruppo == g).sum()), "unione_ha": float(u.area / 1e4), **{k: float(v) for k, v in Z_gruppo[g].items()}} for g, u in by_g.items()},
    "stati": {s: {"poligoni": int(d.shape[0]), "somma_ha": float(d.area_ha.sum()), **{k: float(v) for k, v in Z_stato[s].items()}} for s, d in poly.groupby("stato")},
    "stati_progetti": prog.groupby("stato").agg(n=("nome", "count"), ha=("area_ha", "sum")).reset_index().to_dict("records"),
    "tipi": tipi.to_dict("records"),
    "suolo": {"ambiti": Z_all, "citta": Z_city, "quota_nuovo_in_ambiti_pct": float(100 * Z_all["nuovo"] / Z_city["nuovo"]),
              "quota_ambiti_su_citta_pct": float(100 * Z_all["ha"] / Z_city["ha"]), "ambiti_gia_consumati_2012_pct": float(100 * Z_all["cons2012"] / Z_all["ha"]),
              "citta_consumata_2012_pct": float(100 * Z_city["cons2012"] / Z_city["ha"])},
    "correlazioni": corr, "confronto_gruppi_nil": conf.to_dict("records"),
    "pa_obbligatori": [{"nome": k, "ha": float(v)} for k, v in sorted(pa_g.items(), key=lambda x: -x[1])],
    "ers": {"aree": len(ers), "ha": float(sum(a for _, a in ers)), "elenco": [{"indirizzo": p["indirizzo"], "ha": float(a)} for p, a in ers]},
    "grandi_funzioni": [{"nome": p["nome"], "tipo": p["tipo"], "ha": float(a)} for p, a in gfu],
    "rig_ambientale": {"n": len(ra), "ha_somma": float(sum(a for _, a in ra)), "ha_unione": float(ru.area / 1e4), "ha_dentro_ambiti": float(ru.intersection(U).area / 1e4)},
    "r10_rigenerazione": {"n": len(r10), "ha_unione": float(ur10.area / 1e4), "ha_dentro_ambiti": float(ur10.intersection(U).area / 1e4)},
}
json.dump(RIEP, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=float)
say("scritto in", PU)
