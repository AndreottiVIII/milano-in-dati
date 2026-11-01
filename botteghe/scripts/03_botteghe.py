"""Costruisce pulito/botteghe.csv: una riga per attività (entità) con categoria, anni, indirizzo, coordinate, NIL, prove di presenza.
Fonti usate per la presenza oggi: stato "attiva/cessata" dell'Albo comunale 2024 (ds2858), elenco Regione corrente (ds612, 19/10/2026),
OpenStreetMap (estratto Geofabrik 31/10/2026), registri commerciali del Comune 2026 (ds49 vicinato, ds58/59/250 pubblici esercizi e artigianato alimentare).
Uso: python -I -X utf8 03_botteghe.py <botteghe abs> <milano-in-dati abs>"""
import sys, os, csv, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_botteghe import *
import shapely
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
B, P = sys.argv[1:3]
rec = list(csv.DictReader(open(B + "/pulito/entita_record.csv", encoding="utf-8")))
ENT = collections.OrderedDict()
for r in rec:
    ENT.setdefault(r["ent_id"], []).append(r)

# ---------- settore
REG = [
    ("farmacia", r"farmaci"),
    ("ristorante", r"ristorant|trattori|osteri|pizzeri|birreri|ristorazione|tavola calda|locale storico|pub"),
    ("bar_caffe", r"\bbar\b|caff[eè]|caffett|\bcafe\b|torrefa"),
    ("pasticceria_gelateria", r"pasticc|gelateri|confetter|dolci|ciocco|panettone|marron"),
    ("panificio", r"panific|forno|pane\b|panettier"),
    ("alimentari", r"salumer|gastronom|macelle|pescher|droghe|alimentar|frutta|verdur|latteri|formagg|enotec|vini|liquor|pizzicher|norcin|polleri|uova|pastificio|rosticcer"),
    ("gioielleria_orologeria", r"gioiell|orolog|orefice|argenter|bigiotter|preziosi|gemm"),
    ("ottica_foto", r"ottic|\bfoto|fotograf"),
    ("cura_persona", r"parrucch|barbier|estetist|profumer|acconciatur|cosmet|cura della persona"),
    ("tabaccheria", r"tabacc|fumator|pipe"),
    ("fiori_piante", r"fior|piante|vivaio"),
    ("stampa_incisioni", r"tipograf|stampa tipo|tipolitograf|incision|copisteria|eliograf|litograf|legatori|cartotecn"),
    ("servizi_spettacolo", r"agenzia|funebr|onoranze|cambi|pulizi|autorimess|biglietteria|albergo|hotel|teatro|cinema"),
    ("laboratori_produzione", r"bronz|fornace|vetrat|maglific|marmi|lavorazion|produzion|acciai|metall|tele metalliche|impianti|fabbric|officina|manifattura|laborator"),
    ("libreria_cartoleria", r"libreri|libri|cartoler|cartolibr|edicol|penne|timbri|stampe|filateli|giornal|cartotecn|legatori|musica|dischi"),
    ("sartoria_riparazioni", r"sartori|calzolai|riparazion|rammend|arrotin|tintori|lavanderi|su misura|modister"),
    ("calzature_pelletteria", r"calzatur|scarp|pelletter|borse|valig|ombrell"),
    ("abbigliamento", r"chiusure lampo|bottoni|filati|abbigliament|boutique|camic|pellicc|maglieri|intimo|moda\b|cappell|bianchery|biancheria|merceri|tessuti|confezioni|cravatt|guanti|uomo|donna|bambin"),
    ("sport_tempo_libero", r"sport|bicicl|giocattol|strumenti musical|pesca|hobby|armeri|caccia|modellism"),
    ("auto_moto", r"\bauto\b|\bmoto|pneumatic|carrozz|motocicl|veicol|concession"),
    ("salute_benessere", r"ortoped|sanitar|erborist|salute"),
    ("casa_ferramenta", r"tappet|colorific|vernic|vetrer|porcellan|cristall|ferrament|casaling|mobil|arred|elettrodom|cornici|illumin|colteller|vetri|lampad|ceramic|antiquari|galleria d|arte\b|radio tv|idraul|elettric|tappezz|tende|\bcasa\b"),
]


