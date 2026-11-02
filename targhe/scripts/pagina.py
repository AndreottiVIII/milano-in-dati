"""Costruisce i dati della pagina docs/targhe/ (lapidi e targhe di Milano da fonti libere).
Uso: python -I -X utf8 pagina.py <targhe> <milano-in-dati>     (percorsi assoluti)
Legge: statue/pulito (lapidi gia' unite da OSM e Wikidata, soggetto e sesso da Wikidata P21),
       targhe/raw/osm/overpass_targhe.json (OSM, 2/11/2026), targhe/raw/commons/plaques_milan.json (solo metadati),
       citta-15-minuti (confini NIL), donne-nelle-vie e docs/statue/data/pagina.json (confronti).
NON legge raw/pdm (Pietre della Memoria: diritti riservati, non usato).
Scrive: targhe/pulito/ e milano-in-dati/docs/targhe/data/ (tutto sovrascritto: rilanciabile).
Il file docs/targhe/index.html e' scritto a mano e legge pagina.json e targhe_mappa.json."""
import sys, os, re, csv, json, math, shutil, collections, datetime
import shapely
from shapely.geometry import shape, Point
T, P = sys.argv[1:3]
S = os.path.join(P, "statue", "pulito")
OUT = os.path.join(T, "pulito")
DOC = os.path.join(P, "docs", "targhe", "data")
os.makedirs(OUT, exist_ok=True); os.makedirs(DOC, exist_ok=True)

def rd(p):
    with open(p, encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def dist(a, b): return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 78000)
def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]

