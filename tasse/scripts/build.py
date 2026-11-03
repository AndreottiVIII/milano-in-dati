"""Costruisce i dati della pagina docs/tasse/ e i controlli automatici.

Uso: python -I -X utf8 build.py <cartella tasse> <cartella milano-in-dati>

Legge (sola lettura):
  bilancio-comune: docs/bilancio-comune/data (tributi, capitoli, entrate), pulito/indice FOI
  tasse/pulito: tabelle gia' estratte (Ministero Interno 2016-2018, SIOPE, MEF, popolazione)
Scrive:
  docs/tasse/data/*.csv e riepilogo.json
  tasse/out/controlli.txt
"""
import sys, os, re, json, math
import pandas as pd

BASE, ROOT = sys.argv[1], sys.argv[2]
PUL = os.path.join(BASE, 'pulito')
DOCB = os.path.join(ROOT, 'docs', 'bilancio-comune', 'data')
OUT = os.path.join(ROOT, 'docs', 'tasse', 'data')
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(BASE, 'out'), exist_ok=True)

CTRL = []
FAIL = [0]


def ctrl(ok, msg):
    CTRL.append(('OK    ' if ok else 'ERRORE') + ' ' + msg)
    if not ok:
        FAIL[0] += 1


def M(x, nd=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x) / 1e6, nd)


def R(x, nd=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), nd)


ANNI = list(range(2015, 2026))
CITTA = ['milano', 'roma', 'torino', 'napoli', 'bologna', 'firenze', 'genova']
NOME = {c: c.capitalize() for c in CITTA}

# ------------------------------------------------------------------ abitanti e prezzi
pop = pd.read_csv(os.path.join(PUL, 'popolazione_1gen_citta.csv'), sep=';')
P = {(r.citta, int(r.anno_1_gennaio)): int(r.residenti) for r in pop.itertuples()}
foi = pd.read_csv(os.path.join(ROOT, 'bilancio-comune', 'pulito', 'indice_prezzi_annuo_FOI_da_strand12.csv'))
FOI = {int(r.anno): float(r.indice_raccordato_2025_100) for r in foi.itertuples()}


def euro25(v, a):
    return v * 100.0 / FOI[a]


# ------------------------------------------------------------------ PARTE 1: accertato del Comune di Milano (bilancio gia' pubblicato)
cap = pd.read_csv(os.path.join(DOCB, 'capitoli_usati.csv'), sep=';', encoding='utf-8-sig')
cap = cap[cap.voce.isin(['casa', 'rifiuti', 'irpef', 'soggiorno', 'evasione'])].copy()


def classe(r):
    d = r.capitolo.upper()
    if r.voce == 'evasione':
        if re.search(r'\bIMU\b|I\.?C\.?I\.?\b|TASI', d):
            return 'ev_casa'
        if re.search(r'TARI|TARES|TARSU|T\.A\.R\.S\.U', d):
            return 'ev_rifiuti'
        if 'SOGGIORNO' in d:
            return 'ev_soggiorno'
        if re.search(r'ICP|I\.C\.P|PUBBLICIT', d):
            return 'ev_pubblicita'
        return 'ev_altri'
    if r.voce == 'casa':
        return 'tasi' if re.search(r'TASI|INDIVISIBILI', d) else 'imu'
    if r.voce == 'irpef':
        return 'imbarco' if 'IMBARCO' in d else 'addizionale'
    if r.voce == 'rifiuti':
        return 'tari'
    return 'soggiorno'


cap['t'] = cap.apply(classe, axis=1)
ACC = cap.pivot_table(index='anno', columns='t', values='importo_euro', aggfunc='sum').fillna(0.0)
for c in ['ev_altri', 'ev_pubblicita', 'ev_soggiorno', 'tasi', 'imbarco', 'ev_casa', 'ev_rifiuti']:
    if c not in ACC:
        ACC[c] = 0.0
ctrl(cap.groupby('anno').edizione.nunique().max() == 1, 'una sola edizione del bilancio per ogni anno (capitoli_usati.csv)')
ev_tot = ACC[['ev_casa', 'ev_rifiuti', 'ev_soggiorno', 'ev_pubblicita', 'ev_altri']].sum(axis=1)

# controllo contro i tributi principali gia' pubblicati
tp = pd.read_csv(os.path.join(DOCB, 'tributi_principali.csv'), sep=';', encoding='utf-8-sig')
tpp = tp.pivot_table(index='anno', columns='voce', values='importo_euro', aggfunc='sum')
chk = {
    'IMU e TASI (imposte sulla casa)': ACC.imu + ACC.tasi,
    'TARI (tassa sui rifiuti)': ACC.tari,
    'Addizionale comunale IRPEF': ACC.addizionale + ACC.imbarco,
    'Imposta di soggiorno': ACC.soggiorno,
    'Recupero evasione (IMU, TARI, pubblicità, altri)': ev_tot,
}
for k, s in chk.items():
    d = max(abs(tpp[k].get(a, 0) - s.get(a, 0)) for a in ANNI)
    ctrl(d < 20000, f'totali uguali a docs/bilancio-comune (tributi_principali.csv) per "{k}": differenza massima {d:,.0f} euro')

# entrate correnti (titoli 1-3) dalla pagina del bilancio
ent = pd.read_csv(os.path.join(DOCB, 'entrate_per_tipo.csv'), sep=';', encoding='utf-8-sig')
ent_corr = ent.groupby('anno').importo_euro.sum()
ent_trib = ent[ent.tipo_entrata.str.startswith('Tributi')].set_index('anno').importo_euro

