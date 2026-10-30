"""Registrazioni sonore alla Scala (catalogo SBN) -> sbn/sbn_registrazioni.csv  (SOLO esecuzioni dal vivo/storiche al Teatro alla Scala; niente registrazioni in studio).
Legge sbn/_registrazioni_candidati.json (ricerche, scritto da sbn_registrazioni_cerca.py) e le schede complete in raw/sbn/full
(scaricate da sbn_registrazioni_cerca.py per 377 candidati e da sbn_registrazioni_tutte.py per gli altri ~2.600).
Scrive:
  sbn/sbn_registrazioni.csv           solo le esecuzioni alla Scala (dal vivo): data ("Registrazione dal vivo, Milano, Teatro alla Scala, 10 maggio 1961"), luogo, titolo, compositore, direttore, interpreti con voce/ruolo dove c'e'
  sbn/_registrazioni_tutte_schede.csv tutte le schede lette (anche studio, antologie, senza data), con il motivo dell'esclusione
Uso (dalla cartella scala/):  python -I -X utf8 scripts/sbn_registrazioni.py"""
import sys, os, re, csv, json, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_nomi as N
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SBN = os.path.join(ROOT, "sbn")

RX_NUM = re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4}|\d{2})(?!\d)")
RX_LIVE = re.compile(r"dal vivo|\blive\b|in diretta|registrazione storica|registrazione (?:di|della) (?:una )?(?:rappresentazione|serata|recita)|regiatrazione dal vivo", re.I)
RX_INEDITA = re.compile(r"inedit", re.I)
RX_STUDIO = re.compile(r"\bstudio\b|auditorium|abanella|casa verdi|sala di registrazione|chiesa|basilica|in studio|studios?\b", re.I)
RX_SCALA_LUOGO = re.compile(r"(?:teatro alla scala|alla scala|la scala di milano|scala, milano|scala di milano|al teatro alla scala|presso la scala)", re.I)
RX_ORCH_SCALA = re.compile(r"(orchestra|coro|chorus|choeur|professori|solisti|filarmonica|corpo di ballo|soli).{0,45}scala|scala.{0,30}(orchestra|chorus|choeur)|teatro alla scala", re.I)
RX_MILANO = re.compile(r"\bmilano\b", re.I)
RX_ALTROVE = re.compile(r"\b(?:salisburgo|salzburg|vienna|parigi|paris|londra|london|tokyo|tokio|new york|berlino|berlin|bruxelles|brussels|mosca|moscow|edimburgo|edinburgh|cremona|verona|pesaro|torino|roma|napoli|firenze|venezia|bologna|genova|palermo|bari|montpellier|lucerna|luzern|amburgo|hamburg|monaco di baviera|monaco|monte ?carlo|buenos aires|osaka|pechino|beijing|san francisco|chicago|lisbona|madrid|barcellona|amsterdam|teatro (?:regio|la fenice|san carlo|massimo|comunale|carcano|lirico|del maggio)|sala (?:verdi|grande)|carnegie|royal albert|covent garden|musikverein|konzerthaus)\b", re.I)

def date_reg(testi):
    """-> (iso, tipo) dalla prima data completa nelle note/titolo; tipo = 'giorno' | 'mese' | 'anno' | ''."""
    for t in testi:
        for d in N.date_in_testo(t):
            return d["iso"], "giorno"
        for m in RX_NUM.finditer(t):
            g, mo, a = int(m.group(1)), int(m.group(2)), m.group(3)
            a = int(a) if len(a) == 4 else (1900 + int(a) if int(a) > 30 else 2000 + int(a))
            if 1 <= g <= 31 and 1 <= mo <= 12 and 1900 < a < 2027:
                return "%04d-%02d-%02d" % (a, mo, g), "giorno"
    for t in testi:
        m = N.mese_in_testo(t)
        if m: return m, "mese"
    for t in testi:
        if not re.search(r"regist|dal vivo|live|storica|effettuat", t, re.I): continue
        t2 = re.sub(r"(?:℗|©|\(p\)|\bp|\bc)\s*(?:19|20)\d\d", " ", t)          # anni di pubblicazione/copyright: non sono l'anno dell'esecuzione
        m = re.search(r"(?<!\d)(19[4-9]\d|20[0-2]\d)(?!\d)", t2)
        if m: return m.group(1), "anno"
    return "", ""

def senza_doppi(lst):
    visti, out = set(), []
    for n_ in lst:
        k = N.chiave_libera(n_)[0]
        if k and k not in visti: visti.add(k); out.append(n_)
    return out

