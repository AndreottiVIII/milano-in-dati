"""Pulizia: raw/ -> pulito/ (violenza-donne). Rieseguibile.

Uso:  python -I -X utf8 costruisci.py <cartella violenza-donne assoluta>
Richiede openpyxl (solo per leggere l'xlsx ISTAT). Nessun dato personale: solo conteggi.
Non scrive indirizzi, telefoni, e-mail, nomi di centri o case rifugio.
"""
import sys, os, csv, json, datetime, collections

BASE = sys.argv[1]
RAW = os.path.join(BASE, "raw")
OUT = os.path.join(BASE, "pulito")
os.makedirs(OUT, exist_ok=True)


def wcsv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def rcsv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


controlli = []
riep = {}

# ---------- 1522: serie annuale 2013-2024 (esploradati) + 2025 (xlsx) ----------
ut = rcsv(os.path.join(RAW, "istat", "1522_utenti_regione.csv"))
vi = rcsv(os.path.join(RAW, "istat", "1522_vittime_regione.csv"))
u = {(r["REF_AREA"], int(r["TIME_PERIOD"])): int(r["OBS_VALUE"]) for r in ut
     if r["TYPES_USERS"] == "ALL_VAL" and r["SEX"] == "T"}
vt = {(r["REF_AREA"], int(r["TIME_PERIOD"])): int(r["OBS_VALUE"]) for r in vi if r["AGE"] == "TOTAL" and r["SEX"] == "T"}
vf = {(r["REF_AREA"], int(r["TIME_PERIOD"])): int(r["OBS_VALUE"]) for r in vi if r["AGE"] == "TOTAL" and r["SEX"] == "F"}

import openpyxl
wb = openpyxl.load_workbook(os.path.join(RAW, "istat", "Tavole_ITA_REV-19ottobre2026.xlsx"), data_only=True)


def tab_regioni(nome):
    """Tavola 6/7: dict regione -> {(anno,trim): valore}"""
    ws = wb[nome]
    rows = list(ws.iter_rows(values_only=True))
    anni = {}
    cur = None
    for j, v in enumerate(rows[1]):
        if isinstance(v, int):
            cur = v
        if j > 0 and cur:
            anni[j] = cur
    out = {}
    for r in rows[3:]:
        if r[0] and not str(r[0]).startswith("Fonte") and r[1] is not None:
            d = {}
            for j in range(1, 13):
                q = int(str(rows[2][j])[0])
                x = r[j]
                d[(anni[j], q)] = int(x) if isinstance(x, (int, float)) else 0
            out[str(r[0]).strip()] = d
    return out


T6 = tab_regioni("Tavola 6")  # chiamate da utenti per regione
T7 = tab_regioni("Tavola 7")  # chiamate da vittime per regione


def tot(d, anno):
    return sum(v for (a, q), v in d.items() if a == anno)


for anno in (2023, 2024):
    for reg, cod in (("ITALIA", "IT"), ("Lombardia", "ITC4")):
        a, b = tot(T6[reg], anno), u[(cod, anno)]
        controlli.append(f"utenti {reg} {anno}: tavola 6 = {a}, esploradati = {b}, {'OK' if a == b else 'DIVERSO'}")
        a, b = tot(T7[reg], anno), vt[(cod, anno)]
        controlli.append(f"vittime {reg} {anno}: tavola 7 = {a}, esploradati = {b}, {'OK' if a == b else 'DIVERSO'}")

righe = []
for anno in range(2013, 2026):
    if anno <= 2024:
        ui, ul = u[("IT", anno)], u[("ITC4", anno)]
        vi_, vl = vt[("IT", anno)], vt[("ITC4", anno)]
        vfi, vfl = vf[("IT", anno)], vf[("ITC4", anno)]
        fonte = "Istat esploradati"
    else:
        ui, ul = tot(T6["ITALIA"], anno), tot(T6["Lombardia"], anno)
        vi_, vl = tot(T7["ITALIA"], anno), tot(T7["Lombardia"], anno)
        vfi = vfl = ""
        fonte = "Istat tavole 1522 anno 2025"
    if anno <= 2022:
        serie = "piattaforma precedente"
    elif anno <= 2024:
        serie = "nuova piattaforma"
    else:
        serie = "mista (1 trim. vecchio gestore, poi nuovo)"
    righe.append([anno, serie, ui, ul, round(100 * ul / ui, 2), vi_, vl, vfi, vfl, fonte])
