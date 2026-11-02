TITOLO = "Le comunità quartiere per quartiere"
CSS = ".chips{display:flex;flex-wrap:wrap;gap:6px;margin:.5em 0} .chips button{font:inherit;font-size:.85rem;border:1px solid var(--line);background:#fff;padding:2px 10px;border-radius:14px;cursor:pointer} .chips button.on{color:#fff;border-color:transparent} #yr{font-weight:700;min-width:3.2em;display:inline-block} th.so{cursor:pointer;user-select:none} th.so:hover{color:var(--ink)} #q{font:inherit;border:1px solid var(--line);border-radius:14px;padding:4px 10px;min-width:0;flex:1 1 180px;max-width:320px}"
BODY = """
<h1>Le comunità quartiere per quartiere</h1>
@@NAV@@
<p>L’anagrafe del Comune scrive, per ogni residente, la <b>cittadinanza</b>. Qui la guardiamo per i 88 quartieri di Milano (i NIL, Nuclei di Identità Locale) dal 1999 al 2025. Una parola di cautela, che vale per tutta la pagina: <b>cittadinanza, non origine</b>. Chi ha preso la cittadinanza italiana conta come «Italia»; i figli di stranieri nati a Milano hanno quasi sempre la cittadinanza dei genitori. Il dato dice quanti residenti hanno una certa cittadinanza, non da dove «vengono» né quanto una comunità sia «integrata».</p>

<div class="surp" id="sorpresa"><p class="sub">Caricamento…</p></div>

<div class="warm"><b>Prima di leggere.</b> Il registro del Comune ha più stranieri di quanti ne conti ISTAT dopo il censimento permanente: al 31/12/2025 <b>295.805</b> residenti con cittadinanza non italiana nel registro contro <b>267.986</b> per ISTAT al 1° gennaio 2026 (+10,4%); la quota sul totale sarebbe 21,1% contro 19,7%. I numeri di questa pagina sono quelli del registro. Vedi <a href="#limiti">i limiti dei dati</a>.</div>

<h2 id="mappa">La mappa, anno per anno</h2>
<p>Scegli una cittadinanza e muovi il cursore degli anni. Il colore dice la quota di residenti del quartiere con quella cittadinanza (o il loro numero). Clic su un quartiere per la scheda.</p>
<div class="ctl"><label class="sub" for="sel-cit">Cittadinanza:</label><select id="sel-cit" aria-label="Scegli una cittadinanza"></select>
<button type="button" data-m="q" class="on">Quota dei residenti</button><button type="button" data-m="n">Numero di residenti</button></div>
<div class="ctl"><span class="sub">Anno:</span><input type="range" id="rng" min="1999" max="2025" step="1" value="2025" aria-label="Anno"><span id="yr">2025</span><button type="button" id="play" aria-label="Avvia la sequenza degli anni">▶ anni</button></div>
<div class="ctl"><label class="sub" for="sel-nil">Il tuo quartiere:</label><select id="sel-nil" aria-label="Scegli un quartiere"></select></div>
<p class="sub" id="map-desc"></p>
<div id="map" class="map" role="img" aria-label="Mappa dei quartieri di Milano colorati per cittadinanza dei residenti"></div>
<div class="lgd" id="lg-map"></div>
<p class="src">Residenti al 31 dicembre di ogni anno, per quartiere e cittadinanza: Comune di Milano, «Popolazione: residenti per cittadinanza e quartiere (1999-2025)» (ds27, CC BY, scaricato il 1° novembre 2026). Mappa © OpenStreetMap contributors. I colori sono gli stessi per tutti gli anni (soglie calcolate su tutti gli anni insieme), così si vede il cambiamento. In grigio, nella mappa delle quote, i quartieri con meno di 3.000 residenti in quell’anno. Le 30 cittadinanze in elenco sono le più numerose nel 2025.</p>
<div id="scheda" class="card"><span class="sub">Scegli un quartiere sulla mappa o dall’elenco.</span></div>
<div id="nilcit" class="card" style="display:none"></div>

<h2 id="tutte">Tutte le cittadinanze di Milano</h2>
<div class="ctl"><label class="sub" for="sel-yr">Anno:</label><select id="sel-yr" aria-label="Anno"></select><span class="sub">(è lo stesso cursore della mappa)</span></div>
<div id="tutte-testo"></div>
<div class="ch" id="ch-dist" role="img" aria-label="Numero di cittadinanze straniere diverse presenti, 1999-2025"></div>
<div class="lgd" id="lg-dist"></div>
<div class="ctl"><label class="sub" for="q">Cerca:</label><input type="search" id="q" placeholder="per esempio: Perù" aria-label="Cerca una cittadinanza"><span class="sub" id="q-n"></span></div>
<div class="scroll tabmax"><table id="tab-tutte"></table></div>
<p class="src">Residenti con cittadinanza non italiana al 31 dicembre, tutte le voci del registro (ds27, Comune di Milano, CC BY, scaricato il 1° novembre 2026). Clic sulle intestazioni per ordinare. La variazione dal 1999 e dal 2011 è la differenza di residenti; «nuova» = nessun residente con quella cittadinanza nell’anno di partenza. Il file non raggruppa le cittadinanze per continente: non lo facciamo noi, per non inventare categorie. Le voci sono quelle dell’anagrafe e cambiano nel tempo («ex Jugoslavia», «Serbia», «Montenegro», «Kosovo»); «Altre nazioni o n.d.» e «Apolide» non sono paesi. Cittadinanza, non origine.</p>

<h2 id="classifica">Quali cittadinanze, e come cambiano</h2>
<div id="class-testo"></div>
<div class="chips" id="chips"></div>
<div class="ctl"><label class="sub" for="sel-add">Aggiungi:</label><select id="sel-add" aria-label="Aggiungi una cittadinanza al grafico"></select></div>
<div class="ch" id="ch-top" role="img" aria-label="Residenti per cittadinanza, 1999-2025"></div>
<p class="src">Residenti con ciascuna cittadinanza in tutta la città, al 31 dicembre (ds27, CC BY). Prima del 1999 (dal 1979) c’è solo il totale per cittadinanza della città: <a href="data/residenti_per_cittadinanza_citta.csv">residenti_per_cittadinanza_citta.csv</a> parte dal 1999; la serie dal 1979 è nel dataset ds74 del Comune.</p>
<h3>Le naturalizzazioni</h3>
<div id="nat-testo"></div>
<div class="ch" id="ch-nat" role="img" aria-label="Acquisizioni di cittadinanza italiana per anno"></div>
<div class="scroll"><table id="tab-nat"></table></div>
<p class="src">Acquisizioni della cittadinanza italiana a Milano: Comune di Milano ds221 (2003-2020) e ds1964 (2021-2024); per cittadinanza precedente ds1963 (2021-2024), CC BY, scaricati il 1° novembre 2026. Chi si naturalizza passa nel registro da «straniera» a «Italia»: una parte del calo di alcune cittadinanze (Filippine, Ecuador, dal 2023 Egitto) è questo, e non partenze.</p>

<h2 id="dove">Dove vivono: una cittadinanza, tanti quartieri</h2>
<div id="dove-testo"></div>
<div class="ch" id="ch-cina" role="img" aria-label="Residenti con cittadinanza cinese in tre quartieri, 1999-2025"></div>
<div class="lgd" id="lg-cina"></div>
<div class="scroll"><table id="tab-cina"></table></div>
<h3>Quanto sono concentrate le cittadinanze</h3>
<p>L’<b>indice di dissimilarità</b> (di Duncan) dice quale quota di una cittadinanza dovrebbe cambiare quartiere perché sia distribuita come tutti gli altri residenti. 0 = distribuzione uguale; 1 = quartieri completamente separati. Nel 2025:</p>
<div class="scroll"><table id="tab-conc"></table></div>
<p class="src">Calcolo nostro su ds27, 2025, sui 88 quartieri. La colonna «nei 5 quartieri» è la quota del gruppo che vive nei cinque NIL dove è più numeroso.</p>

<h2 id="diversita">Quartieri più e meno vari</h2>
<div id="div-testo"></div>
<div class="ctl"><span class="sub">Anno:</span><button type="button" data-y="1999">1999</button><button type="button" data-y="2011">2011</button><button type="button" data-y="2025" class="on">2025</button></div>
<div class="grid2"><div><p class="sub"><b>Meno vari</b> (numero effettivo di cittadinanze)</p><div class="bars" id="b-meno"></div></div>
<div><p class="sub"><b>Più vari</b></p><div class="bars" id="b-piu"></div></div></div>
<details><summary>Tutti i quartieri, per varietà</summary><div class="scroll tabmax"><table id="tab-div"></table></div></details>
<p class="src">Solo quartieri con almeno 3.000 residenti e 500 stranieri nell’anno. Il «numero effettivo» è 1 diviso la somma dei quadrati delle quote di ogni cittadinanza straniera: vuol dire quanti gruppi di uguale peso ci sarebbero. Calcolo nostro su ds27. Più stranieri non vuol dire più varietà: conta come sono divisi.</p>

<h2 id="ucraina">L’Ucraina nel 2022</h2>
<div id="ucr-testo"></div>
<div class="ch" id="ch-ucr" role="img" aria-label="Residenti con cittadinanza ucraina, 2010-2025"></div>

<h2 id="limiti">I limiti dei dati</h2>
<div class="warm"><ul>
<li><b>Cittadinanza non è origine.</b> Nel registro chi ottiene la cittadinanza italiana diventa «Italia» (7.660-9.021 persone l’anno nel 2022-2024). I figli di stranieri nati a Milano restano, nel registro, con la cittadinanza dei genitori. Non c’è il luogo di nascita. Le voci cambiano nome: «ex Jugoslavia», «Serbia», «Montenegro», «Kosovo» sono separate; «Altre nazioni o n.d.» esiste.</li>
<li><b>Il registro conta più persone di ISTAT.</b> Dal 2020 la differenza sul totale è tra +1,3% e +3,4%; per gli stranieri è +10,4% (2025). Nei quartieri il registro ha in media circa 3 punti di stranieri in più dei censimenti 2001 e 2011.</li>
<li><b>Salti nelle serie.</b> Il totale dei residenti cala di 53.857 persone tra il 2002 e il 2003 e cresce di 24.579 tra il 2011 e il 2012: sono con ogni probabilità revisioni del registro dopo i censimenti (ipotesi non verificata), non spostamenti. Vale anche per i singoli quartieri.</li>
<li><b>Quartieri piccoli e parchi.</b> 18 quartieri su 88 hanno meno di 3.000 residenti e sono esclusi dalle classifiche e in grigio sulla mappa delle quote.</li>
<li><b>Quartieri fuori scala.</b> A Comasina e a Monluè-Ponte Lambro le quote di stranieri sono molto alte (43,9% e 50,4% nel 2025). Il dato dice dove sono iscritti i residenti; non spiega il perché (forse residenze collettive, grandi condomini o altro: nessuna ipotesi è verificata). Un confronto con il secondo dataset del Comune (ds205) dà gli stessi numeri per Comasina.</li>
<li><b>I NIL prima del 2012.</b> I residenti del 1999-2011 sono assegnati ai quartieri di oggi; il dataset non spiega come. Il dataset ds205 del Comune, per le prime tre cittadinanze, coincide con ds27 nel 99,8% dei casi; i due casi diversi sono errori di ds205.</li>
<li><b>Niente giudizi.</b> Questa pagina non dice se una concentrazione sia «buona» o «cattiva», né se una comunità sia «integrata»: misura dove risiedono persone con una certa cittadinanza.</li>
</ul></div>

<h2 id="file">Fonti e file</h2>
<p><b>Fonti e licenze.</b> Comune di Milano, <a href="https://dati.comune.milano.it/">dati.comune.milano.it</a>: ds27 (residenti per cittadinanza e quartiere 1999-2025), ds74 (stranieri per cittadinanza dal 1979), ds221, ds1963, ds1964 (cittadinanza italiana acquisita), ds205 (controllo), confini dei NIL ds964; tutti Creative Commons Attribution (CC BY, versione non indicata dal portale), scaricati il 1° novembre 2026. ISTAT, <a href="https://demo.istat.it/">demo.istat.it</a>: popolazione straniera al 1° gennaio 2026 (STRASA), CC BY 4.0, scaricato il 30 ottobre 2026. Mappa: © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ODbL. Per i censimenti 1991-2023 per quartiere vedi <a href="../censimenti/">I censimenti di Milano</a>.</p>
<p>File: <a href="data/residenti_per_cittadinanza_nil.csv">residenti_per_cittadinanza_nil.csv</a> (le 30 cittadinanze, per quartiere e anno), <a href="data/residenti_per_cittadinanza_citta.csv">residenti_per_cittadinanza_citta.csv</a>, <a href="data/diversita_nil.csv">diversita_nil.csv</a>, <a href="data/nil.geojson">nil.geojson</a>, <a href="data/cittadinanze.json">cittadinanze.json</a>, <a href="data/cittadinanze_tutte.json">cittadinanze_tutte.json</a> (tutte le voci di cittadinanza, città, 1999-2025), <code>data/anno/&lt;anno&gt;.json</code> (tutte le cittadinanze per quartiere, un file per anno: <a href="data/anno/2025.json">2025</a>), <a href="data/riepilogo.json">riepilogo.json</a>.</p>
<footer><p>Altre pagine: <a href="../arrivi-partenze/">Chi arriva e chi lascia Milano</a> · <a href="../eta/">Età e centenari</a> · <a href="../censimenti/">I censimenti di Milano</a>. Programmi e note: <a href="https://github.com/AndreottiVIII/milano-in-dati">github.com/AndreottiVIII/milano-in-dati</a>.</p></footer>
"""
JS = r"""
var Z=null,RZ=null,NF=null,ANNI=[],IDX={},CUR='ALL',MET='q',YI=26,SEL=null,MAP=null,LAY=null,BR=[],TIMER=null;
var PAL=['#00695c','#c26a1b','#3a6ea5','#8e44ad','#b03a48','#6d6d6d','#2e7d32','#d4a017','#0b4f45','#7a5230'];
var T=null,YC={},TS={k:'n',d:-1},TQ='';
Promise.all([J('data/cittadinanze.json'),J('data/riepilogo.json'),J('data/nil.geojson'),J('data/cittadinanze_tutte.json')]).then(function(a){Z=a[0];RZ=a[1];NF=a[2];T=a[3];ANNI=Z.anni;ANNI.forEach(function(y,i){IDX[y]=i});
  try{sorpresa();mappa();tutteInit();classifica();dove();diversita();ucraina()}catch(e){console.error(e);setH('sorpresa','<b>Errore nella pagina.</b> '+esc(e.message))}
}).catch(function(e){setH('sorpresa','<b>Dati non caricati.</b> '+esc(e.message))});
function citBy(k){for(var i=0;i<Z.cit.length;i++)if(Z.cit[i].k===k)return Z.cit[i]}
function sorpresa(){var c=citBy('Cinese, Rep. Popolare'),cm=c.n['82'],sa=c.n['69'],vi=c.n['71'],r=Z.nil['82'].r,rs=Z.nil['69'].r,s82=Z.nil['82'].s;
  var h='<p><b>A Comasina il '+nf(100*cm[26]/r[26],1)+'% dei residenti ha cittadinanza cinese</b> ('+f0(cm[26])+' persone su '+f0(r[26])+', e più della metà degli stranieri del quartiere: '+nf(100*cm[26]/s82[26],1)+'%). Nel 1999 erano <b>'+cm[0]+'</b> persone, nel 2011 '+f0(cm[12])+'. A Sarpi, la «Chinatown» per eccellenza, sono '+f0(sa[26])+' ('+nf(100*sa[26]/rs[26],1)+'% dei residenti).</p>';
  h+='<p>Il quartiere con più residenti di cittadinanza cinese non è Sarpi ma <b>Villapizzone-Cagnola-Boldinasco</b> ('+f0(vi[26])+', il '+nf(100*vi[26]/Z.nil['71'].r[26],1)+'% dei suoi residenti): nell’ordine vengono poi Sarpi e Comasina. Nel 2025 in città sono '+f0(c.c[26])+' (7.516 nel 1999).</p>';
  h+='<p class="src">Residenti al 31/12/2025 per cittadinanza (ds27, Comune di Milano, CC BY). Cittadinanza, non origine; il registro ha più stranieri di ISTAT (<a href="#limiti">limiti dei dati</a>). Il secondo dataset del Comune (ds205) dà per Comasina 2.243 residenti con cittadinanza cinese nel 2024, come ds27.</p>';
  setH('sorpresa',h)}
/* ---- mappa ---- */
function valore(i,yi){var n=Z.nil[i];if(CUR==='ALL')return n.s[yi];var s=Z.cit_cur.n[i];return s?s[yi]:0}
function lbl(){return CUR==='ALL'?'cittadinanza non italiana':Z.cit_cur.l}
function misura(i,yi){var v=valore(i,yi),r=Z.nil[i].r[yi];if(MET==='n')return v;return r>=3000?100*v/r:null}
function calcolaSoglie(){Z.cit_cur=CUR==='ALL'?null:citBy(CUR);var all=[];Object.keys(Z.nil).forEach(function(i){for(var y=0;y<ANNI.length;y++){var m=misura(i,y);if(m!=null&&(MET==='q'||m>0))all.push(m)}});
  var b=qbreaks(all,6).map(function(v){return MET==='q'?Math.round(v*10)/10:Math.round(v)});BR=b.filter(function(v,i,a){return i===0||v>a[i-1]});if(!BR.length)BR=[1]}
function stile(f){var p=f.properties,m=misura(p.i,YI),sel=SEL===p.i;var c=m==null?'#bdbdbd':(m===0?'#f4f4f4':SEQ[Math.min(5,cls(m,BR)+(6-BR.length-1))]);return {fillColor:c,fillOpacity:.85,color:sel?'#000':'#fff',weight:sel?3:1}}
function mappa(){
  var sel=el('sel-cit');sel.innerHTML='<option value="ALL">Tutti gli stranieri (cittadinanza non italiana)</option>'+Z.cit.map(function(c){return '<option value="'+esc(c.k)+'">'+esc(c.l)+'</option>'}).join('');sel.value='Cinese, Rep. Popolare';CUR=sel.value;calcolaSoglie();
  MAP=baseMap('map');
  LAY=L.geoJSON(NF,{style:stile,onEachFeature:function(f,l){l.bindTooltip(function(){var p=f.properties,n=valore(p.i,YI),r=Z.nil[p.i].r[YI];return '<b>'+esc(p.n)+'</b><br>'+ANNI[YI]+': '+f0(n)+' residenti con '+esc(CUR==='ALL'?'cittadinanza non italiana':'cittadinanza '+Z.cit_cur.l)+(r>0?' su '+f0(r)+' ('+nf(100*n/r,1)+'%)':'')},{sticky:true});l.on('click',function(){scegli(f.properties.i,false)})}}).addTo(MAP);
  MAP.fitBounds(LAY.getBounds());setTimeout(function(){MAP.invalidateSize();MAP.fitBounds(LAY.getBounds())},500);
  var s2=el('sel-nil');s2.innerHTML='<option value="">— scegli —</option>'+NF.features.map(function(f){return f.properties}).sort(function(a,b){return a.n.localeCompare(b.n,'it')}).map(function(p){return '<option value="'+p.i+'">'+esc(p.n)+'</option>'}).join('');
  s2.addEventListener('change',function(){if(s2.value)scegli(parseInt(s2.value,10),true)});
  sel.addEventListener('change',function(){CUR=sel.value;ric(true)});
  Array.prototype.forEach.call(document.querySelectorAll('button[data-m]'),function(b){b.addEventListener('click',function(){MET=b.getAttribute('data-m');Array.prototype.forEach.call(document.querySelectorAll('button[data-m]'),function(x){x.classList.toggle('on',x===b)});ric(true)})});
  var r=el('rng');r.addEventListener('input',function(){YI=IDX[parseInt(r.value,10)];ric(false)});
  el('play').addEventListener('click',function(){if(TIMER){clearInterval(TIMER);TIMER=null;this.textContent='▶ anni';return}var b=this;b.textContent='■ ferma';if(YI>=26)YI=0;TIMER=setInterval(function(){YI++;if(YI>=26){clearInterval(TIMER);TIMER=null;b.textContent='▶ anni'}r.value=ANNI[YI];ric(false)},550)});
  ric(true)}
function ric(soglie){if(soglie)calcolaSoglie();LAY.setStyle(stile);el('yr').textContent=ANNI[YI];el('rng').value=ANNI[YI];if(el('sel-yr')&&T){el('sel-yr').value=ANNI[YI];tutte()}
  var pal=SEQ.slice(6-BR.length-1),t=[];
  for(var i=0;i<=BR.length;i++){var u=MET==='q'?'%':'';t.push(i===0?'meno di '+nf(BR[0],MET==='q'?1:0)+u:i===BR.length?nf(BR[i-1],MET==='q'?1:0)+u+' o più':nf(BR[i-1],MET==='q'?1:0)+u+' – '+nf(BR[i],MET==='q'?1:0)+u)}
  setH('lg-map',pal.map(function(c,i){return '<span><i style="background:'+c+'"></i>'+t[i]+'</span>'}).join('')+'<span><i style="background:#f4f4f4"></i>nessuno</span>'+(MET==='q'?'<span><i style="background:#bdbdbd"></i>meno di 3.000 residenti</span>':''));
  var cit=CUR==='ALL'?'residenti con cittadinanza non italiana':'residenti con cittadinanza '+Z.cit_cur.l.toLowerCase();var tot=CUR==='ALL'?Z.citta.stranieri[YI]:Z.cit_cur.c[YI];
  setH('map-desc',ANNI[YI]+': '+f0(tot)+' '+cit+' in tutta la città ('+nf(100*tot/Z.citta.totale[YI],1)+'% dei residenti). '+(MET==='q'?'Colore = quota dei residenti del quartiere.':'Colore = numero di residenti.'));
  if(SEL)scheda(SEL)}
function scegli(i,zoom){SEL=i;el('sel-nil').value=String(i);LAY.setStyle(stile);LAY.eachLayer(function(l){if(l.feature.properties.i===i){l.bringToFront();if(zoom)MAP.fitBounds(l.getBounds(),{maxZoom:14})}});scheda(i)}
function scheda(i){var n=Z.nil[i],pts=[],pc=[];
  for(var y=0;y<ANNI.length;y++){var v=valore(i,y),r=n.r[y];pts.push([ANNI[y],MET==='q'?(r>=3000?100*v/r:null):v]);pc.push([ANNI[y],100*(CUR==='ALL'?Z.citta.stranieri[y]:Z.cit_cur.c[y])/Z.citta.totale[y]])}
  var v=valore(i,YI),r=n.r[YI],s=n.s[YI];
  setH('scheda','<h3>'+esc(n.n)+'</h3><p>Nel '+ANNI[YI]+': <b>'+f0(r)+'</b> residenti, di cui <b>'+f0(s)+'</b> con cittadinanza non italiana ('+nf(r?100*s/r:0,1)+'%).'+(CUR==='ALL'?'':' Con cittadinanza '+esc(Z.cit_cur.l.toLowerCase())+': <b>'+f0(v)+'</b> ('+nf(r?100*v/r:0,1)+'% dei residenti, '+(s?nf(100*v/s,1):'0')+'% degli stranieri del quartiere).')+'</p><div class="ch" id="ch-sch"></div><p class="sub">'+esc(lbl())+(MET==='q'?', quota dei residenti del quartiere (linea continua) e della città (tratteggio)':', numero di residenti nel quartiere')+'. Dal 1999 al 2025.</p>');
  nilcit(i);
  var ser=[{n:n.n,c:ACC,pts:pts}];if(MET==='q')ser.push({n:'Tutta la città',c:GRY,dash:1,pts:pc});
  lineChart('ch-sch',{series:ser,xmin:1999,xmax:2025,xt:[2000,2005,2010,2015,2020,2025],ymin:0,h:200,yf:MET==='q'?function(v){return nf(v,1)+'%'}:f0})}
/* ---- classifica ---- */
var SHOW=[];
function classifica(){var tops=Z.cit.slice(0,10).map(function(c){return c.k});SHOW=tops.slice();
  var E=citBy('Egitto'),F=citBy('Filippine'),C=citBy('Cinese, Rep. Popolare');
  setH('class-testo','<p>Nel 2025 le prime cittadinanze straniere per numero di residenti sono <b>Egitto '+f0(E.c[26])+', Cina '+f0(C.c[26])+', Filippine '+f0(F.c[26])+'</b>, poi Perù '+f0(citBy('Perù').c[26])+', Sri Lanka '+f0(citBy('Sri Lanka (ex Ceylon)').c[26])+', Romania '+f0(citBy('Romania').c[26])+', Bangladesh '+f0(citBy('Bangladesh').c[26])+' e Ucraina '+f0(citBy('Ucraina').c[26])+'.</p><p><b>Dal 2021 la prima è l’Egitto</b>: nel 2020 le Filippine ne avevano '+f0(F.c[21])+' contro '+f0(E.c[21])+', nel 2021 '+f0(F.c[22])+' contro '+f0(E.c[22])+'. Le Filippine erano prime dal 1999 (16.472 contro 11.842) e hanno il massimo nel 2018 ('+f0(F.c[19])+'); l’Egitto ha il massimo nel 2023 ('+f0(E.c[24])+') e scende a '+f0(E.c[26])+' nel 2025. La Cina cresce di cinque volte dal 1999 ('+f0(C.c[0])+' → '+f0(C.c[26])+'). L’Ecuador scende da '+f0(citBy('Ecuador').c[12])+' (2011) a '+f0(citBy('Ecuador').c[26])+'. In totale gli stranieri sono '+f0(Z.citta.stranieri[0])+' nel 1999 ('+nf(100*Z.citta.stranieri[0]/Z.citta.totale[0],1)+'%) e '+f0(Z.citta.stranieri[26])+' nel 2025 ('+nf(100*Z.citta.stranieri[26]/Z.citta.totale[26],1)+'%); le persone con cittadinanza italiana sono invece '+f0(Z.citta.italia[0])+' e '+f0(Z.citta.italia[26])+'.</p>');
  var add=el('sel-add');add.innerHTML='<option value="">— altre cittadinanze —</option>'+Z.cit.slice(10).map(function(c){return '<option value="'+esc(c.k)+'">'+esc(c.l)+'</option>'}).join('');
  add.addEventListener('change',function(){if(add.value&&SHOW.indexOf(add.value)<0){SHOW.push(add.value);chips();ch()}add.value=''});
  function chips(){setH('chips',SHOW.map(function(k,i){var on=true;return '<button type="button" data-k="'+esc(k)+'" class="on" style="background:'+PAL[i%PAL.length]+'">'+esc(citBy(k).l)+' ✕</button>'}).join(''));
    Array.prototype.forEach.call(document.querySelectorAll('#chips button'),function(b){b.addEventListener('click',function(){var k=b.getAttribute('data-k');SHOW=SHOW.filter(function(x){return x!==k});chips();ch()})})}
  function ch(){lineChart('ch-top',{series:SHOW.map(function(k,i){var c=citBy(k);return {n:c.l,c:PAL[i%PAL.length],dash:i>=10,pts:c.c.map(function(v,j){return [ANNI[j],v]})}}),xmin:1999,xmax:2025,xt:[2000,2005,2010,2015,2020,2025],ymin:0,h:340,marks:[{x:2021,t:'Egitto supera Filippine'}],yf:f0,ml:56})}
  chips();ch();
  var nat=RZ.naturalizzazioni,ys=Object.keys(nat).map(Number).sort(),v=ys.map(function(y){return nat[y]});
  setH('nat-testo','<p>Ogni anno qualche migliaio di residenti stranieri diventa cittadino italiano: da 730 nel 2003 a <b>'+f0(nat[2016])+' nel 2016</b>, 2.279 nel 2020 e <b>'+f0(nat[2024])+' nel 2024</b>. Per le cittadinanze più numerose, dal 2021 al 2024 hanno preso la cittadinanza italiana '+f0(RZ.naturalizzazioni_per_cittadinanza_2021_2024['Egitto'])+' residenti con cittadinanza egiziana, '+f0(RZ.naturalizzazioni_per_cittadinanza_2021_2024['Filippine'])+' filippina, '+f0(RZ.naturalizzazioni_per_cittadinanza_2021_2024['Perù'])+' peruviana e '+f0(RZ.naturalizzazioni_per_cittadinanza_2021_2024['Ecuador'])+' ecuadoriana. Nel registro diventano «Italia»: sono una parte, non l’intera spiegazione, del calo dei gruppi.</p>');
  colChart('ch-nat',{cats:ys,series:[{n:'Acquisizioni di cittadinanza italiana',c:ACC,v:v}],h:220,yf:f0,step:3});
  var np=RZ.naturalizzazioni_per_cittadinanza_2021_2024;table('tab-nat',['Cittadinanza precedente','Acquisizioni 2021-2024'],Object.keys(np).map(function(k){return [esc(k),f0(np[k])]}))}
/* ---- dove ---- */
function dove(){var c=citBy('Cinese, Rep. Popolare'),ks=[['82','Comasina',WARM],['69','Sarpi',ACC],['71','Villapizzone-Cagnola-Boldinasco','#3a6ea5']];
  setH('dove-testo','<p>Un esempio: le persone con cittadinanza cinese in tre quartieri. <b>Sarpi</b> è il caso noto: '+f0(c.n['69'][0])+' nel 1999, '+f0(c.n['69'][12])+' nel 2011, '+f0(c.n['69'][26])+' nel 2025. Ma altrove il numero cresce più in fretta: <b>Comasina</b> passa da '+c.n['82'][0]+' a '+f0(c.n['82'][26])+', <b>Villapizzone-Cagnola-Boldinasco</b> da '+f0(c.n['71'][0])+' a '+f0(c.n['71'][26])+'. I dati non spiegano le ragioni: dicono dove i residenti sono iscritti.</p>');
  setH('lg-cina',lgd(ks.map(function(k){return {c:k[2],t:k[1]}})));
  lineChart('ch-cina',{series:ks.map(function(k){return {n:k[1],c:k[2],pts:c.n[k[0]].map(function(v,j){return [ANNI[j],v]})}}),xmin:1999,xmax:2025,xt:[2000,2005,2010,2015,2020,2025],ymin:0,h:260,yf:f0,ml:50});
  table('tab-cina',['Quartiere (2025)','Residenti','Con cittadinanza cinese','% dei residenti','% degli stranieri'],ks.map(function(k){var n=Z.nil[k[0]],v=c.n[k[0]][26];return [esc(k[1]),f0(n.r[26]),f0(v),nf(100*v/n.r[26],1)+'%',nf(100*v/n.s[26],1)+'%']}));
  table('tab-conc',['Cittadinanza','Residenti 2025','Dissimilarità','Nei 5 quartieri'],RZ.concentrazione_2025.map(function(r){return [esc(r.l),f0(r.n),nf(r.d,2),f0(r.t5)+'%']}))}
/* ---- diversita ---- */
function diversita(){setH('div-testo','<p>Quanto è variata la composizione per cittadinanza degli stranieri di un quartiere? Se tutti avessero la stessa cittadinanza il numero effettivo sarebbe 1; se ce ne fossero 20 di peso uguale sarebbe 20. Nel 2025 il quartiere <b>meno vario</b> è <b>Comasina</b> (3,2: il 53,7% degli stranieri ha cittadinanza cinese), seguito da Sarpi (5,2; Cina 42,3%) e San Siro (6,0; Egitto 37,0%); i <b>più vari</b> sono Porta Vigentina-Porta Lodovica (30,7), Brera (29,0) e Porta Ticinese-Conca del Naviglio (27,1), dove nessun gruppo supera il 10%. Più stranieri non vuol dire più varietà: Comasina ha una delle quote di stranieri più alte (43,9%) e la varietà più bassa; Brera il 19,4% e la più alta.</p><p>Nel 1999 il quartiere meno vario era Stadio-Ippodromi (5,9; Francia 38% degli stranieri); nel 2011 Sarpi (6,8).</p>');
  var Y='2025';
  function draw(){var L=RZ.diversita[Y],lo=L.slice(0,8),hi=L.slice(-8).reverse(),mx=Math.max.apply(null,hi.map(function(r){return r.ne}));
    hbars('b-meno',lo.map(function(r){return {nm:r.n,v:r.ne,txt:nf(r.ne,1)+' <span class="sub">'+esc(r.top)+' '+f0(r.tq)+'%</span>',t:r.n}}),{max:mx});
    hbars('b-piu',hi.map(function(r){return {nm:r.n,v:r.ne,txt:nf(r.ne,1)+' <span class="sub">'+esc(r.top)+' '+f0(r.tq)+'%</span>',t:r.n,c:'#136459'}}),{max:mx});
    table('tab-div',['Quartiere '+Y,'Varietà (n. effettivo)','Stranieri','% stranieri','Prima cittadinanza (quota sugli stranieri)'],L.map(function(r){return [esc(r.n),nf(r.ne,1),f0(r.str),nf(r.qs,1)+'%',esc(r.top)+' '+nf(r.tq,1)+'%']}))}
  Array.prototype.forEach.call(document.querySelectorAll('button[data-y]'),function(b){b.addEventListener('click',function(){Y=b.getAttribute('data-y');Array.prototype.forEach.call(document.querySelectorAll('button[data-y]'),function(x){x.classList.toggle('on',x===b)});draw()})});
  draw()}
/* ---- ucraina ---- */
function ucraina(){var u=citBy('Ucraina').c;
  setH('ucr-testo','<p>Con la guerra del febbraio 2022 ci si aspetterebbe un salto. Nel registro dei residenti, invece: <b>8.530</b> persone con cittadinanza ucraina a fine 2021, <b>8.817</b> a fine 2022 (<b>solo +287</b>), 9.704 nel 2023, 9.865 nel 2024, 9.811 nel 2025. Il registro conta le persone <i>residenti</i>; chi è arrivato con la protezione temporanea può non avere (ancora) la residenza a Milano. È un’ipotesi: i dati non lo dicono.</p>');
  lineChart('ch-ucr',{series:[{n:'Cittadinanza ucraina',c:ACC,pts:u.map(function(v,j){return [ANNI[j],v]}).filter(function(p){return p[0]>=2010})}],xmin:2010,xmax:2025,xt:[2010,2013,2016,2019,2022,2025],ymin:0,h:240,yf:f0,marks:[{x:2022,t:'2022'}]})}

/* ---- tutte le cittadinanze: citta' ---- */
function tutteInit(){var sel=el('sel-yr');sel.innerHTML=ANNI.slice().reverse().map(function(y){return '<option value="'+y+'">'+y+'</option>'}).join('');sel.value=ANNI[YI];
  sel.addEventListener('change',function(){YI=IDX[parseInt(sel.value,10)];ric(false)});
  el('q').addEventListener('input',function(){TQ=this.value.trim().toLowerCase();tutte()});
  setH('lg-dist',lgd([{c:ACC,t:'Cittadinanze straniere diverse presenti'},{c:GRY,t:'Senza «Altre nazioni o n.d.» e «Apolide»',dash:1}]));
  lineChart('ch-dist',{series:[{n:'Cittadinanze diverse',c:ACC,pts:T.distinte.map(function(v,j){return [ANNI[j],v]})},{n:'Senza le voci generiche',c:GRY,dash:1,pts:T.distinte_senza_generiche.map(function(v,j){return [ANNI[j],v]})}],xmin:1999,xmax:2025,xt:[2000,2005,2010,2015,2020,2025],ymin:140,ymax:180,h:200,yf:f0,ml:44});
  tutte()}
function tutte(){var y=YI,Y=ANNI[y],tot=Z.citta.totale[y],st=Z.citta.stranieri[y];
  var rows=T.cit.map(function(c){var n=c.c[y];return {l:c.l,k:c.k,n:n,pf:st?100*n/st:0,pr:100*n/tot,d99:n-c.c[0],d11:n-c.c[12],n99:c.c[0],n11:c.c[12]}}).filter(function(r){return r.n>0});
  var nuove=0,sparite=0;T.cit.forEach(function(c){if(c.c[y]>0&&c.c[0]===0)nuove++;if(c.c[0]>0&&c.c[y]===0)sparite++});
  var di=T.distinte[y],dg=T.distinte_senza_generiche[y];
  setH('tutte-testo','<p>Nel <b>'+Y+'</b> il registro del Comune ha <b>'+f0(st)+'</b> residenti con cittadinanza non italiana ('+nf(100*st/tot,1)+'% dei '+f0(tot)+' residenti), divisi in <b>'+di+' cittadinanze diverse</b> ('+dg+' senza contare le voci generiche «Altre nazioni o n.d.» e «Apolide»). Nel 1999 erano <b>'+T.distinte[0]+'</b> ('+T.distinte_senza_generiche[0]+' senza le voci generiche) e nel 2011 '+T.distinte[12]+'. '+(Y>1999?'Rispetto al 1999 ci sono '+nuove+' voci che allora non avevano residenti e '+sparite+' che non ne hanno più: in parte sono cambi di nome o di confini (ex Jugoslavia, Serbia, Montenegro, Kosovo e simili). ':'')+'Le ultime voci della lista hanno pochissimi residenti ciascuna.</p>');
  var q=TQ,list=q?rows.filter(function(r){return r.l.toLowerCase().indexOf(q)>=0||r.k.toLowerCase().indexOf(q)>=0}):rows;
  var k=TS.k,d=TS.d;list.sort(function(a,b){var c=k==='l'?a.l.localeCompare(b.l,'it'):(a[k]-b[k]);return d>0?c:-c});
  function dl(v,base,ok){if(!ok)return '<span class="sub">—</span>';return base===0?'<b>'+sg(v)+'</b> <span class="sub">nuova</span>':sg(v)}
  var H=[['l','Cittadinanza'],['n','Residenti'],['pf','% degli stranieri'],['pr','% dei residenti'],['d99','Variazione dal 1999'],['d11','Variazione dal 2011']];
  el('tab-tutte').innerHTML='<thead><tr>'+H.map(function(h,i){return '<th class="so'+(i?' r':'')+'" data-s="'+h[0]+'" title="Ordina">'+h[1]+(TS.k===h[0]?(TS.d<0?' ▼':' ▲'):'')+'</th>'}).join('')+'</tr></thead><tbody>'+list.map(function(r){return '<tr><td>'+esc(r.l)+'</td><td class="r">'+f0(r.n)+'</td><td class="r">'+nf(r.pf,r.pf<1?2:1)+'%</td><td class="r">'+nf(r.pr,r.pr<0.1?3:2)+'%</td><td class="r">'+dl(r.d99,r.n99,Y>1999)+'</td><td class="r">'+dl(r.d11,r.n11,Y>2011)+'</td></tr>'}).join('')+'</tbody>';
  Array.prototype.forEach.call(el('tab-tutte').querySelectorAll('th.so'),function(th){th.addEventListener('click',function(){var s=th.getAttribute('data-s');if(TS.k===s)TS.d=-TS.d;else{TS.k=s;TS.d=s==='l'?1:-1}tutte()})});
  el('q-n').textContent=list.length+' di '+rows.length+' cittadinanze'}
/* ---- un quartiere: tutte le cittadinanze ---- */
function loadY(y){return YC[y]?Promise.resolve(YC[y]):J('data/anno/'+y+'.json').then(function(d){YC[y]=d;return d})}
function nilcit(i){var Y=ANNI[YI],box=el('nilcit');box.style.display='';box.innerHTML='<p class="sub">Caricamento…</p>';
  loadY(Y).then(function(D){if(SEL!==i||ANNI[YI]!==Y)return;var l=D.n[String(i)]||[],n=Z.nil[i],r=n.r[YI],s=n.s[YI],sh=l.map(function(x){return {c:T.cit[x[0]],n:x[1]}});
    if(!l.length){box.innerHTML='<h3>'+esc(n.n)+', '+Y+': cittadinanze</h3><p>Nessun residente con cittadinanza non italiana in questo quartiere nel '+Y+'.</p>';return}
    var top=sh.slice(0,15),rest=sh.slice(15),mx=top[0].n;
    function rows(a){return a.map(function(x){return {nm:x.c.l,nmh:esc(x.c.l)+'<br><span class="sub">'+nf(100*x.n/s,1)+'% degli stranieri · '+nf(100*x.n/r,x.n/r<0.001?2:1)+'% dei residenti</span>',v:x.n,txt:f0(x.n),t:x.c.l}})}
    box.innerHTML='<h3>'+esc(n.n)+', '+Y+': tutte le cittadinanze</h3><p><b>'+f0(s)+'</b> residenti con cittadinanza non italiana ('+nf(r?100*s/r:0,1)+'% di '+f0(r)+'), divisi in <b>'+l.length+' cittadinanze diverse</b> (la prima, '+esc(top[0].c.l)+', è il '+nf(100*top[0].n/s,1)+'% degli stranieri). Cittadinanza, non origine.</p><div class="bars" id="b-nc"></div>'+(rest.length?'<details><summary>Altre '+rest.length+' cittadinanze (da '+f0(rest[0].n)+' a '+f0(rest[rest.length-1].n)+' residenti)</summary><div class="bars" id="b-nc2"></div></details>':'')+'<p class="sub">Prime 15 per numero di residenti. Fonte: ds27, Comune di Milano, CC BY.</p>';
    hbars('b-nc',rows(top),{max:mx});if(rest.length)hbars('b-nc2',rows(rest),{max:mx})}).catch(function(e){box.innerHTML='<p class="sub">Dati non caricati: '+esc(e.message)+'</p>'})}
"""
