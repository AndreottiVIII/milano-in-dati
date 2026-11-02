"""Pulizia e controlli dei dati del Ministero della Giustizia per la pagina "Il tribunale di Milano".

Uso (percorso assoluto, si puo' rilanciare):
  python -I -X utf8 build.py <tribunale_dir>

Legge raw/ministero/*.xlsx (scaricati con scarica.py) e scrive pulito/:
  uffici_dt.csv            civile e penale per ufficio e anno: definiti, pendenti, disposition time ricalcolato, arretrato (>3 anni), obiettivi PNRR
  flussi_civili.csv        iscritti, definiti, pendenti per ufficio e anno (aggregato SICID del monitoraggio distrettuale), indice di ricambio,
                           e la quota di "protezione internazionale"
  flussi_penali.csv        idem per il penale (tribunali: GIP/GUP + dibattimento + assise; corti di appello: ordinaria, assise, minorenni)
  durata_effettiva.csv     durata media effettiva dei procedimenti civili definiti (registro SICID), 2014-2025
  materie_milano.csv       tribunale di Milano: iscritti, definiti, pendenti per materia (SICID), 2014-2025
  verifiche.csv            ogni controllo incrociato (calcolato, atteso, esito)
Nessun numero e' scritto a mano: gli "attesi" dei controlli sono letti dagli altri file del Ministero (fogli Indicatori, monitoraggio
distrettuale di Milano, relazione I semestre 2026 riportata a mano SOLO nei controlli e indicata come tale).
"""
import sys, os, calendar, csv
import numpy as np, pandas as pd, openpyxl

T = sys.argv[1]
RAW = os.path.join(T, "raw", "ministero")
PU = os.path.join(T, "pulito")
os.makedirs(PU, exist_ok=True)
VER = []


def verifica(nome, calcolato, atteso, tol=0.0, nota=""):
    ok = abs(float(calcolato) - float(atteso)) <= tol
    VER.append({"controllo": nome, "calcolato": round(float(calcolato), 6), "atteso": round(float(atteso), 6), "tolleranza": tol,
                "esito": "ok" if ok else "DIVERSO", "nota": nota})
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso}, tol {tol})")


def chiave(s):
    s = str(s).strip().lower().replace("/bozen", "")
    return " ".join(s.split())


# ------------------------------------------------------------------ 1. Monitoraggio PNRR: definiti, pendenti, disposition time
F = os.path.join(RAW, "Monitoraggio_PNRR.xlsx")
civ = pd.read_excel(F, sheet_name="Civile")
pen = pd.read_excel(F, sheet_name="Penale")
for d in (civ, pen):
    d.loc[d["Tipo ufficio"] == "Cassazione", ["Sede", "Distretto", "Ripartizione"]] = ["Corte di Cassazione", "-", "-"]  # nel file la Cassazione non ha sede
    d["Sede"] = d["Sede"].str.strip()


def giorni(r):
    a = int(r["Anno"])
    if r["Periodo"] == "Intero anno":
        return 366 if calendar.isleap(a) else 365
    assert r["Periodo"] == "Primo semestre", r["Periodo"]
    return 182 if calendar.isleap(a) else 181


for d in (civ, pen):
    d["giorni_periodo"] = d.apply(giorni, axis=1)
    d["dt_giorni"] = d["giorni_periodo"] * d["Pendenti a fine periodo"] / d["Definiti"]
    d["tipo"] = d["Tipo ufficio"].map({"Tribunale": "tribunale", "Corte d'appello": "corte_appello", "Cassazione": "cassazione"})
    d["chiave"] = d["Sede"].map(chiave)

uff = pd.concat([civ.assign(settore="civile"), pen.assign(settore="penale")], ignore_index=True)
uff = uff.rename(columns={"Anno": "anno", "Periodo": "periodo", "Distretto": "distretto", "Sede": "sede", "Ripartizione": "ripartizione",
                          "Definiti": "definiti", "Pendenti a fine periodo": "pendenti", "Pendenti al 31/12/2019": "pendenti_31_12_2019",
                          "Arretrato": "arretrato_oltre_soglia", "Baseline obiettivo 2024": "baseline_obiettivo_2024",
                          "Pendenti per obiettivo 2024": "pendenti_obiettivo_2024", "Baseline obiettivo 2026": "baseline_obiettivo_2026",
                          "Pendenti per obiettivo 2026": "pendenti_obiettivo_2026"})
