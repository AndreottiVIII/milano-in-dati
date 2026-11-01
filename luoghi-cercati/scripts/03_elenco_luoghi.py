"""Passo 3: unisce elementi Wikidata, classi, sitelink e NIL -> pulito/luoghi.csv, pulito/titoli_wikipedia.csv,
pulito/classi_non_riconosciute.csv.
Elementi: (a) P131* = Milano con coordinate (wikidata_items_classi.json); (b) in aggiunta, quelli entro 12 km dal Duomo con
articolo it.wikipedia, senza catena P131 a Milano, ma con coordinate DENTRO i confini degli 88 NIL (+30 m) (wikidata_raggio12km.json).
Si tengono solo quelli con almeno un articolo Wikipedia e le coordinate.
Uso: python -I -X utf8 03_elenco_luoghi.py <luoghi-cercati assoluto> <milano-in-dati assoluto>"""
import sys, os, json, re, csv, collections
from shapely.geometry import shape, Point
from shapely.ops import unary_union

base, mid = sys.argv[1], sys.argv[2]
raw = os.path.join(base, "raw")
out = os.path.join(base, "pulito")


def ld(f):
    return json.load(open(os.path.join(raw, f), encoding="utf8"))


# NIL (poligoni vigenti, EPSG:4326)
g = json.load(open(os.path.join(mid, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf8"))
nil = [(f["properties"]["ID_NIL"], f["properties"]["NIL"], shape(f["geometry"])) for f in g["features"]]
union = unary_union([p for _, _, p in nil])


def nil_di(x, y):
    pt = Point(x, y)
    for i, n, p in nil:
        if p.contains(pt):
            return i, n, "dentro"
    best = min(nil, key=lambda t: t[2].distance(pt))
    d = best[2].distance(pt) * 78000  # gradi -> metri circa a 45,4 N (media tra lon e lat)
    if d <= 150:
        return best[0], best[1], "vicino_%dm" % int(d)
    return None, None, "fuori"


def xy(c):
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", c)
    return float(m[1]), float(m[2])


items = {}


def add(r, via):
    q = r["item"].split("/")[-1]
    d = items.setdefault(q, {"qid": q, "nome_it": "", "nome_en": "", "x": None, "y": None, "classi": {}, "via": via})
    if r.get("itemLabel_it"):
        d["nome_it"] = r["itemLabel_it"]
    if r.get("itemLabel_en"):
        d["nome_en"] = r["itemLabel_en"]
    if r.get("coord") and d["x"] is None:
        d["x"], d["y"] = xy(r["coord"])
    if r.get("cls"):
        d["classi"][r["cls"].split("/")[-1]] = r.get("clsLabel_en") or r.get("clsLabel_it") or ""


for r in ld("wikidata_items_classi.json")["righe"]:
    add(r, "P131")
n_p131 = len(items)
for r in ld("wikidata_raggio12km.json")["righe"]:
    q = r["item"].split("/")[-1]
    if q in items and items[q]["via"] == "P131":
        continue
    x, y = xy(r["coord"])
    if not union.buffer(0.0003).contains(Point(x, y)):
        continue
    add(r, "raggio+poligono")
sup = len(items) - n_p131

EXCL = {"commons", "species", "meta", "wikidata", "mediawiki", "sources", "incubator", "foundation", "outreach",
        "wikimania", "strategy", "nostalgia", "test", "test2", "testwikidata", "wikifunctions"}
SPEC = {"be_x_old": "be-tarask", "zh_yue": "zh-yue", "zh_classical": "zh-classical", "roa_tara": "roa-tara",
        "zh_min_nan": "zh-min-nan", "bat_smg": "bat-smg", "map_bms": "map-bms", "fiu_vro": "fiu-vro",
        "cbk_zam": "cbk-zam", "nds_nl": "nds-nl"}
tit = collections.defaultdict(dict)
for r in ld("wikidata_sitelinks.json")["righe"]:
    k = r["sitekey"]
    if not k.endswith("wiki"):
        continue
    l = k[:-4]
    if l in EXCL:
        continue
    lang = SPEC.get(l, l.replace("_", "-"))
    tit[r["item"]][lang] = r["title"].replace(" ", "_")
for r in ld("wikidata_raggio12km.json")["righe"]:
    q = r["item"].split("/")[-1]
    if q in items and items[q]["via"] != "P131":
        tit[q].setdefault("it", r["title"].replace(" ", "_"))

# categorie: primo match, in ordine di priorita, sulle etichette inglesi delle classi (P31) dell'elemento
CAT = [
    ("stato_storico", r"(historical country|sister republic|vassal state|signoria)"),
    ("stadio_sport", r"(stadium|sports venue|arena|racecourse|velodrome|swimming|sports hall|sports centre|sports complex|racing|football pitch|golf|ice rink|hippodrome|sports facility|gymnasium|football venue|rugby)"),
    ("stazione", r"(station|tram stop|bus stop|stop$|railway|airport|terminal)"),
    ("teatro_cultura", r"(theatre|theater|opera house|concert hall|auditorium|movie theat|cinema|music venue|nightclub|cultural centre|cultural center|exhibition centre|conference)"),
    ("museo", r"(museum|art gallery|exhibition hall)"),
    ("piazza", r"(square|piazza|plaza|courtyard|roundabout)"),
    ("strada", r"(street|road|avenue|boulevard|pedestrian|bridge|footbridge|alley|tunnel|highway|motorway|viaduct|junction|arcade|galleria)"),
    ("chiesa_religioso", r"(church|basilica|cathedral|chapel|oratory|monastery|convent|abbey|cloister|bell tower|synagogue|mosque|baptistery|sanctuary|religious|temple|parish|hermitage|belfry)"),
    ("parco_verde", r"(park|garden|cemetery|botanical|woodland|forest|zoo|fountain|tree)"),
    ("canale_acqua", r"(canal|river|stream|lake|pond|waterway|navigli|lock|basin|conca)"),
    ("quartiere", r"(quarter|neighbo|district|housing estate|municipi|local identity|frazione|locality|suburb|borough|village|hamlet|contrada|zone|ward|city district|urban area|cascina|municipality|sestiere)"),
    ("biblioteca_archivio", r"(librar|archive|biblioteca)"),
    ("istruzione", r"(school|university|kindergarten|college|liceo|istituto|academy|conservatory|institute|faculty|educational|campus)"),
    ("castello_difesa", r"(castle|fortification|fortress|city gate|walls|barracks|citadel|bastion|gate$)"),
    ("monumento_arte", r"(monument|memorial|statue|sculpture|obelisk|column|grave|tomb|cenotaph|mausoleum|artwork|mural|relief|fresco|mosaic|public art|artistic|triumphal arch|arch$)"),
    ("ospedale", r"(hospital|medical facility|clinic|sanatorium|nursing home)"),
    ("edificio_palazzo", r"(palace|palazzo|building|house|villa|skyscraper|tower|architectural|hotel|hospital|real property|residential|multifamily|office|complex|pavilion|farm|factory|industrial|market|shopping|mall|apartment|facility|heritage|structure|palazzina|villino|restaurant|bank|prison|clinic|insurance|headquarters|warehouse|power|plant|site|ruins|archaeolog|historic building|historic house|bar$|caf|depot|garage)"),
    ("non_luogo", r"(organization|business|company|brand|nonprofit|foundation|publisher|firm|coachbuilder|syndicate|association|research institute|religious institute|recurring|rebellion|battle|siege|bombing|historical country|province|circle of|race|exhibition|painting|pipe organ|plaque|event|festival|party|club|label|fashion|newspaper|magazine|film|human|class of|aircraft|ship|train|vehicle|mountain|metropolitan city|comune of italy|functional urban|region of italy|attack|murder|homicide|season|world's fair|championship|accident|enterprise|brick and mortar)"),
]


def categoria(cl):
    labs = [v.lower() for v in cl.values() if v]
    if not labs:
        return "senza_classe"
    for c, rx in CAT:
        for l in labs:
            if re.search(chr(92)+"b"+rx, l):
                return c
    return "altro"


# correzioni a mano (poche, documentate): scripts/categorie_manuali.csv
man = {r["qid"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "categorie_manuali.csv"), encoding="utf8"), delimiter=";")}
TIPO = {"ospedale": "istituzione", "stato_storico": "non_luogo", "istruzione": "istituzione", "biblioteca_archivio": "istituzione", "non_luogo": "non_luogo", "altro": "non_luogo", "senza_classe": "non_luogo"}
rows = []
trows = []
cc = collections.Counter()
unk = collections.Counter()
for q, d in items.items():
    t = tit.get(q, {})
    if not t or d["x"] is None:
        continue
    iid, nname, pos = nil_di(d["x"], d["y"])
    cat = categoria(d["classi"])
    if cat in ("altro", "senza_classe"):
        for k, v in d["classi"].items():
            unk[(k, v)] += 1
    nome = d["nome_it"] or d["nome_en"] or t.get("it") or t.get("en") or q
    tipo = TIPO.get(cat, "luogo")
    if re.match(r"^Municipio \d", nome):
        cat, tipo = "ente_territoriale", "non_luogo"
    if q in man:
        cat, tipo = man[q]["categoria"], man[q]["tipo"]
    rows.append({"qid": q, "nome": nome.replace("_", " "), "nome_en": d["nome_en"], "lon": round(d["x"], 6),
                 "lat": round(d["y"], 6), "categoria": cat, "tipo": tipo,
                 "classi": "|".join("%s:%s" % (k, v) for k, v in d["classi"].items()),
                 "id_nil": iid if iid is not None else "", "nil": nname or "", "nil_posizione": pos,
                 "origine": d["via"], "n_wikipedia": len(t), "titolo_it": t.get("it", "")})
    for lang, title in t.items():
        trows.append({"qid": q, "lingua": lang, "titolo": title})
    cc[cat] += 1
os.makedirs(out, exist_ok=True)


def wcsv(fn, rr):
    with open(os.path.join(out, fn), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rr)


wcsv("luoghi.csv", rows)
wcsv("titoli_wikipedia.csv", trows)
wcsv("classi_non_riconosciute.csv", [{"qid_classe": k, "etichetta": v, "elementi": n} for (k, v), n in unk.most_common()])
print("P131:", n_p131, "aggiunti da raggio+poligono:", sup, "; con articolo e coordinate:", len(rows), "; titoli:", len(trows))
print(cc.most_common())
print("fuori NIL:", sum(1 for r in rows if r["nil_posizione"] == "fuori"))