# ------------------------------------------------------------------ serie Milano (accertato di competenza)
TR = [('imu', 'IMU'), ('tasi', 'TASI'), ('tari', 'TARI'), ('addizionale', 'Addizionale comunale IRPEF'),
      ('soggiorno', 'Imposta di soggiorno')]
serie = []
for a in ANNI:
    ab = P[('milano', a)]
    row = {'anno': a, 'abitanti_1_gennaio': ab, 'foi_2025_100': FOI[a]}
    for k, _ in TR:
        row[k + '_euro'] = round(float(ACC.loc[a, k]), 2)
    row['recupero_evasione_euro'] = round(float(ev_tot[a]), 2)
    row['recupero_evasione_casa_euro'] = round(float(ACC.loc[a, 'ev_casa']), 2)
    row['recupero_evasione_rifiuti_euro'] = round(float(ACC.loc[a, 'ev_rifiuti']), 2)
    row['recupero_evasione_altri_euro'] = round(float(ev_tot[a] - ACC.loc[a, 'ev_casa'] - ACC.loc[a, 'ev_rifiuti']), 2)
    quattro = sum(ACC.loc[a, k] for k, _ in TR)
    row['quattro_tributi_euro'] = round(float(quattro), 2)
    row['entrate_correnti_euro'] = round(float(ent_corr[a]), 2)
    row['tributi_titolo1_euro'] = round(float(ent_trib[a]), 2)
    row['quota_quattro_su_entrate_correnti'] = round(float(quattro / ent_corr[a]), 4)
    row['quota_quattro_su_tributi'] = round(float(quattro / ent_trib[a]), 4)
    serie.append(row)
pd.DataFrame(serie).to_csv(os.path.join(OUT, 'milano_accertato_tributi.csv'), sep=';', index=False)

# ------------------------------------------------------------------ cassa SIOPE
sio = pd.read_csv(os.path.join(PUL, 'siope_tributi.csv'), sep=';')
GR = {'IMU': 'casa', 'TASI': 'casa', 'ICI': 'casa', 'Addizionale IRPEF': 'addizionale', 'Imposta di soggiorno': 'soggiorno',
      'Rifiuti (TARI/TARSU)': 'rifiuti', 'Rifiuti (TARES)': 'rifiuti', 'Occupazione suolo': 'altre',
      'Pubblicita e affissioni': 'altre', 'Altre imposte e tasse': 'altre'}
sio['gr'] = sio.tributo.map(GR)
sp = sio[sio.gr.notna()]
cassa = sp.pivot_table(index=['citta', 'anno'], columns='gr', values='incassi_euro', aggfunc='sum').fillna(0.0)
cassa['totale'] = cassa.sum(axis=1)
disp = sorted(set(sio.citta.unique()))
ctrl(True, 'SIOPE: citta presenti nei dati scaricati: ' + ', '.join(disp))
anni_cassa = {c: sorted(cassa.loc[c].index) for c in disp if c in cassa.index.get_level_values(0)}

# controllo: SIOPE Milano 2016-2018 = riscossioni (competenza + residui) del Ministero, tipologia 101
q2 = pd.read_csv(os.path.join(PUL, 'ministero_q2_entrate_gestione.csv'), sep=';')
q9 = pd.read_csv(os.path.join(PUL, 'ministero_q9_accertamenti.csv'), sep=';')
q18 = pd.read_csv(os.path.join(PUL, 'ministero_q18_fcde.csv'), sep=';')
q20 = pd.read_csv(os.path.join(PUL, 'ministero_q20_indicatori.csv'), sep=';')
q1 = pd.read_csv(os.path.join(PUL, 'ministero_q1_popolazione.csv'), sep=';')
ip = q2[q2.voce.str.startswith('Imposte tasse')]
for c, a in [('milano', 2016)] + [(c_, 2018) for c_ in CITTA]:
    r = ip[(ip.citta == c) & (ip.anno == a)].iloc[0]
    tot_min = r.RC + r.RR
    # SIOPE: stesse voci della tipologia 101 (esclude fondi perequativi e compartecipazioni)
    s_ = float(cassa.loc[(c, a), 'totale']) if (c, a) in cassa.index else float('nan')
    ctrl(abs(tot_min - s_) / tot_min < 0.005, f'incassi {NOME[c]} {a}: SIOPE {s_/1e6:,.1f} M contro Ministero (riscossioni competenza + residui, imposte e tasse) {tot_min/1e6:,.1f} M')

# controllo: bilancio gia' pubblicato = Ministero (accertamenti 2016-2018), Milano
# Nel quadro 9 i nomi delle righe cambiano da un anno all'altro: nel 2016 la TARI sta nella riga "Altre imposte, tasse e
# proventi" e la TASI si chiama "Tassa sui servizi comunali". Per questo per il confronto fra citta' si usa solo il totale
# "Imposte, tasse e proventi assimilati".
PREF = {
    2016: {'IMU': ['Imposta municipale propria', 'Imposta comunale sugli immobili'],
           'TASI': ['Tassa sui servizi comunali'],
           'TARI': ['Tassa smaltimento rifiuti solidi urbani', 'Tributo comunale sui rifiuti e sui servizi', 'Altre imposte, tasse e proventi n.a.c.']},
    2017: {'IMU': ['Imposta municipale propria', 'Imposta comunale sugli immobili'],
           'TASI': ['Tributo per i servizi indivisibili'],
           'TARI': ['Tassa sui rifiuti (TARI)', 'Tassa per la raccolta', 'Tributo comunale sui rifiuti e sui servizi']},
}
PREF[2018] = PREF[2017]
for t in ('IMU', 'TASI', 'TARI'):
    pass
