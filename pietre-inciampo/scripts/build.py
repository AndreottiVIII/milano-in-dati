"""Costruisce pulito/pietre.csv unendo: schede del Comitato (campi + coordinate della mappa), Wikipedia (data posa esatta, controllo),
civici del Comune (controllo indirizzo/coordinate), NIL.
Uso: python -I -X utf8 build.py <pietre-inciampo_abs> <milano-in-dati_abs>"""
import sys, os, re, json, math, difflib, unicodedata
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from shapely import STRtree
from pyproj import Transformer

A, P = sys.argv[1], sys.argv[2]
pul = os.path.join(A, "pulito")
log = {}
MESI = {m: i + 1 for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}


def norm(s):
    s = (s or "").replace("’", " ").replace("'", " ").replace("f.lli", "fratelli").replace("F.lli", "fratelli")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s).split()


def d2iso(s):
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


# ---------- Comitato
S = pd.read_csv(os.path.join(pul, "comitato_schede.csv"), sep=";", dtype=str, keep_default_na=False)
recs = []
for _, s in S.iterrows():
    r = {"id_scheda": int(s.id_scheda)}
    campi = [x.strip() for x in s.campi_raw.split(" | ")]
    ib = next(j for j, x in enumerate(campi) if re.match(r"(Nat[oa]|Arrestat[oa]|Mort[oa])\b", x))
    r["nome_proprio"], r["cognome"] = campi[ib - 2], campi[ib - 1]
    r["sesso"] = "F" if re.match(r"(Nata|Arrestata|Morta)\b", campi[ib]) else "M"
    nat = campi[ib] if re.match(r"Nat[oa]\b", campi[ib]) else ""
    dates = re.findall(r"\d\d/\d\d/\d{4}", nat)
    r["data_nascita"] = d2iso(dates[0]) if dates else ""
    m = re.search(r"\d{4}\s+a\s+(.+?)(?:\s+il\s+\d\d/|$)", nat)
    r["luogo_nascita"] = m.group(1).strip() if m else ""
    extra = dates[1:]
    arr = s["f_Arrestato"] or s["f_Arrestata"]
    mor = s["f_Morto"] or s["f_Morta"]
    r["luogo_arresto"] = ""; r["data_arresto"] = ""; r["luogo_morte"] = ""; r["data_morte"] = ""
    note = []
    if arr:
        m = re.match(r"a\s+(.+?)(?:\s+il\s+(\d\d/\d\d/\d{4}))?(?:\s+il\s+(\d\d/\d\d/\d{4}))?\s*$", arr)
        if m:
            r["luogo_arresto"] = m.group(1).strip()
            r["data_arresto"] = d2iso(m.group(2))
            if m.group(3):
                r["data_morte"] = d2iso(m.group(3))
                note.append("morte: solo data (luogo mancante nella scheda)")
        else:
            r["luogo_arresto"] = arr
    elif extra:
        r["data_arresto"] = d2iso(extra[0])
        note.append("arresto: solo data (luogo mancante nella scheda)")
        if len(extra) > 1:
            r["data_morte"] = d2iso(extra[1])
            note.append("morte: solo data (luogo mancante nella scheda)")
    if mor:
        m = re.match(r"a\s+(.+?)(?:\s+il\s+(\d\d/\d\d/\d{4}))?\s*$", mor)
        if m:
            r["luogo_morte"] = m.group(1).strip()
            r["data_morte"] = d2iso(m.group(2))
    r["categoria"] = {"persecuzione razziale": "razziale", "persecuzione politica": "politica", "internato militare italiano": "IMI"}.get(s["f_Motivo dell'arresto"], s["f_Motivo dell'arresto"])
    r["anno_posa"] = int(s["f_Anno di posa della pietra"])
    r["detenzione"] = s["f_Detenzione"]; r["deportazione"] = s["f_Deportazione"]; r["trasporto"] = s["f_Trasporto"]
    r["indirizzo"] = s["f_Pietra in"]; r["richiesta_da"] = s["f_Richiesta da"]
    r["lon"], r["lat"] = float(s.lon), float(s.lat)
    r["bio_scioper"], r["bio_cibeno"] = int(s.bio_scioper), int(s.bio_cibeno)
    r["note_scheda"] = "; ".join(note)
    recs.append(r)
