"""Pulisce i dati sul turismo per provenienza (Comune di Milano ds210-ds220, PoliS-Lombardia xzck-giqt, c9ae-qhbj, vyxt-7jdx, mzxz-sz25).
uso: python -I -X utf8 07_pulisci_comune_polis.py <cartella turisti assoluta>
Scrive in <turisti>/pulito/ tabelle tidy:
  annuale_paese.csv        anno, paese, area, arrivi, presenze, permanenza_media, fonte   (comune di Milano, tutte le strutture; 2000-2025)
  annuale_paese_tipo.csv   anno, paese, tipo_struttura, arrivi, presenze                  (stranieri per paese 2008-2025 + Italiani totale)
  italiani_regione_tipo.csv anno, regione, tipo_struttura, arrivi, presenze               (2008-2025)
  mensile_paese.csv        anno, mese, paese, arrivi, presenze                            (comune di Milano, 2015-2025)
  provincia_mensile.csv    anno, mese, provenienza, tipo_provenienza, paese_o_regione, tipo_struttura, arrivi, presenze (provincia di Milano 2019-2025)
  milano_top10.csv         anno, graduatoria, provenienza, arrivi, presenze (comune di Milano 2019-2024, solo Totale)
  milano_italiani_stranieri.csv  anno, tipo_struttura, cittadinanza, arrivi, presenze     (vyxt-7jdx, comune di Milano 2019-2025)
  milano_mensile_totale.csv anno, mese, arrivi, presenze                                  (mzxz-sz25, comune di Milano, 2019-2025, Totale)
  controlli.txt            controlli di coerenza"""
import csv, sys, os, re, collections

base = sys.argv[1]
RAW = os.path.join(base, "raw"); OUT = os.path.join(base, "pulito")
os.makedirs(OUT, exist_ok=True)
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

def rd(path, delim=";"):
    return list(csv.DictReader(open(path, encoding="utf-8-sig", newline=""), delimiter=delim))

def num(s):
    s = (s or "").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):   # trappola: in ds212/ds219 alcuni valori hanno il punto come separatore delle migliaia ("29.531" = 29531)
        s = s.replace(".", "")
    s = s.replace(",", "")
    return int(float(s)) if s not in ("", "-") else None

MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
MESI_LONG = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# --- nomi dei paesi: unico nome per ogni paese (maiuscole, refusi, 'Israel')
def norm_paese(s):
    k = re.sub(r"\s+", " ", s.strip()).casefold()
    k = k.replace("altri parsi", "altri paesi").replace("austrialia", "australia")
    k = {"israel": "israele"}.get(k, k)
    return k
CANON = {}
def canon(s):
    k = norm_paese(s)
    if k not in CANON:
        # il primo nome in forma 'Titolo' normale
        CANON[k] = s.strip()
    return k
# nomi canonici scelti a mano per le forme maiuscole/miste
NOMI = {}
def nome_bello(k):
    if k in NOMI: return NOMI[k]
    t = k.title()
    for a, b in [(" Del ", " del "), (" Dell'", " dell'"), (" Di ", " di "), (" E ", " e "), (" D'", " d'"), ("Dell'", "dell'")]:
        t = t.replace(a, b)
    t = t.replace("Stati Uniti d'America", "Stati Uniti d'America")
    return t

# gruppi dall'ultima edizione (ds213, 2025); il Regno Unito e' stato spostato fuori dalla UE dal 2022
def area_di(paese_k, area_raw):
    return area_raw

# =========================================================
# 1. annuale per paese: ds211/ds213 (2005-2025), ds210/ds212 (2000-2004 per le serie lunghe; i dati 2005-2024 delle serie 2000 non si usano due volte)
def serie(arr_file, pres_file, fonte, anno_min, anno_max):
    out = {}
    for fname, campo in [(arr_file, "arrivi"), (pres_file, "presenze")]:
        for x in rd(os.path.join(RAW, "comune_milano", fname)):
            anno = int(x["Anno"]);
            if not (anno_min <= anno <= anno_max): continue
            v = [x[k] for k in x if k.lower() in ("valori", "valore")][0]
            k = (anno, canon(x["Paese di provenienza"]))
            d = out.setdefault(k, {"area": x["Area geografica"].strip(), "arrivi": None, "presenze": None, "fonte": fonte})
            if d[campo] is not None:
                P("ATTENZIONE doppione", fonte, k, campo)
            d[campo] = num(v)
    return out
s05 = serie("ds211.csv", "ds213.csv", "ds211+ds213", 2005, 2025)
s00 = serie("ds210.csv", "ds212.csv", "ds210+ds212", 2000, 2004)
tutto = {}
tutto.update(s00); tutto.update(s05)
righe = []
for (anno, k), d in sorted(tutto.items()):
    a, p = d["arrivi"], d["presenze"]
    righe.append([anno, nome_bello(k), d["area"], a, p, round(p / a, 2) if a and p else "", d["fonte"]])
