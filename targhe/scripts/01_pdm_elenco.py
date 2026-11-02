"""Scarica le pagine ELENCO (non le schede) di pietredellamemoria.it/comuni/milano/ per contare le voci.
1 richiesta ogni 1,3 s, User-Agent che dice chi siamo. Uso: python -I -X utf8 01_pdm_elenco.py <cartella raw/pdm assoluta>"""
import sys, time, urllib.request, pathlib
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
UA = "milano-in-dati research (davide.caniatti@gmail.com)"
for p in range(1, 84):
    f = out / f"elenco_{p:02d}.html"
    if f.exists() and f.stat().st_size > 5000: continue
    u = "https://www.pietredellamemoria.it/comuni/milano/" + (f"page/{p}/" if p > 1 else "")
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40)
        f.write_bytes(r.read())
    except Exception as e:
        print(p, e)
    time.sleep(1.3)
print("fatto")