CON_Q9 = {}


def q9grp(c, a, tributo):
    g = q9[(q9.citta == c) & (q9.anno == a)]
    pre = PREF[a][tributo]
    x = g[g.voce.apply(lambda v: any(v.startswith(p) for p in pre))]
    return x


for a in (2016, 2017, 2018):
    g = q9[(q9.citta == 'milano') & (q9.anno == a)]

    def v(prefix):
        x = g[g.voce.str.startswith(prefix)]
        return float(x.accertamenti.sum())
    add_m = v('Addizionale comunale IRPEF')
    sog_m = v('Imposta di soggiorno')
    ctrl(abs(add_m - ACC.loc[a, 'addizionale']) < 20000, f'addizionale {a}: Ministero {add_m/1e6:,.2f} M = bilancio {ACC.loc[a,"addizionale"]/1e6:,.2f} M')
    ctrl(abs(sog_m - ACC.loc[a, 'soggiorno']) < 20000, f'imposta di soggiorno {a}: Ministero {sog_m/1e6:,.2f} M = bilancio {ACC.loc[a,"soggiorno"]/1e6:,.2f} M')
    imu_m = float(q9grp('milano', a, 'IMU').accertamenti.sum())
    tasi_m = float(q9grp('milano', a, 'TASI').accertamenti.sum())
    imu_b = ACC.loc[a, 'imu'] + ACC.loc[a, 'ev_casa']
    ctrl(abs((imu_m + tasi_m) - (imu_b + ACC.loc[a, 'tasi'])) / (imu_m + tasi_m) < 0.01,
         f'IMU+ICI+TASI con recupero {a}: Ministero {(imu_m+tasi_m)/1e6:,.1f} M, bilancio {(imu_b+ACC.loc[a,"tasi"])/1e6:,.1f} M (scarto sotto 1%)')
    tari_m = float(q9grp('milano', a, 'TARI').accertamenti.sum())
    tari_b = ACC.loc[a, 'tari'] + ACC.loc[a, 'ev_rifiuti']
    ctrl(abs(tari_m - tari_b) / tari_m < 0.02, f'rifiuti con recupero {a}: Ministero {tari_m/1e6:,.1f} M, bilancio {tari_b/1e6:,.1f} M (scarto sotto 2%)')

# ------------------------------------------------------------------ confronto fra citta: incassi (cassa) per abitante, media 2019-2025
ANNI_CFR = list(range(2019, 2026))
conf = []
for c in CITTA:
    if c not in anni_cassa:
        continue
    ok = [a for a in ANNI_CFR if a in anni_cassa[c]]
    if len(ok) < len(ANNI_CFR):
        continue
    abit = sum(P[(c, a)] for a in ok)
    row = {'citta': NOME[c], 'anni': f'{ok[0]}-{ok[-1]}', 'n_anni': len(ok), 'abitanti_media': round(abit / len(ok))}
    # Le righe rifiuti / soggiorno / altre non si possono separare in modo uguale per tutte le citta' (Roma registra la TARI
    # come TARES e l'imposta di soggiorno fra le "altre imposte"): le sommiamo insieme.
    for g, cols in [('casa', ['casa']), ('addizionale', ['addizionale']), ('rifiuti_soggiorno_altre', ['rifiuti', 'soggiorno', 'altre']),
                    ('totale', ['totale'])]:
        s = sum(float(cassa.loc[(c, a), k]) for a in ok for k in cols if k in cassa.columns)
        row[g + '_euro_per_abitante_anno'] = round(s / abit, 1)
    conf.append(row)
conf_df = pd.DataFrame(conf)
if len(conf_df):
    conf_df.to_csv(os.path.join(OUT, 'citta_incassi_per_abitante.csv'), sep=';', index=False)
ctrl(len(conf_df) >= 5, f'confronto fra citta (incassi 2019-2025): {len(conf_df)} citta con tutti i 7 anni')

# ------------------------------------------------------------------ cassa Milano e rapporto con accertato
mil_cassa = []
for a in ANNI:
    if ('milano', a) not in cassa.index:
        continue
    c = cassa.loc[('milano', a)]
    sm = sio[(sio.citta == 'milano') & (sio.anno == a)]
    ver = float(sm[sm.tipo == 'verifica_controllo'].incassi_euro.sum())
    mil_cassa.append({'anno': a, 'casa': float(c.get('casa', 0)), 'rifiuti': float(c.get('rifiuti', 0)),
                      'addizionale': float(c.get('addizionale', 0)), 'soggiorno': float(c.get('soggiorno', 0)),
                      'altre': float(c.get('altre', 0)), 'totale': float(c['totale']), 'di_cui_verifica_controllo': ver})
pd.DataFrame(mil_cassa).to_csv(os.path.join(OUT, 'milano_incassi_cassa.csv'), sep=';', index=False)
MC = {r['anno']: r for r in mil_cassa}

# ------------------------------------------------------------------ PARTE 4: chi non paga
# 4a. Ministero 2016-2018, sette citta': imposte e tasse (tipologia 101)
def q9row(c, a, pref):
    g = q9[(q9.citta == c) & (q9.anno == a) & q9.voce.str.startswith(pref)]
    return g


