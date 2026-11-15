"""Serie dal 1880: nati, morti, abitanti e tassi di natalità e mortalità del Comune di Milano.
Fonti (Comune di Milano, CC BY 4.0): ds1495 (nati vivi), ds1494 (popolazione), ds2918 (tassi), ds71 (morti in numero; fino al 2002 coincide con le altre serie, dopo conta i morti avvenuti a Milano e può differire un poco dal tasso di ds2918).
Scrive docs/nascite/data/serie_1880_2024.csv.
Uso (dalla cartella del progetto): python -I -X utf8 nascite/scripts/05_serie_1880.py"""
import csv, glob
B = '_esplorazione/dati/ckan/csv/'
def rd(p):
    return list(csv.DictReader(open(glob.glob(B + p)[0], encoding='utf-8-sig'), delimiter=';'))
pop = {int(r['Anno']): int(r['Popolazione']) for r in rd('ds1494*/*.csv')}
nati = {int(r['Anno']): int(r['Numero Nati']) for r in rd('ds1495*/*.csv')}
tas = {int(r['Anno']): (float(r['Tasso natalità']), float(r['Tasso mortalità'])) for r in rd('ds2918*/*.csv') if r['Tasso natalità']}
mov = {int(r['Anni']): r for r in rd('ds71*/*.csv')}
righe = []
for y in range(1880, 2025):
    m = int(mov[y]['Morti'])
    if y < 2003: assert int(mov[y]['Nati vivi']) == nati[y], y   # dal 2003 ds71 conta i nati avvenuti a Milano, ds1495 quelli di madri residenti
    righe.append([y, pop[y], nati[y], m, tas[y][0], tas[y][1]])
with open('docs/nascite/data/serie_1880_2024.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['anno', 'abitanti', 'nati', 'morti_ds71', 'natalita_per_mille', 'mortalita_per_mille']); w.writerows(righe)
more = [r[0] for r in righe if r[3] > r[2]]
print('anni con più morti che nati (numeri):', more)
print('anni con più morti (tassi):', [r[0] for r in righe if r[5] > r[4]])
print('1951-53:', [r for r in righe if 1949 <= r[0] <= 1955])
