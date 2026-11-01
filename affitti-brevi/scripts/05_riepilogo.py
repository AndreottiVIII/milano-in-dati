r"""Fase 1 - riepilogo: annunci, host, NIL, prezzi, crescita, confronto con gli affitti OMI.
Uso: python -I -X utf8 05_riepilogo.py <affitti-brevi (assoluta)> <milano-in-dati (assoluta)>
Legge pulito\ (e censimenti\pulito\indicatori_NIL.csv, docs\prezzi-case\data\zone_ultimo_semestre.csv).
Scrive tabelle in pulito\ e out\riepilogo.txt (tutti i numeri citati nel NOTE.md).
Snapshot principale: 2026-09-19 (ultimo, completo). Il 2026-03-27 e' INCOMPLETO (vedi NOTE.md).
"""
import sys
from pathlib import Path
import pandas as pd, numpy as np

base = Path(sys.argv[1]); prog = Path(sys.argv[2]); P = base/'pulito'; (base/'out').mkdir(exist_ok=True)
SN = '2026-09-19'
log = []
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); log.append(s)

a = pd.read_csv(P/'annunci_snapshot.csv', low_memory=False)
L = a[a.snapshot == SN].copy()

# ---------- 1. conteggi per snapshot e tipo ----------
t = a.groupby(['snapshot', 'room_type']).size().unstack(fill_value=0)
t['totale'] = t.sum(axis=1); t['host_distinti'] = a.groupby('snapshot')['host_id'].nunique()
t['con_recensione_ultimi_12_mesi'] = a[a.number_of_reviews_ltm > 0].groupby('snapshot').size()
t['CIN_formato_valido'] = a[a.licenza_tipo == 'CIN_formato_valido'].groupby('snapshot').size()
t.reset_index().to_csv(P/'riepilogo_snapshot.csv', index=False)
say('== 1. Conteggi per snapshot\n', t.to_string())
e = (L.room_type == 'Entire home/apt').sum(); r = (L.room_type == 'Private room').sum()
say(f'[{SN}] annunci {len(L)}; casa intera {e} ({e/len(L):.1%}); stanza privata {r} ({r/len(L):.1%}); condivisa {(L.room_type=="Shared room").sum()}; hotel {(L.room_type=="Hotel room").sum()}')
say(f'[{SN}] con almeno una recensione negli ultimi 12 mesi: {(L.number_of_reviews_ltm>0).sum()} ({(L.number_of_reviews_ltm>0).mean():.1%}); mai recensiti: {(L.number_of_reviews==0).sum()}')

# ---------- 2. host ----------
hc = L.groupby('host_id').size().rename('n')
bins = [0, 1, 2, 4, 9, 19, 1e9]; lab = ['1', '2', '3-4', '5-9', '10-19', '20 o piu']
L['host_n'] = L['host_id'].map(hc)
L['fascia_host'] = pd.cut(L['host_n'], bins=bins, labels=lab)
hh = pd.DataFrame({'host': hc.groupby(pd.cut(hc, bins=bins, labels=lab), observed=False).size(),
                   'annunci': L.groupby('fascia_host', observed=False).size()})
hh['quota_host'] = hh.host/hh.host.sum(); hh['quota_annunci'] = hh.annunci/hh.annunci.sum()
hh.index.name = 'annunci_per_host'; hh.reset_index().to_csv(P/'host_concentrazione.csv', index=False)
say('\n== 2. Host (host_id nel file listings)\n', hh.round(4).to_string())
top = hc.sort_values(ascending=False)
say(f'host totali {len(hc)}; con 2+ annunci: {(hc>=2).sum()} ({(hc>=2).mean():.1%}); annunci in mano a host con 2+: {(L.host_n>=2).mean():.1%}; con 5+: {(L.host_n>=5).mean():.1%}; con 10+: {(L.host_n>=10).mean():.1%}; con 20+: {(L.host_n>=20).mean():.1%}')
say(f'i 10 host piu grandi hanno annunci: {top.head(10).tolist()}  = {top.head(10).sum()} annunci ({top.head(10).sum()/len(L):.1%})')
E_ = L[L.room_type == 'Entire home/apt']; he = E_.groupby('host_id').size()
say(f'solo case intere: host {len(he)}, con 2+: {(he>=2).mean():.1%}; quota di case intere in mano a host con 2+: {E_.host_id.map(he).ge(2).mean():.1%}, con 5+: {E_.host_id.map(he).ge(5).mean():.1%}')