cfr_min = []
for c in CITTA:
    rr = []
    for a in (2016, 2017, 2018):
        r = ip[(ip.citta == c) & (ip.anno == a)].iloc[0]
        f = q18[(q18.citta == c) & (q18.anno == a) & q18.voce.str.startswith('Imposte, tasse')]
        fp = float(f.perc_accantonamento.iloc[0]) if len(f) else None
        pab = int(q1[(q1.citta == c) & (q1.anno == a)].popolazione_residente.iloc[0])
        rr.append({'citta': NOME[c], 'anno': a, 'accertato': float(r.A), 'riscosso_competenza': float(r.RC),
                   'riscosso_residui': float(r.RR), 'residui_inizio': float(r.RS), 'residui_fine': float(r.TR_RESIDUI),
                   'residui_da_anni_prec': float(r.EP), 'residui_da_anno': float(r.EC), 'fcde_perc': fp, 'abitanti_rendiconto': pab})
    cfr_min.extend(rr)
cfr_min = pd.DataFrame(cfr_min)
cfr_min.to_csv(os.path.join(OUT, 'citta_riscossione_2016_2018.csv'), sep=';', index=False)
ctrl(len(cfr_min) == 21, 'Ministero: 7 citta x 3 anni, quadro 2 letto per tutte')

# ordine di grandezza di coerenza: RS + A - RC - RR + R = residui fine
for r in cfr_min.itertuples():
    pass
chk_res = ip.copy()
chk_res['calc'] = chk_res.RS - chk_res.RR + chk_res.R + chk_res.A - chk_res.RC
ctrl(((chk_res.calc - chk_res.TR_RESIDUI).abs() < 5).all(), 'Ministero quadro 2: residui finali = iniziali - riscosso + riaccertato + accertato - riscosso in competenza (tutte le righe)')

# 4b. Milano per tributo 2016-2018 dal quadro 9
mil_trib_min = []
for a in (2016, 2017, 2018):
    for nome, tt in [('IMU (compreso il recupero)', 'IMU'), ('TASI', 'TASI'), ('TARI (compreso il recupero)', 'TARI')]:
        g = q9grp('milano', a, tt)
        mil_trib_min.append({'anno': a, 'tributo': nome, 'accertato': float(g.accertamenti.sum()),
                             'riscosso_competenza': float(g.riscossioni_competenza.sum()),
                             'riscosso_residui': float(g.riscossioni_residui.sum())})
    for nome, pref in [('Addizionale IRPEF', 'Addizionale comunale IRPEF'), ('Imposta di soggiorno', 'Imposta di soggiorno')]:
        g = q9[(q9.citta == 'milano') & (q9.anno == a) & q9.voce.str.startswith(pref)]
        mil_trib_min.append({'anno': a, 'tributo': nome, 'accertato': float(g.accertamenti.sum()),
                             'riscosso_competenza': float(g.riscossioni_competenza.sum()),
                             'riscosso_residui': float(g.riscossioni_residui.sum())})
pd.DataFrame(mil_trib_min).to_csv(os.path.join(OUT, 'milano_tributi_riscossione_2016_2018.csv'), sep=';', index=False)

# 4c. Milano 2024 e 2025: rendiconti (pareri dei revisori, documenti del Comune), numeri trascritti e controllati
# Fonte: parere dell'Organo di revisione sul Rendiconto 2024 e sul Rendiconto 2025, tabelle "principali entrate correnti"
# (accertamenti di competenza e residuo di competenza = non incassato nell'anno).
RENDICONTI = {
    2024: {'soggiorno': (80176337.11, 16797267.77), 'imu': (777817854.10, 1517196.48), 'tari': (322111673.29, 93011727.32),
           'addizionale': (240000000.00, 151237709.21), 'recupero_evasione': (90076215.31, 66716692.56),
           'titolo1': (1535365730.85, 329287670.44), 'titolo1_incassi_competenza': 1206078060.41},
    2025: {'soggiorno': (114000245.42, 21484633.13), 'imu': (776848468.85, 1647465.66), 'tari': (304257291.15, 86120345.04),
           'addizionale': (250000000.00, 156450433.60), 'recupero_evasione': (112648635.29, 74832453.03),
           'titolo1': (1563219500.80, 340535330.46), 'titolo1_incassi_competenza': 1222684170.34},
}
for a, d in RENDICONTI.items():
    ctrl(abs(d['titolo1'][0] - d['titolo1_incassi_competenza'] - d['titolo1'][1]) < 5,
         f'rendiconto {a}: accertato - incassato in competenza = residuo di competenza (Titolo 1)')
    # accertato dei rendiconti = accertato gia' pubblicato nella pagina del bilancio
    for k, kk in [('soggiorno', 'soggiorno'), ('imu', 'imu'), ('tari', 'tari')]:
        ctrl(abs(d[k][0] - ACC.loc[a, kk]) < 5, f'rendiconto {a}: {k} accertato {d[k][0]/1e6:,.2f} M = bilancio gia pubblicato {ACC.loc[a,kk]/1e6:,.2f} M')
    ctrl(abs(d['recupero_evasione'][0] - ev_tot[a]) < 5, f'rendiconto {a}: recupero evasione accertato = bilancio gia pubblicato ({ev_tot[a]/1e6:,.2f} M)')
    ctrl(abs(d['addizionale'][0] - ACC.loc[a, 'addizionale']) < 100000, f'rendiconto {a}: addizionale accertata = bilancio ({ACC.loc[a,"addizionale"]/1e6:,.2f} M, esclusi i diritti d\'imbarco)')