def leggi(f, bid):
    note = f.get("note", []) or []
    titolo = f["titolo"]
    testi_note = [n for n in note if re.search(r"regist|dal vivo|live|esecuzione|concerto|rappresentazione|stagione|storica|inedit|effettuat", n, re.I)]
    blob_note = " ".join(note)
    live = bool(RX_LIVE.search(blob_note + " " + titolo))
    inedita = bool(RX_INEDITA.search(blob_note))
    # persone con ruolo e voce
    dirett, interp, comp, voci = [], [], [], {}
    for raw in f.get("nomi", []) or []:
        nome, chiave, ini = N.nome_pulito(raw)
        ruolo, dett, tag = N.ruolo_da_tag(raw)
        if N.ENTE.search(nome): continue
        if ruolo == "direttore": dirett.append(nome)
        elif ruolo == "interprete": interp.append(nome); voci[nome] = dett if dett and not dett.startswith(("cantante", "interprete", "codice")) else ""
        elif ruolo == "compositore": comp.append(nome)
        elif not ruolo:
            for rr, s_ in N.dichiarazioni(titolo):
                if N.parola_in(chiave, s_):
                    {"direttore": dirett, "interprete": interp, "compositore": comp}.get(rr, []).append(nome)
    if not dirett:
        for rr, s_ in N.dichiarazioni(titolo):
            if rr == "direttore": dirett += N.spezza_nomi(s_)
    for rr, s_ in N.dichiarazioni(titolo):
        if rr == "interprete": interp += N.spezza_nomi(s_)
    for m in re.finditer(r"(?:\[?(?:interpreti|cantanti)\]?\s*:?|;\s*con)\s+([^;]+)", titolo, re.I):
        interp += N.spezza_nomi(re.sub(r"\[[^\]]*\]", " ", m.group(1)))
    # maestri del coro (etichetta SBN o dicitura nel titolo): non sono direttori d'orchestra
    coristi = [N.nome_pulito(raw)[0] for raw in f.get("nomi", []) or [] if N.ruolo_da_tag(raw)[0] == "maestro del coro"]
    for m in re.finditer(r"(?:maestro del coro|direttore del coro|maestro dei cori|chorus master)\s*:?\s*([A-ZÀ-Ý][\w'’.-]*(?: [A-ZÀ-Ý][\w'’.-]*){0,3})|([A-ZÀ-Ý][\w'’.-]*(?: [A-ZÀ-Ý][\w'’.-]*){0,3}),?\s*(?:maestro del coro|direttore del coro)", titolo, re.I):
        coristi.append(m.group(1) or m.group(2))
    ck = {N.chiave_libera(c)[0] for c in coristi if c}
    dirett = [d for d in dirett if N.chiave_libera(d)[0] not in ck]
    interp = senza_doppi([x for x in interp if x not in dirett and N.chiave_libera(x)[0] not in ck]); dirett = senza_doppi(dirett)
    # ruolo del personaggio: "Nome (Ruolo)" o "Ruolo: Nome" nel titolo
    ruoli_pers = {}
    for m in re.finditer(r"([A-ZÀ-Ý][\w'’.-]+(?: [A-ZÀ-Ý][\w'’.-]+){0,2})\s*\(([A-ZÀ-Ýa-zà-ÿ' ]{3,25})\)", titolo):
        ruoli_pers[m.group(1)] = m.group(2)
    # luogo
    scala_nelle_note = bool(RX_SCALA_LUOGO.search(blob_note))
    scala_nel_titolo_luogo = bool(re.search(r"(?:live|dal vivo|recorded|registrat\w*) (?:at|alla|al|a)\s+(?:the\s+)?(?:teatro\s+)?(?:alla\s+)?la scala|teatro alla scala,? (?:milano|stagione|\d)", titolo, re.I))
    studio = bool(RX_STUDIO.search(blob_note)) and not live
    altrove = bool(RX_ALTROVE.search(blob_note)) and not scala_nelle_note
    orch_scala = bool(RX_ORCH_SCALA.search(titolo + " " + " ".join(f.get("nomi", []))))
    milano = bool(RX_MILANO.search(blob_note))
    iso, tipo_d = date_reg(testi_note + [titolo]) if (live or inedita or scala_nelle_note) else ("", "")
    if scala_nelle_note: luogo, cert = "Teatro alla Scala", "esplicito"
    elif scala_nel_titolo_luogo: luogo, cert = "Teatro alla Scala", "esplicito (titolo)"
    elif live and milano and orch_scala and not altrove: luogo, cert = "Milano (Teatro alla Scala probabile)", "probabile"
    elif live and orch_scala and not altrove and iso: luogo, cert = "(non indicato)", "da_verificare"
    else: luogo, cert = "", ""
    # motivo di esclusione/inclusione
    if studio: motivo = "studio"
    elif altrove: motivo = "altro luogo"
    elif scala_nelle_note and not live and not inedita: motivo = "alla Scala ma dal vivo non dichiarato (forse studio)"
    elif not (live or (inedita and scala_nelle_note)): motivo = "non dal vivo"
    elif not cert: motivo = "luogo non riconducibile alla Scala"
    elif cert == "da_verificare": motivo = "luogo non indicato"
    else: motivo = ""
    m_anno = re.search(r"(19[0-9]\d|20[0-2]\d)", f.get("pubblicazione", "") or "")
    # titolo dell'opera: parte prima della prima " / " (responsabilita')
    opera = re.sub(r"\s+", " ", titolo.split(" / ")[0]).strip(" .")
    opera = re.sub(r"^\d+\s*:\s*", "", opera)
    return dict(
        bid=bid, titolo=re.sub(r"\s+", " ", titolo)[:200], opera=opera[:120], compositore="; ".join(dict.fromkeys(comp)), direttore="; ".join(dict.fromkeys(dirett)),
        interpreti="; ".join(dict.fromkeys(i + (" (" + voci.get(i, "") + ")" if voci.get(i) else "") for i in interp)),
        ruoli_personaggi="; ".join("%s: %s" % (r, n) for n, r in ruoli_pers.items()),
        dal_vivo="si" if live else ("inedita" if inedita else "no"), data_registrazione=iso, data_tipo=tipo_d, luogo=luogo, luogo_certezza=cert,
        nota_registrazione=" | ".join(testi_note)[:300], scala_come="esecutore" if orch_scala else "luogo",
        anno_pubblicazione=m_anno.group(1) if m_anno else "", etichetta=(f.get("pubblicazione") or "")[:80],
        url="https://opac.sbn.it/bid/" + bid.replace("IT\\ICCU\\", "").replace("\\", ""), n_biblioteche=len(f.get("localizzazioni", []) or []), esclusa=motivo)

