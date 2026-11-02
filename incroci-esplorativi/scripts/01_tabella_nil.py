"""Costruisce la tabella ordinata per quartiere (NIL) e il dizionario delle colonne.
Uscite: out/nil_tabella.csv, out/nil_tabella_tutti.csv, out/dizionario.csv, out/nil_vicini.csv
Ogni variabile dichiara: fonte di origine (per riconoscere le coppie meccaniche), anno,
come è costruita (conteggio, CAP, zona OMI, modello, sezioni), denominatore, affidabilità, nota sui limiti.
Regola: i NIL sotto 3.000 residenti (2024) restano nel file _tutti ma non nell'analisi."""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*fragmented.*")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

from comune import OUT, SOGLIA_RESIDENTI, path, rd

g = json.load(open(path("docs", "quartiere", "data", "nil.geojson"), encoding="utf8"))
IDS = [f["properties"]["i"] for f in g["features"]]
NOMI = {f["properties"]["i"]: f["properties"]["n"] for f in g["features"]}
POL = {f["properties"]["i"]: shape(f["geometry"]).buffer(0) for f in g["features"]}
T = pd.DataFrame(index=sorted(IDS))
T.index.name = "id_nil"
T["nil"] = pd.Series(NOMI)
DIZ = []


def add(nome, s, tema, descr, fonte, campo, anno, fid, tipo="livello", costr="conteggio", den="", aff="alta", nota="", ctrl=False):
    """Aggiunge una colonna alla tabella e una riga al dizionario."""
    s = pd.to_numeric(pd.Series(s), errors="coerce")
    s.index = pd.to_numeric(s.index, errors="coerce")
    s = s[~s.index.duplicated()]
    T[nome] = s.reindex(T.index)
    DIZ.append(dict(variabile=nome, tema=tema, descrizione=descr, file=fonte, campo=campo, anno=anno, fonte_id=fid, tipo=tipo,
                    costruzione=costr, denominatore=den, affidabilita=aff, nota_limite=nota, controllo=int(ctrl)))


def col(rel, idc, c):
    d = rd(rel)
    return d.set_index(idc)[c]


# ---------- geografia e controlli
ana = rd("popolazione/pulito/nil_anagrafica.csv").set_index("id_nil")
T["municipio"] = ana["municipio_prevalente"].reindex(T.index)
cv = rd("docs/case-vuote/data/nil.csv").set_index("id_nil")
area = pd.Series({i: None for i in T.index}, dtype=float)
# centroide in coordinate metriche approssimate (Milano: 1 grado lon = 77,9 km; lat = 111,2 km)
D_LON, D_LAT = 9.1919, 45.4641
cent = {}
for i in T.index:
    c = POL[i].centroid
    cent[i] = (c.x, c.y)
    area[i] = POL[i].area * 77.9 * 111.2
T["lon"] = pd.Series({i: cent[i][0] for i in T.index})
T["lat"] = pd.Series({i: cent[i][1] for i in T.index})
add("area_km2", area, "Geografia", "Superficie dal poligono NIL", "docs/quartiere/data/nil.geojson", "geometria", "PGT 2030", "geo", costr="geometria", aff="alta", ctrl=True,
    nota="Calcolata sui poligoni perché il ds205 ha superfici scambiate per 3 NIL")
dist = pd.Series({i: (((cent[i][0] - D_LON) * 77.9) ** 2 + ((cent[i][1] - D_LAT) * 111.2) ** 2) ** 0.5 for i in T.index})
add("dist_duomo_km", dist, "Geografia", "Distanza in linea d'aria del centroide dal Duomo", "docs/quartiere/data/nil.geojson", "geometria", "PGT 2030", "geo", costr="geometria", ctrl=True)

eta = rd("popolazione/pulito/eta_nil_anno_indicatori.csv")
e25 = eta[eta.anno == 2025].set_index("id_nil")
e24 = eta[eta.anno == 2024].set_index("id_nil")
e14 = eta[eta.anno == 2014].set_index("id_nil")
e12 = eta[eta.anno == 2012].set_index("id_nil")
FE = "popolazione/pulito/eta_nil_anno_indicatori.csv"
add("residenti_2024", e24.residenti, "Chi ci abita", "Residenti anagrafe", FE, "residenti", 2024, "ds27", costr="conteggio", ctrl=True, nota="Anagrafe > ISTAT dal 2020 (+2,7% nel 2025)")
add("log_residenti", np.log(e24.residenti.clip(lower=1)), "Geografia", "Logaritmo dei residenti", FE, "residenti", 2024, "ds27", ctrl=True)
add("densita_kmq", e24.residenti / T["area_km2"], "Geografia", "Residenti per km2", FE, "residenti/area", 2024, "ds27", den="area", ctrl=True)
add("eta_media", e25.eta_media, "Chi ci abita", "Età media", FE, "eta_media", 2025, "ds27", ctrl=True, nota="Sotto 3.000 residenti oscilla (convivenze)")
add("q0_14", e25.q_0_14 * 100, "Chi ci abita", "% 0-14 anni", FE, "q_0_14", 2025, "ds27", den="residenti")
add("q65", e25.q_65p * 100, "Chi ci abita", "% 65+", FE, "q_65p", 2025, "ds27", den="residenti")
add("q80", e25.q_80p * 100, "Chi ci abita", "% 80+", FE, "q_80p", 2025, "ds27", den="residenti")
add("q20_34", e25.n_20_34 / e25.residenti * 100, "Chi ci abita", "% 20-34 anni", FE, "n_20_34/residenti", 2025, "ds27", den="residenti")
add("var_pop_14_25", (e25.residenti / e14.residenti - 1) * 100, "Chi ci abita", "Variazione residenti 2014-2025 %", FE, "residenti", "2014-2025", "ds27", tipo="variazione", nota="Salti di registro; grandi cantieri")
add("var_q20_34", e25.n_20_34 / e25.residenti * 100 - e14.n_20_34 / e14.residenti * 100, "Chi ci abita", "Variazione punti % 20-34", FE, "n_20_34", "2014-2025", "ds27", tipo="variazione")
add("var_eta_media", e25.eta_media - e14.eta_media, "Chi ci abita", "Variazione età media", FE, "eta_media", "2014-2025", "ds27", tipo="variazione")
add("var_q0_14", (e25.q_0_14 - e14.q_0_14) * 100, "Chi ci abita", "Variazione punti % 0-14", FE, "q_0_14", "2014-2025", "ds27", tipo="variazione")
cn = rd("popolazione/pulito/cittadinanze_nil_indicatori.csv")
c25 = cn[cn.anno == 2025].set_index("id_nil")
c14 = cn[cn.anno == 2014].set_index("id_nil")
FC = "popolazione/pulito/cittadinanze_nil_indicatori.csv"
add("q_stranieri", c25.quota_stranieri * (100 if c25.quota_stranieri.max() <= 1 else 1), "Chi ci abita", "% cittadinanza non italiana", FC, "quota_stranieri", 2025, "ds27_cit", den="residenti",
    nota="Cittadinanza non è origine; registro > ISTAT di 10% sugli stranieri. Usata solo come controllo o con parole neutre")
add("var_q_stranieri", (c25.quota_stranieri - c14.quota_stranieri) * (100 if c25.quota_stranieri.max() <= 1 else 1), "Chi ci abita", "Variazione punti % cittadinanza non italiana", FC, "quota_stranieri", "2014-2025", "ds27_cit", tipo="variazione")
add("n_eff_cittadinanze", c25.n_effettivo, "Chi ci abita", "Numero effettivo di cittadinanze (diversità)", FC, "n_effettivo", 2025, "ds27_cit")

