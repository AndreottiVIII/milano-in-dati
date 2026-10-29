"""Fase 2, passo 3: percentuali di donne (sicure e con incerti; con e senza santi; per decennio di intitolazione).
Uso: python -I 12_percentuali.py strade_classificate_v2.csv out_dir"""
import sys, json
import pandas as pd

csv, outdir = sys.argv[1:3]
d = pd.read_csv(csv, dtype=str).fillna('')
d['santo_any'] = ((d.santa == '1') | (d.santo == '1')).astype(int)
d['persona'] = d.categoria.isin(['donna', 'uomo', 'misto'])


def calc(x, label):
    tot = len(x)
    pers_s = x[x.persona & (x.confidenza == 'sicuro')]
    pers_i = x[x.persona & (x.confidenza == 'incerto')]
    W = int((pers_s.categoria == 'donna').sum())
    P = len(pers_s)
    Iw = int((pers_i.categoria == 'donna').sum())
    Ip = len(pers_i)
    Wf, Pf = W + Iw, P + Ip           # "a prima vista": tutti gli incerti presi per buoni
    r = dict(scope=label, strade_totali=tot, persone_sicure=P, donne_sicure=W, uomini_sicuri=int((pers_s.categoria == 'uomo').sum()), misti_sicuri=int((pers_s.categoria == 'misto').sum()),
             persone_incerte=Ip, donne_incerte=Iw, uomini_incerti=int((pers_i.categoria == 'uomo').sum()),
             sconosciute=int((x.categoria == 'sconosciuto').sum()), non_persone=int((x.categoria == 'non_persona').sum()))
    r['quota_donne_su_persone_ferma'] = W / P
    r['quota_donne_su_persone_con_incerti'] = Wf / Pf
    r['quota_donne_su_persone_estremo_basso'] = W / (P + Ip - Iw)  # estremo basso: nessuna delle incerte e donna (e non e persona), tutti gli altri incerti sono persone
    r['quota_donne_su_persone_estremo_alto'] = (W + Iw) / (P + Iw)  # estremo alto: tutte le incerte sono donne, gli altri incerti non sono persone
    r['quota_donne_su_tutte_le_strade_ferma'] = W / tot
    r['quota_donne_su_tutte_le_strade_con_incerti'] = Wf / tot
    r['quota_donne_su_tutte_le_strade_estremo_basso'] = W / tot
    r['quota_donne_su_tutte_le_strade_estremo_alto'] = (W + Iw) / tot
    return r


res = [calc(d, 'con santi'), calc(d[d.santo_any == 0], 'senza santi')]
# decenni
dd = d[d.persona & (d.confidenza.isin(['sicuro', 'incerto']))].copy()
dd['anno'] = dd.data_intitolazione.str[:4]
dd = dd[dd.data_intitolazione.str.len() == 8]
dd = dd[~dd.data_intitolazione.isin(['17000101', '19000101'])]
dd['anno'] = dd.anno.astype(int)
dd['decennio'] = dd.anno // 10 * 10
rows = []
for dec, g in dd.groupby('decennio'):
    gs = g[g.confidenza == 'sicuro']
    rows.append(dict(decennio=dec, persone_sicure=len(gs), donne_sicure=int((gs.categoria == 'donna').sum()),
                     quota_ferma=((gs.categoria == 'donna').sum() / len(gs)) if len(gs) else None,
                     persone_con_incerti=len(g), donne_con_incerti=int((g.categoria == 'donna').sum()),
                     quota_con_incerti=((g.categoria == 'donna').sum() / len(g)) if len(g) else None))
dec = pd.DataFrame(rows)
dec.to_csv(f"{outdir}/percentuali_per_decennio.csv", index=False, encoding='utf-8-sig')
# anche per periodi larghi (le donne con data sono poche)
bins = [(0, 1949, 'fino al 1949'), (1950, 1979, '1950-1979'), (1980, 1999, '1980-1999'), (2000, 2030, '2000 e dopo')]
rows = []
for a, b, lab in bins:
    g = dd[(dd.anno >= a) & (dd.anno <= b)]
    gs = g[g.confidenza == 'sicuro']
    rows.append(dict(periodo=lab, persone_sicure=len(gs), donne_sicure=int((gs.categoria == 'donna').sum()),
                     quota_ferma=((gs.categoria == 'donna').sum() / len(gs)) if len(gs) else None,
                     persone_con_incerti=len(g), donne_con_incerti=int((g.categoria == 'donna').sum()),
                     quota_con_incerti=((g.categoria == 'donna').sum() / len(g)) if len(g) else None))
per = pd.DataFrame(rows)
per.to_csv(f"{outdir}/percentuali_per_periodo.csv", index=False, encoding='utf-8-sig')
# conteggi di controllo
extra = dict(
    totale_con_data_valida=int(len(dd)), totale_con_data_valida_e_persona_sicura=int((dd.confidenza == 'sicuro').sum()),
    donne_sicure_per_fonte=d[(d.categoria == 'donna') & (d.confidenza == 'sicuro')].fonte.value_counts().to_dict(),
    donne_incerte_per_fonte=d[(d.categoria == 'donna') & (d.confidenza == 'incerto')].fonte.value_counts().to_dict(),
    donne_sicure_sante=int(((d.categoria == 'donna') & (d.confidenza == 'sicuro') & (d.santa == '1')).sum()),
    donne_incerte_sante=int(((d.categoria == 'donna') & (d.confidenza == 'incerto') & (d.santa == '1')).sum()),
    uomini_sicuri_santi=int(((d.categoria == 'uomo') & (d.confidenza == 'sicuro') & (d.santo == '1')).sum()),
    gruppi_sorelle=int(((d.categoria == 'donna') & (d.gruppo == '1')).sum()),
    categorie=d.groupby(['categoria', 'confidenza']).size().rename('n').reset_index().to_dict('records'))
json.dump(dict(percentuali=res, extra=extra), open(f"{outdir}/percentuali.json", 'w', encoding='utf8'), ensure_ascii=False, indent=1)
for r in res:
    print(json.dumps(r, ensure_ascii=False, indent=0))
print(dec.to_string())
print(per.to_string())
print(json.dumps(extra, ensure_ascii=False)[:1500])