# recupero evasione: dettaglio 2024 e 2025 (tabella dei revisori)
EVASIONE = {
    2024: {'totale': (90076215.31, 23359522.75), 'imu_ici': (66240172.48, 15863163.53), 'tasi': (112602.29, 41970.71),
           'rifiuti': (19663522.23, 6528590.92), 'soggiorno': (457448.20, 3907.80), 'pubblicita': (3602470.11, 921889.79),
           'residui_inizio': 315661001.95, 'residui_riscossi': 33075831.31, 'residui_eliminati': 83815431.19,
           'residui_fine_anni_prec': 198769739.45, 'residui_competenza': 66716692.56, 'residui_totali': 265486432.01,
           'fcde': 188999790.95, 'fcde_perc': 71.19},
    2025: {'totale': (112648635.29, 37816182.26), 'imu_ici': (81594848.06, 25663197.53), 'tasi': (42001.71, 42001.71),
           'rifiuti': (29081969.57, 11595461.36), 'soggiorno': (106524.60, 93.60), 'pubblicita': (1823291.35, 515428.06),
           'residui_inizio': 265486432.01, 'residui_riscossi': 28602293.11, 'residui_eliminati': 47225400.55,
           'residui_fine_anni_prec': 189658738.35, 'residui_competenza': 74832453.03, 'residui_totali': 264491191.38,
           'fcde': 173135933.88, 'fcde_perc': 65.46},
}
for a, d in EVASIONE.items():
    s_acc = sum(d[k][0] for k in ('imu_ici', 'tasi', 'rifiuti', 'soggiorno', 'pubblicita'))
    s_ris = sum(d[k][1] for k in ('imu_ici', 'tasi', 'rifiuti', 'soggiorno', 'pubblicita'))
    ctrl(abs(s_acc - d['totale'][0]) < 5 and abs(s_ris - d['totale'][1]) < 5, f'recupero evasione {a}: le voci sommano al totale (accertato {s_acc/1e6:,.2f} M, riscosso {s_ris/1e6:,.2f} M)')
    ctrl(abs(d['residui_inizio'] - d['residui_riscossi'] - d['residui_eliminati'] - d['residui_fine_anni_prec']) < 5, f'recupero evasione {a}: residui iniziali - riscossi - eliminati = residui rimasti')
    ctrl(abs(d['residui_fine_anni_prec'] + d['residui_competenza'] - d['residui_totali']) < 5, f'recupero evasione {a}: residui rimasti + residui dell anno = totale')
    ctrl(abs(d['residui_competenza'] - (d['totale'][0] - d['totale'][1])) < 5, f'recupero evasione {a}: residuo dell anno = accertato - riscosso')
    ctrl(abs(d['residui_competenza'] - RENDICONTI[a]['recupero_evasione'][1]) < 5, f'recupero evasione {a}: residuo dell anno uguale a quello della tabella delle entrate')
ctrl(abs(EVASIONE[2025]['residui_inizio'] - EVASIONE[2024]['residui_totali']) < 5, 'recupero evasione: residui totali 2024 = residui iniziali 2025')

# anzianita' dei residui attivi del Titolo 1 (tutte le entrate tributarie), 31/12
ANZ = {
    2024: {'etichette': ['2019 e prima', '2020', '2021', '2022', '2023', '2024'],
           'valori': [63276899.37, 62129342.60, 58083184.90, 88745443.32, 123315903.93, 329287670.44], 'totale': 724838444.56,
           'stralci': 310945801.43, 'stralci_anni': '2017 e 2018', 'riscosso_su_residui_perc': 22.5},
    2025: {'etichette': ['2020 e prima', '2021', '2022', '2023', '2024', '2025'],
           'valori': [52115051.53, 47557971.58, 79522951.75, 84213638.59, 111042482.54, 340535330.46], 'totale': 714987426.45,
           'stralci': 141343587.65, 'stralci_anni': '2019', 'riscosso_su_residui_perc': 23.0},
}
for a, d in ANZ.items():
    ctrl(abs(sum(d['valori']) - d['totale']) < 5, f'residui attivi Titolo 1 al 31/12/{a}: le fasce di anzianita sommano al totale ({d["totale"]/1e6:,.1f} M)')
    ctrl(abs(d['valori'][-1] - RENDICONTI[a]['titolo1'][1]) < 5, f'residui Titolo 1 {a}: la fascia dell anno = residuo di competenza')

# serie dei residui di Titolo 1 / imposte e tasse a fine anno
res_serie = []
for a in (2016, 2017, 2018):
    r = ip[(ip.citta == 'milano') & (ip.anno == a)].iloc[0]
    res_serie.append({'anno': a, 'residui_fine': float(r.TR_RESIDUI), 'di_cui_anni_precedenti': float(r.EP), 'di_cui_anno': float(r.EC),
                      'accertato_anno': float(r.A), 'fonte': 'Ministero dell\'Interno, certificato al rendiconto, quadro 2, imposte tasse e proventi assimilati'})
for a in (2024, 2025):
    d = ANZ[a]
    res_serie.append({'anno': a, 'residui_fine': d['totale'], 'di_cui_anni_precedenti': d['totale'] - d['valori'][-1], 'di_cui_anno': d['valori'][-1],
                      'accertato_anno': RENDICONTI[a]['titolo1'][0], 'fonte': 'parere dei revisori sul rendiconto, Titolo 1'})
pd.DataFrame(res_serie).to_csv(os.path.join(OUT, 'milano_residui_tributi.csv'), sep=';', index=False)

