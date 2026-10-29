"""Fase 3: dai risultati di f3_tutte.py (tutte le coppie cella -> cella, 3 fasce) scrive
 - out/quote_vittorie.csv, out/tempi_mediani.csv (tabelle generali)
 - ../docs/bici-auto-mezzi/data/*.json e o/*.bin.gz (dati della pagina; nessun tempo di Google)
Uso: python -I f3_esporta.py <ABS strand> [passo_griglia_celle=3]"""
import sys, os, json, glob, gzip, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import f2_parametri as P
from f3_origini import ORIGINI
S = sys.argv[1]; STEP = int(sys.argv[2]) if len(sys.argv) > 2 else 3
DOCS = S + '/../docs/bici-auto-mezzi/data'
os.makedirs(DOCS + '/o', exist_ok=True)
cel = np.load(S + '/out/celle.npz'); nd = len(cel['x'])
BANDS = P.BANDS
def carica(fn):
    z = np.load(fn, allow_pickle=True); return {k: z[k] for k in z.files}
def tmin(a):   # uint16 (secondi/2) -> minuti float, inf se 65535
    a = a.astype(np.float64) * 2 / 60; a[a >= 65534 * 2 / 60] = np.inf; return a
def calcola(Z):
    """-> dict con tempi (minuti, porta a porta) e esito per ogni origine/fascia/destinazione"""
    n = len(Z['idx']); park = Z['park'].astype(float)
    bike = tmin(Z['bike']); walk = tmin(Z['walk']); st = Z['straight'].astype(float)
    R = {'bike': bike, 'walk': walk, 'st': st, 'dlen': Z['dlen'], 'areac': Z['areac']}
    car = np.zeros((n, 3, nd)); trn = np.zeros((n, 3, nd)); cdr = np.zeros((n, 3, nd))
    for b in range(3):
        cdr[:, b] = tmin(Z['cdrive'][:, b]); car[:, b] = cdr[:, b] + (2 * P.CAR_WALK_S + park[None, :]) / 60; trn[:, b] = tmin(Z['tr'][:, b])
    R['car'] = car; R['tr'] = trn; R['cdr'] = cdr
    return R
def esito(R, same):
    """winner (0 bici,1 auto,2 mezzi,3 nessuno), netta, piedi -> array (n,3,nd)"""
    n = R['bike'].shape[0]
    T = np.stack([np.broadcast_to(R['bike'][:, None, :], (n, 3, nd)), R['car'], R['tr']], axis=-1)
    T = np.where(np.isfinite(T), T, np.inf)
    w = T.argmin(-1).astype(np.uint8); srt = np.sort(T, -1)
    netta = srt[..., 1] > srt[..., 0] * 1.1
    piedi = R['walk'][:, None, :] < srt[..., 0]
    w = np.where(same[:, None, :], 3, w).astype(np.uint8)
    return w, netta, piedi, T
# ---------- tutte le celle come origine
files = sorted(glob.glob(S + '/out/f3_celle_[0-9].npz'))
parts = [carica(f) for f in files]
idx = np.concatenate([p['idx'] for p in parts]); o = np.argsort(idx); idx = idx[o]
assert len(idx) == nd and (idx == np.arange(nd)).all(), 'mancano origini: %d di %d' % (len(idx), nd)
ALL = {}
for k in ('bike', 'walk', 'straight', 'cdrive', 'tr', 'areac', 'dlen'):
    ALL[k] = np.concatenate([p[k] for p in parts])[o]
