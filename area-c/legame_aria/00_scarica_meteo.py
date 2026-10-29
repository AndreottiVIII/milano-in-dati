# Scarica da dati.lombardia.it (ARPA Lombardia, CC0) vento, pioggia e temperatura di Milano Brera (2016-2024) e Milano Lambrate (2010-2014).
# Sensori: Brera vento 19007, pioggia 19373, temperatura 5897; Lambrate vento 2003, pioggia 2006, temperatura 2001 (registro nf78-nj6b).
# uso: python -I 00_scarica_meteo.py <cartella raw_meteo>   (riprende: salta i file gia' completi)
import requests, sys, os, time
H = {"User-Agent": "milano-in-dati/1.0 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
DS = {"vento": ["x9gp-z9xx", "hu5q-68e3"], "pioggia": ["2kar-pnuk", "pstb-pga6"], "temperatura": ["d4kj-kbpj", "w9wd-u6jh"]}
SENS = {"Brera": {"vento": "19007", "pioggia": "19373", "temperatura": "5897", "da": "2016-08-25", "a": "2024-12-05"},
        "Lambrate": {"vento": "2003", "pioggia": "2006", "temperatura": "2001", "da": "2010-12-01", "a": "2014-12-31"}}
def get(url, params):
    for a in range(12):
        try:
            r = requests.get(url, params=params, headers=H, timeout=300)
            if r.status_code in (429, 502, 503, 504):
                w = min(30 * 2 ** a, 900); print("attesa", w, r.status_code, flush=True); time.sleep(w); continue
            r.raise_for_status(); return r.text
        except Exception as e:
            print("err", e, flush=True); time.sleep(20)
    raise RuntimeError("fail")
for stz, c in SENS.items():
    for var in ["vento", "pioggia", "temperatura"]:
        sid = c[var]
        for did in DS[var]:
            fn = os.path.join(out, f"{stz}_{var}_{did}_sensore{sid}.csv")
            if os.path.exists(fn): continue
            parts = []; off = 0
            while True:
                t = get(f"https://www.dati.lombardia.it/resource/{did}.csv", {"$where": f"idsensore='{sid}' AND data >= '{c['da']}T00:00:00' AND data <= '{c['a']}T23:59:59'",
                                                                              "$order": "data", "$limit": 50000, "$offset": off})
                lines = t.splitlines(); n = len(lines) - 1
                if off == 0: parts.append("\n".join(lines))
                elif n > 0: parts.append("\n".join(lines[1:]))
                if n < 50000: break
                off += 50000; time.sleep(2)
            open(fn + ".tmp", "w", encoding="utf-8").write("\n".join(parts) + "\n"); os.replace(fn + ".tmp", fn)
            print(stz, var, did, off + n, flush=True); time.sleep(3)
print("done", flush=True)
