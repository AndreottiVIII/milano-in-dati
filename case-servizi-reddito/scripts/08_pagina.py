"""08_pagina.py - prepara i dati della pagina docs/case-servizi-reddito/ (filone 12 x 9).

Uso (Python 3.12):  python -I -X utf8 08_pagina.py ABS CS
  ABS = percorso assoluto di milano-in-dati
  CS  = percorso assoluto di milano-in-dati/case-servizi-reddito

Legge SOLO i file gia' prodotti in CS/out (fase 1) e i nomi brevi delle zone da
docs/prezzi-case/data/zone.geojson (in sola lettura; la pagina usa quel file per
URL relativo, non lo copia). Scrive in ABS/docs/case-servizi-reddito/data/:
  riepilogo.json                    tutti i numeri della pagina
  zone_servizi_prezzo.csv           una riga per zona (prezzo, servizi, reddito, residuo del modello)
  servizi_singoli.csv, modelli.csv, robustezza.csv, stessa_distanza.csv,
  gruppi_terzili.csv, spearman_parziale.csv   (copie con etichette in italiano)
Si puo' rilanciare: riscrive tutto da capo. Le uniche rielaborazioni sono
(1) il passaggio da coefficiente di log a percentuale, exp(b)-1,
(2) le rette e i punti "corretti" del grafico principale (stesse 4 regressioni di
    modelli.csv, rifatte qui con numpy e CONTROLLATE contro i coefficienti del file).
"""
import csv, json, math, os, shutil, sys
from decimal import Decimal, ROUND_HALF_UP
import numpy as np

if len(sys.argv) != 3:
    sys.exit(__doc__)
ABS, CS = sys.argv[1], sys.argv[2]
OUT = os.path.join(CS, 'out')
DST = os.path.join(ABS, 'docs', 'case-servizi-reddito', 'data')
os.makedirs(DST, exist_ok=True)


