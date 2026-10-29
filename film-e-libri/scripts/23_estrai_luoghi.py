"""Estrae i luoghi di Milano dalle sezioni utili degli articoli Wikipedia (it/en) e li lega alle opere.
Scrive (solo locale) pulito/_frasi_locali.csv con le frasi; scrive pulito/_match_tutti.csv (senza frasi) e pulito/luoghi.csv.
Uso: python -I 23_estrai_luoghi.py <strand> <root milano-in-dati>"""
import sys, os, re, csv, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_luoghi import norm, tokens, ARTICOLI, TOK
from lib_wikitext import *
from shapely.geometry import shape, Point
base, root = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(base, *a)
conf = shape(json.load(open(os.path.join(root, "citta-15-minuti", "raw", "comune_milano", "confine_comune", "confine_comune_milano_layer_0_confine_comune_milano.geojson"), encoding="utf8"))["features"][0]["geometry"]).buffer(0.002)

# ---------- gazetteer
SAFE_NIL = set("assiano boldinasco bovisasca bruzzano cagnola calvairate casoretto cimiano comasina dergano figino forlanini ghisolfa gorla lampugnano maciachini maggiolina missaglia moncucco morivione ortica portello precotto quintosole roserio rottole stadera taliedo tibaldi trenno turro vialba villapizzone sarpi muggiano nolo conchetta".split())
CUE_NEEDED = {"baggio", "brera", "loreto", "bocconi", "linate", "arcimboldi", "ticinese", "politecnico", "policlinico", "darsena", "naviglio"}
CUE = {"quartiere", "zona", "rione", "periferia", "nel", "nella", "in", "a", "ad", "verso", "da", "dal", "alla", "al", "sul", "sui", "di", "presso", "vicino", "dalla", "nei", "fino"}
GAZ = {}
for r in csv.DictReader(open(P("pulito", "_gazetteer.csv"), encoding="utf8")):
    k = r["chiave"]; n = k.count(" ") + 1
    if n == 1 and not (r["fonte"] == "elenco_a_mano" or (r["fonte"] == "NIL" and k in SAFE_NIL)): continue
    r["lat"], r["lon"] = float(r["lat"]), float(r["lon"]); r["n"] = n
    GAZ[k] = r
PREP_VIA = {"in","a","di","da","la","nella","sulla","per","su","lungo","dalla","e","o","tra","fra","con","della","alla","sulle","nelle","vicino","presso","verso","davanti","dietro","oltre","al","dal","nel","sul","the","on","at","near","of","and","ad","lo","il","delle","dei","nei"}
DESCSET = {"villa","palazzo","castello","chiesa","basilica","teatro","cinema","museo","hotel","ospedale","stazione","parco","giardino","casa","torre","ponte","cimitero"}
TITOLO_RX = re.compile(r"(libro|book|novel|racconti|released as|titled|intitolat|dal titolo|tratto da|ispirat[oa] a)", re.I)
RELEASE_RX = re.compile(r"(uscita (?:nelle sale|nei cinema|in sala)|debutta in sala|distribuit[oa] (?:da|in)|presentat[oa] (?:al|alla|in anteprima|a un)|anteprima|premiere|home media|released|screened|in prima visione|rappresentat[oa] (?:per la prima|in prima)|andat[oa] in scena|first performed|prima assoluta|prima rappresentazione|nei cinema|nelle sale|debutt|approd|spettacolo (?:del|dello|della) |messo in scena|allestimento)", re.I)
TITOLI_NOTI = re.compile(r"(San Babila ore 20|ponte della Ghisolfa|Romanzo di una strage|Piazza Fontana: The Italian Conspiracy|Il segreto di piazza Fontana)", re.I)
MAXN = max(r["n"] for r in GAZ.values())
COMMON = set("roma garibaldi mazzini dante manzoni verdi marconi cavour vittorio emanuele ii italia liberta repubblica indipendenza unita matteotti mille venezia torino napoli milano firenze genova bologna trieste europa america stazione san marco cesare battisti xx settembre giuseppe garibaldi giacomo matteotti".split())
ALTRE_CITTA = re.compile(r"\b(Roma|Napoli|Torino|Venezia|Firenze|Genova|Bologna|Parigi|Paris|Londra|London|Berlino|Berlin|Vienna|Madrid|Palermo|Bari|Trieste|Verona|Bergamo|Brescia|Como|Pavia|Monza|New York|Rome|Naples|Venice|Turin|Florence|Genoa|Switzerland|Svizzera|Lugano|Zurigo|Sicilia|Sicily|Sardegna|Catania|Sesto San Giovanni|Corsico|Segrate|Rho|Cinisello|Pioltello|Vimercate|Varese|Cremona|Lecco|Novara|Albenga|Forte dei Marmi|Gignese)\b")
MILANO = re.compile(r"\b(Milan|Milano|milanese|milanesi|Milanese|Mediolanum|Meneghin\w*)\b")
RIP_KW = re.compile(r"(girat[aoie]|girare|riprese|ripres[oi]|location|\bset\b|sul set|filmed|\bshot\b|shooting|filming|principal photography|fotografia principale|sceneggiat[aoi]? (?:presso|negli|nei))", re.I)
AMB_KW = re.compile(r"(ambientat|\bset in\b|\bsetting\b|si svolge|si svolgono|takes? place|is set|are set|was set|ambientazione|racconta|narra|vive\b|abita|lives)", re.I)

