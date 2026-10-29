"""Passo 3: aggrega per famiglia, territorio ed elezione; scrive i JSON del sito.
uso: python -I 16_aggrega.py <cartella elezioni> <cartella docs/elezioni>
Scrive: pulito/aggregati_territorio.csv, docs/elezioni/data/index.json, docs/elezioni/data/e/<id>.json
"""
import sys, os, re, json
import numpy as np
import pandas as pd

base, docs = sys.argv[1], sys.argv[2]
pul = os.path.join(base, 'pulito')
os.makedirs(os.path.join(docs, 'data', 'e'), exist_ok=True)

cat = pd.read_csv(os.path.join(pul, 'elezioni.csv'), encoding='utf-8-sig')
ris = pd.read_csv(os.path.join(pul, 'risultati_sezione.csv'), encoding='utf-8-sig', low_memory=False)
voti = pd.read_csv(os.path.join(pul, 'voti_sezione.csv'), encoding='utf-8-sig', dtype={'lista': str}, low_memory=False)
fam = pd.read_csv(os.path.join(base, 'famiglie_partiti.csv'), sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False)

ORDER = ['Sinistra', 'Centrosinistra', 'M5S', 'Centro', 'Centrodestra', 'Lega', 'Destra', 'Altri']
COLORI = {'Sinistra': '#b3202a', 'Centrosinistra': '#e8707a', 'M5S': '#e6b800', 'Centro': '#8a6fb5', 'Centrodestra': '#4a90d9',
          'Lega': '#1f7a3a', 'Destra': '#1f3b73', 'Altri': '#9a9a9a', 'Sì': '#2e8b57', 'No': '#c0392b'}

cat = cat[cat.nel_sito == 'si'].copy()
voti = voti[voti.elezione_id.isin(cat.elezione_id)]
ris = ris[ris.elezione_id.isin(cat.elezione_id)]

# ---- mappa lista -> famiglia (con intervalli di anni)
rules = {}
for r in fam.itertuples():
    a = int(r.anno_da) if r.anno_da else -1
    b = int(r.anno_a) if r.anno_a else 9999
    rules.setdefault(r.lista, []).append((a, b, r.famiglia))
anno_el = cat.set_index('elezione_id').anno.to_dict()
unmapped = {}


def fam_of(lista, anno):
    for a, b, f in rules.get(lista, []):
        if a <= anno <= b:
            return f
    unmapped[lista] = unmapped.get(lista, 0) + 1
    return 'Altri'


voti = voti.copy()
voti['anno'] = voti.elezione_id.map(anno_el)
key = voti[['lista', 'anno']].drop_duplicates()
key['famiglia'] = [fam_of(l, a) for l, a in zip(key.lista, key.anno)]
voti = voti.merge(key, on=['lista', 'anno'], how='left')

# ---- mojibake nei titoli dei quesiti (trappola nei metadati del portale)
def fix_title(t):
    t = t.replace('Servit�', 'Servitù').replace('Unit�', 'Unità')
    return t.replace('�', 'à')


def label(r):
    t = fix_title(str(r.titolo))
    if r.gruppo == 'referendum':
        t = re.sub(r'^Elezioni:\s*', '', t)
        t = re.sub(r'\s+del\s+\d{1,2}(-\d{1,2})?/\d{1,2}/\d{4}\s*$', '', t)
        t = re.sub(r'\s+\d{1,2}(-\d{1,2})?/\d{1,2}/\d{4}\s+', ' ', t)
        return t
    return re.sub(r'^Elezioni (del )?', '', t)


TIPI = {
    'comunali_consiglio': 'Comunali - Consiglio comunale',
    'comunali_sindaco': 'Comunali - Sindaco (primo turno)',
    'comunali_ballottaggio': 'Comunali - Ballottaggio',
    'municipali_consiglio': 'Municipali - Consiglio',
    'circoscrizionali_liste': 'Circoscrizionali 2011 - Liste',
    'camera': 'Politiche - Camera',
    'senato': 'Politiche - Senato',
    'europee': 'Europee',
    'regionali_consiglio': 'Regionali - Consiglio',
    'provinciali_consiglio': 'Provinciali 2009 - Consiglio',
    'referendum': 'Referendum',
}
SIST = {'circoscrizione': 'Circoscrizione', 'zona': 'Zona', 'municipio': 'Municipio'}

