"""Scrive i file dati della pagina "Il benessere della Citta' metropolitana di Milano" (docs/benessere/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <benessere_dir> <docs_dir>

Legge (fase 1): benessere/pulito/*.csv (milano_posizione_ultimo_anno, cm14_ultimo_anno, cm14_graduatoria_*, milano_cambiamenti,
milano_serie, indicatori, bes_lungo, controlli_*). Scrive in <docs_dir>/benessere/data/: riepilogo.json e i CSV scaricabili.
Solo valori aggregati ISTAT (CC BY 4.0): territori di livello provinciale/metropolitano, nessun dato personale.
Polarita': solo quella scritta da ISTAT (tabella o testo, con pagina) o, se indicata, "derivata"; gli indicatori senza polarita'
non entrano in nessuna graduatoria (vedi alias_polarita.csv)."""
import sys, os, json, re, shutil
import numpy as np
import pandas as pd

B, DOCS = sys.argv[1], sys.argv[2]
P = os.path.join(B, 'pulito')
OUT = os.path.join(DOCS, 'benessere', 'data')
os.makedirs(OUT, exist_ok=True)

pos = pd.read_csv(os.path.join(P, 'milano_posizione_ultimo_anno.csv'))
cm = pd.read_csv(os.path.join(P, 'cm14_ultimo_anno.csv'))
grad = pd.read_csv(os.path.join(P, 'cm14_graduatoria_sintetica.csv'))
gdom = pd.read_csv(os.path.join(P, 'cm14_graduatoria_per_dominio.csv'))
cam = pd.read_csv(os.path.join(P, 'milano_cambiamenti.csv'))
ser = pd.read_csv(os.path.join(P, 'milano_serie.csv'))
ind = pd.read_csv(os.path.join(P, 'indicatori.csv'), dtype=str).fillna('')
lungo = pd.read_csv(os.path.join(P, 'bes_lungo.csv'), low_memory=False)
ctrl = json.load(open(os.path.join(P, 'controlli_confronto.json'), encoding='utf-8'))

ISTAT = ['istat', 'istat_testo']
DOM_ORDINE = ['Salute', 'Istruzione e formazione', 'Lavoro e conciliazione dei tempi di vita', 'Benessere economico',
              'Relazioni sociali', 'Politica e istituzioni', 'Sicurezza', 'Paesaggio e patrimonio culturale', 'Ambiente',
              'Innovazione, ricerca e creatività', 'Qualità dei servizi']


def num(x, d=None):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), d) if d is not None else float(x)


# decimali da mostrare per indicatore (dal valore grezzo ISTAT di Milano e Italia nell'anno di riferimento)
dec = {}
for _, r in pos.iterrows():
    if pd.isna(r.anno_ultimo):
        continue
    g = lungo[(lungo.codice == r.codice) & (lungo.sesso == 'Totale') & (lungo.anno == int(r.anno_ultimo)) &
              (lungo.territorio.isin(['Milano', 'Italia']))]['valore_grezzo'].astype(str)
    d = 0
    for s in g:
        if ',' in s:
            d = max(d, len(s.split(',')[1].strip()))
    if max(abs(x) for x in [r.valore_milano, r.valore_italia if pd.notna(r.valore_italia) else 0]) >= 1000:
        d = 0
    dec[r.codice] = d

# ---------------- indicatori per dominio ----------------
cm_ok = cm.copy()
dom_out = []
for dn in DOM_ORDINE:
    sub = pos[pos.dominio == dn]
    items, senza = [], []
    for _, r in sub.iterrows():
        meta = ind[ind.codice == r.codice].iloc[0]
        base = dict(cod=r.codice, nome=r.indicatore, unita=r.unita, anno=num(r.anno_ultimo), liv=r.livello_polarita,
                    pol=(r.polarita if isinstance(r.polarita, str) else ''), dec=dec.get(r.codice, 0),
                    vm=num(r.valore_milano, 4), vi=num(r.valore_italia, 4), n107=num(r.n_province), n14=num(r.n_cm))
        if pd.isna(r.anno_ultimo):
            base['nota'] = 'non confrontabile: troppo pochi territori con il dato'
            senza.append(base); continue
        if pd.notna(r.rango_107) and r.livello_polarita in ISTAT + ['derivata']:
            c = cm_ok[cm_ok.codice == r.codice].sort_values('citta_metropolitana')
            base.update(r107=int(r.rango_107), r14=int(r.rango_14), perc=num(r.percentile_107, 1),
                        gap=num(r.gap_standardizzato, 2),
                        cm=[[x.citta_metropolitana, num(x.valore, 4), num(x.percentile_107, 1), int(x.rango_14)] for x in c.itertuples()])
            items.append(base)
        else:
            base.update(rv107=int(r.rango_valore_107), rv14=int(r.rango_valore_14),
                        primo14=r.prima_tra_14, ultimo14=r.ultima_tra_14,
                        min=num(r.valore_min_province, 4), max=num(r.valore_max_province, 4))
            motivo = meta['motivo_polarita'] if 'motivo_polarita' in meta else ''
            base['nota'] = ("L'Istat scrive + ma è un tasso di sofferenza dei prestiti: probabile refuso, escluso dalle graduatorie"
                            if r.livello_polarita == 'dubbia' else "L'Istat non dice se un valore più alto è meglio o peggio")
            senza.append(base)
    items.sort(key=lambda x: x['perc'])
    g = gdom[(gdom.dominio == dn) & (gdom.citta_metropolitana == 'Milano')]
    perc_dom = pos[(pos.dominio == dn) & pos.livello_polarita.isin(ISTAT) & pos.percentile_107.notna()].percentile_107.mean()
    dom_out.append(dict(nome=dn, n_tot=int(len(sub)), perc_medio_istat=num(perc_dom, 1),
                        pos14=(int(g.posizione_tra_14.iloc[0]) if len(g) else None),
                        n_istat=int(((sub.livello_polarita.isin(ISTAT)) & sub.rango_107.notna()).sum()),
                        indicatori=items, senza=senza))