# ------------------------------------------------------------------ PARTE 3: IRPEF (MEF) e popolazione
mef = pd.read_csv(os.path.join(PUL, 'mef_citta.csv'), sep=';')
cl = pd.read_csv(os.path.join(PUL, 'mef_milano_classi.csv'), sep=';')
irp = []
for c in CITTA:
    x = mef[(mef.citta == c) & (mef.anno == 2024)].iloc[0]
    ab = P[(c, 2025)]
    irp.append({'citta': NOME[c], 'anno_imposta': 2024, 'contribuenti': int(x.contribuenti), 'abitanti_1_1_2025': ab,
                'irpef_netta_euro': float(x.imposta_netta_eur), 'irpef_per_contribuente': round(x.imposta_netta_eur / x.contribuenti, 1),
                'irpef_per_abitante': round(x.imposta_netta_eur / ab, 1), 'addizionale_comunale_euro': float(x.addiz_com_eur),
                'addizionale_per_contribuente': round(x.addiz_com_eur / x.contribuenti, 1),
                'addizionale_su_irpef_perc': round(100 * x.addiz_com_eur / x.imposta_netta_eur, 2),
                'contribuenti_con_addizionale': int(x.addiz_com_n), 'contribuenti_con_imponibile_addizionale': int(x.imponibile_addiz_n),
                'aliquota_media_effettiva_perc': round(100 * x.addiz_com_eur / x.imponibile_addiz_eur, 3)})
pd.DataFrame(irp).to_csv(os.path.join(OUT, 'irpef_citta_2024.csv'), sep=';', index=False)

irpef_mil = []
for a in range(2000, 2025):
    x = mef[(mef.citta == 'milano') & (mef.anno == a)].iloc[0]
    abn = P.get(('milano', a + 1))
    irpef_mil.append({'anno_imposta': a, 'contribuenti': int(x.contribuenti), 'irpef_netta_euro': float(x.imposta_netta_eur),
                      'irpef_netta_euro_2025': round(euro25(float(x.imposta_netta_eur), min(a, 2025)), 0),
                      'irpef_per_contribuente_euro_2025': round(euro25(float(x.imposta_netta_eur), a) / x.contribuenti, 1),
                      'addizionale_comunale_euro': float(x.addiz_com_eur),
                      'abitanti_1_gennaio_anno_dopo': abn})
pd.DataFrame(irpef_mil).to_csv(os.path.join(OUT, 'irpef_milano_serie.csv'), sep=';', index=False)

# controllo: dati MEF = dataset del Comune (ds312) per l'addizionale e l'imposta netta
ds = pd.read_csv(os.path.join(ROOT, 'bilancio-comune', 'raw', 'ckan_ds312', 'ds312_economia_variabili_irpefaddizionale_comunale_regionale_-1.csv'), sep=';')
dd = ds[ds.Variabile == 'Addizionale comunale dovuta'].set_index('Anno di Imposta')['Ammontare in euro']
dn = ds[ds.Variabile == 'Imposta netta'].set_index('Anno di Imposta')['Ammontare in euro']
mm = mef[mef.citta == 'milano'].set_index('anno')
dmax = max(abs(dd[a] - mm.loc[a, 'addiz_com_eur']) for a in dd.index if a in mm.index)
dmax2 = max(abs(dn[a] - mm.loc[a, 'imposta_netta_eur']) for a in dn.index if a in mm.index)
ctrl(dmax < 1 and dmax2 < 1, f'IRPEF Milano 2012-2024: MEF = dataset del Comune (ds312), addizionale e imposta netta, differenza massima {max(dmax,dmax2):.2f} euro')

# classi di reddito Milano 2024
c24 = cl[cl.anno == 2024]
ETIC = {'cl0_le0': 'fino a 0', 'cl1_0_10k': '0 - 10.000', 'cl2_10_15k': '10.000 - 15.000', 'cl3_15_26k': '15.000 - 26.000',
        'cl4_26_55k': '26.000 - 55.000', 'cl5_55_75k': '55.000 - 75.000', 'cl6_75_120k': '75.000 - 120.000', 'cl7_oltre120k': 'oltre 120.000'}
tn, te = c24.contribuenti.sum(), c24.reddito_euro.sum()
classi = [{'classe': ETIC[r.classe], 'contribuenti': int(r.contribuenti), 'reddito_euro': float(r.reddito_euro),
           'quota_contribuenti': round(r.contribuenti / tn, 4), 'quota_reddito': round(r.reddito_euro / te, 4)} for r in c24.itertuples()]
pd.DataFrame(classi).to_csv(os.path.join(OUT, 'milano_classi_reddito_2024.csv'), sep=';', index=False)
x24 = mef[(mef.citta == 'milano') & (mef.anno == 2024)].iloc[0]
ctrl(abs(te - x24.reddito_complessivo_eur) / te < 0.001, f'Milano 2024: somma dei redditi delle classi = campo reddito complessivo MEF ({te/1e9:,.2f} miliardi)')

# ------------------------------------------------------------------ ESEMPI (ipotesi in chiaro; ogni aliquota ha fonte)
RENDITA = 1000.0
base_imu = RENDITA * 1.05 * 160
ES_IMU = [
    {'caso': 'Seconda casa tenuta a disposizione (altri fabbricati)', 'aliquota_perc': 1.14, 'riduzione': 0, 'imu': round(base_imu * 0.0114, 0)},
    {'caso': 'Casa affittata a canone libero', 'aliquota_perc': 1.04, 'riduzione': 0, 'imu': round(base_imu * 0.0104, 0)},
    {'caso': 'Casa affittata a canone concordato (inquilino che ci abita)', 'aliquota_perc': 0.73, 'riduzione': 25, 'imu': round(base_imu * 0.0073 * 0.75, 0)},
]
ALIQ_ADD = 0.008
SOGLIA_ADD = 23000
def addiz(reddito):
    return round(reddito * ALIQ_ADD, 0) if reddito > SOGLIA_ADD else 0.0
