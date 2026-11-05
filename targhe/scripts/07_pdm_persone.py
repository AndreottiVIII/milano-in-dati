"""Persone nominate nel TITOLO delle schede Pietre della Memoria, cercate su Wikidata (CC0) con corrispondenza ESATTA del nome.
Il sesso si legge solo dal campo P21 di Wikidata della persona trovata, mai dal nome.
Regola di prudenza: per le targhe di guerra/Resistenza (tag 'seconda guerra mondiale' o parole chiave) si accetta la persona solo se in Wikidata e' morta tra il 1943 e il 1946; per le altre, solo se e' l'unica persona con quel nome.
Uso: python -I -X utf8 07_pdm_persone.py <targhe assoluto> <milano-in-dati assoluto>
Legge pulito/_pdm_campi.csv. Scrive pulito/pdm_persone.csv. Cache: raw/wikidata/ (ricerche e entita')."""
import sys, os, re, csv, json, time
import requests
T, P = sys.argv[1:3]
sys.path.insert(0, os.path.join(P, "statue", "scripts"))
from wdlib import norm, G
UA = {"User-Agent": "milano-in-dati research (milano-in-dati)"}
os.makedirs(os.path.join(T, "raw/wikidata"), exist_ok=True)
SF = os.path.join(T, "raw/wikidata/pdm_search_cache.json"); EF = os.path.join(T, "raw/wikidata/pdm_entities_cache.json")
sc = json.load(open(SF, encoding="utf8")) if os.path.exists(SF) else {}
ec = json.load(open(EF, encoding="utf8")) if os.path.exists(EF) else {}
rows = list(csv.DictReader(open(os.path.join(T, "pulito/_pdm_campi.csv"), encoding="utf-8-sig")))
NOTP = re.compile(r"caduti|martiri|alpini|bersaglieri|resistenza|partigiani|vittime|deportati|lavoratori|guerra|battaglia|zona|municipio|scuola|liceo|istituto|famiglia|ferrovieri|operai|studenti|insegnanti|giornalisti|medici|sacerdoti|carabinieri|poliziotti|combattenti|soldati|stazione|piazza|via |palazzo|casa |comune|cittadini|ebrei|fascismo|libert|patria|italia|milano", re.I)
ROLE = r"(?:il |la |lo |l'|l’)?(?:partigian[oa]|operai[oa]|sacerdote|studente|studentessa|avvocato|dottor|dott\.|professor|prof\.|ingegner|ing\.|don|padre|suor|vigile|poliziotto|carabiniere|ferroviere|tranviere|giornalista|medico|comandante|capitano|tenente|generale|maresciallo|sottotenente|colonnello|sergente|caporale|soldato|alpino|internato|deportat[oa])"
HEAD = re.compile(r"^(?:lastra|lapide|targa|epigrafe)(?: commemorativ[oa]| celebrativ[oa]| marmore[oa]| in bronzo| in marmo)?\s+(?:a ricordo di|in ricordo di|in memoria di|alla memoria di|a ricordo|in onore di|dedicata a|ad|a|al|alla|per|di)\s+(.+)$", re.I)
def cands(titolo):
    t = re.sub(r"\s*[–-]\s*Milano(?: \(MI\))?\s*$", "", titolo).strip()
    t = re.split(r"\s+[–-]\s+", t)[0]
    m = HEAD.match(t)
    if not m: return []
    x = m.group(1).strip()
    if NOTP.search(x): return []
    out = []
    for part in re.split(r"\s+e\s+|,\s*|\s+ed\s+", x):
        part = re.sub(r"^" + ROLE + r"\s+", "", part.strip(), flags=re.I)
        part = re.sub(r"^" + ROLE + r"\s+", "", part, flags=re.I)
        part = re.sub(r"\s*\([^)]*\)", "", part).strip(" .")
        w = part.split()
        if 2 <= len(w) <= 5 and all(re.match(r"[A-ZÀ-Ý]|de|di|da|del|della|dei|van|von|d’|d'|le|la", z) for z in w) and re.match(r"[A-ZÀ-Ý]", w[0]) and not NOTP.search(part):
            out.append(part)
    return out
