"""Campioni piccoli dalle fonti alternative alla Scala (nessuna raccolta di massa).
Uso: python -I scripts/fonti_alternative.py raw/alternative
Fa: (1) Wikidata: stagioni della Scala -> produzioni (P527) con direttore/regia/cast; (2) Wikipedia: estratto 1957-58 dal JSON gia' scaricato;
(3) sito pubblico della Scala (fuori da /it/archivio): lista pagine di stagione dalla sitemap + UNA pagina di spettacolo con cast, in CSV;
(4) Marangoni-Vanbianchi: estratto di una stagione dal testo OCR gia' scaricato. Pausa tra richieste, UA descrittivo, si saltano i file gia' presenti."""
import sys, os, re, json, csv, time, html, requests
out = sys.argv[1]; base = os.path.dirname(os.path.dirname(os.path.abspath(out))) if False else os.path.abspath(os.path.join(out, "..", ".."))
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}

def put(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8", newline="").write(text)

# (1) Wikidata
p = os.path.join(out, "wikidata", "stagioni_produzioni.json")
if not os.path.exists(p):
    q = """SELECT ?prod ?prodLabel ?sea ?seaLabel ?start ?pdate
  (GROUP_CONCAT(DISTINCT ?condL; separator=" / ") AS ?direttori) (GROUP_CONCAT(DISTINCT ?dirL; separator=" / ") AS ?registi)
  (COUNT(DISTINCT ?perf) AS ?n_interpreti) WHERE {
 ?sea wdt:P276 wd:Q5471 ; wdt:P31 ?t . ?t rdfs:label "stagione del Teatro alla Scala"@it .
 OPTIONAL{?sea wdt:P580 ?start}
 ?sea wdt:P527 ?prod .
 OPTIONAL{?prod wdt:P585 ?pdate}
 OPTIONAL{?prod wdt:P3300 ?cond . ?cond rdfs:label ?condL . FILTER(LANG(?condL)="it" || LANG(?condL)="en")}
 OPTIONAL{?prod wdt:P57 ?dir . ?dir rdfs:label ?dirL . FILTER(LANG(?dirL)="it" || LANG(?dirL)="en")}
 OPTIONAL{?prod wdt:P175|wdt:P161 ?perf}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } } GROUP BY ?prod ?prodLabel ?sea ?seaLabel ?start ?pdate"""
    r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"},
                     headers=dict(UA, Accept="application/sparql-results+json"), timeout=180)
    r.raise_for_status(); put(p, r.text)
    rows = r.json()["results"]["bindings"]
    with open(os.path.join(out, "wikidata", "stagioni_produzioni.csv"), "w", encoding="utf8", newline="") as f:
        w = csv.writer(f); w.writerow(["stagione", "inizio_stagione", "produzione", "data_produzione", "direttori", "registi", "n_interpreti", "qid_produzione"])
        for x in sorted(rows, key=lambda x: x.get("start", {}).get("value", "")):
            g = lambda k: x.get(k, {}).get("value", "")
            w.writerow([g("seaLabel"), g("start")[:10], g("prodLabel"), g("pdate")[:10], g("direttori"), g("registi"), g("n_interpreti"), g("prod").split("/")[-1]])
    print("wikidata", len(rows), "righe"); time.sleep(5)

# (2) Wikipedia: estratto 1957-1959 (testo CC BY-SA 4.0, da it.wikipedia.org/wiki/Stagioni_liriche_del_Teatro_alla_Scala)
p = os.path.join(out, "wikipedia", "estratto_1957_1959.txt")
src = os.path.join(base, "raw", "wikipedia", "Stagioni_liriche_del_Teatro_alla_Scala.json")
if not os.path.exists(p) and os.path.exists(src):
    j = json.load(open(src, encoding="utf8"))
    def find(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and len(v) > 100000: return v
                r = find(v)
                if r: return r
        elif isinstance(o, list):
            for v in o:
                r = find(v)
                if r: return r
    t = find(j); a = t.find("'''1957'''"); b = t.find("'''1960'''")
    put(p, "Fonte: it.wikipedia.org, voce 'Stagioni liriche del Teatro alla Scala' (CC BY-SA 4.0), wikitesto grezzo, anni 1957-1959\n\n" + t[a:b])
    print("wikipedia estratto", b - a, "caratteri")

# (3) Sito pubblico della Scala
d = os.path.join(out, "scala_sito_pubblico")
p = os.path.join(d, "urls_stagione.txt")
if not os.path.exists(p):
    r = requests.get("https://www.teatroallascala.org/it/sitemap.html", headers=UA, timeout=60); r.raise_for_status()
    urls = re.findall(r"<loc>([^<]+)</loc>", r.text)
    put(p, "\n".join(u for u in urls if re.search(r"/it/stagione/20\d\d-20\d\d/", u)) + "\n"); time.sleep(4)
pg = os.path.join(d, "la-forza-del-destino_2024-25.html")
if not os.path.exists(pg):
    r = requests.get("https://www.teatroallascala.org/it/stagione/2024-2025/opera/la-forza-del-destino.html", headers=UA, timeout=60); r.raise_for_status()
    put(pg, r.text); time.sleep(4)
h = open(pg, encoding="utf8", errors="replace").read()
clean = lambda s: html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).replace("\xa0", " ").strip()
rows = []
titolo = clean(re.search(r"<title>(.*?)</title>", h, re.S).group(1)).replace(" - Teatro alla Scala", "")
dati = re.search(r'<section id="cast".*?</section>', h, re.S).group(0)
for k, v in re.findall(r'<th scope="row">(.*?)</th><td>(.*?)</td>', dati, re.S): rows.append(["staff", clean(k), clean(v)])
cast = re.search(r'<table class="evt">(.*?)</table>', h, re.S).group(1)
for k, v in re.findall(r'<td class="dt">(.*?)</td>\s*<td>(.*?)</td>', cast, re.S): rows.append(["cast", clean(k), clean(v)])
date = re.search(r"Tutte le date(.*?)(Vedi tutti|In breve)", clean(h), re.S)
if date: rows.append(["date", "tutte_le_date", date.group(1).strip()])
with open(os.path.join(d, "la-forza-del-destino_2024-25.csv"), "w", encoding="utf8", newline="") as f:
    w = csv.writer(f); w.writerow(["tipo", "ruolo", "valore"]); w.writerow(["titolo", "titolo", titolo]); w.writerows(rows)
print("scala sito: righe", len(rows) + 1)

# (4) Marangoni-Vanbianchi: stagione di carnevale-quaresima 1910-11 dal testo OCR (solo pista, non ripubblicare)
p = os.path.join(out, "marangoni", "estratto_stagione_1910-11.txt")
src = os.path.join(base, "raw", "cambiasi", "pdf24_merged-16", "pdf24_merged-16_djvu.txt")
if not os.path.exists(p) and os.path.exists(src):
    t = open(src, encoding="utf8", errors="replace").read(); i = t.find("STAGIONE DI CARNEVALE-QUARESIBMA 1010-1911")
    put(p, "Fonte: G. Marangoni e C. Vanbianchi, 'La Scala. Studi e ricerche' (1922), testo OCR di Internet Archive (pdf24_merged-16). SOLO CAMPIONE DI LAVORO.\n\n" + t[i - 50:i + 3200])
    print("marangoni estratto")
