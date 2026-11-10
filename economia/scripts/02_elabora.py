"""Legge le tabelle Eurostat scaricate da 01_scarica.py e scrive i file della pagina in docs/economia/data/.
Uso, dalla cartella del progetto:  python -I -X utf8 economia/scripts/02_elabora.py"""
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import load
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
OUT = os.path.join(os.path.dirname(ROOT), 'docs', 'economia', 'data')
os.makedirs(OUT, exist_ok=True)
T = lambda n: load(os.path.join(RAW, n + '.tsv.gz'))[1]
gdp, pop, emp, gva, met = T('nama_10r_3gdp'), T('nama_10r_3popgdp'), T('nama_10r_3empers'), T('nama_10r_3gva'), T('met_10r_3gdp')


def pick(L, **kw):
    for k, v in L:
        if all(k.get(a) == b for a, b in kw.items()):
            return v
    raise KeyError(kw)


ANNI = list(range(2000, 2024))
r1 = lambda x, n=1: round(x, n)
MI, MB, IT = 'ITC4C', 'ITC4D', 'IT'
PROV = [('Milano', 'ITC4C'), ('Roma', 'ITI43'), ('Torino', 'ITC11'), ('Napoli', 'ITF33'), ('Bologna', 'ITH55')]

# ---- 1. PIL e quota sull'Italia (prezzi correnti)
pil = {c: pick(gdp, unit='MIO_EUR', geo=c) for c in (MI, MB, IT)}
quota = [100 * pil[MI][y] / pil[IT][y] for y in ANNI]
quota_mb = [100 * (pil[MI][y] + pil[MB][y]) / pil[IT][y] for y in ANNI]

# ---- 2. euro di oggi: deflatore nazionale del valore aggiunto (prezzi dell'anno precedente)
cp = pick(gva, unit='CP_MEUR', nace_r2='TOTAL', geo=IT)
pyp = pick(gva, unit='PYP_MEUR', nace_r2='TOTAL', geo=IT)
P = {2000: 1.0}
for y in range(2001, 2024):
    P[y] = P[y - 1] * cp[y] / pyp[y]
reale = [pil[MI][y] * P[2023] / P[y] for y in ANNI]
reale_it = [pil[IT][y] * P[2023] / P[y] for y in ANNI]

# ---- 3. PIL per abitante (euro correnti)
pc = {n: pick(gdp, unit='EUR_HAB', geo=c) for n, c in PROV}
pc['Italia'] = pick(gdp, unit='EUR_HAB', geo=IT)
tutte = {k['geo']: v for k, v in gdp if k['unit'] == 'EUR_HAB' and k['geo'].startswith('IT') and len(k['geo']) == 5 and 2023 in v}
ordine = sorted(tutte, key=lambda c: -tutte[c][2023])
rango_pc = ordine.index(MI) + 1
sec_pc = tutte[ordine[1]][2023]
tot23 = {k['geo']: v[2023] for k, v in gdp if k['unit'] == 'MIO_EUR' and k['geo'].startswith('IT') and len(k['geo']) == 5 and 2023 in v}
rango_pil = sorted(tot23, key=lambda c: -tot23[c]).index(MI) + 1

# ---- 4. paesi europei a confronto (PIL 2023, milioni di euro)
paesi = {'EL': 'Grecia', 'HU': 'Ungheria', 'PT': 'Portogallo', 'CZ': 'Cechia', 'RO': 'Romania'}
paesi_pil = {n: pick(gdp, unit='MIO_EUR', geo=c)[2023] for c, n in paesi.items()}

# ---- 5. abitanti, occupati, PIL: quota di Milano sull'Italia
popm, popi = pick(pop, geo=MI), pick(pop, geo=IT)
empm = pick(emp, geo=MI, wstatus='EMP', nace_r2='TOTAL')
empi = pick(emp, geo=IT, wstatus='EMP', nace_r2='TOTAL')
pesi = {str(y): {'abitanti': 100 * popm[y] / popi[y], 'occupati': 100 * empm[y] / empi[y], 'pil': quota[ANNI.index(y)]} for y in (2000, 2008, 2023)}
gva_m, gva_i = pick(gva, unit='CP_MEUR', nace_r2='TOTAL', geo=MI), cp
per_occ = {'milano': 1000 * gva_m[2023] / empm[2023], 'italia': 1000 * gva_i[2023] / empi[2023]}  # euro per occupato

