r"""Prepara i dati leggeri per la pagina docs\bilancio-comune (filone 17, bilancio del Comune di Milano).

Entrata (sola lettura): <bilancio-comune>\pulito\
    spesa_missioni.csv, entrate.csv, bilancio_capitoli.csv, popolazione_milano.csv,
    indice_prezzi_annuo_FOI_da_strand12.csv, controllo_coerenza.csv
Uscite (in <docs>\bilancio-comune\data\):
    riepilogo.json                 tutti i numeri che la pagina mostra
    spesa_per_missione.csv         spese correnti per missione e anno (euro, euro 2025, per abitante)
    entrate_per_tipo.csv           entrate correnti per tipo e anno
    tributi_principali.csv         i quattro tributi piu' grandi + recupero evasione
    voci_concrete.csv              multe, Area C, imposta di soggiorno, trasporto pubblico, dividendi
    capitoli_usati.csv             ogni capitolo del bilancio sommato nelle voci concrete (con edizione e anno)
    entrate_prime_voci_2025.csv    le 15 voci di entrata piu' grandi del 2025
    abitanti_e_prezzi.csv          denominatori usati
Regole (da NOTE.md):
  - solo consuntivo (rendiconto): una sola edizione per anno (la piu' recente che lo contiene = colonna da_usare);
  - "spesa" = spese correnti (titolo 1): niente conto capitale, prestiti, partite di giro;
  - euro 2025 = importo * 100 / FOI(anno)  (indice FOI senza tabacchi, 2025 = 100);
  - abitanti = popolazione calcolata ISTAT a fine anno (ds71, Comune di Milano); il 2025 non c'e' nel file: si usa il 2024 (stima, segnalata);
  - le voci concrete sono somme di capitoli scelti per NOME (i nomi cambiano quasi ogni anno): i capitoli usati sono elencati in capitoli_usati.csv.
Si puo' rilanciare tale e quale.
Uso: python -I -X utf8 pagina.py <cartella bilancio-comune> [cartella di uscita]
"""
import sys, os, re, json, math
import pandas as pd
import warnings
warnings.filterwarnings('ignore', message='This pattern is interpreted as a regular expression')

BASE = sys.argv[1]
PUL = os.path.join(BASE, 'pulito')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(BASE)), 'docs', 'bilancio-comune', 'data')
os.makedirs(OUT, exist_ok=True)

A0, A1 = 2015, 2025
ANNI = list(range(A0, A1 + 1))
DATA_SCARICO = '29-30/10/2026'


def rd(name):
    return pd.read_csv(os.path.join(PUL, name), sep=';', encoding='utf-8-sig', low_memory=False)


def M(x):          # euro -> milioni, 2 decimali
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x) / 1e6, 2)


def r1(x, nd=1):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else round(float(x), nd)


# ------------------------------------------------------------------ denominatori
foi = pd.read_csv(os.path.join(PUL, 'indice_prezzi_annuo_FOI_da_strand12.csv')).set_index('anno')['indice_raccordato_2025_100']
pop_df = rd('popolazione_milano.csv').set_index('anno')
pop_istat = pop_df['pop_calcolata_istat_fine_anno'].astype(float)
pop_anag = pop_df['pop_anagrafe_somma_quartieri'].astype(float)
pop_usata = {}
pop_stima = {}
for a in ANNI:
    if a in pop_istat.index and not math.isnan(pop_istat[a]):
        pop_usata[a] = float(pop_istat[a]); pop_stima[a] = False
    else:                        # 2025: non c'e' nel file -> si usa il 2024
        pop_usata[a] = float(pop_istat[a - 1]); pop_stima[a] = True


def defl(a):                    # moltiplicatore euro di quell'anno -> euro 2025
    return 100.0 / float(foi[a])


# ------------------------------------------------------------------ spesa per missione (titolo 1)
sp = rd('spesa_missioni.csv')
sp = sp[(sp.fase == 'consuntivo') & (sp.da_usare == 1) & (sp.anno >= A0) & (sp.anno <= A1)]
sp1 = sp[sp.titolo == 1]
ed_spesa = sp1.groupby('anno').fonte.first().to_dict()

NOMI = {   # codice: (nome semplice, funzione prevalente, voci spostate?)
    1: 'Amministrazione e servizi generali', 2: 'Giustizia', 3: 'Polizia locale e sicurezza',
    4: 'Scuola e diritto allo studio', 5: 'Cultura', 6: 'Sport e giovani', 7: 'Turismo',
    8: 'Territorio e case popolari', 9: 'Ambiente e rifiuti', 10: 'Trasporti e strade',
    11: 'Protezione civile', 12: 'Servizi sociali, famiglia e nidi', 13: 'Salute',
    14: 'Commercio e sviluppo economico', 15: 'Lavoro e formazione', 16: 'Agricoltura',
    17: 'Energia', 19: 'Relazioni internazionali', 20: 'Fondi e accantonamenti'}
