"""Legge i file SIOPE (entrate, incassi cumulati a dicembre) filtrati per le sette citta' e scrive pulito/siope_tributi.csv.
Incassi = CASSA (soldi entrati nell'anno, anche se riferiti ad anni precedenti).

Uso: python -I -X utf8 estrai_siope.py <cartella tasse>
"""
import sys, os, csv, glob, re

NOMI = {'COMUNE DI MILANO': 'milano', 'ROMA CAPITALE': 'roma', 'COMUNE DI ROMA': 'roma', 'COMUNE DI TORINO': 'torino',
        'COMUNE DI NAPOLI': 'napoli', 'COMUNE DI BOLOGNA': 'bologna', 'COMUNE DI FIRENZE': 'firenze', 'COMUNE DI GENOVA': 'genova'}

# nuovo piano dei conti (dal 2018): prefisso codice -> tributo
NUOVO = [('E1010106', 'IMU'), ('E1010108', 'ICI'), ('E1010116', 'Addizionale IRPEF'), ('E1010141', 'Imposta di soggiorno'),
         ('E1010151', 'Rifiuti (TARI/TARSU)'), ('E1010161', 'Rifiuti (TARES)'), ('E1010176', 'TASI'),
         ('E1010152', 'Occupazione suolo'), ('E1010153', 'Pubblicita e affissioni'), ('E1010199', 'Altre imposte e tasse'),
         ('E10104', 'Compartecipazioni'), ('E1030101', 'Fondo di solidarieta comunale')]
# vecchio piano dei conti (2015-2017)
VECCHIO = {'E1101': 'IMU', 'E1102': 'IMU', 'E1104': 'TASI', 'E1103': 'IMU', 'E1111': 'Addizionale IRPEF', 'E1175': 'Imposta di soggiorno',
           'E1201': 'Rifiuti (TARES)', 'E1202': 'Rifiuti (TARES)', 'E1204': 'Rifiuti (TARI/TARSU)', 'E1203': 'Rifiuti (TARI/TARSU)',
           'E1161': 'Pubblicita e affissioni', 'E1162': 'Pubblicita e affissioni', 'E1301': 'Pubblicita e affissioni',
           'E1211': 'Occupazione suolo', 'E1212': 'Occupazione suolo', 'E1303': 'Fondo di solidarieta comunale'}


def main(base):
    d = os.path.join(base, 'raw', 'siope')
    out = csv.writer(open(os.path.join(base, 'pulito', 'siope_tributi.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    out.writerow(['citta', 'anno', 'tributo', 'tipo', 'codice', 'descrizione', 'incassi_euro', 'popolazione_bdap', 'file'])
    righe = 0
    for fn in sorted(glob.glob(os.path.join(d, 'siope_entrate_*.csv'))):
        if os.path.getsize(fn) < 1000:
            continue
        anno = int(re.search(r'_(\d{4})\.csv$', fn).group(1))
        for r in csv.reader(open(fn, encoding='utf-8', errors='replace'), delimiter=';'):
            if len(r) < 17 or r[0].startswith('Codice'):
                continue
            ente = r[6]
            if ente not in NOMI or r[9] != f'{anno}/12' or r[10] != 'Entrata':
                continue
            cod = r[13]
            citta = NOMI[ente]
            trib, tipo = None, 'non_distinto'
            if cod.startswith('E1') and len(cod) == 11:
                for p, t in NUOVO:
                    if cod.startswith(p):
                        trib = t
                        break
                if trib and cod[-3:] == '001':
                    tipo = 'ordinaria'
                elif trib and cod[-3:] == '002':
                    tipo = 'verifica_controllo'
            elif len(cod) == 5 and cod in VECCHIO:
                trib = VECCHIO[cod]
            if trib is None:
                continue
            out.writerow([citta, anno, trib, tipo, cod, r[14], r[16], r[15], os.path.basename(fn)])
            righe += 1
    print('righe', righe)


if __name__ == '__main__':
    main(sys.argv[1])
