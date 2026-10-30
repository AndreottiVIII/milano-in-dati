"""Tavola di corrispondenza tra le zonizzazioni OMI di un comune (default Milano, F205), da sovrapposizione spaziale.
Entrata: <cartella>/<codcom>_<AAAAS>.json, risposta del servizio di mappa GEOPOI (richiesta=6): FeatureCollection, una
         feature per zona (properties.zona). Esempio nome: F205_20261.json = 2026 primo semestre.
Uscite (in <pulito>/):
  zone_periodi.csv           semestri raggruppati in "periodi di zonizzazione" (stesse zone, stessi perimetri a meno di ritocchi)
  zone_corrispondenza.csv    ogni coppia (zona del periodo A, zona del periodo B) che si sovrappone, con le quote di area
  zone_non_1a1.csv           le zone che NON hanno un corrispondente uno-a-uno: da guardare a mano, mai unite in silenzio
  zone_serie.csv             per ogni semestre e zona: id della serie confrontabile nel tempo (solo catene 1:1)
Regole:
  - il perimetro e' letto con la regola pari/dispari sugli anelli (OR esclusivo): il servizio mette in un unico "Polygon" piu'
    pezzi staccati, che il GeoJSON standard leggerebbe come buchi (l'area di Milano scenderebbe da 181 a ~100 km2).
  - due zone sono "1:1" solo se si sovrappongono per almeno SOGLIA_11 (0,90) dell'area di entrambe.
  - un cambio di periodo c'e' se cambia l'insieme dei codici zona o se un perimetro si discosta oltre SOGLIA_STESSO (IoU < 0,95).
  - i frammenti di sovrapposizione sotto 1% di entrambe le zone e sotto 10.000 m2 sono ignorati ma contati nel log.
Uso: python -I 05_zone_corrispondenza.py <cartella_json> <cartella_pulito> [codcom]
"""
import sys, os, glob, json, re
from functools import reduce
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from shapely.validation import make_valid

SOGLIA_11 = 0.90
SOGLIA_STESSO = 0.95
SOGLIA_QUOTA = 0.10      # quota minima per considerare "significativo" il passaggio di area da una zona all'altra
MIN_FRAMMENTO_M2 = 10000
MIN_FRAMMENTO_Q = 0.01

TR = Transformer.from_crs(4326, 32632, always_xy=True)


def geom_feature(feat):
    """Perimetro in metri (UTM 32N). Anelli combinati con OR esclusivo (pari/dispari)."""
    ps = []
    for ring in feat['geometry']['coordinates']:
        a = np.array(ring, dtype=float)
        x, y = TR.transform(a[:, 0], a[:, 1])
        ps.append(make_valid(Polygon(np.column_stack([x, y]))))
    return reduce(lambda p, q: p.symmetric_difference(q), ps)


def carica(path):
    d = json.load(open(path, encoding='utf-8'))
    z = {}
    for f in d['dat']['features']:
        cod = f['properties']['zona']
        g = geom_feature(f)
        z[cod] = z[cod].union(g) if cod in z else g
    return z


def semestre_etichetta(s):
    return f'{s[:4]}-S{s[4]}'


def stesso_perimetro(a, b):
    """True se stesso insieme di codici e ogni perimetro ha IoU >= SOGLIA_STESSO. Restituisce (bool, IoU minima)."""
    if set(a) != set(b):
        return False, None
    ious = []
    for k in a:
        u = a[k].union(b[k]).area
        ious.append(a[k].intersection(b[k]).area / u if u > 0 else 1.0)
    m = min(ious)
    return m >= SOGLIA_STESSO, m


def confronta(ga, gb):
    """Righe di sovrapposizione tra due zonizzazioni + log dei frammenti ignorati."""
    keys_b = list(gb)
    tree = STRtree([gb[k] for k in keys_b])
    righe, ignorati = [], 0.0
    for ka, A in ga.items():
        for j in tree.query(A):
            kb = keys_b[j]
            B = gb[kb]
            i = A.intersection(B).area
            if i <= 0:
                continue
            qa, qb = i / A.area, i / B.area
            if i < MIN_FRAMMENTO_M2 and qa < MIN_FRAMMENTO_Q and qb < MIN_FRAMMENTO_Q:
                ignorati += i
                continue
            righe.append(dict(zona_a=ka, zona_b=kb, area_comune_m2=round(i), quota_di_a=round(qa, 4), quota_di_b=round(qb, 4),
                              area_a_m2=round(A.area), area_b_m2=round(B.area)))
    return pd.DataFrame(righe), ignorati


