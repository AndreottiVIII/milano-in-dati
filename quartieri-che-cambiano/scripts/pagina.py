"""Pagina - dati per docs/quartieri-che-cambiano/ (riscrive tutto ogni volta).
Entrate: quartieri-che-cambiano/out/*.csv|json (passi 01-05) e citta-15-minuti/out/nil_poligoni_punteggi.geojson (confini NIL).
Uscite in <docs>/quartieri-che-cambiano/data/: riepilogo.json, nil.geojson, nil.csv, robustezza_varianti.csv, indicatori_definizioni.csv
NON si pubblicano: civici_collegamenti.csv (derivato dai civici), i file grezzi.
Uso: python -I -X utf8 pagina.py <milano-in-dati> <quartieri-che-cambiano> <docs>/quartieri-che-cambiano
"""
import sys, os, json, math, datetime
import numpy as np
import pandas as pd
from shapely.geometry import shape, mapping

BASE, QC, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(QC, 'out')
DATA = os.path.join(DOCS, 'data')
os.makedirs(DATA, exist_ok=True)
rd = lambda f, **k: pd.read_csv(os.path.join(OUT, f), **k)

T = rd('tipologie_nil.csv', index_col=0)
E = rd('indice_nil.csv', index_col=0)
D = rd('indicatori_nil.csv', index_col=0)
PC = rd('robustezza_pesi_casuali.csv', index_col=0)
RV = rd('robustezza_varianti.csv')
LOO = rd('robustezza_loo.csv')
COR = rd('correlazioni_indicatori.csv', index_col=0)
CN = rd('collegamento_cap_nil.csv')
ZN = rd('collegamento_omi_nil.csv')
MUN = rd('municipi.csv', index_col=0)
pca = json.load(open(os.path.join(OUT, 'pca_indicatori.json'), encoding='utf-8'))
tlog = json.load(open(os.path.join(OUT, 'tipologie_log.json'), encoding='utf-8'))
clog = json.load(open(os.path.join(OUT, 'collegamenti_log.json'), encoding='utf-8'))
anag = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'nil_anagrafica.csv')).set_index('id_nil')

FIX = {"Citta' studi": 'Città Studi', "Monlue' - Ponte Lambro": 'Monluè - Ponte Lambro', "Parco Bosco in citta'": 'Parco Bosco in città',
       'Pta Romana': 'Porta Romana', 'QT 8': 'QT8', 'Magenta - S.Vittore': 'Magenta - San Vittore', 'Giardini P.ta Venezia': 'Giardini Porta Venezia'}
nome = lambda s: FIX.get(s, s)

