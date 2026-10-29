"""Unisce i match (Wikipedia) e i luoghi precisi di Wikidata -> pulito/luoghi.csv + pulito/_statistiche_luoghi.json
Uso: python -I 24_luoghi_csv.py <strand>"""
import sys, os, csv, json, math, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
base = sys.argv[1]
P = lambda *a: os.path.join(base, *a)
OPERE = {}
for f, tipo_opera in (("film", "film"), ("serie_tv", "serie_tv"), ("libri", "libro"), ("altro", "altro")):
    for r in csv.DictReader(open(P("pulito", f + ".csv"), encoding="utf8")):
        wid = r["qid"] or ("OL:" + r["ol_key"] if r["ol_key"] else "")
        if not wid: wid = "LOC:" + (r["titolo_it"] or r["titolo_en"])[:60]
        r["tipo_opera"] = tipo_opera; OPERE[wid] = r
ORD = {"alta": 3, "media": 2, "bassa": 1}
rows = []   # wid, luogo, lat, lon, tipo, tipo_luogo, sezione, conf, fonte
for m in json.load(open(P("pulito", "_match_tutti.json"), encoding="utf8")):
    if m["conf"] == "bassa": continue
    rows.append(dict(wid=m["wid"], luogo=m["luogo"], lat=m["lat"], lon=m["lon"], tipo=m["tipo"], tipo_luogo=m["tipo_luogo"], sezione=m["sezione"],
                     conf=m["conf"], fonte="wikipedia_" + m["lang"], gf=m["fonte"]))
# Wikidata: P840 -> ambientazione, P915 -> riprese (solo luoghi diversi da Milano citta, con coordinate)
for prop, tipo in (("p840", "ambientazione"), ("p915", "riprese")):
    for b in json.load(open(P("raw", "wikidata", f"luoghi_{prop}.json"), encoding="utf8"))["results"]["bindings"]:
        pl = b["pl"]["value"].rsplit("/", 1)[1]
        if pl == "Q490" or "coord" not in b: continue
        wid = b["w"]["value"].rsplit("/", 1)[1]
        if wid not in OPERE: continue
        mm = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"]["value"])
        if not mm: continue
        nome = b.get("plLabel", {}).get("value", pl)
        if re.match(r"^Q\d+$", nome): continue
        tl = b.get("plInstLabel", {}).get("value", "luogo")
        rows.append(dict(wid=wid, luogo=nome, lat=float(mm.group(2)), lon=float(mm.group(1)), tipo=tipo, tipo_luogo=tl, sezione="Wikidata " + prop.upper(), conf="alta", fonte="wikidata"))
PRIO = {"elenco_a_mano": 0, "civici_comune": 1, "civici_comune_cognome": 1, "NIL": 2, "OSM": 3, "wikidata": 4, "wikilink": 5}
for r in rows: r["pr"] = PRIO.get(r.get("gf", r["fonte"]), 5)
rows.sort(key=lambda r: r["pr"])
# --- raggruppamento dei luoghi: stesso posto se a meno di 60 m
def dist_m(a, b): return math.hypot((a[0]-b[0])*111000, (a[1]-b[1])*111000*0.7)
clusters = []   # {lat, lon, nomi Counter, tipo_luogo Counter}
def cluster_di(r):
    for c in clusters:
        if dist_m((c["lat"], c["lon"]), (r["lat"], r["lon"])) < 60: return c
    c = dict(id=len(clusters)+1, lat=r["lat"], lon=r["lon"], nomi=collections.Counter(), tl=collections.Counter()); clusters.append(c); return c
for r in rows:
    c = cluster_di(r); c["nomi"][r["luogo"]] += 1; c["tl"][r["tipo_luogo"]] += 1; r["cid"] = c["id"]
def nome_cluster(c):
    # nome piu frequente, a parita il piu corto
    return sorted(c["nomi"].items(), key=lambda x: (-x[1], len(x[0])))[0][0]
