"""Costruisce il gazetteer dei luoghi di Milano (solo locale, pulito/_gazetteer.csv).
Fonti: civici del Comune (strade), NIL vigenti, OSM via Overpass (raw/osm), elenco a mano di luoghi famosi.
Uso: python -I 21_gazetteer.py <strand> <root milano-in-dati>"""
import sys, os, re, csv, gzip, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_luoghi import norm, tokens, ARTICOLI
from shapely.geometry import shape, Point
base, root = sys.argv[1], sys.argv[2]
cm = os.path.join(root, "citta-15-minuti", "raw", "comune_milano")
conf = shape(json.load(open(os.path.join(cm, "confine_comune", "confine_comune_milano_layer_0_confine_comune_milano.geojson"), encoding="utf8"))["features"][0]["geometry"])
conf_b = conf.buffer(0.002)
G = {}   # chiave -> lista di voci
def add(key, nome, tipo, lat, lon, fonte, prio, wd=""):
    G.setdefault(key, []).append(dict(nome=nome, tipo=tipo, lat=lat, lon=lon, fonte=fonte, prio=prio, wd=wd))

# ---- 1) elenco a mano (priorita 0): nomi alternativi separati da |, poi tipo, lat, lon
HAND = """
Duomo di Milano|Duomo|cattedrale di Milano|Piazza del Duomo|Piazza Duomo|Cattedrale di Milano;monumento;45.4641;9.1919
Galleria Vittorio Emanuele II|Galleria Vittorio Emanuele;monumento;45.4659;9.1900
Castello Sforzesco;monumento;45.4705;9.1795
Teatro alla Scala|Teatro La Scala|la Scala di Milano|Scala di Milano|Teatro della Scala|alla Scala|La Scala|dalla Scala;teatro;45.4674;9.1894
Stazione Centrale|Milano Centrale|Stazione di Milano Centrale|Stazione Milano Centrale|Centrale FS|Stazione Centrale di Milano;stazione;45.4862;9.2043
Pirellone|Grattacielo Pirelli|Palazzo Pirelli|Torre Pirelli;grattacielo;45.4846;9.2020
Torre Velasca;grattacielo;45.4607;9.1925
Stazione Cadorna|Cadorna FNM|Stazione Nord|Milano Cadorna;stazione;45.4678;9.1760
Porta Garibaldi|Stazione di Porta Garibaldi|Stazione Garibaldi|Garibaldi FS|Milano Porta Garibaldi;stazione;45.4840;9.1870
Porta Venezia;zona;45.4747;9.2053
Porta Romana;zona;45.4519;9.2055
Porta Ticinese;zona;45.4516;9.1762
Porta Nuova;zona;45.4852;9.1905
Porta Vittoria;zona;45.4584;9.2150
Porta Genova|Stazione di Porta Genova;stazione;45.4531;9.1706
Porta Magenta;zona;45.4660;9.1693
Porta Volta;zona;45.4806;9.1810
Navigli|Naviglio|zona Navigli;quartiere;45.4510;9.1730
Naviglio Grande;canale;45.4513;9.1720
Naviglio Pavese;canale;45.4470;9.1745
Darsena;canale;45.4519;9.1790
San Siro|Stadio San Siro|Stadio Meazza|Stadio Giuseppe Meazza|ippodromo di San Siro;stadio;45.4781;9.1240
Brera|Pinacoteca di Brera|quartiere Brera;quartiere;45.4720;9.1880
Bovisa;quartiere;45.5030;9.1590
Quarto Oggiaro;quartiere;45.5127;9.1426
Cimitero Monumentale;cimitero;45.4872;9.1763
Cimitero Maggiore|Musocco;cimitero;45.5130;9.1190
Parco Sempione;parco;45.4730;9.1770
Arco della Pace;monumento;45.4756;9.1722
Santa Maria delle Grazie|Cenacolo vinciano|Ultima Cena;chiesa;45.4660;9.1710
Basilica di Sant'Ambrogio|Sant'Ambrogio;chiesa;45.4620;9.1737
Basilica di San Lorenzo|Colonne di San Lorenzo|San Lorenzo Maggiore;monumento;45.4579;9.1829
Basilica di Sant'Eustorgio|Sant'Eustorgio;chiesa;45.4559;9.1814
San Satiro;chiesa;45.4631;9.1873
San Babila|Piazza San Babila;zona;45.4659;9.1966
Quadrilatero della moda|Quadrilatero d'oro|via Montenapoleone|via Monte Napoleone;zona;45.4690;9.1950
Triennale|Palazzo dell'Arte;edificio;45.4721;9.1728
Palazzo di Giustizia;edificio;45.4577;9.2012
San Vittore|carcere di San Vittore;carcere;45.4616;9.1647
Policlinico|Ospedale Maggiore|Ospedale Policlinico;ospedale;45.4590;9.1950
Ospedale Niguarda|Niguarda;ospedale;45.5120;9.1900
Universita Statale|Universita degli Studi di Milano;universita;45.4601;9.1944
Bocconi|Universita Bocconi;universita;45.4478;9.1888
Politecnico|Politecnico di Milano;universita;45.4780;9.2270
Citta Studi;quartiere;45.4783;9.2260
Lambrate|Stazione di Lambrate;quartiere;45.4840;9.2380
Corvetto;quartiere;45.4413;9.2239
Gratosoglio;quartiere;45.4150;9.1790
Rogoredo|Santa Giulia;quartiere;45.4337;9.2390
Bicocca;quartiere;45.5170;9.2100
Hangar Bicocca|HangarBicocca;edificio;45.5200;9.2150
quartiere Isola|zona Isola;quartiere;45.4880;9.1880
Chinatown|Chinatown di Milano;quartiere;45.4821;9.1785
Ortomercato;edificio;45.4400;9.2300
Idroscalo;parco;45.4631;9.2878
Aeroporto di Linate|Linate;aeroporto;45.4451;9.2767
CityLife|Tre Torri;grattacielo;45.4783;9.1559
Bosco Verticale;grattacielo;45.4870;9.1910
Fiera Milano City|Fieramilanocity|Fiera di Milano|Fiera Campionaria;edificio;45.4780;9.1550
Palazzo Marino;edificio;45.4649;9.1888
Palazzo Reale;edificio;45.4630;9.1920
Biblioteca Ambrosiana|Pinacoteca Ambrosiana;edificio;45.4635;9.1858
Palazzo della Ragione;edificio;45.4640;9.1888
Piccolo Teatro|Piccolo Teatro Strehler|Piccolo Teatro di Milano;teatro;45.4710;9.1815
Teatro Dal Verme;teatro;45.4715;9.1822
Teatro Lirico;teatro;45.4613;9.1922
Mudec|MUDEC;edificio;45.4529;9.1627
Fondazione Prada;edificio;45.4453;9.2056
Museo del Novecento|Arengario;edificio;45.4640;9.1912
Museo della Scienza e della Tecnologia|Museo della Scienza;edificio;45.4625;9.1710
Planetario|Planetario Hoepli;edificio;45.4727;9.2000
Giardini di Porta Venezia|Giardini pubblici di Porta Venezia|giardini pubblici Indro Montanelli;parco;45.4731;9.2000
Acquario Civico;edificio;45.4742;9.1739
Galleria d'Arte Moderna|Villa Reale;edificio;45.4734;9.1984
Casa Verdi|Casa di riposo per musicisti;edificio;45.4668;9.1555
Giambellino;quartiere;45.4450;9.1480
Lorenteggio;quartiere;45.4465;9.1430
Barona;quartiere;45.4310;9.1580
Baggio;quartiere;45.4630;9.0990
Affori;quartiere;45.5160;9.1740
Stazione di Greco Pirelli|Greco Pirelli;stazione;45.5000;9.2133
QT8|Quartiere QT8;quartiere;45.4830;9.1350
Monte Stella|Montagnetta di San Siro;parco;45.4875;9.1255
Crescenzago;quartiere;45.5090;9.2440
Gallaratese;quartiere;45.4960;9.1100
Vigentino;quartiere;45.4310;9.1950
Chiaravalle|Abbazia di Chiaravalle;chiesa;45.4230;9.2350
Ticinese;quartiere;45.4535;9.1780
zona Tortona;quartiere;45.4520;9.1640
Piazzale Loreto|Loreto;zona;45.4857;9.2175
Corso Buenos Aires|via Buenos Aires;strada;45.4772;9.2063
Corso Como;strada;45.4846;9.1873
Stazione di Rogoredo;stazione;45.4337;9.2390
Piazza Gae Aulenti|Gae Aulenti;zona;45.4835;9.1900
Torre Unicredit|UniCredit Tower;grattacielo;45.4833;9.1895
Palazzo Lombardia|Grattacielo Lombardia;grattacielo;45.4863;9.1963
Borsa di Milano|Palazzo Mezzanotte|Piazza Affari;edificio;45.4678;9.1832
Cordusio;zona;45.4658;9.1853
San Fedele;chiesa;45.4660;9.1895
San Celso;chiesa;45.4510;9.1865
Conservatorio di Milano|Conservatorio Giuseppe Verdi;edificio;45.4640;9.2000
Teatro Franco Parenti|Teatro Parenti;teatro;45.4545;9.1998
Teatro Carcano;teatro;45.4544;9.1989
Teatro degli Arcimboldi|Arcimboldi;teatro;45.5190;9.2120
Arena Civica|Arena Gianni Brera;stadio;45.4757;9.1788
Velodromo Vigorelli|Vigorelli;stadio;45.4878;9.1470
Scalo Farini;zona;45.4950;9.1720
Cascina Cuccagna;edificio;45.4545;9.2060
Villa Necchi Campiglio;edificio;45.4694;9.2003
Casa degli Omenoni;edificio;45.4670;9.1950
"""
for line in HAND.strip().splitlines():
    nomi, tipo, lat, lon = line.split(";")
    names = nomi.split("|")
    for n in names:
        add(" ".join(tokens(n)), names[0], tipo, float(lat), float(lon), "elenco_a_mano", 0)

