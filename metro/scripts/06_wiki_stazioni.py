"""Legge il wikitext di it.wikipedia 'Stazioni della metropolitana di Milano' (CC BY-SA 4.0) e produce pulito/stazioni_wikipedia.csv:
una riga per stazione-linea con data di apertura (quando la cella ha una data per linea) o la data unica.
Solo la sezione 'Stazioni aperte'. Uso: python -I -X utf8 06_wiki_stazioni.py <wikitext> <out_csv>"""
import sys, re, csv
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf-8").read()
sec = t.split("==Stazioni aperte==")[1]
sec = re.split(r"\n==[^=]", sec)[0]
MESI = {m: i for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}
def iso(s):
    m = re.search(r"(\d{1,2})[º°]?\s+(\w+)\s+(\d{4})", s)
    if m and m.group(2).lower() in MESI: return f"{m.group(3)}-{MESI[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"(\w+)\s+(\d{4})", s)
    if m and m.group(1).lower() in MESI: return f"{m.group(2)}-{MESI[m.group(1).lower()]:02d}"
    m = re.search(r"(\d{4})", s)
    return m.group(1) if m else ""
def clean(c):
    c = re.sub(r'data-sort-value="[^"]*"\s*\|', "", c)
    c = re.sub(r"\[\[(\d{4})\]\]", r"\1", c)
    c = re.sub(r"<ref.*?(</ref>|/>)", "", c, flags=re.S)
    c = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", c)
    c = re.sub(r"<br\s*/?>", " ", c); c = re.sub(r"<[^>]+>|\{\{.*?\}\}", "", c)
    return c.strip()
rows = []
for blk in sec.split("\n|-")[1:]:
    blk = blk.split("\n", 1)[1] if "\n" in blk else ""
    cells = [c for c in re.split(r"\n\|(?!\|)", "\n" + blk) if c.strip()]
    if len(cells) < 6 or cells[0].lstrip().startswith("!"): continue
    nome = clean(cells[0])
    linee = sorted(set(re.findall(r"linea M(\d)", cells[1])))
    comune = clean(cells[2])
    dtxt = clean(cells[4]); tip = clean(cells[5])
    per_linea = re.findall(r"(\d{1,2}[º°]?\s+\w+\s+\d{4})\s*\(M(\d)\)", dtxt)
    if per_linea:
        dd = {f"M{l}": iso(d) for d, l in per_linea}
    else:
        dd = {f"M{l}": iso(dtxt) for l in linee}
    for l in linee:
        rows.append([nome, f"M{l}", comune, dd.get(f"M{l}", ""), dtxt, tip])
w = csv.writer(open(out, "w", newline="", encoding="utf-8")); w.writerow(["stazione","linea","comune","apertura_iso","apertura_testo_wikipedia","tipologia"]); w.writerows(rows)
print(len(rows), "righe stazione-linea,", len({r[0] for r in rows}), "stazioni")
print([r for r in rows if r[3]==""])
