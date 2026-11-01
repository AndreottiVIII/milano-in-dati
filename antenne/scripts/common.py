"""Funzioni comuni (classificazione gestori, NIL). Importato dagli altri script (stessa cartella)."""
import re, json, os
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape
from shapely import STRtree

MOBILE = {"TIM": r"^TIM S\.p\.A", "Vodafone": r"^VODAFONE", "WindTre": r"^(Wind Tre|WIND TELECOMUNICAZIONI|H3G)", "Iliad": r"^ILIAD"}
INFRA = {"CommsCon": r"^CommsCon", "Cellnex": r"^Cellnex", "INWIT": r"^INWIT", "OpNet": r"^OpNet", "Hightel Towers": r"^HIGHTEL", "TowerCo": r"^TowerCo"}
RADIOTV = (r"(radio|\btv\b|televis|tele[a-z]|\brai\b|persidera|elemedia|r\.t\.i|publiaudio|mediapason|dab|sky italia|\bla ?[79]\b|canale|rete a|"
           r"multimedia san paolo|centro di produzione|emmeciuno|\bteva\b|tivu|ei towers|elettronica industriale|3lettronica|mediatech|videobyte|"
           r"europa way|elite|unitedcom|lattemiele|prima tv|europa tv|tecninvest|wavw|e-via|sediv|digital)")


def fix_moji(s):
    if isinstance(s, str) and "Ã" in s:
        try:
            return s.encode("latin-1").decode("utf-8")
        except Exception:
            return s
    return s


def classifica(gestore, tipo):
    """-> (gruppo_gestore, categoria)"""
    g = (gestore or "").strip()
    for k, p in MOBILE.items():
        if re.search(p, g, re.I):
            return k, "operatore mobile"
    for k, p in INFRA.items():
        if re.search(p, g, re.I):
            return k, "societa infrastrutture"
    if re.search(r"^(FASTWEB|SOLARIS|LINKEM|WORLDSPACE)", g, re.I):
        return g, "altro operatore TLC"
    if tipo in ("Radiofonia", "Televisione") or re.search(RADIOTV, g, re.I):
        return g, "radio e TV"
    return g, "altro (enti, ponti radio, reti di servizio)"


def load_nil(P):
    g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
    polys = [shape(f["geometry"]) for f in g["features"]]
    ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
    names = [f["properties"]["NIL"] for f in g["features"]]
    return polys, ids, names


def assegna_nil(lon, lat, polys, ids, names, tol_m=100):
    """punto in poligono; se fuori, NIL piu' vicino entro tol_m (UTM 32N). -> (id, nome, metodo, aree_km2 dei poligoni)"""
    from pyproj import Transformer
    str_ = STRtree(polys)
    pts = shapely.points(np.asarray(lon, float), np.asarray(lat, float))
    pi, gi = str_.query(pts, predicate="within")
    idx = np.full(len(pts), -1)
    for a, b in zip(pi, gi):
        idx[a] = b
    meto = np.where(idx >= 0, "poligono", "nessuno")
    tr = Transformer.from_crs(4326, 32632, always_xy=True)
    pol_utm = [shapely.transform(p, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for p in polys]
    st2 = STRtree(pol_utm)
    for i in np.where(idx < 0)[0]:
        x, y = tr.transform(float(lon[i]), float(lat[i]))
        pt = shapely.Point(x, y)
        j = st2.nearest(pt)
        if pt.distance(pol_utm[j]) <= tol_m:
            idx[i] = j
            meto[i] = f"vicino<={tol_m}m"
    nid = [ids[j] if j >= 0 else None for j in idx]
    nn = [names[j] if j >= 0 else None for j in idx]
    return nid, nn, list(meto), [p.area / 1e6 for p in pol_utm]
