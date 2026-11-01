"""Perimetro del filone "I soldi per i quartieri popolari": progetti con CUP nel Comune di Milano, da OpenCoesione, PNRR (ReGiS/Italia Domani) e PNC.
Uso (percorsi assoluti): python -I -X utf8 05_perimetro.py <fondi-quartieri> <milano-in-dati>
Legge:  raw/opencoesione/oc_milano_tutti.csv (script 01), raw/italiadomani/pnrr_milano_unito.csv (script 02), raw/italiadomani/OpenData_PNC_*.csv,
        raw/italiadomani/PNRR_Gare.csv, citta-15-minuti/out/civici_tempi.csv (civici con NIL)
Scrive: pulito/progetti_perimetro.csv (una riga per progetto), pulito/progetti_esclusi_verifica.csv, pulito/perimetro_log.txt
Il perimetro e' DICHIARATO: l'elenco dei CUP di OpenCoesione e' scelto a mano dopo lettura di titolo e sintesi (OC_REGOLE qui sotto, con il motivo);
per il PNRR e' per sotto-misura (PINQuA, Housing First = nucleo; Piani urbani integrati = perimetro largo). nucleo=1 -> entra nei totali "titolo".
Importi: OpenCoesione = costo coesione / pagamenti coesione (OC_COSTO_COESIONE, OC_PAGAMENTI_COESIONE); PNRR = Finanziamento Totale / Pagamento Totale (ReGiS, stesso CUP);
PNC = solo importi AGGIUDICATI nelle gare (il finanziamento per progetto non e' nei dati aperti)."""
import sys, os, re, unicodedata, json
import pandas as pd

F, P = sys.argv[1], sys.argv[2]
PU = os.path.join(F, "pulito")
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")


