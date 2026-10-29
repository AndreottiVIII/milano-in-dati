import sys, json, csv
base = sys.argv[1]; docs = sys.argv[2]
rows = json.load(open(base + "/pulito/eventi.json", encoding="utf-8"))
# correzioni del coordinatore (pulito/correzioni_coordinatore.csv: id;tipo;motivo), applicate qui e al CSV pubblicato
import os
fixp = base + "/pulito/correzioni_coordinatore.csv"
FIX = {r["id"]: r["tipo"] for r in csv.DictReader(open(fixp, encoding="utf-8-sig"), delimiter=";")} if os.path.exists(fixp) else {}
for r in rows:
    if r["id"] in FIX: r["tipo"] = FIX[r["id"]]
out = []
for r in rows:
    out.append(dict(id=r["id"], d=r["data"], dm=r["data_morte"], y=r["anno"], t=r["titolo"], tp=r["tipo"], lat=r["lat"], lon=r["lon"], m=r["morti"], f=r["feriti"], v=r["vittime_nomi"],
        r=r["responsabili_wikipedia"][:220].replace("*", "; ").replace(";  ;", ";").strip(" ;"), riv=r["rivendicazione_citata"] == "sì", con=r["condanne_citate"] == "sì", wp=r["wikipedia_it"], wt=r["wikipedia_titolo"],
        en=r["wikipedia_en"], q=r["wikidata_qid"], vt=r["voce_tipo"], c=r["confidenza"], n=r["nota"], ind=r["indirizzo"], mc=r["metodo_coordinate"], rd=r["wikipedia_rev_data"]))
json.dump(out, open(docs + "/data/eventi.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
src = list(csv.DictReader(open(base + "/pulito/eventi.csv", encoding="utf-8-sig")))
for r in src:
    if r["id"] in FIX: r["tipo"] = FIX[r["id"]]
keep = [c for c in src[0].keys() if c not in ("rivendicazione_snippet", "note_tabella")]
with open(docs + "/data/eventi.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keep, extrasaction="ignore"); w.writeheader(); w.writerows(src)
import shutil; shutil.copy(base + "/pulito/esclusi.csv", docs + "/data/esclusi.csv")
print(len(out))
