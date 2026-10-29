"""Passo 3: aggrega per partito (lista) e per famiglia, territorio ed elezione; scrive i JSON del sito.
Nel sito ogni elezione ha: fam (famiglie, per tabella sezioni e mappa), par (lista di [nome, indice famiglia]), city.v e terr[n].v (voti per partito, nell'ordine di par).
Le liste sotto lo 0,5% dei voti di lista della citta (se almeno 2 nella stessa famiglia) sono unite in "Altre liste" della famiglia.
Dal 2026-10-29 include anche le consultazioni 1946-1979 di Eligendo (pulito/milano_pre1979.csv): solo totale della citta, nessun territorio ne' sezione
(flag pre=True, sistema=None, terr={}). Le coppie (tipo, data) gia' presenti nei dati del Comune (es. Camera 1979) non si duplicano.
Dal 2026-10-29 (seconda parte) aggrega anche per quartiere (NIL) le elezioni dal 2016 in cui almeno il 95% delle sezioni (e dei votanti) e' in
pulito/sezione_nil.csv (prodotto da 40_sezione_nil.py): scrive docs/elezioni/data/nil/<id>.json con due varianti (p = sezioni divise in proporzione
ai civici, m = sezione assegnata al NIL prevalente) e aggiunge a ogni elezione di index.json il campo "nil".
uso: python -I 16_aggrega.py <cartella elezioni> <cartella docs/elezioni>
Scrive: pulito/aggregati_territorio.csv, docs/elezioni/data/index.json, docs/elezioni/data/e/<id>.json, docs/elezioni/data/nil/<id>.json
"""
import sys, os, re, json
import numpy as np
import pandas as pd

base, docs = sys.argv[1], sys.argv[2]
pul = os.path.join(base, 'pulito')
os.makedirs(os.path.join(docs, 'data', 'e'), exist_ok=True)
os.makedirs(os.path.join(docs, 'data', 'nil'), exist_ok=True)
SOGLIA_NIL = 0.95   # quota minima di sezioni E di votanti abbinate a un NIL per pubblicare l'elezione per quartiere
ANNO_NIL = 2016
WNIL = pd.read_csv(os.path.join(base, 'pulito', 'sezione_nil.csv'), encoding='utf-8-sig')
NILMATCH = []       # righe per il rapporto sul match

cat = pd.read_csv(os.path.join(pul, 'elezioni.csv'), encoding='utf-8-sig')
ris = pd.read_csv(os.path.join(pul, 'risultati_sezione.csv'), encoding='utf-8-sig', low_memory=False)
voti = pd.read_csv(os.path.join(pul, 'voti_sezione.csv'), encoding='utf-8-sig', dtype={'lista': str}, low_memory=False)
fam = pd.read_csv(os.path.join(base, 'famiglie_partiti.csv'), sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False)

ORDER = ['Sinistra', 'Centrosinistra', 'M5S', 'Centro', 'Centrodestra', 'Lega', 'Destra', 'Altri']
# colori guidati da quelli storici: PCI rosso, PSI/PDS/PD rosa-rosso, DC bianco, Forza Italia azzurro, Lega verde, MSI nero, M5S giallo
COLORI = {'Sinistra': '#c1121f', 'Centrosinistra': '#ef6f6c', 'M5S': '#f2c500', 'Centro': '#ffffff', 'Centrodestra': '#3a8fd9',
          'Lega': '#1e8a3c', 'Destra': '#222222', 'Altri': '#9a9a9a', 'Sì': '#2e8b57', 'No': '#c0392b'}
SOGLIA = 0.005

cat = cat[cat.nel_sito == 'si'].copy()
voti = voti[voti.elezione_id.isin(cat.elezione_id)]
ris = ris[ris.elezione_id.isin(cat.elezione_id)]


