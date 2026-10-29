"""Unisce le fonti pulite nella tabella unica pulito/cartellone.csv e scrive pulito/copertura.csv (per anno 1778-2027) e pulito/copertura_stagioni_1906_1963.csv.
Colonne: stagione,data,anno,titolo,autore,genere,direttore,regista,interpreti,sala,fonte,affidabilita,riga_fonte,ripubblicabile
Uso: python -I -X utf8 scripts/costruisci_cartellone.py pulito
Ogni riga = un titolo in una stagione secondo UNA fonte (le fonti si sovrappongono di proposito: il confronto e' in differenze.md)."""
import sys, os, csv, json, re, unicodedata, collections, datetime

P = sys.argv[1]
COLS = ["stagione", "data", "anno", "titolo", "autore", "genere", "direttore", "regista", "interpreti", "sala", "fonte", "affidabilita", "riga_fonte", "ripubblicabile"]
rows = []
def rd(fn): return list(csv.DictReader(open(os.path.join(P, fn), encoding="utf-8")))
def add(**k):
    r = {c: "" for c in COLS}; r.update(k); rows.append(r)
def title_case_name(s):
    s = s.strip()
    if s.isupper(): s = " ".join(w.capitalize() if len(w) > 3 or w.lower() not in ("de", "di", "da", "van", "von") else w.lower() for w in s.split())
    return s
SALA = "Teatro alla Scala"

# ---- Cambiasi 1881
for x in rd("_cambiasi_pulito.csv"):
    conf = float(x["conf_ocr"] or 0)
    aff = "media" if conf >= 45 else "bassa"
    add(stagione=x["stagione"], data=x["data"], anno=x["anno"], titolo=x["titolo"], autore=x["autore"], genere=x["genere"] + (" (scritta per la Scala)" if x["prima_per_la_scala"] else ""),
        interpreti=x["interpreti"], sala=SALA, fonte="cambiasi_1881", affidabilita=aff, riga_fonte=x["riga_fonte"], ripubblicabile="si")
# ---- Romani 1862
for x in rd("_romani_opere.csv"):
    add(stagione=(x["stagione_nome"] + " " + x["anno"]).strip(), anno=x["anno"], titolo=x["titolo"], autore=x["autore"], genere=x["genere"], sala=SALA,
        fonte="romani_1862", affidabilita="media", riga_fonte=x["riga_fonte"], ripubblicabile="si")
# ---- Wikipedia
for x in rd("_wp_stagioni.csv"):
    if not x["anno"].isdigit() or not x["titolo"].strip(): continue
    stg = x["stagione"] if len(x["stagione"]) < 40 else ""
    interp = x["interpreti"]
    add(stagione=stg, data=x["data"], anno=x["anno"], titolo=x["titolo"], autore=x["compositore"], genere="lirica" + (" (prima assoluta)" if "assoluta" in x["prima"].lower() else ""),
        direttore=x["direttore"], regista=x["regista"], interpreti=interp, sala=SALA, fonte="wikipedia_it_stagioni_liriche",
        affidabilita="media", riga_fonte="it.wikipedia 'Stagioni liriche del Teatro alla Scala', " + x["riga_fonte"] + ((" ; rimanda a " + x["ref"]) if x["ref"] else ""), ripubblicabile="si")
# ---- Wikidata (prime assolute alla Scala)
seen = set()
for fn in ("premiere_p4647.json", "premiere_location_any.json"):
    d = json.load(open(os.path.join(P, "..", "raw", "wikidata", fn), encoding="utf-8"))
    for b in d["results"]["bindings"]:
        q = b["work"]["value"].rsplit("/", 1)[-1]
        if q in seen or "date" not in b: continue
        dt = b["date"]["value"][:10]
        if not re.match(r"^\d{4}-\d\d-\d\d$", dt): continue
        y = int(dt[:4]); mo = int(dt[5:7])
        seen.add(q)
        stg = "%d-%02d" % (y if mo >= 9 else y - 1, (y + 1 if mo >= 9 else y) % 100) if y >= 1900 else ""
        gen = b.get("genreLabel", {}).get("value", "") or b.get("instLabel", {}).get("value", "")
        add(stagione=stg, data=dt, anno=y, titolo=b["workLabel"]["value"], autore=b.get("composerLabel", {}).get("value", ""), genere=(gen + " (prima assoluta)").strip(),
            sala=SALA, fonte="wikidata_prime", affidabilita="media", riga_fonte="https://www.wikidata.org/wiki/" + q, ripubblicabile="si")
# ---- Marangoni-Vanbianchi
for x in rd("_marangoni_opere.csv"):
    add(stagione=x["stagione_nome"], anno=x["anno"], titolo=x["titolo"], autore=x["autore"], genere="opera", sala=SALA, fonte="marangoni_vanbianchi_1922",
        affidabilita="media", riga_fonte=x["riga_fonte"], ripubblicabile="no")