# ---------- censimento permanente
ce = rd("censimenti/pulito/indicatori_NIL.csv")
c23 = ce[ce.anno == 2023].set_index("nil")
c11 = ce[ce.anno == 2011].set_index("nil")
c91 = ce[ce.anno == 1991].set_index("nil")
FI = "censimenti/pulito/indicatori_NIL.csv"
NC = "Censimento permanente: stime da registri e campioni, confronto col 2011 cauto"
add("laureati", c23.quota_laureati_su_base, "Istruzione", "% laureati su residenti 9+", FI, "quota_laureati_su_base", 2023, "censimento", den="residenti", costr="sezioni censuarie", nota=NC, ctrl=True)
add("famiglie_sole", c23.quota_famiglie_1_comp, "Chi ci abita", "% famiglie di una persona", FI, "quota_famiglie_1_comp", 2023, "censimento", costr="sezioni censuarie", nota=NC)
add("famiglia_media", c23.famiglie_comp_medio_esatto.fillna(c23.famiglie_comp_medio_approx), "Chi ci abita", "Componenti per famiglia", FI, "famiglie_comp_medio", 2023, "censimento", costr="sezioni censuarie", nota=NC)
add("case_non_occ", c23.quota_abit_non_occ_da_residenti, "Casa", "% abitazioni non occupate da residenti", FI, "quota_abit_non_occ_da_residenti", 2023, "censimento", den="abitazioni", costr="sezioni censuarie", nota="Cambio di metodo 2021 (catasto): 2011 e 2021 non si confrontano", aff="media")
add("case_non_occ_2011", c11.quota_abit_non_occ_da_residenti, "Casa", "% abitazioni non occupate da residenti", FI, "quota_abit_non_occ_da_residenti", 2011, "censimento", den="abitazioni", costr="sezioni censuarie", aff="media")
add("laureati_1991", c91.quota_laureati_su_base, "Istruzione", "% laureati su base 1991", FI, "quota_laureati_su_base", 1991, "censimento_storico", costr="sezioni censuarie", aff="media", nota="Confini 1991 riportati ai NIL per sovrapposizione")
add("var_pop_91_11", (c11["pop"] / c91["pop"] - 1) * 100, "Chi ci abita", "Variazione residenti 1991-2011 %", FI, "pop", "1991-2011", "censimento_storico", tipo="variazione", aff="media", nota="NIL ricostruiti")
add("var_laureati_91_23", c23.quota_laureati_su_residenti - c91.quota_laureati_su_residenti, "Istruzione", "Variazione punti laureati su residenti 1991-2023", FI, "quota_laureati_su_residenti", "1991-2023", "censimento_storico", tipo="variazione", aff="media", nota=NC)

# ---------- lavoro
lv = rd("docs/lavoro/data/nil_lavoro.csv")
l23 = lv[lv.anno == 2023].set_index("nil")
l11 = lv[lv.anno == 2011].set_index("nil")
FL = "docs/lavoro/data/nil_lavoro.csv"
NL = "2021-2023 è una serie a parte: mai confrontare NIL per NIL col 2011"
add("tasso_occ", l23.tasso_occ, "Lavoro", "Tasso di occupazione 15-64", FL, "tasso_occ", 2023, "censimento", costr="sezioni censuarie", nota=NL)
add("gap_occ_mf", l23.gap_occ_mf, "Lavoro", "Divario occupazione uomini-donne (punti)", FL, "gap_occ_mf", 2023, "censimento", costr="sezioni censuarie", nota=NL)
add("disocc_2011", l11.tasso_disocc, "Lavoro", "Tasso di disoccupazione", FL, "tasso_disocc", 2011, "censimento_storico", costr="sezioni censuarie")
add("studenti_2011", l11.studenti_100, "Lavoro", "Studenti ogni 100 residenti 15+", FL, "studenti_100", 2011, "censimento_storico", costr="sezioni censuarie")

# ---------- redditi, prezzi (CAP, OMI)
qi = rd("quartieri-che-cambiano/out/indicatori_nil.csv").set_index("id_nil")
FQ = "quartieri-che-cambiano/out/indicatori_nil.csv"
NCAP = "Da CAP (38 zone) ai NIL: NIL vicini condividono il valore; è del contribuente, non del residente; 20121/20122 instabili"
NOMI2 = "Zona OMI portata al NIL: stima dell'Agenzia, non prezzo di vendita; NIL vicini condividono il valore; salto 2023-24"
add("reddito", qi.reddito_2024, "Soldi", "Reddito medio per contribuente", FQ, "reddito_2024", 2024, "mef_cap", costr="CAP", aff="media", nota=NCAP, ctrl=True)
add("var_reddito", qi.reddito_var, "Soldi", "Variazione reale reddito 2011-2024 (%)", FQ, "reddito_var", "2011-2024", "mef_cap", tipo="variazione", costr="CAP", aff="media", nota=NCAP + "; Duomo, Brera, Guastalla, P.Vigentina esclusi")
add("prezzo", qi.prezzo_2026_reale, "Soldi", "Prezzo vendita abitazioni civili EUR/m2", FQ, "prezzo_2026_reale", "2026-1", "omi", costr="zona OMI", aff="media", nota=NOMI2, ctrl=True)
add("var_prezzo", qi.prezzo_var, "Soldi", "Variazione reale prezzo 2014-2026 (%)", FQ, "prezzo_var", "2014-2026", "omi", tipo="variazione", costr="zona OMI", aff="media", nota=NOMI2)
add("affitto", qi.affitto_2026_reale, "Soldi", "Affitto OMI EUR/m2 mese", FQ, "affitto_2026_reale", "2026-1", "omi", costr="zona OMI", aff="media", nota=NOMI2)
add("var_affitto", qi.affitto_var, "Soldi", "Variazione reale affitto 2014-2026 (%)", FQ, "affitto_var", "2014-2026", "omi", tipo="variazione", costr="zona OMI", aff="media", nota=NOMI2)
add("rendimento_lordo", qi.affitto_2026_reale * 12 / qi.prezzo_2026_reale * 100, "Soldi", "Affitto annuo su prezzo (%)", FQ, "affitto_2026_reale,prezzo_2026_reale", "2026-1", "omi", costr="zona OMI", aff="media", nota=NOMI2)
dr = rd("divisa/out/reddito_nil_milano.csv")
d24 = dr[dr.anno == dr.anno.max()].set_index("id_nil")
add("quota_alti", d24.alto, "Soldi", "Quota contribuenti oltre la fascia alta (CAP)", "divisa/out/reddito_nil_milano.csv", "alto", int(dr.anno.max()), "mef_cap", costr="CAP", aff="media", nota=NCAP)
add("quota_bassi", d24.basso, "Soldi", "Quota contribuenti in fascia bassa (CAP)", "divisa/out/reddito_nil_milano.csv", "basso", int(dr.anno.max()), "mef_cap", costr="CAP", aff="media", nota=NCAP)

