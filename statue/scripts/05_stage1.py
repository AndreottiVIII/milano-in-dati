"""Fase 1 della pulizia: unisce Wikidata, OpenStreetMap e ICCD in un elenco di opere (senza ancora cercare i soggetti non collegati).
Uso: python -I -X utf8 05_stage1.py <statue> <milano-in-dati>
Scrive pulito/_lavoro/stage1.json e pulito/_lavoro/stage1_log.json"""
import sys, os, re, json, math, collections
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Transformer
S, P = sys.argv[1:3]
sys.path.insert(0, os.path.join(S, "scripts"))
from wdlib import WD, norm
wd = WD(os.path.join(S, "raw/wikidata/entities_cache.json"))
LOG = {}
os.makedirs(os.path.join(S, "pulito/_lavoro"), exist_ok=True)

# ---------- NIL
g = json.load(open(os.path.join(P, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
NIL_ID = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
NIL_NAME = [f["properties"]["NIL"] for f in g["features"]]
tree = STRtree(polys)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
polys_m = [shapely.transform(p, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for p in polys]
tree_m = STRtree(polys_m)
def nil_of(lon, lat):
    """-> (id, nome, stato) stato: dentro | entro100m | fuori"""
    pt = shapely.Point(lon, lat)
    hit = tree.query(pt, predicate="within")
    if len(hit): return NIL_ID[hit[0]], NIL_NAME[hit[0]], "dentro"
    x, y = tr.transform(lon, lat)
    i, d = tree_m.query_nearest(shapely.Point(x, y), return_distance=True)
    if d[0] <= 100: return NIL_ID[i[0]], NIL_NAME[i[0]], "entro100m"
    return None, "", "fuori"
def dist_m(a, b):
    x1, y1 = tr.transform(*a); x2, y2 = tr.transform(*b)
    return math.hypot(x1 - x2, y1 - y2)

# ---------- classi Wikidata
CLASS_TIPO = {
 "Q860861": "scultura o installazione", "Q179700": "statua", "Q241045": "busto", "Q2293362": "scultura o installazione", "Q245117": "scultura o installazione", "Q14562306": "scultura o installazione",
 "Q20437094": "scultura o installazione", "Q19479037": "scultura o installazione", "Q9325291": "scultura o installazione", "Q29168169": "statua", "Q134082204": "statua", "Q572916": "scultura o installazione",
 "Q123079143": "scultura o installazione", "Q838948": "scultura o installazione",
 "Q4989906": "monumento", "Q5003624": "monumento", "Q575759": "monumento ai caduti", "Q114124381": "monumento ai caduti", "Q64374896": "monumento ai caduti", "Q20011797": "monumento", "Q1885014": "monumento",
 "Q125727479": "monumento", "Q143912": "monumento", "Q3683544": "cippo, stele o pietra", "Q11734477": "cippo, stele o pietra", "Q1752223": "cippo, stele o pietra", "Q178743": "cippo, stele o pietra",
 "Q721747": "lapide o targa", "Q203443": "lapide o targa", "Q123223970": "lapide o targa",
 "Q483453": "fontana",
 "Q56055312": "monumento funebre o tomba", "Q381885": "monumento funebre o tomba", "Q173387": "monumento funebre o tomba", "Q321053": "monumento funebre o tomba", "Q162875": "monumento funebre o tomba",
 "Q192619": "monumento funebre o tomba", "Q6023295": "monumento funebre o tomba", "Q3738842": "monumento funebre o tomba",
 "Q106071447": "murale o opera decorativa",
}
EXCL = {"Q82117", "Q41176", "Q16560", "Q1364150", "Q108325", "Q16970", "Q19860854", "Q1137365", "Q188507", "Q259209", "Q1241568", "Q14750991", "Q15255892", "Q623106", "Q1650313", "Q722604", "Q116958504",
        "Q389959", "Q274153", "Q80793", "Q1406758", "Q392371", "Q21167233", "Q657100", "Q1497364", "Q23418", "Q854429", "Q4306024", "Q1076486", "Q3395121", "Q1497375", "Q187833", "Q4265944", "Q36794", "Q16887380", "Q750778"}
PRIO = ["statua", "busto", "monumento ai caduti", "lapide o targa", "cippo, stele o pietra", "fontana", "monumento", "scultura o installazione", "murale o opera decorativa", "monumento funebre o tomba"]

def tipo_refine(tipo, label):
    l = (label or "").lower()
    if tipo in ("monumento", "scultura o installazione", "altro memoriale"):
        if re.search(r"\bbust[oi]\b", l): return "busto"
        if re.search(r"\bstatu[ae]\b", l): return "statua"
        if re.search(r"\b(lapide|targa)\b", l): return "lapide o targa"
        if re.search(r"caduti|\bwar memorial\b|monumento alla resistenza|ai martiri", l): return "monumento ai caduti"
        if re.search(r"\bfontana\b", l): return "fontana"
        if re.search(r"\b(cippo|stele|obelisco)\b", l): return "cippo, stele o pietra"
    return tipo

# ---------- date
def year_from_osm(s):
    if not s: return None
    m = re.match(r"^\s*(\d{4})(?:-\d{2}(?:-\d{2})?)?\s*$", s)
    if m: return int(m.group(1))
    m = re.match(r"^\s*(\d{4})\s*(?:;|\.\.)", s)
    if m: return int(m.group(1))
    return None
def year_wd(q):
    ts = wd.times(q, "P571")
    ys = sorted({y for y, p in ts if p >= 9})
    return (ys[0] if ys else None), bool(ts and not ys)

def contesto(cids, label):
    """dove sta l'opera, dedotto dai contenitori di Wikidata (P131, P276, P361): guarda il tipo (P31) del contenitore, non solo il nome"""
    if re.search(r"all'interno|interno|nel duomo|nella chiesa|nel museo", label.lower()): return "chiesa o interno"
    for c in cids:
        tp = " ; ".join(wd.lab(x) for x in wd.ids(c, "P31")).lower()
        if re.search(r"piazza|strada|parco|giardin|isola pedonale|sagrato|quartiere|comune|citt|municipio|capoluogo", tp) or wd.lab(c).lower().startswith(("piazza", "via ", "viale", "largo", "corso", "sagrato")): continue
        t = (wd.lab(c) + " ; " + tp).lower()
        if re.search(r"cimitero|famedio|cappella funeraria|sepolcr", t): return "cimitero"
        if re.search(r"chiesa|basilica|cattedrale|abbazia|santuario|battistero|monastero|convento|oratorio|cappella|certosa|duomo di milano", t): return "chiesa o interno"
        if re.search(r"museo|castello|palazzo|pinacoteca|biblioteca|teatro|villa|universit|collezione|galleria d|casa museo", t): return "museo o edificio"
    return ""

works = []
# ---------- Wikidata
base = set()
for n in ["A_p131", "B_box"]:
    for r in json.load(open(os.path.join(S, f"raw/wikidata/{n}.json"), encoding="utf8"))["results"]["bindings"]:
        base.add(r["item"]["value"].rsplit("/", 1)[-1])
LOG["wd_qid_trovati_da_sparql"] = len(base)
drop = collections.Counter()
wd_works = {}
for q in sorted(base, key=lambda x: int(x[1:])):
    e = wd.C.get(q)
    if not e or "missing" in e: drop["entita_mancante"] += 1; continue
    p31 = wd.ids(q, "P31")
    tt = [CLASS_TIPO[c] for c in p31 if c in CLASS_TIPO]
    if not tt: drop["nessuna_classe_ammessa"] += 1; continue
    if set(p31) & EXCL: drop["anche_edificio_o_altro_escluso"] += 1; continue
    label = wd.lab(q)
    tipo = min(tt, key=PRIO.index)
    tipo = tipo_refine(tipo, label)
    co = wd.coord(q)
    nil = (None, "", "")
    if co:
        nil = nil_of(*co)
        if nil[2] == "fuori": drop["coordinate_fuori_dal_comune"] += 1; continue
    else:
        loc = wd.ids(q, "P131")
        if not any(x == "Q490" or "Milano" in wd.lab(x) or "Municipio" in wd.lab(x) for x in loc):
            drop["senza_coordinate_e_P131_non_milanese"] += 1; continue
    y, nota = year_wd(q)
    cont_l = [wd.lab(x) for x in wd.ids(q, "P131") + wd.ids(q, "P276") + wd.ids(q, "P361")]
    subj = []
    for p in ("P180", "P547", "P921"):
        for s_ in wd.ids(q, p):
            if s_ not in subj: subj.append(s_)
    w = dict(src=["wikidata"], qid=q, osm=[], iccd=[], nome=label, tipo=tipo, tipo_wd=[wd.lab(c) for c in p31],
             lon=co[0] if co else None, lat=co[1] if co else None, nil_id=nil[0], nil=nil[1], nil_stato=nil[2],
             anno=y, anno_nota=("data imprecisa (decennio o secolo)" if nota else ""), anno_fonte="wikidata P571" if y else "",
             autori=[wd.lab(c) for c in wd.ids(q, "P170")], autori_qid=wd.ids(q, "P170"), subj_struct=subj, subj_fonte=["wikidata P180/P547/P921"] if subj else [],
             contesto=contesto(wd.ids(q, "P131") + wd.ids(q, "P276") + wd.ids(q, "P361"), label), contenitori=cont_l, descr=wd.desc(q))
    wd_works[q] = w
    works.append(w)
LOG["wd_scartati"] = dict(drop)
LOG["wd_tenuti"] = len(wd_works)

# ---------- OSM
osm = json.load(open(os.path.join(S, "raw/osm/overpass_statue.json"), encoding="utf8"))
LOG["osm_timestamp"] = osm["osm3s"]["timestamp_osm_base"]
LOG["osm_elementi"] = len(osm["elements"])
odrop = collections.Counter()
def osm_tipo(t):
    mem, art, h = t.get("memorial"), t.get("artwork_type"), t.get("historic")
    nm = (t.get("name") or "").lower()
    if mem == "stolperstein": return "pietra d'inciampo"
    if mem == "ghost_bike": return "bicicletta bianca"
    if mem == "plaque": return "lapide o targa"
    if mem == "war_memorial" or "caduti" in nm or "war_memorial" in (t.get("monument") or ""): return "monumento ai caduti"
    if mem == "bust" or art == "bust": return "busto"
    if mem == "statue" or art == "statue": return "statua"
    if mem in ("sculpture",) or art in ("sculpture", "installation"): return "scultura o installazione"
    if mem in ("stele", "stone", "obelisk", "cross") or art in ("stone", "monolite", "column"): return "cippo, stele o pietra"
    if art in ("mural", "graffiti", "painting", "mosaic", "tilework", "azulejo", "architecture"): return "murale o opera decorativa"
    if h == "wayside_cross": return "cippo, stele o pietra"
    if h == "monument": return "monumento"
    if t.get("tourism") == "artwork": return "scultura o installazione"
    return "altro memoriale"
osm_works = []
for e in osm["elements"]:
    t = e["tags"]
    lon, lat = (e["lon"], e["lat"]) if e["type"] == "node" else (e["center"]["lon"], e["center"]["lat"])
    tipo = osm_tipo(t)
    if tipo in ("pietra d'inciampo", "bicicletta bianca"):
        odrop[tipo] += 1; continue
    nil = nil_of(lon, lat)
    if nil[2] == "fuori": odrop["fuori_dal_comune"] += 1; continue
    name = t.get("name") or t.get("name:it") or ""
    tipo = tipo_refine(tipo, name)
    subj = []
    for k_ in ("subject:wikidata", "memorial:subject:wikidata", "commemorates:wikidata", "buried:wikidata"):
        for v in t.get(k_, "").split(";"):
            if re.fullmatch(r"Q\d+", v.strip()) and v.strip() not in subj: subj.append(v.strip())
    wq = [v.strip() for v in t.get("wikidata", "").split(";") if re.fullmatch(r"Q\d+", v.strip())]
    aq = [v.strip() for v in t.get("artist:wikidata", "").split(";") if re.fullmatch(r"Q\d+", v.strip())]
    anno = year_from_osm(t.get("start_date"))
    autori = [x.strip() for x in (t.get("artist_name") or "").split(";") if x.strip()]
    ctx = "museo o edificio" if (t.get("indoor") == "yes" or t.get("level") not in (None, "0")) else ""
    w = dict(src=["osm"], qid=None, osm=[e["type"][0] + str(e["id"])], iccd=[], nome=name, tipo=tipo, tipo_wd=[], lon=lon, lat=lat, nil_id=nil[0], nil=nil[1], nil_stato=nil[2],
             anno=anno, anno_nota="", anno_fonte="osm start_date" if anno else "", autori=autori, autori_qid=aq, subj_struct=subj, subj_fonte=["osm subject:wikidata"] if subj else [],
             contesto=ctx, contenitori=[], descr=(t.get("inscription") or t.get("description") or "")[:300],
             osm_tags={k: t[k] for k in ("memorial", "historic", "artwork_type", "subject", "wikidata", "inscription", "material", "start_date") if k in t}, wd_tag=wq)
    osm_works.append(w)
LOG["osm_scartati"] = dict(odrop)
LOG["osm_tenuti"] = len(osm_works)

# ---------- unione OSM -> Wikidata
STOP = set("monumento statua busto lapide targa cippo stele memoriale commemorativa commemorativo caduti guerra piazza via viale largo piazzale giardini parco giardino della del dello dei degli delle alla alle agli all ad per con fontana scultura opera sul sulla porta corso milano san santa sant santo qui".split())
def toks(s): return {t for t in norm(s).split() if len(t) >= 4 and t not in STOP}
merged_qid = merged_sp = 0
for w in osm_works:
    done = False
    for q in w["wd_tag"]:
        if q in wd_works:
            tgt = wd_works[q]
        elif wd.is_human(q):
            w["subj_struct"].append(q); w["subj_fonte"].append("osm wikidata (persona)"); continue
        else:
            # un elemento Wikidata fuori dalla nostra selezione (es. Arco della Pace): lo usiamo per autore, anno, soggetto
            if q in wd.C and "missing" not in wd.C[q]:
                w["qid"] = q
                for c in wd.ids(q, "P170"):
                    if c not in w["autori_qid"]: w["autori_qid"].append(c); w["autori"].append(wd.lab(c))
                y, nota = year_wd(q)
                if y and not w["anno"]: w["anno"], w["anno_fonte"] = y, "wikidata P571"
                if not w["nome"]: w["nome"] = wd.lab(q)
                for p in ("P180", "P547", "P921"):
                    for s_ in wd.ids(q, p):
                        if s_ not in w["subj_struct"]: w["subj_struct"].append(s_); w["subj_fonte"].append("wikidata P180/P547/P921")
            continue
        tgt["osm"] += w["osm"]; tgt["src"] = sorted(set(tgt["src"]) | {"osm"})
        for s_ in w["subj_struct"]:
            if s_ not in tgt["subj_struct"]: tgt["subj_struct"].append(s_); tgt["subj_fonte"].append("osm subject:wikidata")
        if tgt["lon"] is None: tgt.update(lon=w["lon"], lat=w["lat"], nil_id=w["nil_id"], nil=w["nil"], nil_stato=w["nil_stato"])
        if not tgt["anno"] and w["anno"]: tgt["anno"], tgt["anno_fonte"] = w["anno"], w["anno_fonte"]
        if not tgt["autori"] and w["autori"]: tgt["autori"] = w["autori"]
        tgt["osm_tags"] = w["osm_tags"]
        done = True; merged_qid += 1; break
    w["_done"] = done
rest = [w for w in osm_works if not w.get("_done")]
wlist = [w for w in works if w["lon"] is not None]
for w in rest:
    tw = toks(w["nome"])
    best = None
    if tw:
        for v in wlist:
            if v["tipo"] == "monumento funebre o tomba": continue
            d = dist_m((w["lon"], w["lat"]), (v["lon"], v["lat"]))
            if d <= 60 and tw & toks(v["nome"]):
                if best is None or d < best[0]: best = (d, v)
    if best:
        v = best[1]; v["osm"] += w["osm"]; v["src"] = sorted(set(v["src"]) | {"osm"}); merged_sp += 1
        for s_ in w["subj_struct"]:
            if s_ not in v["subj_struct"]: v["subj_struct"].append(s_); v["subj_fonte"].append("osm subject:wikidata")
        if not v["anno"] and w["anno"]: v["anno"], v["anno_fonte"] = w["anno"], w["anno_fonte"]
        if not v["autori"] and w["autori"]: v["autori"] = w["autori"]
        v["osm_tags"] = w["osm_tags"]
    else:
        works.append(w)
LOG["osm_unite_a_wikidata_per_qid"] = merged_qid
LOG["osm_unite_a_wikidata_per_vicinanza_e_nome"] = merged_sp

# ---------- ICCD
ic = pd.read_csv(os.path.join(P, "beni-culturali/pulito/beni_milano.csv"), dtype=str, low_memory=False).fillna("")
ic = ic[ic.sede_milano == "1"]
LOG["iccd_schede_milano"] = len(ic)
ic["lat_f"] = pd.to_numeric(ic.lat, errors="coerce"); ic["lon_f"] = pd.to_numeric(ic["long"], errors="coerce")
hub = ic.dropna(subset=["lat_f"]).groupby(["lat_f", "lon_f"]).size()
hub = set(hub[hub >= 10].index)
TY = {"monumento ai caduti": "monumento ai caduti", "monumento": "monumento", "cippo": "cippo, stele o pietra", "stele": "cippo, stele o pietra", "targa": "lapide o targa",
      "lapide commemorativa": "lapide o targa", "lapide celebrativa": "lapide o targa", "lapide documentaria": "lapide o targa", "busto": "busto", "statua": "statua", "gruppo scultoreo": "scultura o installazione"}
tl = ic.tipo_oggetto.str.lower()
cand = ic[tl.isin(TY)].copy()
LOG["iccd_schede_dei_tipi_cercati"] = len(cand)
LOG["iccd_per_tipo"] = tl[tl.isin(TY)].value_counts().to_dict()
idrop = collections.Counter(); inc = []
for r in cand.itertuples():
    if r.istituzione != "non indicata": idrop["con_istituzione_detentrice"] += 1; continue
    if pd.isna(r.lat_f): idrop["senza_coordinate"] += 1; continue
    if (r.lat_f, r.lon_f) in hub: idrop["coordinate_di_museo_o_deposito(>=10 schede)"] += 1; continue
    if r.coord_in_comune != "1": idrop["coordinate_fuori_comune"] += 1; continue
    nil = nil_of(r.lon_f, r.lat_f)
    ty = TY[r.tipo_oggetto.lower()]
    if r.tipo_oggetto.lower() == "monumento" and r.titolo.strip().lower() == "monumento": idrop["monumento_senza_titolo"] += 1; continue
    nome = re.sub(r"\s*\([^)]*\)\s*$", "", r.titolo).strip()
    ys = int(r.anno_inizio) if r.anno_inizio.lstrip("-").isdigit() else None
    inc.append(dict(src=["iccd"], qid=None, osm=[], iccd=[r.iri], nome=nome, tipo=tipo_refine(ty, nome), tipo_wd=[], lon=r.lon_f, lat=r.lat_f, nil_id=nil[0], nil=nil[1], nil_stato=nil[2],
                    anno=ys, anno_nota="", anno_fonte="iccd datazione" if ys else "", autori=[a for a in r.autori.split(" | ") if a], autori_qid=[], subj_struct=[], subj_fonte=[],
                    contesto="", contenitori=[], descr=r.soggetto, iccd_url=r.url_catalogo, iccd_indirizzo=r.luogo_attuale))
LOG["iccd_scartati"] = dict(idrop); LOG["iccd_candidati_tenuti"] = len(inc)
merged_ic = 0
allw = [w for w in works if w["lon"] is not None]
for w in inc:
    tw = toks(w["nome"]) | toks(w["descr"])
    best = None
    for v in allw:
        if v["tipo"] == "monumento funebre o tomba": continue
        d = dist_m((w["lon"], w["lat"]), (v["lon"], v["lat"]))
        if (d <= 150 and (tw & toks(v["nome"]))) or (d <= 60 and v["tipo"] == w["tipo"] == "monumento ai caduti"):
            if best is None or d < best[0]: best = (d, v)
    if best:
        v = best[1]; v["iccd"] += w["iccd"]; v["src"] = sorted(set(v["src"]) | {"iccd"}); merged_ic += 1
        if not v["anno"] and w["anno"]: v["anno"], v["anno_fonte"] = w["anno"], w["anno_fonte"]
        if not v["autori"] and w["autori"]: v["autori"] = w["autori"]
    else:
        works.append(w)
LOG["iccd_unite_a_opere_esistenti"] = merged_ic
LOG["opere_totali_dopo_unione"] = len(works)
LOG["per_fonte"] = dict(collections.Counter("+".join(sorted(w["src"])) for w in works))
for i, w in enumerate(works, 1): w["id"] = f"MI{i:04d}"
for w in works: w.pop("_done", None)
json.dump(works, open(os.path.join(S, "pulito/_lavoro/stage1.json"), "w", encoding="utf8"), ensure_ascii=False)
json.dump(LOG, open(os.path.join(S, "pulito/_lavoro/stage1_log.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(LOG, ensure_ascii=False, indent=1))
