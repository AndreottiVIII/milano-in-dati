"""Fase 1 - caldo / isola di calore: dalla temperatura oraria (valori alle ore :00) ai riepiloghi per stazione.
uso: python -I -X utf8 analisi_caldo.py <pioggia-e-caldo assoluta>
Entrata: pulito/intermedi/T_orario.parquet, sensori_selezionati.csv, stazioni_nil_alberi.csv
Uscita (in pulito/): temp_giornaliera.csv.gz, caldo_estate_sensore.csv, caldo_isola_ora.csv, caldo_isola_stazione.csv,
                     caldo_isola_anno.csv, caldo_copertura_matrice.csv, caldo_notti_tropicali.csv, caldo_alberi_confronto.csv
Definizioni:
  giorno valido = almeno 20 ore su 24 con lettura valida; tmin/tmax = minimo/massimo delle letture alle ore :00 del giorno solare
  (ARPA pubblica ora solare; l'estremo vero tra due letture puo' essere un po' piu' alto/basso: stesso metodo per tutte le stazioni e gli anni).
  estate = giugno-luglio-agosto (JJA), 92 giorni; estate 'completa' se almeno 80 giorni validi.
  notte tropicale = giorno con tmin >= 20 gradi.
  Isola di calore = temperatura della stazione urbana meno media delle stazioni di riferimento rurali, stesso istante."""
import sys, os
import numpy as np, pandas as pd
base = sys.argv[1]
pu = os.path.join(base, 'pulito')
sel = pd.read_csv(os.path.join(pu, 'sensori_selezionati.csv'), dtype=str)
nome = dict(zip(sel.idsensore, sel.nomestazione))
dist = dict(zip(sel.idsensore, sel.dist_duomo_km.astype(float)))
T = pd.read_parquet(os.path.join(pu, 'intermedi', 'T_orario.parquet'))
T['data'] = T.ora.dt.floor('D')
T['h'] = T.ora.dt.hour
d = T.groupby(['idsensore', 'data']).agg(n=('t', 'size'), tmin=('t', 'min'), tmax=('t', 'max'), tmean=('t', 'mean')).reset_index()
d = d[d.n >= 20].copy()
d['anno'] = d.data.dt.year
d['mese'] = d.data.dt.month
d.round(2).to_csv(os.path.join(pu, 'temp_giornaliera.csv.gz'), index=False, compression='gzip')

# copertura: giorni validi per sensore e anno
cov = d.groupby(['idsensore', 'anno']).size().unstack(fill_value=0)
cov.insert(0, 'nomestazione', cov.index.map(nome))
cov.to_csv(os.path.join(pu, 'caldo_copertura_matrice.csv'))

# estate JJA
j = d[d.mese.isin([6, 7, 8])]
E = j.groupby(['idsensore', 'anno']).agg(giorni_validi=('tmin', 'size'), tmin_media=('tmin', 'mean'), tmax_media=('tmax', 'mean'),
                                         tmean_media=('tmean', 'mean'), notti_tropicali=('tmin', lambda s: int((s >= 20).sum())),
                                         giorni_tmax_ge30=('tmax', lambda s: int((s >= 30).sum())), giorni_tmax_ge35=('tmax', lambda s: int((s >= 35).sum())),
                                         tmax_massima=('tmax', 'max'), tmin_massima=('tmin', 'max')).reset_index()
E['nomestazione'] = E.idsensore.map(nome)
E['dist_duomo_km'] = E.idsensore.map(dist)
E['estate_completa'] = E.giorni_validi >= 80
E.round(2).to_csv(os.path.join(pu, 'caldo_estate_sensore.csv'), index=False)
# notti tropicali: tabella larga per anno (solo estati complete; le incomplete sono un minimo)
nt = E.pivot(index='idsensore', columns='anno', values='notti_tropicali')
nt.insert(0, 'nomestazione', nt.index.map(nome))
nt.to_csv(os.path.join(pu, 'caldo_notti_tropicali.csv'))

# ---- isola di calore ---------------------------------------------------------------
# classi: scelta mia (giudizio, non misura) in base a nome e luogo; vedi NOTE.md. Riferimento rurale = campagna aperta
# o centro minore a oltre 12 km dal Duomo; urbane = stazioni dentro il Comune di Milano.
URBANE = ['5897', '5909', '5911', '5920', '8162', '2001']          # Brera, Juvara, Marche, Zavattari, Feltre, Lambrate
RURALI = ['5917', '2187', '5910', '4066', '17488', '2122', '12716']  # Rodano, Landriano, Lacchiarella, Arconate, Magenta, Sant'Angelo L., Bereguardo
CINTURA = ['5903', '4058', '14742']                                 # Corsico, Parco Nord (Cinisello), Rho
pd.DataFrame([dict(idsensore=i, nomestazione=nome.get(i), classe=c, dist_duomo_km=dist.get(i)) for c, L in
              [('urbana', URBANE), ('cintura', CINTURA), ('rurale', RURALI)] for i in L]).to_csv(os.path.join(pu, 'stazioni_classi.csv'), index=False)
