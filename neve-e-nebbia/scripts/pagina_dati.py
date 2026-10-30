"""Fase 2: dalle tabelle pulite (pulito/) ai file JSON della pagina docs/neve-e-nebbia/.
Si pubblicano SOLO conteggi derivati (giorni per inverno/anno, medie per decennio, elenchi di date con una bandiera):
mai osservazioni grezze (dati non USA = Risoluzione 40 WMO).
Uso: python -I pagina_dati.py [<cartella_strand> [<cartella_uscita>]]
Si puo rifare quante volte si vuole: riscrive tutto da zero."""
import sys, os, json, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
OUT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(BASE), "docs", "neve-e-nebbia", "data")
os.makedirs(OUT, exist_ok=True)
P = lambda *a: os.path.join(BASE, "pulito", *a)

STAZ = ["LINATE", "MALPENSA"]
MIN_PCT = 90          # un inverno/anno e completo se almeno il 90% dei giorni ha 4 ore o piu di osservazioni
DA = 1950             # le tabelle della pagina partono dal 1950 (prima: 1931-38 con 1-2 osservazioni al giorno)


def clean(v):
    if v is None:
        return None
    if isinstance(v, (float, np.floating)):
        return None if (math.isnan(v) or math.isinf(v)) else (int(v) if float(v).is_integer() else round(float(v), 3))
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def dump(name, obj):
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [walk(v) for v in o]
        return clean(o)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(walk(obj), f, ensure_ascii=False, separators=(",", ":"))
    print("scritto", name, os.path.getsize(os.path.join(OUT, name)), "byte")


inv = pd.read_csv(P("inverni_neve_nebbia.csv"))
ann = pd.read_csv(P("totali_annuali.csv"))
comp = pd.read_csv(P("completezza_per_anno.csv"))
day = pd.read_csv(P("giorni_neve_nebbia.csv"), usecols=[
    "date", "station", "isd_n_hours", "snow_obs_strict", "snow_heavy_obs", "fog_synoptic_code_vis_lt1km"])

# ---- anno: completezza e nebbia sinottica con visibilita < 1 km (dal file giornaliero)
day["year"] = day["date"].str[:4].astype(int)
fs = day.groupby(["station", "year"])["fog_synoptic_code_vis_lt1km"].sum().rename("fog_days_synoptic_vis_lt1km").reset_index()
ann = ann.merge(comp[["station", "year", "days_in_year", "mean_hours_per_day"]], on=["station", "year"], how="left").merge(fs, on=["station", "year"], how="left")
ann["pct"] = 100.0 * ann["days_isd_ge4h"] / ann["days_in_year"]
ann["complete"] = ann["pct"] >= MIN_PCT
inv["complete"] = inv["winter_complete_isd"].eq("si")
assert (inv.loc[inv.complete, "pct_days_ge4h"] >= MIN_PCT).all() and (inv.loc[~inv.complete, "pct_days_ge4h"] < MIN_PCT).all()
assert (inv["snow_days_heavy"] <= inv["snow_days_strict"]).all()

# ---- inverni.json
INV, ANN = {}, {}
for s in STAZ:
    x = inv[(inv.station == s) & (inv.winter >= DA)].sort_values("winter")
    INV[s] = [dict(w=int(r.winter), n=r.snow_days_strict, h=r.snow_days_heavy, wide=r.snow_days_wide, syn=r.snow_days_synoptic,
                   gs=r.snow_days_gsod_flag, pct=round(r.pct_days_ge4h), c=int(r.complete), t=r.brera_tmean_nov_mar)
              for r in x.itertuples()]
    y = ann[(ann.station == s) & (ann.year >= DA)].sort_values("year")
    ANN[s] = [dict(y=int(r.year), v=r.fog_days_code_vis_lt1km, c_=r.fog_days_code_strict, syn=r.fog_days_synoptic_vis_lt1km,
                   gs=r.fog_days_gsod_flag, pct=round(r.pct), c=int(r.complete)) for r in y.itertuples()]
    for r in ANN[s]:
        r["code"] = r.pop("c_")