def settore(r):
    # prima il testo libero dell'Albo (genere), la categoria Regione e l'insegna; la denominazione sociale per ultima
    t1 = " ".join([r.get("genere", ""), r.get("cat", ""), r.get("insegna", "")]).lower()
    t2 = r.get("denom", "").lower()
    for t in (t1, t2):
        for nome, rx in REG:
            if re.search(rx, sa(t)):
                return nome
    return "altro"


# ---------- NIL da poligoni
g = json.load(open(P + "/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson", encoding="utf-8"))
polys = [shape(f["geometry"]).buffer(0) for f in g["features"]]
nilp = [(f["properties"]["ID_NIL"], f["properties"]["NIL"]) for f in g["features"]]
tree = STRtree(polys)


def nil_di(lon, lat):
    pt = Point(lon, lat)
    for i in tree.query(pt):
        if polys[i].contains(pt):
            return nilp[i]
    return (None, None)


# ---------- OSM
osm = json.load(open(B + "/raw/osm/osm_milano_poi_con_nome.json", encoding="utf-8"))["elements"]
GEN = {"milano", "milanese", "ristorante", "trattoria", "osteria", "pasticceria", "bar", "caffe", "caffetteria", "gioielleria", "farmacia", "libreria", "cartoleria", "pizzeria", "ottica", "gelateria", "panificio", "macelleria", "salumeria", "boutique", "antica", "storica", "ferramenta", "profumeria", "orologeria", "oreficeria", "calzature", "abbigliamento", "parrucchiere", "sartoria", "tabaccheria", "cartolibreria", "enoteca", "pescheria", "merceria", "fiori", "fiorista", "casalinghi", "antico", "vecchia", "vecchio", "nuova", "nuovo", "dal", "figli", "fratelli", "lli", "storico"}


def tk(s):
    return frozenset(w for w in toks_nome(s) if w not in GEN)


cell = 0.0012
grid = collections.defaultdict(list)
for i, e in enumerate(osm):
    grid[(int(e["lon"] / cell), int(e["lat"] / cell))].append(i)


def osm_vicini(lon, lat, rad):
    cx, cy = int(lon / cell), int(lat / cell)
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in grid.get((cx + dx, cy + dy), ()):
                e = osm[i]
                d = dist_m(lon, lat, e["lon"], e["lat"])
                if d <= rad:
                    out.append((d, i))
    return sorted(out)


def osm_nome_tags(e):
    t = e["tags"]
    return [t.get(k, "") for k in ("name", "brand", "old_name", "alt_name", "official_name", "operator") if t.get(k)]


