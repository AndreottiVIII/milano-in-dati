"""Riepiloghi dalle tabelle pulite. Scrive pulito/riepilogo.json, pulito/riepilogo.txt e alcune tabelle CSV.
Uso: python -I -X utf8 11_riepilogo.py <pulito_dir>"""
import sys, csv, os, json, collections, statistics
P = sys.argv[1]
rd = lambda f: list(csv.DictReader(open(os.path.join(P, f), encoding="utf-8")))
out, L = {}, []
def say(s=""):
    L.append(s); print(s)
# ---------- 1. linee per anno
lin = rd("metro_passeggeri_linea_anno.csv")
v = {(r["linea"], int(r["anno"])): float(r["passeggeri_mln"]) for r in lin}
anni = sorted({a for _, a in v})
say("== 1. Passeggeri metro per linea (mln)")
say("anno " + " ".join(f"{l:>6}" for l in ("M1", "M2", "M3", "M4", "M5")) + "  totale")
tot = {}
for a in anni:
    row = [v.get((l, a), 0.0) for l in ("M1", "M2", "M3", "M4", "M5")]
    tot[a] = sum(row)
    say(f"{a} " + " ".join(f"{x:6.1f}" for x in row) + f"  {tot[a]:6.1f}")
out["totale_somma_linee_mln"] = {a: round(t, 1) for a, t in tot.items()}
say()
say("== 2. Covid: variazione rispetto al 2019 (per linea)")
cov = {}
for l in ("M1", "M2", "M3", "M5"):
    cov[l] = {"2019_mln": v[(l, 2019)]}
    for a in (2020, 2021, 2022, 2023, 2024, 2025):
        cov[l][f"{a}_%"] = round(100 * v[(l, a)] / v[(l, 2019)] - 100, 1)
    say(f"{l}: " + "  ".join(f"{k}={x}" for k, x in cov[l].items()))
tt = lambda a: sum(v.get((l, a), 0) for l in ("M1", "M2", "M3", "M5"))
say(f"M1+M2+M3+M5 (le linee che c'erano nel 2019): 2019={tt(2019):.1f} 2020={tt(2020):.1f} ({100*tt(2020)/tt(2019)-100:.1f}%) 2024={tt(2024):.1f} ({100*tt(2024)/tt(2019)-100:.1f}%) 2025={tt(2025):.1f} ({100*tt(2025)/tt(2019)-100:.1f}%)")
say(f"Rete intera 2025 (con M4) = {tot[2025]:.1f} mln = {100*tot[2025]/tot[2019]-100:+.1f}% sul 2019")
out["covid_per_linea"] = cov
out["esistenti_2019_senza_M4"] = {a: round(tt(a), 1) for a in anni}
# ---------- 3. effetto M4
say()
say("== 3. M4 e le altre linee (confronto, NON prova di causa)")
for a in (2022, 2023, 2024, 2025):
    say(f"{a}: M4={v.get(('M4', a), 0):.1f}  M1+M2+M3={v[('M1', a)] + v[('M2', a)] + v[('M3', a)]:.1f}  M5={v[('M5', a)]:.1f}")
