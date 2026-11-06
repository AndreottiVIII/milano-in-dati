# -*- coding: utf-8 -*-
"""Pulisce il dataset ds2914 e conta i cambi di nome. Scrive pulito/vie.json e pulito/riepilogo.json.
Regola dei cambi veri e di grafia: vedi NOTE.md. Uso: python -I -X utf8 pulisci.py"""
import csv, json, os, re, unicodedata, collections

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(QUI)
CSV = os.path.join(BASE, "raw", "ds2914_vie-milano-corrispondenza-mappe-storiche.csv")
OUT = os.path.join(BASE, "pulito")
ANNI = [1884, 1910, 1930, 1946, 1956, 1965, 1972, 1990, 2006, 2012]

TIPI = {"via", "viale", "corso", "piazza", "piazzale", "largo", "vicolo", "strada"}
VUOTE = {"di", "del", "della", "delle", "dei", "dello", "degli", "dell", "d", "e", "tra", "il", "la", "lo", "le", "i", "al", "alla"}
SINONIMI = {"giovine": "giovane", "ospitale": "ospedale", "xxiv": "24", "xxv": "25", "ventiquattro": "24", "venticinque": "25", "s": "san", "p": "porta"}
# parole che indicano un'altra cosa (un canale, una porta, un ponte): se sono l'unica differenza, e' un cambio vero
STRUTTURA = {"naviglio", "cerchia", "porta", "cascina", "ponte", "quartiere", "cimitero", "bastioni", "bastione", "doppia"}
MANCANTI = {"non esistente": "nonesiste", "mappa non leggibile": "illeggibile", "": "illeggibile"}