# ---------------- NIL (punto in poligono)
g = json.load(open(os.path.join(P, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf-8"))
NIL = [(int(f["properties"]["ID_NIL"]), f["properties"]["NIL"], shape(f["geometry"])) for f in g["features"]]
def nil_of(lon, lat):
    pt = Point(lon, lat)
    for i, n, poly in NIL:
        if poly.contains(pt): return i, n
    return None, ""

# ---------------- OSM fresco (2/11/2026)
osm = json.load(open(os.path.join(T, "raw/osm/overpass_targhe.json"), encoding="utf8"))
osm_ts = osm["osm3s"]["timestamp_osm_base"]
osm_by = {}
for e in osm["elements"]:
    t = e["tags"]
    if t.get("memorial") == "plaque" or t.get("memorial:type") == "plaque" or t.get("artwork_type") == "plaque":
        osm_by[e["type"][0] + str(e["id"])] = t
n_osm_targhe = len(osm_by)

# ---------------- base: lapidi del filone statue
opere = rd(os.path.join(S, "opere.csv"))
sogg = rd(os.path.join(S, "soggetti.csv"))
base = [r for r in opere if r["tipo"] == "lapide o targa"]
osm_usati = set()
rows = []
for r in base:
    ids = r["osm_id"].split()
    insc = ""; start = ""
    for i in ids:
        osm_usati.add(i)
        if i in osm_by:
            insc = insc or osm_by[i].get("inscription", "").replace("\n", " ").strip()
            start = start or osm_by[i].get("start_date", "")
    rows.append(dict(nome=r["nome"], soggetto=r["soggetto"], soggetto_qid=r["soggetto_qid"], genere=r["genere soggetto"], gruppo=r["professione"],
                     anno=r["anno posa"], testo=insc, lon=r["lon"], lat=r["lat"], NIL=r["NIL"], id_nil=r["id_nil"], fonte=r["fonte"],
                     osm_id=r["osm_id"], qid=r["qid_opera"], file="", id_statue=r["id"], stipo=r["soggetto_tipo"]))
osm_non_in_base = [i for i in osm_by if i not in osm_usati]   # sono plaque OSM classificate da statue come altro tipo (es. monumento)

# ---------------- Commons: solo metadati, regola stretta
cm = json.load(open(os.path.join(T, "raw/commons/plaques_milan.json"), encoding="utf8"))["file"]
CAT = re.compile(r"Plaque (to|for) |Plaques? (of|to) |Targa commemorativa|Antifascists plaques|ANPI plaques|Here-(lived|died|was-born|worked) plaques|Gedenktafel", re.I)
TIT = re.compile(r"targa|lapide|lastra|plaque|gedenktafel|epigrafe", re.I)
EXC = re.compile(r"Interior|Latin inscr|Duomo")
pts = [(float(r["lat"]), float(r["lon"])) for r in rows if r["lat"]]
cands = []
for k, v in cm.items():
    if not v["lat"]: continue
    cats = " ".join(v["cat_origine"] + v["cats"])
    if not (CAT.search(cats) or CAT.search(k)): continue
    if not TIT.search(k) or EXC.search(cats + k): continue
    p = (v["lat"], v["lon"])
    if any(dist(p, q) <= 30 for q in pts): continue
    i, n = nil_of(v["lon"], v["lat"])
    if i is None: continue
    cands.append((k, v, i, n))
com = []
for k, v, i, n in cands:
    p = (v["lat"], v["lon"])
    if all(dist(p, (c[1]["lat"], c[1]["lon"])) > 30 for c in com): com.append((k, v, i, n))
def nome_commons(k):
    s = re.sub(r"^File:", "", k); s = re.sub(r"\.(jpe?g|png|tiff?)$", "", s, flags=re.I)
    s = re.split(r" - Foto| Foto|\. Foto| - Photo", s)[0]
    s = re.sub(r"^\d{3,4} - ", "", s)
    return s.replace("_", " ").strip()
for k, v, i, n in com:
    rows.append(dict(nome=nome_commons(k), soggetto="", soggetto_qid="", genere="", gruppo="", anno="", testo="", lon=str(v["lon"]), lat=str(v["lat"]), NIL=n, id_nil=str(i),
                     fonte="commons", osm_id="", qid="", file=k, id_statue="", stipo=""))

# ---------------- categorie: regole semplici in ordine, sul nome e sul testo OSM
RULES = [
 ("Resistenza e vittime del nazifascismo", r"partigian|resistenz|nazifasc|nazist|antifasc|deportat|lager|sterminio|concentramento|caduti per la libert|liberazione|fucilat|trucidat|gappist|\bcln\b|martiri|eccidio|rappresaglia|persecuzion"),
 ("Vittime di terrorismo e violenza", r"terroris|attentat|strage|piazza fontana|brigate rosse|assassinat|ucciso|uccis|vittim[ae] del (dovere|terrorismo|lavoro)|mafia|nassiriya|adempimento del dovere"),
 ("Guerre e caduti", r"caduti|guerra|combattent|alpini|reduci|mutilat|bersaglier|soldat|1915"),
]
GR = {"artista": "Arte, musica e letteratura", "scrittore o giornalista": "Arte, musica e letteratura", "scienziato o medico": "Scienza e medicina",
      "politico o giurista": "Politica, diritto e Risorgimento", "patriota o resistente": "Politica, diritto e Risorgimento", "sovrano o nobile": "Politica, diritto e Risorgimento",
      "militare o forze dell'ordine": "Politica, diritto e Risorgimento", "vittima o caduto": "Vittime di terrorismo e violenza",
      "religioso o santo": "Chiese, religione e benefattori", "imprenditore o benefattore": "Chiese, religione e benefattori", "sportivo": "Altri personaggi"}
KW2 = [("Chiese, religione e benefattori", r"chiesa|consacra|basilica|parrocch|vescov|benefattor|restaur|parroco|\bdon\b|santo"),
       ("Eventi e luoghi della storia", r"cinque giornate|insorti|moti |rivolta|sciopero|inaugura|fondat|bombardament|risorgiment|1848|qui sorgeva|colonna infame"),
       ("Arte, musica e letteratura", r"compositor|poeta|scrittor|musicist|pittor|scultor|architett|teatro|artista|cantante|attore|attrice")]
CASA = re.compile(r"qui (nacque|visse|abit|mor[ìi]|dimor|lavor)|casa natale|in questa casa|nacque|visse in questa", re.I)
ALTRO = "Non classificabile (nome o testo non leggibili)"
def classifica(r):
    txt = (r["nome"] + " " + r["testo"] + " " + r["soggetto"]).lower()
    for lab, rx in RULES:
        if re.search(rx, txt): return lab, "parole nel nome o nel testo"
    for gk in (r["gruppo"] or "").split(" | "):
        if gk in GR: return GR[gk], "mestiere in Wikidata"
    for lab, rx in KW2:
        if re.search(rx, txt): return lab, "parole nel nome o nel testo"
    return ALTRO, ""
for i, r in enumerate(rows, 1):
    r["id"] = "T%04d" % i
    r["categoria"], r["categoria_come"] = classifica(r)
    r["casa"] = "1" if CASA.search(r["nome"] + " " + r["testo"]) else ""

# ---------------- scrittura tabella pulita
COLS = ["id", "nome", "categoria", "categoria_come", "soggetto", "soggetto_qid", "genere_soggetto", "gruppo_professione", "anno_posa", "casa", "testo_osm", "lon", "lat", "NIL", "id_nil", "fonte", "osm_id", "qid_wikidata", "file_commons", "id_filone_statue"]
def line(r): return [r["id"], r["nome"], r["categoria"], r["categoria_come"], r["soggetto"], r["soggetto_qid"], r["genere"], r["gruppo"], r["anno"], r["casa"], r["testo"], r["lon"], r["lat"], r["NIL"], r["id_nil"], r["fonte"], r["osm_id"], r["qid"], r["file"], r["id_statue"]]
with open(os.path.join(OUT, "targhe.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(COLS); [w.writerow(line(r)) for r in rows]

# persone (coppie targa-persona) da soggetti.csv del filone statue
idmap = {r["id_statue"]: r for r in rows if r["id_statue"]}
sp = [dict(id_targa=idmap[s["id_opera"]]["id"], targa=s["opera"], qid=s["qid"], persona=s["persona"], genere=s["genere"], nascita=s["nascita"], morte=s["morte"], gruppo_professione=s["gruppo_professione"],
           come_trovato=s["come_trovato"], anno_posa=s["anno_posa"]) for s in sogg if s["id_opera"] in idmap]
with open(os.path.join(OUT, "persone.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sp[0].keys())); w.writeheader(); w.writerows(sp)

# ---------------- numeri
n = len(rows)
fonte = collections.Counter(r["fonte"] for r in rows)
con_coord = sum(1 for r in rows if r["lat"])
out = dict(generato=datetime.date.today().isoformat(), osm_timestamp=osm_ts, n=n, fonte=dict(fonte), con_coord=con_coord,
           osm_targhe=n_osm_targhe, osm_con_nome=sum(1 for t in osm_by.values() if "name" in t), osm_con_testo=sum(1 for t in osm_by.values() if "inscription" in t),
           osm_con_nome_o_testo=sum(1 for t in osm_by.values() if "name" in t or "inscription" in t), osm_non_in_base=len(osm_non_in_base),
           commons_file=len(cm), commons_con_coord=sum(1 for v in cm.values() if v["lat"]), commons_candidate=len(cands), commons_usate=len(com))
st = json.load(open(os.path.join(P, "docs/statue/data/pagina.json"), encoding="utf8"))
ov = st["overlap"]["lapidi_e_targhe"]
out["stima"] = ov
out["quota_vista"] = round(100 * n / ov["stima_grezza_totale"], 1)
# pietre della memoria (solo conteggi pubblici, nessun dato)
out["pdm"] = dict(voci=496, targhe=326, lastre=204, lapidi=121, targa=1, inciampo=101, monumenti=26, cippi=11, stele=9, altro=22, data="2 novembre 2026")
# categorie
cat = collections.Counter(r["categoria"] for r in rows)
out["categorie"] = [[k, int(v)] for k, v in cat.most_common()]
out["categoria_come"] = dict(collections.Counter(r["categoria_come"] for r in rows if r["categoria"] != ALTRO))
out["casa"] = sum(1 for r in rows if r["casa"])
# con testo/nome leggibile
out["con_soggetto"] = sum(1 for r in rows if r["soggetto"])
out["con_nome"] = sum(1 for r in rows if r["nome"])
out["senza_nome"] = sum(1 for r in rows if not r["nome"])
out["con_anno"] = sum(1 for r in rows if r["anno"])
out["anni"] = sorted(int(r["anno"]) for r in rows if r["anno"].isdigit())
dec = collections.Counter(a // 10 * 10 for a in out["anni"])
out["decenni"] = sorted(dec.items())
# persone e donne
u = {}
for s in sp: u.setdefault(s["qid"], s)
noti = [s for s in u.values() if s["genere"] in ("uomo", "donna")]
nd = sum(1 for s in noti if s["genere"] == "donna")
lo, hi = wilson(nd, len(noti))
out["persone"] = dict(uniche=len(u), sesso_noto=len(noti), donne=nd, quota=round(100 * nd / len(noti), 1), lo=lo, hi=hi,
                      donne_elenco=[[s["persona"], s["targa"], s["gruppo_professione"]] for s in u.values() if s["genere"] == "donna"])
G = st["genere"]
out["confronto"] = dict(statue=G[1], vie=G[-1], quota_vie=st["quota_vie"])
# piu' ricordati
cnt = collections.Counter(); info = {}
for s in sp:
    cnt[s["qid"]] += 1; info[s["qid"]] = s
top = sorted(cnt.items(), key=lambda x: (-x[1], info[x[0]]["persona"]))
out["top"] = [[info[q]["persona"], c, info[q]["gruppo_professione"], info[q]["genere"]] for q, c in top[:12]]
out["top_max"] = top[0][1] if top else 0
out["n_persone_con_2"] = sum(1 for q, c in top if c >= 2)
gp = collections.Counter(s["gruppo_professione"] or "non indicato" for s in u.values())
out["professioni"] = [[k, v, sum(1 for s in u.values() if (s["gruppo_professione"] or "non indicato") == k and s["genere"] == "donna")] for k, v in gp.most_common()]
# resistenza
res = [r for r in rows if r["categoria"].startswith("Resistenza")]
out["resistenza"] = dict(n=len(res), elenco=[[r["nome"] or "(senza nome)", r["NIL"], r["fonte"]] for r in res][:40],
                         press_2021=500, press_fonte="https://www.ilfattoquotidiano.it/2021/04/16/25-aprile-a-milano-le-storie-dei-partigiani-arrivano-sullo-smartphone-le-lapidi-dotate-di-qr-code-con-le-bio-da-sergio-a-jenide-chi-sono/6145293/")
# NIL
nl = collections.Counter(r["NIL"] for r in rows if r["NIL"])
out["nil_top"] = [[k, v] for k, v in nl.most_common(10)]
out["nil_con"] = len(nl); out["nil_tot"] = len(NIL)
out["nil_duomo_brera"] = nl.get("DUOMO", 0) + nl.get("BRERA", 0)
with open(os.path.join(OUT, "per_nil.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["id_nil", "NIL", "targhe", "targhe_con_persona", "targhe_resistenza"])
    for i, nm, _ in sorted(NIL, key=lambda x: x[1]):
        rr = [r for r in rows if r["NIL"] == nm]
        w.writerow([i, nm, len(rr), sum(1 for r in rr if r["soggetto"]), sum(1 for r in rr if r["categoria"].startswith("Resistenza"))])
json.dump(out, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ---------------- mappa
mcols = ["id", "nome", "cat", "soggetto", "genere", "anno", "NIL", "fonte", "url"]
cats = [c[0] for c in out["categorie"]]
def url(r):
    if r["osm_id"]:
        i = r["osm_id"].split()[0]; return "https://www.openstreetmap.org/%s/%s" % ({"n": "node", "w": "way", "r": "relation"}[i[0]], i[1:])
    if r["qid"]: return "https://www.wikidata.org/wiki/" + r["qid"]
    if r["file"]: return "https://commons.wikimedia.org/wiki/" + r["file"].replace(" ", "_")
    return ""
pts_out = [[r["id"], r["nome"] or "(senza nome)", cats.index(r["categoria"]), r["soggetto"], r["genere"], int(r["anno"]) if r["anno"].isdigit() else None, r["NIL"], r["fonte"], url(r), float(r["lon"]), float(r["lat"])]
           for r in rows if r["lat"]]
json.dump({"colonne": mcols + ["lon", "lat"], "categorie": cats, "punti": pts_out}, open(os.path.join(DOC, "targhe_mappa.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(out, open(os.path.join(DOC, "pagina.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
for fn in ["targhe.csv", "persone.csv", "per_nil.csv"]: shutil.copy(os.path.join(OUT, fn), os.path.join(DOC, fn))
open(os.path.join(DOC, "LICENZE.txt"), "w", encoding="utf8").write(
"""Milano in dati - Lapidi e targhe: licenze dei file in questa cartella
Dati scaricati il 1 e 2 novembre 2026.

- Dati derivati da OpenStreetMap (nomi, posizioni, testi delle iscrizioni, anni): (c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0.
  Chi riusa o ripubblica questi file deve citare la fonte e distribuire i dati derivati con la stessa licenza (share-alike). https://www.openstreetmap.org/copyright
- Dati ricavati da Wikidata (nomi delle targhe, persone, sesso, mestieri): CC0 (pubblico dominio).
- Wikimedia Commons: solo metadati (titolo del file, coordinate) di 10 foto, con il link alla pagina del file; nessuna immagine copiata. Le singole foto hanno ciascuna la propria licenza (vedi la pagina del file).
- Confini dei NIL e nomi dei quartieri: Comune di Milano, CC BY (dati.comune.milano.it, ds964).
- Il file targhe.csv unisce le fonti: la colonna "fonte" dice da dove viene ogni riga. Trattatelo come ODbL (share-alike) per le righe con OSM.
- Pietre della Memoria (ANMIG) NON e' stata usata: tutti i diritti sono riservati. Ne cito solo il numero di voci.
- I programmi e le note sono nel repository del progetto.
""")
print("targhe", n, dict(fonte), "con coordinate", con_coord, "commons", len(com), "categorie", dict(cat))
print("persone", out["persone"]["uniche"], "donne", nd, "su", len(noti), "resistenza", len(res))
