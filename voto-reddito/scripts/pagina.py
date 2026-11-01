"""Passo 5: scrive i dati della pagina docs/voto-reddito/data/ a partire da voto-reddito/out/.
Rieseguibile. Uso: python -I -X utf8 pagina.py <milano-in-dati> <voto-reddito>
Scrive: pagina.json (generale), elezioni.json (per elezione: decili con intervalli, gap, Spearman, quote per CAP),
sez/<elezione>.json (quote per sezione, voci chiave; caricate solo quando servono), copie dei CSV aggregati.
Nessun dato di singole persone: solo quote per decile, CAP, sezione.
"""
import sys, os, json, shutil
import numpy as np
import pandas as pd

base, dest = sys.argv[1], sys.argv[2]
OUT = os.path.join(dest, 'out')
DOC = os.path.join(base, 'docs', 'voto-reddito', 'data')
os.makedirs(os.path.join(DOC, 'sez'), exist_ok=True)


def rd(n):
    return pd.read_csv(os.path.join(OUT, n))


g = rd('gradiente_per_voce.csv')
dd = rd('decili_per_voce.csv')
cp = rd('cap_per_voce.csv')
cr = rd('cap_reddito.csv')
dfn = rd('decili_definizione.csv')
rob = rd('robustezza.csv')
sq = rd('sezioni_quote_voci_chiave.csv')
sezr = rd('sezioni_reddito_decile.csv')
par = json.load(open(os.path.join(OUT, 'parametri.json'), encoding='utf-8'))
ctrl = json.load(open(os.path.join(OUT, 'controllo_cap_filone9.json'), encoding='utf-8'))
rr = rd('nil_rapporto_elettori_adulti_reddito.csv')
comp = rd('composizione_decili_per_cap.csv')

# ---- correzioni di ortografia nelle etichette (i nomi interni sono senza accenti)
FIX = [('Si =', 'Sì ='), ('Incandidabilita', 'Incandidabilità'), ('Indennita', 'Indennità'), ('piu autonomia', 'più autonomia'),
       ('Lavoro 2025 - Sicurezza appalti', 'Lavoro 2025 - Responsabilità negli appalti'),
       ('Lavoro 2025 - Indennità licenziamento', 'Lavoro 2025 - Indennità nelle piccole imprese'),
       ('Lavoro 2025 - Licenziamenti (Sì = abrogare)', 'Lavoro 2025 - Licenziamenti illegittimi (Sì = abrogare)')]


def lab(s):
    for a, b in FIX:
        s = s.replace(a, b)
    return s


TIPO_PAG = {'camera': 'politiche', 'senato': 'politiche', 'europee': 'europee', 'regionali_consiglio': 'regionali',
            'comunali_consiglio': 'comunali', 'comunali_sindaco': 'comunali', 'comunali_ballottaggio': 'comunali', 'referendum': 'referendum'}
UFFICIOSE = {'camera_2018-03-04', 'camera_2022-09-25', 'senato_2018-03-04', 'senato_2022-09-25', 'regionali_consiglio_2023-02-12'}

caps = sorted(cr.cap.tolist())
elez = []
ids = g[['elezione_id', 'etichetta', 'data', 'gruppo']].drop_duplicates().sort_values(['data', 'elezione_id'])
# Senato: stessa storia della Camera, tolto per semplicita. ds1893 (Elezione CSM) ha gli stessi numeri di ds1892 in tutte le sezioni: tenuto solo ds1892
ids = ids[(ids.gruppo != 'senato') & (ids.elezione_id != 'referendum_2022-06-12_ds1893')]
for r in ids.itertuples():
    e = r.elezione_id
    ge = g[g.elezione_id == e]
    de = dd[dd.elezione_id == e]
    ce = cp[cp.elezione_id == e]
    voci = []
    for v in ge.itertuples():
        if v.voce == 'No':
            continue
        dv = de[de.voce == v.voce].sort_values('decile')
        item = dict(n=v.voce, tp=v.tipo, city=v.quota_citta_pct,
                    dec=dv.quota_pct.tolist(), lo=dv.ic_lo.tolist(), hi=dv.ic_hi.tolist(),
                    gap=v.gap_D10_D1_pp, glo=v.gap_ic_lo, ghi=v.gap_ic_hi, gap9=v.gap_D9_D1_pp,
                    sp=v.spearman_cap, splo=v.sp_ic_lo, sphi=v.sp_ic_hi)
        if v.tipo in ('famiglia', 'blocco', 'quesito', 'affluenza'):
            cv = ce[ce.voce == v.voce].set_index('cap')
            item['cap'] = [None if (c not in cv.index or not np.isfinite(cv.quota_pct.get(c, np.nan))) else float(cv.quota_pct[c]) for c in caps]
        voci.append(item)
    elez.append(dict(id=e, label=lab(r.etichetta), data=r.data, anno=int(r.data[:4]), gruppo=r.gruppo, tipo=TIPO_PAG[r.gruppo],
                     copertura=float(ge.copertura_votanti_pct.iloc[0]), ufficiose=e in UFFICIOSE, voci=voci))
