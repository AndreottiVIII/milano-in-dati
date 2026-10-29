"""Per le pagine collegate che hanno un QID ma nessuna coordinata su Wikipedia, chiede a Wikidata (P625).
Aggiorna raw/wikitext/_link_coordinate.json.  Uso: python -I 22b_link_wikidata.py <strand>"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wd_lib import sparql
base = sys.argv[1]
fn = os.path.join(base, "raw", "wikitext", "_link_coordinate.json")
res = json.load(open(fn, encoding="utf8"))
qids = sorted({v["qid"] for v in res.values() if v and not v["lat"] and v["qid"]})
print(len(qids), "qid senza coordinate", flush=True)
out = os.path.join(base, "raw", "wikitext", "wd_p625"); os.makedirs(out, exist_ok=True)
coord = {}
for i in range(0, len(qids), 500):
    q = "SELECT ?q ?c WHERE { VALUES ?q { " + " ".join("wd:" + x for x in qids[i:i+500]) + " } ?q wdt:P625 ?c }"
    for b in sparql(f"p625_{i:05d}", q, out) or []:
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["c"]["value"])
        if m: coord[b["q"]["value"].rsplit("/", 1)[1]] = (float(m.group(2)), float(m.group(1)))
n = 0
for v in res.values():
    if v and not v["lat"] and v["qid"] in coord:
        v["lat"], v["lon"] = coord[v["qid"]]; v["da_wikidata"] = 1; n += 1
json.dump(res, open(fn, "w", encoding="utf8"), ensure_ascii=False)
print("coordinate aggiunte da Wikidata:", n)
