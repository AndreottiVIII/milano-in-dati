"""Prova a scaricare dal sito pubblico della Scala (robots.txt non vieta /it/stagione/; autorizzazione 29/10/2026) le pagine della serata
inaugurale delle stagioni 2012-13 ... 2022-23 (indirizzi indovinati dal modello delle stagioni recenti). Pochissime richieste (una alla volta, 4 s),
si ferma a un blocco 403/429/captcha. Cache in raw/aperture_scala/. Uso: python -I -X utf8 aperture_scala_vecchie.py <cartella>"""
import sys, os, time, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research project, authorized by Teatro alla Scala (contact: davide.caniatti@gmail.com)"}
CAND = {
 "2021-2022": ["macbeth-7-dicembre-serata-inaugurale", "macbeth-prima-della-scala"],
 "2019-2020": ["tosca-7-dicembre-serata-inaugurale", "tosca"],
 "2018-2019": ["attila-7-dicembre-serata-inaugurale", "attila"],
 "2017-2018": ["andrea-chenier-7-dicembre-serata-inaugurale", "andrea-chenier"],
 "2016-2017": ["madama-butterfly-7-dicembre-serata-inaugurale", "madama-butterfly-1904"],
 "2015-2016": ["giovanna-d-arco-7-dicembre-serata-inaugurale", "giovanna-d-arco"],
 "2014-2015": ["fidelio-7-dicembre-serata-inaugurale", "fidelio"],
 "2013-2014": ["la-traviata-7-dicembre-serata-inaugurale", "la-traviata"],
}
for stag, slugs in CAND.items():
    for slug in slugs:
        p = os.path.join(out, f"{stag}__opera__{slug}.html")
        if os.path.exists(p): break
        u = f"https://www.teatroallascala.org/it/stagione/{stag}/opera/{slug}.html"
        try: r = requests.get(u, headers=UA, timeout=60)
        except Exception as e: print("rete", u, e, flush=True); time.sleep(8); continue
        low = r.text[:5000].lower()
        if r.status_code in (403, 429, 503) or "captcha" in low: print("BLOCCO: stop", r.status_code, u, flush=True); sys.exit(2)
        print(r.status_code, len(r.text), "Direttore" in r.text, u, flush=True)
        if r.status_code == 200 and "Direttore" in r.text:
            open(p, "w", encoding="utf8").write(r.text); time.sleep(4); break
        time.sleep(4)
