"""Controlli di coerenza. python -I scripts/check.py (da bilancio-comune/)"""
import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_rows',500); pd.set_option('display.float_format','{:,.1f}'.format)
L=pd.read_pickle('raw/_L.pkl')
out=[]
# 1) stesso anno di rendiconto in due edizioni consecutive
R=L[L.fase=='consuntivo']
ed=sorted(R.edizione.unique())
print('--- 1. rendiconto stesso anno, due edizioni: totali (milioni) per tipo/titolo')
for tipo in ['uscite','entrate']:
    t=R[R.tipo==tipo].groupby(['anno','edizione','liv1']).importo.sum().unstack('edizione')/1e6
    t['diff_max']=t.max(axis=1)-t.min(axis=1)
    print(tipo);print(t.round(1).to_string())
    for (a,l),r in t.iterrows():
        vals=r.drop('diff_max').dropna()
        out.append(dict(controllo='rendiconto_stesso_anno_due_edizioni',tipo=tipo,anno=a,dettaglio=f'titolo {l}',valori='; '.join(f'{k}={v:,.2f}M' for k,v in vals.items()),differenza_max_milioni=round(r.diff_max,3)))
# riga per riga (capitolo)
print('--- 1b. differenze a livello di capitolo (|diff|>1 euro)')
for a in sorted(R.anno.unique()):
    x=R[(R.anno==a)]
    es=sorted(x.edizione.unique())
    if len(es)<2: continue
    e1,e2=es[0],es[1]
    for tipo in ['uscite','entrate']:
        k=['capitolo','liv1','missione','programma']
        p1=x[(x.edizione==e1)&(x.tipo==tipo)].groupby(k).importo.sum()
        p2=x[(x.edizione==e2)&(x.tipo==tipo)].groupby(k).importo.sum()
        j=pd.concat([p1,p2],axis=1,keys=['a','b']).fillna(0)
        d=(j.a-j.b).abs()
        # confronto senza missione/programma (riclassificazioni)
        q1=x[(x.edizione==e1)&(x.tipo==tipo)].groupby('capitolo').importo.sum()
        q2=x[(x.edizione==e2)&(x.tipo==tipo)].groupby('capitolo').importo.sum()
        jq=pd.concat([q1,q2],axis=1,keys=['a','b']).fillna(0)
        dq=(jq.a-jq.b).abs()
        s=f'{tipo} {a} {e1} vs {e2}: righe={len(j)}, righe diverse (cap+missione+programma)={int((d>1).sum())}, capitoli diversi={int((dq>1).sum())} su {len(jq)}, somma|diff| capitoli={dq.sum()/1e6:,.2f}M, totale {e1}={q1.sum()/1e6:,.1f}M {e2}={q2.sum()/1e6:,.1f}M'
        print(s)
        out.append(dict(controllo='rendiconto_stesso_anno_capitoli',tipo=tipo,anno=a,dettaglio=f'{e1} vs {e2}',valori=s,differenza_max_milioni=round(dq.sum()/1e6,3)))
# 2) pareggio previsioni
print('--- 2. pareggio previsioni (entrate - uscite, milioni)')
P=L[(L.fase=='previsione')&(L.misura!='stanziamento_cassa')&(L.misura!='assestato_cassa')]
t=P.groupby(['edizione','anno','tipo']).importo.sum().unstack('tipo')/1e6
t['diff']=t.entrate-t.uscite
print(t.round(2).to_string())
for (e,a),r in t.iterrows():
    out.append(dict(controllo='pareggio_previsione_competenza',tipo='entrate-uscite',anno=a,dettaglio=e,valori=f'entrate={r.entrate:,.2f}M uscite={r.uscite:,.2f}M',differenza_max_milioni=round(r['diff'],3)))
