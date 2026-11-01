"""Funzioni comuni: caricamento dati e modello di proiezione "per coorti".

Idea (semplice e dichiarata):
  alunni(scuola, anno N) = alunni(scuola, ultimo anno osservato T0) x
                           (bambini dell'area nella fascia d'eta' dell'ordine, anno N)
                           / (bambini dell'area nella stessa fascia, anno T0)
dove i bambini dell'area per gli anni futuri si ottengono facendo "invecchiare" i residenti
per eta' singola (metodo delle coorti), con il passaggio osservato da un'eta' alla successiva
(che include immigrazione ed emigrazione) e con i nati dei prossimi anni fissati da uno scenario.

Fascia d'eta' per ordine (eta' compiuta al 31/12 dell'anno N = anno d'inizio dell'a.s. N/N+1):
  infanzia 3-5, primaria 6-10, secondaria di I grado 11-13  (stessa definizione di scuole/NOTE.md).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BANDE = {"infanzia": (3, 5), "primaria": (6, 10), "sec1": (11, 13)}
ORDINI = list(BANDE)
ANNI_RES = np.arange(1999, 2026)   # residenti per eta' singola: 1999-2025 (ds27)
ETA_MAX = 100


def percorsi(base):
    b = Path(base)
    return {
        "res": b / "popolazione" / "pulito" / "residenti_nil_anno_eta_genere.csv",
        "scuole": b / "scuole" / "pulito" / "scuole_anno_tidy.csv",
        "geo": b / "citta-15-minuti" / "raw" / "comune_milano" / "nil_vigenti" / "ds964_nil_wm.geojson",
        "nil": b / "popolazione" / "pulito" / "nil_anagrafica.csv",
        "nati1945": b / "nomi-bambini" / "raw" / "milano_nascite" / "ds1945_nascite_milano_2021_2024.csv",
        "nati289": b / "nomi-bambini" / "pulito" / "nascite_milano_ds289.csv",
    }


def carica_residenti(base):
    """Array R[nil_idx, anno_idx, eta] e lista id_nil (ds27, popolazione/pulito)."""
    p = percorsi(base)
    r = pd.read_csv(p["res"])
    ids = sorted(r.id_nil.unique())
    R = np.zeros((len(ids), len(ANNI_RES), ETA_MAX + 1))
    idx = {i: k for k, i in enumerate(ids)}
    g = r.groupby(["id_nil", "anno", "eta"]).residenti.sum().reset_index()
    R[g.id_nil.map(idx).values, (g.anno - ANNI_RES[0]).values, g.eta.values] = g.residenti.values
    return R, ids


def carica_scuole(base):
    s = pd.read_csv(percorsi(base)["scuole"], sep=";")
    s = s[s.ordine.isin(ORDINI)].copy()
    s["id_nil"] = s["id_nil"].astype(int)
    return s


def adiacenze(base, ids):
    """Matrici 0/1 [n,n]: anello 0 (solo il NIL), anello 1 (NIL + confinanti), anello 2 (+ confinanti dei confinanti)."""
    from shapely.geometry import shape
    g = json.load(open(percorsi(base)["geo"], encoding="utf-8"))
    geo = {f["properties"]["ID_NIL"]: shape(f["geometry"]).buffer(2e-5) for f in g["features"]}
    n = len(ids)
    A1 = np.eye(n)
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            if i != j and geo[a].intersects(geo[b]):
                A1[i, j] = 1
    A2 = ((A1 @ A1) > 0).astype(float)
    return {"nil": np.eye(n), "anello1": A1, "anello2": A2, "citta": np.ones((n, n))}


def passaggi_coorte(Ra, lres, K, eta_max=13):
    """Rapporto osservato R[t+1, a+1] / R[t, a], sommato sugli ultimi K passaggi che finiscono in lres.
    Ra: [n, anni, eta]. Restituisce g[n, a] per a = 0..eta_max-1."""
    t0 = lres - K - ANNI_RES[0]
    t1 = lres - ANNI_RES[0]
    num = Ra[:, t0 + 1:t1 + 1, 1:eta_max + 1].sum(axis=1)
    den = Ra[:, t0:t1, 0:eta_max].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.where(den > 0, num / den, 1.0)
    return g


def nascite_base(Ra, lres, ultimi=3):
    t1 = lres - ANNI_RES[0]
    return Ra[:, t1 - ultimi + 1:t1 + 1, 0].mean(axis=1)


def tasso_nascite_citta(R, lres, anni=5):
    """Variazione media annua dei residenti di eta' 0 (tutta la citta'), ultimi `anni` anni (CAGR)."""
    c = R[:, :, 0].sum(axis=0)
    t1 = lres - ANNI_RES[0]
    return (c[t1] / c[t1 - anni]) ** (1.0 / anni) - 1.0


def proietta_bande(Ra, lres, anni_target, g, B_future, eta_max=13):
    """Proietta i residenti per eta' (0..eta_max) dell'area per ciascun anno in anni_target (> lres, oppure <= lres: osservati).
    Ra: [n, anni, eta]; g: [n, eta_max]; B_future: dict anno_nascita -> array[n] (bambini di eta' 0 a fine anno).
    Restituisce P[n, len(anni_target), eta_max+1]."""
    n = Ra.shape[0]
    out = np.zeros((n, len(anni_target), eta_max + 1))
    cum = np.ones((n, eta_max + 1))          # prodotto dei g da eta' 0 a eta' a
    for a in range(1, eta_max + 1):
        cum[:, a] = cum[:, a - 1] * g[:, a - 1]
    for k, N in enumerate(anni_target):
        if N <= lres:
            out[:, k, :] = Ra[:, N - ANNI_RES[0], :eta_max + 1]
            continue
        d = N - lres
        for a in range(0, eta_max + 1):
            if a >= d:
                a0 = a - d
                prod = cum[:, a] / np.where(cum[:, a0] > 0, cum[:, a0], 1)
                out[:, k, a] = Ra[:, lres - ANNI_RES[0], a0] * prod
            else:
                y = N - a   # anno di nascita: nato dopo lres
                out[:, k, a] = B_future[y] * cum[:, a]
    return out


def scenario_nascite(R, Ra, lres, anni_target, scenario, ultimi=3, finestra_tasso=5, oracolo=None):
    """B_future[y] per y in lres+1..max(anni_target): bambini di eta' 0 a fine anno y, per area.
    scenario: 'stabili' (livello medio degli ultimi 3 anni, costante), 'calo' (continua il tasso medio annuo
    degli ultimi 5 anni della citta'), 'risalita' (stesso tasso con segno opposto), 'oracolo' (valori veri, solo per i test)."""
    base = nascite_base(Ra, lres, ultimi)
    r = tasso_nascite_citta(R, lres, finestra_tasso)
    B = {}
    for y in range(lres + 1, max(anni_target) + 1):
        h = y - lres
        if scenario == "stabili":
            f = 1.0
        elif scenario == "calo":
            f = (1 + r) ** h
        elif scenario == "risalita":
            f = (1 - r) ** h
        elif scenario == "oracolo":
            B[y] = oracolo[:, y - ANNI_RES[0]]
            continue
        else:
            raise ValueError(scenario)
        B[y] = base * f
    return B


def fattori_area(R, A, t0, anni_target, K, scenario, mig="coorte", oracolo=False, ultimi=3):
    """Fattore di variazione per area e ordine: F[ordine] = array[n, len(anni_target)]
    = bambini dell'area nella fascia (anno N) / bambini dell'area nella fascia (anno t0).
    t0 = ultimo anno scolastico osservato (inizio a.s.); i residenti noti arrivano a lres = t0 + 1.
    mig: 'coorte' (passaggi osservati ultimi K anni) | 'nessuna' (g = 1)."""
    lres = t0 + 1
    Ra = np.einsum("ij,jta->ita", A, R)
    if mig == "coorte":
        g = passaggi_coorte(Ra, lres, K)
    else:
        g = np.ones((Ra.shape[0], 13))
    B = scenario_nascite(R, Ra, lres, anni_target, "oracolo" if oracolo else scenario, ultimi=ultimi,
                         oracolo=np.einsum("ij,jt->it", A, R[:, :, 0]) if oracolo else None)
    P = proietta_bande(Ra, lres, anni_target, g, B)
    F = {}
    for o, (lo, hi) in BANDE.items():
        tot = P[:, :, lo:hi + 1].sum(axis=2)
        base = Ra[:, t0 - ANNI_RES[0], lo:hi + 1].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            F[o] = np.where(base[:, None] > 0, tot / base[:, None], np.nan)
    return F, P


# --- Metodo centrale e varianti -------------------------------------------------------------
# nome -> (area, peso dell'area locale w, migrazione, K)
#   fattore finale = F_citta^(1-w) * F_area^w   (media geometrica)
VARIANTI = {
    "centrale": ("anello1", 0.5, "nessuna", 5),       # meta' tendenza della citta', meta' del NIL e dei NIL confinanti
    "solo_citta": ("citta", 0.0, "nessuna", 5),
    "solo_nil": ("nil", 1.0, "nessuna", 5),           # solo i bambini residenti nel NIL della scuola
    "con_migrazione": ("anello1", 0.5, "coorte", 5),  # come centrale ma con i passaggi di eta' osservati (include arrivi e partenze)
}


def fattori_variante(R, ADJ, t0, anni_target, variante, scenario="stabili", oracolo=False):
    area, w, mig, K = VARIANTI[variante] if isinstance(variante, str) else variante
    Fc, Pc = fattori_area(R, ADJ["citta"], t0, anni_target, K, scenario, mig=mig, oracolo=oracolo)
    if w == 0:
        return Fc, Pc
    Fa, Pa = fattori_area(R, ADJ[area], t0, anni_target, K, scenario, mig=mig, oracolo=oracolo)
    F = {}
    for o in ORDINI:
        fa = np.clip(Fa[o], 0.4, 2.5)
        fa = np.where(np.isnan(fa), Fc[o], fa)
        F[o] = np.exp((1 - w) * np.log(Fc[o]) + w * np.log(fa))
    return F, Pa


def log(msg, path=None):
    print(msg, flush=True)
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
