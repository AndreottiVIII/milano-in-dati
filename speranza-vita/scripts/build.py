"""Fase 1 - passo 1: costruisce le tabelle pulite di base.
Uso: python -I -X utf8 build.py <speranza-vita_dir> <milano-in-dati_dir>   (percorsi assoluti, si puo' rilanciare)
Legge (file non fidati, solo come dati):
  raw/comune_ds137  decessi dei residenti per quartiere (NIL) x genere x cittadinanza, 2003-2020  (Comune di Milano, CC BY)
  raw/comune_ds1940 idem 2021-2024
  raw/comune_ds1938 decessi dei residenti per genere x classe di eta', 2021-2024 (solo controllo)
  ../popolazione/pulito/residenti_nil_anno_eta_genere.csv  residenti al 31/12, NIL x eta' x genere, 1999-2025 (Comune, ds27)
  ../popolazione/pulito/nil_anagrafica.csv
  ../morti/pulito/decessi_giorno_eta_sesso.csv  decessi ISTAT per eta'/sesso, Milano (residenza), 2011-2026
Scrive in pulito/: decessi_nil_anno_genere.csv, residenti_nil_anno_cl_genere.csv, decessi_citta_anno_cl_sesso.csv, controlli_build.json
Classi di eta' ISTAT (cl_eta 0..21): 0 = 0 anni, 1 = 1-4, c>=2 = 5(c-1)..5(c-1)+4, 21 = 100+.
"""
import sys, os, csv, json, re, unicodedata, collections
SV, P = sys.argv[1], sys.argv[2]
PU = os.path.join(SV, "pulito"); os.makedirs(PU, exist_ok=True)
def norm(s):
    s = unicodedata.normalize("NFKD", s); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())
ana = list(csv.DictReader(open(os.path.join(P, "popolazione", "pulito", "nil_anagrafica.csv"), encoding="utf8")))
BYN = {norm(r["nil"]): int(r["id_nil"]) for r in ana}
def nil_id(name):
    k = norm(name)
    if k in BYN: return BYN[k]
    c = [v for kk, v in BYN.items() if kk.startswith(k)]   # nomi troncati a 50 caratteri nei file del Comune
    return c[0] if len(c) == 1 and len(k) >= 25 else None
CTRL = {}
rows = []; non = collections.Counter()
for f, col in [("comune_ds137/ds137-popolazione-residenti-decessi-quartiere.csv", "Numerosita"), ("comune_ds1940/ds1940_popolazione-residenti-decessi-quartiere.csv", "Numerosità")]:
    for r in csv.DictReader(open(os.path.join(SV, "raw", f), encoding="utf-8-sig"), delimiter=";"):
        q = r["Quartiere"].strip(); n = int(r[col]); y = int(r["Anno_evento"])
        i = nil_id(q) if q else None
        if i is None: non[(y, q or "(vuoto)")] += n; continue
        rows.append((y, i, "M" if r["Genere"] == "Maschi" else "F", r["Cittadinanza_deceduto"], n))
agg = collections.defaultdict(lambda: [0, 0])
for y, i, s, c, n in rows: agg[(y, i, s)][0 if c == "Italiana" else 1] += n
with open(os.path.join(PU, "decessi_nil_anno_genere.csv"), "w", encoding="utf8", newline="") as o:
    w = csv.writer(o); w.writerow(["anno", "id_nil", "sesso", "decessi", "di_cui_italiani", "di_cui_stranieri"])
    for k in sorted(agg): w.writerow([*k, sum(agg[k]), agg[k][0], agg[k][1]])
CTRL["decessi_non_assegnati_a_un_NIL"] = {f"{y}|{q}": n for (y, q), n in sorted(non.items())}
tot = collections.defaultdict(int)
for (y, i, s), v in agg.items(): tot[y] += sum(v)
CTRL["decessi_NIL_per_anno"] = dict(sorted(tot.items()))
# controllo: ds1938 (genere x eta', residenti) contro somma NIL 2021-2024
d38 = collections.defaultdict(int)
for r in csv.DictReader(open(os.path.join(SV, "raw", "comune_ds1938", "ds1938_popolazione-residenti-decessi-genere_eta.csv"), encoding="utf-8-sig"), delimiter=";"):
    d38[int(r["Anno_evento"])] += int(r["Numerosità"])
CTRL["ds1938_totale_per_anno"] = dict(d38)
# ISTAT: decessi Milano per anno x classe x sesso
ist = collections.defaultdict(int)
for r in csv.DictReader(open(os.path.join(P, "morti", "pulito", "decessi_giorno_eta_sesso.csv"), encoding="utf8")):
    if r["scope"] != "Milano": continue
    y = int(r["data"][:4]); c = int(r["cl_eta"])
    ist[(y, c, "M")] += int(r["M"]); ist[(y, c, "F")] += int(r["F"])
with open(os.path.join(PU, "decessi_citta_anno_cl_sesso.csv"), "w", encoding="utf8", newline="") as o:
    w = csv.writer(o); w.writerow(["anno", "cl_eta", "sesso", "decessi"])
    for k in sorted(ist): w.writerow([*k, ist[k]])
CTRL["istat_totale_per_anno"] = {y: sum(v for (yy, c, s), v in ist.items() if yy == y) for y in range(2011, 2027)}
# residenti: NIL x anno x classe ISTAT x sesso (31/12)
def cl(e):
    return 0 if e == 0 else 1 if e <= 4 else 21 if e >= 100 else e // 5 + 1
pop = collections.defaultdict(int)
for r in csv.DictReader(open(os.path.join(P, "popolazione", "pulito", "residenti_nil_anno_eta_genere.csv"), encoding="utf8")):
    pop[(int(r["anno"]), int(r["id_nil"]), cl(int(r["eta"])), "M" if r["genere"] == "Maschi" else "F")] += int(r["residenti"])
with open(os.path.join(PU, "residenti_nil_anno_cl_genere.csv"), "w", encoding="utf8", newline="") as o:
    w = csv.writer(o); w.writerow(["anno", "id_nil", "cl_eta", "sesso", "residenti"])
    for k in sorted(pop): w.writerow([*k, pop[k]])
CTRL["residenti_citta_31dic"] = {y: sum(v for (yy, i, c, s), v in pop.items() if yy == y) for y in range(1999, 2026)}
json.dump(CTRL, open(os.path.join(PU, "controlli_build.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(CTRL, ensure_ascii=False, indent=1)[:3500])
