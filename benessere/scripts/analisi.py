"""Fase 1 - Bes dei territori: riepiloghi su Milano (= Citta' metropolitana / provincia di Milano).
Uso: python -I -X utf8 analisi.py <benessere assoluto>
Legge pulito/bes_lungo.csv e pulito/indicatori.csv; scrive i riepiloghi in pulito/.
Regole:
 - solo sesso = Totale; confronto tra le 107 province (tipo_territorio = provincia) e le 14 citta' metropolitane;
 - rango 1 = migliore secondo la polarita' (+ piu' alto e' meglio, - piu' basso e' meglio);
 - la polarita' viene dalla Nota metodologica ISTAT (vedi indicatori.csv); dove ISTAT non la da', i ranghi "per valore"
   (1 = valore piu' alto) sono sempre calcolati ma l'indicatore resta fuori dalle liste migliori/peggiori;
 - 'ISTAT' = polarita' scritta da ISTAT; 'derivata' = complemento/componente di un indicatore con polarita' ISTAT;
 - anno di riferimento = ultimo anno in cui Milano ha il valore e almeno 80 province hanno il valore."""
import sys, json, pathlib
import numpy as np
import pandas as pd

base = pathlib.Path(sys.argv[1])
P = base / 'pulito'
L = pd.read_csv(P / 'bes_lungo.csv', low_memory=False)
IND = pd.read_csv(P / 'indicatori.csv', dtype=str).fillna('')
L = L[L.sesso == 'Totale'].copy()
MIN_PROV = 80
CM14 = sorted(L[L.citta_metropolitana].territorio.unique())

prov = L[L.tipo_territorio == 'provincia']
wide = {}   # (codice) -> DataFrame territorio x anno (province + italia + ripartizioni + regioni)
for cod, g in L.groupby('codice'):
    wide[cod] = g.pivot_table(index='territorio', columns='anno', values='valore', aggfunc='first')
tipo = L[['territorio', 'tipo_territorio']].drop_duplicates().set_index('territorio')['tipo_territorio']
prov_names = sorted(tipo[tipo == 'provincia'].index)
assert len(prov_names) == 107, len(prov_names)


def anno_riferimento(w):
    ultimo = max(w.columns)
    for y in sorted(w.columns, reverse=True):
        if ultimo - y > 3:
            break          # anno troppo lontano dall'ultimo disponibile: non e' una fotografia attuale (es. elezioni regionali)
        col = w.loc[w.index.isin(prov_names), y].dropna()
        if len(col) >= MIN_PROV and 'Milano' in col.index:
            return int(y)
    return None


def pos(w, y, sign):
    """rango (1 = migliore per polarita') tra 107 province e 14 CM, a pari merito 'min'; sign None -> per valore"""
    col = w.loc[w.index.isin(prov_names), y].dropna()
    s = (col * (sign if sign else 1))
    r107 = s.rank(ascending=False, method='min')
    cm = s[s.index.isin(CM14)]
    r14 = cm.rank(ascending=False, method='min')
    return col, r107, r14


