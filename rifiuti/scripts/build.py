"""Fase 1: legge i file scaricati in raw/ e scrive le tabelle pulite in pulito/.

Uso (percorsi assoluti):
    python -I -X utf8 build.py <cartella rifiuti>

Scrive:
    pulito/rifiuti_comuni_lungo.csv   tutti i comuni italiani, 2010-2024 (ISPRA Catasto rifiuti), tonnellate
    pulito/costi_comuni_lungo.csv     costi di gestione pro capite (euro/abitante) per comune, 2011-2024 (ISPRA)
    pulito/controlli.json             controlli di coerenza (somme, numero di righe, intestazioni)
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from comune import ANNI, COL_T, leggi_ispra_rifiuti, leggi_ispra_costi  # noqa: E402


def main(base):
    raw = os.path.join(base, 'raw')
    out = os.path.join(base, 'pulito')
    os.makedirs(out, exist_ok=True)
    controlli = {'rifiuti': {}, 'costi': {}}

    # ---------------- rifiuti per comune
    righe = 0
    with open(os.path.join(out, 'rifiuti_comuni_lungo.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n')
        w.writerow(['anno', 'cod_istat', 'regione', 'provincia', 'comune', 'popolazione', 'riferito_a'] + [c + '_t' for c in COL_T] + ['rd_pct_ispra'])
        for y in ANNI:
            rs = leggi_ispra_rifiuti(os.path.join(raw, 'ispra_comuni', 'rifiuti_comuni_%d.csv' % y))
            brutte = 0
            for r in rs:
                s = (r['tot_rd'] or 0) + (r['ingombranti_smaltimento'] or 0) + (r['indifferenziato'] or 0)
                if r['tot_ru'] is not None and abs(s - r['tot_ru']) > 0.01 * max(1, r['tot_ru']):
                    brutte += 1
                w.writerow([y, r['cod'], r['regione'], r['provincia'], r['comune'], r['pop'], r['riferito_a']] +
                           ['' if r[c] is None else r[c] for c in COL_T] + ['' if r['rd_pct_ispra'] is None else r['rd_pct_ispra']])
            righe += len(rs)
            controlli['rifiuti'][y] = {'righe': len(rs), 'aggregazioni': sum(1 for r in rs if r['riferito_a'] != 'Comune'),
                                      'righe_con_RD+ingombranti+indiff_diverso_da_RU_oltre_1pct': brutte}
    controlli['rifiuti_righe_totali'] = righe

    # ---------------- costi per comune
    colonne = ['CRTab', 'CTSab', 'CACab', 'CGINDab', 'CRDab', 'CTRab', 'CGDab', 'CSLab', 'CCab', 'CKab', 'Altri costi', 'CTOTab']
    righe = 0
    with open(os.path.join(out, 'costi_comuni_lungo.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n')
        w.writerow(['anno', 'cod_istat', 'comune', 'provincia', 'n_comuni', 'popolazione'] + colonne)
        for y in range(2011, 2025):
            p = os.path.join(raw, 'ispra_costi', 'costi_procapite_%d.csv' % y)
            rs = leggi_ispra_costi(p)
            for r in rs:
                w.writerow([y, r['cod'], r['comune'], r['provincia'], r['n_comuni'], int(r.get('Pop.(abitanti)') or 0)] +
                           ['' if r.get(c) is None else r[c] for c in colonne])
            righe += len(rs)
            controlli['costi'][y] = {'righe': len(rs), 'colonne_presenti': sorted(set(k for r in rs[:50] for k in r) - {'cod', 'comune', 'provincia', 'n_comuni'})}
    controlli['costi_righe_totali'] = righe
    with open(os.path.join(out, 'controlli.json'), 'w', encoding='utf-8') as f:
        json.dump(controlli, f, ensure_ascii=False, indent=1)
    print('ok', controlli['rifiuti_righe_totali'], controlli['costi_righe_totali'])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
