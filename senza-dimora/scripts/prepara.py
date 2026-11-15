"""Prepara i dati della pagina «Senza dimora» (persone senza tetto e senza fissa dimora iscritte in anagrafe, Milano).
Uso: python -I -X utf8 prepara.py <cartella milano-in-dati>
Legge censimenti/pulito/sezioni_2001/2011/2021/2023.csv, indicatori_NIL.csv e docs/senza-dimora/data/citta_2021_2023.csv
(prodotto da citta.py). Scrive in docs/senza-dimora/data/: riepilogo.json, serie.csv, eta_2021_2023.csv, citta.csv."""
import sys, os, csv, json
R = sys.argv[1]
P = os.path.join(R, 'censimenti', 'pulito')
O = os.path.join(R, 'docs', 'senza-dimora', 'data')
def sez(y):
    return list(csv.DictReader(open(os.path.join(P, 'sezioni_%d.csv' % y), encoding='utf-8')))
def num(x):
    return float(x) if x not in ('', None) else 0.0
cfg = {2001: ('PRO_COM', 'SEZIONE'), 2011: ('PROCOM', 'SEZ2011'), 2021: ('PROCOM', 'SEZ21_ID'), 2023: ('PROCOM', 'SEZ21_ID')}
out = {'serie': {}, 'eta': {}, 'stran': {}}
fitt = {}
tot = {}
for y in (2001, 2011, 2021, 2023):
    c, k = cfg[y]
    mi = [x for x in sez(y) if int(float(x[c])) == 15146]
    # sezione fittizia: gli ultimi 7 caratteri del codice iniziano con 8888 (2001, 2011) o 88888 (2021, 2023)
    def fi(x):
        s = str(x[k]).split('.')[0]
        return s[-7:].startswith('8888')
    f = [x for x in mi if fi(x)]
    tot[y] = sum(num(x['P1']) for x in mi)
    out['serie'][y] = {'sd': sum(num(x['P1']) for x in f), 'sezioni': len(f), 'abitanti': tot[y]}
    fitt[y] = (mi, f)
for y in (2021, 2023):
    mi, f = fitt[y]
    B = ['P14','P15','P16','P17','P18','P19','P20','P21','P22','P23','P24','P25','P26','P27','P28','P29']
    BM = ['P%d' % i for i in range(30, 46)]
    BF = ['P%d' % i for i in range(67, 83)]
    s = lambda cols, rows: [sum(num(x[c]) for x in rows) for c in cols]
    out['eta'][y] = {'m': s(BM, f), 'f': s(BF, f), 'tot': s(B, f)}
    ita = lambda rows: [sum(num(x[c]) for x in rows) for c in ('IT1', 'IT2', 'IT3')]
    st = lambda rows: [sum(num(x[c]) for x in rows) for c in ('ST22', 'ST23', 'ST24')]
    resto = [x for x in mi if x not in f]
    out['stran'][y] = {'sd': {'ita': ita(f), 'str': st(f), 'tot': sum(num(x['P1']) for x in f), 'uomini': sum(num(x['P2']) for x in f)},
                       'resto': {'ita': ita(resto), 'str': st(resto), 'tot': sum(num(x['P1']) for x in resto), 'uomini': sum(num(x['P2']) for x in resto)}}
# quartieri
nil = [x for x in csv.DictReader(open(os.path.join(P, 'indicatori_NIL.csv'), encoding='utf-8')) if x['anno'] == '2023']
pops = sorted(num(x['pop']) for x in nil)
sd23 = out['serie'][2023]['sd']
out['nil'] = {'n': len(pops), 'meno_di_sd': sum(1 for p in pops if p < sd23), 'tot_nil': sum(pops)}
out['nil_lista'] = sorted([[x['nil_nome'], int(num(x['pop']))] for x in nil], key=lambda r: r[1])
# citta
rows = list(csv.DictReader(open(os.path.join(O, 'citta_2021_2023.csv'), encoding='utf-8')))
out['citta'] = [{'citta': r['citta'], 'ab21': int(r['abitanti_2021']), 'sd21': int(r['senza_dimora_2021']), 'ab23': int(r['abitanti_2023']), 'sd23': int(r['senza_dimora_2023'])} for r in rows]
out['italia_2021'] = 96197
out['stran_italia_2021_pct'] = 38  # dal comunicato ISTAT (non ricalcolato)
json.dump(out, open(os.path.join(O, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(os.path.join(O, 'serie.csv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo, delimiter=';'); w.writerow(['anno', 'iscritti_senza_dimora', 'sezioni_fittizie', 'abitanti_milano'])
    for y in (2001, 2011, 2021, 2023):
        d = out['serie'][y]; w.writerow([y, int(d['sd']), d['sezioni'], int(d['abitanti'])])
with open(os.path.join(O, 'eta_2021_2023.csv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo, delimiter=';'); w.writerow(['anno', 'fascia_eta', 'uomini', 'donne'])
    lab = ['0-4','5-9','10-14','15-19','20-24','25-29','30-34','35-39','40-44','45-49','50-54','55-59','60-64','65-69','70-74','75+']
    for y in (2021, 2023):
        for i, l in enumerate(lab):
            w.writerow([y, l, int(out['eta'][y]['m'][i]), int(out['eta'][y]['f'][i])])
with open(os.path.join(O, 'citta.csv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo, delimiter=';'); w.writerow(['citta', 'abitanti_2021', 'iscritti_2021', 'ogni_10000_2021', 'abitanti_2023', 'iscritti_2023', 'ogni_10000_2023'])
    for c in out['citta']:
        w.writerow([c['citta'], c['ab21'], c['sd21'], round(c['sd21'] / c['ab21'] * 1e4, 1), c['ab23'], c['sd23'], round(c['sd23'] / c['ab23'] * 1e4, 1)])
print(json.dumps({k: out[k] for k in ('serie', 'nil')}, indent=1))
