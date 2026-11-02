"""Funzioni comuni (lettura dei CSV del Catasto rifiuti ISPRA e dei CSV del Comune di Milano).

Non si lancia da solo: lo importano build.py e pagina.py (che aggiungono questa cartella a sys.path).
I file in raw/ sono dati scaricati e quindi non fidati: si leggono solo come testo (csv), mai eseguiti.
"""
import csv
import re

ANNI = list(range(2010, 2025))

# colonne dei file ISPRA dei rifiuti (stesso ordine in tutti gli anni, controllato da build.py)
COL_T = ['umido', 'verde', 'carta', 'vetro', 'legno', 'metallo', 'plastica', 'raee', 'tessili', 'selettiva',
         'cd', 'spazzamento_recupero', 'ingombranti_recupero', 'altro', 'tot_rd', 'ingombranti_smaltimento',
         'indifferenziato', 'tot_ru']
HEAD_ATTESA = ['IstatComune', 'Regione', 'Provincia', 'Comune', 'Popolazione', 'Dato riferito a',
               'Frazione umida(1) (t)', 'Verde (t)', 'Carta e cartone (t)', 'Vetro (t)', 'Legno (t)', 'Metallo (t)',
               'Plastica (t)', 'RAEE (t)', 'Tessili (t)', 'Selettiva (t)', 'Rifiuti da C e D (t)',
               'Pulizia stradale a recupero (t)', 'Ingombranti misti a recupero (t)', 'Altro (t)', 'Totale RD (t)',
               'Ingombranti a smaltimento (t)', 'Indifferenziato (t)', 'Totale RU (t)', 'Percentuale RD (%)']

# le grandi citta' del confronto (codice ISTAT a 8 cifre: regione + comune)
CITTA = {
    '03015146': 'Milano', '12058091': 'Roma', '01001272': 'Torino', '15063049': 'Napoli',
    '08037006': 'Bologna', '09048017': 'Firenze', '07010025': 'Genova',
}


def num_it(s):
    """'1.412,641' -> 1412.641 ; '-' o vuoto -> None ; '64,79%' -> 64.79"""
    s = (s or '').strip().replace('%', '').strip()
    if s in ('', '-'):
        return None
    s = s.replace('.', '').replace(',', '.')
    return float(s)


def leggi_ispra_rifiuti(path):
    """Ritorna lista di dict, una riga per comune (o aggregazione). Salta le righe senza dati."""
    with open(path, encoding='utf-8-sig', errors='replace', newline='') as f:
        rows = list(csv.reader(f, delimiter=';'))
    head = [h.strip() for h in rows[1]]
    if head != HEAD_ATTESA:
        raise ValueError('intestazione diversa in ' + path + ': ' + repr(head))
    out = []
    for r in rows[2:]:
        if len(r) < 25:
            continue
        cod = r[0].strip()
        if not re.fullmatch(r'\d{8}', cod):
            continue
        d = {'cod': cod, 'regione': r[1].strip(), 'provincia': r[2].strip(), 'comune': r[3].strip(),
             'pop': int(num_it(r[4]) or 0), 'riferito_a': r[5].strip()}
        for k, v in zip(COL_T, r[6:24]):
            d[k] = num_it(v)
        d['rd_pct_ispra'] = num_it(r[24])
        out.append(d)
    return out


def leggi_ispra_costi(path):
    """File dei costi pro capite: le colonne cambiano dal 2020, quindi si legge per nome."""
    with open(path, encoding='utf-8-sig', errors='replace', newline='') as f:
        txt = f.read()
    if '<html' in txt[:200].lower():
        raise ValueError('risposta HTML (non un CSV) in ' + path)
    rows = list(csv.reader(txt.splitlines(), delimiter=';'))
    head = [h.strip() for h in rows[2]]
    out = []
    for r in rows[3:]:
        if len(r) < 8:
            continue
        cod = r[0].strip()
        if not re.fullmatch(r'\d{8}', cod):
            continue
        d = {'cod': cod, 'comune': r[1].strip(), 'provincia': r[2].strip(), 'n_comuni': r[3].strip()}
        for h, v in zip(head[4:], r[4:]):
            d[h] = num_it(v)
        out.append(d)
    return out