C = pd.DataFrame(recs)
log["schede_comitato"] = len(C)

# ---------- Wikipedia (riempimento dei gruppi di celle unite)
W = pd.read_csv(os.path.join(pul, "wikipedia_pdi.csv"), sep=";", dtype=str, keep_default_na=False)
lu_unito = (W.luogo == "unito").values
for c in ["data_posa", "luogo", "lat", "lon"]:
    last = ""; out = []
    for v, lu in zip(W[c], lu_unito):
        fill = (v == "unito") if c in ("data_posa", "luogo") else lu
        v2 = last if fill else v
        if not fill:
            last = v
        out.append(v2)
    W[c] = out


def wname(sc):
    t = re.sub(r"\s*/\s*", " ", re.sub(r"<[^>]+>", "/", sc))
    t = re.sub(r"^\s*QUI\s+\w+\s*", "", t)
    return re.split(r"\s(NAT[OA]|ARRESTAT[OA])\b", t)[0]


def wdate(s):
    m = re.match(r"(\d+)\S?\s+(\w+)\s+(\d{4})", s or "")
    if m and m.group(2).lower() in MESI:
        return f"{m.group(3)}-{MESI[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return ""


W["nome_w"] = W.scritta.map(wname)
W["data_posa_iso"] = W.data_posa.map(wdate)
W["tok"] = W.nome_w.map(lambda s: frozenset(norm(s)))
W["usata"] = False
match = []
for i, r in C.iterrows():
    t = frozenset(norm(r.nome_proprio + " " + r.cognome))
    free = [j for j in W.index if not W.usata[j]]
    cand = [j for j in free if W.tok[j] == t]
    how = "nome uguale"
    if not cand:
        cand = [j for j in free if (t <= W.tok[j] or W.tok[j] <= t) and len(W.tok[j] & t) >= 2]
        how = "nome incluso"
    if len(cand) > 1:
        c2 = [j for j in cand if W.data_posa_iso[j][:4] == str(r.anno_posa)]
        if c2:
            cand = c2
    if not cand:
        sc = {j: difflib.SequenceMatcher(None, " ".join(sorted(W.tok[j])), " ".join(sorted(t))).ratio() for j in free}
        jb = max(sc, key=sc.get) if sc else None
        if jb is not None and sc[jb] >= .85:
            cand = [jb]; how = f"nome simile ({sc[jb]:.2f})"
    if cand:
        j = cand[0]
        W.loc[j, "usata"] = True
        match.append((j, how))
    else:
        match.append((None, "nessuno"))
C["wiki_idx"] = [m[0] for m in match]
C["wiki_match"] = [m[1] for m in match]
log["match_wikipedia"] = C.wiki_match.value_counts().to_dict()
log["wikipedia_righe"] = len(W)
log["wikipedia_non_abbinate"] = [W.nome_w[j] + " | " + W.data_posa_iso[j] + " | " + W.luogo[j] for j in W.index if not W.usata[j]]
log["comitato_non_abbinate"] = [r.nome_proprio + " " + r.cognome for _, r in C.iterrows() if r.wiki_match == "nessuno"]


def wget(j, col):
    return W[col][j] if j is not None and not pd.isna(j) else ""


C["data_posa"] = [wget(j, "data_posa_iso") for j in C.wiki_idx]
C["scritta_wikipedia"] = [wget(j, "scritta") for j in C.wiki_idx]
C["municipio"] = [wget(j, "municipio_wiki") for j in C.wiki_idx]


def hav(lo1, la1, lo2, la2):
    p = math.pi / 180
    a = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


