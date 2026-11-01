"""Beni confiscati a Milano - riepiloghi. Uso: python -I -X utf8 analisi.py <A = .../beni-confiscati>
Legge A/pulito e A/raw, scrive riepilogo.json e le tabelle riepilogative in A/pulito. Nessun nome di persona o azienda."""
import sys, os, csv, json, re, collections, statistics, unicodedata

A = sys.argv[1]
RAW, OUT = os.path.join(A, "raw"), os.path.join(A, "pulito")
Cn = collections.Counter


def rd(path, delim=",", enc="utf8"):
    return list(csv.DictReader(open(path, encoding=enc, errors="replace", newline=""), delimiter=delim))


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(name, len(rows))


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").replace("\xa0", " "))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().replace("'", " ").replace("-", " ").strip()


imm = rd(os.path.join(OUT, "immobili_anbsc_milano.csv"))
com = rd(os.path.join(OUT, "comune_ds147_milano.csv"))
azm = rd(os.path.join(OUT, "aziende_anbsc_milano.csv"))
azu = rd(os.path.join(OUT, "aziende_unioncamere_sede_milano.csv"))
tot = rd(os.path.join(OUT, "tutti_i_beni_per_comune.csv"))
R = {}

# ------------------------------------------------------------------ 1. immobili Milano per stato e tipo
R["immobili_milano_totale"] = len(imm)
R["immobili_milano_per_stato"] = Cn(r["stato"] for r in imm)
R["immobili_milano_per_dettaglio_stato"] = Cn((r["stato"], r["dettaglio_stato"].split(" - quota")[0]) for r in imm).most_common()
R["immobili_milano_per_tipo"] = Cn(r["tipo"] for r in imm)
R["immobili_milano_tipo_per_stato"] = {s: Cn(r["tipo"] for r in imm if r["stato"] == s) for s in ("in gestione", "destinato", "uscito")}
dest = [r for r in imm if r["fonte"] == "ANBSC destinati"]
R["destinati_per_destinatario_tipo"] = Cn(r["destinatario_tipo"] for r in dest)
R["destinati_per_finalita"] = Cn(r["finalita"] or "(vuoto)" for r in dest)
R["destinati_al_comune_per_finalita"] = Cn(r["finalita"] or "(vuoto)" for r in dest if r["destinatario_tipo"] == "Comune")
R["gestione_per_dettaglio_provvedimento"] = Cn(r["dettaglio_stato"].split(" - quota")[0] for r in imm if r["stato"] == "in gestione")
R["gestione_quota_parziale"] = sum(1 for r in imm if r["stato"] == "in gestione" and "quota" in r["dettaglio_stato"] and "100%" not in r["dettaglio_stato"])
# anno di destinazione (decreto)
anni = Cn(int(r["anno_destinazione"]) for r in dest if r["anno_destinazione"])
R["destinati_per_anno_decreto"] = dict(sorted(anni.items()))
anni_c = Cn(int(r["anno_destinazione"]) for r in dest if r["anno_destinazione"] and r["destinatario_tipo"] == "Comune")
R["destinati_al_comune_per_anno_decreto"] = dict(sorted(anni_c.items()))
R["destinati_anno_procedura"] = dict(sorted(Cn(int(r["anno_procedura"]) for r in dest if r["anno_procedura"]).items()))
ap = [int(r["anno_procedura"]) for r in dest if r["anno_procedura"]]
R["anno_procedura_mediano_destinati"] = statistics.median(ap) if ap else None
lag = [int(r["anno_destinazione"]) - int(r["anno_procedura"]) for r in dest if r["anno_destinazione"] and r["anno_procedura"]]
R["anni_dal_procedimento_al_decreto_mediana"] = statistics.median(lag)
R["anni_dal_procedimento_al_decreto_dist"] = Cn(l for l in lag)
# edifici (indirizzi distinti) nei destinati geocodificati
bld = Cn(r["via_abbinata"] + "|" + re.sub(r"\D", "", r["indirizzo"].split(",")[0]) for r in dest if r["via_abbinata"])
R["destinati_indirizzi_distinti"] = len(bld)
R["destinati_unita_nei_5_indirizzi_piu_grandi"] = bld.most_common(5)
R["destinati_posizione_qualita"] = Cn(r["qualita_posizione"] for r in dest)