# missioni con un salto che sembra un cambio di classificazione (verificato sui programmi, vedi NOTE.md Fase 3)
RICLASS = {1: '2018/2019: il programma "Risorse umane" passa da 51 a 123 M, la polizia locale scende di 39 M',
           2: '2015/2016: scende da 18 a 4 M',
           3: '2018/2019: il programma "Polizia locale" scende da 213 a 174 M mentre "Risorse umane" (missione 1) sale',
           14: '2015/2016: il programma "Commercio" scende da 89 a 9 M'}

# nomi ufficiali (edizione piu' recente che ha quella missione)
uff = sp.sort_values('anno').groupby('missione').desc_missione.last().to_dict()


def sentence(s):
    s = str(s).strip().lower()
    return s[:1].upper() + s[1:]


missioni = []
tab_miss = {}                   # (m, a) -> euro
for m, g in sp1.groupby('missione'):
    for a, gg in g.groupby('anno'):
        tab_miss[(m, a)] = float(gg.importo.sum())
tot_nom = {a: sum(v for (m, aa), v in tab_miss.items() if aa == a) for a in ANNI}
# programmi principali 2025 per missione
pr25 = sp1[sp1.anno == A1].groupby(['missione', 'programma', 'desc_programma']).importo.sum().reset_index()

for m in sorted(set(k[0] for k in tab_miss)):
    nom = [tab_miss.get((m, a), 0.0) for a in ANNI]
    if max(nom) < 1e5 and m not in NOMI:
        continue
    reale = [nom[i] * defl(a) for i, a in enumerate(ANNI)]
    pc = [reale[i] / pop_usata[a] for i, a in enumerate(ANNI)]
    progs = pr25[pr25.missione == m].sort_values('importo', ascending=False).head(3)
    missioni.append({
        'cod': int(m), 'nome': NOMI.get(m, sentence(uff.get(m, str(m)))), 'ufficiale': sentence(uff.get(m, '')),
        'nom_milioni': [M(x) for x in nom], 'reale_milioni': [M(x) for x in reale], 'reale_pc': [r1(x, 2) for x in pc],
        'programmi_2025': [{'nome': str(p.desc_programma).strip(), 'milioni': M(p.importo)} for p in progs.itertuples() if p.importo > 1e5],
        'riclass': RICLASS.get(m)})

tot_tutti = {a: float(sp[sp.anno == a].importo.sum()) for a in ANNI}
tot_real = [tot_nom[a] * defl(a) for a in ANNI]
tot_pc = [tot_real[i] / pop_usata[a] for i, a in enumerate(ANNI)]
i15, i16, i24, i25 = 0, 1, ANNI.index(2024), ANNI.index(2025)

# sensibilita': abitanti dell'anagrafe (somma quartieri) 2015-2024
tot_pc_anag = {a: tot_real[i] / float(pop_anag[a]) for i, a in enumerate(ANNI) if a in pop_anag.index and not math.isnan(pop_anag[a])}

# ------------------------------------------------------------------ capitoli: una edizione per anno
cap = rd('bilancio_capitoli.csv')
cap = cap[(cap.misura == 'rendiconto') & (cap.anno >= A0) & (cap.anno <= A1)].copy()
cap['ord'] = cap.edizione.str[:4].astype(int)
cap = cap[cap.ord == cap.groupby(['tipo', 'anno']).ord.transform('max')]
ed_cap = cap.groupby('anno').edizione.first().to_dict()
cap['desc'] = cap.desc_capitolo.astype(str).str.strip()
# controllo: le spese correnti dei capitoli = spesa_missioni (titolo 1)
for a in ANNI:
    s1 = cap[(cap.tipo == 'uscite') & (cap.liv1 == 1) & (cap.anno == a)].importo.sum()
    if abs(s1 - tot_nom[a]) > 5:
        print('ATTENZIONE: spese correnti capitoli != spesa_missioni', a, s1, tot_nom[a])

# ------------------------------------------------------------------ entrate (entrate.csv)
en = rd('entrate.csv')
en = en[(en.fase == 'consuntivo') & (en.da_usare == 1) & (en.anno >= A0) & (en.anno <= A1)]
ed_entr = en.groupby('anno').fonte.first().to_dict()


def sum_en(mask):
    return {a: float(en[mask & (en.anno == a)].importo.sum()) for a in ANNI}