dist = []
for i, r in C.iterrows():
    j = r.wiki_idx
    if j is None or pd.isna(j) or W.lat[j] == "":
        dist.append(np.nan)
    else:
        dist.append(hav(r.lon, r.lat, float(W.lon[j]), float(W.lat[j])))
C["dist_wiki_m"] = dist
C["anno_posa_wiki"] = [int(wget(j, "data_posa_iso")[:4]) if wget(j, "data_posa_iso") else np.nan for j in C.wiki_idx]
log["anno_posa_comitato_vs_wikipedia_diversi"] = int(((C.anno_posa_wiki.notna()) & (C.anno_posa_wiki != C.anno_posa)).sum())
log["dist_comitato_wikipedia_m"] = {"n": int(C.dist_wiki_m.notna().sum()), "mediana": float(C.dist_wiki_m.median()), "p95": float(C.dist_wiki_m.quantile(.95)),
                                    "oltre_100m": int((C.dist_wiki_m > 100).sum()), "oltre_300m": int((C.dist_wiki_m > 300).sum())}


def wfate(sc):
    m = re.search(r"(ASSASSINAT[OA]|DECEDUT[OA])", sc or "")
    return m.group(1)[:3] if m else ""


C["esito_wikipedia"] = [{"ASS": "assassinato/a", "DEC": "deceduto/a", "": ""}[wfate(x)] for x in C.scritta_wikipedia]

# ---------- campi derivati
C["anno_nascita"] = C.data_nascita.str[:4]


def eta(a, b):
    try:
        return int((pd.Timestamp(b) - pd.Timestamp(a)).days // 365.2425)
    except Exception:
        return np.nan


C["eta_arresto"] = [eta(a, b) if a and b else np.nan for a, b in zip(C.data_nascita, C.data_arresto)]
C["eta_morte"] = [eta(a, b) if a and b else np.nan for a, b in zip(C.data_nascita, C.data_morte)]
CAMPI = [("cibeno", "Fossoli (Poligono di Cibeno)"), ("auschwitz", "Auschwitz"), ("birkenau", "Auschwitz"), ("mauthausen", "Mauthausen e sottocampi"),
         ("gusen", "Mauthausen e sottocampi"), ("ebensee", "Mauthausen e sottocampi"), ("hartheim", "Mauthausen e sottocampi"), ("melk", "Mauthausen e sottocampi"),
         ("linz", "Mauthausen e sottocampi"), ("steyr", "Mauthausen e sottocampi"), ("gross", "Gross-Rosen"), ("dachau", "Dachau e sottocampi"),
         ("berlingen", "Dachau e sottocampi"), ("buchenwald", "Buchenwald e sottocampi"), ("flossenb", "Flossenburg e sottocampi"), ("hersbruck", "Flossenburg e sottocampi"),
         ("bergen", "Bergen-Belsen"), ("ravensbr", "Ravensbruck"), ("sachsenhausen", "Sachsenhausen"), ("neuengamme", "Neuengamme e sottocampi"),
         ("mittelbau", "Mittelbau-Dora"), ("dora", "Mittelbau-Dora"), ("natzweiler", "Natzweiler"), ("bolzano", "Bolzano"), ("fossoli", "Fossoli"),
         ("risiera", "Risiera di San Sabba"), ("theresienstadt", "Theresienstadt")]


def campo(x):
    x = (x or "").lower()
    for k, v in CAMPI:
        if k in x:
            return v
    return "altro" if x else "non indicato"


last_depo = [(d.split(",")[-1].strip() if d else "") for d in C.deportazione]
C["luogo_ultimo_deportazione"] = last_depo
C["campo_gruppo"] = [campo(m) if m else campo(l) for m, l in zip(C.luogo_morte, last_depo)]
C["esito"] = ["morto/a" if (m or d) else ("morto/a (solo da Wikipedia)" if e else "non indicato nella scheda")
              for m, d, e in zip(C.luogo_morte, C.data_morte, C.esito_wikipedia)]


def sotto(r):
    if "cibeno" in (r.luogo_morte or "").lower():
        return "strage di Cibeno (Fossoli, 12/7/1944)"
    if r.categoria == "politica" and (r.data_arresto or "")[:7] == "1944-03":
        return "arrestato a marzo 1944 (scioperi, probabile)" + (" - la scheda cita lo sciopero" if r.bio_scioper else "")
    return ""


C["sottogruppo"] = C.apply(sotto, axis=1)

# ---------- civici (controllo indirizzo / coordinate)
cf = os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "civici", "estratto", "ds634_civici_coordinategeografiche_20261001_final.csv")
cv = pd.read_csv(cf, sep=";", dtype=str, keep_default_na=False)
cv = cv[cv.STATOCIVICO == "Applicato"].copy()
cv["lon"] = cv.LONG_WGS84.astype(float)
cv["lat"] = cv.LAT_WGS84.astype(float)
PART = {"di", "del", "della", "dei", "delle", "degli", "de", "da", "d", "il", "la", "lo", "l", "e", "dell", "dello", "san", "s"}


