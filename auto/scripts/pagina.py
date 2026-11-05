"""Le auto dei milanesi - passo 2: dalle tabelle pulite (auto/pulito/) ai file della pagina (docs/auto/).
Scrive docs/auto/index.html e docs/auto/data/*. Rilanciabile.
Uso: python -I -X utf8 <...>/auto/scripts/pagina.py <cartella auto> <cartella milano-in-dati>   (percorsi assoluti)
"""
import csv
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
ROOT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.dirname(AUTO)
PUL = os.path.join(AUTO, "pulito")
OUT = os.path.join(ROOT, "docs", "auto")
DATA = os.path.join(OUT, "data")
os.makedirs(DATA, exist_ok=True)
CONTROLLI = []


def rd(nome):
    with open(os.path.join(PUL, nome), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def fl(x):
    return float(x) if x not in ("", None) else 0.0


def controllo(cond, msg):
    if not cond:
        CONTROLLI.append(msg)


CITTA = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze", "Genova", "Verona", "Bari", "Palermo"]
ANNI = list(range(2019, 2026))

# ------------------------------------------------------------------------------------ serie Milano
serie = rd("serie_milano_comune.csv")
S = [dict(a=int(r["anno"]), auto=int(r["autovetture"]), moto=int(r["motocicli"]), pop=int(r["popolazione"]),
          p1000=fl(r["per1000_auto"]), m1000=fl(r["per1000_moto"]), imm=int(r["immatricolazioni"]), rad=int(r["radiazioni"]))
     for r in serie]
s07, s19, s25 = S[0], [x for x in S if x["a"] == 2019][0], S[-1]
smin = min(S, key=lambda x: x["p1000"])
controllo(s07["a"] == 2007 and s25["a"] == 2025, "serie non 2007-2025")
controllo(s25["auto"] == 706764, "autovetture 2025 diverse da 706.764 (ds529)")

# ------------------------------------------------------------------------------------ confronto citta
conf = rd("confronto_citta.csv")
def val(anno, terr, tipo, campo):
    for r in conf:
        if int(r["anno"]) == anno and r["territorio"] == terr and r["tipo"] == tipo:
            return fl(r[campo])
    raise KeyError((anno, terr, tipo, campo))

citta = dict(anni=ANNI, nomi=CITTA, p1000={}, m1000={}, prov_p1000={}, italia=[], italia_m=[])
for c in CITTA:
    citta["p1000"][c] = [val(a, c, "comune", "per1000_auto") for a in ANNI]
    citta["m1000"][c] = [val(a, c, "comune", "per1000_moto") for a in ANNI]
    citta["prov_p1000"][c] = [val(a, c, "provincia", "per1000_auto") for a in ANNI]
citta["italia"] = [val(a, "Italia", "Italia", "per1000_auto") for a in ANNI]
citta["italia_m"] = [val(a, "Italia", "Italia", "per1000_moto") for a in ANNI]
citta["resto_prov_milano"] = [val(a, "Milano", "resto_provincia", "per1000_auto") for a in ANNI]
# coerenza: 2019 e 2025 di Milano con la serie del Comune (ds529)
controllo(abs(citta["p1000"]["Milano"][0] - s19["p1000"]) < 0.05 and abs(citta["p1000"]["Milano"][-1] - s25["p1000"]) < 0.05,
          "per 1000 di Milano diverso tra ACI e ds529")

uso = rd("bande_uso_soggetto.csv")
def usov(anno, prov, tab, voce):
    for r in uso:
        if int(r["anno"]) == anno and r["provincia"] == prov and r["tabella"] == tab and r["voce"] == voce:
            return fl(r["valore"])
    return None

euro_c = rd("euro_comuni.csv")
def euro_c_pct(anno, terr, campo):
    for r in euro_c:
        if int(r["anno"]) == anno and r["territorio"] == terr:
            return 100 * fl(r[campo]) / fl(r["totale"])
tab25 = []
for c in CITTA + ["Italia"]:
    if c == "Italia":
        pop_p = val(2025, "Italia", "Italia", "popolazione")
        auto_p = val(2025, "Italia", "Italia", "autovetture")
        row = dict(n="Italia", p1000_c=None, p1000_prov=auto_p / pop_p * 1000, auto_c=None, pop_c=None,
                   priv1000_prov=usov(2025, "Italia", "uso", "PRIVATO") / pop_p * 1000,
                   nlt_pct=100 * usov(2025, "Italia", "uso", "NOLEGGIO SENZA CONDUCENTE") / usov(2025, "Italia", "uso", "TOT"),
                   giur_pct=100 * usov(2025, "Italia", "soggetto", "PERSONA GIURIDICA") / usov(2025, "Italia", "soggetto", "TOT"),
                   euro6=None, euro01=None, m1000_c=val(2025, "Italia", "Italia", "per1000_moto"))
    else:
        pop_p = val(2025, c, "provincia", "popolazione")
        row = dict(n=c, auto_c=int(val(2025, c, "comune", "autovetture")), pop_c=int(val(2025, c, "comune", "popolazione")),
                   p1000_c=val(2025, c, "comune", "per1000_auto"), p1000_prov=val(2025, c, "provincia", "per1000_auto"),
                   priv1000_prov=usov(2025, c, "uso", "PRIVATO") / pop_p * 1000,
                   nlt_pct=100 * usov(2025, c, "uso", "NOLEGGIO SENZA CONDUCENTE") / usov(2025, c, "uso", "TOT"),
                   giur_pct=100 * usov(2025, c, "soggetto", "PERSONA GIURIDICA") / usov(2025, c, "soggetto", "TOT"),
                   euro6=euro_c_pct(2025, c, "euro6"), euro01=euro_c_pct(2025, c, "euro0_1"),
                   m1000_c=val(2025, c, "comune", "per1000_moto"))
    tab25.append(row)
citta["tab2025"] = tab25
rank = sorted([(r["p1000_c"], r["n"]) for r in tab25 if r["p1000_c"]])
citta["rank_basso"] = [n for _, n in rank]

# ------------------------------------------------------------------------------------ carburante
carb = rd("carburante_province.csv")
GR = ["benzina", "gasolio", "ibrido", "elettrico", "gpl", "metano", "altro"]
carbj = dict(anni=ANNI, gruppi=GR, pct={}, n={})
for prov in ("Milano", "Roma", "Torino", "Italia"):
    carbj["pct"][prov] = {g: [] for g in GR}
    carbj["n"][prov] = {g: [] for g in GR}
    carbj["n"][prov]["totale"] = []
    for a in ANNI:
        r = [x for x in carb if int(x["anno"]) == a and x["provincia"] == prov][0]
        t = fl(r["totale"])
        for g in GR:
            carbj["pct"][prov][g].append(100 * fl(r[g]) / t)
            carbj["n"][prov][g].append(int(fl(r[g])))
        carbj["n"][prov]["totale"].append(int(t))
        controllo(abs(sum(fl(r[g]) for g in GR) - t) < 1, "carburante: somma gruppi diversa dal totale %s %d" % (prov, a))
quota_citta = s25["auto"] / carbj["n"]["Milano"]["totale"][-1]

# ------------------------------------------------------------------------------------ Euro (Milano comune)
ev = rd("euro_milano_comune_2007_2025.csv")
CL = ["euro0", "euro1", "euro2", "euro3", "euro4", "euro5", "euro6", "altro"]
eurj = dict(anni=[], classi=CL, pct={c: [] for c in CL}, n={c: [] for c in CL}, tot=[], fonte=[])
for r in ev:
    t = fl(r["totale"])
    eurj["anni"].append(int(r["anno"]))
    eurj["tot"].append(int(t))
    eurj["fonte"].append(r["fonte"])
    altro = fl(r["non_contemplato"]) + fl(r["non_definito"])
    for c in CL[:-1]:
        eurj["pct"][c].append(100 * fl(r[c]) / t)
        eurj["n"][c].append(int(fl(r[c])))
    eurj["pct"]["altro"].append(100 * altro / t)
    eurj["n"]["altro"].append(int(altro))
    controllo(abs(sum(fl(r[c]) for c in CL[:-1]) + altro - t) < 1, "Euro: somma classi diversa dal totale %s" % r["anno"])
i07, i25 = 0, len(eurj["anni"]) - 1
eurj["euro0_3_pct_2007"] = sum(eurj["pct"][c][i07] for c in CL[:4])
eurj["euro0_3_pct_2025"] = sum(eurj["pct"][c][i25] for c in CL[:4])
i18 = eurj["anni"].index(2018)
eurj["euro0_3_pct_2018"] = sum(eurj["pct"][c][i18] for c in CL[:4])

# Area B: auto vietate dal primo giorno nella provincia (benzina Euro 0, gasolio Euro 0-3)
dm = rd("euro_milano_provincia_per_carburante.csv")
ab = dict(anni=ANNI, gasolio03=[], benzina0=[], gasolio_tot=[], benzina_tot=[], tot_vietate=[])
for a in ANNI:
    g = [x for x in dm if int(x["anno"]) == a and x["territorio"] == "Milano (gasolio)"][0]
    b = [x for x in dm if int(x["anno"]) == a and x["territorio"] == "Milano (benzina)"][0]
    g03 = int(fl(g["euro0"]) + fl(g["euro1"]) + fl(g["euro2"]) + fl(g["euro3"]))
    b0 = int(fl(b["euro0"]))
    ab["gasolio03"].append(g03)
    ab["benzina0"].append(b0)
    ab["gasolio_tot"].append(int(fl(g["totale"])))
    ab["benzina_tot"].append(int(fl(b["totale"])))
    ab["tot_vietate"].append(g03 + b0)
ab["inizio"] = "2019-02-25"

# ------------------------------------------------------------------------------------ eta' e potenza
ep = rd("eta_potenza_province.csv")
epj = {}
for prov in ("Milano", "Roma", "Torino", "Italia"):
    epj[prov] = {}
    for a in (2019, 2025):
        r = [x for x in ep if int(x["anno"]) == a and x["provincia"] == prov][0]
        epj[prov][str(a)] = {k: (fl(v) if k not in ("banda_vecchie", "banda_nuove", "provincia") else v) for k, v in r.items()}
epj["serie_milano"] = {k: [] for k in ("vecchie16_pct", "ultimi2_pct", "kw_oltre100_pct", "kw_oltre130_pct", "cil_oltre2000_pct")}
epj["serie_italia"] = {k: [] for k in epj["serie_milano"]}
for a in ANNI:
    for prov, key in (("Milano", "serie_milano"), ("Italia", "serie_italia")):
        r = [x for x in ep if int(x["anno"]) == a and x["provincia"] == prov][0]
        for k in epj[key]:
            epj[key][k].append(fl(r[k]))

# ------------------------------------------------------------------------------------ moto
mt = rd("euro_moto_comuni.csv")
motoj = {}
for a in (2019, 2025):
    r = [x for x in mt if int(x["anno"]) == a and x["territorio"] == "Milano"][0]
    t = fl(r["totale"])
    motoj[str(a)] = dict(tot=int(t), euro01=100 * fl(r["euro0_1"]) / t, euro2=100 * fl(r["euro2"]) / t, euro3=100 * fl(r["euro3"]) / t,
                         euro4=100 * fl(r["euro4"]) / t, euro56=100 * fl(r["euro5_6"]) / t)

# ------------------------------------------------------------------------------------ 2017 (Motorizzazione)
with open(os.path.join(PUL, "milano_2017_motorizzazione.json"), encoding="utf-8") as f:
    m17 = json.load(f)
na = m17["auto"]
snap = dict(
    auto=int(na), moto=int(m17["moto"]),
    benzina=100 * m17["f_benzina"] / na, gasolio=100 * m17["f_gasolio"] / na, gpl=100 * m17["f_gpl"] / na,
    metano=100 * m17["f_metano"] / na, ibrido=100 * m17["f_ibrido"] / na, elettrico=100 * m17["f_elettrico"] / na,
    euro0_3=100 * (m17["euro_0"] + m17["euro_1"] + m17["euro_2"] + m17["euro_3"]) / na,
    euro6=100 * m17["euro_6"] / na,
    kw_oltre100=100 * m17["kw_oltre100"] / m17["kw_valido"], kw_oltre130=100 * m17["kw_oltre130"] / m17["kw_valido"],
    kw_fino70=100 * m17["kw_fino70"] / m17["kw_valido"],
    massa_oltre2000=100 * m17["massa_oltre2000"] / m17["massa_valida"],
    eta_media=m17["eta_media"], co2_media=m17["co2_media"],
    locazione=100 * m17["uso_locazione"] / na,
    senza_eta=100 * m17["intest_giuridica"] / na,
    donne=100 * m17["intest_donne"] / m17["intest_persona"], over65=100 * m17["intest_65"] / m17["intest_persona"],
    under35=100 * m17["intest_under35"] / m17["intest_persona"],
    fino2001=100 * m17["imm_fino2001"] / m17["anno_valido"],
    ds1094_2017=700723, istantanea=m17["istantanea"])
controllo(abs(sum(m17["f_" + k] for k in ("benzina", "gasolio", "gpl", "metano", "ibrido", "elettrico", "altro")) - na) < 1, "2017: carburanti non sommano")

# ------------------------------------------------------------------------------------ Area C
ac = rd("areac_composizione_pct.csv")
acj = dict(anni=[], diesel=[], benzina=[], ibrido=[], elettrico=[], moto=[], nc=[])
for r in ac:
    acj["anni"].append(int(r["y"]))
    acj["diesel"].append(fl(r["alim_diesel"]))
    acj["benzina"].append(fl(r["alim_benzina"]))
    acj["ibrido"].append(fl(r["alim_ibrido"]))
    acj["elettrico"].append(fl(r["alim_elettrico"]))
    acj["moto"].append(fl(r["tipo_moto"]))
    acj["nc"].append(fl(r["alim_nc"]))
# parco di Milano (provincia) negli stessi anni 2019-2024, per confronto
acj["parco"] = {k: [] for k in ("anni", "diesel", "benzina", "ibrido", "elettrico")}
for a in ANNI[:-1]:
    acj["parco"]["anni"].append(a)
    i = ANNI.index(a)
    for k in ("diesel", "benzina", "ibrido", "elettrico"):
        kk = {"diesel": "gasolio"}.get(k, k)
        acj["parco"][k].append(carbj["pct"]["Milano"][kk][i])

# ------------------------------------------------------------------------------------ riepilogo
immigr = dict(
    imm_2007=s07["imm"], imm_2025=s25["imm"], rad_2022=[x for x in S if x["a"] == 2022][0]["rad"], rad_2024=[x for x in S if x["a"] == 2024][0]["rad"],
    rad_2025=s25["rad"])
R = dict(
    meta=dict(creato="2026-11-02", anni_aci=ANNI),
    serie=S, minimo_p1000=dict(a=smin["a"], v=smin["p1000"]),
    citta=citta, carburante=carbj, quota_citta_su_provincia=quota_citta,
    euro=eurj, areab=ab, eta_potenza=epj, moto=motoj, snap2017=snap, areac=acj, ritmi=immigr,
    origine=dict(
        serie="Autovetture e motocicli iscritti al PRA con proprietario residente a Milano: Comune di Milano, ds529 (CC-BY), 2007-2025. Residenti: ISTAT, bilancio demografico ricostruito (31/12, 2007-2018) e POSAS (1 gennaio dell'anno dopo, 2019-2025), CC BY 4.0.",
        citta="ACI, Autoritratto 2019-2025, Parco veicolare per categoria e comune/provincia (CC BY 4.0, aci.gov.it/open-data). Residenti: ISTAT POSAS al 1 gennaio dell'anno dopo.",
        carburante="ACI Autoritratto, Circolante Copert, autovetture per provincia, alimentazione e classe Euro (solo provincia).",
        euro="Comune di Milano ds1081 (2007-2018) e ACI Autoritratto, autovetture per comune ed Euro (2019-2025). Controllato con ds529, ds530.",
        areab="ACI Autoritratto, autovetture della provincia di Milano per alimentazione e classe Euro; regole all'avvio di Area B: Confcommercio Milano (2019).",
        eta_potenza="ACI Autoritratto, autovetture per provincia e anno di immatricolazione, kW e cilindrata.",
        snap2017="Comune di Milano ds545 (Motorizzazione, parco circolante dei residenti, fine 2017): solo conteggi aggregati.",
        areac="Pagina Area C: passaggi dei giorni feriali normali, % su tutti i passaggi (anche moto, furgoni, bus, non classificati); Comune di Milano / AMAT (CC-BY).",
    ))
json.dump(R, open(os.path.join(DATA, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# file da scaricare (copie delle tabelle pulite)
for nome in ("serie_milano_comune.csv", "confronto_citta.csv", "carburante_province.csv", "euro_milano_comune_2007_2025.csv", "euro_comuni.csv",
             "euro_province.csv", "euro_milano_provincia_per_carburante.csv", "euro_moto_comuni.csv", "eta_potenza_province.csv",
             "bande_uso_soggetto.csv", "areac_composizione_pct.csv"):
    shutil.copy(os.path.join(PUL, nome), os.path.join(DATA, nome))
shutil.copy(os.path.join(PUL, "milano_2017_motorizzazione.json"), os.path.join(DATA, "milano_2017_aggregati.json"))

# html
with open(os.path.join(HERE, "pagina_template.html"), encoding="utf-8") as f:
    html = f.read()
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)

print("scritto", OUT)
print("segnaposto numeri: Milano 2007 %.1f, 2019 %.1f, 2025 %.1f per 1000; minimo %s" % (s07["p1000"], s19["p1000"], s25["p1000"], smin["a"]))
print("citta piu basse nel 2025:", citta["rank_basso"][:3])
print("CONTROLLI:", len(CONTROLLI))
for c in CONTROLLI:
    print(" -", c)
