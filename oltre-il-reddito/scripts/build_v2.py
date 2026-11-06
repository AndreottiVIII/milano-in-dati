"""Oltre il reddito, versione 2: dati per i grafici nuovi (gruppi sulla mappa, coppie dello stesso CAP, quadrante, scheda del quartiere).

Uso:  python -I -X utf8 C:\\Users\\davide\\Desktop\\ClaudeTower\\milano-in-dati\\oltre-il-reddito\\scripts\\build_v2.py

Parte da docs/oltre-il-reddito/data/riepilogo.json (scritto da build.py, non lo modifica) e da file locali del progetto.
Scrive, con nomi nuovi:
  docs/oltre-il-reddito/data/quartieri_v2.json   70 quartieri + riferimenti di Milano + coppie + CAP + quadrante
  docs/oltre-il-reddito/data/confini_nil.json    confini dei 88 quartieri (coordinate a 4 decimali, solo id e nome)
"""
import json
import os

import numpy as np
import pandas as pd

R = r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati'
DATA = os.path.join(R, 'docs', 'oltre-il-reddito', 'data')


def p(*a):
    return os.path.join(R, *a)


d = json.load(open(os.path.join(DATA, 'riepilogo.json'), encoding='utf8'))
q = pd.DataFrame(d['quartieri'])

# anni di vita stimati (speranza-vita, 2022-2024, tutti) e riferimento di Milano
sm = pd.read_csv(p('speranza-vita', 'pulito', 'nil_smr_e0.csv'))
t = sm[(sm.finestra == '2022-2024') & (sm.sesso == 'T')].set_index('id_nil')
q['e0'] = q.i.map(t.e0)
q['e0lo'] = q.i.map(t.e0_lo)
q['e0hi'] = q.i.map(t.e0_hi)
e0_citta = float(t.e0_citta.dropna().iloc[0])

# CAP dominante del quartiere
cc = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL'])
cc['id'] = cc.ID_NIL.astype(int)
dom = cc.sort_values('quota_nil').groupby('id').tail(1).set_index('id')
q['cap'] = q.i.map(dom.CAP).astype(int)

# affluenza di Milano: tutti i votanti sugli elettori della Camera 2022, 88 quartieri
cam = json.load(open(p('docs', 'elezioni', 'data', 'nil', 'camera_2022-09-25.json'), encoding='utf8'))['p']
aff_milano = sum(v['vt'] for v in cam.values()) / sum(v['e'] for v in cam.values()) * 100

# tre gruppi per affluenza (24 / 23 / 23, come build.py)
q['g'] = pd.qcut(q.aff, 3, labels=[0, 1, 2]).astype(int)
terzi = []
for g in (0, 1, 2):
    s = q[q.g == g]
    terzi.append(dict(g=g, n=int(len(s)), aff_min=float(s.aff.min()), aff_max=float(s.aff.max()), O=int(s.O.sum()), E=float(d['terzi'][g]['E']),
                      rapporto=float(d['terzi'][g]['rapporto']), e0=float((s.e0 * s.res).sum() / s.res.sum()), res=int(s.res.sum())))

# fasce di reddito: terzi per reddito, dentro due metà per affluenza (come build.py)
q['fr'] = pd.qcut(q.red, 3, labels=[0, 1, 2]).astype(int)
fasce = []
for fr in (0, 1, 2):
    s0 = q[q.fr == fr]
    med = s0.aff.rank(method='first')
    m = pd.qcut(med, 2, labels=[0, 1]).astype(int)
    for ma in (0, 1):
        s = s0[m == ma]
        fasce.append(dict(fr=fr, ma=ma, n=int(len(s)), O=int(s.O.sum()), E=float(s.E.sum()), rapporto=float(s.O.sum() / s.E.sum()),
                          aff_media=float(s.aff.mean()), media_smr=float(s.smr.mean())))
# nota: build.py usa qcut dell'affluenza dentro la fascia; qui si controlla che coincida
for f_old in d['fasce']:
    fr = {'basso': 0, 'medio': 1, 'alto': 2}[f_old['reddito']]
    ma = {'bassa': 0, 'alta': 1}[f_old['affluenza']]
    f_new = [x for x in fasce if x['fr'] == fr and x['ma'] == ma][0]
    assert abs(f_new['rapporto'] - f_old['rapporto']) < 1e-4, (f_old, f_new)