# ---------- nascite
na = rd("docs/nascite/data/nil_2022_2024.csv").set_index("id_nil")
FN = "docs/nascite/data/nil_2022_2024.csv"
add("nati_x1000_donne", na.nati_per_1000_donne_15_49_2022_2024, "Nascite", "Nati ogni 1.000 donne 15-49", FN, "nati_per_1000_donne_15_49_2022_2024", "2022-24", "ds_nati", den="donne 15-49", nota="Non standardizzato per età delle donne")
add("var_nati_x1000", na.nati_per_1000_donne_15_49_2022_2024 / na.nati_per_1000_donne_15_49_2003_2005 * 100 - 100, "Nascite", "Variazione nati per donna 2003/05-2022/24 %", FN, "nati_per_1000_donne", "2003/05-2022/24", "ds_nati", tipo="variazione", den="donne 15-49", aff="media", nota="NIL prima del 2012: assegnazione non documentata")

# ---------- mortalità (SMR osservati/attesi; la e0 è un modello e non si usa)
sm = rd("speranza-vita/pulito/nil_smr_e0.csv")
sm = sm[sm.sesso.astype(str).str.lower().str.startswith("t")] if sm.sesso.astype(str).str.lower().str.startswith("t").any() else sm
def smr(fin, c="smr"):
    return sm[sm.finestra == fin].set_index("id_nil")[c]
FS = "speranza-vita/pulito/nil_smr_e0.csv"
NS = "SMR standardizzato su età ma con età reale dei decessi non disponibile per NIL; residenze per anziani non identificabili (Morivione)"
add("smr_12_19", smr("2012-2019"), "Salute", "Morti osservate/attese 2012-2019", FS, "smr", "2012-2019", "smr", costr="standardizzazione indiretta", nota=NS, aff="media")
add("smr_22_24", smr("2022-2024"), "Salute", "Morti osservate/attese 2022-2024", FS, "smr", "2022-2024", "smr", costr="standardizzazione indiretta", nota=NS, aff="media")
add("var_smr", smr("2022-2024") / smr("2012-2019") * 100 - 100, "Salute", "Variazione SMR 2012/19-2022/24 %", FS, "smr", "2012/19-2022/24", "smr", tipo="variazione", costr="standardizzazione indiretta", aff="bassa", nota=NS)
if (sm.finestra == "2020").any():
    add("smr_2020", smr("2020"), "Salute", "Morti osservate/attese nel 2020 (Covid)", FS, "smr", 2020, "smr", costr="standardizzazione indiretta", aff="media", nota=NS)
    add("eccesso_2020", smr("2020") / smr("2016-2019") * 100 - 100, "Salute", "SMR 2020 rispetto a SMR 2016-2019 (%)", FS, "smr", "2020 vs 2016-19", "smr", tipo="variazione", costr="standardizzazione indiretta", aff="media", nota=NS)
dm = rd("speranza-vita/pulito/decessi_nil_anno_genere.csv")
# ---------- medici e farmacie
me = rd("docs/medici-farmacie/data/nil.csv").set_index("id_nil")
FM = "docs/medici-farmacie/data/nil.csv"
NM = "Fotografia ottobre 2026; indirizzo dell'ambulatorio principale"
add("medici_x1000", me.medici_famiglia_ogni_1000_residenti_14_e_piu, "Salute", "Medici di famiglia ogni 1.000 residenti 14+", FM, "medici_famiglia_ogni_1000_residenti_14_e_piu", 2026, "ds234", den="residenti", nota=NM)
add("farmacie_x10k", me.farmacie_ogni_10000_residenti, "Salute", "Farmacie ogni 10.000 residenti", FM, "farmacie_ogni_10000_residenti", 2026, "ds501", den="residenti")
add("minuti_farmacia", me.minuti_a_piedi_farmacia_mediana, "Salute", "Minuti a piedi alla farmacia (mediana)", FM, "minuti_a_piedi_farmacia_mediana", 2026, "ds501", costr="rete pedonale")
add("minuti_medico", me.minuti_a_piedi_ambulatorio_medico_mediana, "Salute", "Minuti a piedi al medico (mediana)", FM, "minuti_a_piedi_ambulatorio_medico_mediana", 2026, "ds234", costr="rete pedonale")
add("medici_65piu", me.titolari_65_anni_e_piu_solo_se_almeno_10_medici / me.di_cui_titolari * 100, "Salute", "% medici titolari con 65+ anni (solo con almeno 10 medici)", FM, "titolari_65_anni_e_piu_solo_se_almeno_10_medici/di_cui_titolari", 2026, "ds234", aff="bassa", nota="Valore presente solo se il NIL ha almeno 10 medici")

# ---------- flussi di residenza
fl = rd("popolazione/pulito/flussi_nil_riepilogo.csv")
FF = "popolazione/pulito/flussi_nil_riepilogo.csv"
per = sorted(fl.periodo.astype(str).unique())
p_old, p_new = per[0], per[-1]
f1 = fl[fl.periodo.astype(str) == p_old].set_index("id_nil")
f2 = fl[fl.periodo.astype(str) == p_new].set_index("id_nil")
anni_new = 5 if "2020" in p_new else 1
add("saldo_italia_12_19", f1.saldo_italia_x1000_anno, "Movimenti", "Saldo con altri comuni italiani x1000 l'anno", FF, "saldo_italia_x1000_anno", p_old, "ds_flussi", tipo="variazione", den="residenti", aff="media", nota="Cancellazioni 'altro' fuori scala nel 2013-14; registro")
add("saldo_estero_12_19", f1.saldo_estero_x1000_anno, "Movimenti", "Saldo con l'estero x1000 l'anno", FF, "saldo_estero_x1000_anno", p_old, "ds_flussi", tipo="variazione", den="residenti", aff="media", nota="Registrazioni accumulate; cancellazioni per estero in ritardo")
add("saldo_italia_20_24", f2.saldo_italia_x1000_anno, "Movimenti", "Saldo con altri comuni italiani x1000 l'anno", FF, "saldo_italia_x1000_anno", p_new, "ds_flussi", tipo="variazione", den="residenti", aff="media")
add("saldo_estero_20_24", f2.saldo_estero_x1000_anno, "Movimenti", "Saldo con l'estero x1000 l'anno", FF, "saldo_estero_x1000_anno", p_new, "ds_flussi", tipo="variazione", den="residenti", aff="media", nota="2024 incompleto per le uscite")
fa = rd("popolazione/pulito/flussi_nil_anno.csv")
fa2 = fa[fa.anno.between(2015, 2019)]
ric = (fa2.groupby("id_nil")[["isc_italia", "isc_estero", "canc_italia", "canc_estero"]].sum().sum(axis=1) / 5) / e14.residenti * 1000
add("ricambio_15_19", ric, "Movimenti", "Iscritti + cancellati per Italia/estero x1000 l'anno", "popolazione/pulito/flussi_nil_anno.csv", "isc_*, canc_*", "2015-2019", "ds_flussi", den="residenti", aff="media", nota="Anni scelti per evitare le pulizie del registro 2013-14 e il Covid")