righe, serie, cm_rows = [], [], []
for _, ind in IND.iterrows():
    cod = ind['codice']
    w = wide[cod]
    pol = ind['polarita']
    sign = {'+': 1, '-': -1}.get(pol)
    liv = ind['livello_polarita']
    y = anno_riferimento(w)
    r = dict(dominio=ind['dominio'], num_indicatore=ind['num_indicatore'], codice=cod, indicatore=ind['indicatore'],
             unita=ind['unita'], tipo_indicatore=ind['tipo_indicatore'], polarita=pol, livello_polarita=liv)
    # serie di Milano e confronti
    for t in ['Milano', 'Italia', 'Nord-ovest', 'Lombardia']:
        if t in w.index:
            for yy, v in w.loc[t].dropna().items():
                serie.append(dict(codice=cod, indicatore=ind['indicatore'], territorio=t, anno=int(yy), valore=v))
    if y is None:
        r.update(anno_ultimo=None, nota='non confrontabile: meno di %d province con il dato nell\'anno in cui Milano lo ha' % MIN_PROV)
        righe.append(r); continue
    col, r107, r14 = pos(w, y, sign)
    _, rv107, rv14 = pos(w, y, None)
    mi, it = w.loc['Milano', y], (w.loc['Italia', y] if 'Italia' in w.index else np.nan)
    sd = col.std(ddof=0)
    it_ok = pd.notna(it) and col.min() <= it <= col.max()
    if not it_ok:
        r['avviso'] = 'valore Italia fuori dall intervallo dei valori provinciali: i totali non sono confrontabili con le province (si veda NOTE.md)'
        it = np.nan
    r.update(anno_ultimo=y, n_province=len(col), n_cm=len(r14), valore_milano=mi, valore_italia=it,
             valore_nord_ovest=w.loc['Nord-ovest', y] if 'Nord-ovest' in w.index else np.nan,
             valore_lombardia=w.loc['Lombardia', y] if 'Lombardia' in w.index else np.nan,
             diff_vs_italia=mi - it, diff_pct_vs_italia=(mi - it) / abs(it) * 100 if it else np.nan,
             sd_province=sd, gap_standardizzato=(sign * (mi - it) / sd) if (sign and sd) else np.nan,
             rango_107=r107['Milano'] if sign else np.nan, rango_14=r14['Milano'] if sign else np.nan,
             rango_valore_107=rv107['Milano'], rango_valore_14=rv14['Milano'],
             valore_min_province=col.min(), valore_max_province=col.max(),
             prima_tra_14=(r14.idxmin() if sign else (rv14.idxmin())),
             ultima_tra_14=(r14.idxmax() if sign else (rv14.idxmax())),
             prima_tra_107=(r107.idxmin() if sign else rv107.idxmin()),
             ultima_tra_107=(r107.idxmax() if sign else rv107.idxmax()),
             fonte='bes_lungo.csv: codice %s, anno %d, ed. 2025 (Istat, Bes dei territori, CC BY 4.0)' % (cod, y))
    if sign:
        r['percentile_107'] = (len(col) - r107['Milano']) / (len(col) - 1) * 100
        r['percentile_14'] = (len(r14) - r14['Milano']) / (len(r14) - 1) * 100
    # tutte le CM nell'anno di riferimento
    for c in CM14:
        if c in col.index:
            cm_rows.append(dict(codice=cod, indicatore=ind['indicatore'], dominio=ind['dominio'], polarita=pol,
                                livello_polarita=liv, anno=y, citta_metropolitana=c, valore=col[c],
                                rango_14=(r14[c] if sign else np.nan), rango_107=(r107[c] if sign else np.nan),
                                rango_valore_14=rv14[c], percentile_107=((len(col) - r107[c]) / (len(col) - 1) * 100) if sign else np.nan))
    # cambiamenti nel tempo
    def cambia(by, etichetta):
        if by is None or by == y:
            return
        colb, r107b, r14b = pos(w, by, sign)
        sdb = colb.std(ddof=0)
        mib = w.loc['Milano', by]
        itb = w.loc['Italia', by] if 'Italia' in w.index else np.nan
        d = dict(codice=cod, indicatore=ind['indicatore'], dominio=ind['dominio'], polarita=pol, livello_polarita=liv,
                 orizzonte=etichetta, anno_base=by, anno_ultimo=y, valore_base=mib, valore_ultimo=mi,
                 var_assoluta=mi - mib, var_pct=(mi - mib) / abs(mib) * 100 if mib else np.nan,
                 var_italia_assoluta=it - itb, sd_base=sdb)
        if sign and sdb:
            d['var_std_milano'] = sign * (mi - mib) / sdb
            d['var_std_italia'] = sign * (it - itb) / sdb
            d['var_std_relativa_italia'] = d['var_std_milano'] - d['var_std_italia']
            d['rango_107_base'] = r107b['Milano']; d['rango_107_ultimo'] = r107['Milano']
            d['rango_107_guadagno'] = r107b['Milano'] - r107['Milano']      # positivo = e' salito in classifica
            d['rango_14_base'] = r14b['Milano']; d['rango_14_ultimo'] = r14['Milano']
            d['rango_14_guadagno'] = r14b['Milano'] - r14['Milano']
        cambi.append(d)
    anni_ok = [int(a) for a in sorted(w.columns)
               if w.loc[w.index.isin(prov_names), a].notna().sum() >= MIN_PROV and pd.notna(w.loc['Milano', a])]
    b19 = 2019 if (2019 in anni_ok and y >= 2021) else None
    lungo = [a for a in anni_ok if y - a >= 5]
    blungo = lungo[0] if lungo else None
    if 'cambi' not in globals():
        cambi = []
    cambia(b19, 'rispetto al 2019')
    cambia(blungo, 'serie lunga (primo anno disponibile)')
    righe.append(r)

pos_df = pd.DataFrame(righe)
cam = pd.DataFrame(cambi)
cm_df = pd.DataFrame(cm_rows)
ser = pd.DataFrame(serie)

pos_df.to_csv(P / 'milano_posizione_ultimo_anno.csv', index=False, encoding='utf-8')
cam.to_csv(P / 'milano_cambiamenti.csv', index=False, encoding='utf-8')
cm_df.to_csv(P / 'cm14_ultimo_anno.csv', index=False, encoding='utf-8')
ser.to_csv(P / 'milano_serie.csv', index=False, encoding='utf-8')

# ---------------- riepiloghi ----------------
cl = pos_df[(pos_df.livello_polarita.isin(['istat', 'istat_testo'])) & pos_df.rango_107.notna()].copy()
cl_d = pos_df[(pos_df.livello_polarita.isin(['istat', 'istat_testo', 'derivata'])) & pos_df.rango_107.notna()].copy()


def top_bottom(df, nome):
    d = df.sort_values(['percentile_107', 'gap_standardizzato'], ascending=[False, False])
    cols = ['dominio', 'codice', 'indicatore', 'anno_ultimo', 'valore_milano', 'valore_italia', 'unita', 'rango_107', 'n_province',
            'rango_14', 'n_cm', 'percentile_107', 'gap_standardizzato', 'prima_tra_14', 'livello_polarita']
    top = d.head(10)[cols].assign(gruppo='migliori_10_' + nome)
    bot = d.tail(10).iloc[::-1][cols].assign(gruppo='peggiori_10_' + nome)
    return pd.concat([top, bot])