GRUPPI = [   # id, nome, maschera, spiegazione
    ('tributi', 'Tributi (IMU, rifiuti, addizionale IRPEF, imposta di soggiorno...)', (en.titolo == 1), 'Titolo 1: entrate tributarie e fondi perequativi'),
    ('trasferimenti', 'Trasferimenti (Stato, Regione, altri enti)', (en.titolo == 2), 'Titolo 2: trasferimenti correnti'),
    ('servizi', 'Servizi e beni (biglietti del trasporto pubblico, rette, affitti...)', (en.titolo == 3) & (en.tipologia == 1), 'Titolo 3, tipologia 1: vendita di beni e servizi e gestione dei beni'),
    ('multe', 'Multe e sanzioni', (en.titolo == 3) & (en.tipologia == 2), 'Titolo 3, tipologia 2: controllo e repressione delle irregolarita'),
    ('dividendi', 'Dividendi e interessi', (en.titolo == 3) & (en.tipologia.isin([3, 4])), 'Titolo 3, tipologie 3 e 4: interessi attivi e redditi da capitale (soprattutto dividendi)'),
    ('altre', 'Rimborsi e altre entrate correnti', (en.titolo == 3) & (en.tipologia == 5), 'Titolo 3, tipologia 5: rimborsi e altre entrate correnti'),
]
gruppi = []
ent_tab = {}
for gid, nome, mask, spieg in GRUPPI:
    nom = sum_en(mask)
    ent_tab[gid] = nom
    gruppi.append({'id': gid, 'nome': nome, 'spiega': spieg,
                   'nom_milioni': [M(nom[a]) for a in ANNI],
                   'reale_milioni': [M(nom[a] * defl(a)) for a in ANNI],
                   'reale_pc': [r1(nom[a] * defl(a) / pop_usata[a], 2) for a in ANNI]})
ent_corr = {a: sum(ent_tab[g[0]][a] for g in GRUPPI) for a in ANNI}
ent_non_corr = {a: float(en[(en.titolo.isin([4, 5, 6, 7, 9])) & (en.anno == a)].importo.sum()) for a in ANNI}
ent_tot = {a: float(en[en.anno == a].importo.sum()) for a in ANNI}

# ------------------------------------------------------------------ tributi principali (capitoli, titolo 1 delle entrate)
tr = cap[(cap.tipo == 'entrate') & (cap.liv1 == 1)]
TRIB = [
    ('casa', 'IMU e TASI (imposte sulla casa)', r'^(IMU|IMPOSTA MUNICIPALE UNICA|TRIBUTO PER I SERVIZI INDIVISIBILI)', r'RECUPERO'),
    ('rifiuti', 'TARI (tassa sui rifiuti)', r'^(TASSA SUI RIFIUTI \(TARI\)|TARI TASSA SUI RIFIUTI RISCOSSA)', None),
    ('irpef', 'Addizionale comunale IRPEF', r'^ADDIZIONALE COMUNALE', None),
    ('soggiorno', 'Imposta di soggiorno', r'^IMPOSTA DI SOGGIORNO', None),
    ('evasione', "Recupero evasione (IMU, TARI, pubblicità, altri)", r'RECUPERO EVASIONE', None),
]
trib_rows = []
trib_cap = []
usati = set()
trib_series = []
for tid, nome, pat, excl in TRIB:
    nom = {}
    for a in ANNI:
        x = tr[tr.anno == a]
        m = x.desc.str.contains(pat, regex=True, case=False)
        if excl:
            m &= ~x.desc.str.contains(excl, regex=True, case=False)
        if tid != 'evasione':
            m &= ~x.desc.str.contains('RECUPERO EVASIONE', regex=True)
        xs = x[m]
        usati.update(xs.index)
        nom[a] = float(xs.importo.sum())
        for r in xs.itertuples():
            trib_cap.append({'voce': tid, 'anno': a, 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})
    trib_series.append((tid, nome, nom))
trib_tot = ent_tab['tributi']
altri_trib = {a: trib_tot[a] - sum(s[2][a] for s in trib_series) for a in ANNI}
tributi = [{'id': t, 'nome': n, 'nom_milioni': [M(v[a]) for a in ANNI]} for t, n, v in trib_series]
tributi.append({'id': 'altri', 'nome': "Altri tributi (pubblicità, fondi perequativi, ...)", 'nom_milioni': [M(altri_trib[a]) for a in ANNI]})
tributi.append({'id': 'totale', 'nome': 'Totale tributi e fondi perequativi', 'nom_milioni': [M(trib_tot[a]) for a in ANNI]})