CORE = ['reddito_var', 'prezzo_var', 'affitto_var', 'costruzioni_100', 'airbnb_100', 'ristoranti_var', 'botteghe_var', 'giovani_var', 'laureati_var']
IND = [
    dict(id='reddito_var', et='Reddito reale', blocco='casa', unita='%', dec=1, segno=True,
         desc='Variazione del reddito medio reale per contribuente (euro 2025), anno d\'imposta 2011 → 2024. È il dato del CAP, portato al quartiere.',
         fonte='MEF, Dip. Finanze (redditi/pulito/cap_milano_media_euro2025.csv)', link='../redditi/'),
    dict(id='prezzo_var', et='Prezzo delle case (OMI)', blocco='casa', unita='%', dec=1, segno=True,
         desc='Variazione del prezzo di vendita stimato dall\'OMI, abitazioni civili, in euro 2025, 2014/2 → 2026/1. È una stima dell\'Agenzia delle Entrate.',
         fonte='Agenzia delle Entrate, OMI (prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv)', link='../prezzi-case/'),
    dict(id='affitto_var', et='Affitto (OMI)', blocco='casa', unita='%', dec=1, segno=True,
         desc='Variazione dell\'affitto stimato dall\'OMI, abitazioni civili, in euro 2025, 2014/2 → 2026/1. Stima, non affitti pagati.',
         fonte='Agenzia delle Entrate, OMI (stesso file)', link='../prezzi-case/'),
    dict(id='costruzioni_100', et='Nuove abitazioni', blocco='casa', unita=' ogni 1.000 residenti', dec=1, segno=False,
         desc='Abitazioni in nuovi fabbricati con permesso di costruire tra il 2014 e il 2024, ogni 1.000 residenti (2024). Sono permessi, non cantieri finiti; le ricostruzioni dopo demolizione sono incluse; ristrutturazioni e demolizioni senza ricostruzione non ci sono.',
         fonte='Comune di Milano, permessi di costruire (costruzioni/pulito/nil_costruzioni.csv)', link=None),
    dict(id='airbnb_100', et='Affitti brevi', blocco='commercio', unita=' ogni 100 abitazioni', dec=1, segno=False,
         desc='Annunci Airbnb ogni 100 abitazioni, fotografia del 19 settembre 2026. È un livello, non una variazione.',
         fonte='Inside Airbnb, CC BY 4.0 (affitti-brevi/pulito/nil_riepilogo.csv)', link='../affitti-brevi/'),
    dict(id='ristoranti_var', et='Locali (bar, ristoranti)', blocco='commercio', unita='%', dec=1, segno=True,
         desc='Indirizzi con un locale di somministrazione nuovi meno scomparsi, 2019 → 2026, in percentuale delle pratiche del 2019.',
         fonte='Comune di Milano, registro pubblici esercizi (ristoranti/pulito/registro_2019_2026_nil.csv)', link='../ristoranti/'),
    dict(id='botteghe_var', et='Botteghe storiche perse', blocco='commercio', unita='%', dec=1, segno=False,
         desc="Quota delle botteghe dell'Albo comunale 2017 che nel 2024 risultano cessate o non sono più nell'Albo. Solo quartieri con almeno 5 botteghe nell'Albo 2017 (23). «Cessata» è l'etichetta del Comune, senza data.",
         fonte="Comune di Milano, Albo delle Botteghe Storiche 2017 e 2024 (botteghe/pulito/botteghe.csv)", link=None),
    dict(id='giovani_var', et='Residenti 25-34 anni', blocco='persone', unita=' punti', dec=1, segno=True,
         desc='Variazione della quota di residenti di 25-34 anni, 2014 → 2025 (punti percentuali). Anagrafe del Comune.',
         fonte='Comune di Milano, residenti per età (popolazione/pulito/eta_nil_anno_indicatori.csv)', link=None),
    dict(id='laureati_var', et='Laureati', blocco='persone', unita=' punti', dec=1, segno=True,
         desc='Variazione della quota di laureati sui residenti, censimento 2011 → 2023 (punti percentuali).',
         fonte='ISTAT, censimenti (censimenti/pulito/indicatori_NIL.csv)', link='../censimenti/'),
]
r1 = lambda x, d=1: None if pd.isna(x) else round(float(x), d)

# ------------------------------------------------------------------ limiti per NIL
cap_dom = CN.sort_values('quota_nil', ascending=False).groupby('ID_NIL').head(1).set_index('ID_NIL')
zon_dom = ZN.sort_values('quota_nil', ascending=False).groupby('ID_NIL').head(1).set_index('ID_NIL')


def limiti(i):
    d = D.loc[i]
    L = []
    if not bool(d.idoneo):
        L.append('Meno di 2.000 residenti nel 2024: fuori classifica. I valori sono mostrati ma non ordinati.')
    if i in cap_dom.index:
        c = cap_dom.loc[i]
        if pd.isna(d.reddito_var) and d.quota_civici_cap_instabili > 0.5:
            L.append('Reddito non calcolato: più della metà delle case sta nei CAP 20121 e 20122, la cui sede fiscale cambia senza motivo economico.')
        elif not pd.isna(d.reddito_var):
            L.append('Il reddito è quello del CAP %d (%d%% delle case del quartiere): quartieri vicini condividono lo stesso numero.' % (c.CAP, round(c.quota_nil * 100)))
    if i in zon_dom.index and not pd.isna(d.prezzo_var):
        z = zon_dom.loc[i]
        L.append('Prezzi e affitti sono quelli delle zone OMI (stime dell\'Agenzia); zona principale %s, %d%% delle case.' % (z.zona_2026_1, round(z.quota_nil * 100)))
    if pd.isna(d.ristoranti_var) and bool(d.idoneo):
        L.append('Locali non calcolati: meno di 20 pratiche nel registro 2019.')
    if pd.isna(d.botteghe_var) and bool(d.idoneo):
        L.append("Botteghe storiche non calcolate: meno di 5 botteghe nell'Albo 2017 (la quota sarebbe rumore).")
    if not pd.isna(d.costruzioni_100) and d.costruzioni_100 > 100:
        L.append('Molte case nuove con permesso 2014-2024: %d ogni 1.000 residenti. Il "cambiamento" qui è anche edilizia.' % round(d.costruzioni_100))
    if pd.isna(d.airbnb_100) and bool(d.idoneo):
        L.append('Affitti brevi non calcolati: troppo poche abitazioni per un rapporto sensato.')
    if not pd.isna(d.pop_var) and d.pop_var > 25:
        L.append('Quartiere con molte case nuove: residenti %+.0f%% dal 2014 al 2025. Il cambiamento qui è anche costruzione.' % d.pop_var)
    if bool(d.idoneo):
        n = int(E.loc[i, 'n_indicatori']) if i in E.index and not pd.isna(E.loc[i, 'n_indicatori']) else 0
        if 0 < n < 9:
            L.append('Indice calcolato su %d indicatori su 9.' % n)
    return L


