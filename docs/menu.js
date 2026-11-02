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
    { path: 'caldo/',            label: 'Il quartiere più caldo' },
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
    { path: 'elenco/', label: 'Elenco di tutte le pagine' }
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
  var current = null;
  var isHome = (here === rootPath);
  for (var j = 0; j < SEZIONI.length; j++) {
    // la pagina e' nella sezione se il suo percorso comincia con quello della sezione (vale anche per le sottopagine, es. scala/prime/)
    if (here === rootPath + SEZIONI[j].path || here.indexOf(rootPath + SEZIONI[j].path) === 0) { current = SEZIONI[j].path; break; }
  }

  var css =
    '#mid-menu{font:15px/1.4 system-ui,"Segoe UI",Arial,sans-serif;color:#000;background:#fff;' +
    'border-bottom:1px solid #000;margin:0;padding:0;box-sizing:border-box;text-align:left}' +
    '#mid-menu *{box-sizing:border-box}' +
    '#mid-menu .mid-bar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;' +
    'gap:4px 16px;max-width:1100px;margin:0 auto;padding:6px 16px}' +
    '#mid-menu a{color:#000;text-decoration:none}' +
    '#mid-menu a:hover{text-decoration:underline}' +
    '#mid-menu .mid-home{font-weight:700;padding:4px 0}' +
    '#mid-menu .mid-toggle{font:inherit;color:#000;background:#fff;border:1px solid #000;border-radius:0;' +
    'padding:4px 12px;margin:0;cursor:pointer;min-height:32px}' +
    '#mid-menu .mid-toggle:hover{background:#eee}' +
    '#mid-menu a:focus-visible,#mid-menu button:focus-visible{outline:2px solid #000;outline-offset:2px}' +
    '#mid-menu .mid-panel{max-width:1100px;margin:0 auto;padding:0 16px 8px}' +
    '#mid-menu .mid-panel[hidden]{display:none}' +
    '#mid-menu ul{list-style:none;margin:0;padding:0;columns:1}' +
    '#mid-menu li{margin:0;padding:0;break-inside:avoid}' +
    '#mid-menu li a{display:block;padding:7px 0;border-top:1px solid #ddd}' +
    '#mid-menu li a[aria-current]{font-weight:700;text-decoration:underline;text-underline-offset:3px}' +
    '#mid-menu .mid-home[aria-current]{text-decoration:underline;text-underline-offset:3px}' +
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

  var home = document.createElement('a');
  home.className = 'mid-home';
  home.href = rootUrl.href;
  home.textContent = 'Milano in dati';
  if (isHome) home.setAttribute('aria-current', 'page');

  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'mid-toggle';
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'mid-panel');
  btn.textContent = 'Sezioni ▾';

  bar.appendChild(home);
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
  panel.appendChild(ul);

  nav.appendChild(bar);
  nav.appendChild(panel);

  function setOpen(open) {
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'Sezioni ▴' : 'Sezioni ▾';
  }
  btn.addEventListener('click', function () { setOpen(panel.hidden); });
  nav.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { setOpen(false); btn.focus(); }
  });

  document.body.insertBefore(nav, document.body.firstChild);

  // ---- "Pagine vicine": in fondo a ogni pagina (non sulla home né sulle bozze), 3-5 link a pagine dello stesso tema.
  // L'elenco dei temi sta in docs/temi.json (letto una volta); se manca o qualcosa va storto, la pagina resta com'è.
  try {
    if (!isHome && current && here.indexOf(rootPath + 'elenco/') !== 0 && window.fetch) {
      fetch(new URL('temi.json', rootUrl).href, { cache: 'no-cache' })
        .then(function (r) { return r.ok ? r.json() : null; })
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
})();