# ---- 6. settori (valore aggiunto 2023)
SET = [('A', 'Agricoltura'), ('B-E', 'Industria'), ('F', 'Costruzioni'), ('G-I', 'Commercio, trasporti, alberghi e ristoranti'),
       ('J', 'Informatica e comunicazione'), ('K', 'Banche e assicurazioni'), ('L', 'Immobiliare'), ('M_N', 'Professioni e servizi alle imprese'),
       ('O-Q', 'Pubblica amministrazione, scuola e sanità'), ('R-U', 'Cultura, sport e altri servizi')]
tm, ti = gva_m[2023], gva_i[2023]
settori = []
for cod, nome in SET:
    vm = pick(gva, unit='CP_MEUR', nace_r2=cod, geo=MI)
    vi = pick(gva, unit='CP_MEUR', nace_r2=cod, geo=IT)
    settori.append({'cod': cod, 'nome': nome, 'mi': r1(vm[2023]), 'it': r1(vi[2023]), 'quota': r1(100 * vm[2023] / vi[2023], 2),
                    'quota_2008': r1(100 * vm[2008] / vi[2008], 2), 'peso_mi': r1(100 * vm[2023] / tm, 1), 'peso_it': r1(100 * vi[2023] / ti, 1)})
somma = sum(s['mi'] for s in settori)

# ---- 7. aree metropolitane europee (potere d'acquisto, UE = 100)
mi_idx = {k['metroreg']: v for k, v in met if k['unit'] == 'PPS_HAB_EU27_2020'}
mi_pps = {k['metroreg']: v for k, v in met if k['unit'] == 'PPS_EU27_2020_HAB'}


def classifica(y):
    return sorted(((v[y], c) for c, v in mi_idx.items() if y in v and len(c) > 4 and not c.endswith('_NM')), reverse=True)


def posizione(r, y):
    v = mi_idx['IT002M'][y]
    return 1 + sum(1 for x, c in r if x > v)


r00, r21 = classifica(2000), classifica(2021)
CITTA = [('IT002M', 'Milano', 'mi'), ('IT001MC', 'Roma', 'it'), ('IT004M', 'Torino', 'it'), ('IT009M', 'Bologna', 'it'), ('IT003M', 'Napoli', 'it'),
         ('DE003M', 'Monaco', 'x'), ('FR001MC', 'Parigi', 'x'), ('SE001MC', 'Stoccolma', 'x'), ('DE005M', 'Francoforte', 'x'), ('NL002MC', 'Amsterdam', 'x'),
         ('DE002M', 'Amburgo', 'x'), ('AT001MC', 'Vienna', 'x'), ('ES001MC', 'Madrid', 'x'), ('ES002M', 'Barcellona', 'x'), ('DE001MC', 'Berlino', 'x'),
         ('DK001MC', 'Copenaghen', 'x'), ('PL001MC', 'Varsavia', 'x'), ('CZ001MC', 'Praga', 'x'), ('RO001MC', 'Bucarest', 'x'), ('PT001MC', 'Lisbona', 'x'),
         ('EL001MC', 'Atene', 'x'), ('HU001MC', 'Budapest', 'x')]
europa = [{'cod': c, 'nome': n, 'tipo': t, 'v2000': mi_idx[c][2000], 'v2021': mi_idx[c][2021]} for c, n, t in CITTA]
eu = {'rango_2000': posizione(r00, 2000), 'su_2000': len(r00), 'rango_2021': posizione(r21, 2021), 'su_2021': len(r21),
      'pps_2000': mi_pps['IT002M'][2000], 'pps_2021': mi_pps['IT002M'][2021]}

