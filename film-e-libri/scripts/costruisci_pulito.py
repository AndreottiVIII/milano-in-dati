"""Costruisce pulito/film.csv, serie_tv.csv, libri.csv, altro.csv + pulito/_statistiche.json da raw/. Uso: python -I costruisci_pulito.py <cartella_strand>"""
import sys, os, json, csv, re, glob, time, collections, unicodedata, requests
base = sys.argv[1]
RAW = lambda *a: os.path.join(base, "raw", *a)
OUT = os.path.join(base, "pulito"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
q = lambda u: u.split("/")[-1]
def load(n): return json.load(open(RAW("wikidata", n + ".json"), encoding="utf8"))["results"]["bindings"]
def v(x, k): return x.get(k, {}).get("value")
W = {}  # qid -> record
def rec(qid):
    return W.setdefault(qid, {"qid": qid, "titolo_it": None, "titolo_en": None, "classi": set(), "anno": None, "persone": {}, "generi": set(), "luoghi": {}, "imdb": set(), "itwiki": None, "enwiki": None, "fonti": set(), "cat_itwiki": set()})
# --- Wikidata
for x in load("opere_base"):
    r = rec(q(v(x, "w"))); r["fonti"].add("wikidata")
    r["titolo_base"] = v(x, "wLabel")
for x in load("opere_it_en"):
    r = rec(q(v(x, "w"))); r["titolo_it"] = v(x, "lit") or r["titolo_it"]; r["titolo_en"] = v(x, "len") or r["titolo_en"]
for x in load("opere_classi"): rec(q(v(x, "w")))["classi"].add((q(v(x, "c")), v(x, "cLabel")))
for x in load("opere_anno"):
    d = v(x, "data"); m = re.match(r"(-?\d{4})", d or "")
    if m: rec(q(v(x, "w")))["anno"] = int(m.group(1))
for x in load("opere_persone"): rec(q(v(x, "w")))["persone"][(v(x, "prop"), q(v(x, "p")))] = v(x, "pLabel")
for x in load("opere_genere"): rec(q(v(x, "w")))["generi"].add(v(x, "gLabel"))
for x in load("opere_id_e_link"):
    r = rec(q(v(x, "w")))
    if v(x, "imdb"): r["imdb"].add(v(x, "imdb"))
    for k in ("itwiki", "enwiki"):
        if v(x, k): r[k] = requests.utils.unquote(v(x, k).split("/wiki/")[-1]).replace("_", " ")
for prop in ("p840", "p915"):
    for x in load("luoghi_" + prop):
        r = rec(q(v(x, "w"))); pq = q(v(x, "pl"))
        r["fonti"].add("wd_" + prop.upper())
        L = r["luoghi"].setdefault((prop.upper(), pq), {"nome": v(x, "plLabel"), "coord": v(x, "coord"), "classi": set()})
        if v(x, "plInstLabel"): L["classi"].add(v(x, "plInstLabel"))
n_wd = len(W)
# --- Wikipedia categorie
pq_ = json.load(open(RAW("wikipedia", "pagine_qid.json"), encoding="utf8"))["pagine"]
miss = json.load(open(RAW("wikipedia", "mancanti_wikidata.json"), encoding="utf8"))
need = set()
for e in miss.values():
    for k in ("P31", "P57", "P50", "P136", "P840", "P915"): need.update(e[k])
lab_p = RAW("wikidata", "etichette_extra.json")
if not os.path.exists(lab_p):
    need = sorted(need); lab = {}
    for i in range(0, len(need), 50):
        time.sleep(1.5)
        r = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": "|".join(need[i:i+50]), "props": "labels", "languages": "it|en", "format": "json"}, headers=UA, timeout=90).json()
        for k, e in r["entities"].items(): lab[k] = (e.get("labels", {}).get("it") or e.get("labels", {}).get("en") or {}).get("value")
    json.dump(lab, open(lab_p, "w", encoding="utf8"), ensure_ascii=False)
lab = json.load(open(lab_p, encoding="utf8"))
for t, p in pq_.items():
    qid = p["qid"]
    if not qid: continue
    r = rec(qid); r["fonti"].add("itwiki_categoria"); r["cat_itwiki"].update(p["categorie"])
    r["itwiki"] = r["itwiki"] or t
    if qid in miss:
        e = miss[qid]
        r["titolo_it"] = r["titolo_it"] or e["it"]; r["titolo_en"] = r["titolo_en"] or e["en"]
        for c in e["P31"]: r["classi"].add((c, lab.get(c)))
        if e["P577"] and not r["anno"]:
            m = re.match(r"\+?(-?\d{4})", e["P577"][0]); r["anno"] = int(m.group(1)) if m else None
        for c in e["P57"]: r["persone"][("regia", c)] = lab.get(c)
        for c in e["P50"]: r["persone"][("autore", c)] = lab.get(c)
        for c in e["P136"]: r["generi"].add(lab.get(c))
        for c in e["P345"]: r["imdb"].add(c)
        r["enwiki"] = r["enwiki"] or e["enwiki"]
        r["altri_luoghi_wd"] = sorted({(lab.get(c) or c) for c in e["P840"] + e["P915"]})
# --- Classificazione
FILM = {"Q11424", "Q20650540", "Q506240"}
SERIE = {"Q5398426", "Q1259759", "Q15416", "Q116048824"}
LIB = {"Q7725634", "Q47461344", "Q386724", "Q277759", "Q24723", "Q571", "Q8261", "Q25379"}
def kind(r):
    c = {a for a, _ in r["classi"]}
    if c & FILM: return "film"
    if c & SERIE: return "serie_tv"
    if c & LIB: return "libro"
    cats = " ".join(r["cat_itwiki"])
    if not c:
        if "Romanzi" in cats: return "libro"
        if "Film" in cats: return "film"
        if "Serie televisive" in cats: return "serie_tv"
    return "altro"
def decade(a): return (a // 10 * 10) if a else ""
def row(r):
    pers = lambda t: "; ".join(sorted({n for (k, _), n in r["persone"].items() if k == t and n}))
    pl = [(p, qq, L) for (p, qq), L in r["luoghi"].items()]
    spec = [(p, qq, L) for p, qq, L in pl if qq != "Q490"]
    spec_c = [(p, qq, L) for p, qq, L in spec if L["coord"]]
    first = spec_c[0] if spec_c else None
    coord = ""
    if first:
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", first[2]["coord"] or "")
        if m: coord = f"{m.group(2)},{m.group(1)}"  # lat,lon
    return {
        "qid": r["qid"], "titolo_it": r["titolo_it"] or r.get("titolo_base") or "", "titolo_en": r["titolo_en"] or "", "anno": r["anno"] or "", "decennio": decade(r["anno"]),
        "tipo_wikidata": "; ".join(sorted(n or a for a, n in r["classi"])), "regia": pers("regia"), "autore": pers("autore"), "genere": "; ".join(sorted(g for g in r["generi"] if g)),
        "luogo_P840_milano": "; ".join(sorted(L["nome"] or qq for p, qq, L in pl if p == "P840")),
        "luogo_P915_milano": "; ".join(sorted(L["nome"] or qq for p, qq, L in pl if p == "P915")),
        "luogo_preciso": "; ".join(sorted(L["nome"] or qq for p, qq, L in spec)), "classe_luogo_preciso": "; ".join(sorted({c for p, qq, L in spec for c in L["classi"]})),
        "ha_luogo_preciso": int(bool(spec)), "ha_luogo_preciso_con_coordinate": int(bool(spec_c)), "lat_lon_primo_luogo_preciso": coord,
        "altri_luoghi_wikidata": "; ".join(r.get("altri_luoghi_wd", [])),
        "itwiki": r["itwiki"] or "", "enwiki": r["enwiki"] or "", "imdb_id": "; ".join(sorted(r["imdb"])),
        "fonte_wikidata_P840": int(any(p == "P840" for p, _ in r["luoghi"])), "fonte_wikidata_P915": int(any(p == "P915" for p, _ in r["luoghi"])),
        "fonte_itwiki_categoria": "; ".join(sorted(r["cat_itwiki"])), "fonte_openlibrary": 0, "fonte_loc": 0, "fonte_sbn": 0, "ol_key": "",
    }
rows = {"film": [], "serie_tv": [], "libro": [], "altro": []}
for r in W.values(): rows[kind(r)].append(row(r))
# --- Open Library -> libri
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
docs = {}; src_ol = collections.defaultdict(set)
for f in glob.glob(RAW("openlibrary", "*.json")):
    nm = os.path.basename(f)[:-5]
    for d in json.load(open(f, encoding="utf8"))["docs"]: docs[d["key"]] = d; src_ol[d["key"]].add(nm)
FIC = re.compile(r"fiction|narrativ|romanz|novel|racconti|short stories|gialli|detective|mystery", re.I)
ol_fic = {k: d for k, d in docs.items() if any(FIC.search(s) for s in d.get("subject", []))}
idx = collections.defaultdict(list)
for rw in rows["libro"]:
    for t in (rw["titolo_it"], rw["titolo_en"]):
        if t: idx[norm(t)].append(rw)
ol_match = 0; ol_new = []
for k, d in ol_fic.items():
    t = norm(d["title"]); hit = None
    for rw in idx.get(t, []):
        a = norm(rw["autore"]); au = [norm(x) for x in d.get("author_name", [])]
        if not a or any(x.split()[-1:] and x.split()[-1] in a for x in au if x): hit = rw; break
    if hit: hit["fonte_openlibrary"] = 1; hit["ol_key"] = k; ol_match += 1
    else: ol_new.append((k, d))
for k, d in ol_new:
    rows["libro"].append({"qid": "", "titolo_it": d["title"], "titolo_en": "", "anno": d.get("first_publish_year", ""), "decennio": decade(d.get("first_publish_year")), "tipo_wikidata": "", "regia": "", "autore": "; ".join(d.get("author_name", [])), "genere": "", "luogo_P840_milano": "", "luogo_P915_milano": "", "luogo_preciso": "", "classe_luogo_preciso": "", "ha_luogo_preciso": 0, "ha_luogo_preciso_con_coordinate": 0, "lat_lon_primo_luogo_preciso": "", "altri_luoghi_wikidata": "", "itwiki": "", "enwiki": "", "imdb_id": "", "fonte_wikidata_P840": 0, "fonte_wikidata_P915": 0, "fonte_itwiki_categoria": "", "fonte_openlibrary": 1, "fonte_loc": 0, "fonte_sbn": 0, "ol_key": k})
# --- LoC (SRU, dc) -> libri
import xml.etree.ElementTree as ET
DC = "{http://purl.org/dc/elements/1.1/}"
loc_n = 0; loc_match = 0
for f in sorted(glob.glob(RAW("loc", "fiction_*.xml"))):
    root = ET.parse(f).getroot()
    for dcn in root.iter("{info:srw/schema/1/dc-schema}dc"):
        g = lambda t: [e.text or "" for e in dcn.findall(DC + t)]
        title = (g("title") or [""])[0]; au = (g("creator") or [""])[0]; dt = (g("date") or [""])[0]
        ym = re.search(r"\d{4}", dt); yr = int(ym.group()) if ym else ""
        loc_n += 1
        key3 = " ".join(norm(title).split()[:3]); sur = norm(au.split(",")[0])
        hit = None
        for rw in rows["libro"]:
            if sur and sur in norm(rw["autore"]) and key3 and (" ".join(norm(rw["titolo_it"]).split()[:3]) == key3 or " ".join(norm(rw["titolo_en"]).split()[:3]) == key3): hit = rw; break
        if hit: hit["fonte_loc"] = 1; loc_match += 1
        else:
            rows["libro"].append({"qid": "", "titolo_it": "", "titolo_en": title.rstrip(" /;:."), "anno": yr, "decennio": decade(yr), "tipo_wikidata": "", "regia": "", "autore": au, "genere": "", "luogo_P840_milano": "", "luogo_P915_milano": "", "luogo_preciso": "", "classe_luogo_preciso": "", "ha_luogo_preciso": 0, "ha_luogo_preciso_con_coordinate": 0, "lat_lon_primo_luogo_preciso": "", "altri_luoghi_wikidata": "", "itwiki": "", "enwiki": "", "imdb_id": "", "fonte_wikidata_P840": 0, "fonte_wikidata_P915": 0, "fonte_itwiki_categoria": "", "fonte_openlibrary": 0, "fonte_loc": 1, "fonte_sbn": 0, "ol_key": ""})
# tutti i record OL (anche non narrativa) in file a parte
with open(os.path.join(OUT, "openlibrary_tutti.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["ol_key", "titolo", "autori", "anno_prima_pubblicazione", "lingue", "narrativa_probabile", "interrogazioni", "soggetti_con_milan"])
    for k, d in sorted(docs.items()):
        w.writerow([k, d["title"], "; ".join(d.get("author_name", [])), d.get("first_publish_year", ""), "; ".join(d.get("language", [])), int(k in ol_fic), "; ".join(sorted(src_ol[k])), "; ".join(s for s in d.get("subject", []) + d.get("place", []) if re.search("milan", s, re.I))[:300]])
names = {"film": "film.csv", "serie_tv": "serie_tv.csv", "libro": "libri.csv", "altro": "altro.csv"}
for kk, fn in names.items():
    rs = sorted(rows[kk], key=lambda r: (r["anno"] if r["anno"] != "" else 9999, r["titolo_it"]))
    with open(os.path.join(OUT, fn), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0].keys()) if rs else ["qid"]); w.writeheader(); w.writerows(rs)
# --- statistiche
st = {"wd_totale_opere": n_wd, "righe": {k: len(v) for k, v in rows.items()}, "ol_narrativa": len(ol_fic), "ol_tutti": len(docs), "ol_agganciati_a_wd_o_wiki": ol_match, "ol_nuovi": len(ol_new), "loc_fiction": loc_n, "loc_agganciati": loc_match}
for kk in rows:
    rs = rows[kk]
    st[kk] = {"con_anno": sum(1 for r in rs if r["anno"] != ""), "per_decennio": dict(sorted(collections.Counter(r["decennio"] for r in rs if r["decennio"] != "").items())),
              "solo_wikidata": sum(1 for r in rs if (r["fonte_wikidata_P840"] or r["fonte_wikidata_P915"]) and not r["fonte_itwiki_categoria"]),
              "solo_itwiki_categoria": sum(1 for r in rs if r["fonte_itwiki_categoria"] and not (r["fonte_wikidata_P840"] or r["fonte_wikidata_P915"])),
              "wikidata_e_itwiki": sum(1 for r in rs if r["fonte_itwiki_categoria"] and (r["fonte_wikidata_P840"] or r["fonte_wikidata_P915"])),
              "P840": sum(r["fonte_wikidata_P840"] for r in rs), "P915": sum(r["fonte_wikidata_P915"] for r in rs),
              "luogo_preciso": sum(r["ha_luogo_preciso"] for r in rs), "luogo_preciso_coord": sum(r["ha_luogo_preciso_con_coordinate"] for r in rs),
              "con_regia_o_autore": sum(1 for r in rs if r["regia"] or r["autore"]), "con_genere": sum(1 for r in rs if r["genere"]), "con_imdb": sum(1 for r in rs if r["imdb_id"]), "con_itwiki": sum(1 for r in rs if r["itwiki"])}
json.dump(st, open(os.path.join(OUT, "_statistiche.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(st, ensure_ascii=False, indent=1))
