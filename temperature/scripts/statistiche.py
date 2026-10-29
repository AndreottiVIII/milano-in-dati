"""Statistiche di temperatura Milano Brera, calcolate SOLO da serie/serie_unica.csv.

uso: python -I statistiche.py SERIE_CSV SPLICE_JSON OUTDIR
  SERIE_CSV    temperature/serie/serie_unica.csv   (date,tmin,tmax,tmean,fonte,qflag)
  SPLICE_JSON  temperature/splice.json             (solo per scrivere stato e segmenti nei metadati)
  OUTDIR       docs/temperature/data               (meta, annuale, mensile, clima, giorni, records, gelate .json,
                                                     giorni/AAAA0.json per decennio, giorni/ordinati/MM.json)

Licenza: dal 2026-10-29 il sito pubblica anche la serie giornaliera completa (giorni/AAAA0.json), con le citazioni delle
fonti (ECA&D: uso non commerciale per ricerca e istruzione; sito non commerciale). Vedi la sezione Fonti della pagina.
Nei campi 'riga' c'e' il numero di riga (da 1, intestazione = riga 1) in serie_unica.csv (file locale della serie).

Soglie (documentate anche in meta.json):
  anno valido           >= 330 giorni con tmin e tmax (circa 90%)
  mese valido           >= 80% dei giorni del mese
  anno valido per gelate >= 90% dei giorni con tmin tra 1 gen-30 apr e tra 1 ott-31 dic, oltre ad anno valido
  tmean giornaliera     (tmin+tmax)/2; tmean annuale = media delle tmean giornaliere; tmin/tmax annuali = medie giornaliere
  classifiche (anni, mesi, estati, inverni): solo periodi validi
  ultimi 20 / 5 anni    gli ultimi 20 / 5 anni VALIDI (anno corrente parziale escluso)
"""
import sys, os, json, math, calendar
import numpy as np
import pandas as pd

csv_path, splice_path, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
splice = json.load(open(splice_path, encoding='utf-8-sig'))

MIN_GIORNI_ANNO = 330
MIN_FRAZ_MESE = 0.80
DATA_SCARICO = '2026-10-29'
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre',
        'novembre', 'dicembre']

df = pd.read_csv(csv_path, parse_dates=['date'], index_col='date', dtype={'qflag': str, 'fonte': str})
df['qflag'] = df.qflag.fillna('')
df['riga'] = np.arange(len(df)) + 2
df['y'] = df.index.year
df['m'] = df.index.month
df['d'] = df.index.day
ULT = df.index.max()
ANNO_CORR = int(ULT.year)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o is None or math.isnan(o)) else round(float(o), 2)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.strftime('%Y-%m-%d')
    return o


def salva(nome, obj):
    p = os.path.join(outdir, nome)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(clean(obj), f, ensure_ascii=False, separators=(',', ':'))
    print(f'{nome}: {os.path.getsize(p)/1024:.1f} KB')


def fmt(x, n=1):
    return f'{x:.{n}f}'.replace('.', ',')


def dstr(ts):
    return ts.strftime('%Y-%m-%d')


def giorno(ts, **extra):
    r = df.loc[ts]
    o = {'data': dstr(ts), 'tmin': r.tmin, 'tmax': r.tmax, 'fonte': r.fonte, 'riga': int(r.riga), 'qflag': r.qflag}
    o.update(extra)
    return o


