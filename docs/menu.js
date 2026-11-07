/* Menu del sito "Milano in dati": barra in cima a ogni pagina, con il link alla home
   e l'elenco di tutte le sezioni. Nessuna dipendenza.
   Ogni pagina lo carica con:  <script src="../menu.js" defer></script>  (sulla home: menu.js).

   >>> QUANDO SI AGGIUNGE (O SI RINOMINA) UNA SEZIONE: aggiornare l'elenco SEZIONI qui sotto,
   >>> nello stesso ordine e con le stesse etichette dell'elenco numerato di docs/index.html.
   >>> Vedi docs/MENU_README.md. */
(function () {
  'use strict';

  // path = cartella della sezione, relativa a docs/ (con la barra finale)
  var SEZIONI = [
    { path: 'temperature/',       label: 'Temperature' },
    { path: 'vie/',               label: 'Donne nelle vie' },
    { path: 'beni-culturali/',    label: 'Beni culturali' },
    { path: 'elezioni/',          label: 'Elezioni' },
    { path: 'aria/',              label: 'Aria' },
    { path: 'area-c/',            label: 'Area C' },
    { path: 'bici-auto-mezzi/',   label: 'Bici, auto o mezzi' },
    { path: 'scala/',             label: 'La Scala' },
    { path: 'citta-15-minuti/',   label: 'La città dei 15 minuti' },
    { path: 'violenza-politica/', label: 'Violenza politica' },
    { path: 'milano-raccontata/', label: 'Milano raccontata' },
    { path: 'neve-e-nebbia/',     label: 'Neve e nebbia' },
    { path: 'derby/',             label: 'Il derby' },
    { path: 'nomi-fermate/',      label: 'Nomi delle fermate' },
    { path: 'cinema-spariti/',    label: 'Cinema spariti' },
    { path: 'acqua-del-sindaco/', label: 'Acqua del sindaco' },
    { path: 'fogne/', label: 'Acqua e fogne' },
    { path: 'censimenti/',       label: 'Censimenti' },
    { path: 'prezzi-case/',      label: 'Prezzi delle case' },
    { path: 'bilancio-comune/',  label: 'Bilancio del Comune' },
    { path: 'appalti/',          label: 'Appalti pubblici' },
    { path: 'affitti-brevi/',    label: 'Affitti brevi' },
    { path: 'case-servizi-reddito/', label: 'Servizi e prezzi delle case' },
    { path: 'alberi/',           label: 'Alberi della città' },
    { path: 'cani/',             label: 'Cani di Milano' },
    { path: 'morti/',            label: 'Morti giorno per giorno' },
    { path: 'matrimoni/',        label: 'Matrimoni e separazioni' },
    { path: 'biblioteche/',      label: 'Biblioteche' },
    { path: 'redditi/',          label: 'Redditi dal 2000' },
    { path: 'scuole/',           label: 'Scuole' },
    { path: 'pioggia/',          label: 'Quanto piove' },
    { path: 'caldo/',            label: 'Isola di calore' },
    { path: 'costo-vita/',       label: 'Quanto costa vivere' },
    { path: 'metro/',            label: 'Il metrò' },
    { path: 'ristoranti/',       label: 'Cosa si mangia' },
    { path: 'turisti/',          label: 'Turisti' },
    { path: 'pietre-inciampo/',  label: "Pietre d'inciampo" },
    { path: 'luoghi-cercati/',   label: 'Luoghi più cercati' },
    { path: 'scuole-domani/', label: 'Scuole di domani' },
    { path: 'quartieri-che-cambiano/', label: 'Quartieri che cambiano' },
    { path: 'pollini/', label: 'Pollini' },
    { path: 'case-popolari/', label: 'Case popolari vuote' },
    { path: 'beni-confiscati/', label: 'Beni confiscati' },
    { path: 'voto-reddito/', label: 'Voto e reddito' },
    { path: 'antenne/', label: 'Antenne dei cellulari' },
    { path: 'costruzioni/', label: 'Dove si costruisce' },
    { path: 'arrivi-partenze/', label: 'Chi arriva e chi lascia' },
    { path: 'comunita/', label: 'Le comunità' },
    { path: 'eta/', label: 'Età e centenari' },
    { path: 'benessere/', label: 'Benessere ISTAT' },
    { path: 'statue/', label: 'Statue e monumenti' },
    { path: 'incroci/', label: 'Incroci e incidenti' },
    { path: 'amministratori/', label: 'Chi governa Milano' },
    { path: 'botteghe/', label: 'Botteghe storiche' },
    { path: 'suolo/', label: 'Quanto suolo si consuma' },
    { path: 'pendolari/', label: 'Pendolari' },
    { path: 'reati/', label: 'Reati denunciati' },
    { path: 'quartiere/', label: 'Il tuo quartiere' },
    { path: 'permettersi/', label: 'Chi può permettersi dove' },
    { path: 'viaggio-linea/', label: 'Un viaggio in tram' },
    { path: 'speranza-vita/', label: 'Quanto si vive' },
    { path: 'case-vuote/', label: 'Le case vuote' },
    { path: 'fondi-quartieri/', label: 'Soldi per i quartieri popolari' },
    { path: 'quartiere-ideale/', label: 'Il mio quartiere ideale' },
    { path: 'divisa/', label: 'Quanto è divisa Milano' },
    { path: 'sfratti/', label: 'Gli sfratti' },
    { path: 'lavoro/', label: 'Il lavoro per quartiere' },
    { path: 'rigenerazione/', label: 'Progetti di rigenerazione' },
    { path: 'rifiuti/', label: 'Rifiuti e differenziata' },
    { path: 'poverta-educativa/', label: 'Povertà educativa' },
    { path: 'parcheggi/', label: 'Parcheggi' },
    { path: 'targhe/', label: 'Lapidi e targhe' },
    { path: 'palazzi/', label: 'Età dei palazzi' },
    { path: 'reati-citta/', label: 'Reati e sicurezza in città' },
    { path: 'omicidi/', label: 'Gli omicidi' },
    { path: 'il-tuo-giorno/', label: 'Il tuo giorno a Milano' },
    { path: 'milano-trema/', label: 'Quante volte Milano ha tremato' },
    { path: 'indovina-quartiere/', label: 'Indovina il quartiere' },
    { path: 'attesa-fermata/', label: 'Quanto aspetti alla fermata' },
    { path: 'chilometri-duomo/', label: 'Milano per chilometri dal Duomo' },
    { path: 'storia-centro/', label: 'Il centro cambia' },
    { path: 'storia-case/', label: 'Le case vuote' },
    { path: 'anno-covid/', label: 'L’anno del Covid' },
    { path: 'nascite/', label: 'Nascite e mamme' },
    { path: 'tribunale/', label: 'Il tribunale di Milano' },
    { path: 'auto/', label: 'Le auto dei milanesi' },
    { path: 'carceri/', label: 'Le carceri di Milano' },
    { path: 'musei/', label: 'Musei' },
    { path: 'aeroporti/', label: 'Aeroporti' },
    { path: 'bici/', label: 'BikeMi e bici' },
    { path: 'medici-farmacie/', label: 'Medici e farmacie' },
    { path: 'consiglio/', label: 'Consiglio comunale' },
    { path: 'verde/', label: 'Parchi e verde' },
    { path: 'sport/', label: 'Impianti sportivi' },
    { path: 'violenza-donne/', label: 'Violenza contro le donne' },
    { path: 'terzo-settore/', label: 'Associazioni e terzo settore' },
    { path: 'imprese/', label: 'Imprese che nascono e muoiono' },
    { path: 'elenco/', label: 'Elenco di tutte le pagine' },
    { path: 'fonti/', label: 'Fonti e metodo' },
    { path: 'oltre-il-reddito/', label: 'Oltre il reddito' },
    { path: 'hinterland/', label: 'Hinterland' },
    { path: 'telefoni-pubblici/', label: 'Telefoni pubblici' },
    { path: 'tasse/', label: 'Tasse' },
    { path: 'vibrazioni/', label: 'Il respiro di Milano' },
    { path: 'consumi/', label: 'Quanta corrente, quanta acqua' }
  ];

  if (document.getElementById('mid-menu')) return; // già inserito

  // Radice del sito = cartella in cui sta menu.js (funziona anche se il sito è in una sottocartella)
  var script = document.currentScript;
  if (!script) {
    var all = document.getElementsByTagName('script');
    for (var i = 0; i < all.length; i++) {
      if (/(^|\/)menu\.js(\?|#|$)/.test(all[i].getAttribute('src') || '')) { script = all[i]; break; }
    }
  }
  var rootUrl = script ? new URL('./', script.src) : new URL('./', location.href);
  var rootPath = rootUrl.pathname;

  // Sezione corrente: il percorso della pagina, senza "index.html", confrontato con quello di ogni sezione
  var here = location.pathname.replace(/index\.html$/, '');
  // le anteprime (anteprima/<pagina>/) si comportano come la pagina vera: stessi capitoli, stessa voce accesa
  if (here.indexOf(rootPath + 'anteprima/') === 0) here = rootPath + here.slice((rootPath + 'anteprima/').length);
  var current = null;
  var isHome = (here === rootPath);
  for (var j = 0; j < SEZIONI.length; j++) {
    // la pagina e' nella sezione se il suo percorso comincia con quello della sezione (vale anche per le sottopagine, es. scala/prime/)
    if (here === rootPath + SEZIONI[j].path || here.indexOf(rootPath + SEZIONI[j].path) === 0) { current = SEZIONI[j].path; break; }
  }

  var css =
    '#mid-menu{font:15px/1.4 system-ui,"Segoe UI",Arial,sans-serif;color:#000;background:#fff;' +
    'border-bottom:1px solid #000;margin:0;padding:0;box-sizing:border-box;text-align:left;' +
    'position:sticky;top:0;z-index:1500;box-shadow:0 2px 6px rgba(0,0,0,.12)}' +
    '#mid-menu *{box-sizing:border-box}' +
    '#mid-menu .mid-bar{display:flex;flex-wrap:nowrap;align-items:center;justify-content:space-between;' +
    'gap:4px 12px;max-width:1100px;margin:0 auto;padding:6px 16px}' +
    '#mid-menu .mid-b{flex:none;display:inline-flex;align-items:center;gap:5px;font:inherit;font-size:14px;line-height:1.2;' +
    'color:#000;background:#fff;border:1.5px solid #000;border-radius:18px;padding:5px 11px;margin:0;min-height:34px;' +
    'white-space:nowrap;cursor:pointer;text-decoration:none}' +
    '#mid-menu .mid-b:hover{background:#eee;text-decoration:none}' +
    '#mid-menu .mid-home{background:#000;color:#fff;font-weight:700}' +
    '#mid-menu .mid-home:hover{background:#333}' +
    '#mid-menu .mid-lnk[aria-current]{background:#ffe1d6;border-color:#ff5a36}' +
    '#mid-menu .mid-toggle{margin-left:auto}' +
    '#mid-menu .mid-toggle[aria-expanded=true]{background:#000;color:#fff}' +
    '@media (max-width:400px){#mid-menu .mid-bar{padding:6px 10px;gap:5px}#mid-menu .mid-b{font-size:13px;padding:5px 9px}#mid-menu .mid-tx{display:none}#mid-menu .mid-toggle{padding:5px 9px}}' +
    '@media (max-width:360px){#mid-menu .mid-home span{display:none}#mid-menu .mid-b{font-size:12.5px;padding:5px 7px}}' +
    '#mid-menu .mid-panel{max-height:calc(100vh - 120px);overflow-y:auto}' +
    '#mid-menu .mid-cap{display:flex;gap:6px;overflow-x:auto;max-width:1100px;margin:0 auto;padding:6px 16px 8px;' +
    'border-top:1px solid #ddd;scrollbar-width:none;-webkit-overflow-scrolling:touch}' +
    '#mid-menu .mid-cap::-webkit-scrollbar{display:none}' +
    '#mid-menu .mid-cap a{flex:none;max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;' +
    'font-size:13px;line-height:1.3;border:1px solid #000;border-radius:14px;padding:4px 10px;color:#000;text-decoration:none}' +
    '#mid-menu .mid-cap a:hover{text-decoration:none;background:#eee}' +
    '#mid-menu .mid-cap a.on{background:#000;color:#fff}' +
    '#mid-menu .mid-prog{height:3px;width:0;background:#ff5a36}' +
    '#mid-menu a{color:#000;text-decoration:none}' +
    '#mid-menu a:hover{text-decoration:underline}' +
    '#mid-menu a:focus-visible,#mid-menu button:focus-visible{outline:2px solid #000;outline-offset:2px}' +
    '#mid-menu .mid-panel{max-width:1100px;margin:0 auto;padding:0 16px 8px}' +
    '#mid-menu .mid-panel[hidden]{display:none}' +
    '#mid-menu ul{list-style:none;margin:0;padding:0;columns:1}' +
    '#mid-menu li{margin:0;padding:0;break-inside:avoid}' +
    '#mid-menu li a{display:block;padding:7px 0;border-top:1px solid #ddd}' +
    '#mid-menu li a[aria-current]{font-weight:700;text-decoration:underline;text-underline-offset:3px}' +
    '#mid-menu .mid-q{display:block;width:100%;font:inherit;color:#000;background:#fff;border:1px solid #000;border-radius:0;padding:6px 10px;margin:0 0 8px;min-height:36px}' +
    '#mid-menu .mid-chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px;padding:0}' +
    '#mid-menu .mid-chip{font:inherit;font-size:14px;color:#000;background:#fff;border:2px solid var(--c);border-radius:0;padding:3px 10px;margin:0;cursor:pointer;min-height:32px}' +
    '#mid-menu .mid-chip[aria-pressed=true]{background:var(--c);color:var(--tc);font-weight:700}' +
    '#mid-menu .mid-chip small{font-size:12px;opacity:.8}' +
    '#mid-menu .mid-vuoto{margin:8px 0;color:#555}' +
    '#mid-menu li[hidden]{display:none}' +
    '@media (min-width:600px){#mid-menu ul{columns:2;column-gap:32px}}' +
    '@media (min-width:900px){#mid-menu ul{columns:3}}' +
    '@media print{#mid-menu{display:none}}';

  var style = document.createElement('style');
  style.id = 'mid-menu-style';
  style.textContent = css;
  document.head.appendChild(style);

  var nav = document.createElement('nav');
  nav.id = 'mid-menu';
  nav.setAttribute('aria-label', 'Sezioni');

  var bar = document.createElement('div');
  bar.className = 'mid-bar';

  // Barra: Home, i due strumenti sui quartieri, Cerca (apre l'elenco di tutte le pagine con la ricerca)
  var ICO_HOME = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><path d="M8 1.5 1 7.5h2v7h4v-4.5h2v4.5h4v-7h2z" fill="currentColor"/></svg>';
  var ICO_CERCA = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><circle cx="6.8" cy="6.8" r="4.8" fill="none" stroke="currentColor" stroke-width="2"/><path d="m10.4 10.4 4.1 4.1" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';
  var home = document.createElement('a');
  home.className = 'mid-b mid-home';
  home.href = rootUrl.href;
  home.innerHTML = ICO_HOME + '<span>Home</span>';
  home.title = 'Milano in dati: la pagina iniziale';
  if (isHome) home.setAttribute('aria-current', 'page');
  bar.appendChild(home);
  [['quartiere/', 'Il tuo quartiere'], ['quartiere-ideale/', 'Quartiere ideale']].forEach(function (x) {
    var a = document.createElement('a');
    a.className = 'mid-b mid-lnk';
    a.href = new URL(x[0], rootUrl).href;
    a.textContent = x[1];
    if (current === x[0]) a.setAttribute('aria-current', 'page');
    bar.appendChild(a);
  });

  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'mid-b mid-toggle';
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'mid-panel');
  btn.setAttribute('aria-label', 'Cerca una pagina');
  btn.innerHTML = ICO_CERCA + '<span class="mid-tx">Cerca</span>';
  bar.appendChild(btn);

  var panel = document.createElement('div');
  panel.className = 'mid-panel';
  panel.id = 'mid-panel';
  panel.hidden = true;

  var ul = document.createElement('ul');
  SEZIONI.forEach(function (s) {
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = new URL(s.path, rootUrl).href;
    a.textContent = s.label;
    if (s.path === current) a.setAttribute('aria-current', 'page');
    li.appendChild(a);
    ul.appendChild(li);
  });
  var lis = ul.children;
  var q = document.createElement('input');
  q.type = 'search'; q.className = 'mid-q'; q.placeholder = 'Cerca una pagina (es. scuole, metro, affitti)'; q.setAttribute('aria-label', 'Cerca una pagina');
  var chipBox = document.createElement('div');
  chipBox.className = 'mid-chips'; chipBox.setAttribute('role', 'group'); chipBox.setAttribute('aria-label', 'Filtra per tema'); chipBox.hidden = true;
  var vuoto = document.createElement('p');
  vuoto.className = 'mid-vuoto'; vuoto.hidden = true; vuoto.textContent = 'Nessuna sezione corrisponde.';
  panel.appendChild(q);
  panel.appendChild(chipBox);
  panel.appendChild(ul);
  panel.appendChild(vuoto);

  // temi.json (letto una sola volta, da tutti): se manca, il menu funziona senza pulsanti dei temi
  var temiP = null;
  function getTemi() {
    if (!temiP) {
      temiP = window.fetch ? fetch(new URL('temi.json', rootUrl).href, { cache: 'no-cache' })
        .then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }) : Promise.resolve(null);
    }
    return temiP;
  }
  function norm(x) { return String(x || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  var temaDi = {}, descDi = {}, filtroTema = '';
  function filtra() {
    var w = norm(q.value).split(/\s+/).filter(Boolean), n = 0;
    for (var m = 0; m < SEZIONI.length; m++) {
      var l = norm(SEZIONI[m].label + ' ' + (descDi[SEZIONI[m].path] || ''));
      var ok = (!filtroTema || temaDi[SEZIONI[m].path] === filtroTema) && w.every(function (x) { return l.indexOf(x) !== -1; });
      lis[m].hidden = !ok; if (ok) n++;
    }
    vuoto.hidden = n !== 0;
    Array.prototype.forEach.call(chipBox.children, function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-tema') === filtroTema ? 'true' : 'false'); });
  }
  q.addEventListener('input', filtra);
  function costruisciTemi() {
    if (chipBox.children.length) return;
    getTemi().then(function (T) {
      try {
        if (!T || !T.temi || !T.pagine || chipBox.children.length) return;
        var cont = {};
        T.pagine.forEach(function (p) { temaDi[p.path] = p.tema; descDi[p.path] = p.descrizione || ''; cont[p.tema] = (cont[p.tema] || 0) + 1; });
        T.temi.forEach(function (t) {
          if (!cont[t.id]) return;
          var b = document.createElement('button');
          b.type = 'button'; b.className = 'mid-chip'; b.setAttribute('data-tema', t.id); b.setAttribute('aria-pressed', 'false');
          b.style.setProperty('--c', t.colore); b.style.setProperty('--tc', t.testo || '#fff');
          b.appendChild(document.createTextNode(t.nome + ' '));
          var sm = document.createElement('small'); sm.textContent = '(' + cont[t.id] + ')'; b.appendChild(sm);
          b.addEventListener('click', function () { filtroTema = (filtroTema === t.id ? '' : t.id); filtra(); });
          chipBox.appendChild(b);
        });
        chipBox.hidden = !chipBox.children.length;
        filtra();
      } catch (e3) { /* niente pulsanti, il menu resta com'era */ }
    });
  }

  nav.appendChild(bar);
  nav.appendChild(panel);

  function setOpen(open) {
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      costruisciTemi();
      // la casella di ricerca pronta per scrivere (sul telefono apre la tastiera: è quello che si vuole toccando "Cerca")
      try { q.focus({ preventScroll: true }); } catch (e4) { q.focus(); }
    }
  }
  btn.addEventListener('click', function () { setOpen(panel.hidden); });
  nav.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { setOpen(false); btn.focus(); }
  });

  document.body.insertBefore(nav, document.body.firstChild);

  // ---- Barra fissa: i capitoli della pagina (dove ce ne sono almeno 4), la linea di lettura,
  // e gli elementi della pagina che restano fermi in alto spostati sotto la barra.
  try {
    var prog = document.createElement('div');
    prog.className = 'mid-prog';
    var cap = null, capH = [];
    var FUORI = /limiti|come (è|e'|&egrave;) fatto|metodo|^file|scaricabil|download|^fonti|pagine collegate|pagine vicine/i;
    function costruisciCapitoli() {
      if (cap || isHome || !current || current === 'elenco/' || current.indexOf('storia-') === 0) return;
      var hs = Array.prototype.filter.call(document.querySelectorAll('h2'), function (h) {
        var t = (h.textContent || '').trim();
        return t && !h.closest('#mid-menu') && !h.closest('#mid-vicine') && !h.closest('details') &&
          h.offsetParent !== null && !FUORI.test(t) && !FUORI.test(h.id || '');
      });
      if (hs.length < 4) return;
      cap = document.createElement('div');
      cap.className = 'mid-cap';
      cap.setAttribute('aria-label', 'Capitoli della pagina');
      hs.forEach(function (h, i) {
        if (!h.id) h.id = 'cap-' + (i + 1);
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent.trim().replace(/^\d+\.\s*/, '');
        a.title = a.textContent;
        cap.appendChild(a);
      });
      capH = hs;
      nav.insertBefore(cap, prog);
      aggiorna();
    }
    nav.appendChild(prog);

    var onK = -1;
    function aggiorna() {
      var navH = nav.offsetHeight;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      prog.style.width = (max > 0 ? Math.min(100, 100 * window.scrollY / max) : 0) + '%';
      if (!cap) return;
      var k = -1;
      for (var i = 0; i < capH.length; i++) { if (capH[i].getBoundingClientRect().top <= navH + 24) k = i; }
      if (k === onK) return;
      onK = k;
      for (var m = 0; m < cap.children.length; m++) cap.children[m].classList.toggle('on', m === k);
      if (k >= 0) {
        var c = cap.children[k];
        cap.scrollLeft = c.offsetLeft - cap.clientWidth / 2 + c.offsetWidth / 2;
      }
    }
    var tick = false;
    window.addEventListener('scroll', function () {
      if (tick) return; tick = true;
      window.requestAnimationFrame(function () { tick = false; aggiorna(); });
    }, { passive: true });

    // gli elementi "sticky" della pagina con top vicino a 0 finirebbero sotto la barra: li sposto sotto
    var altezzaPrima = -1;
    function spostaSticky() {
      // se il body ha un margine interno, la barra lo copre lo stesso: altrimenti il testo che scorre si vede ai lati
      var bs = window.getComputedStyle(document.body);
      nav.style.marginLeft = (-parseFloat(bs.paddingLeft) || 0) + 'px';
      nav.style.marginRight = (-parseFloat(bs.paddingRight) || 0) + 'px';
      nav.style.marginTop = (-parseFloat(bs.paddingTop) || 0) + 'px';
      var navH = nav.offsetHeight;
      document.documentElement.style.scrollPaddingTop = (navH + 8) + 'px';
      if (navH === altezzaPrima) return;
      altezzaPrima = navH;
      var tutti = document.body.querySelectorAll('*');
      for (var i = 0; i < tutti.length; i++) {
        var e = tutti[i];
        if (e === nav || nav.contains(e)) continue;
        var cs = window.getComputedStyle(e);
        if (cs.position !== 'sticky') continue;
        if (e.getAttribute('data-mid-top') === null) {
          if (cs.top === 'auto') continue;
          var t0 = parseFloat(cs.top);
          if (!(t0 < 80)) continue;
          // se un antenato scorre per conto suo (tabelle con barra di scorrimento), lo sticky vale li' dentro: non si tocca
          var p = e.parentElement, propria = false;
          while (p && p !== document.body) {
            var o = window.getComputedStyle(p);
            if (/(auto|scroll|hidden)/.test(o.overflowY + o.overflowX)) { propria = true; break; }
            p = p.parentElement;
          }
          if (propria) continue;
          e.setAttribute('data-mid-top', String(t0));
          if (parseInt(cs.zIndex, 10) >= 1500) e.style.zIndex = '1400';
        }
        e.style.top = (parseFloat(e.getAttribute('data-mid-top')) + navH) + 'px';
      }
    }
    // alcuni titoli si completano dopo (es. "Il 2026"): i nomi dei capitoli si rileggono
    function rinomina() {
      if (!cap) return;
      for (var i = 0; i < capH.length; i++) {
        var t = capH[i].textContent.trim().replace(/^\d+\.\s*/, '');
        if (t && cap.children[i].textContent !== t) { cap.children[i].textContent = t; cap.children[i].title = t; }
      }
    }
    function tutto() { costruisciCapitoli(); rinomina(); spostaSticky(); aggiorna(); }
    tutto();
    window.addEventListener('load', tutto);
    setTimeout(tutto, 2500);
    // sul telefono la barra degli indirizzi che compare e sparisce fa "resize" di continuo: si ricalcola solo se cambia la larghezza
    var rt, larg = window.innerWidth;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(function () { if (window.innerWidth !== larg && panel.hidden) { larg = window.innerWidth; tutto(); } }, 200);
    });
  } catch (e0) { /* barra fissa senza capitoli, pagina intatta */ }

  // ---- "Pagine vicine": in fondo a ogni pagina (non sulla home né sulle bozze), 3-5 link a pagine dello stesso tema.
  // L'elenco dei temi sta in docs/temi.json (letto una volta); se manca o qualcosa va storto, la pagina resta com'è.
  try {
    if (!isHome && current && here.indexOf(rootPath + 'elenco/') !== 0) {
      getTemi()
        .then(function (T) {
          try {
            if (!T || !T.pagine || document.getElementById('mid-vicine')) return;
            var mia = null, i2;
            for (i2 = 0; i2 < T.pagine.length; i2++) { if (T.pagine[i2].path === current) { mia = T.pagine[i2]; break; } }
            if (!mia) return;
            var stesse = T.pagine.filter(function (p) { return p.tema === mia.tema; });
            var pos = stesse.indexOf(mia);
            var vicine = [];
            for (var k = 1; k < stesse.length && vicine.length < 4; k++) vicine.push(stesse[(pos + k) % stesse.length]);
            if (!vicine.length) return;
            var nomeTema = '';
            (T.temi || []).forEach(function (t) { if (t.id === mia.tema) nomeTema = t.nome; });

            var st = document.createElement('style');
            st.id = 'mid-vicine-style';
            st.textContent =
              '#mid-vicine{font:15px/1.4 system-ui,"Segoe UI",Arial,sans-serif;color:#000;background:#fff;' +
              'border-top:1px solid #000;margin:32px 0 0;padding:0;box-sizing:border-box;text-align:left;clear:both}' +
              '#mid-vicine *{box-sizing:border-box}' +
              '#mid-vicine .mv-in{max-width:1100px;margin:0 auto;padding:12px 16px 24px}' +
              '#mid-vicine h2{font:700 15px/1.3 system-ui,"Segoe UI",Arial,sans-serif;margin:0 0 6px;padding:0;color:#000}' +
              '#mid-vicine ul{list-style:none;margin:0;padding:0}' +
              '#mid-vicine li{margin:0;padding:0}' +
              '#mid-vicine li a{display:block;padding:8px 0;border-top:1px solid #ddd;color:#000;text-decoration:none}' +
              '#mid-vicine li a:hover b{text-decoration:underline}' +
              '#mid-vicine li span{display:block;color:#555;font-size:13px}' +
              '#mid-vicine a:focus-visible{outline:2px solid #000;outline-offset:2px}' +
              '@media print{#mid-vicine{display:none}}';
            document.head.appendChild(st);

            var box = document.createElement('aside');
            box.id = 'mid-vicine';
            box.setAttribute('aria-label', 'Pagine vicine');
            var inner = document.createElement('div');
            inner.className = 'mv-in';
            var h = document.createElement('h2');
            h.textContent = 'Pagine vicine' + (nomeTema ? ' · ' + nomeTema : '');
            var ul2 = document.createElement('ul');
            vicine.forEach(function (p) {
              var li = document.createElement('li');
              var a = document.createElement('a');
              a.href = new URL(p.path, rootUrl).href;
              var b = document.createElement('b');
              b.textContent = p.label;
              a.appendChild(b);
              if (p.descrizione) {
                var sp = document.createElement('span');
                sp.textContent = p.descrizione;
                a.appendChild(sp);
              }
              li.appendChild(a);
              ul2.appendChild(li);
            });
            inner.appendChild(h);
            inner.appendChild(ul2);
            box.appendChild(inner);
            document.body.appendChild(box);
          } catch (e2) { /* niente blocco, pagina intatta */ }
        })
        .catch(function () { /* niente blocco, pagina intatta */ });
    }
  } catch (e1) { /* niente blocco, pagina intatta */ }

  // ---- Menu a tendina per i campi "scrivi il tuo quartiere / comune / via" (Davide, 7/11/2026):
  // ogni <input list="..."> della pagina mostra sotto di sé l'elenco delle scelte, filtrato mentre si scrive.
  // Le scelte si leggono dal <datalist> ogni volta (alcune pagine lo riempiono dopo).
  try {
    var st2 = document.createElement('style');
    st2.textContent =
      '.mid-tendina{position:absolute;z-index:1600;background:#fff;border:1.5px solid #000;border-top:0;max-height:264px;overflow-y:auto;' +
      'font:15px/1.3 system-ui,"Segoe UI",Arial,sans-serif;color:#000;box-shadow:0 6px 14px rgba(0,0,0,.18);-webkit-overflow-scrolling:touch}' +
      '.mid-tendina[hidden]{display:none}' +
      '.mid-tendina button{display:block;width:100%;text-align:left;font:inherit;color:#000;background:#fff;border:0;border-top:1px solid #eee;' +
      'padding:10px 12px;margin:0;cursor:pointer;min-height:44px}' +
      '.mid-tendina button:hover,.mid-tendina button.on{background:#ffe1d6}' +
      '.mid-tendina .mid-vuota{padding:10px 12px;color:#555}';
    document.head.appendChild(st2);
    var tend = document.createElement('div');
    tend.className = 'mid-tendina';
    tend.hidden = true;
    tend.setAttribute('role', 'listbox');
    document.body.appendChild(tend);
    var attivo = null, scelte = [], evid = -1;
    var normT = function (x) { return String(x || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, ' ').trim(); };
    function opzioni(inp) {
      var dl = document.getElementById(inp.getAttribute('data-mid-list') || '');
      if (!dl) return [];
      var out = [];
      Array.prototype.forEach.call(dl.querySelectorAll('option'), function (o) {
        var v = o.value || o.textContent; if (v) out.push({ v: v, t: o.label && o.label !== v ? v + ' · ' + o.label : v });
      });
      return out;
    }
    function posiziona() {
      if (!attivo) return;
      var r = attivo.getBoundingClientRect();
      tend.style.left = (r.left + window.scrollX) + 'px';
      tend.style.top = (r.bottom + window.scrollY) + 'px';
      tend.style.width = Math.max(200, r.width) + 'px';
    }
    function apri(inp) {
      attivo = inp;
      var q = normT(inp.value), tutte = opzioni(inp);
      scelte = tutte.filter(function (o) { return !q || normT(o.v).indexOf(q) !== -1 || normT(o.t).indexOf(q) !== -1; });
      // prima quelle che cominciano con quanto scritto
      if (q) scelte.sort(function (a, b) { return (normT(a.v).indexOf(q) === 0 ? 0 : 1) - (normT(b.v).indexOf(q) === 0 ? 0 : 1); });
      if (!tutte.length) { chiudi(); return; }
      if (scelte.length === 1 && normT(scelte[0].v) === q) { chiudi(); return; }
      tend.innerHTML = '';
      evid = -1;
      if (!scelte.length) {
        var vv = document.createElement('div'); vv.className = 'mid-vuota'; vv.textContent = 'Nessun risultato'; tend.appendChild(vv);
      }
      scelte.slice(0, 200).forEach(function (o) {
        var b = document.createElement('button');
        b.type = 'button'; b.setAttribute('role', 'option'); b.textContent = o.t;
        b.addEventListener('pointerdown', function (e) { e.preventDefault(); });
        b.addEventListener('click', function () { scegli(o.v); });
        tend.appendChild(b);
      });
      posiziona();
      tend.hidden = false;
    }
    function chiudi() { tend.hidden = true; evid = -1; }
    function scegli(v) {
      if (!attivo) return;
      var inp = attivo;
      inp.value = v;
      chiudi();
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      inp.dispatchEvent(new Event('change', { bubbles: true }));
      try { inp.blur(); } catch (e5) { /* niente */ }
    }
    function aggancia(inp) {
      if (inp.getAttribute('data-mid-list')) return;
      var id = inp.getAttribute('list');
      if (!id) return;
      inp.setAttribute('data-mid-list', id);
      inp.removeAttribute('list'); // niente doppio elenco del browser
      inp.setAttribute('autocomplete', 'off');
      inp.addEventListener('focus', function () { apri(inp); });
      inp.addEventListener('input', function () { if (document.activeElement === inp) apri(inp); });
      inp.addEventListener('blur', function () { setTimeout(function () { if (attivo === inp) chiudi(); }, 150); });
      inp.addEventListener('keydown', function (e) {
        if (tend.hidden) return;
        var bs = tend.querySelectorAll('button');
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          evid = Math.max(0, Math.min(bs.length - 1, evid + (e.key === 'ArrowDown' ? 1 : -1)));
          Array.prototype.forEach.call(bs, function (b, i) { b.classList.toggle('on', i === evid); });
          if (bs[evid]) bs[evid].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter' && evid >= 0 && scelte[evid]) { e.preventDefault(); scegli(scelte[evid].v); }
        else if (e.key === 'Escape') chiudi();
      });
    }
    function cercaCampi() { Array.prototype.forEach.call(document.querySelectorAll('input[list]'), aggancia); }
    cercaCampi();
    window.addEventListener('load', cercaCampi);
    setTimeout(cercaCampi, 2500);
    window.addEventListener('resize', posiziona);
    window.addEventListener('scroll', function () { if (!tend.hidden) posiziona(); }, { passive: true });
  } catch (e6) { /* senza tendina, i campi restano come erano */ }
})();