def search(q):
    if q in sc: return sc[q]
    for a in range(6):
        r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbsearchentities", search=q, language="it", uselang="it", type="item", limit=10, format="json"), headers=UA, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        if "search" in j:
            sc[q] = [dict(id=x["id"], label=x.get("label", ""), match=x.get("match", {}).get("text", "")) for x in j["search"]]; time.sleep(0.5); return sc[q]
        time.sleep(min(60, 4 * 2 ** a))
    sc[q] = []; return []
def fetch(qs):
    need = [q for q in qs if q not in ec]
    for i in range(0, len(need), 50):
        for a in range(6):
            r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(need[i:i + 50]), props="labels|descriptions|claims", languages="it|en", format="json"), headers=UA, timeout=90)
            j = r.json() if r.status_code == 200 else {}
            if "entities" in j: ec.update(j["entities"]); break
            time.sleep(min(60, 4 * 2 ** a))
        time.sleep(1)
def ids(q, p): return [c["mainsnak"]["datavalue"]["value"]["id"] for c in (ec.get(q) or {}).get("claims", {}).get(p, []) if c.get("rank") != "deprecated" and c.get("mainsnak", {}).get("datavalue")]
def year(q, p):
    for c in (ec.get(q) or {}).get("claims", {}).get(p, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "time" in v:
            m = re.match(r"([+-])(\d+)-", v["time"]); 
            if m: return int(m.group(2)) * (-1 if m.group(1) == "-" else 1)
    return None
def desc(q): return ((ec.get(q) or {}).get("descriptions", {}).get("it") or (ec.get(q) or {}).get("descriptions", {}).get("en") or {}).get("value", "")
todo = [(r, c) for r in rows for c in cands(r["titolo"])]
print("schede con nomi candidati:", len({r["id_pdm"] for r, _ in todo}), "nomi:", len(todo), flush=True)
for i, (r, c) in enumerate(todo):
    search(c)
    if i % 30 == 0: json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False); print(i, flush=True)
json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False)
exact = {c: [x["id"] for x in sc.get(c, []) if norm(x["label"]) == norm(c) or norm(x["match"]) == norm(c)] for _, c in todo}
fetch({q for v in exact.values() for q in v}); json.dump(ec, open(EF, "w", encoding="utf8"), ensure_ascii=False)
out = []
for r, c in todo:
    hum = [q for q in exact[c] if "Q5" in ids(q, "P31")]
    guerra = "seconda guerra" in r["tags"].lower() or re.search(r"partigian|resistenz|liberazione|nazifasc|caduti per la libert|deportat", (r["titolo"] + " " + r["iscrizione"]).lower())
    esito, qid = "nessuna persona con questo nome", ""
    if guerra:
        ok = [q for q in hum if (year(q, "P570") or 0) in range(1943, 1947)]
        if len(ok) == 1: esito, qid = "accettata (morta 1943-46)", ok[0]
        elif len(ok) > 1: esito = "omonimi morti 1943-46"
        elif hum: esito = "persona omonima non compatibile (morte fuori 1943-46)"
    else:
        if len(hum) == 1: esito, qid = "accettata (nome unico)", hum[0]
        elif len(hum) > 1: esito = "omonimi"
    gen = ""
    if qid:
        g = [G.get(x, "altro") for x in ids(qid, "P21")]; gen = g[0] if len(set(g)) == 1 else ""
    out.append(dict(id_pdm=r["id_pdm"], nome_nel_titolo=c, esito=esito, qid=qid, etichetta=((((ec.get(qid) or {}).get("labels", {}).get("it") or (ec.get(qid) or {}).get("labels", {}).get("en") or {}).get("value", c)) if qid else ""), genere=gen,
                    nascita=year(qid, "P569") if qid else "", morte=year(qid, "P570") if qid else "", descrizione=desc(qid) if qid else "", candidati_umani=len(hum)))
with open(os.path.join(T, "pulito/pdm_persone.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
import collections
print(collections.Counter(o["esito"] for o in out), collections.Counter(o["genere"] for o in out if o["qid"]))
