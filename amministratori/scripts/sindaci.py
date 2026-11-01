"""Sindaci di Milano dal 1946: date di mandato, partito, anno di nascita, sesso.
Uso: python -I -X utf8 sindaci.py <amministratori_dir>
Fonti (salvate in raw/wikidata/):
  - Wikipedia italiana, voce "Sindaci di Milano" (wikitext, CC BY-SA 4.0): date di inizio/fine mandato e partito  -> wp_sindaci_milano.json
  - Wikidata (CC0), interrogazione SPARQL P39 = "sindaco di Milano" (Q3961545): anno di nascita e sesso  -> sindaci_p39.json
  - Ministero dell'Interno (DAIT), fotografie 2007-2025 e elenco in carica: controllo dei nomi dal 2006 in poi
Le date sono scritte qui sotto e il programma controlla che ogni data compaia nel testo salvato di Wikipedia
(altrimenti si ferma): niente numeri a memoria.
Scrive pulito/sindaci_milano.csv e pulito/controlli_sindaci.json
"""
import sys, os, json, csv, datetime as dt
A = sys.argv[1]
WP = json.load(open(os.path.join(A, "raw", "wikidata", "wp_sindaci_milano.json"), encoding="utf8"))["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
WD = json.load(open(os.path.join(A, "raw", "wikidata", "sindaci_p39.json"), encoding="utf8"))["results"]["bindings"]

# (nome per Wikidata, nome mostrato, inizio, fine, stringhe da trovare in Wikipedia, partito, nota)
# Greppi: sindaco di nomina CLN dal 27/4/1945; qui il mandato "repubblicano" dal 7/4/1946 (linea temporale di Wikipedia)
S = [
 ("Antonio Greppi", "Antonio Greppi", "1946-04-07", "1951-06-25", ["25 giugno 1951", "07/04/1946"], "PSI (dal 1949 PSU)", "Nominato dal CLN il 27/4/1945; eletto dal consiglio nel 1946"),
 ("Virgilio Ferrari", "Virgilio Ferrari", "1951-06-25", "1961-01-21", ["21 gennaio 1961"], "PSDI", ""),
 ("Gino Cassinis", "Gino Cassinis", "1961-01-21", "1964-01-13", ["13 gennaio 1964"], "PSDI", "Morto in carica"),
 ("Pietro Bucalossi", "Pietro Bucalossi", "1964-02-17", "1967-12-13", ["17 febbraio 1964", "13 dicembre 1967"], "PSDI", "Wikidata indica PRI; Wikipedia PSDI (qui: Wikipedia)"),
 ("Aldo Aniasi", "Aldo Aniasi", "1967-12-13", "1976-05-12", ["12 maggio 1976"], "PSI", ""),
 ("Carlo Tognoli", "Carlo Tognoli", "1976-05-12", "1986-12-21", ["21 dicembre 1986"], "PSI", ""),
 ("Paolo Pillitteri", "Paolo Pillitteri", "1986-12-21", "1992-01-18", ["18 gennaio 1992"], "PSI", ""),
 ("Giampiero Borghini", "Giampiero Borghini", "1992-01-18", "1993-03-11", ["11 marzo 1993"], "PSI", "Dimesso; poi commissario fino al 21/6/1993"),
 ("Marco Formentini", "Marco Formentini", "1993-06-21", "1997-05-12", ["21 giugno 1993", "12 maggio 1997"], "Lega Nord", "Primo sindaco eletto direttamente dai cittadini"),
 ("Gabriele Albertini", "Gabriele Albertini", "1997-05-12", "2006-05-30", ["30 maggio 2006"], "Forza Italia", "Due mandati (1997, 2001)"),
 ("Letizia Moratti", "Letizia Moratti", "2006-05-30", "2011-06-01", ["1º giugno 2011"], "Indipendente, poi PdL (2009)", ""),
 ("Giuliano Pisapia", "Giuliano Pisapia", "2011-06-01", "2016-06-21", ["21 giugno 2016"], "Indipendente (coalizione di centrosinistra)", ""),
 ("Giuseppe Sala", "Giuseppe Sala", "2016-06-21", None, ["6 ottobre 2021", "in carica"], "Indipendente (coalizione di centrosinistra)", "Rieletto nel 2021; in carica al 24/8/2026"),
]
OGGI = dt.date(2026, 8, 24)  # data dell'elenco "in carica"
righe = []; ctrl = {"date_non_trovate": [], "nomi_wikidata_non_trovati": []}
for nome_wd, nome, ini, fin, chiavi, partito, nota in S:
    for k in chiavi:
        if k not in WP: ctrl["date_non_trovate"].append((nome, k))
    anni = [b for b in WD if b["sLabel"]["value"].startswith(nome_wd.split(" (")[0])]
    if not anni: ctrl["nomi_wikidata_non_trovati"].append(nome)
    nasc = sorted({int(b["birth"]["value"][:4]) for b in anni if "birth" in b})
    ses = sorted({b["genderLabel"]["value"] for b in anni if "genderLabel" in b})
    i = dt.date.fromisoformat(ini); f = dt.date.fromisoformat(fin) if fin else OGGI
    righe.append({"sindaco": nome, "inizio": ini, "fine": fin or "", "in_carica": fin is None,
                  "durata_anni": round((f - i).days / 365.25, 1),
                  "anno_nascita": nasc[0] if len(nasc) == 1 else "", "eta_inizio": (i.year - nasc[0]) if len(nasc) == 1 else "",
                  "sesso": "F" if ses == ["femmina"] else ("M" if ses == ["maschio"] else ""),
                  "partito": partito, "nota": nota,
                  "eletto_direttamente": i >= dt.date(1993, 6, 21)})
assert not ctrl["date_non_trovate"], ctrl["date_non_trovate"]
assert not ctrl["nomi_wikidata_non_trovati"], ctrl["nomi_wikidata_non_trovati"]
assert all(r["anno_nascita"] and r["sesso"] for r in righe), [r for r in righe if not (r["anno_nascita"] and r["sesso"])]
# controllo con il Ministero dell'Interno (2006 in poi): nome e anno di nascita del sindaco nelle fotografie
import pandas as pd
mi = pd.read_csv(os.path.join(A, "pulito", "milano_amministratori.csv"))
s = mi[mi.ruolo == "sindaco"].drop_duplicates(["anno", "cognome", "nome"])
ctrl["sindaci_nel_file_ministero"] = [[int(a), c, n, int(an) if an == an else None] for a, c, n, an in zip(s.anno, s.cognome, s.nome, s.anno_nascita)]
ctrl["durata_totale_anni_dal_1946"] = round((OGGI - dt.date(1946, 4, 7)).days / 365.25, 1)
ctrl["donne"] = [r["sindaco"] for r in righe if r["sesso"] == "F"]
with open(os.path.join(A, "pulito", "sindaci_milano.csv"), "w", newline="", encoding="utf8") as fo:
    w = csv.DictWriter(fo, fieldnames=list(righe[0].keys())); w.writeheader(); w.writerows(righe)
json.dump(ctrl, open(os.path.join(A, "pulito", "controlli_sindaci.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
for r in righe: print(r["sindaco"], r["inizio"], r["fine"], r["durata_anni"], r["anno_nascita"], r["eta_inizio"], r["sesso"], r["partito"])
print(ctrl["sindaci_nel_file_ministero"], ctrl["donne"])
