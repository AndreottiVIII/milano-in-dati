"""Milanesi iscritti all'AIRE (anagrafe degli italiani residenti all'estero), Comune di Milano, CC BY 4.0.
Legge i tre file in milanesi-estero/raw/ (ds355 2016-2020 per paese e motivo, ds1961 2021-2022 per paese, ds1962 2021-2022 per motivo)
e scrive docs/comunita/data/estero.json.
Uso, dalla cartella del progetto:  python -I -X utf8 milanesi-estero/scripts/01_elabora.py"""
import csv, glob, json, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
OUT = os.path.join(os.path.dirname(ROOT), 'docs', 'comunita', 'data', 'estero.json')


def rd(p):
    return list(csv.DictReader(open(glob.glob(os.path.join(RAW, p))[0], encoding='utf-8-sig'), delimiter=';'))


NOME = {"Stati Uniti D'America": 'Stati Uniti', 'Cinese, Rep. Popolare': 'Cina', 'Russa, Federazione': 'Russia', 'Ceca, Rep.': 'Cechia',
        'Corea del Sud, Rep.': 'Corea del Sud', 'Dominicana, Rep.': 'Rep. Dominicana', 'Emirati Arabi Uniti': 'Emirati Arabi'}
paese = collections.defaultdict(lambda: collections.defaultdict(int))
motivo = collections.defaultdict(lambda: collections.defaultdict(int))
for r in rd('ds355*.csv'):
    y, n = int(r['Anno']), int(r['Numerosità'])
    paese[NOME.get(r['Nazione di residenza'], r['Nazione di residenza'])][y] += n
    motivo[y][r["Motivo iscrizione all'estero"]] += n
for r in rd('ds1961*.csv'):
    y, n = int(r['Anno']), int(r['Numerosità'])
    paese[NOME.get(r['Nazione di residenza'], r['Nazione di residenza'])][y] += n
for r in rd('ds1962*.csv'):
    motivo[int(r['Anno'])][r["Motivo iscrizione all'estero"]] += int(r['Numerosità'])

ANNI = list(range(2016, 2023))
totale = [sum(p[y] for p in paese.values()) for y in ANNI]
assert totale == [sum(motivo[y].values()) for y in ANNI], 'i totali per paese e per motivo non tornano'
top = sorted(paese, key=lambda p: -paese[p][2022])[:10]
# controllo: i paesi che erano nei primi 10 nel 2016 devono esserci
top16 = sorted(paese, key=lambda p: -paese[p][2016])[:10]
extra = [p for p in top16 if p not in top]
mot = {'emigrazione': "all'emigrazione", 'nascita': 'per nascita', 'cittadinanza': 'per acquisto cittadinanza'}
serie_mot = {k: [motivo[y][v] for y in ANNI] for k, v in mot.items()}
serie_mot['altri'] = [totale[i] - sum(serie_mot[k][i] for k in mot) for i in range(len(ANNI))]
out = {'anni': ANNI, 'totale': totale,
       'paesi': {p: [paese[p][y] for y in ANNI] for p in top + extra}, 'primi10_2022': top, 'primi10_2016': top16,
       'motivi': serie_mot, 'altri_residenza_2022': motivo[2022]["per residenza all'estero"], 'n_paesi_2022': sum(1 for p in paese if paese[p][2022] > 0)}
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(totale, top, extra, serie_mot, out['n_paesi_2022'])
print({p: paese[p][2016] for p in top16})
