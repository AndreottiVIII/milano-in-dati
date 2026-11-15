"""Calcola i numeri della pagina «La falda che risale».

Entrata: falda/dati_grezzi/ (linee isopiezometriche 2010 e 2022, soggiacenza 2022, punti di controllo del Comune)
         docs/negozi/data/nil.geojson (confini dei quartieri già usati dal sito)
         docs/metro/data/stazioni_metro.csv
Uscita:  docs/fogne/data/falda_*.json e falda_*.csv (capitolo «La falda sotto i piedi» della pagina Acqua e fogne);
         falda/dati_extra/ per i file non pubblicati (sezione nord-sud, punti di controllo, serie della città)
"""
import json, csv, math, pathlib, collections
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform as sh_transform
from shapely import prepared
from scipy.interpolate import LinearNDInterpolator

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "falda" / "dati_grezzi"
OUT = ROOT / "docs" / "fogne" / "data"
OUT.mkdir(parents=True, exist_ok=True)
EXTRA = ROOT / "falda" / "dati_extra"
EXTRA.mkdir(parents=True, exist_ok=True)
import shutil
shutil.copyfile(ROOT / "docs" / "negozi" / "data" / "nil.geojson", OUT / "falda_confini.geojson")
T = Transformer.from_crs(4326, 32632, always_xy=True)
proj = lambda g: sh_transform(T.transform, g)


def num(s):
    return float(str(s).replace(",", "."))


def carica_isolinee(nome, campo):
    d = json.load(open(RAW / nome, encoding="utf8"))
    out = []
    for f in d["features"]:
        v = f["properties"].get(campo)
        if v in (None, ""):
            continue
        pr = f["properties"]
        out.append((num(v), proj(shape(f["geometry"])), pr.get("tipo") or pr.get("piezom") or pr.get("stimata")))
    return out


