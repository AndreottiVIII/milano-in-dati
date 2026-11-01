"""Funzioni comuni per leggere la cache Wikidata (raw/wikidata/entities_cache.json). Importata dagli altri programmi."""
import json, re, unicodedata

class WD:
    def __init__(self, path):
        self.C = json.load(open(path, encoding="utf8"))
    def lab(self, q):
        e = self.C.get(q)
        if not e or "missing" in e: return q
        l = e.get("labels", {})
        return (l.get("it") or l.get("en") or {}).get("value", q)
    def desc(self, q):
        e = self.C.get(q) or {}
        d = e.get("descriptions", {})
        return (d.get("it") or d.get("en") or {}).get("value", "")
    def ids(self, q, p):
        e = self.C.get(q) or {}
        out = []
        for c in e.get("claims", {}).get(p, []):
            if c.get("rank") == "deprecated": continue
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v: out.append(v["id"])
        return out
    def times(self, q, p):
        """lista di (anno:int, precisione:int) per un'affermazione di tipo data"""
        e = self.C.get(q) or {}
        out = []
        for c in e.get("claims", {}).get(p, []):
            if c.get("rank") == "deprecated": continue
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "time" in v:
                m = re.match(r"([+-])(\d+)-", v["time"])
                if m:
                    y = int(m.group(2)) * (-1 if m.group(1) == "-" else 1)
                    out.append((y, v.get("precision", 9)))
        return out
    def coord(self, q):
        e = self.C.get(q) or {}
        for c in e.get("claims", {}).get("P625", []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "latitude" in v: return v["longitude"], v["latitude"]
        return None
    def is_human(self, q):
        return "Q5" in self.ids(q, "P31")
    def nonreal(self, q):
        """True se e' una figura biblica, mitologica, leggendaria o di fantasia (anche se Wikidata la marca 'umano')"""
        bad = {"Q20643955", "Q15632617", "Q4271324", "Q13002315", "Q95074", "Q178885", "Q22988604", "Q21070598", "Q116119467", "Q3658341", "Q24334685"}
        return bool(set(self.ids(q, "P31")) & bad)

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.replace("'", " ").replace("’", " "))
    return re.sub(r"\s+", " ", s).strip()

# --- genere
G = {"Q6581097": "uomo", "Q6581072": "donna", "Q2449503": "altro", "Q15145778": "uomo", "Q15145779": "donna", "Q1052281": "altro", "Q48270": "altro", "Q1097630": "altro", "Q189125": "altro", "Q12964198": "altro", "Q505371": "altro"}

# --- gruppi di professioni (regole: la prima occupazione di Wikidata, nell'ordine in cui e' scritta, che rientra in un gruppo)
GRP = [
 ("sovrano o nobile", r"sovran|\bre\b|regina|imperator|imperatrice|monarca|duca|duchessa|principe|principessa|nobil|aristocrati|conte\b|contessa|marchese|signore di|doge|dinasta|granduca"),
 ("religioso o santo", r"santo|santa|martire|beato|beata|vescovo|arcivescovo|cardinale|papa\b|sacerdote|monaco|monaca|religios|teologo|missionari|frate|suora|prelato|presbitero|abate|badessa|eremita|predicatore|mistic"),
 ("militare o forze dell'ordine", r"poliziott|agente di polizia|carabinier|militare|soldato|generale|ufficiale|ammiraglio|condottiero|comandante|aviatore|alpino|carabinier|bersagliere|maresciallo|capitano|colonnello|stratega|guerrier|marinaio|pilota militare|eroe di guerra|aviator"),
 ("patriota o resistente", r"patriota|partigian|rivoluzionari|resistente|antifascista|irredentista|cospirator|esule|combattente|garibaldino|martire della liberta|vittima"),
 ("artista", r"pittore|scultore|architetto|musicista|compositore|cantante|attore|attrice|regista|direttore d|fotografo|designer|disegnatore|incisore|cantautore|illustratore|artista|ballerin|coreografo|violinist|pianista|organista|librettista|scenografo|vignettista|fumettista|ceramista|orafo|decoratore|cantante lirico|soprano|tenore|baritono|doppiatore|presentatore|cabarettista|comico|commediografo"),
 ("scienziato o medico", r"scienziato|fisico|chimico|matematico|medico|ingegnere|inventore|astronomo|biologo|naturalista|geologo|botanico|chirurgo|farmacista|psichiatra|anatomista|fisiolog|esploratore|geografo|ricercatore|professore|docente|pedagogista|economista|statistico|psicolog|neurolog|igienista|pediatra|cartografo"),
 ("scrittore o giornalista", r"scrittore|scrittrice|poeta|poetessa|drammaturgo|giornalista|saggista|traduttore|storico|filosofo|umanista|letterato|romanziere|editore|critico|pubblicista|commediografo|paroliere|biografo|memorialista|narratore"),
 ("politico o giurista", r"politico|politica|statista|deputato|senatore|sindaco|diplomatico|giurista|magistrato|avvocato|sindacalista|ministro|prefetto|funzionario|amministratore|notaio|giudice|parlamentare|consigliere|attivista|presidente|governatore|podesta|legislatore|capo di stato"),
 ("imprenditore o benefattore", r"imprenditore|industriale|banchiere|filantropo|mecenate|commerciante|benefattor|finanziere|manager|dirigente|collezionista|costruttore|orologiaio|editore|proprietario"),
 ("sportivo", r"calciatore|ciclista|atleta|sportivo|pilota|allenatore|tennista|nuotatore|schermidore|pugile|alpinista|giocatore|motociclista|podista|sciatore|canottiere|cestista|rugbista|velista|automobilista"),
]
GRP_VITTIMA = ("vittima o caduto", r"vittima|ucciso|condannat[oa] a morte|deportat|caduto|assassinat|giustiziat")
def group_of(occ_labels, desc=""):
    for lab in occ_labels:
        l = lab.lower()
        for g, rx in GRP:
            if re.search(rx, l): return g
    # senza professione utile in Wikidata: si prova con la descrizione breve
    d = (desc or "").lower()
    if d:
        if re.search(GRP_VITTIMA[1], d): return GRP_VITTIMA[0]
        for g, rx in GRP:
            if re.search(rx, d): return g
    return "altro o non indicata" if occ_labels else "non indicata"
