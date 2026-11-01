"""Unisce le righe di tutte le edizioni in "attività" (entità): stesso ID Regione, oppure stesso civico + nome simile.
Geocodifica con il file civici del Comune (ds634) per: validare le coordinate della fonte, riempire quelle mancanti, trovare la via.
Scrive pulito/entita_record.csv (ogni riga di edizioni_lunga + ent_id) e pulito/geocodifica_log.json.
Uso: python -I -X utf8 02_unifica.py <botteghe abs> <civici csv abs>"""
import sys, os, csv, json, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_botteghe import *
B, CIV = sys.argv[1:3]
G = Geocoder(CIV)
rows = list(csv.DictReader(open(B + "/pulito/edizioni_lunga.csv", encoding="utf-8")))
n = len(rows)
# --- geocodifica per indirizzo (cache)
cache = {}
esiti = collections.Counter()
for i, r in enumerate(rows):
    ind = r["indirizzo"]
    if ind not in cache:
        g = G.geocodifica(ind)
        st, civ, let = parse_ind(ind)
        cv, j = (G.trova_via(st) if st else (None, 0))
        g["cv"] = cv if (cv and j >= 0.5) else None
        g["civ"] = civ; g["let"] = let
        cache[ind] = g
    r["_g"] = cache[ind]
    r["civ"] = cache[ind]["civ"]
    r["cv"] = cache[ind]["cv"]
    r["street_t"] = toks_street(parse_ind(ind)[0])
    esiti[(r["elenco"], cache[ind]["esito"])] += 1
# coordinate: tengo quelle della fonte se presenti e sensate, altrimenti civici
dist_alte = []
for r in rows:
    g = r["_g"]
    try: lon, lat = float(r["lon"]), float(r["lat"])
    except: lon = lat = None
    ok_src = lon is not None and 9.0 < lon < 9.4 and 45.35 < lat < 45.6
    if ok_src and "lon" in g:
        d = dist_m(lon, lat, g["lon"], g["lat"])
        if d > 200: dist_alte.append((r["elenco"], r["edizione"], r["id"], r["insegna"], r["indirizzo"], round(d)))
    if ok_src: r["lon_f"], r["lat_f"], r["coord_da"] = lon, lat, "fonte"
    elif "lon" in g: r["lon_f"], r["lat_f"], r["coord_da"] = g["lon"], g["lat"], "civici"
    else: r["lon_f"] = r["lat_f"] = None; r["coord_da"] = ""