def main():
    cand = json.load(open(os.path.join(SBN, "_registrazioni_candidati.json"), encoding="utf8"))
    full = N.carica_full()
    tutte = []
    for r in cand:
        bid = r["codiceIdentificativo"]; f = full.get(bid)
        if not f: continue
        if not (f.get("tipo") or r.get("tipo") or "").lower().startswith("registrazione sonora"): continue
        tutte.append(leggi(f, bid))
    COLS = list(tutte[0].keys())
    with open(os.path.join(SBN, "_registrazioni_tutte_schede.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(tutte)
    scala = [r for r in tutte if not r["esclusa"]]
    scala.sort(key=lambda r: (r["data_registrazione"] or "9999", r["opera"]))
    with open(os.path.join(SBN, "sbn_registrazioni.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=[c for c in COLS if c != "esclusa"]); w.writeheader()
        for r in scala:
            r = dict(r); r.pop("esclusa"); w.writerow(r)
    print("schede lette:", len(tutte), "su candidati", len(cand))
    print("esclusioni:", dict(collections.Counter(r["esclusa"] or "TENUTA" for r in tutte)))
    print("tenute (esecuzioni alla Scala):", len(scala), "| luogo esplicito:", sum(1 for r in scala if r["luogo_certezza"].startswith("esplicito")), "probabile:", sum(1 for r in scala if r["luogo_certezza"] == "probabile"))
    print("con giorno:", sum(1 for r in scala if r["data_tipo"] == "giorno"), "mese:", sum(1 for r in scala if r["data_tipo"] == "mese"), "solo anno:", sum(1 for r in scala if r["data_tipo"] == "anno"), "senza data:", sum(1 for r in scala if not r["data_tipo"]))
    print("con direttore:", sum(1 for r in scala if r["direttore"]), "con interpreti:", sum(1 for r in scala if r["interpreti"]), "con compositore:", sum(1 for r in scala if r["compositore"]))
    # confronto con i programmi di sala: stessa data
    prog = list(csv.DictReader(open(os.path.join(SBN, "sbn_programmi.csv"), encoding="utf-8-sig")))
    per_data = collections.defaultdict(list)
    for p in prog:
        for d in (p.get("date_scala") or p.get("data_iso") or "").split(";"):
            if d: per_data[d].append(p)
    print("registrazioni con giorno che coincide con la data di un programma di sala:", sum(1 for r in scala if r["data_tipo"] == "giorno" and r["data_registrazione"] in per_data))

if __name__ == "__main__":
    main()
