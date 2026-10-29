"""Confronti tra le scelte di abbinamento sezione -> NIL (solo per le note; non scrive nel sito).
 A) proporzionale (pesi 2020) contro prevalente (pesi 2020)
 B) pesi del 2020 contro pesi ricavati dallo stradario dell'anno dell'elezione (civici ritrovati nel ds939 per via+civico+barrato)
Misure per elezione, sui NIL con almeno 2.000 votanti nella variante proporzionale:
 NIL col leader (famiglia piu' votata) diverso; scarto medio e massimo (punti percentuali) della quota della famiglia in testa.
uso: python -I 42_nil_confronti.py <cartella elezioni> <cartella docs/elezioni>
Scrive pulito/nil_confronti.csv
"""
import sys, os, glob, json
import pandas as pd
import numpy as np

base, docs = sys.argv[1], sys.argv[2]
pul = os.path.join(base, 'pulito')
W = pd.read_csv(os.path.join(pul, 'sezione_nil.csv'), encoding='utf-8-sig')
idx = json.load(open(os.path.join(docs, 'data', 'index.json'), encoding='utf-8'))
EL = {e['id']: e for e in idx['elezioni']}


def leggi(path):
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            return pd.read_csv(path, sep=None, engine='python', encoding=enc, dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            continue


d = leggi(glob.glob(os.path.join(base, 'raw', 'ds939-*', '*.csv'))[0])
d = d[d.ID_NIL != ''].copy()
d['k'] = d.CODICE_VIA.str.strip() + '|' + d.CIVICO.str.strip() + '|' + d.BARRATO.str.strip().str.upper().replace({'0': ''})
nilk = d.drop_duplicates('k').set_index('k').ID_NIL.astype(int)


def famiglie(eid):
    D = json.load(open(os.path.join(docs, 'data', 'e', eid + '.json'), encoding='utf-8'))
    df = pd.DataFrame(D['righe'], columns=['sezione', 'terr', 'e', 'vt'] + D['fam'])
    return df, D['fam']


def alloca(df, fams, w, prev=False):
    j = df[['sezione'] + fams].merge(w, on='sezione')
    if prev:
        j = j[j.prevalente == 'si']
        return j.groupby('id_nil')[fams].sum()
    j[fams] = j[fams].multiply(j.peso, axis=0)
    return j.groupby('id_nil')[fams].sum()


def misura(a, b, min_vot=2000):
    """a, b: DataFrame NIL x famiglie. Confronto sui NIL presenti in entrambi e con abbastanza voti in a."""
    ix = [n for n in a.index if n in b.index and a.loc[n].sum() >= min_vot]
    pa = a.loc[ix].div(a.loc[ix].sum(axis=1), axis=0)
    pb = b.loc[ix].div(b.loc[ix].sum(axis=1), axis=0)
    lead_a, lead_b = pa.idxmax(axis=1), pb.idxmax(axis=1)
    diff = [abs(pa.loc[n, lead_a[n]] - pb.loc[n, lead_a[n]]) * 100 for n in ix]
    return len(ix), int((lead_a != lead_b).sum()), float(np.mean(diff)), float(np.max(diff))


STR = {'comunali_consiglio_2016-06-05': 'ds1118', 'camera_2018-03-04': 'ds1120', 'comunali_consiglio_2021-10-03': 'ds1614',
       'regionali_consiglio_2023-02-12': 'ds2169', 'europee_2024-06-08': 'ds2741', 'referendum_2026-03-22_ds2975': 'ds2973'}
out = []
for eid in ['comunali_consiglio_2016-06-05', 'camera_2018-03-04', 'comunali_consiglio_2021-10-03', 'regionali_consiglio_2023-02-12',
            'europee_2024-06-08', 'referendum_2026-03-22_ds2975']:
    df, fams = famiglie(eid)
    prop = alloca(df, fams, W)
    prev = alloca(df, fams, W, prev=True)
    n, nc, mm, mx = misura(prop, prev)
    r = dict(elezione=eid, confronto='proporzionale contro prevalente', nil_confrontati=n, leader_diverso=nc, scarto_medio_pp=round(mm, 2), scarto_max_pp=round(mx, 2))
    out.append(r)
    ds = STR[eid]
    f = glob.glob(os.path.join(base, 'raw', ds + '[-_]*', '**', '*.csv'), recursive=True)[0]
    x = leggi(f)
    cs, cv, cc, cb = (('Sezione', 'CodVia', 'Civico', 'Barrato') if 'Sezione' in x.columns else
                      ('SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'))
    x = x[x[cs].str.strip() != '']
    x['k'] = x[cv].str.strip() + '|' + x[cc].str.strip() + '|' + x[cb].str.strip().str.upper().replace({'0': ''})
    x = x.drop_duplicates('k')
    x['sezione'] = x[cs].astype(int)
    x['id_nil'] = x.k.map(nilk)
    xt = x.dropna(subset=['id_nil'])
    w2 = xt.groupby(['sezione', 'id_nil']).size().rename('n').reset_index()
    w2['peso'] = w2.n / w2.groupby('sezione').n.transform('sum')
    w2 = w2.sort_values(['sezione', 'peso', 'id_nil'], ascending=[True, False, True])
    w2['prevalente'] = (~w2.duplicated('sezione')).map({True: 'si', False: 'no'})
    w2['id_nil'] = w2.id_nil.astype(int)
    # sezioni senza civici ritrovati: pesi del 2020
    mancano = set(W.sezione) - set(w2.sezione)
    w2 = pd.concat([w2[['sezione', 'id_nil', 'peso', 'prevalente']], W[W.sezione.isin(mancano)][['sezione', 'id_nil', 'peso', 'prevalente']]])
    prop2 = alloca(df, fams, w2)
    prev2 = alloca(df, fams, w2, prev=True)
    n, nc, mm, mx = misura(prop, prop2)
    out.append(dict(elezione=eid, confronto='pesi 2020 contro pesi stradario %s (proporzionale)' % ds, nil_confrontati=n, leader_diverso=nc,
                    scarto_medio_pp=round(mm, 2), scarto_max_pp=round(mx, 2)))
    n, nc, mm, mx = misura(prev, prev2)
    out.append(dict(elezione=eid, confronto='pesi 2020 contro pesi stradario %s (prevalente)' % ds, nil_confrontati=n, leader_diverso=nc,
                    scarto_medio_pp=round(mm, 2), scarto_max_pp=round(mx, 2)))
r = pd.DataFrame(out)
r.to_csv(os.path.join(pul, 'nil_confronti.csv'), index=False, encoding='utf-8-sig')
print(r.to_string())

# ---- C) controllo con un dato indipendente: elettori (Comunali 2021, proporzionale e prevalente) contro residenti adulti 2021 per NIL
# (ds205, filone citta-15-minuti, sola lettura). Residenti adulti = Totale - Minori (comprende gli stranieri, che non votano: il rapporto non e' 1).
pop = pd.read_csv(os.path.join(base, '..', 'citta-15-minuti', 'raw', 'comune_milano', 'pop_caratteristiche_quartiere', 'ds205_dati_quartieri_2011_2024_.csv'),
                  sep=';', encoding='utf-8-sig')
pop = pop[pop.Anno == 2021].set_index('NIL')
ad = (pop.Totale - pop.Minori)
nd = json.load(open(os.path.join(docs, 'data', 'nil', 'comunali_consiglio_2021-10-03.json')))
rows = []
for var in ('p', 'm'):
    el = pd.Series({int(k): v['e'] for k, v in nd[var].items()})
    j = pd.concat([el.rename('elettori'), ad.rename('adulti')], axis=1, join='inner')
    j['rapp'] = j.elettori / j.adulti
    rows.append((var, len(j), j.elettori.corr(j.adulti), j.rapp.median(), j.rapp.quantile(.1), j.rapp.quantile(.9)))
    if var == 'p':
        print(j.sort_values('rapp').head(6).to_string()); print(j.sort_values('rapp').tail(6).to_string())
print(pd.DataFrame(rows, columns=['variante', 'nil', 'correlazione', 'rapporto_mediano', 'p10', 'p90']).to_string())

# ---- D) NIL "fragili": rapporto elettori/residenti adulti fuori da 0,5-1,5 (proporzionale, Comunali 2021). Scritto in pulito/nil_controllo_popolazione.csv
# e come campo x (1 = fragile) e r (rapporto) in docs/.../data/nil_info.json: la pagina li segna insieme ai NIL con pochi votanti.
el = pd.Series({int(k): v['e'] for k, v in nd['p'].items()})
j = pd.concat([el.rename('elettori'), ad.rename('adulti')], axis=1, join='outer')
j = j[j.index.notna() & j.elettori.notna()]
j['rapporto'] = (j.elettori / j.adulti.replace(0, np.nan)).round(2)
j['fragile'] = ((j.rapporto < 0.5) | (j.rapporto > 1.5) | j.rapporto.isna()).astype(int)
j.index.name = 'id_nil'
j.to_csv(os.path.join(pul, 'nil_controllo_popolazione.csv'), encoding='utf-8-sig')
pi = os.path.join(docs, 'data', 'nil_info.json')
info = json.load(open(pi, encoding='utf-8'))
nomi = {k: v['nome'] for k, v in info.items()}
for k in info:
    row = j.loc[int(k)]
    info[k]['x'] = int(row.fragile)
    info[k]['r'] = None if pd.isna(row.rapporto) else float(row.rapporto)
json.dump(info, open(pi, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('NIL fragili:', int(j.fragile.sum()), [(int(i), nomi[str(int(i))]) for i in j.index[j.fragile == 1]])
