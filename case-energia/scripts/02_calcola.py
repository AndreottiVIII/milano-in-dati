"""Calcola i dati aggregati della pagina "Quanto consumano le case" (niente record singoli, niente indirizzi).
Uso: python -I -X utf8 02_calcola.py <cartella progetto milano-in-dati>
Legge:
  - CENED vecchio (dati.lombardia.it rsg3-xhvk, 2009-2016, solo Milano): _esplorazione/aree/energia/lombardia_rsg3-xhvk/milano.csv
  - CENED+2 (bbky-sde5, 2016-2026, solo Milano): case-energia/raw/cened2_milano.csv   (da 01_scarica_cened2.py)
  - sezioni di censimento 2011 -> quartieri (NIL): censimenti/pulito/raccordo_sezioni_2011.csv
  - confini dei quartieri: docs/ospedali/data/nil_quartieri.geojson
  - colonnine e teleriscaldamento del Comune: _esplorazione/aree/energia/ds540*, ds1575*, ds1536*, ds1535*
Scrive in docs/case-energia/data/."""
import sys, os, json, csv
import numpy as np, pandas as pd
R = sys.argv[1]
OUT = os.path.join(R, 'docs', 'case-energia', 'data'); os.makedirs(OUT, exist_ok=True)
E = os.path.join(R, '_esplorazione', 'aree', 'energia')
CL = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
BANDE = ['prima del 1930', '1930-1945', '1946-1960', '1961-1976', '1977-1992', '1993-2006', 'dopo il 2006']
def r1(x): return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 1)
def vir(x): return '' if x is None else str(x).replace('.', ',')

def banda(s):
    if pd.isna(s): return np.nan
    s = s.strip().lower()
    m = {b: i for i, b in enumerate(BANDE)}
    if s in m: return m[s]
    try: y = int(s)
    except ValueError: return np.nan
    return 0 if y < 1930 else 1 if y <= 1945 else 2 if y <= 1960 else 3 if y <= 1976 else 4 if y <= 1992 else 5 if y <= 2006 else 6

def classe_unica(c):  # A+ e A1..A4 diventano A
    return 'A' if str(c).startswith('A') else c

# ---------------- CENED vecchio ----------------
o = pd.read_csv(os.path.join(E, 'lombardia_rsg3-xhvk', 'milano.csv'), dtype=str)
o['cl'] = o.classe_energetica.map(classe_unica)
o['b'] = o.anno_costruzione.map(banda)
o['co2'] = pd.to_numeric(o.emissioni_di_co2, errors='coerce')
o.loc[(o.co2 <= 0) | (o.co2 > 1000), 'co2'] = np.nan
o['y'] = 2000 + pd.to_numeric(o.data_chiusura_pratica.str[-2:], errors='coerce')
o['fg'] = o.cl.isin(['F', 'G'])
ab_o = o[o.destinazione_di_uso == 'E.1(1)']
N_O = len(o)

# ---------------- CENED+2 ----------------
n = pd.read_csv(os.path.join(R, 'case-energia', 'raw', 'cened2_milano.csv'), dtype=str)
N_N_TUTTI = len(n)
n = n[n.residenziale == 'True'].copy()
n['cl'] = n.classe_energetica.map(classe_unica)
n['b'] = n.anno_costruzione.map(banda)
n['co2'] = pd.to_numeric(n.emissioni_co2, errors='coerce')
n.loc[(n.co2 <= 0) | (n.co2 > 1000), 'co2'] = np.nan
n['y'] = pd.to_numeric(n.data_ins.str[-4:], errors='coerce')
n['fg'] = n.cl.isin(['F', 'G'])
n['abb'] = n.cl.isin(['A', 'B'])
N_N = len(n)

# ---------------- classi: tutto il vecchio CENED ----------------
classi = {'n': N_O, 'cont': [int((o.cl == c).sum()) for c in CL], 'cont_abitazioni': [int((ab_o.cl == c).sum()) for c in CL],
          'n_abitazioni': len(ab_o), 'fg': int(o.fg.sum()), 'quota_fg': r1(100 * o.fg.mean()), 'quota_g': r1(100 * (o.cl == 'G').mean()),
          'quota_a': r1(100 * (o.cl == 'A').mean()), 'quota_fg_nuovo': r1(100 * n.fg.mean()),
          'cont_nuovo': [int((n.cl == c).sum()) for c in CL]}