def key_tokens(s):
    return frozenset(t for t in norm(s) if t not in PART)


cv["tipo_n"] = cv.TIPO.str.lower()
cv["name_set"] = cv.DESCRITTIVO.map(key_tokens)
cv["num"] = (cv.NUMERO.str.lstrip("0") + cv.LETTERA.str.lower()).str.strip()
streets = cv.drop_duplicates(["tipo_n", "name_set"])[["tipo_n", "name_set", "DESCRITTIVO"]].reset_index(drop=True)
ADDR = re.compile(r"(?i)^(via privata|viale|via|piazzale|piazza|piazzetta|corso|largo|alzaia|vicolo|galleria|ripa|bastioni|foro|strada|passaggio)\s+(.*?)[, ]+\s*(\d+\s*[a-zA-Z]?)(?:[ /].*)?$")


def addr_parse(a):
    m = ADDR.match(re.sub(r"\s+", " ", a.strip()))
    return (m.group(1).lower(), m.group(2), m.group(3).replace(" ", "").lower()) if m else None


def abbrev_ok(ks, ns):
    return bool(ks) and all(any(t == u or (len(t) == 1 and u.startswith(t)) for u in ns) for t in ks)


res = []
for a in C.indirizzo:
    p = addr_parse(a)
    if not p:
        res.append((None, None, "indirizzo non interpretato"))
        continue
    tipo, nome, num = p
    ks = key_tokens(nome)
    cand = streets[streets.tipo_n == tipo]
    if cand[cand.name_set == ks].empty and cand.empty is False and streets[streets.name_set == ks].shape[0] == 1:
        tipo = streets[streets.name_set == ks].tipo_n.iloc[0]
        cand = streets[streets.tipo_n == tipo]
    best = cand[cand.name_set == ks]
    how = "via esatta"
    if best.empty:
        best = cand[cand.name_set.map(lambda ns: abbrev_ok(ks, ns))]
        how = "via per iniziali/sottoinsieme"
    if best.empty:
        sc = cand.DESCRITTIVO.map(lambda x: difflib.SequenceMatcher(None, " ".join(sorted(key_tokens(x))), " ".join(sorted(ks))).ratio())
        if len(sc) and sc.max() >= .85:
            best = cand.loc[[sc.idxmax()]]
            how = "via simile"
    if best.empty:
        res.append((None, None, "via non trovata"))
        continue
    sel = cv[(cv.tipo_n == tipo) & (cv.name_set.isin(best.name_set))]
    hit = sel[sel.num == num]
    if hit.empty:
        res.append((None, None, f"civico non trovato ({how})"))
        continue
    res.append(((hit.lon.median(), hit.lat.median()), len(hit), how))
