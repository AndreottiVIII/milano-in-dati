"""Estrae da un ritaglio OSM (osm.gz, ODbL) i nodi/vie con tag di antenne/tralicci di comunicazione.
Uso: python -I -X utf8 osm_antenne.py <osm.gz assoluto> <out_csv assoluto>"""
import sys, gzip, csv
import xml.etree.ElementTree as ET
src, out = sys.argv[1], sys.argv[2]
rows = []
def keep(t):
    return (t.get("man_made") in ("mast", "tower", "antenna", "communications_tower") or t.get("tower:type") == "communication"
            or any(k.startswith("communication:") for k in t) or t.get("telecom") in ("antenna",) or t.get("man_made") == "monitoring_station" and False)
n = 0
for ev, el in ET.iterparse(gzip.open(src), events=("end",)):
    if el.tag in ("node", "way"):
        t = {c.get("k"): c.get("v") for c in el.findall("tag")}
        if t and keep(t):
            rows.append({"tipo": el.tag, "id": el.get("id"), "lat": el.get("lat"), "lon": el.get("lon"), "man_made": t.get("man_made", ""), "tower_type": t.get("tower:type", ""),
                         "operator": t.get("operator", ""), "name": t.get("name", ""), "tags_comm": ";".join(f"{k}={v}" for k, v in t.items() if k.startswith("communication:") or k in ("height", "start_date", "5g", "frequency"))})
        el.clear()
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["tipo"], delimiter=";"); w.writeheader(); w.writerows(rows)
print(len(rows))
