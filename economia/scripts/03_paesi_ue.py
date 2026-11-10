"""PIL 2023 dei 27 paesi dell'UE (Eurostat nama_10_gdp, B1GQ, CP_MEUR = milioni di euro a prezzi correnti).
Scarica la tabella intera, la salva in raw/ e aggiorna paesi_pil_2023 in docs/economia/data/riepilogo.json.
Da lanciare dopo 02_elabora.py:  python -I -X utf8 economia/scripts/03_paesi_ue.py"""
import os, gzip, json, urllib.request
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(B, 'raw'); os.makedirs(R, exist_ok=True)
dest = os.path.join(R, 'nama_10_gdp.tsv.gz')
URL = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/nama_10_gdp?format=TSV&compressed=true'
if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
    req = urllib.request.Request(URL, headers={'User-Agent': 'milano-in-dati/1.0'})
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, 'wb') as f: f.write(r.read())
NOMI = dict(AT='Austria', BE='Belgio', BG='Bulgaria', HR='Croazia', CY='Cipro', CZ='Cechia', DK='Danimarca', EE='Estonia', FI='Finlandia', FR='Francia', DE='Germania', EL='Grecia', HU='Ungheria', IE='Irlanda', IT='Italia', LV='Lettonia', LT='Lituania', LU='Lussemburgo', MT='Malta', NL='Paesi Bassi', PL='Polonia', PT='Portogallo', RO='Romania', SK='Slovacchia', SI='Slovenia', ES='Spagna', SE='Svezia')
out = {}
with gzip.open(dest, 'rt', encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t'); cols = [c.strip() for c in head]; i23 = cols.index('2023')
    for ln in f:
        p = ln.rstrip('\n').split('\t'); k = p[0].split(',')   # freq,unit,na_item,geo
        if k[0] == 'A' and k[1] == 'CP_MEUR' and k[2] == 'B1GQ' and k[3] in NOMI:
            v = p[i23].strip().split(' ')[0]
            if v and v != ':': out[NOMI[k[3]]] = float(v)
assert len(out) == 27, len(out)
fp = os.path.join(os.path.dirname(B), 'docs', 'economia', 'data', 'riepilogo.json')
d = json.load(open(fp, encoding='utf-8')); d['paesi_pil_2023'] = out
json.dump(d, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
mi = d['pil_mi_2023']; print(len(out), 'paesi; Milano', mi, 'posto', 1 + sum(1 for v in out.values() if v > mi))
