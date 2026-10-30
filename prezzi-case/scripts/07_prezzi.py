"""Prezzi OMI di Milano per zona/tipologia/semestre: valore medio del campo (min+max)/2 con l'ampiezza, nominale e reale (ISTAT FOI
senza tabacchi, euro 2025), vendita e affitto, rapporto affitto/prezzo.
Entrate (in <pulito>/): omi_milano_valori.csv (da 06_leggi_omi.py), foi_mensile.csv (da 03_istat_foi.py),
                        zone_serie.csv (da 05_zone_corrispondenza.py, facoltativo)
Uscite (in <pulito>/):
  prezzi_zona_semestre.csv        una riga per semestre/zona/tipologia/stato (tutte le righe OMI, nessuna scartata)
  prezzi_zona_semestre_prevalente.csv  solo la riga di stato prevalente di ogni tipologia (Stato_prev = P)
  prezzi_citta_mediana_zone.csv   mediana NON pesata fra le zone, per semestre e tipologia (non e' un prezzo medio della citta')
Definizioni:
  centro   = (min + max) / 2           (euro/m2 per la vendita; euro/m2/mese per l'affitto)
  ampiezza = max - min ; ampiezza_rel = ampiezza / centro
  deflatore del semestre = media dell'indice FOI senza tabacchi nei mesi del semestre (gen-giu o lug-dic), 2025 = 100
  reale_2025 = nominale * 100 / deflatore      (si paga attenzione: ultimo semestre puo' avere meno di 6 mesi di indice)
  resa_lorda_annua = affitto_centro * 12 / prezzo_centro      anni_di_affitto = 1 / resa_lorda_annua
  un valore 0 o vuoto significa "dato assente", non zero: diventa vuoto e la riga e' segnalata (flag_loc / flag_compr).
Uso: python -I 07_prezzi.py <cartella_pulito>
"""
import sys, os
import numpy as np
import pandas as pd

CATEGORIA = {1: 'residenziale', 19: 'residenziale', 20: 'residenziale', 21: 'residenziale', 22: 'residenziale',
             5: 'commerciale', 9: 'commerciale', 17: 'commerciale', 23: 'commerciale', 24: 'commerciale',
             6: 'terziaria', 18: 'terziaria', 7: 'produttiva', 8: 'produttiva', 10: 'produttiva',
             13: 'parcheggi', 14: 'parcheggi', 15: 'parcheggi', 16: 'parcheggi'}


