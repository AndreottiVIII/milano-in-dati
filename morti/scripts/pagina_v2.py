"""Pagina Morti v2: crea tre file NUOVI in docs/morti/data/ (non tocca quelli vecchi).
Uso: python -I -X utf8 pagina_v2.py <cartella morti> <cartella docs/morti/data>
  tabella_mesi_anni.json   mese per mese 2011-2026 (morti, normale, differenza %), con i mesi delle ondate di caldo
  eta_sesso_anno.json      morti per anno, fascia di eta (10 anni) e sesso, 2011-2025
  caldo_giorni_estate.json giorni di giugno-agosto 2014-2025: massima di Brera, morti, normale
Fonti: i file gia' elaborati in pulito/ (ISTAT CC BY 4.0, temperature di Brera)."""
import sys, os, json, csv, datetime as dt
from collections import defaultdict
M, OUT = sys.argv[1], sys.argv[2]
PUL = os.path.join(M, 'pulito')

# ---- giorno per giorno (2014-2026) con normale B e massima
giorni = []
with open(os.path.join(PUL, 'milano_giorno.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        a = float(r['attesi_B']) if r.get('attesi_B') else None
        giorni.append(dict(d=r[''] if '' in r else list(r.values())[0], morti=float(r['morti']), att=a,
                           tx=float(r['TX']) if r.get('TX') not in (None, '') else None))
print('giorni', len(giorni), giorni[0], giorni[-1])

# ---- 2011-2013: solo morti (dal file per eta e sesso)
mes = defaultdict(float)      # (anno, mese) -> morti
eta = defaultdict(lambda: [[0] * 8, [0] * 8])  # anno -> [M[8], F[8]]
def banda(c):
    if c <= 8: return 0
    if c <= 10: return 1
    if c <= 12: return 2
    if c <= 14: return 3
    if c <= 16: return 4
    if c <= 18: return 5
    if c <= 20: return 6
    return 7
with open(os.path.join(PUL, 'decessi_giorno_eta_sesso.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['scope'] != 'Milano': continue
        y, m = int(r['data'][:4]), int(r['data'][5:7])
        mes[(y, m)] += int(r['T'])
        if y <= 2025:
            b = banda(int(r['cl_eta']))
            eta[y][0][b] += int(r['M']); eta[y][1][b] += int(r['F'])

# ---- mensile con normale
att = defaultdict(float)
for g in giorni:
    y, m = int(g['d'][:4]), int(g['d'][5:7])
    if g['att'] is not None: att[(y, m)] += g['att']
# ondate di caldo per mese (giorni dell'ondata, non la coda)
ond = []
with open(os.path.join(PUL, 'ondate_caldo.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f): ond.append(r)
caldo_mese = defaultdict(list)
for o in ond:
    a = dt.date.fromisoformat(o['inizio']); b = dt.date.fromisoformat(o['fine'])
    mesi = {(a.year, a.month), (b.year, b.month)}
    for k in mesi:
        caldo_mese[k].append(dict(inizio=o['inizio'], fine=o['fine'], tx_max=float(o['tx_max']), eccesso=float(o['eccesso_B']), pct=float(o['pct_B'])))
righe = []
ult = max(k for k in mes if k[0] == 2026 and (k[0], k[1]) in att)
for y in range(2011, 2027):
    for m in range(1, 13):
        if (y, m) not in mes: continue
        if y == 2026 and m > 6: continue
        a = att.get((y, m))
        o = dict(anno=y, mese=m, morti=int(mes[(y, m)]))
        if a:
            o['normale'] = round(a, 1); o['pct'] = round((mes[(y, m)] / a - 1) * 100, 1)
        if (y, m) in caldo_mese:
            o['ondate'] = caldo_mese[(y, m)]
        righe.append(o)
json.dump(dict(origine='ISTAT, decessi giornalieri per comune di residenza (CC BY 4.0), elaborazione Milano in dati; normale B = media dello stesso giorno nei 5 anni precedenti senza 2020 e 2021',
               mesi=righe), open(os.path.join(OUT, 'tabella_mesi_anni.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

json.dump(dict(origine='ISTAT, decessi giornalieri per comune di residenza (CC BY 4.0), Milano',
               fasce=['0-39', '40-49', '50-59', '60-69', '70-79', '80-89', '90-99', '100 e più'],
               anni={str(y): dict(M=eta[y][0], F=eta[y][1]) for y in sorted(eta)}),
          open(os.path.join(OUT, 'eta_sesso_anno.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---- caldo, giorno per giorno
est = [g for g in giorni if g['tx'] is not None and g['att'] and g['d'][5:7] in ('06', '07', '08') and 2014 <= int(g['d'][:4]) <= 2025]
indo = set()
for o in ond:
    a = dt.date.fromisoformat(o['inizio']); b = dt.date.fromisoformat(o['fine'])
    while a <= b: indo.add(a.isoformat()); a += dt.timedelta(days=1)
pts = [[g['d'], g['tx'], int(g['morti']), round(g['att'], 1), 1 if g['d'] in indo else 0] for g in est]
classi = [(-99, 27, 'sotto 27'), (27, 30, '27-30'), (30, 33, '30-33'), (33, 36, '33-36'), (36, 99, 'sopra 36')]
cl = []
for lo, hi, n in classi:
    s = [g for g in est if lo < g['tx'] <= hi]
    if not s: continue
    cl.append(dict(nome=n, giorni=len(s), morti=sum(g['morti'] for g in s), normale=round(sum(g['att'] for g in s), 1),
                   rapporto=round(sum(g['morti'] for g in s) / sum(g['att'] for g in s), 3)))
json.dump(dict(origine='ISTAT (CC BY 4.0), temperature di Brera; giugno-agosto 2014-2025; giorno: [data, massima, morti, normale, dentro un\'ondata]',
               giorni=pts, classi=cl), open(os.path.join(OUT, 'caldo_giorni_estate.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(righe), 'mesi;', len(pts), 'giorni estate;', cl)
top = sorted(est, key=lambda g: -g['tx'])[:12]
print([(g['d'], g['tx'], g['morti'], g['att']) for g in top])
top = sorted(est, key=lambda g: -(g['morti'] - g['att']))[:10]
print([(g['d'], g['tx'], g['morti'], g['att']) for g in top])
