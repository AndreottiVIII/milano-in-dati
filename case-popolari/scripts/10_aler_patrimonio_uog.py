"""Legge la pagina 'Patrimonio di proprieta' ALER' (aler.mi.it/amministrazione-trasparente/patrimonio/, scaricata il 1/11/2026) e scrive
pulito/aler_patrimonio_per_uog.csv (UOG, localita', destinazione, numero unita' immobiliari). Poi verifica i totali dichiarati dalla pagina.
Uso: python -I -X utf8 10_aler_patrimonio_uog.py <case-popolari>   (percorso assoluto)"""
import sys, os, re, html, csv

base = sys.argv[1]
t = open(os.path.join(base, "raw", "aler_trasparenza", "patrimonio.html"), encoding="utf-8", errors="replace").read()
t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
L = [x.strip() for x in t.split("\n") if x.strip()]
i0 = next(i for i, x in enumerate(L) if x.startswith("Il patrimonio di edilizia pubblica di ALER Milano"))
print(L[i0])
j = next(i for i, x in enumerate(L) if i > i0 and x == "Totale")
DEST = {"ALLOGGI", "BOX / POSTI AUTO", "COMMERCIALE", "STRUMENTALE"}
rows = []
uog, loc = None, None
declared = {}
k = j + 1
while k < len(L):
    x = L[k]
    if re.fullmatch(r"UOG\w*", x) and k + 1 < len(L) and not L[k + 1].endswith("Totale"):
        uog = x
    elif x.endswith("Totale") and k + 1 < len(L) and re.fullmatch(r"[\d\.]+", L[k + 1]):
        declared[x] = int(L[k + 1].replace(".", ""))
        k += 1
    elif x in DEST and k + 1 < len(L) and re.fullmatch(r"[\d\.]+", L[k + 1]):
        rows.append(dict(UOG=uog, localita=loc, destinazione=x, unita_immobiliari=int(L[k + 1].replace(".", ""))))
        k += 1
    elif x == "Totale complessivo":
        declared["Totale complessivo " + (uog or "")] = int(L[k + 1].replace(".", ""))
        k += 1
    elif x not in DEST and not re.fullmatch(r"[\d\.]+", x) and x.upper() == x and len(x) > 2 and not x.startswith("UOG"):
        loc = x
    if x.startswith("Fare clic") or x.startswith("Copyright") or x.startswith("Aler Milano - "):
        break
    k += 1
with open(os.path.join(base, "pulito", "aler_patrimonio_per_uog.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["UOG", "localita", "destinazione", "unita_immobiliari", "fonte"])
    w.writeheader()
    for r in rows:
        r["fonte"] = "aler.mi.it/amministrazione-trasparente/patrimonio/ (pagina scaricata il 2026-11-01; data dei dati non dichiarata)"
        w.writerow(r)
print(len(rows), "righe; totali dichiarati:", declared)
import collections
tot = collections.Counter()
mil = collections.Counter()
for r in rows:
    tot[r["destinazione"]] += r["unita_immobiliari"]
    if r["localita"] and r["localita"].startswith("MILANO"):
        mil[r["destinazione"]] += r["unita_immobiliari"]
print("somma righe, tutte le localita':", dict(tot), sum(tot.values()))
print("somma righe, Milano citta':", dict(mil), sum(mil.values()))