cols = ["settore", "tipo", "anno", "periodo", "ripartizione", "distretto", "sede", "definiti", "pendenti", "giorni_periodo", "dt_giorni",
        "pendenti_31_12_2019", "arretrato_oltre_soglia", "baseline_obiettivo_2024", "pendenti_obiettivo_2024", "baseline_obiettivo_2026",
        "pendenti_obiettivo_2026", "chiave"]
uff = uff[cols].sort_values(["settore", "tipo", "sede", "anno", "periodo"]).reset_index(drop=True)

# controllo: il disposition time ricalcolato coincide con quello dei fogli "Indicatori" dello stesso file (tribunali e corti di appello)
wb = openpyxl.load_workbook(F, read_only=True, data_only=True)
maxdiff = {"civile": 0.0, "penale": 0.0}
maxdiff_rif = {"civile": "", "penale": ""}
n_conf = 0
for foglio, tipo in (("Indicatori tribunali", "tribunale"), ("Indicatori corti appello", "corte_appello")):
    rows = list(wb[foglio].iter_rows(values_only=True))
    h1, h2 = rows[2], rows[3]
    nomi, cur = [], None
    for a, b in zip(h1, h2):
        cur = a if a else cur
        nomi.append((cur, b))
    idx = {}
    for i, (a, b) in enumerate(nomi):
        if a and a.startswith("Disposition time civile") and b in (2019, 2020, 2021, 2022, 2023, 2024, 2025):
            idx[("civile", b)] = i
        if a and a.startswith("Disposition time penale") and b in (2019, 2020, 2021, 2022, 2023, 2024, 2025):
            idx[("penale", b)] = i
    assert len(idx) == 14, idx
    for r in rows[4:]:
        if not r[1] or r[0] == "Totale nazionale":
            continue
        k = chiave(r[1])
        for (sett, anno), i in idx.items():
            v = r[i]
            m = uff[(uff.settore == sett) & (uff.tipo == tipo) & (uff.chiave == k) & (uff.anno == anno) & (uff.periodo == "Intero anno")]
            if v is None or not len(m):
                continue
            dd = abs(float(m.dt_giorni.iloc[0]) - float(v))
            n_conf += 1
            if dd > maxdiff[sett]:
                maxdiff[sett], maxdiff_rif[sett] = dd, f"{tipo} {r[1]} {anno}"
print("confronti DT con il foglio Indicatori:", n_conf)
verifica("numero di confronti del DT ricalcolato con il foglio Indicatori (civile e penale, tribunali e corti, 2019-2025)", n_conf, n_conf, 0, "serve a dire quanti confronti sono stati fatti")
for s in maxdiff:
    verifica(f"DT {s} ricalcolato vs foglio Indicatori (scarto massimo in giorni; {maxdiff_rif[s]})", maxdiff[s], 0, 0.5,
             "scarti maggiori di 0,5 giorni = ricalcolo diverso dal Ministero (vedi NOTE)")

# totale nazionale ricalcolato dai tribunali = riga "Totale nazionale" del Ministero
rows = list(wb["Indicatori tribunali"].iter_rows(values_only=True))
tot = [r for r in rows if r[0] == "Totale nazionale"][0]
nat = uff[(uff.settore == "civile") & (uff.tipo == "tribunale") & (uff.periodo == "Intero anno")].groupby("anno")[["definiti", "pendenti"]].sum()
verifica("pendenti civili 2025, somma dei 140 tribunali vs riga 'Totale nazionale'", nat.loc[2025, "pendenti"], tot[8], 0)
verifica("DT civile 2025 nazionale (somma 140 tribunali) vs 'Totale nazionale'", 365 * nat.loc[2025, "pendenti"] / nat.loc[2025, "definiti"], tot[17], 0.01)
verifica("DT civile 2019 nazionale vs relazione I sem. 2026 (tab. 5: 556; arrotondato)", 365 * nat.loc[2019, "pendenti"] / nat.loc[2019, "definiti"], 556, 0.5,
         "atteso scritto a mano dalla relazione del Ministero, pag. 8")

