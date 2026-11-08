#!/usr/bin/env python3
"""Costo della vita, giro 3: indici annui 2005-2025 (2005 = 100) di 22 voci e di 9 gruppi di spesa.

Uso (percorsi assoluti):
    python -I -X utf8 <...>/costo-vita/scripts/build_extra_v3.py <...>/costo-vita <...>/docs/costo-vita/data

Legge costo-vita/pulito/nic_milano_voci_base2015.csv (indici mensili del Comune di Milano su dati ISTAT, CC BY)
e docs/costo-vita/data/paniere_v2.json (indice generale 2005-2025). Scrive voci_annue_2005_100_v3.json.
Media annua = media dei mesi presenti (gli zeri sono dati mancanti); si tiene solo chi ha tutti gli anni 2005-2025.
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

C, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NOMI = {
 'pane':'Pane','pasta':'Pasta','latte':'Latte','uova':'Uova','caffe_prodotto':'Caffè in pacco','ristoranti':'Ristoranti e pizzerie',
 'affitti':'Affitti (contratti in corso)','acqua':'Acqua','rifiuti':'Tassa rifiuti','elettricita':'Luce','gas':'Gas','benzina':'Benzina',
 'bus_tram_metro':'Trasporto urbano','taxi':'Taxi','treno':'Treno','cinema_teatri':'Cinema e teatri','alberghi':'Alberghi','giornali':'Giornali',
 'libri_scolastici':'Libri scolastici','telefonia_mobile':'Telefono','medicinali':'Medicinali','sigarette':'Sigarette','univ':'Università','assic_auto':'Assicurazione auto'}
GRUPPI = [
 ('casa','Affitto',['affitti']),
 ('energia','Luce, gas, acqua',['elettricita','gas','acqua']),
 ('spesa','Spesa al supermercato',['pane','pasta','latte','uova']),
 ('fuori','Ristoranti e pizzerie',['ristoranti']),
 ('benzina','Benzina',['benzina']),
 ('mezzi','Mezzi pubblici e treno',['bus_tram_metro','treno']),
 ('assic','Assicurazione auto',['assic_auto']),
 ('telefono','Telefono',['telefonia_mobile']),
 ('svago','Cinema, teatro, alberghi',['cinema_teatri','alberghi'])]
YS = list(range(2005, 2026))
m = defaultdict(lambda: defaultdict(list))
with open(C/'pulito'/'nic_milano_voci_base2015.csv', encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f, delimiter=';'):
        v = float(r['indice_base2015_100'] or 0)
        if v > 0: m[r['voce']][int(r['periodo'][:4])].append(v)
def ann(k):
    d = m[k]
    if any(y not in d for y in YS) or len(d[2005]) < 12: return None
    a = {y: sum(d[y])/len(d[y]) for y in YS}
    return {y: a[y]/a[2005]*100 for y in YS}
voci, S = [], {}
for k, n in NOMI.items():
    s = ann(k)
    if s is None: print('scartata', k); continue
    S[k] = s
    voci.append({'id': k, 'nome': n, 'serie': [round(s[y], 2) for y in YS]})
gr = []
for gid, n, mem in GRUPPI:
    gr.append({'id': gid, 'nome': n, 'voci': mem, 'serie': [round(sum(S[k][y] for k in mem)/len(mem), 2) for y in YS]})
P = json.load(open(OUT/'paniere_v2.json', encoding='utf-8'))
gen = [P['indice_generale_2005_100'][str(y)] for y in YS]
json.dump({'generato_da': 'costo-vita/scripts/build_extra_v3.py', 'anni': YS, 'generale': gen, 'voci': voci, 'gruppi': gr,
           'fonte': 'Comune di Milano su dati ISTAT, CC BY; medie annue, 2005 = 100'},
          open(OUT/'voci_annue_2005_100_v3.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(voci), 'voci', len(gr), 'gruppi')
