# Massima giornaliera di Linate 2026 dai messaggi SYNOP: gruppo 1sTTT della sezione 333 nel messaggio delle 18 UTC (massima 06-18 UTC),
# insieme alla massima delle letture orarie. Conta i giorni con almeno 35 e 30 gradi e li confronta con Brera.
import csv, os, glob
B=r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\temperature'
D=os.path.join(B,'raw','linate_2026')
tx18={}
for f in sorted(glob.glob(os.path.join(D,'synop_2026*.txt'))):
    for l in open(f,encoding='latin1'):
        p=l.strip().split(',')
        if len(p)<7 or p[4]!='18': continue
        t=p[6].rstrip('=').split()
        if '333' not in t: continue
        for g in t[t.index('333')+1:]:
            if len(g)==5 and g[0]=='1' and g[1] in '01' and g[2:].isdigit():
                v=int(g[2:])/10; tx18[f'{p[1]}-{p[2]}-{p[3]}']=-v if g[1]=='1' else v; break
            if g[0] in '5678' : break
hor={r['data']:float(r['tmax']) for r in csv.DictReader(open(os.path.join(D,'linate_2026_giorni.csv')))}
nh={r['data']:int(r['n_ore']) for r in csv.DictReader(open(os.path.join(D,'linate_2026_giorni.csv')))}
bre={}
for r in csv.DictReader(open(os.path.join(B,'discrepanza','out','serie_continua_1763_oggi.csv'),encoding='utf8')):
    if r['data'].startswith('2026') and r['TX']: bre[r['data']]=float(r['TX'])
days=[d for d in sorted(hor) if d in bre and (d in tx18 or nh[d]>=20)]
lt={d:max(hor[d],tx18.get(d,-99)) for d in days}
print('giorni con massima di Linate:',len(tx18),' giorni confrontabili con Brera:',len(days))
for s in (35,30):
    print(f'>= {s}: Linate (massima vera) {sum(lt[d]>=s for d in days)}, Linate (solo letture orarie) {sum(hor[d]>=s for d in days)}, Brera {sum(bre[d]>=s for d in days)}')
dd=[bre[d]-lt[d] for d in days]; print('Brera meno Linate (massima), media',round(sum(dd)/len(dd),2))
es=[bre[d]-lt[d] for d in days if '06'<=d[5:7]<='08']; print('estate',round(sum(es)/len(es),2),len(es))
print('max Linate',max(days,key=lambda d:lt[d]),max(lt.values()))
# se si toglie a Brera la differenza media: quanti giorni >=35
off=sum(dd)/len(dd)
print('Brera corretta della differenza media: >=35',sum(bre[d]-off>=35 for d in days),' >=30',sum(bre[d]-off>=30 for d in days))
import json
storico={}
for f in sorted(glob.glob(os.path.join(B,'raw','gsod_linate','16080099999_*.csv'))):
    y=int(os.path.basename(f).split('_')[1][:4]); g35=0;g30=0;n=0
    for r in csv.DictReader(open(f,encoding='utf8')):
        try: mx=float(r['MAX'])
        except: continue
        if mx>900: continue
        c=(mx-32)/1.8; n+=1; g35+=c>=34.95; g30+=c>=29.95
    storico[y]={'giorni_con_dato':n,'gg_35':g35,'gg_30':g30}
out={'nota':'Verifica dei giorni caldi del 2026 con la stazione di Milano Linate (SYNOP 16080, via Ogimet; massima giornaliera dal messaggio delle 18 UTC, altrimenti dalle letture orarie). Confronto sui giorni in cui ci sono sia Linate sia Brera. Storico Linate: NOAA GSOD.',
 'giorni_confrontati':len(days),'periodo':'1 gennaio - 28 ottobre 2026',
 'linate':{'gg_35':sum(lt[d]>=35 for d in days),'gg_30':sum(lt[d]>=30 for d in days),'massima':max(lt.values())},
 'brera':{'gg_35':sum(bre[d]>=35 for d in days),'gg_30':sum(bre[d]>=30 for d in days)},
 'brera_meno_linate_massima_media':round(sum(dd)/len(dd),2),'brera_meno_linate_estate':round(sum(es)/len(es),2),
 'linate_storico_gsod':storico}
json.dump(out,open(r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\docs\temperature\data\verifica_linate_2026.json','w',encoding='utf8'),ensure_ascii=False,indent=1)
print('scritto')
