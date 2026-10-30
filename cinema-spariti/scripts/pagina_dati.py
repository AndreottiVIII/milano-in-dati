# -*- coding: utf-8 -*-
r"""Costruisce i dati e la pagina docs/cinema-spariti/ (rieseguibile).

Uso (dalla cartella cinema-spariti):   python -I scripts\pagina_dati.py
Legge:    pulito/cinema.csv  (+ scripts/pagina_template.html)
Scrive:   ../docs/cinema-spariti/data/cinema.json, serie.json  e  ../docs/cinema-spariti/index.html

Regole di pubblicazione (licenza):
- dall'elenco spazioCinema (Anteo, 2017, copyright) si pubblicano SOLO i fatti: nome, indirizzo,
  anni di attivita'. Non si pubblica il testo originale ("periodo_testo_originale") ne' il PDF.
- posizioni: Wikidata (CC0) e OSM (ODbL) = esatte; Nominatim = "approssimata".
- date incerte: marcate "circa" (flag *_incerta nel CSV).
"""
import csv, json, re, sys, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent            # .../cinema-spariti
OUT = BASE.parent / "docs" / "cinema-spariti"
(OUT / "data").mkdir(parents=True, exist_ok=True)
ANNO_OGGI = 2026

rows = list(csv.DictReader(open(BASE / "pulito" / "cinema.csv", encoding="utf-8-sig")))

# ---------------------------------------------------------------------------
# Anni di apertura dei cinema ancora aperti (da Wikidata / Wikipedia / OSM).
# Solo questi sono noti: per gli altri aperti oggi l'anno e' ignoto e non entrano nella storia.
# chiave = id in cinema.csv ; (anno apertura, circa?, anno chiusura o None, nota, fonte)
APERTURA_NOTA = {
    "OSM_n442587403": (1907, 1, None, "Anno da tag start_date di OpenStreetMap, non verificato.", "osm"),
    "OSM_n251293086": (1929, 0, 2023, "Inaugurato il 26/11/1929; chiuso il 31/07/2023 per riconversione (previsti 5 schermi e una galleria commerciale). OpenStreetMap lo dava ancora attivo.", "wikipedia"),
    "OSM_n29978509": (1938, 0, None, "Data di apertura ufficiale 1938 (Wikidata, proprieta' P1619).", "wikidata"),
    "OSM_n442586656": (1948, 0, None, "Fondato nel 1948 in una ex sala parrocchiale degli anni Trenta (Wikipedia, voce Cinema multisala).", "wikipedia"),
    "OSM_n9545441783": (1925, 1, None, "Sala costruita negli anni Venti (Wikipedia, voce Nolo); anno indicativo.", "wikipedia"),
    "OSM_w372493995": (1967, 0, None, "Dal 1967 solo cinema; prima teatro di rivista dagli anni Trenta; multisala dalla meta' degli anni Novanta (Wikipedia, voce Teatro Plinius).", "wikipedia"),
    "OSM_n3307148582": (1979, 0, None, "Cinema Anteo fondato nel 1979; rinnovato nel 2017 come Anteo Palazzo del Cinema (Wikipedia).", "wikipedia"),
    "OSM_n5259883590": (2017, 0, None, "Inaugurato il 16/12/2017 nel centro commerciale CityLife (Wikipedia).", "wikipedia"),
}
# Luoghi presenti solo in Wikidata, senza date: non entrano in mappa, conteggi ed elenco
ESCLUSI_WD = {r["id"] for r in rows if r["id"].startswith("WD_")}

TAG_IT = {
    "fast_food": "fast food", "cafe": "bar o caffè", "restaurant": "ristorante", "pub": "pub", "bar": "bar",
    "clothes": "abbigliamento", "convenience": "minimarket", "supermarket": "supermercato", "bank": "banca",
    "hotel": "albergo", "guest_house": "pensione", "apartment": "appartamenti", "books": "libreria",
    "pharmacy": "farmacia", "optician": "ottica", "beauty": "estetica", "hairdresser": "parrucchiere",
    "jewelry": "gioielleria", "gift": "negozio di regali", "shoes": "scarpe", "perfumery": "profumeria",
    "telecommunication": "telefonia", "computer": "informatica", "fabric": "tessuti", "furniture": "arredamento",
    "fitness_centre": "palestra", "police": "polizia", "post_office": "ufficio postale", "ice_cream": "gelateria",
    "theatre": "teatro", "information": "punto informazioni", "florist": "fiorista", "cosmetics": "cosmetici",
    "general": "negozio", "company": "ufficio", "estate_agent": "agenzia immobiliare", "visa": "ufficio pratiche",
    "supermarket ": "supermercato",
}