# ---------- casa e palazzi
pa = rd("docs/palazzi/data/nil.csv").set_index("id_nil")
FP = "docs/palazzi/data/nil.csv"
NP = "Censimento 2011, quote affidabili solo con almeno 100 edifici; età dell'edificio, non della ristrutturazione"
add("edifici_pre1946", pa.quota_prima_del_1946_pct, "Casa", "% edifici residenziali prima del 1946", FP, "quota_prima_del_1946_pct", 2011, "censimento_edifici", costr="sezioni censuarie", nota=NP)
add("edifici_46_70", pa.quota_1946_1970_pct, "Casa", "% edifici 1946-1970", FP, "quota_1946_1970_pct", 2011, "censimento_edifici", costr="sezioni censuarie", nota=NP)
add("edifici_post80", pa.quota_dopo_il_1980_pct, "Casa", "% edifici dopo il 1980", FP, "quota_dopo_il_1980_pct", 2011, "censimento_edifici", costr="sezioni censuarie", nota=NP)
add("interni_x_edificio", pa.interni_per_edificio, "Casa", "Abitazioni occupate per edificio", FP, "interni_per_edificio", 2011, "censimento_edifici", costr="sezioni censuarie", nota=NP)
co = rd("docs/costruzioni/data/nil.csv").set_index("id_nil")
FCO = "docs/costruzioni/data/nil.csv"
NCO = "Permessi, non cantieri finiti; un solo intervento sposta il quartiere"
add("nuove_case_x1000", co.nuove_abitazioni_ogni_1000_abitanti_2024, "Casa", "Nuove abitazioni con titolo 2014-2024 ogni 1.000 abitanti", FCO, "nuove_abitazioni_ogni_1000_abitanti_2024", "2014-2024", "titoli_edilizi", tipo="variazione", den="residenti", nota=NCO)
add("volume_nuovo_x_kmq", co.volume_nuovi_fabbricati_m3 / T["area_km2"], "Casa", "Volume nuovi fabbricati m3 per km2", FCO, "volume_nuovi_fabbricati_m3", "2014-2024", "titoli_edilizi", tipo="variazione", den="area", nota=NCO)
cp = rd("docs/case-popolari/data/nil.csv").set_index("id_nil")
add("aler_x_abitazione", cp.canone_ALER_2016_per_abitazione_euro.fillna(0), "Casa", "Canone ALER 2016 per abitazione (proxy case popolari ALER)", "docs/case-popolari/data/nil.csv", "canone_ALER_2016_per_abitazione_euro", 2016, "aler", den="abitazioni", aff="media", nota="Solo ALER, mancano le case del Comune; include negozi e box")
ab = rd("affitti-brevi/pulito/nil_riepilogo.csv").set_index("nil")
FA = "affitti-brevi/pulito/nil_riepilogo.csv"
NA = "Inside Airbnb, un portale, una fotografia; posizione spostata fino a 150 m"
abok = ab.annunci_per_100_abitazioni.where(ab.piccolo_denominatore.astype(str).str.lower().isin(["false", "0", "nan"]))
add("airbnb_x100", abok, "Casa", "Annunci Airbnb ogni 100 abitazioni", FA, "annunci_per_100_abitazioni", "2026-09", "inside_airbnb", den="abitazioni", nota=NA)
add("airbnb_case_intere", ab.case_intere / ab.annunci * 100, "Casa", "% case intere sugli annunci", FA, "case_intere/annunci", "2026-09", "inside_airbnb", nota=NA)
add("airbnb_prezzo", ab.prezzo_mediano_case_intere_quotazione.where(ab.n_prezzi >= 30), "Casa", "Prezzo mediano notte case intere", FA, "prezzo_mediano_case_intere_quotazione", "2026-09", "inside_airbnb", aff="media", nota="Quotazione per date precise")
ac = rd("affitti-brevi/pulito/crescita_nil.csv").set_index("nil_id")
add("airbnb_crescita", ac.rapporto_2025_su_2019.where(ac.annunci_con_recensione_2019 >= 15), "Casa", "Annunci recensiti 2025 / 2019", "affitti-brevi/pulito/crescita_nil.csv", "rapporto_2025_su_2019", "2019-2025", "inside_airbnb", tipo="variazione", aff="bassa", nota="Solo i sopravvissuti: passato sottostimato. Solo NIL con almeno 15 annunci recensiti nel 2019")

# ---------- 15 minuti (stessa fonte: rete pedonale sui civici)
c15 = rd("docs/citta-15-minuti/data/nil_punteggi.csv").set_index("ID_NIL")
c15x = rd("docs/citta-15-minuti/data/nil_punteggi_extra.csv").set_index("ID_NIL")
F15 = "docs/citta-15-minuti/data/nil_punteggi.csv"
N15 = "Tempo a piedi su rete OSM dai civici; il Parco Sud manca; Cascina Merlata falsata"
add("c15_punteggio", c15.punteggio_su_10, "Servizi", "Punteggio 15 minuti su 10", F15, "punteggio_su_10", 2025, "c15", costr="rete pedonale", nota=N15)
for k in ["medici", "scuole", "biblioteche", "mercati", "parchi", "vicinato"]:
    add(f"c15_{k}", c15[f"quota_entro15_{k}"], "Servizi", f"% residenti entro 15 min: {k}", F15, f"quota_entro15_{k}", 2025, "c15", costr="rete pedonale", nota=N15)
for k in ["cinema", "teatri_musei", "giochi", "metro", "bikemi", "supermercati", "ospedali", "librerie"]:
    add(f"c15_{k}", c15x[f"quota_entro15_{k}"], "Servizi", f"% residenti entro 15 min: {k}", "docs/citta-15-minuti/data/nil_punteggi_extra.csv", f"quota_entro15_{k}", 2025, "c15", costr="rete pedonale", nota=N15)

# ---------- locali e cucine
ri = rd("docs/ristoranti/data/nil.csv").set_index("id_nil")
FR = "docs/ristoranti/data/nil.csv"
NR = "Pratiche del registro, non locali aperti; denominatore residenti non conta chi lavora"
add("locali_x1000", ri.in_piano_per_1000ab, "Servizi", "Pubblici esercizi in piano ogni 1.000 residenti", FR, "in_piano_per_1000ab", 2026, "ds58", den="residenti", nota=NR)
add("locali_x_kmq", ri.in_piano_per_km2, "Servizi", "Pubblici esercizi in piano per km2", FR, "in_piano_per_km2", 2026, "ds58", den="area", nota=NR)
add("artigianato_x1000", ri.pratiche_artigianato_alim / T["residenti_2024"] * 1000, "Servizi", "Artigianato alimentare ogni 1.000 residenti", FR, "pratiche_artigianato_alim", 2026, "ds58", den="residenti", nota=NR)
rv = rd("docs/ristoranti/data/pratiche_2019_2026_nil.csv").set_index("id_nil")
add("var_locali", rv.variazione_pct.where(rv.registro_2019 >= 40), "Servizi", "Variazione pratiche 2019-2026 %", "docs/ristoranti/data/pratiche_2019_2026_nil.csv", "variazione_pct", "2019-2026", "ds58", tipo="variazione", nota="Solo NIL con almeno 40 pratiche nel 2019")
cu = rd("docs/ristoranti/data/nil_cucine.csv").set_index("id_nil")
for k in ["pizza", "italiana", "giapponese_sushi", "cinese", "indiana_sudasiatica", "kebab_medio_oriente", "hamburger_panini", "pesce", "veg_insalate_poke"]:
    add(f"cuc_{k}", cu[f"{k}_pct"].where(cu.n_con_cucina >= 15), "Cucine", f"% {k} tra i locali con cucina nota", "docs/ristoranti/data/nil_cucine.csv", f"{k}_pct", 2026, "osm_cucine", costr="OSM volontario", den="locali", aff="bassa", nota="OSM: cucina nota 69%, più in centro. Solo NIL con almeno 15 locali con cucina")

