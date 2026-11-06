"""Elabora i dati scaricati e scrive i file della pagina "Dove va l'acqua che scarichi".
Uso: python -I -X utf8 03_elabora.py <cartella_filone> <cartella_docs_pagina> <file_FOI>
  <cartella_filone>  = ...\\milano-in-dati\\fogne-depurazione
  <cartella_docs_pagina> = ...\\milano-in-dati\\docs\\fogne
  <file_FOI> = ...\\bilancio-comune\\pulito\\indice_prezzi_annuo_FOI_da_strand12.csv
Legge solo raw/ (e i numeri citati da PDF, scritti qui sotto con la fonte).
Scrive pulito/*.csv e <docs>/data/*.
"""
import json, sys, pathlib, csv, statistics
import pandas as pd
import openpyxl

F = pathlib.Path(sys.argv[1]); RAW = F / 'raw'; PUL = F / 'pulito'
OUT = pathlib.Path(sys.argv[2]) / 'data'; FOI = pathlib.Path(sys.argv[3])
PUL.mkdir(exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
log = []
def L(*a):
    s = ' '.join(str(x) for x in a); print(s); log.append(s)

R = {'meta': {'scaricato': '2026-11-06', 'generato_da': 'scripts/03_elabora.py'}}

# ---------------------------------------------------------------- 1. EEA depuratori
def num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).replace(',', '.'))
    except ValueError: return None

PLANTS = {'IT03160128000456': 'Nosedo', 'IT03160128000457': 'San Rocco', 'IT03160128000464': 'Peschiera Borromeo'}
RECV = {'IT03N008044003071LO': 'Vettabbia', 'IT03N0080440021LO': 'Lambro Meridionale', 'IT03N0080445LO': 'Lambro'}
dep_rows = []; R['depuratori'] = {}
for anno, lay in [(2020, '2020'), (2022, '2022')]:
    tp = json.loads((RAW / 'eea' / f'TreatmentPlants_{lay}_IT.json').read_text(encoding='utf-8'))
    dp = json.loads((RAW / 'eea' / f'DischargePoints_{lay}_IT.json').read_text(encoding='utf-8'))
    ag = json.loads((RAW / 'eea' / f'Agglomerations_{lay}_IT.json').read_text(encoding='utf-8'))
    for t in tp:
        if t['uwwCode'] not in PLANTS: continue
        nome = PLANTS[t['uwwCode']]
        wb = [d['dcpWaterbodyID'] for d in dp if d['uwwCode'] == t['uwwCode']]
        r = {'anno': anno, 'depuratore': nome, 'codice_eea': t['uwwCode'],
             'acqua_trattata_m3': num(t['uwwWasteWaterTreated']),
             'riuso_pct_dichiarato': num(t['uwwWasteWaterReuse']),
             'carico_entrante_ae': num(t['uwwLoadEnteringUWWTP']), 'capacita_ae': num(t['uwwCapacity'])}
        for s, k in [('BOD', 'BOD'), ('COD', 'COD'), ('N', 'N'), ('P', 'P')]:
            r[f'{s}_entrata_t'] = num(t[f'uww{k}IncomingMeasured'])
            r[f'{s}_uscita_t'] = num(t[f'uww{k}DischargeMeasured'])
        r['corpo_idrico_scarico'] = ';'.join(x or '' for x in wb)
        r['scarica_in'] = ';'.join(RECV.get(x, x or '') for x in wb)
        dep_rows.append(r)
    mi = [a for a in ag if a['aggCode'] == 'IT03160121000230'][0]
    R['depuratori'][str(anno)] = {'agglomerato_ae': mi['aggGenerated'], 'raccolto_in_fogna_pct': mi['aggC1'],
                                  'senza_trattamento_pct': mi['aggPercWithoutTreatment']}
dep = pd.DataFrame(dep_rows)
dep.to_csv(PUL / 'depuratori_eea.csv', sep=';', index=False)
dep.to_csv(OUT / 'depuratori.csv', sep=';', index=False)
L('depuratori', len(dep))
R['depuratori']['righe'] = dep_rows

def tot(anno, col, nomi=('Nosedo', 'San Rocco')):
    x = dep[(dep.anno == anno) & dep.depuratore.isin(nomi)]
    return float(x[col].sum())

