r"""Fase 1 - crescita nel tempo: recensioni Inside Airbnb a confronto con i dati ufficiali.
Uso: python -I -X utf8 06_crescita.py <affitti-brevi (assoluta)>
Legge pulito\recensioni_*.csv, pulito\ufficiale_*.csv, pulito\nil_riepilogo.csv. Scrive:
  pulito\crescita_confronto.csv  (anno per anno: Airbnb da recensioni, ISTAT extra-alberghiero, Comune CAV+LT, imposta di soggiorno)
  pulito\crescita_nil.csv        (annunci con recensione nel 2019, 2023, 2025 per NIL)
  out\crescita.txt               (numeri citati nel NOTE.md)
"""
import sys
from pathlib import Path
import pandas as pd, numpy as np

base = Path(sys.argv[1]); P = base/'pulito'
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); log.append(s)

ra = pd.read_csv(P/'recensioni_anno.csv').set_index('anno')
us = pd.read_csv(P/'ufficiale_strutture_milano.csv')
uf = pd.read_csv(P/'ufficiale_flussi_milano.csv')

c = pd.DataFrame(index=range(2012, 2027))
c['airbnb_annunci_con_recensione_unione'] = ra['annunci_con_recensione_unione']
c['airbnb_annunci_con_recensione_ultimo'] = ra['annunci_con_recensione_ultimo']
c['airbnb_annunci_prima_recensione_unione'] = ra['annunci_prima_recensione_unione']
c['airbnb_recensioni_unione'] = ra['recensioni_unione']
c['airbnb_recensioni_ultimo'] = ra['recensioni_ultimo']
x = us[us.serie.str.startswith('esercizi ricettivi ISTAT') & (us.tipo == 'Es. Extra-Alberghieri')].copy(); x.index = x.periodo.astype(int)
c['istat_extra_alberghieri_strutture'] = x.strutture; c['istat_extra_alberghieri_letti'] = x.posti_letto
d = us[us.serie.str.startswith('strutture attive per tipologia')].copy(); d['anno'] = d.periodo.astype(int)
for cod, nome in [('VA', 'comune_case_vacanza_CAV'), ('LT', 'comune_locazioni_turistiche'), ('EA', 'comune_extra_alberghiere_classiche')]:
    y = d[d.tipo.str.startswith(cod+' ')].set_index('anno'); c[nome] = y.strutture
