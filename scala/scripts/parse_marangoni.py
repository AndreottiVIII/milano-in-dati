"""Marangoni-Vanbianchi 1922, 'Serie delle opere' (1906-1920): testo OCR djvu, tabella a colonne separate -> pulito/_marangoni_opere.csv
Si leggono SOLO i campi della parte sinistra della tabella (anno, stagione, mese, giorno, titolo, genere, maestro-poeta) dove l'OCR li ha lasciati
sulla stessa riga; i nomi degli esecutori (colonne separate) non sono abbinabili in modo sicuro e restano fuori.
Uso: python -I -X utf8 scripts/parse_marangoni.py raw/cambiasi/pdf24_merged-16/pdf24_merged-16_djvu.txt pulito/_marangoni_opere.csv"""
import re, sys, csv, collections

t = open(sys.argv[1], encoding="utf-8").read().replace("\r", "")
A = t.find("Data della I")          # inizio tabella (testata colonne)
if A < 0: A = 1060000
B = t.find("SERIE DEI BALLI")
if B < 0: B = 1115000
# la tabella delle opere puo' iniziare prima: cerca il primo '1906' vicino a 'Anno Stagione'
S0 = t.rfind("SERIE DELLE OPERE", 0, B)
start = max(S0, A - 60000) if S0 >= 0 else A - 60000
seg = t[start:B]
MESI = "Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|Settembre|Ottobre|Novembre|Dicembre|Genn|Febb|Sett|Ott|Nov|Dic"
GEN = r"(Serio|Comico|Semiserio|Semi-serio|Buffo|Poema lirico|Poema tragico|Poema|Leggenda|Mistero|Dramma lirico|Dramma|Commedia lirica|Comm\. fant\.|Fiaba|Azione|Opera)"
rows = []; anno = None; stag = ""; mese = ""
cnt = collections.Counter()
line_re = re.compile(r"(?:(?P<mese>%s)|id\.|idem)?\s*(?P<giorno>\d{1,2})?\s*[\[\|;]?\s*(?P<titolo>[A-Z«“L][^|\n]{2,60}?)\s*\]?\s+(?P<gen>%s)\.?\s*[|]?\s*(?P<aut>[A-Z][^|\n]{2,40})?" % (MESI, GEN))
for ln in seg.split("\n"):
    L = ln.strip()
    if not L: continue
    ym = re.match(r"^(?:[^\w]{0,3})?(19[012]\d)\s*[|\s]", L)
    if ym:
        anno = int(ym.group(1))
    if re.search(r"Carnevale", L): stag = "Carnevale-Quaresima"
    elif re.search(r"Autunno", L): stag = "Autunno"
    elif re.search(r"Primavera", L): stag = "Primavera"
    elif re.search(r"Straordinaria|Verdiana", L): stag = "Straordinaria"
    m = line_re.search(L)
    if not m or not anno: continue
    tit = m.group("titolo").strip(" |[]»>.")
    tit = re.sub(r"^(?:Carnevale e Qua-?|resima|Autunno|Straordinaria|Verdiana)\s*\|?\s*", "", tit)
    tit = re.sub(r"^(?:%s)\s+\d{0,2}\s*" % MESI, "", tit)
    tit = re.sub(r"^[|>\s\d]+", "", tit)
    if len(tit) < 3 or tit.lower().startswith(("data", "anno", "numero", "esito", "maestro")): continue
    if not re.search(r"[a-z]", tit): continue
    mese_f = (m.group("mese") or "")
    rows.append({"anno": anno, "stagione_nome": stag, "mese": mese_f, "giorno": m.group("giorno") or "", "titolo": tit, "genere": m.group("gen"),
                 "autore": (m.group("aut") or "").strip(" |-"), "riga_fonte": "Marangoni-Vanbianchi 1922, riga: " + L[:70]})
    cnt[anno] += 1
with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["anno", "stagione_nome", "mese", "giorno", "titolo", "genere", "autore", "riga_fonte"]); w.writeheader(); w.writerows(rows)
print(len(rows), "righe; per anno:", dict(sorted(cnt.items())))
