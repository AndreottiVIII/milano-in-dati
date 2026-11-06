# -*- coding: utf-8 -*-
"""Conta i nomi precedenti in OSM (dati gia scaricati da donne-nelle-vie) e li confronta con le 36 vie del Comune (ds2914)."""
import json, re, unicodedata, os
QUI = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(QUI))
def n(s): return re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()).strip()
osm = json.load(open(B + "/donne-nelle-vie/raw/osm/overpass_milano.json", encoding="utf-8"))["elements"]
vecchi = {}
for e in osm:
    t = e.get("tags", {})
    if "old_name" in t: vecchi.setdefault(t["name"], set()).update(x.strip() for x in t["old_name"].split(";"))
print("nomi OSM con old_name:", len(vecchi), "| con un anno nel testo:", sum(1 for v in vecchi.values() if any(re.search(r"1[89]\d\d", x) for x in v)))
print("tipo 'Strada Comunale/Provinciale/Statale':", sum(1 for v in vecchi.values() if all(re.match(r"strada (comunale|provinciale|statale)", x.lower()) for x in v)))
vie = json.load(open(os.path.dirname(QUI) + "/pulito/vie.json", encoding="utf-8"))
print(type(vie), (list(vie[0].keys()) if isinstance(vie, list) else list(vie)[:5]))
nomiosm = {n(k): k for k in vecchi}
tr = 0
for v in (vie if isinstance(vie, list) else vie.get("vie", [])):
    att = v.get("attuale") or v.get("nome_attuale") or ""
    k = n(att)
    if k in nomiosm: tr += 1; print("  in OSM con old_name:", att, "->", vecchi[nomiosm[k]])
print("vie del Comune con old_name in OSM:", tr)
for k in sorted(vecchi)[:0]: pass
json.dump({k: sorted(v) for k, v in vecchi.items()}, open(os.path.dirname(QUI) + "/raw/osm/old_name_estratti.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