# Sostanze: Nosedo + San Rocco (i due impianti di MM), 2022
sost = []
for s, nome in [('BOD', 'Sporco organico'), ('N', 'Azoto'), ('P', 'Fosforo'), ('COD', 'Sostanze ossidabili (COD)')]:
    for anno in (2020, 2022):
        e, u = tot(anno, f'{s}_entrata_t'), tot(anno, f'{s}_uscita_t')
        sost.append({'sostanza': s, 'nome': nome, 'anno': anno, 'entrata_t': round(e, 1), 'uscita_t': round(u, 1),
                     'tolto_pct': round((1 - u / e) * 100, 2)})
    for anno in (2022,):
        x = dep[(dep.anno == anno) & (dep.depuratore == 'Peschiera Borromeo')].iloc[0]
        sost.append({'sostanza': s, 'nome': nome, 'anno': anno, 'impianto': 'Peschiera Borromeo',
                     'entrata_t': x[f'{s}_entrata_t'], 'uscita_t': x[f'{s}_uscita_t'],
                     'tolto_pct': round((1 - x[f'{s}_uscita_t'] / x[f'{s}_entrata_t']) * 100, 2)})
R['sostanze'] = sost
for s in sost: L('sostanza', s)

# ---------------------------------------------------------------- 2. ISTAT 2020 (acqua del rubinetto)
wb = openpyxl.load_workbook(RAW / 'istat' / 'Istat_Tavole_Censimento_acque_2020-21122022.xlsx', read_only=True)
def riga(tav, comune):
    for r in wb[tav].iter_rows(values_only=True):
        if r and isinstance(r[0], str) and r[0].strip() == comune: return [c for c in r if c is not None]
t15 = riga('Tav 15', 'Milano'); t16 = riga('Tav 16', 'Milano'); t36 = riga('Tav 36', 'Milano')
R['istat2020'] = {'immessa_mila_m3': t15[1], 'immessa_l_ab_g': t15[2], 'erogata_mila_m3': t15[3], 'erogata_l_ab_g': t15[4],
                  'perdite_pct': t15[5], 'fatturata_mila_m3': t16[1], 'fatturata_domestica_mila_m3': t16[3],
                  'fatturata_domestica_l_ab_g': t16[4], 'servita_fognatura_pct': t36[1], 'servita_depurazione_pct': t36[2],
                  'fonte': 'ISTAT, Censimento delle acque per uso civile 2020, tavole 15, 16, 36'}
L('istat2020', R['istat2020'])

# Flusso 2020 (stesso anno per rubinetti e depuratori)
imm = t15[1] / 1000; ero = t15[3] / 1000
nos = tot(2020, 'acqua_trattata_m3', ('Nosedo',)) / 1e6; sro = tot(2020, 'acqua_trattata_m3', ('San Rocco',)) / 1e6
rn = dep[(dep.anno == 2020) & (dep.depuratore == 'Nosedo')].riuso_pct_dichiarato.iloc[0]
rs = dep[(dep.anno == 2020) & (dep.depuratore == 'San Rocco')].riuso_pct_dichiarato.iloc[0]
R['flusso2020'] = {'immessa': round(imm, 1), 'perdite': round(imm - ero, 1), 'erogata': round(ero, 1),
                   'nosedo': round(nos, 1), 'san_rocco': round(sro, 1), 'depuratori': round(nos + sro, 1),
                   'in_piu': round(nos + sro - ero, 1), 'litri_ogni_100': round((nos + sro) / ero * 100),
                   'riuso_nosedo': round(nos * rn / 100, 1), 'riuso_san_rocco': round(sro * rs / 100, 1),
                   'fiume_nosedo': round(nos * (1 - rn / 100), 1), 'fiume_san_rocco': round(sro * (1 - rs / 100), 1),
                   'riuso_pct_nosedo': rn, 'riuso_pct_san_rocco': rs,
                   'peschiera_trattata': round(tot(2020, 'acqua_trattata_m3', ('Peschiera Borromeo',)) / 1e6, 1)}
R['flusso2022'] = {'nosedo': round(tot(2022, 'acqua_trattata_m3', ('Nosedo',)) / 1e6, 1),
                   'san_rocco': round(tot(2022, 'acqua_trattata_m3', ('San Rocco',)) / 1e6, 1),
                   'peschiera_trattata': round(tot(2022, 'acqua_trattata_m3', ('Peschiera Borromeo',)) / 1e6, 1)}
L('flusso2020', R['flusso2020']); L('flusso2022', R['flusso2022'])

