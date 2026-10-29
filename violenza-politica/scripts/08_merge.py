import sys, json, re, csv, statistics, urllib.parse
sys.path.insert(0, sys.argv[1])
import wp, infobox as ib
from eventi_seed import SEEDS, ESCLUSI, CRON_SQ, CRON_PB
base = sys.argv[2]                       # cartella violenza-politica
civici = sys.argv[3]                     # csv civici ds634 (sola lettura)
raw = base + "/raw"; out = base + "/pulito"
W = json.load(open(raw + "/wikipedia/wikitext_eventi.json", encoding="utf-8"))
S1 = {}
for r in json.load(open(raw + "/wikipedia/piombo_righe_tutte.json", encoding="utf-8")):
    S1[r["nome"]] = r
L = json.load(open(raw + "/wikipedia/liste_piombo.json", encoding="utf-8"))

# --- Wikidata
def wd(n): return json.load(open(f"{raw}/wikidata/{n}.json", encoding="utf-8"))["results"]["bindings"]
WD = {}
v = lambda x, k: x.get(k, {}).get("value", "")
for n in ("A_eventi_milano", "B_attentati_italia"):
    for x in wd(n):
        q = v(x, "item").split("/")[-1]
        d = WD.setdefault(q, {"label": v(x, "itemLabel"), "deaths": set(), "inj": set(), "dates": set(), "coord": "", "it": v(x, "itwiki"), "en": v(x, "enwiki")})
        if re.match(r"^[\d.]+$", v(x, "deaths")): d["deaths"].add(int(float(v(x, "deaths"))))
        if re.match(r"^[\d.]+$", v(x, "inj")): d["inj"].add(int(float(v(x, "inj"))))
        if v(x, "date"): d["dates"].add(v(x, "date")[:10])
        if v(x, "coord"): d["coord"] = v(x, "coord")
        if v(x, "enwiki"): d["en"] = v(x, "enwiki")
def pt(s):
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", s or "")
    return (float(m.group(2)), float(m.group(1))) if m else None

# --- geocoder sui civici del Comune (ds634), sola lettura
import pandas as pd
df = pd.read_csv(civici, sep=";", dtype=str, usecols=["NUMEROCOMPLETO", "TIPO", "DENOMINAZIONE", "LONG_WGS84", "LAT_WGS84"])
df["lon"] = df.LONG_WGS84.astype(float); df["lat"] = df.LAT_WGS84.astype(float)
def geocode(tipo, den, civ):
    m = df[(df.TIPO.str.lower() == tipo.lower()) & (df.DENOMINAZIONE.str.upper() == den.upper())]
    if m.empty: return None
    if civ:
        mm = m[m.NUMEROCOMPLETO.str.upper().str.startswith(str(civ).upper())]
        if not mm.empty: return (round(mm.lat.median(), 6), round(mm.lon.median(), 6), "civico (registro civici Comune ds634)")
    return (round(m.lat.median(), 6), round(m.lon.median(), 6), "strada, centro dei civici (registro civici Comune ds634)")

MESI = {m: i + 1 for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}
def snippet(txt, pat, n=170):
    m = re.search(pat, txt, re.I)
    if not m: return ""
    a = txt.rfind(".", 0, m.start()) + 1; b = txt.find(".", m.end())
    s = txt[a:b if b > 0 else None].strip()
    return s[:n]

