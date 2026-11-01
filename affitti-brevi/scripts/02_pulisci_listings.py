"""Fase 1 - pulisce gli annunci Inside Airbnb di Milano (4 snapshot) e li assegna a NIL e zone OMI.
Uso: python -I -X utf8 02_pulisci_listings.py <cartella affitti-brevi (assoluta)> <cartella milano-in-dati (assoluta)>
Scrive in pulito: annunci_snapshot.csv (una riga per annuncio e snapshot, SENZA nomi, descrizioni, foto, host_name),
                    snapshot_controlli.csv.
Le colonne personali (nome, descrizione, host_name, host_about, url, foto) NON vengono copiate.
"""
import sys, json, re
from pathlib import Path
import pandas as pd, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

base = Path(sys.argv[1]); prog = Path(sys.argv[2])
SNAP = ['2025-12-26', '2026-03-27', '2026-06-25', '2026-09-19']

def load_polys(path, key_fields):
    gj = json.load(open(path, encoding='utf8'))
    geoms, props = [], []
    for f in gj['features']:
        geoms.append(shape(f['geometry'])); props.append({k: f['properties'][k] for k in key_fields})
    return geoms, props

nil_g, nil_p = load_polys(prog/'citta-15-minuti/out/nil_poligoni_punteggi.geojson', ['ID_NIL', 'NIL'])
zon_g, zon_p = load_polys(prog/'docs/prezzi-case/data/zone.geojson', ['zona', 'fascia'])
air_g, air_p = load_polys(base/'raw/insideairbnb/2026-09-19/neighbourhoods.geojson', ['neighbourhood'])
trees = {n: (STRtree(g), g, p) for n, (g, p) in {'nil': (nil_g, nil_p), 'zon': (zon_g, zon_p), 'air': (air_g, air_p)}.items()}

def assegna(lon, lat, which, tol_deg=0.002):
    """poligono che contiene il punto; se nessuno, il piu' vicino entro ~200 m (tol_deg); altrimenti None"""
    tree, g, p = trees[which]
    pt = Point(lon, lat)
    hit = tree.query(pt, predicate='within')
    if len(hit): return p[int(hit[0])], 'dentro'
    i = int(tree.nearest(pt)); d = g[i].distance(pt)
    if d <= tol_deg: return p[i], 'vicino'
    return None, 'fuori'

def tipo_licenza(s):
    if not isinstance(s, str) or not s.strip(): return 'assente'
    t = s.strip()
    if re.fullmatch(r'IT\d{6}[A-Z]\d[A-Z0-9]{8}', t): return 'CIN_formato_valido'
    if t.lower().startswith('exempt'): return 'esente'
    if 'applied for a cin' in t.lower(): return 'CIN_richiesto_non_ricevuto'
    return 'altro_testo'

out, ctrl = [], []
for d in SNAP:
    df = pd.read_csv(base/f'raw/insideairbnb/{d}/listings.csv.gz', low_memory=False)
    n0 = len(df)
    price = pd.to_numeric(df['price'].astype(str).str.replace(r'[$€,]', '', regex=True), errors='coerce')
    # il prezzo e' una "quotazione" per date precise: tenere traccia se e' prezzo mensile
    monthly = pd.Series(np.nan, index=df.index)
    if 'price_quote_raw' in df:
        def ismonth(s):
            if not isinstance(s, str): return np.nan
            try: return bool(json.loads(s)['quote'].get('is_monthly_priced'))
            except Exception: return np.nan
        monthly = df['price_quote_raw'].map(ismonth)
        curr = df['price_quote_raw'].map(lambda s: (json.loads(s)['quote'].get('currency') if isinstance(s, str) else None))
        ci = pd.to_datetime(df['price_quote_checkin_date']); co = pd.to_datetime(df['price_quote_checkout_date'])
        stay = (co - ci).dt.days
    else:
        curr = pd.Series(None, index=df.index); stay = pd.Series(np.nan, index=df.index)
    res = pd.DataFrame({
        'snapshot': d, 'id': df['id'], 'host_id': df['host_id'],
        'room_type': df['room_type'], 'property_type': df['property_type'],
        'lat': df['latitude'], 'lon': df['longitude'],
        'neighbourhood_airbnb': df['neighbourhood_cleansed'],
        'accommodates': df['accommodates'], 'bedrooms': df['bedrooms'],
        'price_eur_quote': price, 'price_quote_monthly': monthly, 'price_quote_stay_nights': stay, 'price_quote_currency': curr,
        'minimum_nights': df['minimum_nights'], 'availability_365': df['availability_365'],
        'number_of_reviews': df['number_of_reviews'], 'number_of_reviews_ltm': df['number_of_reviews_ltm'],
        'first_review': df['first_review'], 'last_review': df['last_review'],
        'review_scores_rating': df['review_scores_rating'],
        'licenza_tipo': df['license'].map(tipo_licenza),
        'host_listings_in_city': df['calculated_host_listings_count'],
        'host_entire_homes': df['calculated_host_listings_count_entire_homes'],
        'host_private_rooms': df['calculated_host_listings_count_private_rooms'],
        'est_occupancy_l365d': df['estimated_occupancy_l365d'], 'est_revenue_l365d': df['estimated_revenue_l365d'],
        'last_scraped': df['last_scraped'],
    })
    nil_id, nil_nome, nil_how, zona, zona_how = [], [], [], [], []
    for lon, lat in zip(res['lon'], res['lat']):
        p, h = assegna(lon, lat, 'nil'); nil_id.append(p['ID_NIL'] if p else None); nil_nome.append(p['NIL'] if p else None); nil_how.append(h)
        p, h = assegna(lon, lat, 'zon'); zona.append(p['zona'] if p else None); zona_how.append(h)
    res['nil_id'] = nil_id; res['nil_nome'] = nil_nome; res['nil_assegnazione'] = nil_how
    res['zona_omi'] = zona; res['zona_omi_assegnazione'] = zona_how
    out.append(res)
    ctrl.append({'snapshot': d, 'righe_file': n0, 'id_distinti': res['id'].nunique(), 'host_distinti': res['host_id'].nunique(),
                 'prezzo_presente': int(price.notna().sum()), 'prezzo_mancante': int(price.isna().sum()),
                 'valuta_quotazione': ','.join(sorted(set(curr.dropna()))) if curr.notna().any() else 'n.d. (colonne price_quote_* assenti)',
                 'nil_dentro': nil_how.count('dentro'), 'nil_vicino_200m': nil_how.count('vicino'), 'nil_fuori': nil_how.count('fuori'),
                 'zona_omi_dentro': zona_how.count('dentro'), 'zona_omi_vicino': zona_how.count('vicino'), 'zona_omi_fuori': zona_how.count('fuori'),
                 'last_scraped_min': df['last_scraped'].min(), 'last_scraped_max': df['last_scraped'].max()})
    print(d, ctrl[-1], flush=True)

allr = pd.concat(out, ignore_index=True)
(base/'pulito').mkdir(exist_ok=True)
allr.to_csv(base/'pulito/annunci_snapshot.csv', index=False, encoding='utf-8')
pd.DataFrame(ctrl).to_csv(base/'pulito/snapshot_controlli.csv', index=False, encoding='utf-8')
print('scritto', len(allr))
