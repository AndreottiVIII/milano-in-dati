"""Unisce: elenco spazioCinema (storico) + geocodifica Nominatim + Wikidata + OSM -> pulito/cinema.csv"""
import sys, csv, json, re, unicodedata, math
base = sys.argv[1]
def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\b(via|viale|piazza|piazzale|corso|largo|galleria|milano|n)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s); return re.sub(r"\s+", " ", s).strip()
def addrkey(a):
    a = a.split(",")[0].split(" / ")[0]
    m = re.match(r"(.*?)(\d+)", a)
    return (norm(m.group(1)), m.group(2)) if m else (norm(a), "")
def pulisci(a):
    a = a.split(" / ")[0]; a = re.sub(r",? poi \d+.*", "", a); a = re.sub(r"^(.*?)\s*-\s*largo.*", r"\1", a)
    a = re.sub(r"/\s*v\..*", "", a); a = re.sub(r"\b(\d+)/(\d+)\b", r"\1", a); a = re.sub(r"(\d+)[a-z]\b", r"\1", a); return a.strip()
elenco = list(csv.DictReader(open(f"{base}/pulito/elenco_spaziocinema_parsed.csv", encoding="utf-8")))
geo = json.load(open(f"{base}/raw/storiche/geocode_nominatim.json", encoding="utf-8"))
# Wikidata
wd = {}
for b in json.load(open(f"{base}/raw/wikidata/a_cinema_inMilano_P131.json", encoding="utf-8"))["results"]["bindings"]:
    q = b["item"]["value"].split("/")[-1]
    g = lambda k: b.get(k, {}).get("value", "")
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", g("coord"))
    street = g("streetLabel"); addr = g("address") or (street + " " + g("hn")).strip()
    e = wd.setdefault(q, {"qid": q, "label": g("itemLabel"), "addr": addr, "lon": float(m.group(1)) if m else None, "lat": float(m.group(2)) if m else None, "inception": g("inception")[:4], "dissolved": g("dissolved")[:4], "wp": g("article")})
# OSM
osm = []
for e in json.load(open(f"{base}/raw/osm/cinema_attuali_e_storici.json", encoding="utf-8"))["elements"]:
    t = e["tags"]
    if not (t.get("amenity") == "cinema" or "disused:amenity" in t): continue
    lat = e.get("lat") or e.get("center", {}).get("lat"); lon = e.get("lon") or e.get("center", {}).get("lon")
    osm.append({"id": f'{e["type"][0]}{e["id"]}', "name": t.get("name", ""), "lat": lat, "lon": lon, "screens": t.get("screen", ""), "stato": "attivo" if t.get("amenity") == "cinema" else "disused",
                "addr": (t.get("addr:street", "") + " " + t.get("addr:housenumber", "")).strip(), "start": t.get("start_date", "")})
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2; return 12742000 * math.asin(math.sqrt(x))
wd_by_addr = {}
for w in wd.values(): wd_by_addr.setdefault(addrkey(w["addr"]), []).append(w)
out = []; used_wd = set(); used_osm = set()
for r in elenco:
    nomi = [n.strip() for n in re.split(r"\s+-\s+", r["nomi_tutti"]) if n.strip()]
    nome = nomi[0]
    q = pulisci(r["indirizzo_elenco"]); gg = geo.get(q)
    lat = lon = ""; prec = "nessuna"; fonte_geo = ""
    k = addrkey(r["indirizzo_elenco"]); w = None
    cand = [x for x in wd_by_addr.get(k, []) if x["lat"]]
    if cand: w = cand[0]
    if w:
        lat, lon, prec, fonte_geo = w["lat"], w["lon"], "civico_wikidata", "wikidata:" + w["qid"]; used_wd.update(x["qid"] for x in cand)
    elif gg:
        lat, lon = float(gg["lat"]), float(gg["lon"]); hn = gg.get("address", {}).get("house_number")
        prec = "civico_geocodifica" if hn else "via_o_zona"; fonte_geo = "nominatim"
    attivo_osm = ""; screens = ""; osm_id = ""
    if lat != "":
        for o in osm:
            if o["lat"] and hav(float(lat), float(lon), o["lat"], o["lon"]) < 60 and set(norm(o["name"]).split()) & set(norm(" ".join(nomi)).split()) - {"cinema", "multisala", "teatro", "spazio"}:
                osm_id = o["id"]; screens = o["screens"]; attivo_osm = o["stato"]; used_osm.add(o["id"]); break
    out.append({"id": r["id_elenco"], "nome": nome, "altri_nomi": " | ".join(nomi[1:]), "indirizzo": r["indirizzo_elenco"], "lat": lat, "lon": lon, "precisione_posizione": prec, "fonte_posizione": fonte_geo,
        "anno_apertura": r["anno_apertura"], "anno_chiusura": r["anno_chiusura"], "apertura_incerta": r["apertura_incerta"], "chiusura_incerta": r["chiusura_incerta"],
        "periodi_attivita": r["intervalli"], "periodo_testo_originale": r["periodo_testo"], "n_sale": screens, "stato_2026": "chiuso (elenco 2017)" if not attivo_osm else ("ancora in OSM come " + attivo_osm),
        "wikidata": w["qid"] if w else "", "osm_id": osm_id, "cosa_c_ora": "", "fonti": "spaziocinema_elenco_2017" + ("; wikidata" if w else "") + ("; osm" if osm_id else "")})