# ---------- 3. NIL ----------
ind = pd.read_csv(prog/'censimenti/pulito/indicatori_NIL.csv'); ind = ind[ind.anno == 2023][['nil', 'nil_nome', 'pop', 'abit_tot', 'abit_occ', 'abit_non_occ_da_residenti']]
var = pd.read_csv(prog/'censimenti/pulito/variazioni_NIL_1991_2023.csv')[['nil', 'robusto']]
ind = ind.merge(var, on='nil', how='left')
L['is_ent'] = L.room_type == 'Entire home/apt'; L['is_priv'] = L.room_type == 'Private room'
L['rec12'] = L.number_of_reviews_ltm > 0; L['cin_ok'] = L.licenza_tipo == 'CIN_formato_valido'
L['ent_rec12'] = L.is_ent & L.rec12
n = L.groupby('nil_id').agg(annunci=('id', 'size'), case_intere=('is_ent', 'sum'), stanze_private=('is_priv', 'sum'),
                            con_recensione_12m=('rec12', 'sum'), case_intere_con_recensione_12m=('ent_rec12', 'sum'),
                            CIN_valido=('cin_ok', 'sum'), host_distinti=('host_id', 'nunique'))
q = L[L.is_ent & (L.price_quote_monthly == False) & (L.price_quote_stay_nights <= 7)]
n['prezzo_mediano_case_intere_quotazione'] = q.groupby('nil_id')['price_eur_quote'].median()
n['n_prezzi'] = q.groupby('nil_id').size()
n['annunci_dic2025'] = a[a.snapshot == '2025-12-26'].groupby('nil_id').size()
n = n.reset_index().rename(columns={'nil_id': 'nil'})
n = ind.merge(n, on='nil', how='left').rename(columns={'pop': 'residenti_2023', 'abit_tot': 'abitazioni_2023', 'abit_occ': 'abitazioni_occupate_da_residenti_2023', 'abit_non_occ_da_residenti': 'abitazioni_non_occupate_da_residenti_2023'})
for c in ['annunci', 'case_intere', 'stanze_private', 'con_recensione_12m', 'case_intere_con_recensione_12m', 'CIN_valido', 'host_distinti', 'annunci_dic2025']: n[c] = n[c].fillna(0).astype(int)
n['annunci_per_100_abitazioni'] = 100*n.annunci/n.abitazioni_2023
n['case_intere_per_100_abitazioni'] = 100*n.case_intere/n.abitazioni_2023
n['case_intere_recensite_12m_per_100_abitazioni'] = 100*n.case_intere_con_recensione_12m/n.abitazioni_2023
n['annunci_per_1000_residenti'] = 1000*n.annunci/n.residenti_2023
n['quota_annunci_con_CIN'] = n.CIN_valido/n.annunci.replace(0, np.nan)
n['piccolo_denominatore'] = (n.abitazioni_2023 < 2000) | (n.residenti_2023 < 2000)
n.to_csv(P/'nil_riepilogo.csv', index=False)
say('\n== 3. NIL (snapshot', SN, '; abitazioni = censimento permanente 2023, campo abit_tot di censimenti\\pulito\\indicatori_NIL.csv)')
say(f'NIL con annunci: {(n.annunci>0).sum()} su {len(n)}; annunci assegnati {n.annunci.sum()} su {len(L)}')
tot_ab = n.abitazioni_2023.sum()
say(f'abitazioni 2023 (somma 88 NIL) {tot_ab:.0f}; annunci per 100 abitazioni, intera citta: {100*n.annunci.sum()/tot_ab:.2f}; case intere: {100*n.case_intere.sum()/tot_ab:.2f}; case intere con recensione negli ultimi 12 mesi: {n.case_intere_con_recensione_12m.sum()} => {100*n.case_intere_con_recensione_12m.sum()/tot_ab:.2f} per 100')
tot_occ = n.abitazioni_occupate_da_residenti_2023.sum()
say(f'abitazioni occupate da residenti 2023 {tot_occ:.0f}; case intere per 100 abitazioni occupate da residenti: {100*n.case_intere.sum()/tot_occ:.2f}')
cols = ['nil', 'nil_nome', 'annunci', 'case_intere', 'abitazioni_2023', 'annunci_per_100_abitazioni', 'case_intere_per_100_abitazioni', 'quota_annunci_con_CIN', 'prezzo_mediano_case_intere_quotazione', 'piccolo_denominatore']
say('Prime 12 per annunci/100 abitazioni:\n', n.sort_values('annunci_per_100_abitazioni', ascending=False)[cols].head(12).round(2).to_string(index=False))
say('Ultime 5 (con annunci):\n', n[n.annunci > 0].sort_values('annunci_per_100_abitazioni')[cols].head(5).round(2).to_string(index=False))
nr = n[~n.piccolo_denominatore]
say(f'NIL con almeno 2.000 abitazioni e 2.000 residenti: {len(nr)}; mediana annunci/100 abitazioni {nr.annunci_per_100_abitazioni.median():.2f}; massimo {nr.annunci_per_100_abitazioni.max():.2f} ({nr.loc[nr.annunci_per_100_abitazioni.idxmax(),"nil_nome"]})')
say('NIL (non piccoli) con almeno 5 annunci per 100 abitazioni:', int((nr.annunci_per_100_abitazioni >= 5).sum()), '; con almeno 10:', int((nr.annunci_per_100_abitazioni >= 10).sum()))
say('Quota di tutti gli annunci nei 10 NIL piu densi (non piccoli): %.1f%%' % (100*nr.sort_values('annunci_per_100_abitazioni', ascending=False).annunci.head(10).sum()/len(L)))