# ------------------------------------------------------------------ geometrie
g = json.load(open(os.path.join(BASE, 'citta-15-minuti', 'out', 'nil_poligoni_punteggi.geojson'), encoding='utf-8'))
geo = {int(f['properties']['ID_NIL']): shape(f['geometry']) for f in g['features']}


def rnd(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 5), round(coords[1], 5)]
    return [rnd(c) for c in coords]


feats, rows = [], []
N = int(T.shape[0])
for i in D.index:
    d = D.loc[i]
    cl = i in T.index
    p = dict(i=int(i), n=nome(d.nil), mun=int(anag.loc[i, 'municipio_prevalente']), ab=None if pd.isna(d.residenti_2024) else int(d.residenti_2024), cl=1 if cl else 0,
             v=[r1(d[c], 2) for c in CORE], ctx=dict(pop=r1(d.pop_var), str=r1(d.stranieri_var), sc=r1(d.scuole_var), cr=r1(d.airbnb_cresc_100, 2)),
             liv_v=dict(red=r1(d.reddito_2024, 0), pre=r1(d.prezzo_2026_reale, 0), lau=r1(d.laureati_2023)))
    if cl:
        t, e = T.loc[i], E.loc[i]
        p.update(rk=int(t.rango), ix=r1(t.indice, 3), rmin=int(t.rango_min_varianti), rmax=int(t.rango_max_varianti), p5=r1(t.rango_p5, 0), p95=r1(t.rango_p95, 0),
                 q10=r1(t.quota_top10_pesi_casuali, 2), b10=r1(t.quota_bottom10_pesi_casuali, 2), liv=r1(t.livello, 3), bc=r1(t.blocco_casa, 3), bn=r1(t.blocco_negozi, 3),
                 bp=r1(t.blocco_persone, 3), tip=t.tipologia, ns=int(t.n_segnali_alti), nind=int(t.n_indicatori),
                 z=[r1(e['z_' + c], 3) for c in CORE])
    p['lim'] = limiti(i)
    geom = geo[i].simplify(0.00018, preserve_topology=True)
    m = mapping(geom)
    feats.append(dict(type='Feature', properties=p, geometry=dict(type=m['type'], coordinates=rnd(m['coordinates']))))
    rows.append(dict(id_nil=int(i), nil=nome(d.nil), municipio=p['mun'], residenti_2024=p['ab'], in_classifica=int(cl),
                     rango=p.get('rk'), indice=p.get('ix'), rango_min_varianti=p.get('rmin'), rango_max_varianti=p.get('rmax'), rango_p5_pesi_casuali=p.get('p5'), rango_p95_pesi_casuali=p.get('p95'),
                     tipologia=p.get('tip'), livello=p.get('liv'), **{c: r1(d[c], 3) for c in CORE},
                     **{('z_' + c): (p['z'][k] if cl else None) for k, c in enumerate(CORE)},
                     variazione_residenti_2014_2025_pct=r1(d.pop_var), variazione_quota_stranieri_punti=r1(d.stranieri_var), variazione_iscritti_scuole_pct=r1(d.scuole_var)))