# ---------- sport, terzo settore, biblioteche
sp = rd("docs/sport/data/nil_sport.csv").set_index("ID_NIL")
FSP = "docs/sport/data/nil_sport.csv"
add("sport_x10k", sp.per10k_tutti, "Servizi", "Impianti sportivi ogni 10.000 residenti", FSP, "per10k_tutti", 2025, "sport_multi", den="residenti", aff="media", nota="Fonti miste: OSM, Comune, Regione; ds34 del 2011")
add("sport_comunali_x10k", sp.per10k_comunali, "Servizi", "Impianti comunali ogni 10.000 residenti", FSP, "per10k_comunali", 2025, "sport_multi", den="residenti", aff="media")
ts = rd("docs/terzo-settore/data/nil.csv").set_index("id_nil")
FT = "docs/terzo-settore/data/nil.csv"
NT = "Sede legale, non operativa; elenchi piccoli e volontari"
add("associazioni_x10k", ts.associazioni_registro_comune_per_10000, "Società", "Associazioni registro Comune ogni 10.000", FT, "associazioni_registro_comune_per_10000", 2026, "terzo_comune", den="residenti", aff="media", nota=NT)
add("cooperative_x10k", ts.cooperative_sociali_albo_comune_per_10000, "Società", "Cooperative sociali albo Comune ogni 10.000", FT, "cooperative_sociali_albo_comune_per_10000", 2026, "terzo_comune", den="residenti", aff="bassa", nota=NT)
add("pers_giur_x10k", ts.persone_giuridiche_regione_per_10000, "Società", "Persone giuridiche Regione ogni 10.000", FT, "persone_giuridiche_regione_per_10000", 2026, "terzo_regione", den="residenti", aff="bassa", nota=NT)
bi = rd("biblioteche/pulito/nil_biblioteche.csv").set_index("ID_NIL")
add("distanza_biblioteca", bi.distanza_centroide_m, "Servizi", "Metri dal centroide alla biblioteca più vicina", "biblioteche/pulito/nil_biblioteche.csv", "distanza_centroide_m", 2025, "sbm", costr="geometria")
pr = rd("docs/biblioteche/data/biblioteche_anno.csv")

# ---------- verde, alberi, suolo, parcheggi
al = rd("docs/alberi/data/nil.csv").set_index("id_nil")
FAL = "docs/alberi/data/nil.csv"
NAL = "Solo alberi del Comune (strade, parchi, cimiteri), mancano i giardini privati"
add("alberi_x1000", al.alberi_per_1000_abitanti_2025, "Verde", "Alberi schedati ogni 1.000 abitanti", FAL, "alberi_per_1000_abitanti_2025", 2025, "alberi", den="residenti", nota=NAL)
add("alberi_x_kmq", al.alberi_per_km2_2025, "Verde", "Alberi schedati per km2", FAL, "alberi_per_km2_2025", 2025, "alberi", den="area", nota=NAL)
add("var_alberi", al.variazione_pct_2023_2025, "Verde", "Variazione alberi 2023-2025 %", FAL, "variazione_pct_2023_2025", "2023-2025", "alberi", tipo="variazione", aff="bassa", nota="Il perimetro dell'elenco cambia tra edizioni")
ve = rd("docs/verde/data/nil_verde.csv").set_index("id_nil")
FV = "docs/verde/data/nil_verde.csv"
add("verde_a_m2ab", ve.m2_ab_A, "Verde", "Verde stima A m2 per abitante", FV, "m2_ab_A", "2014+", "verde_stima", den="residenti", costr="modello", aff="bassa", nota="Stima: elenco 2014 senza mappa")
add("verde_b_m2ab", ve.m2_ab_B, "Verde", "Verde stima B m2 per abitante", FV, "m2_ab_B", "2014+", "alberi", den="residenti", costr="modello", aff="bassa", nota="B è collocata con gli alberi: legame con gli alberi costruito")
add("verde_a_pct", ve.pct_area_A, "Verde", "% area a verde (stima A)", FV, "pct_area_A", "2014+", "verde_stima", den="area", costr="modello", aff="bassa")
add("min_parco", ve.min_parco_mediana, "Verde", "Minuti al parco più vicino", FV, "min_parco_mediana", 2025, "c15", costr="rete pedonale", aff="media", nota="Solo parchi disegnati, manca il Parco Sud")
add("calore", ve.calore_esposizione, "Verde", "Indice esposizione al calore (satellite)", FV, "calore_esposizione", "n.d.", "spotted", costr="modello", aff="bassa", nota="SPOTTED: metodo su portale con registrazione, non verificato")
add("indice_verde", ve.indice_verde_spotted, "Verde", "Indice verde (satellite)", FV, "indice_verde_spotted", "n.d.", "spotted", costr="modello", aff="bassa")
add("gioco_x10k", ve.gioco_n / T["residenti_2024"] * 1e4, "Verde", "Aree gioco ogni 10.000 residenti", FV, "gioco_n", 2024, "verde_aree", den="residenti", aff="media")
add("orti_m2ab", ve.orti_m2 / T["residenti_2024"], "Verde", "Orti m2 per abitante", FV, "orti_m2", 2024, "verde_aree", den="residenti", aff="bassa")
ca = rd("docs/cani/data/aree_cani_per_nil.csv").set_index("id_nil")
add("cani_x100k", ca.aree_cani_per_100mila_ab, "Verde", "Aree cani ogni 100.000", "docs/cani/data/aree_cani_per_nil.csv", "aree_cani_per_100mila_ab", 2024, "verde_aree", den="residenti", aff="media")
su = rd("docs/suolo/data/nil_suolo.csv").set_index("id_nil")
FSU = "docs/suolo/data/nil_suolo.csv"
add("suolo_pct", su.pct_2025, "Verde", "% suolo consumato", FSU, "pct_2025", 2025, "ispra", den="area")
add("nuovo_suolo", su.nuovo_ha_per_100ha_nil, "Verde", "Nuovo suolo consumato 2012-2025 ha ogni 100 ha", FSU, "nuovo_ha_per_100ha_nil", "2012-2025", "ispra", tipo="variazione", den="area", nota="Cantieri contano come consumato")
ri2 = rd("docs/rigenerazione/data/nil.csv").set_index("id_nil")
add("ambiti_rigen_pct", ri2.ambiti_pct, "Casa", "% area in ambiti di rigenerazione PGT", "docs/rigenerazione/data/nil.csv", "ambiti_pct", 2026, "pgt", den="area")
pk = rd("docs/parcheggi/data/nil.csv").set_index("id_nil")
FK = "docs/parcheggi/data/nil.csv"
add("sosta_m2_ab", pk.STIMA_m2_stalli_per_abitante, "Mobilità", "m2 di sosta su strada per abitante (stima)", FK, "STIMA_m2_stalli_per_abitante", 2026, "strade_modello", den="residenti", costr="modello", aff="bassa", nota="Modello per lunghezza di strada")
add("ciclabili_km_x_kmq", pk.ciclabili_km / T["area_km2"], "Mobilità", "km di ciclabili per km2", FK, "ciclabili_km", 2026, "ciclabili", den="area", aff="media", nota="Non contate strade 30 e promiscue")
add("ped_m2_ab", pk.aree_pedonali_m2 / T["residenti_2024"], "Mobilità", "Aree pedonali m2 per abitante", FK, "aree_pedonali_m2", 2026, "ds51", den="residenti", aff="media")
ant = rd("docs/antenne/data/nil.csv").set_index("id_nil")
FAN = "docs/antenne/data/nil.csv"
NAN = "Conta impianti, non potenza né esposizione"
add("antenne_x_kmq", ant.mobile_per_km2, "Mobilità", "Impianti telefonia mobile per km2", FAN, "mobile_per_km2", 2025, "castel", den="area", nota=NAN)
add("antenne_x1000", ant.mobile_per_1000_ab, "Mobilità", "Impianti telefonia mobile ogni 1.000 ab", FAN, "mobile_per_1000_ab", 2025, "castel", den="residenti", nota=NAN)
acr = rd("antenne/pulito/nil_crescita_2020_2025.csv").set_index("id_nil")
add("var_antenne", acr.variazione_pct.where(acr.mobile_2020_21 >= 10), "Mobilità", "Variazione impianti mobili 2020-2025 %", "antenne/pulito/nil_crescita_2020_2025.csv", "variazione_pct", "2020-2025", "castel", tipo="variazione", aff="bassa", nota="La copia 2020-21 non è del tutto confrontabile")

