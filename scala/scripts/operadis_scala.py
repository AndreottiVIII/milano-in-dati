"""Operadis/CLOR (discografia di opere in commercio, ferma al 2009): estrae le registrazioni con orchestra o coro 'Teatro alla Scala'
(anno, tipo LI=dal vivo, direttore, cast, data se scritta nei commenti). Solo come CONTROLLO INCROCIATO, locale.
Controlli fatti 30/10/2026: robots.txt vieta solo SemrushBot e MJ12bot; nessuna condizione d'uso scritta; 1 richiesta ogni 3 s, cache in raw/discografie/operadis/.
Uso (dalla cartella scala/): python -I -X utf8 scripts/operadis_scala.py   (riprendibile)"""
import sys, os, re, csv, time, html, urllib.request, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(ROOT, "raw", "discografie", "operadis"); os.makedirs(CACHE, exist_ok=True)
BASE = "https://www.operadis-opera-discography.org.uk/"
UA = "milano-in-dati research project (davide.caniatti@gmail.com; controllo incrociato, 1 richiesta ogni 3 s)"
last = [0.0]
def pagina(nome):
    p = os.path.join(CACHE, nome)
    if os.path.exists(p): return open(p, encoding="latin-1").read()
    w = 3 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    last[0] = time.time()
    for k in range(3):
        try:
            data = urllib.request.urlopen(urllib.request.Request(BASE + nome, headers={"User-Agent": UA}), timeout=90).read()
            open(p, "wb").write(data); return data.decode("latin-1")
        except Exception as e:
            print("errore", nome, e, flush=True); time.sleep(20 * (k + 1))
    return ""
def testo(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t.replace("\r", "")))
    t = re.sub(r"[ \t\xa0]+", " ", t); return re.sub(r"\n\s*\n+", "\n", t)
home = pagina("OPERADIS.HTM")
compositori = sorted(set(re.findall(r'HREF\s*=\s*"?(CLOR[A-Z]+\.HTM)', home, re.I)) - {"CLORLINK.HTM"})
print("pagine compositore:", len(compositori), flush=True)
opere = []
for c in compositori:
    t = pagina(c)
    for m in re.finditer(r'<A HREF\s*=\s*"(CL[A-Z]{2}[A-Z0-9]+\.HTM)"\s*>\s*([^<]+)</A>', t, re.I):
        if m.group(1).upper() not in [o[0] for o in opere] and not m.group(1).upper().startswith("CLOR"):
            opere.append((m.group(1).upper(), html.unescape(m.group(2)).strip(), c))
PRIO = ["CLORVERD", "CLORPUCC", "CLORROSS", "CLORDONI", "CLORBELL", "CLORMOZA", "CLORWAGN", "CLORSTRA", "CLORGIOR", "CLORMASC", "CLORLEON", "CLORCHER", "CLORGLUC",
        "CLORCILE", "CLORPONC", "CLORBOIT", "CLORTCHA", "CLORMUSS", "CLORBIZE", "CLORGOUN", "CLORMASS", "CLORBEET", "CLORZAND", "CLORPACI", "CLORMONT", "CLORPROK", "CLORBARTO"]
def prio(o):
    c = o[2].upper().replace(".HTM", "")
    return PRIO.index(c) if c in PRIO else len(PRIO)
opere.sort(key=prio)   # prima i compositori piu' frequenti alla Scala (la cache rende il riavvio gratuito)
print("pagine opera:", len(opere), flush=True)
righe = []
for i, (f, titolo, c) in enumerate(opere):
    t = pagina(f)
    if i % 25 == 0: print(f"{i}/{len(opere)}", flush=True)
    if not t: continue
    tx = testo(t)
    m0 = re.search(r"\n\s*(.+?) by (.+?) performed in", tx)
    comp = ""
    mc = re.search(r"recordings of (.+?) by (.+?) on file", tx)
    if mc: titolo, comp = mc.group(1).strip(), mc.group(2).strip()
    blocchi = re.split(r"\*{20,}", tx)
    for b in blocchi:
        if not re.search(r"Teatro alla Scala|La Scala", b): continue
        mdir = re.search(r"Conductor (.+?) - (\d{4}[^\n]*)", b)
        if not mdir: continue
        scala_orch = bool(re.search(r"(Orchestra|Chorus|Orchestra and Chorus|Orchestra & Chorus) - Teatro alla Scala", b))
        comm = ""
        mcm = re.search(r"Comments:-(.*?)(?:\n\s*Top|\Z)", b, re.S)
        if mcm: comm = re.sub(r"\s+", " ", mcm.group(1)).strip()
        dates = re.findall(r"\b(\d{1,2}(?:[/ .-]\d{1,2}[/ .-]\d{2,4}|\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}))", mdir.group(2) + " " + comm)
        cast = re.findall(r"\n\s*([^\n]{2,60}?) - ([^\n]{2,60})", b[mdir.end():b.find("------", mdir.end()) if "------" in b else None])
        cast = [f"{a.strip()}: {n.strip()}" for a, n in cast if not re.match(r"(Orchestra|Chorus)", a)]
        anno = re.match(r"\d{4}", mdir.group(2)).group(0)
        tipo = (re.search(r"\(([A-Z]{2,3})[;)]", mdir.group(2)) or [None, ""])[1]
        righe.append(dict(opera=titolo, compositore=comp, anno=anno, tipo_registrazione=tipo, orchestra_scala="si" if scala_orch else "citata_nei_commenti",
                          dichiarato_alla_scala="si" if re.search(r"(performance|recorded|recording|concert)[^.]{0,40}at La Scala|at the Teatro alla Scala|La Scala,? Milan", comm + " " + mdir.group(2), re.I) else "",
                          direttore=mdir.group(1).strip(), dettaglio_riga=mdir.group(2).strip(), date_scritte="; ".join(dict.fromkeys(dates)),
                          cast=" | ".join(cast), commento=comm[:400], pagina=f))
with open(os.path.join(ROOT, "raw", "discografie", "operadis_scala.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(righe[0].keys())); w.writeheader(); w.writerows(righe)
print("registrazioni con Scala:", len(righe), collections.Counter(r["tipo_registrazione"] for r in righe).most_common(8), flush=True)
print("FINE", flush=True)
