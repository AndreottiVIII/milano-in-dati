"""Passo 2 - indicatori grezzi per NIL (nessuna standardizzazione qui).

Ogni indicatore: valore per NIL, finestra, fonte (file e campo) in out/indicatori_definizioni.csv.
Indicatori "di nucleo" (entrano nell'indice): reddito_var, prezzo_var, affitto_var, airbnb_100, ristoranti_var,
                                              giovani_var, laureati_var
Indicatori "di contesto" (non entrano nell'indice di base; servono per descrivere e per le varianti):
   pop_var, stranieri_var, eta_media_var, scuole_var, airbnb_cresc_100, ... e i livelli (reddito_2024, prezzo_2026, laureati_2023)
Non disponibili al momento della stesura: botteghe storiche (botteghe/pulito vuota), nuove costruzioni (costruzioni/pulito vuota).
Uso: python -I -X utf8 02_indicatori.py <milano-in-dati> <quartieri-che-cambiano>
"""
import sys, os, json
import numpy as np
import pandas as pd

BASE = sys.argv[1]
QC = sys.argv[2]
OUT = os.path.join(QC, 'out')
P = lambda *a: os.path.join(BASE, *a)
defs = []   # (id, etichetta, unita, verso, finestra, fonte, ruolo)
log = {}


def aggiungi(i, et, un, verso, fin, fonte, ruolo):
    defs.append(dict(id=i, etichetta=et, unita=un, verso=verso, finestra=fin, fonte=fonte, ruolo=ruolo))


nil = pd.read_csv(P('popolazione', 'pulito', 'nil_anagrafica.csv'))[['id_nil', 'nil', 'area_km2']]
nil['nil'] = nil['nil'].str.replace("Citta' studi", "Città Studi")
D = nil.set_index('id_nil')