def rd(name):
    with open(os.path.join(OUT, name), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def fl(x):
    return None if x in ('', None) else float(x)


def hu(x, d=2):                   # arrotondamento 'normale' (0,735 -> 0,74)
    return float(Decimal(str(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def pct(b):                       # coefficiente di log -> variazione percentuale
    return round((math.exp(b) - 1) * 100, 1)


# ---------------------------------------------------------------- lettura
zt = {r['zona']: r for r in rd('zone_tabella.csv')}
so = {r['zona']: r for r in rd('sorprese_zone.csv')}
modelli = {r['modello']: r for r in rd('modelli.csv')}
robu = rd('robustezza.csv')
sing = rd('servizi_singoli.csv')
par = rd('spearman_parziale.csv')
terz = rd('gruppi_terzili.csv')
sdist = rd('stessa_distanza.csv')
corr = rd('correlazioni_spearman.csv')
R3 = json.load(open(os.path.join(OUT, 'risultati_03.json'), encoding='utf-8'))
L1 = json.load(open(os.path.join(OUT, 'log_01.json'), encoding='utf-8'))
L2 = json.load(open(os.path.join(OUT, 'log_02.json'), encoding='utf-8'))
capz = rd('cap_per_zona.csv')
NIL = json.load(open(os.path.join(OUT, 'nil_risultati.json'), encoding='utf-8'))
gj = json.load(open(os.path.join(ABS, 'docs', 'prezzi-case', 'data', 'zone.geojson'), encoding='utf-8'))
breve = {f['properties']['zona']: f['properties']['nome_breve'] for f in gj['features']}

# ---------------------------------------------------------------- zone
zone = []
for z, r in zt.items():
    if r['prezzo_eur_m2'] == '':          # R2: nessun prezzo OMI
        continue
    camp = z in so
    s = so.get(z)
    row = dict(
        zona=z, nome=r['nome'], nome_breve=breve.get(z, r['nome']), fascia=r['fascia'],
        stato=r['stato_prevalente'], in_campione=camp,
        n_civici_res=int(r['n_civici_residenziali']), residenti=round(fl(r['residenti_stimati'])),
        s10=fl(r['servizi10_pesato']), s20=fl(r['servizi20_pesato']), sx=fl(r['servizi_extra_pesato']),
        reddito=fl(r['reddito_imponibile_medio_2024_pesato']), n_cap=int(r['n_cap']),
        dist_km=fl(r['dist_duomo_centroide_m']) / 1000,
        prezzo=fl(r['prezzo_eur_m2']), prezzo_min=fl(r['prezzo_min']), prezzo_max=fl(r['prezzo_max']),
        affitto=fl(r['affitto_eur_m2_mese']),
    )
    if camp:
        rb = fl(s['residuo_B_con_distanza_reddito'])
        row.update(
            prezzo_atteso=round(fl(s['prezzo_atteso_B'])),
            residuo_pct=round((math.exp(rb) - 1) * 100, 1),
            rango_s10=fl(s['rango_servizi10']), rango_s20=fl(s['rango_servizi20']),
            rango_prezzo=fl(s['rango_prezzo']),
            scarto_s10=fl(s['scarto_rango_servizi10_meno_prezzo']),
            scarto_s20=fl(s['scarto_rango_servizi20_meno_prezzo']))
    zone.append(row)
zone.sort(key=lambda r: -r['prezzo'])
camp = [r for r in zone if r['in_campione']]
assert len(camp) == 41, len(camp)

# ---------------------------------------------------------------- 4 regressioni del grafico principale
S = np.array([r['s20'] for r in camp])
lnP = np.log([r['prezzo'] for r in camp])
lnD = np.log([r['dist_km'] for r in camp])
lnY = np.log([r['reddito'] for r in camp])
refD, refY = float(np.median(lnD)), float(np.median(lnY))
MOD = [('nessuno', 'S20 solo', []), ('dist', 'S20 + distanza', ['D']),
       ('red', 'S20 + reddito', ['Y']), ('dist_red', 'S20 + distanza + reddito', ['D', 'Y'])]
modi = []
for mid, mname, ctr in MOD:
    cols = [np.ones(41), S] + ([lnD] if 'D' in ctr else []) + ([lnY] if 'Y' in ctr else [])
    X = np.column_stack(cols)
    beta = np.linalg.lstsq(X, lnP, rcond=None)[0]
    m = modelli[mname]
    assert abs(beta[1] - fl(m['b_S20'])) < 2e-4, (mid, beta[1], m['b_S20'])
    k = 2
    cD = cY = 0.0
    if 'D' in ctr:
        cD = beta[k]; assert abs(cD - fl(m['b_lnD'])) < 2e-4; k += 1
    if 'Y' in ctr:
        cY = beta[k]; assert abs(cY - fl(m['b_lnY'])) < 2e-4
    # prezzo "come se" la zona fosse alla distanza e al reddito mediani (residuo parziale)
    yadj = lnP - cD * (lnD - refD) - cY * (lnY - refY)
    b1, a1 = np.polyfit(S, yadj, 1)
    assert abs(b1 - beta[1]) < 1e-6
    for r, v in zip(camp, yadj):
        r.setdefault('adj', {})[mid] = round(float(math.exp(v)))
    modi.append(dict(
        id=mid, modello=mname, controlli=ctr, n=int(m['n']), b=round(float(b1), 5),
        pct=pct(float(b1)), ic=[pct(fl(m['ic95_boot_basso'])), pct(fl(m['ic95_boot_alto']))],
        r2=round(fl(m['r2']), 3), a=round(float(a1), 5)))
rng = R3['range_S20_zone']
for m in modi:
    m['linea'] = [[x, round(math.exp(m['a'] + m['b'] * x))] for x in (10.5, 20.0)]
dist_ref_km = round(math.exp(refD), 2)
red_ref = round(math.exp(refY))

# controllo incrociato con risultati_03.json
assert modi[0]['pct'] == R3['coef_S20_solo_pct_per_servizio'], modi[0]['pct']
assert modi[3]['pct'] == R3['coef_S20_controllato_pct_per_servizio'], modi[3]['pct']
assert modi[3]['ic'] == R3['coef_S20_controllato_ic_boot_pct'], modi[3]['ic']

# ---------------------------------------------------------------- servizi singoli
LAB = dict(metro='Metro', poste='Uffici postali', cani='Aree cani', supermercati='Supermercati',
           ospedali='Ospedali', teatri_musei='Teatri e musei', cinema='Cinema', bikemi='BikeMi',
           scuole='Scuole', piscine='Piscine', sport='Impianti sportivi', giochi='Aree gioco',
           vicinato='Negozi di vicinato', nidi='Asili nido', librerie='Librerie', farmacie='Farmacie',
           medici='Medici di base', mercati='Mercati', parchi='Parchi', biblioteche='Biblioteche')
servizi = []
for r in sing:
    servizi.append(dict(
        id=r['servizio'], nome=LAB[r['servizio']], tipo=r['tipo'], quota=round(fl(r['quota_media_zone']) * 100),
        spearman=round(fl(r['spearman_prezzo']), 2), parz=round(fl(r['spearman_parziale']), 2),
        ic=[round(fl(r['ic95_basso']), 2), round(fl(r['ic95_alto']), 2)]))
servizi.sort(key=lambda s: -s['parz'])
assert len(servizi) == 20

# ---------------------------------------------------------------- altri blocchi
def mrow(name):
    m = modelli[name]
    return dict(modello=name, b=fl(m['b_target']), pct=pct(fl(m['b_target'])),
                ic=[pct(fl(m['ic95_boot_basso'])), pct(fl(m['ic95_boot_alto']))], n=int(m['n']))

ess = mrow('essenziali(10) + extra + distanza + reddito [effetto essenziali]')
ext = mrow('essenziali(10) + extra + distanza + reddito [effetto extra]')
fasce_omi = mrow('S20 + distanza + reddito + fascia OMI')

parz = {}
for r in par:
    parz.setdefault(r['servizi'], {})[r['controlli']] = [round(fl(r['spearman_parziale']), 2),
                                                          round(fl(r['ic95_basso']), 2), round(fl(r['ic95_alto']), 2)]
sp = {r['coppia']: [round(fl(r['spearman']), 2), round(fl(r['ic95_basso']), 2), round(fl(r['ic95_alto']), 2)] for r in corr}

robustezza = [dict(variante=r['variante'], n=int(r['n']), pct=round(fl(r['pct_per_servizio']), 1), r2=None if r['r2'] == '' else round(fl(r['r2']), 2),
                   ic=None if r['ic95_boot_basso_pct'] == '' else [round(fl(r['ic95_boot_basso_pct']), 1), round(fl(r['ic95_boot_alto_pct']), 1)])
              for r in robu]

terzili = [dict(criterio=r['criterio'], terzile=r['terzile'], n=int(r['n_zone']), valore=round(fl(r['valore_mediano']), 2),
                prezzo=round(fl(r['prezzo_mediano'])), pmin=round(fl(r['prezzo_min'])), pmax=round(fl(r['prezzo_max'])),
                affitto=round(fl(r['affitto_mediano']), 2)) for r in terz]

stessa = [dict(fascia=r['fascia_distanza'], n=int(r['n']), km=[round(fl(r['dist_km_da']), 1), round(fl(r['dist_km_a']), 1)],
               prezzo_piu=round(fl(r['prezzo_mediano_piu_servizi'])), prezzo_meno=round(fl(r['prezzo_mediano_meno_servizi'])),
               s20_piu=round(fl(r['servizi20_mediano_piu']), 1), s20_meno=round(fl(r['servizi20_mediano_meno']), 1),
               red_piu=round(fl(r['reddito_mediano_piu'])), red_meno=round(fl(r['reddito_mediano_meno']))) for r in sdist]

nil_r = NIL['risultati']['prezzo per residenti']
nil_a = NIL['risultati']['prezzo per area']
nil = dict(
    n_ammessi=NIL['nil_ammessi'], n_totali=NIL['n_nil'], zone_dominanti=NIL['zone_OMI_distinte_come_dominanti'],
    quota_dominante_80=round(NIL['quota_nil_con_zona_dominante_ge80pct'] * 100, 1),
    quota_due_zone=round(NIL['quota_nil_che_toccano_2_o_piu_zone_ge10pct'] * 100, 1),
    spearman_servizi20=[hu(x) for x in nil_r['spearman_prezzo-servizi20']],
    lordo=[nil_r['reg S20 solo']['pct_per_servizio'], nil_r['reg S20 solo']['ic95_grappoli_pct']],
    controllato=[nil_r['reg S20 + distanza + reddito']['pct_per_servizio'], nil_r['reg S20 + distanza + reddito']['ic95_grappoli_pct']],
    controllato_area=[nil_a['reg S20 + distanza + reddito']['pct_per_servizio'], nil_a['reg S20 + distanza + reddito']['ic95_grappoli_pct']],
    puliti=[NIL['n_nil_puliti_ge80pct'], NIL['reg_nil_puliti_prezzo_residenti']['pct_per_servizio'],
            NIL['reg_nil_puliti_prezzo_residenti']['ic95_grappoli_pct']])

un_m2 = R3['un_servizio_in_piu_eur_m2']
un_70 = R3['un_servizio_in_piu_eur_appartamento_70m2']
valore = dict(
    eur_m2=un_m2[0], eur_m2_ic=[un_m2[1], un_m2[2]],
    eur_70=int(round(un_70[0], -2)), eur_70_ic=[int(round(un_70[1], -2)), int(round(un_70[2], -3))],
    prezzo_mediano=R3['prezzo_mediano_zone_principale_eur_m2'], sd=R3['sd_S20_zone'], sd_pct=R3['un_sd_di_servizi_pct_controllato'],
    sopravvive=round(R3['quota_coefficiente_che_sopravvive_S20'] * 100), range_s20=rng,
    loo=R3['loo'], r2=R3['r2'], vif=R3['VIF'])

def pick(z):
    r = next(r for r in zone if r['zona'] == z)
    return dict(zona=z, nome=r['nome_breve'], s10=r['s10'], s20=r['s20'], prezzo=r['prezzo'], n_civici_res=r['n_civici_res'])

sorpresa = dict(quarto_oggiaro=pick('E8'), citylife=pick('C13'), porta_nuova=pick('C14'), sant_ambrogio=pick('B16'),
                venezia=pick('B19'), brera=pick('B15'),
                rango_s10_e8=next(r for r in camp if r['zona'] == 'E8')['rango_s10'],
                rango_prezzo_e8=next(r for r in camp if r['zona'] == 'E8')['rango_prezzo'])

tracce = dict(
    n_zone_omi=L1['n_zone'], area_km2=L1['area_totale_km2'], area_sovrapposta_m2=L1['area_sovrapposta_tra_zone_m2'],
    n_civici=L1['n_civici'], civici_in_due_zone=L1['civici_in_piu_zone'], civici_fuori_zona=L1['civici_fuori_zona_riparati_entro_50m'],
    residenti=L1['residenti_distribuiti'], n_ottimo=L2['stato_prevalente']['OTTIMO'], n_normale=L2['stato_prevalente']['NORMALE'],
    zone_con_2_cap_ge10=sum(1 for r in capz if int(float(r['n_cap_ge10pct'])) >= 2),
    zone_con_un_cap_ge90=sum(1 for r in capz if float(r['quota_cap_principale']) > 0.9),
    n_zone_cap=len(capz))
assert tracce['zone_con_2_cap_ge10'] == 30 and tracce['zone_con_un_cap_ge90'] == 12, tracce

riep = dict(
    meta=dict(semestre='2026/1', n_zone=41, n_zone_con_prezzo=len(zone), data_omi='30 ottobre 2026', data_comune='29 ottobre 2026',
              dist_ref_km=dist_ref_km, red_ref=red_ref, campione_esclusi=R3['zone_escluse_dal_principale'],
              etichette_scatter=['E8', 'B19', 'C14', 'B15', 'C13']),
    zone=zone, modi=modi, servizi=servizi, essenziali=ess, extra=ext, fasce_omi=fasce_omi,
    spearman=sp, parziale=parz, robustezza=robustezza, terzili=terzili, stessa_distanza=stessa,
    nil=nil, valore=valore, sorpresa=sorpresa, tracce=tracce)
with open(os.path.join(DST, 'riepilogo.json'), 'w', encoding='utf-8') as f:
    json.dump(riep, f, ensure_ascii=False, separators=(',', ':'))

# ---------------------------------------------------------------- CSV
def wcsv(name, head, rows):
    with open(os.path.join(DST, name), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)

wcsv('zone_servizi_prezzo.csv',
     ['zona', 'nome', 'in_campione_principale', 'stato_omi', 'fascia_omi', 'civici_residenziali', 'servizi_su_10_essenziali', 'servizi_su_20',
      'servizi_extra_su_10', 'reddito_imponibile_medio_2024_per_cap', 'distanza_duomo_km', 'prezzo_omi_eur_m2_stima', 'prezzo_min', 'prezzo_max',
      'affitto_omi_eur_m2_mese_stima', 'prezzo_atteso_dal_modello', 'scarto_dal_previsto_pct', 'posto_servizi_su_10', 'posto_servizi_su_20', 'posto_prezzo'],
     [[r['zona'], r['nome'], 'si' if r['in_campione'] else 'no', r['stato'], r['fascia'], r['n_civici_res'], round(r['s10'], 2), round(r['s20'], 2),
       round(r['sx'], 2), round(r['reddito']), round(r['dist_km'], 2), r['prezzo'], r['prezzo_min'], r['prezzo_max'], r['affitto'],
       r.get('prezzo_atteso', ''), r.get('residuo_pct', ''), r.get('rango_s10', ''), r.get('rango_s20', ''), r.get('rango_prezzo', '')] for r in zone])
wcsv('servizi_singoli.csv', ['servizio', 'tipo', 'quota_media_residenti_con_servizio_entro_15_min_pct', 'spearman_con_prezzo', 'spearman_parziale_controllo_distanza_reddito', 'ic95_basso', 'ic95_alto'],
     [[s['nome'], s['tipo'], s['quota'], s['spearman'], s['parz'], s['ic'][0], s['ic'][1]] for s in servizi])
for n in ('modelli.csv', 'robustezza.csv', 'stessa_distanza.csv', 'gruppi_terzili.csv', 'spearman_parziale.csv'):
    shutil.copyfile(os.path.join(OUT, n), os.path.join(DST, n))
print('ok', DST, len(zone), 'zone;', os.path.getsize(os.path.join(DST, 'riepilogo.json')), 'byte')
print('rif. distanza km', dist_ref_km, 'reddito', red_ref)
for m in modi:
    print(m['id'], m['pct'], m['ic'], m['r2'])
print('ess', ess, 'ext', ext)
