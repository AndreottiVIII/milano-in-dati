"""Fase 1: pulizia e riepiloghi di presenze e votazioni dei consiglieri comunali di Milano (mandati 2016-2021 e 2021-2026).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 build.py <consiglio_dir> <amministratori_dir>

Legge  consiglio/raw/ds743/*.csv   (2016-2021: totali per anno 2016, 2017, 2018; poi CUMULATI dall'inizio del mandato, mese per mese)
       consiglio/raw/ds1643/*.csv  (2021-2026: totali CUMULATI dall'inizio del mandato, mese per mese, fino a maggio 2026)
       consiglio/raw/ds1914/*.csv  (dimissioni e surrogazioni 2021-2026)
       amministratori/pulito/{milano_amministratori.csv, milano_in_carica.csv}  (solo per il sesso, dal Ministero dell'Interno)
Scrive consiglio/pulito/: serie_cumulata.csv, consiglieri.csv, gruppi.csv, per_periodo.csv, per_sesso.csv, surroghe.csv, controlli.json, build_log.txt

Cosa misura il dato (vedi NOTE.md): per ogni consigliere, quante sedute del consiglio c'erano da quando e' in carica, a quante e' stato
presente, quante votazioni c'erano e a quante ha partecipato. NON c'e' il VOTO (si/no/astenuto) ne' il titolo della delibera.
"""
import sys, os, re, csv, glob, json, unicodedata, collections, datetime

BASE, AMM = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(BASE, "raw"), os.path.join(BASE, "pulito")
os.makedirs(PU, exist_ok=True)
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)
CHECKS = {}
def check(nome, ok, dettaglio=""):
    CHECKS[nome] = {"ok": bool(ok), "dettaglio": str(dettaglio)}
    log(("ok  " if ok else "!!  ") + nome + (" - " + str(dettaglio) if dettaglio else ""))

MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
        "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}

def noacc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

TYPO = {"barberis filipppo": "barberis filippo",            # refuso nel file di luglio 2024
        "celestino pietro girgio": "celestino pietro giorgio"}  # refuso nel nome (il Ministero scrive Giorgio)
