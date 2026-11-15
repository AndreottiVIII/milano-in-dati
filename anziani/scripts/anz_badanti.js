/* ---------- badanti ---------- */
function dsum(p,k){var d=DO.province[p];return d[k+'_f'].map(function(v,i){return v+d[k+'_m'][i]})}
function bad25(p){var a=dsum(p,'bad');return a[a.length-1]}
function badSerie(){
  var A=DO.anni,bad=dsum('Milano','bad'),col=dsum('Milano','colf'),box=$('ch-badanti-serie'),W=width('ch-badanti-serie'),H=320,m={l:50,r:14,t:40,b:30},pw=W-m.l-m.r,ph=H-m.t-m.b,hi=70000,n=A.length-1;
  function X(i){return m.l+i/n*pw}function Y(v){return m.t+ph-v/hi*ph}
  var s=svgOpen(W,H);
  [0,20000,40000,60000].forEach(function(v){s+=L(m.l,Y(v),m.l+pw,Y(v),C.grid)+T(m.l-6,Y(v)+4,f0(v),{a:'end',c:'m'})});
  A.forEach(function(a,i){if(i===0||a===2019||a===2022||a===2025)s+=L(X(i),Y(0),X(i),Y(0)+5,C.axis)+T(X(i),H-10,a,{a:i===0?'start':i===n?'end':'middle',c:'m'})});
  var i20=A.indexOf(2020);
  s+=L(X(i20),m.t-8,X(i20),Y(0),C.ink,1.2,' stroke-dasharray="3 4"');
  s+='<circle cx="'+r1(X(i20))+'" cy="'+r1(m.t-18)+'" r="9" fill="#0b0d12"/>'+T(X(i20),m.t-14,'1',{a:'middle',c:'w'});
  [[col,C.ora,'colf'],[bad,C.m2,'badanti']].forEach(function(sr){
    var d='';sr[0].forEach(function(v,i){d+=(i?'L':'M')+r1(X(i))+' '+r1(Y(v))});
    s+='<path d="'+d+'" fill="none" stroke="'+sr[1]+'" stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round"/>';
    sr[0].forEach(function(v,i){s+='<circle cx="'+r1(X(i))+'" cy="'+r1(Y(v))+'" r="'+(i===0||i===n?5.5:4)+'" fill="'+sr[1]+'" stroke="#fff" stroke-width="1.6"'+tip('<b>'+A[i]+'</b><br>'+(sr[2]==='colf'?'Colf e altri lavoratori domestici':'Badanti')+': '+f0(v))+'/>'});
    s+=T(X(0)+2,Y(sr[0][0])-12,f0(sr[0][0]),{c:'k',st:'font-size:13px;fill:'+(sr[2]==='colf'?'#B85600':'#007A3B')});
    s+=T(X(n),Y(sr[0][n])+(sr[2]==='colf'?24:-12),f0(sr[0][n]),{a:'end',c:'k',st:'font-size:13px;fill:'+(sr[2]==='colf'?'#B85600':'#007A3B')});
  });
  box.innerHTML=s+'</svg>';
  $('t-badanti-serie').textContent='In provincia di Milano le badanti in regola passano da '+f0(bad[0])+' nel 2016 a '+f0(bad[n])+' nel 2025 ('+(bad[n]>bad[0]?'+':'−')+f0(Math.abs(100*(bad[n]/bad[0]-1)))+'%); le colf da '+f0(col[0])+' a '+f0(col[n])+' ('+(col[n]>col[0]?'+':'−')+f0(Math.abs(100*(col[n]/col[0]-1)))+'%)';
}
function badProv(){
  var rows=PV.map(function(p){return {n:p.nome,b:100*bad25(p.nome)/p.o80,r:rt(p.o80,p.posti),nb:bad25(p.nome),p:p}}).sort(function(a,b){return b.b-a.b});
  var box=$('ch-badanti-prov'),W=width('ch-badanti-prov'),rh=34,m={l:2,r:14,t:6,b:30},n=rows.length,H=m.t+m.b+n*rh,xm=18,lw=Math.min(128,Math.floor(W*0.36)),pw=W-m.l-lw-m.r;
  function X(v){return m.l+lw+v/xm*pw}
  var s=svgOpen(W,H);
  [0,4,8,12,16].forEach(function(v){s+=L(X(v),m.t,X(v),m.t+n*rh,C.grid)+T(X(v),H-10,v,{a:'middle',c:'m'})});
  rows.forEach(function(r,i){
    var y=m.t+i*rh+rh/2,isM=r.n==='Milano',lo=Math.min(r.b,r.r),hi=Math.max(r.b,r.r);
    s+=T(m.l,y+4,isM?'Milano (provincia)':r.n,{c:isM?'k':'m',st:'font-size:13px;'+(isM?'fill:'+C.mi:'fill:#2f3440')});
    s+=L(X(lo),y,X(hi),y,isM?C.mi:'#c3c8d0',isM?4:3);
    var t=tip('<b>Provincia di '+esc(r.n)+'</b><br>Badanti in regola: '+f0(r.nb)+' ('+f1(r.b)+' ogni 100 over 80)<br>Posti in RSA: '+f0(r.p.posti)+' ('+f1(r.r)+' ogni 100 over 80)<br>Persone con 80 anni o più: '+f0(r.p.o80));
    s+='<circle cx="'+r1(X(r.r))+'" cy="'+r1(y)+'" r="'+(isM?8:6.5)+'" fill="'+C.m5+'" stroke="#fff" stroke-width="2"'+t+'/>';
    s+='<circle cx="'+r1(X(r.b))+'" cy="'+r1(y)+'" r="'+(isM?8:6.5)+'" fill="'+C.m2+'" stroke="#fff" stroke-width="2"'+t+'/>';
    var bl=r.b<r.r;
    s+=T(X(r.b)+(bl?-11:11),y+4,f1(r.b),{a:bl?'end':'start',c:'k',st:'font-size:13px;fill:#007A3B'});
    s+=T(X(r.r)+(bl?11:-11),y+4,f1(r.r),{a:bl?'start':'end',c:'k',st:'font-size:13px;fill:'+C.m5});
  });
  box.innerHTML=s+'</svg>';
  var mi_=rows.filter(function(r){return r.n==='Milano'})[0];
  var cnt=rows.filter(function(r){return r.b>r.r}).length;
  $('t-badanti-prov').textContent='In provincia di Milano le badanti in regola sono '+f1(mi_.nb/mi_.p.posti)+' volte i posti in RSA ('+f0(mi_.nb)+' contro '+f0(mi_.p.posti)+'); in '+cnt+' province lombarde su 12 sono più dei posti';
}
function badChi(){
  var M=DO.province['Milano'],k=DO.anni.length-1,box=$('ch-badanti-chi'),W=width('ch-badanti-chi'),m={l:2,r:2,t:4,b:4},rh=78,H=m.t+m.b+3*rh,pw=W-m.l-m.r;
  var bf=M.bad_f[k],bm=M.bad_m[k],cf=M.colf_f[k],cm=M.colf_m[k],tot=bf+bm+cf+cm;
  var G=[
   {a:['donne',bf+cf,C.dn],b:['uomini',bm+cm,C.uo]},
   {a:['stranieri',M.str[k],C.m5],b:['italiani',M.ita[k],'#8a919b']},
   {a:['badanti',bf+bm,C.m2],b:['colf e altro',cf+cm,C.ora]}];
  var s=svgOpen(W,H);
  G.forEach(function(g,i){
    var y=m.t+i*rh,t=g.a[1]+g.b[1],w1=g.a[1]/t*pw,pa=100*g.a[1]/t,pb=100*g.b[1]/t;
    var tt='<b>'+g.a[0]+' / '+g.b[0]+'</b><br>'+g.a[0]+': '+f0(g.a[1])+' ('+f1(pa)+'%)<br>'+g.b[0]+': '+f0(g.b[1])+' ('+f1(pb)+'%)';
    s+=T(m.l,y+16,g.a[0]+' '+f0(pa)+'%',{c:'k',st:'font-size:14px'})+T(m.l+pw,y+16,g.b[0]+' '+f0(pb)+'%',{a:'end',c:'k',st:'font-size:14px'});
    s+='<rect x="'+r1(m.l)+'" y="'+(y+24)+'" width="'+r1(w1)+'" height="34" fill="'+g.a[2]+'"'+tip(tt)+'/>';
    s+='<rect x="'+r1(m.l+w1)+'" y="'+(y+24)+'" width="'+r1(pw-w1)+'" height="34" fill="'+g.b[2]+'"'+tip(tt)+'/>';
    s+=T(m.l+4,y+46,f0(g.a[1]),{c:'w'})+T(m.l+pw-4,y+46,f0(g.b[1]),{a:'end',c:'w'});
  });
  box.innerHTML=s+'</svg>';
  $('t-badanti-chi').textContent='Su '+f0(tot)+' lavoratori domestici in regola, '+f0(100*(bf+cf)/tot)+'% sono donne e '+f0(100*M.str[k]/(M.str[k]+M.ita[k]))+'% hanno cittadinanza straniera';
}