json.dump(dict(caps=caps, elezioni=elez), open(os.path.join(DOC, 'elezioni.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---- sezioni: ordine fisso, reddito, CAP prevalente; quote per elezione (file a parte)
sezr = sezr.sort_values('sezione').reset_index(drop=True)
sec_ids = sezr.sezione.tolist()
pos = {s: i for i, s in enumerate(sec_ids)}
sezj = dict(sez=sec_ids, cap=sezr.cap_prev.astype(int).tolist(), inc=[int(round(x)) for x in sezr.inc], dec=sezr.decile.astype(int).tolist(),
            peso=[round(float(x), 2) for x in sezr.peso_prev])
json.dump(sezj, open(os.path.join(DOC, 'sezioni.json'), 'w'), separators=(',', ':'))
keep = {e['id'] for e in elez}
nfile = 0
for e, gg in sq.groupby('elezione_id'):
    if e not in keep:
        continue
    out = {}
    for v, g2 in gg.groupby('voce'):
        arr = [None] * len(sec_ids)
        for s, q in zip(g2.sezione, g2.quota_pct):
            if s in pos:
                arr[pos[s]] = float(q)
        out[v] = arr
    json.dump(out, open(os.path.join(DOC, 'sez', e + '.json'), 'w'), separators=(',', ':'))
    nfile += 1

# ---- registro elettorale: elettori / adulti residenti per quinto di reddito dei NIL
rr = rr.copy()
q = rr.groupby('q').rapporto.agg(['median', 'min', 'max', 'count']).reset_index()
from scipy.stats import spearmanr
rho = float(spearmanr(rr.rapporto, rr.reddito_2019_22_euro2025).statistic)
registro = dict(quinti=[dict(q=int(r.q), mediana=round(float(r['median']), 2), min=round(float(r['min']), 2), max=round(float(r['max']), 2), n=int(r['count']))
                        for _, r in q.iterrows()], rho=round(rho, 2))

# ---- robustezza: poche righe scelte
sel_e = ['Comunali - Sindaco 2021', 'Politiche - Camera 2018', 'Politiche - Camera 2022', 'Regionali - Consiglio 2023', 'Europee 2024']
sel_v = ['Sx (Sinistra+Centrosinistra)', 'Centrosinistra', 'Centro', 'M5S', 'Dx (Centrodestra+Lega+Destra)', 'AFFLUENZA']
rb = rob[rob.etichetta.isin(sel_e) & rob.voce.isin(sel_v)]
rows = []
for (et, v), gg in rb.groupby(['etichetta', 'voce']):
    pr = gg[gg.variante.str.startswith('principale')].iloc[0]
    s3 = gg[gg.variante.str.startswith('senza')].iloc[0]
    nl = gg[gg.livello == 'NIL'].iloc[0]
    rows.append(dict(e=et, v=v, sp=float(pr.spearman), pend=float(pr.pendenza_pp_per_10k), sp3=float(s3.spearman), pend3=float(s3.pendenza_pp_per_10k),
                     nil_pend=float(nl.pendenza_pp_per_10k), nil_ctrl=float(nl.pend_con_controlli), nil_ctrl_lo=float(nl.pend_con_controlli_ic_lo),
                     nil_ctrl_hi=float(nl.pend_con_controlli_ic_hi), nil_n=int(nl.variante.split('(')[1].split(' ')[0])))
rob_small = rows
rv = rob[rob.variante.str.startswith('varianza')]
var_small = [dict(e=r.etichetta, v=r.voce, eta2=float(r.eta2_tra_cap), r2=float(r.r2_reddito)) for r in rv.itertuples() if r.etichetta in sel_e and r.voce in sel_v]

pj = dict(
    aggiornato='2026-11-01', sezioni_con_legame=par['sezioni_con_legame'], civici=ctrl['civici_ds939'], civici_esclusi=ctrl['civici_senza_reddito_cap100_cap54'],
    stesso_cap_pct=ctrl['stesso_cap_pct'], civici_confrontabili=ctrl['civici_confrontabili'],
    decili=[dict(d=int(r.decile), sezioni=int(r.sezioni), quota=round(float(r.quota_elettori_2021), 3), rmin=round(float(r.reddito_min)), rmax=round(float(r.reddito_max)),
                 rmed=round(float(r.reddito_medio_pesato)), ncap=int(r.n_cap_prevalenti)) for r in dfn.itertuples()],
    d10_cap=[dict(cap=int(r.cap_prev), quota=round(float(r.quota_decile), 3), red=round(float(r.reddito_cap))) for r in comp[comp.decile == 10].itertuples() if r.quota_decile > 0.05],
    cap=[dict(cap=int(r.cap), red=round(float(r.reddito_2019_22_euro2025)), contrib=round(float(r.contribuenti_2019_22)), civici=int(r.civici_ds939))
         for r in cr.sort_values('cap').itertuples()],
    cap_instabili=[20121, 20122, 20145],
    registro=registro, robustezza=rob_small, varianza=var_small,
    cop_min=float(g.copertura_votanti_pct.min()), cop_max=float(g.copertura_votanti_pct.max()),
    popolazione_anno=par['anno_popolazione'])
json.dump(pj, open(os.path.join(DOC, 'pagina.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---- CSV aggregati scaricabili
for n in ['gradiente_per_voce.csv', 'decili_per_voce.csv', 'cap_per_voce.csv', 'cap_reddito.csv', 'robustezza.csv', 'decili_definizione.csv']:
    shutil.copyfile(os.path.join(OUT, n), os.path.join(DOC, n))
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DOC) for f in fs)
print('elezioni', len(elez), '; file sez', nfile, '; totale dati', round(tot / 1e6, 2), 'MB')