COMPAT = {
    "farmacia": {"pharmacy", "chemist", "herbalist"},
    "ristorante": {"restaurant", "fast_food", "pub", "bar", "cafe", "food_court", "biergarten", "ice_cream"},
    "bar_caffe": {"bar", "cafe", "pub", "restaurant", "ice_cream", "coffee", "tobacco", "pastry", "fast_food", "confectionery"},
    "pasticceria_gelateria": {"pastry", "confectionery", "chocolate", "bakery", "ice_cream", "coffee", "cafe", "bar", "deli"},
    "panificio": {"bakery", "pastry", "deli", "convenience"},
    "alimentari": {"butcher", "deli", "greengrocer", "convenience", "supermarket", "seafood", "cheese", "wine", "beverages", "alcohol", "pasta", "bakery", "pastry", "restaurant", "bar", "farm", "health_food", "tea", "coffee"},
    "gioielleria_orologeria": {"jewelry", "watches", "jewellery", "antiques"},
    "ottica_foto": {"optician", "photo", "camera", "photo_studio", "photographer", "electronics"},
    "cura_persona": {"hairdresser", "beauty", "perfumery", "cosmetics", "barber", "massage", "chemist"},
    "tabaccheria": {"tobacco", "e-cigarette", "kiosk"},
    "libreria_cartoleria": {"books", "stationery", "newsagent", "copyshop", "art", "gift", "kiosk", "craft", "printing", "second_hand", "music", "musical_instrument", "video"},
    "sartoria_riparazioni": {"tailor", "dry_cleaning", "laundry", "shoe_repair", "clothes", "fabric", "repair", "locksmith", "sewing"},
    "calzature_pelletteria": {"shoes", "bag", "leather", "clothes", "shoe_repair", "fashion_accessories"},
    "abbigliamento": {"clothes", "fabric", "haberdashery", "boutique", "fashion", "fashion_accessories", "lingerie", "tailor", "furs", "bag", "shoes", "textile", "wool"},
    "sport_tempo_libero": {"sports", "bicycle", "toys", "musical_instrument", "fishing", "hobby", "games", "outdoor", "weapons", "music"},
    "auto_moto": {"car", "car_repair", "motorcycle", "tyres", "car_parts", "car_rental", "bicycle", "fuel"},
    "casa_ferramenta": {"hardware", "houseware", "furniture", "kitchen", "appliance", "electronics", "interior_decoration", "frame", "doityourself", "antiques", "lighting", "carpet", "paint", "glaziery", "art", "gift", "curtain", "bed", "locksmith", "tiles", "craft"},
}
def osm_compat(sett, e):
    ok = COMPAT.get(sett)
    if ok is None:
        return True
    t = e["tags"]
    vals = {t.get(k) for k in ("shop", "amenity", "craft", "office", "tourism", "healthcare", "leisure")} - {None}
    return bool(vals & ok) or (sett in ("ristorante", "bar_caffe") and "restaurant" in vals)

def osm_chiuso(e):
    return any(k.startswith(("disused:", "was:", "abandoned:", "razed:")) for k in e["tags"])


# ---------- registri 2026
reg = []
for r in csv.DictReader(open(P + "/citta-15-minuti/raw/comune_milano/vicinato/ds49_commercio_esercizi_vicinato_sede_fissa.csv", encoding="utf-8-sig"), delimiter=";"):
    try:
        reg.append((float(r["LONG_X_4326"]), float(r["LAT_Y_4326"]), r["insegna"].strip(), "ds49:" + r["settore_merceologico"].lower(), r["Codice"]))
    except Exception:
        pass
for r in csv.DictReader(open(P + "/ristoranti/pulito/registro.csv", encoding="utf-8")):
    try:
        reg.append((float(r["lon"]), float(r["lat"]), (r["insegna"] or "").strip(), r["registro"], r["Codice"]))
    except Exception:
        pass
rgrid = collections.defaultdict(list)
for i, x in enumerate(reg):
    rgrid[(int(x[0] / cell), int(x[1] / cell))].append(i)


def reg_vicini(lon, lat, rad):
    cx, cy = int(lon / cell), int(lat / cell)
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in rgrid.get((cx + dx, cy + dy), ()):
                d = dist_m(lon, lat, reg[i][0], reg[i][1])
                if d <= rad:
                    out.append((d, i))
    return sorted(out)


# ---------- cerimonia Botteghe Storiche 11/11/2019 (elenco PDF del Comune, copia Wayback 12/4/2021; solo la colonna "targa")
t19 = []
try:
    righe19 = [l.rstrip() for l in open(B + "/raw/wayback/albo_premiate_2019.txt", encoding="utf-8", errors="replace")]
    col = [l[:34].strip() for l in righe19]
    col = [c for c in col if c and not re.match(r"^(targa|BOTTEGHE|CERIMONIA)", c, re.I) and not re.match(r"^\d", c)]
    for i, c in enumerate(col):
        t19.append(c)
        if i + 1 < len(col): t19.append(c + " " + col[i + 1])
