"""Riepilogo dei numeri principali (tutti calcolati dalle tabelle in pulito/).
Uso: python -I -X utf8 riepilogo.py <costo-vita assoluto>
Scrive pulito/riepilogo_costo_vita.json e pulito/riepilogo_costo_vita.txt"""
import sys, os, csv, json, statistics, collections
C = sys.argv[1]; PU = os.path.join(C, "pulito")
out = {}; txt = []
def say(s): print(s); txt.append(s)
def rd(fn): return list(csv.DictReader(open(os.path.join(PU, fn), encoding="utf-8"), delimiter=";"))

# ---------- indici
voci = collections.defaultdict(dict)
for r in rd("nic_milano_voci_base2015.csv"): voci[r["voce"]][r["periodo"]] = float(r["indice_base2015_100"])
div = collections.defaultdict(dict)
for r in rd("nic_milano_divisioni_base2015.csv"): div[r["divisione"]][r["periodo"]] = float(r["indice_base2015_100"])
ita = collections.defaultdict(dict)
for r in rd("nic_italia_divisioni_base2015.csv"): ita[r["codice_ecoicop"]][r["periodo"]] = float(r["indice_base2015_100"])
def avg(s, y):
    v = [s.get("%04d-%02d" % (y, m)) for m in range(1, 13)]
    return statistics.mean(v) if all(x is not None for x in v) else None
def chg(s, y0, y1):
    a, b = avg(s, y0), avg(s, y1)
    return (b / a - 1) * 100 if a and b else None

ann = {int(r["anno"]): r for r in rd("nic_milano_generale_annuo_2000_2025.csv")}
Lm = {y: float(r["livello_milano_2025_100_da_tassi"]) for y, r in ann.items()}
Li = {y: float(r["livello_italia_2025_100_NIC"]) for y, r in ann.items()}
say("== INFLAZIONE (indice generale, medie annue)")
for y0 in (2000, 2005, 2010, 2015, 2020):
    m = (Lm[2025] / Lm[y0] - 1) * 100; i = (Li[2025] / Li[y0] - 1) * 100
    out["inflazione_%d_2025" % y0] = {"milano": round(m, 1), "italia": round(i, 1)}
    say("  %d -> 2025: Milano %+.1f%%  Italia %+.1f%%" % (y0, m, i))
say("  tasso annuo Milano ds1821: 2022 %.1f%%, 2023 %.1f%%, 2024 %.1f%%, 2025 %.1f%%; Italia (calcolato) 2022 %s%%, 2023 %s%%" % (float(ann[2022]["tasso_annuo_milano_ds1821_pct"]), float(ann[2023]["tasso_annuo_milano_ds1821_pct"]), float(ann[2024]["tasso_annuo_milano_ds1821_pct"]), float(ann[2025]["tasso_annuo_milano_ds1821_pct"]), ann[2022]["tasso_italia_NIC_pct_calcolato"], ann[2023]["tasso_italia_NIC_pct_calcolato"]))
# mensile Milano ds1499
mens = {r["Periodo"][:7]: float(r["Tasso"]) for r in csv.DictReader(open(os.path.join(C, "raw", "comune", "ds1499", [f for f in os.listdir(os.path.join(C, "raw", "comune", "ds1499")) if f.endswith(".csv")][0]), encoding="utf-8"), delimiter=";")}
pk = max((v, k) for k, v in mens.items() if "2021-01" <= k <= "2026-12")
out["inflazione_mensile_picco_2021_2026"] = {"mese": pk[1], "tasso": pk[0]}
say("  tasso mensile Milano ds1499, picco 2021-2026: %s = %.1f%% ; ultimo mese %s = %.1f%%" % (pk[1], pk[0], max(mens), mens[max(mens)]))

