"""Costruisce i file della pagina docs/rifiuti/ (docs/rifiuti/data/).

Uso (percorsi assoluti; si puo' rilanciare quando arrivano nuovi dati):
    python -I -X utf8 pagina.py <cartella rifiuti> <cartella milano-in-dati>

Legge:
    rifiuti/pulito/rifiuti_comuni_lungo.csv, costi_comuni_lungo.csv   (da build.py)
    bilancio-comune/pulito/indice_prezzi_annuo_FOI_da_strand12.csv    (sola lettura)
    docs/bilancio-comune/data/capitoli_usati.csv                      (TARI, sola lettura)
    docs/turisti/data/serie_totale.csv                                (notti, sola lettura)
Scrive in docs/rifiuti/data/: riepilogo.json + CSV con ';' e punto decimale.
"""
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comune import CITTA  # noqa: E402

ANNI = list(range(2010, 2025))
ROTTURA = {2011, 2012}   # abitanti del censimento 2011: non confrontabili con gli altri anni
CODICE_MI = '03015146'
GRUPPI = [  # id, nome, colonne ISPRA
    ('indiff', 'Indifferenziato', ['indifferenziato', 'ingombranti_smaltimento']),
    ('organico', 'Organico (umido)', ['umido']),
    ('carta', 'Carta e cartone', ['carta']),
    ('vpm', 'Vetro, plastica e metalli', ['vetro', 'plastica', 'metallo']),
    ('altre', 'Altre raccolte differenziate', ['verde', 'legno', 'raee', 'tessili', 'selettiva', 'cd',
                                               'spazzamento_recupero', 'ingombranti_recupero', 'altro']),
]


def fl(x):
    return float(x) if x not in ('', None) else None


def r1(x, d=1):
    return None if x is None else round(x, d)


def leggi(path, delim=';'):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delim))


