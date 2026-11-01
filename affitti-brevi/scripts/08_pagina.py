r"""Fase 2 - dati della pagina "Affitti brevi" (docs/affitti-brevi/).
Uso: python -I -X utf8 08_pagina.py <affitti-brevi (assoluta)> <milano-in-dati (assoluta)>
Legge pulito\ (tabelle aggregate; annunci_snapshot.csv e il listings.csv.gz grezzo SOLO per calcolare conteggi), i poligoni dei NIL
(citta-15-minuti\out\nil_poligoni_punteggi.geojson) e i nomi delle zone OMI (docs\prezzi-case\data\zone.geojson).
Scrive in docs\affitti-brevi\data\: SOLO DATI AGGREGATI (per NIL, per zona OMI, per anno, per fascia di annunci per host).
LICENZA: Inside Airbnb chiede "Do not republish the data". Qui non esce nessuna riga per singolo annuncio, nessun host_id,
nessuna coordinata di annuncio: lo script, alla fine, controlla che nei file non compaiano colonne o campi di quel tipo.
Rilanciabile: riscrive sempre gli stessi file.
"""
import sys, json, csv, re
from pathlib import Path
import numpy as np
import pandas as pd

base = Path(sys.argv[1]); prog = Path(sys.argv[2])
P = base/'pulito'; OUT = prog/'docs'/'affitti-brevi'/'data'; OUT.mkdir(parents=True, exist_ok=True)
SN = '2026-09-19'
MIN_PREZZI_NIL = 30     # sotto questa soglia niente prezzo mediano per NIL
MIN_ANNUNCI_ZONA = 30   # sotto questa soglia la zona OMI e' in grigio nel conto del proprietario


def rd(name, **k): return pd.read_csv(P/name, **k)
def num(x, d=None):
    if x is None or (isinstance(x, float) and np.isnan(x)): return None
    return int(x) if d is None and float(x).is_integer() else (round(float(x), d) if d is not None else float(x))


R = {}
R['meta'] = dict(
    data_scarico='1/11/2026', snapshot_principale=SN,
    abitazioni_anno=2023, soglia_prezzi_nil=MIN_PREZZI_NIL, soglia_annunci_zona=MIN_ANNUNCI_ZONA,
    soglia_piccolo='meno di 2.000 abitazioni o meno di 2.000 residenti nel NIL (censimento permanente 2023)',
    superficie_ipotesi_mq=60, zone_omi_semestre='2026/1')

# ---------- snapshot ----------
sn = rd('riepilogo_snapshot.csv'); ctl = rd('snapshot_controlli.csv')
R['snapshot'] = [dict(snapshot=r.snapshot, annunci=int(r.totale), case_intere=int(r['Entire home/apt']), stanze_private=int(r['Private room']),
                      host=int(r.host_distinti), con_prezzo=int(c.prezzo_presente), CIN_formato_valido=int(r.CIN_formato_valido),
                      scarico_dal=c.last_scraped_min, scarico_al=c.last_scraped_max)
                 for (_, r), (_, c) in zip(sn.iterrows(), ctl.iterrows())]
L9 = sn[sn.snapshot == SN].iloc[0]
R['ultimo'] = dict(annunci=int(L9.totale), case_intere=int(L9['Entire home/apt']), stanze_private=int(L9['Private room']),
                   condivise=int(L9['Shared room']), hotel=int(L9['Hotel room']), host=int(L9.host_distinti),
                   quota_case_intere=round(L9['Entire home/apt']/L9.totale, 4), quota_stanze_private=round(L9['Private room']/L9.totale, 4),
                   con_recensione_12m=int(L9.con_recensione_ultimi_12_mesi))