# ------------------------------------------------------------------ 2. elenco del Comune (ds147)
R["ds147_unita"] = len(com)
R["ds147_per_tipo"] = Cn(r["tipo"] for r in com)
R["ds147_per_stato_uso"] = Cn(r["stato_uso"] for r in com)
R["ds147_per_finalita"] = Cn(r["finalita"] for r in com)
R["ds147_per_ente_tipo"] = Cn(r["ente_tipo"] or "(nessuno)" for r in com)
R["ds147_per_municipio"] = dict(sorted(Cn(int(r["municipio"]) for r in com).items()))
R["ds147_indirizzi_distinti"] = len({(r["via_abbinata"], re.sub(r"\D", "", r["indirizzo"].split(",")[0])) for r in com})
R["ds147_stato_x_tipo"] = {s: Cn(r["tipo"] for r in com if r["stato_uso"] == s) for s in sorted({r["stato_uso"] for r in com})}
sociale = [r for r in com if r["stato_uso"] in ("assegnato a terzi", "gestione diretta del Comune")]
R["ds147_riusati_per_scopi_sociali_o_istituzionali"] = len(sociale)
R["ds147_in_attesa_o_non_assegnati"] = len(com) - len(sociale)
R["ds147_nuova_acquisizione_2026"] = sum(1 for r in com if r["nota_comune_breve"])
R["ds147_contratti_scaduti_giugno_2026"] = Cn(r["contratto_scaduto_a_giugno_2026"] for r in com if r["stato_uso"] == "assegnato a terzi")
# attesa: anni dal decreto di destinazione (ANBSC) per chi non e' assegnato
att = [int(r["anni_da_destinazione"]) for r in com if r["stato_uso"] in ("in attesa di assegnazione", "non assegnato: lavori o problemi", "non assegnato: nessuna informazione") and r["anni_da_destinazione"] != ""]
R["ds147_attesa_anni_da_decreto_non_assegnati"] = {"n": len(att), "mediana": statistics.median(att) if att else None, "media": round(statistics.mean(att), 1) if att else None, "max": max(att) if att else None, "min": min(att) if att else None, "oltre_10_anni": sum(1 for a in att if a >= 10), "oltre_5_anni": sum(1 for a in att if a >= 5)}
R["ds147_non_assegnati_senza_anno_decreto"] = sum(1 for r in com if r["stato_uso"] in ("in attesa di assegnazione", "non assegnato: lavori o problemi", "non assegnato: nessuna informazione") and r["anni_da_destinazione"] == "")
# tempo decreto -> inizio contratto, per le assegnate
l2 = [int(r["anni_destinazione_contratto"]) for r in com if r["stato_uso"] == "assegnato a terzi" and r["anni_destinazione_contratto"] != "" and int(r["anni_destinazione_contratto"]) >= 0]
neg = sum(1 for r in com if r["stato_uso"] == "assegnato a terzi" and r["anni_destinazione_contratto"] != "" and int(r["anni_destinazione_contratto"]) < 0)
R["ds147_anni_da_decreto_a_contratto"] = {"n": len(l2), "mediana": statistics.median(l2) if l2 else None, "media": round(statistics.mean(l2), 1) if l2 else None, "max": max(l2) if l2 else None, "contratto_prima_del_decreto_(dati_incoerenti)": neg, "oltre_5_anni": sum(1 for a in l2 if a >= 5)}
R["ds147_anno_inizio_contratto"] = dict(sorted(Cn(int(r["anno_inizio_contratto"]) for r in com if r["anno_inizio_contratto"] != "").items()))
R["ds147_anni_da_decreto_tutte"] = dict(sorted(Cn(int(r["anni_da_destinazione"]) for r in com if r["anni_da_destinazione"] != "").items()))
R["ds147_posizione_qualita"] = Cn(r["qualita_posizione"] for r in com)

