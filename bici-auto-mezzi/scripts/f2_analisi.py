"""Quote di vittoria per fascia di distanza, dalle coppie di f2_citta.py. Uso: python -I f2_analisi.py <ABS strand>
-> out/quote_vittorie.csv, out/tempi_mediani.csv, out/mappa_citta_08.png (e _12, _21)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import f2_parametri as P
from f2_motore import Motore
S = sys.argv[1]
Z = np.load(S + '/out/citta_coppie.npz'); cel = np.load(S + '/out/celle.npz')
org = Z['org']; ncell = len(cel['x'])
st = Z['straight_m_08']
mm = Motore(S, verbose=False); D = mm.dest(cel['lon'], cel['lat'])
zona = np.broadcast_to(D.zona[None, :], st.shape)
bands = [(0, 1000, '0-1 km'), (1000, 2000, '1-2 km'), (2000, 4000, '2-4 km'), (4000, 6000, '4-6 km'), (6000, 8000, '6-8 km'), (8000, 12000, '8-12 km'), (12000, 1e9, 'oltre 12 km')]
rows = []; med = []
bike = Z['bike_s_08']; walk = Z['walk_s_08']
for fa in P.BANDS:
    car = Z['car_s_' + fa]; cdr = Z['car_drive_s_' + fa]; tr = Z['transit_s_' + fa]; ac = Z['areac_' + fa] > 0
    T = np.stack([bike, car, tr], axis=-1).astype(float)
    T[~np.isfinite(T)] = np.inf
    valid = st > 0
    for lo, hi, nome in bands + [(0, 1e9, 'tutte')]:
        m = valid & (st >= lo) & (st < hi)
        if m.sum() == 0: continue
        t = T[m]; w = t.argmin(axis=1)
        bestwalk = (walk[m] < t.min(axis=1))
        shares = [np.mean(w == k) for k in range(3)]
        # vittoria "netta": vince con almeno 10% di vantaggio sul secondo
        srt = np.sort(t, axis=1); netta = (srt[:, 1] > srt[:, 0] * 1.1)
        rows.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': nome, 'coppie': int(m.sum()),
                     'bici_pct': round(100 * shares[0], 1), 'auto_pct': round(100 * shares[1], 1), 'mezzi_pct': round(100 * shares[2], 1),
                     'netta_10pct_pct': round(100 * netta.mean(), 1),
                     'a_piedi_batte_tutti_pct': round(100 * bestwalk.mean(), 1),
                     'auto_con_area_c_pct': round(100 * ac[m].mean(), 1),
                     'mezzi_non_raggiungibili_pct': round(100 * np.mean(~np.isfinite(T[m][:, 2])), 1)})
        fin = lambda a: float(np.nanmedian(np.where(np.isfinite(a), a, np.nan))) / 60
        med.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': nome, 'bici_min': round(fin(bike[m]), 1), 'auto_guida_min': round(fin(cdr[m]), 1),
                    'auto_porta_a_porta_min': round(fin(car[m]), 1), 'mezzi_min': round(fin(tr[m]), 1), 'a_piedi_min': round(fin(walk[m]), 1)})
    # mappa: per ogni cella destinazione, quota di origini in cui vince ciascun modo
    valid2 = valid & np.isfinite(bike)
    w = T.argmin(axis=-1)
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.4))
    for k, (nm, cm) in enumerate([('bici', 'Greens'), ('auto', 'Oranges'), ('mezzi pubblici', 'Blues')]):
        share = np.array([np.mean((w[:, j] == k)[valid[:, j]]) for j in range(ncell)])
        sc = axs[k].scatter(cel['x'], cel['y'], c=share, cmap=cm, s=12, marker='s', linewidths=0, vmin=0, vmax=1)
        axs[k].set_aspect('equal'); axs[k].axis('off'); axs[k].set_title('%s: quota di partenze (a caso) da cui arrivi prima' % nm, fontsize=10)
        fig.colorbar(sc, ax=axs[k], shrink=0.6)
    fig.suptitle('Milano, martedi ore %s:00, 300 partenze a caso verso ogni cella da 250 m' % fa)
    fig.savefig(S + '/out/mappa_citta_%s.png' % fa, dpi=100, bbox_inches='tight'); plt.close(fig)
pd.DataFrame(rows).to_csv(S + '/out/quote_vittorie.csv', index=False, sep=';', encoding='utf-8-sig')
pd.DataFrame(med).to_csv(S + '/out/tempi_mediani.csv', index=False, sep=';', encoding='utf-8-sig')
pd.set_option('display.width', 250)
print(pd.DataFrame(rows).to_string()); print(pd.DataFrame(med).to_string())