C["civico_lon"] = [r[0][0] if r[0] else np.nan for r in res]
C["civico_lat"] = [r[0][1] if r[0] else np.nan for r in res]
C["civico_stato"] = [r[2] for r in res]
C["dist_civico_m"] = [hav(a, b, c, d) if not pd.isna(c) else np.nan for a, b, c, d in zip(C.lon, C.lat, C.civico_lon, C.civico_lat)]
log["civici_abbinati"] = int(C.civico_lon.notna().sum())
log["civici_stati"] = C.civico_stato.value_counts().to_dict()
log["dist_comitato_civico_m"] = {"mediana": float(C.dist_civico_m.median()), "p90": float(C.dist_civico_m.quantile(.9)),
                                 "oltre_100m": int((C.dist_civico_m > 100).sum()), "oltre_300m": int((C.dist_civico_m > 300).sum())}
C["fonte_coord"] = "Comitato (mappa del sito)"
miss = C.lon.isna() | C.lat.isna()
C.loc[miss, "lon"] = C.civico_lon[miss]
C.loc[miss, "lat"] = C.civico_lat[miss]
C.loc[miss, "fonte_coord"] = "civici Comune"
log["coord_da_civici"] = int(miss.sum())
dwc = []
for i, r in C.iterrows():
    j = r.wiki_idx
    if j is None or pd.isna(j) or W.lat[j] == "" or pd.isna(r.civico_lon):
        dwc.append(np.nan)
    else:
        dwc.append(hav(float(W.lon[j]), float(W.lat[j]), r.civico_lon, r.civico_lat))
C["dist_wiki_civico_m"] = dwc
log["coord_a_oltre_300m_dal_civico"] = C.loc[C.dist_civico_m > 300, ["id_scheda", "cognome", "indirizzo", "dist_civico_m", "dist_wiki_m", "dist_wiki_civico_m"]].round(0).to_dict("records")
# regola: se la mappa del Comitato e' a >300 m dal civico, e Wikipedia e civico si accordano (<100 m) fra loro, si usa il civico
fix = (C.dist_civico_m > 300) & (C.dist_wiki_civico_m < 100)
log["coord_corrette_con_civico"] = C.loc[fix, ["id_scheda", "cognome", "indirizzo", "dist_civico_m"]].round(0).to_dict("records")
C.loc[fix, "lon"] = C.civico_lon[fix]
C.loc[fix, "lat"] = C.civico_lat[fix]
C.loc[fix, "fonte_coord"] = "civici Comune (la mappa del Comitato era lontana, Wikipedia concorda col civico)"

