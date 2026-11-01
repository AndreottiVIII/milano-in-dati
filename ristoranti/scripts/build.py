"""Fase 1, parte pulizia e riepiloghi (solo se il verdetto sulla freschezza e' positivo).
Uso: python -I -X utf8 build.py <ristoranti_abs> <milano-in-dati_abs>
Legge raw/osm/osm_milano_food_overpass.json (tutti i tag), il registro del Comune (ds58, ds59, ds250) e la copia 2019 (Wayback).
Scrive in pulito/: locali.csv, nil_locali_per_1000ab.csv, nil_cucine.csv, cucine_concentrazione.csv, locali_milanesi.csv, registro_2019_2026_nil.csv, build_log.json"""
import sys, os, json, re
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Transformer

D, P = sys.argv[1], sys.argv[2]
RAW, OUT = os.path.join(D, "raw"), os.path.join(D, "pulito")
NOW = pd.Timestamp("2026-11-01", tz="UTC")
L = {}
SIX = ["restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream"]

# ---------- NIL e abitanti
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
names = dict(zip(ids, [f["properties"]["NIL"] for f in g["features"]]))
tree = STRtree(polys)
Tu = Transformer.from_crs(4326, 32632, always_xy=True)
area = {i: shapely.transform(p, lambda c: np.column_stack(Tu.transform(c[:, 0], c[:, 1]))).area / 1e6 for i, p in zip(ids, polys)}
d205 = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"), sep=None, engine="python")
d205 = d205[d205.NIL.notna()].copy()
d205["id_nil"] = d205.NIL.astype(int)
pop = d205[d205.Anno == 2024].set_index("id_nil")["Totale"]


def assign_nil(lon, lat):
    pi, gi = tree.query(shapely.points(np.asarray(lon, float), np.asarray(lat, float)), predicate="within")
    out = np.full(len(lon), -1)
    out[pi] = [ids[j] for j in gi]
    return out


# ---------- mappa cucine OSM
GROUPS = {
    "pizza": {"pizza", "italian_pizza", "pizzeria"},
    "italiana": {"italian", "regional", "pasta", "romana", "napoletana", "pugliese", "sicilian", "sardinian", "tuscan", "lombard", "milanese", "risotto", "piadina", "piemontese", "ligurian", "emilian", "bolognese", "roman", "neapolitan", "calabrian", "trattoria", "osteria"},
    "giapponese_sushi": {"japanese", "sushi", "ramen", "izakaya", "udon", "yakitori", "sashimi", "tempura", "teppanyaki", "okonomiyaki"},
    "cinese": {"chinese", "dim_sum", "hot_pot", "hotpot", "fried_skewers", "dumplings", "cantonese", "sichuan", "chinese_noodles"},
    "altro_asiatico": {"asian", "korean", "thai", "vietnamese", "filipino", "noodle", "noodles", "indonesian", "malaysian", "singaporean", "taiwanese", "mongolian"},
    "indiana_sudasiatica": {"indian", "sri_lankan", "pakistani", "bangladeshi", "nepalese", "tibetan", "afghan"},
    "kebab_medio_oriente": {"kebab", "turkish", "lebanese", "arab", "falafel", "persian", "syrian", "israeli", "middle_eastern", "iranian", "shawarma", "doner", "uzbek", "georgian", "armenian", "kurdish", "egyptian", "levantine", "palestinian", "jordanian", "iraqi"},
    "latinoamericana": {"peruvian", "mexican", "brazilian", "argentinian", "salvadoran", "tacos", "latin_american", "colombian", "venezuelan", "ecuadorian", "chilean", "cuban", "dominican", "bolivian", "burrito", "tex-mex", "empanada", "argentine"},
    "africana": {"african", "eritrean", "ethiopian", "moroccan", "senegalese", "nigerian", "tunisian", "algerian", "somali", "ghanaian", "cameroonian", "maghreb", "couscous"},
    "hamburger_panini": {"burger", "hot_dog", "chicken", "fried_chicken", "sandwich", "american", "fast_food", "panini", "kumpir", "wings"},
    "pesce": {"seafood", "fish", "fish_and_chips", "friture"},
    "carne_griglia": {"steak_house", "meat", "barbecue", "grill", "steak", "bbq"},
    "altre_europee": {"french", "spanish", "greek", "german", "russian", "tapas", "mediterranean", "polish", "portuguese", "british", "irish", "austrian", "swiss", "scandinavian", "ukrainian", "romanian", "hungarian", "balkan", "croatian", "serbian"},
    "dolci_caffe": {"dessert", "cake", "ice_cream", "coffee_shop", "tea", "crepe", "pastry", "breakfast", "juice", "bubble_tea", "coffee", "bakery", "brunch", "chocolate", "waffle", "donut", "smoothie", "gelato", "frozen_yogurt"},
    "veg_insalate_poke": {"vegetarian", "vegan", "salad", "poke", "healthy", "bowl", "raw_food", "organic"},
    "fusion_internazionale": {"fusion", "international", "contemporary", "creative", "modern", "world"},
}
TOK2G = {t: g_ for g_, ts in GROUPS.items() for t in ts}
ETNICHE = ["giapponese_sushi", "cinese", "altro_asiatico", "indiana_sudasiatica", "kebab_medio_oriente", "latinoamericana", "africana"]


