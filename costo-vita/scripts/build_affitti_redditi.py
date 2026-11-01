"""Affitto (quotazioni OMI, STIME) contro reddito dei residenti di Milano, per anno 2006-2024 (anno di imposta).
Uso: python -I -X utf8 build_affitti_redditi.py <costo-vita assoluto> <prezzi-case assoluto>
Fonti:
 - affitto: prezzi-case/pulito/prezzi_citta_mediana_zone.csv (Agenzia delle Entrate OMI, valori di locazione in euro/m2/mese,
   media del centro (min+max)/2 per zona, mediana NON pesata fra le zone; tipologia 'Abitazioni civili' e 'Abitazioni di tipo economico')
 - redditi: Comune di Milano ds941-ds957, ds1267, ds1589, ds1824, ds2274, ds2276, ds2733, ds2947, ds3010 (dichiarazioni Irpef per comune, MEF)
Scrive pulito/affitto_vs_reddito.csv e pulito/controlli_affitto_reddito.txt"""
import sys, os, csv, glob, re, statistics
C, P = sys.argv[1], sys.argv[2]
log = []
def say(s): print(s); log.append(s)

def readtext(p):
    b = open(p, "rb").read()
    try: return b.decode("utf-8-sig")
    except UnicodeDecodeError: return b.decode("cp1252", errors="replace")

# ---- redditi per anno di imposta
inc = {}
for p in glob.glob(os.path.join(C, "raw", "comune", "ds*", "*.csv")):
    t = readtext(p)
    rows = [r for r in csv.reader(t.splitlines(), delimiter=";") if len(r) >= 2]
    d = {r[0].strip(): r[1].strip() for r in rows}
    if d.get("Denominazione Comune", "").upper() != "MILANO": continue
    y = d.get("Anno di imposta") or d.get("Anno di Imposta")
    if not y or not y.isdigit(): continue
    y = int(y)
    def g(prefix, kind):
        for k, v in d.items():
            if k.startswith(prefix) and k.endswith(kind) or (k.startswith(prefix) and kind in k):
                try: return float(v)
                except ValueError: return None
        return None
    rec = {"file": os.path.relpath(p, C).replace("\\", "/")}
    # imponibile addizionale
    f = a = None
    for k, v in d.items():
        if k.startswith("Reddito imponibile addizionale") and "Frequenza" in k: f = float(v)
        if k.startswith("Reddito imponibile addizionale") and "Ammontare" in k: a = float(v)
    rec["imp_freq"], rec["imp_amm"] = f, a
    # lavoro dipendente
    f = a = None
    for k, v in d.items():
        if k.startswith("Reddito da lavoro dipendente") and "Frequenza" in k: f = float(v)
        if k.startswith("Reddito da lavoro dipendente") and "Ammontare" in k: a = float(v)
    rec["dip_freq"], rec["dip_amm"] = f, a
    rec["contribuenti"] = float(d["Numero contribuenti"]) if "Numero contribuenti" in d else None
    # classi di reddito complessivo
    cl = []
    for k, v in d.items():
        if k.startswith("Reddito complessivo") and "Frequenza" in k:
            n = k.replace("Reddito complessivo", "")
            if "minore o uguale a zero" in n or "minore di zero" in n: lo, hi = None, 0
            elif "oltre" in n: lo, hi = float(re.search(r"oltre (\d+)", n).group(1)), None
            else:
                m = re.search(r"da (\d+) a (\d+)", n); lo, hi = float(m.group(1)), float(m.group(2))
            am = d.get(k.replace("Frequenza", "Ammontare")) or d.get(k.replace("Frequenza", "Ammontare in euro"))
            cl.append((lo, hi, float(v), float(am) if am else None))
    rec["classi"] = sorted(cl, key=lambda x: (x[0] is not None, x[0] or 0))
    inc[y] = rec

def median_classes(cl):
    tot = sum(c[2] for c in cl); half = tot / 2; cum = 0
    for lo, hi, n, _ in cl:
        if cum + n >= half and lo is not None and hi is not None:
            return lo + (hi - lo) * (half - cum) / n
        cum += n
    return None

