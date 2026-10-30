r"""Passo 3: dalle pagine in cache (raw\omi_pubblico_cache\stampa\) costruisce, per ogni semestre, due CSV nel formato dei file OMI "SPID":
  raw\omi_pubblico\QI_PUB_1_<AAAAS>_VALORI.csv e QI_PUB_1_<AAAAS>_ZONE.csv   (stesse colonne del tracciato dal 2016, separatore ";", numeri con la virgola)
Piu' un file di controllo raw\omi_pubblico\controlli_conversione.txt. Non scarica nulla.
Regole: lo stato conservativo in MAIUSCOLO sulla pagina = stato prevalente -> Stato_prev = P (legenda della pagina). Un asterisco (*) accanto a un
valore (valore rettificato) viene tolto dal numero e segnalato nell'ultima colonna 'Rettifica'. Valori vuoti/0 restano come sono.
Uso: python -I 08c_omi_pubblico_csv.py <cartella prezzi-case>
"""
import os, sys, re, json, html, collections

base = sys.argv[1]
C = os.path.join(base, 'raw', 'omi_pubblico_cache')
S = os.path.join(C, 'stampa')
OUT = os.path.join(base, 'raw', 'omi_pubblico')
COD = {'ville e villini': 1, 'negozi': 5, 'uffici': 6, 'capannoni tipici': 7, 'capannoni industriali': 8, 'magazzini': 9, 'laboratori': 10, 'box': 13,
       'posti auto coperti': 14, 'posti auto scoperti': 15, 'autorimesse': 16, 'centri commerciali': 17, 'uffici strutturati': 18,
       'abitazioni signorili': 19, 'abitazioni civili': 20, 'abitazioni di tipo economico': 21, 'abitazioni tipiche dei luoghi': 22,
       'pensioni e assimilati': 23}


def pulisci(x):
    return html.unescape(re.sub(r'<[^>]+>', '', x)).replace('\xa0', ' ').strip()


def parse(txt):
    h = {}
    m = re.search(r'Anno\s+(\d{4})\s*-\s*Semestre\s+(\d)', txt)
    h['sem'] = m.group(1) + m.group(2) if m else None
    for k, lab in (('fascia', 'Fascia'), ('zona_descr', 'Zona'), ('zona', 'Codice zona'), ('destinazione', 'Destinazione'),
                   ('tip_prev', 'Tipologia prevalente'), ('dest_prev', 'Destinazione prevalente'), ('comune', 'Comune')):
        m = re.search(r'<strong>%s:</strong>\s*<span[^>]*>(.*?)</span>' % re.escape(lab), txt, re.S)
        h[k] = pulisci(m.group(1)) if m else ''
    rows = []
    i = txt.find('<table')
    j = txt.find('</table>', i)
    for tr in re.findall(r'<tr>(.*?)</tr>', txt[i:j], re.S):
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
        if len(tds) == 8:
            rows.append([pulisci(x) for x in tds])
        elif len(tds) not in (0, 1, 2):
            rows.append(['??'] + [pulisci(x) for x in tds])
    h['no_results'] = 'Non sono presenti risultati' in txt
    return h, rows


def num(x):
    return x.replace('*', '').strip(), '*' in x


