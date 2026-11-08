"""Dati per la pagina rifatta (v2): secoli per tipo, autori, detentori, punti con quartiere.
Scrive docs/beni-culturali/data/v2.json (nome nuovo, non tocca i file della pagina attuale)."""
import csv, json, os, collections, statistics
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rows = [r for r in csv.DictReader(open(os.path.join(R,'beni-culturali','pulito','beni_milano.csv'),encoding='utf8')) if r['sede_milano']=='1']
GR = {'OA':'oa','OAC':'oa','D':'ds','S':'ds','RA':'ar','MA':'ar','CA':'ar','PST':'ps','A':'ax','BDM':'al','F':'al','NU':'al','PG':'al'}
GROUPS = ['oa','ds','ar','ps','ax','al']
def slot(s):
    if s=='' : return None
    s=int(s)
    return -6 if s<=-6 else s
SLOTS = [-6,-5,-4,-3,-2,-1]+list(range(1,22))
mat = {str(s):{g:0 for g in GROUPS} for s in SLOTS}
for r in rows:
    s = slot(r['secolo'])
    if s is not None: mat[str(s)][GR[r['tipo_scheda']]] += 1
nodata = sum(1 for r in rows if r['secolo']=='')
tot_g = collections.Counter(GR[r['tipo_scheda']] for r in rows)

def etich(r):
    t=(r['tipo_oggetto'] or '').lower(); so=(r['soggetto'] or '').lower()
    x = t if t else (r['titolo'] or '').lower()
    if so and so!=t: x = (x+': '+so) if x else so
    x = x.split(' | ')[0].replace('stampa stampa','stampa')
    return (x[:1].upper()+x[1:])[:90]
def anno(r):
    try:
        a=int(r['anno_inizio']); b=int(r['anno_fine'] or a); return (a+b)/2
    except: return None
def esempio(r):
    return [etich(r), (r['autore_principale'] or ''), r['datazione_testo'], r['iri']]
# barre da 25 anni, 1300-2024, per gruppo (anno medio della data; solo schede con secolo)
NB=29
bins=[{g:0 for g in GROUPS} for _ in range(NB)]
pre1300=0; pre_a=0; pre_g={g:0 for g in GROUPS}
for r in rows:
    if r['secolo']=='': continue
    y=anno(r)
    if y is None: continue
    if y<1300:
        pre1300+=1; pre_g[GR[r['tipo_scheda']]]+=1
        if y<0: pre_a+=1
    elif y<2025: bins[int((y-1300)//25)][GR[r['tipo_scheda']]]+=1
# esempi per secolo: 5 schede, con autore e soggetto, gruppi diversi
bysec = collections.defaultdict(list)
for r in rows:
    s=slot(r['secolo'])
    if s is not None: bysec[s].append(r)
esempi={}
for s,lst in bysec.items():
    lst=sorted(lst,key=lambda r:(-(1 if r['autore_principale'] else 0),-(1 if r['soggetto'] and r['soggetto']!=r['tipo_oggetto'].lower() else 0),r['iri']))
    out=[];usati=set()
    for r in lst:
        g=GR[r['tipo_scheda']]
        if g in usati: continue
        usati.add(g); out.append(esempio(r))
        if len(out)>=5: break
    for r in lst:
        if len(out)>=5: break
        e=esempio(r)
        if e not in out: out.append(e)
    # autori principali del secolo
    ca=collections.Counter()
    for r in lst:
        for x in r['autori'].split(' | '):
            if x: ca[x]+=1
    esempi[str(s)]={'ex':out,'aut':ca.most_common(5)}
# autori
A=collections.defaultdict(list)
for r in rows:
    for x in r['autori'].split(' | '):
        if x: A[x].append(r)
autori=[]
for n,lst in A.items():
    if len(lst)<4: continue
    ys=sorted(y for y in (anno(r) for r in lst) if y is not None)
    tg=collections.Counter(GR[r['tipo_scheda']] for r in lst)
    ex=[esempio(r) for r in sorted(lst,key=lambda r:(-(1 if r['soggetto'] and r['soggetto']!=r['tipo_oggetto'].lower() else 0),r['iri']))[:3]]
    q=lambda p: round(ys[min(len(ys)-1,int(p*(len(ys)-1)))]) if ys else None
    autori.append({'n':n,'c':len(lst),'p10':q(.1),'md':q(.5),'p90':q(.9),'nd':len(ys),'tg':dict(tg),'ex':ex})
autori.sort(key=lambda a:-a['c'])
# detentori
cd=collections.Counter(r['istituzione'] for r in rows)
non=cd.pop('non indicata',0)
det=[[k,v] for k,v in cd.most_common(12)]
# punti con quartiere
nil=json.load(open(os.path.join(R,'docs','medici-farmacie','data','nil.geojson'),encoding='utf8'))
def pip(x,y,ring):
    ins=False;j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i];xj,yj=ring[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: ins=not ins
        j=i
    return ins
def quartiere(lo,la):
    for f in nil['features']:
        g=f['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for p in polys:
            if pip(lo,la,p[0]) and not any(pip(lo,la,h) for h in p[1:]): return f['properties']['n']
    return None
P=collections.defaultdict(list)
for r in rows:
    if r['coord_in_comune']=='1' and r['lat']: P[(round(float(r['lat']),6),round(float(r['long']),6))].append(r)
punti=[]
for (la,lo),lst in P.items():
    ci=collections.Counter(r['istituzione'] for r in lst if r['istituzione']!='non indicata')
    nome,cn = ci.most_common(1)[0] if ci else ('',0)
    to=collections.Counter((r['tipo_oggetto'] or r['titolo']).lower().split(' | ')[0] for r in lst).most_common(3)
    tg=collections.Counter(GR[r['tipo_scheda']] for r in lst)
    punti.append({'la':la,'lo':lo,'n':len(lst),'nome':nome,'nn':cn,'og':to,'tg':dict(tg),'q':quartiere(lo,la)})
punti.sort(key=lambda p:-p['n'])
qn=collections.Counter()
for p in punti: qn[p['q']]+=p['n']
num=json.load(open(os.path.join(R,'docs','beni-culturali','data','numeri.json'),encoding='utf8'))
out={'bins':bins,'pre1300':pre1300,'pre_g':pre_g,'pre_ac':pre_a,'slots':SLOTS,'mat':mat,'nodata':nodata,'tot_g':tot_g,'esempi':esempi,'autori':autori,'det':det,'det_non':non,'punti':punti,'quartieri':qn.most_common(),'num':{k:v for k,v in num.items() if k!='per_secolo'}}
json.dump(out,open(os.path.join(R,'docs','beni-culturali','data','v2.json'),'w',encoding='utf8'),ensure_ascii=False,separators=(',',':'))
print(os.path.getsize(os.path.join(R,'docs','beni-culturali','data','v2.json')),len(autori),len(punti),qn.most_common(6))
print(autori[:3]); print(punti[:10])
