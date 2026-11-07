"""Classe energetica degli attestati (CENED+2, Comune di Milano ds623, CC0) per epoca di costruzione.
Uso: python -I -X utf8 energia.py <cartella_progetto> <cartella_docs>
Legge palazzi/raw_cened/ds623/*.csv, scrive docs/palazzi/data/energia_classi_per_epoca.csv e energia_riepilogo.json.
Solo conteggi aggregati: nessun indirizzo, nessun certificato singolo."""
import csv, glob, json, os, re, sys, collections
P, D = sys.argv[1], sys.argv[2]
f = glob.glob(os.path.join(P, 'palazzi', 'raw_cened', 'ds623', '*.csv'))[0]
BANDE = ['prima del 1930', '1930-1945', '1946-1960', '1961-1976', '1977-1992', '1993-2006', 'dopo il 2006']
def banda(s):
    s = s.strip().lower()
    if s.startswith('prima'): return 0
    if s.startswith('dopo'): return 6
    m = re.fullmatch(r'(\d{4})-(\d{4})', s)
    if m: a = int(m.group(1)); return {1930: 1, 1946: 2, 1961: 3, 1977: 4, 1993: 5}.get(a)
    if re.fullmatch(r'\d{4}', s):
        y = int(s)
        if y < 1800 or y > 2026: return None
        for i, lim in enumerate([1930, 1946, 1961, 1977, 1993, 2007]):
            if y < lim: return i
        return 6
    return None
def classe(c):
    c = c.strip().upper()
    if c.startswith('A'): return 'A'
    return c if c in 'BCDEFG' and len(c) == 1 else None
CL = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
cnt = [collections.Counter() for _ in BANDE]
visti = set(); tot = scartati = 0; date = []
for r in csv.DictReader(open(f, encoding='utf-8', errors='replace'), delimiter=';'):
    if r['COMUNE'].strip().upper() != 'MILANO' or r['RESIDENZIALE'].strip().lower() != 'true': continue
    cod = r['COD_APE']
    if cod in visti: continue
    visti.add(cod); tot += 1
    b, c = banda(r['ANNO_COSTRUZIONE']), classe(r['CLASSE_ENERGETICA'])
    if b is None or c is None: scartati += 1; continue
    cnt[b][c] += 1
    date.append(r['DATA_INS'][-4:])
out = os.path.join(D, 'palazzi', 'data')
with open(os.path.join(out, 'energia_classi_per_epoca.csv'), 'w', encoding='utf-8', newline='') as g:
    w = csv.writer(g); w.writerow(['epoca_costruzione'] + ['classe_' + c for c in CL] + ['totale'])
    for i, b in enumerate(BANDE): w.writerow([b] + [cnt[i][c] for c in CL] + [sum(cnt[i].values())])
ok = sum(sum(c.values()) for c in cnt)
assert ok + scartati == tot
fg = sum(cnt[i][c] for i in range(7) for c in 'FG')
json.dump({'bande': BANDE, 'classi': CL, 'conteggi': [[cnt[i][c] for c in CL] for i in range(7)], 'attestati_residenziali_milano': tot,
           'usati': ok, 'scartati_senza_epoca_o_classe': scartati, 'quota_FG_pct': round(fg / ok * 100, 1),
           'anni_inserimento': [min(date), max(date)],
           'origine': 'Comune di Milano, ds623 Database CENED+2 (CC0), attestati di prestazione energetica, solo residenziali del comune di Milano, senza doppioni'},
          open(os.path.join(out, 'energia_riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(tot, ok, scartati, round(fg / ok * 100, 1), min(date), max(date))
for i, b in enumerate(BANDE): print(b, sum(cnt[i].values()), [round(cnt[i][c] / max(1, sum(cnt[i].values())) * 100) for c in CL])
