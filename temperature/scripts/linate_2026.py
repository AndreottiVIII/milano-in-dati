# Scarica i SYNOP orari di Milano Linate (stazione 16080) da Ogimet, giorno per mese, e conta i giorni caldi del 2026.
# Poi li confronta con Brera (serie del sito). Uso: python -I -X utf8 linate_2026.py
import urllib.request, time, csv, os, sys, datetime as dt
BASE=r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\temperature'
OUT=os.path.join(BASE,'raw','linate_2026')
os.makedirs(OUT,exist_ok=True)
def get(url):
    r=urllib.request.Request(url,headers={'User-Agent':'milano-in-dati/1.0'})
    return urllib.request.urlopen(r,timeout=90).read().decode('latin1')
def mese(y,m):
    f=os.path.join(OUT,f'synop_{y}{m:02d}.txt')
    if os.path.exists(f) and os.path.getsize(f)>1000: return open(f,encoding='latin1').read()
    a=dt.date(y,m,1); b=(dt.date(y+(m==12),(m%12)+1,1)-dt.timedelta(days=1))
    t=get(f'https://www.ogimet.com/cgi-bin/getsynop?block=16080&begin={a:%Y%m%d}0000&end={b:%Y%m%d}2359')
    open(f,'w',encoding='latin1').write(t); time.sleep(25); return t
def temp(line):
    p=line.strip().rstrip('=').split(',')
    if len(p)<7: return None
    tok=p[6].split()
    if len(tok)<6: return None
    # tok: AAXX YYGGi 16080 iRiXhVV Nddff [00fff] 1sTTT ...
    for t in tok[5:]:
        if len(t)==5 and t[0]=='1' and t[1] in '01' and t[2:].isdigit():
            v=int(t[2:])/10; return -v if t[1]=='1' else v
        if t[0] in '2345': break
    return None
if __name__=='__main__':
    anno=int(sys.argv[1]) if len(sys.argv)>1 else 2026
    ult=int(sys.argv[2]) if len(sys.argv)>2 else 10
    days={}
    for m in range(1,ult+1):
        t=mese(anno,m)
        for l in t.splitlines():
            p=l.split(',')
            if len(p)<7: continue
            v=temp(l)
            if v is None: continue
            d=f'{p[1]}-{p[2]}-{p[3]}'; days.setdefault(d,[]).append((int(p[4]),v))
    with open(os.path.join(OUT,f'linate_{anno}_giorni.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['data','n_ore','tmax','tmin'])
        for d in sorted(days):
            vs=[v for h,v in days[d]]; w.writerow([d,len(vs),max(vs),min(vs)])
    print('giorni',len(days))