# ---------------- epoca ----------------
epo = {'bande': BANDE, 'vecchio': {'n': [], 'cont': [], 'co2_mediana': []}, 'nuovo': {'n': [], 'cont': [], 'co2_mediana': []}}
for i in range(7):
    s = ab_o[ab_o.b == i]
    epo['vecchio']['n'].append(len(s)); epo['vecchio']['cont'].append([int((s.cl == c).sum()) for c in CL])
    epo['vecchio']['co2_mediana'].append(r1(s.co2.median()))
    t = n[n.b == i]
    epo['nuovo']['n'].append(len(t)); epo['nuovo']['cont'].append([int((t.cl == c).sum()) for c in CL])
    epo['nuovo']['co2_mediana'].append(r1(t.co2.median()))
epo['vecchio']['senza_epoca'] = int(ab_o.b.isna().sum())
with open(os.path.join(OUT, 'classi_per_epoca.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['periodo_certificati', 'epoca_costruzione', 'certificati'] + CL + ['kg_co2_m2_anno_mediana'])
    for k, nm in (('vecchio', '2009-2016'), ('nuovo', '2016-2026')):
        for i in range(7):
            w.writerow([nm, BANDE[i], epo[k]['n'][i]] + epo[k]['cont'][i] + [vir(epo[k]['co2_mediana'][i])])

# ---------------- anni ----------------
anni = {'vecchio': [], 'nuovo': []}
for y in range(2010, 2016):
    s = o[o.y == y]
    anni['vecchio'].append({'a': y, 'n': len(s), 'fg': r1(100 * s.fg.mean()), 'ab': r1(100 * s.cl.isin(['A', 'B']).mean())})
for y in range(2017, 2026):
    s = n[n.y == y]; v = s[s.b <= 3]
    anni['nuovo'].append({'a': y, 'n': len(s), 'fg': r1(100 * s.fg.mean()), 'ab': r1(100 * s.abb.mean()),
                          'fg_vecchie': r1(100 * v.fg.mean()), 'n_vecchie': len(v),
                          'nuove_costr': r1(100 * (s.nuova_costruzione == 'True').mean())})
with open(os.path.join(OUT, 'classi_per_anno.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['periodo_certificati', 'anno', 'certificati', 'quota_F_o_G_pct', 'quota_A_o_B_pct', 'quota_F_o_G_case_fino_al_1976_pct'])
    for r in anni['vecchio']: w.writerow(['2009-2016', r['a'], r['n'], vir(r['fg']), vir(r['ab']), ''])
    for r in anni['nuovo']: w.writerow(['2016-2026', r['a'], r['n'], vir(r['fg']), vir(r['ab']), vir(r['fg_vecchie'])])

# ---------------- perché si fa un certificato (per i limiti) ----------------
mot = {}
for k, c in (('compravendita', 'passaggio_proprieta'), ('affitto', 'locazione'), ('nuova_costruzione', 'nuova_costruzione'),
             ('ristrutturazione', 'ristrutturazione_importante'), ('riqualificazione', 'riqualificazione_energetica')):
    s = n[n[c] == 'True']
    mot[k] = {'n': len(s), 'quota': r1(100 * len(s) / N_N), 'fg': r1(100 * s.fg.mean()), 'ab': r1(100 * s.abb.mean())}
mot_o = o.motivazione_ace.value_counts()
mot['vecchio'] = {'compravendita': int(mot_o.get('Trasferimento a titolo oneroso', 0)), 'affitto': int(mot_o.get('Contratto di locazione', 0)),
                  'volontario': int(mot_o.get('Ace volontario', 0)), 'nuova_costruzione': int(mot_o.get('Nuova costruzione', 0)), 'n': N_O}

# ---------------- riscaldamento ----------------
imp_nome = {'Generatore a combustione': 'Caldaia a gas o gasolio', 'Pompa di calore': 'Pompa di calore', 'Teleriscaldamento': 'Teleriscaldamento'}
n['imp'] = n.ci_tipo_impianto_1.map(imp_nome).fillna('Altro o non indicato')
ris = []
for k in ['Caldaia a gas o gasolio', 'Pompa di calore', 'Teleriscaldamento', 'Altro o non indicato']:
    s = n[n.imp == k]
    ris.append({'tipo': k, 'n': len(s), 'quota': r1(100 * len(s) / N_N), 'fg': r1(100 * s.fg.mean()), 'co2': r1(s.co2.median()),
                'eta_pre1977': r1(100 * (s.b <= 3).mean())})
vet = n.ci_vettore_energetico_1.fillna('non indicato').replace({'Gasolio e olio combustibile': 'Gasolio', 'Olio combustibile': 'Gasolio', 'Energia elettrica': 'Elettricità'})
vet = vet.where(vet.isin(['Gas naturale', 'Elettricità', 'Teleriscaldamento', 'Gasolio']), 'Altro o non indicato')
comb = [{'tipo': k, 'n': int((vet == k).sum()), 'quota': r1(100 * (vet == k).mean())} for k in ['Gas naturale', 'Elettricità', 'Teleriscaldamento', 'Gasolio', 'Altro o non indicato']]
gen = o.tipologia_generatore.fillna('')
comb_o = o.tipologia_combustibile.fillna('')
o['pdc'] = gen.str.contains('Pompa di calore'); o['tele'] = gen.str.contains('Teleriscaldamento'); o['gasolio'] = comb_o.str.contains('Gasolio|Olio combustibile')
n['pdc'] = n.imp == 'Pompa di calore'; n['tele'] = n.imp == 'Teleriscaldamento'; n['gasolio'] = vet == 'Gasolio'
serie = {k: {'vecchio': [], 'nuovo': []} for k in ('pdc', 'tele', 'gasolio')}
for k in serie:
    for y in range(2010, 2016): serie[k]['vecchio'].append({'a': y, 'v': r1(100 * o[o.y == y][k].mean())})
    for y in range(2017, 2026): serie[k]['nuovo'].append({'a': y, 'v': r1(100 * n[n.y == y][k].mean())})
risc = {'impianti': ris, 'combustibili': comb, 'serie': serie, 'vecchio_solo_gas': r1(100 * (comb_o == 'Gas naturale').mean()),
        'vecchio_gasolio': r1(100 * o.gasolio.mean()), 'pdc_2017': r1(100 * n[n.y == 2017].pdc.mean()), 'pdc_2025': r1(100 * n[n.y == 2025].pdc.mean())}
with open(os.path.join(OUT, 'riscaldamento.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['impianto_principale', 'certificati_2016_2026', 'quota_pct', 'quota_F_o_G_pct', 'kg_co2_m2_anno_mediana'])
    for r in ris: w.writerow([r['tipo'], r['n'], vir(r['quota']), vir(r['fg']), vir(r['co2'])])
with open(os.path.join(OUT, 'riscaldamento_per_anno.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['periodo_certificati', 'anno', 'pompa_di_calore_pct', 'teleriscaldamento_pct', 'gasolio_pct'])
    for k, nm in (('vecchio', '2009-2016'), ('nuovo', '2016-2026')):
        for j in range(len(serie['pdc'][k])):
            w.writerow([nm, serie['pdc'][k][j]['a']] + [vir(serie[x][k][j]['v']) for x in ('pdc', 'tele', 'gasolio')])

# ---------------- quartieri ----------------
rac = pd.read_csv(os.path.join(R, 'censimenti', 'pulito', 'raccordo_sezioni_2011.csv'))
n['sez'] = pd.to_numeric(n.sez_censimento.str[-7:], errors='coerce')
n = n.merge(rac[['sezione', 'nil']], left_on='sez', right_on='sezione', how='left')
n.loc[~n.sez_censimento.fillna('').str.startswith('15146'), 'nil'] = np.nan
con_nil = int(n.nil.notna().sum())
gj = json.load(open(os.path.join(R, 'docs', 'ospedali', 'data', 'nil_quartieri.geojson'), encoding='utf-8'))
nomi = {f['properties']['i']: f['properties']['n'] for f in gj['features']}
qs = {}; rows = []
for i, nm in sorted(nomi.items(), key=lambda t: t[1]):
    s = n[n.nil == i]
    if len(s) == 0: continue
    cnt = [int((s.cl == c).sum()) for c in CL]
    d = {'i': int(i), 'n': nm, 'cert': len(s), 'fg': r1(100 * s.fg.mean()), 'ab': r1(100 * s.abb.mean()), 'co2': r1(s.co2.median()),
         'cont': cnt, 'pre1946': r1(100 * (s.b <= 1).mean())}
    qs[int(i)] = d
    rows.append([i, nm, len(s)] + cnt + [vir(d['fg']), vir(d['co2'])])
with open(os.path.join(OUT, 'quartieri.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['id_quartiere', 'quartiere', 'certificati'] + CL + ['quota_F_o_G_pct', 'kg_co2_m2_anno_mediana'])
    w.writerows(rows)
tc = {}
for i in qs:
    s = n[n.nil == i]; riga = []
    for b in range(7):
        t = s[s.b == b]
        riga.append([len(t)] + [int((t.cl == c).sum()) for c in CL] + [r1(t.co2.median()) if len(t) else None])
    tc[str(i)] = riga
citta_epoca = []
for b in range(7):
    t = n[n.b == b]
    citta_epoca.append([len(t)] + [int((t.cl == c).sum()) for c in CL] + [r1(t.co2.median())])
def arrotonda(c):
    return [arrotonda(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]
feats = [{'type': 'Feature', 'properties': {'i': f['properties']['i'], 'n': f['properties']['n']},
          'geometry': {'type': f['geometry']['type'], 'coordinates': arrotonda(f['geometry']['coordinates'])}} for f in gj['features']]
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'nil.geojson'), 'w', encoding='utf-8'), separators=(',', ':'))
json.dump({'nil': tc, 'citta': citta_epoca, 'cl': CL, 'bande': BANDE}, open(os.path.join(OUT, 'tuacasa.json'), 'w', encoding='utf-8'), separators=(',', ':'))

# ---------------- fuori casa ----------------
c = pd.read_csv(os.path.join(E, 'ds540_colonnine-di-ricarica', 'ricarica_colonnine.csv'), sep=';')
c['veloce'] = c.infra.str.contains('Fast', na=False)
pa = []; cum = 0
for a in range(2016, 2025):
    s = c[c.anno == a]; cum += len(s)
    pa.append({'a': a, 'nuove': len(s), 'veloci': int(s.veloce.sum()), 'tot': cum})
oper = c.titolare.str.strip().str.upper().replace({'ENEL X WAY ITALIA': 'ENEL X', 'ENEL X MOBILITY': 'ENEL X'}).value_counts()
col = {'postazioni': len(c), 'colonnine': int(c.numero_col.sum()), 'punti': int(c.numero_pdr.sum()), 'quartieri': int(c.id_nil.nunique()),
       'per_anno': pa, 'dal_2022': int((c.anno >= 2022).sum()), 'veloci': int(c.veloce.sum()),
       'operatori': [[{'A2A ENERGY SOLUTIONS': 'A2A', 'ENEL X': 'Enel X', 'BECHARGE': 'BeCharge', 'POWERPOINT CITY CAR': 'PowerPoint City Car', 'NHP': 'NHP'}.get(k, k.title()), int(v)] for k, v in oper.head(5).items()],
       'altri_operatori': int(oper.iloc[5:].sum())}
cn = c.groupby('id_nil').size().sort_values(ascending=False)
col['per_quartiere'] = [{'i': int(i), 'n': nomi.get(int(i), str(i)), 'v': int(v)} for i, v in cn.head(8).items()]
with open(os.path.join(OUT, 'colonnine_per_anno.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['anno_ordinanza', 'postazioni_nuove', 'di_cui_veloci', 'postazioni_totale'])
    for r in pa: w.writerow([r['a'], r['nuove'], r['veloci'], r['tot']])
t = pd.read_csv(os.path.join(E, 'ds1536-teleriscaldamento-serie-storica-abitanti-serviti', 'ds1536_abitanti_serviti_teleriscaldamento.csv'), sep=';')
t.columns = ['anno', 'abitanti', 'pct']
v = pd.read_csv(os.path.join(E, 'ds1535-teleriscaldamento-serie-storica-volumetria-servita', 'ds1535_volumetria_servita_da_teleriscaldamento.csv'), sep=';')
v.columns = ['anno', 'm3']
pod = pd.read_csv(os.path.join(E, 'ds1575-punti-di-fornitura-teleriscaldamento-pod', 'ds1575_teleriscaldamento_punti_di_prelievo_pod_final.csv'), sep=';')
tele = {'serie': [{'a': int(r.anno), 'ab': int(r.abitanti), 'pct': float(r.pct), 'm3': int(v[v.anno == r.anno].m3.iloc[0])} for r in t.itertuples()],
        'pod': len(pod), 'pod_municipio4': int((pod.MUNICIPIO == 4).sum())}
with open(os.path.join(OUT, 'teleriscaldamento_abitanti.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['anno', 'abitanti_serviti', 'quota_residenti_pct', 'volumetria_servita_m3'])
    for r in tele['serie']: w.writerow([r['a'], r['ab'], vir(r['pct']), r['m3']])

riep = {'meta': {'cened_vecchio': N_O, 'cened_nuovo_tutti': N_N_TUTTI, 'cened_nuovo_residenziali': N_N, 'con_quartiere': con_nil, 'soglia_mappa': 150},
        'classi': classi, 'epoca': epo, 'anni': anni, 'motivi': mot, 'riscaldamento': risc, 'quartieri': list(qs.values()),
        'citta_epoca': citta_epoca, 'colonnine': col, 'tele': tele}
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
print('quartiere assegnato a', con_nil, 'su', N_N)
