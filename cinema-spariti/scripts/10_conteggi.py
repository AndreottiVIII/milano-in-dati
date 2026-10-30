import sys, csv, collections
base = sys.argv[1]
rows = list(csv.DictReader(open(f"{base}/pulito/cinema.csv", encoding="utf-8-sig")))
sc = [r for r in rows if r["id"].startswith("SC")]
def iv(r): return [tuple(map(int, p.split("-"))) for p in r["periodi_attivita"].split(";") if p]
def attivo(r, y): return any(a <= y <= b for a, b in iv(r))
osm_att = [r for r in rows if r["id"].startswith("OSM_") and r["stato_2026"].startswith("attivo")]
out = []
print("anno | attivi (elenco spazioCinema, chiusi entro 2017) | + attivi OSM oggi")
for y in range(1900, 2021, 10):
    n = sum(attivo(r, y) for r in sc)
    n_ca = sum(attivo(r, y) and (r["apertura_incerta"] == "1" or r["chiusura_incerta"] == "1") for r in sc)
    extra = len(osm_att) if y >= 2020 else 0
    print(y, n, "(di cui con date 'circa':", n_ca, ")", extra)
    out.append((y, n, n_ca, extra))
print("decennio | aperture | chiusure (fine ultimo periodo)")
ap = collections.Counter(int(r["anno_apertura"]) // 10 * 10 for r in sc); ch = collections.Counter(int(r["anno_chiusura"]) // 10 * 10 for r in sc)
for d in range(1890, 2020, 10): print(d, ap.get(d, 0), ch.get(d, 0))
with open(f"{base}/pulito/conteggi_decenni_preliminari.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["anno_istantanea", "attivi_da_elenco", "di_cui_date_circa", "attivi_osm_oggi"]); w.writerows(out)
print("cinema con almeno un periodo che include anno 1953:", sum(attivo(r,1953) for r in sc), "(fonte stampa: 125 nel 1953)")
print("1950:", sum(attivo(r,1950) for r in sc), "(110) | 1946:", sum(attivo(r,1946) for r in sc), "(77) | 1975:", sum(attivo(r,1975) for r in sc),"(~160 anni 70)")