def ols(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    if n < 5:
        return None
    xm = x.mean(); sxx = ((x - xm) ** 2).sum()
    b = ((x - xm) * (y - y.mean())).sum() / sxx
    a = y.mean() - b * xm
    res = y - (a + b * x)
    se = math.sqrt((res ** 2).sum() / (n - 2) / sxx)
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return {'pend_secolo': b * 100, 'se_secolo': se * 100, 'r2': r2, 'n': n, 'da': int(x.min()), 'a': int(x.max())}


# ------------------------------------------------------------------ ANNUALE
g = df.groupby('y')
ann = pd.DataFrame({
    'n': g.tmean.count(), 'n_tmin': g.tmin.count(), 'n_tmax': g.tmax.count(),
    'tmedia': g.tmean.mean(), 'tmin_media': g.tmin.mean(), 'tmax_media': g.tmax.mean(),
    'gg_gelo': (df.tmin < 0).groupby(df.y).sum(), 'gg_caldi': (df.tmax >= 30).groupby(df.y).sum(),
    'notti_tropicali': (df.tmin >= 20).groupby(df.y).sum(), 'gg_35': (df.tmax >= 35).groupby(df.y).sum(),
})
ann['max_ass'] = g.tmax.max(); ann['max_data'] = g.tmax.idxmax()
ann['min_ass'] = g.tmin.min(); ann['min_data'] = g.tmin.idxmin()
ann['fonti'] = g.fonte.agg(lambda s: '+'.join(sorted(set(s))))
ann['ok'] = ann.n >= MIN_GIORNI_ANNO
ann['in_corso'] = ann.index == ANNO_CORR     # anno in corso: non valido per soglia, ma mostrato e confrontato 'finora'
V = ann[ann.ok]                       # anni validi
ULT_VALIDO = int(V.index.max())
L20 = (ULT_VALIDO - 19, ULT_VALIDO)
L5 = (ULT_VALIDO - 4, ULT_VALIDO)

righe_ann = []
for y, r in ann.iterrows():
    righe_ann.append({
        'anno': int(y), 'ok': bool(r.ok), 'n': int(r.n), 'n_tmin': int(r.n_tmin), 'n_tmax': int(r.n_tmax),
        'tmedia': r.tmedia, 'tmin_media': r.tmin_media, 'tmax_media': r.tmax_media,
        'max_ass': r.max_ass, 'max_data': r.max_data, 'min_ass': r.min_ass, 'min_data': r.min_data,
        'gg_gelo': int(r.gg_gelo), 'gg_caldi': int(r.gg_caldi), 'notti_tropicali': int(r.notti_tropicali),
        'gg_35': int(r.gg_35), 'fonti': r.fonti, 'in_corso': bool(r.in_corso)})
salva('annuale.json', {'campi_nota': 'un oggetto per anno; ok=false: anno escluso dalle classifiche (meno di '
                       f'{MIN_GIORNI_ANNO} giorni con tmin e tmax); i conteggi di giorni di un anno non valido sono un minimo. '
                       f'in_corso=true: anno in corso, dati fino al {dstr(ULT)}; per confrontarlo vedi finora.json',
                       'anni': righe_ann})

# ------------------------------------------------------------------ MENSILE
gm = df.groupby(['y', 'm'])
men = pd.DataFrame({'n': gm.tmean.count(), 'tmedia': gm.tmean.mean(), 'tmin': gm.tmin.mean(), 'tmax': gm.tmax.mean()})
men['dim'] = [calendar.monthrange(y, m)[1] for y, m in men.index]
men['ok'] = men.n >= MIN_FRAZ_MESE * men.dim
men = men.reset_index()
salva('mensile.json', {
    'campi': ['anno', 'mese', 'tmedia', 'tmin', 'tmax', 'n', 'ok'],
    'nota': f'medie mensili delle medie/minime/massime giornaliere; ok=1 se almeno {int(MIN_FRAZ_MESE*100)}% dei giorni del mese',
    'righe': [[int(r.y), int(r.m), r.tmedia, r.tmin, r.tmax, int(r.n), int(r.ok)] for r in men.itertuples()]})
MV = men[men.ok]

# ------------------------------------------------------------------ CLIMA: mensile per periodo, decenni, normali, tendenze
periodi = {'serie_intera': (0, 9999), '1961_1990': (1961, 1990), '1991_2020': (1991, 2020),
           'ultimi_20': L20}
clima_mensile = []
for m in range(1, 13):
    sub = MV[MV.m == m]
    riga = {'mese': m, 'nome': MESI[m - 1]}
    for k, (a, b) in periodi.items():
        s = sub[(sub.y >= a) & (sub.y <= b)]
        riga[k] = {'tmedia': s.tmedia.mean(), 'tmin': s.tmin.mean(), 'tmax': s.tmax.mean(), 'n_anni': int(len(s))}
    cal = sub.loc[sub.tmedia.idxmax()]; fre = sub.loc[sub.tmedia.idxmin()]
    riga['mese_piu_caldo'] = {'anno': int(cal.y), 'tmedia': cal.tmedia}
    riga['mese_piu_freddo'] = {'anno': int(fre.y), 'tmedia': fre.tmedia}
    dm = df[df.m == m]
    riga['record_max'] = giorno(dm.tmax.idxmax()); riga['record_max']['valore'] = dm.tmax.max()
    riga['record_min'] = giorno(dm.tmin.idxmin()); riga['record_min']['valore'] = dm.tmin.min()
    clima_mensile.append(riga)

decenni = []
for dec in range(int(ann.index.min()) // 10 * 10, ANNO_CORR + 1, 10):
    s = V[(V.index >= dec) & (V.index <= dec + 9)]
    if len(s) == 0:
        continue
    decenni.append({'decennio': dec, 'n_anni': int(len(s)), 'tmedia': s.tmedia.mean(), 'tmin_media': s.tmin_media.mean(),
                    'tmax_media': s.tmax_media.mean(), 'gg_gelo': s.gg_gelo.mean(), 'gg_caldi': s.gg_caldi.mean(),
                    'notti_tropicali': s.notti_tropicali.mean(), 'gg_35': s.gg_35.mean()})

normali = []
for nome, (a, b) in [('1961-1990', (1961, 1990)), ('1991-2020', (1991, 2020)), ('1981-2010', (1981, 2010))]:
    s = V[(V.index >= a) & (V.index <= b)]
    normali.append({'periodo': nome, 'n_anni': int(len(s)), 'anni_attesi': b - a + 1, 'tmedia': s.tmedia.mean(),
                    'tmin_media': s.tmin_media.mean(), 'tmax_media': s.tmax_media.mean(),
                    'gg_gelo': s.gg_gelo.mean(), 'gg_caldi': s.gg_caldi.mean(), 'notti_tropicali': s.notti_tropicali.mean()})

tendenze = []
for var in ['tmedia', 'tmin_media', 'tmax_media']:
    for start in [None, 1900, 1950, 1980]:
        s = V if start is None else V[V.index >= start]
        o = ols(s.index.values, s[var].values)
        if o:
            o.update({'variabile': var, 'dal': start if start else int(V.index.min())})
            tendenze.append(o)

salva('clima.json', {
    'clima_mensile': clima_mensile, 'decenni': decenni, 'normali': normali, 'tendenze': tendenze,
    'nota': 'clima_mensile: medie dei soli mesi validi (>=80% dei giorni). decenni/normali/tendenze: solo anni validi. '
            'tendenze: regressione lineare ai minimi quadrati sulle medie annue, pend_secolo in C per 100 anni, '
            'se_secolo errore standard (non corretto per autocorrelazione), r2 quota di varianza spiegata.',
    'periodi': {'ultimi_20': list(L20), 'ultimi_5': list(L5)}})

# ------------------------------------------------------------------ GIORNO PER GIORNO
cal = df[~((df.m == 2) & (df.d == 29))].copy()   # 365 giorni; il 29 feb si tratta a parte
chiave = df.groupby(['m', 'd'])
giorni = []
anni_in = lambda a, b: (df.y >= a) & (df.y <= b)
sel20, sel5, sel9120 = anni_in(*L20), anni_in(*L5), anni_in(1991, 2020)
mm_all = chiave[['tmax', 'tmin', 'tmean']].mean()
mm20 = df[sel20].groupby(['m', 'd'])[['tmax', 'tmin', 'tmean']].mean()
mm5 = df[sel5].groupby(['m', 'd'])[['tmax', 'tmin', 'tmean']].mean()
mm9120 = df[sel9120].groupby(['m', 'd'])[['tmax', 'tmin', 'tmean']].mean()
mm6190 = df[anni_in(1961, 1990)].groupby(['m', 'd'])[['tmax', 'tmin', 'tmean']].mean()
ntx = chiave.tmax.count(); ntn = chiave.tmin.count()
cur = df[df.y == ANNO_CORR].set_index(['m', 'd'])
nn = chiave.tmean.count()
txmax = chiave.tmax.idxmax(); tnmin = chiave.tmin.idxmin()
for (m, d) in mm_all.index:
    a = df.loc[txmax[(m, d)]]; b = df.loc[tnmin[(m, d)]]
    row = [m, d, a.tmax, int(a.y), a.fonte, int(a.riga), b.tmin, int(b.y), b.fonte, int(b.riga),
           mm_all.loc[(m, d), 'tmax'], mm_all.loc[(m, d), 'tmin'], mm_all.loc[(m, d), 'tmean'],
           mm20.loc[(m, d), 'tmax'], mm20.loc[(m, d), 'tmin'], mm20.loc[(m, d), 'tmean'],
           mm5.loc[(m, d), 'tmax'], mm5.loc[(m, d), 'tmin'], mm5.loc[(m, d), 'tmean'], int(nn[(m, d)]),
           cur.tmax.get((m, d), np.nan), cur.tmin.get((m, d), np.nan),
           mm9120.loc[(m, d), 'tmean'],
           mm6190.loc[(m, d), 'tmax'], mm6190.loc[(m, d), 'tmin'], mm6190.loc[(m, d), 'tmean'],
           mm9120.loc[(m, d), 'tmax'], mm9120.loc[(m, d), 'tmin'], int(ntx[(m, d)]), int(ntn[(m, d)])]
    giorni.append(row)
salva('giorni.json', {
    'campi': ['m', 'd', 'tx_rec', 'tx_rec_anno', 'tx_rec_fonte', 'tx_rec_riga', 'tn_rec', 'tn_rec_anno', 'tn_rec_fonte',
              'tn_rec_riga', 'tx_med', 'tn_med', 'tm_med', 'tx_20', 'tn_20', 'tm_20', 'tx_5', 'tn_5', 'tm_5', 'n_anni',
              'tx_att', 'tn_att', 'tm_9120', 'tx_6190', 'tn_6190', 'tm_6190', 'tx_9120', 'tn_9120', 'n_tx', 'n_tn'],
    'nota': 'tx_rec = massima piu alta mai registrata in quel giorno del calendario (a parita il primo anno); tn_rec = minima piu '
            'bassa. *_med = media su tutta la serie; *_20 e *_5 = media sugli ultimi 20 / 5 anni validi; tm_9120 = media '
            f'1991-2020 (tx_9120, tn_9120 per massima e minima); *_6190 = media 1961-1990; n_tx / n_tn = anni con massima / minima in quel giorno. *_att = valore dell\'anno {ANNO_CORR} (ARPA 5897); n_anni = anni con dato in tutta la serie.',
    'anno_attuale': ANNO_CORR, 'ultimi_20': list(L20), 'ultimi_5': list(L5), 'righe': giorni})

# ------------------------------------------------------------------ SERIE GIORNALIERA PUBBLICATA (per decennio) + ordinati per giorno del calendario
import shutil
FONTI_COD = ['MAUGERI', 'LINATE', 'BRERA_H', 'VICINE_ARPA']
nuove_fonti = sorted(set(df.fonte) - set(FONTI_COD))
if nuove_fonti:
    raise SystemExit(f'fonte non prevista in serie_unica.csv: {nuove_fonti}; aggiornare FONTI_COD qui e FONTE_NOMI nella pagina')


def num(x):
    """numero compatto per il JSON: None se mancante, intero se senza decimali, 2 decimali al massimo"""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    x = round(float(x), 2)
    return int(x) if x == int(x) else x


gdir = os.path.join(outdir, 'giorni')
shutil.rmtree(gdir, ignore_errors=True)
os.makedirs(os.path.join(gdir, 'ordinati'))
tot = 0
for dec in range(int(df.y.min()) // 10 * 10, ANNO_CORR + 1, 10):
    sub = df[(df.y >= dec) & (df.y <= dec + 9)]
    if not len(sub):
        continue
    t0, t1 = sub.index.min(), sub.index.max()
    idx = pd.date_range(t0, t1)
    sub = sub.reindex(idx)
    righe, qf = [], {}
    for i, r in enumerate(sub.itertuples()):
        if pd.isna(r.fonte):
            righe.append(None)          # giorno assente dalla serie
            continue
        righe.append([num(r.tmin), num(r.tmax), num(r.tmean), FONTI_COD.index(r.fonte)])
        if r.qflag:
            qf[i] = r.qflag
    p = os.path.join(gdir, f'{dec}.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'da': dstr(t0), 'a': dstr(t1), 'fonti': FONTI_COD, 'campi': ['tmin', 'tmax', 'tmean', 'fonte'],
                   'nota': 'r[i] = giorno da+i: [tmin, tmax, tmean, indice in fonti]; null = giorno assente dalla serie; '
                           'valori null dentro la riga = misura mancante; qflag[i] = flag NOAA GHCN-D (primo carattere minima, secondo massima; '
                           'I = incoerenza interna, N = fuori norma): valore da verificare.',
                   'qflag': qf, 'r': righe}, f, ensure_ascii=False, separators=(',', ':'))
    tot += os.path.getsize(p)
print(f'giorni/AAAA0.json: {len(os.listdir(gdir)) - 1} file, {tot/1024:.0f} KB')

# valori ordinati per giorno del calendario (per la posizione in classifica di un giorno), un file per mese
tot2 = 0
for m in range(1, 13):
    out = {}
    for d in range(1, calendar.monthrange(2000, m)[1] + 1):
        sub = df[(df.m == m) & (df.d == d)]
        out[str(d)] = {k: [num(v) for v in sorted(sub[c].dropna())] for k, c in (('tn', 'tmin'), ('tx', 'tmax'), ('tm', 'tmean'))}
    p = os.path.join(gdir, 'ordinati', f'{m:02d}.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'nota': 'per ogni giorno del mese: valori di tmin (tn), tmax (tx), tmean (tm) di tutti gli anni con dato, in ordine crescente',
                   'g': out}, f, separators=(',', ':'))
    tot2 += os.path.getsize(p)
print(f'giorni/ordinati/MM.json: 12 file, {tot2/1024:.0f} KB')

# ------------------------------------------------------------------ ANNO IN CORSO "FINORA": stesso periodo (1 gen - ultimo giorno) di ogni anno
mdc = (int(ULT.month), int(ULT.day))
inper = (df.m < mdc[0]) | ((df.m == mdc[0]) & (df.d <= mdc[1]))
# stessi giorni del calendario per tutti gli anni: solo quelli in cui l'anno in corso ha minima e massima
# (cosi un mese mancante, per esempio marzo 2026, non sposta il confronto)
cc = df[(df.y == ANNO_CORR) & inper & df.tmin.notna() & df.tmax.notna()]
giorni_ok = set(zip(cc.m, cc.d))
n_periodo = int(((pd.Timestamp(year=ANNO_CORR, month=mdc[0], day=mdc[1]) - pd.Timestamp(year=ANNO_CORR, month=1, day=1)).days) + 1)
mancano = pd.date_range(f'{ANNO_CORR}-01-01', ULT).difference(cc.index)
mesi_manc = {}
for t in mancano:
    mesi_manc[t.month] = mesi_manc.get(t.month, 0) + 1
dp = df[inper & pd.Series(list(zip(df.m, df.d)), index=df.index).isin(giorni_ok)]
gp = dp.groupby('y')
fin = pd.DataFrame({'n_tmin': gp.tmin.count(), 'n_tmax': gp.tmax.count(), 'tmedia': gp.tmean.mean(), 'tmin_media': gp.tmin.mean(),
                    'tmax_media': gp.tmax.mean(), 'gg_gelo': (dp.tmin < 0).groupby(dp.y).sum(), 'gg_caldi': (dp.tmax >= 30).groupby(dp.y).sum(),
                    'notti_tropicali': (dp.tmin >= 20).groupby(dp.y).sum(), 'gg_35': (dp.tmax >= 35).groupby(dp.y).sum()})
fin['atteso'] = len(giorni_ok)
fin['ok'] = (fin.n_tmin >= 0.9 * fin.atteso) & (fin.n_tmax >= 0.9 * fin.atteso)
FV = fin[fin.ok]
nome_f = {'tmedia': ('temperatura media', 1), 'tmin_media': ('media delle minime', 1), 'tmax_media': ('media delle massime', 1),
          'gg_gelo': ('giorni di gelo (minima sotto 0 °C)', 0), 'gg_caldi': ('giorni con massima da 30 °C', 0),
          'notti_tropicali': ('notti tropicali (minima da 20 °C)', 0), 'gg_35': ('giorni con massima da 35 °C', 0)}
righe_f = []
if ANNO_CORR in FV.index:
    altri = FV[FV.index != ANNO_CORR]
    for k, (nome, dec) in nome_f.items():
        v = float(FV.at[ANNO_CORR, k])
        sp = FV[k]
        righe_f.append({'var': k, 'nome': nome, 'decimali': dec, 'valore': v, 'media_altri': altri[k].mean(),
                        'media_9120': FV[(FV.index >= 1991) & (FV.index <= 2020)][k].mean(),
                        'rank_alto': int((sp > v).sum()) + 1, 'rank_basso': int((sp < v).sum()) + 1, 'n': int(len(sp)),
                        'pari': int((sp == v).sum()) - 1,
                        'max': {'anno': int(altri[k].idxmax()), 'valore': altri[k].max()},
                        'min': {'anno': int(altri[k].idxmin()), 'valore': altri[k].min()}})
tm_f = FV.tmedia.sort_values(kind='stable')
salva('finora.json', {
    'anno': ANNO_CORR, 'da': '01-01', 'giorni_confronto': len(giorni_ok), 'giorni_periodo': n_periodo,
    'giorni_mancanti_anno_corso': int(len(mancano)), 'mesi_con_giorni_mancanti': {str(k): v for k, v in mesi_manc.items()}, 'a': f'{mdc[0]:02d}-{mdc[1]:02d}', 'ultimo_giorno': ULT,
    'nota': f'Confronto dell anno in corso ({ANNO_CORR}) con lo stesso periodo (1 gennaio - {mdc[1]} {MESI[mdc[0]-1]}) di ogni altro anno, '
            f'ma solo sui {len(giorni_ok)} giorni del calendario (su {n_periodo}) in cui il {ANNO_CORR} ha minima e massima: i giorni mancanti sono esclusi per tutti gli anni. '
            'Entrano gli anni con almeno il 90% dei giorni del periodo con minima e con massima (anno in corso incluso). '
            'rank_alto = posizione partendo dal valore piu alto (1 = il piu alto), rank_basso partendo dal piu basso; pari = altri anni con lo stesso valore. '
            'Anche i conteggi di giorni riguardano solo questi giorni. Media: media delle medie giornaliere.',
    'anni_esclusi': [int(y) for y in fin.index[~fin.ok]], 'n_anni': int(len(FV)), 'righe': righe_f,
    'classifica_tmedia_caldi': [{'anno': int(y), 'tmedia': v} for y, v in tm_f[::-1].head(10).items()],
    'classifica_tmedia_freddi': [{'anno': int(y), 'tmedia': v} for y, v in tm_f.head(10).items()]})

# ------------------------------------------------------------------ RECORD: giorni estremi
def top(serie, n=10, asc=False, extra=None):
    s = serie.dropna().sort_values(ascending=asc, kind='stable').head(n)
    out = []
    for ts, v in s.items():
        o = giorno(ts, valore=v)
        out.append(o)
    return out

df['escursione'] = df.tmax - df.tmin
giorni_estremi = {
    'tmax_alta': top(df.tmax), 'tmin_bassa': top(df.tmin, asc=True), 'tmin_alta': top(df.tmin),
    'tmax_bassa': top(df.tmax, asc=True), 'tmedia_alta': top(df.tmean), 'tmedia_bassa': top(df.tmean, asc=True),
    'escursione_max': top(df.escursione)}

# anni, mesi, stagioni
anni_caldi = [{'anno': int(y), 'tmedia': r.tmedia, 'n': int(r.n)} for y, r in V.sort_values('tmedia', ascending=False, kind='stable').head(10).iterrows()]
anni_freddi = [{'anno': int(y), 'tmedia': r.tmedia, 'n': int(r.n)} for y, r in V.sort_values('tmedia', kind='stable').head(10).iterrows()]
mesi_caldi = [{'anno': int(r.y), 'mese': int(r.m), 'tmedia': r.tmedia} for r in MV.sort_values('tmedia', ascending=False, kind='stable').head(10).itertuples()]
mesi_freddi = [{'anno': int(r.y), 'mese': int(r.m), 'tmedia': r.tmedia} for r in MV.sort_values('tmedia', kind='stable').head(10).itertuples()]

mi = men.set_index(['y', 'm'])
est, inv = [], []
for y in range(int(men.y.min()), ANNO_CORR + 1):
    try:
        t = [mi.loc[(y, k)] for k in (6, 7, 8)]
        if all(x.ok for x in t):
            est.append({'anno': y, 'tmedia': float(np.mean([x.tmedia for x in t]))})
    except KeyError:
        pass
    try:
        t = [mi.loc[(y - 1, 12)], mi.loc[(y, 1)], mi.loc[(y, 2)]]
        if all(x.ok for x in t):
            inv.append({'anno': y, 'tmedia': float(np.mean([x.tmedia for x in t]))})
    except KeyError:
        pass
est_s = sorted(est, key=lambda o: o['tmedia']); inv_s = sorted(inv, key=lambda o: o['tmedia'])

# serie di eventi consecutivi (un giorno mancante interrompe la serie)
full = pd.date_range(df.index.min(), df.index.max())


def serie_eventi(cond, valcol, n=10):
    c = cond.reindex(full).fillna(False).to_numpy(bool)
    dd = np.diff(np.concatenate(([0], c.astype(np.int8), [0])))
    st = np.where(dd == 1)[0]; en = np.where(dd == -1)[0] - 1
    runs = []
    for s, e in zip(st, en):
        a, b = full[s], full[e]
        sub = df.loc[a:b]
        runs.append({'inizio': dstr(a), 'fine': dstr(b), 'giorni': int(e - s + 1), 'media': sub[valcol].mean(),
                     'fonti': '+'.join(sorted(set(sub.fonte))), 'riga_inizio': int(df.at[a, 'riga']), 'riga_fine': int(df.at[b, 'riga'])})
    runs.sort(key=lambda o: (-o['giorni'], o['inizio']))
    return runs[:n], len(runs)


caldo, n_caldo = serie_eventi(df.tmax >= 30, 'tmax')
tropic, n_trop = serie_eventi(df.tmin >= 20, 'tmin', 5)
gelo, n_gelo = serie_eventi(df.tmin < 0, 'tmin')
ghiaccio, n_ghi = serie_eventi(df.tmax < 0, 'tmax', 5)

records = {
    'giorni_estremi': giorni_estremi, 'anni_caldi': anni_caldi, 'anni_freddi': anni_freddi, 'mesi_caldi': mesi_caldi,
    'mesi_freddi': mesi_freddi, 'estati_calde': est_s[::-1][:5], 'estati_fredde': est_s[:5],
    'inverni_caldi': inv_s[::-1][:5], 'inverni_freddi': inv_s[:5],
    'serie_caldo_tmax30': caldo, 'serie_notti_tropicali': tropic, 'serie_gelo_tmin0': gelo, 'serie_ghiaccio_tmax0': ghiaccio,
    'n_serie': {'caldo_tmax30': n_caldo, 'notti_tropicali': n_trop, 'gelo_tmin0': n_gelo, 'ghiaccio_tmax0': n_ghi},
    'nota': 'Una serie e una successione di giorni consecutivi che rispettano la soglia; un giorno mancante interrompe la serie. '
            'media = media di tmax (caldo, ghiaccio) o di tmin (notti tropicali, gelo) nei giorni della serie.'}

# ------------------------------------------------------------------ GELATE per anno
gel = []
for y in ann.index:
    if not ann.at[y, 'ok']:
        continue
    d = df[df.y == y]
    n1 = d[(d.m <= 4)].tmin.count(); n2 = d[(d.m >= 10)].tmin.count()
    if n1 < 0.9 * (120 + calendar.isleap(y)) or n2 < 0.9 * 92:
        continue
    fr = d[d.tmin < 0]
    spr = fr[fr.m <= 7]; aut = fr[fr.m >= 8]
    o = {'anno': int(y), 'ultima': None, 'prima': None}
    if len(spr):
        t = spr.index.max(); o.update({'ultima': dstr(t), 'ultima_doy': int(t.day_of_year), 'ultima_fonte': spr.at[t, 'fonte'], 'ultima_riga': int(spr.at[t, 'riga'])})
    if len(aut):
        t = aut.index.min(); o.update({'prima': dstr(t), 'prima_doy': int(t.day_of_year), 'prima_fonte': aut.at[t, 'fonte'], 'prima_riga': int(aut.at[t, 'riga'])})
    if o['ultima'] and o['prima']:
        o['senza_gelo'] = o['prima_doy'] - o['ultima_doy'] - 1
    o['gg_gelo'] = int(len(fr))
    gel.append(o)
G = pd.DataFrame(gel)
gel_tend = []
for var, nome in [('ultima_doy', 'ultima gelata (primavera)'), ('prima_doy', 'prima gelata (autunno)'), ('senza_gelo', 'giorni tra ultima e prima gelata')]:
    for start in [None, 1900, 1950, 1980]:
        s = G.dropna(subset=[var]); s = s if start is None else s[s.anno >= start]
        o = ols(s.anno.values, s[var].values)
        if o:
            o.update({'variabile': var, 'nome': nome, 'dal': start if start else int(G.anno.min())})
            gel_tend.append(o)
gel_dec = []
for dec in range(int(G.anno.min()) // 10 * 10, ANNO_CORR + 1, 10):
    s = G[(G.anno >= dec) & (G.anno <= dec + 9)]
    if len(s):
        gel_dec.append({'decennio': dec, 'n_anni': int(len(s)), 'ultima_doy': s.ultima_doy.mean(), 'prima_doy': s.prima_doy.mean(),
                        'senza_gelo': s.senza_gelo.mean(), 'gg_gelo': s.gg_gelo.mean()})


def estremo(col, f):
    s = G.dropna(subset=[col]); r = s.loc[f(s[col])]
    base = col.split('_')[0]
    return {'anno': int(r.anno), 'data': r[base], 'doy': int(r[col]), 'fonte': r[base + '_fonte'], 'riga': int(r[base + '_riga'])}


gel_estremi = {
    'ultima_piu_precoce': estremo('ultima_doy', lambda x: x.idxmin()), 'ultima_piu_tardiva': estremo('ultima_doy', lambda x: x.idxmax()),
    'prima_piu_precoce': estremo('prima_doy', lambda x: x.idxmin()), 'prima_piu_tardiva': estremo('prima_doy', lambda x: x.idxmax())}
n_senza_gelo_anno = [int(r.anno) for r in G.itertuples() if r.gg_gelo == 0]
salva('gelate.json', {
    'nota': 'ultima gelata = ultimo giorno con tmin<0 tra 1 gen e 31 lug; prima gelata = primo giorno con tmin<0 tra 1 ago e 31 dic. '
            'doy = giorno dell\'anno (1 gen = 1). Solo anni validi con almeno il 90% delle tmin tra gen-apr e ott-dic. '
            'senza_gelo = giorni tra ultima e prima gelata. Se in un anno non ci sono gelate la data e null.',
    'anni': gel, 'tendenze': gel_tend, 'decenni': gel_dec, 'estremi': gel_estremi, 'anni_senza_gelate': n_senza_gelo_anno})

# ------------------------------------------------------------------ CURIOSITA' (testo + fonte + righe)
cur_list = []


def fatto(testo, fonte, righe=None):
    cur_list.append({'testo': testo, 'fonte': fonte, 'righe': righe or []})


def rg(ts):
    return {'data': dstr(ts), 'fonte': df.at[ts, 'fonte'], 'riga': int(df.at[ts, 'riga'])}


te = giorni_estremi['tmax_alta'][0]
fatto(f"Il giorno piu caldo della serie e il {te['data']}: massima {fmt(te['valore'])} °C.", 'serie_unica.csv, campo tmax; records.json giorni_estremi.tmax_alta', [te])
te = giorni_estremi['tmin_bassa'][0]
fatto(f"Il giorno piu freddo (minima piu bassa) e il {te['data']}: {fmt(te['valore'])} °C.", 'serie_unica.csv, campo tmin; records.json giorni_estremi.tmin_bassa', [te])
te = giorni_estremi['tmax_bassa'][0]
fatto(f"La massima piu bassa di sempre e {fmt(te['valore'])} °C, il {te['data']}.", 'serie_unica.csv, campo tmax; records.json giorni_estremi.tmax_bassa', [te])
te = giorni_estremi['tmin_alta'][0]
fatto(f"La notte piu calda (minima piu alta) e il {te['data']}: {fmt(te['valore'])} °C.", 'serie_unica.csv, campo tmin; records.json giorni_estremi.tmin_alta', [te])
te = giorni_estremi['escursione_max'][0]
fatto(f"La maggiore escursione termica in un giorno e {fmt(te['valore'])} °C (da {fmt(te['tmin'])} a {fmt(te['tmax'])}), il {te['data']}.", 'serie_unica.csv, campi tmax-tmin', [te])
a, b = anni_caldi[0], anni_freddi[0]
fatto(f"L'anno piu caldo e il {a['anno']} ({fmt(a['tmedia'])} °C di media), il piu freddo il {b['anno']} ({fmt(b['tmedia'])} °C): differenza {fmt(a['tmedia']-b['tmedia'])} °C.", 'annuale.json campo tmedia (solo anni validi)', [])
a, b = mesi_caldi[0], mesi_freddi[0]
fatto(f"Il mese piu caldo di sempre e {MESI[a['mese']-1]} {a['anno']} ({fmt(a['tmedia'])} °C di media); il piu freddo {MESI[b['mese']-1]} {b['anno']} ({fmt(b['tmedia'])} °C).", 'mensile.json campo tmedia (solo mesi validi)', [])
a, b = est_s[-1], est_s[0]
fatto(f"L'estate (giu-ago) piu calda e quella del {a['anno']} ({fmt(a['tmedia'])} °C), la piu fredda quella del {b['anno']} ({fmt(b['tmedia'])} °C).", 'mensile.json campo tmedia, mesi 6-7-8', [])
a, b = inv_s[-1], inv_s[0]
fatto(f"L'inverno (dic-feb) piu caldo e quello che finisce nel {a['anno']} ({fmt(a['tmedia'])} °C), il piu freddo quello che finisce nel {b['anno']} ({fmt(b['tmedia'])} °C).", 'mensile.json campo tmedia, mesi 12-1-2', [])
top10 = [o['anno'] for o in anni_caldi]
fatto(f"Dei 10 anni piu caldi, {sum(1 for y in top10 if y>=2000)} sono dal 2000 in poi e {sum(1 for y in top10 if y>=1990)} dal 1990 in poi (anni: {', '.join(str(y) for y in sorted(top10))}).", 'records.json anni_caldi', [])
w = caldo[0]
fatto(f"La serie piu lunga di giorni consecutivi con massima di almeno 30 °C dura {w['giorni']} giorni, dal {w['inizio']} al {w['fine']} (massima media {fmt(w['media'])} °C).", 'serie_unica.csv, campo tmax; records.json serie_caldo_tmax30', [{'data': w['inizio'], 'fonte': w['fonti'], 'riga': w['riga_inizio']}, {'data': w['fine'], 'fonte': w['fonti'], 'riga': w['riga_fine']}])
w = gelo[0]
fatto(f"La serie piu lunga di giorni consecutivi con gelo (minima sotto 0 °C) dura {w['giorni']} giorni, dal {w['inizio']} al {w['fine']}.", 'serie_unica.csv, campo tmin; records.json serie_gelo_tmin0', [{'data': w['inizio'], 'fonte': w['fonti'], 'riga': w['riga_inizio']}, {'data': w['fine'], 'fonte': w['fonti'], 'riga': w['riga_fine']}])
w = ghiaccio[0]
fatto(f"La serie piu lunga di «giorni di ghiaccio» (massima sotto 0 °C) dura {w['giorni']} giorni, dal {w['inizio']} al {w['fine']}.", 'serie_unica.csv, campo tmax; records.json serie_ghiaccio_tmax0', [{'data': w['inizio'], 'fonte': w['fonti'], 'riga': w['riga_inizio']}])
w = tropic[0]
fatto(f"La serie piu lunga di notti tropicali (minima di almeno 20 °C) dura {w['giorni']} giorni, dal {w['inizio']} al {w['fine']}.", 'serie_unica.csv, campo tmin; records.json serie_notti_tropicali', [{'data': w['inizio'], 'fonte': w['fonti'], 'riga': w['riga_inizio']}])
nt = df[df.tmin >= 20]
if len(nt):
    t0 = nt.index.min()
    fatto(f"La prima notte tropicale della serie e il {dstr(t0)}; in tutto le notti tropicali sono {len(nt)}, di cui {int((nt.y>=2000).sum())} dal 2000 in poi.", 'serie_unica.csv, campo tmin>=20', [rg(t0)])
h35 = df[df.tmax >= 35]
if len(h35):
    fatto(f"Giorni con massima di almeno 35 °C: {len(h35)} in tutta la serie, il primo il {dstr(h35.index.min())}, l'ultimo il {dstr(h35.index.max())}.", 'serie_unica.csv, campo tmax>=35', [rg(h35.index.min()), rg(h35.index.max())])
r = V.loc[V.gg_caldi.idxmax()]; r2 = V.loc[V.notti_tropicali.idxmax()]
fatto(f"L'anno con piu giorni caldi (massima >= 30 °C) e il {int(r.name)} con {int(r.gg_caldi)}; quello con piu notti tropicali il {int(r2.name)} con {int(r2.notti_tropicali)}.", 'annuale.json campi gg_caldi, notti_tropicali (anni validi)', [])
r = V.loc[V.gg_gelo.idxmax()]; r2 = V.loc[V.gg_gelo.idxmin()]
fatto(f"L'anno con piu giorni di gelo e il {int(r.name)} con {int(r.gg_gelo)}; quello con meno il {int(r2.name)} con {int(r2.gg_gelo)}.", 'annuale.json campo gg_gelo (anni validi)', [])
a1 = V[(V.index >= 1951) & (V.index <= 1980)].gg_gelo.mean(); a2 = V[(V.index >= 1991) & (V.index <= 2020)].gg_gelo.mean()
fatto(f"Giorni di gelo l'anno in media: {fmt(a1)} nel 1951-1980, {fmt(a2)} nel 1991-2020.", 'annuale.json campo gg_gelo (media sugli anni validi dei due periodi)', [])
dt = df.tmean.reindex(full).diff().dropna()
tup, tdw = dt.idxmax(), dt.idxmin()
fatto(f"Il maggiore salto di temperatura media da un giorno al successivo: +{fmt(dt.max())} °C il {dstr(tup)}; il maggiore calo {fmt(dt.min())} °C il {dstr(tdw)}.", 'serie_unica.csv, campo tmean (giorni consecutivi)', [rg(tup), rg(tdw)])
# anno corrente rispetto a 1991-2020, sugli stessi giorni
c = df[(df.y == ANNO_CORR) & df.tmean.notna()]
base = mm9120['tmean']
diff = [r.tmean - base.loc[(r.m, r.d)] for r in c.itertuples()]
fatto(f"Il {ANNO_CORR} finora ({len(c)} giorni con dato, fino al {dstr(c.index.max())}) e stato {fmt(np.mean(diff))} °C sopra la media 1991-2020 degli stessi giorni del calendario."
      if np.mean(diff) >= 0 else
      f"Il {ANNO_CORR} finora ({len(c)} giorni con dato, fino al {dstr(c.index.max())}) e stato {fmt(-np.mean(diff))} °C sotto la media 1991-2020 degli stessi giorni del calendario.",
      'serie_unica.csv, campo tmean dell\'anno corrente (ARPA 5897) contro media 1991-2020 per giorno del calendario (giorni.json campo tm_9120)', [])
if righe_f:
    rt = righe_f[0]
    fatto(f"Nello stesso periodo (1 gennaio - {mdc[1]} {MESI[mdc[0]-1]}) il {ANNO_CORR} e al posto {rt['rank_alto']} su {rt['n']} per temperatura media ({fmt(rt['valore'])} °C; media degli altri anni {fmt(rt['media_altri'])} °C), contando dal piu caldo.",
          'finora.json campo righe (tmedia); stesso periodo di ogni anno con almeno il 90% dei giorni', [])
records['curiosita'] = cur_list
salva('records.json', records)

# ------------------------------------------------------------------ META
salva('meta.json', {
    'stato_cucitura': splice.get('stato'), 'segmenti': [s for s in splice.get('segmenti', []) if s.get('attivo', True)], 'config_fonti': splice.get('fonti'),  # segmenti spenti (proposte) esclusi
    'data_scarico': DATA_SCARICO, 'primo_giorno': df.index.min(), 'ultimo_giorno': ULT, 'anno_corrente': ANNO_CORR,
    'ultimo_anno_valido': ULT_VALIDO, 'n_giorni': int(len(df)), 'n_giorni_tmean': int(df.tmean.count()),
    'soglie': {'giorni_anno_valido': MIN_GIORNI_ANNO, 'frazione_mese_valido': MIN_FRAZ_MESE, 'gelo': 'tmin < 0', 'caldo': 'tmax >= 30',
               'notte_tropicale': 'tmin >= 20', 'caldo_forte': 'tmax >= 35'},
    'fonti_codici': {'maugeri': 'Maugeri / GHCN-D ITE00100554 (copia di ECA&D SOUID 105248, 105247)',
                     'arpa5897': 'ARPA Lombardia sensore 5897 Milano v.Brera'},
    'n_anni_validi': int(len(V)), 'n_anni_totali': int(len(ann)), 'anni_non_validi': [int(y) for y in ann.index[~ann.ok] if y != ANNO_CORR], 'anno_in_corso_parziale': bool(not ann.at[ANNO_CORR, 'ok']),
})
print('anni validi', len(V), 'su', len(ann), '| ultimo valido', ULT_VALIDO)