ALL['park'] = parts[0]['park']; ALL['idx'] = idx
R = calcola(ALL); same = R['st'] < 1.0
W, NET, PIE, T = esito(R, same)
# ---------- tabelle generali
dbands = [(0, 1000, '0-1 km'), (1000, 2000, '1-2 km'), (2000, 4000, '2-4 km'), (4000, 6000, '4-6 km'), (6000, 8000, '6-8 km'), (8000, 12000, '8-12 km'), (12000, 1e9, 'oltre 12 km'), (0, 1e9, 'tutte')]
rows = []; med = []
for b, fa in enumerate(BANDS):
    for lo, hi, nome in dbands:
        mk = (~same) & (R['st'] >= lo) & (R['st'] < hi)
        if mk.sum() == 0: continue
        w = W[:, b][mk]
        rows.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': nome, 'coppie': int(mk.sum()),
                     'bici_pct': round(100 * np.mean(w == 0), 1), 'auto_pct': round(100 * np.mean(w == 1), 1), 'mezzi_pct': round(100 * np.mean(w == 2), 1),
                     'netta_10pct_pct': round(100 * np.mean(NET[:, b][mk]), 1), 'a_piedi_batte_tutti_pct': round(100 * np.mean(PIE[:, b][mk]), 1),
                     'auto_con_area_c_pct': round(100 * np.mean(R['areac'][:, b][mk]), 1),
                     'mezzi_non_raggiungibili_pct': round(100 * np.mean(~np.isfinite(R['tr'][:, b][mk])), 1)})
        def fin(a):
            a = a[np.isfinite(a)]
            return round(float(np.median(a)), 1) if a.size else None
        med.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': nome, 'bici_min': fin(R['bike'][mk]), 'auto_guida_min': fin(R['cdr'][:, b][mk]),
                    'auto_porta_a_porta_min': fin(R['car'][:, b][mk]), 'mezzi_min': fin(R['tr'][:, b][mk]), 'a_piedi_min': fin(R['walk'][mk])})
# ---------- (verifica mezzi) stesse quote, ma solo tra coppie con una fermata a piedi (<= 800 m) a entrambe le estremita
serv_o = np.isfinite(R['tr'][:, 0, :]).any(axis=1)      # la cella di partenza ha almeno una fermata raggiungibile
serv_d = np.isfinite(R['tr'][:, 0, :]).any(axis=0)      # la cella di arrivo ha almeno una fermata raggiungibile
rows_s = []
for b, fa in enumerate(BANDS):
    for lo, hi, nome in dbands:
        mk = (~same) & (R['st'] >= lo) & (R['st'] < hi) & serv_o[:, None] & serv_d[None, :]
        if mk.sum() == 0: continue
        w = W[:, b][mk]
        rows_s.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': nome, 'coppie': int(mk.sum()),
                       'bici_pct': round(100 * np.mean(w == 0), 1), 'auto_pct': round(100 * np.mean(w == 1), 1), 'mezzi_pct': round(100 * np.mean(w == 2), 1),
                       'netta_10pct_pct': round(100 * np.mean(NET[:, b][mk]), 1)})
celle_info = {'totale': int(nd), 'senza_fermata': int((~serv_d).sum()), 'senza_fermata_pct': round(100 * float((~serv_d).mean()), 1),
              'coppie_servite_pct': round(100 * float(((~same) & serv_o[:, None] & serv_d[None, :]).sum() / (~same).sum()), 1)}
print('celle', celle_info)
pd.DataFrame(rows).to_csv(S + '/out/quote_vittorie.csv', index=False, sep=';', encoding='utf-8-sig')
pd.DataFrame(med).to_csv(S + '/out/tempi_mediani.csv', index=False, sep=';', encoding='utf-8-sig')
# ---------- sensibilita: bici piu lenta (f3_sens.py), le altre colonne restano uguali
sens = {}
sf = sorted(glob.glob(S + '/out/f3_sens_[0-9].npz'))
if len(sf) == 6:
    ps = [carica(f) for f in sf]; ii = np.concatenate([p['idx'] for p in ps]); oo = np.argsort(ii)
    SB = np.concatenate([p['bike'] for p in ps])[oo]
    for si, nome in enumerate(['media', 'lenta']):
        R2 = dict(R); R2['bike'] = tmin(SB[:, si]); W2, N2, P2, _ = esito(R2, same); rr = []
        for b, fa in enumerate(BANDS):
            for lo, hi, dn in dbands:
                mk = (~same) & (R['st'] >= lo) & (R['st'] < hi); w = W2[:, b][mk]
                rr.append({'fascia_oraria': fa + ':00', 'distanza_in_linea_retta': dn, 'coppie': int(mk.sum()), 'bici_pct': round(100 * np.mean(w == 0), 1),
                           'auto_pct': round(100 * np.mean(w == 1), 1), 'mezzi_pct': round(100 * np.mean(w == 2), 1), 'netta_10pct_pct': round(100 * np.mean(N2[:, b][mk]), 1),
                           'mezzi_non_raggiungibili_pct': round(100 * np.mean(~np.isfinite(R['tr'][:, b][mk])), 1)})
        sens[nome] = rr
        print('sensibilita', nome, [r for r in rr if r['distanza_in_linea_retta'] == 'tutte'])
        del W2, N2, P2, R2