# ------------------------------------------------------------------ voci concrete
voci_cap = []   # per capitoli_usati.csv


def serie_cap(tipo, liv1, pat, voce, excl=None, liv2=None):
    """Somma per anno dei capitoli il cui nome corrisponde (regex, maiuscole indifferenti)."""
    out = {}
    for a in ANNI:
        x = cap[(cap.tipo == tipo) & (cap.liv1 == liv1) & (cap.anno == a)]
        if liv2 is not None:
            x = x[x.liv2 == liv2]
        m = x.desc.str.contains(pat, regex=True, case=False)
        if excl:
            m &= ~x.desc.str.contains(excl, regex=True, case=False)
        xs = x[m]
        out[a] = float(xs.importo.sum())
        for r in xs.itertuples():
            voci_cap.append({'voce': voce, 'anno': a, 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})
    return out


def blocco(nom, nota=None, anni_ok=None):
    d = {'nom_milioni': [M(nom[a]) if (anni_ok is None or a in anni_ok) else None for a in ANNI],
         'reale_milioni': [M(nom[a] * defl(a)) if (anni_ok is None or a in anni_ok) else None for a in ANNI]}
    if nota:
        d['nota'] = nota
    return d


cds_pat = r'^SANZIONI PER VIOLAZIONI (ALLE|DELLE) NORME DEL CODICE DELLA STRADA(, A LEGGI E REGOLAMENTI COMUNALI)?$'
multe = serie_cap('entrate', 3, cds_pat, 'multe_cds')
multe_prec = {}
for a in ANNI:
    x = cap[(cap.tipo == 'entrate') & (cap.liv1 == 3) & (cap.anno == a)]
    m = x.desc.str.contains('CODICE DELLA STRADA', case=False) & x.desc.str.contains(r'ESERCIZI PRECEDENTI$|^RECUPERO MOROSITA', regex=True, case=False)
    xs = x[m]
    multe_prec[a] = float(xs.importo.sum())
    for r in xs.itertuples():
        voci_cap.append({'voce': 'multe_cds_esercizi_precedenti', 'anno': a, 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})
spese_postali = serie_cap('entrate', 3, r'^RECUPERO SPESE POSTALI PER NOTIFICA VERBALI', 'recupero_spese_postali_verbali')
area_c = serie_cap('entrate', 3, r'^PROVENTI DA ZTL AREA C$', 'area_c')
ztl_nuova = serie_cap('entrate', 3, r'^PROVENTI DA ZTL - NUOVA TARIFFAZIONE', 'ztl_nuova_tariffazione')
soggiorno = serie_cap('entrate', 1, r'^IMPOSTA DI SOGGIORNO', 'imposta_di_soggiorno', excl=r'RECUPERO EVASIONE')
tpl_tariffe = serie_cap('entrate', 3, r'^PROVENTI DA TARIFFE PER IL TRASPORTO PUBBLICO LOCALE$', 'tpl_tariffe')
tpl_trasf = serie_cap('entrate', 2, r'^(CONTRIBUTI REGIONALI PER IL TRASPORTO PUBBLICO LOCALE|TRASFERIMENTI DA REGIONE PER IL TRASPORTO PUBBLICO LOCALE|(TPL - )?TRASFERIMENTI DA AGENZIA PER IL TPL BACINO)', 'tpl_trasferimenti_regione_agenzia')
tpl_covid = serie_cap('entrate', 2, r'^(TPL - TRASFERIMENTI FONDO PER RIDUZIONE RICAVI TARIFFARI|TPL - TRASFERIMENTI PER FINANZIAMENTO SERVIZI AGGIUNTIVI)', 'tpl_fondi_stato_ricavi_tariffari_e_covid')
m4 = serie_cap('uscite', 1, r'^LINEA M4 - SERVIZI DI TPL', 'spesa_tpl_linea_m4')
m5 = serie_cap('uscite', 1, r'^LINEA M5 - SERVIZI DI TPL', 'spesa_tpl_linea_m5')
tpl_spesa = {a: float(sp1[(sp1.missione == 10) & (sp1.programma == 2) & (sp1.anno == a)].importo.sum()) for a in ANNI}
dividendi = {a: float(en[(en.titolo == 3) & (en.tipologia == 4) & (en.categoria == 2) & (en.anno == a)].importo.sum()) for a in ANNI}
# dividendi per societa' (capitoli)
div_cap = {}
for a in (2015, 2019, 2025):
    x = cap[(cap.tipo == 'entrate') & (cap.liv1 == 3) & (cap.anno == a) & cap.desc.str.startswith('DIVIDENDI')]
    div_cap[a] = [{'nome': r.desc, 'milioni': M(r.importo)} for r in x.sort_values('importo', ascending=False).itertuples() if r.importo > 1e5]
    for r in x.itertuples():
        voci_cap.append({'voce': 'dividendi', 'anno': a, 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})