say("== SHOCK ENERGETICO (indici Milano, base 2015=100)")
shock = {}
for k in ("elettricita", "gas", "benzina", "gasolio_auto"):
    s = voci[k]; a21 = avg(s, 2021)
    mx = max((v, p) for p, v in s.items() if "2021-01" <= p <= "2025-12")
    shock[k] = {"media_2021": round(a21, 1), "picco": mx[0], "mese_picco": mx[1], "picco_su_media_2021": round((mx[0] / a21 - 1) * 100, 0), "media_2022_su_2021": round(chg(s, 2021, 2022), 1), "media_2023_su_2021": round(chg(s, 2021, 2023), 1), "media_2025_su_2021": round(chg(s, 2021, 2025), 1), "2026-09": s.get("2026-09")}
    say("  %-13s media 2021 %.1f -> picco %.1f (%s, %+.0f%%); media 2022 %+.1f%%, 2023 %+.1f%%, 2025 %+.1f%% rispetto al 2021; 2026-09 = %s" % (k, a21, mx[0], mx[1], (mx[0] / a21 - 1) * 100, chg(s, 2021, 2022), chg(s, 2021, 2023), chg(s, 2021, 2025), s.get("2026-09")))
out["shock_energetico"] = shock
g = div["0"]; a21 = avg(g, 2021)
mx = max((v, p) for p, v in g.items() if "2021-01" <= p <= "2025-12")
say("  indice generale Milano: media 2021 %.1f, picco %.1f (%s); 2026-09 = %.1f" % (a21, mx[0], mx[1], g["2026-09"]))
out["generale_picco"] = {"media_2021": round(a21, 1), "picco": mx[0], "mese": mx[1]}

say("== VOCI DI MILANO: aumenti (media annua 2025 sulla media annua dell'anno indicato)")
rows = rd("riepilogo_indici_voci.csv")
for col, lab in (("var_pct_2005_2025", "dal 2005"), ("var_pct_2010_2025", "dal 2010"), ("var_pct_2020_2025", "dal 2020")):
    v = [(float(r[col]), r["etichetta"]) for r in rows if r["tipo"] == "voce Milano" and r[col] != ""]
    v.sort(reverse=True)
    say("  %s - piu' su: %s" % (lab, "; ".join("%s %+.0f%%" % (b, a) for a, b in v[:6])))
    say("  %s - meno su: %s" % (lab, "; ".join("%s %+.0f%%" % (b, a) for a, b in v[-6:])))
    out["voci_" + col] = {"top": v[:6], "bottom": v[-6:]}
gen_m = [r for r in rows if r["tipo"] == "divisione Milano" and r["chiave"] == "00"][0]
say("  indice generale Milano (da 2015) %s%% ; 2020 %s%%" % (gen_m["var_pct_2015_2025"], gen_m["var_pct_2020_2025"]))

say("== BIGLIETTO ATM")
atm = [(r["data_inizio"], float(r["prezzo_eur"])) for r in rd("atm_tariffe_storico.csv") if r["titolo"] == "biglietto ordinario" and r["data_inizio"]]
t02, t26 = 1.00, 2.20
say("  biglietto ordinario: 1,00 euro (2002) -> 2,20 euro (2023, ancora in vigore 1/11/2026): %+.0f%%" % ((t26 / t02 - 1) * 100))
say("  inflazione Milano 2002 -> 2025 (medie annue): %+.1f%% ; Italia %+.1f%%" % ((Lm[2025] / Lm[2002] - 1) * 100, (Li[2025] / Li[2002] - 1) * 100))
say("  il biglietto in euro 2025 (deflazionato con l'indice di Milano): 1,00 euro del 2002 = %.2f euro 2025; oggi 2,20 = %.2f volte il valore reale del 2002" % (1.0 / Lm[2002] * 100, 2.2 / (1.0 / Lm[2002] * 100)))
say("  1,50 euro (set 2011) -> 2,20: %+.0f%% ; inflazione Milano 2011->2025 %+.1f%%" % ((2.2 / 1.5 - 1) * 100, (Lm[2025] / Lm[2011] - 1) * 100))
b = voci["bus_tram_metro"]
say("  indice ISTAT 'trasporto su autobus' Milano: 2005->2025 %+.1f%%, 2011->2025 %+.1f%%, 2015->2025 %+.1f%%, 2019->2025 %+.1f%%" % (chg(b, 2005, 2025), chg(b, 2011, 2025), chg(b, 2015, 2025), chg(b, 2019, 2025)))
out["atm"] = {"biglietto_2002": 1.0, "biglietto_2026": 2.2, "var_pct": round((2.2 / 1.0 - 1) * 100), "inflazione_milano_2002_2025": round((Lm[2025] / Lm[2002] - 1) * 100, 1), "indice_istat_autobus_2011_2025": round(chg(b, 2011, 2025), 1), "indice_istat_autobus_2005_2025": round(chg(b, 2005, 2025), 1)}