# 3) stessa previsione di un anno in edizioni diverse (vintage)
print('--- 3. stanziamento competenza dello stesso anno in edizioni diverse (uscite, milioni)')
v=P[P.tipo=='uscite'].groupby(['anno','edizione']).importo.sum().unstack('edizione')/1e6
print(v.round(0).to_string())
for a,r in v.iterrows():
    out.append(dict(controllo='stanziamento_stesso_anno_edizioni_diverse',tipo='uscite',anno=a,dettaglio='',valori='; '.join(f'{k}={x:,.0f}M' for k,x in r.dropna().items()),differenza_max_milioni=round(r.max()-r.min(),1)))
# 4) previsione vs consuntivo stesso anno
print('--- 4. consuntivo vs primo stanziamento (anni_dopo=1), uscite totali e titolo1, milioni')
c=R[R.tipo=='uscite'].groupby(['anno']).importo.sum()/1e6
f=P[(P.tipo=='uscite')&(P.anni_dopo_ultimo_rendiconto==1)].groupby('anno').importo.sum()/1e6
c1=R[(R.tipo=='uscite')&(R.liv1==1)].groupby(['anno','edizione']).importo.sum()/1e6
f1=P[(P.tipo=='uscite')&(P.anni_dopo_ultimo_rendiconto==1)&(P.liv1==1)].groupby('anno').importo.sum()/1e6
print(pd.concat([c.rename('consuntivo_tot'),f.rename('prev_tot_anno+1'),c1.groupby('anno').last().rename('consuntivo_tit1'),f1.rename('prev_tit1_anno+1')],axis=1).round(0).to_string())
# 5) confronto dataset 2013: ds227 assestato vs ds284 consuntivo
S=pd.read_csv('pulito/spesa_missioni.csv',sep=';',encoding='utf-8-sig')
x=S[(S.anno==2013)&(S.titolo==1)].groupby(['fonte','misura']).importo.sum()/1e6
print('--- 5. 2013 spesa corrente: ',x.round(1).to_dict())
x2=S[(S.titolo==1)&(S.fonte.isin(['ds227','ds284','ds397','ds396']))].groupby(['anno','fonte','misura']).importo.sum()/1e6
print(x2.round(1).to_string())
for (a,f_,m),val in x2.items():
    out.append(dict(controllo='spesa_corrente_totale_per_fonte',tipo='uscite titolo1',anno=a,dettaglio=f'{f_} {m}',valori=f'{val:,.2f}M',differenza_max_milioni=np.nan))
# 6) totale missioni 2012: somma programmi vs TOTALE dichiarato in ds227
import glob
a=pd.read_csv(glob.glob('raw/ckan_ds227/*.csv')[0],sep=';',encoding='cp1252',dtype=str)
a.columns=['M','P','c2012','a2013','p2014']
for col in ['c2012','a2013','p2014']: a[col]=a[col].str.replace(',','.').astype(float)
a['M']=a.M.str.strip(); a['P']=a.P.str.strip()
tm=a[(a.M!='TOTALE')&(a.P=='TOTALE')][['M','c2012','a2013','p2014']].set_index('M')
sm=a[(a.M!='TOTALE')&(a.P!='TOTALE')].groupby('M')[['c2012','a2013','p2014']].sum()
dd=(tm-sm).abs()
print('--- 6. ds227: TOTALE missione vs somma programmi, max diff (M):',dd.max().round(2).to_dict())
gt=a[(a.M=='TOTALE')][['c2012','a2013','p2014']].iloc[0]
print('   TOTALE generale',gt.to_dict(),'somma TOTALE missioni',tm.sum().round(2).to_dict())
out.append(dict(controllo='ds227_totale_vs_somma_programmi',tipo='uscite titolo1',anno=2012,dettaglio='max diff su missioni (c2012,a2013,p2014)',valori=str(dd.max().round(2).to_dict()),differenza_max_milioni=float(dd.max().max())))
out.append(dict(controllo='ds227_totale_generale_vs_somma_missioni',tipo='uscite titolo1',anno=2012,dettaglio='',valori=f'TOTALE={gt.to_dict()} somma={tm.sum().round(2).to_dict()}',differenza_max_milioni=float((gt-tm.sum()).abs().max())))
pd.DataFrame(out).to_csv('pulito/controllo_coerenza.csv',index=False,sep=';',encoding='utf-8-sig')
