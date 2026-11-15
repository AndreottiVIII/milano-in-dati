import json,re,os
R=r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati'
neg=open(R+r'\docs\negozi\index.html',encoding='utf-8').read()
css=neg[neg.index('<style>'):neg.index('</style>')+8]
D=json.load(open(R+r'\docs\sharing\data\riepilogo.json',encoding='utf-8'))
def f0(x):return f'{round(x):,}'.replace(',','.')
def f1(x):return f'{x:.1f}'.replace('.',',')
def f2(x):return f'{x:.2f}'.replace('.',',')
s25=[r for r in D['serie'] if r['anno']==2025][0];m=D['mezzi25'];inc=D['incidenti'];i24=inc[-1];i20=inc[0];pa=D['picco_auto']
hl=[('t-linee',f0(s25['monopattini']),f"noleggi al giorno di monopattini nel 2025: il servizio più usato, più di BikeMi ({f0(s25['bici_stazione'])})."),
('t-classifica','1° → 4°',f"le auto libere: prime dal 2018 al 2023, quarte nel 2025. Noleggi giù del {abs(pa['calo_pct'])}% dal picco del {pa['anno']}."),
('t-punti',f1(m['monopattini']['noleggi_per_mezzo_giorno']),f"noleggi al giorno per ogni monopattino. Per ogni bici: {f2(m['bici']['noleggi_per_mezzo_giorno'])}."),
('t-km',f0(m['auto_libere']['km_per_mezzo_anno']),f"chilometri all'anno per ogni auto libera. Un monopattino ne fa {f0(m['monopattini']['km_per_mezzo_anno'])} km."),
('t-incidenti',f0(i24['incidenti']),f"incidenti con feriti con un monopattino nel {i24['anno']}. Nel {i20['anno']} erano {f0(i20['incidenti'])}."),
('t-tasso',f0(i24['incidenti_per_milione_noleggi']),f"incidenti con monopattini ogni milione di noleggi in condivisione nel {i24['anno']}; nel {i20['anno']} {f0(i20['incidenti_per_milione_noleggi'])}. Conto approssimato.")]
st='<!--statico--><div class="statico"><ul>'+''.join(f'<li><a href="#{h}"><strong>{n}</strong> {t}</a></li>' for h,n,t in hl)+'</ul></div><!--/statico-->'
body=open('shr_body.html',encoding='utf-8').read().replace('@@STATICO@@',st)
desc="Quante volte al giorno si noleggia un mezzo in condivisione a Milano, dal 2011 a oggi: monopattini, scooter, auto e bici, a confronto, con gli incidenti con i monopattini."
head=f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><link rel="icon" href="../favicon.svg" type="image/svg+xml"><link rel="icon" href="../favicon.ico" sizes="48x48"><link rel="apple-touch-icon" href="../apple-touch-icon.png"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milano in dati · Monopattini, scooter e auto in condivisione</title><meta name="description" content="{desc}">
'''
html=head+css+'<script src="../menu.js" defer></script></head><body><main>\n'+body
os.makedirs(R+r'\bozze-grafici\sharing-v2',exist_ok=True)
open(R+r'\bozze-grafici\sharing-v2\index.html','w',encoding='utf-8').write(html)
print(len(html))