# ---------- memoria
sta = rd("docs/statue/data/per_nil.csv").set_index("id_nil")
FST = "docs/statue/data/per_nil.csv"
NST = "Wikidata, OSM e ICCD: distorsione verso centro e opere note"
add("opere_x_kmq", sta.opere_per_kmq, "Memoria", "Opere pubbliche per km2", FST, "opere_per_kmq", 2026, "statue_osm", den="area", aff="media", nota=NST)
add("murali", sta.murali, "Memoria", "Murali (conteggio)", FST, "murali", 2026, "statue_osm", aff="bassa", nota=NST)
tg = rd("docs/targhe/data/per_nil.csv").set_index("id_nil")
add("targhe_x10k", tg.targhe / T["residenti_2024"] * 1e4, "Memoria", "Lapidi e targhe ogni 10.000 residenti", "docs/targhe/data/per_nil.csv", "targhe", 2026, "targhe_pdm", den="residenti", aff="media", nota="Pietre della Memoria + altre fonti: non è un censimento")
add("targhe_resist_x10k", tg.targhe_resistenza / T["residenti_2024"] * 1e4, "Memoria", "Targhe della Resistenza ogni 10.000 residenti", "docs/targhe/data/per_nil.csv", "targhe_resistenza", 2026, "targhe_pdm", den="residenti", aff="media")
pi = rd("docs/pietre-inciampo/data/nil.csv").set_index("id")
add("pietre_x10k", pi.per10mila, "Memoria", "Pietre d'inciampo ogni 10.000", "docs/pietre-inciampo/data/nil.csv", "per10mila", 2026, "pietre_comitato", den="residenti", aff="media", nota="Una pietra è una richiesta, non un censimento")
add("pietre_politiche", pi.politica, "Memoria", "Pietre di deportati politici (conteggio)", "docs/pietre-inciampo/data/nil.csv", "politica", 2026, "pietre_comitato", aff="media")
bc = json.load(open(path("docs", "beni-confiscati", "data", "nil.geojson"), encoding="utf8"))
bcs = pd.Series({f["properties"].get("i", f["properties"].get("id")): f["properties"].get("cu") for f in bc["features"]})
add("confiscati_x10k", pd.to_numeric(bcs, errors="coerce").fillna(0) / T["residenti_2024"] * 1e4, "Memoria", "Unità confiscate del Comune ogni 10.000", "docs/beni-confiscati/data/nil.geojson", "cu", 2026, "confiscati", den="residenti", aff="media", nota="Conta unità, non edifici; tre palazzi pesano 59 su 274")
bo = rd("botteghe/pulito/per_nil.csv").set_index("nil_id")
add("botteghe_x10k", bo.per_10000_abitanti, "Memoria", "Botteghe storiche ogni 10.000", "botteghe/pulito/per_nil.csv", "per_10000_abitanti", 2024, "botteghe", den="residenti", aff="media", nota="Due elenchi con criteri diversi")
add("botteghe_cessate", (bo.n_cessate / bo.n_albo24 * 100).where(bo.n_albo24 >= 5), "Memoria", "% botteghe cessate sull'Albo (almeno 5)", "botteghe/pulito/per_nil.csv", "n_cessate/n_albo24", "2017-2024", "botteghe", tipo="variazione", aff="bassa", nota="Cessata non è definita")
lu = rd("luoghi-cercati/pulito/totali_luogo.csv")
lu2 = lu.groupby("id_nil").agg(v=("views_totali", "sum"), it=("views_it", "sum"), n=("qid", "size"))
add("wiki_views_x_kmq", lu2.v / T["area_km2"], "Memoria", "Letture Wikipedia dei luoghi per km2", "luoghi-cercati/pulito/totali_luogo.csv", "views_totali", "2015-2026", "wiki", den="area", aff="media", nota="Letture non visite; poche voci pesano molto")
add("wiki_quota_estero", (1 - lu2.it / lu2.v).where(lu2.n >= 5) * 100, "Memoria", "% letture in lingue non italiane", "luoghi-cercati/pulito/totali_luogo.csv", "views_it,views_totali", "2015-2026", "wiki", aff="media", nota="Lingua non è nazionalità; solo NIL con almeno 5 voci")


# ---------- punti da attribuire ai NIL per coordinate
def conta_punti(lon, lat):
    """Restituisce per ogni punto l'id NIL del poligono che lo contiene, o NaN."""
    ids = list(T.index)
    tree = STRtree([POL[i] for i in ids])
    pts = [Point(a, b) if pd.notna(a) and pd.notna(b) else None for a, b in zip(lon, lat)]
    res = np.full(len(pts), np.nan)
    valid = [k for k, p in enumerate(pts) if p is not None]
    q = tree.query([pts[k] for k in valid], predicate="within")
    for a, b in zip(q[0], q[1]):
        res[valid[a]] = ids[b]
    return res


inc = pd.read_csv(path("incroci", "pulito", "incidenti_geo.csv.gz"), low_memory=False)
inc = inc[inc.lon.notna()]
inc["id_nil"] = conta_punti(inc.lon.values, inc.lat.values)
inc = inc[inc.id_nil.notna()]
FI2 = "incroci/pulito/incidenti_geo.csv.gz"
NI = "Solo incidenti con feriti; 80% posizionato; nessun dato di traffico; residenti non sono chi passa"
i1 = inc[inc.anno.between(2012, 2019)].groupby("id_nil")
i2 = inc[inc.anno.between(2022, 2024)].groupby("id_nil")
a1, a2 = i1.size() / 8, i2.size() / 3
add("incidenti_x_kmq", a2 / T["area_km2"], "Mobilità", "Incidenti con feriti posizionati per km2 l'anno", FI2, "punti", "2022-2024", "incidenti", den="area", nota=NI)
add("incidenti_x1000", a2 / T["residenti_2024"] * 1000, "Mobilità", "Incidenti ogni 1.000 residenti l'anno", FI2, "punti", "2022-2024", "incidenti", den="residenti", nota=NI)
add("var_incidenti", a2 / a1 * 100 - 100, "Mobilità", "Variazione incidenti 2012/19-2022/24 %", FI2, "punti", "2012/19-2022/24", "incidenti", tipo="variazione", aff="media", nota=NI + "; quota posizionata può cambiare negli anni")
t2 = inc[inc.anno.between(2015, 2024)].groupby("id_nil")
tot = t2.size()
add("incid_q_pedoni", t2.ped.sum() / tot * 100, "Mobilità", "% incidenti con pedoni", FI2, "ped", "2015-2024", "incidenti", den="incidenti", aff="media", nota=NI)
add("incid_q_bici", (t2.bici.sum() + t2.monop.sum()) / tot * 100, "Mobilità", "% incidenti con bici o monopattino", FI2, "bici,monop", "2015-2024", "incidenti", den="incidenti", aff="media", nota=NI)
add("incid_q_moto", t2.moto.sum() / tot * 100, "Mobilità", "% incidenti con moto", FI2, "moto", "2015-2024", "incidenti", den="incidenti", aff="media", nota=NI)
add("morti_x1000_incid", inc[inc.anno.between(2010, 2024)].groupby("id_nil").morti.sum() / inc[inc.anno.between(2010, 2024)].groupby("id_nil").size() * 1000, "Mobilità", "Morti ogni 1.000 incidenti con feriti", FI2, "morti", "2010-2024", "incidenti", den="incidenti", aff="media", nota=NI + "; numeri piccoli")