# ------------------------------------------------------------------ 3. per NIL
nil = collections.defaultdict(lambda: {"ds147_unita": 0, "ds147_in_attesa": 0, "ds147_assegnati": 0, "anbsc_destinati": 0, "anbsc_destinati_comune": 0})
for r in com:
    n = r["nil"] or "(senza NIL)"
    nil[n]["ds147_unita"] += 1
    if r["stato_uso"] in ("assegnato a terzi", "gestione diretta del Comune"):
        nil[n]["ds147_assegnati"] += 1
    else:
        nil[n]["ds147_in_attesa"] += 1
for r in dest:
    n = r["nil"] or "(senza NIL)"
    nil[n]["anbsc_destinati"] += 1
    if r["destinatario_tipo"] == "Comune":
        nil[n]["anbsc_destinati_comune"] += 1
idn = {r["nil"]: r["id_nil"] for r in com + dest if r["nil"]}
rows = [dict(nil=k, id_nil=idn.get(k, ""), **v) for k, v in sorted(nil.items(), key=lambda kv: -kv[1]["ds147_unita"])]
wr("per_nil.csv", rows, ["nil", "id_nil", "ds147_unita", "ds147_assegnati", "ds147_in_attesa", "anbsc_destinati", "anbsc_destinati_comune"])
R["nil_con_beni_ds147"] = sum(1 for v in nil.values() if v["ds147_unita"])
R["nil_top10_ds147"] = [(k, v["ds147_unita"]) for k, v in sorted(nil.items(), key=lambda kv: -kv[1]["ds147_unita"])[:10]]
top3 = sum(v for _, v in R["nil_top10_ds147"][:3])
R["nil_top3_quota_ds147"] = round(top3 / len(com), 3)
# edifici piu' grandi ds147
bds = Cn((r["via_abbinata"], re.sub(r"\D", "", r["indirizzo"].split(",")[0])) for r in com)
R["ds147_edifici_top5"] = bds.most_common(5)
R["ds147_edifici_con_5_o_piu_unita"] = sum(1 for v in bds.values() if v >= 5)
R["ds147_unita_in_edifici_con_5_o_piu"] = sum(v for v in bds.values() if v >= 5)

# ------------------------------------------------------------------ 4. aziende
R["aziende_milano_totale_anbsc"] = len(azm)
R["aziende_milano_per_stato"] = Cn(r["stato"] for r in azm)
R["aziende_milano_gestione_per_settore"] = Cn(r["settore"] or "(non indicato)" for r in azm if r["stato"] == "in gestione").most_common()
R["aziende_milano_uscite_per_settore"] = Cn(r["settore"] or "(non indicato)" for r in azm if r["stato"] == "uscita").most_common()
R["aziende_milano_tutte_per_settore"] = Cn(r["settore"] or "(non indicato)" for r in azm).most_common()
R["aziende_milano_uscite_per_esito"] = Cn(r["dettaglio"] for r in azm if r["stato"] == "uscita")
R["aziende_milano_forma_giuridica"] = Cn(r["forma_giuridica"] for r in azm).most_common()
R["aziende_milano_uscite_per_anno"] = dict(sorted(Cn(int(r["anno_destinazione"]) for r in azm if r["anno_destinazione"]).items()))
R["aziende_milano_gestione_provvedimento"] = Cn(r["dettaglio"] for r in azm if r["stato"] == "in gestione")
R["aziende_unioncamere_sede_milano_totale"] = len(azu)
R["aziende_unioncamere_stato_attivita"] = Cn(r["stato_attivita"] for r in azu)
R["aziende_unioncamere_stato_amministrativo"] = Cn(r["stato_amministrativo"] for r in azu)
R["aziende_unioncamere_ateco_sezione"] = Cn(r["ateco_sezione"] + " " + r["ateco_sezione_descrizione"] for r in azu).most_common()
R["aziende_unioncamere_ateco_attivita_top15"] = Cn(r["ateco_attivita"] for r in azu).most_common(15)
R["aziende_unioncamere_natura_giuridica"] = Cn(r["natura_giuridica"] for r in azu)
R["aziende_unioncamere_attive_in_gestione"] = sum(1 for r in azu if r["stato_attivita"] == "ATTIVA" and r["stato_amministrativo"] == "IN GESTIONE")

