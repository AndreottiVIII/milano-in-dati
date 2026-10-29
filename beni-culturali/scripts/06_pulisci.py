"""Fase 2, passo 1: pulizia di beni_culturali_milano.csv -> pulito/beni_milano.csv (+ log dei problemi in JSON).

uso: python -I 06_pulisci.py <csv_fase1> <confine_comune.geojson> <cartella_output>

Chiave: iri (id non e' unico). Una riga per scheda. Tutti i controlli contano i casi e li scrivono in
<output>/problemi_conteggi.json, che poi finisce in problemi.md (scritto a mano con questi numeri).
"""
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from shapely.geometry import Point, shape
from shapely.prepared import prep

TIPO = {
    "OA": "opera d'arte: dipinto, scultura, oggetto",
    "D": "disegno",
    "RA": "reperto archeologico",
    "S": "stampa",
    "PST": "strumento scientifico o tecnologico",
    "A": "architettura",
    "F": "fotografia",
    "BDM": "bene demoetnoantropologico",
    "OAC": "opera d'arte contemporanea",
    "MA": "monumento archeologico",
    "NU": "moneta o medaglia (numismatica)",
    "CA": "complesso archeologico",
    "PG": "parco o giardino",
    "BNZ": "bene naturalistico (zoologia)",
    "SMO": "strumento musicale",
    "VeAC": "veste o tessuto antico (sigla VeAC)",
}

QUALIF = ["attribuito", "bottega", "scuola", "maniera", "cerchia", "e aiuti", "ex salviati"]

# unioni esplicite di nomi di luoghi (varianti dello stesso posto, trovate guardando l'elenco)
LUOGHI = {
    "Palazzo Reala": "Palazzo Reale",
    "San Gottardo in Corte": "Chiesa di San Gottardo in Corte",
    "S. Lorenzo Maggiore": "Basilica di San Lorenzo Maggiore",
    "Basilica di S. Ambrogio": "Basilica di Sant'Ambrogio",
    "Basilica minore romana di S.Ambrogio": "Basilica di Sant'Ambrogio",
    "Basilica minore romana di S. Ambrogio": "Basilica di Sant'Ambrogio",
    "Basilica minore romana S.Ambrogio": "Basilica di Sant'Ambrogio",
    "Basilica di S. Eustorgio": "Basilica di Sant'Eustorgio",
    "Basilica dei SS. Apostoli e Nazaro Maggiore": "Basilica dei Santi Apostoli e Nazaro Maggiore",
    "Santi Apostoli e Nazaro Maggiore": "Basilica dei Santi Apostoli e Nazaro Maggiore",
    "Accademia di Belle Arti": "Accademia di Belle Arti di Brera",
    "Palazzo di Brera": "Accademia di Belle Arti di Brera",
    "chiesa di S. Sepolcro": "Chiesa del Santo Sepolcro",
}
LUOGO_VUOTO = {"", "contenitore fisico", "non identificabile"}

P = Counter()  # contatori dei problemi
ES = defaultdict(list)  # esempi


def nota(chiave, esempio=None):
    P[chiave] += 1
    if esempio is not None and len(ES[chiave]) < 4:
        ES[chiave].append(esempio)


def norm_sp(x):
    return re.sub(r"\s+", " ", x.replace(" ", " ")).strip()


def sans_acc(x):
    return "".join(c for c in unicodedata.normalize("NFD", x) if unicodedata.category(c) != "Mn")


def dedupe_pipe(x, chiave=None):
    """toglie i valori ripetuti in un campo 'a | b | a'"""
    if not x:
        return x
    vals = [norm_sp(v) for v in x.split(" | ") if norm_sp(v)]
    out, seen = [], set()
    for v in vals:
        k = v.lower()
        if k in seen:
            if chiave:
                nota("valori_doppi_nel_campo_" + chiave)
            continue
        seen.add(k)
        out.append(v)
    return " | ".join(out)