# ---------- link
LC = json.load(open(P("raw", "wikitext", "_link_coordinate.json"), encoding="utf8"))
NON_LUOGHI = ["regno lombardo", "ducato di milano", "repubblica cisalpina", "milan metro", "metropolitana di milano", "milan metropolitan", "five days", "cinque giornate", "rivolta di milano", "bombardamenti", "strage di", "expo 2015", "salani", "adelphi", "skira", "dolce & gabbana", "dolce e gabbana", "moncler", "loro piana", "baldini", "mondadori", "rizzoli", "bompiani", "feltrinelli", "passante ferroviario", "lombardia", "madonnina (statue)"]
EXCL_TITOLI = {norm(x) for x in ["Milano", "Milan", "Comune di Milano", "Città metropolitana di Milano", "Provincia di Milano", "Lombardia", "Storia di Milano", "Milano (disambigua)", "Municipi di Milano", "Quartieri di Milano", "Zone di Milano", "Italia", "Mediolanum"]}
def link_place(lang, target):
    v = LC.get(f"{lang}:{target[:1].upper() + target[1:]}")
    if not v or not v.get("lat"): return None
    nt = norm(v["titolo"])
    if nt in EXCL_TITOLI or nt.startswith(("municipio ", "quartiere ")) or any(x in nt for x in NON_LUOGHI): return None
    if not conf.contains(Point(v["lon"], v["lat"])): return None
    return v

# ---------- opere
OPERE = {}
for f, tipo_opera in (("film", "film"), ("serie_tv", "serie_tv"), ("libri", "libro"), ("altro", "altro")):
    for r in csv.DictReader(open(P("pulito", f + ".csv"), encoding="utf8")):
        wid = r["qid"] or ("OL:" + r["ol_key"] if r["ol_key"] else "")
        if not wid: continue
        r["wid"] = wid; r["tipo_opera"] = tipo_opera
        OPERE[wid] = r

def trova(frase, offs, spans, lang, wid, libro):
    """frase: testo; spans: link (s,e,target) in coordinate del paragrafo; offs: inizio frase nel paragrafo"""
    fb = TITOLI_NOTI.sub(lambda m: " " * len(m.group()), frase)
    tk = [(norm(m.group()), m.group(), m.start(), m.end()) for m in TOK.finditer(fb)]
    out = []; i = 0
    while i < len(tk):
        trovato = None
        for n in range(min(MAXN, len(tk) - i), 0, -1):
            key = " ".join(t[0] for t in tk[i:i+n])
            g = GAZ.get(key)
            if not g: continue
            orig = [t[1] for t in tk[i:i+n]]
            # almeno una parola maiuscola che non sia un articolo
            if not any(o[:1].isupper() and norm(o) not in ARTICOLI for o in orig): continue
            if n == 1 and key in CUE_NEEDED and not (i > 0 and tk[i-1][0] in CUE): continue
            if re.search(r"[-–]", frase[tk[i][2]:tk[i+n-1][3]]): continue   # "la linea Milano-Domodossola"
            prev = tk[i-1][0] if i > 0 else ""
            # "fa andare via Luciano": il "via" minuscolo deve seguire una preposizione o una virgola
            if tk[i][1] == "via" and i > 0 and prev not in PREP_VIA and not re.search(r"[,;:(\[]\s*$", frase[:tk[i][2]]): continue
            # nome di edificio ridotto (senza "villa", "palazzo"...) preceduto da un'altra parola descrittiva: altro edificio
            if prev in DESCSET and g["fonte"] == "OSM" and not norm(g["nome"]).startswith(prev): continue
            trovato = (n, key, g); break
        if not trovato: i += 1; continue
        n, key, g = trovato
        s, e = tk[i][2], tk[i+n-1][3]
        out.append(dict(s=s, e=e, testo=frase[s:e], nome=g["nome"], tipo_luogo=g["tipo"], lat=g["lat"], lon=g["lon"], fonte=g["fonte"], key=key, link=0))
        i += n
    # link a pagine con coordinate dentro Milano
    for (a, b, t) in spans:
        a2, b2 = a - offs, b - offs
        if a2 < 0 or b2 > len(frase): continue
        v = link_place(lang, t)
        if not v: continue
        sov = [m for m in out if m["s"] < b2 and a2 < m["e"]]
        if sov:
            for m in sov: m["link"] = 1
        else:
            gk = " ".join(tokens(re.sub(r"\s*\(.*?\)", "", v["titolo"])))
            g = GAZ.get(gk)
            if g and abs(g["lat"]-v["lat"]) < 0.01 and abs(g["lon"]-v["lon"]) < 0.01:
                out.append(dict(s=a2, e=b2, testo=frase[a2:b2], nome=g["nome"], tipo_luogo=g["tipo"], lat=g["lat"], lon=g["lon"], fonte=g["fonte"], key=gk, link=1))
            else:
                out.append(dict(s=a2, e=b2, testo=frase[a2:b2], nome=v["titolo"], tipo_luogo="luogo (Wikipedia)", lat=v["lat"], lon=v["lon"], fonte="wikilink", key="", link=1))
    return sorted(out, key=lambda m: m["s"])

