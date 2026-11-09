"""Divide la tabella dei residenti per quartiere, cittadinanza e anno (pagina Comunita') per anno.
Regola dei 2 MB per file (Google legge solo i primi 2 MB): il file grande residenti_per_cittadinanza_nil.csv (2,4 MB) diventa piu' file per
gruppi di cittadinanze, ciascuno sotto 1,4 MB, con la stessa riga di intestazione. Le righe restano nell'ordine di prima.

Uso:  python -I -X utf8 popolazione/scripts/10_dividi_residenti_nil.py [file di partenza] [cartella di arrivo]
Il file di partenza e' residenti_per_cittadinanza_nil.csv in docs/comunita/data/ (lo scrive pagina.py); i file nuovi si chiamano residenti_per_cittadinanza_nil_parte1.csv, _parte2.csv... e vanno in docs/comunita/data/.
"""
import csv, glob, io, os, sys

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(R, 'docs', 'comunita', 'data')
NOME = 'residenti_per_cittadinanza_nil'
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, NOME + '.csv')
OUT = sys.argv[2] if len(sys.argv) > 2 else DATA
SEP = ';'
COLONNA = 'cittadinanza'  # colonna che decide dove tagliare: un gruppo di righe con lo stesso valore non si divide

BUDGET = 1400 * 1024


def main():
    testo = open(SRC, encoding='utf-8-sig', newline='').read()
    righe = testo.splitlines(keepends=True)
    testa, corpo = righe[0], righe[1:]
    k = next(i for i, h in enumerate(csv.reader([testa], delimiter=SEP).__next__()) if h.strip() == COLONNA)
    gruppi, ultimo = [], None
    for r in corpo:
        v = r.split(SEP)[k]
        if v != ultimo:
            gruppi.append([v, []])
            ultimo = v
        gruppi[-1][1].append(r)
    parti, cur, peso = [], [], 0
    for v, rr in gruppi:
        b = sum(len(x.encode('utf-8')) for x in rr)
        if cur and peso + b > BUDGET:
            parti.append(cur)
            cur, peso = [], 0
        cur.append((v, rr))
        peso += b
    if cur:
        parti.append(cur)
    for f in glob.glob(os.path.join(OUT, NOME + '_*.csv')):
        os.remove(f)
    for n, p in enumerate(parti, 1):
        a, z = p[0][0], p[-1][0]
        nome = os.path.join(OUT, '%s_parte%d.csv' % (NOME, n))
        with open(nome, 'w', encoding='utf-8', newline='') as f:
            f.write(testa)
            for v, rr in p:
                f.writelines(rr)
        print(nome, round(os.path.getsize(nome) / 1024), 'KB', '| cittadinanze da', a, 'a', z)


main()