# ---- affitti OMI
om = {}
for r in csv.DictReader(open(os.path.join(P, "pulito", "prezzi_citta_mediana_zone.csv"), encoding="utf-8")):
    if r["tipologia"] in ("Abitazioni civili", "Abitazioni di tipo economico"):
        om[(r["tipologia"], r["semestre"])] = (float(r["loc_mediana_zone"]), int(r["n_zone"]), float(r["compr_mediana_zone"]))
foi = {int(r["anno"]): float(r["indice_raccordato_2025_100"]) for r in csv.DictReader(open(os.path.join(P, "pulito", "foi_annuale.csv"), encoding="utf-8"))}

M2 = 60.0; ORE = 173.0   # appartamento di 60 m2 (ipotesi); ore lavorate al mese a tempo pieno 40 h x 52 / 12 (ipotesi)
out = []
for y in range(2006, 2025):
    if y not in inc: continue
    r = inc[y]
    row = {"anno": y}
    for tip, tag in (("Abitazioni civili", "civ"), ("Abitazioni di tipo economico", "eco")):
        v = [om[(tip, "%d-S%d" % (y, s))][0] for s in (1, 2) if (tip, "%d-S%d" % (y, s)) in om]
        row["affitto_%s_eur_m2_mese" % tag] = round(statistics.mean(v), 3) if v else ""
        row["affitto_%s_%dm2_mese" % (tag, M2)] = round(statistics.mean(v) * M2, 1) if v else ""
    row["reddito_imponibile_medio_mese"] = round(r["imp_amm"] / r["imp_freq"] / 12, 1) if r["imp_freq"] else ""
    row["reddito_complessivo_medio_mese"] = round(sum(c[3] for c in r["classi"]) / sum(c[2] for c in r["classi"]) / 12, 1) if r["classi"] and all(c[3] for c in r["classi"]) else ""
    med = median_classes(r["classi"]) if r["classi"] else None
    row["reddito_complessivo_mediano_mese_interpolato"] = round(med / 12, 1) if med else ""
    row["reddito_dipendente_medio_mese"] = round(r["dip_amm"] / r["dip_freq"] / 12, 1) if r["dip_freq"] else ""
    row["n_contribuenti_classi"] = int(sum(c[2] for c in r["classi"])) if r["classi"] else ""
    row["foi_2025_100"] = foi.get(y, "")
    ac = row["affitto_civ_%dm2_mese" % M2]
    for nome, k in (("mediano", "reddito_complessivo_mediano_mese_interpolato"), ("imponibile_medio", "reddito_imponibile_medio_mese"), ("dipendente_medio", "reddito_dipendente_medio_mese")):
        row["affitto_civ_su_reddito_%s_pct" % nome] = round(ac / row[k] * 100, 1) if ac != "" and row[k] != "" else ""
        row["ore_di_lavoro_per_affitto_civ_%s" % nome] = round(ac / row[k] * ORE, 1) if ac != "" and row[k] != "" else ""
    row["file_redditi"] = r["file"]
    out.append(row)
cols = list(out[0].keys())
with open(os.path.join(C, "pulito", "affitto_vs_reddito.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter=";"); w.writeheader(); w.writerows(out)
for r in out:
    say("%d | affitto 60m2 civili %s | mediano %s | imp.medio %s | dip.medio %s | quota su mediano %s%% | ore (mediano) %s" % (r["anno"], r["affitto_civ_60m2_mese"], r["reddito_complessivo_mediano_mese_interpolato"], r["reddito_imponibile_medio_mese"], r["reddito_dipendente_medio_mese"], r["affitto_civ_su_reddito_mediano_pct"], r["ore_di_lavoro_per_affitto_civ_mediano"]))
# controllo: coerenza tra mediana e media, e tra 'Numero contribuenti' e somma delle classi (anni dal 2012)
for y in (2012, 2018, 2024):
    r = inc[y]; say("controllo %d: Numero contribuenti=%s, somma classi=%d" % (y, r["contribuenti"], sum(c[2] for c in r["classi"])))
open(os.path.join(C, "pulito", "controlli_affitto_reddito.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
