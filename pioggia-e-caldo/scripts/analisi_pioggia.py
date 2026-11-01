"""Fase 1 - pioggia: riepiloghi per sensore e anno, tendenze, eventi massimi, serie lunghe giornaliere.
uso: python -I -X utf8 analisi_pioggia.py <pioggia-e-caldo assoluta> <milano-in-dati assoluta>
Entrata: pulito/intermedi/P_orario.parquet, P_10min.parquet, sensori_selezionati.csv,
         raw/ecad_rr/blend_rr/RR_STAID000173.txt, neve-e-nebbia/pulito/giorni_neve_nebbia.csv (GSOD Linate).
Uscita: pulito/pioggia_anno_sensore.csv, pioggia_tendenze.csv, pioggia_eventi_top_ore.csv, pioggia_eventi_top_giorni.csv,
        pioggia_lungo_periodo.csv, pioggia_lungo_tendenze.csv, pioggia_copertura_matrice.csv"""
import sys, os
import numpy as np, pandas as pd
base, root = sys.argv[1], sys.argv[2]
pu = os.path.join(base, 'pulito')
rng = np.random.default_rng(12345)
sel = pd.read_csv(os.path.join(pu, 'sensori_selezionati.csv'), dtype=str)
nome = dict(zip(sel.idsensore, sel.nomestazione))
P = pd.read_parquet(os.path.join(pu, 'intermedi', 'P_orario.parquet'))
# l'ora t (es. 00:00) e' la somma di 23:10-00:00: il giorno solare e' quello di (t - 10 minuti)
P['giorno'] = (P.ora - pd.Timedelta(minutes=10)).dt.floor('D')
P['anno_g'] = P.giorno.dt.year
ORE_ANNO = 8760.0

# --- serie di riferimento giornaliere indipendenti: ECA&D Milano (1858-2008) e GSOD Linate (flag con 24 ore coperte) ---
eca = pd.read_csv(os.path.join(base, 'raw/ecad_rr/blend_rr/RR_STAID000173.txt'), skiprows=20, skipinitialspace=True)
eca.columns = [c.strip() for c in eca.columns]
eca['data'] = pd.to_datetime(eca.DATE.astype(str), format='%Y%m%d')
eca = eca[(eca.RR != -9999) & (eca.Q_RR == 0)]
eca['mm'] = eca.RR / 10.0
# GSOD: flag A,B,C,E = periodo di 6/12 ore incompleto (somma parziale) -> scartati; D,F,G = 24 ore coperte; H,I = zero
gs = pd.read_csv(os.path.join(root, 'neve-e-nebbia/pulito/giorni_neve_nebbia.csv'), usecols=['date', 'station', 'gsod_prcp_mm', 'gsod_prcp_flag'])
gs = gs[(gs.station == 'LINATE') & gs.gsod_prcp_mm.notna() & gs.gsod_prcp_flag.isin(list('DFGHI'))].copy()
gs['data'] = pd.to_datetime(gs.date)
gs['mm'] = gs.gsod_prcp_mm
ref_ext = pd.concat([eca[['data', 'mm']].assign(f='ECA_Milano'), gs[['data', 'mm']].assign(f='GSOD_Linate')])
ref_ext_max = ref_ext.groupby('data').mm.max()

# --- validazione dei giorni: un giorno >= 40 mm e' "non confermato" se tutti i riferimenti disponibili (altri pluviometri entro 15 km dal sensore
#     con >= 20 ore valide; per i sensori entro 12 km dal Duomo anche ECA&D Milano e GSOD Linate) misurano meno di 0,40 volte il suo valore ---
dist = dict(zip(sel.idsensore, sel.dist_duomo_km.astype(float)))
Dall = P.groupby(['idsensore', 'giorno']).agg(mm=('mm', 'sum'), n=('mm', 'size')).reset_index()
Dall = Dall[Dall.n >= 20]
lat = dict(zip(sel.idsensore, sel.lat.astype(float))); lng = dict(zip(sel.idsensore, sel.lng.astype(float)))
def km(i, j):
    return float(np.hypot((lat[i] - lat[j]) * 111.2, (lng[i] - lng[j]) * 111.2 * np.cos(np.radians(45.5))))
