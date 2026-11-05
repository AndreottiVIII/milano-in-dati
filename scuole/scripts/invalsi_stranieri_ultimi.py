import re,sys,runpy,numpy as np,pandas as pd
B,R=sys.argv[1],sys.argv[2]
for c in ['MIIC8B600G','MIIC8FT00E']:
    t=open(f'{R}/rav/ind/{c}_2.2.a.1.html','rb').read().decode('utf8','replace')
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    cel=[re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',x)).strip() for x in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',t,flags=re.S)]
    lab=[x for x in cel if re.search(r'[A-Za-z]{2}',x) and not re.search(r'Punteggio|Percentuale|Riferimenti|Diff\.|Istituto/Plesso|Italiano|Matematica|Inglese|n\.d\.',x)]
    print(c,len(cel),'etichette:',pd.Series(lab).value_counts().head(8).to_dict())
    print('  plessi/classi? codici:',len(set(re.findall(r'MI[A-Z0-9]{8}',t))),'parole classe:',len(re.findall(r'(?i)\bclasse\b',t)))
    tt=open(f'{R}/rav/ind/{c}_2.2.a.2.html','rb').read().decode('utf8','replace')
    tt=re.sub(r'<script.*?</script>|<style.*?</style>','',tt,flags=re.S)
    tt=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',tt)); print('  2.2.a.2:',tt[:220])
    print('  origine/stranieri in 2.2.a.1 o .2:',len(re.findall(r'(?i)stranier|nativ|generazione|origine',t+tt)))
a=pd.read_csv(f'{B}/pulito/miur_scuole_anno.csv',sep=';',dtype={'codice_mecc':str})
a=a[(a.anno_inizio==2024)&(a.ordine=='sec1')&(a.tipo=='statale')]
g=pd.read_csv(f'{B}/raw/miur/SCUANAGRAFESTAT20252620250901.csv',dtype=str,keep_default_na=False)
g=g[g.CODICECOMUNESCUOLA=='F205'][['CODICESCUOLA','CODICEISTITUTORIFERIMENTO']].rename(columns={'CODICESCUOLA':'codice_mecc','CODICEISTITUTORIFERIMENTO':'istituto'})
s=a.merge(g,on='codice_mecc').groupby('istituto').agg(i=('iscritti','sum'),n=('cittadinanza_non_italiana','sum'))
s['q8']=s.n/s.i*100
d=pd.read_csv(f'{R}/rav/tabella_10.csv',sep=';',encoding='utf-8-sig')
d['vs_lomb']=d.punteggio-d.lombardia
d=d.merge(s[['q8']],left_on='istituto',right_index=True,how='left')
d['g']=np.where(d.grado.str.contains('quinte'),5,np.where(d.grado.str.contains('terze'),8,2))
d=d[d.g>2]
print(d.pivot_table(index=['quota_primaria','q8','istituto'],columns=['g','materia'],values=['vs_lomb','diff_escs']).round(1).to_string())
for g_,qc in ((5,'quota_primaria'),(8,'q8')):
    for m in ('Italiano','Matematica'):
        x=d[(d.g==g_)&(d.materia==m)]
        y=x.dropna(subset=['diff_escs'])
        print(g_,m,'n',x.vs_lomb.notna().sum(),'Spearman quota vs (punt - Lombardia)',round(x[qc].corr(x.vs_lomb,method='spearman'),2),'| n',len(y),'quota vs diff ESCS',round(y[qc].corr(y.diff_escs,method='spearman'),2))
sys.argv=['x',R,f'{B}/pulito']
m=runpy.run_path(f'{B}/scripts/invalsi_stranieri.py',run_name='lib')
D,_=m['tutto']()
D=D[D.punteggio.notna()&D.peso.notna()]
for (gr,an) in ((5,'2024-25'),(8,'2024-25')):
  for mat in ('ita','mat'):
    for nom,f in (('Lombardia',D.cod_reg==4),('Italia',D.cod_reg>0)):
        q=D[(D.grado==gr)&(D.anno==an)&(D.materia==mat)&f]
        print(gr,an,mat,nom,{int(o):round(np.average(k.punteggio,weights=k.peso),1) for o,k in q[q.origine.isin([1,2,3])].groupby('origine')},'tot',round(np.average(q.punteggio,weights=q.peso),1))
