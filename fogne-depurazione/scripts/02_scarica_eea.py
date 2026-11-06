"""Scarica dal servizio pubblico EEA (WISE UWWTD, ArcGIS REST) i record italiani di
depuratori, agglomerati e punti di scarico, rapporti 2020 e 2022 (dati 2018 e 2020-2022).
Uso: python -I -X utf8 02_scarica_eea.py <cartella_raw>
Scrive <raw>/eea/<layer>_IT.json (tutte le pagine unite). Riprendibile.
"""
import json, sys, time, pathlib
import requests

H = {'User-Agent': 'milano-in-dati/1.0'}
B = 'https://water.discomap.eea.europa.eu/arcgis/rest/services/WISE_UWWTD/{}/MapServer/0/query'
LAYERS = ['TreatmentPlants_2022', 'TreatmentPlants_2020', 'Agglomerations_2022', 'Agglomerations_2020',
          'DischargePoints_2022', 'DischargePoints_2020']
out = pathlib.Path(sys.argv[1]) / 'eea'
out.mkdir(parents=True, exist_ok=True)
for L in LAYERS:
    f = out / f'{L}_IT.json'
    if f.exists():
        print(L, 'gia presente'); continue
    righe, off = [], 0
    while True:
        p = {'where': "rptMStateKey='IT'", 'outFields': '*', 'returnGeometry': 'false', 'f': 'json',
             'resultOffset': off, 'resultRecordCount': 2000, 'orderByFields': 'OBJECTID'}
        for tent in range(4):
            try:
                r = requests.get(B.format(L), params=p, headers=H, timeout=180)
                r.raise_for_status(); d = r.json(); break
            except Exception as e:
                print('  riprovo', L, off, e); time.sleep(20)
        else:
            raise SystemExit('fallito ' + L)
        feat = [x['attributes'] for x in d.get('features', [])]
        righe += feat
        print(L, off, len(feat))
        time.sleep(4)
        if not d.get('exceededTransferLimit') and len(feat) < 2000:
            break
        off += len(feat)
    f.write_text(json.dumps(righe, ensure_ascii=False), encoding='utf-8')
    print(L, 'totale', len(righe))