def cosa_ora(txt):
    if not txt.startswith("candidato OSM"):
        return ""
    corpo = txt.split("):", 1)[1].strip()
    voci = []
    for v in corpo.split(";"):
        m = re.match(r"\s*(.*?)\s*\[(\w+)=([\w_]+)\]\s*$", v)
        if not m:
            continue
        nome, chiave, val = m.groups()
        tipo = TAG_IT.get(val, val.replace("_", " "))
        voci.append(tipo if nome == "(senza nome)" else f"{nome} ({tipo})")
    return "; ".join(voci[:3])

def periodi(r):
    return [[int(x) for x in p.split("-")] for p in r["periodi_attivita"].split(";") if p]

def fonti(r):
    t = []
    toks = [x.strip() for x in r["fonti"].split(";")]
    if "spaziocinema_elenco_2017" in toks: t.append("A")
    if "wikidata" in toks: t.append("W")
    if "osm" in toks: t.append("O")
    if r["fonte_posizione"] == "nominatim": t.append("N")
    return t

def posizione(r):
    if not r["lat"]: return ""
    return "a" if r["fonte_posizione"] == "nominatim" else "e"

cin = []
for r in rows:
    if r["id"] in ESCLUSI_WD:
        continue
    rec = {"id": r["id"], "n": r["nome"], "alt": ", ".join(x.strip() for x in r["altri_nomi"].split("|") if x.strip()), "ind": r["indirizzo"],
           "lat": round(float(r["lat"]), 6) if r["lat"] else None,
           "lon": round(float(r["lon"]), 6) if r["lon"] else None,
           "pos": posizione(r), "wd": r["wikidata"], "fo": fonti(r)}
    if r["id"].startswith("SC"):
        rec.update(st="chiuso", per=periodi(r), ac=int(r["apertura_incerta"] or 0), cc=int(r["chiusura_incerta"] or 0),
                   cosa=cosa_ora(r["cosa_c_ora"]), nota="")
    else:
        # cinema aperto oggi (OSM 29/10/2026)
        rec.update(st="aperto", per=[], ac=0, cc=0, cosa="", nota="", sale=int(r["n_sale"]) if r["n_sale"] else None)
        if r["id"] in APERTURA_NOTA:
            a, circa, chiusura, nota, fonte = APERTURA_NOTA[r["id"]]
            rec["ac"] = circa; rec["nota"] = nota
            rec["fo"] = [x for x in rec["fo"]]
            rec["fo"].append({"wikipedia": "P", "wikidata": "W", "osm": "O"}[fonte])
            rec["fo"] = sorted(set(rec["fo"]))
            if chiusura:
                rec["st"] = "chiuso"; rec["per"] = [[a, chiusura]]; rec["cosa"] = "in riconversione: previsti 5 schermi e una galleria commerciale"
            else:
                rec["per"] = [[a, ANNO_OGGI]]
    if rec["pos"] == "":
        rec["lat"] = rec["lon"] = None
    cin.append(rec)

chiusi = [c for c in cin if c["st"] == "chiuso"]
aperti = [c for c in cin if c["st"] == "aperto"]
aperti_noti = [c for c in aperti if c["per"]]
for c in chiusi: c["a"] = c["per"][0][0]; c["c"] = c["per"][-1][1]
for c in aperti_noti: c["a"] = c["per"][0][0]

def attivo(c, y):
    return any(a <= y <= b for a, b in c["per"])

