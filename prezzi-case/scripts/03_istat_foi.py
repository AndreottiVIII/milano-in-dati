"""Serie FOI senza tabacchi (ISTAT) raccordata tra le basi, mensile e annuale.
Entrata: i CSV SDMX scaricati in raw/istat (169_748_DF_DCSP_FOI1B2025_1.m.csv = mensile 2003-12 -> oggi, 4 basi;
         169_750_DF_DCSP_FOI2B2025_1.csv = medie annue 1996-2025, 3 basi).
Uscita: pulito/foi_mensile.csv e pulito/foi_annuale.csv, con
   indice originale (nella base in cui ISTAT lo pubblica) e indice raccordato (2025 = 100).
Metodo del raccordo: per ogni cambio di base B, il coefficiente e' la media dell'anno-base B nella serie della base
precedente / 100 (cosi' fa ISTAT: l'indice dell'anno base e' 100 = media dell'anno). Nessun dato inventato.
Uso: python -I 03_istat_foi.py <cartella_raw_istat> <cartella_pulito>
"""
import sys, os
import pandas as pd

raw, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

# basi mensili: codice DATA_TYPE -> (anno base, primo mese pubblicato)
BASI_M = {'4': 1995, '11': 2010, '55': 2015, '101': 2025}
BASI_A = {'5': 1995, '12': 2010, '56': 2015}


def chain(df, basi, col_per, annual):
    """df: righe 00ST con DATA_TYPE, OBS_VALUE (indice), TIME_PERIOD. Restituisce serie raccordata base 2025=100."""
    df = df.copy()
    df['base'] = df['DATA_TYPE'].map(basi)
    df['v'] = pd.to_numeric(df['OBS_VALUE'])
    df['anno'] = df['TIME_PERIOD'].str[:4].astype(int)
    ordine = sorted(basi.values())
    coeff = {}  # moltiplicatore per portare la base b a "base 2025 = 100" (quando b e' l'ultima, 1.0)
    # serie per base
    # c[b] = (indice base-b) -> indice "nella base precedente": prodotto dei coefficienti
    # k[b] = media dell'anno b nella base precedente / 100  (indice precedente = indice b * k[b])
    k = {}
    for i, b in enumerate(ordine):
        if i == 0:
            k[b] = 1.0
            continue
        prec = ordine[i - 1]
        x = df[(df.base == prec) & (df.anno == b)]
        n_attesi = 1 if annual else 12
        if len(x) != n_attesi:
            # il valore dell'anno-base nella base precedente non e' completo: non si puo' raccordare in modo esatto
            raise SystemExit(f'Raccordo impossibile {prec}->{b}: trovati {len(x)} valori invece di {n_attesi}')
        k[b] = x['v'].mean() / 100.0
    # indice nella base piu' vecchia (1995=100): moltiplico per il prodotto cumulato dei k
    cum = {}
    p = 1.0
    for b in ordine:
        p *= k[b]
        cum[b] = p
    df['idx_base1995'] = df.apply(lambda r: r['v'] * cum[r['base']], axis=1)
    # riporto a 2025 = 100: divido per la media del 2025 espressa in base 1995 (= cum[2025] * 100 / 100)
    ref = df[df.anno == 2025]['idx_base1995'].mean()   # media 2025 espressa in base 1995
    df['idx_2025_100'] = df['idx_base1995'] / ref * 100.0
    return df


# ---- mensile
m = pd.read_csv(os.path.join(raw, '169_748_DF_DCSP_FOI1B2025_1.m.csv'), dtype=str)
m = m[(m.ECOICOP_2 == '00ST') & (m.MEASURE == '4')]
# nel mese di passaggio non ci sono doppioni: ogni mese e' in una sola base
assert m.groupby('TIME_PERIOD').size().max() == 1, 'mesi doppi'
mc = chain(m, BASI_M, 'TIME_PERIOD', annual=False)
mc = mc.sort_values('TIME_PERIOD')
res = mc[['TIME_PERIOD', 'base', 'v', 'idx_2025_100']].rename(columns={'TIME_PERIOD': 'mese', 'base': 'base_originale', 'v': 'indice_originale', 'idx_2025_100': 'indice_raccordato_2025_100'})
res['indice_raccordato_2025_100'] = res['indice_raccordato_2025_100'].round(3)
res['var_su_12_mesi_pct'] = (res['indice_raccordato_2025_100'] / res['indice_raccordato_2025_100'].shift(12) - 1) * 100
res['var_su_12_mesi_pct'] = res['var_su_12_mesi_pct'].round(2)
res.to_csv(os.path.join(out, 'foi_mensile.csv'), index=False)
print('mensile:', res.mese.min(), '->', res.mese.max(), len(res), 'righe')

# ---- annuale
a = pd.read_csv(os.path.join(raw, '169_750_DF_DCSP_FOI2B2025_1.csv'), dtype=str)
a = a[(a.ECOICOP_2 == '00ST') & (a.MEASURE == '4')]
assert a.groupby('TIME_PERIOD').size().max() == 1, 'anni doppi'
ac = chain(a, BASI_A, 'TIME_PERIOD', annual=True).sort_values('TIME_PERIOD')
ra = ac[['TIME_PERIOD', 'base', 'v', 'idx_2025_100']].rename(columns={'TIME_PERIOD': 'anno', 'base': 'base_originale', 'v': 'indice_originale', 'idx_2025_100': 'indice_raccordato_2025_100'})
ra['indice_raccordato_2025_100'] = ra['indice_raccordato_2025_100'].round(3)
ra.to_csv(os.path.join(out, 'foi_annuale.csv'), index=False)
print('annuale:', ra.anno.min(), '->', ra.anno.max(), len(ra), 'righe')