# ---- correlazione neve-temperatura (solo associazione), inverni completi
def corr(df):
    df = df.dropna(subset=["snow_days_strict", "brera_tmean_nov_mar"])
    if len(df) < 5:
        return None
    r = float(np.corrcoef(df.snow_days_strict, df.brera_tmean_nov_mar)[0, 1])
    rho = float(df.snow_days_strict.rank().corr(df.brera_tmean_nov_mar.rank()))
    return dict(n=int(len(df)), r=round(r, 2), rho=round(rho, 2))


CORR = {}
for s in STAZ:
    d = inv[(inv.station == s) & inv.complete]
    CORR[s] = dict(tutti=corr(d), senza_2008_2016=corr(d[~d.winter.between(2008, 2016)]),
                   fino_1999=corr(d[d.winter <= 1999]), dal_2000=corr(d[d.winter >= 2000]))
dump("inverni.json", dict(inverni=INV, correlazione=CORR,
                          nota_temperatura="brera_tmean_nov_mar = media delle temperature medie giornaliere nov-mar della serie unica di Brera (pagina Temperature)"))
dump("anni.json", ANN)


# ---- medie per decennio (solo inverni/anni completi)
def decadi(rows, key, metric):
    out = {}
    for r in rows:
        if not r["c"] or r.get(metric) is None:
            continue
        d = (r[key] // 10) * 10
        out.setdefault(d, []).append((r[key], r[metric]))
    return [dict(d=d, n=len(v), m=round(float(np.mean([a[1] for a in v])), 2), mn=min(a[1] for a in v), mx=max(a[1] for a in v),
                 da=min(a[0] for a in v), a=max(a[0] for a in v)) for d, v in sorted(out.items())]


DEC = {"inverni": {}, "anni": {}}
for s in STAZ:
    DEC["inverni"][s] = {m: decadi(INV[s], "w", m) for m in ["n", "h", "wide", "syn", "gs"]}
    DEC["anni"][s] = {m: decadi(ANN[s], "y", m) for m in ["v", "code", "syn", "gs"]}
dump("decenni.json", DEC)

# ---- da ricordare
RIC = {}
Lc = [r for r in INV["LINATE"] if r["c"]]
Mw = {r["w"]: r for r in INV["MALPENSA"]}
RIC["inverni_linate"] = [dict(w=r["w"], n=r["n"], h=r["h"], t=r["t"], mal=(Mw[r["w"]]["n"] if r["w"] in Mw and Mw[r["w"]]["c"] else None))
                         for r in sorted(Lc, key=lambda r: (-r["n"], -r["h"], r["w"]))[:10]]
Ml = [r for r in INV["MALPENSA"] if r["c"]]
Lw = {r["w"]: r for r in INV["LINATE"]}
RIC["inverni_malpensa"] = [dict(w=r["w"], n=r["n"], h=r["h"], t=r["t"], lin=(Lw[r["w"]]["n"] if r["w"] in Lw and Lw[r["w"]]["c"] else None))
                           for r in sorted(Ml, key=lambda r: (-r["n"], -r["h"], r["w"]))[:10]]
RIC["minimi_linate"] = [dict(w=r["w"], n=r["n"], t=r["t"]) for r in sorted(Lc, key=lambda r: (r["n"], r["w"]))[:6]]

RIC["forte"], RIC["serie"] = {}, {}
for s in STAZ:
    d = day[day.station == s].sort_values("date")
    f = d[d.snow_heavy_obs > 0]
    RIC["forte"][s] = [dict(data=r.date, ore=int(r.isd_n_hours)) for r in f.itertuples()]
    sn = d[(d.snow_obs_strict > 0) & (d.date >= "1951-01-01")].copy()
    sn["ord"] = pd.to_datetime(sn["date"]).map(pd.Timestamp.toordinal)
    runs, cur = [], []
    for r in sn.itertuples():
        if cur and r.ord == cur[-1].ord + 1:
            cur.append(r)
        else:
            if cur:
                runs.append(cur)
            cur = [r]
    if cur:
        runs.append(cur)
    runs.sort(key=lambda g: (-len(g), g[0].date))
    RIC["serie"][s] = [dict(da=g[0].date, a=g[-1].date, n=len(g), h=int(sum(1 for r in g if r.snow_heavy_obs > 0))) for g in runs[:8]]
dump("ricordi.json", RIC)

# ---- meta
def frac(y, m):
    return round(y + (m - 1) / 12, 3)

BANDE = [
    dict(id="A", da=frac(1956, 10), a=frac(1962, 1), st=["LINATE"], brev="1-4 osservazioni al giorno",
         txt="Da ottobre 1956 a fine 1961 Linate ha nei dati NOAA da 1 a 4 osservazioni al giorno (invece di 24); i buchi di file seguono."),
    dict(id="B", da=frac(1964, 8), a=frac(1971, 4), st=["LINATE", "MALPENSA"], brev="solo ogni 3 ore",
         txt="Dal 1964 al marzo 1971 le osservazioni sono ogni 3 ore (8 al giorno): fenomeni brevi possono sfuggire."),
    dict(id="C", da=frac(1983, 8), a=frac(1990, 12), st=["LINATE"], brev="solo SYNOP ogni 3 ore",
         txt="Da agosto 1983 a novembre 1990 per Linate ci sono solo i rapporti SYNOP ogni 3 ore: i METAR orari mancano nei dati NOAA, anche se l'aeroporto li emetteva."),
    dict(id="D", da=frac(1993, 7), a=frac(1999, 1), st=["LINATE", "MALPENSA"], brev="metà delle osservazioni",
         txt="Da luglio 1993 a dicembre 1998 le osservazioni orarie scendono da 24 a 16-20 ore al giorno e nel 1994-98 solo il 40-50% dei rapporti ha il codice del tempo presente (poi 90-98%)."),
    dict(id="E", da=frac(2005, 1), a=frac(2007, 1), st=["LINATE", "MALPENSA"], brev="cambio di codifica",
         txt="Nel 2005-06 cambia la codifica: compare il testo METAR completo e il codice di nebbia comprende anche la nebbia a banchi (BCFG, MIFG) con visibilità sopra 1 km. Il conteggio per codice sale, quello con visibilità sotto 1 km no."),
    dict(id="F", da=frac(2018, 1), a=2026.0, st=["LINATE"], brev="METAR automatici (AUTO)",
         txt="Dal 2018 a Linate compaiono METAR con la sigla AUTO (1% nel 2018, 23% nel 2020, poi 1-5%), quasi tutti di notte, e il codice automatico del tempo presente."),
]
last = day.groupby("station")["date"].max().to_dict()
first = day.groupby("station")["date"].min().to_dict()
excl_w = {s: [r["w"] for r in INV[s] if not r["c"]] for s in STAZ}
excl_y = {s: [r["y"] for r in ANN[s] if not r["c"]] for s in STAZ}
meta = dict(
    scaricato="2026-10-30", ultimo_giorno=last["LINATE"], primo_giorno=first, soglia_completo=MIN_PCT, anno_da=DA,
    bande=BANDE, inverni_esclusi=excl_w, anni_esclusi=excl_y,
    n_inverni_completi={s: sum(1 for r in INV[s] if r["c"]) for s in STAZ},
    n_anni_completi={s: sum(1 for r in ANN[s] if r["c"]) for s in STAZ},
    stazioni=dict(LINATE=dict(nome="Milano Linate", usaf_wban="160800-99999", wmo="16080", icao="LIML", quota_m=107),
                  MALPENSA=dict(nome="Milano Malpensa", usaf_wban="160660-99999", wmo="16066", icao="LIMC", quota_m=234)),
)
dump("meta.json", meta)
print("inverni completi", meta["n_inverni_completi"], "anni completi", meta["n_anni_completi"])
print("correlazione", json.dumps(CORR))