def chiave(nome):
    """Nome senza note tra parentesi (o dopo 'dall'...'), minuscolo, senza accenti e apostrofi."""
    n = re.sub(r"\(.*$", "", nome)                   # (dal ...), (dimissionario ...) anche senza chiusa
    n = re.sub(r"\s+dall['’].*$", "", n)             # "Abbiati Gabriele Luigi dall'8-11-2018)"
    n = noacc(n).lower().replace("'", "").replace("’", "")
    n = re.sub(r"[^a-z ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return TYPO.get(n, n)
def nome_pulito(nome):
    n = re.sub(r"\(.*$", "", nome)
    n = re.sub(r"\s+dall['’].*$", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    # "SALA Giuseppe" -> "Sala Giuseppe"
    toks = n.split(" ")
    if toks and toks[0].isupper() and len(toks[0]) > 1: toks[0] = toks[0].capitalize()
    n = " ".join(toks)
    return {"Barberis Filipppo": "Barberis Filippo", "Celestino Pietro Girgio": "Celestino Pietro Giorgio"}.get(n, n)   # refusi del Comune
def nota_nome(nome):
    m = re.search(r"\((.*)$", nome) or re.search(r"(dall['’].*)$", nome)
    return m.group(1).strip(" )") if m else ""
def intero(x):
    x = (x or "").strip()
    return int(x) if x != "" else None
def gruppo_pulito(g):
    g = re.sub(r"\s*\(dal [^)]*\)?", "", g or "")   # "GRUPPO (dal 17.01.2023)" -> "GRUPPO": la data del cambio e' nel nome, non e' un altro gruppo
    return re.sub(r"\s+", " ", g.strip())

def leggi(path):
    t = open(path, encoding="utf-8-sig").read()
    prima = t.splitlines()[0]
    delim = ";" if prima.count(";") > prima.count(",") else ","
    righe = list(csv.reader(t.splitlines(), delimiter=delim))
    h = [x.strip().lower() for x in righe[0]]
    out = []
    for r in righe[1:]:
        if not any(x.strip() for x in r): continue
        d = dict(zip(h, r))
        nome = (d.get("consiglieri") or d.get("consigliere") or "").strip()
        if not nome: continue
        out.append({
            "nome_orig": nome, "gruppo": gruppo_pulito(d.get("gruppo")),
            "sedute": intero(d.get("tot. sedute") or d.get("totale sedute")),
            "presenze": intero(d.get("presenze") if "presenze" in d else d.get("totale presenze")),
            "vot_tot": intero(d.get("tot. vot") or d.get("totale votazioni")),
            "vot_eff": intero(d.get("votazioni") if "votazioni" in d and "tot. vot" in d else d.get("votazioni effettuate")),
            "pct_pres_file": (d.get("percentuale presenze") or "").strip(), "pct_vot_file": (d.get("percentuale votazioni") or "").strip(),
            "nota_file": (d.get("note") or "").strip()})
    return out

def pct_file(s):
    s = s.replace("%", "").replace(",", ".").strip()
    return float(s) if s else None

righe = []   # serie cumulata dall'inizio del mandato
sorgenti = []

# ---------------------------------------------------------------- 2016-2021 (ds743)
A = "2016-2021"
annuali = {}  # periodo -> {chiave: riga}
mensili = []
for f in sorted(glob.glob(os.path.join(RAW, "ds743", "*.csv"))):
    nf = os.path.basename(f)
    m = re.search(r"2016-2021_(.+)\.csv$", nf)
    etichetta = m.group(1)
    rr = leggi(f)
    sorgenti.append((nf, len(rr)))
    if etichetta == "da_luglio_a_dicembre_2016": per, kind = "2016-12", "anno"
    elif etichetta == "anno_2017": per, kind = "2017-12", "anno"
    elif etichetta == "anno_2018": per, kind = "2018-12", "anno"
    else:
        mese, anno = etichetta.split("_")
        per, kind = f"{anno}-{MESI[mese]:02d}", "cum"
    mensili.append((per, kind, nf, rr))
mensili.sort(key=lambda x: x[0])

# i primi tre file sono totali del solo anno: li sommo per avere i cumulati dall'inizio del mandato
run = {}   # chiave -> [sedute, presenze, vot_tot, vot_eff]
for per, kind, nf, rr in mensili:
    if kind == "anno":
        for r in rr:
            k = chiave(r["nome_orig"])
            c = run.setdefault(k, [0, 0, 0, 0])
            for i, c_ in enumerate(("sedute", "presenze", "vot_tot", "vot_eff")): c[i] += r[c_]
        snap = []
        for r in rr:
            k = chiave(r["nome_orig"]); c = run[k]
            snap.append(dict(r, sedute=c[0], presenze=c[1], vot_tot=c[2], vot_eff=c[3], _kind="somma"))
        rr_out = snap
    else:
        rr_out = [dict(r, _kind="file") for r in rr]
    for r in rr_out:
        righe.append(dict(r, mandato=A, periodo=per, file=nf))

# ---------------------------------------------------------------- 2021-2026 (ds1643)
B = "2021-2026"
f = glob.glob(os.path.join(RAW, "ds1643", "*.csv"))[0]
t = open(f, encoding="utf-8-sig").read().splitlines()
rd = csv.DictReader(t, delimiter=";")
n1643 = 0
for d in rd:
    n1643 += 1
    per = f"{int(d['Anno'])}-{MESI[d['Mese'].strip().lower()]:02d}"
    righe.append({"mandato": B, "periodo": per, "file": os.path.basename(f), "nome_orig": d["CONSIGLIERE"].strip(),
                  "gruppo": gruppo_pulito(d["GRUPPO"]), "sedute": intero(d["Totale Sedute"]), "presenze": intero(d["Totale Presenze"]),
                  "vot_tot": intero(d["Totale Votazioni"]), "vot_eff": intero(d["Votazioni Effettuate"]),
                  "pct_pres_file": "", "pct_vot_file": "", "nota_file": (d["Note"] or "").strip(), "_kind": "file"})
sorgenti.append((os.path.basename(f), n1643))
check("righe lette da ds1643", n1643 == 2549, n1643)

# ---------------------------------------------------------------- controllo incrociato con tre file mensili separati del Comune
ver = {}
for fv, per, cols in (("ds2966_*", "2025-12", ("Totale Presenze",)), ("ds2967_*", "2025-12", ("Totale Votazioni", "Votazioni Effettuate")), ("presenze_2021-2026_novembre_2021.csv", "2021-11", ("Totale Presenze",))):
    ff = glob.glob(os.path.join(RAW, "verifica", fv))
    if not ff: continue
    n_ok = n_tot = 0
    for d in csv.DictReader(open(ff[0], encoding="utf-8-sig").read().splitlines(), delimiter=";"):
        k = chiave(d["CONSIGLIERE"])
        m_ = [r for r in righe if r["mandato"] == B and r["periodo"] == per and chiave(r["nome_orig"]) == k]
        if not m_: n_tot += 1; continue
        r = m_[0]; n_tot += 1
        ok = int(d["Totale Sedute"]) == r["sedute"]
        if "Totale Presenze" in cols: ok = ok and int(d["Totale Presenze"]) == r["presenze"]
        if "Totale Votazioni" in cols: ok = ok and int(d["Totale Votazioni"]) == r["vot_tot"] and int(d["Votazioni Effettuate"]) == r["vot_eff"]
        n_ok += ok
    check(f"file mensile {os.path.basename(ff[0])[:30]} uguale a ds1643", n_ok == n_tot, f"{n_ok} su {n_tot} consiglieri uguali")

# ---------------------------------------------------------------- pulizia comune
for r in righe:
    r["chiave"] = chiave(r["nome_orig"]); r["nome"] = nome_pulito(r["nome_orig"]); r["nota_nome"] = nota_nome(r["nome_orig"])
    if r["gruppo"] == "": r["gruppo"] = "(nessun gruppo indicato)"

# controlli: valori mancanti, presenze <= sedute, voti <= totali, percentuali del file = ricalcolate
vuoti = [r for r in righe if None in (r["sedute"], r["presenze"], r["vot_tot"], r["vot_eff"])]
check("nessun valore mancante in sedute/presenze/votazioni", not vuoti, len(vuoti))
check("presenze <= sedute e votazioni effettuate <= totali", all(r["presenze"] <= r["sedute"] and r["vot_eff"] <= r["vot_tot"] for r in righe),
      sum(1 for r in righe if not (r["presenze"] <= r["sedute"] and r["vot_eff"] <= r["vot_tot"])))
diff = []
for r in righe:
    if r["_kind"] == "file" and r["pct_pres_file"]:
        p = pct_file(r["pct_pres_file"]); q = pct_file(r["pct_vot_file"])
        if r["sedute"] and abs(100 * r["presenze"] / r["sedute"] - p) > 0.01: diff.append((r["periodo"], r["nome"], "presenze", p))
        if r["vot_tot"] and abs(100 * r["vot_eff"] / r["vot_tot"] - q) > 0.01: diff.append((r["periodo"], r["nome"], "votazioni", q))
check("percentuali scritte nel file = ricalcolate (2016-21, tolleranza 0,01)", not diff, f"{len(diff)} diverse: {diff[:5]}")
dup = collections.Counter((r["mandato"], r["periodo"], r["chiave"]) for r in righe)
check("nessun consigliere ripetuto nello stesso mese", all(v == 1 for v in dup.values()), [k for k, v in dup.items() if v > 1][:5])

# monotonia dei cumulati per persona
per_pers = collections.defaultdict(list)
for r in righe: per_pers[(r["mandato"], r["chiave"])].append(r)
nonmon = []
for k, lst in per_pers.items():
    lst.sort(key=lambda r: r["periodo"])
    for a, b in zip(lst, lst[1:]):
        if b["sedute"] < a["sedute"] or b["presenze"] < a["presenze"] or b["vot_tot"] < a["vot_tot"] or b["vot_eff"] < a["vot_eff"]:
            nonmon.append((k, a["periodo"], b["periodo"]))
log(f"AVVISO dati del Comune: cumulati che scendono tra due mesi (errori nella fonte, incrementi azzerati): {nonmon}")
CHECKS["cumulati_che_scendono"] = {"ok": True, "dettaglio": f"{len(nonmon)} casi nella fonte, incremento posto a 0: {nonmon}"}
# i totali (sedute, votazioni) del consiglio: stessi per tutti nello stesso mese (massimo)
tot_per = collections.defaultdict(lambda: [0, 0])
for r in righe:
    t_ = tot_per[(r["mandato"], r["periodo"])]
    t_[0] = max(t_[0], r["sedute"]); t_[1] = max(t_[1], r["vot_tot"])
for mand in (A, B):
    ps = sorted(p for (m, p) in tot_per if m == mand)
    ok = all(tot_per[(mand, a)][0] <= tot_per[(mand, b)][0] and tot_per[(mand, a)][1] <= tot_per[(mand, b)][1] for a, b in zip(ps, ps[1:]))
    check(f"sedute e votazioni totali del consiglio crescono ({mand})", ok, f"{ps[0]} -> {ps[-1]}: {tot_per[(mand, ps[-1])]}")
# dopo la somma 2016-2018, il gennaio 2019 deve essere >= dicembre 2018
check("2016-21: cumulo a dicembre 2018 <= gennaio 2019", tot_per[(A, "2018-12")][0] <= tot_per[(A, "2019-01")][0],
      f"{tot_per[(A, '2018-12')]} -> {tot_per[(A, '2019-01')]}")

# ---------------------------------------------------------------- sesso (Ministero dell'Interno, DAIT)
def tokens(s): return noacc(s).lower().replace("'", "").replace("’", "").split()
sess = {}
for fn in ("milano_amministratori.csv", "milano_in_carica.csv"):
    for d in csv.DictReader(open(os.path.join(AMM, "pulito", fn), encoding="utf-8-sig")):
        if d["sesso"] in ("M", "F"):
            sess[" ".join(re.sub(r"[^a-z ]", " ", noacc(d["cognome"] + " " + d["nome"]).lower().replace("'", "")).split())] = d["sesso"]
def cerca_sesso(k):
    if k in sess: return sess[k], "esatto"
    cand = set()
    for kk, s in sess.items():
        a, b = kk.split(), k.split()
        if a[:len(b)] == b or b[:len(a)] == a: cand.add((kk, s))
    ss = {s for _, s in cand}
    if len(ss) == 1: return ss.pop(), "prefisso"
    return "", "non trovato"

# ---------------------------------------------------------------- serie_cumulata.csv
righe.sort(key=lambda r: (r["mandato"], r["periodo"], r["nome"]))
with open(os.path.join(PU, "serie_cumulata.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "periodo", "consigliere", "gruppo", "sedute", "presenze", "votazioni_totali", "votazioni_effettuate", "nota_nel_file", "nota_nel_nome", "file"])
    for r in righe:
        w.writerow([r["mandato"], r["periodo"], r["nome"], r["gruppo"], r["sedute"], r["presenze"], r["vot_tot"], r["vot_eff"], r["nota_file"], r["nota_nome"], r["file"]])

# ---------------------------------------------------------------- consiglieri.csv (totali per mandato)
cons = []
for (mand, k), lst in sorted(per_pers.items()):
    last, first = lst[-1], lst[0]
    gruppi_visti = []
    for r in lst:
        if r["gruppo"] not in gruppi_visti: gruppi_visti.append(r["gruppo"])
    s, how = cerca_sesso(k)
    sedute, pres, vt, ve = last["sedute"], last["presenze"], last["vot_tot"], last["vot_eff"]
    cons.append({"mandato": mand, "chiave": k, "consigliere": last["nome"], "sesso": s, "sesso_fonte": how,
                 "gruppo_finale": last["gruppo"], "gruppi": " > ".join(gruppi_visti), "cambi_gruppo": len(gruppi_visti) - 1,
                 "primo_periodo": first["periodo"], "ultimo_periodo": last["periodo"],
                 "sedute": sedute, "presenze": pres, "pct_presenze": round(100 * pres / sedute, 2) if sedute else None,
                 "votazioni_totali": vt, "votazioni_effettuate": ve, "pct_votazioni": round(100 * ve / vt, 2) if vt else None,
                 "nota": "; ".join(sorted({r["nota_nome"] for r in lst if r["nota_nome"]} | {r["nota_file"] for r in lst if r["nota_file"]}))})
non_trov = [c["consigliere"] for c in cons if c["sesso"] == ""]
check("sesso trovato per tutti i consiglieri (Ministero dell'Interno; Sacerdoti non e' ancora nell'elenco del 24/8/2026)", len(non_trov) <= 1, f"{len(cons) - len(non_trov)} su {len(cons)}; mancano: {non_trov}")
for c in cons:
    c["sindaco"] = 1 if c["chiave"] in ("sala giuseppe",) else 0
campi = list(cons[0].keys())
with open(os.path.join(PU, "consiglieri.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.DictWriter(fo, fieldnames=campi); w.writeheader(); w.writerows(cons)
for mand in (A, B):
    cm = [c for c in cons if c["mandato"] == mand]
    log(f"{mand}: {len(cm)} persone (con sindaco), donne {sum(1 for c in cm if c['sesso']=='F')}, uomini {sum(1 for c in cm if c['sesso']=='M')}")

# ---------------------------------------------------------------- per_periodo.csv: incrementi tra due fotografie
# per ogni persona, incremento = cumulato(t) - cumulato(t-1) (se compare per la prima volta: il suo cumulato)
incr = []  # righe di incremento
for (mand, k), lst in per_pers.items():
    prev = None
    for r in lst:
        p = prev or {"sedute": 0, "presenze": 0, "vot_tot": 0, "vot_eff": 0}
        incr.append({"mandato": mand, "periodo": r["periodo"], "chiave": k, "gruppo": r["gruppo"],
                     "ds": max(0, r["sedute"] - p["sedute"]), "dp": max(0, r["presenze"] - p["presenze"]), "dvt": max(0, r["vot_tot"] - p["vot_tot"]), "dve": max(0, r["vot_eff"] - p["vot_eff"])})
        prev = r
sind = {c["chiave"] for c in cons if c["sindaco"]}
sexmap = {(c["mandato"], c["chiave"]): c["sesso"] for c in cons}

def periodo_anno(mand, per):
    """Etichetta del periodo di calendario: anno (per il mandato 2021-26 ottobre-dicembre 2021 e' a se')."""
    return per[:4]
agg = collections.OrderedDict()
for x in incr:
    key = (x["mandato"], periodo_anno(x["mandato"], x["periodo"]))
    a = agg.setdefault(key, collections.Counter())
    for esc in (("tutti", True), ("senza_sindaco", x["chiave"] not in sind)):
        if esc[1]:
            a[esc[0] + "_ds"] += x["ds"]; a[esc[0] + "_dp"] += x["dp"]; a[esc[0] + "_dvt"] += x["dvt"]; a[esc[0] + "_dve"] += x["dve"]
# numero di sedute e votazioni in quel periodo (consiglio intero) = differenza dei massimi cumulati
def cum_tot(mand, per): return tot_per[(mand, per)]
with open(os.path.join(PU, "per_periodo.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "periodo", "primo_mese_nel_periodo", "ultimo_mese_nel_periodo", "sedute_del_consiglio", "votazioni_del_consiglio",
                "pct_presenze_senza_sindaco", "pct_votazioni_senza_sindaco", "pct_presenze_con_sindaco", "presenti_medi_per_seduta", "partecipanti_medi_per_votazione"])
    for (mand, anno), a in agg.items():
        ps = sorted(p for (m, p) in tot_per if m == mand and p[:4] == anno)
        # sedute del periodo = cumulo del consiglio a fine periodo - cumulo a fine periodo precedente dello stesso mandato
        prec = sorted(p for (m, p) in tot_per if m == mand and p[:4] < anno)
        s0 = tot_per[(mand, prec[-1])][0] if prec else 0
        v0 = tot_per[(mand, prec[-1])][1] if prec else 0
        sed = tot_per[(mand, ps[-1])][0] - s0; vot = tot_per[(mand, ps[-1])][1] - v0
        w.writerow([mand, anno, ps[0], ps[-1], sed, vot,
                    round(100 * a["senza_sindaco_dp"] / a["senza_sindaco_ds"], 2) if a["senza_sindaco_ds"] else "",
                    round(100 * a["senza_sindaco_dve"] / a["senza_sindaco_dvt"], 2) if a["senza_sindaco_dvt"] else "",
                    round(100 * a["tutti_dp"] / a["tutti_ds"], 2) if a["tutti_ds"] else "",
                    round(a["tutti_dp"] / sed, 2) if sed else "", round(a["tutti_dve"] / vot, 2) if vot else ""])
# NB: l'intervallo 2016-21 comincia a luglio 2016 e il mandato 2021-26 a ottobre 2021

# ---------------------------------------------------------------- gruppi.csv: per gruppo, sommando gli incrementi (il gruppo e' quello del mese)
gagg = collections.OrderedDict()
membri = collections.defaultdict(set)
for x in incr:
    key = (x["mandato"], x["gruppo"])
    a = gagg.setdefault(key, collections.Counter())
    if x["chiave"] in sind: continue
    a["ds"] += x["ds"]; a["dp"] += x["dp"]; a["dvt"] += x["dvt"]; a["dve"] += x["dve"]
    membri[key].add(x["chiave"])
sind_group = {}
with open(os.path.join(PU, "gruppi.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "gruppo", "persone_che_ne_hanno_fatto_parte", "sedute_persona", "presenze", "pct_presenze", "votazioni_persona", "votazioni_effettuate", "pct_votazioni", "differenza_punti"])
    for (mand, g), a in sorted(gagg.items(), key=lambda kv: (kv[0][0], -kv[1]["ds"])):
        if not a["ds"]: continue
        pp = 100 * a["dp"] / a["ds"]; pv = 100 * a["dve"] / a["dvt"]
        w.writerow([mand, g, len(membri[(mand, g)]), a["ds"], a["dp"], round(pp, 2), a["dvt"], a["dve"], round(pv, 2), round(pp - pv, 2)])

# ---------------------------------------------------------------- per_sesso.csv
with open(os.path.join(PU, "per_sesso.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "sesso", "persone", "sedute_persona", "presenze", "pct_presenze", "votazioni_persona", "votazioni_effettuate", "pct_votazioni",
                "mediana_pct_presenze_per_persona", "mediana_pct_votazioni_per_persona"])
    for mand in (A, B):
        for s in ("F", "M"):
            cm = [c for c in cons if c["mandato"] == mand and c["sesso"] == s and not c["sindaco"]]
            ds = sum(c["sedute"] for c in cm); dp = sum(c["presenze"] for c in cm); dvt = sum(c["votazioni_totali"] for c in cm); dve = sum(c["votazioni_effettuate"] for c in cm)
            def med(v):
                v = sorted(v); n = len(v); return round((v[n // 2] + v[(n - 1) // 2]) / 2, 2)
            w.writerow([mand, s, len(cm), ds, dp, round(100 * dp / ds, 2), dvt, dve, round(100 * dve / dvt, 2),
                        med([c["pct_presenze"] for c in cm]), med([c["pct_votazioni"] for c in cm])])

# ---------------------------------------------------------------- a parita' di gruppo: le donne e gli uomini rispetto alla media del loro gruppo
# presenze attese = sedute della persona x tasso di presenza del gruppo (stesso mese, tutti i membri tranne il sindaco)
with open(os.path.join(PU, "per_sesso_gruppo.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "sesso", "sedute_persona", "presenze_osservate", "presenze_attese_dal_gruppo", "pct_osservata", "pct_attesa_dal_gruppo", "differenza_punti",
                "votazioni_persona", "votazioni_osservate", "votazioni_attese_dal_gruppo", "pct_vot_osservata", "pct_vot_attesa_dal_gruppo", "differenza_punti_vot"])
    grate = collections.defaultdict(lambda: [0, 0, 0, 0])
    for x in incr:
        if x["chiave"] in sind: continue
        g = grate[(x["mandato"], x["periodo"], x["gruppo"])]
        g[0] += x["ds"]; g[1] += x["dp"]; g[2] += x["dvt"]; g[3] += x["dve"]
    for mand in (A, B):
        for sx in ("F", "M"):
            ds = dp = dvt = dve = ep = ev = 0
            for x in incr:
                if x["mandato"] != mand or x["chiave"] in sind or sexmap.get((mand, x["chiave"])) != sx: continue
                g = grate[(mand, x["periodo"], x["gruppo"])]
                ds += x["ds"]; dp += x["dp"]; dvt += x["dvt"]; dve += x["dve"]
                ep += x["ds"] * (g[1] / g[0] if g[0] else 0); ev += x["dvt"] * (g[3] / g[2] if g[2] else 0)
            w.writerow([mand, sx, ds, dp, round(ep, 1), round(100 * dp / ds, 2), round(100 * ep / ds, 2), round(100 * (dp - ep) / ds, 2),
                        dvt, dve, round(ev, 1), round(100 * dve / dvt, 2), round(100 * ev / dvt, 2), round(100 * (dve - ev) / dvt, 2)])

# ---------------------------------------------------------------- quanto puo' essere un caso? (rimescolando il sesso tra persone dello stesso gruppo)
import numpy as np
rng = np.random.default_rng(20261102)
test = {}
for mand in (A, B):
    pers = {}
    for x in incr:
        if x["mandato"] != mand or x["chiave"] in sind or sexmap.get((mand, x["chiave"])) not in ("F", "M"): continue
        g = grate[(mand, x["periodo"], x["gruppo"])]
        q = pers.setdefault(x["chiave"], [0, 0, 0.0])
        q[0] += x["ds"]; q[1] += x["dp"]; q[2] += x["ds"] * (g[1] / g[0] if g[0] else 0)
    ch = list(pers); ds = np.array([pers[k][0] for k in ch]); dp = np.array([pers[k][1] for k in ch]); ep = np.array([pers[k][2] for k in ch])
    sx0 = np.array([sexmap[(mand, k)] for k in ch])
    gfin = np.array([next(c["gruppo_finale"] for c in cons if c["mandato"] == mand and c["chiave"] == k) for k in ch])
    def stat(sx):
        m_ = sx == "F"; return 100 * (dp[m_].sum() - ep[m_].sum()) / ds[m_].sum()
    obs = stat(sx0); sims = []
    for _ in range(20000):
        s2 = sx0.copy()
        for g_ in sorted(set(gfin)):
            idx = np.where(gfin == g_)[0]; s2[idx] = rng.permutation(sx0[idx])
        sims.append(stat(s2))
    test[mand] = {"differenza_punti_donne": round(float(obs), 2), "p_due_code": round(float(np.mean(np.abs(sims) >= abs(obs))), 4), "permutazioni": 20000}
    log(f"{mand}: donne rispetto al loro gruppo {obs:+.2f} punti, rimescolando il sesso nel gruppo p = {test[mand]['p_due_code']}")
json.dump(test, open(os.path.join(PU, "per_sesso_test.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- surroghe: ingressi/uscite lette nei nomi del file di presenze vs ds1914
sur = list(csv.DictReader(open(glob.glob(os.path.join(RAW, "ds1914", "*.csv"))[0], encoding="utf-8-sig"), delimiter=";"))
with open(os.path.join(PU, "surroghe.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["mandato", "consigliere", "primo_mese", "ultimo_mese", "nota_nel_file_presenze", "in_ds1914"])
    nomi1914 = {chiave(r["CONSIGLIERE USCENTE"]) for r in sur} | {chiave(r["CONSIGLIERE ENTRANTE"]) for r in sur if r["CONSIGLIERE ENTRANTE"]}
    # chiavi del ds1914 sono "Nome Cognome" o "Cognome Nome": confronto per insieme di parole
    ins1914 = [set(chiave(r["CONSIGLIERE USCENTE"]).split()) for r in sur] + [set(chiave(r["CONSIGLIERE ENTRANTE"]).split()) for r in sur if r["CONSIGLIERE ENTRANTE"]]
    mov = []
    for c in cons:
        if c["mandato"] != B: continue
        entra = c["primo_periodo"] > "2021-10"
        esce = c["ultimo_periodo"] < "2026-05"
        if entra or esce:
            ws = set(c["chiave"].split())
            in1914 = any(a <= ws or ws <= a for a in ins1914)
            w.writerow([B, c["consigliere"], c["primo_periodo"], c["ultimo_periodo"], c["nota"], "si" if in1914 else "no"])
            mov.append((c["consigliere"], entra, esce, in1914))
n_in = sum(1 for m in mov if m[3])
log(f"AVVISO dati del Comune: ds1914 (surroghe 2021-26) ha {len(sur)} righe e nomina {n_in} delle {len(mov)} persone che nei file di presenze entrano o escono durante il mandato")
CHECKS["ds1914_incompleto"] = {"ok": True, "dettaglio": f"{len(sur)} righe di dati; {n_in} su {len(mov)} persone con ingresso o uscita nei file di presenze compaiono in ds1914"}

json.dump(CHECKS, open(os.path.join(PU, "controlli.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(PU, "build_log.txt"), "w", encoding="utf-8").write("\n".join(LOG) + "\n")
