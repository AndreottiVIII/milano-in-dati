"""03: quanto sono separati anziani e giovani tra i 88 quartieri (NIL), 1999-2025.
Entrata: popolazione/pulito/residenti_nil_anno_eta_genere.csv (ds27 del Comune: residenti al 31/12 per NIL x eta' singola x genere).
Uscite in divisa/out/: eta_serie.csv (anno), eta_nil.csv (anno x NIL), eta_log.json
Uso: python -I -X utf8 03_eta.py <milano-in-dati assoluto> <divisa assoluto>
Misure: D tra over 65 e under 35 (principale); D tra over 75 e 25-34 anni (variante); isolamento degli over 65;
indice a ordine di rango su tutte le eta' singole 0-100+ (quanta parte della differenza di eta' tra le persone si spiega col quartiere).
Intervalli: ricampionamento multinomiale (200). Valore a caso: 50 riallocazioni."""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import misure as M

BASE, DIV = sys.argv[1], sys.argv[2]
OUT = os.path.join(DIV, 'out')
e = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'residenti_nil_anno_eta_genere.csv'))
ana = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'nil_anagrafica.csv'))
ids = ana.id_nil.tolist()
E = e.groupby(['anno', 'id_nil', 'eta']).residenti.sum().unstack('eta').fillna(0)
ET = np.array(E.columns, int)
assert ET.min() == 0 and ET.max() == 100 and len(ET) == 101
rng = np.random.default_rng(65)
log = {}


def d6535(R):
    return M.dissimilarita(R[:, 65:].sum(1), R[:, :35].sum(1))


def d75(R):
    return M.dissimilarita(R[:, 75:].sum(1), R[:, 25:35].sum(1))


rows = []; nil = []
for anno in sorted(E.index.get_level_values(0).unique()):
    p = E.loc[anno].reindex(ids).fillna(0)
    Cm = p.to_numpy(float)
    keep = Cm.sum(1) > 0
    C = Cm[keep]
    t = C.sum(1)
    old = C[:, 65:].sum(1)
    r = dict(anno=int(anno), residenti=int(t.sum()), n_nil=int(keep.sum()), quota_65p=old.sum() / t.sum(), quota_u35=C[:, :35].sum() / t.sum(),
             eta_media=float((C * (ET + 0.5)).sum() / t.sum()))
    r['d'] = d6535(C)
    _, r['d_lo'], r['d_hi'] = M.bootstrap(C, d6535, 200, rng)
    r['d_base'] = M.basale(C, d6535, 50, rng)[0]
    r['d_75_2534'] = d75(C)
    r['iso_65p'] = M.isolamento(old, t)
    r['hr'] = M.rank_order_H(C)
    _, r['hr_lo'], r['hr_hi'] = M.bootstrap(C, M.rank_order_H, 200, rng)
    r['hr_base'] = M.basale(C, M.rank_order_H, 50, rng)[0]
    rows.append(r)
    for nid in p.index:
        v = p.loc[nid].to_numpy(float)
        nil.append(dict(anno=int(anno), id_nil=int(nid), residenti=int(v.sum()), a65=int(v[65:].sum()), u35=int(v[:35].sum()), a2534=int(v[25:35].sum()),
                        a75=int(v[75:].sum()), eta_somma=float((v * (ET + 0.5)).sum())))
    print(anno, round(r['d'], 3), round(r['d_base'], 3), round(r['hr'], 4), round(r['hr_base'], 4), flush=True)
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'eta_serie.csv'), index=False, float_format='%.5f')
pd.DataFrame(nil).to_csv(os.path.join(OUT, 'eta_nil.csv'), index=False, float_format='%.3f')
json.dump(log, open(os.path.join(OUT, 'eta_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