d = {l: v[(l, 2025)] - v[(l, 2024)] for l in ("M1", "M2", "M3", "M4", "M5")}
say("variazione 2024->2025 (mln): " + ", ".join(f"{l} {x:+.1f}" for l, x in d.items()) + f"  | somma {sum(d.values()):+.1f}")
say("ATTENZIONE: 2024 e' letto da un grafico (+-0,5 mln), 2025 e' citato da Wikipedia; stesse definizioni non garantite")
out["delta_2024_2025_mln"] = {l: round(x, 1) for l, x in d.items()}
# ---------- 4. Linate M4 mensile
lin4 = rd("report24_m4_linate_mese.csv")
say()
say("== 4. Linate M4 passeggeri/mese (migliaia, letti dal grafico)")
m4 = [(r["mese"], float(r["passeggeri_migliaia_letto_da_grafico"])) for r in lin4]
mx = max(m4, key=lambda x: x[1])
mn = min(m4, key=lambda x: x[1])
say(f"primo mese {m4[0]}, minimo {mn}, massimo {mx}, ultimo {m4[-1]}")
out["linate_m4"] = {"primo": m4[0], "min": mn, "max": mx, "ultimo": m4[-1]}
# ---------- 5. totale ATM Carta
carta = rd("atm_carta_mobilita_numeri.csv")
say()
say("== 5. Passeggeri rete ATM (metro+superficie) dalle Carte della Mobilita, e quota metro")
tt_ = {int(r["anno_dati"]): int(r["passeggeri_rete_atm_metro_e_superficie"]) for r in carta}
for a in sorted(tt_):
    met = tot.get(a)
    say(f"{a}: rete {tt_[a]/1e6:7.1f} mln" + (f" | metro (somma linee) {met:6.1f} = {100*met/(tt_[a]/1e6):.0f}%" if met else ""))
out["rete_atm_carta"] = {a: tt_[a] for a in tt_}
# ---------- 6. stazioni treno Milano
say()
say("== 6. Stazioni FERROVIARIE di Milano (Trenord, saliti giorno feriale medio di novembre)")
fr = rd("stazioni_treno_milano_frequentazione.csv")
nov = {}
for r in fr:
    if r["tipo_giorno"] == "Feriale" and r["mese_rilevazione"] == "11":
        nov[(r["stazione"], int(r["anno"]))] = (int(float(r["saliti_24h"])), int(float(r["saliti_7_9"] or 0)), int(float(r["discesi_7_9"] or 0)))
st = sorted({s for s, _ in nov})
tab = []
for s in st:
    g = lambda a, i=0: nov.get((s, a), (None,) * 3)[i]
    d19, d20, d25 = g(2019), g(2020), g(2025)
    tab.append({"stazione": s, "saliti_2015": g(2015), "saliti_2019": d19, "saliti_2020": d20, "saliti_2021": g(2021), "saliti_2022": g(2022),
                "saliti_2023": g(2023), "saliti_2024": g(2024), "saliti_2025": d25,
                "pct_2020_su_2019": round(100 * d20 / d19, 1) if d19 and d20 else None,
                "pct_2025_su_2019": round(100 * d25 / d19, 1) if d19 and d25 else None,
                "rapporto_discesi_su_saliti_7_9_2019": round(g(2019, 2) / g(2019, 1), 2) if g(2019, 1) else None})
w = csv.DictWriter(open(os.path.join(P, "stazioni_treno_covid_ripresa.csv"), "w", newline="", encoding="utf-8"), fieldnames=list(tab[0]))
w.writeheader()
w.writerows(tab)
t2 = [t for t in tab if t["pct_2025_su_2019"] is not None]
say("stazione | saliti 2019 | 2020 (% del 2019) | 2025 (% del 2019) | discesi/saliti 7-9 nel 2019 (>1 = si arriva qui al mattino)")
for t in sorted(t2, key=lambda t: t["pct_2025_su_2019"]):
    say(f"{t['stazione']:36} {t['saliti_2019']:>6} {t['pct_2020_su_2019']:>6}% {t['pct_2025_su_2019']:>6}%  {t['rapporto_discesi_su_saliti_7_9_2019']}")
pairs = [(t["rapporto_discesi_su_saliti_7_9_2019"], t["pct_2025_su_2019"]) for t in t2 if t["rapporto_discesi_su_saliti_7_9_2019"]]
if len(pairs) > 3:
    xs, ys = zip(*pairs)
    mx_, my_ = statistics.mean(xs), statistics.mean(ys)
    r_ = sum((a - mx_) * (b - my_) for a, b in pairs) / (sum((a - mx_) ** 2 for a in xs) ** .5 * sum((b - my_) ** 2 for b in ys) ** .5)
    say(f"correlazione (Pearson) tra 'rapporto arrivi/partenze 7-9 nel 2019' e 'ripresa 2025/2019' su {len(pairs)} stazioni: {r_:.2f}")
    out["corr_arrivi_ripresa_treni"] = round(r_, 2)
