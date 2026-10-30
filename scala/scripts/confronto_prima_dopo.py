"""Confronto prima/dopo dei dati della pagina (docs/scala/data/titoli.json): copertura di data, direttore, interpreti nel periodo 1946-2022 e balli per stagione 1778-1881.
Uso: python -I -X utf8 scripts/confronto_prima_dopo.py   (legge pulito/_backup_prima_balli/titoli.json = versione di ieri, e ../docs/scala/data/titoli.json)"""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = os.path.join(HERE, "..")
old = json.load(open(os.path.join(BASE, "pulito", "_backup_prima_balli", "titoli.json"), encoding="utf-8"))
new = json.load(open(os.path.join(BASE, "..", "docs", "scala", "data", "titoli.json"), encoding="utf-8"))
def stat(t, a, b, nonconc=True):
    r = [x for x in t if a <= x[0] <= b and (x[5] not in ("c",) or not nonconc)]
    iso = lambda s: bool(re.match(r"^\d{4}-\d\d-\d\d$", s or ""))
    return dict(righe=len(r), con_data=sum(1 for x in r if iso(x[2])), con_direttore=sum(1 for x in r if x[6]), con_regia=sum(1 for x in r if x[7]), con_interpreti=sum(1 for x in r if x[8]))
for a, b in [(1946, 1963), (1964, 2022), (1946, 2022)]:
    print("%d-%d prima %s" % (a, b, stat(old, a, b))); print("%d-%d dopo  %s" % (a, b, stat(new, a, b)))
bal = lambda t: sum(1 for x in t if 1778 <= x[0] <= 1881 and x[5] == "b")
print("balli in titoli.json 1778-1881: prima", bal(old), "dopo", bal(new))
print("titoli totali: prima", len(old), "dopo", len(new))
