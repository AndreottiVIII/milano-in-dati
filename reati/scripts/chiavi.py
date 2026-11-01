"""Numeri chiave per NOTE.md -> pulito/riepilogo.json e inventario_fonti.csv. Uso: chiavi.py <reati> <milano-in-dati>"""
import sys, csv, json, collections
R, M = sys.argv[1], sys.argv[2]
OUT = f"{R}/pulito"
def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))
K = {}
lines = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)
# conteggi Comune ds564 (2004-2023) + ISTAT 2024 per il comune
c564 = {(int(r["anno"]), r["tipo_codice"]): int(r["denunce_comune"]) for r in rd(f"{OUT}/milano_comune_ds564.csv")}
lg = rd(f"{OUT}/delitti_tipo_territorio_anno.csv")
for r in lg:
    if r["codice_istat"] == "015146" and r["anno"] == "2024" and r["denunce"]:
        c564[(2024, r["tipo_codice"])] = int(r["denunce"])
P("== Milano comune, denunce assolute (ds564 2004-2023, ISTAT 2024)")
for t in ["TOT", "THEFT", "PICKTHEF", "BAGTHEF", "BURGTHEF", "VEHITHEF", "CARTHEF", "ROBBER", "STREETROB", "DAMAGE", "SWINCYB", "CYBERCRIM", "DRUG", "RAPE", "CULPINJU", "INTENHOM"]:
    P(t, {y: c564.get((y, t)) for y in (2004, 2006, 2007, 2011, 2019, 2020, 2023, 2024)})
K["milano_comune_totale"] = {y: c564.get((y, "TOT")) for y in range(2004, 2025)}
tot = K["milano_comune_totale"]
P("picco", max(tot, key=tot.get), tot[max(tot, key=tot.get)], "minimo", min(tot, key=tot.get), tot[min(tot, key=tot.get)], "2024 vs 2004", f"{(tot[2024]/tot[2004]-1)*100:.1f}%", "2024 vs picco", f"{(tot[2024]/max(tot.values())-1)*100:.1f}%")
P("scippi/borseggi al giorno 2024:", round(c564[(2024, 'PICKTHEF')] / 366, 1), "(2024 bisestile), furti totali al giorno", round(c564[(2024, 'THEFT')] / 366))
# comune su provincia, 2024
d = {(r["codice_istat"], r["anno"], r["tipo_codice"]): r for r in lg}
mc, mp = d[("015146", "2024", "TOT")], d[("ITC45", "2024", "TOT")]
P("comune/provincia 2024: denunce", int(mc["denunce"]) / int(mp["denunce"]), "popolazione", int(mc["popolazione_istat_implicita"]) / int(mp["popolazione_istat_implicita"]))
# 12 grandi comuni 2024
AREAN = json.load(open(f"{R}/raw/probe/codelists.json", encoding="utf8"))["CL_ITTER107"]
for y in (2019, 2024):
    big = {r["REF_AREA"]: float(r["OBS_VALUE"]) for r in rd(f"{R}/raw/istat/df8_grandi_comuni_CRIMET.csv") if r["TYPE_CRIME"] == "TOT" and r["TIME_PERIOD"] == str(y) and r["OBS_VALUE"]}
    P("12 grandi comuni", y, [(AREAN[k], round(v)) for k, v in sorted(big.items(), key=lambda kv: -kv[1])])
# Italia / ISTAT
P("Italia totale tasso 2006 2007 2020 2024:", [round(float(d[("IT", str(y), "TOT")]["per_100mila"])) for y in (2006, 2007, 2020, 2024)])
P("Milano+Monza 2006->2024", d[("ITC45+IT108", "2006", "TOT")]["per_100mila"], d[("ITC45+IT108", "2024", "TOT")]["per_100mila"])
# omicidi volontari consumati: denunce assolute Milano comune e Italia
P("omicidi volontari consumati, Milano comune:", {y: c564.get((y, "INTENHOM")) for y in range(2004, 2025)})
P("omicidi volontari consumati, Italia:", {y: d[("IT", str(y), "INTENHOM")]["denunce"] for y in (2006, 2010, 2015, 2019, 2024)})
# gravi: tasso per 100k Milano comune vs Italia 2024
for t in ("INTENHOM", "RAPE", "ROBBER", "THEFT", "PICKTHEF"):
    P(t, "2024 Milano comune / Italia =", round(float(d[("015146", "2024", t)]["per_100mila"]) / float(d[("IT", "2024", t)]["per_100mila"]), 2), "| Milano prov / Italia =", round(float(d[("ITC45", "2024", t)]["per_100mila"]) / float(d[("IT", "2024", t)]["per_100mila"]), 2))
json.dump(K, open(f"{OUT}/riepilogo.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
open(f"{R}/out/chiavi.txt", "w", encoding="utf8").write("\n".join(lines))
