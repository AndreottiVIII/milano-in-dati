"""Costruisce docs/reati-citta/index.html e docs/reati-citta/data/ (rieseguibile).

Uso:  python -I -X utf8 pagina.py <cartella reati-citta assoluta> <cartella docs/reati-citta assoluta>

Legge pulito/riepilogo.json e pulito/*.csv (prodotti da costruisci.py), scrive la pagina con i numeri
del testo presi dai dati (nessun numero scritto a mano nel testo che non venga da riepilogo.json).
"""
import sys, os, json, shutil

BASE, DEST = sys.argv[1], sys.argv[2]
R = json.load(open(os.path.join(BASE, "pulito", "riepilogo.json"), encoding="utf-8"))
A, B, C = R["A"], R["B"], R["C"]


def it(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def sg(x, d=1):
    return ("+" if x > 0 else "−" if x < 0 else "") + it(abs(x), d)


def ann(t, a, y):
    return A["annuale"][t][a][str(y)]  # [denunce, tasso]


def var(t, a, y0, y1):
    return (ann(t, a, y1)[1] / ann(t, a, y0)[1] - 1) * 100


m572, i572 = ann("CP572", "ITC45", 2024), ann("CP572", "IT", 2024)
m612, i612 = ann("CP612BIS", "ITC45", 2024), ann("CP612BIS", "IT", 2024)
mter, iter_ = ann("CP612TER", "ITC45", 2024), ann("CP612TER", "IT", 2024)
tot_m, tot_i = A["tot2024"]["ITC45"], A["tot2024"]["IT"]
st = A["stagionalita"]
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def minmax(t):
    v = st[t]["ITC45"]
    i0, i1 = v.index(min(v)), v.index(max(v))
    return it(min(v), 1), MESI_IT[i0], it(max(v), 1), MESI_IT[i1]


mm572, mm612 = minmax("CP572"), minmax("CP612BIS")


def milano(tab, y):
    return [x for x in B[tab][str(y)] if x["nome"] == "Milano"][0]


r22, r23, r24 = milano("rischio", 2022), milano("rischio", 2023), milano("rischio", 2024)
b22, b23, b24 = milano("buio", 2022), milano("buio", 2023), milano("buio", 2024)
n22, n24 = len(B["rischio"]["2022"]), len(B["rischio"]["2024"])
top24r, top24b = B["rischio"]["2024"][0], B["buio"]["2024"][0]
avg24b = sum(x["v"] for x in B["buio"]["2024"]) / n24
avg24r = sum(x["v"] for x in B["rischio"]["2024"]) / n24
conf = {c["nome"]: c for c in B["confronto"]}
den_rank = {c["nome"]: i + 1 for i, c in enumerate(B["confronto"])}  # gia' ordinati per denunce decrescenti
nap = conf["Napoli"]
gen = conf["Genova"]
agg = dict(zip(C["anni"], C["aggressioni_vgr"]))
quota = dict(zip(C["anni"], C["quota_pct"]))
tot118 = dict(zip(C["anni"], C["totale_vgr"]))
mn118 = min(agg, key=agg.get)
mx118 = max(agg, key=agg.get)
q_min, q_max = min(quota.values()), max(quota.values())

HTML = r'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milano in dati · Reati e sicurezza in città</title>
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
.ctl{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:.5em 0}
.ctl button,.ctl select{font:inherit;border:1px solid var(--line);background:#fff;color:var(--ink);padding:4px 10px;border-radius:14px;cursor:pointer;max-width:100%}
.ctl button.on{border-color:var(--acc);color:var(--acc);font-weight:700}
.lgd{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.85rem;margin:.5em 0} .lgd span{white-space:nowrap} .lgd i{display:inline-block;width:16px;height:12px;vertical-align:-1px;margin-right:4px;border:1px solid #888}
.lgd i.ln{height:0;border:0;border-top:3px solid;vertical-align:3px;width:22px} .lgd i.ln.d{border-top-style:dashed}
.scroll{overflow-x:auto}
.bars{margin:.4em 0} .bars .row{display:grid;grid-template-columns:minmax(100px,38%) 1fr 150px;gap:6px;align-items:center;font-size:.88rem;padding:2px 0}
.bars .nm{line-height:1.2;overflow-wrap:anywhere} .bars .tr{background:#f1f1f1;height:10px;position:relative} .bars .fill{display:block;height:10px;background:var(--acc);position:absolute;top:0}
.bars .v{text-align:right;font-variant-numeric:tabular-nums}
@media(max-width:760px){th,td{padding:5px 4px;font-size:.88rem} .bars .row{grid-template-columns:1fr 1fr;} .bars .row .tr{grid-column:1/3;order:3} .bars .row .v{text-align:right}}
.ch{position:relative;width:100%} .ch svg{display:block;width:100%;font:11px system-ui,Arial,sans-serif} .ch svg text{fill:#111} .ch svg .mu{fill:#666}
.tip{position:absolute;pointer-events:none;background:#fff;border:1px solid #888;padding:4px 8px;font-size:.8rem;line-height:1.35;white-space:nowrap;z-index:5;box-shadow:0 1px 4px rgba(0,0,0,.15)}
details{margin:.4em 0} summary{cursor:pointer;color:var(--acc)} ul.m li{margin:.35em 0}
footer{margin:2.5em 0 1em;font-size:.82rem;color:var(--mut);border-top:1px solid var(--line);padding-top:.8em}
tr.hl td{font-weight:700;background:var(--soft)}
</style><script src="../menu.js" defer></script></head><body><main>
<h1>Reati e sicurezza dentro Milano: che cosa si trova davvero</h1>
<p>La pagina sui <a href="../reati/">reati denunciati</a> arriva fino al comune intero. Qui ho cercato dati aperti più fini (per municipio, quartiere, via, ora del giorno) e altre misure ufficiali che quella pagina non ha. <b>Risposta breve: sotto il livello del comune non esiste nessun dato aperto sui reati.</b> Esistono invece tre serie ufficiali in più, che metto qui: i delitti di violenza in famiglia e stalking (provincia di Milano), quanto ci si sente sicuri (comune di Milano, confrontato con altri 26 comuni) e gli interventi del 118 per aggressioni (fino al 2015).</p>

<div class="warm"><b>Prima di leggere.</b>
<ul>
<li><b>Denunciato non vuol dire commesso.</b> I delitti dell&rsquo;Istat sono quelli che qualcuno denuncia e che la polizia registra. Se si denuncia di più, il numero sale anche senza che accada di più; può contare di più per i reati commessi in casa o tra conoscenti (qui non è misurato).</li>
<li><b>Conta il luogo del reato</b>, non dove abita chi lo subisce o lo commette. Per le percezioni conta invece dove abita chi risponde.</li>
<li><b>Il territorio cambia da una sezione all&rsquo;altra</b>: provincia di Milano (violenza in famiglia e stalking), comune di Milano (sicurezza percepita), &ldquo;118 Milano&rdquo; (interventi). Ogni grafico lo dice.</li>
<li><b>Sentirsi sicuri non è un conteggio di reati</b>: è una risposta a un&rsquo;intervista.</li>
<li>Questa pagina non cerca cause e non dice niente su chi commette i reati; la nazionalità non è stata usata.</li>
</ul>
Tutti i dettagli sono in <a href="#limiti">I limiti dei dati</a>.</div>

<div class="surp"><p>Nel 2024 la provincia di Milano ha <b>__TOT_RATIO__ volte</b> le denunce totali dell&rsquo;Italia per abitante (__TOT_M__ contro __TOT_I__ ogni 100.000), ma per i <b>maltrattamenti in famiglia</b> il suo tasso (__M572__ ogni 100.000) è appena sotto quello italiano (__I572__), e per lo stalking (__M612__ contro __I612__) è sotto.</p>
<p>Il comune di Milano, invece, è <b>il primo di 27 comuni</b> per quota di chi si sente poco o per niente sicuro camminando al buio da solo nella zona in cui abita: <b>__B24__%</b> nel 2024, di poco davanti a __SEC24B__ (media semplice dei 27 comuni: __AVGB__%). Nel 2022 era quinto su __N22__.</p>
<p class="sub">Sono misure diverse (denunce di certi delitti, risposte a un&rsquo;intervista): non si possono sommare né leggere una come spiegazione dell&rsquo;altra.</p></div>

<h2 id="cercato">Che cosa ho cercato e che cosa ho trovato</h2>
<p>Ricerche fatte il 2 novembre 2026, dopo le 20 ricerche per parola chiave sul catalogo del Comune già fatte per la pagina sui reati.</p>
<div class="scroll"><table>
<tr><th>Fonte</th><th>Esito</th></tr>
<tr><td>Comune di Milano, dati aperti (<code>dati.comune.milano.it</code>)</td><td>25 ricerche per parola chiave (polizia locale, sanzioni, verbali, violazioni, sicurezza urbana, furti di biciclette, segnalazioni, ordinanze, vigilanza, multe, contravvenzioni, autovelox, rimozioni, sequestri, aggressioni, interventi, controlli, stupefacenti, vandalismo, graffiti, denunce, pronto intervento, ztl, infrazioni, accertamenti). <b>Nessun dataset di reati, interventi o sanzioni della polizia locale per municipio, quartiere o via.</b> Ci sono: i reati del comune intero (ds564, già nella pagina sui reati), l&rsquo;elenco dei comandi decentrati (ds1302), gli incidenti stradali anche per zona di decentramento (ds175-ds179: un altro tema), gli edifici degradati (ds503) e gli interventi del 118 (ds516, usato sotto).</td></tr>
<tr><td>Regione Lombardia, dati aperti (<code>dati.lombardia.it</code>)</td><td>Ricerche su reati, sicurezza, polizia, criminalità, aggressioni, denunce, furti, violenza, 118. Nessun dato sui reati; solo incidenti stradali, indirizzi delle polizie locali e alcune tabelle di singole polizie locali (altri comuni, per esempio Monza), nessuna per Milano.</td></tr>
<tr><td>Polizia Locale di Milano</td><td>Non ho trovato un rapporto annuale ufficiale. Le cifre complessive (multe, controlli, sequestri) si trovano solo in articoli di stampa che riportano un intervento del sindaco: non le uso come dato.</td></tr>
<tr><td>ATM (aggressioni sulla rete)</td><td>Il documento <i>Rendicontazione di sostenibilità 2025 &ndash; Informazioni sociali</i> considera le aggressioni al personale un rischio (p. 244) e scrive che l&rsquo;aumento degli infortuni 2024-2025 è dovuto anche alle &ldquo;aggressioni registrate sui mezzi&rdquo; (p. 278), ma <b>non dà il numero</b>.</td></tr>
<tr><td>Ministero dell&rsquo;Interno</td><td>I dati per provincia non sono scaricabili in forma aperta (vedi la pagina sui reati). Non ho letto la Relazione al Parlamento sull&rsquo;attività delle forze di polizia, un PDF molto lungo, e non so se contenga tavole utili sotto la provincia.</td></tr>
<tr><td>Sequestri di droga (Relazione annuale della Direzione centrale per i servizi antidroga)</td><td>Esiste una relazione annuale in PDF, che secondo la scheda ha un capitolo su regioni e città metropolitane. Non l&rsquo;ho letta.</td></tr>
<tr><td>PoliS-Lombardia e Università Cattolica, <i>Sicurezza in Lombardia</i> (gennaio 2025)</td><td>Rapporto sui reati nella Città metropolitana di Milano e nelle province lombarde 2011-2023, con dati del Ministero dell&rsquo;Interno. Lo conosco solo da articoli di stampa; non l&rsquo;ho letto.</td></tr>
<tr><td>Istat, banca dati <i>esploradati</i></td><td>Tre tabelle nuove rispetto alla pagina sui reati: altri delitti per mese (violenza in famiglia, stalking), sicurezza percepita nei grandi comuni. Il BES territoriale &ldquo;Sicurezza&rdquo; (province) ripete voci già nella pagina sui reati: non usato.</td></tr>
<tr><td>Questura, Prefettura, Polizia ferroviaria</td><td>Bilanci e cifre solo in articoli di stampa: non usati.</td></tr>
</table></div>

<h2 id="famiglia">1. Violenza in famiglia, stalking e immagini intime diffuse</h2>
<p>La pagina sui reati non ha tre voci che l&rsquo;Istat pubblica a parte: i <b>maltrattamenti contro familiari e conviventi</b>, gli <b>atti persecutori</b> (stalking) e la <b>diffusione illecita di immagini o video sessualmente espliciti</b>. L&rsquo;Istat le dà per provincia, non per comune: qui è la provincia di Milano (la Città metropolitana).</p>
<div class="ctl" id="ctl-fam"></div>
<div class="lgd" id="lg-fam"></div>
<div class="ch" id="ch-fam" role="img" aria-label="Grafico: delitti denunciati ogni 100.000 abitanti, provincia di Milano e Italia, dal 2018"></div>
<p class="src">Delitti commessi nell&rsquo;anno e denunciati, ogni 100.000 abitanti. Fonte: Istat, <i>Altri delitti denunciati dalle forze di polizia all&rsquo;autorità giudiziaria</i>, per mese del commesso delitto (CC BY 4.0). Il tasso usa la popolazione ricavata dai dati dell&rsquo;Istat come nella pagina sui reati (vedi i limiti).</p>
<div class="scroll"><table id="tab-fam"></table></div>
<ul class="m">
<li><b>Maltrattamenti contro familiari e conviventi.</b> Provincia di Milano: __N572__ casi nel 2024 (__M572__ ogni 100.000), contro __I572__ in Italia. Dal 2018 al 2024 il tasso è cambiato di __V572M__% a Milano e di __V572I__% in Italia.</li>
<li><b>Atti persecutori.</b> __N612__ casi nel 2024 (__M612__ ogni 100.000; Italia __I612__). Dal 2018: __V612M__% a Milano, __V612I__% in Italia.</li>
<li><b>Diffusione illecita di immagini.</b> __NTER__ casi nel 2024 (__MTER__ ogni 100.000; Italia __ITER__); erano __NTER19__ nel 2019. L&rsquo;articolo 612-ter del codice penale è del 2019 (legge 69/2019, dato non verificato in questa ricerca): per questo la serie parte da lì.</li>
<li><b>Mese per mese</b> (2019-2024, file in fondo): nessuna stagione netta. A Milano la quota di maltrattamenti va da __MM572A__% (__MM572B__) a __MM572C__% (__MM572D__) del totale; quella degli atti persecutori da __MM612A__% (__MM612B__) a __MM612C__% (__MM612D__). Il mese è quello in cui il delitto è stato commesso.</li>
</ul>

<h2 id="percezione">2. Quanto ci si sente sicuri</h2>
<p>L&rsquo;Istat pubblica per 27 grandi comuni (Milano compreso) due risposte di un&rsquo;indagine campionaria sulle famiglie e sulle persone: quanto è presente il <b>rischio di criminalità nella zona in cui si vive</b> (per le famiglie) e quanto ci si sente <b>sicuri camminando al buio da soli nella zona in cui si abita</b> (persone da 14 anni). Sono dati del 2022, 2023 e 2024.</p>
<div class="ctl" id="ctl-perc"></div>
<div class="bars" id="b-perc"></div>
<p class="src" id="src-perc"></p>
<ul class="m">
<li><b>Rischio di criminalità nella zona</b> (famiglie che rispondono &ldquo;molto&rdquo; o &ldquo;abbastanza&rdquo;), comune di Milano: __R22__% nel 2022 (__R22R__° su __N22__), __R23__% nel 2023 (__R23R__° su 27), __R24__% nel 2024 (__R24R__° su 27, dopo __TOP24R__). Media semplice dei 27 comuni nel 2024: __AVGR__%.</li>
<li><b>Camminare al buio</b> (persone che si sentono &ldquo;poco&rdquo; o &ldquo;per niente&rdquo; sicure), comune di Milano: __B22__% nel 2022 (__B22R__° su __N22__), __B23__% nel 2023 (__B23R__° su 27), __B24__% nel 2024 (__B24R__° su 27, davanti di poco a __SEC24B__). Nel 2024 i &ldquo;per niente sicuri&rdquo; sono __BN24__%; un altro __BX24__% dice di non uscire mai (o mai da solo/a).</li>
</ul>
<p class="warn">I tre anni sono stime di un&rsquo;indagine campionaria, senza margini di errore nel file: <b>non so se la differenza tra 2022 e 2023 a Milano (da __B22__% a __B23__%) sia più grande dell&rsquo;errore</b> di campionamento.</p>
<h3>Percezione e denunce nei 12 comuni più grandi, 2024</h3>
<p>Per i 12 comuni che hanno anche il tasso di denunce della pagina sui reati, ecco le due misure affiancate (ordinate per denunce).</p>
<div class="scroll"><table id="tab-conf"></table></div>
<p class="src">Denunce: tasso del comune, delitti ogni 100.000 abitanti, Istat (pagina <a href="../reati/">Reati denunciati</a>). Percezione: Istat, tabelle <code>DCSS_BEST_PPC</code>. Le due colonne di percezione sono quelle della sezione sopra.</p>
<p>Le due misure non vanno insieme in modo semplice. Napoli è la prima per rischio percepito nella zona (__NAPR__%) ma è __NAPD__ª su 12 per denunce (__NAPDEN__ ogni 100.000); Genova ha la quota più bassa di rischio percepito dei 12 (__GENR__%) ed è __GEND__ª su 12 per denunce (__GENDEN__ ogni 100.000). Milano è seconda sia per denunce sia per percezione del rischio nella zona. Non so spiegare perché, e i dati non lo permettono.</p>

<h2 id="118">3. Interventi del 118 per aggressioni, 2004-2015</h2>
<p>Il Comune pubblica gli interventi del &ldquo;118 Milano&rdquo; per tipo di evento e gravità. Una voce è <b>&ldquo;Aggressioni ed eventi violenti&rdquo;</b>: non sono reati denunciati, sono chiamate di soccorso, con o senza denuncia. La serie si ferma al 2015 e la scheda dice che non verrà aggiornata.</p>
<div class="ch" id="ch-118" role="img" aria-label="Grafico: interventi del 118 per aggressioni ed eventi violenti, 2004-2015"></div>
<p class="src">Interventi del 118 Milano per &ldquo;Aggressioni ed eventi violenti&rdquo;, codici verde, giallo e rosso (il codice bianco c&rsquo;è dal 2012 e non è sommato). Fonte: Comune di Milano, ds516 (CC BY).</p>
<ul class="m">
<li>Da __A2004__ interventi nel 2004 a __A2015__ nel 2015 (__AVAR__%). Il minimo è nel __MN118__ (__AMN__), il massimo nel __MX118__ (__AMX__): nel 2007 cala anche il totale degli interventi del 118 (__T2007__ contro __T2006__ nel 2006), quindi quell&rsquo;anno può essere un problema di registrazione.</li>
<li>Le aggressioni sono tra il __QMIN__% e il __QMAX__% di tutti gli interventi (verde, giallo, rosso): __Q2004__% nel 2004, __Q2015__% nel 2015.</li>
<li>La suddivisione per colore non è confrontabile nel tempo (i rossi passano da __ROSSO06__ nel 2006 a __ROSSO07__ nel 2007): per questo uso il totale.</li>
</ul>

<h2 id="fine">Il livello più fine: perché non c&rsquo;è</h2>
<p>Per municipio, quartiere, via o ora del giorno non ho trovato niente di aperto, né nel Comune né in Regione né in Istat. Non vuol dire che i dati non esistano: la Polizia Locale e le forze di polizia ne hanno. Una strada, che richiede una richiesta formale, sarebbe l&rsquo;accesso civico generalizzato (decreto legislativo 33/2013) al Comune o alla Questura. Non l&rsquo;ho fatta.</p>

<h2 id="limiti">I limiti dei dati</h2>
<div class="warm"><ul>
<li><b>Denunciato non è commesso.</b> Violenza in famiglia, stalking e immagini diffuse sono delitti per cui la differenza tra ciò che accade e ciò che viene denunciato può essere ampia; questi dati non la misurano. Una crescita del tasso può essere più reati, più denunce o l&rsquo;introduzione di nuove regole, e qui non si distingue.</li>
<li><b>Provincia non è città.</b> Le tre voci della sezione 1 sono della provincia di Milano (Città metropolitana, circa __POP__ abitanti nel 2024 secondo il denominatore usato): il comune di Milano non si può isolare. Per Milano le serie partono dal 2018 (maltrattamenti, atti persecutori) e dal 2019 (immagini); l&rsquo;Italia ha dati dal 2014.</li>
<li><b>Anno di riferimento.</b> Nel file l&rsquo;Istat indica per questi delitti il periodo &ldquo;durante l&rsquo;anno di riferimento&rdquo;: non ho letto la nota metodologica completa e non so come siano contati i delitti commessi in un anno e denunciati in un altro (e i maltrattamenti sono spesso reati che durano nel tempo).</li>
<li><b>Denominatore.</b> Il tasso usa la popolazione ricavata come nella pagina sui reati (denunce totali divise per il tasso pubblicato dall&rsquo;Istat): non è la popolazione ufficiale, e dopo il censimento 2011 l&rsquo;Istat segnala un salto non reale.</li>
<li><b>Sicurezza percepita.</b> Stime da indagine campionaria (nel file non ci sono errori di campionamento), 27 comuni nel 2023 e 2024, 26 nel 2022 (manca Rimini), solo tre anni. Il nome dell&rsquo;indagine non è indicato nel file scaricato e non ho verificato le domande esatte. &ldquo;Poco o per niente sicuro&rdquo; non comprende chi dice di non uscire mai. La media dei 27 comuni è semplice, non pesata per abitanti.</li>
<li><b>118.</b> Serie ferma al 2015. Non è dichiarato se &ldquo;118 Milano&rdquo; coincida con i confini del comune. Il file non spiega come viene classificato un intervento come &ldquo;aggressione&rdquo;. Il codice bianco manca prima del 2012.</li>
<li><b>I dati sono &ldquo;congelati&rdquo;</b> alcuni mesi dopo la fine dell&rsquo;anno; i numeri di altre fonti, consolidati dopo, possono differire. L&rsquo;ultimo anno è il 2024.</li>
<li><b>Niente sotto il comune.</b> Mancare di dati aperti non vuol dire che il fenomeno non ci sia in una zona o che ci sia di più in un&rsquo;altra.</li>
<li><b>Le cause.</b> Questi dati non dicono perché i numeri salgono o scendono, né chi commette i reati. Non si possono attribuire le variazioni a politiche, eventi o gruppi di persone. La nazionalità non è stata usata.</li>
</ul></div>

<h2 id="metodo">Come è fatto</h2>
<ul class="m">
<li>Delitti per tipo e mese: Istat, dataflow <code>73_1187_DF_DCCV_ALTRIDELPS_2</code>, aree <code>ITC45</code> (provincia di Milano) e <code>IT</code> (Italia), voci <code>CP572</code>, <code>CP612BIS</code>, <code>CP612TER</code>. Controllo: la somma dei 12 mesi coincide con il totale dell&rsquo;anno in tutti i 34 casi controllati.</li>
<li>Tasso = denunce / popolazione implicita &times; 100.000, con la popolazione implicita già costruita per la pagina sui reati (denunce totali / tasso pubblicato). Le variazioni percentuali sono calcolate sui tassi.</li>
<li>Percezione: dataflow <code>DF_DCSS_BEST_PPC_1_GC</code> (famiglie) e <code>DF_DCSS_BEST_PPC_6_GC</code> (persone da 14 anni), solo il totale dei due sessi. Le percentuali sono la stima delle famiglie (persone) che dà quella risposta divisa per il totale stimato; la somma delle categorie coincide col totale (scarto 0,0%). &ldquo;Molto o abbastanza&rdquo; e &ldquo;poco o per niente sicuro&rdquo; sono somme di due categorie.</li>
<li>118: file ds516 del Comune, letto come testo Windows-1252; somma dei codici verde, giallo, rosso per la voce &ldquo;Aggressioni ed eventi violenti&rdquo;, divisa per la somma di tutti gli interventi con gli stessi codici.</li>
<li>Programmi rieseguibili. Nessun dato personale, nessuna registrazione, nessun accesso aggirato.</li>
</ul>

<h2 id="download">File</h2>
<p><a href="data/famiglia_stalking_annuale.csv">famiglia_stalking_annuale.csv</a> (denunce e tassi per anno), <a href="data/famiglia_stalking_mensile.csv">famiglia_stalking_mensile.csv</a> (per mese), <a href="data/percezione_rischio_criminalita_zona.csv">percezione_rischio_criminalita_zona.csv</a>, <a href="data/percezione_sicurezza_buio.csv">percezione_sicurezza_buio.csv</a>, <a href="data/confronto_denunce_percezione_2024.csv">confronto_denunce_percezione_2024.csv</a>, <a href="data/interventi_118_milano_2004_2015.csv">interventi_118_milano_2004_2015.csv</a>, <a href="data/inventario_fonti.csv">inventario_fonti.csv</a> (indirizzi, data di scaricamento e sha256) e <a href="data/riepilogo.json">riepilogo.json</a>, da cui sono disegnati i grafici.</p>

<p>Vedi anche: <a href="../reati/">Reati denunciati a Milano</a>, <a href="../incroci/">Gli incroci di Milano con più incidenti</a>, <a href="../benessere/">Il benessere della Città metropolitana di Milano</a>.</p>

<footer>
<p><b>Fonti e licenze, scaricate il 2 novembre 2026.</b> Istat, <a href="https://esploradati.istat.it/">esploradati.istat.it</a>: <i>Altri delitti denunciati dalle forze di polizia all&rsquo;autorità giudiziaria</i> (<code>73_1187_DF_DCCV_ALTRIDELPS_2</code>, aggiornamento 23 gennaio 2026 secondo i metadati); <i>Famiglie per percezione del rischio di criminalità nella zona in cui abitano</i> e <i>Persone di 14 anni e più per percezione della sicurezza camminando al buio da soli</i> (<code>DF_DCSS_BEST_PPC_1_GC</code>, <code>DF_DCSS_BEST_PPC_6_GC</code>); licenza Creative Commons Attribution 4.0 (CC BY 4.0; la pagina delle condizioni non è stata riletta il giorno dello scaricamento). Tassi di denunce dei 12 comuni e denominatori: Istat, vedi la pagina sui reati. Interventi del 118 Milano, ds516: Comune di Milano, <a href="https://dati.comune.milano.it/">dati.comune.milano.it</a>, licenza Creative Commons Attribution (CC BY, versione non indicata dal portale), scheda modificata l&rsquo;8 maggio 2026. ATM, <i>Rendicontazione di sostenibilità 2025 &ndash; Informazioni sociali</i> (PDF, <a href="https://risultati.atm.it/">risultati.atm.it</a>): consultato per la tabella delle ricerche, nessun numero ripreso; condizioni d&rsquo;uso non verificate.</p>
<p>Programmi e note: <a href="https://github.com/AndreottiVIII/milano-in-dati">github.com/AndreottiVIII/milano-in-dati</a>.</p>
</footer>
</main>
<script>
(function(){
'use strict';
var ACC='#00695c',WARM='#c26a1b',GRY='#8a8a8a';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function nf(x,d){return x==null?'':Number(x).toLocaleString('it-IT',{minimumFractionDigits:d,maximumFractionDigits:d})}
function f0(x){return x==null?'':Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')}
function f1(x){return nf(x,1)}
function J(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.json()})}
function el(id){return document.getElementById(id)}
function setH(id,h){el(id).innerHTML=h}
function niceStep(r){var p=Math.pow(10,Math.floor(Math.log(r)/Math.LN10)),f=r/p;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p}
function lgdLine(items){return items.map(function(it){return '<span><i class="ln'+(it.dash?' d':'')+'" style="border-top-color:'+it.color+'"></i>'+it.t+'</span>'}).join('')}
var D={};
function lineChart(box,o){
  box.innerHTML='';
  var W=box.clientWidth||320,H=o.h||300,m={l:o.ml||48,r:o.mr||12,t:14,b:26};
  var xs=o.x,x0=xs[0],x1=xs[xs.length-1],y0=o.y0!=null?o.y0:0,y1=0;
  o.series.forEach(function(s){s.vals.forEach(function(v){if(v!=null&&v>y1)y1=v})});
  var sy=niceStep((y1-y0)/5);y1=Math.ceil(y1/sy)*sy;
  var pw=W-m.l-m.r,ph=H-m.t-m.b;
  function X(v){return m.l+(v-x0)/(x1-x0)*pw} function Y(v){return m.t+ph-(v-y0)/(y1-y0)*ph}
  var s='<svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" aria-hidden="true">';
  for(var v=y0;v<=y1+sy/2;v+=sy)s+='<line x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#e3e3e3"/><text class="mu" x="'+(m.l-6)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+nf(v,o.yd||0)+'</text>';
  var step=o.step||(W<520?4:2);
  xs.forEach(function(x){if((x-x0)%step===0){s+='<line x1="'+X(x)+'" x2="'+X(x)+'" y1="'+(m.t+ph)+'" y2="'+(m.t+ph+4)+'" stroke="#888"/><text class="mu" x="'+X(x)+'" y="'+(m.t+ph+17)+'" text-anchor="middle">'+x+'</text>'}});
  s+='<line x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+(m.t+ph)+'" y2="'+(m.t+ph)+'" stroke="#888"/>';
  o.series.forEach(function(se){
    var d='',pen=false;
    se.vals.forEach(function(val,i){if(val==null){pen=false;return}d+=(pen?'L':'M')+X(xs[i]).toFixed(1)+' '+Y(val).toFixed(1);pen=true});
    s+='<path d="'+d+'" fill="none" stroke="'+se.color+'" stroke-width="'+(se.w||2)+'"'+(se.dash?' stroke-dasharray="6 4"':'')+' stroke-linejoin="round"/>';
    se.vals.forEach(function(val,i){if(val!=null)s+='<circle cx="'+X(xs[i]).toFixed(1)+'" cy="'+Y(val).toFixed(1)+'" r="2.5" fill="'+se.color+'"/>'})});
  s+='<line id="vl" y1="'+m.t+'" y2="'+(m.t+ph)+'" stroke="#111" style="display:none"/><rect x="'+m.l+'" y="'+m.t+'" width="'+pw+'" height="'+ph+'" fill="transparent" style="touch-action:pan-y"/></svg>';
  box.innerHTML=s+'<div class="tip" style="display:none"></div>';
  var svg=box.firstChild,tip=box.lastChild,vl=svg.querySelector('#vl'),rect=svg.querySelector('rect:last-of-type');
  function show(ev){var t=ev.touches?ev.touches[0]:ev,r=svg.getBoundingClientRect(),k=W/r.width,px=(t.clientX-r.left)*k;
    var i=Math.round((px-m.l)/pw*(xs.length-1));i=Math.max(0,Math.min(xs.length-1,i));
    vl.setAttribute('x1',X(xs[i]));vl.setAttribute('x2',X(xs[i]));vl.style.display='';
    var rows=o.series.filter(function(se){return se.vals[i]!=null}).sort(function(a,b){return b.vals[i]-a.vals[i]});
    tip.innerHTML='<b>'+xs[i]+'</b><br>'+rows.map(function(se){return '<span style="color:'+se.color+'">&#9632;</span> '+se.name+': '+(o.fmt?o.fmt(se.vals[i]):f0(se.vals[i]))}).join('<br>');
    tip.style.display='';var tw=tip.offsetWidth,left=X(xs[i])/k+10;if(left+tw>r.width)left=X(xs[i])/k-tw-10;if(left<0)left=0;tip.style.left=left+'px';tip.style.top='6px'}
  function hide(){tip.style.display='none';vl.style.display='none'}
  rect.addEventListener('mousemove',show);rect.addEventListener('mouseleave',hide);rect.addEventListener('touchstart',show,{passive:true});rect.addEventListener('touchmove',show,{passive:true});
}
var TIPI=[['CP572','Maltrattamenti in famiglia'],['CP612BIS','Atti persecutori (stalking)'],['CP612TER','Immagini intime diffuse']];
var YRS=[2018,2019,2020,2021,2022,2023,2024];
function fam(){
  var cur=D.famSel||'CP572';
  setH('ctl-fam','<span class="sub">Delitto:</span>'+TIPI.map(function(t){return '<button type="button" data-t="'+t[0]+'" class="'+(t[0]===cur?'on':'')+'">'+t[1]+'</button>'}).join(''));
  Array.prototype.forEach.call(el('ctl-fam').querySelectorAll('button'),function(b){b.addEventListener('click',function(){D.famSel=b.getAttribute('data-t');fam()})});
  var a=D.R.A.annuale[cur];
  function ser(area){return YRS.map(function(y){var v=a[area][String(y)];return v?v[1]:null})}
  setH('lg-fam',lgdLine([{t:'Provincia di Milano',color:ACC},{t:'Italia',color:GRY,dash:true}]));
  lineChart(el('ch-fam'),{x:YRS,step:1,yd:0,fmt:f1,series:[{name:'Provincia di Milano',color:ACC,vals:ser('ITC45'),w:3},{name:'Italia',color:GRY,vals:ser('IT'),dash:true}]});
  var h='<tr><th>Anno</th><th class="r">Milano: denunce</th><th class="r">Milano: per 100.000</th><th class="r">Italia: denunce</th><th class="r">Italia: per 100.000</th></tr>';
  YRS.forEach(function(y){var m=a.ITC45[String(y)],i=a.IT[String(y)];if(!m&&!i)return;
    h+='<tr><td>'+y+'</td><td class="r">'+(m?f0(m[0]):'&ndash;')+'</td><td class="r">'+(m?f1(m[1]):'&ndash;')+'</td><td class="r">'+(i?f0(i[0]):'&ndash;')+'</td><td class="r">'+(i?f1(i[1]):'&ndash;')+'</td></tr>'});
  setH('tab-fam',h);
}
function perc(){
  var ind=D.pInd||'buio',y=D.pY||'2024';
  var yrs=['2022','2023','2024'];
  setH('ctl-perc','<span class="sub">Domanda:</span><button type="button" data-i="buio" class="'+(ind==='buio'?'on':'')+'">Camminare al buio</button><button type="button" data-i="rischio" class="'+(ind==='rischio'?'on':'')+'">Rischio di criminalità nella zona</button> <label class="sub" for="sel-y">Anno:</label><select id="sel-y" aria-label="Scegli l&rsquo;anno">'+yrs.map(function(v){return '<option'+(v===y?' selected':'')+'>'+v+'</option>'}).join('')+'</select>');
  Array.prototype.forEach.call(el('ctl-perc').querySelectorAll('button'),function(b){b.addEventListener('click',function(){D.pInd=b.getAttribute('data-i');perc()})});
  el('sel-y').addEventListener('change',function(){D.pY=this.value;perc()});
  var items=D.R.B[ind][y],max=0;items.forEach(function(it){if(it.v>max)max=it.v});max=Math.ceil(max/10)*10;
  setH('b-perc',items.map(function(it){var M=it.nome==='Milano';return '<div class="row"><span class="nm">'+(M?'<b>':'')+it.rango+'. '+esc(it.nome)+(M?'</b>':'')+'</span><span class="tr"><span class="fill" style="left:0;width:'+(it.v/max*100).toFixed(1)+'%;'+(M?'background:'+WARM:'')+'"></span></span><span class="v">'+(M?'<b>':'')+f1(it.v)+'%'+(M?'</b>':'')+'</span></div>'}).join(''));
  setH('src-perc',(ind==='buio'?'Persone di 14 anni e più che si sentono poco o per niente sicure camminando al buio da sole nella zona in cui abitano':'Famiglie che dicono che il rischio di criminalità nella zona in cui abitano è molto o abbastanza presente')+', '+y+', '+items.length+' comuni. Fonte: Istat (CC BY 4.0). Stime da indagine campionaria.');
}
function conf(){
  var h='<tr><th>Comune</th><th class="r">Denunce per 100.000</th><th class="r">Rischio nella zona (%)</th><th class="r">Poco o per niente sicuri al buio (%)</th></tr>';
  D.R.B.confronto.forEach(function(c){h+='<tr'+(c.nome==='Milano'?' class="hl"':'')+'><td>'+esc(c.nome)+'</td><td class="r">'+f0(c.den)+'</td><td class="r">'+f1(c.risk)+'</td><td class="r">'+f1(c.buio)+'</td></tr>'});
  setH('tab-conf',h);
}
function c118(){
  var C=D.R.C;
  lineChart(el('ch-118'),{x:C.anni,step:W118(),yd:0,y0:0,fmt:f0,series:[{name:'Aggressioni ed eventi violenti',color:ACC,vals:C.aggressioni_vgr,w:3}]});
}
function W118(){return (el('ch-118').clientWidth||320)<520?3:1}
J('data/riepilogo.json').then(function(R){
  D.R=R;fam();perc();conf();c118();
  var tm=null,w0=window.innerWidth;window.addEventListener('resize',function(){if(window.innerWidth===w0)return;w0=window.innerWidth;clearTimeout(tm);tm=setTimeout(function(){fam();c118()},150)});
}).catch(function(e){setH('ctl-fam','<p>Non riesco a caricare i dati ('+esc(e.message)+'). Riprova più tardi.</p>')});
})();
</script>
</body></html>
'''

import csv
_bm = [r for r in csv.DictReader(open(os.path.join(BASE, "pulito", "percezione_sicurezza_buio.csv"), encoding="utf-8")) if r["codice_istat"] == "015146" and r["anno"] == "2024"][0]
pop24 = round(A["annuale"]["CP572"]["ITC45"]["2024"][0] / A["annuale"]["CP572"]["ITC45"]["2024"][1] * 1e5)
REP = {
    "TOT_RATIO": it(tot_m[1] / tot_i[1], 1), "TOT_M": it(tot_m[1]), "TOT_I": it(tot_i[1]),
    "M572": it(m572[1], 1), "I572": it(i572[1], 1), "M612": it(m612[1], 1), "I612": it(i612[1], 1),
    "MTER": it(mter[1], 1), "ITER": it(iter_[1], 1),
    "N572": it(m572[0]), "N612": it(m612[0]), "NTER": it(mter[0]), "NTER19": it(ann("CP612TER", "ITC45", 2019)[0]),
    "V572M": sg(var("CP572", "ITC45", 2018, 2024)), "V572I": sg(var("CP572", "IT", 2018, 2024)),
    "V612M": sg(var("CP612BIS", "ITC45", 2018, 2024)), "V612I": sg(var("CP612BIS", "IT", 2018, 2024)),
    "MM572A": mm572[0], "MM572B": mm572[1], "MM572C": mm572[2], "MM572D": mm572[3],
    "MM612A": mm612[0], "MM612B": mm612[1], "MM612C": mm612[2], "MM612D": mm612[3],
    "B22": it(b22["v"], 1), "B23": it(b23["v"], 1), "B24": it(b24["v"], 1), "B22R": str(b22["rango"]), "B23R": str(b23["rango"]), "B24R": str(b24["rango"]),
    "R22": it(r22["v"], 1), "R23": it(r23["v"], 1), "R24": it(r24["v"], 1), "R22R": str(r22["rango"]), "R23R": str(r23["rango"]), "R24R": str(r24["rango"]),
    "BN24": it(float(_bm["pct_per_niente_sicuro"]), 1), "BX24": it(float(_bm["pct_non_esce_mai_o_mai_da_solo"]), 1), "N22": str(n22), "AVGB": it(avg24b, 1), "AVGR": it(avg24r, 1),
    "SEC24B": f'{B["buio"]["2024"][1]["nome"]} con {it(B["buio"]["2024"][1]["v"], 1)}%', "TOP24R": f'{top24r["nome"]} con {it(top24r["v"], 1)}%',
    "NAPR": it(nap["risk"], 1), "NAPD": str(den_rank["Napoli"]), "NAPDEN": it(nap["den"]),
    "GEND": str(den_rank["Genova"]), "GENDEN": it(gen["den"]), "GENR": it(gen["risk"], 1),
    "A2004": it(agg[2004]), "A2015": it(agg[2015]), "AVAR": sg((agg[2015] / agg[2004] - 1) * 100) + "",
    "MN118": str(mn118), "MX118": str(mx118), "AMN": it(agg[mn118]), "AMX": it(agg[mx118]),
    "T2007": it(tot118[2007]), "T2006": it(tot118[2006]),
    "QMIN": it(q_min, 1), "QMAX": it(q_max, 1), "Q2004": it(quota[2004], 1), "Q2015": it(quota[2015], 1),
    "POP": it(round(pop24, -4)), "ROSSO06": it(C["rosso"]["2006"]), "ROSSO07": it(C["rosso"]["2007"]),
}
# controlli sul testo: nessuna affermazione che non sia vera con i dati
assert b24["rango"] == 1 and top24b["nome"] == "Milano", "Milano non e' piu' prima al buio nel 2024: riscrivere il testo"
assert r24["rango"] == 2 and top24r["nome"] == "Napoli", "il testo assume Napoli prima e Milano seconda per rischio nella zona"
assert nap["risk"] == max(c["risk"] for c in B["confronto"]), "Napoli deve essere prima per rischio tra i 12"
assert gen["risk"] == min(c["risk"] for c in B["confronto"]), "Genova deve avere il rischio piu' basso tra i 12"
assert den_rank["Genova"] == 10, "il testo assume Genova 10a su 12 per denunce"
assert den_rank["Milano"] == 2 and [c for c in B["confronto"]][1]["risk"] == sorted([c["risk"] for c in B["confronto"]], reverse=True)[1], "Milano deve essere seconda per denunce e per rischio"
assert tot_m[1] / tot_i[1] > 1 and m572[1] < i572[1] and m612[1] < i612[1]

html = HTML
for k, v in REP.items():
    html = html.replace("__" + k + "__", v)
assert "__" not in html, [x for x in html.split() if x.startswith("__")][:5]
os.makedirs(os.path.join(DEST, "data"), exist_ok=True)
open(os.path.join(DEST, "index.html"), "w", encoding="utf-8").write(html)
for f in ["famiglia_stalking_annuale.csv", "famiglia_stalking_mensile.csv", "percezione_rischio_criminalita_zona.csv", "percezione_sicurezza_buio.csv",
          "confronto_denunce_percezione_2024.csv", "interventi_118_milano_2004_2015.csv", "inventario_fonti.csv", "riepilogo.json"]:
    shutil.copyfile(os.path.join(BASE, "pulito", f), os.path.join(DEST, "data", f))
print("pagina scritta:", os.path.join(DEST, "index.html"), len(html), "byte")
