"""Scrive i file dati della pagina "Beni confiscati alla mafia a Milano" (docs/beni-confiscati/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <beni_confiscati_dir> <milano_in_dati_dir> <docs_dir>

Legge (fase 1): beni-confiscati/pulito/*.csv e riepilogo.json, i poligoni dei quartieri (NIL) di citta-15-minuti e i nomi dei NIL
di censimenti/pulito/nil_2021_anagrafica.csv.
Scrive in <docs_dir>/beni-confiscati/data/: riepilogo.json, nil.geojson, edifici.json, unita_comune.csv, destinati_anbsc.csv,
aziende_per_settore.csv, confronto_citta.csv, confronto_comuni.csv, serie_milano.csv.

Regole: mai nomi di persone, mai nomi di aziende, mai nomi di chi ha in uso i beni (solo il TIPO di ente).
Indirizzi a livello di edificio solo da due fonti aperte: elenco del Comune (ds147, CC BY) e beni destinati ANBSC (IODL 2.0).
I beni "in gestione" ANBSC non hanno indirizzo e restano solo conteggi."""
import sys, os, json, csv, re, collections, shutil

A, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(A, "pulito")
OUT = os.path.join(DOCS, "beni-confiscati", "data")
os.makedirs(OUT, exist_ok=True)
Cn = collections.Counter
AVVISI = []


def check(nome, calcolato, atteso):
    ok = calcolato == atteso
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


def rd(name):
    return list(csv.DictReader(open(os.path.join(PU, name), encoding="utf8", newline="")))


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(name, len(rows))


RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
imm = rd("immobili_anbsc_milano.csv")
com = rd("comune_ds147_milano.csv")
azm = rd("aziende_anbsc_milano.csv")
azu = rd("aziende_unioncamere_sede_milano.csv")
cmn = rd("confronto_comuni.csv")
dest = [r for r in imm if r["fonte"] == "ANBSC destinati"]
gest = [r for r in imm if r["stato"] == "in gestione"]

# ---------------------------------------------------------------- etichette e pulizie
TIPO_IT = {"abitazione": "abitazioni", "box_posto_auto": "box e posti auto", "negozio_laboratorio": "negozi e laboratori",
           "magazzino": "magazzini", "terreno": "terreni", "altro_pertinenza": "cantine, solai e simili",
           "altro_commerciale_industriale": "altri locali commerciali", "altro": "altro"}
# ente: l'elenco del Comune ha 'Impresa / privato' e 'Altro': li unisco, per non rendere riconoscibile un singolo locatario
ENTE = {"Comune (gestione diretta)": "Comune (gestione diretta)", "Fondazione": "Fondazione", "Cooperativa / impresa sociale": "Cooperativa o impresa sociale",
        "Associazione / volontariato": "Associazione o volontariato", "Impresa / privato": "Altro (impresa o privato)", "Altro": "Altro (impresa o privato)", "": "nessun assegnatario"}
USO = {"assegnato a terzi": "uso", "gestione diretta del Comune": "uso", "in attesa di assegnazione": "attesa",
       "non assegnato: lavori o problemi": "altro", "non assegnato: nessuna informazione": "altro"}
GRP_DEST = {"Comune": "Comune", "Forze dell'ordine e sicurezza": "Stato (forze dell'ordine)", "Stato (ministeri, amministrazioni)": "Stato (ministeri)",
            "Provincia / Citta metropolitana": "Provincia o Città metropolitana", "Altro": "Altro", "ANBSC": "ANBSC", "non indicato": "Altro"}