wcsv("1522_annuale_italia_lombardia.csv",
     ["anno", "serie", "chiamate_valide_utenti_italia", "chiamate_valide_utenti_lombardia", "quota_lombardia_su_italia_pct",
      "chiamate_vittime_italia", "chiamate_vittime_lombardia", "vittime_donne_italia", "vittime_donne_lombardia", "fonte"], righe)

# ---------- quota Lombardia sul totale con regione nota, e quota di popolazione femminile ----------
pop = rcsv(os.path.join(RAW, "istat", "pop_1.csv"))
popf = {(r["REF_AREA"], int(r["TIME_PERIOD"])): int(r["OBS_VALUE"]) for r in pop if r["SEX"] == "2" and r["MARITAL_STATUS"] == "99"}
riga_q = []
for anno in range(2013, 2026):
    if anno <= 2024:
        tot_it = u[("IT", anno)]
        ignoto = u.get(("ITNI", anno), 0)
    else:
        tot_it = tot(T6["ITALIA"], anno)
        ignoto = tot(T6["N.D."], anno) + tot(T6["Non risponde"], anno)
    if anno == 2024:
        ignoto_t = tot(T6["N.D."], anno) + tot(T6["Non risponde"], anno)
        controlli.append(f"2024 regione ignota: esploradati ITNI = {ignoto}, tavola 6 N.D.+Non risponde = {ignoto_t}")
    nota = tot_it - ignoto
    lom = u[("ITC4", anno)] if anno <= 2024 else tot(T6["Lombardia"], anno)
    k = popf.get(("ITC4", anno + 1))
    pq = round(100 * k / popf[("IT", anno + 1)], 2) if k else ""
    riga_q.append([anno, tot_it, ignoto, round(100 * ignoto / tot_it, 1), lom, round(100 * lom / nota, 2), pq])
wcsv("1522_regione_ignota_e_quota.csv",
     ["anno", "chiamate_valide_utenti_italia", "con_regione_ignota_o_non_risponde", "pct_regione_ignota", "lombardia",
      "quota_lombardia_su_regione_nota_pct", "quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"], riga_q)

# ---------- 1522: trimestri per Lombardia e Italia ----------
righe = []
for reg in ("Lombardia", "ITALIA", "N.D.", "Non risponde"):
    for (a, q), v in sorted(T6[reg].items()):
        righe.append([a, q, reg, v, T7[reg][(a, q)]])
wcsv("1522_trimestri_regioni.csv", ["anno", "trimestre", "territorio", "chiamate_utenti", "chiamate_vittime"], righe)

# ---------- 1522: motivi (tavola 1) ----------
ws = wb["Tavola 1"]
rows = list(ws.iter_rows(values_only=True))
anni = {}
cur = None
for j, v in enumerate(rows[1]):
    if isinstance(v, int):
        cur = v
    if j > 0 and cur:
        anni[j] = cur
voci = {"Richiesta di aiuto vittima di violenza": "aiuto_violenza", "Richiesta di aiuto vittima di stalking": "aiuto_stalking",
        "Segnalazione di un caso di violenza": "segnalazione_caso", "Informazioni sui Centri Antiviolenza Nazionali": "info_centri_antiviolenza",
        "Informazioni sul servizio 1522": "info_servizio_1522", "Informazioni Giuridiche": "info_giuridiche",
        "Chiamate fuori target": "fuori_target", "Totale chiamate valide": "totale_valide", "Totale chiamate non valide": "totale_non_valide",
        "Totale chiamate": "totale"}
righe = []
for r in rows[3:]:
    k = str(r[0]).strip() if r[0] else ""
    if k in voci:
        for j in range(1, 13):
            q = int(str(rows[2][j])[0])
            righe.append([anni[j], q, voci[k], int(r[j]) if isinstance(r[j], (int, float)) else 0])
wcsv("1522_motivi_trimestri_italia.csv", ["anno", "trimestre", "motivo", "chiamate"], righe)

