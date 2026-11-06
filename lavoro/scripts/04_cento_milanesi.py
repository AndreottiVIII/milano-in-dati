"""Lavoro, passo 4: la condizione dei residenti di 15 anni e piu' (nel 1991 dai 14), per quartiere e per Milano.
Uso: python -I -X utf8 04_cento_milanesi.py <milano-in-dati>
Input : lavoro/out/lavoro_NIL.csv, lavoro/out/lavoro_comune.csv (passo 2)
Output: docs/lavoro/data/cento_milanesi.json  (nome nuovo: non sostituisce nessun file della pagina)
Gruppi (si sommano alla base, che e' forze di lavoro + non forze di lavoro):
  lav = occupati, cerca = in cerca di lavoro (comprende il primo lavoro), stu = studenti, casa = casalinghe/i,
  pens = pensionati ("ritirati dal lavoro"; nel 2011 la voce P139), altri = il resto delle non forze di lavoro.
Solo 1991, 2001, 2011: per 2021 e 2023 il censimento permanente non pubblica queste voci."""
import sys, json
import pandas as pd

root = sys.argv[1]
n = pd.read_csv(root + "/lavoro/out/lavoro_NIL.csv")
c = pd.read_csv(root + "/lavoro/out/lavoro_comune.csv")
G = ["lav", "cerca", "stu", "casa", "pens", "altri"]


def riga(r):
    base = r.fl + r.nfl
    altri = r.nfl - r.rit - r.cas - r.stu
    v = [r.occ, r.cerca, r.stu, r.cas, r.rit, altri]
    assert abs(sum(v) - base) < 1e-6 and altri >= 0, r
    return [int(base)] + [int(x) for x in v]


out = {"anni": [1991, 2001, 2011], "gruppi": ["base"] + G,
       "nota": "Per ogni anno: [base, " + ", ".join(G) + "]. Base = residenti di 15 anni e piu' (1991: dai 14).",
       "milano": {}, "nil": []}
for y in out["anni"]:
    out["milano"][str(y)] = riga(c[c.anno == y].iloc[0])
for i, g in n.groupby("nil"):
    g = g.set_index("anno")
    e = {"i": int(i), "n": g.iloc[0]["nil_nome"], "rob": bool(g.iloc[0]["robusto"])}
    for y in out["anni"]:
        e[str(y)] = riga(g.loc[y])
    out["nil"].append(e)
out["generato_da"] = "lavoro/scripts/04_cento_milanesi.py"
open(root + "/docs/lavoro/data/cento_milanesi.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print("ok", len(out["nil"]))