except Exception as ex:
    print("PDF 2019 non letto:", ex)


def num(x):
    try:
        return int(x)
    except Exception:
        return None


GEO = Geocoder(P + "/citta-15-minuti/raw/comune_milano/civici/estratto/ds634_civici_coordinategeografiche_20261001_final.csv")
righe = []
cat_per_settore = collections.defaultdict(collections.Counter)
for eid, rs in ENT.items():
    rs = sorted(rs, key=lambda r: r["data_edizione"])
    Bs = [r for r in rs if r["elenco"] == "B_regione"]
    A17 = [r for r in rs if r["elenco"] == "A_albo" and r["edizione"] == "2017"]
    A24 = [r for r in rs if r["elenco"] == "A_albo" and r["edizione"] == "2024"]
    Bc = [r for r in Bs if r["edizione"] == "20261019"]
    ref = (Bc or A24 or (Bs[-1:] if Bs else []) or A17)[0]
    ref2 = A24[0] if A24 else ref
    MANG = re.compile(r"[?…•—]")
    nomi_ok = [r["insegna"].strip() for r in (A17 + A24) if r["insegna"].strip() and not MANG.search(r["insegna"])]
    nomi_b = [r["insegna"].strip() or r["denom"].strip() for r in (Bc + Bs[::-1]) if (r["insegna"] or r["denom"]).strip()]
    nome_rovinato = ""
    if nomi_ok:
        insegna = nomi_ok[0]
    elif nomi_b:
        insegna = nomi_b[0]
    else:
        insegna = (ref["insegna"] or ref["denom"]).strip()
        nome_rovinato = "sì" if MANG.search(insegna) else ""
    genere = (A24 or A17 or [{}])[0].get("genere", "")
    cat_b = next((r["cat"] for r in reversed(Bs) if r["cat"]), "")
    tx = dict(genere=genere, cat=cat_b, insegna=insegna, denom=(Bs[-1]["denom"] if Bs else ""))
    sett = settore(tx)
    if cat_b:
        cat_per_settore[sett][cat_b] += 1
    anni = [num(r["anno_inizio"]) for r in rs if num(r["anno_inizio"])]
    anno = num(ref["anno_inizio"]) or (anni[-1] if anni else None)
    anno_diversi = len(set(anni)) > 1
    anno_ric = next((r["anno_ric"] for r in reversed(Bs) if r["anno_ric"]), "")
    ordine_ind = Bc + Bs[::-1] + A17 + A24
    ind = ordine_ind[0]["indirizzo"].strip()
    cand = [r for r in ordine_ind if r["lon_f"]]
    ind_discordante = ""
    discordanza_m = ""
    if A24 and cand and cand[0]["elenco"] != "A_albo" and A24[0]["lon_f"]:
        dd = dist_m(float(cand[0]["lon_f"]), float(cand[0]["lat_f"]), float(A24[0]["lon_f"]), float(A24[0]["lat_f"]))
        discordanza_m = round(dd)
        if dd > 200:
            ind_discordante = f"Albo 2024 la colloca a {round(dd)} m: {A24[0]['indirizzo']}"
    lon = lat = None
    coord_da = ""
    if cand:
        lon, lat, coord_da = float(cand[0]["lon_f"]), float(cand[0]["lat_f"]), cand[0]["coord_da"]
    nil_id, nil = (None, None)
    coord_ver = ""
    coord_dist = ""
    if lon is not None:
        nil_id, nil = nil_di(lon, lat)
        gg_ = GEO.geocodifica(ind)
        if nil_id is None and "lon" in gg_:
            # coordinate della fonte fuori dal Comune: uso il punto del civico (file civici ds634)
            lon, lat, coord_da = gg_["lon"], gg_["lat"], "civici (coordinate della fonte fuori Milano)"
            nil_id, nil = nil_di(lon, lat)
        if "lon" in gg_:
            coord_dist = round(dist_m(lon, lat, gg_["lon"], gg_["lat"]))
            coord_ver = "ok (<=50 m dal civico)" if coord_dist <= 50 else ("scarto 50-200 m dal civico" if coord_dist <= 200 else "scarto >200 m dal civico: controllare")
        else:
            coord_ver = "civico non trovato nel file dei civici (" + gg_["esito"] + ")"
    prove = []
    stato_albo = A24[0]["stato"] if A24 else ""
    if A24:
        prove.append(f"Albo comunale 12/2024: {stato_albo}")
    elif A17:
        prove.append("Albo comunale 2017 sì, assente dall'Albo 2024")
    if Bc:
        prove.append("elenco Regione 19/10/2026: presente")
    elif Bs:
        prove.append(f"elenco Regione: assente dal 19/10/2026 (ultima copia vista {Bs[-1]['data_edizione']})")
    osm_f = False
    osm_id = osm_nome = ""
    osm_d = None
    osm_ts = ""
    osm_cl = False
    if lon is not None:
        nomi_q = [x for x in (insegna, ref["denom"], ref2["insegna"]) if x]
        via_t = toks_street(parse_ind(ind)[0])
        tq = [tk(x) - via_t for x in nomi_q]
        tq_full = [tk(x) for x in nomi_q]
        best = None
        for d, i in osm_vicini(lon, lat, 90):
            e = osm[i]
            comp = osm_compat(sett, e)
            s = 0
            for nm in osm_nome_tags(e):
                tn_full = tk(nm)
                tn = tn_full - via_t
                for a, tqk, tqf in zip(nomi_q, tq, tq_full):
                    if tqk and tn:
                        inter = len(tqk & tn)
                        v = max(inter / len(tqk | tn), 0.8 * inter / min(len(tqk), len(tn)))
                        # senza compatibilita' di tipo serve un nome quasi identico
                        if not comp and v < 0.9:
                            v = 0
                        s = max(s, v)
                    elif tqf and tn_full and tqf == tn_full and d <= 40 and comp:
                        s = max(s, 0.9)
                    elif not tqf and not tn_full and d <= 30 and comp:
                        s = max(s, sim_nome(a, nm))
            if s >= 0.5 and (best is None or s > best[0] or (s == best[0] and d < best[1])):
                best = (s, d, i)
        if best:
            s, d, i = best
            e = osm[i]
            osm_f = True
            osm_id = f"{e['type']}/{e['id']}"
            osm_nome = (e["tags"].get("name") or osm_nome_tags(e)[0])
            osm_d = round(d)
            osm_ts = e["ts"]
            osm_cl = osm_chiuso(e)
            if osm_cl:
                prove.append(f"OSM {osm_id} '{osm_nome}' a {osm_d} m segnato come chiuso (disused/was)")
            else:
                prove.append(f"OSM {osm_id} '{osm_nome}' a {osm_d} m, ultima modifica {osm_ts}")
        else:
            prove.append("OSM: nessun punto con nome simile entro 90 m")
    reg_f = "no"
    reg_t = ""
    if lon is not None:
        vic = reg_vicini(lon, lat, 40)
        nomi_q = [x for x in (insegna, ref["denom"]) if x]
        for d, i in vic:
            x = reg[i]
            if x[2] and any(sim_nome(a, x[2]) >= 0.5 for a in nomi_q):
                reg_f = "forte"
                reg_t = f"{x[4]} '{x[2]}' a {round(d)} m"
                break
        if reg_f == "no":
            comp = {"ristorante": "ds58|ds59|ds250", "bar_caffe": "ds58|ds59|ds250", "pasticceria_gelateria": "ds58|ds59|ds250|ds49", "panificio": "ds250|ds49"}.get(sett, "ds49")
            for d, i in vic:
                if d <= 25 and re.search(comp, reg[i][3]):
                    reg_f = "debole"
                    reg_t = f"pratica {reg[i][4]} stesso settore a {round(d)} m (insegna: {reg[i][2] or 'n.d.'})"
                    break
        if reg_f == "forte":
            prove.append(f"registro Comune 2026: {reg_t}")
        elif reg_f == "debole":
            prove.append(f"registro Comune 2026 (debole): {reg_t}")
        else:
            prove.append("registro Comune 2026: nessuna pratica compatibile entro 25 m")
    if stato_albo == "cessata":
        giud = "contraddittoria" if ((osm_f and not osm_cl) or reg_f == "forte") else "cessata"
    elif osm_cl and reg_f != "forte":
        giud = "cessata_probabile"
    elif (osm_f and not osm_cl) or reg_f == "forte":
        giud = "si"
    elif stato_albo == "attiva" or Bc:
        giud = "probabile"
    else:
        giud = "non_verificabile"
    cer19 = ""
    if (A17 or A24) and t19:
        if any(sim_nome(insegna, c) >= 0.85 and toks_nome(insegna) for c in t19): cer19 = "sì"
    fonti = []
    if A17 or A24:
        fonti.append("Albo comunale (ds290 2017, ds2858 2024; CC-BY)")
    if Bs:
        fonti.append("Regione Lombardia NLS (ds612 e copie; CC0)")
    righe.append(dict(id=eid, id_regione_nls=(Bs[-1]["id"] if Bs else ""), id_albo_2024=(A24[0]["id"] if A24 else ""), nome_insegna=insegna, categoria=cat_b, settore=sett, genere_albo=genere, anno_fondazione=anno or "", anno_dubbio=("sì" if anno_diversi else ""), nome_rovinato=nome_rovinato, indirizzo_discordante=ind_discordante, discordanza_albo2024_m=discordanza_m,
                      anno_riconoscimento_regione=anno_ric, indirizzo=ind, lon=round(lon, 6) if lon else "", lat=round(lat, 6) if lat else "", coord_da=coord_da, coord_verifica=coord_ver, coord_scarto_m=coord_dist,
                      nil_id=nil_id or "", nil=nil or "",
                      in_albo_2017="sì" if A17 else "", albo_riconoscimento=("2004-2017" if A17 else ("2019 (cerimonia 11/11/2019)" if cer19 else ("2018-2024, anno non indicato" if A24 else ""))), in_albo_2024="sì" if A24 else "", stato_albo_2024=stato_albo, in_regione_2026="sì" if Bc else "",
                      regione_prima_vista=Bs[0]["data_edizione"] if Bs else "", regione_ultima_vista=Bs[-1]["data_edizione"] if Bs else "",
                      osm_trovata="sì" if osm_f else "no", osm_id=osm_id, osm_nome=osm_nome, osm_dist_m=osm_d if osm_d is not None else "",
                      osm_ultima_modifica=osm_ts, osm_chiusa="sì" if osm_cl else "",
                      registro_2026=reg_f, ancora_attiva=giud, prove=" | ".join(prove), fonte=" + ".join(fonti)))
for r in righe:
    if not r["categoria"]:
        c = cat_per_settore.get(r["settore"])
        r["categoria"] = (c.most_common(1)[0][0] + " (stimata)") if c else ""
os.makedirs(B + "/pulito", exist_ok=True)
with open(B + "/pulito/botteghe.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(righe[0].keys()))
    w.writeheader()
    w.writerows(righe)
c = collections.Counter(r["ancora_attiva"] for r in righe)
print(len(righe), c)
print(collections.Counter(r["settore"] for r in righe).most_common())
print("senza coordinate:", sum(1 for r in righe if not r["lon"]), "senza NIL:", sum(1 for r in righe if not r["nil"]))
json.dump({s: dict(c) for s, c in cat_per_settore.items()}, open(B + "/pulito/settore_vs_categoria_regione.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
