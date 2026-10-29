import csv,collections,json
out={}
m=list(csv.DictReader(open('pulito/fermate_metro_nomi.csv',encoding='utf-8-sig')))
out['metro_stazioni']=len(m)
out['metro_per_categoria']=dict(collections.Counter(r['categoria'] for r in m))
pp=[r for r in m if r['categoria'] in('persona','santo/santa')]
out['metro_persone_totali']=len(pp)
out['metro_persona_laica']=dict(collections.Counter(r['sesso'] for r in m if r['categoria']=='persona'))
out['metro_santi']=dict(collections.Counter(r['sesso'] for r in m if r['categoria']=='santo/santa'))
out['metro_persone_e_santi_per_sesso']=dict(collections.Counter(r['sesso'] for r in pp))
out['metro_gruppo_mestiere_persone_laiche']=dict(collections.Counter(r['gruppo_mestiere'] for r in m if r['categoria']=='persona'))
out['metro_luogo_sottocat']=dict(collections.Counter(r['sottocategoria'] for r in m if r['categoria']=='luogo'))
out['metro_da_verificare']=sum(1 for r in m if r['da_verificare'])
# secoli di nascita delle persone
def anno(x):
    try: return int(x.split('–')[0])
    except: return None
sec=collections.Counter()
for r in m:
    if r['categoria']=='persona':
        a=anno(r['nascita_morte'])
        if a is not None: sec[(a//100+1) if a>0 else 0]+=1
out['metro_persone_per_secolo_nascita']=dict(sorted(sec.items()))
t=list(csv.DictReader(open('pulito/fermate_tram_nomi.csv',encoding='utf-8-sig')))
out['tram_denominazioni']=len(t)
out['tram_per_categoria_denominazioni']=dict(collections.Counter(r['categoria'] for r in t))
w=collections.Counter()
for r in t: w[r['categoria']]+=int(r['n_fermate'])
out['tram_per_categoria_pesato_fermate']=dict(w)
tp=[r for r in t if r['categoria'] in('persona','santo/santa')]
out['tram_persone_per_sesso_denominazioni']=dict(collections.Counter(r['sesso'] for r in t if r['categoria']=='persona'))
out['tram_santi_per_sesso']=dict(collections.Counter(r['sesso'] for r in t if r['categoria']=='santo/santa'))
out['tram_gruppo_mestiere_persone']=dict(collections.Counter(r['gruppo_mestiere'] for r in t if r['categoria']=='persona'))
out['tram_da_verificare']=sum(1 for r in t if r['da_verificare'])
json.dump(out,open('pulito/riepilogo.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