# ---- consultazioni prima del 1979 (Eligendo, ministero dell'Interno): una "sezione" finta (0) = totale della citta
PRE = {}
pre = pd.read_csv(os.path.join(pul, 'milano_pre1979.csv'), encoding='utf-8-sig')
pre['gruppo'] = pre.tipo.map({'comunali': 'comunali_consiglio', 'regionali': 'regionali_consiglio'}).fillna(pre.tipo)
pre['qn'] = pre.quesito.fillna('').str.extract(r'^(\d+)')[0].fillna('0').astype(int)
pre['eid'] = [e if q == 0 else '%s_q%d' % (e, q) for e, q in zip(pre.elezione_id, pre.qn)]
dup = set(zip(cat.gruppo, cat.data))
pre = pre[[(g, d) not in dup for g, d in zip(pre.gruppo, pre.data)]]
LAB_PRE = {'costituente': 'Assemblea Costituente %s', 'camera': 'Politiche %s - Camera', 'senato': 'Politiche %s - Senato',
           'regionali_consiglio': 'Regionali %s - Consiglio Regionale', 'comunali_consiglio': 'Comunali %s - Consiglio Comunale'}
NOME_REF = {'referendum_1946-06-02_q1': 'Referendum istituzionale (Repubblica o Monarchia)',
            'referendum_1974-05-12_q1': 'Referendum Abrogativo su Divorzio', 'referendum_1978-06-11_q1': 'Referendum Abrogativo su Ordine pubblico',
            'referendum_1978-06-11_q2': 'Referendum Abrogativo su Finanziamento pubblico dei partiti'}
cat_p, ris_p, voti_p = [], [], []
for eid, g in pre.groupby('eid'):
    x = g.iloc[0]
    ref = x.gruppo == 'referendum'
    lab = NOME_REF[eid] if ref else LAB_PRE[x.gruppo] % x.data[:4]
    PRE[eid] = dict(label=lab, ref=ref, tipo=x.gruppo, liste=set(g.lista))
    cat_p.append(dict(elezione_id=eid, gruppo=x.gruppo, etichetta=lab, data=x.data, anno=int(x.data[:4]), titolo=lab,
                      ds_risultati=float(x.qn), sistema_territorio=None, nel_sito='si'))
    ris_p.append(dict(elezione_id=eid, sezione=0, territorio=np.nan, elettori=x.elettori, votanti=x.votanti))
    for r in g.itertuples():
        l = {'SI': 'Sì', 'NO': 'No'}.get(r.lista, r.lista) if ref else r.lista
        voti_p.append(dict(elezione_id=eid, sezione=0, territorio=np.nan, lista=l, voti=int(r.voti)))