Dn = Dall.pivot(index='giorno', columns='idsensore', values='mm')
sus = []
for _, r in Dall[Dall.mm >= 40].iterrows():
    vicini = [j for j in Dn.columns if j != r.idsensore and km(r.idsensore, j) <= 15]
    others = Dn.loc[r.giorno, vicini].dropna() if (r.giorno in Dn.index and vicini) else pd.Series(dtype=float)
    refs = list(others.values)
    if dist.get(r.idsensore, 99) < 12 and r.giorno in ref_ext_max.index:
        refs.append(ref_ext_max[r.giorno])
    stato = 'non_verificabile' if len(refs) == 0 else ('confermato' if max(refs) >= 0.40 * r.mm else 'NON_CONFERMATO')
    sus.append(dict(idsensore=r.idsensore, nomestazione=nome[r.idsensore], giorno=r.giorno, mm_giorno=round(r.mm, 1), n_riferimenti=len(refs),
                    max_riferimenti=round(max(refs), 1) if refs else np.nan, stato=stato))
sus = pd.DataFrame(sus)
sus.to_csv(os.path.join(pu, 'pioggia_giorni_ge40mm_verifica.csv'), index=False)
bad = set(zip(sus[sus.stato == 'NON_CONFERMATO'].idsensore, sus[sus.stato == 'NON_CONFERMATO'].giorno))
P['sospetto'] = [(a, b) in bad for a, b in zip(P.idsensore, P.giorno)]
Pgrezzo = P
P = P[~P.sospetto].copy()   # i giorni NON confermati sono tolti dalle statistiche "validate" (restano nella grezza)
graw = Pgrezzo.groupby(['idsensore', 'anno_g']).mm.max().rename('max_oraria_mm_grezza').reset_index().rename(columns={'anno_g': 'anno'})


def anno_stats(g):
    n = len(g)
    tot = g.mm.sum()
    d = g.groupby('giorno').agg(mm=('mm', 'sum'), n=('mm', 'size'))
    k = max(1, int(np.ceil(0.01 * n)))
    top = np.sort(g.mm.values)[::-1][:k].sum()
    wet = g[g.mm > 0].mm.values
    kw = max(1, int(np.ceil(0.01 * len(wet)))) if len(wet) else 1
    topw = np.sort(wet)[::-1][:kw].sum() if len(wet) else 0
    return pd.Series(dict(
        ore_valide=n, copertura=round(n / ORE_ANNO, 3), tot_mm=round(tot, 1),
        giorni_validi_ge20h=int((d.n >= 20).sum()), giorni_piovosi_1mm=int((d.mm >= 1.0).sum()),
        giorni_piovosi_02mm=int((d.mm >= 0.2).sum()), giorni_ge30mm=int((d.mm >= 30).sum()), giorni_ge50mm=int((d.mm >= 50).sum()),
        max_oraria_mm=round(g.mm.max(), 1), max_giornaliera_mm=round(d.mm.max(), 1),
        ore_ge10=int((g.mm >= 10).sum()), ore_ge20=int((g.mm >= 20).sum()), ore_ge30=int((g.mm >= 30).sum()),
        ore_piovose=int((g.mm > 0).sum()),
        quota_top1pct_ore=round(top / tot, 4) if tot > 0 else np.nan,
        quota_top1pct_ore_piovose=round(topw / tot, 4) if tot > 0 else np.nan))


A = P.groupby(['idsensore', 'anno_g']).apply(anno_stats, include_groups=False).reset_index().rename(columns={'anno_g': 'anno'})
A.insert(1, 'nomestazione', A.idsensore.map(nome))
P10 = pd.read_parquet(os.path.join(pu, 'intermedi', 'P_10min.parquet'))
P10 = P10[P10.ora >= '2014-01-01 00:10']   # prima del 2014 i dati sono orari: il 'massimo a 10 minuti' non esiste
P10['anno'] = (P10.ora - pd.Timedelta(minutes=10)).dt.year
m10 = P10.groupby(['idsensore', 'anno']).mm.max().rename('max_10min_mm').reset_index()
A = A.merge(m10, how='left', on=['idsensore', 'anno'])
A = A.merge(graw, how='left', on=['idsensore', 'anno'])
ns = sus[sus.stato == 'NON_CONFERMATO'].assign(anno=lambda x: pd.to_datetime(x.giorno).dt.year).groupby(['idsensore', 'anno']).size().rename('giorni_non_confermati').reset_index()
A = A.merge(ns, how='left', on=['idsensore', 'anno'])
A['giorni_non_confermati'] = A.giorni_non_confermati.fillna(0).astype(int)
A['anno_completo'] = A.copertura >= 0.90
A.to_csv(os.path.join(pu, 'pioggia_anno_sensore.csv'), index=False)