# sosta: voci che non mostriamo come serie
sosta = {}
for a in ANNI:
    x = cap[(cap.tipo == 'entrate') & (cap.liv1 == 3) & (cap.anno == a) & cap.desc.str.contains('SOSTA A PAGAMENTO', case=False)]
    sosta[a] = [{'nome': r.desc, 'milioni': M(r.importo)} for r in x.itertuples()]
    for r in x.itertuples():
        voci_cap.append({'voce': 'sosta_NON_mostrata', 'anno': a, 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})

voci_cap += trib_cap

voci = {
    'multe': {**blocco(multe, 'Capitolo "Sanzioni per violazioni delle norme del codice della strada". Nel 2015 e 2016 il capitolo comprendeva anche le sanzioni ai regolamenti comunali.'),
              'esercizi_precedenti': blocco(multe_prec, 'Sanzioni di anni passati (nomi dei capitoli diversi nel 2015-2019 e dal 2020: li abbiamo considerati equivalenti dal nome).'),
              'spese_postali': blocco(spese_postali, 'Rimborso delle spese di notifica dei verbali: non e\' una multa.')},
    'area_c': {**blocco(area_c), 'nuova_tariffazione': blocco(ztl_nuova, 'Capitolo "Proventi da ZTL - nuova tariffazione accesso al centro storico", dal 2020: non sommato ad Area C.')},
    'soggiorno': blocco(soggiorno, 'Capitoli "Imposta di soggiorno" (nome diverso nel 2015-2019 e dal 2020; il recupero evasione, 1,3 M al massimo, è escluso): stima per nome.'),
    'tpl': {'spesa': blocco(tpl_spesa, 'Missione 10, programma 2 "Trasporto pubblico locale", spese correnti'),
            'tariffe': blocco(tpl_tariffe, 'Capitolo "Proventi da tariffe per il trasporto pubblico locale" (stesso nome in tutti gli anni)'),
            'trasferimenti': blocco(tpl_trasf, 'Contributi della Regione, poi dell\'Agenzia del TPL: tre nomi diversi nel tempo, considerati lo stesso flusso dal nome'),
            'fondi_stato': blocco(tpl_covid, 'Fondo statale per i mancati ricavi tariffari e servizi aggiuntivi Covid (dal 2020)'),
            'linea_m4': blocco(m4, 'Capitolo di spesa "Linea M4 - servizi di TPL su nuova infrastruttura metropolitana" (dal 2021)'),
            'linea_m5': blocco(m5, 'Capitolo di spesa "Linea M5 - servizi di TPL su nuova infrastruttura metropolitana" (dal 2023)')},
    'dividendi': {**blocco(dividendi, 'Entrate da distribuzione di dividendi (tipologia 3, categoria 2 del titolo 3 delle entrate)'),
                  'societa': {str(k): v for k, v in div_cap.items()}},
}

# ------------------------------------------------------------------ cosa sorprende
def idx(a):
    return ANNI.index(a)


def share(a, b):
    return None if not b else a / b