def classifica(df, zone_a, zone_b):
    """Per ogni zona di A: esito rispetto a B. Per ogni zona di B: esito rispetto ad A."""
    sig = df[(df.quota_di_a >= SOGLIA_QUOTA) | (df.quota_di_b >= SOGLIA_QUOTA)] if len(df) else df
    out_a, out_b = {}, {}
    for a in zone_a:
        s = sig[sig.zona_a == a]
        dest = s[s.quota_di_a >= SOGLIA_QUOTA]
        if len(dest) == 0:
            out_a[a] = ('senza_corrispondente', '')
            continue
        # quante zone di A alimentano ciascuna destinazione
        nd = []
        for b in dest.zona_b:
            nd.append(int((sig[(sig.zona_b == b)].quota_di_b >= SOGLIA_QUOTA).sum()))
        if len(dest) == 1 and nd[0] == 1:
            r = dest.iloc[0]
            if r.quota_di_a >= SOGLIA_11 and r.quota_di_b >= SOGLIA_11:
                out_a[a] = ('1:1', r.zona_b)
            else:
                out_a[a] = ('1:1_perimetro_cambiato', r.zona_b)
        elif len(dest) > 1 and all(n == 1 for n in nd):
            out_a[a] = ('divisa', ';'.join(dest.zona_b))
        elif len(dest) == 1 and nd[0] > 1:
            out_a[a] = ('accorpata', dest.iloc[0].zona_b)
        else:
            out_a[a] = ('complessa', ';'.join(dest.zona_b))
    for b in zone_b:
        s = sig[sig.zona_b == b]
        orig = s[s.quota_di_b >= SOGLIA_QUOTA]
        if len(orig) == 0:
            out_b[b] = ('senza_corrispondente', '')
            continue
        if len(orig) == 1:
            a = orig.iloc[0].zona_a
            if out_a.get(a, ('',))[0] == '1:1':
                out_b[b] = ('1:1', a)
            elif out_a.get(a, ('',))[0] == '1:1_perimetro_cambiato':
                out_b[b] = ('1:1_perimetro_cambiato', a)
            else:
                out_b[b] = ('nata_da_divisione', a)
        else:
            out_b[b] = ('nata_da_accorpamento', ';'.join(orig.zona_a))
    return out_a, out_b