cov = A.pivot(index='idsensore', columns='anno', values='copertura')
cov.insert(0, 'nomestazione', cov.index.map(nome))
cov.to_csv(os.path.join(pu, 'pioggia_copertura_matrice.csv'))


def theil_sen(x, y):
    sl = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(x)) for j in range(i + 1, len(x)) if x[j] != x[i]]
    return float(np.median(sl))


def tend(x, y, B=2000):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    s = theil_sen(x, y)
    bs = []
    for _ in range(B):
        ix = rng.integers(0, len(x), len(x))
        if len(set(x[ix])) < 3:
            continue
        bs.append(theil_sen(x[ix], y[ix]))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return s, lo, hi


VARS = ['tot_mm', 'giorni_piovosi_1mm', 'max_oraria_mm', 'max_giornaliera_mm', 'ore_ge20', 'quota_top1pct_ore']
rows = []
Ac = A[A.anno_completo]
for sid, g in Ac.groupby('idsensore'):
    if len(g) < 10:
        continue
    for v in VARS:
        s, lo, hi = tend(g.anno.values, g[v].values)
        rows.append(dict(idsensore=sid, nomestazione=nome[sid], variabile=v, anni=len(g), da=int(g.anno.min()), a=int(g.anno.max()),
                         media=round(g[v].mean(), 3), pendenza_per_decennio=round(s * 10, 3), ic95_lo=round(lo * 10, 3),
                         ic95_hi=round(hi * 10, 3), ic_esclude_zero=bool(lo > 0 or hi < 0)))
pd.DataFrame(rows).to_csv(os.path.join(pu, 'pioggia_tendenze.csv'), index=False)

# eventi: ore massime tra i sensori entro 8,5 km dal Duomo, una per giorno
milano_ids = set(sel[(sel.tipologia == 'Precipitazione') & (sel.dist_duomo_km.astype(float) < 8.5)].idsensore)
Pm = Pgrezzo[Pgrezzo.idsensore.isin(milano_ids)].copy()
top = Pm.sort_values('mm', ascending=False).head(400)
ev = []
for _, r in top.iterrows():
    same = Pm[(Pm.ora == r.ora) & (Pm.idsensore != r.idsensore)]
    same_day = Pm[(Pm.giorno == r.giorno) & (Pm.idsensore != r.idsensore)].groupby('idsensore').mm.sum()
    day_here = Pm[(Pm.giorno == r.giorno) & (Pm.idsensore == r.idsensore)].mm.sum()
    ev.append(dict(ora=r.ora, giorno=r.giorno, idsensore=r.idsensore, nomestazione=nome[r.idsensore], mm_ora=r.mm,
                   mm_giorno_sensore=round(day_here, 1), n_altri_sensori_attivi=len(same),
                   max_altri_stessa_ora=round(same.mm.max(), 1) if len(same) else np.nan,
                   max_altri_stesso_giorno=round(same_day.max(), 1) if len(same_day) else np.nan))
ev = pd.DataFrame(ev)
ev = ev.merge(sus[['idsensore', 'giorno', 'stato']].rename(columns={'stato': 'verifica_giorno'}), how='left', on=['idsensore', 'giorno'])
ev['eca_milano_mm_giorno'] = ev.giorno.map(eca.set_index('data').mm)
ev['gsod_linate_mm_giorno'] = ev.giorno.map(gs.set_index('data').mm)
ev1 = ev[ev.verifica_giorno != 'NON_CONFERMATO'].sort_values('mm_ora', ascending=False).drop_duplicates('giorno').head(40)
ev[ev.verifica_giorno == 'NON_CONFERMATO'].sort_values('mm_ora', ascending=False).drop_duplicates(['idsensore', 'giorno']).to_csv(os.path.join(pu, 'pioggia_ore_estreme_non_confermate.csv'), index=False)
ev1.to_csv(os.path.join(pu, 'pioggia_eventi_top_ore.csv'), index=False)
D = Pm.groupby(['idsensore', 'giorno']).agg(mm=('mm', 'sum'), n=('mm', 'size')).reset_index()
D = D[D.n >= 20]
D = D.merge(sus[sus.stato == 'NON_CONFERMATO'][['idsensore', 'giorno']].assign(x=1), how='left', on=['idsensore', 'giorno'])
D = D[D.x.isna()].drop(columns='x')
D['nomestazione'] = D.idsensore.map(nome)
D['eca_milano_mm'] = D.giorno.map(eca.set_index('data').mm)
D['gsod_linate_mm'] = D.giorno.map(gs.set_index('data').mm)
D1 = D.sort_values('mm', ascending=False).drop_duplicates('giorno').head(40)
D1.to_csv(os.path.join(pu, 'pioggia_eventi_top_giorni.csv'), index=False)