PROFILI = [
    {'id': 'sola', 'nome': 'Persona sola, 28 anni, in affitto',
     'ipotesi': 'Reddito imponibile 24.000 euro. Vive in 52 metri quadrati, non è proprietaria. Non ha figli.',
     'voci': [{'v': 'Addizionale comunale IRPEF', 'euro': addiz(24000), 'nota': '0,8% di 24.000 (sopra la soglia di 23.000, si paga su tutto il reddito)'},
              {'v': 'IMU', 'euro': 0, 'nota': 'non possiede case'},
              {'v': 'TARI', 'euro': 113, 'nota': 'esempio del Comune: persona sola con meno di 30 anni, 52 metri quadrati, 2026'}]},
    {'id': 'famiglia', 'nome': 'Famiglia di tre persone, casa di proprietà',
     'ipotesi': 'Due adulti e un figlio. Redditi imponibili 38.000 e 22.000 euro. Casa in cui vivono: 106 metri quadrati, unica casa di proprietà.',
     'voci': [{'v': 'Addizionale comunale IRPEF', 'euro': addiz(38000) + addiz(22000), 'nota': '0,8% di 38.000; il secondo reddito (22.000) è sotto la soglia di 23.000 e non paga'},
              {'v': 'IMU', 'euro': 0, 'nota': 'abitazione principale, esente (non di lusso)'},
              {'v': 'TARI', 'euro': 293, 'nota': 'esempio del Comune: tre persone, 106 metri quadrati, 2026'}]},
    {'id': 'seconda', 'nome': 'La stessa famiglia, con una seconda casa',
     'ipotesi': 'Appartamento con rendita catastale di 1.000 euro (ipotesi nostra, categoria A, non di lusso). Imposta calcolata come la legge prevede: rendita x 1,05 x 160 x aliquota.',
     'voci': [{'v': 'IMU sulla seconda casa a disposizione', 'euro': ES_IMU[0]['imu'], 'nota': '1,14% su una base di 168.000 euro'},
              {'v': 'oppure, se la affitta a canone libero', 'euro': ES_IMU[1]['imu'], 'nota': '1,04%'},
              {'v': 'oppure, se la affitta a canone concordato', 'euro': ES_IMU[2]['imu'], 'nota': '0,73%, con sconto di legge del 25%'}]},
]
for p in PROFILI:
    if p['id'] != 'seconda':
        p['totale'] = sum(v['euro'] for v in p['voci'])
ctrl(abs(base_imu - 168000) < 1e-6, 'esempio IMU: base imponibile 1.000 x 1,05 x 160 = 168.000 euro')
ctrl(PROFILI[0]['totale'] == 192 + 113 and PROFILI[1]['totale'] == 304 + 293, 'esempi: addizionale e TARI sommati correttamente')

# ------------------------------------------------------------------ riepilogo JSON
def serie_cols(key):
    return [round(float(r[key]), 2) for r in serie]


J = {'meta': {'anni': ANNI, 'data_build': pd.Timestamp.today().strftime('%Y-%m-%d')}}
J['milano'] = {
    'anni': ANNI,
    'abitanti': [r['abitanti_1_gennaio'] for r in serie],
    'foi': [r['foi_2025_100'] for r in serie],
    'tributi': [{'id': k, 'nome': n, 'nom_euro': [r[k + '_euro'] for r in serie]} for k, n in TR],
    'recupero_evasione': {'totale': [r['recupero_evasione_euro'] for r in serie], 'casa': [r['recupero_evasione_casa_euro'] for r in serie],
                          'rifiuti': [r['recupero_evasione_rifiuti_euro'] for r in serie], 'altri': [r['recupero_evasione_altri_euro'] for r in serie]},
    'entrate_correnti': [r['entrate_correnti_euro'] for r in serie],
    'tributi_titolo1': [r['tributi_titolo1_euro'] for r in serie],
    'quota_su_entrate_correnti': [r['quota_quattro_su_entrate_correnti'] for r in serie],
    'quota_su_tributi': [r['quota_quattro_su_tributi'] for r in serie],
}
J['cassa_milano'] = [{**r} for r in mil_cassa]
J['confronto_cassa'] = conf
J['aliquote_imu_2026'] = [
    {'voce': 'Abitazione principale di lusso (categorie A/1, A/8, A/9), con detrazione di 200 euro', 'aliquota': 0.68},
    {'voce': 'Abitazione principale non di lusso', 'aliquota': None, 'nota': 'esente'},
    {'voce': 'Altri fabbricati: seconde case, case a disposizione, uffici e negozi non nelle categorie sotto', 'aliquota': 1.14},
    {'voce': 'Casa affittata a canone libero', 'aliquota': 1.04},
    {'voce': 'Casa affittata a canone concordato (l\'inquilino ci abita)', 'aliquota': 0.73, 'nota': 'poi ridotta del 25% per legge'},
    {'voce': 'Negozi e botteghe (C/1), laboratori (C/3) usati per l\'attività o affittati con contratto registrato', 'aliquota': 0.95},
    {'voce': 'Fabbricati del gruppo D (capannoni, uffici grandi, alberghi...)', 'aliquota': 1.14},
    {'voce': 'Aree edificabili', 'aliquota': 1.14},
    {'voce': 'Terreni agricoli', 'aliquota': 1.06},
    {'voce': 'Fabbricati rurali strumentali', 'aliquota': 0.1},
]
J['soggiorno_2026'] = [
    {'cat': 'Hotel 5 stelle', 'gen_mar': 10.0, 'da_apr': 12.0}, {'cat': 'Hotel 4 stelle', 'gen_mar': 10.0, 'da_apr': 10.0},
    {'cat': 'Hotel 3 stelle', 'gen_mar': 7.4, 'da_apr': 7.0}, {'cat': 'Hotel 2 stelle', 'gen_mar': 5.0, 'da_apr': 4.0},
    {'cat': 'Hotel 1 stella', 'gen_mar': 4.0, 'da_apr': 3.0},
    {'cat': 'Case vacanza, affitti brevi, B&B', 'gen_mar': 9.5, 'da_apr': 9.5}, {'cat': 'Case per ferie', 'gen_mar': 7.0, 'da_apr': 7.0},
    {'cat': 'Ostelli e campeggi', 'gen_mar': 3.0, 'da_apr': 3.0}]