cin = rd("cinema-spariti/pulito/cinema.csv")
cin["id_nil"] = conta_punti(cin.lon.values, cin.lat.values)
FCI = "cinema-spariti/pulito/cinema.csv"
add("cinema_storici_x_kmq", cin.groupby("id_nil").size().reindex(T.index).fillna(0) / T["area_km2"], "Memoria", "Cinema esistiti (aperti o chiusi) per km2", FCI, "lat,lon", "storico", "cinema", den="area", aff="media", nota="Elenco non completo, precisione variabile")
add("cinema_storici_x10k", cin.groupby("id_nil").size().reindex(T.index).fillna(0) / T["residenti_2024"] * 1e4, "Memoria", "Cinema esistiti ogni 10.000 residenti", FCI, "lat,lon", "storico", "cinema", den="residenti", aff="media")
fl_ = rd("film-e-libri/pulito/luoghi.csv")
fl_ = fl_[fl_.lat.notna()].drop_duplicates(["id_opera", "id_luogo"])
fl_["id_nil"] = conta_punti(fl_.lon.values, fl_.lat.values)
add("film_libri_x_kmq", fl_.groupby("id_nil").size().reindex(T.index).fillna(0) / T["area_km2"], "Memoria", "Luoghi di film e libri per km2", "film-e-libri/pulito/luoghi.csv", "lat,lon", "storico", "wiki_film", den="area", aff="bassa", nota="Wikipedia: centro favorito")
vp = rd("violenza-politica/pulito/eventi.csv")
vp["id_nil"] = conta_punti(vp.lon.values, vp.lat.values)
add("violenza_pol_eventi", vp.groupby("id_nil").size().reindex(T.index).fillna(0), "Memoria", "Eventi di violenza politica (conteggio)", "violenza-politica/pulito/eventi.csv", "lat,lon", "1919-", "wiki_violenza", aff="bassa", nota="Da Wikipedia; 84 eventi")
bk = rd("bici/pulito/gbfs_fotografia_2026-11-02.csv")
bk["id_nil"] = conta_punti(bk.lon.values, bk.lat.values)
add("bikemi_x_kmq", bk.groupby("id_nil").size().reindex(T.index).fillna(0) / T["area_km2"], "Mobilità", "Stazioni BikeMi per km2", "bici/pulito/gbfs_fotografia_2026-11-02.csv", "lat,lon", 2026, "bikemi", den="area")
mt = rd("metro/pulito/gtfs_metro_stazioni.csv")
mx = ((mt.lon.values[None, :] - T.lon.values[:, None]) * 77.9) ** 2 + ((mt.lat.values[None, :] - T.lat.values[:, None]) * 111.2) ** 2
add("dist_metro_km", pd.Series(np.sqrt(mx.min(axis=1)), index=T.index), "Mobilità", "Distanza del centroide dalla stazione di metro più vicina", "metro/pulito/gtfs_metro_stazioni.csv", "lat,lon", 2026, "metro", costr="geometria")
try:
    bcu = pd.read_csv(path("beni-culturali", "beni_culturali_milano.csv"), usecols=lambda c: c in ("lat", "long", "ambito", "classe_bene"), low_memory=False)
    lonc, latc = "long", "lat"
    bcu = bcu[pd.to_numeric(bcu[latc], errors="coerce").notna()]
    bcu["id_nil"] = conta_punti(pd.to_numeric(bcu[lonc]).values, pd.to_numeric(bcu[latc]).values)
    add("beni_cult_x_kmq", bcu.groupby("id_nil").size().reindex(T.index).fillna(0) / T["area_km2"], "Memoria", "Beni culturali catalogati con coordinate per km2", "beni-culturali/beni_culturali_milano.csv", "lat,lon", 2026, "iccd", den="area", aff="bassa", nota="Catalogo: copre ciò che è stato schedato")
except Exception as ex:
    print("beni culturali non letti:", ex)

# ---------- scuole
sc = rd("docs/scuole/data/nil_scuole.csv").set_index("id_nil")
FSC = "docs/scuole/data/nil_scuole.csv"
add("var_alunni", sc.Iv, "Scuola", "Variazione alunni 2015-2024 %", FSC, "Iv", "2015-2024", "scuole", tipo="variazione", aff="media", nota="Contati dove sta la scuola, non dove abitano")
add("var_bambini", sc.Rv, "Scuola", "Variazione residenti in età scolare 2015-2024 %", FSC, "Rv", "2015-2024", "ds27", tipo="variazione", aff="media")
st = rd("scuole/pulito/nil_stranieri_2024.csv")
prim = st[st.ordine.astype(str).str.contains("prim", case=False)].set_index("id_nil")
add("scuola_gap_cit", (prim.quota_pupilli_pct - prim.quota_residenti_fascia_pct).where(prim.iscritti >= 200), "Scuola", "Primaria: % alunni cittadinanza non italiana meno % residenti di quell'età", "scuole/pulito/nil_stranieri_2024.csv", "quota_pupilli_pct-quota_residenti_fascia_pct", 2024, "scuole", aff="media", nota="Cittadinanza non è origine; la scuola può attrarre da fuori; solo con almeno 200 iscritti")
pe = rd("docs/poverta-educativa/data/milano_nil_poverta_educativa.csv").set_index("id_nil")
FPE = "docs/poverta-educativa/data/milano_nil_poverta_educativa.csv"
add("tempo_pieno", pe.tp_pct_statali, "Scuola", "% alunni primaria statale a tempo pieno", FPE, "tp_pct_statali", 2024, "mim", aff="media", nota="Per scuola, non per residenza")
add("paritarie", pe.quota_paritaria_pct, "Scuola", "% alunni primaria in paritarie", FPE, "quota_paritaria_pct", 2024, "mim", aff="media")
add("nidi_x1000", pe.sedi_nido_per_1000_0_2, "Scuola", "Sedi di nido ogni 1.000 bambini 0-2", FPE, "sedi_nido_per_1000_0_2", 2018, "ds47", aff="bassa", nota="Sedi, non posti; dato 2018/19")

# ---------- voto (ricostruito da sezioni: NIL = stima)
ix = json.load(open(path("docs", "elezioni", "data", "index.json"), encoding="utf8"))
EL = {e["id"]: e for e in ix["elezioni"]}
FAM = [f["nome"] for f in ix["famiglie"]]