say("== PREZZI IN EURO (Osservatorio Prezzi e Tariffe MIMIT, Milano)")
pr = rd("prezzi_medi_milano_mimit.csv")
def norm(n): return n.split(" (")[0].replace("Con Farina Di Grano", "").strip()
ser = collections.defaultdict(dict)
for r in pr: ser[(norm(r["prodotto"]), "", "")][(int(r["anno"]), int(r["mese"]))] = (float(r["prezzo_medio_eur"]), float(r["prezzo_min_eur"]), float(r["prezzo_max_eur"]))
mesi = sorted(set((int(r["anno"]), int(r["mese"])) for r in pr))
say("  mesi coperti: %s -> %s (%d)" % (mesi[0], mesi[-1], len(mesi)))
pr_out = {}
for key in sorted(ser):
    s = ser[key]; ks = sorted(s)
    f, l = ks[0], ks[-1]
    # media annua
    y = collections.defaultdict(list)
    for (a, m), v in s.items(): y[a].append(v[0])
    pr_out[key[0]] = {"primo": [f, s[f][0]], "ultimo": [l, s[l][0]], "var_pct": round((s[l][0] / s[f][0] - 1) * 100, 1) if s[f][0] else None, "medie_annue": {a: round(statistics.mean(v), 3) for a, v in sorted(y.items()) if len(v) >= 6}, "n_mesi": len(ks)}
out["prezzi_mimit"] = pr_out
for key in ("Caffè Espresso Al Bar", "Cappuccino Al Bar", "Panino Al Bar", "Pasto In Pizzeria", "Pasto Al Fast-food", "Trasporto Urbano Multimodale - Biglietto", "Cinema - Biglietto", "Taglio Capelli Uomo", "Pane Fresco", "Benzina Verde Senza Servizio Alla Pompa", "Gasolio Per Auto Senza Servizio Alla Pompa", "Taxi - Corsa Per L'aeroporto", "Rifiuti Solidi - Tariffa", "Bed And Breakfast"):
    for k, v in pr_out.items():
        if k.startswith(key):
            say("  %-60s %s %.2f -> %s %.2f (%+.1f%%)  medie annue %s" % (k[:60], v["primo"][0], v["primo"][1], v["ultimo"][0], v["ultimo"][1], v["var_pct"] or 0, v["medie_annue"]))
# confronto con indice
say("  confronto pane: prezzo medio MIMIT (euro/kg) 2021->2025 media annua vs indice ISTAT 'pane' Milano")
pn = [v for k, v in pr_out.items() if k.startswith("Pane Fresco")][0]
say("    prezzo: %s ; indice: %+.1f%% (2021->2025)" % (pn["medie_annue"], chg(voci["pane"], 2021, 2025)))

say("== AFFITTI e REDDITI")
ar = rd("affitto_vs_reddito.csv")
for r in ar:
    if int(r["anno"]) in (2006, 2010, 2015, 2019, 2021, 2022, 2023, 2024):
        say("  %s: affitto 60 m2 (OMI, stima) %s euro/mese; reddito complessivo mediano (interpolato) %s euro/mese; quota %s%%; ore di lavoro %s | reddito dipendente medio %s" % (r["anno"], r["affitto_civ_60m2_mese"], r["reddito_complessivo_mediano_mese_interpolato"], r["affitto_civ_su_reddito_mediano_pct"], r["ore_di_lavoro_per_affitto_civ_mediano"], r["reddito_dipendente_medio_mese"]))