def campiona(linee, passo=150):
    P, V = [], []
    for v, g, _ in linee:
        for ln in getattr(g, "geoms", [g]):
            n = max(2, int(ln.length // passo) + 1)
            for i in range(n + 1):
                p = ln.interpolate(i / n, normalized=True)
                P.append((p.x, p.y))
                V.append(v)
    return np.array(P), np.array(V)


def superficie(linee):
    P, V = campiona(linee)
    return LinearNDInterpolator(P, V)


# --- quartieri
nil = json.load(open(ROOT / "docs" / "negozi" / "data" / "nil.geojson", encoding="utf8"))
quartieri = []
for f in nil["features"]:
    g = proj(shape(f["geometry"]))
    quartieri.append((f["properties"]["i"], f["properties"]["n"], g, f["properties"].get("ab")))

# --- isopieze: tutte le carte disponibili (marzo e settembre)
CARTE = [("2007-03", "piezo_2007_03", "piezometri"), ("2007-09", "piezo_2007_09", "piezometri"),
         ("2009-03", "piezo_2009_03", "zlevel"), ("2009-09", "piezo_2009_09", "contour"),
         ("2010-03", "piezo_2010_03", "contour"), ("2010-09", "piezo_2010_09", "contour"),
         ("2011-03", "piezo_2011_03", "contour"), ("2011-09", "piezo_2011_09", "contour"),
         ("2012-03", "piezo_2012_03", "quota"), ("2012-09", "piezo_2012_09", "quota"),
         ("2013-09", "piezo_2013_09", "quota"),
         ("2022-03", "piezo_2022_03", "text"), ("2022-09", "piezo_2022_09", "text")]
LINEE = {k: carica_isolinee(f + ".geojson", c) for k, f, c in CARTE}
SUP = {k: superficie(l) for k, l in LINEE.items()}
s22, s10 = SUP["2022-03"], SUP["2010-03"]

from shapely.ops import unary_union
MILANO = unary_union([g for _, _, g, _ in quartieri]).buffer(3000)


def convalida(linee):
    """Tengo solo le linee ogni 5 metri (come le carte 2007-2013) e ricostruisco quelle intermedie ogni 2,5 m."""
    livelli = sorted({v for v, _, _ in linee})
    tolti = set(v for v in livelli if v % 5 != 0)
    f = superficie([l for l in linee if l[0] not in tolti])
    err = []
    for v, g, _ in linee:
        if v not in tolti:
            continue
        for ln in getattr(g, "geoms", [g]):
            for i in range(0, int(ln.length // 400) + 1):
                p = ln.interpolate(min(i * 400, ln.length))
                if not MILANO.contains(p):
                    continue
                r = f(p.x, p.y)
                if not np.isnan(r):
                    err.append(float(r) - v)
    err = np.array(err)
    return {"punti": int(len(err)), "errore_medio_assoluto_m": round(float(np.abs(err).mean()), 2),
            "errore_massimo_m": round(float(np.abs(err).max()), 2), "livelli_ricostruiti": len(tolti),
            "errore_medio_con_segno_m": round(float(err.mean()), 2)}


conv = {"2022_03_solo_linee_ogni_5_m": convalida(LINEE["2022-03"]), "2022_09_solo_linee_ogni_5_m": convalida(LINEE["2022-09"])}
conv["linee_stimate_su_totale"] = {k: [sum(1 for _, _, t in l if t in ("stimata", "si")), len(l)] for k, l in LINEE.items() if any(t for _, _, t in l)}
print("convalida", conv)

# --- celle da 100 m dentro ogni quartiere
righe, tutti = [], []
for i, n, g, ab in quartieri:
    pg = prepared.prep(g)
    minx, miny, maxx, maxy = g.bounds
    xs = np.arange(math.floor(minx / 100) * 100 + 50, maxx, 100)
    ys = np.arange(math.floor(miny / 100) * 100 + 50, maxy, 100)
    pts = [(x, y) for x in xs for y in ys if pg.contains(Point(x, y))]
    if not pts:
        c = g.representative_point()
        pts = [(c.x, c.y)]
    pts = np.array(pts)
    val = {k: f(pts[:, 0], pts[:, 1]) for k, f in SUP.items()}
    a22, a10 = val["2022-03"], val["2010-03"]
    ok = ~np.isnan(a22) & ~np.isnan(a10)
    ok9 = ~np.isnan(val["2022-09"]) & ~np.isnan(val["2010-09"])
    righe.append({"i": i, "n": n, "ab": ab, "celle": int(len(pts)), "celle_ok": int(ok.sum()),
                  "q22": float(np.mean(a22[ok])) if ok.any() else None,
                  "q10": float(np.mean(a10[ok])) if ok.any() else None,
                  "q22s": float(np.mean(val["2022-09"][ok9])) if ok9.any() else None,
                  "q10s": float(np.mean(val["2010-09"][ok9])) if ok9.any() else None})
    tutti.append((pts, a22, a10, val))

# serie: media sulle celle dove tutte le carte hanno il valore
okall = np.concatenate([np.all([~np.isnan(v[k]) for k in SUP], axis=0) for _, _, _, v in tutti])
serie = {}
for k in SUP:
    serie[k] = round(float(np.concatenate([v[k] for _, _, _, v in tutti])[okall].mean()), 2)
print("celle comuni a tutte le carte:", int(okall.sum()), "su", len(okall), serie)
copertura = {k: round(float(np.mean(~np.isnan(np.concatenate([v[k] for _, _, _, v in tutti])))), 3) for k in SUP}
print("copertura", copertura)

# --- soggiacenza (marzo 2022) a classi
sog = json.load(open(RAW / "soggiacenza_2022_03.geojson", encoding="utf8"))
CENTRI = {"< 2,5": 1.25, "2,5 - 5": 3.75, "5 - 7,5": 6.25, "7,5 - 10": 8.75, "10 - 15": 12.5, "15 - 20": 17.5,
          "20 - 25": 22.5, "25 - 35": 30.0, "> 35": 40.0, "> 5": None}
poli = []
etic = collections.Counter()
for f in sog["features"]:
    c = f["properties"]["classe"]
    etic[c] += 1
    poli.append((c, proj(shape(f["geometry"]))))
print("classi presenti", dict(etic))


def classe_in(x, y):
    p = Point(x, y)
    for c, g in poli:
        if g.contains(p):
            return c
    return None


for r, (pts, a22, a10, _v) in zip(righe, tutti):
    cnt = collections.Counter(classe_in(x, y) for x, y in pts)
    tot = sum(v for k, v in cnt.items() if k)
    r["quote_classi"] = {k: round(v / tot, 4) for k, v in cnt.items() if k} if tot else {}
    val = [(CENTRI[k], v) for k, v in cnt.items() if k and CENTRI.get(k) is not None]
    t2 = sum(v for _, v in val)
    r["soggiacenza_media"] = round(sum(a * v for a, v in val) / t2, 2) if t2 else None
    r["classe_prevalente"] = max((k for k in cnt if k), key=lambda k: cnt[k], default=None)
    r["sotto_5m"] = round(sum(v for k, v in cnt.items() if k in ("< 2,5", "2,5 - 5")) / tot, 4) if tot else None

# --- stazioni del metrò
staz = []
for s in csv.DictReader(open(ROOT / "docs" / "metro" / "data" / "stazioni_metro.csv", encoding="utf8")):
    x, y = T.transform(float(s["lon"]), float(s["lat"]))
    c = classe_in(x, y)
    q22, q10 = s22(x, y), s10(x, y)
    staz.append({"stazione": s["stazione"], "linee": s["linee"], "lat": float(s["lat"]), "lon": float(s["lon"]),
                 "classe": c, "sog": CENTRI.get(c),
                 "q22": None if np.isnan(q22) else round(float(q22), 1), "q10": None if np.isnan(q10) else round(float(q10), 1)})

# --- punti di controllo del Comune
punti = {}
for r in csv.DictReader(open(RAW / "ds587.csv", encoding="utf-8-sig"), delimiter=";"):
    k = r["CODICE_PP"]
    p = punti.setdefault(k, {"nome": r["DESC_PUNTO_PRELIEVO"].strip(), "lat": r["GEO_Y"], "lon": r["GEO_X"],
                             "nil": r["NIL"], "misure": 0, "campioni": set(), "anno": r["ANNO"]})
    p["misure"] += 1
    p["campioni"].add(r["DATACAMPIONAMENTO"])
pc = []
for k, p in punti.items():
    if not p["lat"]:
        continue
    x, y = T.transform(float(p["lon"]), float(p["lat"]))
    pc.append({"codice": k, "nome": p["nome"], "lat": round(float(p["lat"]), 5), "lon": round(float(p["lon"]), 5),
               "nil": p["nil"], "misure": p["misure"], "campioni": len(p["campioni"]), "anno": p["anno"],
               "classe": classe_in(x, y)})
n_senza_coord = sum(1 for p in punti.values() if not p["lat"])

# --- quanto "balla" un quartiere da una carta alla successiva rispetto alla media di Milano
_A = np.array([[np.nanmean(v[k]) for k in SUP] for (_, _, _, v) in tutti])
_ks = list(SUP.keys())
_scarti = []
for j in range(1, 10):   # coppie consecutive fra 2007 e 2012 (nessun salto di anni)
    dd = _A[:, j] - _A[:, j - 1]
    _scarti.append(np.abs(dd - dd.mean()))
RUMORE = {"mediana_m": round(float(np.median(np.concatenate(_scarti))), 2), "percentile90_m": round(float(np.percentile(np.concatenate(_scarti), 90)), 2)}
print("rumore quartieri", RUMORE)

# --- uscite
with open(OUT / "falda_quartieri.csv", "w", encoding="utf8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "quartiere", "abitanti", "quota_2010_m", "quota_2022_m", "variazione_m", "soggiacenza_2022_m",
                "classe_prevalente", "quota_area_sotto_5m", "celle"])
    for r in righe:
        d = None if r["q10"] is None else round(r["q22"] - r["q10"], 2)
        w.writerow([r["i"], r["n"], r["ab"], "" if r["q10"] is None else round(r["q10"], 2),
                    "" if r["q22"] is None else round(r["q22"], 2), "" if d is None else d,
                    r["soggiacenza_media"], r["classe_prevalente"], r["sotto_5m"], r["celle_ok"]])
json.dump([{"i": r["i"], "n": r["n"], "ab": r["ab"], "q10": None if r["q10"] is None else round(r["q10"], 2),
            "q22": None if r["q22"] is None else round(r["q22"], 2),
            "d": None if r["q10"] is None else round(r["q22"] - r["q10"], 2), "sog": r["soggiacenza_media"],
            "cl": r["classe_prevalente"], "s5": r["sotto_5m"], "quote": r["quote_classi"]} for r in righe],
          open(OUT / "falda_quartieri.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(staz, open(OUT / "falda_stazioni.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(pc, open(EXTRA / "punti_controllo.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)

# sezione nord-sud lungo un meridiano che passa vicino al Duomo
lon0 = 9.1900
sez = []
for lat in np.arange(45.58, 45.37, -0.0025):
    x, y = T.transform(lon0, lat)
    riga = {"lat": round(float(lat), 4), "classe": classe_in(x, y)}
    for k in ("2007-03", "2010-03", "2022-03"):
        q = SUP[k](x, y)
        riga["q" + k[:4]] = None if np.isnan(q) else round(float(q), 2)
    sez.append(riga)
json.dump(sez, open(EXTRA / "sezione_nord_sud.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# valori di ogni quartiere in ogni carta (per il grafico nel tempo)
nil_serie = {"carte": list(SUP.keys()), "quartieri": {}}
for r, (pts, a22, a10, val) in zip(righe, tutti):
    nil_serie["quartieri"][str(r["i"])] = [round(float(np.nanmean(val[k])), 2) for k in SUP]
json.dump(nil_serie, open(OUT / "falda_serie_quartieri.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump({"carte": serie}, open(EXTRA / "serie_citta.json", "w", encoding="utf8"), ensure_ascii=False)

# --- riepilogo (ogni cella da 100 m pesa uguale = peso per superficie)
a22 = np.concatenate([a[~np.isnan(a) & ~np.isnan(b)] for _, a, b, _v in tutti])
a10 = np.concatenate([b[~np.isnan(a) & ~np.isnan(b)] for _, a, b, _v in tutti])
diff = a22 - a10
ok = [r for r in righe if r["q10"] is not None]
dq = np.array([r["q22"] - r["q10"] for r in ok])
riep = {
    "celle_milano": int(len(a22)),
    "quota_media_2010": round(float(a10.mean()), 2), "quota_media_2022": round(float(a22.mean()), 2),
    "variazione_media_m": round(float(diff.mean()), 2), "variazione_mediana_m": round(float(np.median(diff)), 2),
    "quota_celle_in_salita": round(float((diff > 0).mean()), 4),
    "quota_celle_salita_oltre_2m": round(float((diff > 2).mean()), 4),
    "salita_2007_2013_settembre_m": round(serie["2013-09"] - serie["2007-09"], 2),
    "salita_2007_2022_marzo_m": round(serie["2022-03"] - serie["2007-03"], 2),
    "nil_sopra_2007_nel_2022_marzo": int(sum(1 for r in righe if nil_serie["quartieri"][str(r["i"])][11] > nil_serie["quartieri"][str(r["i"])][0])),
    "nil_totali": len(righe), "nil_con_dato_2010_2022": len(ok),
    "nil_in_salita": int((dq > 0).sum()), "nil_in_discesa": int((dq < 0).sum()),
    "nil_scesi_oltre_1_5m": int((dq < -1.5).sum()), "nil_saliti_oltre_1_5m": int((dq > 1.5).sum()),
    "nil_scesi_oltre_50cm": int((dq < -0.5).sum()), "nil_saliti_oltre_50cm": int((dq > 0.5).sum()),
    "nil_salita_massima": max(((round(r["q22"] - r["q10"], 2), r["n"]) for r in ok)),
    "nil_discesa_massima": min(((round(r["q22"] - r["q10"], 2), r["n"]) for r in ok)),
    "convalida": conv, "rumore_quartieri_tra_carte_consecutive": RUMORE, "serie_quota_media": serie, "celle_comuni_serie": int(okall.sum()), "copertura_carte": copertura,
    "variazione_media_settembre_m": round(float(np.mean([r["q22s"] - r["q10s"] for r in righe if r["q10s"] is not None])), 2),
    "nil_in_discesa_settembre": int(sum(1 for r in righe if r["q10s"] is not None and r["q22s"] < r["q10s"])),
    "punti_controllo_con_coordinate": len(pc), "punti_controllo_senza_coordinate": n_senza_coord,
}
sg = [r for r in righe if r["sotto_5m"] is not None]
ab_tot = sum(r["ab"] for r in sg if r["ab"])
ab_5 = sum(r["ab"] * r["sotto_5m"] for r in sg if r["ab"])
riep["abitanti_con_falda_sotto_5m_stima"] = int(round(ab_5, -2))
riep["quota_abitanti_falda_sotto_5m"] = round(ab_5 / ab_tot, 4)
riep["nil_prevalenza_sotto_5m"] = sum(1 for r in sg if r["sotto_5m"] >= 0.5)
riep["nil_senza_dato_soggiacenza"] = len(righe) - len(sg)
riep["nil_soggiacenza_minima"] = min((r["soggiacenza_media"], r["n"]) for r in sg if r["soggiacenza_media"])
riep["nil_soggiacenza_massima"] = max((r["soggiacenza_media"], r["n"]) for r in sg if r["soggiacenza_media"])
riep["stazioni_totali"] = len(staz)
riep["stazioni_con_classe"] = len([s for s in staz if s["classe"]])
riep["stazioni_falda_sotto_5m"] = len([s for s in staz if s["classe"] in ("< 2,5", "2,5 - 5")])
riep["stazioni_falda_sotto_10m"] = len([s for s in staz if s["classe"] in ("< 2,5", "2,5 - 5", "5 - 7,5", "7,5 - 10")])
json.dump(riep, open(OUT / "falda_riepilogo.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(riep, ensure_ascii=False, indent=1))