def voto(eid):
    """Affluenza e quote per famiglia per NIL da un'elezione. Scarta i NIL con meno di 1.000 elettori."""
    d = json.load(open(path("docs", "elezioni", "data", "nil", eid + ".json"), encoding="utf8"))
    e = EL[eid]
    fam = e.get("fam") or []
    rows = {}
    for k, v in d["p"].items():
        if v.get("e", 0) < 1000 or v.get("vt") is None:
            continue
        r = {"aff": v["vt"] / v["e"] * 100}
        if "v" in v and e.get("par"):
            tot = sum(v["v"]) or 1
            acc = {}
            for (nome, fi), n in zip(e["par"], v["v"]):
                acc[fam[fi]] = acc.get(fam[fi], 0) + n
            for f_, n in acc.items():
                r[f_] = n / tot * 100
        if "si" in v and v.get("no") is not None:
            r["si"] = v["si"] / max(v["si"] + v["no"], 1) * 100
        rows[int(k)] = r
    return pd.DataFrame(rows).T


NV = "Da sezioni a NIL: stima; registro elettorale più grande degli adulti nei NIL ricchi (filone voto-reddito); stranieri non votano; famiglie politiche sono raggruppamenti del progetto"
vt = {k: voto(k) for k in ["comunali_consiglio_2016-06-05", "comunali_consiglio_2021-10-03", "camera_2018-03-04", "camera_2022-09-25", "europee_2019-05-26", "europee_2024-06-08", "referendum_2025-06-08_ds2930", "referendum_2026-03-22_ds2975", "referendum_2016-12-04_ds1370"]}
FE1 = "docs/elezioni/data/nil/"
add("aff_com_2021", vt["comunali_consiglio_2021-10-03"].aff, "Voto", "Affluenza Comunali 2021", FE1 + "comunali_consiglio_2021-10-03.json", "vt/e", 2021, "elezioni", costr="sezioni", nota=NV, aff="media")
add("aff_cam_2022", vt["camera_2022-09-25"].aff, "Voto", "Affluenza Camera 2022", FE1 + "camera_2022-09-25.json", "vt/e", 2022, "elezioni", costr="sezioni", nota=NV, aff="media")
add("aff_eur_2024", vt["europee_2024-06-08"].aff, "Voto", "Affluenza Europee 2024", FE1 + "europee_2024-06-08.json", "vt/e", 2024, "elezioni", costr="sezioni", nota=NV, aff="media")
add("aff_ref_2025", vt["referendum_2025-06-08_ds2930"].aff, "Voto", "Affluenza referendum 2025", FE1 + "referendum_2025-06-08_ds2930.json", "vt/e", 2025, "elezioni", costr="sezioni", nota=NV, aff="media")
add("var_aff_16_21", vt["comunali_consiglio_2021-10-03"].aff - vt["comunali_consiglio_2016-06-05"].aff, "Voto", "Variazione affluenza Comunali 2016-2021", FE1, "vt/e", "2016-2021", "elezioni", tipo="variazione", costr="sezioni", nota=NV, aff="media")
add("var_aff_18_22", vt["camera_2022-09-25"].aff - vt["camera_2018-03-04"].aff, "Voto", "Variazione affluenza Camera 2018-2022", FE1, "vt/e", "2018-2022", "elezioni", tipo="variazione", costr="sezioni", nota=NV, aff="media")


def blocco(eid, fam):
    d = vt[eid]
    return d[[f for f in fam if f in d.columns]].sum(axis=1)


SX = ["Sinistra", "Centrosinistra"]
DX = ["Centrodestra", "Lega", "Destra"]
for eid, tag, an in [("comunali_consiglio_2021-10-03", "com21", 2021), ("camera_2022-09-25", "cam22", 2022), ("europee_2024-06-08", "eur24", 2024)]:
    add(f"sx_{tag}", blocco(eid, SX), "Voto", f"% Sinistra+Centrosinistra {tag}", FE1 + eid + ".json", "famiglie", an, "elezioni", costr="sezioni", nota=NV, aff="media")
add("dx_cam22", blocco("camera_2022-09-25", DX), "Voto", "% Centrodestra+Lega+Destra Camera 2022", FE1 + "camera_2022-09-25.json", "famiglie", 2022, "elezioni", costr="sezioni", nota=NV, aff="media")
add("lega_eur19", blocco("europee_2019-05-26", ["Lega"]), "Voto", "% Lega Europee 2019", FE1 + "europee_2019-05-26.json", "famiglie", 2019, "elezioni", costr="sezioni", nota=NV, aff="media")
add("destra_cam22", blocco("camera_2022-09-25", ["Destra"]), "Voto", "% Destra (FdI ecc.) Camera 2022", FE1 + "camera_2022-09-25.json", "famiglie", 2022, "elezioni", costr="sezioni", nota=NV, aff="media")
add("m5s_cam18", blocco("camera_2018-03-04", ["M5S"]), "Voto", "% M5S Camera 2018", FE1 + "camera_2018-03-04.json", "famiglie", 2018, "elezioni", costr="sezioni", nota=NV, aff="media")
add("var_sx_18_22", blocco("camera_2022-09-25", SX) - blocco("camera_2018-03-04", SX), "Voto", "Variazione % sx Camera 2018-2022", FE1, "famiglie", "2018-2022", "elezioni", tipo="variazione", costr="sezioni", nota=NV, aff="media")
add("var_dx_18_22", blocco("camera_2022-09-25", DX) - blocco("camera_2018-03-04", DX), "Voto", "Variazione % dx Camera 2018-2022", FE1, "famiglie", "2018-2022", "elezioni", tipo="variazione", costr="sezioni", nota=NV, aff="media")
ec = rd("elezioni/pulito/nil_controllo_popolazione.csv").set_index("id_nil")
add("elettori_su_adulti", ec.rapporto, "Voto", "Elettori / adulti residenti 2021", "elezioni/pulito/nil_controllo_popolazione.csv", "rapporto", 2021, "elezioni", costr="sezioni", aff="media", nota="Indica il registro elettorale; include residenti all'estero")

# ---------- filtro
T["analisi"] = (T["residenti_2024"] >= SOGLIA_RESIDENTI).astype(int)
T.to_csv(os.path.join(OUT, "nil_tabella_tutti.csv"), encoding="utf-8-sig")
A = T[T.analisi == 1].copy()
A.to_csv(os.path.join(OUT, "nil_tabella.csv"), encoding="utf-8-sig")
D = pd.DataFrame(DIZ)
cop = A[D.variabile].notna().sum()
D["nil_con_valore"] = D.variabile.map(cop)
D["valori_distinti"] = D.variabile.map(A[D.variabile].nunique())
D.to_csv(os.path.join(OUT, "dizionario.csv"), index=False, encoding="utf-8-sig")

# ---------- vicini: contiguità regina tra tutti i NIL
righe = []
for a in T.index:
    for b in T.index:
        if a < b and POL[a].buffer(0.0003).intersects(POL[b]):
            righe.append((a, b))
pd.DataFrame(righe, columns=["a", "b"]).to_csv(os.path.join(OUT, "nil_vicini.csv"), index=False)
print("NIL totali", len(T), "in analisi", len(A), "variabili", len(D), "coppie contigue", len(righe))
print(D[["variabile", "nil_con_valore", "valori_distinti"]].sort_values("nil_con_valore").head(30).to_string())
print(A[D.variabile[D.controllo == 1]].describe().T[["count", "min", "50%", "max"]].to_string())
print(T.loc[T.analisi == 0, ["nil", "residenti_2024"]].to_string())