def indirizzo_pulito(s):
    s = re.sub(r"\(.*?\)|\(.*$", " ", s or "")
    s = s.replace("?", "'") if "LOCALIT?" in s else s
    s = re.sub(r"\bN\s*[.\-]\s*(?=\d)", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;-")
    s = s.split(" ANGOLO ")[0].split(" - ANG.")[0].split("/VIA ")[0].split(". Via ")[0]
    s = re.sub(r"\bpiano.*$", "", s, flags=re.I).strip(" ,")
    t = s.lower()
    t = re.sub(r"(^|[\s'(\-/.])([a-zàèéìòù])", lambda m: m.group(1) + m.group(2).upper(), t)
    t = re.sub(r"\bIi\b", "II", t)
    t = re.sub(r"\b(Di|Del|Della|Delle|Dei|Degli|Da|De|Dal)\b(?!$)", lambda m: m.group(1).lower(), t)
    t = re.sub(r" N\. ", " ", t)
    return t.replace("Via Via", "Via").strip()


PART = {"Di", "Del", "Della", "Delle", "Dei", "Degli", "Dello", "Da", "De", "Dal", "E"}


def titolo(s, primo=True):
    parole = s.lower().split()
    out = []
    for i, w in enumerate(parole):
        w2 = re.sub(r"(^|')([a-zàèéìòù])", lambda m: m.group(1) + m.group(2).upper(), w)
        out.append(w2.lower() if (w2 in PART and (i > 0 or not primo)) else w2)
    return " ".join(out)


def ind(r):
    """indirizzo in forma ufficiale (tipo + nome via del registro civici + numero); se non c'e', quello pulito"""
    if r.get("via_ufficiale"):
        tipo = r["via_ufficiale"].split(" ", 1)
        return (titolo(tipo[0]) + " " + titolo(tipo[1], primo=False) + (" " + r["civico_testo"] if r.get("civico_testo") else "")).strip()
    return indirizzo_pulito(r["indirizzo"])


def anno(r):
    return int(r) if r not in ("", None) else None


# ---------------------------------------------------------------- controlli sui totali (devono tornare con la fase 1)
check("immobili Milano", len(imm), 477)
check("destinati ANBSC Milano", len(dest), 319)
check("in gestione ANBSC Milano", len(gest), 158)
check("unita Comune", len(com), 274)
check("aziende ANBSC Milano", len(azm), 188)
check("aziende Unioncamere sede Milano", len(azu), 153)
check("in uso Comune", sum(1 for r in com if USO[r["stato_uso"]] == "uso"), 193)
check("in attesa Comune", sum(1 for r in com if USO[r["stato_uso"]] == "attesa"), 47)

# ---------------------------------------------------------------- NIL
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
nomi = {}
for r in csv.DictReader(open(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"), encoding="utf8")):
    nomi[int(r["nil"])] = r["nil_nome"]
nil_id_by_name = {}
for r in com + dest:
    if r["nil"] and r["id_nil"]:
        nil_id_by_name[r["nil"]] = int(r["id_nil"])
agg = collections.defaultdict(lambda: Cn())
for r in com:
    i = nil_id_by_name.get(r["nil"])
    if i is None:
        continue
    agg[i]["cu"] += 1
    agg[i]["c_" + USO[r["stato_uso"]]] += 1
for r in dest:
    i = nil_id_by_name.get(r["nil"])
    if i is None:
        continue
    agg[i]["ad"] += 1
    if r["destinatario_tipo"] == "Comune":
        agg[i]["adc"] += 1
check("unita Comune con quartiere", sum(v["cu"] for v in agg.values()), 274)
check("destinati ANBSC con quartiere", sum(v["ad"] for v in agg.values()), 319)


def rnd(c):
    return [round(x, 5) for x in c] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]


from shapely.geometry import shape, mapping
feats = []
for f in nilgeo["features"]:
    i = int(f["properties"]["ID_NIL"])
    g = shape(f["geometry"]).simplify(0.00003, preserve_topology=True)
    a = agg.get(i, Cn())
    feats.append({"type": "Feature", "properties": {"i": i, "n": nomi.get(i) or f["properties"]["NIL"].title(), "cu": a["cu"], "cuso": a["c_uso"],
                  "catt": a["c_attesa"], "calt": a["c_altro"], "ad": a["ad"], "adc": a["adc"]},
                  "geometry": {"type": g.geom_type, "coordinates": rnd(mapping(g)["coordinates"])}})
check("NIL", len(feats), 88)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
NIL_NOME = {f["properties"]["i"]: f["properties"]["n"] for f in feats}

# ---------------------------------------------------------------- edifici (punti)
OKQ = {"civico", "civico_senza_lettera", "via_civico_vicino"}
ed = {}


def gets(k, lon, lat, nilname, q):
    if k not in ed:
        ed[k] = {"lon": float(lon), "lat": float(lat), "nil": NIL_NOME.get(nil_id_by_name.get(nilname)) or "", "addr_c": [], "addr_a": [],
                 "approx": False, "cu": 0, "tipo_c": Cn(), "uso": Cn(), "ente": Cn(), "ydc": [], "ad": 0, "dest": Cn(), "tipo_a": Cn(), "yda": []}
    if q == "via_civico_vicino":
        ed[k]["approx"] = True
    return ed[k]


for r in com:
    if r["qualita_posizione"] in OKQ and r["lon"]:
        e = gets((r["lon"], r["lat"]), r["lon"], r["lat"], r["nil"], r["qualita_posizione"])
        e["addr_c"].append(ind(r))
        e["cu"] += 1; e["tipo_c"][r["tipo"]] += 1; e["uso"][USO[r["stato_uso"]]] += 1; e["ente"][ENTE[r["ente_tipo"]]] += 1
        if r["anno_destinazione_anbsc"]:
            e["ydc"].append(int(r["anno_destinazione_anbsc"]))
for r in dest:
    if r["qualita_posizione"] in OKQ and r["lon"]:
        e = gets((r["lon"], r["lat"]), r["lon"], r["lat"], r["nil"], r["qualita_posizione"])
        e["addr_a"].append(ind(r))
        e["ad"] += 1; e["dest"][GRP_DEST[r["destinatario_tipo"]]] += 1; e["tipo_a"][r["tipo"]] += 1
        if r["anno_destinazione"]:
            e["yda"].append(int(r["anno_destinazione"]))
edifici = []
for n, (k, e) in enumerate(sorted(ed.items(), key=lambda kv: (-(kv[1]["cu"] + kv[1]["ad"]), kv[0])), 1):
    ac = Cn(e["addr_c"]).most_common(1)
    aa = Cn(e["addr_a"]).most_common(1)
    edifici.append({"id": n, "a": (ac or aa)[0][0], "lon": e["lon"], "lat": e["lat"], "q": "vicino" if e["approx"] else "civico", "nil": e["nil"],
                    "cu": e["cu"], "tc": dict(e["tipo_c"]), "uso": e["uso"]["uso"], "att": e["uso"]["attesa"], "alt": e["uso"]["altro"],
                    "ente": dict(e["ente"]), "yc": [min(e["ydc"]), max(e["ydc"])] if e["ydc"] else None,
                    "ad": e["ad"], "dd": dict(e["dest"]), "ta": dict(e["tipo_a"]), "ya": [min(e["yda"]), max(e["yda"])] if e["yda"] else None})
check("unita Comune sui punti", sum(x["cu"] for x in edifici), sum(1 for r in com if r["qualita_posizione"] in OKQ and r["lon"]))
check("destinati sui punti", sum(x["ad"] for x in edifici), sum(1 for r in dest if r["qualita_posizione"] in OKQ and r["lon"]))
json.dump(edifici, open(os.path.join(OUT, "edifici.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print("edifici", len(edifici), "(di cui con unita del Comune:", sum(1 for x in edifici if x["cu"]), ")")

# ---------------------------------------------------------------- tabelle scaricabili (per unita', senza nomi)
rows = []
for r in com:
    rows.append({"id": r["id"], "tipo": TIPO_IT.get(r["tipo"], r["tipo"]), "indirizzo": ind(r), "municipio": r["municipio"],
                 "quartiere": NIL_NOME.get(nil_id_by_name.get(r["nil"]), ""), "lon": r["lon"], "lat": r["lat"], "posizione": r["qualita_posizione"],
                 "finalita": r["finalita"], "stato_uso": r["stato_uso"], "tipo_assegnatario": ENTE[r["ente_tipo"]],
                 "anno_inizio_contratto": r["anno_inizio_contratto"], "anno_decreto_anbsc": r["anno_destinazione_anbsc"], "anni_dal_decreto": r["anni_da_destinazione"]})
wr("unita_comune.csv", rows, ["id", "tipo", "indirizzo", "municipio", "quartiere", "lon", "lat", "posizione", "finalita", "stato_uso", "tipo_assegnatario", "anno_inizio_contratto", "anno_decreto_anbsc", "anni_dal_decreto"])
rows = []
for r in dest:
    rows.append({"tipo": TIPO_IT.get(r["tipo"], r["tipo"]), "categoria_catastale": r["sottocategoria"], "esito": r["dettaglio_stato"], "destinatario": r["destinatario_tipo"],
                 "finalita": r["finalita"], "anno_decreto": r["anno_destinazione"], "anno_procedimento": r["anno_procedura"], "indirizzo": ind(r),
                 "quartiere": NIL_NOME.get(nil_id_by_name.get(r["nil"]), ""), "lon": r["lon"], "lat": r["lat"], "posizione": r["qualita_posizione"]})
wr("destinati_anbsc.csv", rows, ["tipo", "categoria_catastale", "esito", "destinatario", "finalita", "anno_decreto", "anno_procedimento", "indirizzo", "quartiere", "lon", "lat", "posizione"])

# ---------------------------------------------------------------- aziende
set_ = sorted({r["settore"] or "(non indicato)" for r in azm})
rows = []
for s in set_:
    rows.append({"settore": s, "in_gestione": sum(1 for r in azm if (r["settore"] or "(non indicato)") == s and r["stato"] == "in gestione"),
                 "uscite": sum(1 for r in azm if (r["settore"] or "(non indicato)") == s and r["stato"] == "uscita"),
                 "uscite_liquidate": sum(1 for r in azm if (r["settore"] or "(non indicato)") == s and r["stato"] == "uscita" and r["dettaglio"] == "Liquidazione"),
                 "uscite_vendute": sum(1 for r in azm if (r["settore"] or "(non indicato)") == s and r["stato"] == "uscita" and r["dettaglio"] == "Vendita")})
rows.sort(key=lambda r: -(r["in_gestione"] + r["uscite"]))
wr("aziende_per_settore.csv", rows, ["settore", "in_gestione", "uscite", "uscite_liquidate", "uscite_vendute"])
SET_BREVE = {"Attività immobiliari, noleggio, informatica, ricerca, servizi alle imprese": "Immobiliare, informatica e servizi alle imprese",
             "Commercio ingrosso-dettaglio, riparazione veicoli, beni personali, casa": "Commercio e riparazioni", "Altri servizi pubblici, sociali e personali": "Altri servizi",
             "Trasporti, magazzinaggio e comunicazioni": "Trasporti e comunicazioni", "Attività finanziarie": "Finanza", "Attività manifatturiere": "Manifattura",
             "Agricoltura, caccia e silvicoltura": "Agricoltura", "Pesca, piscicoltura e servizi connessi": "Pesca", "(non indicato)": "Settore non indicato"}
AZ_SET = [[SET_BREVE.get(r["settore"], r["settore"]), r["in_gestione"], r["uscite"]] for r in rows]

# ---------------------------------------------------------------- confronto citta' (popolazione ISTAT 1/1/2025)
GRANDI = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Bari", "Catania", "Venezia", "Verona", "Messina", "Padova", "Trieste", "Brescia", "Bergamo", "Monza", "Reggio di Calabria"]
byname = {r["comune"]: r for r in cmn}
citta = []
for g in GRANDI:
    r = byname[g]
    imm_t = int(r["immobili"])
    citta.append({"comune": g, "ab": int(r["popolazione_2025"]), "tot": int(r["totale"]), "imm": imm_t, "az": int(r["aziende"]),
                  "p100k": float(r["per_100mila_abitanti"]), "imm_gest": int(r["immobili_in_gestione"]),
                  "quota_gest": round(100 * int(r["immobili_in_gestione"]) / imm_t, 1) if imm_t else None, "az_gest": int(r["aziende_in_gestione"])})
wr("confronto_citta.csv", citta, ["comune", "ab", "tot", "imm", "az", "p100k", "imm_gest", "quota_gest", "az_gest"])
shutil.copyfile(os.path.join(PU, "confronto_comuni.csv"), os.path.join(OUT, "confronto_comuni.csv"))
top_ass = [[r["comune"], int(r["totale"])] for r in sorted(cmn, key=lambda r: -int(r["totale"]))[:12]]
check("posizione di Milano", [t[0] for t in top_ass].index("Milano") + 1, 8)

# ---------------------------------------------------------------- serie nel tempo
S = RIEP["serie_milano"]
k14, k24, k26 = list(S)
serie = [
    {"data": "settembre 2014", "fonte": "copia ANBSC su confiscatibene.it (Wayback Machine)", "imm_gest": S[k14]["immobili_stati"]["Immobili in gestione"],
     "imm_dest": S[k14]["immobili_stati"]["Immobili destinati consegnati"] + S[k14]["immobili_stati"]["Immobili destinati non consegnati"],
     "az_gest": S[k14]["aziende_stati"]["Aziende in gestione"], "az_dest": S[k14]["aziende_stati"]["Aziende uscite dalla gestione"]},
    {"data": "agosto 2024", "fonte": "copia ANBSC su confiscatibene.it (Wayback Machine)", "imm_gest": S[k24]["immobili_in_gestione"], "imm_dest": S[k24]["immobili_destinati"],
     "az_gest": S[k24]["aziende_in_gestione"], "az_dest": S[k24]["aziende_destinate"]},
    {"data": "novembre 2026", "fonte": "ANBSC, scaricato il 1/11/2026", "imm_gest": S[k26]["immobili_in_gestione"], "imm_dest": S[k26]["immobili_destinati"],
     "az_gest": S[k26]["aziende_in_gestione"], "az_dest": S[k26]["aziende_destinate"]},
]
wr("serie_milano.csv", serie, ["data", "fonte", "imm_gest", "imm_dest", "az_gest", "az_dest"])

# ---------------------------------------------------------------- numeri per la pagina
tipi_ord = ["abitazione", "box_posto_auto", "terreno", "negozio_laboratorio", "magazzino", "altro_pertinenza", "altro_commerciale_industriale", "altro"]


def conta_tipo(rows, key="tipo"):
    c = Cn(r[key] for r in rows)
    return [[TIPO_IT[t], c.get(t, 0)] for t in tipi_ord]


stato_tipo = []
for t in tipi_ord:
    stato_tipo.append([TIPO_IT[t], sum(1 for r in imm if r["tipo"] == t and r["stato"] == "in gestione"),
                       sum(1 for r in imm if r["tipo"] == t and r["stato"] == "destinato"), sum(1 for r in imm if r["tipo"] == t and r["stato"] == "uscito")])
uso_tipo = []
for t in tipi_ord:
    rr = [r for r in com if r["tipo"] == t]
    if rr:
        uso_tipo.append([TIPO_IT[t], sum(1 for r in rr if USO[r["stato_uso"]] == "uso"), sum(1 for r in rr if USO[r["stato_uso"]] == "attesa"), sum(1 for r in rr if USO[r["stato_uso"]] == "altro")])
anni = sorted({int(r["anno_destinazione"]) for r in dest if r["anno_destinazione"]})
dec = [[a, sum(1 for r in dest if r["anno_destinazione"] == str(a) and r["destinatario_tipo"] == "Comune"),
        sum(1 for r in dest if r["anno_destinazione"] == str(a) and r["destinatario_tipo"] != "Comune")] for a in range(min(anni), max(anni) + 1)]
check("decreti con anno", sum(d[1] + d[2] for d in dec), sum(1 for r in dest if r["anno_destinazione"]))
att = [int(r["anni_da_destinazione"]) for r in com if USO[r["stato_uso"]] != "uso" and r["anni_da_destinazione"] != ""]
att_sorted = sorted(att)
mediana = (att_sorted[len(att_sorted) // 2] if len(att_sorted) % 2 else (att_sorted[len(att_sorted) // 2 - 1] + att_sorted[len(att_sorted) // 2]) / 2)
att_nocarlo = sorted(int(r["anni_da_destinazione"]) for r in com if USO[r["stato_uso"]] != "uso" and r["anni_da_destinazione"] != "" and r["via_abbinata"] != "CARLO TORRE")
check("non in uso con anno", len(att), 57)
check("mediana anni dal decreto", mediana, 18)
check("mediana senza Carlo Torre 24", att_nocarlo[len(att_nocarlo) // 2], 19)
torre = [r for r in com if r["via_abbinata"] == "CARLO TORRE"]
check("unita Via Carlo Torre 24", len(torre), 18)
check("di cui in attesa", sum(1 for r in torre if USO[r["stato_uso"]] == "attesa"), 18)
check("di cui box", sum(1 for r in torre if r["tipo"] == "box_posto_auto"), 18)
check("anno decreto Via Carlo Torre", {r["anno_destinazione_anbsc"] for r in torre}, {"2008"})
b3 = Cn((r["via_abbinata"], re.sub(r"\D", "", r["indirizzo"].split(",")[0])) for r in com)
top5 = b3.most_common(5)
check("tre palazzi", sum(v for _, v in top5[:3]), 59)
check("cinque palazzi", sum(v for _, v in top5), 75)
dec_anni_att = Cn(2026 - a for a in att)
quartieri_top = sorted(((f["properties"]["n"], f["properties"]["cu"]) for f in feats), key=lambda x: -x[1])[:6]
check("primi quattro quartieri", sum(v for _, v in quartieri_top[:4]), 102)

ec = [r for r in com if r["stato_uso"] == "assegnato a terzi"]
ente_cnt = Cn(ENTE[r["ente_tipo"]] for r in com if r["stato_uso"] in ("assegnato a terzi", "gestione diretta del Comune"))
fin_c = Cn(r["finalita"] for r in com)
dest_cnt = Cn(GRP_DEST[r["destinatario_tipo"]] for r in dest)
fin_dc = Cn(r["finalita"] or "non indicata" for r in dest if r["destinatario_tipo"] == "Comune")
az_u = {"stato_attivita": Cn(r["stato_attivita"] for r in azu), "stato_amm": Cn(r["stato_amministrativo"] for r in azu)}
ATECO_IT = {"A": "Agricoltura e pesca", "B": "Estrazione", "C": "Manifattura", "D": "Energia", "E": "Acqua e rifiuti", "F": "Costruzioni", "G": "Commercio",
            "H": "Trasporto e magazzinaggio", "I": "Alloggio e ristorazione", "J": "Informazione e comunicazione", "K": "Finanza e assicurazioni",
            "L": "Attività immobiliari", "M": "Attività professionali e tecniche", "N": "Noleggio e servizi alle imprese", "O": "Pubblica amministrazione",
            "P": "Istruzione", "Q": "Sanità e assistenza", "R": "Arte, sport, intrattenimento", "S": "Altri servizi", "X": "Imprese non classificate"}
ateco = [[ATECO_IT.get(k, k), v] for k, v in Cn(r["ateco_sezione"] for r in azu).most_common()]
att_top = Cn(r["ateco_attivita"] for r in azu).most_common(8)
comp = Cn(r["ateco_attivita"] for r in azu)["Compravendita di beni immobili effettuata su beni propri"]
check("compravendita immobili", comp, 31)
check("aziende attive Unioncamere", az_u["stato_attivita"]["ATTIVA"], 46)
mov = RIEP["movimenti_immobili_2024_2026"]
nazionale = {k: v for k, v in RIEP["nazionale_aziende_uscite_esiti"]}
check("aziende uscite Italia", sum(nazionale.values()), 1790)
check("liquidate Italia", nazionale["Liquidazione"], 1697)
reg_lomb = RIEP["lombardia_per_provincia"]
mi_row = byname["Milano"]

riep = {
    "data_scarico": "2026-11-01",
    "milano": {"totale": 665, "immobili": 477, "aziende": 188, "pop": int(mi_row["popolazione_2025"]), "p100k": float(mi_row["per_100mila_abitanti"]),
               "pos_italia": 8, "quota_italia_pct": round(100 * 665 / RIEP["italia_totale_beni"], 2), "italia_totale": RIEP["italia_totale_beni"],
               "italia_immobili": RIEP["italia_immobili_aziende"][0], "italia_aziende": RIEP["italia_immobili_aziende"][1]},
    "top_assoluti": top_ass,
    "immobili_stato": {"in_gestione": len(gest), "destinati": sum(1 for r in imm if r["stato"] == "destinato"), "venduti": sum(1 for r in imm if r["stato"] == "uscito"),
                       "destinati_enti": sum(1 for r in imm if r["dettaglio_stato"].startswith("Trasferimento")), "destinati_stato": sum(1 for r in imm if r["dettaglio_stato"].startswith("Mantenimento"))},
    "stato_tipo": stato_tipo, "uso_tipo": uso_tipo, "tipi_tot": conta_tipo(imm),
    "gestione_provvedimento": RIEP["gestione_per_dettaglio_provvedimento"],
    "destinatari": dict(dest_cnt), "finalita_comune": dict(fin_dc),
    "comune": {"unita": 274, "indirizzi": RIEP["ds147_indirizzi_distinti"], "uso": 193, "in_gestione_diretta": 28, "assegnate_terzi": 165, "attesa": 47, "lavori": 10, "senza_info": 24,
               "nuove_2026": RIEP["ds147_nuova_acquisizione_2026"], "enti": dict(ente_cnt), "finalita": dict(fin_c), "per_tipo": conta_tipo(com),
               "contratti_scaduti": RIEP["ds147_contratti_scaduti_giugno_2026"].get("si", 0), "contratti_senza_date": RIEP["ds147_contratti_scaduti_giugno_2026"].get("", 0),
               "anni_decreto_non_in_uso": dict(sorted(dec_anni_att.items())), "n_non_in_uso_con_anno": len(att), "mediana_anni": mediana, "mediana_senza_torre": att_nocarlo[len(att_nocarlo) // 2],
               "oltre_10": sum(1 for a in att if a >= 10), "oltre_5": sum(1 for a in att if a >= 5), "agganciate_a_anbsc": sum(1 for r in com if r["anno_destinazione_anbsc"] != ""),
               "top5_palazzi": [[x["a"], x["cu"]] for x in sorted(edifici, key=lambda x: -x["cu"])[:5]], "tre_palazzi": 59, "cinque_palazzi": 75, "quartieri_top": quartieri_top,
               "torre": {"unita": 18, "in_attesa_totali": 47, "decreto": 2008, "anni": 18}},
    "anbsc_dest_comune": 215, "decreti": dec, "decreto_2008_comune": next(d[1] for d in dec if d[0] == 2008), "decreto_2008_tot": next(d[1] + d[2] for d in dec if d[0] == 2008),
    "aziende": {"gest": 115, "uscite": 73, "liquidate": 68, "vendute": 5, "settori": AZ_SET, "italia_esiti": nazionale, "italia_uscite": 1790,
                "quota_liquidate_italia": round(100 * nazionale["Liquidazione"] / 1790, 1), "forma": RIEP["aziende_milano_forma_giuridica"],
                "uc": {"tot": 153, "stato_attivita": dict(az_u["stato_attivita"]), "stato_amm": dict(az_u["stato_amm"]), "ateco": ateco, "attivita_top": att_top, "compravendita_immobili": comp}},
    "citta": citta, "quota_gestione": RIEP["immobili_quota_in_gestione"],
    "provincia": {"tot": RIEP["provincia_milano"]["totale"], "pos": RIEP["provincia_milano_posizione"], "quota_citta": RIEP["milano_comune_quota_provincia"],
                  "comuni": RIEP["comuni_provincia_milano_top12"], "lombardia": reg_lomb, "lombardia_tot": RIEP["lombardia_totale"], "dettaglio": RIEP["provincia_milano"]},
    "tipo_it_vs_mi": {"it_terreni_pct": round(100 * RIEP["tipo_immobili_Italia"]["terreno"] / RIEP["italia_immobili_aziende"][0], 1),
                      "mi_terreni_pct": round(100 * RIEP["tipo_immobili_Milano"]["terreno"] / 477, 1),
                      "it_abit_pct": round(100 * RIEP["tipo_immobili_Italia"]["abitazione"] / RIEP["italia_immobili_aziende"][0], 1),
                      "mi_abit_pct": round(100 * RIEP["tipo_immobili_Milano"]["abitazione"] / 477, 1)},
    "serie": serie, "movimenti": {"gest_2024": mov["gestione_2024"], "ancora_gest": mov["di_cui_ancora_in_gestione_2026"], "ora_destinati": mov["di_cui_ora_tra_i_destinati_2026"],
                                   "non_piu_visibili": mov["di_cui_non_piu_in_nessun_elenco"], "nuovi_destinati": mov["destinati_2026_nuovi_rispetto_2024"],
                                   "destinati_2024_ancora": mov["di_cui_ancora_destinati_2026"], "destinati_2024": mov["destinati_2024"],
                                   "az_gest_2024": RIEP["movimenti_aziende_2024_2026"]["in_gestione_2024"], "az_ancora": RIEP["movimenti_aziende_2024_2026"]["ancora_in_gestione_2026"], "az_nuove": RIEP["movimenti_aziende_2024_2026"]["nuove_in_gestione_2026"],
                                   "nuovi_per_anno": mov["nuovi_2026_per_anno_decreto"]},
    "posizione": {"anbsc": RIEP["destinati_posizione_qualita"], "comune": RIEP["ds147_posizione_qualita"], "edifici": len(edifici)},
    "anni_procedimento_mediana": RIEP["anno_procedura_mediano_destinati"], "anni_procedimento_decreto_mediana": RIEP["anni_dal_procedimento_al_decreto_mediana"],
}
check("pos. Milano nel confronto", riep["provincia"]["pos"], 8)
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("riepilogo.json scritto")

# ---------------------------------------------------------------- controllo: nessun nome nei file scritti
vietati = ["passepartout", "somaschi", "casa della carit", "progetto arca", "gelatamo", "staylist", "atomic garden", "syed", "ripari", "archè", "kayros", "anteo"]
for fn in os.listdir(OUT):
    t = open(os.path.join(OUT, fn), encoding="utf8", errors="replace").read().lower()
    for v in vietati:
        if v in t:
            AVVISI.append(f"NOME in {fn}: {v}")
print("\nAVVISI:" if AVVISI else "\nnessun avviso", *AVVISI, sep="\n")