# ---------------------------------------------------------------- datazioni
RE_SIDE = r"(?P<q{n}>ca |post |ante |\(\?\) )?(?P<y{n}>\d{{1,4}})(?:/(?P<m{n}>\d\d)/(?P<d{n}>\d\d))?(?: (?P<e{n}>a\.C|d\.C))?"
RE_RANGE = re.compile("^" + RE_SIDE.format(n=1) + r"\s*-\s*" + RE_SIDE.format(n=2) + "$")
RE_HALF_L = re.compile(r"^" + RE_SIDE.format(n=1) + r"\s*-\s*$")
RE_HALF_R = re.compile(r"^-\s*" + RE_SIDE.format(n=2) + "$")


def parse_date(txt):
    """ritorna (anno_inizio, anno_fine, incerta, nota) del PRIMO intervallo (quello principale).
    Anni a.C. negativi. None se non interpretabile."""
    if not txt:
        return None, None, 0, "vuota"
    first = txt.split(" | ")[0].strip()
    first = re.sub(r"(?<![A-Za-z])a\.? ?[cC](?![A-Za-z])\.?", "a.C", first)      # a.c / a. C / a C -> a.C
    first = re.sub(r"(?<![A-Za-z])d\.? ?[cC](?![A-Za-z])\.?", "d.C", first)
    first = re.sub(r"(?<![\d)])\.(?=\d)", "", first)           # '.360 a.C' -> '360 a.C'
    first = re.sub(r"^-(?=\d+\s*-)", "", first)               # '-450-425 a.C' -> '450-425 a.C'
    m = RE_RANGE.match(first)
    if m:
        y1, y2 = int(m["y1"]), int(m["y2"])
        e1, e2 = m["e1"], m["e2"]
        bc2 = e2 == "a.C"
        bc1 = e1 == "a.C" or (e1 is None and bc2 and y1 >= y2)
        if e1 is None and e2 == "d.C":
            bc1 = False
        a = -y1 if bc1 else y1
        b = -y2 if bc2 else y2
        inc = int(bool(m["q1"] or m["q2"]))
        if a > b:
            if e1 is None and e2 is None and y1 < 1000:
                return None, None, inc, "intervallo invertito senza era"
            a, b = b, a
            return a, b, inc, "intervallo invertito"
        return a, b, inc, ""
    m = RE_HALF_L.match(first)
    if m:
        y = int(m["y1"])
        y = -y if m["e1"] == "a.C" else y
        return y, None, 1, "solo inizio"
    m = RE_HALF_R.match(first)
    if m:
        y = int(m["y2"])
        y = -y if m["e2"] == "a.C" else y
        return None, y, 1, "solo fine"
    return None, None, 0, "formato non riconosciuto"