# anno di posa: data esatta di Wikipedia se c'e'; altrimenti l'anno del Comitato. Conflitti segnalati
C["anno_posa_comitato"] = C.anno_posa
C["anno_posa_conflitto"] = ((C.anno_posa_wiki.notna()) & (C.anno_posa_wiki != C.anno_posa)).astype(int)
cib = C.sottogruppo.str.startswith("strage di Cibeno")
usa_wiki = C.anno_posa_wiki.notna() & ((C.anno_posa_conflitto == 0) | cib)
C["anno_posa"] = [int(w) if u else int(a) for u, w, a in zip(usa_wiki, C.anno_posa_wiki, C.anno_posa_comitato)]
C["fonte_anno_posa"] = ["Wikipedia (data esatta; per Cibeno anche contro il Comitato)" if u else "Comitato (solo anno)" for u in usa_wiki]
# conflitto non-Cibeno: la data di Wikipedia (celle unite, fragile) non si usa
C.loc[(C.anno_posa_conflitto == 1) & ~cib, "data_posa"] = ""
C.loc[(C.anno_posa_conflitto == 1) & ~cib, "note_scheda"] = C.note_scheda + "; anno posa in conflitto con Wikipedia: da verificare"
# verifica fatta il 1/11/2026 con stampa e altre fonti (vedi NOTE, sezione 7): anno, data (se nota), stato, fonte
RISOLTI = {
    113: (2019, "", "verificato", "Elenco 2019 (citydoormilano.it, che riprende il Comitato); totali cumulati 62 nel 2019 e 90 dopo le 28 pietre del gennaio 2020 (Mosaico)"),
    119: (2019, "", "verificato", "Elenco 2019 (citydoormilano.it, pietredinciampo.eu); totali cumulati 62 e 90 come sopra"),
    137: (2025, "2025-01-23", "verificato", "AGI e Mentelocale del 23/1/2025 (la pietra di via Zumbini 39 e' posata quel giorno) e Wikipedia"),
    201: (2025, "2025-03-13", "annunciato", "Mentelocale (gennaio 2025) annuncia la posa del 13/3/2025 in via Gadames 119; Wikipedia cita il Comune; il Comitato scrive 2026"),
    45: (2023, "", "da verificare", "Il Comitato scrive 2023 (coerente con le 171 pietre 2017-2023 di Sky TG24); Wikipedia scrive 25/1/2024; nessuna fonte di stampa trovata"),
}
C["anno_posa_stato"] = ""
C["anno_posa_fonte_verifica"] = ""
for sid, (yy, dd, stato, fonte) in RISOLTI.items():
    k = C.index[C.id_scheda == sid]
    assert len(k) == 1, sid
    k = k[0]
    C.loc[k, "anno_posa"] = yy
    C.loc[k, "data_posa"] = dd
    C.loc[k, "anno_posa_stato"] = stato
    C.loc[k, "anno_posa_fonte_verifica"] = fonte
    C.loc[k, "fonte_anno_posa"] = "verifica: " + fonte
    C.loc[k, "note_scheda"] = (C.note_scheda[k].replace("; anno posa in conflitto con Wikipedia: da verificare", "") + f"; anno posa {stato}").strip("; ")
cibm = C.sottogruppo.str.startswith("strage di Cibeno")
C.loc[cibm & (C.anno_posa_conflitto == 1), "anno_posa_stato"] = "Wikipedia (Fondazione Fossoli) contro il Comitato"
log["anno_posa_risolti"] = {str(k): [v[0], v[2]] for k, v in RISOLTI.items()}
log["anno_posa_conflitti_non_cibeno"] = C.loc[(C.anno_posa_conflitto == 1) & ~cib, ["id_scheda", "cognome", "anno_posa_comitato", "anno_posa_wiki"]].to_dict("records")

# ---------- NIL
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
names = [f["properties"]["NIL"] for f in g["features"]]
tree = STRtree(polys)
pi, gi = tree.query(shapely.points(C.lon.values, C.lat.values), predicate="within")
nil = np.full(len(C), -1)
for a, b in zip(pi, gi):
    nil[a] = b
