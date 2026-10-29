"""Fase 3: strumenti per la taratura sui 20 tragitti (valori Google solo per la taratura, non si pubblicano)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from f2_motore import Motore, xy_of
import f2_parametri as P

FILES = ['tragitti_prova.csv', 'tragitti_prova_2.csv']   # il secondo si legge solo se esiste (altro agente)

def carica(S):
    """Legge tutti i tragitti con almeno un valore Google. Divisione 70/30 per fascia oraria e distanza:
    dentro ogni ora (08, 12, 21) i tragitti in ordine di distanza in linea retta; in 'controllo' le posizioni 2, 5, 8 ogni 10."""
    parts = []
    for f in FILES:
        if not os.path.exists(S + '/' + f): continue
        x = pd.read_csv(S + '/' + f, sep=';', decimal=',', encoding='utf-8-sig')
        x['file'] = f; x['id'] = [f.replace('tragitti_prova', 'A').replace('.csv', '').replace('_', '') + '-' + str(n) for n in x.n]
        parts.append(x)
    d = pd.concat(parts, ignore_index=True)
    for c in ('google_bici_min', 'google_auto_min', 'google_mezzi_min', 'km_in_linea_retta'):
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d = d[d[['google_bici_min', 'google_auto_min', 'google_mezzi_min']].notna().any(axis=1)].reset_index(drop=True)
    d['band'] = d.ora_partenza.str[:2]
    d['gruppo'] = 'taratura'
    for b, x in d.groupby('band'):
        o = x.sort_values(['km_in_linea_retta', 'id']).index.tolist()
        for pos, i in enumerate(o):
            if pos % 10 in (2, 5, 8): d.loc[i, 'gruppo'] = 'controllo'
    return d

class Banco:
    def __init__(self, S):
        self.S = S; self.d = carica(S); self.m = Motore(S, verbose=False)
        self.o = [self.m_xy(r.lon_partenza, r.lat_partenza) for r in self.d.itertuples()]
        self.D = [self.m.dest([r.lon_arrivo], [r.lat_arrivo]) for r in self.d.itertuples()]
    def m_xy(self, lon, lat):
        x, y = xy_of(lon, lat); return (float(x[0]), float(y[0]))
    def bici(self):            # minuti di pedalata (senza il lucchetto)
        return np.array([self.m.bici(o, D)[0] / 60 for o, D in zip(self.o, self.D)])
    def auto(self):            # minuti di sola guida
        return np.array([self.m.auto(o, D, b)[0][0] / 60 for o, D, b in zip(self.o, self.D, self.d.band)])
    def mezzi(self):
        return np.array([self.m.mezzi(o, D, P.DEPARTURES[b])[0] / 60 for o, D, b in zip(self.o, self.D, self.d.band)])

def errori(stima, google, mask=None):
    """-> (rapporto mediano, errore mediano in %, errore medio assoluto in %, n)"""
    st = np.asarray(stima, float); g = np.asarray(google, float)
    if mask is not None: st = st[mask]; g = g[mask]
    ok = np.isfinite(st) & np.isfinite(g)
    r = st[ok] / g[ok]
    return float(np.median(r)), float(np.median(np.abs(r - 1)) * 100), float(np.mean(np.abs(r - 1)) * 100), int(ok.sum())
