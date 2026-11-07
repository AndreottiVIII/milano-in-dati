"""Prepara i dati della pagina Matrimoni (versione 2) leggendo le tabelle già in docs/matrimoni/data.
Scrive docs/matrimoni/data/matrimoni_v2.json e serie_per_anno_v2.csv (nomi nuovi: non tocca i file della pagina attuale).
Uso: python -I -X utf8 pagina_v2.py <percorso assoluto di milano-in-dati>"""
import csv, json, os, sys
R = sys.argv[1]
D = os.path.join(R, 'docs', 'matrimoni', 'data')
def rd(n):
    return list(csv.DictReader(open(os.path.join(D, n), encoding='utf-8'), delimiter=';'))
def num(x):
    return float(x) if x not in ('', None) else None

tassi = rd('tassi_per_mille_milano.csv')
rito = [dict(a=int(r['anno']), civ=int(r['civile']), rel=int(r['religioso']), pm=num(r['per1000_ab_ds1494'])) for r in tassi]
ita = [r for r in rd('istat_italia_rito_1930_2024.csv') if int(r['anno']) >= 1948]
italia = [dict(a=int(r['anno']), civ=int(float(r['civili'])), rel=int(float(r['religiosi']))) for r in ita]

def prima_soglia(serie, s):
    """primo anno da cui la quota di civili resta >= s per tutti gli anni dopo"""
    q = [(x['a'], 100 * x['civ'] / (x['civ'] + x['rel'])) for x in serie]
    for i in range(len(q)):
        if all(v >= s for _, v in q[i:]):
            return q[i][0]
    return None
soglie = [dict(s=s, mi=prima_soglia(rito, s), it=prima_soglia(italia, s)) for s in (25, 50, 75)]

# età
em = rd('istat_eta_media_al_matrimonio_2004_2024.csv')
def eta(sesso):
    return {int(r['anno']): num(r['eta_media_totale']) for r in em if r['territorio'] == 'provincia_milano' and r['sesso'] == sesso}
prim = rd('istat_primo_matrimonio_lombardia_italia_1990_2024.csv')
def primo(ind):
    return {int(r['anno']): num(r['valore']) for r in prim if r['indicatore'] == ind and r['territorio'] == 'Lombardia'}
ps, pf = primo('eta_media_sposi_primo_matrimonio'), primo('eta_media_spose_primo_matrimonio')
es, ef = eta('sposi'), eta('spose')
coppie = [r for r in rd('eta_sposi_milano_2021_2024.csv') if r['perimetro'] == 'celebrati_a_milano' and r['anno'] == '2024'][0]
eta_out = dict(
    prov=dict(sposi=[es[2004], es[2024]], spose=[ef[2004], ef[2024]]),
    primo=dict(sposi=[ps[1990], ps[2024]], spose=[pf[1990], pf[2024]]),
    coppia_2024=dict(sposa_piu_grande=num(coppie['sposa_piu_grande_pct']), stessa_classe=num(coppie['stessa_classe_pct']),
                     n=int(coppie['n_con_eta_nota'])))

un = [dict(a=int(r['anno']), m=int(r['uomini']), f=int(r['donne'])) for r in rd('unioni_civili_riepilogo.csv')]
sd = [dict(a=int(r['anno']), sep=int(float(r['separazioni_milano_piu_monza'])), div=int(float(r['divorzi_milano_piu_monza']))) for r in rd('separazioni_divorzi_riepilogo.csv')]

# numeri per la nota sui limiti
ref = [r for r in rd('rito_milano_1948_2024.csv') if r['anno'] == '2024' and r['rito'] == 'civile'][0]
cf = [r for r in rd('confronto_comune_istat_2004_2024.csv') if r['anno'] == '2010'][0]
rv = [r for r in rd('residenti_vs_celebrati_2011_2024.csv') if r['anno'] == '2011'][0]
t24 = [r for r in tassi if r['anno'] == '2024'][0]
note = dict(refuso=dict(fonte=int(ref['n_fonte']), usato=int(ref['n_usato'])),
            dieci=dict(comune=int(float(cf['comune_religiosi'])) + int(float(cf['comune_civili'])), istat=int(float(cf['istat_religiosi'])) + int(float(cf['istat_civili']))),
            res2011=dict(res_rel=int(float(rv['residenti_religiosi'])), cel_rel=int(float(rv['celebrati_religiosi']))),
            pm24=dict(comune=num(t24['per1000_ab_ds1494']), istat=num(t24['per1000_ab_istat_pop'])))
out = dict(note=note, rito=rito, italia=italia, soglie=soglie, eta=eta_out, unioni=un, sepdiv=sd)
json.dump(out, open(os.path.join(D, 'matrimoni_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
unm = {u['a']: u['m'] + u['f'] for u in un}
with open(os.path.join(D, 'serie_per_anno_v2.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['anno', 'matrimoni_civili_milano', 'matrimoni_religiosi_milano', 'matrimoni_totale_milano', 'matrimoni_per_1000_abitanti', 'quota_civili_milano_pct', 'quota_civili_italia_pct', 'unioni_civili_milano'])
    im = {x['a']: x for x in italia}
    for r in rito:
        t = r['civ'] + r['rel']; i = im[r['a']]
        w.writerow([r['a'], r['civ'], r['rel'], t, r['pm'], round(100 * r['civ'] / t, 1), round(100 * i['civ'] / (i['civ'] + i['rel']), 1), unm.get(r['a'], '')])
print(soglie, eta_out)