# ------------------------------------------------------------------ 5. confronti tra comuni
pop = {}
for r in csv.reader(open(os.path.join(RAW, "istat_pop", "estratto", "POSAS_2025_it_Comuni.csv"), encoding="utf-8-sig"), delimiter=";"):
    if len(r) > 3 and r[2] == "999":
        pop.setdefault(fold(r[1]), []).append(int(r[-1]))
    elif len(r) > 3 and r[2] == "Età":
        pass
cmn = collections.defaultdict(lambda: Cn())
for r in tot:
    key = (r["comune"], r["provincia"])
    cmn[key]["imm_" + r["stato"]] += 1 if r["genere"] == "immobili" else 0
    cmn[key]["az_" + r["stato"]] += 1 if r["genere"] == "aziende" else 0
    cmn[key]["tot"] += 1
    cmn[key]["imm_tot"] += 1 if r["genere"] == "immobili" else 0
    cmn[key]["az_tot"] += 1 if r["genere"] == "aziende" else 0
    cmn[key]["terreni"] += 1 if r["tipo"] == "terreno" else 0
    cmn[key]["abitazioni"] += 1 if r["tipo"] == "abitazione" else 0
rows = []
for (c, p), v in cmn.items():
    pp = pop.get(fold(c), [])
    pop_c = pp[0] if len(pp) == 1 else None
    rows.append(dict(comune=c, provincia=p, popolazione_2025=pop_c or "", totale=v["tot"], immobili=v["imm_tot"], aziende=v["az_tot"],
                     immobili_in_gestione=v["imm_in gestione"], immobili_destinati=v["imm_destinato"], immobili_usciti=v["imm_uscito"],
                     aziende_in_gestione=v["az_in gestione"], aziende_uscite=v["az_uscita"],
                     per_100mila_abitanti=round(v["tot"] / pop_c * 100000, 1) if pop_c else ""))
rows.sort(key=lambda r: -r["totale"])
wr("confronto_comuni.csv", rows, ["comune", "provincia", "popolazione_2025", "totale", "immobili", "aziende", "immobili_in_gestione", "immobili_destinati", "immobili_usciti", "aziende_in_gestione", "aziende_uscite", "per_100mila_abitanti"])
mi = next(r for r in rows if r["comune"] == "Milano")
R["milano_riga_confronto"] = mi
R["milano_posizione_per_totale"] = [r["comune"] for r in rows].index("Milano") + 1
R["n_comuni_con_beni"] = len(rows)
R["italia_totale_beni"] = sum(r["totale"] for r in rows)
R["italia_immobili_aziende"] = (sum(r["immobili"] for r in rows), sum(r["aziende"] for r in rows))
R["milano_quota_italia"] = round(mi["totale"] / R["italia_totale_beni"], 4)
R["top15_comuni_per_totale"] = [(r["comune"], r["totale"], r["per_100mila_abitanti"]) for r in rows[:15]]
grandi = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Bari", "Catania", "Venezia", "Verona", "Messina", "Padova", "Trieste", "Brescia", "Reggio Calabria", "Bergamo", "Monza"]
R["grandi_citta"] = [{k: r[k] for k in ("comune", "popolazione_2025", "totale", "immobili", "aziende", "immobili_destinati", "immobili_in_gestione", "aziende_in_gestione", "per_100mila_abitanti")} for g in grandi for r in rows if r["comune"] == g and (g != "Reggio Calabria" or True)]
# per provincia
prov = collections.defaultdict(Cn)
for r in tot:
    prov[(r["regione"], r["provincia"])]["tot"] += 1
    prov[(r["regione"], r["provincia"])][r["genere"] + "_" + r["stato"]] += 1
