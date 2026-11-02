"""Fase 2 (con autorizzazione di ANMIG dichiarata da Davide il 2/11/2026): scarica le SCHEDE di Pietre della Memoria per il Comune di Milano,
escluse le pietre d'inciampo. Riprende da dove si e' fermato (cache in raw/pdm/schede/), 1 richiesta ogni 1,3 s, User-Agent che dice chi siamo.
robots.txt: vieta solo /wp-admin/. Si salva l'HTML in raw/pdm/schede/ (NON pubblicare); le foto non si scaricano.
Uso: python -I -X utf8 05_pdm_schede.py <raw/pdm assoluto>"""
import sys, json, time, pathlib, re, urllib.request
raw = pathlib.Path(sys.argv[1]); out = raw / "schede"; out.mkdir(exist_ok=True)
UA = "milano-in-dati research (davide.caniatti@gmail.com)"
items = json.load(open(raw / "_elenco_titoli.json", encoding="utf8"))
todo = [(u, t) for u, t in items.items() if not re.search(r"inciampo", t, re.I)]
print(len(items), "voci;", len(todo), "da scaricare (senza pietre d'inciampo)", flush=True)
log = open(raw / "schede_log.csv", "a", encoding="utf8")
for n, (u, t) in enumerate(todo, 1):
    slug = u.rstrip("/").split("/")[-1]
    f = out / (slug + ".html")
    if f.exists() and f.stat().st_size > 20000: continue
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60)
        b = r.read(); f.write_bytes(b); log.write(f"{u};{r.status};{len(b)}\n"); log.flush()
    except Exception as e:
        log.write(f"{u};ERR;{e}\n"); log.flush()
    time.sleep(1.3)
    if n % 25 == 0: print(n, flush=True)
print("fatto", flush=True)
