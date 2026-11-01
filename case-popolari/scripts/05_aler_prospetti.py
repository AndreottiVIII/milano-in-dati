"""Legge i 'Prospetto n.5 - entrate da canoni di locazione per titolo giuridico' di ALER Milano (2018-2025, PDF)
e scrive pulito/aler_sfitti_serie.csv (una riga per anno e voce).
Uso: python -I -X utf8 05_aler_prospetti.py <cartella canoni con prospetto_<anno>.pdf/.txt> <cartella pulito>   (percorsi assoluti)
Il testo e' quello di `pdftotext -layout` (stesso nome .txt); la pagina e' sempre la 1 (il prospetto e' lungo 2 pagine, le occupazioni stanno a p.2)."""
import sys, os, re, csv
src, out = sys.argv[1], sys.argv[2]
num = lambda s: int(s.replace(".", ""))
VOCI = [  # (nome voce, regex sulla riga)
 ("canone sociale con contratto", r"^\s*2\s+con contratto\s+([\d\.]+)\s+([\d\.]+)"),
 ("canone sociale con contratto (piani di valorizzazione)", r"^\s*con contratto piani di valorizzazione\s+([\d\.]+)\s+([\d\.]+)"),
 ("senza contratto (occupati senza titolo)", r"^\s*3\s+senza contratto\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti (totale)", r"^\s*4\s+sfitti di cui:\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti: in corso di ristrutturazione", r"^\s*5\s+in corso di ristrutturazione\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti: in corso di riassegnazione", r"^\s*6\s+in corso di riassegnazione\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti: in fase di demolizione", r"^\s*in fase di demolizione\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti: destinati a piani di vendita", r"^\s*(?:7\s+)?destinati a piani di vendita\s+([\d\.]+)\s+([\d\.]+)"),
 ("sfitti: destinati a piani di valorizzazione", r"^\s*destinati a piani di valorizzazione.*?\s([\d\.]+)\s+([\d\.]+)\s*$"),
 ("totale ALER a canone sociale", r"^\s*8\s+Totale Aler\s+([\d\.]+)\s+([\d\.,]+)"),
]
rows = []
for anno in range(2018, 2026):
    txt = open(os.path.join(src, f"prospetto_{anno}.txt"), encoding="utf-8", errors="replace").read().split("\n")
    for nome, rx in VOCI:
        for i, l in enumerate(txt):
            m = re.search(rx, l, re.I)
            if m:
                rows.append(dict(anno=anno, voce=nome, n_alloggi=num(m.group(1)), mq_convenzionali=m.group(2).replace(".", "").split(",")[0], riga_testo=l.strip()[:120],
                                 fonte=f"aler.mi.it/download/anticorruzione/beni_immobiliari_gestione_patrimonio/canoni_incassati/prospetto_{anno}.pdf (prospetto n.5, p.1)"))
                break
    # occupazioni senza titolo (pagina 2): il primo numero dopo l'intestazione
    for i, l in enumerate(txt):
        if "Occupazioni senza titolo" in l:
            nums = [x for x in re.findall(r"(?<![\d\.,])(\d{1,3}(?:\.\d{3})*|\d+)(?![\d\.,])", " ".join(txt[i:i+14]))]
            nums = [n for n in nums if n not in ("48", "49")]
            rows.append(dict(anno=anno, voce="occupazioni senza titolo (p.2)", n_alloggi=num(nums[0]) if nums else "", mq_convenzionali="", riga_testo=" | ".join(nums[:4]),
                             fonte=f"aler.mi.it/.../canoni_incassati/prospetto_{anno}.pdf (prospetto n.5, p.2)"))
            break
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "aler_sfitti_serie.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# tabella larga
import collections
piv = collections.OrderedDict()
for r in rows: piv.setdefault(r["voce"], {})[r["anno"]] = r["n_alloggi"]
print("voce;" + ";".join(str(a) for a in range(2018, 2026)))
for v, d in piv.items(): print(v + ";" + ";".join(str(d.get(a, "")) for a in range(2018, 2026)))
