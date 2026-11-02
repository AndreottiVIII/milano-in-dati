"""Costruisce i dati della pagina docs/targhe/ (lapidi e targhe di Milano da fonti libere).
Uso: python -I -X utf8 pagina.py <targhe> <milano-in-dati>     (percorsi assoluti)
Legge: statue/pulito (lapidi gia' unite da OSM e Wikidata, soggetto e sesso da Wikidata P21),
       targhe/raw/osm/overpass_targhe.json (OSM, 2/11/2026), targhe/raw/commons/plaques_milan.json (solo metadati),
       citta-15-minuti (confini NIL), donne-nelle-vie e docs/statue/data/pagina.json (confronti).
Legge targhe/pulito/_pdm_campi.csv e pdm_persone.csv (campi fattuali estratti dalle schede di Pietre della Memoria, ANMIG, dati usati con
autorizzazione dichiarata da Davide il 2/11/2026; vedi 05-07). NON legge raw/pdm (HTML grezzi: non pubblicare).
Scrive: targhe/pulito/ e milano-in-dati/docs/targhe/data/ (tutto sovrascritto: rilanciabile).
Il file docs/targhe/index.html e' scritto a mano e legge pagina.json e targhe_mappa.json."""
import sys, os, re, csv, json, math, shutil, collections, datetime
import shapely
sys.path.insert(0, os.path.join(sys.argv[2], "statue", "scripts"))
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

# ---------------- base: lapidi del filone statue (OSM + Wikidata)
opere = rd(os.path.join(S, "opere.csv"))
sogg = rd(os.path.join(S, "soggetti.csv"))
base = [r for r in opere if r["tipo"] == "lapide o targa"]
osm_usati = set()
rows = []
def vuoto(x):
    x = (x or "").strip()
    return "" if x.lower().startswith("informazione non reperita") or x.lower() in ("non noto", "non nota", "n.d.") else x
for r in base:
    ids = r["osm_id"].split()
    insc = ""
    for i in ids:
        osm_usati.add(i)
        if i in osm_by: insc = insc or osm_by[i].get("inscription", "").replace("\n", " ").strip()
    rows.append(dict(nome=r["nome"], soggetto=r["soggetto"], soggetto_qid=r["soggetto_qid"], genere=r["genere soggetto"], gruppo=r["professione"],
                     anno=r["anno posa"], testo=insc, lon=r["lon"], lat=r["lat"], NIL=r["NIL"], id_nil=r["id_nil"], fonte=r["fonte"],
                     osm_id=r["osm_id"], qid=r["qid_opera"], file="", id_statue=r["id"], stipo=r["soggetto_tipo"],
                     pdm_id="", pdm_url="", indirizzo="", ente="", data_posa="", tags=""))
osm_non_in_base = [i for i in osm_by if i not in osm_usati]
n_free = len(rows)
free_con_coord = sum(1 for r in rows if r["lat"])
free_pts_all = [(float(r["lat"]), float(r["lon"])) for r in rows if r["lat"]]

# ---------------- Pietre della Memoria (ANMIG): campi fattuali, targhe (non pietre d'inciampo, non monumenti/cippi/stele)
pdm_all = rd(os.path.join(OUT, "_pdm_campi.csv"))
PLAQ = re.compile(r"^(lapide|lastra|targa|epigrafe|lapidi|lastre|targhe)\b", re.I)
pdm = []; pdm_altri = collections.Counter()
for r in pdm_all:
    if PLAQ.match(r["titolo"]): pdm.append(r)
    else:
        pdm_altri[re.split(r"[ ,]", r["titolo"].lower())[0]] += 1
STOP = set("lapide lastra targa commemorativa celebrativa ricordo memoria caduti caduto partigiano partigiana partigiani milano della delle dello degli dell guerra mondiale prima seconda libertà liberta resistenza vittime ricorda zona sulla sulle nella nelle edificio palazzo".split())
def toks(s): return {w for w in norm(s).split() if len(w) >= 4 and w not in STOP}
def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", (s or "").lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s)).strip()
def titolo_pulito(t): return re.sub(r"\s*[–-]\s*Milano(?: \(MI\))?\s*$", "", t).strip()
pdm_pers = {}
pp = os.path.join(OUT, "pdm_persone.csv")
if os.path.exists(pp):
    for x in rd(pp):
        if x["qid"]: pdm_pers.setdefault(x["id_pdm"], []).append(x)