# ---------- la sorpresa: notti fuori dagli alberghi (vyxt-7jdx) ----------
fl = rd('ufficiale_flussi_milano.csv')
fl = fl[fl.cittadinanza == 'Totale'].pivot(index='anno', columns='tipo_struttura', values='presenze')
fl = fl.rename(columns={'Es. Alberghieri': 'alb', 'Es. Extra-Alberghieri': 'extra', 'Totale': 'tot'})
assert (fl.alb+fl.extra == fl.tot).all()
fl['quota_extra'] = fl.extra/fl.tot
R['flussi'] = [dict(anno=int(a), alberghi=int(r.alb), extra=int(r.extra), totale=int(r.tot), quota_extra=round(float(r.quota_extra), 4)) for a, r in fl.iterrows()]
f19, f25, f22 = fl.loc[2019], fl.loc[2025], fl.loc[2022]
R['sorpresa'] = dict(
    anno0=2019, anno1=2025, alb0=int(f19.alb), alb1=int(f25.alb), var_alberghi=round(float(f25.alb/f19.alb-1), 4),
    extra0=int(f19.extra), extra1=int(f25.extra), moltiplicatore_extra=round(float(f25.extra/f19.extra), 2),
    tot0=int(f19.tot), tot1=int(f25.tot), var_totale=int(f25.tot-f19.tot),
    aggiunte_extra=int(f25.extra-f19.extra), perse_alberghi=int(f19.alb-f25.alb),
    quota0=round(float(f19.quota_extra), 4), quota2022=round(float(f22.quota_extra), 4), quota1=round(float(f25.quota_extra), 4))
fl.reset_index().rename(columns={'anno': 'anno', 'alb': 'presenze_alberghi', 'extra': 'presenze_extra_alberghiere', 'tot': 'presenze_totale'}).round({'quota_extra': 4}) \
  .to_csv(OUT/'notti_alberghi_extra.csv', index=False)

# ---------- NIL ----------
n = rd('nil_riepilogo.csv')
tot_ab = n.abitazioni_2023.sum(); tot_occ = n.abitazioni_occupate_da_residenti_2023.sum()
nr = n[~n.piccolo_denominatore]
R['citta'] = dict(
    abitazioni=int(tot_ab), abitazioni_occupate=int(tot_occ), annunci_per_100=round(100*n.annunci.sum()/tot_ab, 2),
    intere_per_100=round(100*n.case_intere.sum()/tot_ab, 2), nil_non_piccoli=int(len(nr)),
    mediana_nil_non_piccoli=round(float(nr.annunci_per_100_abitazioni.median()), 2), nil_5_o_piu=int((nr.annunci_per_100_abitazioni >= 5).sum()),
    nil_10_o_piu=int((nr.annunci_per_100_abitazioni >= 10).sum()),
    quota_annunci_10_nil_densi=round(float(nr.sort_values('annunci_per_100_abitazioni', ascending=False).annunci.head(10).sum()/n.annunci.sum()), 4),
    nil_con_annunci=int((n.annunci > 0).sum()), nil_totali=int(len(n)))
nilcsv = pd.DataFrame(dict(
    nil=n.nil, nome=n.nil_nome, residenti_2023=n.residenti_2023, abitazioni_2023=n.abitazioni_2023,
    abitazioni_non_occupate_da_residenti_2023=n.abitazioni_non_occupate_da_residenti_2023,
    annunci_2026_09=n.annunci, case_intere=n.case_intere, stanze_private=n.stanze_private,
    annunci_per_100_abitazioni=n.annunci_per_100_abitazioni.round(2), case_intere_per_100_abitazioni=n.case_intere_per_100_abitazioni.round(2),
    quota_case_intere=(n.case_intere/n.annunci.replace(0, np.nan)).round(3), quota_con_CIN_formato_valido=n.quota_annunci_con_CIN.round(3),
    n_prezzi_case_intere=n.n_prezzi.fillna(0).astype(int),
    prezzo_mediano_case_intere=np.where(n.n_prezzi.fillna(0) >= MIN_PREZZI_NIL, n.prezzo_mediano_case_intere_quotazione.round(0), np.nan),
    annunci_2025_12=n.annunci_dic2025, piccolo_denominatore=n.piccolo_denominatore))
nilcsv.to_csv(OUT/'nil.csv', index=False)