c['comune_CAV_piu_LT'] = c['comune_case_vacanza_CAV'].fillna(0) + c['comune_locazioni_turistiche'].fillna(0)
c.loc[c['comune_CAV_piu_LT'] == 0, 'comune_CAV_piu_LT'] = np.nan
t = us[us.serie.str.startswith('strutture accreditate imposta')].copy()
t['anno'] = t.periodo.str[:4].astype(int); t['ult'] = t.periodo.str.endswith('-12') | t.periodo.str.endswith('-T4')
c['comune_accreditate_imposta_soggiorno_fine_anno'] = t[t.ult].set_index('anno').strutture
f = uf[(uf.cittadinanza == 'Totale')].pivot(index='anno', columns='tipo_struttura', values='presenze')
c['istat_presenze_extra_alberghiere'] = f['Es. Extra-Alberghieri']; c['istat_presenze_totale'] = f['Totale'] if 'Totale' in f else f.sum(axis=1)
c['quota_presenze_extra_alberghiere'] = c.istat_presenze_extra_alberghiere/c.istat_presenze_totale
c.index.name = 'anno'; c.reset_index().to_csv(P/'crescita_confronto.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
say('== Crescita: Airbnb (recensioni) e fonti ufficiali\n', c.round(3).to_string())

# stabilita' del passato: quanto si perde da un file all'altro
s0, s1 = '2025-12-26', '2026-09-19'
say('\n== Erosione del passato (annunci con almeno una recensione nell anno, file di dicembre 2025 contro settembre 2026)')
for y in (2019, 2022, 2023, 2024, 2025):
    a0 = ra.loc[y, f'annunci_con_recensione_nel_file_{s0}']; a1 = ra.loc[y, f'annunci_con_recensione_nel_file_{s1}']
    r0 = ra.loc[y, f'recensioni_nel_file_{s0}']; r1 = ra.loc[y, f'recensioni_nel_file_{s1}']
    say(f'{y}: annunci {a0} -> {a1} ({a1/a0-1:+.1%}); recensioni {r0} -> {r1} ({r1/r0-1:+.1%})')

# confronti di livello 2025
r = c.loc[2025]
say(f'\n2025: annunci Airbnb con recensione nel 2025 (unione) {r.airbnb_annunci_con_recensione_unione:.0f}; ISTAT extra-alberghiere {r.istat_extra_alberghieri_strutture:.0f}; Comune CAV+LT {r.comune_CAV_piu_LT:.0f}')
say(f'quota presenze extra-alberghiere: 2019 {c.loc[2019,"quota_presenze_extra_alberghiere"]:.1%}; 2022 {c.loc[2022,"quota_presenze_extra_alberghiere"]:.1%}; 2025 {c.loc[2025,"quota_presenze_extra_alberghiere"]:.1%}')
say(f'ISTAT extra-alberghiere strutture: 2019 {c.loc[2019,"istat_extra_alberghieri_strutture"]:.0f} -> 2025 {c.loc[2025,"istat_extra_alberghieri_strutture"]:.0f} (x{c.loc[2025,"istat_extra_alberghieri_strutture"]/c.loc[2019,"istat_extra_alberghieri_strutture"]:.1f}); Airbnb annunci con recensione (unione): 2019 {c.loc[2019,"airbnb_annunci_con_recensione_unione"]:.0f} -> 2025 {c.loc[2025,"airbnb_annunci_con_recensione_unione"]:.0f} (x{c.loc[2025,"airbnb_annunci_con_recensione_unione"]/c.loc[2019,"airbnb_annunci_con_recensione_unione"]:.1f})')
say(f'presenze extra-alberghiere 2019 {c.loc[2019,"istat_presenze_extra_alberghiere"]:.0f} -> 2025 {c.loc[2025,"istat_presenze_extra_alberghiere"]:.0f}; alberghiere 2019 {uf[(uf.anno==2019)&(uf.tipo_struttura=="Es. Alberghieri")&(uf.cittadinanza=="Totale")].presenze.iloc[0]:.0f} -> 2025 {uf[(uf.anno==2025)&(uf.tipo_struttura=="Es. Alberghieri")&(uf.cittadinanza=="Totale")].presenze.iloc[0]:.0f}')
say(f'recensioni Airbnb (unione): 2019 {c.loc[2019,"airbnb_recensioni_unione"]:.0f}; 2020 {c.loc[2020,"airbnb_recensioni_unione"]:.0f}; 2025 {c.loc[2025,"airbnb_recensioni_unione"]:.0f}; 2015 {c.loc[2015,"airbnb_recensioni_unione"]:.0f}; 2014 {c.loc[2014,"airbnb_recensioni_unione"]:.0f}')
pa = pd.read_csv(P/'recensioni_per_annuncio.csv', parse_dates=['prima_recensione', 'ultima_recensione'])
say(f'annunci nell unione con almeno una recensione: {len(pa)}; con prima recensione prima del 2015: {(pa.prima_recensione.dt.year<2015).sum()}; ancora con recensioni nel 2026: {((pa.prima_recensione.dt.year<2015)&(pa.ultima_recensione.dt.year==2026)).sum()}')

# per NIL
nr = pd.read_csv(P/'recensioni_nil_anno.csv')
w = nr.pivot_table(index=['nil_id', 'nil_nome'], columns='anno', values='annunci_con_recensione', aggfunc='sum').fillna(0)
cn = w[[2015, 2019, 2023, 2025]].copy(); cn.columns = [f'annunci_con_recensione_{y}' for y in cn.columns]
cn['rapporto_2025_su_2019'] = cn.annunci_con_recensione_2025/cn.annunci_con_recensione_2019.replace(0, np.nan)
cn = cn.reset_index(); cn.to_csv(P/'crescita_nil.csv', index=False)
big = cn[cn.annunci_con_recensione_2019 >= 30]
say(f'\nNIL con almeno 30 annunci recensiti nel 2019: {len(big)}; rapporto 2025/2019 mediano {big.rapporto_2025_su_2019.median():.2f}; massimo {big.rapporto_2025_su_2019.max():.2f} ({big.loc[big.rapporto_2025_su_2019.idxmax(),"nil_nome"]}); minimo {big.rapporto_2025_su_2019.min():.2f} ({big.loc[big.rapporto_2025_su_2019.idxmin(),"nil_nome"]})')
tot = cn[['annunci_con_recensione_2019', 'annunci_con_recensione_2025']].sum()
duo = cn[cn.nil_id.isin([1, 2, 10])][['annunci_con_recensione_2019', 'annunci_con_recensione_2025']].sum()
say(f'quota dei 3 NIL con piu densita (Duomo 1, Brera 2, Stazione Centrale 10) sugli annunci recensiti: 2019 {duo.iloc[0]/tot.iloc[0]:.1%}; 2025 {duo.iloc[1]/tot.iloc[1]:.1%}')
(base/'out'/'crescita.txt').write_text('\n'.join(log), encoding='utf-8')
