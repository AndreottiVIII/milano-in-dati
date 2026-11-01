"""Scrive i file dati della pagina "Chi governa Milano" (docs/amministratori/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <amministratori_dir> <docs_dir>

Legge (fase 1): amministratori/pulito/{serie_temporali.csv, ricambio.csv, milano_mandati.csv, milano_ricambio_dettaglio.csv, milano_liste.csv,
  titoli_professioni.csv, sindaci_milano.csv, milano_in_carica.csv, grandi_citta_in_carica.csv, comuni_ruoli.csv.gz, riepilogo.json}
Scrive in <docs_dir>/amministratori/data/: riepilogo.json, serie.json, sindaci_milano.csv, milano_in_carica.csv, serie_temporali.csv,
  ricambio.csv, professioni_2007.csv, sindaci_grandi_citta_oggi.csv
Dati pubblicati: aggregati; l'elenco di Milano "in carica" ha nome, ruolo, lista, sesso, FASCIA di eta', titolo di studio e categoria di
professione (come nel file del Ministero), SENZA data ne' luogo di nascita. Nessun dato dei comuni piccoli a livello di persona.
"""
import sys, os, json, csv
import pandas as pd, numpy as np

A, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(A, "pulito"); OUT = os.path.join(DOCS, "amministratori", "data"); os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")
def num(x, d=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)

RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
ser = pd.read_csv(os.path.join(PU, "serie_temporali.csv"))
ANNI = list(range(2007, 2026))
GRUPPI = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze", "Genova", "Palermo", "Bari", "Catania",
          "Grandi città (10)", "Comuni sopra 100.000 abitanti", "Tutta Italia (tutti i comuni)"]

# ------------------------------------------------------------ serie (per i grafici)
def serie(corpo, col, mask_col=None, mask_min=None):
    o = {}
    for g in GRUPPI:
        x = ser[(ser.gruppo == g) & (ser.corpo == corpo)].set_index("anno")
        v = []
        for a in ANNI:
            if a not in x.index or pd.isna(x.at[a, col]): v.append(None); continue
            if mask_col and (pd.isna(x.at[a, mask_col]) or x.at[a, mask_col] < mask_min): v.append(None); continue
            if x.at[a, "n"] < 5: v.append(None); continue
            v.append(num(x.at[a, col]))
        o[g] = v
    return o
S = {"anni": ANNI, "gruppi": GRUPPI,
     "consiglio": {"donne_pct": serie("consiglio", "donne_pct"), "eta_media": serie("consiglio", "eta_media"),
                   "under40_pct": serie("consiglio", "under40_pct"), "over60_pct": serie("consiglio", "over60_pct"),
                   "laurea_pct": serie("consiglio", "laurea_pct_dei_dichiarati", "titolo_dichiarato_pct", 70),
                   "titolo_dichiarato_pct": serie("consiglio", "titolo_dichiarato_pct")},
     "giunta": {"donne_pct": serie("giunta", "donne_pct"), "eta_media": serie("giunta", "eta_media"),
                "laurea_pct": serie("giunta", "laurea_pct_dei_dichiarati", "titolo_dichiarato_pct", 70),
                "esterni_pct": serie("giunta", "esterni_pct")},
     "n": {c: {g: [int(ser[(ser.gruppo == g) & (ser.corpo == c) & (ser.anno == a)].n.iloc[0]) if len(ser[(ser.gruppo == g) & (ser.corpo == c) & (ser.anno == a)]) else 0 for a in ANNI] for g in GRUPPI} for c in ("consiglio", "giunta")},
     "sindaci_donne_pct_italia": serie("sindaco", "donne_pct")["Tutta Italia (tutti i comuni)"],
     "sindaci_eta_media_italia": serie("sindaco", "eta_media")["Tutta Italia (tutti i comuni)"],
     "sindaci_n_italia": [int(ser[(ser.gruppo == "Tutta Italia (tutti i comuni)") & (ser.corpo == "sindaco") & (ser.anno == a)].n.iloc[0]) for a in ANNI]}