# Numeri citati da PDF (nessuna licenza aperta: solo il numero, con la fonte)
R['citati'] = {
  'rete_fognaria_km': {'v': 1630, 'testo': 'circa 1.630 km', 'fonte': 'MM Spa, presentazione "Riuso delle acque depurate", Brescia 16 giugno 2026, slide 2 (impiantitrattamentoacque.unibs.it)'},
  'fognatura_mista': {'v': True, 'fonte': 'come sopra: "Rete Fognatura mista"'},
  'collettati_mln_m3': {'v': 240, 'fonte': 'come sopra: "Volumi collettati ~240 mln mc/anno"'},
  'irriguo_nosedo_mln_m3': {'v': 60, 'ettari': 3000, 'stagione': 'aprile-settembre', 'fonte': 'come sopra, slide "Riuso irriguo Nosedo"'},
  'irriguo_sanrocco_mln_m3': {'v': 15, 'ettari': 7700, 'stagione': 'maggio-agosto', 'fonte': 'come sopra, slide "Riuso irriguo San Rocco"'},
  'peschiera_ae': {'v': 250000, 'fonte': 'come sopra: bacino orientale, Peschiera Borromeo, 250.000 AE, in gestione ad altro operatore'},
  'seveso_record_arpa': {'fonte': 'ARPA Lombardia, comunicato sull\'evento del 22 settembre 2025 (ripreso da Legnanonews): colmo 4,92 m a Niguarda come l\'esondazione dell\'8 luglio 2014; massimo storico novembre 2014, 5,01 m'},
  'vasca_parco_nord': {'mc': 250000, 'da': '2023-11', 'fonte': 'Comune di Milano, citato da Il Fatto Quotidiano 31/10/2023; operativa da novembre 2023 secondo la stampa'},
}

# ---------------------------------------------------------------- 3. Fiumi (ARPA, CC0)
def fnum(s):
    try: return float(str(s).replace(',', '.'))
    except ValueError: return None
lim = pd.read_csv(RAW / 'lombardia' / 'dati' / 'mnqh-idjz.csv', dtype=str)
lim['v'] = lim.VALORE.map(fnum); lim['COMUNE'] = lim.COMUNE.str.strip()
lim13 = pd.read_csv(RAW / 'lombardia' / 'dati' / '7ayk-kdfa.csv', dtype=str)
lim13['v'] = lim13.LIMeco_VALORE.map(fnum)
an = pd.read_csv(RAW / 'lombardia' / 'dati' / 'kr6i-f553_MI_MB_LO.csv', dtype=str)
an['v'] = pd.to_numeric(an.valore_numerico, errors='coerce')
# stazioni: id interno, corso, comune nei tre file
ST = [  # id, nome breve, corso (file 2018-20), comune (2018-20), corso 2013, comune 2013, codice stazione analisi
 ('lesmo', 'Lambro a Lesmo', "Lambro (Fiume)", 'Lesmo', 'Lambro (Fiume)', 'Lesmo', 'N0080444lo1'),
 ('peschiera', 'Lambro a Peschiera Borromeo', "Lambro (Fiume)", 'Peschiera Borromeo', 'Lambro (Fiume)', 'Peschiera Borromeo', 'N0080445lo1'),
 ('santangelo', "Lambro a Sant'Angelo Lodigiano", "Lambro (Fiume)", "Sant'Angelo Lodigiano", 'Lambro (Fiume)', 'Sant.Angelo Lodigiano', 'N0080446lo1'),
 ('orio', 'Lambro a Orio Litta', "Lambro (Fiume)", 'Orio Litta', 'Lambro (Fiume)', 'Orio Litta', 'N0080447lo1'),
 ('vettabbia', 'Vettabbia a San Giuliano Milanese', 'Vettabbia (Cavo)', 'San Giuliano Milanese', 'Cavo Vettabbia', 'S. Giuliano Milanese', 'N008044003071lo1'),
 ('locate', 'Lambro Meridionale a Locate di Triulzi', 'Lambro Meridionale (Colatore)', 'Locate di Triulzi', 'Lambro Meridionale (Fiume)', 'Locate Triulzi', 'N0080440021lo1'),
 ('lmsantangelo', "Lambro Meridionale a Sant'Angelo", 'Lambro Meridionale (Fiume)', "Sant'Angelo Lodigiano", 'Lambro Meridionale (Fiume)', 'S. Angelo Lodigiano', 'N0080440022lo1'),
 ('po', 'Po a Somaglia', 'Po (Fiume)', 'Somaglia', None, None, 'N00814ir1'),
 ('martesana', 'Naviglio Martesana a Milano', 'Naviglio Martesana (Canale)', 'Milano', None, None, 'POLSSEMACA1lo1'),
 ('grande', 'Naviglio Grande a Milano', 'Naviglio Grande (Canale)', 'Milano', None, None, '001098160011ir1'),
 ('pavese', 'Naviglio Pavese a Casarile', 'Naviglio Pavese (Canale)', 'Casarile', 'Naviglio Pavese', 'Casarile', 'POTI3NPCA1lo1'),
 ('seveso', 'Seveso a Lentate', 'Seveso (Torrente)', 'Lentate sul Seveso', 'Seveso (Torrente)', 'Lentate sul Seveso', 'N008001091013lo1'),
 ('olonarho', 'Olona a Rho', 'Olona (Fiume)', 'Rho', None, None, 'N008044002013lo1'),
 ('olonaleg', 'Olona a Legnano', 'Olona (Fiume)', 'Legnano', 'Olona (Fiume)', 'Legnano', 'N008044002012lo1'),
]
fiumi = []
for sid, nome, c1, m1, c13, m13, cod in ST:
    x = lim[(lim["CORSO D'ACQUA"] == c1) & (lim.COMUNE.str.lower() == m1.lower())]
    o = {'id': sid, 'nome': nome, 'codice_stazione': cod}
    for a in ('2018', '2019', '2020'):
        y = x[x.ANNO == a]
        o['limeco_' + a] = float(y.v.iloc[0]) if len(y) and pd.notna(y.v.iloc[0]) else None
        o['classe_' + a] = (y.CLASSE.iloc[0] if len(y) else None)
        if o['classe_' + a] == '-': o['classe_' + a] = None
    if c13:
        y = lim13[(lim13.CORSO_D_ACQUA.str.strip() == c13) & (lim13.COMUNE.str.strip() == m13)]
        if len(y) > 1: L('ATTENZIONE 2013 piu righe', nome, y.v.tolist())
        o['limeco_2013'] = float(y.v.iloc[0]) if len(y) else None
        o['classe_2013'] = y.LIMeco_CLASSE.iloc[0] if len(y) else None
    z = an[an.codice_stazione == cod]
    for par, k in [('Azoto ammoniacale', 'ammonio_mg_l'), ('Fosforo Totale', 'fosforo_ug_l'),
                   ('Escherichia coli', 'ecoli_mpn_100ml'), ('Azoto nitrico', 'nitrati_n_mg_l')]:
        w = z[(z.parametro == par)]
        # valori "<" (sotto soglia) esclusi dalla mediana; contati
        o[k] = float(w[w.segno.isna()].v.median()) if len(w) else None
        o[k + '_n'] = int(len(w)); o[k + '_sotto_soglia'] = int((w.segno == '<').sum())
    o['anni_analisi'] = sorted(z.anno.dropna().unique().tolist())
    fiumi.append(o)
    L('fiume', o)