spes = {
    'anno0': A0, 'anno1': A1,
    'nom0': M(tot_nom[A0]), 'nom1': M(tot_nom[A1]), 'var_nom': r1(tot_nom[A1] / tot_nom[A0] - 1, 4),
    'pc0': r1(tot_pc[i15], 0), 'pc1': r1(tot_pc[i25], 0), 'var_pc': r1(tot_pc[i25] / tot_pc[i15] - 1, 4),
    'pc_2024': r1(tot_pc[i24], 0), 'var_pc_2015_2024': r1(tot_pc[i24] / tot_pc[i15] - 1, 4),
    'pc_2016': r1(tot_pc[i16], 0), 'var_pc_2016_2025': r1(tot_pc[i25] / tot_pc[i16] - 1, 4),
    'var_pc_anagrafe_2015_2024': r1(tot_pc_anag[2024] / tot_pc_anag[2015] - 1, 4) if 2024 in tot_pc_anag and 2015 in tot_pc_anag else None,
    'pop0': int(pop_usata[A0]), 'pop1': int(pop_usata[A1]), 'pop_2024': int(pop_usata[2024]),
    'max_anno': ANNI[max(range(len(ANNI)), key=lambda i: tot_pc[i])], 'min_anno': ANNI[min(range(len(ANNI)), key=lambda i: tot_pc[i])],
    'min_pc': r1(min(tot_pc), 0), 'max_pc': r1(max(tot_pc), 0),
}
tpl_q = {a: tpl_tariffe[a] / tpl_spesa[a] for a in ANNI}
tpl_q2 = {a: (tpl_tariffe[a] + tpl_trasf[a]) / tpl_spesa[a] for a in ANNI}
trasporti_m10 = tab_miss[(10, A1)]
tpl_s = {
    'spesa_2015': M(tpl_spesa[2015]), 'spesa_2019': M(tpl_spesa[2019]), 'spesa_2025': M(tpl_spesa[2025]),
    'tariffe_2015': M(tpl_tariffe[2015]), 'tariffe_2019': M(tpl_tariffe[2019]), 'tariffe_2020': M(tpl_tariffe[2020]), 'tariffe_2025': M(tpl_tariffe[2025]),
    'quota_2015': r1(tpl_q[2015], 4), 'quota_2019': r1(tpl_q[2019], 4), 'quota_2025': r1(tpl_q[2025], 4),
    'quota_trasf_2015': r1(tpl_q2[2015], 4), 'quota_trasf_2025': r1(tpl_q2[2025], 4), 'trasf_2025': M(tpl_trasf[2025]),
    'quota_spesa_corrente_2025': r1(tpl_spesa[2025] / tot_nom[2025], 4), 'quota_missione10_2025': r1(trasporti_m10 / tot_nom[2025], 4),
    'm4_2021': M(m4[2021]), 'm4_2025': M(m4[2025]), 'm5_2023': M(m5[2023]), 'm5_2025': M(m5[2025]),
}
covid = {
    'ent_corr_2019': M(ent_corr[2019]), 'ent_corr_2020': M(ent_corr[2020]), 'var_ent_corr': r1(ent_corr[2020] / ent_corr[2019] - 1, 4),
    'serv_multe_2019': M(ent_tab['servizi'][2019] + ent_tab['multe'][2019]), 'serv_multe_2020': M(ent_tab['servizi'][2020] + ent_tab['multe'][2020]),
    'extra_2019': M(ent_tab['servizi'][2019] + ent_tab['multe'][2019] + ent_tab['dividendi'][2019] + ent_tab['altre'][2019]),
    'extra_2020': M(ent_tab['servizi'][2020] + ent_tab['multe'][2020] + ent_tab['dividendi'][2020] + ent_tab['altre'][2020]),
    'trasf_2019': M(ent_tab['trasferimenti'][2019]), 'trasf_2020': M(ent_tab['trasferimenti'][2020]), 'trasf_2021': M(ent_tab['trasferimenti'][2021]),
    'trib_2019': M(ent_tab['tributi'][2019]), 'trib_2020': M(ent_tab['tributi'][2020]),
}
covid['var_extra'] = M((ent_tab['servizi'][2020] + ent_tab['multe'][2020] + ent_tab['dividendi'][2020] + ent_tab['altre'][2020]) -
                       (ent_tab['servizi'][2019] + ent_tab['multe'][2019] + ent_tab['dividendi'][2019] + ent_tab['altre'][2019]))
covid['var_trasf'] = M(ent_tab['trasferimenti'][2020] - ent_tab['trasferimenti'][2019])
covid['var_trib'] = M(ent_tab['tributi'][2020] - ent_tab['tributi'][2019])
# capitolo statale Covid
cv = cap[(cap.tipo == 'entrate') & (cap.liv1 == 2) & cap.desc.str.contains('EMERGENZA COVID', case=False) & cap.desc.str.contains('TRASFERIMENTI STATALI DI CUI AI DECRETI', case=False)]
covid['decreti_stato'] = {str(a): M(cv[cv.anno == a].importo.sum()) for a in (2020, 2021, 2022)}
for r in cv.itertuples():
    voci_cap.append({'voce': 'trasferimenti_statali_covid', 'anno': int(r.anno), 'edizione': r.edizione, 'capitolo': r.desc, 'importo_euro': round(r.importo, 2)})
covid['fondo_ricavi_tariffari'] = {str(a): M(tpl_covid[a]) for a in (2020, 2021, 2022)}
div_s = {'div_2015': M(dividendi[2015]), 'div_2025': M(dividendi[2025]), 'x_nom': r1(dividendi[2025] / dividendi[2015], 2),
         'x_reale': r1(dividendi[2025] * defl(2025) / (dividendi[2015] * defl(2015)), 2),
         'quota_2015': r1(dividendi[2015] / ent_corr[2015], 4), 'quota_2025': r1(dividendi[2025] / ent_corr[2025], 4)}
sorprese = {'spesa': spes, 'tpl': tpl_s, 'covid': covid, 'dividendi': div_s}