riep = {
    'meta': {'anni': ANNI, 'ultimo': 2023, 'salto': 2008},
    'quota': {'milano_mln': [r1(pil[MI][y]) for y in ANNI], 'italia_mln': [r1(pil[IT][y]) for y in ANNI], 'quota': [r1(x, 2) for x in quota],
              'monza_mln': [r1(pil[MB][y]) for y in ANNI], 'quota_con_monza': [r1(x, 2) for x in quota_mb]},
    'reale': {'milano_euro2023_mln': [r1(x) for x in reale], 'italia_euro2023_mln': [r1(x) for x in reale_it], 'prezzi_2023_su_2000': r1(P[2023], 3)},
    'pc': {n: [v[y] for y in ANNI] for n, v in pc.items()},
    'pc_rango': {'milano': rango_pc, 'su': len(tutte), 'seconda_provincia_2023': sec_pc, 'seconda': ordine[1]},
    'pil_rango': rango_pil, 'paesi_pil_2023': paesi_pil,
    'pesi': {a: {b: r1(c, 2) for b, c in d.items()} for a, d in pesi.items()}, 'per_occupato': {a: r1(b) for a, b in per_occ.items()},
    'occupati_mi': [empm[y] for y in ANNI], 'abitanti_mi': [popm[y] for y in ANNI],
    'settori': settori, 'va_totale_mi_2023': tm, 'va_totale_it_2023': ti, 'pil_mi_2023': pil[MI][2023], 'pil_it_2023': pil[IT][2023],
    'europa': europa, 'eu': eu,
}
with open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8') as f:
    json.dump(riep, f, ensure_ascii=False, separators=(',', ':'))


def csvw(nome, head, rows):
    with open(os.path.join(OUT, nome), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(head)
        w.writerows(rows)


csvw('quota_pil.csv', ['anno', 'pil_milano_milioni_euro', 'pil_italia_milioni_euro', 'quota_milano_su_italia_pct', 'quota_milano_e_monza_pct', 'pil_milano_euro_2023_milioni'],
     [[y, r1(pil[MI][y]), r1(pil[IT][y]), r1(quota[i], 2), r1(quota_mb[i], 2), r1(reale[i])] for i, y in enumerate(ANNI)])
csvw('pil_per_abitante.csv', ['anno'] + list(pc), [[y] + [pc[n][y] for n in pc] for y in ANNI])
csvw('settori_2023.csv', ['codice', 'settore', 'valore_aggiunto_milano_milioni', 'valore_aggiunto_italia_milioni', 'quota_milano_su_italia_pct', 'peso_nel_totale_milano_pct', 'peso_nel_totale_italia_pct'],
     [[s['cod'], s['nome'], s['mi'], s['it'], s['quota'], s['peso_mi'], s['peso_it']] for s in settori])
csvw('europa_pps.csv', ['codice_eurostat', 'citta', 'indice_ue100_2000', 'indice_ue100_2021'], [[e['cod'], e['nome'], e['v2000'], e['v2021']] for e in europa])

print('quota 2000, 2007, 2008, 2023:', [r1(quota[ANNI.index(y)], 2) for y in (2000, 2007, 2008, 2023)])
print('con Monza 2023', r1(quota_mb[-1], 2), 'PIL', riep['pil_mi_2023'], 'pc', pc['Milano'][2023], pc['Italia'][2023], 'rango pc', rango_pc, 'pil', rango_pil)
print('reale 2000->2023', r1(reale[-1] / reale[0] * 100 - 100), r1(reale_it[-1] / reale_it[0] * 100 - 100), 'dal 2008', r1(reale[-1] / reale[8] * 100 - 100), r1(reale_it[-1] / reale_it[8] * 100 - 100))
print('pesi', pesi, per_occ, 'somma settori', somma, tm)
print('eu', eu, paesi_pil)
for s in settori:
    print(s)
print('pc rel', {n: (r1(100 * pc[n][2000] / pc['Italia'][2000]), r1(100 * pc[n][2023] / pc['Italia'][2023])) for n in pc})