for c in clusters: c["nome"] = nome_cluster(c)
agg = {}
for r in rows:
    k = (r["wid"], r["cid"], r["tipo"])
    a = agg.setdefault(k, dict(wid=r["wid"], cid=r["cid"], tipo=r["tipo"], sezioni=[], conf=0, fonti=set(), n=0, tl=collections.Counter()))
    a["n"] += 1; a["conf"] = max(a["conf"], ORD[r["conf"]]); a["fonti"].add(r["fonte"]); a["tl"][r["tipo_luogo"]] += 1
    if r["sezione"] not in a["sezioni"]: a["sezioni"].append(r["sezione"])
CL = {c["id"]: c for c in clusters}
INV = {v: k for k, v in ORD.items()}
out = []
for a in agg.values():
    o = OPERE[a["wid"]]; c = CL[a["cid"]]
    out.append(dict(id_opera=a["wid"], titolo=o["titolo_it"] or o["titolo_en"], tipo_opera=o["tipo_opera"], anno=o["anno"], decennio=o["decennio"],
                    luogo=c["nome"], id_luogo=c["id"], lat=round(c["lat"], 6), lon=round(c["lon"], 6), tipo=a["tipo"], tipo_luogo=c["tl"].most_common(1)[0][0],
                    sezione="; ".join(a["sezioni"]), confidence=INV[a["conf"]], n_menzioni=a["n"], fonte="; ".join(sorted(a["fonti"]))))
out.sort(key=lambda r: (r["tipo_opera"], r["titolo"], r["luogo"], r["tipo"]))
with open(P("pulito", "luoghi.csv"), "w", encoding="utf8", newline="") as f:
    wr = csv.DictWriter(f, list(out[0].keys())); wr.writeheader(); wr.writerows(out)
# --- statistiche
wids = {r["id_opera"] for r in out}
prima = {w for w, o in OPERE.items() if o["ha_luogo_preciso"] == "1" and o["tipo_opera"] in ("film", "libro")}
st = {"righe_luoghi": len(out), "luoghi_distinti": len({r["id_luogo"] for r in out}), "opere_con_luogo_prima": len(prima), "opere_con_luogo_dopo": len(wids)}
for tp in ("film", "libro", "serie_tv", "altro"):
    tot = [w for w, o in OPERE.items() if o["tipo_opera"] == tp]
    st[tp] = dict(tot=len(tot), prima=len([w for w in tot if w in prima]), dopo=len([w for w in tot if w in wids]),
                  con_articolo_wiki=len([w for w in tot if OPERE[w]["itwiki"] or OPERE[w]["enwiki"]]))
dec = collections.defaultdict(lambda: collections.Counter())
for w, o in OPERE.items():
    if o["tipo_opera"] not in ("film", "libro"): continue
    d = o["decennio"] or "senza data"
    dec[o["tipo_opera"]][(d, "tot")] += 1
    if w in wids: dec[o["tipo_opera"]][(d, "con_luogo")] += 1
    if w in prima: dec[o["tipo_opera"]][(d, "prima")] += 1
st["per_decennio"] = {tp: {str(d): {"tot": c[(d, "tot")], "prima": c[(d, "prima")], "dopo": c[(d, "con_luogo")]} for d in sorted({k[0] for k in c}, key=str)} for tp, c in dec.items()}
cnt = collections.Counter(); cl_tipo = {}
for r in out:
    cnt[r["id_luogo"]] += 1
top = []
for cid, n in cnt.most_common(30):
    opere = {r["id_opera"] for r in out if r["id_luogo"] == cid}
    top.append(dict(luogo=CL[cid]["nome"], opere=len(opere), film=len([w for w in opere if OPERE[w]["tipo_opera"] == "film"]), libri=len([w for w in opere if OPERE[w]["tipo_opera"] == "libro"])))
st["top_luoghi"] = top
json.dump(st, open(P("pulito", "_statistiche_luoghi.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in st.items() if k not in ("per_decennio", "top_luoghi")}, ensure_ascii=False, indent=1))
print([ (t["luogo"], t["opere"]) for t in top[:20]])
