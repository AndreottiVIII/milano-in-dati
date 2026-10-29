"""Fase 2, passo 3. Serie "vecchia" 2012 - 18/9/2016 (conteggio diverso), tenuta SEPARATA dalla serie 2016+.
Uso: python -I 07_serie_vecchia.py <raw> <pulito>
Scrive pulito/ingressi_giornalieri_2012-2016_conteggio_diverso.csv e pulito/_agg/serie_vecchia_confronto.txt"""
import sys,glob,os,pandas as pd,numpy as np
raw,out=sys.argv[1:3]
def L(*pats):
    fs=[f for p in pats for f in sorted(glob.glob(os.path.join(raw,p)))]
    d=pd.concat([pd.read_csv(f,sep=';') for f in fs]); d['data']=pd.to_datetime(d.timeIndex); return d.drop(columns='timeIndex').set_index('data')
tot=L('ds779*/*.csv','ds78[0-3]*/*.csv')
days=pd.date_range('2012-01-01','2016-12-31')
df=pd.DataFrame(index=days); df.index.name='data'
df['totale']=tot.totale.reindex(days); df['areac_flag']=tot.areac.reindex(days)
for nome,pats,pre in [('veic',('ds789*/*.csv','ds79[0-3]*/*.csv'),'veic_'),('euro',('ds784*/*.csv','ds78[5-8]*/*.csv'),'euro_'),
                      ('aut',('ds794*/*.csv','ds79[5-8]*/*.csv'),'aut_'),('res',('ds799*/*.csv','ds80[0-3]*/*.csv'),'res_'),
                      ('alim',('ds804*/*.csv','ds80[5-8]*/*.csv'),'alim_'),('serv',('ds809*/*.csv','ds81[0-3]*/*.csv'),'serv_')]:
    t=L(*pats).drop(columns='areac')
    t.columns=[pre+c.lower().replace(' ','_') for c in t.columns]
    df=df.join(t)
df=df[df.index<='2016-09-18']
s=df.totale
r={}
for d,v in s.dropna().items():
    nb=s[(s.index>=d-pd.Timedelta(days=28))&(s.index<=d+pd.Timedelta(days=28))&(s.index.day_of_week==d.day_of_week)&(s.index!=d)].dropna()
    if len(nb)>2: r[d]=v/nb.median()
x=pd.Series(r)
df['flag']='ok'
df.loc[df.index>='2016-01-01','flag']='livello_ridotto_dal_2016'
df.loc[x[x<0.25].index,'flag']='parziale_probabile'
df.loc[df.totale.isna(),'flag']='mancante'
df.insert(0,'serie','2012-2015 (conteggio diverso)')
df.loc[df.index>='2016-01-01','serie']='2016 gen-set (conteggio diverso, livello ridotto)'
it={0:'lun',1:'mar',2:'mer',3:'gio',4:'ven',5:'sab',6:'dom'}
df.insert(1,'giorno_settimana',[it[i] for i in df.index.day_of_week])
df.to_csv(os.path.join(out,'ingressi_giornalieri_2012-2016_conteggio_diverso.csv'),sep=';')
print(df.flag.value_counts()); print(df[df.flag=='parziale_probabile'][['totale']])
# confronto con la serie nuova nei 18 giorni in comune
new=pd.read_csv(os.path.join(out,'ingressi_giornalieri.csv'),sep=';',parse_dates=['data']).set_index('data')
ov=pd.concat([df.totale.rename('vecchia'),new.totale.rename('nuova_ufficiale'),new.tot_mensili.rename('nuova_mensili'),new.tipo_auto.rename('nuova_auto')],axis=1).dropna()
ov=ov[ov.index<='2016-09-18']
ov['rapporto']=ov.vecchia/ov.nuova_ufficiale
ov['dow']=[it[i] for i in ov.index.day_of_week]
with open(os.path.join(out,'_agg','serie_vecchia_confronto.txt'),'w') as f:
    f.write(ov.round(3).to_string()+'\n')
    f.write('medie 18 giorni: vecchia %.0f, nuova ufficiale %.0f, rapporto di medie %.3f\n'%(ov.vecchia.mean(),ov.nuova_ufficiale.mean(),ov.vecchia.mean()/ov.nuova_ufficiale.mean()))
    f.write('rapporto per giorno: min %.3f max %.3f; feriali %.3f; sab-dom %.3f\n'%(ov.rapporto.min(),ov.rapporto.max(),ov[ov.dow.isin(['lun','mar','mer','gio','ven'])].rapporto.mean(),ov[ov.dow.isin(['sab','dom'])].rapporto.mean()))
    # rapporto mensile 2016 su stesso mese 2015
    m=df.totale.groupby([df.index.year,df.index.month]).mean()
    f.write('\nmedia giornaliera per mese (serie vecchia)\n'+m.round(0).to_string()+'\n')
print(open(os.path.join(out,'_agg','serie_vecchia_confronto.txt')).read()[:3500])
