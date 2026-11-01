"""Passo 5 - riepilogo scritto (out/riepilogo.txt): tutti i numeri che finiscono in NOTE.md escono da qui.
Uso: python -I -X utf8 05_riepilogo.py <milano-in-dati> <quartieri-che-cambiano>
"""
import sys, os, json
import numpy as np
import pandas as pd

BASE, QC = sys.argv[1], sys.argv[2]
OUT = os.path.join(QC, 'out')
T = pd.read_csv(os.path.join(OUT, 'tipologie_nil.csv'), index_col=0)
E = pd.read_csv(os.path.join(OUT, 'indice_nil.csv'), index_col=0)
D = pd.read_csv(os.path.join(OUT, 'indicatori_nil.csv'), index_col=0)
rv = pd.read_csv(os.path.join(OUT, 'robustezza_varianti.csv'))
loo = pd.read_csv(os.path.join(OUT, 'robustezza_loo.csv'))
pc = json.load(open(os.path.join(OUT, 'pca_indicatori.json')))
tl = json.load(open(os.path.join(OUT, 'tipologie_log.json')))
cl = json.load(open(os.path.join(OUT, 'collegamenti_log.json')))
cor = pd.read_csv(os.path.join(OUT, 'correlazioni_indicatori.csv'), index_col=0)
mun = pd.read_csv(os.path.join(OUT, 'municipi.csv'), index_col=0)
CORE = ['reddito_var', 'prezzo_var', 'affitto_var', 'costruzioni_100', 'airbnb_100', 'ristoranti_var', 'botteghe_var', 'giovani_var', 'laureati_var']
L = []
P = L.append
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 40)

P('== COPERTURA')
P(f"NIL totali {len(D)}; idonei (>=2.000 residenti nel 2024, popolazione/pulito/eta_nil_anno_indicatori.csv): {int(D.idoneo.sum())}")
P('NIL non in classifica: ' + '; '.join(D.loc[~D.idoneo, 'nil'] + ' (' + D.loc[~D.idoneo, 'residenti_2024'].fillna(0).astype(int).astype(str) + ')'))
P('Indicatori mancanti tra gli idonei (n NIL senza valore):')
P(str(D.loc[D.idoneo, CORE].isna().sum().to_dict()))
P('NIL idonei con meno di 9 indicatori: ' + '; '.join(E.loc[E.n_indicatori < 9, 'nil'] + ' (' + E.loc[E.n_indicatori < 9, 'n_indicatori'].astype(int).astype(str) + ')'))
P('NIL senza reddito (piu\' della meta\' dei civici in CAP 20121/20122): ' + '; '.join(D.loc[D.idoneo & D.reddito_var.isna() & (D.quota_civici_cap_instabili > 0.5), 'nil']))
P('NIL senza locali (meno di 20 pratiche nel 2019): ' + '; '.join(D.loc[D.idoneo & D.ristoranti_var.isna(), 'nil']))
P('NIL senza Airbnb (denominatore piccolo): ' + '; '.join(D.loc[D.idoneo & D.airbnb_100.isna(), 'nil']))
P(f"Valori distinti di reddito_var tra i NIL idonei (CAP): {D.loc[D.idoneo,'reddito_var'].round(6).nunique()} su {int(D.loc[D.idoneo,'reddito_var'].notna().sum())} NIL")
P(f"Collegamento: {json.dumps(cl, ensure_ascii=False)}")

P('\n== MEDIANE DEGLI INDICATORI (NIL idonei)')
P(D.loc[D.idoneo, CORE + ['pop_var', 'stranieri_var', 'scuole_var', 'eta_media_var']].describe().round(2).T.to_string())

P('\n== COERENZA TRA GLI INDICATORI (Spearman)')
P(cor.round(2).to_string())
P(json.dumps(pc, ensure_ascii=False))
P('correlazioni tra blocchi: ' + T[['blocco_casa', 'blocco_negozi', 'blocco_persone', 'livello']].corr(method='spearman').round(2).to_string())

cols = ['nil', 'rango', 'indice', 'rango_min_varianti', 'rango_max_varianti', 'rango_p5', 'rango_p95', 'quota_top10_pesi_casuali', 'blocco_casa', 'blocco_negozi',
        'blocco_persone', 'livello', 'tipologia', 'n_segnali_alti']
