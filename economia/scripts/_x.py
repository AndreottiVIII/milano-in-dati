import sys; sys.path.insert(0,'economia/scripts')
from _lib import load
_,g=load('economia/raw/nama_10r_3gdp.tsv.gz')
G=sorted(set(k['geo'] for k,v in g if len(k['geo'])<=3)); print(G)
m={k['geo']:v for k,v in g if k['unit']=='MIO_EUR'}
for c in ['EL','PT','HU','CZ','RO','IE','DK','FI','AT','BE']:
    print(c, m.get(c,{}).get(2023))
# province IT ranking pc 2023
pc={k['geo']:v for k,v in g if k['unit']=='EUR_HAB' and k['geo'].startswith('IT') and len(k['geo'])==5 and 2023 in v}
print(sorted(((v[2023],c) for c,v in pc.items()),reverse=True)[:6], len(pc))
tot={c:m[c][2023] for c in m if c.startswith('IT') and len(c)==5 and 2023 in m[c]}
print(sorted(((v,c) for c,v in tot.items()),reverse=True)[:4])
for c in ['ITC','ITI','ITI4','ITC4']: print(c,m[c][2023])
