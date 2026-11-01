"""Funzioni comuni (normalizzazione carica, titolo di studio, professione) per build.py e analisi.py."""
import re, unicodedata

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()

# ---------------------------------------------------------------- carica -> ruolo
def ruolo(desc):
    d = _norm(desc)
    if not d: return None
    if d.startswith(("commissar", "commissione", "sub commissar")): return None
    if d.startswith("delega funzioni"): return None
    if d == "sindaco": return "sindaco"
    if d.startswith(("vicesindaco", "assessore")): return "giunta"
    if d.startswith(("consigliere", "presidente del consiglio", "vicepresidente del consiglio")): return "consiglio"
    return None

def esterno(desc):
    return "non di origine elettiva" in _norm(desc)

# ---------------------------------------------------------------- titolo di studio -> 4 livelli
def titolo(t):
    d = _norm(t)
    if not d: return None
    if "laurea" in d or "post-laurea" in d or "post laurea" in d or "dottorato" in d: return "Laurea o più"
    if "media sup" in d or "secondo grado" in d or "post media super" in d: return "Diploma superiore"
    if "media inf" in d or "primo grado" in d or "post media infer" in d: return "Licenza media"
    if "elementare" in d or "primaria" in d or "nessun titolo" in d or "senza titolo" in d or "leggere e scrivere" in d or "prosciogl" in d: return "Elementare o nessun titolo"
    return "Altro"

# ---------------------------------------------------------------- professione -> categorie
PROF = [
 ("Non occupati (pensionati, studenti, casalinghe...)", r"condizioni non professionali|ritirat|pension|studenti|scolari|casaling|disoccup|inoccup|prima occupazione"),
 ("Avvocati e giuristi", r"avvocat|procurator|giuridic|legal|notai|magistrat"),
 ("Medici e sanità", r"dentist|assistenti sociali|medic|chirurg|odontoiatr|veterinar|farmacist|infermier|sanit|salute|radiograf|psicolog|biolog|ostetric|fisioterap"),
 ("Giornalisti, arte, sport", r"interpreti|atleti|pittori|scultori|giornalist|scrittor|pubblicist|artistic|sportiv|spettacolo|attori|musicist|linguistic|letterar|documental|fotograf"),
 ("Insegnanti e ricercatori", r"presidi|insegnant|docent|professori|professore|formazione e della ricerca|ricercator|universit|scolastic|maestr|educator|istruttor"),
 ("Forze dell'ordine e militari", r"forze armate|forze di polizia|carabinier|polizia|guardia|vigili|ufficiali|sottufficiali|militar"),
 ("Dirigenti e funzionari pubblici", r"(dirigent|direttor|funzionar|impiegat)\w*.*(pubblic|amministrazioni, organi)|amministrazioni, organi ed enti pubblici|pubblica amministrazione|enti pubblici"),
 ("Politica, sindacato, associazioni", r"componenti di assemblee|partiti|sindacat|organizzazioni o associazioni|associazioni a prevalente|religios|ecclesiastic"),
 ("Commercialisti, economisti, bancari", r"commercialist|ragionier|contabil|economi|bancari|gestionali|finanziar|assicura|credito e assicur|consulent"),
 ("Imprenditori e dirigenti d'azienda", r"imprenditor|titolari|amministratori delegati|direttori e categorie|direttori generali|dirigenti d|conduttori di aziende|gestori e responsabili|aziende private|amministratori, direttori|dirigent|manager"),
 ("Ingegneri, architetti, tecnici", r"ingegner|architett|geometr|periti|perito|agronom|geolog|chimic|fisic|matematic|informatic|tecnici|tecnico|urbanist|specialisti.*scienze"),
 ("Impiegati", r"impiegat"),
 ("Operai, artigiani, commercianti, agricoltori", r"commessi|stuccator|barbier|parrucchier|fabbri|panettier|barist|macchinist|carpentier|fonditor|pavimentator|macellator|spazzin|saldator|tornitor|ceramist|pasticcier|pescator|installator|capimastri|dattilograf|uscier|bidell|contonier|capistazione|capitreno|alesator|fresator|litograf|incisor|orafi|tagliator|operai|operaio|artigian|commerc|esercent|negozi|agricol|allevator|autist|conduttor|addett|lavorator|muratori|falegnam|elettricist|meccanic|idraulic|manovali|rappresentant|trasport|venditor|agricoltori|alberghi|ristorant"),
]
PROF_ALTRO = "Altro o non classificabile"
PROF_RE = [(n, re.compile(p)) for n, p in PROF]

def prof_cat(p):
    d = _norm(p)
    if not d: return None
    if "non altrove classificabili" in d or "non classificabil" in d: return PROF_ALTRO
    for n, r in PROF_RE:
        if r.search(d): return n
    return PROF_ALTRO