# ---------------------------------------------------------------------------
# Serie: attivi per anno (sale poi chiuse; sale ancora aperte con anno di apertura noto)
anni = list(range(1890, ANNO_OGGI + 1))
s_chiuse = [sum(attivo(c, y) for c in chiusi) for y in anni]
s_aperte = [sum(attivo(c, y) for c in aperti_noti) for y in anni]
decenni = list(range(1890, 2030, 10))
ap_dec = [sum(1 for c in chiusi + aperti_noti if c["a"] // 10 * 10 == d) for d in decenni]
ch_dec = [sum(1 for c in chiusi if c["c"] // 10 * 10 == d) for d in decenni]
snap = list(range(1900, 2020, 10)) + [ANNO_OGGI]
serie = {
    "anni": anni, "chiuse": s_chiuse, "aperte_note": s_aperte,
    "aperti_oggi_totale": len(aperti), "aperti_oggi_anno_noto_attivi": sum(attivo(c, ANNO_OGGI) for c in aperti_noti),
    "decenni": decenni, "aperture": ap_dec, "chiusure": ch_dec,
    "istantanee": [{"anno": y, "chiuse": s_chiuse[anni.index(y)], "aperte_note": s_aperte[anni.index(y)]} for y in snap],
    "stampa": [
        {"anno": 1950, "valore": 110, "etichetta": "110 nel 1950", "fonte": "VareseNews, 3/2/2019 (progetto CineMi, E. Roaro)"},
        {"anno_da": 1970, "anno_a": 1979, "valore": 160, "etichetta": "circa 160 negli anni Settanta", "fonte": "Il Giorno, 17/12/2022 (Anec Lombardia)"},
        {"anno": 2022, "valore": 29, "etichetta": "29 strutture nel 2022", "fonte": "Il Giorno, 17/12/2022 (Anec Lombardia)"},
    ],
}
picco_i = max(range(len(anni)), key=lambda i: s_chiuse[i] + s_aperte[i])

meta = {
    "generato": datetime.date.today().isoformat(), "dati_osm": "2026-10-29",
    "n_chiusi": len(chiusi), "n_aperti": len(aperti),
}
json.dump({"meta": meta, "cinema": cin}, open(OUT / "data" / "cinema.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(serie, open(OUT / "data" / "serie.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------------------------------------------------------------------------
# Pagina: sostituzione dei segnaposto nel modello
chiusi_elenco = [c for c in chiusi if c["id"].startswith("SC")]
numeri = {
    "N_CHIUSI": len(chiusi), "N_CHIUSI_ELENCO": len(chiusi_elenco), "N_APERTI": len(aperti),
    "N_APERTI_NOTI": len(aperti_noti) - sum(1 for c in aperti_noti if c["st"] == "chiuso"),
    "PICCO_N": s_chiuse[picco_i] + s_aperte[picco_i], "PICCO_ANNO": anni[picco_i],
    "PICCO_CHIUSE": s_chiuse[picco_i],
    "N_SENZA_POS": sum(1 for c in chiusi if not c["pos"]),
    "N_APPROX": sum(1 for c in chiusi if c["pos"] == "a"),
    "N_ESATTE": sum(1 for c in chiusi if c["pos"] == "e"),
    "N_COSA": sum(1 for c in chiusi if c["cosa"]),
    "N_CIRCA": sum(1 for c in chiusi if c["ac"] or c["cc"]),
    "N_WD_SOLI": len(ESCLUSI_WD),
    "GENERATO": datetime.date.today().strftime("%d/%m/%Y"),
}
html = (BASE / "scripts" / "pagina_template.html").read_text(encoding="utf-8")
for k, v in numeri.items():
    html = html.replace("{{" + k + "}}", str(v))
assert "{{" not in html, re.findall(r"\{\{\w+\}\}", html)
(OUT / "index.html").write_text(html, encoding="utf-8")

print("chiusi", len(chiusi), "aperti", len(aperti), "(anno apertura noto:", len(aperti_noti), ")")
print("picco", anni[picco_i], s_chiuse[picco_i], "+", s_aperte[picco_i])
print("pos: esatte", numeri["N_ESATTE"], "approssimate", numeri["N_APPROX"], "senza", numeri["N_SENZA_POS"])
print("istantanee", [(d["anno"], d["chiuse"], d["aperte_note"]) for d in serie["istantanee"]])
print("aperture per decennio", dict(zip(decenni, ap_dec)))
print("chiusure per decennio", dict(zip(decenni, ch_dec)))
print("scritti:", OUT / "index.html")