with open(os.path.join(OUT, "annuale_paese.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["anno", "paese", "area_geografica_fonte", "arrivi", "presenze", "permanenza_media", "fonte"]); w.writerows(righe)
P("annuale_paese.csv", len(righe), "righe; anni", min(r[0] for r in righe), max(r[0] for r in righe))
# controlli: voci per anno e valori mancanti
cnt = collections.Counter(r[0] for r in righe)
P("voci per anno:", dict(sorted(cnt.items())))
mancanti = [(r[0], r[1]) for r in righe if r[3] is None or r[4] is None]
P("righe con arrivi o presenze mancanti:", mancanti[:10], len(mancanti))
# stessa serie a confronto 2005-2024 tra ds210/212 e ds211/213 (le due serie coincidono?)
s_old = serie("ds210.csv", "ds212.csv", "ds210+ds212", 2005, 2024)
diff = 0; tot = 0
for k, d in s_old.items():
    if k in s05:
        tot += 1
        if (d["arrivi"], d["presenze"]) != (s05[k]["arrivi"], s05[k]["presenze"]): diff += 1
P("confronto serie 2000 (ds210/212) e serie 2005 (ds211/213) sugli anni comuni: voci confrontate", tot, "voci diverse", diff)
tot_anno = collections.defaultdict(lambda: [0, 0])
for r in righe:
    tot_anno[r[0]][0] += r[3] or 0; tot_anno[r[0]][1] += r[4] or 0
P("totali per anno (arrivi, presenze):", {a: tuple(v) for a, v in sorted(tot_anno.items())})

# =========================================================
# 2. per tipo di struttura: ds219/ds220 stranieri, ds217/ds218 italiani per regione
rows = []
def leggi_tipo(fa, fp, col_paese):
    d = {}
    for fname, campo in [(fa, "arrivi"), (fp, "presenze")]:
        for x in rd(os.path.join(RAW, "comune_milano", fname)):
            k = (int(x["Anno"]), canon(x[col_paese]))
            e = d.setdefault(k, {})
            e[campo] = (num(x["Strutture Alberghiere"]), num(x["Strutture extra - alberghiere"]), num(x["Totale strutture ricettive"]))
    return d
st = leggi_tipo("ds219.csv", "ds220.csv", "Provenienza")
for (anno, k), e in sorted(st.items()):
    for i, tipo in enumerate(["alberghiero", "extra-alberghiero", "totale"]):
        rows.append([anno, nome_bello(k), tipo, e["arrivi"][i], e["presenze"][i]])
# italiani: somma delle regioni
it = leggi_tipo("ds217.csv", "ds218.csv", "Provenienza")
itreg = []
tot_it = collections.defaultdict(lambda: [[0, 0, 0], [0, 0, 0]])
for (anno, k), e in sorted(it.items()):
    for i, tipo in enumerate(["alberghiero", "extra-alberghiero", "totale"]):
        itreg.append([anno, nome_bello(k), tipo, e["arrivi"][i], e["presenze"][i]])
        tot_it[anno][0][i] += e["arrivi"][i] or 0; tot_it[anno][1][i] += e["presenze"][i] or 0
for anno, (a, p) in sorted(tot_it.items()):
    for i, tipo in enumerate(["alberghiero", "extra-alberghiero", "totale"]):
        rows.append([anno, "Italia", tipo, a[i], p[i]])
with open(os.path.join(OUT, "annuale_paese_tipo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["anno", "paese", "tipo_struttura", "arrivi", "presenze"]); w.writerows(rows)
with open(os.path.join(OUT, "italiani_regione_tipo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["anno", "regione", "tipo_struttura", "arrivi", "presenze"]); w.writerows(itreg)
P("annuale_paese_tipo.csv", len(rows), "righe; italiani_regione_tipo.csv", len(itreg), "righe")
# controllo: totale per tipo vs annuale_paese
ap = {(r[0], r[1]): (r[3], r[4]) for r in righe}
bad = 0
for anno in range(2008, 2026):
    pa = sum(r[3] for r in rows if r[0] == anno and r[2] == "totale")
    pp = sum(r[4] for r in rows if r[0] == anno and r[2] == "totale")
    ta, tp = tot_anno[anno]
    P(f"  {anno}: totale per tipo arrivi {pa:,} presenze {pp:,} | totale per paese arrivi {ta:,} presenze {tp:,} | diff presenze {pp - tp:,}")

# =========================================================
# 3. mensile per paese ds214/ds215
mm = {}
for fname, campo in [("ds214.csv", "arrivi"), ("ds215.csv", "presenze")]:
    for x in rd(os.path.join(RAW, "comune_milano", fname)):
        m = MESI.index(x["mese"].strip().lower()[:3]) + 1
        k = (int(x["anno"]), m, canon(x["Paese di provenienza"]))
        if k in mm and campo in mm[k]: P("ATTENZIONE doppione mensile", k)
        mm.setdefault(k, {})[campo] = num(x[campo])
with open(os.path.join(OUT, "mensile_paese.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["anno", "mese", "paese", "arrivi", "presenze"])
    for (a, m, k), e in sorted(mm.items()): w.writerow([a, m, nome_bello(k), e.get("arrivi"), e.get("presenze")])
P("mensile_paese.csv", len(mm), "righe")
# controllo: somma dei mesi = annuale?
somma = collections.defaultdict(lambda: [0, 0])
for (a, m, k), e in mm.items():
    somma[(a, k)][0] += e.get("arrivi") or 0; somma[(a, k)][1] += e.get("presenze") or 0
dif = []
for (a, k), (sa, sp) in sorted(somma.items()):
    if (a, k) in tutto:
        t = tutto[(a, k)]
        if t["arrivi"] != sa or t["presenze"] != sp: dif.append((a, nome_bello(k), sa - (t["arrivi"] or 0), sp - (t["presenze"] or 0)))
    else:
        dif.append((a, nome_bello(k), "assente nell'annuale", ""))
P("somma dei 12 mesi diversa dall'annuale per", len(dif), "voci paese-anno su", len(somma), "; esempi:", dif[:12])

# =========================================================
# 4. provincia di Milano mensile xzck-giqt
REGIONI = {"abruzzo", "basilicata", "bolzano - bozen", "calabria", "campania", "emilia-romagna", "friuli-venezia giulia", "lazio", "liguria",
           "lombardia", "marche", "molise", "piemonte", "puglia", "sardegna", "sicilia", "toscana", "trento", "umbria", "valle d'aosta", "veneto", "regione non specificata"}
with open(os.path.join(OUT, "provincia_mensile.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["anno", "mese", "tipo_provenienza", "provenienza", "tipo_struttura", "arrivi", "presenze"])
    n = 0
    for x in csv.DictReader(open(os.path.join(RAW, "lombardia", "xzck-giqt_milano.csv"), encoding="utf-8")):
        k = norm_paese(x["provenienza_turisti"])
        tp = "italia_regione" if k in REGIONI else ("non_specificato" if "non specificat" in k else "estero")
        m = MESI_LONG.index(x["mese"].lower()) + 1
        nome = nome_bello(k) if tp == "estero" else x["provenienza_turisti"].title() if tp != "estero" else ""
        for tipo, a, p in [("totale", "arrivi_totale", "presenze_totale"), ("alberghiero", "arrivi_alberghiero", "presenze_alberghiero"),
                           ("extra-alberghiero", "arrivi_extra_alberghiero", "presenze_extra_alberghiero")]:
            w.writerow([int(x["anno"]), m, tp, nome, tipo, num(x[a]), num(x[p])]); n += 1
P("provincia_mensile.csv", n, "righe")

# 5. top 10 comune di Milano
with open(os.path.join(OUT, "milano_top10.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["anno", "graduatoria", "provenienza", "arrivi", "presenze", "permanenza_media"])
    for x in csv.DictReader(open(os.path.join(RAW, "lombardia", "c9ae-qhbj_milano.csv"), encoding="utf-8")):
        prov = x["provenienza_turisti"]
        prov = "Stati Uniti d'America" if prov == "USA" else prov.title() if prov.isupper() else prov
        w.writerow([int(x["anno"]), x["graduatoria_provenienza"].replace("°", ""), prov, num(x["arrivi"]), num(x["presenze"]), x["permanenza_media"]])

# 6. vyxt (italiani/stranieri per tipo) e mzxz (mensile totale)
with open(os.path.join(OUT, "milano_italiani_stranieri.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["anno", "tipo_struttura", "cittadinanza", "arrivi", "presenze"])
    for x in csv.DictReader(open(os.path.join(RAW, "lombardia", "vyxt-7jdx_milano.csv"), encoding="utf-8")):
        t = x["tipo_struttura"].strip().lower().replace("es. ", "").replace("alberghieri", "alberghiero").replace("extra-alberghieri", "extra-alberghiero")
        w.writerow([int(x["anno"]), t, x["cittadinanza_turisti"].strip().lower(), num(x["arrivi"]), num(x["presenze"])])
with open(os.path.join(OUT, "milano_mensile_totale.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["anno", "mese", "arrivi", "presenze"])
    rr = sorted(csv.DictReader(open(os.path.join(RAW, "lombardia", "mzxz-sz25_milano.csv"), encoding="utf-8")), key=lambda x: (int(x["anno"]), MESI_LONG.index(x["mese"].lower())))
    for x in rr: w.writerow([int(x["anno"]), MESI_LONG.index(x["mese"].lower()) + 1, num(x["arrivi"]), num(x["presenze"])])
open(os.path.join(OUT, "controlli_comune_polis.txt"), "w", encoding="utf-8").write("\n".join(log))
