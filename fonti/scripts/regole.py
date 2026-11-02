"""Regole di riconoscimento: chi pubblica i dati (editori), con quale licenza, in quale data."""
import re

# ---------------------------------------------------------------- editori
# (nome normalizzato, gruppo, espressione regolare). L'ordine conta: a parità di posizione vince il primo.
_M = r"[’'`]"  # apostrofi
EDITORI = [
    ("ARPA Lombardia", "Regione e agenzie lombarde", r"\bARPA\b(?: Lombardia)?|\bArpa\b"),
    ("Comune di Milano", "Comune di Milano", r"Comune di Milano|dati\.comune\.milano\.it|gisportal\.comune\.milano\.it|portale dati del Comune|Open Data del Comune|dati aperti del Comune|dati del Comune"),
    ("AMAT", "Comune di Milano", r"\bAMAT\b|Agenzia Mobilit[àa]"),
    ("ATM", "Trasporti", r"\bATM\b"),
    ("MM Spa", "Comune di Milano", r"\bMM (?:S\.?p\.?A\.?|spa)\b|\bMM\b(?! ?[0-9])|Metropolitane Milanesi"),
    ("ATS Milano", "Regione e agenzie lombarde", r"\bATS\b(?: (?:della )?(?:Citt[àa] Metropolitana di )?Milano)?"),
    ("Regione Lombardia", "Regione e agenzie lombarde", r"Regione Lombardia|PoliS-Lombardia|dati\.lombardia\.it|Open Data Lombardia|Regione\b(?= su dati\.lombardia)"),
    ("Trenord", "Trasporti", r"\bTrenord\b"),
    ("ISTAT", "Istat", r"\bISTAT\b|\bIstat\b|demo\.istat\.it|IstatData|esploradati"),
    ("MEF", "Ministeri", r"\bMEF\b|Ministero dell" + _M + r"Economia(?: e delle Finanze)?|Dipartimento delle Finanze"),
    ("Ministero dell’Interno", "Ministeri", r"Ministero dell" + _M + r"Interno|\bViminale\b"),
    ("Ministero della Giustizia", "Ministeri", r"Ministero della [Gg]iustizia"),
    ("Ministero dell’Istruzione e del Merito", "Ministeri", r"Ministero dell" + _M + r"Istruzione(?: e del Merito)?|\bMIM\b|\bMIUR\b"),
    ("Ministero della Salute", "Ministeri", r"Ministero della Salute|dati\.salute\.gov\.it"),
    ("Ministero delle Infrastrutture e dei Trasporti", "Ministeri", r"Ministero delle [Ii]nfrastrutture(?: e dei [Tt]rasporti)?|Motorizzazione"),
    ("Ministero della Cultura", "Ministeri", r"Ministero della Cultura|\bMiC\b"),
    ("Ministero delle Imprese e del Made in Italy", "Ministeri", r"\bMIMIT\b|Ministero delle Imprese"),
    ("Ministero dell’Ambiente", "Ministeri", r"\bMASE\b|Ministero dell" + _M + r"Ambiente"),
    ("Ministero del Lavoro", "Ministeri", r"Ministero del Lavoro"),
    ("Ministero della Difesa", "Ministeri", r"Ministero della Difesa"),
    ("Dipartimento della Protezione civile", "Ministeri", r"Protezione [Cc]ivile"),
    ("Polizia di Stato", "Ministeri", r"Polizia di Stato|\bSDI\b"),
    ("ISPRA", "Enti nazionali", r"\bISPRA\b"),
    ("ISS", "Enti nazionali", r"Istituto Superiore di Sanit[àa]"),
    ("INPS", "Enti nazionali", r"\bINPS\b"),
    ("INAIL", "Enti nazionali", r"\bINAIL\b"),
    ("Banca d’Italia", "Enti nazionali", r"Banca d" + _M + r"Italia"),
    ("ACI", "Enti nazionali", r"\bACI\b|Autoritratto"),
    ("ANAC", "Enti nazionali", r"\bANAC\b|dati\.anticorruzione\.it"),
    ("ANBSC", "Enti nazionali", r"\bANBSC\b|OpenRe\.?G\.?I\.?O"),
    ("ENAC", "Enti nazionali", r"\bENAC\b"),
    ("ANMIG", "Associazioni e privati", r"\bANMIG\b"),
    ("Agenzia delle Entrate – OMI", "Enti nazionali", r"Agenzia delle Entrate|\bOMI\b|Osservatorio del Mercato Immobiliare|GEOPOI"),
    ("Unioncamere e InfoCamere", "Enti nazionali", r"\bUnioncamere\b|InfoCamere|Movimprese|Camera di commercio"),
    ("OpenCoesione e OpenCUP", "Enti nazionali", r"OpenCoesione|OpenCUP|Italia Domani"),
    ("ICCD – Catalogo generale dei beni culturali", "Enti nazionali", r"\bICCD\b|\bArCo\b|catalogo\.beniculturali"),
    ("Camera dei deputati e Senato", "Enti nazionali", r"Camera dei [Dd]eputati|\bSenato\b"),
    ("Eurostat", "Fonti internazionali", r"\bEurostat\b"),
    ("NOAA", "Fonti internazionali", r"\bNOAA\b|\bGHCN\b|\bGSOD\b"),
    ("ECA&D", "Fonti internazionali", r"ECA&D|ECA&amp;D|\bECAD\b"),
    ("Inside Airbnb", "Fonti internazionali", r"Inside Airbnb"),
    ("OpenStreetMap", "Fonti collaborative", r"OpenStreetMap|\bOSM\b|Geofabrik|Overpass"),
    ("Wikidata", "Fonti collaborative", r"\bWikidata\b"),
    ("Wikimedia", "Fonti collaborative", r"Wikipedia|Wikimedia|Wikisource|Wikimedia Commons"),
    ("Open Library e Library of Congress", "Fonti collaborative", r"Open Library|Library of Congress"),
    ("Greenpeace Italia", "Associazioni e privati", r"Greenpeace"),
    ("Legambiente", "Associazioni e privati", r"Legambiente"),
    ("Confcommercio", "Associazioni e privati", r"Confcommercio"),
    ("Libera e onData", "Associazioni e privati", r"Confiscati Bene|\bonData\b|\bLibera\b"),
    ("Forestami", "Associazioni e privati", r"Forestami|forestami\.org"),
    ("TomTom", "Associazioni e privati", r"TomTom"),
    ("Antigone", "Associazioni e privati", r"\bAntigone\b"),
    ("INVALSI", "Enti nazionali", r"\bINVALSI\b"),
    ("Comitato Pietre d’inciampo Milano", "Associazioni e privati", r"Comitato per le Pietre d.inciampo|pietredinciampomilano"),
    ("CDEC", "Associazioni e privati", r"\bCDEC\b"),
    ("A. Trentini (Zenodo)", "Associazioni e privati", r"Trentini|Zenodo"),
    ("ALER", "Regione e agenzie lombarde", r"\bALER\b"),
]
EDITORI_RE = [(n, g, re.compile(p)) for n, g, p in EDITORI]
GRUPPO = {n: g for n, g, _ in EDITORI}