unite = set(); n_unite = 0; pdm_nuove = []
cand_idx = list(range(len(rows)))
for r in pdm:
    lat, lon = float(r["lat"]), float(r["lon"])
    nome_t = titolo_pulito(r["titolo"]); tk = toks(nome_t + " " + r["iscrizione"])
    best = None
    for i in cand_idx:
        if i in unite or not rows[i]["lat"]: continue
        d = dist((lat, lon), (float(rows[i]["lat"]), float(rows[i]["lon"])))
        if d > 30: continue
        comune = tk & toks(rows[i]["nome"] + " " + rows[i]["testo"])
        if d <= 8 or comune:
            if best is None or d < best[0]: best = (d, i)
    pe = pdm_pers.get(r["id_pdm"], [])
    campi = dict(pdm_id=r["id_pdm"], pdm_url=r["url"], indirizzo=r["indirizzo"], ente=vuoto(r["ente"]), data_posa=vuoto(r["data_collocazione"]), tags=r["tags"])
    if best:
        t = rows[best[1]]; unite.add(best[1]); n_unite += 1
        t.update(campi); t["fonte"] = t["fonte"] + "+pdm"
        t["testo"] = t["testo"] or vuoto(r["iscrizione"])
        if r["anno_collocazione"] and not t["anno"]: t["anno"] = r["anno_collocazione"]
        if not t["nome"]: t["nome"] = nome_t
        if not t["soggetto"] and pe:
            t["soggetto"] = " | ".join(x["etichetta"] for x in pe); t["soggetto_qid"] = " | ".join(x["qid"] for x in pe)
            t["genere"] = " | ".join(x["genere"] for x in pe if x["genere"]); t["stipo"] = "persona reale (da titolo PdM)"
    else:
        nr = dict(nome=nome_t, soggetto=" | ".join(x["etichetta"] for x in pe), soggetto_qid=" | ".join(x["qid"] for x in pe), genere=" | ".join(x["genere"] for x in pe if x["genere"]),
                  gruppo="", anno=r["anno_collocazione"], testo=vuoto(r["iscrizione"]), lon=r["lon"], lat=r["lat"], NIL="", id_nil="", fonte="pdm", osm_id="", qid="", file="", id_statue="",
                  stipo="persona reale (da titolo PdM)" if pe else "", **campi)
        i_, n_ = nil_of(lon, lat)
        if i_ is None: pdm_altri["fuori dal Comune"] += 1; continue
        nr["id_nil"], nr["NIL"] = str(i_), n_
        rows.append(nr); pdm_nuove.append(nr)
overlap_pdm_free = n_unite

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
                     fonte="commons", osm_id="", qid="", file=k, id_statue="", stipo="", pdm_id="", pdm_url="", indirizzo="", ente="", data_posa="", tags=""))