elez_out = []
agg_rows = []
for r in cat.sort_values(['data', 'ds_risultati']).itertuples():
    eid = r.elezione_id
    rr = ris[ris.elezione_id == eid].copy()
    vv = voti[voti.elezione_id == eid]
    pf = vv.pivot_table(index='sezione', columns='famiglia', values='voti', aggfunc='sum', fill_value=0)
    fams = [f for f in (['Sì', 'No'] if r.gruppo == 'referendum' else ORDER) if f in pf.columns and pf[f].sum() > 0]
    pf = pf.reindex(columns=fams).fillna(0)
    m = rr.set_index('sezione').join(pf, how='left')
    m[fams] = m[fams].fillna(0)
    m = m.reset_index().sort_values('sezione')
    # righe per sezione
    rows = []
    for x in m.itertuples(index=False):
        d = x._asdict()
        rows.append([int(d['sezione']), None if pd.isna(d['territorio']) else int(d['territorio']),
                     None if pd.isna(d['elettori']) else int(d['elettori']),
                     None if pd.isna(d['votanti']) else int(d['votanti'])] + [int(d[f]) for f in fams])
    json.dump({'id': eid, 'fam': fams, 'righe': rows}, open(os.path.join(docs, 'data', 'e', eid + '.json'), 'w'), separators=(',', ':'))

    def aggreg(g):
        e = g.elettori.sum(min_count=1)
        vt = g.votanti.sum(min_count=1)
        return dict(v=[int(g[f].sum()) for f in fams],
                    e=None if pd.isna(e) else int(e), vt=None if pd.isna(vt) else int(vt),
                    ns=int(g.sezione.nunique()))
    city = aggreg(m)
    terr = {}
    for t, g in m.groupby('territorio'):
        terr[str(int(t))] = aggreg(g)
        a = terr[str(int(t))]
        agg_rows.append(dict(elezione_id=eid, territorio=int(t), sistema=r.sistema_territorio, n_sezioni=a['ns'], elettori=a['e'], votanti=a['vt'],
                             **{f: v for f, v in zip(fams, a['v'])}))
    agg_rows.append(dict(elezione_id=eid, territorio=0, sistema='citta', n_sezioni=city['ns'], elettori=city['e'], votanti=city['vt'],
                         **{f: v for f, v in zip(fams, city['v'])}))
    note = []
    if city['e'] is None:
        note.append('affluenza non disponibile (campo Elettori a zero nel dataset)')
    elif city['vt'] is None:
        note.append('affluenza non disponibile (campo Votanti vuoto nel dataset)')
    if 'ufficiosi' in str(r.titolo):
        note.append('dati ufficiosi')
    if r.gruppo in ('comunali_consiglio', 'municipali_consiglio'):
        note.append('solo voti alle liste (esclusi i voti dati solo al sindaco/presidente)')
    if r.gruppo == 'comunali_ballottaggio':
        note.append('data corretta: nel dataset c\'e la data del primo turno')
    if isinstance(r.nota_data, str) and r.nota_data.startswith('Sessione'):
        note.append('data corretta (nel dataset: %s)' % r.nota_data.split(': ')[1])
    elez_out.append(dict(id=eid, tipo=r.gruppo, data=r.data, anno=int(r.anno), label=label(r), sistema=r.sistema_territorio,
                         ds=[int(r.ds_risultati)] + ([int(r.ds_voti)] if r.ds_voti == r.ds_voti and r.ds_voti != '' else []),
                         fam=fams, city=city, terr=terr, note=note))

idx = dict(
    generato='2026-10-29',
    famiglie=[dict(nome=f, colore=COLORI[f]) for f in ORDER + ['Sì', 'No']],
    tipi=[dict(id=k, label=v) for k, v in TIPI.items()],
    sistemi=SIST,
    elezioni=elez_out)
json.dump(idx, open(os.path.join(docs, 'data', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pd.DataFrame(agg_rows).to_csv(os.path.join(pul, 'aggregati_territorio.csv'), index=False, encoding='utf-8-sig')
pd.Series(unmapped).sort_values(ascending=False).to_csv(os.path.join(pul, 'liste_non_mappate.csv'), header=['righe'], encoding='utf-8-sig')
print('elezioni', len(elez_out), 'non mappate', len(unmapped))
tot = sum(os.path.getsize(os.path.join(docs, 'data', 'e', f)) for f in os.listdir(os.path.join(docs, 'data', 'e')))
print('size e/', tot, 'index', os.path.getsize(os.path.join(docs, 'data', 'index.json')))