tot19 = sum(t["saliti_2019"] for t in t2)
tot25 = sum(t["saliti_2025"] for t in t2)
tot20 = sum(t["saliti_2020"] for t in t2)
say(f"Somma stazioni confrontabili ({len(t2)}): 2019={tot19} 2020={tot20} ({100*tot20/tot19:.0f}%) 2025={tot25} ({100*tot25/tot19:.0f}%)")
out["treni_milano_somma"] = {"n": len(t2), "2019": tot19, "2020": tot20, "2025": tot25}
n25 = sorted([(nov[(s, 2025)][0], s) for s in st if (s, 2025) in nov], reverse=True)
say("feriale nov 2025, piu' frequentate (saliti 24h): " + ", ".join(f"{s} {x}" for x, s in n25[:5]))
say("feriale nov 2025, meno frequentate: " + ", ".join(f"{s} {x}" for x, s in n25[-5:]))
wk = collections.defaultdict(dict)
for r in fr:
    if r["anno"] == "2025" and r["mese_rilevazione"] == "11":
        wk[r["stazione"]][r["tipo_giorno"]] = int(float(r["saliti_24h"]))
sf = {k: sum(w_.get(k, 0) for w_ in wk.values()) for k in ("Feriale", "Sabato", "Festivo")}
say(f"nov 2025, somma delle 25 stazioni: feriale={sf['Feriale']} sabato={sf['Sabato']} ({100*sf['Sabato']/sf['Feriale']:.0f}%) festivo={sf['Festivo']} ({100*sf['Festivo']/sf['Feriale']:.0f}%)")
out["treni_giorno_tipo_nov2025"] = sf
# ---------- 7. GTFS servizio
say()
say("== 7. Servizio metro (GTFS feed 425, 26/10-30/11/2026): corse al giorno per linea")
sv = rd("gtfs_metro_servizio_giorno.csv")
agg = collections.defaultdict(set)
for r in sv:
    k = "Feriale" if r["giorno_settimana"] in ("Mon", "Tue", "Wed", "Thu", "Fri") else ("Sabato" if r["giorno_settimana"] == "Sat" else "Domenica")
    agg[(r["linea"], k)].add(int(r["corse"]))
for l in ("M1", "M2", "M3", "M4", "M5"):
    say(f"{l}: feriale {sorted(agg[(l, 'Feriale')])} sabato {sorted(agg[(l, 'Sabato')])} domenica {sorted(agg[(l, 'Domenica')])}")
fw = sum(max(agg[(l, 'Feriale')]) for l in ("M1", "M2", "M3", "M4", "M5"))
say(f"corse metro totali in un feriale: {fw} (ATM Carta 2026: media annuale 3.261 'corse al giorno lun-ven invernale in metropolitana')")
out["gtfs_corse_feriale_totale"] = fw
# ---------- 8. aperture
say()
say("== 8. Stazioni per anno di apertura (it.wikipedia 'Stazioni della metropolitana di Milano', righe stazione-linea)")
wk_ = rd("stazioni_wikipedia.csv")
c = collections.Counter(r["apertura_iso"][:4] for r in wk_)
cum = 0
for y in sorted(c):
    cum += c[y]
    say(f"{y}: +{c[y]} (cumulato {cum})")
nl = collections.Counter(r["stazione"] for r in wk_)
say("stazioni di interscambio (>=2 linee): " + str(sum(1 for s, n in nl.items() if n > 1)) + " su " + str(len(nl)))
say("stazioni con 3 o piu' linee: " + (", ".join(s for s, n in nl.items() if n >= 3) or "-"))
json.dump(out, open(os.path.join(P, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(P, "riepilogo.txt"), "w", encoding="utf-8").write("\n".join(L))
