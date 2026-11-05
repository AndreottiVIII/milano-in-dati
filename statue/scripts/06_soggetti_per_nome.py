"""Per le opere senza un soggetto collegato in Wikidata/OSM, ricava un nome candidato dal titolo ("Monumento a X", "Targa a X", ...)
e lo cerca su Wikidata (wbsearchentities, CC0). Si accetta solo una corrispondenza ESATTA del nome con una persona (P31 = umano).
Il sesso NON si deduce dal nome: si legge poi P21 della persona trovata.
Uso: python -I -X utf8 06_soggetti_per_nome.py <statue>
Legge pulito/_lavoro/stage1.json, scrive pulito/_lavoro/stage2.json e pulito/_lavoro/ricerche_soggetti.csv; cache in raw/wikidata/search_cache.json"""
import sys, os, re, json, time, collections, requests
S = sys.argv[1]
sys.path.insert(0, os.path.join(S, "scripts"))
from wdlib import WD, norm
UA = {"User-Agent": "milano-in-dati/0.3 (milano-in-dati; research on statues and monuments in Milan)"}
CF = os.path.join(S, "raw/wikidata/entities_cache.json")
wd = WD(CF)
SF = os.path.join(S, "raw/wikidata/search_cache.json")
sc = json.load(open(SF, encoding="utf8")) if os.path.exists(SF) else {}
works = json.load(open(os.path.join(S, "pulito/_lavoro/stage1.json"), encoding="utf8"))

TITLES = r"(?:il |la |lo |l'|l’)?(?:vescovo|cardinale?|contessa|marchese|duca|magistrato|monsignore|generale|gen\.|dottor|dott\.|ingegner|ing\.|professor|prof\.|avvocato|avv\.|padre|don|cardinal|beato|beata|papa|re|regina|conte|principe|maestro|senatore|on\.|comandante|capitano|colonnello|maggiore|tenente|sottotenente|partigiano|alpino|cavalier|cav\.|monsignor|mons\.|santa|san|sant'|sant’|santo)"
HEAD = re.compile(r"^(?:il |la |lo |l'|l’)?(?:monumento funebre|monumento commemorativo|monumento equestre|monumento|statua equestre|statua|busto|lapide commemorativa|lapide|targa commemorativa|targa|cippo|stele|medaglione|memoriale|"
                  r"fontana|tomba|cenotafio|sarcofago|mausoleo|arca|lapide con epitaffio|epigrafe|bassorilievo|rilievo|ritratto)(?: commemorativ[oa]| equestre| funebre| marmore[oa]| bronze[oa])?\s+(?:di riconoscenza\s+)?"
                  r"(?:(?:ad|a|di|del|dello|della|per|al|allo|alla|agli|ai|alle|in memoria di|in onore di|dedicat[oa] a)\s+|d'\s*|d’\s*)(.+)$", re.I)
NOT_PERSON = re.compile(r"caduti|martiri|alpini|bersaglieri|resistenza|partigiani|vittime|deportati|lavoratori|guerra|battaglia|insurrezione|cinque giornate|libert|patria|italia|pace|popolo|fanti|marinai|aviatori|carabinieri|polizia|soldati|combattenti|internati|lavoro|donne|bambini|giustizia|duomo|santuario|chiesa|via |piazza|porta |lega|reggimento|brigata|divisione|battaglione|comune di|stazione|ospedale|scuola|universit|ponte|navigli", re.I)

def cands(w):
    """nomi candidati da cercare"""
    out = []
    n = (w["nome"] or "").strip()
    n = re.sub(r"\s*\((?:Milano|[^)]*)\)\s*$", "", n).strip()
    if w["tipo"] in ("monumento ai caduti", "murale o opera decorativa", "fontana"): return out
    m = HEAD.match(n)
    if m:
        x = m.group(1).strip()
    elif w.get("osm") and w["tipo"] in ("lapide o targa", "busto", "statua", "monumento", "scultura o installazione", "cippo, stele o pietra") and re.fullmatch(r"[A-ZÀ-Ý][\w’'.\-]+(?: (?:[A-ZÀ-Ý][\w’'.\-]+|de|di|da|del|della|dei|von|van|le|la|d’|d'))+", n):
        x = n  # nome proprio di persona usato come titolo (frequente nelle lapidi OSM)
    else:
        return out
    x = re.sub(r"\s*\([^)]*\)", "", x).strip(" .,")
    if not x or NOT_PERSON.search(x) or len(x.split()) > 7: return out
    out.append(x)
    if "," in x: out.append(x.split(",")[0].strip())
    y = re.sub(r"^" + TITLES + r"\s+", "", x, flags=re.I)
    if y != x and len(y.split()) >= 2: out.append(y)
    # "Cognome Nome"  -> non ribaltiamo: sarebbe una supposizione
    seen = []
    for z in out:
        if z not in seen and len(z) > 3: seen.append(z)
    return seen

def search(q):
    if q in sc: return sc[q]
    for a in range(8):
        r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbsearchentities", search=q, language="it", uselang="it", type="item", limit=10, format="json"), headers=UA, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        if "search" in j and "error" not in j:
            sc[q] = [dict(id=x["id"], label=x.get("label", ""), desc=x.get("description", ""), match=x.get("match", {}).get("text", "")) for x in j["search"]]
            time.sleep(0.4)
            return sc[q]
        time.sleep(min(60, 4 * 2 ** a))
    sc[q] = None
    return None