def main():
    p = sys.argv[1]
    v = pd.read_csv(os.path.join(p, 'omi_milano_valori.csv'), dtype={'zona': str, 'stato': str, 'stato_prev': str, 'fascia': str})
    f = pd.read_csv(os.path.join(p, 'foi_mensile.csv'))
    f['anno'] = f.mese.str[:4].astype(int)
    f['mm'] = f.mese.str[5:7].astype(int)
    f['sem'] = np.where(f.mm <= 6, 1, 2)
    d = f.groupby(['anno', 'sem']).agg(deflatore_foi_2025_100=('indice_raccordato_2025_100', 'mean'), mesi_indice=('mese', 'count')).reset_index()
    v = v.merge(d, on=['anno', 'sem'], how='left')
    mancano = v[v.deflatore_foi_2025_100.isna()].semestre.unique()
    if len(mancano):
        print('ATTENZIONE: nessun indice FOI per i semestri', list(mancano), '-> colonne reali vuote')

    for k, (a, b, nome) in {'compr': ('compr_min', 'compr_max', 'vendita'), 'loc': ('loc_min', 'loc_max', 'affitto')}.items():
        lo, hi = v[a].replace(0, np.nan), v[b].replace(0, np.nan)
        bad = lo.isna() | hi.isna()
        lo, hi = lo.where(~bad), hi.where(~bad)
        v[f'{k}_centro'] = (lo + hi) / 2
        v[f'{k}_ampiezza'] = hi - lo
        v[f'{k}_ampiezza_rel'] = (hi - lo) / v[f'{k}_centro']
        v[f'{k}_centro_reale_2025'] = v[f'{k}_centro'] * 100 / v['deflatore_foi_2025_100']
        v[f'flag_{k}'] = np.where(bad, 'dato assente (0 o vuoto)', np.where(lo > hi, 'min > max', ''))
    v['resa_lorda_annua'] = v.loc_centro * 12 / v.compr_centro
    v['anni_di_affitto_per_il_prezzo'] = 1 / v.resa_lorda_annua
    v['categoria'] = v.cod_tip.map(lambda x: CATEGORIA.get(int(x), 'altro') if pd.notna(x) else 'altro')
    sp = os.path.join(p, 'zone_serie.csv')
    if os.path.exists(sp):
        s = pd.read_csv(sp, dtype={'zona': str})[['semestre', 'zona', 'periodo', 'id_serie', 'id_serie_larga']]
        v = v.merge(s, on=['semestre', 'zona'], how='left')
        nuovi = v[v.periodo.isna()].semestre.unique()
        if len(nuovi):
            print('Nota: semestri senza perimetri (id_serie vuoto):', list(nuovi)[:6], '...' if len(nuovi) > 6 else '')
    v['prevalente'] = (v.stato_prev.fillna('').str.upper() == 'P')
    v['prevalente_metodo'] = np.where(v.prevalente, 'Stato_prev = P nel file VALORI', '')
    # semestri in cui nessuna riga porta il marcatore P (formato vecchio): uso lo stato prevalente del file ZONE, altrimenti NORMALE
    senza = [sm for sm, g in v.groupby('semestre') if not g.prevalente.any()]
    if senza:
        zp = os.path.join(p, 'omi_milano_zone.csv')
        zz = pd.read_csv(zp, dtype=str) if os.path.exists(zp) else pd.DataFrame(columns=['semestre', 'zona', 'stato_prev'])
        sp_ = {'N': 'NORMALE', 'O': 'OTTIMO', 'S': 'SCADENTE'}
        for sm in senza:
            m = v.semestre == sm
            zs = zz[zz.semestre == sm].set_index('zona').stato_prev.to_dict() if len(zz) else {}
            atteso = v[m].zona.map(lambda z: sp_.get((zs.get(z) or 'N')[:1].upper(), 'NORMALE'))
            v.loc[m, 'prevalente'] = (v[m].stato.str.upper() == atteso)
            v.loc[m, 'prevalente_metodo'] = np.where(v.loc[m, 'prevalente'], 'ricostruito da stato prevalente del file ZONE (o NORMALE)', '')
        print('Nota: semestri senza marcatore P, prevalente ricostruito:', senza)
    cols = ['semestre', 'anno', 'sem', 'periodo', 'id_serie', 'id_serie_larga', 'fascia', 'zona', 'link_zona', 'cod_tip', 'tipologia', 'categoria', 'stato', 'prevalente', 'prevalente_metodo',
            'compr_min', 'compr_max', 'compr_centro', 'compr_ampiezza', 'compr_ampiezza_rel', 'compr_centro_reale_2025', 'flag_compr',
            'loc_min', 'loc_max', 'loc_centro', 'loc_ampiezza', 'loc_ampiezza_rel', 'loc_centro_reale_2025', 'flag_loc',
            'resa_lorda_annua', 'anni_di_affitto_per_il_prezzo', 'deflatore_foi_2025_100', 'mesi_indice', 'sup_compr', 'sup_loc']
    for c in cols:
        if c not in v:
            v[c] = np.nan
    v = v[cols].sort_values(['anno', 'sem', 'zona', 'cod_tip', 'stato'])
    v.round(4).to_csv(os.path.join(p, 'prezzi_zona_semestre.csv'), index=False)
    pv = v[v.prevalente]
    pv.round(4).to_csv(os.path.join(p, 'prezzi_zona_semestre_prevalente.csv'), index=False)
    g = pv.groupby(['semestre', 'anno', 'sem', 'categoria', 'cod_tip', 'tipologia']).agg(
        n_zone=('zona', 'nunique'),
        compr_mediana_zone=('compr_centro', 'median'), compr_mediana_zone_reale_2025=('compr_centro_reale_2025', 'median'),
        loc_mediana_zone=('loc_centro', 'median'), loc_mediana_zone_reale_2025=('loc_centro_reale_2025', 'median'),
        resa_lorda_mediana=('resa_lorda_annua', 'median')).reset_index()
    g.round(4).to_csv(os.path.join(p, 'prezzi_citta_mediana_zone.csv'), index=False)
    print(f'prezzi_zona_semestre.csv: {len(v)} righe; prevalenti: {len(pv)}; mediane: {len(g)}')


if __name__ == '__main__':
    main()