J['esempi'] = {'profili': PROFILI, 'imu_seconda_casa': ES_IMU, 'rendita_ipotesi': RENDITA, 'base_imponibile': base_imu,
               'addizionale_aliquota': ALIQ_ADD, 'addizionale_soglia': SOGLIA_ADD}
J['irpef'] = {'citta_2024': irp, 'serie_milano': irpef_mil, 'classi_2024': classi}
J['riscossione'] = {
    'ministero_2016_2018': cfr_min.to_dict(orient='records'),
    'milano_tributi_2016_2018': mil_trib_min,
    'rendiconti': {str(a): d for a, d in RENDICONTI.items()},
    'evasione': {str(a): d for a, d in EVASIONE.items()},
    'anzianita': {str(a): d for a, d in ANZ.items()},
    'residui_serie': res_serie,
    'indicatore_riscossione_totale_ministero': q20[q20.indicatore.str.startswith('Indicatore concernente')][['citta', 'anno', 'valore_perc']].to_dict(orient='records'),
}
J['fonti_data'] = {'scarico_ministero': '2026-11-03', 'scarico_siope': '2026-11-03', 'mef': '2026-11-01',
                   'comune_pareri': '2026-11-03'}

# alcuni numeri riassuntivi usati nel testo
S = {}
a25 = serie[-1]
S['anno'] = 2025
S['quattro_2025'] = a25['quattro_tributi_euro']
S['per_abitante_2025'] = round(a25['quattro_tributi_euro'] / a25['abitanti_1_gennaio'], 0)
S['quota_entrate_correnti_2025'] = a25['quota_quattro_su_entrate_correnti']
S['residui_2018'] = res_serie[2]['residui_fine']
S['residui_2025'] = res_serie[-1]['residui_fine']
S['titolo1_2025'] = RENDICONTI[2025]['titolo1'][0]
S['incassato_competenza_2025_perc'] = round(100 * RENDICONTI[2025]['titolo1_incassi_competenza'] / RENDICONTI[2025]['titolo1'][0], 1)
S['evasione_riscossa_perc_2025'] = round(100 * EVASIONE[2025]['totale'][1] / EVASIONE[2025]['totale'][0], 1)
S['evasione_riscossa_perc_2024'] = round(100 * EVASIONE[2024]['totale'][1] / EVASIONE[2024]['totale'][0], 1)
S['irpef_per_contribuente_milano'] = irp[0]['irpef_per_contribuente']
J['sintesi'] = S

# ordine in cui Milano si colloca nel confronto del Ministero
ordine = {}
for a in (2016, 2017, 2018):
    pass
mm_ = cfr_min.groupby('citta').apply(lambda g: pd.Series({
    'riscosso_competenza_perc': 100 * g.riscosso_competenza.sum() / g.accertato.sum(),
    'residui_fine_su_accertato_perc': 100 * (g.residui_fine / g.accertato).mean(),
    'residui_fine_per_abitante_2018': float(g[g.anno == 2018].residui_fine.iloc[0] / g[g.anno == 2018].abitanti_rendiconto.iloc[0]),
    'fcde_perc_2018': float(g[g.anno == 2018].fcde_perc.iloc[0]) if g[g.anno == 2018].fcde_perc.notna().all() else None}), include_groups=False)
J['riscossione']['sintesi_citta_2016_2018'] = mm_.round(1).reset_index().to_dict(orient='records')
mm_.round(2).reset_index().to_csv(os.path.join(OUT, 'citta_riscossione_sintesi.csv'), sep=';', index=False)

with open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8') as f:
    json.dump(J, f, ensure_ascii=False, indent=1, default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else (float(o) if hasattr(o, 'item') else str(o)))

# ------------------------------------------------------------------ controlli sui file in docs/tasse
docs_dir = os.path.join(ROOT, 'docs', 'tasse')
bad = []
for dp, dn_, fns in os.walk(docs_dir):
    for fn in fns:
        p = os.path.join(dp, fn)
        if os.path.getsize(p) > 3_000_000 or fn.endswith(('.pdf', '.html')) and 'data' in dp:
            bad.append(p)
ctrl(not bad, 'nessun file grezzo o pesante in docs/tasse (niente PDF, niente pagine scaricate, nessun file sopra 3 MB)')
ctrl(not any(re.search(r'siope_entrate|ministero_interno|\.part$', fn) for dp, dn_, fns in os.walk(docs_dir) for fn in fns),
     'nessun file di dati scaricati copiato in docs/tasse')

with open(os.path.join(BASE, 'out', 'controlli.txt'), 'w', encoding='utf-8') as f:
    f.write('Controlli automatici di build.py\n\n' + '\n'.join(CTRL) + f'\n\nErrori: {FAIL[0]}\n')
print('\n'.join(CTRL))
print('ERRORI', FAIL[0])
sys.exit(1 if FAIL[0] else 0)