# Casi in cui la menzione di un editore NON apre una nuova fonte (è solo la provenienza di un dato).
NON_APRE = re.compile(
    r"(?:\bdati|\bdato|\bfonte originale|\boriginali?|\bsu dati|\btramite|\bvia|\bda copie? di|"
    r"\b(?:ripubblicat\w+|pubblicat\w+|elaborat\w+|raccolt\w+|forniti|forniti)\s+(?:dal|dalla|dall" + _M + r"|da|dai|dagli)|"
    r"\bdal portale di|\bdal sito di|\bcon dati|\bper conto di)\s*(?:di |del |della |dell" + _M + r"|degli |dei )?$", re.I)

# Legami fra due menzioni vicine: stesso blocco di fonte ("Comune di Milano / AMAT", "ISTAT e Comune di Milano")
CONGIUNZIONE = re.compile(r"^\s*(?:/|e|ed|,|–|-|\+|e il|e la|e l[’']|con)\s*$")

# ---------------------------------------------------------------- licenze
LIC_TUTTI = "Tutti i diritti riservati — solo cifre citate"
LIC_CITAZIONE = "Uso con citazione, non aperta"
LIC_ANMIG = "Autorizzazione dichiarata (ANMIG)"
LIC_NC = "CC BY-NC (solo uso non commerciale)"
LIC_PD = "Dominio pubblico"
LIC_NONDICH = "Non indicata"

# (tipo, versione-regex opzionale, regex di riconoscimento). L'ordine è di priorità nella stessa frase.
LICENZE = [
    (LIC_TUTTI, re.compile(r"tutti i diritti riservati|diritto d[’']autore|contenuti protetti|vietano di riprodurre", re.I)),
    (LIC_ANMIG, re.compile(r"autorizzazione[^.]{0,40}ANMIG|ANMIG[^.]{0,60}autorizz", re.I)),
    ("CC BY-SA", re.compile(r"CC[- ]?BY[- ]?SA|Creative Commons Attribut\w+[- ]Share\w+|Attribution[- ]ShareAlike|Attribuzione[^.;]{0,20}Condividi", re.I)),
    (LIC_NC, re.compile(r"CC[- ]?BY[- ]?NC|Creative Commons Attribut\w+ Non ?Commercial|Non Commercial|per ricerca e istruzione non commerciali|solo per finalit[àa] non commerciali|finalit[àa] non commerciali", re.I)),
    ("CC0", re.compile(r"\bCC[- ]?0\b|Creative Commons 1\.0 Universal|Creative Commons CC0|dedica Creative Commons CC0|\bCC0", re.I)),
    ("CC BY", re.compile(r"CC[- ]?BY|Creative Commons Attribut|Attribuzione 4|Creative Commons Attribuzione", re.I)),
    ("IODL 2.0", re.compile(r"\bIODL\b|Italian Open Data License", re.I)),
    ("ODbL", re.compile(r"\bODbL\b", re.I)),
    ("NLOD 2.0", re.compile(r"\bNLOD\b", re.I)),
    (LIC_PD, re.compile(r"dominio pubblico|public domain|dati pubblici|dati statunitensi", re.I)),
    (LIC_CITAZIONE, re.compile(
        r"Risoluzione 40|non (?:indica|indicano|ha|hanno|dichiara|dichiarano|riporta|prevede)[^.;]{0,30}licenz|"
        r"non c[’']è[^.;]{0,25}licenz|nessuna licenza|senza licenza|licenza non (?:indicata|dichiarata|esplicita|presente)|"
        r"senza licenza esplicita|nessuna licenza (?:è )?dichiarata|non (?:è|sono) dichiarat[ae][^.;]{0,20}licenz|"
        r"condizioni di utilizzo|condizioni d[’']uso|note legali[^.;]{0,60}(?:permettono|consentono)|"
        r"consentiti previa citazione|a scopo divulgativo|uso libero|statistiche ufficiali pubbliche|"
        r"sono statistiche ufficiali|riportiamo solo i numeri|citiamo soltanto|solo alcuni numeri|si citano soltanto", re.I)),
]