# quadrante: metà alta/bassa per reddito e per le altre sette misure (posizione 1 = valore più alto)
half = (len(q) + 1) / 2
q['rh'] = np.where(q.pr <= half, 1, 0)   # 1 = reddito alto
q['ih'] = np.where(q.pi <= half, 1, 0)   # 1 = altre misure alte
q['quad'] = q.rh * 2 + q.ih              # 0 entrambi bassi, 1 solo altre misure alte, 2 solo reddito alto, 3 entrambi alti
quad = []
for k in (0, 1, 2, 3):
    s = q[q.quad == k]
    quad.append(dict(k=k, n=int(len(s)), O=int(s.O.sum()), E=float(s.E.sum()), rapporto=float(s.O.sum() / s.E.sum()),
                     aff_media=float(s.aff.mean())))

# CAP con almeno due quartieri: quello con meno affluenza contro quello con più affluenza
cap = []
for c, g in q.groupby('cap'):
    if len(g) < 2:
        continue
    g = g.sort_values('aff')
    a, b = g.iloc[0], g.iloc[-1]
    cap.append(dict(cap=int(c), lo=int(a.i), hi=int(b.i), gap_aff=float(b.aff - a.aff), smr_lo=float(a.smr), smr_hi=float(b.smr),
                    piu_morti_dove_si_vota_meno=bool(a.smr > b.smr), n_quartieri=int(len(g))))
cap.sort(key=lambda x: -x['gap_aff'])

# coppie da raccontare: stesso CAP, ognuno con almeno 8.000 residenti, almeno 4 punti di affluenza di differenza,
# più morti dove si vota meno; le tre con la distanza maggiore tra i morti, un CAP ciascuna; niente quartieri "da leggere con cautela"
cand = []
for c, g in q.groupby('cap'):
    g = g[(g.res >= 8000) & (g.c == 0)].sort_values('aff')
    if len(g) < 2:
        continue
    a, b = g.iloc[0], g.iloc[-1]
    if b.aff - a.aff >= 4 and a.smr > b.smr:
        cand.append((float(a.smr - b.smr), int(a.i), int(b.i), int(c)))
cand.sort(reverse=True)
coppie = [dict(cap=c, lo=lo, hi=hi) for _, lo, hi, c in cand[:3]]

# vicini per reddito: per ogni quartiere gli 8 con reddito più vicino (esclusi sé stessi)
vic = {}
for r in q.itertuples():
    dd = (q.red - r.red).abs()
    dd[q.i == r.i] = 1e18
    vic[int(r.i)] = [int(x) for x in q.loc[dd.sort_values(kind='stable').index[:8], 'i']]

# confini
g = json.load(open(p('docs', 'speranza-vita', 'data', 'nil.geojson'), encoding='utf8'))


def arr(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [arr(x) for x in c]


feat = [dict(type='Feature', properties=dict(i=f['properties']['i'], n=f['properties']['n']),
             geometry=dict(type=f['geometry']['type'], coordinates=arr(f['geometry']['coordinates']))) for f in g['features']]
json.dump(dict(type='FeatureCollection', features=feat), open(os.path.join(DATA, 'confini_nil.json'), 'w', encoding='utf8'),
          ensure_ascii=False, separators=(',', ':'))

rows = []
for r in q.itertuples():
    rows.append(dict(i=int(r.i), n=r.n, res=int(r.res), red=int(r.red), aff=round(float(r.aff), 2), O=int(r.O), E=round(float(r.E), 1),
                     smr=round(float(r.smr), 4), e0=round(float(r.e0), 2), e0lo=round(float(r.e0lo), 2), e0hi=round(float(r.e0hi), 2),
                     cap=int(r.cap), g=int(r.g), pr=float(r.pr), pi=float(r.pi), quad=int(r.quad), c=int(r.c), vic=vic[int(r.i)]))
out = dict(
    n_quartieri=len(q), milano=dict(aff=round(aff_milano, 2), e0=round(e0_citta, 2), smr=1.0, O=d['tot_O'], E=round(d['tot_E'], 1)),
    terzi=terzi, fasce=fasce, soglie_reddito=d['fasce_soglie_reddito'], quad=quad, cap=cap, coppie=coppie,
    stabili=d['indice']['pesi_casuali']['stabili'], indicatori=[x['nome'] for x in d['indice']['indicatori']],
    quartieri=rows)
json.dump(out, open(os.path.join(DATA, 'quartieri_v2.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(rows), 'quartieri;', len(cap), 'CAP;', sum(x['piu_morti_dove_si_vota_meno'] for x in cap), 'con piu morti dove si vota meno;',
      'coppie', [(c['cap'], c['lo'], c['hi']) for c in coppie])
print('terzi', [(t['n'], round(t['rapporto'], 3), round(t['e0'], 2)) for t in terzi], 'milano', out['milano'])
print('quad', [(x['k'], x['n'], round(x['rapporto'], 3)) for x in quad])