# ------------------------------------------------------------------ prime voci di entrata 2025
top = cap[(cap.tipo == 'entrate') & (cap.anno == A1)].groupby(['liv1', 'desc']).importo.sum().reset_index().sort_values('importo', ascending=False).head(15)
TIT = {1: 'Tributi', 2: 'Trasferimenti correnti', 3: 'Entrate extratributarie', 4: 'Conto capitale', 5: 'Riduzione di attivita finanziarie', 6: 'Prestiti', 7: 'Anticipazioni', 9: 'Partite di giro e conto terzi'}
top_entrate = [{'titolo': int(r.liv1), 'tipo': TIT.get(int(r.liv1), ''), 'nome': r.desc, 'milioni': M(r.importo)} for r in top.itertuples()]

# ------------------------------------------------------------------ riepilogo.json
conteggio_ent_non_corr = {str(a): M(ent_non_corr[a]) for a in ANNI}
riepilogo = {
    'meta': {'data_scarico': DATA_SCARICO, 'anni': ANNI, 'primo': A0, 'ultimo': A1, 'base_prezzi': 2025,
             'pop_2025_stimata': True, 'edizioni_spesa': {str(k): v for k, v in ed_spesa.items()},
             'edizioni_entrate': {str(k): v for k, v in ed_entr.items()},
             'edizioni_capitoli': {str(k): v for k, v in ed_cap.items()}},
    'abitanti': {'usati': [int(pop_usata[a]) for a in ANNI], 'stima': [pop_stima[a] for a in ANNI],
                 'anagrafe': [None if (a not in pop_anag.index or math.isnan(pop_anag[a])) else int(pop_anag[a]) for a in ANNI]},
    'indice_foi': [float(foi[a]) for a in ANNI],
    'spesa': {'tutti_i_titoli_nom_milioni': [M(tot_tutti[a]) for a in ANNI], 'totale': {'nom_milioni': [M(tot_nom[a]) for a in ANNI], 'reale_milioni': [M(tot_real[i]) for i, a in enumerate(ANNI)],
                         'reale_pc': [r1(tot_pc[i], 2) for i in range(len(ANNI))]},
              'missioni': missioni},
    'entrate': {'gruppi': gruppi, 'correnti_nom_milioni': [M(ent_corr[a]) for a in ANNI],
                'correnti_reale_milioni': [M(ent_corr[a] * defl(a)) for a in ANNI],
                'correnti_reale_pc': [r1(ent_corr[a] * defl(a) / pop_usata[a], 2) for a in ANNI],
                'non_correnti_nom_milioni': [M(ent_non_corr[a]) for a in ANNI],
                'totale_nom_milioni': [M(ent_tot[a]) for a in ANNI],
                'tributi': tributi, 'top_2025': top_entrate},
    'voci': voci,
    'sosta_non_mostrata': {str(a): sosta[a] for a in (2015, 2019, 2020, 2023, 2024, 2025)},
    'sorprese': sorprese,
    'fonti': {'spesa_missioni': 'bilancio-comune/pulito/spesa_missioni.csv (fase=consuntivo, da_usare=1, titolo=1)',
              'entrate': 'bilancio-comune/pulito/entrate.csv (fase=consuntivo, da_usare=1)',
              'capitoli': 'bilancio-comune/pulito/bilancio_capitoli.csv (misura=rendiconto, edizione piu recente per anno)',
              'abitanti': 'bilancio-comune/pulito/popolazione_milano.csv, colonna pop_calcolata_istat_fine_anno (2025 = valore 2024)',
              'prezzi': 'bilancio-comune/pulito/indice_prezzi_annuo_FOI_da_strand12.csv, colonna indice_raccordato_2025_100'},
}
with open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8') as f:
    json.dump(riepilogo, f, ensure_ascii=False, separators=(',', ':'))

# ------------------------------------------------------------------ CSV scaricabili
def to_csv(rows, name):
    pd.DataFrame(rows).to_csv(os.path.join(OUT, name), sep=';', index=False, encoding='utf-8-sig')


rows = []
for mm in missioni:
    for i, a in enumerate(ANNI):
        rows.append({'anno': a, 'missione': mm['cod'], 'nome_semplice': mm['nome'], 'nome_ufficiale': mm['ufficiale'],
                     'spese_correnti_euro': round(tab_miss.get((mm['cod'], a), 0.0), 2),
                     'spese_correnti_euro_2025': round(mm['reale_milioni'][i] * 1e6, 0),
                     'abitanti_usati': int(pop_usata[a]), 'abitanti_stimati': pop_stima[a],
                     'euro_2025_per_abitante': mm['reale_pc'][i], 'edizione_fonte': ed_spesa.get(a)})