W = T[T.ora.dt.month.isin([6, 7, 8])].pivot_table(index='ora', columns='idsensore', values='t')
FINESTRE = {'2017-2025': ('2017-01-01', '2025-12-31'), '2011-2016': ('2011-01-01', '2016-12-31'), '2002-2010': ('2002-01-01', '2010-12-31')}
rows_h, rows_s = [], []
for fin, (a, b) in FINESTRE.items():
    w = W[(W.index >= a) & (W.index <= b + ' 23:59')]
    ur = [c for c in URBANE if c in w]
    ru = [c for c in RURALI if c in w]
    # riferimento: media dei rurali disponibili, almeno 3 (se ne mancano, istante scartato)
    ref = w[ru].where(w[ru].notna().sum(axis=1) >= 3).mean(axis=1)
    for c in ur + [x for x in CINTURA if x in w] + ru:
        diff = (w[c] - ref).dropna()
        if len(diff) < 500:
            continue
        hh = diff.groupby(diff.index.hour).mean()
        for h, v in hh.items():
            rows_h.append(dict(finestra=fin, idsensore=c, nomestazione=nome[c], ora=h, differenza_vs_rurali=round(v, 3), n=int((diff.index.hour == h).sum())))
        night = diff[diff.index.hour.isin([22, 23, 0, 1, 2, 3, 4, 5])]
        day = diff[diff.index.hour.isin([12, 13, 14, 15, 16])]
        dm = d[(d.idsensore == c) & d.mese.isin([6, 7, 8]) & (d.data >= a) & (d.data <= b)]
        rows_s.append(dict(finestra=fin, idsensore=c, nomestazione=nome[c], dist_duomo_km=dist[c], ore_confronto=len(diff),
                           diff_notte_22_05=round(night.mean(), 3), diff_pomeriggio_12_16=round(day.mean(), 3),
                           diff_ora_massima=int(hh.idxmax()), diff_massima=round(hh.max(), 3),
                           tmin_jja_media=round(dm.tmin.mean(), 2), tmax_jja_media=round(dm.tmax.mean(), 2),
                           notti_tropicali_per_estate=round((dm.tmin >= 20).sum() / max(1, dm.anno.nunique()), 1), estati=dm.anno.nunique()))
    # media dell'insieme urbano
    if len(ur) >= 2:
        urm = w[ur].where(w[ur].notna().sum(axis=1) >= 2).mean(axis=1)
        diff = (urm - ref).dropna()
        hh = diff.groupby(diff.index.hour).mean()
        for h, v in hh.items():
            rows_h.append(dict(finestra=fin, idsensore='URBANE_MEDIA', nomestazione='media stazioni di Milano (' + ','.join(ur) + ')', ora=h, differenza_vs_rurali=round(v, 3), n=int((diff.index.hour == h).sum())))
pd.DataFrame(rows_h).to_csv(os.path.join(pu, 'caldo_isola_ora.csv'), index=False)
S = pd.DataFrame(rows_s)
S.to_csv(os.path.join(pu, 'caldo_isola_stazione.csv'), index=False)

# per anno: JJA tmin (e tmax) stazione meno media rurali dello stesso giorno -> si vedono i salti
dd = d[d.mese.isin([6, 7, 8])].pivot_table(index='data', columns='idsensore', values='tmin')
dx = d[d.mese.isin([6, 7, 8])].pivot_table(index='data', columns='idsensore', values='tmax')
ru = [c for c in RURALI if c in dd]
refn = dd[ru].where(dd[ru].notna().sum(axis=1) >= 3).mean(axis=1)
refx = dx[ru].where(dx[ru].notna().sum(axis=1) >= 3).mean(axis=1)
rows = []
for c in URBANE + CINTURA:
    if c not in dd:
        continue
    a = (dd[c] - refn).dropna()
    b = (dx[c] - refx).dropna()
    for y, g in a.groupby(a.index.year):
        if len(g) >= 40:
            rows.append(dict(idsensore=c, nomestazione=nome[c], anno=y, giorni=len(g), tmin_meno_rurali=round(g.mean(), 2),
                             tmax_meno_rurali=round(b[b.index.year == y].mean(), 2) if (b.index.year == y).sum() >= 40 else np.nan))
A = pd.DataFrame(rows)
A.to_csv(os.path.join(pu, 'caldo_isola_anno.csv'), index=False)

# confronto con gli alberi (solo stazioni dentro Milano)
sn = pd.read_csv(os.path.join(pu, 'stazioni_nil_alberi.csv'), dtype={'idstazione': str})
sel['idstazione'] = sel.idstazione.astype(str)
m = sel[sel.tipologia == 'Temperatura'][['idsensore', 'idstazione']].merge(sn, on='idstazione')
fin = S[S.finestra == '2017-2025']
m = m.merge(fin[['idsensore', 'diff_notte_22_05', 'diff_pomeriggio_12_16', 'tmin_jja_media', 'tmax_jja_media', 'notti_tropicali_per_estate']], on='idsensore')
m = m[m.id_nil.notna()]
m.to_csv(os.path.join(pu, 'caldo_alberi_confronto.csv'), index=False)
print('FATTO caldo')
print(S[S.finestra == '2017-2025'].to_string())