# controllo: il disposition time nazionale (tribunali, corti di appello, Cassazione) e il totale dei tre gradi ricalcolati dai dati per sede
# coincidono con le tabelle 5 (civile) e 9 (penale) della relazione I semestre 2026 (valori scritti a mano da quella relazione, pag. 8 e 13)
REL = {("civile", 2019): (556, 654, 1302, 2512), ("civile", 2025): (435, 492, 863, 1789), ("civile", "I2026"): (291, 352, 608, 1251),
       ("penale", 2019): (392, 841, 166, 1398), ("penale", 2025): (312, 524, 122, 958), ("penale", "I2026"): (299, 483, 73, 856)}
for (sett, per), att in REL.items():
    a_, pe_ = (2026, "Primo semestre") if per == "I2026" else (per, "Intero anno")
    q = uff[(uff.settore == sett) & (uff.anno == a_) & (uff.periodo == pe_)].groupby("tipo")[["definiti", "pendenti", "giorni_periodo"]].agg(
        {"definiti": "sum", "pendenti": "sum", "giorni_periodo": "max"})
    dts = [float(q.loc[t_, "giorni_periodo"] * q.loc[t_, "pendenti"] / q.loc[t_, "definiti"]) for t_ in ("tribunale", "corte_appello", "cassazione")]
    for nome, calc, at in zip(("tribunali", "corti di appello", "Cassazione", "somma dei tre gradi"), dts + [sum(dts)], att):
        verifica(f"DT {sett} {per} {nome} ricalcolato vs relazione I sem. 2026", calc, at, 0.6 if nome != "somma dei tre gradi" else 1.5,
                 "atteso scritto a mano dalla relazione del Ministero" + ("; la relazione ha corretto la baseline penale a 841 e 1398 giorni" if sett == "penale" and per == 2019 else ""))

# ------------------------------------------------------------------ 2. Flussi civili (iscritti, definiti, pendenti), aggregato SICID del monitoraggio
fc = pd.read_excel(os.path.join(RAW, "CivileFlussi20142025.xlsx"), sheet_name="Data").iloc[:, :12]
fc = fc.rename(columns={"Tipo ufficio": "tipo", "Sede": "sede", "Distretto": "distretto", "Anno": "anno", "Sopravvenuti": "iscritti",
                        "Definiti - totale": "definiti", "Pendenti finali": "pendenti"})
