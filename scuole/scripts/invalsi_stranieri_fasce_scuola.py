import sys,runpy,numpy as np,pandas as pd
B,R=sys.argv[1],sys.argv[2]
sys.argv=['x',R,f'{B}/pulito']
m=runpy.run_path(f'{B}/scripts/invalsi_stranieri.py',run_name='lib')
d,c=m['tutto']()
c['ok']=(c.noti>=10)&(c.quota_mancante<=.25)
d=d.merge(c[['id_classe','ok']],on='id_classe'); d=d[d.ok&d.punteggio.notna()&d.peso.notna()]
wls,GEO=m['wls_cl'],m['GEO']
d['f20_30']=((d.quota>.2)&(d.quota<=.3))*1.0; d['f30_50']=((d.quota>.3)&(d.quota<=.5))*1.0; d['f50']=(d.quota>.5)*1.0
xs=['f20_30','f30_50','f50','escs']
for gr in (5,8):
  for mat in ('ita','mat'):
    for geo in ('Lombardia','Nord'):
      s=d[(d.grado==gr)&(d.materia==mat)&GEO[geo](d)&(d.origine==1)]
      r=wls(s,'punteggio',xs,'id_scuola')
      # classi >50% in scuole dove l'altra classe sta sotto il 50%
      u=s.drop_duplicates('id_classe'); k=u.groupby('id_scuola').f50.agg(['sum','count']); disc=((k['sum']>0)&(k['sum']<k['count'])).sum()
      print(gr,mat,geo,'n',r['n'],'classi',r['G_id_classe'],'| '+' | '.join(f"{n} {b:.1f} ({se:.1f})" for n,b,se in zip(xs[:3],r['b'],r['se_id_scuola'])),'| scuole con una sola classe >50%:',disc)