cat = pd.concat([cat, pd.DataFrame(cat_p)], ignore_index=True)
ris = pd.concat([ris, pd.DataFrame(ris_p)], ignore_index=True)
voti = pd.concat([voti, pd.DataFrame(voti_p)], ignore_index=True)

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
_m = voti.elezione_id.isin([k for k, v in PRE.items() if v['ref']])
voti.loc[_m, 'famiglia'] = voti.loc[_m, 'lista']

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
    'costituente': 'Assemblea Costituente 1946',
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
    # ---- partiti: nome lista, famiglia; le piccole (<0.5%) unite in "Altre liste" per famiglia
    vv = vv.copy()
    vv['nome'] = vv.famiglia if r.gruppo == 'referendum' else vv.lista.str.strip()
    if eid.startswith('referendum_1946'):
        vv['nome'] = vv.nome.map({'Sì': 'Repubblica', 'No': 'Monarchia'})
    g1 = vv.groupby(['nome', 'famiglia']).voti.sum().reset_index()
    g1 = g1[g1.voti > 0]
    tot_c = g1.voti.sum()
    piccole = g1[g1.voti < SOGLIA * tot_c]
    unire = {f for f, n in piccole.famiglia.value_counts().items() if n >= 2}
    mp = {(n, f): ('Altre liste' if (f in unire and v < SOGLIA * tot_c) else n) for n, f, v in g1.itertuples(index=False)}
    vv['pnome'] = [mp.get((n, f)) for n, f in zip(vv.nome, vv.famiglia)]
    vv = vv[vv.pnome.notna()]
    g2 = vv.groupby(['pnome', 'famiglia']).voti.sum().reset_index()
    g2['fi'] = g2.famiglia.map({f: i for i, f in enumerate(fams)})
    g2['altre'] = (g2.pnome == 'Altre liste').astype(int)
    g2 = g2.sort_values(['fi', 'altre', 'voti', 'pnome'], ascending=[True, True, False, True]).reset_index(drop=True)
    par = [[n, int(fi)] for n, fi in zip(g2.pnome, g2.fi)]
    pcols = ['P%d' % i for i in range(len(par))]
    pidx = {(n, f): i for i, (n, f) in enumerate(zip(g2.pnome, g2.famiglia))}
    vv['pi'] = [pidx[(n, f)] for n, f in zip(vv.pnome, vv.famiglia)]
    pp = vv.pivot_table(index='sezione', columns='pi', values='voti', aggfunc='sum', fill_value=0).reindex(columns=range(len(par))).fillna(0)
    pp.columns = pcols
    m = rr.set_index('sezione').join(pf, how='left').join(pp, how='left')
    m[fams] = m[fams].fillna(0)
    m[pcols] = m[pcols].fillna(0)
    m = m.reset_index().sort_values('sezione')
    # righe per sezione (solo famiglie: tabella piccola)
    ispre = eid in PRE
    rows = []
    for x in ([] if ispre else m.itertuples(index=False)):
        d = x._asdict()
        rows.append([int(d['sezione']), None if pd.isna(d['territorio']) else int(d['territorio']),
                     None if pd.isna(d['elettori']) else int(d['elettori']),
                     None if pd.isna(d['votanti']) else int(d['votanti'])] + [int(d[f]) for f in fams])
    if not ispre:
        json.dump({'id': eid, 'fam': fams, 'righe': rows}, open(os.path.join(docs, 'data', 'e', eid + '.json'), 'w'), separators=(',', ':'))

    # ---- quartieri (NIL): solo dal 2016 e solo se l'abbinamento sezione -> NIL copre almeno il 95% delle sezioni e dei votanti
    nilmeta = None
    if not ispre and r.anno >= ANNO_NIL and m.votanti.sum() > 0:
        okmask = m.sezione.isin(WNIL.sezione)
        rs, rv = okmask.mean(), m.loc[okmask, 'votanti'].sum() / m.votanti.sum()
        NILMATCH.append(dict(elezione_id=eid, gruppo=r.gruppo, data=r.data, sezioni=len(m), abbinate=int(okmask.sum()), pct_sezioni=round(100 * rs, 2),
                             votanti=int(m.votanti.sum()), votanti_abbinati=int(m.loc[okmask, 'votanti'].sum()), pct_votanti=round(100 * rv, 2),
                             pubblicata='si' if (rs >= SOGLIA_NIL and rv >= SOGLIA_NIL) else 'no'))
        if rs >= SOGLIA_NIL and rv >= SOGLIA_NIL:
            num = ['elettori', 'votanti'] + pcols
            mm = m[['sezione'] + num].copy()
            mm[num] = mm[num].astype(float).fillna(0)
            j = mm.merge(WNIL[['sezione', 'id_nil', 'peso', 'prevalente']], on='sezione', how='inner')

            def pack(g_sum, ns):
                out = {}
                for n, row in g_sum.iterrows():
                    out[str(int(n))] = dict(e=int(round(row.elettori)), vt=int(round(row.votanti)), ns=ns[n], v=[int(round(row[c])) for c in pcols])
                return out
            # proporzionale: voti * peso
            jp = j.copy()
            jp[num] = jp[num].multiply(jp['peso'], axis=0)
            sp = jp.groupby('id_nil')[num].sum()
            nsp = jp.groupby('id_nil').size().to_dict()
            # prevalente: tutta la sezione al NIL col peso maggiore
            jm = j[j.prevalente == 'si']
            sm = jm.groupby('id_nil')[num].sum()
            nsm = jm.groupby('id_nil').size().to_dict()
            na = mm[~okmask.values]
            # differenza tra le due varianti: NIL (presenti in entrambe) in cui cambia la famiglia in testa
            def lead_f(row, cols):
                fv = {}
                for c, (nm, fi) in zip(pcols, par):
                    fv[fi] = fv.get(fi, 0) + row[c]
                return max(fv, key=fv.get) if sum(fv.values()) > 0 else None
            cambia = sum(1 for n in sm.index if n in sp.index and lead_f(sp.loc[n], pcols) != lead_f(sm.loc[n], pcols))
            tot_p = float(sp['votanti'].sum())
            json.dump({'id': eid, 'na': dict(s=int((~okmask).sum()), e=int(na.elettori.sum()), vt=int(na.votanti.sum())),
                       'p': pack(sp, nsp), 'm': pack(sm, nsm)},
                      open(os.path.join(docs, 'data', 'nil', eid + '.json'), 'w'), separators=(',', ':'))
            nilmeta = dict(ps=round(100 * rs, 1), pv=round(100 * rv, 1), cambia=int(cambia), nn=int(len(sm)))
            NILMATCH[-1].update(nil_con_dati_prop=int(len(sp)), nil_con_dati_prev=int(len(sm)), nil_leader_diverso_tra_varianti=int(cambia))
        else:
            nilmeta = None

    def aggreg(g):
        e = g.elettori.sum(min_count=1)
        vt = g.votanti.sum(min_count=1)
        return dict(v=[int(g[c].sum()) for c in pcols], fv=[int(g[f].sum()) for f in fams],
                    e=None if pd.isna(e) else int(e), vt=None if pd.isna(vt) else int(vt),
                    ns=int(g.sezione.nunique()))
    city = aggreg(m)
    terr = {}
    for t, g in ([] if ispre else m.groupby('territorio')):
        terr[str(int(t))] = aggreg(g)
        a = terr[str(int(t))]
        agg_rows.append(dict(elezione_id=eid, territorio=int(t), sistema=r.sistema_territorio, n_sezioni=a['ns'], elettori=a['e'], votanti=a['vt'],
                             **{f: v for f, v in zip(fams, a['fv'])}))
    if not ispre: agg_rows.append(dict(elezione_id=eid, territorio=0, sistema='citta', n_sezioni=city['ns'], elettori=city['e'], votanti=city['vt'],
                         **{f: v for f, v in zip(fams, city['fv'])}))
    for a in [city] + list(terr.values()):
        del a['fv']
    note = []
    fn = []
    if ispre:
        city['ns'] = None
        if r.gruppo == 'senato':
            fn.append('Senato fino al 1979: Eligendo divide Milano in 6 collegi (qui sommati) e conta solo gli elettori di 25 anni e più, quindi elettori e votanti sono meno di quelli della Camera e non si confrontano con le elezioni dopo il 1979.')
        if PRE[eid]['liste'] & {'FR.DEMOCR.POPOLARE', 'SOCIALCOMUNISTI', 'PCI-PSIUP'}:
            note.append('lista comune PCI-PSI (o PCI-PSIUP): non scomponibile')
        if r.gruppo == 'camera' and r.data == '1953-06-07':
            note.append('schede bianche non disponibili')
        if eid.startswith('referendum_1974') or eid.startswith('referendum_1978'):
            note.append('Sì = abrogare la legge')
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
    if ispre:
        elez_out.append(dict(id=eid, tipo=r.gruppo, data=r.data, anno=int(r.anno), label=PRE[eid]['label'], sistema=None, pre=True,
                             ds=[], fam=fams, par=par, city=city, terr=terr, note=note, fn=fn))
        continue
    elez_out.append(dict(id=eid, tipo=r.gruppo, data=r.data, anno=int(r.anno), label=label(r), sistema=r.sistema_territorio,
                         ds=[int(r.ds_risultati)] + ([int(r.ds_voti)] if r.ds_voti == r.ds_voti and r.ds_voti != '' else []),
                         fam=fams, par=par, city=city, terr=terr, note=note))
    if nilmeta:
        elez_out[-1]['nil'] = nilmeta

idx = dict(
    generato='2026-10-29',
    famiglie=[dict(nome=f, colore=COLORI[f]) for f in ORDER + ['Sì', 'No']],
    tipi=[dict(id=k, label=v) for k, v in TIPI.items()],
    sistemi=SIST,
    elezioni=elez_out)
json.dump(idx, open(os.path.join(docs, 'data', 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pd.DataFrame(agg_rows).to_csv(os.path.join(pul, 'aggregati_territorio.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(NILMATCH).to_csv(os.path.join(pul, 'nil_match.csv'), index=False, encoding='utf-8-sig')
pd.Series(unmapped).sort_values(ascending=False).to_csv(os.path.join(pul, 'liste_non_mappate.csv'), header=['righe'], encoding='utf-8-sig')
print('elezioni', len(elez_out), 'non mappate', len(unmapped))
tot = sum(os.path.getsize(os.path.join(docs, 'data', 'e', f)) for f in os.listdir(os.path.join(docs, 'data', 'e')))
print('size e/', tot, 'index', os.path.getsize(os.path.join(docs, 'data', 'index.json')))
