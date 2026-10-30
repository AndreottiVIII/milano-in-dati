"""Registrazioni sonore (dal vivo) alla Scala nel catalogo SBN. Stesso cliente educato di sbn_lib (3 s, cache, STOP su blocchi).
Fase A: ricerche per frasi con 'Teatro alla Scala' + orchestra/coro (tutte le pagine). Fase B: scheda completa dei candidati.
Uso (dalla cartella scala/):  python -I -X utf8 scripts/sbn_registrazioni_cerca.py        (riprendibile)"""
import sys, os, re, json, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib as s
QUERIES = ["orchestra e coro del teatro alla scala", "coro del teatro alla scala", "live teatro alla scala", "milano teatro alla scala live",
           "teatro alla scala live recording", "teatro alla scala dal vivo", "scala di milano dal vivo"]
MAXPAGES = 100
def candidato(r):
    if not (r.get("tipo") or "").lower().startswith("registrazione sonora"): return False
    blob = " ".join([r.get("titolo", ""), r.get("pubblicazione", "") or "", r.get("autorePrincipale", "") or ""])
    return bool(re.search(r"scala", blob, re.I))
tot = {}
for q in QUERIES:
    start = 0
    while True:
        d, cached = s.get("search", {"any": q, "rows": 100, "start": start})
        n = d.get("numFound", 0)
        if start == 0: print(f"{q!r}: numFound={n}", flush=True)
        for r in d.get("briefRecords", []): tot[r["codiceIdentificativo"]] = r
        start += 100
        if start >= n or start >= MAXPAGES * 100 or not d.get("briefRecords"): break
# anche i risultati gia' in cache dalle ricerche precedenti
for f in glob.glob(os.path.join(s.ROOT, "search", "*.json")):
    try:
        for r in json.load(open(f, encoding="utf8")).get("briefRecords", []): tot.setdefault(r["codiceIdentificativo"], r)
    except Exception: pass
cand = [r for r in tot.values() if candidato(r)]
print("record sonori in cache:", sum(1 for r in tot.values() if (r.get('tipo') or '').lower().startswith('registrazione sonora')), "candidati con 'scala':", len(cand), flush=True)
json.dump(cand, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sbn", "_registrazioni_candidati.json"), "w", encoding="utf8"), ensure_ascii=False)
# Fase B: le schede complete (con note tipo "Registrazione dal vivo, 4 febbraio 1954") solo per i candidati probabilmente dal vivo/storici
# (altrimenti sarebbero ~3.000 richieste): parole 'live/dal vivo/inedito', anno nel titolo, o etichette note per le registrazioni dal vivo.
LIVE = re.compile(r"live|dal vivo|inedit|registrazione dal|concerto del|teatro alla scala[, ]+(stagione|\d)|melodram|myto|arkadia|foyer|artists live|mrf|urania|musicom|rcs mediagroup|opera d.oro|gala|hardy|bongiovanni|archipel|andromeda|walhall|premiere opera|legato|cantus classics|living stage|opera lovers|house of opera|nuova era|testament|ideale audience|datum|opera rara|mondo musica", re.I)
ANNO = re.compile(r"\b(19[4-9]\d|20[0-2]\d)\b")   # anno scritto nel TITOLO (non nella data di pubblicazione del disco)
sel = [r for r in cand if LIVE.search(r["titolo"] + " | " + (r.get("pubblicazione") or "")) or ANNO.search(r["titolo"])]
print("da scaricare (probabili dal vivo/storiche):", len(sel), flush=True)
cand = sel
n = 0
for i, r in enumerate(cand):
    d, cached = s.get("full", {"bid": r["codiceIdentificativo"]})
    if not cached:
        n += 1
        if n % 25 == 0: print(f"{i+1}/{len(cand)} scaricate {n}", flush=True)
print("FINE", flush=True)
