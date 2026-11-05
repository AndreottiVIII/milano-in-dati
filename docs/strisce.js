/* Strisce: una striscia per indicatore, dal valore più basso al più alto tra tanti luoghi.
   Vanilla JS, nessuna libreria. Pensata per essere riusata da altre pagine.

   USO
     <script src="../strisce.js"></script>
     Strisce.disegna(document.getElementById('x'), {
       a: {id: 23, nome: 'Isola'},            // luogo scelto
       b: {id: 5,  nome: 'Corvetto'},         // luogo di confronto, facoltativo
       colA: '#00695c', colB: '#c26a1b',      // i due colori dei punti (facoltativi): meglio gli stessi della mappa
       luoghi: 'quartieri',                   // come si chiamano i luoghi nel testo (predefinito: 'luoghi')
       cittaEtichetta: 'la città',            // legenda del trattino, facoltativo
       gruppi: [ {titolo: 'Chi ci abita', colore: '#00A651', righe: [riga, riga, ...]} ]
     });

   Una riga:
     { id:'eta_media', titolo:'Età media', unita:'anni', anno:'2025',
       fmt: function(v){ return String(v) },           // come si scrive un valore
       punti: [ {id:23, nome:'Isola', v:44.0, pos:true},          // pos:true = entra nella classifica
                {id:3,  nome:'Giardini...', v:46.7, pos:false, flag:'poco affidabile'},  // si vede, senza posto
                {id:8,  nome:'X', v:null, mancante:'dato non disponibile'} ],
       citta: {v:45.65, etichetta:'città'},            // trattino; v null = nessun trattino
       tratteggio: false,                              // true: un dato solo per più zone (striscia tratteggiata)
       avviso: 'testo mostrato sotto la striscia',     // facoltativo
       etichette: ['stima da CAP'],                    // piccole etichette accanto all'anno (solo testo)
       coda: '<div>html già pulito</div>'              // facoltativo: html messo in fondo alla riga
     }

   Dentro un gruppo, un elemento {html:'...'} viene messo cosi' com'e' (per indicatori che non sono numeri su una scala).
   La classifica si calcola qui: 1° = valore più alto; i pari hanno lo stesso posto.
   Strisce.riga(riga, opzioni) restituisce l'html di una sola riga; Strisce.legenda(opzioni) quello della legenda.
   Strisce.calcola(riga) restituisce i numeri usati (minimo, massimo, posti), utile per i controlli. */