# quante sindache nelle 10 maggiori citta' ogni anno
t = pd.read_csv(os.path.join(PU, "comuni_ruoli.csv.gz"), dtype={"istat": str})
t["istat"] = t.istat.str.zfill(6)
GR = {"058091": "Roma", "015146": "Milano", "063049": "Napoli", "001272": "Torino", "082053": "Palermo", "010025": "Genova",
      "037006": "Bologna", "048017": "Firenze", "072006": "Bari", "087015": "Catania"}
sg = t[(t.ruolo == "sindaco") & t.istat.isin(GR)]
bc = []
for a in ANNI:
    x = sg[sg.anno == a]
    bc.append({"anno": a, "sindaci": len(x), "donne": int((x.sesso == "F").sum()), "citta_donne": sorted(GR[i] for i in x[x.sesso == "F"].istat)})
S["sindaci_grandi_citta"] = bc
json.dump(S, open(os.path.join(OUT, "serie.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------ sindaci di Milano
sm = pd.read_csv(os.path.join(PU, "sindaci_milano.csv"))
sm.to_csv(os.path.join(OUT, "sindaci_milano.csv"), index=False)
check("sindaci dal 1946", len(sm), 13)
check("sindache dal 1946", int((sm.sesso == "F").sum()), 1)

# ------------------------------------------------------------ Milano oggi
ic = pd.read_csv(os.path.join(PU, "milano_in_carica.csv"))
def fascia(e):
    if pd.isna(e): return "non nota"
    e = float(e)
    return "meno di 30" if e < 30 else "30-39" if e < 40 else "40-49" if e < 50 else "50-59" if e < 60 else "60-69" if e < 70 else "70 o più"
ic["fascia_eta"] = ic.eta.map(fascia)
ordine = {"sindaco": 0, "giunta": 1, "consiglio": 2}
ic["o"] = ic.ruolo.map(ordine)
ic["ruolo_it"] = ic.apply(lambda r: "Sindaco" if r.ruolo == "sindaco" else ("Giunta" if r.ruolo == "giunta" else "Consiglio comunale"), axis=1)
ic["dettaglio"] = ic.apply(lambda r: (r.incarico if isinstance(r.incarico, str) and r.incarico.strip() else r.carica), axis=1)
ic = ic.sort_values(["o", "cognome", "nome"])
def lista_breve(s):
    if not isinstance(s, str) or not s.strip(): return ""
    s = s.strip()
    return s if " | " not in s else "coalizione del sindaco (" + str(s.count(" | ") + 1) + " liste)"
pub = pd.DataFrame({"ruolo": ic.ruolo_it, "dettaglio": ic.dettaglio, "cognome": ic.cognome, "nome": ic.nome, "sesso": ic.sesso,
                    "fascia_eta": ic.fascia_eta, "lista": ic.lista.map(lista_breve), "titolo_di_studio": ic.titolo,
                    "professione_categoria": ic.prof_cat, "in_carica_dal": ic.inizio})
pub.to_csv(os.path.join(OUT, "milano_in_carica.csv"), index=False)
assert "anno_nascita" not in pub.columns and "eta" not in pub.columns

cons = ic[ic.ruolo == "consiglio"]; gi = ic[ic.ruolo == "giunta"]; sin = ic[ic.ruolo == "sindaco"]
chk = RIEP["milano_oggi"]
check("consiglio n", len(cons), chk["consiglio"]["n"]); check("giunta n", len(gi), chk["giunta"]["n"])
check("consiglio donne", int((cons.sesso == "F").sum()), chk["consiglio"]["donne"])
FASCE = ["meno di 30", "30-39", "40-49", "50-59", "60-69", "70 o più"]
def conta(x, col, ordine=None):
    v = x[col].value_counts()
    return [[k, int(v.get(k, 0))] for k in (ordine or list(v.index))]
liste = cons.lista.map(lambda s: s.strip() if isinstance(s, str) and s.strip() else "(non indicata)").value_counts()
OGGI = {
    "data": "2026-08-24",
    "sindaco": {"nome": f"{sin.iloc[0].nome} {sin.iloc[0].cognome}", "eta": int(sin.iloc[0].eta), "in_carica_dal": str(sin.iloc[0].inizio)[:10]},
    "consiglio": {"n": len(cons), "donne": int((cons.sesso == "F").sum()), "eta_media": num(cons.eta.mean()), "eta_mediana": num(cons.eta.median()),
                  "fasce": conta(cons, "fascia_eta", FASCE), "liste": [[k, int(v)] for k, v in liste.items()],
                  "titolo": conta(cons, "titolo", ["Laurea o più", "Diploma superiore", "Licenza media", "Elementare o nessun titolo"]),
                  "titolo_dichiarato": int(cons.titolo.notna().sum()), "prof_dichiarata": int(cons.prof_cat.notna().sum())},
    "giunta": {"n": len(gi), "donne": int((gi.sesso == "F").sum()), "eta_media": num(gi.eta.mean()), "fasce": conta(gi, "fascia_eta", FASCE),
               "titolo": conta(gi, "titolo", ["Laurea o più", "Diploma superiore", "Licenza media", "Elementare o nessun titolo"]),
               "titolo_dichiarato": int(gi.titolo.notna().sum()), "prof_dichiarata": int(gi.prof_cat.notna().sum())},
    "origine": "Ministero dell'Interno, DAIT, elenco amministratori comunali in carica al 24/8/2026 (ammcom.csv), comune di Milano"}
# sindaci delle 10 grandi citta' oggi
gc = pd.read_csv(os.path.join(PU, "grandi_citta_in_carica.csv"))
gs = gc[gc.ruolo == "sindaco"].copy()
gs["fascia_eta"] = gs.eta.map(fascia)
gs[["comune", "cognome", "nome", "sesso", "fascia_eta", "inizio"]].rename(columns={"comune": "citta", "inizio": "in_carica_dal"}).to_csv(
    os.path.join(OUT, "sindaci_grandi_citta_oggi.csv"), index=False)
OGGI["sindaci_grandi_citta"] = [[r.comune, f"{r.nome} {r.cognome}", r.sesso, int(r.eta)] for r in gs.itertuples()]
check("sindaci grandi citta'", len(gs), 10)
gg = gc[gc.ruolo == "giunta"].groupby("comune").agg(n=("sesso", "size"), donne=("sesso", lambda s: int((s == "F").sum())))
OGGI["giunte_grandi_citta"] = {k: [int(v.n), int(v.donne)] for k, v in gg.iterrows()}

# ------------------------------------------------------------ mandati, ricambio
mand = pd.read_csv(os.path.join(PU, "milano_mandati.csv"))
MAND = {}
for m in sorted(mand.mandato.unique()):
    x = mand[mand.mandato == m]
    MAND[int(m)] = {r.corpo: {"persone": int(r.persone_nel_mandato), "donne_pct": num(r.donne_pct_persone), "eta_media": num(r.eta_media_persone)} for r in x.itertuples()}
    MAND[int(m)]["prima_fotografia"] = int(x.prima_fotografia.iloc[0])
rc = pd.read_csv(os.path.join(PU, "ricambio.csv"))
rc.to_csv(os.path.join(OUT, "ricambio.csv"), index=False)
RIC = {g: {int(r.anno_elezione): {"persone": int(r.persone), "riconfermati": int(r.riconfermati), "pct": num(r.riconfermati_pct), "comuni": int(r.comuni)} for r in x.itertuples()}
       for g, x in rc.groupby("gruppo")}
rd = pd.read_csv(os.path.join(PU, "milano_ricambio_dettaglio.csv"))
RIC_MI = [{"mandato": int(r.mandato), "precedente": int(r.precedente), "corpo": r.corpo, "persone": int(r.persone), "riconfermati": int(r.riconfermati),
           "pct": num(r.riconfermati_pct), "precedente_completo": bool(r.precedente_completo)} for r in rd.itertuples()]
check("ricambio Milano 2021 (consiglio)", RIC["Milano"][2021]["pct"], [x for x in RIC_MI if x["mandato"] == 2021 and x["corpo"] == "consiglio"][0]["pct"], 0.05)

# ------------------------------------------------------------ professioni e titoli: snapshot 2007 (97-100% dichiarato) e Milano mandato 2006
tp = pd.read_csv(os.path.join(PU, "titoli_professioni.csv"))
def prof_2007():
    rows = []
    x = t[(t.anno == 2007) & (t.ruolo.isin(["consiglio", "giunta"]))].copy()
    from importlib import util
    for corpo in ("consiglio", "giunta"):
        for g, sub in (("Milano", x[x.istat == "015146"]), ("Grandi città (10)", x[x.istat.isin(GR)]),
                       ("Comuni sopra 100.000 abitanti", x[x["pop"] >= 100000]), ("Tutta Italia (tutti i comuni)", x)):
            sub = sub[sub.ruolo == corpo]
            v = sub.prof_cat.dropna()
            for k, n in v.value_counts().items():
                rows.append({"anno": 2007, "corpo": corpo, "gruppo": g, "categoria": k, "n": int(n), "pct_dei_dichiarati": round(100 * n / len(v), 1), "dichiarati": len(v), "persone": len(sub)})
    return pd.DataFrame(rows)
p7 = prof_2007(); p7.to_csv(os.path.join(OUT, "professioni_2007.csv"), index=False)
PROF = {c: {g: {"dichiarati": int(x.dichiarati.iloc[0]), "persone": int(x.persone.iloc[0]), "cat": [[r.categoria, r.pct_dei_dichiarati, int(r.n)] for r in x.sort_values("n", ascending=False).itertuples()]}
            for g, x in p7[p7.corpo == c].groupby("gruppo")} for c in ("consiglio", "giunta")}
# Milano: quota di consiglieri che dichiara la professione, per mandato (calo)
PROF_DICH = RIEP["milano_prof_dichiarata_pct_per_mandato"]; TIT_DICH = RIEP["milano_titolo_dichiarato_pct_per_mandato"]

# ------------------------------------------------------------ titoli di studio: Milano oggi vs 2007
# cifre per il testo
def v(g, c, a, col):
    r = ser[(ser.gruppo == g) & (ser.corpo == c) & (ser.anno == a)]
    return None if r.empty else num(r.iloc[0][col])

# ------------------------------------------------------------ riepilogo con origine
R = {
    "generato_da": "amministratori/scripts/pagina.py",
    "fonti": {
        "dait": "Ministero dell'Interno - Dipartimento per gli Affari Interni e Territoriali, Anagrafe degli amministratori locali e regionali: amministratori comunali in carica al 31 dicembre di ogni anno 2007-2025 e elenco in carica al 24 agosto 2026 (https://dait.interno.gov.it/elezioni/open-data). Licenza CC BY 4.0 (indicata dai cataloghi dati.gov.it e Comune di Milano che ripubblicano i file; la pagina del DAIT non la scrive).",
        "wikipedia": "Wikipedia italiana, voce 'Sindaci di Milano' (CC BY-SA 4.0): date dei mandati e partito",
        "wikidata": "Wikidata (CC0): anno di nascita e sesso dei sindaci"},
    "scaricato": "2026-11-01",
    "anni": ANNI,
    "oggi": OGGI,
    "persone_oggi": json.loads(pub.drop(columns=["in_carica_dal"]).fillna("").to_json(orient="records", force_ascii=False)),
    "sindaci": json.loads(sm.fillna("").to_json(orient="records", force_ascii=False)),
    "mandati": MAND,
    "ricambio": RIC, "ricambio_milano": RIC_MI,
    "professioni_2007": PROF,
    "professione_dichiarata_milano_consiglio_per_mandato": PROF_DICH, "titolo_dichiarato_milano_consiglio_per_mandato": TIT_DICH,
    "professione_dichiarata_italia_consiglio": {a: v("Tutta Italia (tutti i comuni)", "consiglio", a, "prof_dichiarata_pct") for a in (2007, 2013, 2019, 2025)},
    "citta_anno_incomplete": RIEP["citta_anno_incomplete"],
    "liste_milano": pd.read_csv(os.path.join(PU, "milano_liste.csv")).to_dict("records"),
    "cifre": {
        "giunta_donne_2010": {"n": int(ser[(ser.gruppo == "Milano") & (ser.corpo == "giunta") & (ser.anno == 2010)].n.iloc[0]),
                              "donne": int(ser[(ser.gruppo == "Milano") & (ser.corpo == "giunta") & (ser.anno == 2010)].n_donne.iloc[0]),
                              "pct": v("Milano", "giunta", 2010, "donne_pct")},
        "giunta_donne_2011": {"n": int(ser[(ser.gruppo == "Milano") & (ser.corpo == "giunta") & (ser.anno == 2011)].n.iloc[0]),
                              "donne": int(ser[(ser.gruppo == "Milano") & (ser.corpo == "giunta") & (ser.anno == 2011)].n_donne.iloc[0]),
                              "pct": v("Milano", "giunta", 2011, "donne_pct")},
        "consiglio_donne_milano": {a: v("Milano", "consiglio", a, "donne_pct") for a in (2007, 2012, 2016, 2025)},
        "consiglio_donne_italia": {a: v("Tutta Italia (tutti i comuni)", "consiglio", a, "donne_pct") for a in (2007, 2012, 2016, 2025)},
        "consiglio_donne_100k": {a: v("Comuni sopra 100.000 abitanti", "consiglio", a, "donne_pct") for a in (2007, 2012, 2016, 2025)},
        "consiglio_eta_milano": {a: v("Milano", "consiglio", a, "eta_media") for a in (2007, 2012, 2016, 2025)},
        "consiglio_eta_italia": {a: v("Tutta Italia (tutti i comuni)", "consiglio", a, "eta_media") for a in (2007, 2012, 2016, 2025)},
        "consiglio_laurea_milano": {a: v("Milano", "consiglio", a, "laurea_pct_dei_dichiarati") for a in (2007, 2012, 2016, 2025)},
        "consiglio_laurea_italia": {a: v("Tutta Italia (tutti i comuni)", "consiglio", a, "laurea_pct_dei_dichiarati") for a in (2007, 2012, 2016, 2025)},
        "consiglio_laurea_100k": {a: v("Comuni sopra 100.000 abitanti", "consiglio", a, "laurea_pct_dei_dichiarati") for a in (2007, 2012, 2016, 2025)},
        "consiglio_titolo_dichiarato_milano_2025": v("Milano", "consiglio", 2025, "titolo_dichiarato_pct"),
        "consiglio_titolo_dichiarato_italia_2025": v("Tutta Italia (tutti i comuni)", "consiglio", 2025, "titolo_dichiarato_pct"),
        "sindaci_donne_italia": {a: v("Tutta Italia (tutti i comuni)", "sindaco", a, "donne_pct") for a in (2007, 2016, 2025)},
        "giunta_esterni_milano_2025": v("Milano", "giunta", 2025, "esterni_pct"),
        "giunta_esterni_italia_2025": v("Tutta Italia (tutti i comuni)", "giunta", 2025, "esterni_pct"),
        "giunta_donne_italia_2025": v("Tutta Italia (tutti i comuni)", "giunta", 2025, "donne_pct"),
        "giunta_donne_100k_2025": v("Comuni sopra 100.000 abitanti", "giunta", 2025, "donne_pct"),
        "n_comuni_italia_2025": None,
    },
    "controlli_build": json.load(open(os.path.join(PU, "controlli_build.json"), encoding="utf8"))["per_anno"],
}
R["cifre"]["n_comuni_italia_2025"] = int(t[t.anno == 2025].istat.nunique())
R["cifre"]["n_comuni_100k_2025"] = int(t[(t.anno == 2025) & (t["pop"] >= 100000)].istat.nunique())
check("Milano consiglio donne 2025 (serie vs oggi, snapshot 31/12/2025 vs 24/8/2026)", R["cifre"]["consiglio_donne_milano"][2025] or 0, OGGI["consiglio"]["donne"] / OGGI["consiglio"]["n"] * 100, 5)
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)

# file csv di aggregati
ser.to_csv(os.path.join(OUT, "serie_temporali.csv"), index=False)
print("AVVISI:", AVVISI if AVVISI else "nessuno")
if AVVISI: sys.exit(1)
