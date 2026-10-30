r"""Analisi di prima occhiata (nessun grafico): crescita reale delle quotazioni per zona e confronto M4.
Entrata (in <pulito>): prezzi_zona_semestre_prevalente.csv, omi_milano_zone.csv, zone_serie.csv, fermate_metro.csv; perimetri in raw\geopoi.
Uscite (in <pulito>): crescita_zone_2006_2013.csv, crescita_zone_2014_2026.csv, m4_confronto.csv, link_vs_geometria.txt; stampa un riassunto.
Quotazione di riferimento: Abitazioni civili (cod 20), stato prevalente, centro = (min+max)/2, euro 2025 (FOI senza tabacchi).
Uso: python -I 09_crescita_e_m4.py <cartella prezzi-case>
"""
import sys, os, importlib.util
import numpy as np
import pandas as pd
from shapely.geometry import Point

base = sys.argv[1]
P = os.path.join(base, 'pulito')
spec = importlib.util.spec_from_file_location('z05', os.path.join(base, 'scripts', '05_zone_corrispondenza.py'))
z05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(z05)

v = pd.read_csv(os.path.join(P, 'prezzi_zona_semestre_prevalente.csv'), dtype={'zona': str, 'link_zona': str})
zz = pd.read_csv(os.path.join(P, 'omi_milano_zone.csv'), dtype=str)
r = v[v.cod_tip == 20].copy()
nome = {(a, b): c for a, b, c in zip(zz.semestre, zz.zona, zz.zona_descr)}


def tabella(sem_a, sem_b, chiave):
    a = r[r.semestre == sem_a].dropna(subset=[chiave]).drop_duplicates(chiave).assign(k=lambda d: d[chiave]).set_index('k')
    b = r[r.semestre == sem_b].dropna(subset=[chiave]).drop_duplicates(chiave).assign(k=lambda d: d[chiave]).set_index('k')
    g = pd.DataFrame({
        'zona_inizio': a.zona, 'zona_fine': b.zona, 'fascia_fine': b.fascia,
        'nome_fine': pd.Series([nome.get((sem_b, z), '') for z in b.zona], index=b.index),
        'nominale_inizio': a.compr_centro, 'nominale_fine': b.compr_centro,
        'reale2025_inizio': a.compr_centro_reale_2025, 'reale2025_fine': b.compr_centro_reale_2025,
        'affitto_reale_inizio': a.loc_centro_reale_2025, 'affitto_reale_fine': b.loc_centro_reale_2025}).dropna(subset=['reale2025_inizio', 'reale2025_fine'])
    g['var_nominale'] = g.nominale_fine / g.nominale_inizio - 1
    g['var_reale'] = g.reale2025_fine / g.reale2025_inizio - 1
    g['var_affitto_reale'] = g.affitto_reale_fine / g.affitto_reale_inizio - 1
    return g.sort_values('var_reale')


g1 = tabella('2006-S1', '2013-S2', 'zona')
g1.round(4).to_csv(os.path.join(P, 'crescita_zone_2006_2013.csv'))
g2 = tabella('2014-S2', '2026-S1', 'id_serie')
g2.round(4).to_csv(os.path.join(P, 'crescita_zone_2014_2026.csv'))
c = r.groupby('semestre').compr_centro_reale_2025.median()
print('Mediana NON pesata fra le zone, abitazioni civili, euro 2025: 2006-S1 %.0f, 2013-S2 %.0f, 2014-S2 %.0f, 2021-S2 %.0f, 2026-S1 %.0f' % (
    c['2006-S1'], c['2013-S2'], c['2014-S2'], c['2021-S2'], c['2026-S1']))
print('\n2006-S1 -> 2013-S2 (55 zone, codici uguali): n=%d, reale mediana %.1f%%' % (len(g1), 100 * g1.var_reale.median()))
print(g1[['zona_inizio', 'fascia_fine', 'nome_fine', 'var_reale']].round(3).head(4).to_string())
print(g1[['zona_inizio', 'fascia_fine', 'nome_fine', 'var_reale']].round(3).tail(4).to_string())
print('\n2014-S2 -> 2026-S1 (zone 1:1, id_serie): n=%d, reale mediana %.1f%%' % (len(g2), 100 * g2.var_reale.median()))
print(g2[['zona_fine', 'fascia_fine', 'nome_fine', 'var_nominale', 'var_reale', 'var_affitto_reale']].round(3).to_string())