(function (g) {
  'use strict';

  var CSS = '' +
    '.sz{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;color:#000;line-height:1.35}' +
    '.sz *{box-sizing:border-box}' +
    '.sz-leg{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;margin:6px 0 4px;align-items:center}' +
    '.sz-leg span{display:inline-flex;align-items:center;gap:6px;min-width:0}' +
    '.sz-leg i{display:inline-block;flex:none}' +
    '.sz-grp{font-size:20px;font-weight:800;margin:30px 0 4px;padding-left:10px;border-left:12px solid var(--c,#000);line-height:1.2}' +
    '.sz-riga{padding:14px 0 12px;border-bottom:1px solid #ddd}' +
    '.sz-top{display:flex;justify-content:space-between;align-items:baseline;gap:12px}' +
    '.sz-lab{font-weight:700;font-size:16px;min-width:0;overflow-wrap:anywhere}' +
    '.sz-val{font-size:32px;font-weight:800;letter-spacing:-.02em;line-height:1;color:var(--ca,#000);text-align:right;flex:none;max-width:55%;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}' +
    '.sz-val.no{font-size:14px;font-weight:700;letter-spacing:0;color:#444}' +
    '.sz-sub{font-size:13px;color:#333;margin:2px 0 12px}' +
    '.sz-strip{position:relative;height:14px;background:#eee;margin:0 14px}' +
    '.sz-strip.dash{background:repeating-linear-gradient(90deg,#ccc 0 8px,#fff 8px 12px)}' +
    '.sz-tk{position:absolute;top:-6px;bottom:-6px;width:3px;margin-left:-1.5px;background:#000}' +
    '.sz-st{position:absolute;top:2px;bottom:2px;width:4px;margin-left:-2px;background:#666}' +
    '.sz-dA,.sz-dB{position:absolute;top:50%;border-radius:50%}' +
    '.sz-dA{width:18px;height:18px;margin:-9px 0 0 -9px;background:var(--ca,#000);border:2px solid #fff;z-index:2}' +
    '.sz-dB{width:26px;height:26px;margin:-13px 0 0 -13px;background:var(--cb,#666);border:2px solid #fff;z-index:1}' +
    '.sz-dB.s{position:static;display:inline-block;width:14px;height:14px;margin:0 4px 0 0;border:0;vertical-align:-2px}' +
    '.sz-ends{display:flex;justify-content:space-between;gap:12px;font-size:13px;color:#333;margin-top:8px}' +
    '.sz-ends span{max-width:48%;min-width:0;overflow-wrap:anywhere}' +
    '.sz-ends span:last-child{text-align:right}' +
    '.sz-ends b{font-weight:700;color:#000}' +
    '.sz-cmp{font-size:14px;margin-top:8px;overflow-wrap:anywhere}' +
    '.sz-flag{font-size:13px;margin-top:6px;font-weight:700}' +
    '.sz-pill{display:inline-block;font-size:12px;border:1px solid #000;padding:0 6px;margin:0 6px 2px 0;white-space:nowrap;font-weight:700}' +
    '@media(max-width:480px){.sz-val{font-size:26px}.sz-lab{font-size:15px}.sz-grp{font-size:18px}}';

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function it(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }

  function stile() {
    if (typeof document === 'undefined' || document.getElementById('sz-css')) return;
    var s = document.createElement('style');
    s.id = 'sz-css';
    s.appendChild(document.createTextNode(CSS));
    document.head.appendChild(s);
  }

  /* numeri di una riga: scala, estremi, pari, posti */
  function calcola(r) {
    var tutti = r.punti.filter(function (p) { return p.v != null; });
    var rk = tutti.filter(function (p) { return p.pos !== false; });
    var base = (r.tratteggio || !rk.length) ? tutti : rk;
    var out = { n: rk.length, min: null, max: null, nMin: 0, nMax: 0, nomiMin: [], nomiMax: [], posto: {}, scala: base.length };
    if (!base.length) return out;
    var vals = base.map(function (p) { return p.v; });
    out.min = Math.min.apply(null, vals);
    out.max = Math.max.apply(null, vals);
    base.forEach(function (p) {
      if (p.v === out.min) { out.nMin++; out.nomiMin.push(p.nome); }
      if (p.v === out.max) { out.nMax++; out.nomiMax.push(p.nome); }
    });
    rk.forEach(function (p) {
      var k = 1;
      rk.forEach(function (q) { if (q.v > p.v) k++; });
      out.posto[p.id] = k;
    });
    return out;
  }

  function percento(c, v) {
    if (v == null || c.min == null) return null;
    if (c.max === c.min) return 50;
    return Math.max(0, Math.min(100, 100 * (v - c.min) / (c.max - c.min)));
  }

  function trova(r, id) {
    if (id == null) return null;
    for (var i = 0; i < r.punti.length; i++) if (r.punti[i].id === id) return r.punti[i];
    return null;
  }

  function descrPosto(r, c, p) {
    if (p.pos === false || p.v === 0 || c.posto[p.id] == null) return '';  // con zero il posto a pari merito non dice nulla
    var k = c.posto[p.id], pari = 0;
    r.punti.forEach(function (q) { if (q.pos !== false && q.v === p.v) pari++; });
    return k + '° su ' + c.n + (pari > 1 ? ', a pari con altri ' + (pari - 1) : '');
  }

  function estremo(f, n, nomi, tratt) {
    if (n > 1) return '<b>' + esc(f) + '</b> ' + n + ' ' + (tratt ? 'zone' : 'quartieri') + ' a pari';
    return '<b>' + esc(f) + '</b> ' + esc(nomi[0]);
  }

  function riga(r, o) {
    o = o || {};
    var c = calcola(r), fm = r.fmt || String;
    var A = trova(r, o.a && o.a.id), B = trova(r, o.b && o.b.id);
    var nA = o.a ? o.a.nome : '', nB = o.b ? o.b.nome : '';
    var h = '<div class="sz-riga" id="' + esc(r.dom || ('r-' + r.id)) + '">';
    var unita = r.unita ? esc(r.unita) : '';

    // valore grande del luogo scelto
    var vTxt, sub = [];
    if (A && A.v != null) {
      vTxt = '<span class="sz-val">' + esc(fm(A.v)) + '</span>';
      var ps = descrPosto(r, c, A);
      if (ps) sub.push(esc(ps));
    } else {
      vTxt = '<span class="sz-val no">non disponibile</span>';
    }
    h += '<div class="sz-top"><span class="sz-lab">' + esc(r.titolo) + '</span>' + vTxt + '</div>';

    if (r.citta && r.citta.v != null) sub.push(esc(r.citta.etichetta || 'città') + ' ' + esc(fm(r.citta.v)));
    else if (r.citta && r.citta.testo) sub.push(esc(r.citta.testo));
    if (unita) sub.push(unita);
    if (r.anno) sub.push(esc(r.anno));
    (r.etichette || []).forEach(function (e) { sub.push(esc(e)); });
    h += '<div class="sz-sub">' + sub.join(' · ') + '</div>';

    // striscia
    var ar = [];
    ar.push(r.titolo + (c.min != null ? ', dal più basso ' + fm(c.min) + ' al più alto ' + fm(c.max) : ''));
    if (A && A.v != null) ar.push(nA + ' ' + fm(A.v));
    if (B && B.v != null) ar.push(nB + ' ' + fm(B.v));
    h += '<div class="sz-strip' + (r.tratteggio ? ' dash' : '') + '" role="img" aria-label="' + esc(ar.join('; ')) + '">';
    if (r.tratteggio) {
      r.punti.forEach(function (p) {
        if (p.v == null || (A && p.id === A.id) || (B && p.id === B.id)) return;
        h += '<i class="sz-st" style="left:' + percento(c, p.v).toFixed(1) + '%" title="' + esc(p.nome + ' ' + fm(p.v)) + '"></i>';
      });
    }
    if (r.citta && r.citta.v != null && c.min != null)
      h += '<i class="sz-tk" style="left:' + percento(c, r.citta.v).toFixed(1) + '%" title="' + esc((r.citta.etichetta || 'città') + ' ' + fm(r.citta.v)) + '"></i>';
    if (B && B.v != null) h += '<i class="sz-dB" style="left:' + percento(c, B.v).toFixed(1) + '%" title="' + esc(nB + ' ' + fm(B.v)) + '"></i>';
    if (A && A.v != null) h += '<i class="sz-dA" style="left:' + percento(c, A.v).toFixed(1) + '%" title="' + esc(nA + ' ' + fm(A.v)) + '"></i>';
    h += '</div>';

    // capi
    if (c.min != null) {
      var nm = r.tratteggio ? function (a) { return 'stazione di ' + a; } : null;
      var dmin = c.nomiMin.map(function (x) { return nm ? nm(x) : x; });
      var dmax = c.nomiMax.map(function (x) { return nm ? nm(x) : x; });
      h += '<div class="sz-ends"><span>' + estremo(fm(c.min), c.nMin, dmin, r.tratteggio) + '</span><span>' + estremo(fm(c.max), c.nMax, dmax, r.tratteggio) + '</span></div>';
    }

    // confronto
    if (o.b) {
      h += '<div class="sz-cmp"><i class="sz-dB s"></i> ' + esc(nB) + ' ';
      if (B && B.v != null) {
        var pb = descrPosto(r, c, B);
        h += esc(fm(B.v)) + (pb ? ' · ' + esc(pb) : '');
      } else h += '<span style="color:#444">' + esc((B && B.mancante) || 'dato non disponibile') + '</span>';
      h += '</div>';
    }

    // avvisi per luogo
    function avv(p, nome, scelto) {
      if (!p) return '';
      var t = '';
      if (p.flag) t += '<span class="sz-pill">' + esc(p.flag) + '</span>' + (p.nota ? esc(p.nota) + ' ' : '');
      if (p.v != null && c.min != null && (p.v < c.min || p.v > c.max))
        t += esc('Il valore sta fuori dalla striscia: ' + (p.v < c.min ? 'sotto il più basso, ' + fm(c.min) : 'sopra il più alto, ' + fm(c.max)) + '.');
      if (p.v == null && scelto && p.mancante) t += esc(p.mancante);
      return t ? '<div class="sz-flag">' + (o.b ? esc(nome) + ': ' : '') + t + '</div>' : '';
    }
    h += avv(A, nA, true) + avv(B, nB, false);
    if (r.avviso) h += '<div class="sz-flag">! ' + esc(r.avviso) + '</div>';
    if (r.coda) h += r.coda;
    return h + '</div>';
  }

  function legenda(o) {
    o = o || {};
    var h = '<div class="sz-leg"><span><i style="width:14px;height:14px;border-radius:50%;background:' + esc(o.colA || '#000') + '"></i> ' + esc(o.a ? o.a.nome : 'luogo scelto') + '</span>';
    if (o.b) h += '<span><i style="width:14px;height:14px;border-radius:50%;background:' + esc(o.colB || '#666') + '"></i> ' + esc(o.b.nome) + ' (confronto)</span>';
    h += '<span><i style="width:3px;height:16px;background:#000"></i> ' + esc(o.cittaEtichetta || 'media della città') + '</span></div>';
    h += '<div style="font-size:13px">Ogni striscia va dal valore più basso (a sinistra) al più alto (a destra) tra ' + esc(o.luoghi || 'i luoghi') + '. Posizione: 1° = il valore più alto.</div>';
    return h;
  }

  function disegna(el, o) {
    stile();
    var h = '<div class="sz" style="--ca:' + esc(o.colA || '#000') + ';--cb:' + esc(o.colB || '#666') + '">' + (o.senzaLegenda ? '' : legenda(o));
    (o.gruppi || []).forEach(function (gr) {
      if (!gr.righe || !gr.righe.length) return;
      h += '<div style="--c:' + esc(gr.colore || '#000') + '">';
      if (gr.titolo) h += '<h3 class="sz-grp">' + esc(gr.titolo) + '</h3>';
      h += gr.righe.map(function (r) { return r.html != null ? r.html : riga(r, o); }).join('');
      h += '</div>';
    });
    el.innerHTML = h + '</div>';
  }

  g.Strisce = { disegna: disegna, riga: riga, legenda: legenda, calcola: calcola, stile: stile };
})(typeof window !== 'undefined' ? window : this);