# --- union-find
par = list(range(n))
def f(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
def u(a, b):
    a, b = f(a), f(b)
    if a != b: par[b] = a
# 1) stesso ID Regione
byid = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r["elenco"] == "B_regione": byid[r["id"]].append(i)
for ids in byid.values():
    for k in ids[1:]: u(ids[0], k)
# 2) civico + nome
def nomesim(a, b):
    s = 0
    for x in (a["insegna"], a["denom"]):
        for y in (b["insegna"], b["denom"]):
            if x and y: s = max(s, sim_nome(x, y))
    return s
blocks = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r["civ"] is not None: blocks[r["civ"]].append(i)
legami = 0
for civ, idx in blocks.items():
    # una riga per (cluster provvisorio) basta; confronto a coppie ma salto coppie gia unite
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if f(i) == f(j): continue
            ri, rj = rows[i], rows[j]
            same_street = (ri["cv"] and ri["cv"] == rj["cv"]) or (ri["street_t"] and rj["street_t"] and len(ri["street_t"] & rj["street_t"]) / len(ri["street_t"] | rj["street_t"]) >= 0.6)
            if not same_street: continue
            ns = nomesim(ri, rj)
            ai, aj = ri["anno_inizio"], rj["anno_inizio"]
            stesso_anno = ai and ai == aj
            if ns >= 0.45 or (stesso_anno and ns >= 0.15) or (stesso_anno and ri["elenco"] != rj["elenco"] and ns >= 0.0 and len([k for k in idx if rows[k]["anno_inizio"] == ai]) <= 3 and False):
                u(i, j); legami += 1
print("legami per civico+nome:", legami)
# 3) senza civico (o civico diverso per refusi): stesso nome quasi uguale + stessa via
nocivico = [i for i, r in enumerate(rows) if r["civ"] is None]
bystreet = collections.defaultdict(list)
for i, r in enumerate(rows): 
    if r["cv"]: bystreet[r["cv"]].append(i)
l2 = 0
for i in nocivico:
    r = rows[i]
    for j in bystreet.get(r["cv"], []):
        if f(i) == f(j): continue
        if nomesim(r, rows[j]) >= 0.7 and r["anno_inizio"] == rows[j]["anno_inizio"]:
            u(i, j); l2 += 1
print("legami senza civico:", l2)
# 4) stesso nome (>=0.8) + stesso anno + distanza < 150 m anche con civici diversi (civico cambiato / refuso)
bynome = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r["lon_f"] is not None: bynome[r["anno_inizio"]].append(i)
l3 = 0
for anno, idx in bynome.items():
    if not anno: continue
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if f(i) == f(j): continue
            ri, rj = rows[i], rows[j]
            if dist_m(ri["lon_f"], ri["lat_f"], rj["lon_f"], rj["lat_f"]) > 150: continue
            if nomesim(ri, rj) >= 0.8:
                u(i, j); l3 += 1
print("legami nome+anno+vicinanza:", l3)
# 5) Albo 2024 con indirizzo ri-geocodificato male (es. "Piazza Mercanti 17" -> "Via Luigi Mercantini 17"): lo stesso negozio resta separato.
#    Unisco un gruppo SENZA riga Albo 2024 con un gruppo CON Albo 2024 ma senza Albo 2017, se nome quasi uguale e anno di inizio uguale (+-2),
#    uno a uno e senza righe doppie nella stessa edizione. Ordine: somiglianza del nome, poi distanza.
def gruppi():
    gg = collections.defaultdict(list)
    for i in range(n): gg[f(i)].append(i)
    return gg
gg = gruppi()
def chiavi(idx): return set((rows[i]["elenco"], rows[i]["edizione"]) for i in idx)
def anno_g(idx):
    a = [int(rows[i]["anno_inizio"]) for i in idx if rows[i]["anno_inizio"].isdigit()]
    return a[0] if a else None
def centro(idx):
    pts = [(rows[i]["lon_f"], rows[i]["lat_f"]) for i in idx if rows[i]["lon_f"] is not None]
    return pts[-1] if pts else None
def scheletro(txt):
    # consonanti dei token, per confrontare nomi con accenti rovinati nel file dell'Albo 2024 ("Citt…" vs "Città")
    t = sa(txt).lower().replace("…", " ").replace("•", " ").replace("?", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return frozenset(re.sub(r"[aeiou]", "", w) for w in t.split() if w not in STOPN and len(w) > 1) - {""}
def nomesim2(a, b):
    s = nomesim(a, b)
    for x in (a["insegna"], a["denom"]):
        for y in (b["insegna"], b["denom"]):
            if x and y:
                sx, sy = scheletro(x), scheletro(y)
                if sx and sy and sx == sy: s = max(s, 0.9)
    return s
def ha_albo(idx): return any(rows[i]["elenco"] == "A_albo" for i in idx)
def ha_b(idx): return any(rows[i]["elenco"] == "B_regione" for i in idx)
cands = []
ks = list(gg.keys())
for y in ks:
    cy_ = chiavi(gg[y])
    for x in ks:
        if x == y: continue
        cx_ = chiavi(gg[x])
        r1 = ("A_albo", "2024") not in cx_ and ("A_albo", "2024") in cy_ and ("A_albo", "2017") not in cy_ and not ha_b(gg[y])
        r2 = (not ha_albo(gg[x])) and ha_albo(gg[y]) and not ha_b(gg[y])
        if not (r1 or r2): continue
        if cx_ & cy_: continue
        ay, ax = anno_g(gg[y]), anno_g(gg[x])
        if ay is None or ax is None or abs(ay - ax) > 2: continue
        ns = max(nomesim2(rows[i], rows[j]) for i in gg[y] for j in gg[x])
        if ns < 0.8: continue
        cy, cx = centro(gg[y]), centro(gg[x])
        d = dist_m(cy[0], cy[1], cx[0], cx[1]) if cy and cx else 99999
        cands.append((-ns, d, y, x))
cands.sort()
usati_x, usati_y = set(), set()
l5 = []
for ns, d, y, x in cands:
    if x in usati_x or y in usati_y: continue
    usati_x.add(x); usati_y.add(y)
    u(gg[y][0], gg[x][0]); l5.append((rows[gg[y][0]]["insegna"], rows[gg[y][0]]["indirizzo"], rows[gg[x][0]]["indirizzo"], round(d)))
print("legami Albo2024 con indirizzo diverso:", len(l5))
ent = {}
for i, r in enumerate(rows):
    root = f(i)
    ent.setdefault(root, len(ent) + 1)
    r["ent_id"] = "E%04d" % ent[root]
out = ["ent_id", "elenco", "edizione", "data_edizione", "id", "tipo", "ric", "insegna", "denom", "genere", "cat", "anno_inizio", "anno_ric", "stato", "indirizzo", "municipio", "nil", "lon_f", "lat_f", "coord_da", "civ", "cv"]
with open(B + "/pulito/entita_record.csv", "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, out, extrasaction="ignore"); w.writeheader()
    for r in sorted(rows, key=lambda r: (r["ent_id"], r["elenco"], r["data_edizione"])): w.writerow(r)
n_ent = len(ent)
print("righe", n, "-> attivita'", n_ent)
json.dump({"esiti_geocodifica_per_riga": {f"{k[0]}|{k[1]}": v for k, v in esiti.items()}, "coord_fonte_vs_civici_oltre_200m": dist_alte, "legami": [legami, l2, l3, len(l5)], "legami_albo2024_indirizzo_diverso": l5, "attivita": n_ent}, open(B + "/pulito/geocodifica_log.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