def main():
    cartella, pulito = sys.argv[1], sys.argv[2]
    codcom = sys.argv[3] if len(sys.argv) > 3 else 'F205'
    os.makedirs(pulito, exist_ok=True)
    files = sorted(glob.glob(os.path.join(cartella, f'{codcom}_*.json')))
    sem = {}
    for p in files:
        m = re.search(r'_(\d{5})\.json$', p)
        if not m:
            continue
        sem[m.group(1)] = carica(p)
    if not sem:
        raise SystemExit('nessun file trovato')
    # --- periodi
    periodi, cur = [], None
    for s in sorted(sem):
        if cur is None:
            cur = dict(sem=[s], iou=[]); periodi.append(cur); continue
        ok, m = stesso_perimetro(sem[cur['sem'][-1]], sem[s])
        if ok:
            cur['sem'].append(s); cur['iou'].append(m)
        else:
            cur = dict(sem=[s], iou=[], iou_cambio=m); periodi.append(cur)
    righe_p = []
    for i, p in enumerate(periodi, 1):
        p['id'] = f'P{i}'
        rep = sem[p['sem'][-1]]   # perimetri del PRIMO semestre sono quelli di entrata, uso l'ultimo del periodo come rappresentante
        p['rep'] = p['sem'][-1]
        righe_p.append(dict(periodo=p['id'], primo_semestre=semestre_etichetta(p['sem'][0]), ultimo_semestre=semestre_etichetta(p['sem'][-1]),
                            n_semestri=len(p['sem']), n_zone=len(rep), area_totale_km2=round(sum(g.area for g in rep.values()) / 1e6, 2),
                            iou_minima_tra_semestri_del_periodo=round(min(p['iou']), 4) if p['iou'] else '',
                            iou_minima_al_cambio_dal_periodo_precedente=round(p['iou_cambio'], 4) if p.get('iou_cambio') is not None else ('(codici zona diversi)' if i > 1 else '')))
    pd.DataFrame(righe_p).to_csv(os.path.join(pulito, 'zone_periodi.csv'), index=False)

    # --- corrispondenze tra periodi consecutivi (rappresentante = primo semestre del successivo, ultimo del precedente)
    tutte, nonuno = [], []
    esiti = {}   # (periodo_a, zona_a) -> (esito, zone_b) ; e per b
    log_ign = []
    arco = {}    # (id_periodo_prec, zona) -> (id_periodo_succ, zona) solo 1:1
    arco_largo = {}   # come sopra ma accetta anche '1:1_perimetro_cambiato' (ritocchi del perimetro tra 0,5 e 0,9)
    for i in range(len(periodi) - 1):
        A, B = periodi[i], periodi[i + 1]
        ga, gb = sem[A['sem'][-1]], sem[B['sem'][0]]
        df, ign = confronta(ga, gb)
        log_ign.append((A['id'], B['id'], round(ign)))
        oa, ob = classifica(df, list(ga), list(gb))
        if len(df):
            df.insert(0, 'periodo_a', A['id']); df.insert(1, 'semestre_a', semestre_etichetta(A['sem'][-1]))
            df.insert(2, 'periodo_b', B['id']); df.insert(3, 'semestre_b', semestre_etichetta(B['sem'][0]))
            df['esito_zona_a'] = df.zona_a.map(lambda z: oa[z][0])
            df['esito_zona_b'] = df.zona_b.map(lambda z: ob[z][0])
            tutte.append(df)
        for z, (e, d) in oa.items():
            if e == '1:1_perimetro_cambiato':
                arco_largo[(A['id'], z)] = (B['id'], d)
            if e != '1:1':
                nonuno.append(dict(periodo_a=A['id'], periodo_b=B['id'], lato='zona del periodo precedente', zona=z, esito=e, controparti=d))
            else:
                arco[(A['id'], z)] = (B['id'], d)
                arco_largo[(A['id'], z)] = (B['id'], d)
        for z, (e, d) in ob.items():
            if e != '1:1':
                nonuno.append(dict(periodo_a=A['id'], periodo_b=B['id'], lato='zona del periodo successivo', zona=z, esito=e, controparti=d))
    if tutte:
        pd.concat(tutte).to_csv(os.path.join(pulito, 'zone_corrispondenza.csv'), index=False)
    pd.DataFrame(nonuno).to_csv(os.path.join(pulito, 'zone_non_1a1.csv'), index=False)

    # --- serie confrontabili: stesso codice dentro il periodo; tra periodi solo archi 1:1 (id_serie, rigoroso)
    #     id_serie_larga accetta anche i 1:1 con perimetro ritoccato (da usare solo guardando zone_non_1a1.csv)
    def costruisci(archi):
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for p in periodi:
            for z in sem[p['sem'][0]]:
                find((p['id'], z))
        for (pa, za), (pb, zb) in archi.items():
            parent[find((pa, za))] = find((pb, zb))
        return find

    f_str, f_lar = costruisci(arco), costruisci(arco_largo)
    ids_s, ids_l, serie_righe = {}, {}, []
    for p in periodi:
        for s in p['sem']:
            for z in sem[s]:
                rs, rl = f_str((p['id'], z)), f_lar((p['id'], z))
                if rs not in ids_s:
                    ids_s[rs] = f'S{len(ids_s) + 1:03d}'
                if rl not in ids_l:
                    ids_l[rl] = f'L{len(ids_l) + 1:03d}'
                serie_righe.append(dict(semestre=semestre_etichetta(s), periodo=p['id'], zona=z, id_serie=ids_s[rs], id_serie_larga=ids_l[rl]))
    ds = pd.DataFrame(serie_righe)
    ds['primo_semestre_serie'] = ds.groupby('id_serie').semestre.transform('min')
    ds['n_semestri_serie'] = ds.groupby('id_serie').semestre.transform('nunique')
    ds.to_csv(os.path.join(pulito, 'zone_serie.csv'), index=False)

    print(f'{len(sem)} semestri letti, {len(periodi)} periodi di zonizzazione')
    for r in righe_p:
        print('  ', r['periodo'], r['primo_semestre'], '->', r['ultimo_semestre'], r['n_zone'], 'zone', r['area_totale_km2'], 'km2')
    print('frammenti ignorati (m2) per passaggio:', log_ign)
    print('zone senza 1:1:', len(nonuno), 'righe in zone_non_1a1.csv')
    ult = periodi[-1]['id']
    for col in ('id_serie', 'id_serie_larga'):
        att = ds[ds.periodo == ult][col].unique()
        lunghe = int((ds[ds[col].isin(att)].groupby(col).periodo.nunique() == len(periodi)).sum())
        print(f"{col}: {ds[col].nunique()} serie distinte; {len(att)} arrivano all'ultimo periodo; {lunghe} coprono tutti i {len(periodi)} periodi")


if __name__ == '__main__':
    main()
