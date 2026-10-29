"""Passo 5: quanti incidenti (microdati Lombardia, Milano 2010-2024) hanno un indirizzo usabile e quanti si agganciano
con la geocodifica locale (civici del Comune + nomi strade OSM). Stima su 500 righe a caso (seme fisso).
Uso: python -I f2_incidenti_geo.py <ABS strand> -> out/incidenti_geo_stima.json, out/incidenti_geo_campione500.csv"""
import sys, os, glob, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from f2_geocode import Geocoder
S = sys.argv[1]
rows = []
for f in sorted(glob.glob(S + '/raw/incidenti/lombardia_microdati/*.json')):
    rows += json.load(open(f, encoding='utf-8'))
df = pd.DataFrame(rows); df['nome_strada'] = df.nome_strada.fillna('').astype(str).str.strip()
def cat(s):
    if not s: return 'vuoto'
    if re.search(r'\S\s+-\s', s):
        parts = [p.strip() for p in s.split(' - ') if p.strip() and p.strip() != '-']
        if len(parts) <= 1: return 'solo_via_o_altro'
        return 'civico' if re.match(r'^\d+[a-zA-Z]?$', parts[1]) else 'incrocio'
    if re.search(r'\s(incrocio|inc\.?|ang\.?)\s', s, flags=re.I): return 'incrocio'
    if re.search(r'palo\s*luce', s, flags=re.I): return 'palo_luce'
    if re.match(r'^.*?[, ]+(?:n\.?\s*)?\d+\s*[a-zA-Z]?\s*(/.*)?$', s): return 'civico'
    if re.match(r'^(autostrada|tangenziale|a\d|raccordo|ss|sp|sr|strada statale|strada provinciale)', s, flags=re.I): return 'autostrada_statale'
    return 'solo_via_o_altro'
df['cat'] = df.nome_strada.map(cat)
tot = len(df); cnt = df.cat.value_counts()
out = {'righe_totali_2010_2024': tot, 'per_anno': {int(k): int(v) for k, v in df.anno.value_counts().sort_index().items()},
       'tipo_indirizzo': {k: {'righe': int(v), 'quota_pct': round(100 * v / tot, 1)} for k, v in cnt.items()}}
g = Geocoder(S)
smp = df.sample(500, random_state=11).copy()
res = [g.indirizzo(s) if c in ('civico', 'incrocio', 'palo_luce', 'solo_via_o_altro') else (None, 'non_geocodificabile:' + c) for s, c in zip(smp.nome_strada, smp.cat)]
smp['livello'] = [l for _, l in res]; smp['lon'] = [r[0] if r else None for r, _ in res]; smp['lat'] = [r[1] if r else None for r, _ in res]
smp['livello_base'] = smp.livello.str.replace(r'\(.*\)', '', regex=True)
# controllo di plausibilita: dentro il rettangolo di Milano
ok = smp.lon.notna(); inb = (smp.lon.between(9.04, 9.28)) & (smp.lat.between(45.38, 45.54))
out['campione'] = {'righe': 500, 'categorie': smp.cat.value_counts().to_dict(), 'livelli': smp.livello.value_counts().to_dict(),
                   'con_coordinate': int(ok.sum()), 'con_coordinate_dentro_Milano': int((ok & inb).sum())}
niv = lambda k: int((smp.livello_base == k).sum())
n = 500
out['stima_quote_pct'] = {'civico_esatto': round(100 * niv('civico') / n, 1), 'civico_approssimato': round(100 * niv('civico_approx') / n, 1),
                         'incrocio': round(100 * niv('incrocio') / n, 1), 'solo_via': round(100 * (niv('strada')) / n, 1),
                         'posizione_buona (civico esatto + incrocio)': round(100 * (niv('civico') + niv('incrocio')) / n, 1),
                         'posizione_entro_circa_100m (+ civico approssimato)': round(100 * (niv('civico') + niv('incrocio') + niv('civico_approx')) / n, 1),
                         'nessuna_posizione': round(100 * (~ok).sum() / n, 1)}
# per categoria: quota agganciata
por = {}
for c, sub in smp.groupby('cat'):
    por[c] = {'righe_campione': len(sub), 'agganciate_pct': round(100 * sub.lon.notna().mean(), 1), 'livelli': sub.livello.value_counts().to_dict()}
out['per_categoria_nel_campione'] = por
# errori di agganciamento "no_via": i nomi non trovati piu frequenti
nov = smp[smp.livello.str.contains('no_via|vuoto|non_si_toccano', regex=True)]
out['esempi_non_agganciati'] = nov.nome_strada.head(25).tolist()
json.dump(out, open(S + '/out/incidenti_geo_stima.json', 'w'), indent=1, ensure_ascii=False)
smp[['anno', 'nome_strada', 'cat', 'livello', 'lon', 'lat']].to_csv(S + '/out/incidenti_geo_campione500.csv', index=False, sep=';', encoding='utf-8-sig')
print(json.dumps({k: out[k] for k in ('righe_totali_2010_2024', 'tipo_indirizzo', 'campione', 'stima_quote_pct')}, indent=1, ensure_ascii=False))
print(out['esempi_non_agganciati'])
