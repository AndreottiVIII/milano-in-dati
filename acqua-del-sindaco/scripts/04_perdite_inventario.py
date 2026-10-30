"""Passo 4 - dataset perdite idriche (ISTAT via Comune) + inventario delle fonti.
Uso: python -I 04_perdite_inventario.py <cartella_strand>"""
import sys, os, json, glob
import pandas as pd
BASE = sys.argv[1]
OUT = os.path.join(BASE, 'pulito')
j = json.load(open(glob.glob(os.path.join(BASE, 'raw', 'ds1571*', '*.json'))[0] if False else glob.glob(os.path.join(BASE, 'raw', 'ds1571*', 'ds1571*.json'))[0], encoding='utf-8'))
r = j[0]
k = list(r.keys())
imm, imm_pc, ero, ero_pc, perd = (r[x] for x in k)
pkg = json.load(open(os.path.join(BASE, 'raw', os.path.basename(os.path.dirname(glob.glob(os.path.join(BASE, 'raw', 'ds1571*', 'ds1571*.json'))[0])), '_package.json'), encoding='utf-8'))
tmp = json.loads(pkg['temporal_coverage'])[0]
df = pd.DataFrame([dict(
    anno=2018, periodo_dal=tmp['temporal_start'], periodo_al=tmp['temporal_end'],
    immessa_volume=imm, erogata_volume=ero, immessa_procapite=imm_pc, erogata_procapite=ero_pc,
    perdite_pct_dichiarata=perd,
    perdite_volume_calcolato=imm - ero,
    perdite_pct_calcolata=round(100 * (imm - ero) / imm, 2),
    popolazione_implicita=round(imm * 1e6 / (imm_pc * 365)),
    unita_volume='migliaia di m3 (DEDOTTO, il file non lo scrive)',
    unita_procapite='litri per abitante al giorno (DEDOTTO)',
    fonte='ISTAT, tavola 17 GMA 2021 (via Comune di Milano, dataset ds1571)',
    file_origine='ds1571_acqua_immessa_erogata_perdite_idriche.json/.csv')])
df.to_csv(os.path.join(OUT, 'perdite.csv'), sep=';', index=False, encoding='utf-8')
print(df.T.to_string())

# inventario fonti
inv = json.load(open(os.path.join(BASE, 'raw', '_inventario.json'), encoding='utf-8'))
righe = []
for x in inv:
    p = json.load(open(os.path.join(BASE, 'raw', x['dataset'], '_package.json'), encoding='utf-8'))
    res = [rr for rr in p['resources'] if rr['url'] == x['url']][0]
    righe.append(dict(dataset=x['dataset'], titolo=p['title'], file=x['file'], formato=x['format'], byte=x['size_real'],
                      licenza_ckan=p.get('license_id'), licenza_risorsa=res.get('license_type', ''),
                      creato=p['metadata_created'][:10], modificato=p['metadata_modified'][:10], url=x['url']))
pd.DataFrame(righe).to_csv(os.path.join(OUT, 'inventario_fonti.csv'), sep=';', index=False, encoding='utf-8')
print(pd.DataFrame(righe)[['dataset', 'formato', 'byte', 'licenza_ckan', 'licenza_risorsa']].to_string())