def tipo_match(frase, m, kind, libro):
    if libro: return "ambientazione"
    defa = {"intro": "ambientazione", "trama": "ambientazione", "riprese": "riprese", "produzione": "riprese"}[kind]
    best = None
    for rx, t in ((RIP_KW, "riprese"), (AMB_KW, "ambientazione")):
        for x in rx.finditer(frase):
            d = min(abs(x.start() - m["e"]), abs(x.end() - m["s"]))
            if best is None or d < best[0]: best = (d, t)
    if best and best[0] <= 120: return best[1]
    return defa

def confidenza(frase, m, ctx, altre, kind):
    milano = bool(MILANO.search(frase)) or ctx
    if TITOLO_RX.search(frase[max(0, m["s"]-90):m["s"]]) or (kind != "trama" and RELEASE_RX.search(frase)): return "bassa"
    k = m["key"]; toks = k.split()
    comune = m["fonte"] in ("civici_comune", "civici_comune_cognome") and (" ".join(toks[1:]) in COMMON or (len(toks) > 1 and toks[-1] in COMMON and len(toks) <= 3))
    if altre and not milano and not m["link"]: return "bassa"
    if m["link"] or m["fonte"] == "elenco_a_mano":
        return "alta" if not (comune) else "media"
    if comune and not milano: return "bassa"
    if milano: return "alta"
    return "media"

righe = []   # tutti i match
art = carica_articoli(base)
# mappa titolo richiesto -> opera
idx = {}
for wid, r in OPERE.items():
    if r["itwiki"]: idx[("it", r["itwiki"])] = wid
    if r["enwiki"]: idx[("en", r["enwiki"])] = wid
for (lang, rich), (tit, w) in art.items():
    wid = idx.get((lang, rich))
    if not wid: continue
    libro = OPERE[wid]["tipo_opera"] == "libro"
    ered = {1: None}
    for liv, titolo, testo in sezioni(w):
        kind = classifica_sezione(titolo, ered.get(liv-1) if liv > 2 else None)
        ered[liv] = kind
        if not kind: continue
        # per i libri le sezioni di produzione/riprese non esistono: si tengono solo quelle su trama
        paras = paragrafi(pulisci(testo))
        for pi, (piano, spans) in enumerate(paras):
            ctx_par = bool(MILANO.search(piano))
            for (a, b) in frasi(piano):
                fr = piano[a:b]
                ms = trova(fr, a, spans, lang, wid, libro)
                bl = list(fr)
                for m in ms:
                    for q in range(m["s"], m["e"]): bl[q] = " "
                altre = bool(ALTRE_CITTA.search("".join(bl)))
                for m in ms:
                    t = tipo_match(fr, m, kind, libro)
                    c = confidenza(fr, m, False, altre, kind)
                    righe.append(dict(wid=wid, lang=lang, sezione=titolo or "Introduzione", kind=kind, frase=fr.strip(), testo=m["testo"], luogo=m["nome"], tipo_luogo=m["tipo_luogo"],
                                      lat=round(m["lat"], 6), lon=round(m["lon"], 6), fonte=m["fonte"], via_link=m["link"], tipo=t, conf=c))
print("match totali", len(righe), collections.Counter(r["conf"] for r in righe), flush=True)
# ---------- file locale con le frasi
cols = ["wid", "titolo", "lang", "sezione", "tipo", "conf", "luogo", "testo", "tipo_luogo", "lat", "lon", "fonte", "via_link", "frase"]
with open(P("pulito", "_frasi_locali.csv"), "w", encoding="utf8", newline="") as f:
    wr = csv.DictWriter(f, cols, extrasaction="ignore"); wr.writeheader()
    for r in righe:
        r["titolo"] = OPERE[r["wid"]]["titolo_it"] or OPERE[r["wid"]]["titolo_en"]
        wr.writerow(r)
json.dump(righe, open(P("pulito", "_match_tutti.json"), "w", encoding="utf8"), ensure_ascii=False)