def scrivi(path, head, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n')
        w.writerow(head)
        for r in rows:
            w.writerow(['' if v is None else v for v in r])


def main(base, root):
    out = os.path.join(root, 'docs', 'rifiuti', 'data')
    os.makedirs(out, exist_ok=True)

    # ------------------------------------------------------------ dati
    ris = leggi(os.path.join(base, 'pulito', 'rifiuti_comuni_lungo.csv'))
    cost = leggi(os.path.join(base, 'pulito', 'costi_comuni_lungo.csv'))
    foi = {int(r['anno']): float(r['indice_raccordato_2025_100']) for r in
           leggi(os.path.join(root, 'bilancio-comune', 'pulito', 'indice_prezzi_annuo_FOI_da_strand12.csv'), ',')}
    cap = leggi(os.path.join(root, 'docs', 'bilancio-comune', 'data', 'capitoli_usati.csv'))
    tur = {int(r['anno']): int(r['presenze_totale']) for r in
           leggi(os.path.join(root, 'docs', 'turisti', 'data', 'serie_totale.csv'), ',')}

    T = {}   # (cod, anno) -> riga
    for r in ris:
        T[(r['cod_istat'], int(r['anno']))] = r

    def val(r, k):
        return fl(r[k + '_t']) or 0.0

    def riga_num(r):
        d = {'pop': int(r['popolazione']), 'ru': val(r, 'tot_ru'), 'rd': val(r, 'tot_rd')}
        for gid, _, cols in GRUPPI:
            d[gid] = sum(val(r, c) for c in cols)
        d['umido'] = val(r, 'umido')
        d['rd_comp'] = d['rd'] - val(r, 'cd') - val(r, 'spazzamento_recupero')   # senza le due voci entrate in RD dal 2016
        return d

    def somma(righe):
        s = {}
        for d in righe:
            for k, v in d.items():
                s[k] = s.get(k, 0) + v
        return s

    def pcap(d, k, a):
        return None if a in ROTTURA or not d['pop'] else d[k] / d['pop'] * 1000

    # ------------------------------------------------------------ Milano
    mi = {a: riga_num(T[(CODICE_MI, a)]) for a in ANNI}
    milano = {
        'anni': ANNI,
        'popolazione': [mi[a]['pop'] for a in ANNI],
        'ru_t': [round(mi[a]['ru']) for a in ANNI],
        'rd_t': [round(mi[a]['rd']) for a in ANNI],
        'rd_pct': [r1(mi[a]['rd'] / mi[a]['ru'] * 100) for a in ANNI],
        'rd_pct_senza_cd_spazz': [r1(mi[a]['rd_comp'] / mi[a]['ru'] * 100) for a in ANNI],
        'ru_pc': [r1(pcap(mi[a], 'ru', a)) for a in ANNI],
        'gruppi': [],
    }
    for gid, nome, _ in GRUPPI:
        milano['gruppi'].append({'id': gid, 'nome': nome, 't': [round(mi[a][gid]) for a in ANNI],
                                 'kg_ab': [r1(pcap(mi[a], gid, a)) for a in ANNI]})
    scrivi(os.path.join(out, 'milano_serie.csv'),
           ['anno', 'abitanti_ISPRA', 'rifiuti_urbani_t', 'raccolta_differenziata_t', 'RD_percento_ISPRA',
            'RD_percento_senza_C&D_e_spazzamento', 'kg_per_abitante_RU'] + [g['id'] + '_t' for g in milano['gruppi']] +
           [g['id'] + '_kg_per_abitante' for g in milano['gruppi']],
           [[a, milano['popolazione'][i], milano['ru_t'][i], milano['rd_t'][i], milano['rd_pct'][i],
             milano['rd_pct_senza_cd_spazz'][i], milano['ru_pc'][i]] + [g['t'][i] for g in milano['gruppi']] +
            [g['kg_ab'][i] for g in milano['gruppi']] for i, a in enumerate(ANNI)])

    # ------------------------------------------------------------ Italia (somma dei comuni; senza le righe "Vedi aggregazione")
    ita = {}
    for a in ANNI:
        ita[a] = somma([riga_num(r) for (c, y), r in T.items() if y == a and not r['riferito_a'].startswith('Vedi')])
    italia = {'ru_pc': [r1(pcap(ita[a], 'ru', a)) for a in ANNI],
              'rd_pct': [r1(ita[a]['rd'] / ita[a]['ru'] * 100) for a in ANNI],
              'ru_t': [round(ita[a]['ru']) for a in ANNI]}

    # ------------------------------------------------------------ costi: indice per (cod, anno)
    C = {}
    for r in cost:
        C[(r['cod_istat'], int(r['anno']))] = r

    def costo(cod, a):
        r = C.get((cod, a))
        if not r or r['n_comuni'].strip() != '1':
            return None
        return fl(r['CTOTab'])

    def reale(x, a):
        return None if x is None else x * 100 / foi[a]

    # ------------------------------------------------------------ grandi citta'
    citta = {}
    righe_citta = []
    for cod, nome in CITTA.items():
        d = {a: riga_num(T[(cod, a)]) for a in ANNI}
        citta[nome] = {
            'popolazione': [d[a]['pop'] for a in ANNI],
            'ru_t': [round(d[a]['ru']) for a in ANNI],
            'ru_pc': [r1(pcap(d[a], 'ru', a)) for a in ANNI],
            'rd_pct': [r1(d[a]['rd'] / d[a]['ru'] * 100) for a in ANNI],
            'umido_pc': [r1(pcap(d[a], 'umido', a)) for a in ANNI],
            'indiff_pc': [r1(pcap(d[a], 'indiff', a)) for a in ANNI],
            'costo_pc': [r1(costo(cod, a), 2) for a in ANNI],
            'costo_pc_euro2025': [r1(reale(costo(cod, a), a), 1) for a in ANNI],
        }
        for i, a in enumerate(ANNI):
            righe_citta.append([nome, a, d[a]['pop'], round(d[a]['ru']), citta[nome]['ru_pc'][i], citta[nome]['rd_pct'][i],
                                citta[nome]['umido_pc'][i], citta[nome]['indiff_pc'][i], citta[nome]['costo_pc'][i],
                                citta[nome]['costo_pc_euro2025'][i]])
    scrivi(os.path.join(out, 'grandi_citta.csv'),
           ['citta', 'anno', 'abitanti_ISPRA', 'rifiuti_urbani_t', 'kg_per_abitante_RU', 'RD_percento',
            'umido_kg_per_abitante', 'indifferenziato_kg_per_abitante', 'costo_euro_per_abitante', 'costo_euro_2025_per_abitante'],
           righe_citta)

    # ------------------------------------------------------------ area metropolitana (provincia di Milano, codice 03015...)
    ids = None
    for a in ANNI:
        s = {c for (c, y), r in T.items() if y == a and c.startswith('03015') and r['riferito_a'] == 'Comune'}
        ids = s if ids is None else ids & s
    hint_ids = sorted(ids - {CODICE_MI})
    hint = {a: somma([riga_num(T[(c, a)]) for c in hint_ids]) for a in ANNI}
    # costi dell'hinterland: media pesata per abitanti dei comuni che hanno il costo (copertura per anno)
    cost_h, cop_h = [], []
    for a in ANNI:
        num = den = 0.0
        n = 0
        for c in hint_ids:
            x = costo(c, a)
            p = int(T[(c, a)]['popolazione'])
            if x is not None:
                num += x * p
                den += p
                n += 1
        cost_h.append(r1(num / den, 1) if den and a >= 2011 else None)
        cop_h.append(n if a >= 2011 else None)
    metro = {
        'n_comuni_hinterland': len(hint_ids),
        'popolazione': [hint[a]['pop'] for a in ANNI],
        'ru_pc': [r1(pcap(hint[a], 'ru', a)) for a in ANNI],
        'rd_pct': [r1(hint[a]['rd'] / hint[a]['ru'] * 100) for a in ANNI],
        'umido_pc': [r1(pcap(hint[a], 'umido', a)) for a in ANNI],
        'indiff_pc': [r1(pcap(hint[a], 'indiff', a)) for a in ANNI],
        'costo_pc_media_pesata': cost_h,
        'costo_n_comuni': cop_h,
    }
    # tutti i comuni, 2024
    lista = []
    for c in sorted(ids):
        d = riga_num(T[(c, 2024)])
        r = T[(c, 2024)]
        lista.append({'cod': c, 'comune': r['comune'].title() if r['comune'].isupper() else r['comune'], 'pop': d['pop'],
                      'ru_pc': r1(d['ru'] / d['pop'] * 1000), 'rd_pct': r1(d['rd'] / d['ru'] * 100),
                      'umido_pc': r1(d['umido'] / d['pop'] * 1000), 'indiff_pc': r1(d['indiff'] / d['pop'] * 1000),
                      'costo_pc': costo(c, 2024)})
    scrivi(os.path.join(out, 'area_metropolitana_2024.csv'),
           ['cod_istat', 'comune', 'abitanti_ISPRA', 'kg_per_abitante_RU', 'RD_percento', 'umido_kg_per_abitante',
            'indifferenziato_kg_per_abitante', 'costo_euro_per_abitante'],
           [[x['cod'], x['comune'], x['pop'], x['ru_pc'], x['rd_pct'], x['umido_pc'], x['indiff_pc'], x['costo_pc']] for x in lista])
    grandi = sorted([x for x in lista if x['pop'] >= 30000 and x['cod'] != CODICE_MI], key=lambda x: -x['pop'])
    metro['comuni_grandi_2024'] = grandi
    # posizione di Milano tra i 132 comuni
    mi24 = [x for x in lista if x['cod'] == CODICE_MI][0]
    ordine_rd = sorted(lista, key=lambda x: -x['rd_pct'])
    ordine_pc = sorted(lista, key=lambda x: x['ru_pc'])
    metro['milano_2024'] = {
        'n': len(lista),
        'pos_rd_dall_alto': [x['cod'] for x in ordine_rd].index(CODICE_MI) + 1,
        'pos_rifiuti_pc_dal_basso': [x['cod'] for x in ordine_pc].index(CODICE_MI) + 1,
        'mediana_rd': r1(statistics.median(x['rd_pct'] for x in lista)),
        'mediana_ru_pc': r1(statistics.median(x['ru_pc'] for x in lista)),
        'rd_milano': mi24['rd_pct'], 'ru_pc_milano': mi24['ru_pc'],
    }
    # quanti comuni hanno RD piu' alta di Milano nel 2010 e nel 2024
    def n_sopra(a):
        m = riga_num(T[(CODICE_MI, a)])
        rm = m['rd'] / m['ru']
        n = 0
        for c in ids:
            if c == CODICE_MI:
                continue
            d = riga_num(T[(c, a)])
            if d['ru'] and d['rd'] / d['ru'] > rm:
                n += 1
        return n
    metro['comuni_con_RD_piu_alta_di_Milano'] = {str(a): n_sopra(a) for a in (2010, 2013, 2016, 2019, 2024)}


    # ------------------------------------------------------------ controllo con ISTAT BES (citta' metropolitana di Milano)
    bes = {}
    for r in leggi(os.path.join(root, 'benessere', 'pulito', 'milano_serie.csv'), ','):
        if r['territorio'] == 'Milano' and r['codice'] in ('10AMB024P', '10AMB017'):
            bes[(r['codice'], int(r['anno']))] = float(r['valore'])
    ctrl = []
    for a in ANNI:
        tot = somma([riga_num(T[(c, a)]) for c in sorted(ids)])
        ctrl.append({'anno': a, 'nostro_kg': r1(pcap(tot, 'ru', a)), 'bes_kg': bes.get(('10AMB024P', a)),
                     'nostro_rd': r1(tot['rd'] / tot['ru'] * 100), 'bes_rd': bes.get(('10AMB017', a))})
    metro['controllo_bes'] = ctrl

    # ------------------------------------------------------------ costi di Milano e TARI
    comp = []
    for a in range(2011, 2025):
        r = C[(CODICE_MI, a)]
        g = lambda k: fl(r[k]) or 0.0  # noqa: E731
        pop = int(r['popolazione'])
        rt = g('CRTab') + g('CRDab')
        tr = g('CTSab') + g('CTRab')
        sp = g('CSLab')
        al = g('CACab') + g('CCab') + g('CKab') + g('Altri costi')
        tot = g('CTOTab')
        comp.append({'anno': a, 'pop': pop, 'raccolta_trasporto': r1(rt, 2), 'trattamento': r1(tr, 2), 'spazzamento': r1(sp, 2),
                     'comuni_capitale_altri': r1(al, 2), 'totale': r1(tot, 2),
                     'quadra': abs(rt + tr + sp + al - tot) < 0.05})
    scrivi(os.path.join(out, 'milano_costi.csv'),
           ['anno', 'abitanti_ISPRA', 'raccolta_e_trasporto', 'trattamento_smaltimento_riciclo', 'spazzamento_lavaggio',
            'costi_comuni_capitale_altri', 'totale_euro_per_abitante', 'totale_euro_2025_per_abitante', 'quadra_la_somma'],
           [[c['anno'], c['pop'], c['raccolta_trasporto'], c['trattamento'], c['spazzamento'], c['comuni_capitale_altri'], c['totale'],
             r1(reale(c['totale'], c['anno']), 1), c['quadra']] for c in comp])
    tari = {int(r['anno']): float(r['importo_euro']) for r in cap if r['voce'] == 'rifiuti'}
    tari_rows = []
    for c in comp:
        a = c['anno']
        costo_m = c['totale'] * c['pop'] / 1e6
        t = tari.get(a)
        tari_rows.append({'anno': a, 'costo_milioni': r1(costo_m, 1), 'tari_milioni': r1(t / 1e6, 1) if t else None,
                          'tari_su_costo': r1(t / 1e6 / costo_m * 100, 1) if t else None,
                          'tari_pc': r1(t / c['pop'], 1) if t else None})
    scrivi(os.path.join(out, 'milano_costi_e_tari.csv'),
           ['anno', 'costo_servizio_milioni_euro (costo pro capite x abitanti ISPRA)', 'TARI_milioni_euro (bilancio, accertamenti, parte ordinaria)',
            'TARI_su_costo_percento', 'TARI_euro_per_abitante'],
           [[x['anno'], x['costo_milioni'], x['tari_milioni'], x['tari_su_costo'], x['tari_pc']] for x in tari_rows])
    costi = {'anni': [c['anno'] for c in comp], 'componenti': comp, 'tari': tari_rows,
             'foi': {a: foi[a] for a in range(2011, 2025)}}

    # ------------------------------------------------------------ turisti
    tt = []
    for a in ANNI:
        giorni = 366 if a % 4 == 0 else 365
        eq = tur[a] / giorni
        tt.append({'anno': a, 'notti': tur[a], 'presenti_medi': round(eq), 'su_residenti_pct': r1(eq / mi[a]['pop'] * 100, 2),
                   'kg_per_residente': r1(pcap(mi[a], 'ru', a)),
                   'kg_per_residente_e_turista': None if a in ROTTURA else r1(mi[a]['ru'] / (mi[a]['pop'] + eq) * 1000)})
    scrivi(os.path.join(out, 'milano_turisti_e_rifiuti.csv'),
           ['anno', 'notti_in_strutture', 'turisti_presenti_in_media_ogni_giorno', 'in_percento_dei_residenti',
            'kg_RU_per_residente', 'kg_RU_per_residente_piu_turisti_medi'],
           [[x['anno'], x['notti'], x['presenti_medi'], x['su_residenti_pct'], x['kg_per_residente'], x['kg_per_residente_e_turista']] for x in tt])

    # ------------------------------------------------------------ Covid 2019 -> 2020 -> 2021
    covid = {'milano': {}, 'citta': {}}
    for a in (2019, 2020, 2021):
        covid['milano'][str(a)] = {'ru_t': round(mi[a]['ru']), 'notti': tur[a]}
    for g in ('indiff', 'organico', 'carta', 'vpm', 'altre'):
        covid['milano'][g] = {str(a): round(mi[a][g]) for a in (2019, 2020, 2021)}
    for cod, nome in CITTA.items():
        d = {a: riga_num(T[(cod, a)]) for a in (2019, 2020, 2021, 2024)}
        covid['citta'][nome] = {'var_2019_2020_pct': r1((d[2020]['ru'] / d[2019]['ru'] - 1) * 100),
                                'var_2019_2021_pct': r1((d[2021]['ru'] / d[2019]['ru'] - 1) * 100),
                                'var_2019_2024_pct': r1((d[2024]['ru'] / d[2019]['ru'] - 1) * 100)}
    covid['italia_var_2019_2020_pct'] = r1((ita[2020]['ru'] / ita[2019]['ru'] - 1) * 100)
    covid['notti_var_2019_2020_pct'] = r1((tur[2020] / tur[2019] - 1) * 100)
    covid['notti_var_2019_2024_pct'] = r1((tur[2024] / tur[2019] - 1) * 100)

    # ------------------------------------------------------------ sorprese (calcolate)
    ic = lambda k: ANNI.index(k)  # noqa: E731
    g = {x['id']: x for x in milano['gruppi']}
    cm = costi['componenti']
    cm_by = {c['anno']: c for c in cm}
    cc = {n: citta[n] for n in citta}
    sorprese = {
        'indiff_kg_2010': g['indiff']['t'][0] / mi[2010]['pop'] * 1000,
        'indiff_kg_2024': g['indiff']['kg_ab'][ic(2024)],
        'indiff_t_2010': g['indiff']['t'][0], 'indiff_t_2024': g['indiff']['t'][ic(2024)],
        'ru_t_2010': milano['ru_t'][0], 'ru_t_2024': milano['ru_t'][ic(2024)],
        'ru_pc_2013': milano['ru_pc'][ic(2013)], 'ru_pc_2019': milano['ru_pc'][ic(2019)], 'ru_pc_2024': milano['ru_pc'][ic(2024)],
        'organico_t_2010': g['organico']['t'][0], 'organico_t_2014': g['organico']['t'][ic(2014)], 'organico_t_2024': g['organico']['t'][ic(2024)],
        'organico_t_2012': g['organico']['t'][ic(2012)], 'organico_t_2013': g['organico']['t'][ic(2013)],
        'rd_2010': milano['rd_pct'][0], 'rd_2024': milano['rd_pct'][ic(2024)], 'rd_comp_2024': milano['rd_pct_senza_cd_spazz'][ic(2024)],
        'costo_2011': cm_by[2011]['totale'], 'costo_2019': cm_by[2019]['totale'], 'costo_2024': cm_by[2024]['totale'],
        'costo_reale_2011': r1(reale(cm_by[2011]['totale'], 2011), 1), 'costo_reale_2024': r1(reale(cm_by[2024]['totale'], 2024), 1),
        'costo_2024_citta': {n: cc[n]['costo_pc'][ic(2024)] for n in cc},
        'costo_2019_citta': {n: cc[n]['costo_pc'][ic(2019)] for n in cc},
        'costo_var_2019_2024_citta_pct': {n: r1((cc[n]['costo_pc'][ic(2024)] / cc[n]['costo_pc'][ic(2019)] - 1) * 100)
                                          if cc[n]['costo_pc'][ic(2019)] and cc[n]['costo_pc'][ic(2024)] else None for n in cc},
        'notti_var_2019_2024': covid['notti_var_2019_2024_pct'],
        'ru_t_var_2019_2024': r1((mi[2024]['ru'] / mi[2019]['ru'] - 1) * 100),
    }

    # ------------------------------------------------------------ file riepilogo
    riepilogo = {
        'meta': {'anni': ANNI, 'rottura_abitanti': sorted(ROTTURA), 'scaricato': '2026-11-01',
                 'pagina_generata_da': 'rifiuti/scripts/pagina.py',
                 'gruppi': [{'id': i, 'nome': n, 'colonne_ISPRA': c} for i, n, c in GRUPPI],
                 'n_comuni_italia_2024': sum(1 for (c, y), r in T.items() if y == 2024 and not r['riferito_a'].startswith('Vedi'))},
        'milano': milano, 'italia': italia, 'citta': citta, 'metro': metro, 'costi': costi,
        'turisti': tt, 'covid': covid, 'sorprese': sorprese,
        'fonti': {
            'rifiuti': 'ISPRA, Catasto Rifiuti - dati comunali di produzione e raccolta differenziata dei rifiuti urbani, 2010-2024 (aggiornamento 22/7/2026)',
            'costi': 'ISPRA, Catasto Rifiuti - costi di gestione comunali pro capite, 2011-2024',
            'tari': 'bilancio-comune (capitoli usati), Comune di Milano ds397...ds3013, CC BY',
            'turisti': 'turisti (serie_totale.csv): Comune di Milano / ISTAT / PoliS-Lombardia, CC BY',
            'prezzi': 'ISTAT FOI senza tabacchi, via filone bilancio-comune',
        },
    }
    with open(os.path.join(out, 'riepilogo.json'), 'w', encoding='utf-8') as f:
        json.dump(riepilogo, f, ensure_ascii=False, indent=1)
    print('scritto', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