def groups_of(cuisine):
    if not isinstance(cuisine, str):
        return []
    gs = []
    for t in re.split(r"[;,]", cuisine):
        t = t.strip().lower().replace(" ", "_")
        if t in TOK2G and TOK2G[t] not in gs:
            gs.append(TOK2G[t])
    return gs


# ---------- OSM
d = json.load(open(os.path.join(RAW, "osm", "osm_milano_food_overpass.json"), encoding="utf-8"))
L["osm_timestamp_base"] = d["osm3s"]["timestamp_osm_base"]
rows = []
for e in d["elements"]:
    t = e.get("tags", {})
    lat = e.get("lat", e.get("center", {}).get("lat")); lon = e.get("lon", e.get("center", {}).get("lon"))
    rows.append(dict(fonte="osm", id=f"{e['type']}/{e['id']}", nome=t.get("name"), tipo=t.get("amenity"), tipo_dettaglio=t.get("amenity"), cucina=t.get("cuisine"),
                     lon=lon, lat=lat, ultima_modifica=e.get("timestamp"), check_date=t.get("check_date") or t.get("survey:date"), start_date=t.get("start_date"),
                     opening_hours=t.get("opening_hours"), indirizzo=(" ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x) or None), uid=e.get("uid"),
                     _tags=json.dumps({k: v for k, v in t.items() if k in ("description", "name:it", "alt_name", "diet:vegan", "diet:vegetarian", "takeaway", "brand", "operator")}, ensure_ascii=False)))
osm = pd.DataFrame(rows)

# ---------- Registro
LET = [("a", "Ristorante, trattoria, osteria con cucina e simili", "ristorante_trattoria"), ("b", "Ristorante, trattoria, osteria con cucina tipica", "ristorante_tipico"),
       ("c", "Tavole calde,self service, fast food e simili", "tavola_calda_fastfood"), ("d", "Pizzerie e simili", "pizzeria"), ("e", "Bar gastronomici e simili", "bar_gastronomico"),
       ("f", "Bar caffè e simili", "bar_caffe"), ("g", "Bar pasticceria, bar gelateria, cremeria, creperia e simili", "bar_pasticceria_gelateria"),
       ("h", "Wine bar, birreria, pub enoteche, caffetteria, sala da te e simili", "wine_bar_pub"), ("i", "Disco bar, america bar, locali serali e simili", "disco_bar_serale")]
PRIO = ["ristorante_tipico", "ristorante_trattoria", "pizzeria", "tavola_calda_fastfood", "wine_bar_pub", "disco_bar_serale", "bar_pasticceria_gelateria", "bar_gastronomico", "bar_caffe"]
OLD = [("trattoria", "ristorante_trattoria"), ("ristorante", "ristorante_trattoria"), ("osteria", "ristorante_trattoria"), ("pizzeri", "pizzeria"), ("tavola calda", "tavola_calda_fastfood"), ("tavola fredda", "tavola_calda_fastfood"), ("tav.calde", "tavola_calda_fastfood"),
       ("cibi cotti", "tavola_calda_fastfood"), ("gelateria", "bar_pasticceria_gelateria"), ("pasticc", "bar_pasticceria_gelateria"), ("birreria", "wine_bar_pub"), ("wine", "wine_bar_pub"), ("bar gastronomici", "bar_gastronomico"),
       ("bar caff", "bar_caffe"), ("bar-caffe", "bar_caffe"), ("spaccio bevande", "bar_caffe"), ("sale da ballo", "disco_bar_serale")]


def tipo_ds58(r):
    s = str(r.denominazione_pe) if isinstance(r.denominazione_pe, str) else ""
    found = [t for _, desc, t in LET if desc in s]
    # "tipica" contiene il prefisso di a: se b presente, togli a solo se a non compare da sola
    if "ristorante_tipico" in found and s.count("Ristorante, trattoria, osteria con cucina") == 1:
        found = [t for t in found if t != "ristorante_trattoria"]
    if not found:
        o = str(r.tipo_eser_storico_pe).lower() if isinstance(r.tipo_eser_storico_pe, str) else ""
        found = [t for k, t in OLD if k in o][:1]
    if not found:
        return ("non_classificato", "")
    p = next(t for t in PRIO if t in found)
    return (p, "+".join(found))


def tipo_ds250(r):
    s = " ".join(str(x) for x in (r.tipo_eser_ae, r.des_merceologica_p, r.codice_ateco) if isinstance(x, str)).lower()
    for k, t, c in (("kebab", "kebab", "kebab"), ("pizz", "pizzeria_asporto", "pizza"), ("piadin", "piadineria", "piadina"), ("gelat", "gelateria", "gelato"), ("yogurt", "gelateria", "gelato"), ("pasticc", "pasticceria", None),
                    ("rosticc", "gastronomia_rosticceria", None), ("gastronom", "gastronomia_rosticceria", None), ("pasta fresca", "pasta_fresca", None), ("sushi", "sushi_asporto", "sushi"), ("poke", "poke", "poke")):
        if k in s:
            return (t, c)
    return ("altro_artigianato_alim", None)


def rd(fn, k):
    x = pd.read_csv(os.path.join(RAW, fn), sep=";", dtype=str); x["registro"] = k; return x


r58 = rd("comune_ds58/ds58_commercio_pubblici_esercizi_in_piano.csv", "ds58_in_piano")
r59 = rd("comune_ds59/ds59_commercio_pubblici_esercizi_fuori_piano.csv", "ds59_fuori_piano")
r250 = rd("comune_ds250/ds250_artigianato_settore_alimentare.csv", "ds250_artigianato_alim")
tt = r58.apply(tipo_ds58, axis=1)
r58["tipo"] = [a for a, _ in tt]; r58["tipo_dettaglio"] = [b for _, b in tt]; r58["cucina"] = np.where(r58.tipo == "pizzeria", "pizza", None)
r59["tipo"] = "fuori_piano"; r59["tipo_dettaglio"] = r59.fuori_piano; r59["cucina"] = None
tt = r250.apply(tipo_ds250, axis=1)
r250["tipo"] = [a for a, _ in tt]; r250["tipo_dettaglio"] = r250.tipo_eser_ae.fillna(r250.des_merceologica_p); r250["cucina"] = [b for _, b in tt]
reg = pd.concat([r58, r59, r250], ignore_index=True)
reg["lon"] = pd.to_numeric(reg.LONG_X_4326, errors="coerce"); reg["lat"] = pd.to_numeric(reg.LAT_Y_4326, errors="coerce")
regs = pd.DataFrame(dict(fonte="comune_" + reg.registro.str.split("_").str[0], id=reg.Codice, nome=reg.insegna, tipo=reg.tipo, tipo_dettaglio=reg.tipo_dettaglio, cucina=reg.cucina, lon=reg.lon, lat=reg.lat,
                         ultima_modifica=None, check_date=None, start_date=None, opening_hours=None, indirizzo=reg.Ubicazione.str.replace(r"\s*\(z\.d\. \d+\)", "", regex=True), uid=None, _tags=None))
L["registro_tipo_ds58"] = r58.tipo.value_counts().to_dict()
L["registro_ds58_non_classificato_pct"] = round(100 * (r58.tipo == "non_classificato").mean(), 1)
L["registro_ds250_tipo"] = r250.tipo.value_counts().to_dict()

# ---------- locali.csv
loc = pd.concat([osm, regs], ignore_index=True)
loc["id_nil"] = assign_nil(loc.lon.fillna(-999).values, loc.lat.fillna(-999).values)
loc["nil"] = loc.id_nil.map(names)
loc["cucina_gruppi"] = loc.cucina.map(lambda c: "|".join(groups_of(c)) if isinstance(c, str) else "")
loc = loc[loc.id_nil > 0].copy()  # senza coordinate o fuori dai NIL: esclusi (registro: 427 senza coordinate)
L["locali_righe"] = loc.fonte.value_counts().to_dict()
L["registro_escluso_senza_coordinate"] = int(reg.lon.isna().sum())
cols = ["fonte", "id", "nome", "tipo", "cucina", "lon", "lat", "id_nil", "nil", "ultima_modifica", "tipo_dettaglio", "cucina_gruppi", "check_date", "start_date", "opening_hours", "indirizzo"]
loc[cols].to_csv(os.path.join(OUT, "locali.csv"), sep=";", index=False, encoding="utf-8-sig")

# ---------- 1. locali per 1000 abitanti per NIL
o6 = loc[(loc.fonte == "osm") & loc.tipo.isin(SIX)]
n = pd.DataFrame({"nil": pd.Series(names)})
n["abitanti_2024"] = pop; n["area_km2"] = pd.Series(area).round(3)
n["osm_6tipi"] = o6.groupby("id_nil").size()
for t in SIX:
    n[f"osm_{t}"] = o6[o6.tipo == t].groupby("id_nil").size()
n["registro_in_piano_ds58"] = loc[loc.fonte == "comune_ds58"].groupby("id_nil").size()
n["registro_fuori_piano_ds59"] = loc[loc.fonte == "comune_ds59"].groupby("id_nil").size()
n["registro_artigianato_ds250"] = loc[loc.fonte == "comune_ds250"].groupby("id_nil").size()
n = n.fillna(0)
n["osm_per_1000ab"] = (1000 * n.osm_6tipi / n.abitanti_2024).round(2)
n["ds58_per_1000ab"] = (1000 * n.registro_in_piano_ds58 / n.abitanti_2024).round(2)
n["osm_per_km2"] = (n.osm_6tipi / n.area_km2).round(1)
n["ds58_per_km2"] = (n.registro_in_piano_ds58 / n.area_km2).round(1)
n["rapporto_osm_su_ds58"] = (n.osm_6tipi / n.registro_in_piano_ds58.replace(0, np.nan)).round(3)
n["abitanti_per_locale_ds58"] = (n.abitanti_2024 / n.registro_in_piano_ds58.replace(0, np.nan)).round(1)
n = n.replace([np.inf, -np.inf], np.nan)
n.index.name = "id_nil"
n.to_csv(os.path.join(OUT, "nil_locali_per_1000ab.csv"), sep=";", encoding="utf-8-sig")
L["citta"] = {"abitanti_2024": int(n.abitanti_2024.sum()), "osm_6tipi": int(n.osm_6tipi.sum()), "ds58": int(n.registro_in_piano_ds58.sum()),
              "osm_per_1000ab": round(1000 * n.osm_6tipi.sum() / n.abitanti_2024.sum(), 2), "ds58_per_1000ab": round(1000 * n.registro_in_piano_ds58.sum() / n.abitanti_2024.sum(), 2),
              "ds58_59_per_1000ab": round(1000 * (n.registro_in_piano_ds58.sum() + n.registro_fuori_piano_ds59.sum()) / n.abitanti_2024.sum(), 2)}
big = n[n.abitanti_2024 >= 3000]
L["NIL_piu_locali_per_1000ab_ds58_(>=3000ab)"] = big.sort_values("ds58_per_1000ab", ascending=False).head(8)[["nil", "abitanti_2024", "registro_in_piano_ds58", "ds58_per_1000ab", "osm_6tipi", "osm_per_1000ab"]].to_dict("records")
L["NIL_meno_locali_per_1000ab_ds58_(>=3000ab)"] = big.sort_values("ds58_per_1000ab").head(8)[["nil", "abitanti_2024", "registro_in_piano_ds58", "ds58_per_1000ab", "osm_6tipi", "osm_per_1000ab"]].to_dict("records")
L["NIL_con_meno_di_3000_abitanti"] = n[n.abitanti_2024 < 3000][["nil", "abitanti_2024", "registro_in_piano_ds58", "ds58_per_1000ab"]].to_dict("records")

# ---------- 2. mix di cucine per NIL (OSM: ristoranti + fast food con tag cuisine)
rf = o6[o6.tipo.isin(["restaurant", "fast_food"])]
L["rist_fast_osm"] = {"n": len(rf), "con_cuisine": int(rf.cucina.notna().sum()), "con_cuisine_pct": round(100 * rf.cucina.notna().mean(), 1), "con_gruppo_noto": int((rf.cucina_gruppi != "").sum())}
tok = rf.cucina.dropna().str.lower().str.split(r"[;,]").explode().str.strip()
L["cuisine_token_non_mappati_top"] = tok[~tok.isin(TOK2G.keys())].value_counts().head(25).to_dict()
rfc = rf[rf.cucina_gruppi != ""].copy()
gl = list(GROUPS)
for gname in gl:
    rfc[gname] = rfc.cucina_gruppi.str.split("|").map(lambda x: gname in x)
nc = rfc.groupby("id_nil")[gl].sum()
nc.insert(0, "n_con_cucina", rfc.groupby("id_nil").size())
nc.insert(0, "n_rist_fast_osm", rf.groupby("id_nil").size())
nc = nc.reindex(ids).fillna(0).astype(int)
nc.insert(2, "pct_con_cucina", (100 * nc.n_con_cucina / nc.n_rist_fast_osm.replace(0, np.nan)).round(1))
for gname in gl:
    nc[f"{gname}_pct"] = (100 * nc[gname] / nc.n_con_cucina.replace(0, np.nan)).round(1)
nc.insert(0, "nil", pd.Series(names))
nc.index.name = "id_nil"
nc.to_csv(os.path.join(OUT, "nil_cucine.csv"), sep=";", encoding="utf-8-sig")
tot_c = len(rfc)
L["cucine_citta_(ristoranti+fast_food_OSM_con_cuisine_nota)"] = {"n": tot_c, **{gname: {"n": int(rfc[gname].sum()), "pct": round(100 * rfc[gname].mean(), 1)} for gname in gl}}

# ---------- 3. dove si concentrano le cucine etniche (location quotient per NIL)
conc = []
for gname in gl:
    ng = rfc[gname].sum()
    if ng < 20: continue
    by = rfc.groupby("id_nil")[gname].agg(["sum", "size"])
    by = by.reindex(ids).fillna(0)
    share_city = ng / tot_c
    by["lq"] = (by["sum"] / by["size"].replace(0, np.nan)) / share_city
    by["quota_del_gruppo_in_NIL_pct"] = 100 * by["sum"] / ng
    top = by[by["size"] >= 15].sort_values("lq", ascending=False).head(5)
    topn = by.sort_values("sum", ascending=False).head(5)
    conc.append(dict(gruppo=gname, n_citta=int(ng), quota_citta_pct=round(100 * share_city, 1),
                     top_per_LQ="; ".join(f"{names[i]} (LQ {r.lq:.1f}, {int(r['sum'])}/{int(r['size'])})" for i, r in top.iterrows()),
                     top_per_numero="; ".join(f"{names[i]} ({int(r['sum'])})" for i, r in topn.iterrows()),
                     quota_nei_5_NIL_piu_ricchi_pct=round(float(topn.quota_del_gruppo_in_NIL_pct.sum()), 1)))
cc = pd.DataFrame(conc)
cc.to_csv(os.path.join(OUT, "cucine_concentrazione.csv"), sep=";", index=False, encoding="utf-8-sig")
L["concentrazione_cucine"] = conc
# quota cucine "etniche" (non italiane, non pizza) per NIL
rfc["etnica"] = rfc[ETNICHE].any(axis=1)
e_nil = rfc.groupby("id_nil").etnica.agg(["sum", "size"])
e_nil = e_nil[e_nil["size"] >= 20]
e_nil["pct"] = (100 * e_nil["sum"] / e_nil["size"]).round(1)
L["etniche_quota_citta_pct"] = round(100 * rfc.etnica.mean(), 1)
L["NIL_piu_etnici_pct_(>=20_locali_con_cucina)"] = [dict(nil=names[i], n=int(r["size"]), etnici=int(r["sum"]), pct=r.pct) for i, r in e_nil.sort_values("pct", ascending=False).head(6).iterrows()]
L["NIL_meno_etnici_pct"] = [dict(nil=names[i], n=int(r["size"]), etnici=int(r["sum"]), pct=r.pct) for i, r in e_nil.sort_values("pct").head(6).iterrows()]

# ---------- 4. i piu' milanesi (tag/nome)
PAT = re.compile(r"lombard|milanes|risott|cotolett|ossobuc|cassoeula|casoeula|cazzoeula|mondeghil|busecca|trippa|panettone|ciumbia|osteria|trattoria|latteria|mondo|osso buco", re.I)
CUC = re.compile(r"lombard|milanes|risott|cotolett|ossobuc|cassoeula|casoeula|mondeghil|busecca", re.I)
oo_ = loc[loc.fonte == "osm"].copy()
oo_["tags_extra"] = oo_.id.map(dict(zip(osm.id, osm._tags)))
blob_c = oo_.cucina.fillna("")
blob_n = (oo_.nome.fillna("") + " " + oo_.tags_extra.fillna(""))
oo_["milanese_cucina"] = blob_c.str.contains(CUC)
oo_["milanese_nome_o_descr"] = blob_n.str.contains(re.compile(r"lombard|milanes|risott|cotolett|ossobuc|cassoeula|casoeula|mondeghil|busecca|ciumbia", re.I))
mil = oo_[oo_.milanese_cucina | oo_.milanese_nome_o_descr]
mil[["id", "nome", "tipo", "cucina", "nil", "ultima_modifica", "milanese_cucina", "milanese_nome_o_descr"]].to_csv(os.path.join(OUT, "locali_milanesi.csv"), sep=";", index=False, encoding="utf-8-sig")
L["milanesi"] = {"con_tag_cuisine_milanese_lombard_risotto_cotoletta": int(oo_.milanese_cucina.sum()), "con_parola_nel_nome_o_descrizione": int(oo_.milanese_nome_o_descr.sum()), "totale_unici": len(mil),
                 "per_NIL_top": mil.groupby("nil").size().sort_values(ascending=False).head(8).to_dict(), "cucina_values": oo_[oo_.milanese_cucina].cucina.value_counts().to_dict()}
reg_cuc = oo_[oo_.cucina.fillna("").str.contains("regional")]
L["cucina_regional_n"] = len(reg_cuc)
L["cucina_regional_per_NIL_top"] = reg_cuc.groupby("nil").size().sort_values(ascending=False).head(8).to_dict()
# Il tag 'regional' non dice quale regione: non e' 'milanese'.
nm = oo_[oo_.tipo.isin(["restaurant"]) & oo_.nome.fillna("").str.contains(r"^(trattoria|osteria)\b|\b(trattoria|osteria)\b", case=False, regex=True)]
L["ristoranti_OSM_con_Trattoria_o_Osteria_nel_nome"] = {"n": len(nm), "per_NIL_top": nm.groupby("nil").size().sort_values(ascending=False).head(6).to_dict()}

# ---------- 5. registro 2019 -> 2026 per NIL (aperture/chiusure approssimate dal codice del registro)
w = pd.read_csv(os.path.join(RAW, "wayback", "ds58_2019.csv"), sep=";", dtype=str)
w["lon"] = pd.to_numeric(w.LONG_WGS84, errors="coerce"); w["lat"] = pd.to_numeric(w.LAT_WGS84, errors="coerce")
w["id_nil_calc"] = assign_nil(w.lon.fillna(-999).values, w.lat.fillna(-999).values)
cur = r58.copy(); cur["lon"] = pd.to_numeric(cur.LONG_X_4326, errors="coerce"); cur["lat"] = pd.to_numeric(cur.LAT_Y_4326, errors="coerce"); cur["id_nil_calc"] = assign_nil(cur.lon.fillna(-999).values, cur.lat.fillna(-999).values)
sw, sc = set(w.Codice), set(cur.Codice)
w["ancora"] = w.Codice.isin(sc); cur["nuovo"] = ~cur.Codice.isin(sw)


def addr_key(u):
    m = re.match(r"^(.*?)\s+N\.\s*([0-9]+[A-Za-z]?)", str(u))
    return (re.sub(r"[^a-z0-9]", "", m.group(1).lower()), m.group(2).lower()) if m else None


w["addr"] = w.Ubicazione.map(addr_key); cur["addr"] = cur.Ubicazione.map(addr_key)
aw, ac = set(w.addr.dropna()), set(cur.addr.dropna())
# 'cessato' vero = indirizzo non piu' presente; 'nuovo' vero = indirizzo non presente nel 2019
w["indirizzo_scomparso"] = ~w.addr.isin(ac); cur["indirizzo_nuovo"] = ~cur.addr.isin(aw)
ch = pd.DataFrame({"nil": pd.Series(names)})
ch["registro_2019"] = w[w.id_nil_calc > 0].groupby("id_nil_calc").size()
ch["registro_2026"] = cur[cur.id_nil_calc > 0].groupby("id_nil_calc").size()
ch["codici_nuovi"] = cur[cur.nuovo & (cur.id_nil_calc > 0)].groupby("id_nil_calc").size()
ch["codici_scomparsi"] = w[~w.ancora & (w.id_nil_calc > 0)].groupby("id_nil_calc").size()
ch["indirizzi_nuovi"] = cur[cur.indirizzo_nuovo & (cur.id_nil_calc > 0)].groupby("id_nil_calc").size()
ch["indirizzi_scomparsi"] = w[w.indirizzo_scomparso & (w.id_nil_calc > 0)].groupby("id_nil_calc").size()
ch = ch.fillna(0)
ch["variazione_netta"] = ch.registro_2026 - ch.registro_2019
ch["variazione_pct"] = (100 * ch.variazione_netta / ch.registro_2019.replace(0, np.nan)).round(1)
ch.index.name = "id_nil"
ch.to_csv(os.path.join(OUT, "registro_2019_2026_nil.csv"), sep=";", encoding="utf-8-sig")
L["registro_2019_2026"] = {"2019_righe": len(w), "2026_righe": len(cur), "codici_in_comune": len(sw & sc), "codici_scomparsi": len(sw - sc), "codici_nuovi": len(sc - sw),
                           "codici_nuovi_con_indirizzo_gia_presente_2019_pct": round(100 * (~cur[cur.nuovo].indirizzo_nuovo).mean(), 1),
                           "codici_scomparsi_con_indirizzo_ancora_presente_pct": round(100 * (~w[~w.ancora].indirizzo_scomparso).mean(), 1),
                           "indirizzi_scomparsi": int(w.indirizzo_scomparso.sum()), "indirizzi_nuovi": int(cur.indirizzo_nuovo.sum())}
L["NIL_che_crescono_di_piu_pct_(>=40_nel_2019)"] = ch[ch.registro_2019 >= 40].sort_values("variazione_pct", ascending=False).head(6)[["nil", "registro_2019", "registro_2026", "variazione_pct"]].to_dict("records")
L["NIL_che_calano_di_piu_pct"] = ch[ch.registro_2019 >= 40].sort_values("variazione_pct").head(6)[["nil", "registro_2019", "registro_2026", "variazione_pct"]].to_dict("records")
# start_date OSM
sd = pd.to_datetime(osm.start_date.str[:4], errors="coerce", format="%Y")
L["osm_con_start_date"] = {"n": int(osm.start_date.notna().sum()), "per_anno_ultimi": {int(k): int(v) for k, v in sd.dt.year.value_counts().sort_index().tail(10).items()}}

json.dump(L, open(os.path.join(OUT, "build_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(L, ensure_ascii=False, indent=1, default=str))
