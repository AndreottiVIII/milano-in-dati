"""Dati per la pagina docs/milano-raccontata/ (nuovo schema): luoghi vicini (meno di 100 m) uniti in un gruppo,
con l'elenco delle opere (film, serie, libri) che li nominano. Solo fatti: titolo, anno, tipo; i link stanno gia in opere.json.
Uso: python -I -X utf8 27_gruppi_luoghi_v2.py <cartella docs/milano-raccontata>"""
import sys, os, json, math
out = sys.argv[1]
D = lambda f: os.path.join(out, "data", f)
opere = json.load(open(D("opere.json"), encoding="utf-8"))
luoghi = {l["id"]: l for l in json.load(open(D("luoghi.json"), encoding="utf-8"))}
per = {}
for o in opere:
    if o["k"] == "a":
        continue
    for pid, tipo, conf in o["p"]:
        per.setdefault(pid, {})[o["id"]] = (tipo, conf)
def dist(a, b):
    dy = (a["lat"] - b["lat"]) * 111320
    dx = (a["lon"] - b["lon"]) * 111320 * math.cos(math.radians(45.46))
    return math.hypot(dx, dy)
ordine = sorted(per, key=lambda p: -len(per[p]))
gruppi = []
for pid in ordine:
    l = luoghi[pid]
    for g in gruppi:
        if dist(l, g) < 100:
            g["_ids"].append(pid)
            break
    else:
        gruppi.append({"n": l["n"], "lat": l["lat"], "lon": l["lon"], "tl": l["tl"], "_ids": [pid]})
risultato = []
for g in gruppi:
    ops = {}
    for pid in g["_ids"]:
        for oid, (t, c) in per[pid].items():
            ops.setdefault(oid, [set(), "m"])
            ops[oid][0].add(t)
            if c == "a":
                ops[oid][1] = "a"
    g["o"] = [[oid, "".join(sorted(t)), c] for oid, (t, c) in ops.items()]
    del g["_ids"]
    risultato.append(g)
risultato.sort(key=lambda g: -len(g["o"]))
json.dump(risultato, open(D("raccontata_gruppi.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(risultato), [(g["n"], len(g["o"])) for g in risultato[:12]])