def senza_accenti(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def nomi_di(raw):
    """Un valore della tabella -> elenco di nomi (ognuno e' un insieme di parole significative)."""
    s = re.sub(r"\([^)]*\)", " ", raw)  # annotazione fra parentesi: non e' il nome scritto sulla mappa
    s = senza_accenti(s.lower())
    m = re.match(r"\s*incrocio tra (.+?) e (.+)$", s)
    if m:
        pezzi = [m.group(1), m.group(2)]
    else:
        pezzi = re.split(r"[,/]", s)
    nomi = []
    for p in pezzi:
        p = re.sub(r"['`.]", " ", p)
        par = []
        for t in re.findall(r"[a-z0-9]+", p):
            t = SINONIMI.get(t, t)
            if t in TIPI or t in VUOTE:
                continue
            if len(t) == 1 and t.isalpha() and t not in ("s", "p"):
                continue
            par.append(t)
        if par:
            nomi.append(frozenset(par))
    return nomi


def equivalenti(a, b):
    """Stesso nome scritto in modo diverso: stesse parole, oppure una e' contenuta nell'altra
    (nome di battesimo in piu') e le parole in piu' non indicano un'altra cosa."""
    if a == b:
        return True
    piccolo, grande = (a, b) if len(a) <= len(b) else (b, a)
    return piccolo <= grande and not ((grande - piccolo) & STRUTTURA)


def confronta(na, nb):
    """'uguale' | 'parziale' (almeno un nome in comune, ma non tutti) | 'cambio' (nessun nome in comune)."""
    comuni_a = [x for x in na if any(equivalenti(x, y) for y in nb)]
    comuni_b = [y for y in nb if any(equivalenti(x, y) for x in na)]
    if not comuni_a:
        return "cambio"
    if len(comuni_a) == len(na) and len(comuni_b) == len(nb):
        return "uguale"
    return "parziale"


def leggi():
    with open(CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def elabora(riga):
    attuale = riga["Nome attuale"].strip()
    valori = [(str(a), riga["Mappa %d" % a].strip()) for a in ANNI] + [("oggi", attuale)]
    celle = []
    for et, raw in valori:
        chiave = MANCANTI.get(raw.lower())
        if chiave:
            celle.append({"anno": et, "raw": raw, "stato": chiave, "nomi": []})
        else:
            celle.append({"anno": et, "raw": raw, "stato": "ok", "nomi": nomi_di(raw)})
    righe, eventi = [], []
    ultima = None
    ultimo_idx = None
    mancanti = []
    visto_inesistente = False
    for i, c in enumerate(celle):
        if c["stato"] != "ok":
            mancanti.append(c)
            if c["stato"] == "nonesiste":
                visto_inesistente = True
            continue
        if ultima is None:
            ultima = {"da": c["anno"], "a": c["anno"], "nome": c["raw"], "varianti": [], "esito": "nasce" if visto_inesistente else "inizio", "nomi": c["nomi"]}
            righe.append(ultima)
            if visto_inesistente:
                eventi.append({"tipo": "nasce", "da": None, "a": c["anno"]})
        else:
            esito = confronta(ultima["nomi"], c["nomi"])
            if esito == "uguale":
                ultima["a"] = c["anno"]
                if c["raw"] != ultima["nome"] and c["raw"] not in ultima["varianti"]:
                    ultima["varianti"].append(c["raw"])
            else:
                nuova = {"da": c["anno"], "a": c["anno"], "nome": c["raw"], "varianti": [], "esito": esito, "nomi": c["nomi"]}
                eventi.append({"tipo": esito, "da": ultima["a"], "a": c["anno"], "salto": i - ultimo_idx > 1})
                righe.append(nuova)
                ultima = nuova
        ultimo_idx = i
        mancanti = []
    for r in righe:
        r.pop("nomi", None)
    return {"id": int(riga["identificativo"]), "attuale": attuale, "lon": float(riga["LONG_X_4326"]), "lat": float(riga["LAT_Y_4326"]),
            "righe": righe, "eventi": eventi,
            "celle": [{"anno": c["anno"], "raw": c["raw"], "stato": c["stato"]} for c in celle]}


def main():
    tutte = [elabora(r) for r in leggi()]
    # due righe con le stesse coordinate e lo stesso nome (a meno del nome di battesimo) sono la stessa via: si conta una volta
    viste = {}
    vie = []
    doppie = []
    for v in tutte:
        chiave = (v["lon"], v["lat"])
        if chiave in viste and confronta(nomi_di(viste[chiave]["attuale"]), nomi_di(v["attuale"])) == "uguale":
            doppie.append({"id": v["id"], "attuale": v["attuale"], "uguale_a": viste[chiave]["id"]})
            continue
        viste[chiave] = v
        vie.append(v)
    os.makedirs(OUT, exist_ok=True)
    con_cambio = [v for v in vie if any(e["tipo"] == "cambio" for e in v["eventi"])]
    per_intervallo = collections.Counter()
    salti = collections.Counter()
    for v in vie:
        for e in v["eventi"]:
            if e["tipo"] != "cambio":
                continue
            (salti if e["salto"] else per_intervallo)["%s-%s" % (e["da"], e["a"])] += 1
    n_cambi = collections.Counter(sum(1 for e in v["eventi"] if e["tipo"] == "cambio") for v in vie)
    riep = {
        "righe_nel_file": len(tutte),
        "righe_doppie_escluse": doppie,
        "vie": len(vie),
        "con_almeno_un_cambio": len(con_cambio),
        "cambi_totali": sum(1 for v in vie for e in v["eventi"] if e["tipo"] == "cambio"),
        "per_numero_di_cambi": dict(sorted(n_cambi.items())),
        "per_intervallo": dict(per_intervallo),
        "con_salto_mappa_illeggibile": dict(salti),
        "parziali": sum(1 for v in vie for e in v["eventi"] if e["tipo"] == "parziale"),
        "nate_dopo_il_1884": [v["attuale"] for v in vie if any(e["tipo"] == "nasce" for e in v["eventi"])],
        "senza_nessun_cambio": [v["attuale"] for v in vie if not any(e["tipo"] == "cambio" for e in v["eventi"])],
        "celle_illeggibili": sum(1 for v in vie for c in v["celle"] if c["stato"] == "illeggibile"),
        "celle_non_esistenti": sum(1 for v in vie for c in v["celle"] if c["stato"] == "nonesiste"),
        "grafia_ignorata": [{"via": v["attuale"], "scritture": [r["nome"]] + r["varianti"]} for v in vie for r in v["righe"] if r.get("varianti")],
    }
    with open(os.path.join(OUT, "vie.json"), "w", encoding="utf-8") as f:
        json.dump(vie, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8") as f:
        json.dump(riep, f, ensure_ascii=False, indent=1)
    print(json.dumps(riep, ensure_ascii=False, indent=1))
    print()
    for v in vie:
        print(v["id"], v["attuale"])
        for r in v["righe"]:
            print("    %-10s %-8s %s %s" % ("%s-%s" % (r["da"], r["a"]), r["esito"], r["nome"], r.get("varianti") or ""))


main()