rows = []; problemi = []
for s in SEEDS:
    r = dict(id=s["k"], data=s["data"], anno=int(s["data"][:4]), titolo=s["titolo"], tipo=s["tipo"], nota=s.get("nota", ""), confidenza=s["conf"], fonte=s["fonte"], data_morte=s.get("data_morte", ""))
    page = s["wp"]; Wp = W.get(page) if page in W else None
    if page in (CRON_SQ, CRON_PB): r["voce_tipo"] = "elenco/cronologia"
    else: r["voce_tipo"] = "voce dedicata" if page and (page.startswith(("Omicidio", "Strage", "Assalto", "Attentato", "Bombe", "Giovedì", "Persone")) ) else ("solo voce en/Wikidata" if not page else "voce biografica")
    r["wikipedia_it"] = "https://it.wikipedia.org/wiki/" + urllib.parse.quote(page.replace(" ", "_"), safe="_(),'!:") if page else ""
    r["wikipedia_titolo"] = page or ""
    r["wikipedia_rev"] = ""; r["wikipedia_rev_data"] = ""
    qid = s.get("qid", "")
    if Wp:
        qid = Wp.get("qid") or ""; r["wikipedia_rev"] = Wp["revid"]; r["wikipedia_rev_data"] = Wp["ts"][:10]
    elif page in L:
        r["wikipedia_rev"] = L[page]["revid"]; r["wikipedia_rev_data"] = L[page]["ts"][:10]
    r["wikidata_qid"] = qid
    r["wikipedia_en"] = s.get("en", "")
    d = WD.get(qid)
    if d and d["en"] and not r["wikipedia_en"]: r["wikipedia_en"] = d["en"]
    # responsabili / vittime
    s1 = S1.get(s.get("s1", "")) if s.get("s1") else None
    ibx = ib.infobox(Wp["text"]) if Wp else {}
    resp = s.get("resp")
    if not resp:
        resp = (s1 or {}).get("responsabili") or ibx.get("responsabili") or ibx.get("esecutori") or ""
    r["responsabili_wikipedia"] = resp[:300]
    r["vittime_nomi"] = s.get("vittime") or (s1 or {}).get("vittime", "")
    r["note_tabella"] = (s1 or {}).get("note", "")[:250]
    # rivendicazione / condanne (rilevate nel testo di Wikipedia, senza giudizio nostro)
    txt = ib.strip(Wp["text"]) if (Wp and page not in (CRON_SQ, CRON_PB)) else ""
    txt = txt + " " + r["note_tabella"]
    r["rivendicazione_citata"] = "sì" if re.search(r"rivendic", txt, re.I) else "no"
    r["condanne_citate"] = "sì" if re.search(r"condannat|condanna|ergastol", txt, re.I) else "no"
    r["rivendicazione_snippet"] = snippet(txt, r"rivendic") if r["rivendicazione_citata"] == "sì" else ""
    r["tipo_attribuzione"] = "; ".join(x for x in [("rivendicato" if r["rivendicazione_citata"] == "sì" else ""), ("condannati" if r["condanne_citate"] == "sì" else ""), ("attribuito a" if r["responsabili_wikipedia"] and r["responsabili_wikipedia"].lower() not in ("ignoti", "non indicati") else "ignoti/non indicati")] if x)
    r["morti"] = s.get("morti"); r["feriti"] = s.get("feriti")
    # coordinate
    lat = lon = None; met = ""
    if s.get("coords"): lat, lon = s["coords"]; met = "Wikidata/Wikipedia (coordinate della questura)"
    elif d and pt(d["coord"]): lat, lon = pt(d["coord"]); met = "Wikidata P625"
    elif Wp and Wp["coords"]: lat, lon = Wp["coords"][0]["lat"], Wp["coords"][0]["lon"]; met = "Wikipedia (coordinate della voce)"
    elif s.get("wp_coord_of"):
        c = wp.api(action="query", titles=s["wp_coord_of"], prop="coordinates")["query"]["pages"][0].get("coordinates")
        if c: lat, lon = c[0]["lat"], c[0]["lon"]; met = "Wikipedia (coordinate di " + s["wp_coord_of"] + ")"
    if lat is None and s.get("addr"):
        g = geocode(*s["addr"])
        if g: lat, lon, met = g
        else: problemi.append(f"Geocodifica fallita per {s['k']} {s['addr']}")
    r["lat"] = lat; r["lon"] = lon; r["metodo_coordinate"] = met if lat else "mancanti"
    r["indirizzo"] = (" ".join(x for x in s["addr"] if x) if s.get("addr") else "")
    if lat is not None and not (45.38 <= lat <= 45.54 and 9.04 <= lon <= 9.28):
        problemi.append(f"Coordinate fuori dal Comune per {s['k']}: {lat},{lon}")
    # confronto Wikidata / dati nostri
    if d:
        if d["deaths"] and r["morti"] is not None and r["morti"] not in d["deaths"]:
            problemi.append(f"Morti: {s['k']} Wikipedia/tabella={r['morti']} Wikidata={sorted(d['deaths'])} ({qid})")
        if d["dates"] and s["data"] not in d["dates"]:
            problemi.append(f"Data: {s['k']} nostra={s['data']} Wikidata={sorted(d['dates'])} ({qid})")
        if d["inj"] and r["feriti"] is not None and r["feriti"] not in d["inj"]:
            problemi.append(f"Feriti: {s['k']} nostro={r['feriti']} Wikidata={sorted(d['inj'])} ({qid})")
    if s.get("problema"): problemi.append(f"{s['k']}: {s['problema']}")
    rows.append(r)

rows.sort(key=lambda r: r["data"])
cols = ["id", "data", "data_morte", "anno", "titolo", "tipo", "indirizzo", "lat", "lon", "metodo_coordinate", "morti", "feriti", "vittime_nomi", "responsabili_wikipedia", "tipo_attribuzione", "rivendicazione_citata", "condanne_citate", "rivendicazione_snippet", "note_tabella", "wikipedia_it", "wikipedia_en", "wikipedia_titolo", "voce_tipo", "wikidata_qid", "wikipedia_rev", "wikipedia_rev_data", "fonte", "confidenza", "nota"]
with open(out + "/eventi.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
with open(out + "/esclusi.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["data", "evento", "motivo_esclusione", "fonte"]); w.writerows(ESCLUSI)
json.dump(rows, open(out + "/eventi.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(out + "/problemi_auto.txt", "w", encoding="utf-8").write("\n".join(problemi))
print(len(rows), "eventi;", sum(1 for r in rows if r["lat"] is None), "senza coordinate")
print("\n".join(problemi))