log["nil_fuori_da_ogni_poligono"] = int((nil < 0).sum())
if (nil < 0).any():
    tr = Transformer.from_crs(4326, 32632, always_xy=True)
    pm = [shapely.transform(p, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for p in polys]
    st = STRtree(pm)
    for k in np.where(nil < 0)[0]:
        x, y = tr.transform(C.lon[k], C.lat[k])
        j, d = st.query_nearest(shapely.points(x, y), return_distance=True)
        log.setdefault("nil_fuori_dettaglio", []).append([int(C.id_scheda[k]), C.indirizzo[k], float(d[0])])
        if d[0] <= 100:
            nil[k] = int(j[0])
C["id_nil"] = [ids[i] if i >= 0 else np.nan for i in nil]
C["nil"] = [names[i] if i >= 0 else "" for i in nil]
ok = C.civico_lon.notna().values
nilc = np.full(len(C), -1)
if ok.any():
    pi2, gi2 = tree.query(shapely.points(C.civico_lon[ok].values, C.civico_lat[ok].values), predicate="within")
    idx_ok = np.where(ok)[0]
    for a, b in zip(pi2, gi2):
        nilc[idx_ok[a]] = b
C["id_nil_civico"] = [ids[i] if i >= 0 else np.nan for i in nilc]
log["nil_punto_vs_nil_civico_diversi"] = int(((C.id_nil_civico.notna()) & (C.id_nil != C.id_nil_civico)).sum())

C["nome"] = C.nome_proprio + " " + C.cognome
C["fonte"] = "Comitato Pietre d'inciampo Milano (scheda " + C.id_scheda.astype(str) + "); data posa e controllo: it.wikipedia; civici: Comune di Milano ds634"
C["anno_posa_comitato"] = C.anno_posa_comitato.astype(int)
# pietre presenti solo su Wikipedia (non hanno scheda nel Comitato): le 3 per poliziotti della Questura (28/1/2025) e simili
extra = []
for j in W.index:
    if not W.usata[j]:
        lu = re.sub(r"<[^>]+>", " ", W.luogo[j]).strip()
        nm = re.sub(r"^IN SERVIZIO\s+", "", W.nome_w[j]).title()
        r = {"id_scheda": "", "nome": nm, "categoria": "altro (solo Wikipedia)", "indirizzo": lu, "municipio": W.municipio_wiki[j], "data_posa": W.data_posa_iso[j],
             "anno_posa": int(W.data_posa_iso[j][:4]) if W.data_posa_iso[j] else np.nan, "lon": float(W.lon[j]) if W.lon[j] else np.nan, "lat": float(W.lat[j]) if W.lat[j] else np.nan,
             "fonte_coord": "Wikipedia", "scritta_wikipedia": W.scritta[j], "fonte": "it.wikipedia (nessuna scheda nel Comitato)", "anno_posa_comitato": np.nan}
        extra.append(r)
log["righe_solo_wikipedia"] = [e["nome"] + " | " + e["indirizzo"] for e in extra]
if extra:
    E = pd.DataFrame(extra)
    ok2 = E.lon.notna()
    pe, ge = tree.query(shapely.points(E.lon[ok2].values, E.lat[ok2].values), predicate="within")
    ne = {ok2[ok2].index[a]: b for a, b in zip(pe, ge)}
    E["id_nil"] = [ids[ne[k]] if k in ne else np.nan for k in E.index]
    E["nil"] = [names[ne[k]] if k in ne else "" for k in E.index]
    C = pd.concat([C, E], ignore_index=True)
for c_ in ["anno_posa", "anno_posa_comitato", "id_nil", "id_nil_civico", "eta_arresto", "eta_morte"]:
    C[c_] = C[c_].astype("Int64")
C["anno_posa_conflitto"] = C.anno_posa_conflitto.fillna(0).astype(int)
C["solo_wikipedia"] = (C.categoria == "altro (solo Wikipedia)").astype(int)
cols = ["id_scheda", "nome", "cognome", "nome_proprio", "sesso", "anno_nascita", "data_nascita", "luogo_nascita", "data_arresto", "luogo_arresto", "eta_arresto",
        "categoria", "sottogruppo", "detenzione", "deportazione", "trasporto", "luogo_morte", "data_morte", "eta_morte", "campo_gruppo", "esito", "indirizzo",
        "municipio", "lon", "lat", "fonte_coord", "id_nil", "nil", "anno_posa", "anno_posa_comitato", "anno_posa_conflitto", "anno_posa_stato", "anno_posa_fonte_verifica", "fonte_anno_posa", "solo_wikipedia", "data_posa", "richiesta_da", "note_scheda", "wiki_match", "dist_wiki_m",
        "civico_stato", "dist_civico_m", "id_nil_civico", "esito_wikipedia", "fonte"]
C[cols].round({"lon": 6, "lat": 6, "dist_wiki_m": 0, "dist_civico_m": 0}).to_csv(os.path.join(pul, "pietre.csv"), sep=";", index=False, encoding="utf-8")
W.drop(columns=["tok"]).to_csv(os.path.join(pul, "wikipedia_pdi_riempito.csv"), sep=";", index=False)
json.dump(log, open(os.path.join(pul, "build_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, ensure_ascii=False, indent=1, default=str)[:7000])
