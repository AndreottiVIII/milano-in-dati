"""Scarica le pagine di spettacolo delle stagioni 2023-24 ... 2026-27 dal sito pubblico della Scala.
Autorizzazione della Scala (29/10/2026); robots.txt non vieta /it/stagione/. Una richiesta alla volta, pausa >= 3 s,
cache in raw/scala_stagioni/ (si riprende da dove si e' fermato). Se compare un blocco (403/429/captcha) SI FERMA.
Uso: python -I scripts/scarica_scala_stagioni.py raw/scala_stagioni raw/alternative/scala_sito_pubblico/urls_stagione.txt"""
import sys, os, re, time, requests
out, urlf = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research project, authorized by Teatro alla Scala (contact: davide.caniatti@gmail.com)"}
CAT = ("opera", "balletto", "concerti", "grandi-spettacoli-per-piccoli", "grandi-spettacoli-per-piccoli-e-famiglie", "tournee", "eventi-fuori-sede")
urls = [u.strip() for u in open(urlf, encoding="utf-8") if u.strip()]
sel = []
for u in urls:
    m = re.search(r"/it/stagione/(20(2[3-6])-20\d\d)/([^/]+)/.+\.html$", u)
    if m and m.group(3) in CAT:
        sel.append(u)
print(len(sel), "pagine da avere", flush=True)
n = 0
for u in sel:
    rel = u.split("/it/stagione/")[1].replace("/", "__")
    p = os.path.join(out, rel)
    if os.path.exists(p) and os.path.getsize(p) > 2000:
        continue
    try:
        r = requests.get(u, headers=UA, timeout=60)
    except Exception as e:
        print("errore rete", u, e, flush=True); time.sleep(10); continue
    low = r.text[:5000].lower()
    if r.status_code in (403, 429, 503) or "captcha" in low or "etnobot" in low and r.status_code != 200:
        print("BLOCCO/LIMITE: stop", r.status_code, u, flush=True); sys.exit(2)
    if r.status_code != 200:
        print("stato", r.status_code, u, flush=True); time.sleep(4); continue
    open(p, "w", encoding="utf-8").write(r.text)
    n += 1
    if n % 20 == 0: print(n, "scaricate", flush=True)
    time.sleep(3.5)
print("FINITO", n, "nuove", flush=True)
