"""Controllo: schede la cui istituzione (hasCIS) e' tra quelle presenti nel set Milano ma che NON sono nel set.
uso: python -I 05_verifica_istituzioni.py <cartella_tsv> <csv_milano> <output_txt>"""
import os, sys, csv
from collections import Counter, defaultdict
tsv, csvp, outp = sys.argv[1:4]
mil = {r["iri"]: r for r in csv.DictReader(open(csvp, encoding="utf-8"))}
cis_of = defaultdict(set); lab = {}; cov = {}
for fn in sorted(os.listdir(tsv)):
    for l in open(os.path.join(tsv, fn), encoding="utf-8"):
        s, k, o = l.rstrip("\n").split("\t", 2)
        if k == "hasCIS" and not s.startswith("TimeIndexed"):
            cis_of[s].add(o)
        elif k == "label" and s.startswith("CulturalInstituteOrSite/"):
            lab.setdefault(s, o.strip('"').split('"')[0])
        elif k == "dc_coverage":
            cov[s] = o
inst_mi = Counter()
for p in mil:
    for c in cis_of.get(p, ()):
        inst_mi[c] += 1
out = ["istituzioni del set Milano: totale schede nel set / schede nazionali con quella istituzione / fuori dal set (copertura dc)"]
fuori_tot = 0
for c, n in inst_mi.most_common(40):
    tutte = [p for p, cs in cis_of.items() if c in cs]
    fuori = [p for p in tutte if p not in mil]
    fuori_tot += len(fuori)
    covs = Counter(cov.get(p, "?") for p in fuori).most_common(3)
    out.append(f"{lab.get(c, c)[:60]:60s} set={n:5d} naz={len(tutte):5d} fuori={len(fuori):5d} {covs}")
out.append(f"fuori dal set (top40 istituzioni): {fuori_tot}")
open(outp, "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
