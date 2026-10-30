"""Wikidata (CC0): per le voci 'serata inaugurale della stagione' del Teatro alla Scala scarica le dichiarazioni complete (wbgetentities) e le etichette dei valori.
Cache in raw/aperture_wikidata/. Uso: python -I -X utf8 aperture_wikidata.py <wikidata_raw_p276_event.json> <cartella_out>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
rows = json.load(open(src, encoding="utf8"))["results"]["bindings"]
qs = []
for r in rows:
    inst = r.get("instLabel", {}).get("value", ""); desc = r.get("itemDescription", {}).get("value", "")
    if "inaugurale" in inst or "inaugurale" in desc:
        q = r["item"]["value"].split("/")[-1]
        if q not in qs: qs.append(q)
print(len(qs), "voci")
ents = {}
for i in range(0, len(qs), 40):
    chunk = qs[i:i+40]
    p = os.path.join(out, f"entities_{i//40}.json")
    if not os.path.exists(p):
        r = requests.get("https://www.wikidata.org/w/api.php", headers=UA, timeout=60, params={"action":"wbgetentities","ids":"|".join(chunk),"format":"json","languages":"it|en"})
        r.raise_for_status(); open(p, "w", encoding="utf8").write(r.text); time.sleep(3)
    ents.update(json.load(open(p, encoding="utf8"))["entities"])
# etichette dei valori collegati
vals = set()
for e in ents.values():
    for pid, cl in e.get("claims", {}).items():
        for c in cl:
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v: vals.add(v["id"])
vals = sorted(vals); lab = {}
for i in range(0, len(vals), 50):
    chunk = vals[i:i+50]
    p = os.path.join(out, f"labels_{i//50}.json")
    if not os.path.exists(p):
        r = requests.get("https://www.wikidata.org/w/api.php", headers=UA, timeout=60, params={"action":"wbgetentities","ids":"|".join(chunk),"props":"labels","format":"json","languages":"it|en"})
        r.raise_for_status(); open(p, "w", encoding="utf8").write(r.text); time.sleep(3)
    for k, v in json.load(open(p, encoding="utf8"))["entities"].items():
        l = v.get("labels", {}); lab[k] = (l.get("it") or l.get("en") or {}).get("value", k)
json.dump(lab, open(os.path.join(out, "labels_all.json"), "w", encoding="utf8"), ensure_ascii=False)
print("etichette", len(lab))