# ---------------- conteggi e posizioni ----------------
d = pos[pos.livello_polarita.isin(ISTAT) & pos.rango_107.notna()]
conteggi = dict(
    n_ind=int(len(pos)), n_posiz=int(len(d)),
    primo107=int((d.rango_107 == 1).sum()), top3_107=int((d.rango_107 <= 3).sum()), top10_107=int((d.rango_107 <= 10).sum()),
    primo14=int((d.rango_14 == 1).sum()), top3_14=int((d.rango_14 <= 3).sum()),
    ultimi3_14=int((d.rango_14 >= 12).sum()), ultimo14=int((d.rango_14 == 14).sum()),
    sopra_italia=int((d.gap_standardizzato > 0).sum()), confrontabili=int(d.gap_standardizzato.notna().sum()),
    perc_mediano=num(d.percentile_107.median(), 1))
livelli = ind.livello_polarita.value_counts().to_dict() if 'livello_polarita' in ind else {}
pol_count = dict(istat=int(livelli.get('istat', 0)), istat_testo=int(livelli.get('istat_testo', 0)),
                 derivata=int(livelli.get('derivata', 0)), assente=int(livelli.get('assente', 0)),
                 dubbia=int(livelli.get('dubbia', 0)))


def riga(r):
    return dict(cod=r.codice, nome=r.indicatore, unita=r.unita, anno=num(r.anno_ultimo), dec=dec.get(r.codice, 0), liv=r.livello_polarita,
                vm=num(r.valore_milano, 4), vi=num(r.valore_italia, 4), r107=int(r.rango_107), n107=int(r.n_province),
                r14=int(r.rango_14), n14=int(r.n_cm), gap=num(r.gap_standardizzato, 2), perc=num(r.percentile_107, 1),
                primo14=r.prima_tra_14, ultimo14=r.ultima_tra_14)


primi = [riga(r) for _, r in d[d.rango_107 == 1].sort_values('gap_standardizzato', ascending=False).iterrows()]
ult_nomi = ['10AMB018P', '10AMB016', '10AMB014', '02IST001', '10AMB002P', '10AMB001P']
ultimi = [riga(d[d.codice == c].iloc[0]) for c in ult_nomi if (d.codice == c).any()]
borsegg = riga(pos[pos.codice == '07SIC005P'].iloc[0])
rapina = riga(pos[pos.codice == '07SIC006P'].iloc[0])

# scuola 4-5 anni: serie Milano, Lombardia, Italia
s = ser[ser.codice == '02IST001']
anni = sorted(s.anno.unique().tolist())
scuola = dict(anni=anni)
for t, k in [('Milano', 'milano'), ('Lombardia', 'lombardia'), ('Italia', 'italia')]:
    x = s[s.territorio == t].set_index('anno').valore
    scuola[k] = [num(x.get(a), 1) for a in anni]
scuola['riga'] = riga(pos[pos.codice == '02IST001'].iloc[0])
istr = {c: riga(pos[pos.codice == c].iloc[0]) for c in ['02IST003P-N22', '02IST002-N22', '02IST007-N22']}

# ---------------- Milano vs Italia ----------------
g = d[d.gap_standardizzato.notna()].sort_values('gap_standardizzato', ascending=False)
vs_top = [riga(r) for _, r in g.head(8).iterrows()]
vs_bot = [riga(r) for _, r in g.tail(8).iloc[::-1].iterrows()]
vs_tutti = [riga(r) for _, r in g.iterrows()]

# ---------------- cambiamenti dal 2019 ----------------
c19 = cam[(cam.orizzonte == 'rispetto al 2019') & cam.livello_polarita.isin(ISTAT) & cam.var_std_milano.notna()].copy()