# serie lunghe giornaliere
def lungo(dd, nome_serie, minimo_giorni=330):
    dd = dd.copy()
    dd['anno'] = dd.data.dt.year
    out = dd.groupby('anno').apply(lambda g: pd.Series(dict(
        giorni_validi=len(g), tot_mm=round(g.mm.sum(), 1), giorni_piovosi_1mm=int((g.mm >= 1).sum()),
        max_giornaliera_mm=g.mm.max(), giorni_ge30mm=int((g.mm >= 30).sum()), giorni_ge50mm=int((g.mm >= 50).sum()),
        giorni_ge100mm=int((g.mm >= 100).sum()))), include_groups=False).reset_index()
    out.insert(0, 'serie', nome_serie)
    out['anno_completo'] = out.giorni_validi >= minimo_giorni
    return out


L = pd.concat([lungo(eca[['data', 'mm']], 'ECAD_Milano_RR_Maugeri'), lungo(gs[['data', 'mm']], 'GSOD_Linate_PRCP')])
Dm = D[D.idsensore.isin(['5908', '9341', '2006', '8149', '14121', '19373'])].groupby('giorno').mm.mean().reset_index().rename(columns={'giorno': 'data'})
L = pd.concat([L, lungo(Dm, 'ARPA_media_sensori_Milano')])
L.to_csv(os.path.join(pu, 'pioggia_lungo_periodo.csv'), index=False)
rows = []
for (s, a0, a1) in [('ECAD_Milano_RR_Maugeri', 1858, 2008), ('ECAD_Milano_RR_Maugeri', 1951, 2008), ('GSOD_Linate_PRCP', 1951, 2025),
                    ('GSOD_Linate_PRCP', 1973, 2025), ('ARPA_media_sensori_Milano', 1990, 2025)]:
    g = L[(L.serie == s) & L.anno_completo & L.anno.between(a0, a1)]
    for v in ['tot_mm', 'giorni_piovosi_1mm', 'max_giornaliera_mm', 'giorni_ge30mm']:
        if len(g) < 10:
            continue
        sl, lo, hi = tend(g.anno.values, g[v].values, B=1000)
        rows.append(dict(serie=s, da=a0, a=a1, anni=len(g), variabile=v, media=round(g[v].mean(), 3),
                         pendenza_per_decennio=round(sl * 10, 3), ic95_lo=round(lo * 10, 3), ic95_hi=round(hi * 10, 3),
                         ic_esclude_zero=bool(lo > 0 or hi < 0)))
pd.DataFrame(rows).to_csv(os.path.join(pu, 'pioggia_lungo_tendenze.csv'), index=False)
print('FATTO pioggia')

# ---- composito dei pluviometri di Milano (entro 8,5 km dal Duomo) ---------------------------------------------------------
# per ogni sensore si prendono solo gli anni completi (copertura >= 0,90); ogni anno e' scarto dalla media del sensore, poi media tra i sensori attivi
mil = [i for i in milano_ids if i != '2065']          # Segrate Milano Due escluso (3 anni completi, ore estreme mai confermate)
Cm = A[A.idsensore.isin(mil) & A.anno_completo].copy()
VV = ['tot_mm', 'giorni_piovosi_1mm', 'max_oraria_mm', 'max_giornaliera_mm', 'ore_ge10', 'ore_ge20', 'quota_top1pct_ore', 'quota_top1pct_ore_piovose']
anom = Cm[['idsensore', 'anno'] + VV].copy()
for v in VV:
    mu = anom.groupby('idsensore')[v].transform('mean')
    anom[v] = anom[v] / mu if v in ('tot_mm', 'giorni_piovosi_1mm') else anom[v] - mu