json.dump({'quote': rows, 'quote_servite': rows_s, 'celle': celle_info, 'tempi': med, 'sens': sens, 'sens_param': {'media': 'bici 15 km/h su strada, 17 su ciclabile, semaforo 8 s', 'lenta': 'bici 13 km/h su strada, 15 su ciclabile, semaforo 15 s (le ipotesi iniziali, prima della taratura)'}}, open(DOCS + '/quote.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(pd.DataFrame(rows).to_string())
# ---------- mappa generale: per ogni cella di partenza, quota di destinazioni in cui vince ciascun modo
city = {}
for b, fa in enumerate(BANDS):
    valid = ~same
    sh = np.stack([((W[:, b] == k) & valid).sum(1) / valid.sum(1) for k in range(3)], axis=1)
    city['h' + fa] = np.round(100 * sh).astype(int).ravel().tolist()
# ---------- celle
zona = np.array(['periferia', 'semicentro', 'areac'])
zc = parts[0]['zona']
zcode = np.select([zc == 'areac', zc == 'semicentro'], [2, 1], 0)
json.dump({'lon': np.round(cel['lon'], 5).tolist(), 'lat': np.round(cel['lat'], 5).tolist(), 'z': zcode.tolist(), 'm': P.CELL_M},
          open(DOCS + '/celle.json', 'w'), separators=(',', ':'))
json.dump(city, open(DOCS + '/citta.json', 'w'), separators=(',', ':'))
# ---------- origini della pagina: con nome + griglia (1 ogni STEP celle per lato)
xs = cel['x']; ys = cel['y']
ix = np.round((xs - xs.min()) / P.CELL_M).astype(int); iy = np.round((ys - ys.min()) / P.CELL_M).astype(int)
grid = np.where((ix % STEP == 0) & (iy % STEP == 0))[0]
N = carica(S + '/out/f3_nomi.npz'); RN = calcola(N); sameN = RN['st'] < 150
WN, NETN, PIEN, TN = esito(RN, sameN)
def pacchetto(w, net, pie, Tt, ac):
    """Tt: (3 fasce, nd, 3 modi) minuti -> bytes: per fascia bici, auto, mezzi (uint8 minuti, 255 = no), flags"""
    out = bytearray()
    for b in range(3):
        for k in range(3):
            v = Tt[b][:, k]; q = np.where(np.isfinite(v), np.minimum(np.round(v), 254), 255).astype(np.uint8); out += q.tobytes()
        fl = (w[b] & 3) | (net[b].astype(np.uint8) << 2) | (ac[b].astype(np.uint8) << 3) | (pie[b].astype(np.uint8) << 4)
        out += fl.astype(np.uint8).tobytes()
    return gzip.compress(bytes(out), 9)
tot = 0
for f in glob.glob(DOCS + '/o/*'): os.remove(f)
for j, (nome, lo, la) in enumerate(ORIGINI):
    bts = pacchetto(WN[j], NETN[j], PIEN[j], TN[j], RN['areac'][j]); tot += len(bts)
    open(DOCS + '/o/n%d.bin.gz' % j, 'wb').write(bts)
for i in grid:
    bts = pacchetto(W[i], NET[i], PIE[i], T[i], R['areac'][i]); tot += len(bts)
    open(DOCS + '/o/c%d.bin.gz' % i, 'wb').write(bts)
json.dump({'nomi': [[n, lo, la] for n, lo, la in ORIGINI], 'grid': grid.tolist(), 'passo': STEP}, open(DOCS + '/origini.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('origini con nome', len(ORIGINI), 'griglia', len(grid), 'byte origini', tot)
# ---------- taratura (solo percentuali)
J = json.load(open(S + '/out/f3_taratura.json'))
json.dump({k: J[k] for k in ('parametri', 'prima', 'errori', 'n_tragitti', 'n_taratura', 'n_controllo', 'n_per_ora', 'n_con_google')}, open(DOCS + '/taratura.json', 'w'), ensure_ascii=False, separators=(',', ':'))
gi = json.load(open(S + '/out/gtfs_info.json')); json.dump(gi, open(DOCS + '/gtfs.json', 'w'), ensure_ascii=False)
print('fatto')