json.dump(dict(type='FeatureCollection', features=feats), open(os.path.join(DATA, 'nil.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pd.DataFrame(rows).sort_values(['in_classifica', 'rango'], ascending=[False, True]).to_csv(os.path.join(DATA, 'nil.csv'), index=False)
RV.to_csv(os.path.join(DATA, 'robustezza_varianti.csv'), index=False)
rd('indicatori_definizioni.csv').to_csv(os.path.join(DATA, 'indicatori_definizioni.csv'), index=False)

# ------------------------------------------------------------------ riepilogo
by = lambda nm: T[T.nil.map(nome) == nm].iloc[0]
Dn = D[D.idoneo]
med = {c: r1(Dn[c].median(), 2) for c in CORE}
m1 = T[T.municipio == 1].sort_values('rango')
n_in_top10_mun1 = int(((T.municipio == 1) & (T.rango <= 10)).sum())
sarpi, lamb, magg = by('Sarpi'), by('Lambrate - Ortica'), by('Maggiore - Musocco - Certosa')
lam_d = D.loc[int(T[T.nil == 'Lambrate - Ortica'].index[0])]
sar_d = D.loc[int(T[T.nil == 'Sarpi'].index[0])]
mag_d = D.loc[int(T[T.nil == 'Maggiore - Musocco - Certosa'].index[0])]
rank_cos = int(Dn.costruzioni_100.rank(ascending=False)[int(T[T.nil == 'Lambrate - Ortica'].index[0])])
b12 = pd.read_csv(os.path.join(BASE, 'docs', 'prezzi-case', 'data', 'zone_ultimo_semestre.csv')).set_index('zona').loc['B12', 'var_reale_2014_2_ultimo']
rank_rent = int(Dn.affitto_var.rank(ascending=False)[int(T[T.nil == 'Lambrate - Ortica'].index[0])])
rank_lau = int(Dn.laureati_var.rank(ascending=False)[int(T[T.nil == 'Lambrate - Ortica'].index[0])])
top5 = T.sort_values('rango').head(5)
bot5 = T.sort_values('rango').tail(5)
stable_top = T[T.quota_top10_pesi_casuali >= 0.5].sort_values('rango')
stable_bot = T[T.quota_bottom10_pesi_casuali >= 0.5].sort_values('rango', ascending=False)
w = (T.rango_max_varianti - T.rango_min_varianti)
tip = []
for t, gr in T.groupby('tipologia'):
    tip.append(dict(nome=t, n=int(len(gr)), residenti=int(gr.residenti_2024.sum()), nil=[nome(x) for x in gr.sort_values('rango').nil]))
blocchi = {}
for k, col in [('casa', 'blocco_casa'), ('commercio', 'blocco_negozi'), ('persone', 'blocco_persone')]:
    s = T[col].dropna().sort_values(ascending=False)
    blocchi[k] = dict(alti=[nome(T.loc[x, 'nil']) for x in s.index[:3]], bassi=[nome(T.loc[x, 'nil']) for x in s.index[-3:]])
cor = COR.values
bcor = T[['blocco_casa', 'blocco_negozi', 'blocco_persone']].corr(method='spearman')
R = dict(
    generato=datetime.date.today().isoformat(),
    n_nil=int(len(D)), n_classificati=N, n_fuori=int(len(D) - N), fuori=[nome(x) for x in D[~D.idoneo].nil],
    ind=IND, mediane=med,
    default_w=[1] * len(CORE),
    sorpresa=dict(
        mun1=[dict(n=nome(r.nil), rk=int(r.rango)) for r in m1.itertuples()], mun1_n=int(len(m1)), mun1_peggior=int(m1.rango.min()), mun1_ultimi=int(N - m1.rango.min() + 1),
        mun1_nel_top10=n_in_top10_mun1, b12=r1(b12 * 100, 1),
        sarpi=dict(rk=int(sarpi.rango), rmin=int(sarpi.rango_min_varianti), rmax=int(sarpi.rango_max_varianti), red=r1(sar_d.reddito_var), pre=r1(sar_d.prezzo_var), aff=r1(sar_d.affitto_var), rist=r1(sar_d.ristoranti_var), air=r1(sar_d.airbnb_100)),
        lamb=dict(rk=int(lamb.rango), red=r1(lam_d.reddito_var), pre=r1(lam_d.prezzo_var), aff=r1(lam_d.affitto_var), lau=r1(lam_d.laureati_var), cos=r1(lam_d.costruzioni_100, 0), rk_cos=rank_cos, rk_aff=rank_rent, rk_lau=rank_lau,
                  rmin=int(lamb.rango_min_varianti), rmax=int(lamb.rango_max_varianti)),
        magg=dict(rk=int(magg.rango), cos=r1(mag_d.costruzioni_100, 0), lau=r1(mag_d.laureati_var), red=r1(mag_d.reddito_var)),
        top5=[dict(n=nome(r.nil), rk=int(r.rango), rmax=int(r.rango_max_varianti)) for r in top5.itertuples()],
        bot5=[dict(n=nome(r.nil), rk=int(r.rango), rmin=int(r.rango_min_varianti)) for r in bot5.itertuples()],
    ),
    robustezza=dict(
        varianti=[dict(v=r.variante, rho=float(r.spearman_con_base), t=None if pd.isna(r.top10_in_comune) else int(r.top10_in_comune), b=None if pd.isna(r.bottom10_in_comune) else int(r.bottom10_in_comune), n=int(r.n_NIL)) for r in RV.itertuples()],
        loo=[dict(c=r.escluso, rho=float(r.spearman_con_base), t=int(r.top10_in_comune), b=int(r.bottom10_in_comune)) for r in LOO.itertuples()],
        rho_min=float(min(RV.spearman_con_base.min(), LOO.spearman_con_base.min())), rho_max=float(max(RV.spearman_con_base.max(), LOO.spearman_con_base.max())),
        ampiezza_media=r1(w.mean(), 0), ampiezza_mediana=r1(w.median(), 0), ampiezza_p5p95=r1((T.rango_p95 - T.rango_p5).mean(), 0), pesi_casuali=5000,
        stabili_top=[nome(x) for x in stable_top.nil], stabili_bot=[nome(x) for x in stable_bot.nil]),
    coerenza=dict(alfa=pca['alfa_cronbach'], corr_media=pca['correlazione_media_a_coppie_spearman'], prima_comp=pca['quota_prima_componente'],
                  blocchi=dict(casa_comm=r1(bcor.iloc[0, 1], 2), casa_pers=r1(bcor.iloc[0, 2], 2), comm_pers=r1(bcor.iloc[1, 2], 2)),
                  rho_airbnb_reddito2024=r1(Dn[['airbnb_100', 'reddito_2024']].corr(method='spearman').iloc[0, 1], 2),
                  rho_affitto_reddito2024=r1(Dn[['affitto_var', 'reddito_2024']].corr(method='spearman').iloc[0, 1], 2),
                  rho_giovani_reddito=r1(Dn[['giovani_var', 'reddito_var']].corr(method='spearman').iloc[0, 1], 2),
                  rho_giovani_stranieri=r1(Dn[['giovani_var', 'stranieri_var']].corr(method='spearman').iloc[0, 1], 2),
                  rho_indice_stranieri=r1(E[['indice']].join(D[['stranieri_var']]).corr(method='spearman').iloc[0, 1], 2),
                  corr=[[r1(v, 2) for v in row] for row in cor]),
    tipologie=tip, soglie=tlog['soglie'], silhouette=tlog['silhouette_kmeans'],
    blocchi=blocchi,
    municipi=[dict(m=int(i), n=int(r.n_NIL), ab=int(r.residenti_2024), ix=r1(r.indice_medio_pesato, 2), liv=r1(r.livello_medio_pesato, 2)) for i, r in MUN.iterrows()],
    collegamento=dict(civici=clog['civici_totali'], residenziali=clog['civici_residenziali'], con_omi=clog['residenziali_con_valore_omi']['prezzo_cresc'],
                      cap_dom90=clog['NIL_con_CAP_dominante_ge_90pct'], cap_dom60=clog['NIL_con_CAP_dominante_lt_60pct']),
    n_reddito_mancante=int(Dn.reddito_var.isna().sum()), n_botteghe=int(Dn.botteghe_var.notna().sum()), n_botteghe_mancanti=int(Dn.botteghe_var.isna().sum()), n_locali_mancanti=int(Dn.ristoranti_var.isna().sum()), n_airbnb_mancanti=int(Dn.airbnb_100.isna().sum()),
)
json.dump(R, open(os.path.join(DATA, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for f in sorted(os.listdir(DATA)):
    print(f, os.path.getsize(os.path.join(DATA, f)))
