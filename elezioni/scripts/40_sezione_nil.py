"""Sezione -> NIL (quartiere) dal solo collegamento ufficiale che esiste: ds939 (stradario del referendum 2020, per civico).
Scrive:
  pulito/sezione_nil.csv        una riga per (sezione, NIL): n_civici, peso (quota dei civici della sezione in quel NIL), prevalente (si/no)
  pulito/nil_info.csv           una riga per NIL: nome, municipio, sezioni, civici, quota di civici in sezioni condivise
  pulito/sezione_nil_stabilita.csv  controllo: per ogni stradario 2016-2026, quanti civici hanno la stessa sezione che nel 2020
uso: python -I 40_sezione_nil.py <cartella elezioni>
"""
import sys, os, glob, json
import pandas as pd

base = sys.argv[1]
raw = os.path.join(base, 'raw')
pul = os.path.join(base, 'pulito')


def leggi(path):
    for enc in ('utf-8-sig', 'cp1252'):
        try:
            return pd.read_csv(path, sep=None, engine='python', encoding=enc, dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(path)


def chiave(df, via, civ, bar):
    b = df[bar].str.strip().str.upper().replace({'0': ''})
    return df[via].str.strip() + '|' + df[civ].str.strip() + '|' + b


d = leggi(glob.glob(os.path.join(raw, 'ds939-*', '*.csv'))[0])
d['chiave'] = chiave(d, 'CODICE_VIA', 'CIVICO', 'BARRATO')
d['sez'] = d.SEZIONE.astype(int)
print('ds939 righe', len(d), 'sezioni', d.sez.nunique(), 'senza NIL', (d.ID_NIL == '').sum())
senza = d[d.ID_NIL == '']
for r in senza.itertuples():
    print('  civico senza NIL (escluso dai pesi): sezione', r.sez, r.DESCRIZIONE_VIA, r.CIVICO)
dn = d[d.ID_NIL != ''].copy()
dn['nil'] = dn.ID_NIL.astype(int)

# ---- pesi: quota dei civici della sezione in ciascun NIL
w = dn.groupby(['sez', 'nil']).size().rename('n_civici').reset_index()
w['peso'] = w.n_civici / w.groupby('sez').n_civici.transform('sum')
# NIL prevalente: peso massimo; a parita' piu' civici (stessi) -> NIL con id piu' basso (nessuna parita' esatta tra 3+ NIL e' attesa)
w = w.sort_values(['sez', 'peso', 'nil'], ascending=[True, False, True]).reset_index(drop=True)
w['prevalente'] = (~w.duplicated('sez')).map({True: 'si', False: 'no'})
nomi = dn.drop_duplicates('nil').set_index('nil').NIL.to_dict()
mun = dn.groupby('nil').MUNICIPIO.agg(lambda s: s.value_counts().index[0]).to_dict()
w['nil_nome'] = w.nil.map(nomi)
ties = w.groupby('sez').peso.apply(lambda s: (s == s.max()).sum())
print('sezioni con parita\' esatta del peso massimo:', int((ties > 1).sum()))
w['peso'] = w.peso.round(5)
w[['sez', 'nil', 'nil_nome', 'n_civici', 'peso', 'prevalente']].rename(columns={'sez': 'sezione', 'nil': 'id_nil'}).to_csv(
    os.path.join(pul, 'sezione_nil.csv'), index=False, encoding='utf-8-sig')
split = w.groupby('sez').size()
print('sezioni', len(split), 'su un solo NIL', int((split == 1).sum()), 'su 2', int((split == 2).sum()), 'su 3+', int((split >= 3).sum()))
pm = w[w.prevalente == 'si'].peso
print('peso del NIL prevalente nelle sezioni divise: mediana %.2f, minimo %.2f' % (w[(w.prevalente == 'si') & w.sez.isin(split[split > 1].index)].peso.median(),
                                                                                   w[(w.prevalente == 'si') & w.sez.isin(split[split > 1].index)].peso.min()))

# ---- info per NIL
w['split'] = w.sez.map(split) > 1
inf = w.groupby('nil').agg(sezioni=('sez', 'nunique'), civici=('n_civici', 'sum'), sezioni_eff=('peso', 'sum'),
                           civici_in_condivise=('n_civici', lambda s: s[w.loc[s.index, 'split']].sum()),
                           sezioni_prevalenti=('prevalente', lambda s: (s == 'si').sum())).reset_index()
inf['quota_civici_condivisi'] = (inf.civici_in_condivise / inf.civici).round(3)
inf['sezioni_eff'] = inf.sezioni_eff.round(2)
inf['nome'] = inf.nil.map(nomi)
inf['municipio'] = inf.nil.map(mun)
inf = inf[['nil', 'nome', 'municipio', 'sezioni', 'sezioni_eff', 'sezioni_prevalenti', 'civici', 'civici_in_condivise', 'quota_civici_condivisi']]
inf.to_csv(os.path.join(pul, 'nil_info.csv'), index=False, encoding='utf-8-sig')
print(inf.sort_values('sezioni_eff').head(8).to_string())

# ---- controllo di stabilita': gli altri stradari 2016-2026 (stessa chiave via+civico+barrato) danno la stessa sezione del 2020?
base_sez = d.drop_duplicates('chiave').set_index('chiave').sez
PRIMA = [('ds1096', '2001-05-13'), ('ds1098', '2004-06-12'), ('ds1100', '2005-04-03'), ('ds1102', '2006-04-09'), ('ds1104', '2006-05-28'),
         ('ds1106', '2008-04-13'), ('ds1108', '2009-06-06'), ('ds1110', '2010-03-28'), ('ds1112', '2011-05-15'), ('ds1114', '2013-02-24'),
         ('ds1116', '2014-05-25')]
STR = [(a, b, 'Sezione', 'CodVia', 'Civico', 'Barrato') for a, b in PRIMA] + [('ds348', '2016-12-04 (ref. 2016)', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'),
       ('ds1352', '2016-04-17', 'Sezione', 'CodVia', 'Civico', 'Barrato'), ('ds1118', '2016-06-05', 'Sezione', 'CodVia', 'Civico', 'Barrato'),
       ('ds1353', '2016-12-04', 'Sezione', 'CodVia', 'Civico', 'Barrato'), ('ds1354', '2017-10-22', 'Sezione', 'CodVia', 'Civico', 'Barrato'),
       ('ds1120', '2018-03-04', 'Sezione', 'CodVia', 'Civico', 'Barrato'), ('ds1122', '2019-05-26', 'Sezione', 'CodVia', 'Civico', 'Barrato'),
       ('ds1614', '2021-10-03', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'), ('ds1862', '2022-06-12', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'),
       ('ds1979', '2022-09-25', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'), ('ds2169', '2023-02-12', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'),
       ('ds2741', '2024-06-08', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'), ('ds2922', '2025-06-08', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO'),
       ('ds2973', '2026-03-22', 'SEZIONE', 'CODICE_VIA', 'CIVICO', 'BARRATO')]
out = []
for ds, data, cs, cv, cc, cb in STR:
    fs = [f for f in glob.glob(os.path.join(raw, ds + '[-_]*', '**', '*.csv'), recursive=True)]
    if not fs:
        continue
    x = leggi(fs[0])
    x = x[x[cs].str.strip() != '']
    x['chiave'] = chiave(x, cv, cc, cb)
    x['sez'] = x[cs].astype(int)
    x = x.drop_duplicates('chiave')
    m = x[x.chiave.isin(base_sez.index)]
    stessa = (m.sez.values == base_sez.reindex(m.chiave).values)
    # quota di civici del 2020 ritrovati nello stradario dell'anno
    out.append(dict(stradario=ds, data=data, civici=len(x), trovati_nel_2020=len(m), pct_trovati=round(100 * len(m) / len(x), 2),
                    stessa_sezione_pct=round(100 * stessa.mean(), 2), civici_2020_ritrovati_pct=round(100 * len(m) / len(base_sez), 2),
                    sezioni_anno=x.sez.nunique(), sezioni_anno_non_nel_2020=len(set(x.sez) - set(d.sez))))
st = pd.DataFrame(out)
st.to_csv(os.path.join(pul, 'sezione_nil_stabilita.csv'), index=False, encoding='utf-8-sig')
print(st.to_string())