# ------------------------------------------------------------------ civici -> NIL (via / via+civico)
civ = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["CODICE_VIA", "NUMEROCOMPLETO", "DENOMINAZIONE", "ID_NIL", "NIL"])
civ = civ.dropna(subset=["ID_NIL"])
civ["ID_NIL"] = civ.ID_NIL.astype(int)
NILN = civ.drop_duplicates("ID_NIL").set_index("ID_NIL").NIL.to_dict()
STOPW = {"DI", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DELL", "DELLO", "DA", "D", "LA", "LE", "IL", "LO", "I", "GLI", "SAN", "SANTA", "SANT", "SANTI", "S", "E", "N", "ED"}


def vtoks(name):
    s = strip_acc(name).upper()
    s = re.sub(r"\(.*?\)", " ", s)  # "GIAGGIOLI (DEI)" -> "GIAGGIOLI"
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return frozenset(t for t in s.split() if t not in STOPW)


STREET = {}  # frozenset(token) -> DataFrame dei civici
for (cod, den), g in civ.groupby(["CODICE_VIA", "DENOMINAZIONE"]):
    k = vtoks(den)
    if k and sum(len(t) for t in k) >= 5:
        STREET[k] = pd.concat([STREET[k], g]) if k in STREET else g
INV = {}
for k in STREET:
    for t in k:
        INV.setdefault(t, set()).add(k)
TIPI = r"(?:VIA|VIALE|PIAZZA|PIAZZALE|LARGO|CORSO|VICOLO|STRADA|ALZAIA|PIAZZETTA)"
FINE = {"ED", "E", "A", "NEL", "NEI", "PER", "CON", "DA", "IN", "ANGOLO", "PRESSO", "TORRE", "LOTTO", "CIVICO", "NUOVO", "NUOVI", "OPERE", "OPERA", "RISTRUTTURAZIONE", "RIQUALIFICAZIONE", "REALIZZAZIONE", "DEMOLIZIONE", "INTERVENTO", "COMPARTO", "FABBRICATI", "MILANO", "COMUNE", "ZONA", "QUARTIERE"}


def trova_via(cands):
    """cands: token (senza stopword) che seguono il tipo di via, fino al primo numero/parola di coda. Cerca la via: set uguale, poi unico superset."""
    for n in range(len(cands), 0, -1):
        k = frozenset(cands[:n])
        if k in STREET:
            return k
    for n in range(len(cands), 0, -1):
        k = frozenset(cands[:n])
        if sum(len(t) for t in k) < 5:
            continue
        sets = [INV.get(t, set()) for t in k]
        com = set.intersection(*sets) if sets else set()
        if len(com) == 1:
            return next(iter(com))
    return None


def nil_da_testo(testo):
    """cerca 'VIA <nome> [civico]' nel testo; restituisce (lista NIL, metodo, via)."""
    t = strip_acc(testo).upper()
    t = re.sub(r"[^A-Z0-9 /]", " ", t)
    t = re.sub(r"\s+", " ", t)
    for m in re.finditer(TIPI + r"\s+([A-Z0-9][A-Z0-9 ]{2,45})", t):
        toks = m.group(1).split()
        cands, civico = [], None
        for w in toks:
            if re.match(r"^\d+[A-Z]?$", w):
                civico = w
                break
            if w in FINE:
                break
            if w not in STOPW:
                cands.append(w)
            if len(cands) >= 4:
                break
        if not cands:
            continue
        k = trova_via(cands)
        if k is None:
            continue
        g = STREET[k]
        nome = " ".join(sorted(k))
        if civico:
            cn = re.sub(r"[^A-Z0-9]", "", civico)
            gg = g[g.NUMEROCOMPLETO.astype(str).str.upper().str.replace(r"[^A-Z0-9]", "", regex=True) == cn]
            if len(gg):
                return sorted(gg.ID_NIL.unique().tolist()), "via_e_civico", nome
        share = g.ID_NIL.value_counts(normalize=True)
        if share.iloc[0] >= 0.8:
            return [int(share.index[0])], "via", nome
        return [int(i) for i in share.index[:3]], "via_in_piu_NIL", nome
    return [], "", ""


# nomi di quartiere -> NIL (scelta mia, documentata in NOTE.md)
QUARTIERI = [
    (r"LORENTEGGIO", "Lorenteggio-Giambellino", [53, 49]),
    (r"GIAMBELLINO", "Lorenteggio-Giambellino", [53, 49]),
    (r"SAN SIRO|S\.? ?SIRO|SELINUNTE|BARACCA", "San Siro", [57]),
    (r"GRATOSOGLIO", "Gratosoglio", [41]),
    (r"CORVETTO", "Corvetto", [35]),
    (r"QUARTO OGGIARO", "Quarto Oggiaro", [76]),
    (r"NIGUARDA", "Niguarda", [14]),
    (r"BOVISASCA", "Bovisasca", [81]),
    (r"PONTE LAMBRO", "Ponte Lambro", [31]),
    (r"STADERA", "Stadera", [42]),
    (r"MOLISE|CALVAIRATE", "Molise-Calvairate", [28]),
]


def nil_da_quartiere(testo):
    t = strip_acc(testo).upper()
    hits = []
    for pat, nome, ids in QUARTIERI:
        if re.search(pat, t) and nome not in [h[0] for h in hits]:
            hits.append((nome, ids))
    return hits


def tipo_ente(s):
    u = strip_acc(str(s)).upper()
    if "ALER" in u or "AZIENDA LOMBARDA EDILIZIA" in u:
        return "ALER Milano"
    if re.search(r"\bMM S\.?P\.?A", u) or u.startswith("MM "):
        return "MM spa"
    if "COMUNE DI MILANO" in u:
        return "Comune di Milano"
    if "REGIONE LOMBARDIA" in u:
        return "Regione Lombardia"
    if "CITTA METROPOLITANA" in u or "CITTA' METROPOLITANA" in u:
        return "Citta metropolitana di Milano"
    if "MINISTERO" in u:
        return "Ministero"
    return "Altro/non indicato"


def parse_d(s, fmt):
    return pd.to_datetime(s, format=fmt, errors="coerce")


rows = []

# ============================================================== OpenCoesione
oc = pd.read_csv(os.path.join(F, "raw", "opencoesione", "oc_milano_tutti.csv"), sep=";", dtype=str, keep_default_na=False)
for c in ["OC_COSTO_COESIONE", "OC_PAGAMENTI_COESIONE", "OC_FINANZ_TOT_PUB_NETTO"]:
    oc[c] = num(oc[c])
log("OpenCoesione: righe Milano", len(oc), "di cui comune esattamente 'Milano':", int((oc.DEN_COMUNE == "Milano").sum()))
# regole: CUP (o titolo) -> (ambito, nucleo, motivo). ambiti: ERP = case popolari; ABIT = alloggi per l'emergenza e servizi per l'abitare; QUART = spazi e servizi nei quartieri popolari/fragili
E_ = "ERP"
A_ = "ABIT"
Q_ = "QUART"
OC_REGOLE = {
    "H41H14000130009": (E_, 1, "Accordo di programma Lorenteggio: edifici ERP (titolo)"),
    "I46B14000010008": (E_, 1, "Accordo di programma Lorenteggio: acquisizione alloggi privati negli edifici da riqualificare"),
    "I42H19000260002": (E_, 1, "efficientamento energetico fabbricato ALER (via Cascina dei Prati 25)"),
    "B47H21007240004": (E_, 1, "riqualificazione energetica edilizia pubblica residenziale, via San Romanello 34"),
    "B41E13000120004": (E_, 1, "PON Metro: recupero edilizia residenziale pubblica"),
    "B41E13000140004": (E_, 1, "PON Metro: recupero edilizia residenziale pubblica"),
    "B44F18000180004": (E_, 1, "PSC Citta metropolitana (Bando periferie): sintesi 'edilizia residenziale - riqualificazione edifici pubblici'"),
    "B46D17000180004": (A_, 1, "PON Metro: ristrutturazione alloggi per persone con disabilita'/disagio e per accoglienza temporanea"),
    "B41H17000030004": (A_, 1, "PON Metro: hub per l'ospitalita' temporanea (emergenza abitativa)"),
    "I49F18000680001": (A_, 1, "PON Legalita': unita' abitative temporanee, Ponte Lambro"),
    "B59I17000240006": (A_, 1, "Agenzia sociale per la locazione (poverta' abitativa)"),
    "B49J17000130006": (A_, 1, "supporto abitativo per persone in emarginazione (servizi)"),
    "B41B17000110006": (A_, 1, "piattaforma per georeferenziare alloggi di residenzialita' sociale temporanea"),
    "B46G17000580006": (Q_, 1, "Quartieri connessi: sistema informativo per la gestione ERP"),
    "B44E17000570006": (Q_, 1, "Quartieri connessi: spazi polifunzionali nel patrimonio abitativo per gli inquilini"),
    "B49E19001200006": (Q_, 1, "Quartieri connessi: servizi sociali in quartieri con degrado e marginalita'"),
    "B49G24000190006": (Q_, 1, "'Abitare il quartiere': attivita' sociali nei quartieri ERP"),
    "B47B17000250004": (Q_, 1, "riqualificazione del verde, quartiere Lorenteggio"),
    "B41E17000070004": (Q_, 1, "riqualificazione del verde, quartiere Lorenteggio"),
    "B41H17000140001": (Q_, 1, "servizi di bassa soglia in quartieri periferici (sintesi: 'quartieri periferici')"),
    "B45I17000260004": (Q_, 1, "ristrutturazione edifici in degrado per servizi sociali (marginalita')"),
    "B49J20003110006": (Q_, 1, "coesione sociale in quartieri con fragilita'"),
    "B49J20003120006": (Q_, 1, "servizi di welfare in quartieri con fragilita'"),
    "I44D24000720007": (Q_, 1, "scuola: 'E-state a San Siro'"),
    "E44D24002590007": (Q_, 1, "scuola: 'Base Corvetto'"),
    "B44J25000830001": (Q_, 1, "'Sport Social Lab Selinunte' (San Siro)"),
    # perimetro largo (non nel titolo)
    "B44E17000370004": (Q_, 0, "depavimentazione QT8 e via Rovereto: quartiere non indicato come fragile"),
    "B49J21020950007": (Q_, 0, "economia civile nei quartieri (tutta la citta')"),
    "B49J21020970007": (Q_, 0, "economia civile nei quartieri (tutta la citta')"),
}
OC_ESCLUSI = {
    "I22H19000110002": "titoli 'via dei Larici' e 'via Larici 8 e 10 a Rozzano': comune dubbio (OpenCoesione lo mette a Milano, il titolo dice Rozzano). Escluso dalle somme",
    "F48C25000460007": "alloggi di un privato (Granfonte srl)",
}
FSE_ABITARE = "FINANZIAMENTO DI MODELLI DI SERVIZI TERRITORIALI INTEGRATI PER L"
oc_m = oc[oc.DEN_COMUNE == "Milano"].copy()
sel = []
for _, r in oc_m.iterrows():
    cup = r.CUP
    if cup in OC_ESCLUSI:
        continue
    if cup in OC_REGOLE:
        amb, nuc, why = OC_REGOLE[cup]
    elif r.OC_TITOLO_PROGETTO.upper().startswith(FSE_ABITARE):
        amb, nuc, why = A_, 1, "PR FSE+ Lombardia: accompagnamento all'abitare di persone vulnerabili (servizi)"
    else:
        continue
    sel.append((r, amb, nuc, why))
# controllo: progetti 'ABITATIVE' (CUP) non scelti
ab = oc_m[(oc_m.CUP_DESCR_SOTTOSETTORE == "ABITATIVE")]
nonsc = [c for c in ab.CUP.unique() if c not in OC_REGOLE and c not in OC_ESCLUSI and not ab[ab.CUP == c].OC_TITOLO_PROGETTO.str.upper().str.startswith(FSE_ABITARE).all()]
log("OC: CUP del sottosettore ABITATIVE non scelti (controllo):", nonsc)
mancanti = [c for c in OC_REGOLE if c not in set(oc_m.CUP)]
log("OC: CUP delle regole non trovati nei dati:", mancanti)
for r, amb, nuc, why in sel:
    testo = r.OC_TITOLO_PROGETTO + " " + r.OC_SINTESI_PROGETTO
    att = r.OC_DENOM_ATTUATORE or r.OC_DENOM_BENEFICIARIO or r.OC_DENOM_PROGRAMMATORE
    rows.append(dict(
        fonte="OpenCoesione", id_progetto=r.COD_LOCALE_PROGETTO, cup=r.CUP, titolo=r.OC_TITOLO_PROGETTO, sintesi=r.OC_SINTESI_PROGETTO[:400],
        programma=r.OC_DESCRIZIONE_PROGRAMMA, ciclo=r.OC_DESCR_CICLO.replace("Ciclo di programmazione ", ""), ambito=amb, nucleo=nuc, motivo_perimetro=why,
        ente_attuatore=att, tipo_ente=tipo_ente(att), ente_ruolo="attuatore" if r.OC_DENOM_ATTUATORE else ("beneficiario" if r.OC_DENOM_BENEFICIARIO else "programmatore"),
        importo=r.OC_COSTO_COESIONE, pagato=r.OC_PAGAMENTI_COESIONE, misura_importo="costo coesione / pagamenti coesione (OpenCoesione)",
        stato=r.OC_STATO_PROGETTO, fase=r.OC_DESCR_FASE_CORRENTE, data_inizio=r.OC_DATA_INIZIO_PROGETTO, fine_prevista=r.OC_DATA_FINE_PROGETTO_PREVISTA,
        fine_effettiva=r.OC_DATA_FINE_PROGETTO_EFFETTIVA, data_aggiornamento=r.DATA_AGGIORNAMENTO, fmt_data="%Y%m%d", url=r.OC_LINK, _testo=testo, _cat=r.CUP_DESCR_CATEGORIA))

# ============================================================== PNRR
pn = pd.read_csv(os.path.join(F, "raw", "italiadomani", "pnrr_milano_unito.csv"), sep=";", dtype=str, keep_default_na=False)
for c in ["Finanziamento Totale", "Finanziamento PNRR", "PAG Pagamento Totale", "PAG Pagamento PNRR", "Percentuale di Localizzazione"]:
    pn[c] = num(pn[c])
SM = {"M5C2I2.03.01": ("PNRR - PINQuA (qualita' dell'abitare)", 1), "M5C2I1.03.00": ("PNRR - Housing First e stazioni di posta", 1),
      "M5C2I2.02.03": ("PNRR - Piani urbani integrati (periferie)", 0)}
gare = pd.read_csv(os.path.join(F, "raw", "italiadomani", "PNRR_Gare.csv"), sep=";", dtype=str, encoding="utf-8-sig", usecols=["CUP", "CIG", "Oggetto Gara", "Importo Aggiudicazione"])
gare_t = gare.groupby("CUP")["Oggetto Gara"].apply(lambda s: " | ".join(s.dropna().astype(str).tolist()))
for _, r in pn[pn["Codice Univoco Submisura"].isin(SM)].iterrows():
    prog, nuc = SM[r["Codice Univoco Submisura"]]
    fq = r["Percentuale di Localizzazione"] / 100.0  # quota del progetto localizzata a Milano (piste ciclabili metropolitane: piu' comuni)
    cat = r["CUP Descrizione Categoria"]
    sint = r["Sintesi Progetto"]
    if r["Codice Univoco Submisura"] == "M5C2I1.03.00":
        amb = A_
        titolo = "Housing First (progetto " + r["Titolo Progetto"].split(" ")[1] + ")"
    else:
        titolo = sint.split("*")[-1].strip() if "*" in sint else r["Titolo Progetto"]
        if cat in ("FABBRICATI RESIDENZIALI URBANI", "INFRASTRUTTURE CIVILI PER COMPLESSI RESIDENZIALI"):
            amb = E_
        elif r["Codice Univoco Submisura"] == "M5C2I2.03.01":
            amb = Q_
        else:
            amb = Q_
    gt = gare_t.get(r.CUP, "")
    txt_att = (sint + " " + gt).upper()
    att = r["Soggetto Attuatore"]
    ruolo = "soggetto attuatore (ReGiS)"
    reale = ""
    # esecuzione: MM solo se la sintesi inizia col nome (es. "MM S.P.A.*VIA ..."); ALER solo se le gare parlano di edifici/patrimonio ALER
    if sint.upper().startswith("MM S.P.A"):
        reale = "MM spa"
    elif re.search(r"(EDIFIC[IO]|PATRIMONIO|PROPRIET[AÀ]|DISPONIBILIT[AÀ])[^|]{0,40}\bALER\b", gt.upper()):
        reale = "ALER Milano"
    rows.append(dict(
        fonte="PNRR (ReGiS)", id_progetto=r["Codice Locale Progetto"], cup=r.CUP, titolo=titolo, sintesi=sint[:400], programma=prog,
        ciclo="PNRR 2021-2026", ambito=amb, nucleo=nuc, motivo_perimetro="sotto-misura " + r["Codice Univoco Submisura"] + " (" + r["Descrizione Submisura"][:40] + ")",
        ente_attuatore=att, tipo_ente=tipo_ente(reale or att), ente_ruolo=ruolo + (("; esecuzione indicata nel testo/gare: " + reale) if reale else ""),
        importo=r["Finanziamento Totale"] * fq, pagato=r["PAG Pagamento Totale"] * fq, misura_importo="finanziamento totale / pagamento totale (ReGiS)" + (" x quota localizzata a Milano %.0f%%" % (fq * 100) if fq < 1 else ""),
        quota_pnrr=r["Finanziamento PNRR"] * fq, stato=r["Stato Avanzamento Progetto"], fase=r["Descrizione Fase Iter di Progetto"] + " (" + r["Stato Fase Iter di Progetto"] + ")",
        data_inizio=r["Data Inizio Progetto Effettiva"] or r["Data Inizio Progetto Prevista"], fine_prevista=r["Data Fine Progetto Prevista"], fine_effettiva=r["Data Fine Progetto Effettiva"],
        data_aggiornamento=r["Data di Estrazione"], fmt_data="%d/%m/%Y", url="", _testo=r["Titolo Progetto"] + " " + sint, _cat=cat))
log("PNRR: righe nel perimetro", sum(1 for x in rows if x["fonte"].startswith("PNRR")))

# ============================================================== PNC "Sicuro, verde e sociale" (riqualificazione ERP)
pl = pd.read_csv(os.path.join(F, "raw", "italiadomani", "OpenData_PNC_LocalizzazioneGeografica.csv"), sep=";", dtype=str, encoding="utf-8-sig")
pm = pl[(pl.Comune.str.upper() == "MILANO") & (pl["Codice Intervento"] == "C.13.0.0")]
pg = pd.read_csv(os.path.join(F, "raw", "italiadomani", "OpenData_PNC_Gare.csv"), sep=";", dtype=str, encoding="utf-8-sig")
pg["imp"] = num(pg["Importo Aggiudicazione"])
for cup in pm.CUP.unique():
    g = pg[(pg.CUP == cup)]
    gimp = g.dropna(subset=["imp"])
    big = gimp.sort_values("imp", ascending=False).head(1)
    sa = g["Stazione Appaltante"].dropna().iloc[0] if len(g) else ""
    og = big["Descrizione Oggetto Gara"].iloc[0] if len(big) else ""
    rows.append(dict(
        fonte="PNC (Italia Domani)", id_progetto=cup, cup=cup, titolo=og[:300], sintesi="", programma="PNC - Sicuro, verde e sociale (riqualificazione edilizia residenziale)", ciclo="PNC 2021-2026",
        ambito=E_, nucleo=1, motivo_perimetro="intervento PNC C.13.0.0 'riqualificazione edilizia residenziale', localizzato a Milano", ente_attuatore=sa, tipo_ente=tipo_ente(sa), ente_ruolo="stazione appaltante (gare PNC)",
        importo=float(gimp.imp.sum()), pagato=float("nan"), misura_importo="SOLO importi aggiudicati nelle gare (finanziamento per progetto non nei dati aperti)",
        stato="", fase="", data_inizio="", fine_prevista="", fine_effettiva="", data_aggiornamento="07/03/2024", fmt_data="%d/%m/%Y", url="", _testo=og, _cat=""))

# ============================================================== quartiere
for x in rows:
    t = x["_testo"]
    nil_ids, metodo, area = [], "", ""
    # 1) via e civico / via
    ids, m, via = nil_da_testo(t)
    hits = nil_da_quartiere(t)
    if m in ("via_e_civico", "via") and len(ids) == 1:
        nil_ids, metodo, area = ids, "indirizzo nel testo (" + m + "): " + via.title(), NILN[ids[0]].title()
    elif hits:
        nome, nl = hits[0]
        nil_ids, metodo, area = nl, "nome del quartiere nel testo", nome
    elif m:
        nil_ids, metodo, area = ids, "indirizzo nel testo ma la via attraversa piu' NIL: " + via.title(), ""
    x["_ids"] = nil_ids
    x["quartiere"] = area
    x["nil_id"] = ";".join(str(i) for i in nil_ids)
    x["nil_nome"] = ";".join(NILN[i].title() for i in nil_ids)
    x["metodo_quartiere"] = metodo or "non localizzabile dal testo"

# PINQuA: la proposta (ID nel titolo ReGiS) vale come area per i progetti che il testo non localizza
PROP = {"94": ("Lorenteggio-Giambellino", [53, 49]), "363": ("San Siro", [57]), "318": ("Niguarda", [14]), "510": ("Gratosoglio", [41])}
for x in rows:
    if x["fonte"].startswith("PNRR") and "PINQuA" in x["programma"]:
        mid = re.search(r"ID (\d+)", x["_testo"])
        pid = mid.group(1) if mid else ""
        x["proposta_pinqua_id"] = pid
        if pid in PROP:
            ar, ids = PROP[pid]
            if not x["quartiere"]:
                x["quartiere"], x["_ids"] = ar, ids
                x["nil_id"] = ";".join(map(str, ids)); x["nil_nome"] = ";".join(NILN[i].title() for i in ids)
                x["metodo_quartiere"] = "proposta PINQuA ID %s (le altre opere della proposta sono in questo quartiere)" % pid
            x["area_proposta"] = ar
# i progetti PINQuA della proposta 94 che toccano tutta la linea M4 / il tram non sono in un solo quartiere: segnato
for x in rows:
    if x.get("proposta_pinqua_id") == "94" and re.search(r"LINEA M4|LINEA CIRCOLARE 90", x["_testo"].upper()):
        x["metodo_quartiere"] = "proposta PINQuA ID 94 (opera lungo piu' quartieri: M4 / linea 90-91, non in un solo quartiere)"
        x["quartiere"], x["nil_id"], x["nil_nome"], x["_ids"] = "", "", "", []
        x["ambito"], x["nucleo"] = "MOB", 0
        x["motivo_perimetro"] += "; opera di mobilita' della proposta PINQuA ID 94: fuori dal nucleo (non in un solo quartiere popolare)"
    if x.get("proposta_pinqua_id") == "94" and "OLONA" in x["_testo"].upper():
        x["ambito"], x["nucleo"] = "MOB", 0
        x["motivo_perimetro"] += "; pista ciclabile via Olona (Magenta-S.Vittore) della proposta PINQuA ID 94: fuori dal nucleo"
# dentro l'ID 363 la caserma di via Newton non e' nel quartiere San Siro per testo: usa via_e_civico se c'e'

df = pd.DataFrame(rows)
df["pagato_pct"] = (df.pagato / df.importo * 100).where(df.importo > 0)
fp = [parse_d(a, f) for a, f in zip(df.fine_prevista, df.fmt_data)]
fe = [parse_d(a, f) for a, f in zip(df.fine_effettiva, df.fmt_data)]
df["fine_prevista_iso"] = [x.strftime("%Y-%m-%d") if pd.notna(x) else "" for x in fp]
df["fine_effettiva_iso"] = [x.strftime("%Y-%m-%d") if pd.notna(x) else "" for x in fe]
df["ritardo_giorni"] = [(e - p).days if pd.notna(e) and pd.notna(p) else float("nan") for p, e in zip(fp, fe)]
# stesso CUP in due fonti (OC e PNRR): si segnala
cups = df.groupby("cup").fonte.nunique()
doppi = cups[cups > 1].index.tolist()
df["cup_in_piu_fonti"] = df.cup.isin(doppi).astype(int)
log("CUP presenti in piu' fonti:", doppi)
df = df.drop(columns=["_testo", "_cat", "_ids", "fmt_data"])
col = ["fonte", "cup", "id_progetto", "titolo", "programma", "ciclo", "ambito", "nucleo", "motivo_perimetro", "ente_attuatore", "tipo_ente", "ente_ruolo", "quartiere", "nil_id", "nil_nome", "metodo_quartiere",
       "importo", "pagato", "pagato_pct", "quota_pnrr", "misura_importo", "stato", "fase", "data_inizio", "fine_prevista_iso", "fine_effettiva_iso", "ritardo_giorni", "data_aggiornamento", "proposta_pinqua_id", "area_proposta", "cup_in_piu_fonti", "sintesi", "url"]
for c in col:
    if c not in df.columns:
        df[c] = ""
df[col].to_csv(os.path.join(PU, "progetti_perimetro.csv"), sep=";", index=False, encoding="utf-8")
log("progetti nel perimetro:", len(df), "nucleo:", int(df.nucleo.sum()))
print(df.groupby(["fonte", "nucleo", "ambito"]).agg(n=("cup", "size"), importo=("importo", "sum"), pagato=("pagato", "sum")).round(0).to_string())
# esclusi per verifica
pd.DataFrame([{"fonte": "OpenCoesione", "cup": k, "motivo": v} for k, v in OC_ESCLUSI.items()]).to_csv(os.path.join(PU, "progetti_esclusi_verifica.csv"), sep=";", index=False, encoding="utf-8")
open(os.path.join(PU, "perimetro_log.txt"), "w", encoding="utf-8").write("\n".join(LOG))
