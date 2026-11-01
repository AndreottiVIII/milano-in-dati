"""Beni confiscati a Milano - pulizia. Uso:
python -I -X utf8 build.py <A = .../milano-in-dati/beni-confiscati> <P = .../milano-in-dati>
Legge i file grezzi in A/raw, scrive tabelle pulite in A/pulito. Non scrive mai nomi di persone ne' nomi di aziende.
Geocodifica SOLO con il registro civici del Comune (ds634), niente servizi esterni."""
import sys, os, re, csv, json, unicodedata, collections, statistics, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anbsc_parse import parse_destinati

A, P = sys.argv[1], sys.argv[2]
RAW, OUT = os.path.join(A, "raw"), os.path.join(A, "pulito")
os.makedirs(OUT, exist_ok=True)
CIVICI = os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "civici", "estratto",
                      "ds634_civici_coordinategeografiche_20261001_final.csv")
ANNO_RIF = 2026


def rd(path, delim=","):
    return list(csv.DictReader(open(path, encoding="utf8", newline=""), delimiter=delim))


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} righe")


def fold(s):
    s = unicodedata.normalize("NFKC", s or "").replace("\xa0", " ")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# ------------------------------------------------------------------ indirizzi
STOP = {"DI", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DELLO", "DA", "D", "L", "IL", "LA", "LO", "LE", "I", "GLI", "DE", "E", "AL", "ALLA", "A", "IN", "N", "SS", "VIA", "VIALE", "PIAZZA", "PIAZZALE", "CORSO", "LARGO", "VICOLO", "ALZAIA", "STRADA", "VIALE", "RIPA"}
SUBST = {"FLLI": "FRATELLI", "FRLLI": "FRATELLI", "S": "SAN", "SANT": "SANT", "STE": "SAN", "GB": "GIOVANNI BATTISTA", "GBATTISTA": "GIOVANNI BATTISTA", "G": "", "PZA": "PIAZZA", "P": "", "V": "", "VLE": "VIALE", "C": "CORSO", "SO": "SEMPIONE"}
TIPI = ["VIALE", "VIA", "PIAZZALE", "PIAZZA", "CORSO", "LARGO", "VICOLO", "ALZAIA", "GALLERIA", "RIPA", "STRADA", "BASTIONI", "PIAZZETTA", "VIA PRIVATA"]


def tokens(name):
    s = fold(name).upper().replace("'", " ").replace("’", " ").replace("-", " ")
    s = re.sub(r"F\.?LLI", "FRATELLI", s)
    s = s.replace(".", " ")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    out = []
    for t in s.split():
        t = SUBST.get(t, t)
        for u in t.split():
            if u and u not in STOP and len(u) > 1:
                out.append(u)
    return tuple(out)


ROMANI = {"II": ("SECONDO", "DUE"), "III": ("TERZO", "TRE"), "XX": ("VENTI",), "XXV": ("VENTICINQUE",), "IV": ("QUARTO", "QUATTRO"), "VI": ("SESTO", "SEI")}


def split_indirizzo(raw):
    """-> (tipo, tokens_via, numero(int|None), lettera). Prende il primo indirizzo se ce ne sono due."""
    s = fold(raw).upper().strip()
    s = re.sub(r"\bP\.?LE\b\.?", "PIAZZALE", s)
    s = re.sub(r"\bV\.?LE\b\.?", "VIALE", s)
    s = re.sub(r"\bP\.?ZZA\b|\bP\.ZA\b|\bP\.?ZA\b", "PIAZZA", s)
    s = re.sub(r"\bC\.SO\b", "CORSO", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\(.*$", " ", s)
    s = s.split("/VIA")[0].split(". VIA")[0]
    s = re.sub(r"([A-Z])(\d)", r"\1 \2", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;")
    s = re.sub(r"\bNR\.?\s*", "N. ", s)
    s = s.replace("PIER DELLA FRANCESCA", "PIERO DELLA FRANCESCA")  # refuso nei dati ANBSC
    tipo = ""
    for t in TIPI:
        if s.startswith(t + " ") or s == t:
            tipo = t; break
    body = s[len(tipo):].strip()
    if tipo == "VIA" and body.startswith("RIPA "):
        tipo, body = "RIPA", body[5:]
    m = re.search(r"(?:\bN\.?\s*|[, ]\s*)(\d{1,4})(?:\s*/\s*([A-Z])\b|([A-Z])\b)?", body)
    num, let, name = None, "", body
    if m:
        name = body[: m.start()]
        num = int(m.group(1))
        let = (m.group(2) or m.group(3) or "")
        if let and let not in "ABCDEFGH":
            let = ""
    name = re.sub(r"\bN\.?$", "", name.strip(" ,"))
    return tipo, name, num, let


def variants(name):
    """token della via, piu' varianti con numerali romani (II -> secondo / due)."""
    base = tokens(name)
    out = [base]
    for i, t in enumerate(base):
        for alt in ROMANI.get(t, ()):
            out.append(base[:i] + (alt,) + base[i + 1:])
    return out


class Civici:
    def __init__(self, path):
        self.by_street = collections.defaultdict(lambda: {"pts": {}, "all": []})
        self.nome_uff = {}
        for r in rd(path, ";"):
            if not r["LONG_WGS84"]:
                continue
            tk = tokens(r["DESCRITTIVO"] or r["DENOMINAZIONE"])
            if not tk:
                continue
            key = (r["TIPO"].upper(), tk)
            self.nome_uff.setdefault(key, (r["TIPO"], r["DESCRITTIVO"] or r["DENOMINAZIONE"]))
            e = self.by_street[key]
            try:
                n = int(r["NUMERO"])
            except ValueError:
                continue
            pt = (float(r["LONG_WGS84"]), float(r["LAT_WGS84"]), r["NIL"], r["ID_NIL"], r["MUNICIPIO"], r["STATOCIVICO"] == "Applicato")
            e["pts"].setdefault((n, r["LETTERA"].upper().strip()), []).append(pt)
            e["all"].append(pt)
        self.tokset = {k: set(k[1]) for k in self.by_street}
        self.vocab = sorted({t for k in self.by_street for t in k[1]})

    def fix_typos(self, tk):
        import difflib
        out = []
        for t in tk:
            if t in self.vocab or len(t) < 5:
                out.append(t); continue
            c = difflib.get_close_matches(t, self.vocab, n=2, cutoff=0.86)
            out.append(c[0] if c else t)
        return tuple(out)

    def _search(self, tipo, tk, iniz=()):
        want = set(tk)
        cands = []
        for key, ts in self.tokset.items():
            inter = len(want & ts)
            if inter == 0:
                continue
            cont = inter / min(len(want), len(ts))
            if cont < 1:
                continue
            cands.append((key[0] == tipo.title() or key[0] == tipo, inter / len(want | ts), key))
        if not cands:
            return None
        if iniz:  # "Torre C." -> la via deve avere un'altra parola che comincia per C
            filt = [c for c in cands if all(any(t.startswith(i) for t in c[2][1] if t not in want) for i in iniz)]
            cands = filt or cands
        cands.sort(reverse=True)
        top = cands[0]
        if not top[0] and len(cands) > 1 and cands[1][1] == top[1]:
            return None  # ambiguo
        return top[2]

    def find_street(self, tipo, name):
        iniz = tuple(re.findall(r"(?<![A-Z])([A-Z])" + chr(92) + ".", name.upper()))
        for tk in variants(name):
            if not tk:
                continue
            for t2 in (tk, self.fix_typos(tk)):
                k = self._search(tipo, t2, iniz)
                if k:
                    return k
        return None

    def geocode(self, raw):
        tipo, name, num, let = split_indirizzo(raw)
        key = self.find_street(tipo, name)
        if not key:
            if "RONCHETTO SUL NAVIGLIO" in fold(raw).upper():  # localita', non via: solo il quartiere
                return dict(lon="", lat="", nil="RONCHETTO SUL NAVIGLIO - Q.RE LODOVICO IL MORO", id_nil="48", municipio="", qualita="quartiere_da_testo", via="", num=None, score=0)
            return None
        e = self.by_street[key]
        sc = 1
        for cand, q in (((num, let), "civico"), ((num, ""), "civico_senza_lettera")):
            if num is not None and cand in e["pts"]:
                pts = e["pts"][cand]
                pts = [p for p in pts if p[5]] or pts
                lon = sum(p[0] for p in pts) / len(pts); lat = sum(p[1] for p in pts) / len(pts)
                return dict(lon=round(lon, 6), lat=round(lat, 6), nil=pts[0][2], id_nil=pts[0][3], municipio=pts[0][4], qualita=q, via=" ".join(key[1]), num=num, score=sc, via_nome=self.nome_uff[key], civico_testo=(f"{num}{let}" if q == "civico" else str(num)))
        if num is not None:
            near = sorted(e["pts"], key=lambda k: abs(k[0] - num))[0]
            pts = e["pts"][near]
            return dict(lon=round(pts[0][0], 6), lat=round(pts[0][1], 6), nil=pts[0][2], id_nil=pts[0][3], municipio=pts[0][4], qualita="via_civico_vicino", via=" ".join(key[1]), num=num, score=sc, via_nome=self.nome_uff[key], civico_testo=str(num))
        pts = e["all"]
        nils = collections.Counter((p[2], p[3], p[4]) for p in pts).most_common(1)[0][0]  # NIL piu' frequente lungo la via
        return dict(lon=round(sum(p[0] for p in pts) / len(pts), 6), lat=round(sum(p[1] for p in pts) / len(pts), 6), nil=nils[0], id_nil=nils[1], municipio=nils[2], qualita="via_senza_numero", via=" ".join(key[1]), num=None, score=sc, via_nome=self.nome_uff[key], civico_testo="")


# ------------------------------------------------------------------ classificazioni
def tipo_immobile(cat, sub):
    c, s = fold(cat).lower(), fold(sub).lower()
    if "terreno" in c or s.startswith("terreno"):
        return "terreno"
    if "box" in s or "garage" in s or "posto auto" in s or "autorimessa" in s:
        return "box_posto_auto"
    if "appartamento" in s or "abitazione" in s or "villa" in s or "abit" in s:
        return "abitazione"
    if "negozio" in s or "bottega" in s or "laboratorio" in s or "ufficio" in s:
        return "negozio_laboratorio"
    if "magazzino" in s or "deposito" in s:
        return "magazzino"
    if "albergo" in s or "industriale" in s or "opificio" in s or "commerciale" in s:
        return "altro_commerciale_industriale"
    if "uso di abitazione" in c:
        return "altro_pertinenza"  # 'Altro' dentro la categoria abitazione: cantine, solai, ecc.
    return "altro"


def destinatario_tipo(d):
    d = fold(d).strip().lower()
    if d in ("comune", "comuni"):
        return "Comune"
    if d in ("provincia", "province"):
        return "Provincia / Citta metropolitana"
    if d in ("regione", "regioni"):
        return "Regione"
    if d in ("carabinieri", "guardia di finanza", "polizia di stato", "corpo forestale dello stato", "vigili del fuoco", "prefettura", "prefetture", "capitanerie di porto"):
        return "Forze dell'ordine e sicurezza"
    if d in ("ministeri", "amministrazioni statali", "agenzie fiscali", "universita", "genio civile"):
        return "Stato (ministeri, amministrazioni)"
    if d == "anbsc":
        return "ANBSC"
    if d in ("altro", "consorzi di enti territoriali"):
        return "Altro"
    return "non indicato"


def stato_destinati(tip):
    t = fold(tip).lower()
    if t.startswith("trasferimento") or t.startswith("mantenimento"):
        return "destinato"
    if t.startswith("immobili reintegrati"):
        return "uscito"
    return "uscito"  # vendita, liquidazione, distruzione/demolizione, revoca


def anno_di(s):
    m = re.search(r"(\d{4})", s or "")
    return int(m.group(1)) if m else ""


def tipo_ente_ds147(e):
    s = fold(e).lower()
    if not s.strip():
        return ""
    if "gestione diretta" in s:
        return "Comune (gestione diretta)"
    if s.startswith("ati ") or "ente capofila" in s or "capofila" in s or "mandataria" in s:
        # raggruppamento: si guarda la natura del capofila
        pass
    if "fondazione" in s:
        return "Fondazione"
    if "impresa sociale" in s or "imprese sociali" in s or "cooperativa" in s or "coop." in s or "coop sociale" in s or " coop " in s:
        return "Cooperativa / impresa sociale"
    if "soggetto privato" in s or re.search(r"\b(snc|srl|sas|impresa individuale)\b", s) or " di " in s.split(" via ")[0] and s.split(" via ")[0].isupper():
        return "Impresa / privato"
    if re.search(r"associazione|aps|odv|ets|onlus|circolo|croce rossa|abio|medicina democratica|comunita|sos italia", s):
        return "Associazione / volontariato"
    if s.startswith("ati"):
        return "Raggruppamento (ATI)"
    return "Altro"


def parse_date_it(s):
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", s or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


# ------------------------------------------------------------------ carico
print("carico civici...")
civ = Civici(CIVICI)
print("  strade:", len(civ.by_street))
NAZ = os.path.join(RAW, "anbsc_openregio")
_, di, bad = parse_destinati(os.path.join(NAZ, "nazionale_destinati_immobili.csv"))
_, da, bad2 = parse_destinati(os.path.join(NAZ, "nazionale_destinati_aziende.csv"))
gi = rd(os.path.join(NAZ, "nazionale_gestione_immobili.csv"))
ga = rd(os.path.join(NAZ, "nazionale_gestione_aziende.csv"))
print("destinati imm", len(di), "scartate", len(bad), "| aziende", len(da), len(bad2), "| gest imm", len(gi), "gest az", len(ga))

# ------------------------------------------------------------------ immobili ANBSC, Milano comune
imm = []
geo_cache = {}
for r in di:
    if r["comune"] != "Milano":
        continue
    g = None
    key = r["indirizzo"]
    if key not in geo_cache:
        geo_cache[key] = civ.geocode(key)
    g = geo_cache[key] or {}
    stato = stato_destinati(r["tipologia"])
    imm.append(dict(
        id=r["m_bene"], indirizzo_grezzo=key, fonte="ANBSC destinati", stato=stato,
        dettaglio_stato=r["tipologia"],
        tipo=tipo_immobile(r["categoria"], r["sottocategoria"]), categoria=r["categoria"], sottocategoria=r["sottocategoria"],
        destinatario_tipo=destinatario_tipo(r["destinatario"]), destinatario_originale=r["destinatario"], finalita=r["fine"],
        anno_destinazione=anno_di(r["decreto_anno"]) or anno_di(r["decreto_data"]),
        anno_procedura=anno_di(r["procedura"].split("/")[-1]) if "/" in r["procedura"] else "",
        tipo_procedura=r["fascicolo_tipo"],
        indirizzo=r["indirizzo"].strip(" ,"), lon=g.get("lon", ""), lat=g.get("lat", ""), nil=g.get("nil", ""), id_nil=g.get("id_nil", ""),
        qualita_posizione=g.get("qualita", "non_trovato"), via_abbinata=g.get("via", ""),
        via_ufficiale=" ".join(g["via_nome"]) if g.get("via_nome") else "", civico_testo=g.get("civico_testo", ""),
    ))
for r in gi:
    if r["nome_comune"] != "Milano":
        continue
    imm.append(dict(
        id=r["s_bene"], fonte="ANBSC in gestione", stato="in gestione",
        dettaglio_stato=r["provvedimento"] + (" - quota " + r["quota_confiscata"] if r["quota_confiscata"] else ""),
        tipo=tipo_immobile(r["categoria"], r["sottocategoria"]), categoria=fold(r["categoria"]).replace("  ", " ") if False else r["categoria"].replace("\xa0", " "), sottocategoria=r["sottocategoria"].replace("\xa0", " "),
        destinatario_tipo="", destinatario_originale="", finalita="", anno_destinazione="", anno_procedura="",
        tipo_procedura=r["tipologia_procedura"], indirizzo="", lon="", lat="", nil="", id_nil="", qualita_posizione="indirizzo_non_pubblicato", via_abbinata="", via_ufficiale="", civico_testo="",
    ))
F_IMM = ["id", "fonte", "stato", "dettaglio_stato", "tipo", "categoria", "sottocategoria", "destinatario_tipo", "destinatario_originale", "finalita", "anno_destinazione", "anno_procedura", "tipo_procedura", "indirizzo", "lon", "lat", "nil", "id_nil", "qualita_posizione", "via_abbinata", "via_ufficiale", "civico_testo"]
wr("immobili_anbsc_milano.csv", imm, F_IMM)

# ------------------------------------------------------------------ elenco del Comune (ds147)
ds = rd(os.path.join(RAW, "ds147", "ds147_elenco-beni-immobili-confiscati-06_2026.csv"), ";")
dec_by_addr = collections.defaultdict(list)  # (via abbinata, numero) -> anni decreto ANBSC destinati al Comune
for r in imm:
    if r["fonte"] == "ANBSC destinati" and r["indirizzo"] and r["destinatario_tipo"] == "Comune" and r["anno_destinazione"]:
        g0 = geo_cache.get(r["indirizzo_grezzo"]) or {}
        if g0.get("via") and g0.get("num") is not None:
            dec_by_addr[(g0["via"], g0["num"])].append(r["anno_destinazione"])
com = []
tipo_ds = {"appart.": "abitazione", "villetta schiera": "abitazione", "box": "box_posto_auto", "posto auto": "box_posto_auto", "locale comm.le": "negozio_laboratorio", "laborat. per arti e mestieri": "negozio_laboratorio", "uffici e studi privati": "negozio_laboratorio", "magazzino": "magazzino", "cantina": "altro_pertinenza", "solaio pertin.": "altro_pertinenza", "orto irrig.": "terreno", "semin. irrig.": "terreno", "semin.": "terreno", "terreno": "terreno", "bosco ceduo": "terreno"}
oggi = datetime.date(2026, 6, 30)  # data dell'elenco ("giugno 2026")
for i, r in enumerate(ds, 1):
    ente, nota = r["Ente assegnatario"].strip(), r["note"].strip()
    nl = fold(nota).lower()
    if not ente or ente == "":
        if "attesa" in nl or "nuovo avviso" in nl or "nuova acquisizione" in nl:
            stato = "in attesa di assegnazione"
        elif "manutenzione" in nl or "problematiche" in nl:
            stato = "non assegnato: lavori o problemi"
        else:
            stato = "non assegnato: nessuna informazione"
    elif "gestione diretta" in fold(ente).lower():
        stato = "gestione diretta del Comune"
    else:
        stato = "assegnato a terzi"
    periodo = r["Periodo contratto Dal / al"]
    ds_ = re.findall(r"\d{1,2}[./]\d{1,2}[./]\d{4}", periodo or "")
    d_ini = parse_date_it(ds_[0]) if ds_ else None
    d_fin = parse_date_it(ds_[1]) if len(ds_) > 1 else None
    addr = r["Indirizzo"].strip()
    if addr not in geo_cache:
        geo_cache[addr] = civ.geocode(addr)
    g = geo_cache[addr] or {}
    anni = dec_by_addr.get((g.get("via"), g.get("num")), []) if g.get("num") is not None else []
    anno_dest = min(anni) if anni else ""
    anni_dist = sorted(set(anni))
    com.append(dict(
        id=f"ds147-{i}", tipo=tipo_ds.get(r["Tipologia"].strip(), "altro"), tipo_originale=r["Tipologia"].strip(), municipio=r["Municipio"],
        finalita=r["Tipologia destinazione"].strip().strip('"'), stato_uso=stato, ente_tipo=tipo_ente_ds147(ente),
        anno_inizio_contratto=d_ini.year if d_ini else "", anno_fine_contratto=d_fin.year if d_fin else "",
        contratto_scaduto_a_giugno_2026="si" if d_fin and d_fin < oggi else ("no" if d_fin else ""),
        durata_anni_dichiarata=r["Durata anni  contr."].strip(),
        anno_destinazione_anbsc=anno_dest, anni_destinazione_diversi=len(anni_dist) if anni_dist else "",
        anni_da_destinazione=(ANNO_RIF - anno_dest) if anno_dest else "",
        anni_destinazione_contratto=(d_ini.year - anno_dest) if (anno_dest and d_ini) else "",
        indirizzo=addr, lon=g.get("lon", ""), lat=g.get("lat", ""), nil=g.get("nil", ""), id_nil=g.get("id_nil", ""),
        qualita_posizione=g.get("qualita", "non_trovato"), via_abbinata=g.get("via", ""),
        via_ufficiale=" ".join(g["via_nome"]) if g.get("via_nome") else "", civico_testo=g.get("civico_testo", ""),
        nota_comune_breve=("nuova acquisizione 2026" if "nuova acquisizione" in nl else ""),
    ))
F_COM = ["id", "tipo", "tipo_originale", "municipio", "finalita", "stato_uso", "ente_tipo", "anno_inizio_contratto", "anno_fine_contratto", "contratto_scaduto_a_giugno_2026", "durata_anni_dichiarata", "anno_destinazione_anbsc", "anni_destinazione_diversi", "anni_da_destinazione", "anni_destinazione_contratto", "indirizzo", "lon", "lat", "nil", "id_nil", "qualita_posizione", "via_abbinata", "via_ufficiale", "civico_testo", "nota_comune_breve"]
wr("comune_ds147_milano.csv", com, F_COM)

# ------------------------------------------------------------------ aziende
uj = json.load(open(os.path.join(RAW, "aziende_confiscate_unioncamere", "aziende-confiscate-unioncamere.json"), encoding="utf8"))["@graph"]
aj = json.load(open(os.path.join(RAW, "aziende_confiscate_unioncamere", "aziende-confiscate-anbsc.json"), encoding="utf8"))["@graph"]
amap = {x["@id"]: x for x in aj}
az_uc = []
for k, x in enumerate(sorted(uj, key=lambda z: z["@id"]), 1):
    sl = x["sedeLegale"]
    if sl["comune"].upper() != "MILANO":
        continue
    sez = x["ateco"]["settoreAteco"]
    az_uc.append(dict(
        n=len(az_uc) + 1, stato_amministrativo=amap.get(x["@id"], {}).get("iterAmministrativoAttivo", ""),
        stato_attivita=x["statoAttivita"], natura_giuridica=x["naturaGiuridica"],
        ateco_sezione=sez.split(" ")[0], ateco_sezione_descrizione=sez.split(" ", 1)[1] if " " in sez else "",
        ateco_codice=x["ateco"]["codiceAteco"], ateco_attivita=x["ateco"]["sezioneAteco"].split(" ", 1)[1] if " " in x["ateco"]["sezioneAteco"] else x["ateco"]["sezioneAteco"],
    ))
wr("aziende_unioncamere_sede_milano.csv", az_uc, ["n", "stato_amministrativo", "stato_attivita", "natura_giuridica", "ateco_sezione", "ateco_sezione_descrizione", "ateco_codice", "ateco_attivita"])
az = []
for r in ga:
    if r["nome_comune"] == "Milano":
        az.append(dict(n=len(az) + 1, fonte="ANBSC in gestione", stato="in gestione", dettaglio=r["provvedimento"], settore=r["sottocategoria"].replace("\xa0", " "), forma_giuridica=r["categoria"], anno_destinazione="", anno_procedura="", tipo_procedura=r["tipologia_procedura"]))
for r in da:
    if r["comune"] == "Milano":
        az.append(dict(n=len(az) + 1, fonte="ANBSC destinate", stato="uscita" if True else "", dettaglio=r["tipologia"], settore=r["sottocategoria"], forma_giuridica=r["categoria"], anno_destinazione=anno_di(r["decreto_anno"]), anno_procedura=anno_di(r["procedura"].split("/")[-1]) if "/" in r["procedura"] else "", tipo_procedura=r["fascicolo_tipo"]))
wr("aziende_anbsc_milano.csv", az, ["n", "fonte", "stato", "dettaglio", "settore", "forma_giuridica", "anno_destinazione", "anno_procedura", "tipo_procedura"])

# ------------------------------------------------------------------ tutti i comuni (per confronti), senza indirizzi
tot = []
for r in di:
    tot.append(dict(comune=r["comune"], provincia=r["provincia"], regione=r["regione"], genere="immobili", stato=stato_destinati(r["tipologia"]), dettaglio=r["tipologia"], tipo=tipo_immobile(r["categoria"], r["sottocategoria"]), anno_destinazione=anno_di(r["decreto_anno"])))
for r in gi:
    tot.append(dict(comune=r["nome_comune"], provincia=r["nome_provincia"], regione=r["nome_regione"], genere="immobili", stato="in gestione", dettaglio=r["provvedimento"], tipo=tipo_immobile(r["categoria"], r["sottocategoria"]), anno_destinazione=""))
for r in da:
    tot.append(dict(comune=r["comune"], provincia=r["provincia"], regione=r["regione"], genere="aziende", stato="uscita", dettaglio=r["tipologia"], tipo="azienda", anno_destinazione=anno_di(r["decreto_anno"])))
for r in ga:
    tot.append(dict(comune=r["nome_comune"], provincia=r["nome_provincia"], regione=r["nome_regione"], genere="aziende", stato="in gestione", dettaglio=r["provvedimento"], tipo="azienda", anno_destinazione=""))
wr("tutti_i_beni_per_comune.csv", tot, ["comune", "provincia", "regione", "genere", "stato", "dettaglio", "tipo", "anno_destinazione"])

# report geocodifica
q = collections.Counter(r["qualita_posizione"] for r in imm if r["fonte"] == "ANBSC destinati")
q2 = collections.Counter(r["qualita_posizione"] for r in com)
json.dump({"geocodifica_anbsc_destinati": q, "geocodifica_ds147": q2, "righe_scartate_parser": [len(bad), len(bad2)]}, open(os.path.join(OUT, "controlli_build.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("geocodifica ANBSC:", dict(q), "\ngeocodifica ds147:", dict(q2))
