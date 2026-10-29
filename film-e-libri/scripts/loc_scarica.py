"""LoC catalogo via SRU (lx2.loc.gov:210/lcdb, pubblico). L'API loc.gov/books e dietro Cloudflare (403) e NON e stata aggirata. Uso: python -I loc_scarica.py <raw/loc>"""
import sys, os, time, requests, re
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
QS = {"fiction": 'bath.subject="Milan (Italy)--Fiction"', "tutti_milan_italy": 'bath.subject="Milan (Italy)"'}
def sru(q, start, n):
    for t in range(4):
        time.sleep(3)
        try:
            r = requests.get("http://lx2.loc.gov:210/lcdb", params={"version": "1.1", "operation": "searchRetrieve", "query": q, "startRecord": start, "maximumRecords": n, "recordSchema": "dc"}, headers=UA, timeout=90)
        except requests.RequestException as e: print("rete", e); time.sleep(20*(t+1)); continue
        if r.status_code == 200: return r.text
        print("HTTP", r.status_code); time.sleep(30*(t+1))
    raise RuntimeError("sru")
for name, q in QS.items():
    first = sru(q, 1, 1)
    n = int(re.search(r"<zs:numberOfRecords>(\d+)", first).group(1)); print(name, "numberOfRecords", n, flush=True)
    if name != "fiction": 
        open(os.path.join(out, name + "_conteggio.xml"), "w", encoding="utf8").write(first); continue
    for s in range(1, n + 1, 50):
        p = os.path.join(out, f"{name}_{s:05d}.xml")
        if os.path.exists(p): continue
        open(p, "w", encoding="utf8").write(sru(q, s, 50))
print("FINE")