# secondo passaggio: Wikidata residui agganciati alle righe dell'elenco per via+nome o per distanza (<90 m)
STOP = {"cinema", "multisala", "teatro", "spazio", "cineteatro", "sala"}
def toks(s): return set(norm(s).split()) - STOP
for q, w in wd.items():
    if q in used_wd or not w["lat"]: continue
    best = None
    for x in out:
        if not x["id"].startswith("SC") or x["wikidata"] or x["lat"] == "": continue
        d = hav(float(x["lat"]), float(x["lon"]), w["lat"], w["lon"])
        nm = toks(x["nome"] + " " + x["altri_nomi"]) & toks(w["label"])
        same_street = addrkey(x["indirizzo"])[0] == addrkey(w["addr"])[0] and addrkey(w["addr"])[0] != ""
        if (nm and d < 1500) or (same_street and d < 150) or d < 40:
            if best is None or d < best[0]: best = (d, x, bool(nm))
    if best:
        x = best[1]; x["wikidata"] = q; x["fonti"] += "; wikidata"; used_wd.add(q)
        if x["precisione_posizione"] != "civico_wikidata": x["lat"], x["lon"], x["precisione_posizione"], x["fonte_posizione"] = w["lat"], w["lon"], "civico_wikidata", "wikidata:" + q
        if w["inception"] and not x["anno_apertura"]: x["anno_apertura"] = w["inception"]
# Wikidata duplicati di cinema attivi in OSM
# Cinema attivi OSM non presenti nell'elenco storico (aperti oggi)
for o in osm:
    if o["id"] in used_osm or o["stato"] != "attivo": continue
    out.append({"id": "OSM_" + o["id"], "nome": o["name"], "altri_nomi": "", "indirizzo": o["addr"], "lat": o["lat"], "lon": o["lon"], "precisione_posizione": "punto_osm", "fonte_posizione": "osm",
        "anno_apertura": o["start"][:4], "anno_chiusura": "", "apertura_incerta": "", "chiusura_incerta": "", "periodi_attivita": "", "periodo_testo_originale": "", "n_sale": o["screens"],
        "stato_2026": "attivo (OSM 2026-10-29)", "wikidata": "", "osm_id": o["id"], "cosa_c_ora": "ancora cinema", "fonti": "osm"})
# abbinamenti verificati a mano (stesso indirizzo/nome, stringhe diverse)
MAN = {"Q55993497": ("SC", "A.B.C."), "Q107468010": ("SC", "Trieste"), "Q107290225": ("SC", "Astoria"), "Q3982043": ("SC", "Cinema Manzoni"),
       "Q37158536": ("OSM", "n268616425"), "Q37158646": ("OSM", "n268616425"), "Q3982094": ("OSM", "w372493995"), "Q56034869": ("OSM", "w372493995")}
for q, (kind, key) in MAN.items():
    if q in used_wd: continue
    for x in out:
        if (kind == "SC" and x["id"].startswith("SC") and key in x["nome"] + " " + x["altri_nomi"]) or (kind == "OSM" and x["osm_id"] == key):
            x["wikidata"] = (x["wikidata"] + ";" + q).strip(";"); x["fonti"] += "; wikidata"; used_wd.add(q); break
# Wikidata residui che coincidono con cinema attivi in OSM: si attacca il codice Wikidata alla riga OSM
for q, w in wd.items():
    if q in used_wd or not w["lat"]: continue
    for x in out:
        if not x["id"].startswith("OSM_") or x["wikidata"]: continue
        d = hav(float(x["lat"]), float(x["lon"]), w["lat"], w["lon"])
        if (toks(x["nome"]) & toks(w["label"]) and d < 400) or d < 40:
            x["wikidata"] = q; x["fonti"] += "; wikidata"; used_wd.add(q)
            if not x["anno_apertura"] and w["inception"]: x["anno_apertura"] = w["inception"]
            break
# Wikidata non agganciati
for q, w in wd.items():
    if q in used_wd: continue
    out.append({"id": "WD_" + q, "nome": w["label"], "altri_nomi": "", "indirizzo": w["addr"], "lat": w["lat"] or "", "lon": w["lon"] or "", "precisione_posizione": "punto_wikidata", "fonte_posizione": "wikidata",
        "anno_apertura": w["inception"], "anno_chiusura": w["dissolved"], "apertura_incerta": "", "chiusura_incerta": "", "periodi_attivita": "", "periodo_testo_originale": "", "n_sale": "",
        "stato_2026": "da verificare (solo Wikidata)", "wikidata": q, "osm_id": "", "cosa_c_ora": "", "fonti": "wikidata"})
import os
fn_oggi = f"{base}/raw/osm/oggi_vicino.json"
if os.path.exists(fn_oggi):
    oggi = json.load(open(fn_oggi, encoding="utf-8"))
    for x in out:
        v = oggi.get(x["id"])
        if v: x["cosa_c_ora"] = "candidato OSM (<=30 m): " + "; ".join(v[:3])
with open(f"{base}/pulito/cinema.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "righe;", sum(1 for x in out if x["id"].startswith("SC")), "da elenco;", sum(1 for x in out if x["id"].startswith("OSM_")), "solo OSM;", sum(1 for x in out if x["id"].startswith("WD_")), "solo Wikidata")
print("agganciati WD:", sum(1 for x in out if x["wikidata"] and x["id"].startswith("SC")), " OSM:", sum(1 for x in out if x["osm_id"] and x["id"].startswith("SC")))
print("senza posizione:", sum(1 for x in out if x["lat"] == ""))