# ---------------------------------------------------------------- popolazione (anagrafe, ds27) 2014 -> 2025
e = pd.read_csv(P('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
e = e.set_index(['anno', 'id_nil'])
r14, r25, r24 = e.loc[2014], e.loc[2025], e.loc[2024]
D['residenti_2024'] = r24['residenti']
D['residenti_2014'] = r14['residenti']
D['residenti_2025'] = r25['residenti']
D['pop_var'] = (r25['residenti'] / r14['residenti'] - 1) * 100
g14 = r14['n_25_34'] / r14['residenti'] * 100
g25 = r25['n_25_34'] / r25['residenti'] * 100
D['giovani_2025'] = g25
D['giovani_var'] = g25 - g14
D['stranieri_2025'] = r25['quota_stranieri'] * 100
D['stranieri_var'] = (r25['quota_stranieri'] - r14['quota_stranieri']) * 100
D['eta_media_var'] = r25['eta_media'] - r14['eta_media']
F = 'popolazione/pulito/eta_nil_anno_indicatori.csv'
aggiungi('giovani_var', 'Quota di residenti di 25-34 anni: variazione', 'punti percentuali', '+ = piu\' giovani adulti',
         '1/1/2014 -> 2025', f'{F}: n_25_34 / residenti, anni 2014 e 2025 (anagrafe, ds27 del Comune)', 'nucleo')
aggiungi('pop_var', 'Residenti: variazione', '%', 'contesto (cresce anche dove si costruisce)', '2014 -> 2025',
         f'{F}: residenti', 'contesto')
aggiungi('stranieri_var', 'Quota di residenti stranieri: variazione', 'punti percentuali', 'contesto (verso ambiguo)',
         '2014 -> 2025', f'{F}: quota_stranieri', 'contesto')
aggiungi('eta_media_var', 'Eta media: variazione', 'anni', 'contesto', '2014 -> 2025', f'{F}: eta_media', 'contesto')

# ---------------------------------------------------------------- laureati (censimenti) 2011 -> 2023
c = pd.read_csv(P('censimenti', 'pulito', 'indicatori_NIL.csv'))
c = c.set_index(['anno', 'nil'])
c11, c21, c23 = c.loc[2011], c.loc[2021], c.loc[2023]
D['laureati_2011'] = c11['quota_laureati_su_residenti']
D['laureati_2023'] = c23['quota_laureati_su_residenti']
D['laureati_var'] = c23['quota_laureati_su_residenti'] - c11['quota_laureati_su_residenti']
D['laureati_var_2011_2021'] = c21['quota_laureati_su_residenti'] - c11['quota_laureati_su_residenti']
D['pop_censimento_2011'] = c11['pop']
D['pop_censimento_2023'] = c23['pop']
D['abitazioni_2023'] = c23['abit_tot']
aggiungi('laureati_var', 'Laureati su residenti: variazione', 'punti percentuali', '+ = piu laureati',
         'censimento 2011 -> 2023',
         'censimenti/pulito/indicatori_NIL.csv: quota_laureati_su_residenti, anni 2011 e 2023 (cambia il tipo di censimento: vedi limiti)',
         'nucleo')

# ---------------------------------------------------------------- redditi (CAP) -> NIL con i civici
civ = pd.read_csv(os.path.join(OUT, 'civici_collegamenti.csv'))
res = civ[civ.RESIDENZIALE == 1].copy()
m = pd.read_csv(P('redditi', 'pulito', 'cap_milano_media_euro2025.csv')).set_index('cap')
n = pd.read_csv(P('redditi', 'pulito', 'cap_milano_contribuenti.csv')).set_index('cap')
capd = pd.DataFrame({'media_2011': m['2011'], 'media_2024': m['2024'], 'contrib_2011': n['2011'], 'contrib_2024': n['2024']})
capd['reddito_var'] = (capd.media_2024 / capd.media_2011 - 1) * 100
capd['contrib_var_pct'] = (capd.contrib_2024 / capd.contrib_2011 - 1) * 100
capd['instabile'] = capd.contrib_var_pct.abs() > 30
capd.to_csv(os.path.join(OUT, 'cap_reddito_variazione.csv'))
log['CAP_instabili'] = [int(i) for i in capd.index[capd.instabile]]
res['reddito_var_cap'] = res.CAP.map(capd.reddito_var.where(~capd.instabile))
res['reddito_var_cap_tutti'] = res.CAP.map(capd.reddito_var)
res['reddito_2024_cap'] = res.CAP.map(capd.media_2024)
agg = res.groupby('ID_NIL')
D['reddito_var'] = agg.reddito_var_cap.mean()
D['reddito_var_con_cap_instabili'] = agg.reddito_var_cap_tutti.mean()
D['reddito_2024'] = agg.reddito_2024_cap.mean()
D['quota_civici_cap_instabili'] = agg.apply(lambda g: g.CAP.map(capd.instabile).mean())
# se piu' della meta' dei civici del NIL sta in CAP instabili, il reddito del NIL non si assegna (resterebbe il dato di pochi civici)
D.loc[D.quota_civici_cap_instabili > 0.5, 'reddito_var'] = np.nan
FR = 'redditi/pulito/cap_milano_media_euro2025.csv (campi 2011, 2024); contribuenti: cap_milano_contribuenti.csv'
aggiungi('reddito_var', 'Reddito medio reale per contribuente: variazione', '%', '+ = reddito reale in crescita',
         'anno d\'imposta 2011 -> 2024', f'{FR}; dai 38 CAP ai NIL con i civici residenziali (CAP con contribuenti cambiati oltre 30% esclusi)', 'nucleo')

# ---------------------------------------------------------------- prezzi e affitti OMI (zona del civico) -> NIL
agg = res.groupby('ID_NIL')
D['prezzo_var'] = agg.crescita_prezzo.mean() * 100
D['affitto_var'] = agg.crescita_affitto.mean() * 100
D['prezzo_2026_reale'] = agg.prezzo_reale_1.mean()
D['affitto_2026_reale'] = agg.affitto_reale_1.mean()
D['copertura_omi'] = agg.crescita_prezzo.apply(lambda s: s.notna().mean())
# coperti al meno del 70%: non si assegna valore
D.loc[D.copertura_omi < 0.7, ['prezzo_var', 'affitto_var']] = np.nan
FP = 'prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv (abitazioni civili, stato prevalente; compr_centro_reale_2025 e loc_centro_reale_2025)'
aggiungi('prezzo_var', 'Prezzo di vendita OMI reale (stima): variazione', '%', '+ = prezzi in crescita',
         '2014/2 -> 2026/1', f'{FP}; zona di ogni civico residenziale nei perimetri di ciascun semestre (prezzi-case/raw/geopoi)', 'nucleo')
aggiungi('affitto_var', 'Affitto OMI reale (stima): variazione', '%', '+ = affitti in crescita',
         '2014/2 -> 2026/1', FP + '; stesso metodo', 'nucleo')

# ---------------------------------------------------------------- affitti brevi
a = pd.read_csv(P('affitti-brevi', 'pulito', 'nil_riepilogo.csv')).set_index('nil')
D['airbnb_100'] = a['annunci_per_100_abitazioni'].where(~a['piccolo_denominatore'])
D['airbnb_annunci'] = a['annunci']
D['airbnb_100_grezzo'] = a['annunci_per_100_abitazioni']
D['abitazioni_airbnb_den'] = a['abitazioni_2023']
cr = pd.read_csv(P('affitti-brevi', 'pulito', 'crescita_nil.csv')).set_index('nil_id')
D['airbnb_cresc_100'] = ((cr['annunci_con_recensione_2025'] - cr['annunci_con_recensione_2019']) / a['abitazioni_2023'] * 100).where(~a['piccolo_denominatore'])
aggiungi('airbnb_100', 'Annunci Airbnb ogni 100 abitazioni', 'annunci per 100 abitazioni', '+ = piu affitti brevi',
         'fotografia 19/9/2026', 'affitti-brevi/pulito/nil_riepilogo.csv: annunci_per_100_abitazioni (NIL con piccolo_denominatore = vuoto)', 'nucleo')
aggiungi('airbnb_cresc_100', 'Annunci Airbnb con recensione: aumento 2019 -> 2025, per 100 abitazioni', 'annunci per 100 abitazioni',
         'contesto / variante', '2019 -> 2025', 'affitti-brevi/pulito/crescita_nil.csv: annunci_con_recensione_2025 meno annunci_con_recensione_2019; abitazioni: nil_riepilogo.csv abitazioni_2023', 'contesto')

# ---------------------------------------------------------------- locali (registro pubblici esercizi in piano)
rg = pd.read_csv(P('ristoranti', 'pulito', 'registro_2019_2026_nil.csv'), sep=';').set_index('id_nil')
net_ind = rg['indirizzi_nuovi'] - rg['indirizzi_scomparsi']
D['locali_2019'] = rg['registro_2019']
D['locali_2026'] = rg['registro_2026']
D['ristoranti_var'] = (net_ind / rg['registro_2019'] * 100).where(rg['registro_2019'] >= 20)
D['ristoranti_var_codici'] = (rg['variazione_netta'] / rg['registro_2019'] * 100).where(rg['registro_2019'] >= 20)
D['ristoranti_netto_indirizzi'] = net_ind
aggiungi('ristoranti_var', 'Locali di somministrazione (bar, ristoranti): indirizzi nuovi meno scomparsi, su pratiche 2019', '%',
         '+ = piu locali', '2019 -> 2026',
         'ristoranti/pulito/registro_2019_2026_nil.csv: (indirizzi_nuovi - indirizzi_scomparsi) / registro_2019; solo NIL con almeno 20 pratiche nel 2019', 'nucleo')

# ---------------------------------------------------------------- scuole (iscritti nelle scuole del NIL)
s = pd.read_csv(P('scuole', 'pulito', 'nil_iscritti_variazione_2015_2024.csv'), sep=';')
s['id_nil'] = s.id_nil.astype(int)
sg = s.groupby('id_nil')[['iscritti_2015', 'iscritti_2024']].sum(min_count=1)
D['scuole_2015'] = sg.iscritti_2015
D['scuole_2024'] = sg.iscritti_2024
D['scuole_var'] = ((sg.iscritti_2024 / sg.iscritti_2015 - 1) * 100).where(sg.iscritti_2015 >= 100)
aggiungi('scuole_var', 'Iscritti alle scuole del NIL (infanzia+primaria+media): variazione', '%', 'contesto (calo demografico di tutta la citta)',
         'a.s. 2015/16 -> 2024/25', 'scuole/pulito/nil_iscritti_variazione_2015_2024.csv: iscritti_2015, iscritti_2024 (somma dei tre ordini; NIL con meno di 100 iscritti nel 2015 = vuoto)', 'contesto')

# ---------------------------------------------------------------- non disponibili
for nome, cart in [('botteghe', 'botteghe'), ('costruzioni', 'costruzioni')]:
    pul = P(cart, 'pulito')
    log[f'{nome}_file_presenti'] = len(os.listdir(pul)) if os.path.isdir(pul) else 0

# idoneita': almeno 2.000 residenti nel 2024 (anagrafe)
D['idoneo'] = D.residenti_2024 >= 2000
log['NIL_idonei_ge2000_residenti_2024'] = int(D.idoneo.sum())
log['NIL_non_idonei'] = D.loc[~D.idoneo, 'nil'].tolist()

D.reset_index().to_csv(os.path.join(OUT, 'indicatori_nil.csv'), index=False)
pd.DataFrame(defs).to_csv(os.path.join(OUT, 'indicatori_definizioni.csv'), index=False)
json.dump(log, open(os.path.join(OUT, 'indicatori_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(log, ensure_ascii=False, indent=1))
core = ['reddito_var', 'prezzo_var', 'affitto_var', 'airbnb_100', 'ristoranti_var', 'giovani_var', 'laureati_var']
print(D.loc[D.idoneo, core + ['pop_var', 'stranieri_var', 'scuole_var']].describe().round(2).T)
print(D.loc[D.idoneo, core].isna().sum())
