"""Scarica le schede biografiche del Comitato Pietre d'inciampo Milano (cache, 1 richiesta ogni 1,2 s).
Uso: python -I -X utf8 scarica_biografie.py <raw_dir_assoluto> <id_max>
robots.txt: Disallow vuoto (tutto permesso). Note legali: libero accesso e riproduzione dei contenuti."""
import sys, os, time, urllib.request
raw = sys.argv[1]; idmax = int(sys.argv[2])
d = os.path.join(raw, "biografie"); os.makedirs(d, exist_ok=True)
UA = "milano-in-dati research (davide.caniatti@gmail.com)"
log = open(os.path.join(raw, "download_biografie_log.csv"), "a", encoding="utf-8")
for i in range(1, idmax + 1):
    f = os.path.join(d, f"{i}.html")
    if os.path.exists(f) and os.path.getsize(f) > 50000: continue
    url = f"https://www.pietredinciampomilano.it/?page_id=451&ricerca={i}"
    for tent in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60)
            b = r.read(); open(f, "wb").write(b)
            log.write(f"{i},{r.status},{len(b)},{time.strftime('%Y-%m-%d')}\n"); log.flush(); break
        except Exception as e:
            log.write(f"{i},ERR,{e},{time.strftime('%Y-%m-%d')}\n"); log.flush(); time.sleep(5)
    time.sleep(1.2)
print("fine")