# licenza "d'ufficio" quando la frase non la scrive (è nota dall'editore): marcata come tale.
LICENZA_DEFAULT = {
    "OpenStreetMap": "ODbL",
    "Wikidata": "CC0",
    "Wikimedia": "CC BY-SA",
    "ECA&D": LIC_NC,
    "NOAA": LIC_PD,
    "Inside Airbnb": "CC BY",
}

# versione tipica dentro il testo della licenza (per mostrare "CC BY 4.0")
VERSIONE = re.compile(r"(?:CC[- ]?BY(?:[- ]?(?:SA|NC))?|IODL|NLOD|Attribuzione|Attribution|License|Licence)\s*v?(\d\.\d(?:\s?IT)?)")

# ---------------------------------------------------------------- date
MESI = {m: i + 1 for i, m in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}
_MESI = "|".join(MESI)
DATA_TESTO = rf"(\d{{1,2}})\s*°?\s+({_MESI})\s+(20\d\d)"
DATA_RANGE = rf"(\d{{1,2}})\s*[-–]\s*(\d{{1,2}})\s+({_MESI})\s+(20\d\d)"
DATA_NUM = r"(\d{1,2})[/.](\d{1,2})[/.](20\d\d)"
DATA_ISO = r"(20\d\d)-(\d\d)-(\d\d)"
DATA_ANY = re.compile("|".join([DATA_RANGE, DATA_TESTO, DATA_NUM, DATA_ISO]), re.I)
PAROLA_SCARICO = re.compile(
    r"scaric\w+|interrogat\w+|consultat\w+|lett[aoei]\b|estratt\w+|raccolt\w+|calcolat\w+|prelevat\w+|dati del|aggiornato al|download", re.I)
DS_ID = re.compile(r"\bds\d+(?:\s*[–-]\s*(?:ds)?\d+)?", re.I)
SOCRATA = re.compile(r"\b(?=[a-z0-9]*\d)(?=[a-z0-9]*[a-z])[a-z0-9]{4}-[a-z0-9]{4}\b")
EUROSTAT = re.compile(r"\b(?:avia|demo|ilc|nama|prc|tour|lfst|une|hlth|road|rail)_[a-z0-9_]+")
DOMINIO = re.compile(r"\b(?:[a-z0-9-]+\.)+(?:it|org|com|eu|gov|net|info|edu)\b(?:/[\w./-]*)?", re.I)

# ---------------------------------------------------------------- limiti e "non esistono"
LIMITI_TITOLO = re.compile(r"limiti|che cosa non|cosa non (?:si|dice|pu)|non si (?:sa|può|puo)|cautele|cosa questi dati non|prima di leggere", re.I)
NON_ESISTE = re.compile(
    r"non esist\w+|non (?:è|e’|e'|sono|viene|vengono) (?:stat\w+ )?(?:pubblicat\w+|disponibil\w+|aperti|aperto|resi pubblic\w+|diffus\w+|messi?)|"
    r"non (?:pubblicano|pubblica|rende pubblic\w+|rendono pubblic\w+)|non c[’']è (?:alcun|nessun|un)\b[^.]{0,40}(?:dato|dati|elenco|registro|serie|archivio)|"
    r"non ci sono (?:dati|numeri|serie)[^.]{0,30}(?:pubblic|aperti|disponibil)|nessun (?:dato|elenco|registro|archivio) (?:aperto|pubblico|pubblicato)|"
    r"dato (?:non )?(?:aperto|pubblico)|non (?:è|sono) (?:in )?(?:forma|formato) aperta?|non (?:è|sono) (?:in )?open data|"
    r"(?:richiede|serve|servirebbe|occorre)[^.]{0,25}(?:richiesta|accesso agli atti|FOIA)|accesso agli atti|FOIA", re.I)