# ---------- 4. prezzi ----------
def pct(s): return s.quantile([.05, .25, .5, .75, .95]).round(1).tolist()
rows = []
for snap in ['2026-06-25', SN]:
    X = a[(a.snapshot == snap) & a.price_eur_quote.notna()]
    for lab_, f in [('tutti gli annunci con prezzo', X),
                    ('case intere, notti 1-7, non mensile', X[(X.room_type == 'Entire home/apt') & (X.price_quote_monthly == False) & (X.price_quote_stay_nights <= 7)]),
                    ('stanze private, notti 1-7, non mensile', X[(X.room_type == 'Private room') & (X.price_quote_monthly == False) & (X.price_quote_stay_nights <= 7)]),
                    ('case intere, quotazione mensile (>=28 notti)', X[(X.room_type == 'Entire home/apt') & (X.price_quote_stay_nights >= 28)])]:
        p5, p25, p50, p75, p95 = pct(f.price_eur_quote)
        rows.append(dict(snapshot=snap, gruppo=lab_, n=len(f), p5=p5, p25=p25, mediana=p50, p75=p75, p95=p95, sopra_1000=int((f.price_eur_quote > 1000).sum()), massimo=f.price_eur_quote.max()))
pr = pd.DataFrame(rows); pr.to_csv(P/'prezzi_distribuzione.csv', index=False)
say('\n== 4. Prezzo a notte (EUR; quotazione per date precise, NON prezzo di listino medio)\n', pr.to_string(index=False))
say(f'[{SN}] annunci senza prezzo: {L.price_eur_quote.isna().sum()} su {len(L)} ({L.price_eur_quote.isna().mean():.1%})')

# ---------- 5. licenze / CIN ----------
lic = a.groupby(['snapshot', 'licenza_tipo']).size().unstack(fill_value=0); lic['totale'] = lic.sum(axis=1)
lic.reset_index().to_csv(P/'licenze_per_snapshot.csv', index=False)
say('\n== 5. Campo license (codice CIN) per snapshot\n', lic.to_string())
raw = pd.read_csv(base/f'raw/insideairbnb/{SN}/listings.csv.gz', usecols=['id', 'license'], low_memory=False)
v = raw[raw.license.astype(str).str.fullmatch(r'IT\d{6}[A-Z]\d[A-Z0-9]{8}')].copy()
v['istat'] = v.license.str[2:8]
say(f'CIN formato valido {len(v)}; con codice ISTAT del comune 015146 (Milano): {(v.istat=="015146").sum()} ({(v.istat=="015146").mean():.1%}); di altri comuni: {(v.istat!="015146").sum()} ({v.istat[v.istat!="015146"].nunique()} codici diversi)')
dup = v.license.value_counts(); say(f'CIN usati da piu di un annuncio: {(dup>1).sum()} codici, per {dup[dup>1].sum()} annunci ({dup[dup>1].sum()/len(v):.1%} dei CIN validi); massimo {dup.max()} annunci con lo stesso CIN')
say('lettera dopo il codice ISTAT (non interpretata):', v.license.str[8].value_counts().to_dict())

