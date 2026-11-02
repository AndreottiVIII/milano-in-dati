"""Costruisce le serie finali (per citta' e anno) con le famiglie e i tassi per 1.000 famiglie.

Uso: python -I -X utf8 serie.py <sfratti_dir>
Legge: pulito/province_2013_2025.csv, grandi_province_2001_2012.csv, italia_2001_2025.csv, famiglie_territori.csv
Scrive: pulito/serie_unita.csv (una riga per unita' e anno), pulito/famiglie_per_anno.csv, pulito/controlli_serie.txt

Unita':
  Italia
  Milano (provincia con Monza e Brianza)  = vecchio perimetro, continuo 2001-2025 (dal 2013 il Ministero separa Monza e Brianza)
  Milano (provincia senza Monza)           = 2013-2025
  Comune di Milano                         = solo "capoluogo" dei provvedimenti emessi, 2013-2025
  Torino, Roma, Napoli, Bologna, Firenze   = province (2001-2025)
Famiglie: censimento 2001, censimento 2011, censimento permanente 2018-2024; negli anni in mezzo interpolazione lineare, 2025 = 2024.
"""
import sys, os, csv, collections, json

BASE = sys.argv[1]
PU = os.path.join(BASE, "pulito")
LOG = []
def say(s):
    print(s); LOG.append(s)

def leggi(nome):
    return list(csv.DictReader(open(os.path.join(PU, nome), encoding="utf8"), delimiter=";"))
def f(x):
    return None if x in (None, "") else float(x)

prov = leggi("province_2013_2025.csv")
grandi = leggi("grandi_province_2001_2012.csv")
ita = leggi("italia_2001_2025.csv")
fam = leggi("famiglie_territori.csv")

# ---------------------------------------------------------------- famiglie per unita' e anno
fcens = collections.defaultdict(dict)  # (tipo,territorio) -> anno -> famiglie
for r in fam:
    if r["tipo_dato"] in ("famiglie_censimento", "famiglie_31dic_censimento_permanente"):
        fcens[(r["tipo"], r["territorio"])][int(r["anno"])] = float(r["famiglie"])

def serie_famiglie(chiavi):
    """somma le serie di piu' territori e interpola tra i punti noti"""
    punti = collections.defaultdict(float)
    anni_ok = None
    for k in chiavi:
        d = fcens[k]
        anni_ok = set(d) if anni_ok is None else anni_ok & set(d)
    for k in chiavi:
        for a in anni_ok:
            punti[a] += fcens[k][a]
    noti = sorted(punti)
    out = {}
    for a in range(2001, 2026):
        if a in punti:
            out[a] = (punti[a], "dato ISTAT")
        elif a < noti[0]:
            out[a] = (None, "")
        elif a > noti[-1]:
            out[a] = (punti[noti[-1]], "uguale all'ultimo anno noto (%d)" % noti[-1])
        else:
            a0 = max(x for x in noti if x < a); a1 = min(x for x in noti if x > a)
            out[a] = (punti[a0] + (punti[a1] - punti[a0]) * (a - a0) / (a1 - a0), "interpolato tra %d e %d" % (a0, a1))
    return out

