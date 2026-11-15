# -*- coding: utf-8 -*-
"""Passo 1: dal GTFS del Comune di Milano (ds929) a una tabella con una riga per corsa del giorno feriale tipo.
Per ogni corsa: linea, tipo, ora di partenza, durata capolinea-capolinea, lunghezza del percorso, fermate.
Scrive velocita/lavoro/corse.csv (non pubblicato) e velocita/lavoro/shapes_usate.json.
Uso: python -I -X utf8 velocita/scripts/prepara.py
"""
import os, sys, json, datetime, collections
import numpy as np
import pandas as pd

QUI = os.path.dirname(os.path.abspath(__file__))
RAD = os.path.dirname(os.path.dirname(QUI))
GTFS = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new")
LAV = os.path.join(RAD, "velocita", "lavoro")
os.makedirs(LAV, exist_ok=True)
GIORNO = "20261124"   # martedi 24 novembre 2026, lo stesso giorno di "Quanto aspetti alla fermata"
R = 6371008.8
K = np.cos(np.radians(45.46))

def dist_m(lat1, lon1, lat2, lon2):
    dy = np.radians(np.asarray(lat2) - np.asarray(lat1)) * R
    dx = np.radians(np.asarray(lon2) - np.asarray(lon1)) * R * K
    return np.hypot(dx, dy)

def secondi(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)

cal = pd.read_csv(os.path.join(GTFS, "calendar_dates.txt"), dtype=str)
cal = cal[cal.exception_type == "1"]
per_data = cal.groupby("date").service_id.nunique()
cand = []
for d, n in per_data.items():
    wd = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday()
    if wd in (1, 2, 3):
        cand.append((n, d))
cand.sort(reverse=True)
print("giorno con piu' servizi (mar-gio):", cand[:3])
assert cand[0][1] == GIORNO
servizi = set(cal[cal.date == GIORNO].service_id)

trips = pd.read_csv(os.path.join(GTFS, "trips.txt"), dtype=str, usecols=["route_id", "service_id", "trip_id", "shape_id", "direction_id"])
trips = trips[trips.service_id.isin(servizi)].copy()
print("corse del giorno", len(trips))
attive = set(trips.trip_id)

# fermate
st = pd.read_csv(os.path.join(GTFS, "stops.txt"), dtype=str, usecols=["stop_id", "stop_lat", "stop_lon"])
st["lat"] = st.stop_lat.astype(float); st["lon"] = st.stop_lon.astype(float)
stop_xy = st.set_index("stop_id")[["lat", "lon"]]

# stop_times a pezzi, solo le corse del giorno
pezzi = []
for ch in pd.read_csv(os.path.join(GTFS, "stop_times.txt"), dtype=str, chunksize=2_000_000,
                      usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]):
    ch = ch[ch.trip_id.isin(attive)]
    pezzi.append(ch)
stt = pd.concat(pezzi, ignore_index=True)
stt["seq"] = stt.stop_sequence.astype(int)
stt = stt.sort_values(["trip_id", "seq"])
print("righe stop_times del giorno", len(stt))
stt = stt.join(stop_xy, on="stop_id")
stt["dep"] = stt.departure_time.map(secondi)
stt["arr"] = stt.arrival_time.map(secondi)

# shapes
sh = pd.read_csv(os.path.join(GTFS, "shapes.txt"), dtype=str, usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"])
sh["lat"] = sh.shape_pt_lat.astype(float); sh["lon"] = sh.shape_pt_lon.astype(float); sh["q"] = sh.shape_pt_sequence.astype(int)
sh = sh.sort_values(["shape_id", "q"])
shapes = {}
for sid, g in sh.groupby("shape_id", sort=False):
    lat = g.lat.values; lon = g.lon.values
    seg = dist_m(lat[:-1], lon[:-1], lat[1:], lon[1:])
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    shapes[sid] = (lat, lon, cum)
print("shapes", len(shapes))

def pos_su_shape(lat, lon, cum, la, lo, lo_idx=0):
    d = dist_m(lat[lo_idx:], lon[lo_idx:], la, lo)
    i = int(np.argmin(d))
    return lo_idx + i, float(d[i])

righe = []
g = stt.groupby("trip_id", sort=False)
tinfo = trips.set_index("trip_id")
mancanti = 0
for tid, t in g:
    if tid not in tinfo.index:
        continue
    info = tinfo.loc[tid]
    if t.lat.isna().any() or len(t) < 2:
        continue
    la = t.lat.values; lo = t.lon.values
    cat = float(dist_m(la[:-1], lo[:-1], la[1:], lo[1:]).sum())   # catena di fermate in linea d'aria
    dur = int(t.arr.values[-1] - t.dep.values[0])
    sid = info.shape_id
    lung = None; metodo = ""
    if sid in shapes:
        slat, slon, cum = shapes[sid]
        i0, d0 = pos_su_shape(slat, slon, cum, la[0], lo[0])
        # ultima fermata: cercata dopo la prima (percorsi circolari)
        i1, d1 = pos_su_shape(slat, slon, cum, la[-1], lo[-1], min(i0 + 1, len(slat) - 1))
        if i1 > i0 and max(d0, d1) <= 300:
            lung = float(cum[i1] - cum[i0]); metodo = "percorso"
    if lung is None:
        mancanti += 1
        lung = cat * 1.25; metodo = "stima"
    righe.append((tid, info.route_id, sid, info.direction_id, int(t.dep.values[0]), dur, lung, cat, len(t), metodo))
print("corse senza percorso utilizzabile (stima)", mancanti)
df = pd.DataFrame(righe, columns=["trip_id", "route_id", "shape_id", "direzione", "partenza_s", "durata_s", "lung_m", "catena_m", "fermate", "metodo"])
df.to_csv(os.path.join(LAV, "corse.csv"), index=False)
print(df.metodo.value_counts())
print(df.describe())