def fetch(qs):
    need = sorted({q for q in qs if re.fullmatch(r"Q\d+", q)} - set(wd.C), key=lambda x: int(x[1:]))
    for i in range(0, len(need), 50):
        for a in range(8):
            r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(need[i:i + 50]), props="labels|descriptions|claims", languages="it|en", format="json"), headers=UA, timeout=90)
            j = r.json() if r.status_code == 200 else {}
            if "entities" in j:
                wd.C.update(j["entities"]); break
            time.sleep(min(60, 4 * 2 ** a))
        time.sleep(1)
    return len(need)

SLF = os.path.join(S, "raw/wikidata/sitelinks_cache.json")
slc = json.load(open(SLF, encoding="utf8")) if os.path.exists(SLF) else {}
def sitelinks(qs):
    need = [q for q in qs if q not in slc]
    for i in range(0, len(need), 50):
        for a in range(8):
            r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(need[i:i + 50]), props="sitelinks", format="json"), headers=UA, timeout=90)
            j = r.json() if r.status_code == 200 else {}
            if "entities" in j:
                for q, e in j["entities"].items(): slc[q] = len(e.get("sitelinks", {}))
                break
            time.sleep(min(60, 4 * 2 ** a))
    json.dump(slc, open(SLF, "w"))
    return {q: slc.get(q, 0) for q in qs}

ITA = {"Q38", "Q172579", "Q165154", "Q15913", "Q1384446", "Q23402", "Q9068", "Q2500325", "Q27306", "Q4948", "Q150509"}  # Italia, Regno d'Italia, Sardegna, Lombardia, ecc.

# 1) quali opere hanno gia' una persona reale collegata?
todo = []
for w in works:
    real = [q for q in w["subj_struct"] if wd.is_human(q) and not wd.nonreal(q)]
    w["subj_persone_struct"] = real
    if real: continue
    cs = cands(w)
    if cs: todo.append((w, cs))
print("opere senza persona collegata ma con nome candidato:", len(todo), flush=True)
allq = sorted({c for _, cs in todo for c in cs})
print("ricerche da fare:", len(allq), "(in cache:", sum(q in sc for q in allq), ")", flush=True)
for i, q in enumerate(allq):
    search(q)
    if i % 40 == 0: json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False); print(i, flush=True)
json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False)
# 2) scarica i candidati con corrispondenza esatta
exact = {}
for q in allq:
    res = sc.get(q) or []
    exact[q] = [x["id"] for x in res if norm(x["match"] or x["label"]) == norm(q) or norm(x["label"]) == norm(q)]
print("scaricati", fetch({i for v in exact.values() for i in v}), "candidati")
# occupazioni, cittadinanze: servono le etichette
refs = set()
for v in exact.values():
    for i in v:
        for p in ("P106", "P27", "P21", "P31", "P411", "P39"): refs |= set(wd.ids(i, p))
print("scaricati", fetch(refs), "riferimenti")
json.dump(wd.C, open(CF, "w", encoding="utf8"), ensure_ascii=False)

rows = []
for w, cs in todo:
    chosen = None; why = "nessun candidato esatto"
    for c in cs:
        hum = [i for i in exact.get(c, []) if wd.is_human(i) and not wd.nonreal(i)]
        # coerenza con l'anno di posa: la persona non puo' essere nata dopo
        if w["anno"]:
            ok = []
            for i in hum:
                b = [y for y, p in wd.times(i, "P569")]
                if b and min(b) > w["anno"]: continue
                ok.append(i)
            hum = ok
        if len(hum) == 1: chosen = (hum[0], "nome_unico", c); break
        if len(hum) > 1:
            it = [i for i in hum if set(wd.ids(i, "P27")) & ITA]
            if len(it) == 1: chosen = (it[0], "unico_italiano_tra_omonimi", c); break
            sl = sitelinks(hum)
            ordd = sorted(hum, key=lambda i: -sl.get(i, 0))
            if sl.get(ordd[0], 0) >= 15 and sl.get(ordd[0], 0) >= 5 * max(1, sl.get(ordd[1], 0)): chosen = (ordd[0], "omonimo_molto_piu_noto (%d vs %d pagine wiki)" % (sl[ordd[0]], sl.get(ordd[1], 0)), c); break
            why = f"omonimi ({len(hum)})"
        elif exact.get(c): why = "corrispondenza esatta ma non e' una persona (o nata dopo la posa)"
    if chosen:
        w["subj_persone_nome"] = dict(qid=chosen[0], metodo=chosen[1], query=chosen[2])
    else:
        w["subj_persone_nome"] = None
    rows.append(dict(id=w["id"], nome=w["nome"], tipo=w["tipo"], fonte="+".join(w["src"]), candidati=" | ".join(cs), esito=("accettato" if chosen else "non risolto"), motivo=(chosen[1] if chosen else why),
                     qid_scelto=chosen[0] if chosen else "", etichetta_scelta=wd.lab(chosen[0]) if chosen else "", descrizione_scelta=wd.desc(chosen[0]) if chosen else ""))
import csv
with open(os.path.join(S, "pulito/_lavoro/ricerche_soggetti.csv"), "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
json.dump(works, open(os.path.join(S, "pulito/_lavoro/stage2.json"), "w", encoding="utf8"), ensure_ascii=False)
print(collections.Counter(r["esito"] + ": " + r["motivo"] for r in rows).most_common())
