"""Estrae dai NOTE.md di ogni filone le sezioni e righe sui limiti, in out/limiti_note.txt.
Serve a leggere i limiti prima di usare una variabile."""
import os, re
ROOT = r"C:\Users\davide\Desktop\ClaudeTower\milano-in-dati"
OUT = os.path.join(ROOT, "incroci-esplorativi", "out", "limiti_note.txt")
KW = re.compile(r"limit|trappol|attenz|caut|avvert|non confront|rottura|salto|interruz|cambio di (metodo|definiz)|stima|modello|condivis|piccol|cap\b|omi\b|non affidabil|fragile|artefatt", re.I)
HEAD = re.compile(r"^#+\s*(.*)$")
HEADKW = re.compile(r"limit|trappol|attenz|caut|avvert|problem|difett|non si pu|cosa non", re.I)
res = []
for top in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, top, "NOTE.md")
    if not os.path.isfile(p):
        continue
    txt = open(p, encoding="utf8", errors="replace").read().splitlines()
    sect, take = [], False
    for ln in txt:
        m = HEAD.match(ln)
        if m:
            take = bool(HEADKW.search(m.group(1)))
            if take:
                sect.append(ln)
            continue
        if take and ln.strip():
            sect.append(ln)
    s = "\n".join(sect)
    res.append(f"\n===== {top} ({len(s)} char) =====\n{s}")
open(OUT, "w", encoding="utf8").write("\n".join(res))
print(len(res), sum(len(r) for r in res))
for r in res:
    print(r.split("\n")[1])