P('\n== PRIMI 10')
P(T.sort_values('rango')[cols].head(10).round(2).to_string())
P('\n== ULTIMI 10')
P(T.sort_values('rango')[cols].tail(10).round(2).to_string())
vals = ['nil'] + CORE
P('\n== VALORI GREZZI PRIMI 10')
P(E.loc[T.sort_values('rango').index[:10], vals].round(1).to_string())
P('\n== VALORI GREZZI ULTIMI 10')
P(E.loc[T.sort_values('rango').index[-10:], vals].round(1).to_string())
P('\n== VALORI GREZZI DEL CENTRO E DI NIL CITATI')
nomi = ['Duomo', 'Brera', 'Guastalla', 'Magenta - S.Vittore', 'Sarpi', 'Lambrate - Ortica', 'Loreto - Casoretto - NoLo', 'Porta Garibaldi - Porta Nuova', 'Rogoredo - Santa Giulia',
        'Bicocca', 'Portello', 'Tre Torri', 'Maggiore - Musocco - Certosa', 'Farini']
sel = E[E.nil.isin(nomi)]
P(sel[['nil'] + CORE + ['rango', 'n_indicatori']].round(1).to_string())
P(T[T.nil.isin(nomi)][['nil', 'rango', 'rango_min_varianti', 'rango_max_varianti', 'tipologia', 'livello']].round(2).to_string())

P('\n== TIPOLOGIE')
P(json.dumps(tl, ensure_ascii=False, indent=1))
for t, g in T.groupby('tipologia'):
    P(f"-- {t} ({len(g)}; residenti 2024 {int(g.residenti_2024.sum())}): " + '; '.join(g.sort_values('rango').nil))

P('\n== ROBUSTEZZA: varianti')
P(rv.to_string())
P('\n== ROBUSTEZZA: leave-one-out')
P(loo.to_string())
P('\n== ROBUSTEZZA: stabilita del rango (T)')
P(f"NIL classificati {len(T)}. Primi 5 per rango di base: rango massimo raggiunto in tutte le varianti e LOO: "
  + '; '.join(f"{r.nil} (max {int(r.rango_max_varianti)})" for r in T.sort_values('rango').head(5).itertuples()))
P('Ultimi 5: ' + '; '.join(f"{r.nil} (min {int(r.rango_min_varianti)})" for r in T.sort_values('rango').tail(5).itertuples()))
w = T.rango_max_varianti - T.rango_min_varianti
P(f"Ampiezza media dell'intervallo di rango tra le varianti: {w.mean():.1f} posti; mediana {w.median():.1f}; max {w.max():.0f} ({T.loc[w.idxmax(),'nil']})")
P(f"Ampiezza media dell'intervallo 5-95% con pesi casuali: {(T.rango_p95 - T.rango_p5).mean():.1f} posti")
P(f"NIL che sono nei primi 10 in almeno il 50% delle 5.000 estrazioni a pesi casuali: " + '; '.join(T.loc[T.quota_top10_pesi_casuali >= 0.5].sort_values('rango').nil))
P(f"NIL che sono negli ultimi 10 in almeno il 50%: " + '; '.join(T.loc[T.quota_bottom10_pesi_casuali >= 0.5].sort_values('rango', ascending=False).nil))

P('\n== CONTESTO (non nell\'indice): Spearman con l\'indice di base')
ctx = ['pop_var', 'stranieri_var', 'eta_media_var', 'scuole_var', 'airbnb_cresc_100', 'livello']
X = E.join(T[['livello']].rename(columns={'livello': 'liv2'}), how='left')
c2 = {}
for c in ctx:
    s = E[[c, 'indice']].dropna() if c != 'livello' else E[['livello', 'indice']].dropna()
    c2[c] = (round(float(s.corr(method='spearman').iloc[0, 1]), 2), len(s))
P(str(c2))

P('\n== MUNICIPI (medie pesate con i residenti 2024, NIL classificati)')
P(mun.round(2).to_string())

P('\n== RESIDENTI PER TERZILE DI CAMBIAMENTO')
P(T.groupby('terzile_cambiamento').residenti_2024.sum().to_string())
P(f"totale residenti NIL classificati {int(T.residenti_2024.sum())} su {int(D.residenti_2024.sum())} (tutti i NIL)")

P('\n== SCARTO DAL LIVELLO (cambiamento piu alto/basso del previsto dal livello)')
sc = T.sort_values('scarto_dal_livello')
P(sc[['nil', 'rango', 'livello', 'scarto_dal_livello']].head(5).round(2).to_string())
P(sc[['nil', 'rango', 'livello', 'scarto_dal_livello']].tail(5).round(2).to_string())

open(os.path.join(OUT, 'riepilogo.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
