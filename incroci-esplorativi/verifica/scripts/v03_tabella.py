"""Tabella NIL propria: SMR ricalcolati, affluenza dalle sezioni, elettori AIRE, età degli italiani."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 200)

# ---- ds27 aggregato
pk = os.path.join(OUT, '_ds27.pkl')
d = pd.read_pickle(pk)
d['Eta'] = pd.to_numeric(d.Eta.astype(str).str.extract(r'(\d+)')[0])
d['ita'] = d.Cittadinanza.astype(str).str.strip().str.lower().eq('italia')
print('valori italia:', d[d.ita].Cittadinanza.unique())
print('eta max', d.Eta.max(), 'tot 2024', d[d.Anno == 2024].Residenti.sum())
def cl(e):
    if e == 0: return 0
    if e < 5: return 1
    return min(21, e // 5 + 1)
d['cl_eta'] = d.Eta.map(cl)
d['sesso'] = d.Genere.astype(str).str[0]
a = d.groupby(['Anno', 'IdNil', 'cl_eta', 'sesso', 'ita'], as_index=False).Residenti.sum()
a = a.rename(columns={'Anno': 'anno', 'IdNil': 'id_nil', 'Residenti': 'res'})
a.to_csv(os.path.join(OUT, 'ds27_cl.csv'), index=False)
e1 = d.groupby(['Anno', 'IdNil', 'Eta', 'ita'], as_index=False).Residenti.sum().rename(columns={'Anno': 'anno', 'IdNil': 'id_nil', 'Residenti': 'res', 'Eta': 'eta'})
e1.to_csv(os.path.join(OUT, 'ds27_eta_ita.csv'), index=False)

# ---- controllo sulle classi: confronto con residenti_nil_anno_cl_genere
rp = pd.read_csv(p('speranza-vita', 'pulito', 'residenti_nil_anno_cl_genere.csv'))
chk = a.groupby(['anno', 'id_nil', 'cl_eta', 'sesso']).res.sum().reset_index().merge(rp, on=['anno', 'id_nil', 'cl_eta', 'sesso'], how='outer')
print('classi: scarto assoluto totale', (chk.res.fillna(0) - chk.residenti.fillna(0)).abs().sum())

# ---- SMR propri
dec = pd.read_csv(p('speranza-vita', 'pulito', 'decessi_nil_anno_genere.csv'))
ist = pd.read_csv(p('speranza-vita', 'pulito', 'decessi_citta_anno_cl_sesso.csv'))
def py(an, ita=None):
    x = a if ita is None else a[a.ita == ita]
    x = x.groupby(['anno', 'id_nil', 'cl_eta', 'sesso']).res.sum().reset_index()
    c = x[x.anno == an].set_index(['id_nil', 'cl_eta', 'sesso']).res
    if an == 2012:
        return c
    pr = x[x.anno == an - 1].set_index(['id_nil', 'cl_eta', 'sesso']).res
    return c.add(pr, fill_value=0) / 2

FIN = {'2012-2015': range(2012, 2016), '2016-2019': range(2016, 2020), '2012-2019': range(2012, 2020), '2020': [2020], '2021': [2021], '2022-2024': range(2022, 2025)}
rows = []
for wn, ys in FIN.items():
    for sub, ita, col in [('T', None, 'decessi'), ('ITA', True, 'di_cui_italiani')]:
        Et = {}
        Ot = {}
        for y in ys:
            P = py(y)                  # città: tasso su tutti
            city = P.groupby(['cl_eta', 'sesso']).sum()
            D = ist[ist.anno == y].set_index(['cl_eta', 'sesso']).decessi
            rate = (D / city).fillna(0)
            Pu = P if ita is None else py(y, ita)
            for (i, c, s), v in Pu.items():
                Et[(i, s)] = Et.get((i, s), 0) + v * rate.get((c, s), 0)
            for r in dec[dec.anno == y].itertuples():
                Ot[(r.id_nil, r.sesso)] = Ot.get((r.id_nil, r.sesso), 0) + getattr(r, col)
        for s in ['M', 'F']:
            E = sum(v for k, v in Et.items() if k[1] == s); O = sum(v for k, v in Ot.items() if k[1] == s)
            f = O / E
            for k in list(Et):
                if k[1] == s:
                    Et[k] *= f
        ids = sorted({k[0] for k in Et})
        for i in ids:
            for s in ['M', 'F', 'T']:
                if s == 'T':
                    O = Ot.get((i, 'M'), 0) + Ot.get((i, 'F'), 0); E = Et.get((i, 'M'), 0) + Et.get((i, 'F'), 0)
                else:
                    O = Ot.get((i, s), 0); E = Et.get((i, s), 0)
                rows.append(dict(finestra=wn, pop=sub, sesso=s, id_nil=i, O=O, E=E, smr=O / E if E > 0 else np.nan))
smr = pd.DataFrame(rows)
smr.to_csv(os.path.join(OUT, 'smr_propri.csv'), index=False)
pub = pd.read_csv(p('speranza-vita', 'pulito', 'nil_smr_e0.csv'))
print('sessi nel file pubblicato', pub.sesso.unique(), pub.finestra.unique())
for wn in FIN:
    m = smr[(smr.finestra == wn) & (smr['pop'] == 'T') & (smr.sesso == 'T')].merge(pub[(pub.finestra == wn) & (pub.sesso == 'T')][['id_nil', 'smr', 'osservati', 'attesi']], on='id_nil', suffixes=('', '_pub'))
    big = m[m.E > 100]
    if len(big):
        print(wn, 'n', len(big), 'corr', round(big.smr.corr(big.smr_pub), 4), 'scarto medio', round((big.smr - big.smr_pub).abs().mean(), 4), 'max', round((big.smr - big.smr_pub).abs().max(), 4))

# ---- sezioni -> NIL
sn = pd.read_csv(p('elezioni', 'pulito', 'sezione_nil.csv'))
print('pesi: somma per sezione min/max', sn.groupby('sezione').peso.sum().min(), sn.groupby('sezione').peso.sum().max())
rs = pd.read_csv(p('elezioni', 'pulito', 'risultati_sezione.csv'), low_memory=False)
idx = indice()
ids = [x['id'] for x in idx['elezioni'] if x['anno'] >= 2016 and os.path.exists(p('docs', 'elezioni', 'data', 'nil', x['id'] + '.json'))]
print(len(ids), [i for i in ids][:40])
print('elezione_id nel csv esempi', [i for i in rs.elezione_id.unique() if '2022' in str(i)][:12])
rows = []
map_id = {}
for eid in ids:
    # il csv può avere id diversi per i referendum
    if eid in set(rs.elezione_id):
        map_id[eid] = eid
print('non trovate nel csv:', [i for i in ids if i not in map_id])
out = []
for eid, cid in map_id.items():
    x = rs[rs.elezione_id == cid].copy()
    x['regolare'] = (x.elettori > 0) & (x.votanti <= x.elettori) & (x.votanti > 0)
    y = x.merge(sn[['sezione', 'id_nil', 'peso', 'prevalente']], on='sezione', how='inner')
    y['e_w'] = y.elettori.fillna(0) * y.peso; y['v_w'] = y.votanti.fillna(0) * y.peso
    g_all = y.groupby('id_nil')[['e_w', 'v_w']].sum()
    g_reg = y[y.regolare].groupby('id_nil')[['e_w', 'v_w']].sum()
    pr = y[y.prevalente == 'si']; g_pr = pr[pr.regolare].groupby('id_nil')[['elettori', 'votanti']].sum()
    t = pd.DataFrame({'e_all': g_all.e_w, 'v_all': g_all.v_w, 'e_reg': g_reg.e_w, 'v_reg': g_reg.v_w, 'e_prev': g_pr.elettori, 'v_prev': g_pr.votanti}).reset_index()
    t['eid'] = eid
    t['n_irreg'] = (~x.regolare).sum()
    out.append(t)
se = pd.concat(out)
se['aff_reg'] = se.v_reg / se.e_reg * 100
se['aff_prev'] = se.v_prev / se.e_prev * 100
se.to_csv(os.path.join(OUT, 'nil_affluenza_sezioni.csv'), index=False)
# confronto col JSON
for eid in ['camera_2022-09-25', 'comunali_consiglio_2021-10-03', 'europee_2024-06-08']:
    j = elezione(eid)
    m = j.merge(se[se.eid == eid], on='id_nil')
    print(eid, 'e JSON vs sez: scarto rel max', round(((m.e - m.e_all) / m.e_all.clip(lower=1)).abs().max(), 4), 'vt', round(((m.vt - m.v_all) / m.v_all.clip(lower=1)).abs().max(), 4),
          ' aff JSON-regolare: max', round((m.aff - m.aff_reg)[m.e > 2000].abs().max(), 2), 'irreg', m.n_irreg.iloc[0])
print(se.groupby('eid').n_irreg.first())