# ---------------- categorie: regole semplici in ordine, sul nome, sul testo (OSM o PdM), sull'etichetta di Pietre della Memoria e sul soggetto
RULES = [
 ("Resistenza e vittime del nazifascismo", r"partigian|resistenz|nazifasc|nazist|antifasc|deportat|lager|sterminio|concentramento|caduti per la libert|liberazione (di milano|nazionale)|comitato di liberazione|lotta di liberazione|fucilat|trucidat|gappist|\bcln\b|martiri della libert|eccidio|rappresaglia|persecuzion|brigata (garibaldi|del popolo|partigiana|matteotti|giustizia)|nemici della libert|ideale della libert|combattente\w* (eroico )?della libert"),
 ("Vittime di terrorismo e violenza", r"terroris|attentat|strage|piazza fontana|brigate rosse|assassinat|ucciso|uccis|vittim[ae] del (dovere|terrorismo|lavoro)|mafia|nassiriya|adempimento del dovere"),
 ("Guerre, caduti e forze armate", r"caduti|guerra|combattent|alpini|reduci|mutilat|bersaglier|soldat|1915|valor militare|valore militare|reggimento|battaglione|batterie|artiglieria|medaglia d|carabinier|guardia di finanza"),
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
    gruppi = (r["gruppo"] or "").split(" | ")
    for lab, rx in RULES:
        if re.search(rx, txt): return lab, "parole nel nome o nel testo"
    if "prima guerra mondiale" in r["tags"].lower(): return "Guerre, caduti e forze armate", "etichetta di Pietre della Memoria"
    for gk in gruppi:
        if gk in GR: return GR[gk], "mestiere in Wikidata"
    for lab, rx in KW2:
        if re.search(rx, txt): return lab, "parole nel nome o nel testo"
    if "seconda guerra mondiale" in r["tags"].lower() or "caduti delle guerre" in r["tags"].lower(): return "Guerre, caduti e forze armate", "etichetta di Pietre della Memoria"
    return ALTRO, ""
# mestiere (gruppo) per le persone trovate da PdM: dalla descrizione breve di Wikidata
from wdlib import group_of
for r in rows:
    if r["pdm_id"] and r["soggetto_qid"] and not r["gruppo"]:
        ds = pdm_pers.get(r["pdm_id"], [])
        r["gruppo"] = " | ".join(group_of([], x["descrizione"]) for x in ds) if ds else ""
for i, r in enumerate(rows, 1):
    r["id"] = "T%04d" % i
    r["categoria"], r["categoria_come"] = classifica(r)
    r["casa"] = "1" if CASA.search(r["nome"] + " " + r["testo"]) else ""

# ---------------- chi ha posato / se ne prende cura (campo "Ente preposto alla conservazione" di PdM; se manca, parole nel testo della targa)
POS = [("ANPI", r"a\.?\s?n\.?\s?p\.?\s?i"),
       ("Comune di Milano, Municipio, Consiglio di zona", r"comune|amministrazione comunale|consiglio di zona|municipio|consiglio di quartiere|\bzona \d"),
       ("Associazioni di reduci, combattenti, deportati", r"anmig|mutilati|alpini|\bana\b|combattent|reduci|aned|anei|anpc|anrp|deportati|partigiani d"),
       ("Aziende, ferrovie, lavoratori e sindacati", r"a\.?t\.?m\b|ferrovi|cooperativa|sindacat|cgil|cisl|\buil\b|fabbrica|s\.p\.a|ospedale|operai|lavoratori|dipendenti"),
       ("Scuole e università", r"scuola|liceo|istituto|universit|\bscolast"),
       ("Chiese e parrocchie", r"parrocchia|chiesa|curia|diocesi|basilica|oratorio"),
       ("Famiglie e privati", r"famigli|privat|condomin|amici"),
       ("Forze armate e forze dell'ordine", r"reggimento|guardia di finanza|ministero della difesa|carabinier|battaglione|aeronautica|esercito|marina militare|polizia|vigili del fuoco"),
       ("Stato, Regione e altri enti pubblici", r"ministero|soprintendenza|prefettura|provincia|regione|stato")]
def posatori(r):
    base_t = (r["ente"] or "").lower()
    ris = [lab for lab, rx in POS if re.search(rx, base_t)]
    if "Forze armate e forze dell'ordine" in ris: ris = [x for x in ris if not x.startswith("Stato")]
    if ris: return ris, "ente indicato"
    ins = (r["testo"] or "").lower()
    ris = [lab for lab, rx in POS if lab in ("ANPI", "Comune di Milano, Municipio, Consiglio di zona", "Scuole e università", "Chiese e parrocchie", "Famiglie e privati") and re.search(rx, ins)]
    if ris: return ris, "scritto nel testo della targa"
    return [], ""
for r in rows:
    r["posa"], r["posa_come"] = posatori(r)

# ---------------- scrittura tabella pulita
COLS = ["id", "nome", "categoria", "categoria_come", "soggetto", "soggetto_qid", "genere_soggetto", "gruppo_professione", "anno_posa", "data_posa_pdm", "chi_ha_posato_o_cura", "ente_pdm", "casa", "testo_iscrizione", "indirizzo_pdm", "lon", "lat", "NIL", "id_nil", "fonte", "osm_id", "qid_wikidata", "id_pietre_memoria", "url_pietre_memoria", "file_commons", "id_filone_statue"]
def line(r): return [r["id"], r["nome"], r["categoria"], r["categoria_come"], r["soggetto"], r["soggetto_qid"], r["genere"], r["gruppo"], r["anno"], r["data_posa"], " | ".join(r["posa"]), r["ente"], r["casa"], r["testo"], r["indirizzo"], r["lon"], r["lat"], r["NIL"], r["id_nil"], r["fonte"], r["osm_id"], r["qid"], r["pdm_id"], r["pdm_url"], r["file"], r["id_statue"]]
with open(os.path.join(OUT, "targhe.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(COLS); [w.writerow(line(r)) for r in rows]

idmap = {r["id_statue"]: r for r in rows if r["id_statue"]}
sp = [dict(id_targa=idmap[s_["id_opera"]]["id"], targa=s_["opera"], qid=s_["qid"], persona=s_["persona"], genere=s_["genere"], nascita=s_["nascita"], morte=s_["morte"], gruppo_professione=s_["gruppo_professione"],
           come_trovato=s_["come_trovato"], anno_posa=s_["anno_posa"]) for s_ in sogg if s_["id_opera"] in idmap]
con_persona_statue = {x["id_targa"] for x in sp}
for r in rows:   # persone trovate da PdM (titolo -> Wikidata, regole in 07_pdm_persone.py), solo per le targhe senza persone dal filone statue
    if r["pdm_id"] and r["id"] not in con_persona_statue:
        for x in pdm_pers.get(r["pdm_id"], []):
            sp.append(dict(id_targa=r["id"], targa=r["nome"], qid=x["qid"], persona=x["etichetta"], genere=x["genere"], nascita=x["nascita"], morte=x["morte"],
                           gruppo_professione=group_of([], x["descrizione"]), come_trovato="titolo Pietre della Memoria + Wikidata (" + x["esito"] + ")", anno_posa=r["anno"]))
with open(os.path.join(OUT, "persone.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sp[0].keys())); w.writeheader(); w.writerows(sp)

# ---------------- numeri
n = len(rows)
fonte = collections.Counter(r["fonte"] for r in rows)
con_coord = sum(1 for r in rows if r["lat"])
st = json.load(open(os.path.join(P, "docs/statue/data/pagina.json"), encoding="utf8"))
ov = st["overlap"]["lapidi_e_targhe"]
out = dict(generato=datetime.date.today().isoformat(), osm_timestamp=osm_ts, n=n, fonte=dict(fonte), con_coord=con_coord,
           osm_targhe=n_osm_targhe, osm_con_nome=sum(1 for t in osm_by.values() if "name" in t), osm_con_testo=sum(1 for t in osm_by.values() if "inscription" in t),
           osm_con_nome_o_testo=sum(1 for t in osm_by.values() if "name" in t or "inscription" in t), osm_non_in_base=len(osm_non_in_base),
           commons_file=len(cm), commons_con_coord=sum(1 for v in cm.values() if v["lat"]), commons_candidate=len(cands), commons_usate=len(com))
# --- il punto "i dati APERTI" (OSM + Wikidata): resta come risultato a parte
out["aperti"] = dict(n=n_free, con_coord=free_con_coord, stima=ov, quota=round(100 * n_free / ov["stima_grezza_totale"], 1),
                     solo_osm=sum(1 for r in rows if r["fonte"].startswith("osm") and "wikidata" not in r["fonte"]),
                     solo_wd=sum(1 for r in rows if r["fonte"].startswith("wikidata")), entrambe=sum(1 for r in rows if "osm" in r["fonte"] and "wikidata" in r["fonte"]))
# --- Pietre della Memoria
out["pdm"] = dict(voci=len(pdm_all) + 101, schede_scaricate=len(pdm_all), inciampo=101, targhe=len(pdm), altri_tipi=dict(pdm_altri), unite_con_aperti=overlap_pdm_free, solo_pdm=len(pdm_nuove),
                  con_anno=sum(1 for r in pdm if r["anno_collocazione"]), con_ente=sum(1 for r in pdm if vuoto(r["ente"])), con_iscrizione=sum(1 for r in pdm if vuoto(r["iscrizione"])),
                  data_scarico="2 novembre 2026")
if overlap_pdm_free: out["pdm"]["stima_lp"] = round(len(pdm) * free_con_coord / overlap_pdm_free)
cat = collections.Counter(r["categoria"] for r in rows)
out["categorie"] = [[k, int(v)] for k, v in cat.most_common()]
out["categoria_come"] = dict(collections.Counter(r["categoria_come"] for r in rows if r["categoria"] != ALTRO))
out["casa"] = sum(1 for r in rows if r["casa"])
out["con_soggetto"] = sum(1 for r in rows if r["soggetto"])
out["con_nome"] = sum(1 for r in rows if r["nome"])
out["con_testo"] = sum(1 for r in rows if r["testo"])
out["con_anno"] = sum(1 for r in rows if r["anno"].isdigit())
out["anni"] = sorted(int(r["anno"]) for r in rows if r["anno"].isdigit())
dec = collections.Counter(a // 10 * 10 for a in out["anni"])
out["decenni"] = sorted(dec.items())
out["epoche"] = [[nm, sum(1 for a in out["anni"] if lo_ <= a <= hi_)] for nm, lo_, hi_ in [("prima del 1945", 0, 1944), ("1945-1969 (dopoguerra)", 1945, 1969), ("1970-1999", 1970, 1999), ("dal 2000", 2000, 3000)]]
# --- persone e donne
u = {}
for s_ in sp: u.setdefault(s_["qid"], s_)
noti = [s_ for s_ in u.values() if s_["genere"] in ("uomo", "donna")]
nd = sum(1 for s_ in noti if s_["genere"] == "donna")
lo, hi = wilson(nd, len(noti))
out["persone"] = dict(uniche=len(u), sesso_noto=len(noti), donne=nd, quota=round(100 * nd / len(noti), 1) if noti else None, lo=lo, hi=hi,
                      donne_elenco=[[s_["persona"], s_["targa"], s_["gruppo_professione"]] for s_ in u.values() if s_["genere"] == "donna"],
                      da_pdm=len({s_["qid"] for s_ in sp if "Pietre della Memoria" in s_["come_trovato"]}))
pe_all = rd(pp) if os.path.exists(pp) else []
out["pdm_nomi"] = dict(cercati=len(pe_all), trovati=sum(1 for x in pe_all if x["qid"]))
G_ = st["genere"]
out["confronto"] = dict(statue=G_[1], vie=G_[-1], quota_vie=st["quota_vie"])
cnt = collections.Counter(); info = {}
for s_ in sp: cnt[s_["qid"]] += 1; info[s_["qid"]] = s_
top = sorted(cnt.items(), key=lambda x: (-x[1], info[x[0]]["persona"]))
out["top"] = [[info[q]["persona"], c, info[q]["gruppo_professione"], info[q]["genere"]] for q, c in top[:12]]
out["top_max"] = top[0][1] if top else 0
out["n_persone_con_2"] = sum(1 for q, c in top if c >= 2)
gp = collections.Counter(s_["gruppo_professione"] or "non indicato" for s_ in u.values())
out["professioni"] = [[k, v, sum(1 for s_ in u.values() if (s_["gruppo_professione"] or "non indicato") == k and s_["genere"] == "donna")] for k, v in gp.most_common()]
# --- Resistenza
res = [r for r in rows if r["categoria"].startswith("Resistenza")]
out["resistenza"] = dict(n=len(res), solo_aperti=sum(1 for r in res if "pdm" not in r["fonte"]), con_pdm=sum(1 for r in res if "pdm" in r["fonte"]),
                         con_anno=sum(1 for r in res if r["anno"].isdigit()), con_nome_persona=sum(1 for r in res if r["soggetto"]),
                         press_2021=500, press_fonte="https://www.ilfattoquotidiano.it/2021/04/16/25-aprile-a-milano-le-storie-dei-partigiani-arrivano-sullo-smartphone-le-lapidi-dotate-di-qr-code-con-le-bio-da-sergio-a-jenide-chi-sono/6145293/",
                         anni_2020_26=sum(1 for r in res if r["anno"].isdigit() and int(r["anno"]) >= 2020),
                         elenco_recenti=[[r["nome"], r["anno"], r["NIL"]] for r in sorted(res, key=lambda r: r["anno"] or "0", reverse=True) if r["anno"].isdigit()][:12])
# --- chi ha posato
pc_ = collections.Counter(); pr_ = collections.Counter()
for r in rows:
    for l_ in r["posa"]: pc_[l_] += 1
    pr_[r["posa_come"] or "non indicato"] += 1
out["posatori"] = dict(elenco=[[k, v] for k, v in pc_.most_common()], con_indicazione=sum(1 for r in rows if r["posa"]), come=dict(pr_),
                       con_pdm=sum(1 for r in rows if "pdm" in r["fonte"]), piu_di_uno=sum(1 for r in rows if len(r["posa"]) > 1))
pd_ = collections.defaultdict(collections.Counter)
for r in rows:
    if r["anno"].isdigit() and r["posa"]:
        d_ = int(r["anno"]) // 10 * 10
        for l_ in r["posa"]: pd_[d_][l_] += 1
out["posatori_per_decennio"] = {str(k): dict(v) for k, v in sorted(pd_.items())}
# --- NIL
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
mcols = ["id", "nome", "cat", "soggetto", "genere", "anno", "NIL", "fonte", "url", "posa"]
cats = [c[0] for c in out["categorie"]]
def url(r):
    if r["pdm_url"]: return r["pdm_url"]
    if r["osm_id"]:
        i = r["osm_id"].split()[0]; return "https://www.openstreetmap.org/%s/%s" % ({"n": "node", "w": "way", "r": "relation"}[i[0]], i[1:])
    if r["qid"]: return "https://www.wikidata.org/wiki/" + r["qid"]
    if r["file"]: return "https://commons.wikimedia.org/wiki/" + r["file"].replace(" ", "_")
    return ""
pts_out = [[r["id"], r["nome"] or "(senza nome)", cats.index(r["categoria"]), r["soggetto"], r["genere"], int(r["anno"]) if r["anno"].isdigit() else None, r["NIL"], r["fonte"], url(r), " · ".join(r["posa"]), float(r["lon"]), float(r["lat"])]
           for r in rows if r["lat"]]
json.dump({"colonne": mcols + ["lon", "lat"], "categorie": cats, "punti": pts_out}, open(os.path.join(DOC, "targhe_mappa.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(out, open(os.path.join(DOC, "pagina.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
for fn in ["targhe.csv", "persone.csv", "per_nil.csv"]: shutil.copy(os.path.join(OUT, fn), os.path.join(DOC, fn))
open(os.path.join(DOC, "LICENZE.txt"), "w", encoding="utf8").write(
"""Milano in dati - Lapidi e targhe: licenze dei file in questa cartella
Dati scaricati il 1 e 2 novembre 2026.

- Pietre della Memoria (ANMIG e Fondazione ANMIG, pietredellamemoria.it): campi fattuali (titolo, tipo, indirizzo, coordinate, luogo e data di collocazione,
  ente preposto, testo inciso sulla targa) usati con l'autorizzazione di ANMIG dichiarata dal curatore del progetto. Citare sempre "Pietre della Memoria, ANMIG".
  Non sono copiati ne' le foto ne' i testi delle biografie scritti dai volontari. Per riusare questi campi in altri progetti: chiedere ad ANMIG.
- Dati derivati da OpenStreetMap (nomi, posizioni, testi delle iscrizioni, anni): (c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0.
  Chi riusa o ripubblica questi file deve citare la fonte e distribuire i dati derivati con la stessa licenza (share-alike). https://www.openstreetmap.org/copyright
- Dati ricavati da Wikidata (nomi delle targhe, persone, sesso, mestieri): CC0 (pubblico dominio).
- Wikimedia Commons: solo metadati (titolo del file, coordinate) di alcune foto, con il link alla pagina del file; nessuna immagine copiata. Le singole foto hanno ciascuna la propria licenza.
- Confini dei NIL e nomi dei quartieri: Comune di Milano, CC BY (dati.comune.milano.it, ds964).
- Il file targhe.csv unisce le fonti: la colonna "fonte" dice da dove viene ogni riga (osm, wikidata, pdm, commons, anche insieme). Per le righe con OSM vale ODbL (share-alike).
- I programmi e le note sono nel repository del progetto.
""")
print("targhe", n, dict(fonte), "con coordinate", con_coord, "di cui PdM nuove", len(pdm_nuove), "unite", overlap_pdm_free, "commons", len(com))
print("categorie", dict(cat))
print("persone", out["persone"]["uniche"], "donne", nd, "su", len(noti), "resistenza", len(res), "posatori", out["posatori"]["elenco"])
