"""Prepara i dati della pagina docs/milano-raccontata/: opere.json (tutte le opere), luoghi.json (luoghi con coordinate), stats.json.
Solo fatti e link: niente frasi di Wikipedia.  Uso: python -I 26_dati_pagina.py <strand> <cartella docs/milano-raccontata>"""
import sys, os, csv, json, collections
from urllib.parse import quote
base, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(out, "data"), exist_ok=True)
P = lambda *a: os.path.join(base, *a)
KIND = {"film": "f", "serie_tv": "f", "libro": "l", "altro": "a"}
opere = []; idx = {}
for f, tp in (("film", "film"), ("serie_tv", "serie_tv"), ("libri", "libro"), ("altro", "altro")):
    for r in csv.DictReader(open(P("pulito", f + ".csv"), encoding="utf8")):
        wid = r["qid"] or ("OL:" + r["ol_key"] if r["ol_key"] else "LOC:" + (r["titolo_it"] or r["titolo_en"])[:60])
        titolo = r["titolo_it"] or r["titolo_en"] or r["qid"]
        if titolo == r["qid"] and r["qid"]: titolo = r["qid"] + " (titolo non disponibile)"
        wiki = ""
        if r["itwiki"]: wiki = "https://it.wikipedia.org/wiki/" + quote(r["itwiki"].replace(" ", "_"), safe="()_,'!:")
        elif r["enwiki"]: wiki = "https://en.wikipedia.org/wiki/" + quote(r["enwiki"].replace(" ", "_"), safe="()_,'!:")
        fonti = []
        if r["qid"]: fonti.append("Wikidata/Wikipedia")
        if r["fonte_openlibrary"] == "1": fonti.append("Open Library")
        if r["fonte_loc"] == "1": fonti.append("Library of Congress")
        o = {"id": wid, "t": titolo, "k": KIND[tp], "s": 1 if tp == "serie_tv" else 0,
             "y": int(r["anno"]) if r["anno"] else None, "d": int(r["decennio"]) if r["decennio"] else None,
             "c": (r["regia"] if tp != "libro" else r["autore"]) or (r["autore"] or ""), "w": wiki,
             "q": r["qid"], "ol": ("https://openlibrary.org" + r["ol_key"]) if r["ol_key"] else "", "f": fonti, "p": []}
        idx[wid] = len(opere); opere.append(o)
# luoghi
rows = list(csv.DictReader(open(P("pulito", "luoghi.csv"), encoding="utf8")))
luoghi = {}
for r in rows:
    pid = int(r["id_luogo"])
    L = luoghi.setdefault(pid, {"id": pid, "n": r["luogo"], "lat": float(r["lat"]), "lon": float(r["lon"]), "tl": r["tipo_luogo"]})
    opere[idx[r["id_opera"]]]["p"].append([pid, "a" if r["tipo"] == "ambientazione" else "r", "a" if r["confidence"] == "alta" else "m"])
for o in opere: o["p"].sort()
# togliamo i luoghi senza opere (non dovrebbero esserci) e ordiniamo
lista = sorted(luoghi.values(), key=lambda x: x["id"])
opere.sort(key=lambda o: (o["y"] or 9999, o["t"]))
json.dump(opere, open(os.path.join(out, "data", "opere.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(lista, open(os.path.join(out, "data", "luoghi.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
st = json.load(open(P("pulito", "_statistiche_luoghi.json"), encoding="utf8"))
prec = list(csv.DictReader(open(P("pulito", "_controllo_precisione.csv"), encoding="utf8")))
st["precisione"] = {"ultimo_giro": {"n": int(prec[-1]["campione"]), "giusti": int(prec[-1]["giusti"])},
                    "tutti_i_giri": {"n": sum(int(x["campione"]) for x in prec), "giusti": sum(int(x["giusti"]) for x in prec)}}
st["totali_opere"] = dict(collections.Counter(o["k"] for o in opere))
json.dump(st, open(os.path.join(out, "data", "stats.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
# copie dei due csv (fatti, nessuna frase)
import shutil
shutil.copy(P("pulito", "luoghi.csv"), os.path.join(out, "data", "luoghi.csv"))
print(len(opere), "opere,", len(lista), "luoghi;", {k: os.path.getsize(os.path.join(out, "data", k)) for k in os.listdir(os.path.join(out, "data"))})
