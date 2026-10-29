"""Romani 1862 (testo OCR djvu) -> pulito/_romani_opere.csv: opere per anno e stagione (titolo, genere D.s./D.g./D.sem., maestro quando scritto "di X").
Struttura del libro: intestazione anno (OCR sporca: 1S3S = 1838), stagione (CARNEVALE, QUARESIMA, PRIMAVERA, ESTATE, AUTUNNO),
poi un elenco "Titolo. D. s. ... musica di X; esito." separato da trattini lunghi; poi BALLI.
Uso: python -I -X utf8 scripts/parse_romani.py raw/romani/teatroallascalac00romauoft/teatroallascalac00romauoft_djvu.txt pulito/_romani_opere.csv"""
import re, sys, csv, collections

t = open(sys.argv[1], encoding="utf-8").read()
t = t.replace("\r", "")
t = re.sub(r"[ \t]+", " ", t)
# parte cronologica: dal primo "1778"/"AUTUNNO" in poi
start = t.find("Europa riconosciuta")
if start < 0: start = 90000
body = t[max(0, start - 3000):]
TR = str.maketrans("SGOIlB|", "8601181")
SEAS = r"(CARNEVALE e QUARESIMA|CARNEVALE|QUARESIMA|PRIMAVERA|ESTATE|AUTUNNO|AVVENTO|CARNEV\.?|QUARES\.?)"
tok = re.compile(r"(?m)^\s*([1I][78S][0-9SIlOGB]{2})\s*$|^\s*" + SEAS + r"\b[^\n]{0,30}$|^\s*(BALLI|Balli|OPERE|Opere)\s*$")
events = []
for m in tok.finditer(body):
    if m.group(1):
        y = m.group(1).translate(TR)
        if y.isdigit() and 1778 <= int(y) <= 1862: events.append((m.start(), "Y", int(y)))
    elif m.group(2):
        events.append((m.start(), "S", m.group(2).title()))
    else:
        events.append((m.start(), "B" if m.group(3).lower() == "balli" else "O", None))
events.sort()
rows = []; year = None; stag = ""; mode = "O"
segs = []
for i, (pos, k, v) in enumerate(events):
    end = events[i + 1][0] if i + 1 < len(events) else len(body)
    if k == "Y": year = v; mode = "O"; stag = ""
    elif k == "S": stag = v; mode = "O"
    elif k == "B": mode = "B"
    elif k == "O": mode = "O"
    if k in ("O", "S", "Y") and mode == "O" and year:
        segs.append((year, stag, body[pos:end]))
# estrazione titoli
MARK = re.compile(r"(D\.\s*(?:s|g|sem|semis)\.?|Dramma\s+(?:serio|giocoso|semiserio)|Opera\s+(?:seria|buffa)|Melodramma|Op\.\s*s)", re.I)
n_by_year = collections.Counter()
for (year, stag, seg) in segs:
    seg = re.sub(r"-\s*\n\s*", "", seg)
    seg = re.sub(r"\s*\n\s*", " ", seg)
    # solo l'elenco opere (fino a BALLI)
    seg = re.split(r"\bBALLI\b|\bBalli\b", seg)[0]
    items = re.split(r"\s+[—–]\s+|\s+-\s+(?=[A-Z/I])", seg)
    for it in items:
        it = it.strip()
        if not it: continue
        mm = MARK.search(it)
        if not mm: continue
        title = it[:mm.start()].strip(" .,;:-_/*")
        title = re.sub(r"^(?:OPERE|Opere|CARNEVALE|QUARESIMA|PRIMAVERA|ESTATE|AUTUNNO)\b.*?[.:]\s*", "", title)
        title = re.sub(r"^[0-9il\\]+\s*[.,]\s*", "", title)
        title = re.sub(r"^[/I]\s+(?=[A-Z])", "I ", title)
        title = re.sub(r"^(?:OPERE|Opere|Carnevale|CARNEVALE|Quaresima|Primavera|Estate|Autunno|e|Primo|Secondo|Terzo)\s+(?=[A-Z/I])", "", title)
        title = re.sub(r"^\d+\s+", "", title)
        if len(title) < 3 or len(title) > 70 or not re.search(r"[A-Za-z]{3}", title): continue
        rest = it[mm.end():]
        comp = ""
        mc = re.search(r"musica[^.;]*?\bdi\s+((?:[A-Z][\w'’.]*\s*){1,4})", rest, re.I)
        if not mc: mc = re.match(r"\s*di\s+((?:[A-Z][\w'’.]*\s*){1,4})", rest)
        if mc: comp = mc.group(1).strip(" .,;")
        gen = {"s": "opera seria", "g": "opera buffa", "se": "opera semiseria"}.get(re.sub(r"[^a-z]", "", mm.group(1).lower().replace("d.", "")[:2]), "opera")
        esito = re.search(r"(piacque|non piacque|gran fiasco|esito [a-z]+|fiasco|caduta|applaudit\w+|ottimo|buono|mediocre|cattivo)", rest, re.I)
        rows.append({"anno": year, "stagione_nome": stag, "titolo": title, "autore": comp, "genere": gen,
                     "esito": esito.group(1).lower() if esito else "", "riga_fonte": "Romani 1862 (testo djvu), anno %s" % year})
        n_by_year[year] += 1
with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["anno", "stagione_nome", "titolo", "autore", "genere", "esito", "riga_fonte"]); w.writeheader(); w.writerows(rows)
print(len(rows), "opere; anni con righe:", len(n_by_year), "senza:", [y for y in range(1778, 1863) if y not in n_by_year][:40])
