"""Legge le pagine HTML scaricate dal Ministero dell'Interno (Certificati consuntivi, contabilita' armonizzata)
e scrive tabelle pulite in pulito/.

Uso: python -I -X utf8 estrai_ministero.py <cartella tasse>

Le pagine sono dati non fidati: si leggono solo come testo (nessuna esecuzione).
Quadro 2  = gestione delle entrate (residui, riscossioni, accertamenti) per tipologia
Quadro 9  = accertamenti e riscossioni per categoria (IMU, TARI, addizionale, soggiorno...)
Quadro 18 = fondo crediti di dubbia esigibilita'
Quadro 20 = indicatori (capacita' di riscossione)
Quadro 1  = popolazione residente del rendiconto
"""
import sys, os, re, csv, html

CITTE = ['milano', 'roma', 'torino', 'napoli', 'bologna', 'firenze', 'genova']
ANNI = [2016, 2017, 2018]


def num(s):
    s = s.strip().replace('.', '').replace(',', '.')
    if s in ('', '-'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def testo(fn):
    t = open(fn, encoding='latin-1').read()
    return re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)


def righe_semplici(t):
    out = []
    for r in re.findall(r'<tr[^>]*>(.*?)(?=<tr|</table>)', t, flags=re.S):
        cells = [html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c))).strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, flags=re.S)]
        if any(cells):
            out.append(cells)
    return out


def q2(t):
    """Righe del quadro 2 con le 13 colonne in ordine."""
    res = {}
    parts = re.split(r'class="tftitvert">', t)
    for p in parts[1:]:
        lab = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', p.split('</td>')[0]))).strip()
        body = p.split('<td  rowspan="3"')[0]
        vals = re.findall(r'<strong>([A-Z]{1,2})</strong></td><td class="ad">([^<]*)</td>', body)
        if len(vals) >= 13:
            res[lab] = [(c, num(v)) for c, v in vals[:13]]
    return res


Q2_ORDINE = ['RS', 'RR', 'R', 'EP', 'CP', 'RC', 'A', 'MAGG_MIN_COMP', 'EC', 'CS', 'TR_RISC', 'MAGG_MIN_CASSA', 'TR_RESIDUI']


def main(base):
    raw = os.path.join(base, 'raw', 'ministero_interno')
    out = os.path.join(base, 'pulito')
    os.makedirs(out, exist_ok=True)
    f2 = csv.writer(open(os.path.join(out, 'ministero_q2_entrate_gestione.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    f2.writerow(['citta', 'anno', 'voce'] + Q2_ORDINE + ['file'])
    f9 = csv.writer(open(os.path.join(out, 'ministero_q9_accertamenti.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    f9.writerow(['citta', 'anno', 'voce', 'accertamenti', 'di_cui_non_ricorrenti', 'riscossioni_competenza', 'riscossioni_residui', 'file'])
    f18 = csv.writer(open(os.path.join(out, 'ministero_q18_fcde.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    f18.writerow(['citta', 'anno', 'voce', 'residui_formati_nell_anno', 'residui_anni_precedenti', 'residui_totali', 'importo_minimo_fondo', 'fondo_accantonato', 'perc_accantonamento', 'file'])
    f20 = csv.writer(open(os.path.join(out, 'ministero_q20_indicatori.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    f20.writerow(['citta', 'anno', 'indicatore', 'valore_perc', 'file'])
    f1 = csv.writer(open(os.path.join(out, 'ministero_q1_popolazione.csv'), 'w', newline='', encoding='utf-8'), delimiter=';')
    f1.writerow(['citta', 'anno', 'popolazione_residente', 'rendiconto_approvato_il', 'file'])

    for c in CITTE:
        for a in ANNI:
            # quadro 2
            fn = f'{c}_{a}_q02.html'
            t = testo(os.path.join(raw, fn))
            for lab, vals in q2(t).items():
                d = dict(zip(Q2_ORDINE, [v for _, v in vals]))
                f2.writerow([c, a, lab] + [d[k] for k in Q2_ORDINE] + [fn])
            # quadro 9
            fn = f'{c}_{a}_q09.html'
            for r in righe_semplici(testo(os.path.join(raw, fn))):
                if len(r) == 5 and num(r[1]) is not None and not r[0].startswith('VOCI'):
                    f9.writerow([c, a, r[0], num(r[1]), num(r[2]), num(r[3]), num(r[4]), fn])
            # quadro 18
            fn = f'{c}_{a}_q18.html'
            for r in righe_semplici(testo(os.path.join(raw, fn))):
                if len(r) == 7 and num(r[1]) is not None:
                    f18.writerow([c, a, r[0]] + [num(x) for x in r[1:]] + [fn])
            # quadro 20
            fn = f'{c}_{a}_q20.html'
            for r in righe_semplici(testo(os.path.join(raw, fn))):
                if len(r) == 2 and re.match(r'^(\d+\.\d+ |Indicatore concernente)', r[0]) and num(r[1]) is not None:
                    f20.writerow([c, a, r[0], num(r[1]), fn])
            # quadro 1
            fn = f'{c}_{a}_q01.html'
            rr = righe_semplici(testo(os.path.join(raw, fn)))
            pop, data = None, None
            for r in rr:
                if r and r[0].startswith('Popolazione residente'):
                    pop = num(r[1])
                if r and r[0] == 'in data':
                    data = r[1]
            f1.writerow([c, a, pop, data, fn])


if __name__ == '__main__':
    main(sys.argv[1])
