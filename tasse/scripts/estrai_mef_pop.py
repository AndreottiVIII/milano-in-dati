"""Prepara, in sola lettura dalle cartelle gia' pronte, due tabelle per le sette citta':
 - pulito/popolazione_1gen_citta.csv : residenti ISTAT al 1 gennaio 2002-2026 (ricostruzione 2002-2019, POSAS 2020-2026)
 - pulito/mef_citta.csv              : MEF Dipartimento Finanze, IRPEF per comune, anni d'imposta 2000-2024 (campi utili)
 - pulito/mef_milano_classi.csv      : Milano, contribuenti e reddito per classe di reddito complessivo

Uso: python -I -X utf8 estrai_mef_pop.py <cartella tasse> <cartella redditi>
"""
import sys, os, zipfile, csv, io
import pandas as pd

CITTA = {'milano': ('015146', 'F205', 'Milano'), 'roma': ('058091', 'H501', 'Roma'), 'torino': ('001272', 'L219', 'Torino'),
         'napoli': ('063049', 'F839', 'Napoli'), 'bologna': ('037006', 'A944', 'Bologna'), 'firenze': ('048017', 'D612', 'Firenze'),
         'genova': ('010025', 'D969', 'Genova')}


def popolazione(red, out):
    D = os.path.join(red, 'raw', 'istat_pop')
    righe = []
    z = zipfile.ZipFile(os.path.join(D, 'ricostruzione_2002_2019_comuni.zip'))
    names = z.namelist()
    for c, (istat, cat, nome) in CITTA.items():
        n = [x for x in names if f'Comune_{istat}-' in x]
        assert len(n) == 1, (c, n)
        L = z.read(n[0]).decode('utf8').splitlines()
        anni = [int(a) for a in L[4].split(';')[1:]]
        tot = next(l for l in L if l.startswith('Totale')).split(';')[1:]
        for a, v in zip(anni, tot):
            righe.append([c, a, int(v), f'ricostruzione_2002_2019_comuni.zip / {n[0]} / riga Totale (tutte le cittadinanze)'])
    for y in range(2020, 2027):
        zf = zipfile.ZipFile(os.path.join(D, f'POSAS_{y}_it_Comuni.zip'))
        s = zf.read(zf.namelist()[0]).decode('utf8')
        r = csv.reader(io.StringIO(s), delimiter=';')
        next(r)
        hdr = next(r)
        ti = len(hdr) - 1
        assert hdr[ti].strip().lower() == 'totale'
        tot = {}
        for row in r:
            if len(row) < ti + 1 or not row[0].strip():
                continue
            code = row[0].strip().zfill(6)
            if row[2].strip() == '999':
                continue
            tot[code] = tot.get(code, 0) + int(row[ti])
        for c, (istat, cat, nome) in CITTA.items():
            righe.append([c, y, tot[istat], f"POSAS_{y}_it_Comuni.zip / colonna Totale, somma delle eta' (esclusa riga Eta=999)"])
    with open(os.path.join(out, 'popolazione_1gen_citta.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['citta', 'anno_1_gennaio', 'residenti', 'fonte'])
        w.writerows(sorted(righe, key=lambda r: (r[0], r[1])))
    # controllo contro il file gia' pubblicato del filone redditi
    ref = pd.read_csv(os.path.join(red, 'pulito', 'popolazione_1gen.csv'))
    mine = pd.DataFrame(righe, columns=['citta', 'anno', 'residenti', 'fonte'])
    mine['unita'] = mine.citta.str.capitalize()
    m = mine.merge(ref, left_on=['unita', 'anno'], right_on=['unita', 'anno_1_gennaio'], suffixes=('', '_ref'))
    diff = m[m.residenti != m.popolazione]
    print('popolazione: righe', len(righe), 'confronto con redditi:', len(m), 'differenze', len(diff))


def mef(red, out):
    d = pd.read_csv(os.path.join(red, 'pulito', 'mef_comuni_2000_2024.csv'), low_memory=False)
    cat = {v[1]: k for k, v in CITTA.items()}
    d = d[d.catastale.isin(cat)].copy()
    d['citta'] = d.catastale.map(cat)
    cl = ['cl0_le0', 'cl1_0_10k', 'cl2_10_15k', 'cl3_15_26k', 'cl4_26_55k', 'cl5_55_75k', 'cl6_75_120k', 'cl7_oltre120k']
    cols = ['citta', 'anno', 'comune', 'contribuenti', 'imponibile_n', 'imponibile_eur', 'imposta_netta_n', 'imposta_netta_eur',
            'imponibile_addiz_n', 'imponibile_addiz_eur', 'addiz_com_n', 'addiz_com_eur', 'addiz_reg_n', 'addiz_reg_eur',
            'reddito_complessivo_eur'] + [c + s for c in cl for s in ('_n', '_eur')]
    d[cols].sort_values(['citta', 'anno']).to_csv(os.path.join(out, 'mef_citta.csv'), index=False, sep=';')
    m = d[d.citta == 'milano'].sort_values('anno')
    rows = []
    for _, r in m.iterrows():
        for c in cl:
            rows.append([int(r.anno), c, r[c + '_n'], r[c + '_eur']])
    pd.DataFrame(rows, columns=['anno', 'classe', 'contribuenti', 'reddito_euro']).to_csv(
        os.path.join(out, 'mef_milano_classi.csv'), index=False, sep=';')
    print('mef: righe', len(d))


if __name__ == '__main__':
    base, red = sys.argv[1], sys.argv[2]
    out = os.path.join(base, 'pulito')
    os.makedirs(out, exist_ok=True)
    popolazione(red, out)
    mef(red, out)