prow = [dict(regione=k[0], provincia=k[1], totale=v["tot"], immobili_in_gestione=v["immobili_in gestione"], immobili_destinati=v["immobili_destinato"], immobili_usciti=v["immobili_uscito"], aziende_in_gestione=v["aziende_in gestione"], aziende_uscite=v["aziende_uscita"]) for k, v in prov.items()]
prow.sort(key=lambda r: -r["totale"])
wr("confronto_province.csv", prow, ["regione", "provincia", "totale", "immobili_in_gestione", "immobili_destinati", "immobili_usciti", "aziende_in_gestione", "aziende_uscite"])
pm = next(r for r in prow if r["provincia"] == "Milano" and r["regione"] == "Lombardia")
R["provincia_milano"] = pm
R["provincia_milano_posizione"] = [(r["regione"], r["provincia"]) for r in prow].index(("Lombardia", "Milano")) + 1
R["province_top10"] = [(r["provincia"], r["totale"]) for r in prow[:10]]
R["lombardia_per_provincia"] = [(r["provincia"], r["totale"]) for r in prow if r["regione"] == "Lombardia"]
R["lombardia_totale"] = sum(r["totale"] for r in prow if r["regione"] == "Lombardia")
R["comuni_provincia_milano_top12"] = [(r["comune"], r["totale"], r["per_100mila_abitanti"]) for r in rows if r["provincia"] == "Milano"][:12]
R["milano_comune_quota_provincia"] = round(mi["totale"] / pm["totale"], 3)
# per regione
reg = Cn()
for r in tot:
    reg[r["regione"]] += 1
R["regioni"] = reg.most_common()
# dove vanno i beni: mix nazionale e confronto con Milano
nat_dest = Cn(r["dettaglio"] for r in tot if r["genere"] == "immobili" and r["stato"] != "in gestione")
R["nazionale_immobili_esiti"] = nat_dest.most_common()
nat_az = Cn(r["dettaglio"] for r in tot if r["genere"] == "aziende" and r["stato"] == "uscita")
R["nazionale_aziende_uscite_esiti"] = nat_az.most_common()
tot_az_ex = sum(nat_az.values())
R["nazionale_aziende_uscite_quota_liquidazione"] = round(nat_az.get("Liquidazione", 0) / tot_az_ex, 3)
R["nazionale_aziende_uscite_totale"] = tot_az_ex
# quote: in gestione sul totale (Milano vs Italia vs grandi)
def quota_gest(sel):
    g = sum(1 for r in tot if sel(r) and r["genere"] == "immobili" and r["stato"] == "in gestione")
    t = sum(1 for r in tot if sel(r) and r["genere"] == "immobili")
    return g, t, round(g / t, 3) if t else None
R["immobili_quota_in_gestione"] = {"Milano": quota_gest(lambda r: r["comune"] == "Milano"), "Italia": quota_gest(lambda r: True), "provincia Milano": quota_gest(lambda r: r["provincia"] == "Milano" and r["regione"] == "Lombardia"), "Lombardia": quota_gest(lambda r: r["regione"] == "Lombardia")}
for g in ("Roma", "Napoli", "Torino", "Palermo"):
    R["immobili_quota_in_gestione"][g] = quota_gest(lambda r, g=g: r["comune"] == g)
# tipi: Milano vs Italia
R["tipo_immobili_Italia"] = Cn(r["tipo"] for r in tot if r["genere"] == "immobili")
R["tipo_immobili_Milano"] = Cn(r["tipo"] for r in tot if r["genere"] == "immobili" and r["comune"] == "Milano")