MARANGONI_CARTELLONI = {  # titoli letti nei cartelloni di stagione (OCR corretto a mano sul titolo; nessun testo copiato)
    ("1910-11", 1910): ["Ariane et Barbe-Bleue", "Sigfrido", "Fior di neve", "Saffo", "Il Cavaliere della rosa", "Simon Boccanegra", "Romeo e Giulietta", "Il matrimonio segreto"],
    ("1912-13", 1912): ["Oberon", "Salomé", "Faust", "Lohengrin", "La fanciulla del West", "Don Carlo", "Feuersnot", "La Habanera", "Le donne curiose", "Cavalleria rusticana", "Carmen", "L'amore dei tre re"],
    ("1913-14", 1913): ["Falstaff", "Nabucco", "Aida", "Otello", "Parisina", "Tristano e Isotta", "L'ombra di Don Giovanni", "Parsifal"],
    ("1915-16", 1915): ["Le Prince Igor", "Francesca da Rimini", "Les Béatitudes", "La battaglia di Legnano", "Manon", "Isabeau", "Marta", "Il barbiere di Siviglia", "Aida", "Andrea Chénier", "La Bohème"],
    ("1916-17", 1916): ["Marouf", "Lodoletta", "Mignon", "Siberia", "Lakmé", "Tosca", "Fernando Cortez", "Hernani", "Lucrezia Borgia", "L'elisir d'amore"],
    ("1918-19", 1918): ["La Nave", "Ghismonda", "Urania", "Mefistofele", "Don Pasquale"],
}
for (stg, y), tl in MARANGONI_CARTELLONI.items():
    for t in tl:
        add(stagione=stg, anno=y, titolo=t, genere="opera", sala=SALA, fonte="marangoni_vanbianchi_1922", affidabilita="media",
            riga_fonte="Marangoni-Vanbianchi 1922, cartellone di stagione %s (OCR, titolo corretto)" % stg, ripubblicabile="no")
# ---- Gatti vol.1
n_g = 0
for x in rd("gatti_vol1_citazioni.csv"):
    if x["trovato_nel_testo"] != "si" or x["segnale_spettacolo"] != "si" or x["genere"] == "testo letterario": continue
    if not x["anno"] or int(x["anno"]) < 1882: continue      # prima del 1882 bastano Cambiasi e Romani; l'anno di Gatti e' troppo approssimato
    unc = "incerto" in x["note"]
    add(stagione=x["stagione"], anno=x["anno"], titolo=x["titolo"], autore=x["autore"], genere=x["genere"].replace("opera o balletto", "opera o balletto (non distinto)"),
        direttore="" if unc else x["direttore"], regista="" if unc else x["regista"], interpreti="" if unc else x["interpreti"], sala="",
        fonte="gatti_vol1", affidabilita="media" if (x["confidenza"] in ("alta", "media") and int(x["anno"]) >= 1900) else "bassa", riga_fonte=x["riferimento"], ripubblicabile="no")
    n_g += 1
# ---- sito Scala 2023-27
for x in rd("_scala_sito.csv"):
    if x["nota"] or not x["titolo"]: continue
    add(stagione=x["stagione"], data=x["data"], anno=(x["data"][:4] if x["data"] else "20" + x["stagione"][:2] if False else (x["data"][:4] if x["data"] else x["stagione"][:4])), titolo=x["titolo"], autore=x["autore"], genere=x["genere"],
        direttore=title_case_name(x["direttore"]), regista=title_case_name(x["regista"]), interpreti=";".join(title_case_name(i) for i in x["interpreti"].split(";") if i.strip()),
        sala=x["sala"], fonte="scala_sito_pubblico", affidabilita="alta", riga_fonte=x["riga_fonte"] + " (c) Teatro alla Scala", ripubblicabile="si")

for r in rows:
    r["anno"] = str(r["anno"])
# ordina
def ky(r):
    try: a = int(r["anno"])
    except ValueError: a = 0
    return (a, r["fonte"], r["data"], r["titolo"])
rows.sort(key=ky)
with open(os.path.join(P, "cartellone.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
c = collections.Counter(r["fonte"] for r in rows)
print("righe totali:", len(rows), dict(c))

# ------------------------------------------------------------ chiave di confronto
ART = re.compile(r"^(il|lo|la|le|gli|i|l|un|una|uno|der|die|das|les|le|el|the)\s+")
def key(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("j", "i").replace("’", "'").replace("ph", "f")
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = re.split(r"\s+(?:ossia|o|ovvero|or)\s+", t)[0]
    t = re.sub(r"[^a-z0-9' ]+", " ", t); t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("'", " "); t = re.sub(r"\s+", " ", t).strip()
    t = ART.sub("", t)
    t = ART.sub("", t)
    return t
KEYSRC = collections.defaultdict(lambda: collections.defaultdict(set))   # anno -> fonte -> {chiavi}
for r in rows:
    try: a = int(r["anno"])
    except ValueError: continue
    k = key(r["titolo"])
    if len(k) >= 3: KEYSRC[a][r["fonte"]].add(k)
fonti = ["cambiasi_1881", "romani_1862", "wikipedia_it_stagioni_liriche", "wikidata_prime", "marangoni_vanbianchi_1922", "gatti_vol1", "scala_sito_pubblico"]
with open(os.path.join(P, "copertura.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["anno", "titoli_distinti_tutte_le_fonti", "righe_tutte_le_fonti"] + ["titoli_" + s for s in fonti] + ["fonti_presenti", "nota"])
    for a in range(1778, 2028):
        allk = set()
        for s in fonti: allk |= KEYSRC[a][s]
        nr = sum(1 for r in rows if r["anno"] == str(a))
        pres = [s for s in fonti if KEYSRC[a][s]]
        nota = ""
        if a == 2027: nota = "stagione 2026-27 annunciata"
        if not allk: nota = (nota + " nessun titolo").strip()
        w.writerow([a, len(allk), nr] + [len(KEYSRC[a][s]) for s in fonti] + [";".join(pres), nota])
print("copertura.csv scritta")
json.dump({str(a): {s: sorted(v) for s, v in d.items()} for a, d in KEYSRC.items()}, open(os.path.join(P, "_chiavi_per_anno.json"), "w", encoding="utf-8"), ensure_ascii=False)