to_csv(rows, 'spesa_per_missione.csv')

rows = []
for g in gruppi:
    for i, a in enumerate(ANNI):
        rows.append({'anno': a, 'tipo_entrata': g['nome'], 'importo_euro': round(ent_tab[g['id']][a], 2),
                     'importo_euro_2025': round(g['reale_milioni'][i] * 1e6, 0), 'euro_2025_per_abitante': g['reale_pc'][i],
                     'abitanti_stimati': pop_stima[a], 'regola': g['spiega'], 'fonte': ed_entr.get(a)})
to_csv(rows, 'entrate_per_tipo.csv')

rows = []
for t in tributi:
    for i, a in enumerate(ANNI):
        rows.append({'anno': a, 'voce': t['nome'], 'importo_euro': round((t['nom_milioni'][i] or 0) * 1e6, 0)})
to_csv(rows, 'tributi_principali.csv')

rows = []
def add(voce, nom, nota=''):
    for a in ANNI:
        rows.append({'anno': a, 'voce': voce, 'importo_euro': round(nom[a], 2), 'importo_euro_2025': round(nom[a] * defl(a), 0), 'nota': nota})
add('Multe del codice della strada (anno corrente)', multe, '2015-2016: il capitolo include anche i regolamenti comunali; sono accertamenti, non incassi')
add('Multe del codice della strada (esercizi precedenti)', multe_prec, 'capitoli con nomi diversi nel 2015-2019 e dal 2020: equivalenza stimata dal nome')
add('Recupero spese postali per notifica verbali', spese_postali, 'rimborso spese, non una multa')
add('Area C (proventi ZTL Area C)', area_c)
add('ZTL - nuova tariffazione accesso al centro storico', ztl_nuova, 'capitolo dal 2020')
add('Imposta di soggiorno', soggiorno, 'somma dei capitoli con nome diverso prima e dopo il 2020: stima per nome')
add('Trasporto pubblico locale - spesa corrente (missione 10 programma 2)', tpl_spesa)
add('Trasporto pubblico locale - proventi da tariffe', tpl_tariffe)
add('Trasporto pubblico locale - trasferimenti Regione/Agenzia', tpl_trasf, 'tre nomi diversi nel tempo, considerati lo stesso flusso')
add('Trasporto pubblico locale - fondi dello Stato (mancati ricavi, Covid)', tpl_covid)
add('Spesa linea M4 (servizi TPL su nuova infrastruttura)', m4, 'capitolo dal 2021')
add('Spesa linea M5 (servizi TPL su nuova infrastruttura)', m5, 'capitolo dal 2023')
add('Dividendi', dividendi, 'A2A, SEA, Farmacie milanesi, ATM nel 2017')
to_csv(rows, 'voci_concrete.csv')

to_csv(sorted(voci_cap, key=lambda r: (r['voce'], r['anno'], r['capitolo'])), 'capitoli_usati.csv')
to_csv([{'posizione': i + 1, 'titolo_entrata': t['tipo'], 'voce': t['nome'], 'importo_euro_2025_nominale': round(t['milioni'] * 1e6, 0)} for i, t in enumerate(top_entrate)], 'entrate_prime_voci_2025.csv')
to_csv([{'anno': a, 'abitanti_istat_calcolata': None if math.isnan(pop_istat.get(a, float('nan'))) else int(pop_istat[a]),
         'abitanti_anagrafe_somma_quartieri': None if (a not in pop_anag.index or math.isnan(pop_anag[a])) else int(pop_anag[a]),
         'abitanti_usati': int(pop_usata[a]), 'abitanti_stimati': pop_stima[a], 'indice_FOI_2025_100': float(foi[a])} for a in ANNI], 'abitanti_e_prezzi.csv')

# ------------------------------------------------------------------ riepilogo a video
print('Scritti i file in', OUT)
print('spesa pro capite euro 2025:', {a: round(tot_pc[i]) for i, a in enumerate(ANNI)})
print(json.dumps(sorprese, ensure_ascii=False, indent=1))
print('multe', {a: M(multe[a]) for a in ANNI})
print('multe prec', {a: M(multe_prec[a]) for a in ANNI})
print('soggiorno', {a: M(soggiorno[a]) for a in ANNI})
print('area c', {a: M(area_c[a]) for a in ANNI})
print('tpl trasf', {a: M(tpl_trasf[a]) for a in ANNI})
print('tributi', [(t['id'], t['nom_milioni'][0], t['nom_milioni'][-1]) for t in tributi])
print('entrate correnti', {a: M(ent_corr[a]) for a in ANNI})