UNITA = {
    "Italia": [("paese", "Italia")],
    "Milano (provincia con Monza e Brianza)": [("provincia", "Milano"), ("provincia", "Monza e della Brianza")],
    "Milano (provincia senza Monza)": [("provincia", "Milano")],
    "Comune di Milano": [("comune", "Milano")],
    "Torino": [("provincia", "Torino")], "Roma": [("provincia", "Roma")], "Napoli": [("provincia", "Napoli")],
    "Bologna": [("provincia", "Bologna")], "Firenze": [("provincia", "Firenze")],
    "Comune di Torino": [("comune", "Torino")], "Comune di Roma": [("comune", "Roma")], "Comune di Napoli": [("comune", "Napoli")],
    "Comune di Bologna": [("comune", "Bologna")], "Comune di Firenze": [("comune", "Firenze")],
}
FAMS = {u: serie_famiglie(k) for u, k in UNITA.items()}
with open(os.path.join(PU, "famiglie_per_anno.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["unita", "anno", "famiglie", "origine"])
    for u, d in FAMS.items():
        for a, (v, o) in sorted(d.items()):
            if v is not None:
                w.writerow([u, a, round(v), o])

# ---------------------------------------------------------------- serie sfratti
def pr(anno, nome):
    return [r for r in prov if int(r["anno"]) == anno and r["provincia"] == nome]

RIGHE = []
def riga(unita, anno, nec, fin, mor, tot, ric, ese, fonte, note=""):
    fa, orig = FAMS[unita].get(anno, (None, ""))
    r = dict(unita=unita, anno=anno, nec=nec, fin=fin, mor=mor, emessi=tot, richieste=ric, eseguiti=ese, famiglie=None if fa is None else round(fa),
             origine_famiglie=orig, fonte=fonte, note=note)
    for k, c in (("emessi", "emessi_per_1000_fam"), ("richieste", "richieste_per_1000_fam"), ("eseguiti", "eseguiti_per_1000_fam")):
        v = r[k]
        r[c] = None if (v is None or fa is None) else round(1000.0 * v / fa, 3)
    r["quota_morosita_pct"] = None if (mor is None or not tot) else round(100.0 * mor / tot, 1)
    RIGHE.append(r)

# Italia
for r in ita:
    a = int(r["anno"])
    riga("Italia", a, f(r["nec"]), f(r["fin"]), f(r["mor"]), f(r["totale"]), f(r["richieste"]), f(r["eseguiti"]), r["fonte"])

# 2001-2012 dai rapporti
nome_gr = {"Torino": "Torino", "Roma": "Roma", "Napoli": "Napoli", "Bologna": "Bologna", "Firenze": "Firenze", "Milano (provincia con Monza e Brianza)": "Milano (con Monza e Brianza)"}
for unita, nome in nome_gr.items():
    for g in grandi:
        if g["provincia"] == nome and int(g["anno"]) <= 2012:
            riga(unita, int(g["anno"]), f(g["nec"]), f(g["fin"]), f(g["mor"]), f(g["totale"]), f(g["richieste"]), f(g["eseguiti"]), g["fonte"],
                 "dati incompleti secondo il rapporto" if g["flag"] and unita.startswith("Milano") else "")

# 2013-2025 dai file
def somma(righe_, k):
    v = [f(r[k]) for r in righe_]
    return None if any(x is None for x in v) else sum(v)
for anno in range(2013, 2026):
    for unita, nome in (("Torino", "Torino"), ("Roma", "Roma"), ("Napoli", "Napoli"), ("Bologna", "Bologna"), ("Firenze", "Firenze")):
        rr = pr(anno, nome)
        assert len(rr) == 1, (anno, nome, len(rr))
        r = rr[0]
        nec = f(r["nec_cap"]); nec = None if nec is None else nec + f(r["nec_resto"])
        fin = None if r["fin_cap"] == "" else f(r["fin_cap"]) + f(r["fin_resto"])
        mor = None if r["mor_cap"] == "" else f(r["mor_cap"]) + f(r["mor_resto"])
        riga(unita, anno, nec if r["nec_cap"] != "" else None, fin, mor, f(r["totale"]), f(r["richieste"]), f(r["eseguiti"]), r["fonte"],
             "dati incompleti secondo la nota del foglio" if r["incompleta_secondo_nota"] == "1" else ("derivato dalle variazioni 2021" if r["fonte"].startswith("DERIVATO") else ""))
    mi = pr(anno, "Milano"); mz = pr(anno, "Monza e della Brianza")
    assert len(mi) == 1 and len(mz) == 1, (anno, len(mi), len(mz))
    mi, mz = mi[0], mz[0]
    def tot3(r_, a_, b_):
        if r_[a_] == "":
            return None
        return f(r_[a_]) + f(r_[b_])
    inc = "dati incompleti secondo la nota del foglio" if mi["incompleta_secondo_nota"] == "1" else ""
    der = "derivato dalle variazioni 2021" if mi["fonte"].startswith("DERIVATO") else ""
    nota = inc or der
    # Milano senza Monza
    riga("Milano (provincia senza Monza)", anno, tot3(mi, "nec_cap", "nec_resto"), tot3(mi, "fin_cap", "fin_resto"), tot3(mi, "mor_cap", "mor_resto"),
         f(mi["totale"]), f(mi["richieste"]), f(mi["eseguiti"]), mi["fonte"], nota)
    # con Monza (somma)
    def s2(k):
        a, b = f(mi[k]), f(mz[k])
        return None if a is None or b is None else a + b
    def s2m(k1, k2):
        a, b = tot3(mi, k1, k2), tot3(mz, k1, k2)
        return None if a is None or b is None else a + b
    riga("Milano (provincia con Monza e Brianza)", anno, s2m("nec_cap", "nec_resto"), s2m("fin_cap", "fin_resto"), s2m("mor_cap", "mor_resto"),
         s2("totale"), s2("richieste"), s2("eseguiti"), mi["fonte"] + " + " + mz["fonte"], nota)
    # Comune di Milano: solo il "capoluogo" dei provvedimenti emessi
    if mi["nec_cap"] != "":
        nec, fin, mor = f(mi["nec_cap"]), f(mi["fin_cap"]), f(mi["mor_cap"])
        riga("Comune di Milano", anno, nec, fin, mor, nec + fin + mor, None, None, mi["fonte"], "solo provvedimenti emessi nel capoluogo; richieste ed esecuzioni esistono solo per la provincia. " + nota)
    for unita, nome in (("Comune di Torino", "Torino"), ("Comune di Roma", "Roma"), ("Comune di Napoli", "Napoli"), ("Comune di Bologna", "Bologna"), ("Comune di Firenze", "Firenze")):
        r = pr(anno, nome)[0]
        if r["nec_cap"] != "":
            nec, fin, mor = f(r["nec_cap"]), f(r["fin_cap"]), f(r["mor_cap"])
            riga(unita, anno, nec, fin, mor, nec + fin + mor, None, None, r["fonte"], "solo provvedimenti emessi nel capoluogo")

RIGHE.sort(key=lambda r: (r["unita"], r["anno"]))
cols = ["unita", "anno", "nec", "fin", "mor", "emessi", "richieste", "eseguiti", "famiglie", "origine_famiglie", "emessi_per_1000_fam", "richieste_per_1000_fam",
        "eseguiti_per_1000_fam", "quota_morosita_pct", "note", "fonte"]
with open(os.path.join(PU, "serie_unita.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, delimiter=";")
    w.writeheader()
    w.writerows(RIGHE)
say("righe: %d" % len(RIGHE))

# ---------------------------------------------------------------- controlli e stampa
by = {(r["unita"], r["anno"]): r for r in RIGHE}
say("--- Milano provincia con Monza: emessi, richieste, eseguiti, famiglie, tasso emessi per 1000 famiglie")
for a in range(2001, 2026):
    r = by.get(("Milano (provincia con Monza e Brianza)", a))
    if r:
        say(f"{a} {r['emessi']!s:>7} {r['richieste']!s:>8} {r['eseguiti']!s:>6} fam={r['famiglie']} {r['emessi_per_1000_fam']} mor%={r['quota_morosita_pct']} {r['note']}")
say("--- tasso emessi per 1000 famiglie, province")
us = ["Italia", "Milano (provincia con Monza e Brianza)", "Torino", "Roma", "Napoli", "Bologna", "Firenze"]
say("anno " + " ".join(u[:7].ljust(7) for u in us))
for a in range(2001, 2026):
    say(str(a) + " " + " ".join(str(by[(u, a)]["emessi_per_1000_fam"] if (u, a) in by else "-").ljust(7) for u in us))
say("--- Comune di Milano: emessi capoluogo")
for a in range(2013, 2026):
    r = by.get(("Comune di Milano", a))
    if r is None:
        say(f"{a} (nessun dato: 2020 solo derivato per provincia)"); continue
    say(f"{a} {r['emessi']} fam={r['famiglie']} {r['emessi_per_1000_fam']} mor={r['mor']} fin={r['fin']} nec={r['nec']}")
open(os.path.join(PU, "controlli_serie.txt"), "w", encoding="utf8").write("\n".join(LOG))