out["affitto_reddito"] = {r["anno"]: {k: r[k] for k in ("affitto_civ_60m2_mese", "reddito_complessivo_mediano_mese_interpolato", "affitto_civ_su_reddito_mediano_pct", "ore_di_lavoro_per_affitto_civ_mediano")} for r in ar}
a = {int(r["anno"]): float(r["affitto_civ_eur_m2_mese"]) for r in ar}
om = {}
for r in csv.DictReader(open(os.path.join(os.path.dirname(C), "prezzi-case", "pulito", "prezzi_citta_mediana_zone.csv"), encoding="utf-8")):
    if r["tipologia"] == "Abitazioni civili": om[r["semestre"]] = float(r["loc_mediana_zone"])
say("  OMI affitto civili 2026-S1: %.2f euro/m2/mese = %.0f euro per 60 m2 (2024: %.2f; 2015: %.2f; 2006: %.2f) - reddito disponibile solo fino al 2024" % (om["2026-S1"], om["2026-S1"] * 60, a[2024], a[2015], a[2006]))
af = voci["affitti"]
say("  affitti ISTAT (canoni dei contratti in corso, Milano): 2015->2025 %+.1f%% ; 2020->2025 %+.1f%% ; OMI nuovi contratti 2015->2025 (media S1,S2): %+.1f%% ; 2020->2025: %+.1f%%" % (chg(af, 2015, 2025), chg(af, 2020, 2025), (statistics.mean([om["2025-S1"], om["2025-S2"]]) / statistics.mean([om["2015-S1"], om["2015-S2"]]) - 1) * 100, (statistics.mean([om["2025-S1"], om["2025-S2"]]) / statistics.mean([om["2020-S1"], om["2020-S2"]]) - 1) * 100))
out["affitti_istat_vs_omi"] = {"istat_2015_2025": round(chg(af, 2015, 2025), 1), "istat_2020_2025": round(chg(af, 2020, 2025), 1), "omi_2015_2025": round((statistics.mean([om["2025-S1"], om["2025-S2"]]) / statistics.mean([om["2015-S1"], om["2015-S2"]]) - 1) * 100, 1), "omi_2020_2025": round((statistics.mean([om["2025-S1"], om["2025-S2"]]) / statistics.mean([om["2020-S1"], om["2020-S2"]]) - 1) * 100, 1)}

fn = os.path.join(PU, "carburanti_milano_mensile.csv")
if os.path.exists(fn):
    say("== CARBURANTI Milano (archivio MIMIT, impianti del comune)")
    cm = rd("carburanti_milano_mensile.csv")
    fs = collections.defaultdict(dict)
    for r in cm: fs[(r["carburante"], r["self_service"])][r["mese"]] = float(r["prezzo_mediano_eur_litro_media_mensile"])
    yy = {}
    for k, s in fs.items():
        ann_ = collections.defaultdict(list)
        for m, v in s.items(): ann_[m[:4]].append(v)
        yy[k] = {a: round(statistics.mean(v), 3) for a, v in sorted(ann_.items()) if len(v) >= 11}
        pkk = max((v, m) for m, v in s.items())
        say("  %s self=%s: medie annue %s ; massimo mensile %.3f (%s) ; ultimo mese %s = %.3f" % (k[0], k[1], yy[k], pkk[0], pkk[1], max(s), s[max(s)]))
    out["carburanti_medie_annue"] = {"%s_self_%s" % k: v for k, v in yy.items()}
json.dump(out, open(os.path.join(PU, "riepilogo_costo_vita.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
open(os.path.join(PU, "riepilogo_costo_vita.txt"), "w", encoding="utf-8").write("\n".join(txt) + "\n")
