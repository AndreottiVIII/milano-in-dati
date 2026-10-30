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
    { path: 'censimenti/',       label: 'Censimenti' }
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
})();