g = json.load(open(prog/'citta-15-minuti'/'out'/'nil_poligoni_punteggi.geojson', encoding='utf8'))
bynil = {int(r.nil): r for r in nilcsv.itertuples()}
feats = []
for f in g['features']:
    i = int(f['properties']['ID_NIL']); r = bynil[i]
    pr = dict(id=i, nome=r.nome, residenti=int(r.residenti_2023), abitazioni=int(r.abitazioni_2023),
              non_occupate=int(r.abitazioni_non_occupate_da_residenti_2023), annunci=int(r.annunci_2026_09), intere=int(r.case_intere),
              stanze=int(r.stanze_private), per100=num(r.annunci_per_100_abitazioni, 2), intere_per100=num(r.case_intere_per_100_abitazioni, 2),
              quota_intere=num(r.quota_case_intere, 3), cin=num(r.quota_con_CIN_formato_valido, 3), n_prezzi=int(r.n_prezzi_case_intere),
              prezzo=num(r.prezzo_mediano_case_intere, 0), piccolo=bool(r.piccolo_denominatore), dic2025=int(r.annunci_2025_12))
    feats.append(dict(type='Feature', properties=pr, geometry=f['geometry']))
json.dump(dict(type='FeatureCollection', features=feats), open(OUT/'nil.geojson', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

# ---------- crescita ----------
c = rd('crescita_confronto.csv'); c = c[(c.anno >= 2012) & (c.anno <= 2025)]
R['crescita'] = [dict(anno=int(r.anno), airbnb_annunci_recensiti=int(r.airbnb_annunci_con_recensione_unione), airbnb_recensioni=int(r.airbnb_recensioni_unione),
                      istat_extra_strutture=num(r.istat_extra_alberghieri_strutture), comune_cav_lt=num(r.comune_CAV_piu_LT),
                      accreditate_imposta=num(r.comune_accreditate_imposta_soggiorno_fine_anno)) for r in c.itertuples()]
c.rename(columns={'airbnb_annunci_con_recensione_unione': 'airbnb_annunci_con_recensione_nell_anno_unione_4_snapshot',
                  'airbnb_recensioni_unione': 'airbnb_recensioni_nell_anno_unione_4_snapshot'})[
    ['anno', 'airbnb_annunci_con_recensione_nell_anno_unione_4_snapshot', 'airbnb_recensioni_nell_anno_unione_4_snapshot',
     'istat_extra_alberghieri_strutture', 'comune_case_vacanza_CAV', 'comune_locazioni_turistiche', 'comune_CAV_piu_LT',
     'comune_accreditate_imposta_soggiorno_fine_anno']].to_csv(OUT/'crescita.csv', index=False)
cc = c.set_index('anno')
rev = cc.airbnb_recensioni_unione
R['crescita_note'] = dict(
    rec2014=int(rev[2014]), rec2015=int(rev[2015]), rec2016=int(rev[2016]), rec2019=int(rev[2019]), rec2020=int(rev[2020]), rec2025=int(rev[2025]),
    x_2015_su_2014=round(float(rev[2015]/rev[2014]), 1), x_2016_su_2015=round(float(rev[2016]/rev[2015]), 2), x_2020_su_2019=round(float(rev[2020]/rev[2019]), 2),
    ann2015=int(cc.airbnb_annunci_con_recensione_unione[2015]), ann2019=int(cc.airbnb_annunci_con_recensione_unione[2019]),
    ann2020=int(cc.airbnb_annunci_con_recensione_unione[2020]), ann2025=int(cc.airbnb_annunci_con_recensione_unione[2025]),
    x_airbnb_2019_2025=round(float(cc.airbnb_annunci_con_recensione_unione[2025]/cc.airbnb_annunci_con_recensione_unione[2019]), 1),
    istat2019=int(cc.istat_extra_alberghieri_strutture[2019]), istat2025=int(cc.istat_extra_alberghieri_strutture[2025]),
    x_istat_2019_2025=round(float(cc.istat_extra_alberghieri_strutture[2025]/cc.istat_extra_alberghieri_strutture[2019]), 1),
    comune2024=int(cc.comune_CAV_piu_LT[2024]), istat2024=int(cc.istat_extra_alberghieri_strutture[2024]), imposta2024=int(cc.comune_accreditate_imposta_soggiorno_fine_anno[2024]))
ra = rd('recensioni_anno.csv').set_index('anno')
er = []
for y in (2019, 2022, 2023, 2024, 2025):
    a0, a1 = int(ra.loc[y, 'annunci_con_recensione_nel_file_2025-12-26']), int(ra.loc[y, 'annunci_con_recensione_nel_file_2026-09-19'])
    r0, r1 = int(ra.loc[y, 'recensioni_nel_file_2025-12-26']), int(ra.loc[y, 'recensioni_nel_file_2026-09-19'])
    er.append(dict(anno=y, annunci_dic=a0, annunci_set=a1, var_annunci=round(a1/a0-1, 3), recensioni_dic=r0, recensioni_set=r1, var_recensioni=round(r1/r0-1, 3)))
R['erosione'] = er
R['recensioni_totali'] = dict(unione_4_snapshot=int(ra.recensioni_unione.sum()), ultimo_snapshot=int(ra.recensioni_ultimo.sum()))
assert R['recensioni_totali'] == dict(unione_4_snapshot=1312056, ultimo_snapshot=1171528)
pd.DataFrame(er).to_csv(OUT/'erosione_passato.csv', index=False)

# ---------- tre serie ufficiali sul numero di strutture ----------
R['tre_serie_2024'] = dict(istat=R['crescita_note']['istat2024'], comune=R['crescita_note']['comune2024'], imposta=R['crescita_note']['imposta2024'])
us = rd('ufficiale_strutture_milano.csv')
cav = us[us.tipo.str.startswith('VA')].set_index('periodo'); R['cav_posti_letto'] = {str(y): num(cav.loc[str(y), 'posti_letto']) for y in (2018, 2019)}
R['cav_strutture'] = {str(y): num(cav.loc[str(y), 'strutture']) for y in (2018, 2019)}

# ---------- host ----------
h = rd('host_concentrazione.csv')
R['host'] = [dict(fascia=str(r.annunci_per_host), host=int(r.host), annunci=int(r.annunci), quota_host=round(r.quota_host, 4), quota_annunci=round(r.quota_annunci, 4)) for r in h.itertuples()]
h.round(4).to_csv(OUT/'host_fasce.csv', index=False)
hosts_tot = int(h.host.sum()); ann_tot = int(h.annunci.sum())
h2 = h.iloc[1:]
# dettagli che richiedono il conteggio per host (calcolato in locale, esce solo l'aggregato)
a = pd.read_csv(P/'annunci_snapshot.csv', low_memory=False); L = a[a.snapshot == SN].copy()
hc = L.groupby('host_id').size().sort_values(ascending=False)
L['host_n'] = L.host_id.map(hc)
R['host_sintesi'] = dict(
    host_totali=hosts_tot, annunci_totali=ann_tot, host_con_1=int(h.host.iloc[0]), quota_host_con_1=round(float(h.quota_host.iloc[0]), 4),
    host_con_2_o_piu=int(h2.host.sum()), quota_host_con_2_o_piu=round(float(h2.host.sum()/hosts_tot), 4),
    quota_annunci_host_2_o_piu=round(float(h2.annunci.sum()/ann_tot), 4),
    host_20_o_piu=int(h.host.iloc[-1]), quota_host_20_o_piu=round(float(h.quota_host.iloc[-1]), 4), quota_annunci_host_20_o_piu=round(float(h.quota_annunci.iloc[-1]), 4),
    quota_annunci_host_5_o_piu=round(float((L.host_n >= 5).mean()), 4), quota_annunci_host_10_o_piu=round(float((L.host_n >= 10).mean()), 4),
    piu_grande=int(hc.iloc[0]), dieci_piu_grandi_annunci=int(hc.head(10).sum()), dieci_piu_grandi_quota=round(float(hc.head(10).sum()/len(L)), 4))
assert R['host_sintesi']['annunci_totali'] == len(L) and R['host_sintesi']['host_totali'] == len(hc)

# ---------- il conto del proprietario ----------
cs = rd('confronto_affitto_notti.csv')
R['conto_superficie'] = [dict(mq=int(r.superficie_mq), affitto=num(r.affitto_mediano), notti=round(r.notti_al_mese_mediana, 1), p25=round(r.notti_p25, 1), p75=round(r.notti_p75, 1),
                              meno_di_10=round(r.quota_con_meno_di_10_notti, 3)) for r in cs.itertuples()]
cs.round(3).to_csv(OUT/'conto_per_superficie.csv', index=False)
zn = {f['properties']['zona']: f['properties']['nome_breve'] for f in json.load(open(prog/'docs'/'prezzi-case'/'data'/'zone.geojson', encoding='utf8'))['features']}
cz = rd('confronto_affitto_notti_zone.csv')
cz['nome_breve'] = cz.zona.map(zn)
cz['poco_affidabile'] = cz.case_intere < MIN_ANNUNCI_ZONA
R['conto_zone'] = [dict(zona=r.zona, nome=r.nome_breve, fascia=r.fascia, n=int(r.case_intere), prezzo=num(r.prezzo_mediano, 1), loc_centro=num(r.loc_centro, 1),
                        affitto60=num(r.affitto_60mq_mensile, 0), notti=round(r.notti_al_mese_per_affitto_60mq, 1), notti_min=round(r.notti_con_affitto_min, 1),
                        notti_max=round(r.notti_con_affitto_max, 1), poco=bool(r.poco_affidabile)) for r in cz.itertuples()]
cz.round(2).drop(columns=['nome']).rename(columns={'nome_breve': 'nome_zona', 'case_intere': 'case_intere_con_prezzo', 'prezzo_mediano': 'prezzo_mediano_a_notte'}) \
  .to_csv(OUT/'conto_per_zona_omi.csv', index=False)
R['conto_zone_sintesi'] = dict(mediana_zone=round(float(cz.notti_al_mese_per_affitto_60mq.median()), 1),
                               min=round(float(cz.notti_al_mese_per_affitto_60mq.min()), 1), min_zona=cz.loc[cz.notti_al_mese_per_affitto_60mq.idxmin(), 'zona'],
                               max=round(float(cz.notti_al_mese_per_affitto_60mq.max()), 1), max_zona=cz.loc[cz.notti_al_mese_per_affitto_60mq.idxmax(), 'zona'],
                               n_zone=int(len(cz)), n_zone_poco=int(cz.poco_affidabile.sum()))

# occupazione stimata (modello Inside Airbnb) e ricavo: calcolati qui dalle righe locali, esce solo l'aggregato
L['is_ent'] = L.room_type == 'Entire home/apt'; L['ent_rec12'] = L.is_ent & (L.number_of_reviews_ltm > 0)
M = L[L.is_ent]
occ = M.est_occupancy_l365d
bins = [(0, 0, 'zero notti'), (1, 30, '1-30'), (31, 90, '31-90'), (91, 180, '91-180'), (181, 400, 'oltre 180')]
hist = []
for lo, hi, lab in bins:
    k = int(((occ >= lo) & (occ <= hi)).sum()); hist.append(dict(fascia=lab, case_intere=k, quota=round(k/len(M), 4)))
assert sum(x['case_intere'] for x in hist) == int(occ.notna().sum())
z = rd('confronto_affitto_notti_zone.csv')  # solo per coerenza dei nomi
zo = pd.read_csv(prog/'docs'/'prezzi-case'/'data'/'zone_ultimo_semestre.csv')[['zona', 'loc_centro']]
Mq = L[L.ent_rec12].merge(zo, left_on='zona_omi', right_on='zona', how='left')
Mq = Mq[Mq.loc_centro.notna() & Mq.est_revenue_l365d.notna() & (Mq.price_eur_quote <= 1000)]
ricavo = Mq.est_revenue_l365d/12; affitto60 = Mq.loc_centro*60
R['occupazione'] = dict(
    case_intere=int(len(M)), mediana=round(float(occ.median()), 0), media=round(float(occ.mean()), 1), quota_zero=round(float((occ == 0).mean()), 3),
    istogramma=hist, note_modello='Inside Airbnb: 50% delle prenotazioni lascia una recensione, soggiorno medio 3 notti (o il minimo di notti se piu alto), occupazione con tetto al 70%',
    n_ricavo=int(len(Mq)), ricavo_mensile_mediano=round(float(ricavo.median()), 0), affitto60_mediano=round(float(affitto60.median()), 0),
    quota_ricavo_sopra_affitto=round(float((ricavo > affitto60).mean()), 3))
pd.DataFrame(hist).to_csv(OUT/'occupazione_stimata_istogramma.csv', index=False)
assert abs(R['occupazione']['quota_ricavo_sopra_affitto']-0.476) < 0.001 and R['occupazione']['mediana'] == 30 and R['occupazione']['n_ricavo'] == 14395

# ---------- prezzi ----------
pz = rd('prezzi_distribuzione.csv')
R['prezzi'] = [dict(snapshot=r.snapshot, gruppo=r.gruppo, n=int(r.n), p25=num(r.p25), mediana=num(r.mediana), p75=num(r.p75), p5=num(r.p5), p95=num(r.p95)) for r in pz.itertuples()]
pz.to_csv(OUT/'prezzi_quotazioni.csv', index=False)
R['prezzi_senza_prezzo'] = dict(n=int(L.price_eur_quote.isna().sum()), quota=round(float(L.price_eur_quote.isna().mean()), 3))

# ---------- CIN ----------
lic = rd('licenze_per_snapshot.csv'); l9 = lic[lic.snapshot == SN].iloc[0]
raw = pd.read_csv(base/'raw'/'insideairbnb'/SN/'listings.csv.gz', usecols=['id', 'license'], low_memory=False)
v = raw[raw.license.astype(str).str.fullmatch(r'IT\d{6}[A-Z]\d[A-Z0-9]{8}')].copy()
v['istat'] = v.license.str[2:8]
dup = v.license.value_counts()
R['cin'] = dict(
    totale=int(l9.totale), valido=int(l9.CIN_formato_valido), quota_valido=round(float(l9.CIN_formato_valido/l9.totale), 3),
    richiesto_non_ricevuto=int(l9.CIN_richiesto_non_ricevuto), esente=int(l9.esente), altro_testo=int(l9.altro_testo), assente=int(l9.assente),
    quota_assente=round(float(l9.assente/l9.totale), 3), valido_milano=int((v.istat == '015146').sum()), valido_altri_comuni=int((v.istat != '015146').sum()),
    codici_usati_piu_volte=int((dup > 1).sum()), annunci_con_cin_condiviso=int(dup[dup > 1].sum()), quota_condiviso=round(float(dup[dup > 1].sum()/len(v)), 3),
    massimo_annunci_stesso_cin=int(dup.max()))
assert R['cin']['valido'] == len(v)
lic.to_csv(OUT/'cin_per_snapshot.csv', index=False)

json.dump(R, open(OUT/'riepilogo.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)

# ---------- controllo licenza: niente di per singolo annuncio ----------
vietati = re.compile(r'host_id|\blat\b|\blon\b|latitude|longitude|listing_id|\bid_annuncio\b|annunci_snapshot|recensioni_per_annuncio')
for fpath in OUT.glob('*'):
    if fpath.suffix in ('.csv', '.json') and fpath.name != 'nil.geojson':
        head = fpath.read_text(encoding='utf8')[:4000] if fpath.suffix == '.csv' else json.dumps(list(R.keys()))
        assert not vietati.search(head), fpath
for fpath in OUT.glob('*.csv'):
    d = pd.read_csv(fpath)
    assert len(d) <= 100, (fpath, len(d))   # nessuna tabella ha una riga per annuncio
print('scritti:', *sorted(p.name for p in OUT.glob('*')), sep='\n  ')
print('controllo licenza ok: tutte le tabelle hanno al massimo 100 righe e nessuna colonna per singolo annuncio')
print(json.dumps(R['sorpresa'], ensure_ascii=False)); print(json.dumps(R['host_sintesi'], ensure_ascii=False)); print(json.dumps(R['occupazione'], ensure_ascii=False)); print(json.dumps(R['cin'], ensure_ascii=False)); print(json.dumps(R['crescita_note'], ensure_ascii=False))