def rc(r):
    nm = ind[ind.codice == r.codice].iloc[0]
    return dict(cod=r.codice, nome=r.indicatore, anno_base=int(r.anno_base), anno=int(r.anno_ultimo), dec=dec.get(r.codice, 0),
                unita=nm['unita'], vb=num(r.valore_base, 4), vu=num(r.valore_ultimo, 4),
                std=num(r.var_std_milano, 2), std_it=num(r.var_std_italia, 2), rel=num(r.var_std_relativa_italia, 2),
                rb=int(r.rango_107_base), ru=int(r.rango_107_ultimo), guad=int(r.rango_107_guadagno))


c19 = c19.sort_values('var_std_relativa_italia', ascending=False)
n_tot19 = int(len(c19))
c19 = c19[c19.var_std_relativa_italia.notna()]   # PM10/PM2,5: totale Italia non confrontabile, fuori dal confronto con l'Italia
cambi = dict(n=int(len(c19)), n_senza_italia=n_tot19 - int(len(c19)), migliora=int((c19.var_std_milano > 0).sum()), meglio_italia=int((c19.var_std_relativa_italia > 0).sum()),
             sale=int((c19.rango_107_guadagno > 0).sum()), scende=int((c19.rango_107_guadagno < 0).sum()),
             uguale=int((c19.rango_107_guadagno == 0).sum()),
             migliorati=[rc(r) for _, r in c19.head(8).iterrows()], peggiorati=[rc(r) for _, r in c19.tail(8).iloc[::-1].iterrows()],
             tutti=[rc(r) for _, r in c19.iterrows()])
neet_ecc = {c: rc(c19[c19.codice == c].iloc[0]) for c in ['02IST006-N22', '02IST004', '01SAL001', '02IST007-N22'] if (c19.codice == c).any()}

# ---------------- graduatoria CM ----------------
grad_out = [dict(cm=r.citta_metropolitana, perc=num(r.percentile_medio_107, 1), n=int(r.n_indicatori), pos=int(r.posizione),
                 rango_medio=num(r.rango_medio_14, 1)) for r in grad.itertuples()]

riep = dict(
    meta=dict(edizione=2025, scaricato='2026-11-01', licenza='Creative Commons Attribuzione 4.0 (CC BY 4.0)',
              link_reati=os.path.exists(os.path.join(DOCS, 'reati', 'index.html')),
              n_indicatori=int(len(ind)), n_domini=11, n_province=107, n_cm=14, anni='2004-2024',
              rev_uguali_pct=round(100 * 96236 / 103413, 1),
              confronto_appendice=ctrl['confronto_appendice_report_cm2024']['celle_confrontate'],
              confronto_appendice_ok=ctrl['confronto_appendice_report_cm2024']['entro_arrotondamento_o_0_5pct']),
    pol=pol_count, conteggi=conteggi, graduatoria=grad_out, primi=primi, ultimi=ultimi, borseggio=borsegg, rapina=rapina,
    scuola=scuola, istruzione=istr, domini=dom_out, vs_top=vs_top, vs_bot=vs_bot, vs_n=len(vs_tutti),
    cambi={k: v for k, v in cambi.items() if k != 'tutti'}, cambi_tutti=cambi['tutti'], cambi_evidenza=neet_ecc)
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------------- csv scaricabili ----------------
pos.to_csv(os.path.join(OUT, 'milano_posizione_ultimo_anno.csv'), index=False, encoding='utf-8')
cm.to_csv(os.path.join(OUT, 'cm14_ultimo_anno.csv'), index=False, encoding='utf-8')
grad.to_csv(os.path.join(OUT, 'cm14_graduatoria_sintetica.csv'), index=False, encoding='utf-8')
cam.to_csv(os.path.join(OUT, 'milano_cambiamenti.csv'), index=False, encoding='utf-8')
ser.to_csv(os.path.join(OUT, 'milano_italia_serie.csv'), index=False, encoding='utf-8')
ind[['num_indicatore', 'codice', 'dominio', 'indicatore', 'unita', 'tipo_indicatore', 'definizione', 'fonte_ente', 'fonte_dato',
     'polarita', 'livello_polarita', 'motivo_polarita', 'fonte_polarita']].to_csv(
    os.path.join(OUT, 'indicatori_e_polarita.csv'), index=False, encoding='utf-8')
cmser = lungo[(lungo.sesso == 'Totale') & (lungo.citta_metropolitana | (lungo.territorio == 'Italia'))][
    ['dominio', 'codice', 'indicatore', 'unita', 'territorio', 'anno', 'valore', 'flag_valore']]
cmser.to_csv(os.path.join(OUT, 'serie_14_citta_metropolitane_italia.csv'), index=False, encoding='utf-8')
print('ok', os.path.getsize(os.path.join(OUT, 'riepilogo.json')) // 1024, 'KB riepilogo;', len(dom_out), 'domini;', len(cmser), 'righe serie CM')
