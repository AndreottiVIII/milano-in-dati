"""Copertura SBN per anno e confronto con Wikipedia (pulito/_wp_stagioni.csv, solo lettura).
Scrive sbn/copertura_sbn.csv e sbn/confronto_wikipedia.csv"""
import os, csv, re, collections, difflib, unicodedata
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "sbn")
rows = list(csv.DictReader(open(os.path.join(OUT, "sbn_programmi.csv"), encoding="utf-8-sig")))
wp = list(csv.DictReader(open(os.path.join(ROOT, "pulito", "_wp_stagioni.csv"), encoding="utf-8")))

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\b(il|lo|la|le|i|gli|l|un|una|the|die|der|das|les|des|le|di|del|della|dei|e)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

ALIAS = {"crepuscolo degli dei": "gotterdammerung", "tristano isotta": "tristan isolde", "walkure": "walkure", "walchiria": "walkure", "walkiria": "walkure",
         "pikovaja dama": "dama picche", "guglielmo tell": "guillaume tell", "siegfried": "siegfried", "oro del reno": "rheingold", "aroldo": "aroldo"}
def normA(s):
    n = norm(s)
    for k, v in ALIAS.items():
        if k in n: n = n.replace(k, v)
    return n

def cognome(c):
    c = norm(c.split(";")[0].split(",")[0]) if c else ""
    # "giuseppe verdi" -> verdi ; "Verdi, Giuseppe" gestito sotto
    return c.split()[-1] if c else ""

prod = [r for r in rows if r["tipo"] in ("produzione", "ospiti")]
prod_cmp = prod + [r for r in rows if r["tipo"] == "da_verificare"]
# --- copertura per anno ---
by = collections.defaultdict(lambda: collections.Counter())
titoli = collections.defaultdict(set)
for r in rows:
    y = int(r["anno"]); by[y][r["tipo"]] += 1
    if r["tipo"] in ("produzione", "ospiti"):
        titoli[y].add(norm(r["titolo"])[:40])
wp_per_anno = collections.Counter()
for r in wp:
    if r["anno"].isdigit(): wp_per_anno[int(r["anno"])] += 1
with open(os.path.join(OUT, "copertura_sbn_per_anno.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["anno_stampa", "programmi_produzione", "titoli_distinti_opera_balletto", "ospiti", "concerti", "libretti_stagione", "tournee",
                "con_direttore", "con_regista_o_coreografo", "con_interpreti", "wikipedia_titoli_stesso_anno"])
    for y in range(1963, 2025):
        c = by[y]
        pr = [r for r in prod if int(r["anno"]) == y]
        w.writerow([y, c["produzione"], len(titoli[y]), c["ospiti"], c["concerto"], c["stagione"], c["tournee"],
                    sum(1 for r in pr if r["direttore"]), sum(1 for r in pr if r["regista"] or r["coreografo"]),
                    sum(1 for r in pr if r["interpreti"]), wp_per_anno[y]])

# --- copertura per stagione ---
def stag_of(y): return f"{y}-{str(y+1)[2:]}"
ass = collections.defaultdict(list); senza = collections.Counter()
for r in prod:
    if r["stagione"]: ass[r["stagione"]].append(r)
    else: senza[int(r["anno"])] += 1
conc = collections.Counter(r["stagione"] for r in rows if r["tipo"] == "concerto" and r["stagione"])
lib = collections.Counter(r["stagione"] for r in rows if r["tipo"] == "stagione" and r["stagione"])
wps = collections.Counter()
for r in wp:
    m = re.match(r"(\d{4})-(\d{2})", r["data"] or "")
    if m:
        y, mo = int(m.group(1)), int(m.group(2)); wps[stag_of(y if mo >= 9 else y - 1)] += 1
with open(os.path.join(OUT, "copertura_sbn.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["stagione", "produzioni_con_stagione_nota", "titoli_distinti", "stima_totale_con_quelle_senza_stagione", "ospiti_inclusi", "concerti_con_stagione", "libretti_stagione", "con_direttore", "con_regista_o_coreografo", "wikipedia_titoli"])
    for y in range(1963, 2024):
        S = stag_of(y); g = ass[S]
        stima = len(g) + 0.5 * senza[y] + 0.5 * senza[y + 1]
        w.writerow([S, len(g), len({norm(r["titolo"])[:40] for r in g}), round(stima, 1), sum(1 for r in g if r["tipo"] == "ospiti"), conc[S], lib[S],
                    sum(1 for r in g if r["direttore"]), sum(1 for r in g if r["regista"] or r["coreografo"]), wps[S]])

# --- confronto con Wikipedia ---
def anni_ammessi(data):
    m = re.match(r"(\d{4})-(\d{2})", data or "")
    if not m: return None
    y, mo = int(m.group(1)), int(m.group(2))
    return {y - 1, y} if mo <= 6 else {y, y + 1}

def match(titolo_wp, comp_wp, anni):
    nt = normA(titolo_wp); cg = cognome(comp_wp)
    best = ("", 0.0, "nessuno")
    for r in prod_cmp:
        if int(r["anno"]) not in anni: continue
        ns = normA(r["titolo"]); blob = normA(r["titolo_originale"])
        if nt and (nt == ns or (len(nt) > 3 and nt in blob)):
            return r, 1.0, "titolo"
        ratio = difflib.SequenceMatcher(None, nt, ns).ratio() if nt and ns else 0
        if ratio > best[1] and ratio >= 0.8: best = (r, ratio, "titolo_simile")
        if cg and len(cg) > 3 and cg in blob and best[2] == "nessuno":
            best = (r, 0.5, "solo_compositore")
    return best

out = []
for r in wp:
    if not r["anno"].isdigit() or int(r["anno"]) < 1963: continue
    anni = anni_ammessi(r["data"])
    if not anni: continue
    apertura = r["data"].endswith("-12-07")
    # gruppo di controllo: apertura di ogni anno + tutte le righe delle stagioni 2011-2015 e 2022-2024 (elenchi lunghi)
    y = int(r["anno"])
    if not (apertura or 2011 <= y <= 2015 or y >= 2022): continue
    m, score, tipo = match(r["titolo"], r["compositore"], anni)
    out.append([r["anno"], r["data"], "apertura" if apertura else "stagione", r["titolo"], r["compositore"],
                tipo, f"{score:.2f}" if m else "", m["titolo"] if m else "", m["anno"] if m else "", m["bid"] if m else ""])
with open(os.path.join(OUT, "confronto_wikipedia.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["wp_anno", "wp_data", "gruppo", "wp_titolo", "wp_compositore", "esito", "somiglianza", "sbn_titolo", "sbn_anno", "sbn_bid"])
    w.writerows(out)
cnt = collections.Counter((o[2], o[5]) for o in out)
print(dict(cnt))
