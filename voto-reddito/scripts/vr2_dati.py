"""Prepara i dati della pagina "Voto e reddito" (versione 2): Centrosinistra e Centrodestra per CAP.
Legge docs/voto-reddito/data/elezioni.json e cap_reddito.csv (già pubblicati), scrive:
  docs/voto-reddito/data/vr2_coalizioni.json   (nuovo)
  docs/voto-reddito/data/vr2_cap_mappa.geojson (nuovo, copia dei confini dei CAP di docs/redditi/data)
Centrosinistra = blocco Sinistra + Centrosinistra; Centrodestra = blocco Centrodestra + Lega + Destra
(stesse famiglie di liste di docs/elezioni; I Riformisti 2021 nel Centrosinistra; nessun Centro nel 2016)."""
import json, csv, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'voto-reddito', 'data')
E = json.load(open(os.path.join(D, 'elezioni.json'), encoding='utf-8'))
caps = E['caps']
rows = {int(r['cap']): r for r in csv.DictReader(open(os.path.join(D, 'cap_reddito.csv'), encoding='utf-8-sig'))}
NOMI = {20121:'Brera',20122:'Guastalla',20123:'Duomo',20124:'Porta Venezia',20125:'Maciachini',20126:'Gorla',20127:'Loreto',20128:'Precotto',20129:'Monforte',20131:'Casoretto',20132:'Cimiano',20133:'Città Studi',20134:'Lambrate',20135:'Porta Romana',20136:'Ticinese',20137:'Calvairate',20138:'Forlanini',20139:'Corvetto',20141:'Stadera',20142:'Gratosoglio',20143:'Conchetta',20144:'Porta Magenta',20145:'Pagano',20146:'Bande Nere',20147:'Lorenteggio',20148:'San Siro',20149:'De Angeli',20151:'Gallaratese',20152:'Baggio',20153:'Valsesia',20154:'Sarpi',20155:'Ghisolfa',20156:'Villapizzone',20157:'Quarto Oggiaro',20158:'Bovisa',20159:'Isola',20161:'Affori',20162:'Niguarda'}
red = {c: float(rows[c]['reddito_2019_22_euro2025']) for c in caps}
ordine = sorted(caps, key=lambda c: -red[c])
rank = {c: i + 1 for i, c in enumerate(ordine)}
EL = [('comunali_consiglio_2016-06-05', 'Comunali 2016'), ('camera_2018-03-04', 'Politiche 2018'),
      ('regionali_consiglio_2018-03-04', 'Regionali 2018'), ('europee_2019-05-26', 'Europee 2019'),
      ('comunali_consiglio_2021-10-03', 'Comunali 2021'), ('camera_2022-09-25', 'Politiche 2022'),
      ('regionali_consiglio_2023-02-12', 'Regionali 2023'), ('europee_2024-06-08', 'Europee 2024')]
byid = {e['id']: e for e in E['elezioni']}
def voce(e, pref):
    return [v for v in e['voci'] if v['n'].startswith(pref)][0]
def pack(v):
    return {'city': v['city'], 'dec': v['dec'], 'cap': v['cap']}
out = {'caps': [{'c': c, 'n': NOMI[c], 'r': round(red[c]), 'rk': rank[c]} for c in caps], 'el': []}
for i, l in EL:
    e = byid[i]
    ce = [v for v in e['voci'] if v['n'] == 'Centro']
    out['el'].append({'id': i, 'l': l, 'y': e['anno'], 'uf': bool(e['ufficiose']),
                      'cs': pack(voce(e, 'Sx (')), 'cd': pack(voce(e, 'Dx (')), 'af': pack(voce(e, 'AFFLUENZA')),
                      'ce': pack(ce[0]) if ce else None})
out['rif'] = [v for v in byid['comunali_consiglio_2021-10-03']['voci'] if v['n'].startswith('lista: I RIFORMISTI')][0]['city']
# altre elezioni per l'affluenza (i soli punti usati: tre elezioni)
out['dec'] = E and json.load(open(os.path.join(D, 'pagina.json'), encoding='utf-8'))['decili']
json.dump(out, open(os.path.join(D, 'vr2_coalizioni.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
g = json.load(open(os.path.join(R, 'docs', 'redditi', 'data', 'cap_zone_ricostruite.geojson'), encoding='utf-8'))
json.dump(g, open(os.path.join(D, 'vr2_cap_mappa.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out['el']), 'elezioni;', len(g['features']), 'CAP')
