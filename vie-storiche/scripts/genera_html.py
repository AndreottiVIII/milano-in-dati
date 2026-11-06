# -*- coding: utf-8 -*-
"""Legge pulito/vie.json e pulito/riepilogo.json e scrive la bozza bozze-grafici/vie-storiche.html
(pagina autonoma: dati dentro il file). Uso: python -I -X utf8 genera_html.py"""
import json, os

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(QUI)
RADICE = os.path.dirname(BASE)
VIE = os.path.join(BASE, "pulito", "vie.json")
RIEP = os.path.join(BASE, "pulito", "riepilogo.json")
OUT = os.path.join(RADICE, "bozze-grafici", "vie-storiche.html")

ANNI = [1884, 1910, 1930, 1946, 1956, 1965, 1972, 1990, 2006, 2012]
INTERVALLI = [(ANNI[i], ANNI[i + 1]) for i in range(len(ANNI) - 1)]

vie = json.load(open(VIE, encoding="utf-8"))
riep = json.load(open(RIEP, encoding="utf-8"))

# dati per la pagina
dati_vie = []
for v in vie:
    dati_vie.append({"id": v["id"], "oggi": v["attuale"], "righe": v["righe"],
                     "n": sum(1 for e in v["eventi"] if e["tipo"] == "cambio"),
                     "nomi": sorted({c["raw"] for c in v["celle"] if c["stato"] == "ok"})})
dati_vie.sort(key=lambda x: x["oggi"].lower())

barre = []
for a, b in INTERVALLI:
    k = "%d-%d" % (a, b)
    barre.append({"da": a, "a": b, "anni": b - a, "n": riep["per_intervallo"].get(k, 0)})
salti = sum(riep["con_salto_mappa_illeggibile"].values())
viali_porta = sum(1 for v in vie if v["celle"][0]["raw"].lower().startswith(("viale di porta", "viale di p.")))

# storie scelte dai dati: le vie con piu' nomi diversi + quella con un nome che compare su una sola mappa
def n_nomi(v):
    return sum(1 for r in v["righe"] if r["esito"] != "vuoto")

per_nome = {v["attuale"]: v for v in vie}
scelte = ["Piazza della Repubblica", "Piazza Filippo Meda", "Via Turati", "Parco della Resistenza", "Largo Mattioli"]
storie = []
for nome in scelte:
    v = per_nome[nome]
    cambi = sum(1 for e in v["eventi"] if e["tipo"] == "cambio")
    nomi_distinti = n_nomi(v)
    riga = "%d nomi diversi" % nomi_distinti if nomi_distinti != 3 else "tre nomi diversi"
    # un nome che compare su una sola mappa, a meta' strada
    isolate = [r for r in v["righe"][1:-1] if r["da"] == r["a"] and r["esito"] == "cambio"]
    nota = ""
    if isolate:
        r = isolate[0]
        nota = "Il nome «%s» compare solo sulla mappa del %s." % (r["nome"].strip(), r["da"])
    storie.append({"oggi": nome, "id": v["id"], "frase": "%d %s." % (cambi, "cambio vero di nome" if cambi == 1 else "cambi veri di nome"), "nota": nota})

assert viali_porta and all(any(e["tipo"] == "cambio" and e["a"] == "1930" for e in v["eventi"]) for v in vie if v["celle"][0]["raw"].lower().startswith(("viale di porta", "viale di p."))), "viali di porta"
n_vie = riep["vie"]
n_cambio = riep["con_almeno_un_cambio"]
n_piu = sum(c for k, c in riep["per_numero_di_cambi"].items() if int(k) >= 2)
tot_cambi = riep["cambi_totali"]
b = {(x["da"], x["a"]): x["n"] for x in barre}
n_30_46 = b[(1930, 1946)]
n_10_30 = b[(1910, 1930)]

PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Le vie che hanno cambiato nome</title>
<style>
:root{--m1:#E30613;--m2:#00A651;--m3:#FFD500;--m4:#0072BC;--m5:#8E4FB3;--nero:#111;--grigio:#6d6d6d;--riga:#ddd}
*{box-sizing:border-box}
html,body{margin:0;background:#fff;color:var(--nero);font-family:Helvetica,Arial,sans-serif;font-size:17px;line-height:1.4}
.pagina{max-width:720px;margin:0 auto;padding:0 16px 48px}
.testata{border-top:14px solid var(--m1);padding-top:14px}
.bozza{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--grigio)}
h1{font-size:34px;line-height:1.05;margin:6px 0 10px;font-weight:700;letter-spacing:-.01em}
h2{font-size:22px;margin:34px 0 8px;line-height:1.15}
p{margin:8px 0}
.sotto{font-size:18px;color:#333}
.numeri{display:flex;flex-direction:column;gap:10px;margin:22px 0 4px}
.num{display:flex;align-items:center;gap:14px}
.num b{flex:none;min-width:72px;height:56px;display:flex;align-items:center;justify-content:center;font-size:32px;color:#fff;padding:0 8px}
.num span{font-size:17px;line-height:1.2}
.cerca{display:block;font-weight:700;font-size:16px;margin:14px 0 6px}
input[type=search]{width:100%;font:inherit;font-size:18px;padding:12px;border:3px solid var(--nero);border-radius:0;background:#fff;-webkit-appearance:none}
.sugg{display:flex;flex-direction:column;margin:0}
.sugg button{font:inherit;font-size:16px;text-align:left;padding:11px 8px;border:0;border-bottom:1px solid var(--riga);background:#fff;cursor:pointer}
.sugg button small{display:block;color:var(--grigio);font-size:13px}
.prova{font-size:15px;margin:10px 0 0;color:#333}
.prova button{font:inherit;font-size:15px;border:2px solid var(--nero);background:#fff;padding:4px 9px;margin:4px 6px 0 0;cursor:pointer}
.titolo{font-size:24px;font-weight:700;margin:20px 0 2px;line-height:1.1}
.frase{font-size:17px;margin:2px 0 12px;color:#333}
.linea{list-style:none;margin:6px 0 4px;padding:0 0 0 0;border-left:8px solid var(--m2);margin-left:6px}
.linea li{position:relative;padding:4px 0 14px 18px}
.linea li:before{content:"";position:absolute;left:-17px;top:7px;width:14px;height:14px;border-radius:50%;background:#fff;border:4px solid var(--nero)}
.linea li.cambia:before{background:var(--m3)}
.linea li.vuoto:before{border-color:var(--grigio);border-style:dashed}
.anni{font-size:14px;font-weight:700;letter-spacing:.03em}
.nome{font-size:19px;line-height:1.2;font-weight:700;overflow-wrap:anywhere}
.linea li.vuoto .nome{font-weight:400;color:var(--grigio);font-size:16px}
.det{font-size:14px;color:#444;margin-top:2px}
.tag{display:inline-block;font-size:12px;font-weight:700;background:var(--m3);color:var(--nero);padding:1px 6px;margin-left:6px;vertical-align:2px}
.tag.g{background:#e8e8e8}
.bar{display:grid;grid-template-columns:104px 1fr;gap:8px;align-items:center;margin:6px 0}
.bar .et{font-size:14px;line-height:1.15}
.bar .et small{display:block;color:var(--grigio);font-size:12px}
.bar .tr{display:flex;align-items:center;gap:8px}
.bar .tr i{display:block;height:24px;background:var(--m4);flex:none}
.bar .tr i.max{background:var(--m1)}
.bar .tr b{font-size:17px}
.storie{display:flex;flex-direction:column;gap:22px}
.storia{border-top:3px solid var(--nero);padding-top:8px}
.storia h3{font-size:20px;margin:0 0 2px;line-height:1.15}
.nota{font-size:14px;color:#333;border-top:2px solid var(--nero);padding-top:10px;margin-top:38px}
.nota ul{padding-left:20px;margin:6px 0}
.nota li{margin:4px 0}
.nascosto{display:none}
@media (max-width:420px){h1{font-size:30px}.titolo{font-size:22px}}
</style>
</head>
<body>
<div class="pagina">
<header class="testata">
  <div class="bozza">Bozza · Milano in dati</div>
  <h1>Le vie che hanno cambiato nome</h1>
  <p class="sotto">Come si chiamava la tua via nel 1884, nel 1910, nel 1930, nel 1946 e dopo? Il Comune ha messo in fila i nomi che 36 vie di Milano portano sulle mappe storiche.</p>
</header>

<div class="numeri">
  <div class="num"><b style="background:var(--m4)">__NVIE__</b><span>vie nel dataset, con il nome letto su dieci mappe, dal 1884 al 2012</span></div>
  <div class="num"><b style="background:var(--m1)">__NCAMBIO__</b><span>hanno cambiato nome almeno una volta</span></div>
  <div class="num"><b style="background:var(--m2)">__NPIU__</b><span>lo hanno cambiato più di una volta</span></div>
</div>

<h2>Cerca la tua via</h2>
<label class="cerca" for="q">Scrivi il nome di oggi o uno vecchio</label>
<input id="q" type="search" placeholder="per esempio: Monte Grappa" autocomplete="off">
<div class="sugg" id="sugg"></div>
<div class="prova">Oppure prova: <span id="prova"></span></div>
<div id="scheda"></div>

<h2>Quando cambiano i nomi</h2>
<p>I cambi veri di nome, contati tra una mappa e la successiva. Sono __TOT__ in totale.</p>
<div id="grafico"></div>
<p>Tra il 1930 e il 1946 i cambi sono __N3046__. Il periodo con più cambi è un altro: tra il 1910 e il 1930 ce ne sono __N1030__. Tra le mappe del 1910 e del 1930 passano 20 anni, tra quelle del 1930 e del 1946 ne passano 16.</p>
<p>Altri __SALTI__ cambi ci sono, ma una mappa in mezzo non si legge: non si può dire in quale periodo siano avvenuti.</p>
<p>Dei __VIALI__ viali che nel 1884 si chiamavano «Viale di Porta…», tutti hanno un altro nome dalla mappa del 1930.</p>

<h2>Qualche storia</h2>
<div class="storie" id="storie"></div>

<div class="nota">
  <b>Fonte e limiti dei dati</b>
  <ul>
    <li>Fonte: Comune di Milano, «Vie di Milano e corrispondenza toponomastica nelle mappe storiche dal 1884», licenza CC BY 4.0. Il dataset è del progetto LetMi, che raccoglie i luoghi di Milano citati nei libri.</li>
    <li>Non sono tutte le vie di Milano: sono __NVIE__ vie scelte per quel progetto (una riga del file era doppia e l'ho contata una volta). Quello che vedi qui non dice nulla sul resto della città.</li>
    <li>Le mappe sono dieci: 1884, 1910, 1930, 1946, 1956, 1965, 1972, 1990, 2006, 2012. Un cambio di nome è collocato tra due mappe, non in un anno preciso.</li>
    <li>In __ILLEG__ caselle la mappa non si legge e in __NONEX__ la via non esiste ancora: non sono cambi.</li>
    <li>Ho tenuto come cambio solo un nome davvero diverso. Via/viale/piazza, maiuscole, abbreviazioni, «XXIV» o «Ventiquattro», un nome di battesimo in più o in meno («Via Turati», «Via Filippo Turati») contano come lo stesso nome. Se sulla mappa si aggiunge o si toglie un secondo nome, lo segno ma non lo conto come cambio.</li>
    <li>Quando il file scrive tra parentesi il nome di oggi, non lo considero il nome della mappa.</li>
    <li>Qui non si spiega perché un nome sia cambiato: i dati dicono quando, non perché.</li>
    <li>Tra i nomi di oggi c'è una sola donna, Principessa Clotilde, che compare dalla mappa del 1930. Sui nomi delle mappe del 1884 e 1910 di queste vie non ne ho riconosciute.</li>
  </ul>
</div>
</div>
<script>
var VIE = __VIE__;
var BARRE = __BARRE__;
var STORIE = __STORIE__;
function pulisci(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();}
function el(t,c,h){var e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function anni(r){var a=r.da,b=r.a;if(a===b)return a==='oggi'?'oggi':'mappa del '+a;
  return 'dal '+a+(b==='oggi'?' a oggi':' al '+b);}
function cronologia(v,compatta){
  var ul=el('ul','linea');ul.style.listStyle='none';
  v.righe.forEach(function(r){
    var li=el('li','');
    var tag='';
    if(r.esito==='vuoto'){li.className='vuoto';}
    else if(r.esito==='cambio'){li.className='cambia';tag='<span class="tag">cambia</span>';}
    else if(r.esito==='parziale'){tag='<span class="tag g">nome aggiunto o tolto</span>';}
    else if(r.esito==='nasce'){tag='<span class="tag g">la via nasce</span>';}
    var det='';
    if(r.varianti&&r.varianti.length&&!compatta){det='<div class="det">scritto anche: '+r.varianti.map(esc).join('; ')+'</div>';}
    li.innerHTML='<div class="anni">'+anni(r)+tag+'</div><div class="nome">'+esc(r.nome.trim())+'</div>'+det;
    ul.appendChild(li);
  });
  return ul;
}
function mostra(v){
  var s=document.getElementById('scheda');s.innerHTML='';
  s.appendChild(el('div','titolo',esc(v.oggi)));
  var f=v.n===0?'Nessun cambio di nome sulle mappe.':(v.n===1?'Ha cambiato nome una volta.':'Ha cambiato nome '+v.n+' volte.');
  s.appendChild(el('div','frase',f));
  s.appendChild(cronologia(v,false));
}
function cerca(){
  var q=pulisci(document.getElementById('q').value);var out=document.getElementById('sugg');out.innerHTML='';
  if(q.length<2)return;
  var tro=VIE.filter(function(v){return v.nomi.concat([v.oggi]).some(function(n){return pulisci(n).indexOf(q)>=0;});}).slice(0,6);
  if(!tro.length){out.appendChild(el('p','','Nessuna via trovata. Il dataset ha solo '+VIE.length+' vie.'));return;}
  tro.forEach(function(v){
    var b=el('button','',esc(v.oggi));b.type='button';
    var altro=v.nomi.filter(function(n){return pulisci(n).indexOf(q)>=0&&pulisci(n)!==pulisci(v.oggi);})[0];
    if(altro)b.innerHTML+='<small>nome vecchio: '+esc(altro.trim())+'</small>';
    b.onclick=function(){mostra(v);out.innerHTML='';document.getElementById('q').value='';};
    out.appendChild(b);
  });
}
document.getElementById('q').addEventListener('input',cerca);
(function(){
  var p=document.getElementById('prova');
  ['Viale Monte Grappa','Via Turati','Corso Italia','Via Festa del Perdono'].forEach(function(n){
    var v=VIE.filter(function(x){return x.oggi===n;})[0];if(!v)return;
    var b=el('button','',esc(n));b.type='button';b.onclick=function(){mostra(v);};p.appendChild(b);
  });
  mostra(VIE.filter(function(x){return x.oggi==='Viale Monte Grappa';})[0]);
  var max=Math.max.apply(null,BARRE.map(function(b){return b.n;}));
  var g=document.getElementById('grafico');
  BARRE.forEach(function(b){
    var d=el('div','bar');
    d.appendChild(el('div','et',b.da+' → '+b.a+'<small>'+b.anni+' anni</small>'));
    var t=el('div','tr');var i=el('i',b.n===max?'max':'');i.style.width=Math.max(b.n/max*150,b.n?4:0)+'px';
    t.appendChild(i);t.appendChild(el('b','',String(b.n)));d.appendChild(t);g.appendChild(d);
  });
  var S=document.getElementById('storie');
  STORIE.forEach(function(s){
    var v=VIE.filter(function(x){return x.id===s.id;})[0];
    var d=el('div','storia');d.appendChild(el('h3','',esc(s.oggi)));
    d.appendChild(el('p','',esc(s.frase)+(s.nota?' '+esc(s.nota):'')));
    d.appendChild(cronologia(v,true));S.appendChild(d);
  });
})();
</script>
</body>
</html>
"""

html = (PAGINA
        .replace("__VIE__", json.dumps(dati_vie, ensure_ascii=False))
        .replace("__BARRE__", json.dumps(barre))
        .replace("__STORIE__", json.dumps(storie, ensure_ascii=False))
        .replace("__NVIE__", str(n_vie)).replace("__NCAMBIO__", str(n_cambio)).replace("__NPIU__", str(n_piu))
        .replace("__TOT__", str(tot_cambi)).replace("__N3046__", str(n_30_46)).replace("__N1030__", str(n_10_30))
        .replace("__SALTI__", str(salti)).replace("__VIALI__", str(viali_porta))
        .replace("__ILLEG__", str(riep["celle_illeggibili"])).replace("__NONEX__", str(riep["celle_non_esistenti"])))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("scritto", OUT, len(html), "byte; viali di porta:", viali_porta)