# ---- 2) strade dai civici (priorita 1; variante col cognome priorita 2)
TIPI = {"Via","Viale","Piazza","Corso","Piazzale","Galleria","Largo","Alzaia","Ripa","Vicolo","Foro","Bastioni","Piazzetta","Passaggio","Strada","Parco","Giardino"}
rows = list(csv.DictReader(open(os.path.join(cm, "civici", "estratto", "ds634_civici_coordinategeografiche_20261001_final.csv"), encoding="utf8"), delimiter=";"))
st = collections.defaultdict(list)
for r in rows:
    if r["TIPO"] not in TIPI or not r["DESCRITTIVO"].strip(): continue
    try: lat, lon = float(r["LAT_WGS84"]), float(r["LONG_WGS84"])
    except ValueError: continue
    st[(r["TIPO"], r["DESCRITTIVO"].strip(), r["DENOMINAZIONE"].strip())].append((lat, lon))
PICCOLE = {"del","della","dello","dei","degli","delle","di","da","de","dal","dalla","il","la","lo","le","gli","al","alla","sul","sulla","e","ed","in"}
def bello(x):
    out = []
    for i, w in enumerate(x.lower().split()):
        if re.fullmatch(r"[ivxl]+", w): out.append(w.upper()); continue
        if i > 0 and w in PICCOLE: out.append(w); continue
        if "'" in w:
            a, b_ = w.split("'", 1); out.append((a if a in ("d", "dell", "all", "nell", "sull") and i > 0 else a.capitalize()) + "'" + b_.capitalize()); continue
        out.append(w.capitalize())
    return " ".join(out)
