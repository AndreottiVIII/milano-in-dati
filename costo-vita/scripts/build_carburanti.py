"""Prezzi dei carburanti negli impianti del comune di Milano, dall'archivio MIMIT (prezzo alle 8 di mattina), 2015-2026.
Per ogni giorno: mediana dei prezzi degli impianti (per carburante e self/servito); per ogni mese: media delle mediane giornaliere.
Uso: python -I -X utf8 build_carburanti.py <costo-vita assoluto>
Scrive pulito/carburanti_milano_mensile.csv, pulito/controlli_carburanti.txt"""
import sys, os, csv, glob, statistics, collections
C = sys.argv[1]
d = os.path.join(C, "raw", "mimit", "archivio_milano")
day = collections.defaultdict(list); nst = collections.defaultdict(set); log = []
nrows = 0; dropped = 0
for fn in sorted(glob.glob(os.path.join(d, "prezzi_milano_*.csv"))):
    for r in csv.DictReader(open(fn, encoding="utf-8"), delimiter=";"):
        nrows += 1
        try: p = float(r["prezzo"].replace(",", "."))
        except ValueError: dropped += 1; continue
        if not (0.4 <= p <= 4.0): dropped += 1; continue
        fuel = r["descCarburante"].strip()
        if fuel not in ("Benzina", "Gasolio", "GPL", "Metano"): continue
        key = (r["file_data"], fuel, r["isSelf"].strip())
        day[key].append(p); nst[key].add(r["idImpianto"])
mon = collections.defaultdict(list); ns = collections.defaultdict(list)
for (dt, fuel, self_), v in day.items():
    mon[(dt[:4] + "-" + dt[4:6], fuel, self_)].append(statistics.median(v)); ns[(dt[:4] + "-" + dt[4:6], fuel, self_)].append(len(nst[(dt, fuel, self_)]))
with open(os.path.join(C, "pulito", "carburanti_milano_mensile.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["mese", "carburante", "self_service", "prezzo_mediano_eur_litro_media_mensile", "giorni", "impianti_medi_per_giorno"])
    for k in sorted(mon):
        w.writerow([k[0], k[1], "si" if k[2] == "1" else "no", round(statistics.mean(mon[k]), 4), len(mon[k]), round(statistics.mean(ns[k]), 1)])
log.append("righe lette %d, scartate (prezzo non numerico o fuori 0,4-4,0 euro) %d; mesi coperti %d" % (nrows, dropped, len(set(k[0] for k in mon))))
open(os.path.join(C, "pulito", "controlli_carburanti.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