tb = pd.concat([top_bottom(cl, 'solo_polarita_istat'), top_bottom(cl_d, 'istat_e_derivata')])
tb.to_csv(P / 'milano_migliori_peggiori.csv', index=False, encoding='utf-8')

dom = cl_d.groupby('dominio').agg(
    n_indicatori=('codice', 'size'),
    percentile_medio_107=('percentile_107', 'mean'), percentile_mediano_107=('percentile_107', 'median'),
    percentile_medio_14=('percentile_14', 'mean'), gap_std_mediano=('gap_standardizzato', 'median'),
    n_primo_terzo=('rango_107', lambda s: int((s <= 36).sum())), n_ultimo_terzo=('rango_107', lambda s: int((s >= 72).sum())),
    n_tra_primi_3_su_14=('rango_14', lambda s: int((s <= 3).sum())), n_tra_ultimi_3_su_14=('rango_14', lambda s: int((s >= 12).sum()))
).reset_index()
dom_i = cl.groupby('dominio').agg(n_indicatori_solo_istat=('codice', 'size'),
                                   percentile_medio_107_solo_istat=('percentile_107', 'mean')).reset_index()
dom = dom.merge(dom_i, on='dominio', how='left')
dom['n_indicatori_totale_dominio'] = dom['dominio'].map(IND.groupby('dominio').size())
dom.to_csv(P / 'milano_profilo_domini.csv', index=False, encoding='utf-8')

# graduatoria sintetica tra le 14 CM (percentile medio sui soli indicatori con polarita' ISTAT, anno di riferimento)
gc = cm_df[(cm_df.livello_polarita.isin(['istat', 'istat_testo'])) & cm_df.percentile_107.notna()].groupby('citta_metropolitana').agg(
    percentile_medio_107=('percentile_107', 'mean'), n_indicatori=('codice', 'size'),
    rango_medio_14=('rango_14', 'mean')).sort_values('percentile_medio_107', ascending=False)
gc['posizione'] = range(1, len(gc) + 1)
gc.reset_index().to_csv(P / 'cm14_graduatoria_sintetica.csv', index=False, encoding='utf-8')
# stessa graduatoria per dominio
gd = cm_df[(cm_df.livello_polarita.isin(['istat', 'istat_testo'])) & cm_df.percentile_107.notna()].groupby(['dominio', 'citta_metropolitana']).agg(
    percentile_medio_107=('percentile_107', 'mean'), n=('codice', 'size')).reset_index()
gd['posizione_tra_14'] = gd.groupby('dominio')['percentile_medio_107'].rank(ascending=False, method='min')
gd.to_csv(P / 'cm14_graduatoria_per_dominio.csv', index=False, encoding='utf-8')

# indicatori con rango 14 peggiore / meglio
sorpresa = cl_d[(cl_d.rango_107 >= 54)].sort_values('rango_107', ascending=False)[
    ['dominio', 'indicatore', 'anno_ultimo', 'valore_milano', 'valore_italia', 'unita', 'rango_107', 'rango_14', 'n_province', 'percentile_107', 'gap_standardizzato', 'livello_polarita', 'prima_tra_14', 'ultima_tra_14']]
sorpresa.to_csv(P / 'milano_sotto_la_meta.csv', index=False, encoding='utf-8')

nd = pos_df[pos_df.rango_107.isna()][['dominio', 'codice', 'indicatore', 'livello_polarita', 'anno_ultimo', 'valore_milano', 'valore_italia',
                                       'rango_valore_107', 'rango_valore_14', 'n_province', 'valore_min_province', 'valore_max_province',
                                       'prima_tra_14', 'ultima_tra_14']]
nd.to_csv(P / 'milano_senza_polarita.csv', index=False, encoding='utf-8')

# cambiamenti: migliorati / peggiorati di piu'
def best_worst_changes(c, orizzonte, livelli):
    d = c[(c.orizzonte == orizzonte) & c.livello_polarita.isin(livelli) & c.var_std_milano.notna()]
    return d.sort_values('var_std_relativa_italia', ascending=False)


riep = dict(
    indicatori_totali=int(len(IND)), indicatori_con_posizione=int(pos_df.rango_107.notna().sum()),
    indicatori_con_polarita_istat=int(pos_df.livello_polarita.isin(['istat', 'istat_testo']).sum()),
    indicatori_con_polarita_derivata=int((pos_df.livello_polarita == 'derivata').sum()),
    indicatori_senza_polarita=int(IND.livello_polarita.isin(['assente', 'dubbia']).sum()),
    anni_riferimento=pos_df.anno_ultimo.value_counts().sort_index().to_dict(),
    graduatoria_cm=gc.reset_index().round(2).to_dict('records'),
)
json.dump(riep, open(P / 'riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(riep, ensure_ascii=False, indent=1, default=str))