pd.DataFrame(fiumi).to_csv(PUL / 'fiumi_stazioni.csv', sep=';', index=False)
pd.DataFrame(fiumi).to_csv(OUT / 'fiumi_stazioni.csv', sep=';', index=False)
R['fiumi'] = fiumi

# ---------------------------------------------------------------- 4. Seveso a Niguarda (ARPA, CC0)
sv = pd.concat([pd.read_csv(RAW / 'lombardia' / 'dati' / f) for f in
                ['seveso_niguarda_3118_gsyu-uxt3.csv', 'seveso_niguarda_3118_3e8b-w7ay.csv']])
sv['data'] = pd.to_datetime(sv.data)
sv = sv.drop_duplicates(['data'])
buoni = sv[sv.stato.isin([1, 2])].copy()  # 1 = registrato buona qualita', 2 = elaborato buona qualita'
buoni['giorno'] = buoni.data.dt.date
g = buoni.groupby('giorno').agg(max_cm=('valore', 'max'), n=('valore', 'size')).reset_index()
g['anno'] = pd.to_datetime(g.giorno).dt.year
cop = g.groupby('anno').size()
tutti = sv.groupby(sv.data.dt.year).data.apply(lambda s: s.dt.date.nunique())
R['seveso'] = {'sensore': 3118, 'stazione': 'Milano Niguarda', 'primo': str(sv.data.min()), 'ultimo': str(sv.data.max()),
               'giorni_validi_per_anno': {int(k): int(v) for k, v in cop.items()},
               'righe_per_stato': {int(k): int(v) for k, v in sv.stato.value_counts().items()}}
