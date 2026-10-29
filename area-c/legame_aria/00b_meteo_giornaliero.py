# Dai dati ARPA a 10 minuti (raw_meteo) a valori giornalieri: vento medio (m/s), pioggia totale (mm), temperatura media (gradi C).
# Orario "ora solare" a fine intervallo: l'intervallo 00:00 appartiene al giorno prima. Giorno valido con almeno l'80% degli intervalli (116 su 144).
# uso: python -I 00b_meteo_giornaliero.py <raw_meteo> <file csv di uscita>
import pandas as pd, glob, os, sys
raw, out = sys.argv[1], sys.argv[2]
cols = {}
for stz in ["Brera", "Lambrate"]:
    for var, f in [("vento", "mean"), ("pioggia", "sum"), ("temperatura", "mean")]:
        parti = []
        for fn in sorted(glob.glob(os.path.join(raw, f"{stz}_{var}_*.csv"))):
            d = pd.read_csv(fn, usecols=["data", "valore", "stato"])
            if len(d): parti.append(d)
        if not parti: continue
        d = pd.concat(parti)
        d = d[(d.stato == "VA") & d.valore.notna() & (d.valore > -900)]
        d["t"] = pd.to_datetime(d.data)
        d = d.drop_duplicates("t")
        d["giorno"] = (d.t - pd.Timedelta(minutes=1)).dt.normalize()
        g = d.groupby("giorno").valore
        n = g.size()
        s = (g.mean() if f == "mean" else g.sum())
        s = s[n >= 116]
        cols[f"{var}_{stz}"] = s
        print(stz, var, "giorni validi", len(s), s.index.min().date(), s.index.max().date(), "media", round(s.mean(), 2))
M = pd.DataFrame(cols); M.index.name = "data"
M.round(2).to_csv(out, sep=";")