def centro(pts):
    la = sorted(p[0] for p in pts)[len(pts)//2]; lo = sorted(p[1] for p in pts)[len(pts)//2]
    return min(pts, key=lambda p: (p[0]-la)**2 + (p[1]-lo)**2)
strade = {}
cogn = collections.defaultdict(set)
for (tipo, descr, denom), pts in st.items():
    lat, lon = centro(pts)
    nome = f"{tipo} {bello('x ' + descr)[2:]}"
    toks = tokens(descr)
    variants = {" ".join(toks)}
    t2 = list(toks)
    while len(t2) > 1 and t2[0] in ARTICOLI: t2 = t2[1:]
    variants.add(" ".join(t2))
    dt = tokens(denom)
    if "(" not in denom and len(dt) >= 2 and sorted(dt) == sorted(toks) and dt != toks:
        for k in range(1, len(dt)):
            if dt[-k:] == toks[:k]:
                cogn[(tipo, " ".join(dt[:-k]))].add((nome, lat, lon)); break
    for v in variants:
        key = (tipo, v)
        if key not in strade or strade[key][0] < len(pts):
            strade[key] = (len(pts), nome, lat, lon)
for (tipo, v), (n, nome, lat, lon) in strade.items():
    add(norm(tipo) + " " + v, nome, "strada", lat, lon, "civici_comune", 1)
for (tipo, v), s in cogn.items():
    if (tipo, v) in strade or len(s) != 1: continue
    nome, lat, lon = list(s)[0]
    add(norm(tipo) + " " + v, nome, "strada", lat, lon, "civici_comune_cognome", 2)

# ---- 3) NIL (priorita 2)
for r in csv.DictReader(open(os.path.join(cm, "nil_vigenti", "ds964_nil_wm_4326.csv"), encoding="utf8"), delimiter=";"):
    lat, lon = float(r["LAT_Y_4326_CENTROID"]), float(r["LONG_X_4326_CENTROID"])
    name = r["NIL"].replace("Q.RE", "-")
    parts = [p.strip(" -") for p in name.split(" - ")]
    for p in parts + [r["NIL"].replace("Q.RE", "").strip(" -")]:
        if p and " ".join(tokens(p)) != "buenos aires": add(" ".join(tokens(p)), bello(p), "quartiere", lat, lon, "NIL", 2)

# ---- 4) OSM (priorita 3)
TIPO_OSM = {"theatre": "teatro", "cinema": "cinema", "university": "universita", "college": "universita", "hospital": "ospedale", "courthouse": "edificio", "prison": "carcere",
            "townhall": "edificio", "library": "edificio", "arts_centre": "edificio", "place_of_worship": "chiesa", "marketplace": "mercato"}
def classifica(t):
    if t.get("railway") in ("station", "halt"): return "stazione"
    a = t.get("amenity")
    if a in TIPO_OSM: return TIPO_OSM[a]
    if t.get("tourism") in ("museum", "attraction", "gallery"): return "edificio"
    if t.get("tourism") == "hotel": return "albergo" if "wikidata" in t else None
    if t.get("leisure") == "stadium": return "stadio"
    if t.get("leisure") in ("park", "garden"): return "parco"
    if t.get("historic") in ("castle", "city_gate", "fort", "manor", "building", "archaeological_site", "monument", "ruins", "tower", "citywalls", "palace", "church", "monastery"): return "monumento"
    if t.get("man_made") == "tower": return "monumento"
    if t.get("building") in ("cathedral", "church", "chapel", "castle", "palace", "train_station", "stadium", "theatre", "hospital", "university"): return "edificio"
    if t.get("place") in ("suburb", "quarter", "neighbourhood"): return "quartiere"
    if "wikidata" in t and t.get("building"): return "edificio"
    return None
cand = []
for el in json.load(open(os.path.join(base, "raw", "osm", "overpass_luoghi_milano.json"), encoding="utf8"))["elements"]:
    t = el.get("tags", {})
    if "name" not in t: continue
    c = classifica(t)
    if not c: continue
    lat = el.get("lat") or el.get("center", {}).get("lat"); lon = el.get("lon") or el.get("center", {}).get("lon")
    if lat is None: continue
    cand.append((t["name"], c, lat, lon, t.get("wikidata", "")))
print("OSM candidati", len(cand), flush=True)
DESC = {"basilica","chiesa","stazione","cattedrale","castello","abbazia","santuario"}
GENERIC = {"universita","studi","citta","parrocchiale","parrocchia","comune","municipio","ospedale","centro","cimitero","museo","istituto","scuola","chiesa","teatro","cinema","hotel","palazzo","villa","parco","giardino","giardini","casa","san","santa","sant","santo","santi","direzionale","stazione","basilica","cattedrale","castello","abbazia","santuario","torre","ponte","via","piazza","nuovo","nuova","grande","maggiore","vecchio","centrale","milano","milan","nord","sud","est","ovest"}
SANTI = {"san","sant","santa","santo","santi","beato","beata"}
BLACK = {"villa san giovanni","museo egizio","giuseppe verdi","ornella vanoni","buenos aires"}
def ok_key(k):
    tk = [t for t in k.split() if t not in ARTICOLI]
    if len(tk) < 2 or k in BLACK: return False
    if not [t for t in tk if t not in GENERIC]: return False
    if tk[0] in SANTI and len(tk) == 2: return False
    return True
for nome, c, lat, lon, wd in cand:
    if not conf_b.contains(Point(lon, lat)): continue
    toks = tokens(nome)
    if not toks: continue
    keys = set()
    if ok_key(" ".join(toks)) or (c == "stazione" and len(toks) >= 2): keys.add(" ".join(toks))
    t2 = list(toks)
    if t2[0] in DESC:
        while t2 and (t2[0] in DESC or t2[0] in ARTICOLI): t2 = t2[1:]
        if ok_key(" ".join(t2)) and t2[0] not in SANTI: keys.add(" ".join(t2))
    else: t2 = []
    if c == "stazione":
        b_ = " ".join(t2 or toks)
        keys |= {"stazione " + b_, "stazione di " + b_, "fermata " + b_, "metro " + b_, "metropolitana " + b_, "stazione di milano " + b_}
    for k in keys:
        add(k, nome, c, lat, lon, "OSM", 3, wd)

# ---- risoluzione: una voce per chiave
out = {}
for k, lst in G.items():
    if not k: continue
    bp = min(x["prio"] for x in lst)
    l2 = [x for x in lst if x["prio"] == bp]
    if len(l2) > 1:
        w = [x for x in l2 if x["wd"]]
        if w: l2 = w[:1]
        else:
            d = max(math.hypot(a["lat"]-b["lat"], a["lon"]-b["lon"]) for a in l2 for b in l2)
            if d > 0.02 and bp >= 2: continue
            l2 = l2[:1]
    out[k] = l2[0]
for k in sorted(k for k, v in out.items() if v["fonte"] == "elenco_a_mano"):
    for o in [x for x in G[k] if x["fonte"] == "OSM"][:1]:
        d = math.hypot(o["lat"]-out[k]["lat"], (o["lon"]-out[k]["lon"])*0.7) * 111
        if d > 0.5: print("DISCREPANZA", k, round(d, 2), "km", out[k]["lat"], out[k]["lon"], "OSM", o["lat"], o["lon"])
os.makedirs(os.path.join(base, "pulito"), exist_ok=True)
with open(os.path.join(base, "pulito", "_gazetteer.csv"), "w", encoding="utf8", newline="") as f:
    w = csv.writer(f); w.writerow(["chiave", "nome", "tipo", "lat", "lon", "fonte", "wikidata"])
    for k in sorted(out):
        v = out[k]; w.writerow([k, v["nome"], v["tipo"], round(v["lat"], 6), round(v["lon"], 6), v["fonte"], v["wd"]])
print("chiavi", len(out), collections.Counter(v["fonte"] for v in out.values()))