alti = g[g.max_cm >= 100].copy()
alti['giorno'] = alti.giorno.astype(str)
alti[['giorno', 'anno', 'max_cm']].to_csv(OUT / 'seveso_giorni_sopra_1m.csv', sep=';', index=False)
g.to_csv(PUL / 'seveso_niguarda_massimo_giornaliero.csv', sep=';', index=False)
R['seveso']['giorni'] = [{'g': r.giorno, 'cm': int(r.max_cm)} for r in alti.itertuples()]
for t in (150, 200, 300):
    R['seveso'][f'giorni_sopra_{t}'] = {int(a): int(((g.anno == a) & (g.max_cm >= t)).sum()) for a in range(2014, 2025)}
L('seveso top', g.sort_values('max_cm', ascending=False).head(8).to_dict('records'))
L('seveso giorni validi', R['seveso']['giorni_validi_per_anno'])

# ---------------------------------------------------------------- 5. Tariffe
# Milano MM: dai PDF di latuaacqua.it (2020-2023 testo, 2024-2026 immagini lette a vista)
MM = {2020: (0.143866, 0.368991, 0.988327, 2.533051), 2021: (0.149832, 0.384291, 1.029309, 2.638086),
      2022: (0.162456, 0.416671, 1.116038, 2.860369), 2023: (0.173832, 0.445849, 1.194189, 3.060668),
      2024: (0.184262, 0.472600, 1.265840, 3.244308), 2025: (0.195387, 0.501134, 1.342268, 3.440191),
      2026: (0.195387, 0.501134, 1.342268, 3.440191)}
foi = {int(r['anno']): float(r['indice_raccordato_2025_100']) for r in csv.DictReader(open(FOI, encoding='utf-8'))}
serie = []
for a, (fo, de, qf, qd) in MM.items():
    serie.append({'anno': a, 'fognatura': fo, 'depurazione': de, 'totale_m3': round(fo + de, 6),
                  'quota_fissa_fognatura': qf, 'quota_fissa_depurazione': qd,
                  'totale_m3_euro2025': round((fo + de) * 100 / foi[a], 6) if a in foi else None,
                  'provvisoria': a == 2026})
R['tariffe_milano'] = serie
pd.DataFrame(serie).to_csv(OUT / 'tariffe_milano.csv', sep=';', index=False)
L('tariffe milano', serie)
tc = pd.read_csv(RAW / 'tariffe_citta' / 'tariffe_fogna_depurazione.csv', sep=';', dtype=str)
CITTA = []
def add(nome, fo, de, nota, fonte, extra=None):
    o = {'citta': nome, 'fognatura': fo, 'depurazione': de, 'totale_m3': round(fo + de, 6), 'nota': nota, 'fonte': fonte}
    if extra: o.update(extra)
    CITTA.append(o)
add('Milano', 0.195387, 0.501134, '', 'MM Spa, Tariffe 2025, latuaacqua.it')
for _, r in tc.iterrows():
    c, an_ = r.citta, r.anno
    fo, de = float(r.fognatura_eur_m3), float(r.depurazione_eur_m3)
    if c == 'Roma' and 'lug' in an_: add('Roma', fo, de, '', 'Acea Ato 2, tariffe dal 1/7/2025')
    elif c in ('Torino', 'Bologna', 'Firenze'): add(c, fo, de, '', r.gestore + ', tariffe 2025')
    elif c == 'Napoli': add('Napoli', fo, de, 'depurazione: tariffa regionale fissata nel 2015, indicata dal gestore', 'ABC Napoli, corrispettivi 2025; Regione Campania')
    elif c == 'Hinterland milanese' and an_ == '2025': add('Comuni intorno', fo, de, 'CAP Holding, comuni della città metropolitana', 'CAP Holding, tariffe 2025 (pagina web)')
gen = tc[tc.citta == 'Genova']
gv = [(float(a) + float(b)) for a, b in zip(gen.fognatura_eur_m3, gen.depurazione_eur_m3)]
gA = gen.iloc[0]
add('Genova', float(gA.fognatura_eur_m3), float(gA.depurazione_eur_m3), 'tre fasce secondo la zona: da %.2f a %.2f euro' % (min(gv), max(gv)),
    'IRETI, Città Metropolitana di Genova, tariffe 2025', {'totale_m3_max': round(max(gv), 6)})
R['tariffe_citta'] = CITTA
pd.DataFrame(CITTA).to_csv(OUT / 'tariffe_citta_2025.csv', sep=';', index=False)
for c in CITTA: L('citta', c)

(OUT / 'riepilogo.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)), encoding='utf-8')
(PUL / '_log_elabora.txt').write_text('\n'.join(log), encoding='utf-8')
print('ok')