comp = anom.groupby('anno').agg(n_sensori=('idsensore', 'size'), **{v: (v, 'mean') for v in VV}).reset_index()
comp.round(4).to_csv(os.path.join(pu, 'pioggia_composito_milano.csv'), index=False)
rows = []
for v in VV:
    g = comp[comp.n_sensori >= 2]
    sl, lo, hi = tend(g.anno.values, g[v].values, B=2000)
    rows.append(dict(variabile=v, anni=len(g), da=int(g.anno.min()), a=int(g.anno.max()), sensori=','.join(sorted(mil)),
                     pendenza_per_decennio=round(sl * 10, 4), ic95_lo=round(lo * 10, 4), ic95_hi=round(hi * 10, 4), ic_esclude_zero=bool(lo > 0 or hi < 0),
                     nota='rapporto alla media del sensore' if v in ('tot_mm', 'giorni_piovosi_1mm') else 'scarto dalla media del sensore'))
pd.DataFrame(rows).to_csv(os.path.join(pu, 'pioggia_composito_tendenze.csv'), index=False)
# per periodo (sensore-anni completi di Milano): medie
Cm['periodo'] = pd.cut(Cm.anno, [1989, 2003, 2012, 2025], labels=['1990-2003', '2004-2012', '2013-2025'])
per = Cm.groupby('periodo', observed=True).agg(sensore_anni=('idsensore', 'size'), sensori=('idsensore', 'nunique'), tot_mm=('tot_mm', 'mean'), giorni_piovosi_1mm=('giorni_piovosi_1mm', 'mean'),
        max_oraria_mm=('max_oraria_mm', 'mean'), ore_ge20=('ore_ge20', 'mean'), ore_ge30=('ore_ge30', 'mean'), giorni_ge50mm=('giorni_ge50mm', 'mean'),
        quota_top1pct_ore=('quota_top1pct_ore', 'mean')).round(3).reset_index()
per.to_csv(os.path.join(pu, 'pioggia_periodi_milano.csv'), index=False)
print(per.to_string())
print(pd.DataFrame(rows).drop(columns=['sensori']).to_string())

# ---- serie lunghe per decennio e giorni "di tutta la citta" ------------------------------------------------------------
Lc = L[L.anno_completo].copy()
Lc['decennio'] = (Lc.anno // 10) * 10
dec = Lc.groupby(['serie', 'decennio']).agg(anni=('anno', 'size'), tot_mm=('tot_mm', 'mean'), giorni_piovosi_1mm=('giorni_piovosi_1mm', 'mean'),
      giorni_ge30mm=('giorni_ge30mm', 'mean'), giorni_ge50mm=('giorni_ge50mm', 'mean'), max_giornaliera_mm=('max_giornaliera_mm', 'mean')).round(2).reset_index()
dec.to_csv(os.path.join(pu, 'pioggia_lungo_decenni.csv'), index=False)
ext = Lc[Lc.serie == 'ECAD_Milano_RR_Maugeri']
print('ECA: anno piu secco/piu piovoso', ext.loc[ext.tot_mm.idxmin(), ['anno', 'tot_mm']].tolist(), ext.loc[ext.tot_mm.idxmax(), ['anno', 'tot_mm']].tolist())
# giorni con piu' pluviometri sopra soglia (Milano entro 8,5 km, escluso Segrate): giorno "di tutta la citta"
Dv = D[D.idsensore != '2065']
cit = Dv.groupby('giorno').agg(n=('mm', 'size'), mediana=('mm', 'median'), massimo=('mm', 'max'), minimo=('mm', 'min')).reset_index()
cit = cit[cit.n >= 3].sort_values('mediana', ascending=False).head(25)
cit['eca_milano_mm'] = cit.giorno.map(eca.set_index('data').mm)
cit['gsod_linate_mm'] = cit.giorno.map(gs.set_index('data').mm)
cit.round(1).to_csv(os.path.join(pu, 'pioggia_eventi_citta_giorni.csv'), index=False)
print(cit.head(12).to_string())
print(dec[dec.serie == 'ECAD_Milano_RR_Maugeri'].to_string())