fc["tipo"] = fc["tipo"].map({"Tribunale": "tribunale", "Corte d'Appello": "corte_appello"})
fc["sede"] = fc["sede"].str.strip()
fc["chiave"] = fc["sede"].map(chiave)
sic = fc[fc.Fonte == "SICID"]
# tribunali: tutto il SICID tranne la macromateria "Altre procedure" (giudice tutelare, ATP previdenza, atti amministrativi);
# corti di appello: tutto il SICID (come dichiara la nota metodologica del Ministero)
agg_t = sic[(sic.tipo == "tribunale") & (sic.Macromateria != "Altre procedure")]
agg_c = sic[sic.tipo == "corte_appello"]
agg = pd.concat([agg_t, agg_c])
fl = agg.groupby(["tipo", "distretto", "sede", "chiave", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum()
pi = fc[(fc.tipo == "tribunale") & fc.Dettaglio.str.contains("nternazionale", na=False)]
pi = pi.groupby(["chiave", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum().rename(
    columns={"iscritti": "pi_iscritti", "definiti": "pi_definiti", "pendenti": "pi_pendenti"})
fl = fl.merge(pi, on=["chiave", "anno"], how="left")
fl.loc[fl.tipo != "tribunale", ["pi_iscritti", "pi_definiti", "pi_pendenti"]] = np.nan
fl["indice_ricambio"] = fl.definiti / fl.iscritti
fl = fl.sort_values(["tipo", "sede", "anno"]).reset_index(drop=True)

# controllo: protezione internazionale, pendenti nazionali nei tribunali 2025 = tab. 8 della relazione I sem. 2026 (133.398)
PI_REL = {2019: 94078, 2020: 89165, 2021: 77056, 2022: 64975, 2023: 66855, 2024: 92685, 2025: 133398}  # relazione I sem. 2026, tab. 8, pag. 12 (a mano)
for a_, att in PI_REL.items():
    calc = pi[pi.anno == a_].pi_pendenti.sum()
    verifica(f"protezione internazionale: pendenti nei tribunali {a_} vs relazione I sem. 2026 tab. 8", calc, att, 1100 if a_ in (2019, 2024) else 0,
             "atteso scritto a mano dalla relazione del Ministero, pag. 12" + ("; scarto noto (circa 1%), probabile aggiornamento successivo dei dati" if a_ in (2019, 2024) else ""))

# accertamenti tecnici preventivi (ATP) in materia di previdenza: pendenti nei tribunali, controllo con la tab. 8 della relazione I sem. 2026
atp = fc[(fc.tipo == "tribunale") & fc.Materia.str.contains("Accertamento Tecnico", na=False)]
atp = atp.groupby(["sede", "chiave", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum()
atp.drop(columns=["chiave"]).to_csv(os.path.join(PU, "atp_previdenza.csv"), index=False)
ATP_REL = {2019: 196773, 2020: 193348, 2021: 199776, 2022: 198814, 2023: 182445, 2024: 183533, 2025: 116296}  # relazione I sem. 2026, tab. 8, pag. 12 (a mano)
for a_, att in ATP_REL.items():
    verifica(f"ATP previdenza: pendenti nei tribunali {a_} vs relazione I sem. 2026 tab. 8", atp[atp.anno == a_].pendenti.sum(), att, 200 if a_ == 2019 else 0,
             "atteso scritto a mano dalla relazione del Ministero, pag. 12")

# materia "Stato della persona e diritti della personalita'" nei tribunali (per spiegare i valori estremi di alcuni uffici)
sp = fc[(fc.tipo == "tribunale") & fc.Materia.str.startswith("Stato della persona", na=False)]
sp.groupby(["sede", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum().to_csv(os.path.join(PU, "stato_persona_sedi.csv"), index=False)

# ------------------------------------------------------------------ 3. Flussi penali
fp = pd.read_excel(os.path.join(RAW, "PenaleFlussi20142025.xlsx"), sheet_name="Data")
fp = fp.rename(columns={"Distretto": "distretto", "Circondario/Sede": "sede", "Anno": "anno", "Sopravvenuti": "iscritti", "Definiti": "definiti",
                        "Pendenti Finali": "pendenti", "Sezione": "sezione"})
fp["anno"] = fp["anno"].astype(int)
fp["sede"] = fp["sede"].str.strip()
fp["chiave"] = fp["sede"].map(chiave)
fp["tipo"] = fp["Ufficio"].map({"Tribunale": "tribunale", "Corte di Appello": "corte_appello"})
fp = fp.dropna(subset=["tipo"])
fp["sezione"] = fp["sezione"].str.replace("\xa0", " ").str.strip()
SEZ = {"Giudice per le indagini e per l'udienza preliminare": "gip_gup", "Dibattimento monocratico": "dib_monocratico",
       "Dibattimento monocratico appello g.d.p": "dib_appello_gdp", "Dibattimento collegiale": "dib_collegiale", "Dibattimento assise": "assise",
       "Ordinaria": "ca_ordinaria", "Assise": "ca_assise", "Minorenni": "ca_minorenni"}
assert set(fp.sezione) == set(SEZ), set(fp.sezione) ^ set(SEZ)
fp["sez"] = fp.sezione.map(SEZ)
fpa = fp.groupby(["tipo", "distretto", "sede", "chiave", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum()
dm = fp[fp.sez == "dib_monocratico"][["chiave", "tipo", "anno", "iscritti", "definiti", "pendenti"]].rename(
    columns={"iscritti": "dibm_iscritti", "definiti": "dibm_definiti", "pendenti": "dibm_pendenti"})
gg = fp[fp.sez == "gip_gup"][["chiave", "tipo", "anno", "iscritti", "definiti", "pendenti"]].rename(
    columns={"iscritti": "gip_iscritti", "definiti": "gip_definiti", "pendenti": "gip_pendenti"})
fpa = fpa.merge(dm, on=["chiave", "tipo", "anno"], how="left").merge(gg, on=["chiave", "tipo", "anno"], how="left")
fpa["indice_ricambio"] = fpa.definiti / fpa.iscritti
fpa["dt_giorni"] = np.where(fpa.anno % 4 == 0, 366, 365) * fpa.pendenti / fpa.definiti
fpa["dibm_dt_giorni"] = np.where(fpa.anno % 4 == 0, 366, 365) * fpa.dibm_pendenti / fpa.dibm_definiti
fpa = fpa.sort_values(["tipo", "sede", "anno"]).reset_index(drop=True)

# controllo: pendenti penali del file dei flussi = pendenti del file PNRR (tutti gli uffici, tutti gli anni)
pp = pen[(pen.Periodo == "Intero anno") & pen.tipo.isin(["tribunale", "corte_appello"])][["tipo", "chiave", "Anno", "Pendenti a fine periodo", "Definiti"]]
mm = pp.merge(fpa[["tipo", "chiave", "anno", "pendenti", "definiti"]], left_on=["tipo", "chiave", "Anno"], right_on=["tipo", "chiave", "anno"], how="left",
              indicator=True, suffixes=("_pnrr", "_flussi"))
verifica("penale: uffici-anno del file PNRR senza riscontro nel file dei flussi", int((mm._merge != "both").sum()), 0, 0)
verifica("penale: scarto massimo sui pendenti tra file dei flussi e file PNRR", (mm["Pendenti a fine periodo"] - mm["pendenti"]).abs().max(), 0, 0)
verifica("penale: scarto massimo sui definiti tra file dei flussi e file PNRR", (mm["Definiti"] - mm["definiti"]).abs().max(), 0, 0)

# ------------------------------------------------------------------ 4. Controllo con il monitoraggio distrettuale di Milano (IV trimestre 2025)
def leggi_totali(path, foglio, etichetta):
    """Per ogni ufficio del foglio, i numeri della riga dei totali (iscritti e definiti per anno, in colonna)."""
    ws = openpyxl.load_workbook(path, data_only=True)[foglio]
    out, cur = {}, None
    for r in ws.iter_rows(values_only=True):
        if r[0] and ("Tribunale" in str(r[0]) or "Corte" in str(r[0])) and isinstance(r[1], str):
            cur = " ".join(str(r[0]).replace("Tribunale Ordinario di ", "").replace("Corte d'Appello di ", "Corte ").split())
        if cur and r[0] is None and r[1] == etichetta:
            out[cur] = [c for c in r[2:] if isinstance(c, (int, float))]
    return out


MIL = {"civile": os.path.join(RAW, "251231MilanoMonitoraggioCIVILE.xlsx"), "penale": os.path.join(RAW, "251231MilanoMonitoraggioPENALE.xlsx")}
tc = leggi_totali(MIL["civile"], "Flussi SICID", "TOTALE AREA SICID")
tpn = leggi_totali(MIL["penale"], "Flussi_milano", "TOTALE PENALE")
print("uffici letti dal monitoraggio distrettuale:", sorted(tc), sorted(tpn))
rows_ver = []
nome_ufficio = {"Busto Arsizio": "busto arsizio", "Como": "como", "Lecco": "lecco", "Lodi": "lodi", "Milano": "milano", "Monza": "monza", "Pavia": "pavia",
                "Sondrio": "sondrio", "Varese": "varese"}
dev_civ = []
for nome, k in nome_ufficio.items():
    v = tc[nome]  # iscritti/definiti 2023, 2024, 2025
    for j, a in enumerate((2023, 2024, 2025)):
        m = fl[(fl.tipo == "tribunale") & (fl.chiave == k) & (fl.anno == a)].iloc[0]
        for lab, calc, att in (("iscritti", m.iscritti, v[2 * j]), ("definiti", m.definiti, v[2 * j + 1])):
            dev_civ.append({"ufficio": nome, "anno": a, "voce": lab, "calcolato": int(calc), "monitoraggio": int(att), "scarto_pct": 100 * (calc - att) / att})
dev_civ = pd.DataFrame(dev_civ)
verifica("civile, tribunali del distretto di Milano 2023-2025: scarto massimo % (iscritti e definiti) tra flussi e monitoraggio", dev_civ.scarto_pct.abs().max(), 0, 3.0,
         "l'aggregato e' lo stesso; il file dei flussi da' sempre numeri un po' piu' alti (0,5-2,7%): estrazione diversa del Ministero. Tolleranza 3%")
for a_ in (2023, 2024, 2025):
    mi_ = dev_civ[(dev_civ.ufficio == "Milano") & (dev_civ.anno == a_)].set_index("voce")
    verifica(f"civile, Tribunale di Milano {a_}: indice di ricambio dai flussi (x100) vs monitoraggio (punti di scarto)",
             100 * mi_.loc["definiti", "calcolato"] / mi_.loc["iscritti", "calcolato"], 100 * mi_.loc["definiti", "monitoraggio"] / mi_.loc["iscritti", "monitoraggio"], 1.0)
verifica("civile, Tribunale di Milano 2025: scarto % sugli iscritti", dev_civ[(dev_civ.ufficio == "Milano") & (dev_civ.anno == 2025) & (dev_civ.voce == "iscritti")].scarto_pct.iloc[0], 0, 1.0)
dev_pen = []
for nome, k in nome_ufficio.items():
    v = tpn[nome]
    for j, a in enumerate((2023, 2024, 2025)):
        m = fpa[(fpa.tipo == "tribunale") & (fpa.chiave == k) & (fpa.anno == a)].iloc[0]
        for lab, calc, att in (("iscritti", m.iscritti, v[2 * j]), ("definiti", m.definiti, v[2 * j + 1])):
            dev_pen.append({"ufficio": nome, "anno": a, "voce": lab, "calcolato": int(calc), "monitoraggio": int(att), "scarto": int(calc - att)})
dev_pen = pd.DataFrame(dev_pen)
verifica("penale, tribunali del distretto di Milano 2023-2025: scarto massimo assoluto (iscritti e definiti) tra flussi e monitoraggio", dev_pen.scarto.abs().max(), 0, 0)
dev_civ.to_csv(os.path.join(PU, "controllo_monitoraggio_distrettuale_civile.csv"), index=False)
dev_pen.to_csv(os.path.join(PU, "controllo_monitoraggio_distrettuale_penale.csv"), index=False)

# ------------------------------------------------------------------ 5. Durata effettiva
du = pd.read_excel(os.path.join(RAW, "Durata_SICID_20142025.xlsx"), sheet_name="data")
du = du.rename(columns={"Ripartizione": "ripartizione", "Distretto": "distretto", "Tipo ufficio": "tipo", "Sede": "sede",
                        "Livello di aggregazione": "livello", "Materia": "materia", "Anno": "anno", "Definiti": "definiti",
                        "Durata media in giorni": "durata_giorni"}).drop(columns=["Durata media in anni"])
du["tipo"] = du.tipo.map({"Tribunale": "tribunale", "Corte d'appello": "corte_appello"})
du["livello"] = du.livello.map({"Circondariale": "ufficio", "Distrettuale": "distretto", "Nazionale": "nazionale"})
du["sede"] = du.sede.str.strip()
du["chiave"] = du.sede.map(chiave)
du = du[["tipo", "livello", "distretto", "sede", "chiave", "materia", "anno", "definiti", "durata_giorni"]]
# controllo: la durata "totale delle materie" e' la media pesata sui definiti delle materie (nazionale, tribunali)
n = du[(du.livello == "nazionale") & (du.tipo == "tribunale") & (du.anno == 2025)]
medie = n[n.materia != "Totale delle materie"]
pes = (medie.durata_giorni * medie.definiti).sum() / medie.definiti.sum()
verifica("durata effettiva 2025 nazionale (tribunali): media pesata delle materie vs 'Totale delle materie'", pes, n[n.materia == "Totale delle materie"].durata_giorni.iloc[0], 1.5,
         "le durate sono arrotondate al giorno e alcune materie possono mancare")

# ------------------------------------------------------------------ 6. Tribunale di Milano per materia
mi = fc[(fc.tipo == "tribunale") & (fc.chiave == "milano") & (fc.Fonte == "SICID")]
mat = mi.groupby(["Macromateria", "Materia", "anno"], as_index=False)[["iscritti", "definiti", "pendenti"]].sum()
mat.to_csv(os.path.join(PU, "materie_milano.csv"), index=False)

# ------------------------------------------------------------------ scrittura
uff.drop(columns=["chiave"]).to_csv(os.path.join(PU, "uffici_dt.csv"), index=False)
fl.drop(columns=["chiave"]).to_csv(os.path.join(PU, "flussi_civili.csv"), index=False)
fpa.drop(columns=["chiave"]).to_csv(os.path.join(PU, "flussi_penali.csv"), index=False)
du.drop(columns=["chiave"]).to_csv(os.path.join(PU, "durata_effettiva.csv"), index=False)
pd.DataFrame(VER).to_csv(os.path.join(PU, "verifiche.csv"), index=False)
print("scritti:", sorted(os.listdir(PU)))
bad = [v for v in VER if v["esito"] != "ok"]
print("controlli:", len(VER), "non riusciti:", len(bad))
for b in bad:
    print("  DIVERSO:", b["controllo"], b["calcolato"], b["atteso"])