def main():
    os.makedirs(OUT, exist_ok=True)
    J = json.load(open(os.path.join(C, 'jobs.json')))['jobs']
    by = collections.defaultdict(list)
    for s, z, l in J:
        by[s].append((z, l))
    ctrl = []
    anomalie = collections.Counter()
    tot_val = 0
    for s in sorted(by):
        V, Z = [], []
        visti = set()
        for z, l in by[s]:
            if (z, l) in visti:
                continue
            visti.add((z, l))
            zone_row = None
            for t in 'RCTP':
                p = os.path.join(S, f'{s}_{l}_{t}.html')
                if not os.path.exists(p):
                    anomalie['file non scaricato ' + t] += 1
                    continue
                h, rows = parse(open(p, encoding='utf-8', errors='replace').read())
                if h['sem'] != s:
                    ctrl.append(f'ATTENZIONE {p}: semestre nella pagina {h["sem"]} diverso da {s}')
                if zone_row is None or (t == 'R' and rows):
                    zone_row = (h, rows, t)
                for r in rows:
                    if r[0] == '??':
                        anomalie['riga con numero di celle inatteso'] += 1
                        continue
                    tip, stato, cmin, cmax, sc, lmin, lmax, sl = r
                    cod = COD.get(tip.lower().strip())
                    if cod is None:
                        anomalie['tipologia senza codice: ' + tip] += 1
                    prev = 'P' if stato and stato == stato.upper() and any(c.isalpha() for c in stato) else ''
                    cmin, a1 = num(cmin)
                    cmax, a2 = num(cmax)
                    lmin, a3 = num(lmin)
                    lmax, a4 = num(lmax)
                    V.append(['NORD-OVEST', 'LOMBARDIA', 'MI', '3015146', 'C1AA', ' ', 'F205', 'MILANO', h['fascia'], z, l,
                              '' if cod is None else str(cod), tip, stato, prev, cmin, cmax, sc, lmin, lmax, sl,
                              '*' if (a1 or a2 or a3 or a4) else ''])
            if zone_row:
                h, rows, t = zone_row
                tp = h['tip_prev'] or (rows[0][0] if rows else '')
                codp = COD.get(tp.lower().strip(), '')
                sp = ''
                for r in rows:
                    if r[0] == tp and r[1] == r[1].upper():
                        sp = r[1][:1]
                Z.append(['NORD-OVEST', 'LOMBARDIA', 'MI', '3015146', 'C1AA', ' ', 'F205', 'MILANO', h['fascia'], "'" + h['zona_descr'] + "'", z, l,
                          str(codp), tp, sp, '0'])
        if not V:
            ctrl.append(f'{s}: nessun valore trovato nelle pagine in cache')
        hv = ('Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona;LinkZona;Cod_Tip;'
              'Descr_Tipologia;Stato;Stato_prev;Compr_min;Compr_max;Sup_NL_compr;Loc_min;Loc_max;Sup_NL_loc;Rettifica;')
        hz = ('Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona_Descr;Zona;LinkZona;'
              'Cod_tip_prev;Descr_tip_prev;Stato_prev;Microzona;')
        a, b = s[:4], s[4]
        tit = 'Quotazioni Immobiliari : %s - Semestre %s/%s - ricostruito dalla consultazione pubblica GEOPOI (non e un file SPID)'
        with open(os.path.join(OUT, f'QI_PUB_1_{s}_VALORI.csv'), 'w', encoding='utf-8', newline='') as f:
            f.write(tit % ('Valori di Mercato', a, b) + '\n' + hv + '\n')
            for r in V:
                f.write(';'.join(r) + ';\n')
        with open(os.path.join(OUT, f'QI_PUB_1_{s}_ZONE.csv'), 'w', encoding='utf-8', newline='') as f:
            f.write(tit % ('Informazioni di Zona OMI', a, b) + '\n' + hz + '\n')
            for r in Z:
                f.write(';'.join(r) + ';\n')
        tot_val += len(V)
        ctrl.append(f'{s}: {len(V)} righe VALORI, {len({r[10] for r in V})} zone con valori su {len(visti)} interrogate')
    ctrl.append(f'Totale righe VALORI: {tot_val}')
    ctrl.append('Anomalie: ' + (json.dumps(dict(anomalie), ensure_ascii=False) if anomalie else 'nessuna'))
    open(os.path.join(C, 'controlli_conversione.log'), 'w', encoding='utf-8').write('\n'.join(ctrl) + '\n')
    print('\n'.join(ctrl[-12:]))


if __name__ == '__main__':
    main()