# ------------------------------------------------------------------ 6. serie nel tempo: 2014, 2024, 2026
W = os.path.join(RAW, "confiscatibene_wayback")
ser = {}
m14 = [r for r in rd(os.path.join(W, "immobili_anbsc_2014-09-20.csv")) if r["Comune"] == "Milano"]
ser["2014-09 (confiscatibene, copia ANBSC)"] = {"immobili_stati": Cn(r["Stato"] for r in m14), "immobili_totale": len(m14)}
a14 = [r for r in rd(os.path.join(W, "aziende_anbsc_2014-09-20.csv")) if r["Comune"] == "Milano"]
ser["2014-09 (confiscatibene, copia ANBSC)"]["aziende_stati"] = Cn(r["Stato"] for r in a14)
ser["2014-09 (confiscatibene, copia ANBSC)"]["aziende_totale"] = len(a14)
b24 = [r for r in rd(os.path.join(W, "latest_bid_2024-08-06.csv")) if r["comune"] == "Milano"]
g24 = [r for r in rd(os.path.join(W, "latest_big_2024-08-07.csv")) if r["nome_comune"] == "Milano"]
ad24 = [r for r in rd(os.path.join(W, "latest_ad_2024-08-06.csv")) if r["comune"] == "Milano"]
ag24 = [r for r in rd(os.path.join(W, "latest_aig_2024-08-08.csv")) if r["nome_comune"] == "Milano"]
ser["2024-08 (confiscatibene, copia ANBSC)"] = {"immobili_destinati": len(b24), "immobili_in_gestione": len(g24), "aziende_destinate": len(ad24), "aziende_in_gestione": len(ag24)}
ser["2026-11 (ANBSC, scaricato 1/11/2026)"] = {"immobili_destinati": len(dest), "immobili_in_gestione": sum(1 for r in imm if r["stato"] == "in gestione"), "aziende_destinate": sum(1 for r in azm if r["stato"] == "uscita"), "aziende_in_gestione": sum(1 for r in azm if r["stato"] == "in gestione")}
R["serie_milano"] = ser
# movimenti 2024 -> 2026
ids26_dest = {r["id"] for r in dest}
ids24_dest = {r["m_bene"] for r in b24}
sb24 = {r["s_bene"] for r in g24}
sb26g = {r["id"] for r in imm if r["stato"] == "in gestione"}
# gestione 2026 s_bene, destinati 2026 s_bene: serve il file nazionale
_, = (None,)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anbsc_parse import parse_destinati
_, di, _b = parse_destinati(os.path.join(RAW, "anbsc_openregio", "nazionale_destinati_immobili.csv"))
sb26d = {r["s_bene"] for r in di if r["comune"] == "Milano" and r["s_bene"]}
all26_d_nat = {r["s_bene"] for r in di if r["s_bene"]}
R["movimenti_immobili_2024_2026"] = {
    "gestione_2024": len(sb24), "di_cui_ancora_in_gestione_2026": len(sb24 & sb26g), "di_cui_ora_tra_i_destinati_2026": len(sb24 & all26_d_nat), "di_cui_non_piu_in_nessun_elenco": len(sb24 - sb26g - all26_d_nat),
    "destinati_2024": len(ids24_dest), "di_cui_ancora_destinati_2026": len(ids24_dest & ids26_dest), "destinati_2024_non_piu_nell_elenco": len(ids24_dest - ids26_dest),
    "destinati_2026_nuovi_rispetto_2024": len(ids26_dest - ids24_dest),
    "nuovi_2026_per_anno_decreto": dict(sorted(Cn(r["anno_destinazione"] for r in dest if r["id"] not in ids24_dest).items())),
}
# 2024 -> aziende
sa24g = {r["s_bene"] for r in ag24}
R["movimenti_aziende_2024_2026"] = {"in_gestione_2024": len(sa24g)}
ga26 = rd(os.path.join(RAW, "anbsc_openregio", "nazionale_gestione_aziende.csv"))
sb26a = {r["s_bene"] for r in ga26 if r["nome_comune"] == "Milano"}
R["movimenti_aziende_2024_2026"]["ancora_in_gestione_2026"] = len(sa24g & sb26a)
R["movimenti_aziende_2024_2026"]["nuove_in_gestione_2026"] = len(sb26a - sa24g)

# ------------------------------------------------------------------ 7. coerenza fra le fonti
rl = rd(os.path.join(RAW, "regione_lombardia", "krpf-yure.csv"))
rlm = [r for r in rl if r["comune"].lower() == "milano"]
R["regione_lombardia_milano"] = {"righe": len(rlm), "presenti_in_anbsc_2026": len({r["id_bene"] for r in rlm} & ids26_dest), "data_caricamento": dict(Cn(r["data_caricamento"] for r in rlm))}
dest_com = [r for r in dest if r["destinatario_tipo"] == "Comune"]
R["confronto_comune_vs_anbsc"] = {"anbsc_destinati_al_comune": len(dest_com), "ds147_unita": len(com), "ds147_con_anno_decreto_abbinato": sum(1 for r in com if r["anno_destinazione_anbsc"] != "")}

# ------------------------------------------------------------------ scrittura
def plain(o):
    if isinstance(o, dict):
        return {str(k): plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [plain(x) for x in o]
    return o
json.dump(plain(R), open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("fatto: riepilogo.json con", len(R), "voci")