# ---------- 1522: chiamate giornaliere (tavola 5) ----------
ws = wb["Tavola 5"]
rows = list(ws.iter_rows(values_only=True))
anni5 = list(range(2018, 2026))
giorni = []  # (mese, giorno, anno, valore)
for r in rows[3:]:
    if isinstance(r[0], datetime.datetime):
        m, g = r[0].month, r[0].day
    elif isinstance(r[0], str) and r[0].startswith("29"):
        m, g = 2, 29
    else:
        continue
    for j, a in enumerate(anni5, start=1):
        if r[j] is not None:
            giorni.append((m, g, a, int(r[j])))
tot_anno = collections.Counter()
mens = collections.defaultdict(int)
for m, g, a, v in giorni:
    tot_anno[a] += v
    mens[(a, m)] += v
for a in anni5:
    ref = u.get(("IT", a)) if a <= 2024 else tot(T6["ITALIA"], a)
    controlli.append(f"giornaliere {a}: somma tavola 5 = {tot_anno[a]}, utenti validi annui = {ref}, {'OK' if tot_anno[a] == ref else 'DIVERSO'}")
wcsv("1522_mensile_italia.csv", ["anno", "mese", "chiamate_utenti_valide"], [[a, m, mens[(a, m)]] for a in anni5 for m in range(1, 13)])
top = sorted(giorni, key=lambda x: -x[3])[:15]
wcsv("1522_giorni_di_punta.csv", ["anno", "mese", "giorno", "chiamate_utenti_valide"], [[a, m, g, v] for m, g, a, v in top])
med = {}
for a in anni5:
    vals = sorted(v for m, g, aa, v in giorni if aa == a)
    med[a] = vals[len(vals) // 2]
riep["mediana_giornaliera"] = med
riep["giorni_di_punta"] = [[a, m, g, v] for m, g, a, v in top]
riep["25_novembre"] = [(a, v) for m, g, a, v in giorni if m == 11 and g == 25]

# ---------- Centri antiviolenza e case rifugio (Regione Lombardia, CC0) ----------
lom = os.path.join(RAW, "lombardia")
alb = rcsv(os.path.join(lom, "dphu-pcij.csv"))
conv = rcsv(os.path.join(lom, "jvq8-53gf.csv"))
cr = rcsv(os.path.join(lom, "8eux-iam2.csv"))
sigla = {"MI": "Milano", "BS": "Brescia", "BG": "Bergamo", "VA": "Varese", "MB": "Monza e della Brianza", "CR": "Cremona",
         "PV": "Pavia", "LC": "Lecco", "CO": "Como", "MA": "Mantova", "LO": "Lodi", "SO": "Sondrio"}
prov = sorted(sigla.values())
c_alb = collections.Counter(r["PROVINCIA"].strip() for r in alb)
c_conv = collections.Counter(sigla[r["Provincia"].strip()] for r in conv)
c_conv_centri = collections.Counter(sigla[r["Provincia"].strip()] for r in conv if r["Tipo (centro/sportello)"] == "Centro")
c_cr = collections.Counter(r["PROVINCIA_SEDE_LEGALE"].strip() for r in cr)
righe = [[p, c_alb.get(p, 0), c_conv.get(p, 0), c_conv_centri.get(p, 0), c_cr.get(p, 0)] for p in prov]
righe.append(["Lombardia", len(alb), len(conv), sum(c_conv_centri.values()), len(cr)])
wcsv("centri_lombardia_province.csv",
     ["provincia", "albo_regionale_centri_e_sportelli_apr2026", "convenzionati_centri_e_sportelli_set2026", "convenzionati_solo_centri_set2026",
      "case_rifugio_voci_elenco_provincia_sede_legale"], righe)
controlli.append(f"convenzionati: {len(conv)} righe, centri {sum(c_conv_centri.values())}, sportelli {len(conv)-sum(c_conv_centri.values())}")
controlli.append(f"albo: {len(alb)} righe; enti gestori distinti {len(set(r['ENTE_GESTORE'] for r in alb))}")
nomi_cr = set(r["NOME_CR"] for r in cr)
controlli.append(f"case rifugio: {len(cr)} righe, nomi distinti {len(nomi_cr)}, enti gestori {len(set(r['ENTE _GESTORE'] for r in cr))}")
riep["lombardia"] = {
    "albo_righe": len(alb), "albo_enti": len(set(r["ENTE_GESTORE"] for r in alb)),
    "albo_struttura": dict(collections.Counter(r["STRUTTURE_GESTITE"] for r in alb)),
    "conv_righe": len(conv), "conv_centri": sum(c_conv_centri.values()), "conv_sportelli": len(conv) - sum(c_conv_centri.values()),
    "cr_righe": len(cr), "cr_nomi": len(nomi_cr), "cr_struttura": dict(collections.Counter(r["STRUTTURE_GESTITE"] for r in cr)),
    "albo_milano_provincia": c_alb.get("Milano", 0), "albo_comune_milano": sum(1 for r in alb if r["COMUNE"].strip().lower() == "milano"),
    "conv_milano_provincia": c_conv.get("Milano", 0), "conv_comune_milano": sum(1 for r in conv if r["Comune"].strip().lower() == "milano"),
    "cr_milano_provincia": c_cr.get("Milano", 0),
    "cr_comune_milano": sum(1 for r in cr if r["COMUNE_SEDE_LEGALE"].strip().lower() == "milano"),
}

# ---------- Centri antiviolenza Istat 2024 ----------
cav = rcsv(os.path.join(RAW, "istat", "cav.csv"))


def cv(area, dt, **kw):
    for r in cav:
        if r["REF_AREA"] == area and r["DATA_TYPE"] == dt and all(r[k] == v for k, v in kw.items()):
            return float(r["OBS_VALUE"])


righe = []
nrif = {}
for area, nome in (("IT", "Italia"), ("ITC4", "Lombardia")):
    n = cv(area, "AVC", SERVICE_PROVIDED="ALL", PROVIDER="9", Y_PRESENCE="9", SERVICE="ALL", NUM_BRANCHES="TOT", RISK_ASS_METH="TOT")
    f = popf[(area, 2025)]
    nrif[nome] = n
    righe.append([nome, "centri_antiviolenza_2024", n, ""])
    righe.append([nome, "centri_per_100mila_donne_residenti", round(100000 * n / f, 3), f"donne residenti al 1/1/2025 = {f}"])
    for s, lab in (("H24AVAIL", "reperibilita_24_ore_pct"), ("LINK1522", "adesione_1522_pct"), ("ANSWMAC", "segreteria_telefonica_pct"),
                   ("FREENUM", "numero_verde_pct"), ("SERVCHART", "carta_dei_servizi_pct")):
        righe.append([nome, lab, cv(area, "AVCTER", Y_PRESENCE="1", SERVICE=s), ""])
    righe.append([nome, "centri_con_sportelli_composizione_pct_N1|N2|N3|N4+",
                  "|".join(str(cv(area, "AVCDESK", NUM_BRANCHES=k)) for k in ("N1", "N2", "N3", "N4_GE")), ""])
wcsv("cav_istat_2024.csv", ["territorio", "indicatore", "valore", "nota"], righe)
controlli.append(f"Istat CAV 2024: Lombardia {nrif['Lombardia']} centri, convenzionati 'Centro' {sum(c_conv_centri.values())}")

pm = popf[("ITC45", 2025)]
riep["cav_per_100mila_donne"] = {
    "milano_provincia_albo": round(100000 * c_alb.get("Milano", 0) / pm, 2),
    "milano_provincia_conv": round(100000 * c_conv.get("Milano", 0) / pm, 2),
    "lombardia_albo": round(100000 * len(alb) / popf[("ITC4", 2025)], 2),
    "lombardia_conv": round(100000 * len(conv) / popf[("ITC4", 2025)], 2),
    "italia_istat_centri": round(100000 * nrif["Italia"] / popf[("IT", 2025)], 2),
    "lombardia_istat_centri": round(100000 * nrif["Lombardia"] / popf[("ITC4", 2025)], 2),
    "donne_milano_provincia_2025": pm, "donne_lombardia_2025": popf[("ITC4", 2025)], "donne_italia_2025": popf[("IT", 2025)],
}

# ---------- Femminicidi: serie nazionale (Istat, Report vittime di omicidio 2024, 25/11/2025) ----------
# valori trascritti dal testo del report; nessuna tabella aperta per la Lombardia trovata
fem = [[2019, 111, 101], [2020, 116, 106], [2021, 119, 104], [2022, 126, 105], [2023, 117, 96], [2024, 116, 106]]
wcsv("femminicidi_italia_istat.csv", ["anno", "omicidi_con_vittima_donna", "femminicidi_stimati"], fem)

wcsv("controlli.csv", ["controllo"], [[c] for c in controlli])
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(controlli))
print(json.dumps(riep, ensure_ascii=False)[:3500])