ROM = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
       (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def romano(n):
    s = ""
    for v, r in ROM:
        while n >= v:
            s += r
            n -= v
    return s


def secolo(a, b):
    """secolo del punto medio dell'intervallo (se l'intervallo e' piu' lungo di 300 anni: nessun secolo)"""
    if a is None and b is None:
        return None, "", ""
    if a is None or b is None:
        mid = a if a is not None else b
        nt = "secolo da un solo estremo"
    else:
        if b - a > 300:
            return None, "", "intervallo oltre 300 anni"
        mid = (a + b) / 2
        nt = ""
    if -1 < mid < 1:
        return None, "", "a cavallo dell'anno 0"
    if mid > 0:
        c = int((mid - 1) // 100 + 1)
        return c, romano(c) + " secolo", nt
    c = int((-mid - 1) // 100 + 1)
    return -c, romano(c) + " secolo a.C.", nt


# ---------------------------------------------------------------- titoli
def costruisci_forme(righe):
    """parentesi finali dei titoli: se compare >= 15 volte e' una forma di catalogazione, non parte del titolo"""
    c = Counter()
    for r in righe:
        m = re.search(r"\(([^()]*)\)\s*$", r["titolo"])
        if m:
            c[m.group(1).strip()] += 1
    return {k for k, v in c.items() if v >= 15 and k}


BASE_FORME = {"opera isolata", "serie", "elemento d'insieme", "frammento", "ciclo", "insieme", "coppia",
              "complesso decorativo"}


def pulisci_titolo(t, forme):
    t = norm_sp(t)
    # architettura: 'Casa Galimberti (casa)casa ( )' -> 'Casa Galimberti (casa)'
    m = re.match(r"^(.*?\([^()]+\))\s*[^()]*\s*\(\s*\)$", t)
    if m:
        nota("titoli_architettura_con_coda_vuota", t)
        t = m.group(1).strip()
    t = re.sub(r"\s*\(\s*\)\s*$", "", t)  # 'casa ( )' -> 'casa'
    # 'X, X' -> 'X'
    if ", " in t:
        meta = len(t) // 2
        a, b = t[:meta].rstrip(", "), t[meta:].lstrip(", ")
        if a and a == b:
            nota("titoli_ripetuti_due_volte", t)
            t = a
    m = re.search(r"\s*\(([^()]*)\)\s*$", t)
    if m:
        inner = m.group(1).strip()
        if inner in forme:
            t2 = t[: m.start()].strip()
            if t2:
                return t2
        parti = [x.strip() for x in inner.split(",")]
        if len(parti) >= 2 and parti[-1] in BASE_FORME:
            return (t[: m.start()] + " (" + ", ".join(parti[:-1]) + ")").strip()
    return t


# ---------------------------------------------------------------- autori
def spezza_autore(a):
    """'Luigi Cagnola (attribuito)' -> ('Luigi Cagnola', 'attribuito')"""
    q = ""
    m = re.search(r"\(([^()]*)\)\s*$", a)
    if m:
        q = m.group(1).strip()
        a = a[: m.start()].strip()
    a = norm_sp(a).strip(" ,;")
    return a, q


def bel_nome(n):
    if n.isupper() or n.islower():
        return n.title()
    return n


def chiave_nome(n):
    toks = re.findall(r"[a-z0-9]+", sans_acc(n).lower())
    return " ".join(sorted(toks))


# ---------------------------------------------------------------- luoghi
def parse_luogo_attuale(loc):
    """ritorna (luogo_nome, indirizzo, precisione)"""
    loc = norm_sp(loc)
    if not loc:
        return "", "", "nessuna"
    loc = re.sub(r"\s*\[Milano\]$", "", loc)
    if loc.lower().startswith("sito:"):
        nome = loc[5:].strip()
        nome = re.sub(r"^Contenitore fisico di:\s*", "", nome)
        nome = LUOGHI.get(nome, nome)
        if nome.lower() in LUOGO_VUOTO:
            return "", "", "nessuna"
        return nome, "", "sito"
    m = re.match(r"^(?:ITALIA|Italia)(?:,)?\s*(?:Lombardia\s+)?(?:MI\s+)?Milano\s*(.*)$", loc)
    if m:
        rest = m.group(1).strip(" ,")
        if not rest:
            return "", "", "solo_comune"
        return "", rest, "indirizzo"
    return loc, "", "sito"


def indirizzo_bene_pulito(ind):
    ind = re.sub(r"\s*\[Milano\]$", "", norm_sp(ind))
    parti = [p.strip() for p in ind.split(",")]
    tolgo = {"europa", "italia", "lombardia", "mi", "milano", ""}
    resto = [p for p in parti if p.lower() not in tolgo]
    return ", ".join(resto)


# ---------------------------------------------------------------- main
def main(src, confine_path, outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(src, encoding="utf-8", newline="") as f:
        righe = list(csv.DictReader(f))
    n_in = len(righe)

    # 1. unicita' e righe doppie
    iri_seen, cod_seen, vistes = set(), set(), 0
    uniche = []
    for r in righe:
        if r["iri"] in iri_seen or r["codice_catalogo"] in cod_seen:
            nota("riga_doppia_scartata", r["iri"])
            continue
        iri_seen.add(r["iri"])
        cod_seen.add(r["codice_catalogo"])
        uniche.append(r)
    righe = uniche

    # confine del Comune
    g = json.load(open(confine_path, encoding="utf-8"))
    poly = shape(g["features"][0]["geometry"])
    ppoly = prep(poly)

    forme = costruisci_forme(righe)

    # 2. autori: prima passata per scegliere la forma piu' frequente di ogni persona
    varianti = defaultdict(Counter)  # chiave -> Counter(forma)
    parsed_aut = {}
    for r in righe:
        lst = []
        if r["autore"]:
            for a in r["autore"].split(" | "):
                nome, q = spezza_autore(a)
                if not nome:
                    continue
                lst.append((nome, q))
                varianti[chiave_nome(nome)][bel_nome(nome)] += 1
        parsed_aut[r["iri"]] = lst
    canon = {}
    n_unioni = 0
    for k, c in varianti.items():
        best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        canon[k] = best
        if len(c) > 1:
            n_unioni += 1
            if len(ES["autori_forme_unite"]) < 12:
                ES["autori_forme_unite"].append(" / ".join(f"{a} ({n})" for a, n in c.most_common()))
    P["autori_persone_con_piu_forme"] = n_unioni

    out_rows = []
    for r in righe:
        o = {}
        o["iri"] = r["iri"]
        o["id_catalogo"] = r["id"]
        o["codice_catalogo"] = r["codice_catalogo"]
        o["ambito"] = r["ambito"]
        o["sede_milano"] = 1 if r["ambito"] == "sede_milano" else 0
        ts = r["tipo_scheda"]
        o["tipo_scheda"] = ts
        o["tipo_scheda_etichetta"] = TIPO.get(ts, ts)
        o["classe_bene"] = r["classe_bene"]

        # titolo / soggetto
        tit_orig = dedupe_pipe(r["titolo"], "titolo")
        o["titolo"] = pulisci_titolo(tit_orig, forme)
        if o["titolo"] != norm_sp(r["titolo"]):
            nota("titoli_con_forma_tolta")
        o["tipo_oggetto"] = norm_sp(r["tipo_oggetto"])
        o["soggetto"] = dedupe_pipe(r["soggetto"], "soggetto").lower() if r["soggetto"] else ""
        if not r["soggetto"]:
            nota("soggetto_mancante")

        # autori
        o["autore_originale"] = r["autore"]
        nomi, quals = [], []
        for nome, q in parsed_aut[r["iri"]]:
            cn = canon[chiave_nome(nome)]
            if cn not in nomi:
                nomi.append(cn)
            if q and q.lower() not in [x.lower() for x in quals]:
                quals.append(q)
        o["autori"] = " | ".join(nomi)
        o["autore_principale"] = nomi[0] if nomi else ""
        o["autore_qualifica"] = " | ".join(quals)
        o["n_autori"] = len(nomi)
        if not nomi:
            nota("autore_mancante")

        # datazione
        dt = dedupe_pipe(r["datazione"], "datazione")
        o["datazione_testo"] = dt
        a, b, inc, nt = parse_date(dt)
        o["anno_inizio"] = "" if a is None else a
        o["anno_fine"] = "" if b is None else b
        o["data_incerta"] = inc if dt else ""
        sec, sec_et, nt2 = secolo(a, b)
        o["secolo"] = "" if sec is None else sec
        o["secolo_etichetta"] = sec_et
        note_d = "; ".join(x for x in (nt, nt2) if x and x != "vuota")
        o["datazione_nota"] = note_d
        if nt == "vuota":
            nota("datazione_mancante")
        elif nt in ("formato non riconosciuto",):
            nota("datazione_non_interpretata", dt)
        elif nt:
            nota("datazione_" + nt.replace(" ", "_"), dt)
        if nt2:
            nota("datazione_" + nt2.replace(" ", "_"), dt)
        if dt and " | " in dt:
            nota("datazione_con_piu_intervalli")
        if a is not None and b is not None and (a > 2023 or b > 2023):
            nota("datazione_oltre_2023", dt)

        # materia
        mt = dedupe_pipe(r["materia_tecnica"], "materia")
        o["materia_tecnica"] = mt
        o["materia_prima"] = norm_sp(mt.split(" | ")[0].split("/")[0]) if mt else ""
        if not mt:
            nota("materia_mancante")

        # istituzione
        ist = norm_sp(r["istituzione"]).replace("’", "'")
        o["istituzione_iri"] = ""
        if not ist:
            o["istituzione"] = "non indicata"
        elif ist.startswith("CulturalInstituteOrSite/"):
            o["istituzione"] = "non indicata"
            o["istituzione_iri"] = ist
            nota("istituzione_senza_nome_nel_dump")
        else:
            o["istituzione"] = ist
        if o["istituzione"] == "non indicata" and not ist:
            nota("istituzione_vuota")

        # luogo
        nome_l, ind_l, prec = parse_luogo_attuale(r["localizzazione_attuale"]) if r["ambito"] == "sede_milano" else ("", "", "nessuna")
        ind_bene = indirizzo_bene_pulito(r["indirizzo_bene"]) if r["ambito"] == "sede_milano" else ""
        if ind_bene and not ind_l:
            ind_l = ind_bene
            if prec in ("nessuna", "solo_comune"):
                prec = "indirizzo"
        o["luogo_attuale"] = nome_l
        o["indirizzo"] = ind_l
        o["ubicazione_precisione"] = prec if r["ambito"] == "sede_milano" else "luogo_collegato"
        o["altre_localizzazioni"] = r["altre_localizzazioni"]
        o["codice_sito"] = r["codice_sito"]
        if r["ambito"] == "sede_milano":
            if prec == "nessuna":
                nota("sede_milano_senza_luogo_ne_indirizzo")
            elif prec == "solo_comune":
                nota("sede_milano_solo_comune")

        # coordinate
        lat, lon = r["lat"], r["long"]
        o["lat"] = o["long"] = ""
        o["coord_scambiate_corrette"] = 0
        o["coord_in_comune"] = ""
        if lat and lon:
            try:
                la, lo = float(lat), float(lon)
            except ValueError:
                la = lo = None
                nota("coordinate_non_numeriche", f"{lat},{lon}")
            if la is not None:
                if la < 20 and lo > 40:  # scambiate
                    la, lo = lo, la
                    o["coord_scambiate_corrette"] = 1
                    nota("coordinate_scambiate", r["iri"])
                inside = ppoly.contains(Point(lo, la))
                o["lat"], o["long"] = f"{la:.6f}", f"{lo:.6f}"
                o["coord_in_comune"] = 1 if inside else 0
                if r["ambito"] == "sede_milano" and not inside:
                    nota("sede_milano_coordinate_fuori_comune", f"{r['iri']} {la},{lo}")
                if r["ambito"] != "sede_milano":
                    nota("solo_luogo_collegato_con_coordinate" + ("_fuori_comune" if not inside else "_in_comune"))
        elif r["ambito"] == "sede_milano":
            nota("sede_milano_senza_coordinate")

        # link
        o["url_catalogo"] = "https://catalogo.beniculturali.it/detail/" + r["iri"]
        o["url_catalogo_dump"] = r["url_catalogo"]
        o["proprieta"] = norm_sp(r["diritti"])
        o["ultimo_aggiornamento"] = r["ultimo_aggiornamento"][:10]
        out_rows.append(o)

    # duplicati "quasi": schede diverse con tutti i campi descrittivi uguali
    chiave_q = Counter()
    for o in out_rows:
        if o["sede_milano"]:
            chiave_q[(o["titolo"], o["autori"], o["datazione_testo"], o["materia_tecnica"], o["soggetto"],
                      o["istituzione"], o["lat"], o["long"], o["tipo_scheda"])] += 1
    P["schede_quasi_identiche_gruppi"] = sum(1 for v in chiave_q.values() if v > 1)
    P["schede_quasi_identiche_schede"] = sum(v for v in chiave_q.values() if v > 1)
    P["schede_quasi_identiche_gruppo_max"] = max(chiave_q.values())
    ids = Counter(o["id_catalogo"] for o in out_rows if o["sede_milano"])
    P["id_catalogo_condiviso_tra_schede"] = sum(v for v in ids.values() if v > 1)

    cols = list(out_rows[0].keys())
    with open(os.path.join(outdir, "beni_milano.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)
    P["righe_in_ingresso"] = n_in
    P["righe_in_uscita"] = len(out_rows)
    P["forme_tolte_dai_titoli"] = len(forme)
    json.dump({"conteggi": dict(P), "esempi": dict(ES), "forme_titolo": sorted(forme)},
              open(os.path.join(outdir, "problemi_conteggi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(dict(P), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