# ---- LinkZona contro geometria
rr = r.dropna(subset=['id_serie'])
y = rr.groupby('id_serie').link_zona.nunique()
zl = rr.groupby('link_zona').id_serie.nunique()
txt = ['LinkZona (identificativo della zona nel servizio) contro corrispondenza geometrica (id_serie), abitazioni civili:',
       f'- LinkZona distinti: {r.link_zona.nunique()}; presenti in tutti i {r.semestre.nunique()} semestri: {int((r.groupby("link_zona").semestre.nunique() == r.semestre.nunique()).sum())}',
       f"- id_serie con piu' di un LinkZona: {int((y > 1).sum())} su {len(y)}",
       f"- LinkZona con piu' di un id_serie: {int((zl > 1).sum())} su {len(zl)}"]
open(os.path.join(P, 'link_vs_geometria.txt'), 'w', encoding='utf-8').write('\n'.join(txt) + '\n')
print('\n' + '\n'.join(txt))

# ---- M4: fermate dentro le zone del 2026-S1
zs = z05.carica(os.path.join(base, 'raw', 'geopoi', 'F205_20261.json'))
fm = pd.read_csv(os.path.join(P, 'fermate_metro.csv'))
fm['data_apertura'] = pd.to_datetime(fm.data_apertura)
pts = [z05.TR.transform(lo, la) for lo, la in zip(fm.lon, fm.lat)]
fm['zona26'] = [next((k for k, g in zs.items() if g.contains(Point(x, y_))), None) for x, y_ in pts]
fm = fm.dropna(subset=['zona26'])
vecchie = fm[(fm.linea != 'M4') & (fm.data_apertura < '2022-01-01')]
m4 = fm[(fm.linea == 'M4') & (fm.data_apertura >= '2022-01-01')]
zone_m4 = set(m4.zona26)
zone_vecchia = set(vecchie.zona26) - zone_m4
t = []
for sem_a, sem_b, et in (('2016-S2', '2021-S2', '1 prima (2016/2-2021/2)'), ('2021-S2', '2026-S1', '2 dopo (2021/2-2026/1)')):
    # le zone si confrontano per id_serie (stessa zona nei due semestri)
    sa = r[r.semestre == sem_a].dropna(subset=['id_serie']).drop_duplicates('id_serie').set_index('id_serie')
    sb = r[r.semestre == sem_b].dropna(subset=['id_serie']).drop_duplicates('id_serie').set_index('id_serie')
    comune = sa.index.intersection(sb.index)
    d = pd.DataFrame({'zona': sb.loc[comune].zona, 'fascia': sb.loc[comune].fascia,
                      'var_reale': sb.loc[comune].compr_centro_reale_2025 / sa.loc[comune].compr_centro_reale_2025 - 1,
                      'var_affitto': sb.loc[comune].loc_centro_reale_2025 / sa.loc[comune].loc_centro_reale_2025 - 1})
    d['gruppo'] = np.where(d.zona.isin(zone_m4), 'A con stazione M4 (aperta dal 11/2022)',
                           np.where(d.zona.isin(zone_vecchia), 'B senza M4, con altra metro aperta prima del 2022', 'C senza metro'))
    d['periodo'] = et
    t.append(d.reset_index())
T = pd.concat(t)
T['fascia_gr'] = T.fascia.replace({'Centrale': 'centro+semicentro', 'Semicentrale': 'centro+semicentro', 'Periferica': 'periferia+suburbana', 'Suburbana': 'periferia+suburbana'})
T.round(4).to_csv(os.path.join(P, 'm4_confronto.csv'), index=False)
print('\nZone 2026-S1 con stazioni M4:', sorted(zone_m4))
s = T.groupby(['periodo', 'fascia_gr', 'gruppo']).agg(n=('zona', 'count'), var_reale_mediana=('var_reale', 'median'),
                                                      var_affitto_mediana=('var_affitto', 'median')).round(3)
print(s.to_string())
s2 = T.groupby(['periodo', 'gruppo']).agg(n=('zona', 'count'), var_reale_mediana=('var_reale', 'median'), var_affitto_mediana=('var_affitto', 'median')).round(3)
print(s2.to_string())
print('\nZone con M4, una per una:')
print(T[T.gruppo.str.startswith('A')][['periodo', 'zona', 'fascia', 'var_reale', 'var_affitto']].round(3).sort_values(['periodo', 'zona']).to_string())
print('\nStazioni M4 -> zona 2026-S1:')
print(m4[['fermata', 'data_apertura', 'zona26']].to_string())