# ---------- 6. occupazione stimata (modello Inside Airbnb) ----------
M = L[L.is_ent]
say('\n== 6. Occupazione stimata dal modello Inside Airbnb (50% recensioni->prenotazioni, 3 notti, tetto 70%)')
say(f'case intere: notti occupate stimate in 12 mesi: mediana {M.est_occupancy_l365d.median():.0f}, media {M.est_occupancy_l365d.mean():.1f}; con 0 notti: {(M.est_occupancy_l365d==0).mean():.1%}; totale notti-annuncio stimate (tutti i tipi) = {L.est_occupancy_l365d.sum():.0f}')
say(f'confronto: ISTAT/PoliS presenze (notti-persona) extra-alberghiere Milano 2025 = 8.332.433 (vyxt-7jdx). Notti-annuncio stimate x 2 ospiti (ipotesi) = {2*L.est_occupancy_l365d.sum():.0f}')

# ---------- 7. confronto con gli affitti OMI ----------
z = pd.read_csv(prog/'docs/prezzi-case/data/zone_ultimo_semestre.csv')[['zona', 'nome', 'fascia', 'loc_min', 'loc_max', 'loc_centro']]
base_q = L[L.is_ent & (L.price_quote_monthly == False) & (L.price_quote_stay_nights <= 7) & L.price_eur_quote.notna() & (L.price_eur_quote <= 1000)]
base_q = base_q.merge(z, left_on='zona_omi', right_on='zona', how='left')
say('\n== 7. Notti al mese per eguagliare un affitto lungo (OMI abitazioni civili, locazione, ultimo semestre in zone_ultimo_semestre.csv)')
say(f'case intere con prezzo 1-7 notti, non mensile, <=1000 EUR: {len(base_q)}; con zona OMI e valore: {base_q.loc_centro.notna().sum()}')
res = []
for mq in (40, 60, 80):
    rent = base_q.loc_centro*mq
    notti = rent/base_q.price_eur_quote
    res.append(dict(superficie_mq=mq, affitto_mediano=rent.median(), notti_al_mese_mediana=notti.median(), notti_p25=notti.quantile(.25), notti_p75=notti.quantile(.75), quota_con_meno_di_10_notti=(notti < 10).mean(), quota_con_oltre_20_notti=(notti > 20).mean()))
rs = pd.DataFrame(res); rs.to_csv(P/'confronto_affitto_notti.csv', index=False)
say(rs.round(3).to_string(index=False))
zz = base_q.groupby('zona').agg(nome=('nome', 'first'), fascia=('fascia', 'first'), case_intere=('id', 'size'), prezzo_mediano=('price_eur_quote', 'median'), loc_min=('loc_min', 'first'), loc_max=('loc_max', 'first'), loc_centro=('loc_centro', 'first')).reset_index()
zz['affitto_60mq_mensile'] = zz.loc_centro*60; zz['notti_al_mese_per_affitto_60mq'] = zz.affitto_60mq_mensile/zz.prezzo_mediano
zz['notti_con_affitto_min'] = zz.loc_min*60/zz.prezzo_mediano; zz['notti_con_affitto_max'] = zz.loc_max*60/zz.prezzo_mediano
zz.to_csv(P/'confronto_affitto_notti_zone.csv', index=False)
say('Per zona OMI (60 mq): mediana tra zone delle notti/mese =', round(zz.notti_al_mese_per_affitto_60mq.median(), 1), '; min', round(zz.notti_al_mese_per_affitto_60mq.min(), 1), zz.loc[zz.notti_al_mese_per_affitto_60mq.idxmin(), 'zona'], '; max', round(zz.notti_al_mese_per_affitto_60mq.max(), 1), zz.loc[zz.notti_al_mese_per_affitto_60mq.idxmax(), 'zona'])
say(zz.sort_values('notti_al_mese_per_affitto_60mq')[['zona', 'fascia', 'case_intere', 'prezzo_mediano', 'loc_centro', 'affitto_60mq_mensile', 'notti_al_mese_per_affitto_60mq']].round(1).to_string(index=False))
Mq = L[L.ent_rec12].merge(z, left_on='zona_omi', right_on='zona', how='left')
Mq = Mq[Mq.loc_centro.notna() & Mq.est_revenue_l365d.notna() & (Mq.price_eur_quote <= 1000)]
rev = Mq.est_revenue_l365d/12; rent60 = Mq.loc_centro*60
say(f'Case intere con recensioni negli ultimi 12 mesi, prezzo <=1000, zona OMI ({len(Mq)}): ricavo mensile stimato (modello Inside Airbnb): mediana {rev.median():.0f} EUR; affitto OMI 60 mq mediano {rent60.median():.0f} EUR; quota con ricavo stimato > affitto 60 mq: {(rev>rent60).mean():.1%}; ricavo lordo (prima di commissioni, pulizie, tasse)')
(base/'out'/'riepilogo.txt').write_text('\n'.join(log), encoding='utf-8')
