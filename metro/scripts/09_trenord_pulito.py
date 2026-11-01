"""Pulisce le due tabelle Regione Lombardia/Trenord (CC0) e tiene solo le stazioni ferroviarie nel comune di Milano.
NON sono stazioni della metropolitana: servono da controllo (stazioni dove si cambia per la metro) e per il crollo Covid per stazione.
Output: pulito/stazioni_treno_milano_frequentazione.csv  (stazione, anno, mese, tipo_giorno, saliti_24h, saliti_7_9, discesi_7_9, corse_24h, fonte)
Uso: python -I -X utf8 09_trenord_pulito.py <raw/lombardia_trenord> <out_csv>"""
import sys, csv, os, re
raw, out = sys.argv[1], sys.argv[2]
CANON = {
 "MILANO CENTRALE": "Milano Centrale", "MILANO CERTOSA": "Milano Certosa", "MILANO DATEO": "Milano Dateo",
 "MILANO GRECO PIRELLI": "Milano Greco Pirelli", "MILANO LAMBRATE": "Milano Lambrate", "MILANO LANCETTI": "Milano Lancetti",
 "MILANO NORD BOVISA": "Milano Bovisa", "MILANO BOVISA POLITECNICO": "Milano Bovisa",
 "MILANO P. VENEZIA": "Milano Porta Venezia", "MILANO PORTA VENEZIA": "Milano Porta Venezia",
 "MILANO P.G. PASS.": "Milano Porta Garibaldi (Passante)", "MILANO PORTA GARIBALDI SOTTERRANEA": "Milano Porta Garibaldi (Passante)",
 "MILANO PORTA GARIBALDI": "Milano Porta Garibaldi (superficie)",
 "MILANO P.VITTORIA PASS.": "Milano Porta Vittoria", "MILANO PORTA VITTORIA": "Milano Porta Vittoria",
 "MILANO PORTA GENOVA": "Milano Porta Genova", "MILANO PORTA ROMANA": "Milano Porta Romana", "MILANO REPUBBLICA": "Milano Repubblica",
 "MILANO ROGOREDO": "Milano Rogoredo", "MILANO S. CRISTOFORO": "Milano San Cristoforo", "MILANO S.CRISTOFORO": "Milano San Cristoforo",
 "MILANO VILLAPIZZONE": "Milano Villapizzone", "MILANO AFFORI": "Milano Affori", "MILANO BRUZZANO": "Milano Bruzzano", "MILANO BRUZZANO PARCO NORD": "Milano Bruzzano",
 "MILANO FORLANINI": "Milano Forlanini", "MILANO NORD CADORNA": "Milano Cadorna", "MILANO CADORNA": "Milano Cadorna",
 "MILANO NORD DOMODOSSOLA": "Milano Domodossola", "MILANO DOMODOSSOLA": "Milano Domodossola",
 "MILANO QUARTO OGGIARO": "Milano Quarto Oggiaro", "MILANO ROMOLO": "Milano Romolo",
 "MILANO TIBALDI UNIVERSITA' BOCCONI": "Milano Tibaldi Bocconi"}
GIORNO = {"fer": "Feriale", "feriale": "Feriale", "sabato": "Sabato", "festivo": "Festivo"}
MESE = {"nov": 11, "novembre": 11, "maggio": 5, "luglio": 7}
rows, miss = [], set()
for ds in ("m2u2-frtq", "ut63-s688"):
    for r in csv.DictReader(open(os.path.join(raw, ds + ".csv"), encoding="utf-8")):
        if not r["comune"].lower().startswith("milano"): continue
        key = re.sub(r"\s+", " ", r["stazione"].upper().strip())
        if key not in CANON: miss.add(key); continue
        m = re.search(r"(nov|novembre|maggio|luglio)", r["campagna"].lower())
        rows.append([CANON[key], r["anno"], MESE[m.group(1)], GIORNO[r["tipo_giorno"].lower()], r["saliti24h"], r["saliti7_9"], r["discesi7_9"], r["corse24h"], ds])
print("non mappate:", miss)
rows.sort(key=lambda x: (x[0], int(x[1]), x[2], x[3]))
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["stazione", "anno", "mese_rilevazione", "tipo_giorno", "saliti_24h", "saliti_7_9", "discesi_7_9", "corse_24h", "fonte_dataset"]); w.writerows(rows)
print(len(rows), "righe", len({r[0] for r in rows}), "stazioni")
