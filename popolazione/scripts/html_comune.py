"""Parti comuni (CSS e funzioni JS) delle tre pagine popolazione. Usato da pagine_html.py. Stesso stile di docs/alberi/index.html."""

HEAD = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milano in dati · @@TITOLO@@</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
:root{--acc:#00695c;--ink:#111;--bg:#fff;--mut:#666;--line:#ddd;--soft:#eef6f4;--warm:#8a4a10;--warmbg:#fbf0e2}
*{box-sizing:border-box} body{margin:0;font:16px/1.5 system-ui,Arial,sans-serif;color:var(--ink);background:var(--bg)}
main{max-width:980px;margin:0 auto;padding:16px;overflow-wrap:break-word} h1{font-size:1.7rem;margin:.6em 0 .2em} h2{font-size:1.2rem;margin:1.8em 0 .4em;border-top:2px solid var(--ink);padding-top:.6em} h3{font-size:1rem;margin:1.2em 0 .3em}
table{border-collapse:collapse;width:100%} th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top} th{font-size:.85rem;color:var(--mut);font-weight:600}
td.r,th.r{text-align:right;white-space:nowrap}
.sub{font-size:.85rem;color:var(--mut)} .src{font-size:.8rem;color:var(--mut);margin:.3em 0 .8em} a{color:var(--acc)} code{font-size:.9em}
.surp{border-left:4px solid var(--acc);background:var(--soft);padding:8px 12px;margin:.8em 0} .surp p{margin:.4em 0;font-size:1.05rem} .surp b{color:var(--acc)}
.warn{background:var(--soft);border-left:4px solid var(--acc);padding:6px 10px;margin:.6em 0;font-size:.92rem}
.warm{background:var(--warmbg);border-left:4px solid #c26a1b;padding:6px 10px;margin:.6em 0;font-size:.92rem} .warm ul{margin:.3em 0;padding-left:1.2em} .warm li{margin:.2em 0}
.map{height:62vh;min-height:340px;border:1px solid var(--ink)} .map .leaflet-tile-pane{filter:grayscale(1) brightness(1.08) contrast(.85)}
.ctl{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:.5em 0}
.ctl button,.ctl select{font:inherit;border:1px solid var(--line);background:#fff;color:var(--ink);padding:4px 10px;border-radius:14px;cursor:pointer;max-width:100%}
.ctl button.on{border-color:var(--acc);color:var(--acc);font-weight:700}
.ctl input[type=range]{flex:1 1 200px;min-width:140px;max-width:100%}
.lgd{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.85rem;margin:.5em 0} .lgd span{white-space:nowrap} .lgd i{display:inline-block;width:16px;height:12px;vertical-align:-1px;margin-right:4px;border:1px solid #888}
.lgd i.ln{height:0;border:0;border-top:3px solid;vertical-align:3px;width:22px} .lgd i.ln.d{border-top-style:dashed}
.scroll{overflow-x:auto} .card{border:1px solid var(--line);padding:8px 12px;margin:.6em 0}
.card h3{margin:.1em 0 .1em} .card table td,.card table th{padding:3px 6px}
.bars{margin:.4em 0} .bars .row{display:grid;grid-template-columns:minmax(100px,40%) 1fr 92px;gap:6px;align-items:center;font-size:.88rem;padding:2px 0}
.bars .nm{line-height:1.2;overflow-wrap:anywhere} .bars .tr{background:#f1f1f1;height:10px;position:relative} .bars .fill{display:block;height:10px;background:var(--acc)}
.bars .v{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.bars.dv .tr .fill{position:absolute;top:0} .bars.dv .tr:after{content:"";position:absolute;left:50%;top:-2px;height:14px;border-left:1px solid #666}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 24px} @media(max-width:760px){.grid2{grid-template-columns:1fr} th,td{padding:5px 4px;font-size:.88rem} }
.ch{position:relative;width:100%} .ch svg{display:block;width:100%;font:11px system-ui,Arial,sans-serif} .ch svg text{fill:#111} .ch svg .mu{fill:#666}
.tip{position:absolute;pointer-events:none;background:#fff;border:1px solid #888;padding:4px 8px;font-size:.8rem;line-height:1.35;white-space:nowrap;z-index:5;box-shadow:0 1px 4px rgba(0,0,0,.15)}
details{margin:.4em 0} summary{cursor:pointer;color:var(--acc)} ul.m li{margin:.35em 0}
footer{margin:2.5em 0 1em;font-size:.82rem;color:var(--mut);border-top:1px solid var(--line);padding-top:.8em}
.leaflet-tooltip{font:13px system-ui,Arial,sans-serif}
.tabmax{max-height:340px;overflow:auto}
@media(max-width:760px){.bars .row{grid-template-columns:minmax(80px,32%) 1fr auto} .bars .v{white-space:normal;max-width:150px}} .bars .row>*{min-width:0}
.nav3{font-size:.9rem;margin:.2em 0 .8em} .nav3 a{margin-right:12px}
@@CSS_EXTRA@@
</style><script src="../menu.js" defer></script></head><body><main>
"""

JS_COMUNE = r"""
var ACC='#00695c',WARM='#c26a1b',GRY='#8a8a8a';
var SEQ=['#d7ece7','#a6d3ca','#62b0a4','#2b8a7d','#136459','#052e29'];
var DIVC=['#a8540f','#d98a43','#eeeeee','#bfe0d8','#7dbdb0','#2b8a7d','#0b4f45'];
var RD=[];
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function nf(x,d){return x==null?'':Number(x).toLocaleString('it-IT',{minimumFractionDigits:d,maximumFractionDigits:d})}
function f0(x){return x==null?'':Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')}
function f1(x){return nf(x,1)}
function sg(x,d){if(x==null)return '';var v=Math.abs(x);return (x<0?'−':(x>0?'+':''))+(d?nf(v,d):f0(v))}
function J(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.json()})}
function el(id){return document.getElementById(id)}
function setH(id,h){el(id).innerHTML=h}
function table(id,head,rows){setH(id,'<thead><tr>'+head.map(function(h,i){return '<th'+(i?' class="r"':'')+'>'+h+'</th>'}).join('')+'</tr></thead><tbody>'+rows.map(function(r){return '<tr>'+r.map(function(c,i){return '<td'+(i?' class="r"':'')+'>'+c+'</td>'}).join('')+'</tr>'}).join('')+'</tbody>')}
function niceStep(r){var p=Math.pow(10,Math.floor(Math.log(r)/Math.LN10)),f=r/p;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p}
function sum(a){var s=0;for(var i=0;i<a.length;i++)s+=a[i]||0;return s}
function lgd(items){return items.map(function(it){return '<span><i class="ln'+(it.dash?' d':'')+'" style="border-top-color:'+it.c+'"></i>'+it.t+'</span>'}).join('')}
function lgdBox(items){return items.map(function(it){return '<span><i style="background:'+it.c+'"></i>'+it.t+'</span>'}).join('')}
/* barre orizzontali (anche divergenti) */
function hbars(id,rows,o){o=o||{};var mx=o.max||Math.max.apply(null,rows.map(function(r){return Math.abs(r.v)}))||1;
  setH(id,rows.map(function(r){var col=r.c||(o.dv&&r.v<0?WARM:ACC);var w=Math.abs(r.v)/mx*(o.dv?50:100);
    return '<div class="row"><span class="nm" title="'+esc(r.t||r.nm)+'">'+(r.nmh||esc(r.nm))+'</span><span class="tr"><span class="fill" style="width:'+w+'%;background:'+col+(o.dv?(';'+(r.v<0?'right:50%':'left:50%')):'')+'"></span></span><span class="v">'+r.txt+'</span></div>'}).join(''))}
/* grafico SVG: tooltip e guida */
function mkSvg(box,W,H){box.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img"></svg><div class="tip" style="display:none"></div>';return box.firstChild}
function S(tag,at,txt){var e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(var k in at)e.setAttribute(k,at[k]);if(txt!=null)e.textContent=txt;return e}
function yTicks(lo,hi,n){var st=niceStep((hi-lo)/(n||5)),t=[],v=Math.ceil(lo/st)*st;for(;v<=hi+1e-9;v+=st)t.push(Math.round(v*1e6)/1e6);return t}
/* grafico a linee. o: series[{n,c,dash,pts:[[x,y]],w}], xmin,xmax,ymin,ymax,yf,xf,h,marks[{x,t}],xt */
function lineChart(boxId,o){var box=el(boxId);var W=Math.max(300,box.clientWidth),H=o.h||300,m={l:o.ml||50,r:12,t:12,b:26};
  var ymin=o.ymin,ymax=o.ymax;if(ymin==null||ymax==null){var a=[];o.series.forEach(function(s){s.pts.forEach(function(p){if(p[1]!=null)a.push(p[1])})});ymin=ymin==null?Math.min(0,Math.min.apply(null,a)):ymin;ymax=ymax==null?Math.max.apply(null,a):ymax;ymax+= (ymax-ymin)*.04}
  var yt=yTicks(ymin,ymax,5);var xs=function(x){return m.l+(x-o.xmin)/(o.xmax-o.xmin)*(W-m.l-m.r)},ys=function(y){return H-m.b-(y-ymin)/(ymax-ymin)*(H-m.t-m.b)};
  var svg=mkSvg(box,W,H);
  yt.forEach(function(v){svg.appendChild(S('line',{x1:m.l,x2:W-m.r,y1:ys(v),y2:ys(v),stroke:v===0?'#666':'#e4e4e4'}));svg.appendChild(S('text',{x:m.l-6,y:ys(v)+4,'text-anchor':'end',class:'mu'},(o.yf||f0)(v)))});
  (o.xt||[]).forEach(function(v){svg.appendChild(S('text',{x:xs(v),y:H-8,'text-anchor':'middle',class:'mu'},(o.xf||String)(v)))});
  (o.marks||[]).forEach(function(mk){var x=xs(mk.x);svg.appendChild(S('line',{x1:x,x2:x,y1:m.t,y2:H-m.b,stroke:'#c26a1b','stroke-dasharray':'3 3'}));svg.appendChild(S('text',{x:x+3,y:m.t+9,class:'mu'},mk.t))});
  o.series.forEach(function(s){var d='',pen=false;s.pts.forEach(function(p){if(p[1]==null){pen=false;return}d+=(pen?'L':'M')+xs(p[0]).toFixed(1)+' '+ys(p[1]).toFixed(1);pen=true});
    svg.appendChild(S('path',{d:d,fill:'none',stroke:s.c,'stroke-width':s.w||2,'stroke-dasharray':s.dash?'5 4':'none','stroke-linejoin':'round'}))});
  var gl=S('line',{y1:m.t,y2:H-m.b,stroke:'#555',display:'none'});svg.appendChild(gl);var rect=S('rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'transparent'});svg.appendChild(rect);var tip=box.lastChild;
  function show(ev){var r=svg.getBoundingClientRect(),k=W/r.width,t=ev.touches?ev.touches[0]:ev,mx=(t.clientX-r.left)*k;var x=Math.round(o.xmin+(mx-m.l)/(W-m.l-m.r)*(o.xmax-o.xmin));if(o.xstep)x=Math.round(x/o.xstep)*o.xstep;x=Math.max(o.xmin,Math.min(o.xmax,x));
    var h='<b>'+(o.xtip?o.xtip(x):x)+'</b>';o.series.forEach(function(s){var p=null;for(var i=0;i<s.pts.length;i++)if(s.pts[i][0]===x)p=s.pts[i];if(p&&p[1]!=null)h+='<br><span style="color:'+s.c+'">■</span> '+esc(s.n)+': '+(o.tf||o.yf||f0)(p[1])});
    gl.setAttribute('x1',xs(x));gl.setAttribute('x2',xs(x));gl.removeAttribute('display');tip.innerHTML=h;tip.style.display='';var tw=tip.offsetWidth,left=xs(x)/k+10;if(left+tw>r.width)left=xs(x)/k-tw-10;if(left<0)left=0;tip.style.left=left+'px';tip.style.top='6px'}
  function hide(){tip.style.display='none';gl.setAttribute('display','none')}
  rect.addEventListener('mousemove',show);rect.addEventListener('mouseleave',hide);rect.addEventListener('touchstart',show,{passive:true});rect.addEventListener('touchmove',show,{passive:true});
  box._f=function(){lineChart(boxId,o)};if(RD.indexOf(box)<0)RD.push(box);
}
/* istogramma a colonne raggruppate con valori negativi. o: cats[], series[{n,c,v[]}], yf,h,bands[{i0,i1,t}], tf */
function colChart(boxId,o){var box=el(boxId);var W=Math.max(300,box.clientWidth),H=o.h||300,m={l:o.ml||50,r:10,t:o.bands?26:12,b:26};
  var all=[];o.series.forEach(function(s){s.v.forEach(function(v){if(v!=null)all.push(v)})});var lo=Math.min(0,Math.min.apply(null,all)),hi=Math.max(0,Math.max.apply(null,all));hi+=(hi-lo)*.04;lo-= (hi-lo)*.02;
  var n=o.cats.length,pw=(W-m.l-m.r)/n,ys=function(y){return H-m.b-(y-lo)/(hi-lo)*(H-m.t-m.b)};var svg=mkSvg(box,W,H);
  (o.bands||[]).forEach(function(b,k){svg.appendChild(S('rect',{x:m.l+b.i0*pw,y:m.t,width:(b.i1-b.i0+1)*pw,height:H-m.t-m.b,fill:k%2?'#f6f6f6':'#fff'}));svg.appendChild(S('text',{x:m.l+b.i0*pw+3,y:m.t-8,class:'mu'},b.t))});
  yTicks(lo,hi,5).forEach(function(v){svg.appendChild(S('line',{x1:m.l,x2:W-m.r,y1:ys(v),y2:ys(v),stroke:v===0?'#333':'#e4e4e4'}));svg.appendChild(S('text',{x:m.l-6,y:ys(v)+4,'text-anchor':'end',class:'mu'},(o.yf||f0)(v)))});
  var ns=o.series.length,bw=Math.max(1.5,pw*.8/ns);
  o.cats.forEach(function(c,i){o.series.forEach(function(s,k){var v=s.v[i];if(v==null)return;var x=m.l+i*pw+pw*.1+k*bw,y0=ys(0),y1=ys(v);svg.appendChild(S('rect',{x:x,y:Math.min(y0,y1),width:bw-.5,height:Math.max(.5,Math.abs(y1-y0)),fill:s.c}))});
    if(i%(o.step||(pw<16?3:1))===0)svg.appendChild(S('text',{x:m.l+i*pw+pw/2,y:H-8,'text-anchor':'middle',class:'mu'},String(c).length>4?String(c):(pw<16?String(c).slice(2):c)))});
  var rect=S('rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'transparent'});svg.appendChild(rect);var tip=box.lastChild;
  function show(ev){var r=svg.getBoundingClientRect(),k=W/r.width,t=ev.touches?ev.touches[0]:ev,i=Math.floor(((t.clientX-r.left)*k-m.l)/pw);if(i<0||i>=n){tip.style.display='none';return}
    var h='<b>'+o.cats[i]+'</b>';o.series.forEach(function(s){if(s.v[i]!=null)h+='<br><span style="color:'+s.c+'">■</span> '+esc(s.n)+': '+(o.tf||o.yf||f0)(s.v[i])});if(o.extra)h+=o.extra(i);
    tip.innerHTML=h;tip.style.display='';var tw=tip.offsetWidth,left=(m.l+i*pw+pw/2)/k+10;if(left+tw>r.width)left=(m.l+i*pw+pw/2)/k-tw-10;if(left<0)left=0;tip.style.left=left+'px';tip.style.top='6px'}
  rect.addEventListener('mousemove',show);rect.addEventListener('mouseleave',function(){tip.style.display='none'});rect.addEventListener('touchstart',show,{passive:true});rect.addEventListener('touchmove',show,{passive:true});
  box._f=function(){colChart(boxId,o)};if(RD.indexOf(box)<0)RD.push(box);
}
window.addEventListener('resize',(function(){var t;return function(){clearTimeout(t);t=setTimeout(function(){RD.forEach(function(b){b._f()})},200)}})());
/* mappa a quartieri */
function baseMap(id){var M=L.map(id,{preferCanvas:true}).setView([45.4655,9.19],11);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(M);
  window.addEventListener('resize',function(){M.invalidateSize()});return M}
function cls(v,br){var i=0;while(i<br.length&&v>=br[i])i++;return i}
function qbreaks(vals,k){var s=vals.filter(function(v){return v!=null&&isFinite(v)}).sort(function(a,b){return a-b}),b=[];for(var i=1;i<k;i++)b.push(s[Math.floor(i*s.length/k)]);return b.filter(function(v,i,a){return i===0||v>a[i-1]})}
function nearestInt(v){return Math.round(v)}
"""

FOOT_COMUNE = """<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
"""

NAV = """<p class="nav3"><b>Le tre pagine sulla popolazione:</b> @@N1@@ &middot; @@N2@@ &middot; @@N3@@ &middot; <a href="../censimenti/">I censimenti di Milano</a></p>"""
