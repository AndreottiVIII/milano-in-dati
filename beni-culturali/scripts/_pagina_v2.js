(function(){
'use strict';
var DATA='data/';
var C={mi:'#E30613',m3:'#FFD500',m2:'#00A651',m4:'#0072BC',m5:'#7B3FA0',ora:'#F58220',teal:'#00A19A',mar:'#8C5A32',gri:'#8a919c',ink:'#0b0d12',ink2:'#2f3440',mut:'#5f6673',grid:'#e6e8ec',axis:'#9aa1ad',soft:'#f4f5f7'};
var GR=[
 {id:'oa',nome:"Opere d'arte",lungo:"Dipinti, sculture e oggetti d'arte",col:C.ora,tx:'k',sigle:"OA opere d'arte, OAC arte contemporanea"},
 {id:'ds',nome:'Disegni e stampe',lungo:'Disegni e stampe',col:C.m5,tx:'w',sigle:'D disegni, S stampe'},
 {id:'ar',nome:'Archeologia',lungo:'Reperti archeologici',col:C.m2,tx:'k',sigle:'RA reperti, MA monumenti, CA complessi archeologici'},
 {id:'ps',nome:'Strumenti scientifici',lungo:'Strumenti scientifici',col:C.m4,tx:'w',sigle:'PST strumenti scientifici o tecnologici'},
 {id:'ax',nome:'Architetture',lungo:'Architetture',col:C.mar,tx:'w',sigle:'A architettura'},
 {id:'al',nome:'Altro',lungo:'Altro',col:C.gri,tx:'k',sigle:'BDM beni demoetnoantropologici, F fotografie, NU monete e medaglie, PG parchi e giardini'}];
var V,NIL,RD=[];

/* ---------- formattazione ---------- */
function grp(s){return s.replace(/\B(?=(\d{3})+(?!\d))/g,'.')}
function f0(x){if(x==null)return '';var r=Math.round(x);return (r<0?'−':'')+grp(String(Math.abs(r)))}
function pc(x){return Math.round(x*100)}
function p1(x){return (Math.round(x*1000)/10).toFixed(1).replace('.',',')}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function $(id){return document.getElementById(id)}
function sum(o){var s=0;for(var k in o)s+=o[k];return s}
var ROM=[[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];
function rom(n){var s='';[[20,'XX'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']].forEach(function(p){while(n>=p[0]){s+=p[1];n-=p[0]}});return s}
function secNome(k){k=+k;if(k>0)return rom(k)+' secolo';if(k===-6)return 'prima del V secolo a.C.';return rom(-k)+' secolo a.C.'}
function secAnni(k){k=+k;if(k>0)return ((k-1)*100+1)+'–'+(k*100);if(k===-6)return 'prima del 500 a.C.';return (-k*100)+'–'+(-k*100-99)+' a.C.'}
function gtot(o){return sum(o)}

/* ---------- svg ---------- */
var cvs=document.createElement('canvas').getContext('2d');
function tw(s,size,bold){cvs.font=(bold?'700 ':'400 ')+(size||13)+'px system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif';return cvs.measureText(String(s)).width}
function r1(v){return Math.round(v*10)/10}
function T(x,y,s,o){o=o||{};return '<text x="'+r1(x)+'" y="'+r1(y)+'"'+(o.a?' text-anchor="'+o.a+'"':'')+(o.c?' class="'+o.c+'"':'')+'>'+s+'</text>'}
function L(x1,y1,x2,y2,col,w,extra){return '<line x1="'+r1(x1)+'" y1="'+r1(y1)+'" x2="'+r1(x2)+'" y2="'+r1(y2)+'" stroke="'+(col||C.grid)+'" stroke-width="'+(w||1)+'"'+(extra||'')+'/>'}
function tip(h){return ' data-t="'+esc(h)+'"'}
function svgOpen(W,H,cls){return '<svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'"'+(cls?' class="'+cls+'"':'')+' aria-hidden="true">'}
function sw(c){return '<i style="background:'+c+'"></i>'}
function width(id){return Math.max(300,Math.floor($(id).clientWidth))}
function fit(s,maxw,size,bold){if(tw(s,size,bold)<=maxw)return s;while(s.length>3&&tw(s+'…',size,bold)>maxw)s=s.slice(0,-1);return s.replace(/\s+$/,'')+'…'}
function legGr(ids){return GR.filter(function(g){return !ids||ids.indexOf(g.id)>=0}).map(function(g){return '<span><i style="background:'+g.col+'"></i>'+g.nome+'</span>'}).join('')}
function tipGr(o,intest){var h=intest||'';GR.forEach(function(g){if(o[g.id])h+='<br>'+sw(g.col)+g.nome+': '+f0(o[g.id])});return h}

/* ---------- tooltip ---------- */
var TIP=$('tip');
function showTip(e,el){
  TIP.innerHTML=el.getAttribute('data-t');TIP.style.display='block';
  var w=TIP.offsetWidth,h=TIP.offsetHeight,vw=document.documentElement.clientWidth;
  var x=e.pageX+12,y=e.pageY-h-14;
  if(x+w>window.scrollX+vw-8)x=e.pageX-w-12;
  if(x<window.scrollX+8)x=window.scrollX+8;
  if(y<window.scrollY+8)y=e.pageY+18;
  TIP.style.left=x+'px';TIP.style.top=y+'px';
}
document.addEventListener('pointermove',function(e){if(e.pointerType!=='mouse')return;var el=e.target.closest&&e.target.closest('[data-t]');if(el)showTip(e,el);else TIP.style.display='none'});
document.addEventListener('click',function(e){var el=e.target.closest&&e.target.closest('[data-t]');if(el)showTip(e,el);else TIP.style.display='none'});
window.addEventListener('scroll',function(){if(TIP.style.display==='block'&&!matchMedia('(hover:hover)').matches)TIP.style.display='none'},{passive:true});

/* ---------- dati ---------- */
function getJ(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.json()})}
Promise.all([getJ(DATA+'v2.json'),getJ('../medici-farmacie/data/nil.geojson')]).then(function(r){
  V=r[0];NIL=r[1];
  try{tutto()}catch(e){console.error(e);$('hl').innerHTML='<p>Errore nella pagina: '+esc(e.message)+'</p>'}
}).catch(function(e){$('hl').innerHTML='<p>Dati non caricati: '+esc(e.message)+'</p>'});
function draw(f){f();RD.push(f)}
function tutto(){
  highlights();
  draw(chA);draw(chB);draw(chC);schedaSecolo();draw(chTipi);draw(chAut);cercaAutore();draw(chDet);draw(chMap);draw(chCom);
  cercaSchede();
  var rt,lw=window.innerWidth;window.addEventListener('resize',function(){if(window.innerWidth===lw)return;lw=window.innerWidth;clearTimeout(rt);rt=setTimeout(function(){RD.forEach(function(f){f()})},150)});
}

/* ---------- numeri in alto ---------- */
function totSec(k){return gtot(V.mat[k])}
function highlights(){
  var N=V.num,tot=N.schede_sede_milano,xix=totSec('19'),p0=V.punti[0];
  var cards=[
    {c:C.mi,h:'tipi',n:f0(tot),p:'schede descrivono beni che stanno a Milano'},
    {c:C.m3,h:'tempo',n:pc(xix/tot)+'<small>%</small>',p:'delle schede è dell’Ottocento: '+f0(xix)+', più di ogni altro secolo'},
    {c:C.m2,h:'autori',n:pc(N.autore_presente/tot)+'<small>%</small>',p:'delle schede dice chi è l’autore. Gli autori diversi sono '+f0(N.autori_distinti)},
    {c:C.m4,h:'dove',n:pc(p0.n/N.coordinate_in_comune)+'<small>%</small>',p:'delle schede con coordinate sta in un solo punto: quello di Brera'},
    {c:C.m5,h:'detentori',n:pc(V.det_non/tot)+'<small>%</small>',p:'delle schede non dice chi le conserva, con un nome'},
    {c:C.ora,h:'complete',n:pc(N.luogo_preciso_sito_o_indirizzo/tot)+'<small>%</small>',p:'delle schede dice un luogo più preciso di «Milano»'}];
  $('hl').innerHTML=cards.map(function(k){return '<a href="#'+k.h+'" style="--c:'+k.c+'"><span class="n">'+k.n+'</span><p>'+k.p+'</p><span class="vai">↓ il grafico</span></a>'}).join('');
}

/* ---------- opzione A: aree per tipo ---------- */
function binLab(i){var a=1300+25*i;return a+'–'+(a+24)}
function binTot(b){return sum(b)}
function chA(){
  var B=V.bins,NB=B.length,W=width('ch-a'),H=250,m={l:38,r:10,t:26,b:26},pw=W-m.l-m.r,ph=H-m.t-m.b;
  var tots=B.map(binTot),mx=Math.max.apply(null,tots),top=Math.ceil(mx/1000)*1000;
  function X(y){return m.l+pw*(y-1300)/725}
  function Y(v){return m.t+ph*(1-v/top)}
  var xs=[X(1300)];for(var i=0;i<NB;i++)xs.push(X(1300+25*i+12.5));xs.push(X(2025));
  var cum=[],run=B.map(function(){return 0});
  GR.forEach(function(g){var arr=B.map(function(b,i){run[i]+=b[g.id];return run[i]});arr=[arr[0]].concat(arr).concat([arr[NB-1]]);cum.push(arr)});
  var s=svgOpen(W,H);
  for(var v=0;v<=top;v+=1000){s+=L(m.l,Y(v),W-m.r,Y(v),C.grid)+T(m.l-5,Y(v)+4,f0(v),{a:'end',c:'m'})}
  GR.forEach(function(g,gi){
    var up=cum[gi],lo=gi?cum[gi-1]:up.map(function(){return 0}),d='';
    for(var j=0;j<xs.length;j++)d+=(j?'L':'M')+r1(xs[j])+' '+r1(Y(up[j]));
    for(j=xs.length-1;j>=0;j--)d+='L'+r1(xs[j])+' '+r1(Y(lo[j]));
    s+='<path d="'+d+'Z" fill="'+g.col+'" stroke="#fff" stroke-width=".7"/>';
  });
  for(var y=1300;y<=2000;y+=100)s+=L(X(y),m.t+ph,X(y),m.t+ph+4,C.axis)+T(X(y),m.t+ph+18,y,{a:'middle',c:'m'});
  s+=L(m.l,m.t+ph,W-m.r,m.t+ph,C.axis);
  /* nomi sulle fasce */
  var pk=tots.indexOf(mx),pxk=X(1300+25*pk+12.5);
  GR.forEach(function(g,gi){
    var gs=0;B.forEach(function(b){gs+=b[g.id]});if(gs<2000)return;
    if(g.id==='oa'){
      var w=tw(g.nome,12,true)+10,sp=Math.max(1,Math.round(w/(pw/29)/2)),bj=-1,bs=0;
      for(var j=sp;j<NB-sp;j++){var mt=1e9;for(var q=j-sp;q<=j+sp;q++)mt=Math.min(mt,B[q][g.id]);if(mt>bs){bs=mt;bj=j}}
      s+=T(X(1300+25*bj+12.5),Y(cum[gi][bj+1]-B[bj][g.id]/2)+4,g.nome,{a:'middle',c:g.tx});
    }else{
      var jj=pk-1;
      s+=T(X(1300+25*jj+12.5),Y(cum[gi][jj+1])-7,g.nome,{a:'end',c:'halo'});
    }
  });
  var lab=binLab(pk)+': '+f0(mx),lw=tw(lab,12,true);
  s+=T(Math.max(m.l+lw/2,Math.min(W-m.r-lw/2,pxk-30)),Y(mx)-8,lab,{a:'middle',c:'halo'});
  for(i=0;i<NB;i++)s+='<rect x="'+r1(X(1300+25*i))+'" y="'+m.t+'" width="'+r1(pw/29)+'" height="'+ph+'" fill="transparent"'+tip(tipGr(B[i],'<b>'+binLab(i)+'</b><br>'+f0(tots[i])+' schede'))+'/>';
  $('ch-a').innerHTML=s+'</svg>';
  $('lg-a').innerHTML=legGr();
  var best2=0,bi=0;for(i=0;i<NB-1;i++){var t2=tots[i]+tots[i+1];if(t2>best2){best2=t2;bi=i}}
  var tot=V.num.schede_sede_milano;
  $('t-a').textContent='Dal '+(1300+25*bi)+' al '+(1300+25*bi+49)+' sono datate '+f0(best2)+' schede: il '+pc(best2/tot)+'% di tutte quelle di Milano';
  $('nt-a').textContent='Non nel grafico: '+f0(V.pre1300)+' schede più antiche del 1300 (di cui '+f0(V.pre_ac)+' prima di Cristo) e '+f0(V.nodata)+' senza una data leggibile.';
}

/* ---------- opzione B: un riquadro per tipo ---------- */
function chB(){
  var B=V.bins,NB=B.length,W=width('ch-b'),ph=52,gap=26,head=18,blk=head+ph+gap,H=GR.length*blk+8+34;
  var cw=44,x0=8+cw+10,pw=W-8-x0;function X(y){return x0+pw*(y-1300)/725}
  var s=svgOpen(W,H),y;
  for(y=1300;y<=2000;y+=100)s+=L(X(y),0,X(y),GR.length*blk-gap+2,C.grid);
  var pks=[];
  GR.forEach(function(g,gi){
    var oy=gi*blk,vals=B.map(function(b){return b[g.id]}),pre=V.pre_g[g.id],mx=Math.max.apply(null,vals.concat([pre])),pk=vals.indexOf(Math.max.apply(null,vals));
    pks.push(pk);
    var base=oy+head+ph;
    s+=T(8,oy+13,g.nome,{c:'b'})+T(W-8,oy+13,f0(V.tot_g[g.id])+' schede',{a:'end',c:'m'});
    /* colonna: prima del 1300 */
    if(pre){var hh=ph*pre/mx;s+='<rect x="8" y="'+r1(base-hh)+'" width="'+cw+'" height="'+r1(hh)+'" fill="'+g.col+'"'+tip('<b>'+g.nome+', prima del 1300</b><br>'+f0(pre)+' schede in tutti i secoli prima')+'/>'+(hh>22?T(8+cw/2,base-hh+16,f0(pre),{a:'middle',c:g.tx}):T(8+cw/2,base-hh-4,f0(pre),{a:'middle',c:'halo'}))}
    var xs=[X(1300)];for(var i=0;i<NB;i++)xs.push(X(1300+25*i+12.5));xs.push(X(2025));
    var arr=[vals[0]].concat(vals).concat([vals[NB-1]]);
    var d='M'+r1(xs[0])+' '+r1(base);
    for(var j=0;j<xs.length;j++)d+='L'+r1(xs[j])+' '+r1(base-ph*arr[j]/mx);
    d+='L'+r1(xs[xs.length-1])+' '+r1(base)+'Z';
    s+='<path d="'+d+'" fill="'+g.col+'" fill-opacity=".92"/>'+L(8,base,W-8,base,C.axis);
    if(vals[pk]>=pre*0.3||!pre){
      var lab=binLab(pk)+': '+f0(vals[pk]),lw=tw(lab,12,true),px=X(1300+25*pk+12.5);
      var tx=px+lw+10>W-8?px-8:px+8,an=px+lw+10>W-8?'end':'start';
      s+=T(tx,oy+head+13,lab,{a:an,c:'halo'});
    }
    for(i=0;i<NB;i++)s+='<rect x="'+r1(X(1300+25*i))+'" y="'+(oy+head)+'" width="'+r1(pw/29)+'" height="'+ph+'" fill="transparent"'+tip('<b>'+g.nome+', '+binLab(i)+'</b><br>'+f0(vals[i])+' schede')+'/>';
  });
  var yb=GR.length*blk-gap+2;
  s+=T(8+cw/2,yb+14,'prima',{a:'middle',c:'m'})+T(8+cw/2,yb+28,'del 1300',{a:'middle',c:'m'});
  for(y=1300;y<=2000;y+=100)s+=T(X(y),yb+16,y,{a:'middle',c:'m'});
  $('ch-b').innerHTML=s+'</svg>';
  $('t-b').textContent='Ogni tipo ha il suo picco: disegni e stampe nel '+binLab(pks[1])+', strumenti scientifici nel '+binLab(pks[3])+', archeologia prima del 1300';
}

/* ---------- opzione C: strati per secolo ---------- */
function chC(){
  var M=V.mat,W=width('ch-c'),rh=17,gap=5,lw=64,right=44;
  var rows=[];
  var ac={oa:0,ds:0,ar:0,ps:0,ax:0,al:0};
  [-6,-5,-4,-3,-2,-1].forEach(function(k){GR.forEach(function(g){ac[g.id]+=M[k][g.id]})});
  rows.push({lab:'a.C.',o:ac,nome:'prima di Cristo'});
  for(var k=1;k<=21;k++)rows.push({lab:rom(k)+' sec.',o:M[k],nome:secNome(k)+' ('+secAnni(k)+')'});
  rows.push({lab:'senza data',o:{nd:V.nodata},nome:'senza una data leggibile',nd:1});
  var mx=0;rows.forEach(function(r){if(!r.nd)mx=Math.max(mx,gtot(r.o))});
  var H=rows.length*(rh+gap)+4,bw=W-lw-right-4,s=svgOpen(W,H);
  rows.forEach(function(r,i){
    var y=i*(rh+gap)+2,t=gtot(r.o),x=lw,w;
    s+=T(lw-8,y+rh-4,r.lab,{a:'end',c:r.nd?'m':'b'});
    if(r.nd){w=bw*t/mx;s+='<rect x="'+x+'" y="'+y+'" width="'+r1(w)+'" height="'+rh+'" rx="3" fill="#d5d9df"/>'}
    else GR.forEach(function(g){
      var v=r.o[g.id];if(!v)return;w=bw*v/mx;
      s+='<rect x="'+r1(x)+'" y="'+y+'" width="'+r1(Math.max(w,0.8))+'" height="'+rh+'" fill="'+g.col+'" stroke="#fff" stroke-width=".6"/>';
      if(w>tw(g.nome,12,true)+10)s+=T(x+w/2,y+rh-4,g.nome,{a:'middle',c:g.tx});
      x+=w;
    });
    s+=T(lw+bw*t/mx+6,y+rh-4,f0(t),{c:'b'});
    s+='<rect x="0" y="'+(y-2)+'" width="'+W+'" height="'+(rh+gap)+'" fill="transparent"'+tip(tipGr(r.o,'<b>'+r.nome+'</b><br>'+f0(t)+' schede'))+'/>';
  });
  $('ch-c').innerHTML=s+'</svg>';
  $('lg-c').innerHTML=legGr();
  var mxOld=0;for(var kk=-6;kk<=14;kk++)if(kk!==0)mxOld=Math.max(mxOld,gtot(M[kk]));
  var acTot=gtot(ac);mxOld=Math.max(mxOld,acTot);
  $('t-c').textContent='Prima del XV secolo nessun secolo arriva a '+f0(Math.ceil(mxOld/100)*100)+' schede; l’Ottocento ne ha '+f0(gtot(M[19]))+' e il Novecento '+f0(gtot(M[20]));
}

/* ---------- scegli un secolo ---------- */
function schedaSecolo(){
  var sel=$('sec'),tot=V.num.schede_sede_milano,ks=[];
  Object.keys(V.mat).map(Number).sort(function(a,b){return a-b}).forEach(function(k){if(gtot(V.mat[k])>0)ks.push(k)});
  sel.innerHTML=ks.map(function(k){return '<option value="'+k+'"'+(k===19?' selected':'')+'>'+secNome(k)+' ('+secAnni(k)+') · '+f0(gtot(V.mat[k]))+' schede</option>'}).join('');
  function mostra(){
    var k=sel.value,o=V.mat[k],t=gtot(o),e=V.esempi[k]||{ex:[],aut:[]};
    var h='<b class="big">'+f0(t)+' schede</b>'+secNome(k)+': il '+p1(t/tot).replace(/,0$/,'')+'% di tutte quelle di Milano.';
    h+='<div class="stk">'+GR.map(function(g){return o[g.id]?'<i style="width:'+(100*o[g.id]/t)+'%;background:'+g.col+'"></i>':''}).join('')+'</div>';
    h+='<p class="stl">'+GR.filter(function(g){return o[g.id]}).map(function(g){return '<span>'+sw(g.col)+g.nome+' <b>'+f0(o[g.id])+'</b></span>'}).join(' ')+'</p>';
    if(e.aut.length)h+='<p><b>Autori con più schede:</b> '+e.aut.map(function(a){return esc(a[0])+' ('+f0(a[1])+')'}).join(', ')+'.</p>';
    if(e.ex.length)h+='<p><b>Alcune schede:</b></p><ul class="ex">'+e.ex.map(esEl).join('')+'</ul>';
    $('ris-sec').innerHTML=h;
  }
  sel.addEventListener('change',mostra);sel.addEventListener('input',mostra);mostra();
}
function urlScheda(iri){return 'https://catalogo.beniculturali.it/detail/'+iri}
function fmtData(t){t=t.replace(/\/\d\d\/\d\d/g,'').replace(/\/00/g,'').replace(/\(\?\)\s*/g,'').replace(/ca |post |ante /g,'').replace(/(^|[^\d])0+(\d)/g,'$1$2').trim();var m=t.match(/^(-?\d+)-(-?\d+)$/);if(m&&m[1]===m[2])return m[1];return t}
function esEl(x){return '<li>'+esc(x[0])+(x[1]?' · '+esc(x[1]):'')+(x[2]?' <span class="m">('+esc(fmtData(x[2]))+')</span>':'')+' <a href="'+urlScheda(x[3])+'" target="_blank" rel="noopener">scheda</a></li>'}

/* ---------- treemap dei tipi ---------- */
function squarify(items,x,y,w,h){
  var total=0;items.forEach(function(i){total+=i.v});
  var sc=w*h/total,rest=items.map(function(i){return{it:i,a:i.v*sc}}),out=[];
  while(rest.length){
    var sh=Math.min(w,h),row=[],ra=0,worst=Infinity;
    function wr(r,a){var mn=Infinity,mx=0;r.forEach(function(q){mn=Math.min(mn,q.a);mx=Math.max(mx,q.a)});var s2=sh*sh,a2=a*a;return Math.max(s2*mx/a2,a2/(s2*mn))}
    while(rest.length){
      var nx=rest[0],nr=row.concat([nx]),w2=wr(nr,ra+nx.a);
      if(row.length&&w2>worst)break;
      row=nr;ra+=nx.a;worst=w2;rest.shift();
    }
    var th=ra/sh,pos=0;
    if(w>=h){row.forEach(function(q){var ch=q.a/th;out.push({it:q.it,x:x,y:y+pos,w:th,h:ch});pos+=ch});x+=th;w-=th}
    else{row.forEach(function(q){var cw=q.a/th;out.push({it:q.it,x:x+pos,y:y,w:cw,h:th});pos+=cw});y+=th;h-=th}
  }
  return out;
}
function chTipi(){
  var W=width('ch-tipi'),H=Math.round(Math.min(340,W*1.0)),tot=V.num.schede_sede_milano;
  var items=GR.map(function(g){return{g:g,v:V.tot_g[g.id]}}).sort(function(a,b){return b.v-a.v});
  var rects=squarify(items,0,0,W,H),s=svgOpen(W,H);
  rects.forEach(function(r){
    var g=r.it.g,n=r.it.v;
    s+='<rect x="'+r1(r.x)+'" y="'+r1(r.y)+'" width="'+r1(r.w)+'" height="'+r1(r.h)+'" fill="'+g.col+'" stroke="#fff" stroke-width="2"'+tip('<b>'+g.lungo+'</b><br>'+f0(n)+' schede ('+p1(n/tot)+'%)<br>Sigle: '+g.sigle)+'/>';
    var nm=g.nome;
    if(r.w>tw(nm,13,true)+14&&r.h>40)s+=T(r.x+8,r.y+20,nm,{c:g.tx})+T(r.x+8,r.y+37,f0(n)+' · '+pc(n/tot)+'%',{c:g.tx==='w'?'w2':'k2'});
    else if(r.w>tw(nm,12,true)+8&&r.h>22)s+=T(r.x+5,r.y+17,nm,{c:g.tx});
  });
  $('ch-tipi').innerHTML=s+'</svg>';
  var oa=V.tot_g.oa,ds=V.tot_g.ds;
  $('t-tipi').textContent='Il '+pc(oa/tot)+'% delle schede è un dipinto, una scultura o un oggetto d’arte; disegni e stampe sono il '+pc(ds/tot)+'%';
  $('tab-tipi').innerHTML='<tr><th>Tipo di bene</th><th>Schede</th><th>Quota</th></tr>'+items.map(function(i){return '<tr><td>'+sw(i.g.col)+i.g.nome+'</td><td>'+f0(i.v)+'</td><td>'+p1(i.v/tot)+'%</td></tr>'}).join('')+'<tr class="tot"><td>Totale</td><td>'+f0(tot)+'</td><td>100%</td></tr>';
}

/* ---------- autori su asse del tempo ---------- */
function domGr(tg){var b=null,bv=-1;GR.forEach(function(g){if((tg[g.id]||0)>bv){bv=tg[g.id]||0;b=g}});return b}
function chAut(){
  var A=V.autori.slice(0,14),W=width('ch-aut'),rh=44,m={l:8,r:8,t:4,b:24},pw=W-m.l-m.r,H=A.length*rh+m.t+m.b;
  var mn=Math.floor(Math.min.apply(null,A.map(function(a){return a.p10}))/50)*50,mx=Math.ceil(Math.max.apply(null,A.map(function(a){return a.p90}))/50)*50;
  function X(y){return m.l+pw*(y-mn)/(mx-mn)}
  var s=svgOpen(W,H),y;
  for(y=Math.ceil(mn/100)*100;y<=mx;y+=100)s+=L(X(y),m.t,X(y),H-m.b,C.grid)+T(X(y),H-m.b+16,y,{a:'middle',c:'m'});
  A.forEach(function(a,i){
    var oy=m.t+i*rh,g=domGr(a.tg),ny=oy+16,ty=oy+33,nn=f0(a.c)+' schede';
    var nw=tw(nn,12,false);
    s+=T(m.l,ny,esc(fit(a.n,pw-nw-12,13,true)),{c:'b'})+T(W-m.r,ny,nn,{a:'end',c:'m'});
    var x1=X(a.p10),x2=Math.max(X(a.p90),x1+4);
    s+='<line x1="'+r1(x1)+'" y1="'+ty+'" x2="'+r1(x2)+'" y2="'+ty+'" stroke="'+g.col+'" stroke-width="9" stroke-linecap="round"/>';
    s+='<circle cx="'+r1(X(a.md))+'" cy="'+ty+'" r="5" fill="'+C.ink+'" stroke="#fff" stroke-width="2"/>';
    s+='<rect x="0" y="'+oy+'" width="'+W+'" height="'+rh+'" fill="transparent"'+tip('<b>'+esc(a.n)+'</b><br>'+f0(a.c)+' schede<br>Quasi tutte tra il '+a.p10+' e il '+a.p90+', di mezzo '+a.md+'<br>'+sw(g.col)+'Soprattutto: '+g.nome.toLowerCase())+'/>';
  });
  $('ch-aut').innerHTML=s+'</svg>';
  var a0=V.autori[0],a1=V.autori[1];
  $('t-aut').textContent='Un solo autore, '+a0.n+', ha '+f0(a0.c)+' schede, '+(a0.c>=2*a1.c?'più del doppio':'più')+' del secondo ('+a1.n+', '+f0(a1.c)+')';
}

/* ---------- cerca un artista ---------- */
function cercaAutore(){
  var inp=$('qa'),dl=$('el-aut'),idx={};
  dl.innerHTML=V.autori.map(function(a){idx[a.n.toLowerCase()]=a;return '<option value="'+esc(a.n)+'"></option>'}).join('');
  var vuoto='<p>Scrivi un nome e scegli dal menu: ci sono i '+f0(V.autori.length)+' autori con almeno 4 schede.</p>';
  function mostra(){
    var v=inp.value.trim().toLowerCase(),a=idx[v],box=$('ris-aut');
    if(!v){box.innerHTML=vuoto;return}
    if(!a){box.innerHTML='<p>Nessun autore con questo nome tra quelli con almeno 4 schede. Prova a scrivere solo una parte e scegli dal menu.</p>';return}
    var g=domGr(a.tg),h='<b class="big">'+esc(a.n)+'</b>'+f0(a.c)+' schede, soprattutto di tipo «'+g.nome.toLowerCase()+'».';
    if(a.nd)h+='<p>La maggior parte è datata tra il '+a.p10+' e il '+a.p90+' (di mezzo, il '+a.md+').</p>';
    h+='<div class="stk">'+GR.map(function(q){return a.tg[q.id]?'<i style="width:'+(100*a.tg[q.id]/a.c)+'%;background:'+q.col+'"></i>':''}).join('')+'</div>';
    h+='<p class="stl">'+GR.filter(function(q){return a.tg[q.id]}).map(function(q){return '<span>'+sw(q.col)+q.nome+' <b>'+f0(a.tg[q.id])+'</b></span>'}).join(' ')+'</p>';
    h+='<p><b>Alcune schede:</b></p><ul class="ex">'+a.ex.map(esEl).join('')+'</ul>';
    box.innerHTML=h;
  }
  inp.addEventListener('input',mostra);inp.addEventListener('change',mostra);mostra();
}

/* ---------- chi li conserva ---------- */
function chDet(){
  var tot=V.num.schede_sede_milano,W=width('ch-det'),rh=40,items=[{n:'Senza nome nel catalogo',v:V.det_non,g:1}].concat(V.det.map(function(d){return{n:d[0],v:d[1]}}));
  var H=items.length*rh+4,mx=V.det_non,right=96,bw=W-16-right,s=svgOpen(W,H);
  items.forEach(function(it,i){
    var y=i*rh+2,w=bw*it.v/mx,col=it.g?'#b3b9c3':C.teal;
    s+=T(8,y+14,esc(fit(it.n,W-16,13,false)),{c:it.g?'m':''});
    s+='<rect x="8" y="'+(y+20)+'" width="'+r1(Math.max(w,1.5))+'" height="13" rx="3" fill="'+col+'"/>';
    s+=T(8+w+6,y+31,f0(it.v)+' · '+(it.v/tot<0.1?p1(it.v/tot):pc(it.v/tot))+'%',{c:'b'});
    s+='<rect x="0" y="'+y+'" width="'+W+'" height="'+rh+'" fill="transparent"'+tip('<b>'+esc(it.n)+'</b><br>'+f0(it.v)+' schede ('+p1(it.v/tot)+'%)')+'/>';
  });
  $('ch-det').innerHTML=s+'</svg>';
  $('t-det').textContent='Per il '+pc(V.det_non/tot)+'% delle schede il catalogo non dice chi le conserva; tra le raccolte con un nome, in testa c’è '+V.det[0][0].replace("dell'Accademia","dell’Accademia");
}

/* ---------- mappa ---------- */
var BREVE={'Civica Raccolta delle Stampe "Achille Bertarelli"':'Raccolta Bertarelli','Raccolte Grafiche e Fotografiche del Castello Sforzesco':'Castello: grafiche','Raccolte Artistiche del Castello Sforzesco':'Castello: raccolte artistiche','Museo Poldi Pezzoli':'Poldi Pezzoli','Villa Necchi Campiglio':'Villa Necchi','Museo Archeologico':'Museo Archeologico'};
function ringPath(ring,px,py){var d='';for(var i=0;i<ring.length;i++)d+=(i?'L':'M')+r1(px(ring[i][0]))+' '+r1(py(ring[i][1]));return d+'Z'}
function chMap(){
  var W=width('ch-map'),lon0=9.1545,lon1=9.2075,lat0=45.4500,lat1=45.4800,k=Math.cos(45.465*Math.PI/180),sx=W/((lon1-lon0)*k),H=Math.round((lat1-lat0)*sx);
  function px(lo){return (lo-lon0)*k*sx}function py(la){return (lat1-la)*sx}
  var s=svgOpen(W,H,'mp'),i;
  NIL.features.forEach(function(f){
    var g=f.geometry,polys=g.type==='MultiPolygon'?g.coordinates:[g.coordinates],d='';
    polys.forEach(function(p){p.forEach(function(r){d+=ringPath(r,px,py)})});
    s+='<path d="'+d+'" fill="#f1f3f6" stroke="#b9c0cb" stroke-width=".8" fill-rule="evenodd"/>';
  });
  var P=V.punti,inside=[],fuori=0,fuoriP=0;
  P.forEach(function(p){if(p.lo>=lon0&&p.lo<=lon1&&p.la>=lat0&&p.la<=lat1)inside.push(p);else{fuori+=p.n;fuoriP++}});
  var cir=inside.map(function(p){return{p:p,x:px(p.lo),y:py(p.la),r:Math.min(20,2.8+Math.sqrt(p.n)*0.3)}});
  cir.forEach(function(c){var g=domGr(c.p.tg),nm=c.p.nome||'Senza nome nel catalogo',og=c.p.og.map(function(o){return o[0]+' '+f0(o[1])}).join(', ');
    s+='<circle cx="'+r1(c.x)+'" cy="'+r1(c.y)+'" r="'+r1(c.r)+'" fill="'+g.col+'" fill-opacity=".8" stroke="#fff" stroke-width="1"'+tip('<b>'+esc(nm)+'</b><br>'+f0(c.p.n)+(c.p.n===1?' scheda':' schede')+(c.p.q?' · quartiere '+esc(c.p.q):'')+'<br>Più frequenti: '+esc(og))+'/>'});
  /* numeri sui punti più grandi */
  var lab=cir.filter(function(c){return c.p.n>=600}).sort(function(a,b){return b.p.n-a.p.n});
  function nomeP(p){
    if(p.nome&&p.nn/p.n>=0.7)return p.nome;
    var g=domGr(p.tg);
    if(g.id==='ps')return 'Senza nome nel catalogo (quasi tutti strumenti scientifici)';
    if(p.la>45.4715&&p.la<45.4725&&p.lo>9.188&&p.lo<9.189)return 'Brera, senza nome nel catalogo';
    return 'Senza nome nel catalogo';
  }
  lab.forEach(function(c,i){
    s+='<circle cx="'+r1(c.x)+'" cy="'+r1(c.y)+'" r="9" fill="'+C.ink+'" stroke="#fff" stroke-width="1.5" pointer-events="none"/>'+T(c.x,c.y+4.2,i+1,{a:'middle',c:'w'});
  });
  $('ch-map').innerHTML=s+'</svg>';
  var tot=V.num.coordinate_in_comune,run=0,kk=0;
  for(i=0;i<P.length;i++){run+=P[i].n;kk++;if(run>=tot/2)break}
  $('t-map').textContent='Metà delle schede con coordinate sta in soli '+kk+' punti su '+P.length;
  var q=V.quartieri;
  $('nt-map').textContent='Per quartiere: '+q.slice(0,3).map(function(x){return x[0]+' '+f0(x[1])}).join(', ')+'. Tutti gli altri quartieri insieme hanno '+f0(q.slice(3).reduce(function(a,x){return a+x[1]},0))+' schede. In questa vista non entrano '+f0(fuori)+' schede in '+fuoriP+' punti, più lontani dal centro.';
  var key=lab.map(function(c,i){var p=c.p;return '<li><b class="nb">'+(i+1)+'</b><span>'+esc(nomeP(p))+': <b>'+f0(p.n)+' schede</b>'+(p.q?', quartiere '+esc(p.q):'')+'</span></li>'}).join('');
  if(!$('key-map')){var ol=document.createElement('ol');ol.className='notes';ol.id='key-map';$('ch-map').parentNode.insertBefore(ol,$('nt-map'))}
  $('key-map').innerHTML=key;
  var lgp=GR.filter(function(g){return cir.some(function(c){return domGr(c.p.tg).id===g.id})});
  if(!$('lg-map')){var d=document.createElement('div');d.className='lg';d.id='lg-map';$('ch-map').parentNode.insertBefore(d,$('nt-map'))}
  $('lg-map').innerHTML='<span class="m">Colore = tipo più frequente nel punto:</span>'+legGr(lgp.map(function(g){return g.id}));
}

/* ---------- che cosa dice la scheda ---------- */
function chCom(){
  var N=V.num,tot=N.schede_sede_milano,W=width('ch-com'),rh=46;
  var it=[['Ha una data',N.datazione_presente],['Ha le coordinate',N.coordinate_in_comune],['Dice chi è l’autore',N.autore_presente],['Dice chi la conserva, con un nome',N.istituzione_nominata],['Dice un luogo più preciso di «Milano»',N.luogo_preciso_sito_o_indirizzo]].sort(function(a,b){return b[1]-a[1]});
  var H=it.length*rh+30,x0=10,x1=W-10,s=svgOpen(W,H);
  [0,50,100].forEach(function(v){var x=x0+(x1-x0)*v/100;s+=L(x,0,x,it.length*rh-8,C.grid)+T(x,it.length*rh+10,v+(v===100?'%':''),{a:v===0?'start':v===100?'end':'middle',c:'m'})});
  it.forEach(function(r,i){
    var y=i*rh,q=r[1]/tot,cx=x0+(x1-x0)*q,ty=y+34;
    s+=T(x0,y+15,r[0],{c:'b'});
    s+=L(x0,ty,x1,ty,'#cfd4db',3);
    s+=L(x0,ty,cx,ty,C.teal,3);
    s+='<circle cx="'+r1(cx)+'" cy="'+ty+'" r="9" fill="'+C.teal+'" stroke="#fff" stroke-width="2"/>';
    var lab=p1(q)+'%',w=tw(lab,13,true);
    if(cx+w+18>x1)s+=T(cx-14,ty-8,lab,{a:'end',c:'halo'});else s+=T(cx+14,ty+5,lab,{c:'halo'});
    s+='<rect x="0" y="'+y+'" width="'+W+'" height="'+rh+'" fill="transparent"'+tip('<b>'+r[0]+'</b><br>'+f0(r[1])+' schede su '+f0(tot)+' ('+p1(q)+'%)')+'/>';
  });
  $('ch-com').innerHTML=s+'</svg>';
  $('t-com').textContent='Quasi tutte le schede hanno una data ('+pc(N.datazione_presente/tot)+'%), ma solo il '+pc(N.luogo_preciso_sito_o_indirizzo/tot)+'% dice dove si trova meglio di «Milano»';
}

/* ---------- cerca una scheda ---------- */
function cercaSchede(){
  var voci=null,classi=null,hay=null,ris=[],mostrati=0,STEP=30;
  var tipiNome={"OA":"opera d'arte","S":"stampa","D":"disegno","RA":"reperto archeologico","BDM":"bene demoetnoantropologico","A":"architettura","F":"fotografia","PST":"strumento scientifico","OAC":"arte contemporanea","MA":"monumento archeologico","CA":"complesso archeologico","PG":"parco o giardino","NU":"moneta o medaglia"};
  function url(v){return 'https://catalogo.beniculturali.it/detail/'+classi[v[4].charAt(0)]+'/'+v[4].slice(1)}
  function riga(v){var t='<b>'+esc(v[0])+'</b>'+(v[5]?' · '+esc(v[5]):'');var a=v[1]?esc(v[1].split(' | ').join(', ')):'';return '<li>'+t+'<br><span class="m">'+[a,esc(v[2]),esc(tipiNome[v[3]]||v[3])].filter(Boolean).join(' · ')+'</span> <a href="'+url(v)+'" target="_blank" rel="noopener">scheda</a></li>'}
  function disegna(reset){
    var ul=$('ris');if(reset){ul.innerHTML='';mostrati=0}
    var fine=Math.min(ris.length,mostrati+STEP),h='';
    for(var k=mostrati;k<fine;k++)h+=riga(voci[ris[k]]);
    ul.insertAdjacentHTML('beforeend',h);mostrati=fine;
    $('piu').hidden=mostrati>=ris.length;
    $('qmsg').textContent=f0(ris.length)+' schede'+(ris.length>mostrati?' (ne mostro '+mostrati+')':'')+'.';
  }
  function cerca(){
    var q=$('q').value.trim().toLowerCase(),tp=$('tp').value,pa=q?q.split(/\s+/):[];ris=[];
    for(var i=0;i<voci.length;i++){
      if(tp&&voci[i][3]!==tp)continue;
      var ok=true;for(var j=0;j<pa.length;j++){if(hay[i].indexOf(pa[j])<0){ok=false;break}}
      if(ok)ris.push(i);
    }
    disegna(true);
  }
  getJ(DATA+'oggetti.json').then(function(O){
    voci=O.voci;classi=O.classi;
    hay=voci.map(function(v){return (v[0]+' '+v[1]+' '+v[5]).toLowerCase()});
    var sel=$('tp'),cont={};voci.forEach(function(v){cont[v[3]]=(cont[v[3]]||0)+1});
    Object.keys(cont).sort(function(a,b){return cont[b]-cont[a]}).forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=(tipiNome[k]||k)+' ('+k+') · '+f0(cont[k]);sel.appendChild(o)});
    var q=$('q');q.disabled=false;sel.disabled=false;
    var t=null;q.addEventListener('input',function(){clearTimeout(t);t=setTimeout(cerca,180)});sel.addEventListener('change',cerca);
    $('piu').addEventListener('click',function(){disegna(false)});
    cerca();
  }).catch(function(){$('qmsg').textContent='Elenco non caricato.'});
}
})();
