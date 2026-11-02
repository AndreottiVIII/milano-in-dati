"""Costruisce docs/violenza-donne/index.html e docs/violenza-donne/data/ (rieseguibile).

Uso:  python -I -X utf8 pagina.py <cartella violenza-donne assoluta> <cartella docs/violenza-donne assoluta>

Legge pulito/*.csv e pulito/riepilogo.json (prodotti da costruisci.py). Ogni numero del testo viene
calcolato dai dati (nessun numero scritto a mano nel testo, salvo i valori Istat sui femminicidi, che
stanno in pulito/femminicidi_italia_istat.csv e in 'a mano' sono solo i due dettagli del 2024 citati dal report).
"""
import sys, os, csv, json, shutil, collections

BASE, DEST = sys.argv[1], sys.argv[2]
P = os.path.join(BASE, "pulito")


def rcsv(n):
    return list(csv.DictReader(open(os.path.join(P, n), encoding="utf-8")))


RIEP = json.load(open(os.path.join(P, "riepilogo.json"), encoding="utf-8"))


def it(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def sg(x, d=1):
    return ("+" if x > 0 else "−" if x < 0 else "") + it(abs(x), d)


# ---------- dati ----------
ann = {int(r["anno"]): r for r in rcsv("1522_annuale_italia_lombardia.csv")}
qt = {int(r["anno"]): r for r in rcsv("1522_regione_ignota_e_quota.csv")}
mot = collections.defaultdict(int)
for r in rcsv("1522_motivi_trimestri_italia.csv"):
    mot[(r["motivo"], int(r["anno"]))] += int(r["chiamate"])
mens = rcsv("1522_mensile_italia.csv")
punta = rcsv("1522_giorni_di_punta.csv")
cav = {(r["territorio"], r["indicatore"]): r["valore"] for r in rcsv("cav_istat_2024.csv")}
prov = rcsv("centri_lombardia_province.csv")
fem = rcsv("femminicidi_italia_istat.csv")
L = RIEP["lombardia"]
CP = RIEP["cav_per_100mila_donne"]
MED = {int(k): v for k, v in RIEP["mediana_giornaliera"].items()}
N25 = {int(a): v for a, v in RIEP["25_novembre"]}

u = lambda a, k: int(ann[a][k])
ui = lambda a: u(a, "chiamate_valide_utenti_italia")
ul = lambda a: u(a, "chiamate_valide_utenti_lombardia")
vi_ = lambda a: u(a, "chiamate_vittime_italia")
vl_ = lambda a: u(a, "chiamate_vittime_lombardia")
pv = lambda a, b: (b / a - 1) * 100

# grafico annuale
JS_ANN = [{"anno": a, "serie": ann[a]["serie"], "ui": ui(a), "ul": ul(a), "vi": vi_(a), "vl": vl_(a)} for a in sorted(ann)]
JS_Q = [{"anno": a, "ignoto": float(qt[a]["pct_regione_ignota"]), "lom": float(qt[a]["quota_lombardia_su_regione_nota_pct"]),
         "pop": (float(qt[a]["quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"]) if qt[a]["quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"] else None)}
        for a in sorted(qt)]
JS_MOT = [[k, mot[(k, 2023)], mot[(k, 2024)], mot[(k, 2025)]] for k in
          ("aiuto_violenza", "aiuto_stalking", "segnalazione_caso", "info_centri_antiviolenza", "info_servizio_1522", "info_giuridiche", "fuori_target",
           "totale_valide", "totale_non_valide", "totale")]
JS_PUNTA = [{"anno": a, "n25": N25[a], "mediana": MED[a]} for a in sorted(N25)]
JS_PROV = [{"prov": r["provincia"], "albo": int(r["albo_regionale_centri_e_sportelli_apr2026"]), "conv": int(r["convenzionati_centri_e_sportelli_set2026"]),
            "centri": int(r["convenzionati_solo_centri_set2026"]), "cr": int(r["case_rifugio_voci_elenco_provincia_sede_legale"])} for r in prov if r["provincia"] != "Lombardia"]
JS_FEM = [{"anno": int(r["anno"]), "donne": int(r["omicidi_con_vittima_donna"]), "fem": int(r["femminicidi_stimati"])} for r in fem]
JS_CAV = {"Italia": {k[1]: v for k, v in cav.items() if k[0] == "Italia"}, "Lombardia": {k[1]: v for k, v in cav.items() if k[0] == "Lombardia"}}
DATA = {"ann": JS_ANN, "quota": JS_Q, "motivi": JS_MOT, "punta": JS_PUNTA, "prov": JS_PROV, "fem": JS_FEM, "cav": JS_CAV, "lombardia": L, "cavx100k": CP}

# ---------- numeri del testo ----------
mesi_it = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
tot24 = {int(r["mese"]): 0 for r in mens}
for r in mens:
    if int(r["anno"]) == 2024:
        tot24[int(r["mese"])] = int(r["chiamate_utenti_valide"])
top = punta[0]
n_nov_top = sum(1 for r in punta if int(r["mese"]) == 11)
n23 = sum(1 for r in punta if r["anno"] == "2023" and ((int(r["mese"]) == 11 and int(r["giorno"]) >= 22) or (int(r["mese"]) == 12 and int(r["giorno"]) <= 6)))
cav_it, cav_lo = float(cav[("Italia", "centri_antiviolenza_2024")]), float(cav[("Lombardia", "centri_antiviolenza_2024")])
fem24 = [r for r in fem if r["anno"] == "2024"][0]
fem19 = [r for r in fem if r["anno"] == "2019"][0]

REP = {
    "U2017": it(ui(2017)), "U2019": it(ui(2019)), "U2022": it(ui(2022)), "U2023": it(ui(2023)), "U2024": it(ui(2024)), "U2025": it(ui(2025)),
    "L2017": it(ul(2017)), "L2023": it(ul(2023)), "L2024": it(ul(2024)), "L2025": it(ul(2025)),
    "VARU": sg(pv(ui(2023), ui(2024))), "VARL": sg(pv(ul(2023), ul(2024))),
    "V2023": it(vi_(2023)), "V2024": it(vi_(2024)), "VL2023": it(vl_(2023)), "VL2024": it(vl_(2024)),
    "VARV": sg(pv(vi_(2023), vi_(2024))), "VARVL": sg(pv(vl_(2023), vl_(2024))),
    "X2017_2024": it(ui(2024) / ui(2017), 1),
    "IGN24": it(float(qt[2024]["pct_regione_ignota"]), 1), "IGN25": it(float(qt[2025]["pct_regione_ignota"]), 1),
    "IGN19": it(float(qt[2019]["pct_regione_ignota"]), 1), "IGN23": it(float(qt[2023]["pct_regione_ignota"]), 1),
    "Q24": it(float(qt[2024]["quota_lombardia_su_regione_nota_pct"]), 1), "Q25": it(float(qt[2025]["quota_lombardia_su_regione_nota_pct"]), 1),
    "Q19": it(float(qt[2019]["quota_lombardia_su_regione_nota_pct"]), 1),
    "P24": it(float(qt[2024]["quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"]), 1),
    "P19": it(float(qt[2019]["quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"]), 1),
    "N25_24": it(N25[2024]), "N25_21": it(N25[2021]), "N25_25": it(N25[2025]), "MED24": it(MED[2024]), "MED21": it(MED[2021]), "MED25": it(MED[2025]),
    "N25_19": it(N25[2019]), "MED19": it(MED[2019]), "RAP24": it(N25[2024] / MED[2024], 1),
    "TOPN": it(int(top["chiamate_utenti_valide"])), "TOPD": f'{int(top["giorno"])} {mesi_it[int(top["mese"]) - 1]} {top["anno"]}',
    "NNOV": str(n_nov_top), "N23": str(n23), "NTOP": str(len(punta)),
    "CAVIT": it(cav_it), "CAVLO": it(cav_lo), "CAVIT100": it(float(cav[("Italia", "centri_per_100mila_donne_residenti")]), 2),
    "CAVLO100": it(float(cav[("Lombardia", "centri_per_100mila_donne_residenti")]), 2),
    "H24IT": it(float(cav[("Italia", "reperibilita_24_ore_pct")]), 1), "H24LO": it(float(cav[("Lombardia", "reperibilita_24_ore_pct")]), 1),
    "L1522IT": it(float(cav[("Italia", "adesione_1522_pct")]), 1), "L1522LO": it(float(cav[("Lombardia", "adesione_1522_pct")]), 1),
    "ALBO": it(L["albo_righe"]), "ALBOENTI": it(L["albo_enti"]), "CONV": it(L["conv_righe"]), "CONVC": it(L["conv_centri"]), "CONVS": it(L["conv_sportelli"]),
    "ALBOMI": it(L["albo_milano_provincia"]), "CONVMI": it(L["conv_milano_provincia"]), "CONVMIC": it(L["conv_comune_milano"]), "ALBOMIC": it(L["albo_comune_milano"]),
    "ALBOCAV": it(L["albo_struttura"].get("CAV", 0) + L["albo_struttura"].get("CAV-CR", 0)), "ALBOCR": it(L["albo_struttura"].get("CAV-CR", 0)),
    "CR": it(L["cr_righe"]), "CRN": it(L["cr_nomi"]), "CRMI": it(L["cr_milano_provincia"]), "CRMIC": it(L["cr_comune_milano"]),
    "MI100A": it(CP["milano_provincia_albo"], 2), "MI100C": it(CP["milano_provincia_conv"], 2), "LO100A": it(CP["lombardia_albo"], 2), "LO100C": it(CP["lombardia_conv"], 2),
    "DMI": it(CP["donne_milano_provincia_2025"]), "DLO": it(CP["donne_lombardia_2025"]), "DIT": it(CP["donne_italia_2025"]),
    "F19": fem19["omicidi_con_vittima_donna"], "F24": fem24["omicidi_con_vittima_donna"], "FE24": fem24["femminicidi_stimati"], "FE19": fem19["femminicidi_stimati"],
    "MOTA24": it(mot[("aiuto_violenza", 2024)]), "MOTA23": it(mot[("aiuto_violenza", 2023)]), "MOTS24": it(mot[("aiuto_stalking", 2024)]),
    "MOTC23": it(mot[("info_centri_antiviolenza", 2023)]), "MOTC24": it(mot[("info_centri_antiviolenza", 2024)]),
    "VARC": sg(pv(mot[("info_centri_antiviolenza", 2023)], mot[("info_centri_antiviolenza", 2024)])),
    "MOTC25": it(mot[("info_centri_antiviolenza", 2025)]), "MOTA25": it(mot[("aiuto_violenza", 2025)]),
    "NV24": it(mot[("totale_non_valide", 2024)]), "NV25": it(mot[("totale_non_valide", 2025)]),
    "PCTNV24": it(100 * mot[("totale_non_valide", 2024)] / mot[("totale", 2024)], 1),
    "PCTFT24": it(100 * mot[("fuori_target", 2024)] / mot[("totale_valide", 2024)], 1),
}

HTML = r'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milano in dati · Violenza contro le donne</title>
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
@media(max-width:760px){th,td{padding:5px 4px;font-size:.88rem}}
.ch{position:relative;width:100%} .ch svg{display:block;width:100%;font:11px system-ui,Arial,sans-serif} .ch svg text{fill:#111} .ch svg .mu{fill:#666}
.tip{position:absolute;pointer-events:none;background:#fff;border:1px solid #888;padding:4px 8px;font-size:.8rem;line-height:1.35;white-space:nowrap;z-index:5;box-shadow:0 1px 4px rgba(0,0,0,.15)}
details{margin:.4em 0} summary{cursor:pointer;color:var(--acc)} ul.m li{margin:.35em 0}
footer{margin:2.5em 0 1em;font-size:.82rem;color:var(--mut);border-top:1px solid var(--line);padding-top:.8em}
.aiuto{border:2px solid var(--acc);background:#fff;padding:8px 12px;margin:1.2em 0;font-size:1rem}
tr.hl td{font-weight:700;background:var(--soft)}
</style><script src="../menu.js" defer></script></head><body><main>
<h1>Violenza contro le donne: chi chiede aiuto, dove, e chi risponde</h1>
<p>Questa pagina guarda tre cose che i dati aperti permettono di vedere: le <b>chiamate al 1522</b> (il numero nazionale di aiuto), i <b>centri antiviolenza e le case rifugio</b> in Lombardia e a Milano, e il numero dei <b>femminicidi</b> in Italia. Non ci sono casi singoli, nomi o indirizzi dei luoghi di accoglienza. Le <b>denunce</b> per maltrattamenti in famiglia e stalking nella provincia di Milano sono già nella pagina <a href="../reati-citta/#famiglia">Reati e sicurezza in città</a>: qui non le ripeto.</p>

<div class="warm"><b>Prima di leggere.</b>
<ul>
<li><b>Le chiamate e le denunce misurano chi chiede aiuto, non quanta violenza c&rsquo;è.</b> Se più donne conoscono il 1522 o si fidano di più, i numeri salgono anche senza che accada di più. Quanta violenza esiste lo dicono altre indagini (come quella dell&rsquo;Istat sulla sicurezza delle donne), che qui non uso.</li>
<li><b>Si contano telefonate, non persone.</b> La stessa donna può chiamare più volte; chiama anche chi vuole informazioni o segnala il caso di un&rsquo;altra persona.</li>
<li><b>Per il 1522 il territorio è la regione</b>, non Milano: sotto la regione non ci sono dati aperti. Per i centri antiviolenza invece c&rsquo;è l&rsquo;elenco della Regione, anche per comune.</li>
<li><b>Nel 2023 e nel 2025 il modo di registrare le chiamate è cambiato</b>: i numeri di anni diversi non sempre si possono confrontare. Ogni grafico lo dice.</li>
</ul>
Tutti i dettagli sono in <a href="#limiti">I limiti dei dati</a>.</div>

<div class="aiuto"><b>Se hai bisogno di aiuto o vuoi parlare con qualcuno: 1522.</b> Il numero è gratuito, anonimo e risponde 24 ore su 24. In pericolo immediato: 112.</div>

<h2 id="sorprende">Cosa sorprende</h2>
<div class="surp">
<p>Le chiamate valide al 1522 sono passate da <b>__U2017__</b> nel 2017 a <b>__U2024__</b> nel 2024 (__X2017_2024__ volte), in Lombardia da __L2017__ a __L2024__. Ma nel 2023 la registrazione è cambiata: tra il 2023 e il 2024, anni confrontabili, l&rsquo;aumento è del __VARU__% in Italia e del __VARL__% in Lombardia.</p>
<p>Dal 2023, per più di una chiamata valida su tre la regione di chi chiama <b>non si conosce</b> (__IGN23__% nel 2023, __IGN24__% nel 2024, __IGN25__% nel 2025). I numeri per regione sono quindi una parte, non il tutto.</p>
<p>I giorni con più chiamate sono quasi tutti attorno al <b>25 novembre</b>, la Giornata contro la violenza sulle donne: __NNOV__ dei __NTOP__ giorni più alti dal 2018 sono a novembre. Il 25 novembre 2024 le chiamate valide sono state __N25_24__, contro una mediana di __MED24__ al giorno in quell&rsquo;anno.</p>
<p>Secondo l&rsquo;Istat i centri antiviolenza erano <b>__CAVIT__</b> in Italia nel 2024, di cui <b>__CAVLO__ in Lombardia</b>: __CAVLO100__ ogni 100.000 donne residenti in Lombardia, contro __CAVIT100__ in Italia.</p>
<p class="sub">Sono misure diverse (telefonate, strutture, omicidi): non si leggono una come spiegazione dell&rsquo;altra.</p></div>

<h2 id="1522">1. Le chiamate al 1522</h2>
<p>Il 1522 è il numero di pubblica utilità del Dipartimento per le pari opportunità della Presidenza del Consiglio. Le chiamate (e le chat) vengono registrate dalle operatrici e l&rsquo;Istat le pubblica. Una chiamata è &ldquo;valida&rdquo; se chi chiama chiede aiuto o informazioni sul tema; non lo sono gli scherzi e gli errori.</p>
<div class="ctl" id="ctl-ann"></div>
<div class="lgd" id="lg-ann"></div>
<div class="ch" id="ch-ann" role="img" aria-label="Grafico: chiamate al 1522 per anno, Italia o Lombardia"></div>
<p class="src" id="src-ann"></p>
<div class="scroll"><table id="tab-ann"></table></div>
<ul class="m">
<li><b>Chiamate registrate come &ldquo;vittime&rdquo;</b> (nelle tavole dell&rsquo;Istat: persone che chiedono aiuto per sé o segnalano casi di violenza): in Italia __V2023__ nel 2023 e __V2024__ nel 2024 (__VARV__%); in Lombardia __VL2023__ e __VL2024__ (__VARVL__%).</li>
<li>Dal 2025 l&rsquo;Istat unisce due gestori del servizio e due sistemi di registrazione (il primo trimestre viene dal gestore precedente). Le chiamate valide si sommano (__U2025__ in Italia, __L2025__ con regione Lombardia) ma <b>le categorie dei motivi non sono confrontabili</b> con gli anni prima (vedi sotto).</li>
</ul>

<h3>Perché si chiama</h3>
<p>Ogni chiamata valida ha un motivo principale. Confronto 2023 e 2024 (confrontabili tra loro); 2025 è mostrato ma con un cambio di metodo.</p>
<div class="scroll"><table id="tab-mot"></table></div>
<p class="src">Italia, chiamate valide e non valide. Fonte: Istat, <i>Il numero verde 1522: chi chiama, perché e cosa racconta &ndash; anno 2025</i>, tavola 1 (fonte primaria: Dipartimento per le pari opportunità). &ldquo;Vittime&rdquo; = richieste di aiuto per violenza o stalking.</p>
<ul class="m">
<li>Le richieste di <b>informazioni sui centri antiviolenza</b> sono __MOTC23__ nel 2023 e __MOTC24__ nel 2024 (__VARC__%): è il modo più diretto, nei dati aperti, di vedere quante telefonate riguardano la ricerca di un centro (telefonate, non persone). Nel 2025 il numero scende a __MOTC25__, ma lì il metodo è cambiato: le richieste &ldquo;di aiuto per violenza&rdquo; salgono da __MOTA24__ a __MOTA25__. La nota dell&rsquo;Istat spiega che il nuovo sistema permette alle operatrici di rivedere i motivi a fine colloquio e ha una scheda più articolata; non so quanto questo spieghi il salto.</li>
<li>Nel 2024 le chiamate non valide sono __NV24__, il __PCTNV24__% di tutte le chiamate. Le &ldquo;fuori target&rdquo; (chiamate valide ma non pertinenti al servizio) sono il __PCTFT24__% delle valide.</li>
</ul>

<h3>Giorni di punta</h3>
<p>L&rsquo;Istat pubblica anche le chiamate giorno per giorno dal 2018 (solo l&rsquo;Italia intera).</p>
<div class="scroll"><table id="tab-punta"></table></div>
<p class="src">Chiamate valide di utenti, ogni 25 novembre, e mediana dei giorni dell&rsquo;anno. Fonte: Istat, tavola 5. La fonte non spiega le cause dei picchi. Nel 2023 i valori alti durano più di due settimane: __N23__ dei __NTOP__ giorni più alti dal 2018 sono tra il 22 novembre e il 6 dicembre 2023.</p>

<h2 id="lombardia">2. La Lombardia nelle chiamate</h2>
<p>La regione di chi chiama è nota solo per una parte delle chiamate. Qui confronto la quota della Lombardia tra le chiamate con regione nota con la quota di donne residenti in Lombardia sul totale italiano.</p>
<div class="lgd" id="lg-q"></div>
<div class="ch" id="ch-q" role="img" aria-label="Grafico: quota Lombardia tra le chiamate con regione nota e quota di donne residenti"></div>
<p class="src">Chiamate valide di utenti con regione nota (esclusi &ldquo;non risponde&rdquo; e non disponibile). Fonte: Istat, banca dati <i>esploradati</i> e tavola 6 del 2025; popolazione femminile al 1° gennaio dell&rsquo;anno dopo, Istat.</p>
<div class="scroll"><table id="tab-q"></table></div>
<ul class="m">
<li>Nel 2024 la Lombardia ha il __Q24__% delle chiamate con regione nota e il __P24__% delle donne residenti in Italia; nel 2019 erano __Q19__% e __P19__%. Il divario è piccolo e sale dopo che la quota di regione ignota è salita da __IGN19__% (2019) a __IGN24__% (2024) e a __IGN25__% (2025): <b>non lo leggo come &ldquo;in Lombardia si chiama di più&rdquo;</b>.</li>
<li>Per <b>Milano</b> (comune, provincia) il 1522 non pubblica niente: la scala più fine è la regione.</li>
</ul>

<h2 id="centri">3. Centri antiviolenza e case rifugio</h2>
<h3>Il quadro dell&rsquo;Istat, 2024</h3>
<div class="scroll"><table id="tab-cav"></table></div>
<p class="src">Fonte: Istat, <i>esploradati</i>, tabella <i>Centri antiviolenza</i> (<code>78_1260</code>), anno 2024; donne residenti al 1° gennaio 2025 (Italia __DIT__, Lombardia __DLO__). Per 100.000 donne di tutte le età.</p>
<ul class="m">
<li>__CAVLO__ centri in Lombardia su __CAVIT__ in Italia. Il numero coincide con quello dei &ldquo;centri&rdquo; (non sportelli) dell&rsquo;elenco regionale convenzionato (__CONVC__): i due conti sono compatibili.</li>
<li>Quasi tutti i centri aderiscono al 1522 (__L1522LO__% in Lombardia, __L1522IT__% in Italia). La reperibilità 24 ore su 24 è più frequente in Lombardia (__H24LO__% contro __H24IT__%).</li>
</ul>

<h3>Gli elenchi della Regione Lombardia</h3>
<p>La Regione pubblica due elenchi dei centri antiviolenza (con licenza CC0, dominio pubblico) e un elenco delle case rifugio. Qui uso solo i conteggi: niente indirizzi, telefoni o nomi.</p>
<div class="scroll"><table id="tab-prov"></table></div>
<p class="src">Fonte: Regione Lombardia, dati aperti (<code>dati.lombardia.it</code>): <i>Elenco dei centri antiviolenza iscritti all&rsquo;albo regionale</i> (14 aprile 2026), <i>Centri antiviolenza</i> convenzionati con Regione Lombardia (30 settembre 2026), <i>Elenco delle case rifugio iscritte all&rsquo;albo regionale</i> (14 aprile 2026). Licenza CC0.</p>
<ul class="m">
<li><b>Centri e sportelli.</b> L&rsquo;albo regionale elenca __ALBO__ tra centri e sportelli (__ALBOENTI__ enti gestori, aprile 2026); l&rsquo;elenco dei convenzionati ne ha __CONV__ (__CONVC__ centri e __CONVS__ sportelli, settembre 2026). Sono due liste con date e scopi diversi: non coincidono e non le sommo.</li>
<li><b>Milano.</b> Nella provincia (la Città metropolitana) ci sono __ALBOMI__ strutture nell&rsquo;albo e __CONVMI__ nei convenzionati: __MI100A__ e __MI100C__ ogni 100.000 donne residenti (__DMI__), contro __LO100A__ e __LO100C__ in Lombardia. Nel solo comune di Milano le sedi sono __ALBOMIC__ (albo) e __CONVMIC__ (convenzionati). Il confronto con il conto dell&rsquo;Istat sopra non è diretto: lì si contano solo i centri.</li>
<li><b>Case rifugio.</b> L&rsquo;elenco ha __CR__ voci, con __CRN__ nomi diversi; __CRMI__ hanno la sede legale dell&rsquo;ente gestore in provincia di Milano (__CRMIC__ nel comune). Molte case hanno indirizzo segreto, quindi <b>la provincia indica dove ha sede l&rsquo;ente, non dove sono le case</b>, e non si sa quanti posti letto ci siano.</li>
</ul>

<h2 id="accesso">4. L&rsquo;accesso delle donne ai centri</h2>
<p>I dati aperti non dicono quante donne sono state accolte dai centri della Lombardia o di Milano. L&rsquo;Istat ha previsto un indicatore (donne in carico che hanno iniziato un percorso di uscita dalla violenza), ma non l&rsquo;ho trovato nei file scaricati. Quello che si può vedere è indiretto:</p>
<ul class="m">
<li>le <b>richieste di informazioni sui centri</b> fatte al 1522 (tabella dei motivi sopra);</li>
<li>quanti centri ci sono e quali servizi dicono di offrire (reperibilità 24 ore su 24, sportelli sul territorio).</li>
</ul>
<p>Non so quante donne abbiano chiesto aiuto a un centro e non l&rsquo;abbiano ricevuto, né quanto tempo ci voglia per essere accolte: questi dati non esistono in forma aperta.</p>

<h2 id="femminicidi">5. Femminicidi in Italia</h2>
<p>L&rsquo;Istat pubblica ogni anno le vittime di omicidio (dati del Ministero dell&rsquo;Interno) e stima quanti omicidi di donne sono <b>femminicidi</b>, cioè legati al genere della vittima.</p>
<div class="scroll"><table id="tab-fem"></table></div>
<p class="src">Fonte: Istat, <i>Le vittime di omicidio. Anno 2024</i> (25 novembre 2025), testo del report: valori trascritti, non c&rsquo;è una tabella scaricabile a parte. I numeri possono essere rivisti negli anni.</p>
<ul class="m">
<li>Nel 2024 gli omicidi di donne sono stati __F24__, i femminicidi stimati __FE24__ (91,4%). Nel 2019 erano __F19__ e __FE19__. Sono numeri piccoli, che da un anno all&rsquo;altro oscillano.</li>
<li>Sempre secondo l&rsquo;Istat, nel 2024 62 donne sono state uccise dal partner o dall&rsquo;ex partner e 37 da altri familiari. Il report ha anche un grafico per regione, ma non una tabella aperta: <b>per la Lombardia e per Milano non ho un numero affidabile da pubblicare</b>.</li>
</ul>

<h2 id="limiti">I limiti dei dati</h2>
<div class="warm"><ul>
<li><b>Chiamate non sono persone.</b> Una donna può telefonare più volte; chi chiama non è sempre la vittima. Il sistema non controlla i doppioni anche per ragioni di privacy (nota metodologica Istat).</li>
<li><b>Cambi di registrazione.</b> Nel 2022 la piattaforma è stata modificata e le tavole dal 2023 hanno &ldquo;un&rsquo;interruzione di serie&rdquo; (Istat). Nel 2025 il primo trimestre viene dal gestore precedente, i tre successivi da un&rsquo;estrazione che unisce vecchio e nuovo gestore: le categorie (per esempio &ldquo;aiuto per violenza&rdquo; o &ldquo;informazioni sul servizio&rdquo;) cambiano molto da un trimestre all&rsquo;altro per questo motivo, non perché cambi il fenomeno. Per questo non faccio una linea unica 2013-2025.</li>
<li><b>Regione ignota.</b> Per il __IGN24__% delle chiamate valide nel 2024 e il __IGN25__% nel 2025 la regione non è nota (non risponde o non disponibile). Le tavole regionali sono quindi parziali e il peso della regione ignota cambia da un anno all&rsquo;altro.</li>
<li><b>Solo la regione.</b> Non esistono dati aperti sul 1522 per provincia o comune. Milano è dentro la Lombardia.</li>
<li><b>Elenchi regionali.</b> I due elenchi dei centri hanno date, regole e righe diverse (centri, sportelli, enti). Nelle case rifugio la provincia è quella dell&rsquo;ente, non della casa. I numeri di posti e di donne accolte non ci sono.</li>
<li><b>Donne accolte.</b> I file scaricati dell&rsquo;Istat sui centri contengono i centri e i servizi, non le donne accolte. Non ho cercato dati nei bilanci dei singoli centri.</li>
<li><b>Femminicidi.</b> La definizione è dell&rsquo;Istat e usa più variabili sulla vittima e sull&rsquo;autore; altre fonti (associazioni, rapporti del Ministero dell&rsquo;Interno) usano definizioni e momenti diversi e danno numeri diversi. Qui solo i dati Istat, nazionali.</li>
<li><b>Territori diversi.</b> Il 1522 è per regione, i centri per comune e provincia, i femminicidi per Italia: non si possono mettere sullo stesso grafico.</li>
<li><b>Le cause.</b> Questi dati non dicono perché le chiamate salgono o scendono. Non si possono attribuire le variazioni a campagne, notizie o politiche.</li>
</ul></div>

<h2 id="metodo">Come è fatto</h2>
<ul class="m">
<li>1522: Istat, <i>esploradati</i>, tabelle <i>Utenti del 1522</i> (<code>78_1205_DF_DCCV_1522UTENTI4_3</code>, chiamate valide, tutti i tipi di utente, entrambi i sessi, anni 2013-2024) e <i>Vittime che si rivolgono al 1522</i> (<code>78_1121_DF_DCCV_1522_VITTIME_1</code>, totale età); per il 2025 le tavole 1, 5, 6 e 7 del file Excel dell&rsquo;Istat (revisione del 19 ottobre 2026). Controlli: per il 2023 e il 2024 le somme trimestrali delle tavole 6 e 7 coincidono con le tabelle di <i>esploradati</i> (Italia e Lombardia, tutti i casi); la somma dei giorni della tavola 5 coincide con le chiamate valide annue in tutti gli otto anni; la regione ignota del 2024 è uguale nelle due fonti.</li>
<li>Quota Lombardia = chiamate Lombardia / (totale Italia &minus; regione ignota). Quota di donne = donne residenti in Lombardia / donne residenti in Italia, al 1° gennaio dell&rsquo;anno dopo (Istat, popolazione residente, <code>22_289_DF_DCIS_POPRES1_1</code>; disponibile dal 2019 in questo scarico).</li>
<li>Centri: Istat <code>78_1260</code>, voce &ldquo;centri antiviolenza&rdquo;, e percentuali di servizio (le righe con &ldquo;sì&rdquo;); elenchi della Regione: conteggi per provincia (colonna provincia; per le case rifugio, provincia della sede legale dell&rsquo;ente). Per 100.000 donne = conteggio / donne residenti al 1° gennaio 2025 &times; 100.000. Controllo: 53 centri Istat in Lombardia = 53 &ldquo;centri&rdquo; nell&rsquo;elenco convenzionato.</li>
<li>Femminicidi: valori del report Istat, trascritti in <code>femminicidi_italia_istat.csv</code>.</li>
<li>Programmi rieseguibili in <code>violenza-donne/scripts/</code>: <code>scarica.py</code>, <code>costruisci.py</code>, <code>pagina.py</code>. Nessun dato personale, nessuna registrazione, nessun accesso aggirato; richieste con User-Agent dichiarato.</li>
</ul>

<h2 id="download">File</h2>
<p><a href="data/1522_annuale_italia_lombardia.csv">1522_annuale_italia_lombardia.csv</a>, <a href="data/1522_regione_ignota_e_quota.csv">1522_regione_ignota_e_quota.csv</a>, <a href="data/1522_trimestri_regioni.csv">1522_trimestri_regioni.csv</a>, <a href="data/1522_motivi_trimestri_italia.csv">1522_motivi_trimestri_italia.csv</a>, <a href="data/1522_mensile_italia.csv">1522_mensile_italia.csv</a>, <a href="data/1522_giorni_di_punta.csv">1522_giorni_di_punta.csv</a>, <a href="data/centri_lombardia_province.csv">centri_lombardia_province.csv</a>, <a href="data/cav_istat_2024.csv">cav_istat_2024.csv</a>, <a href="data/femminicidi_italia_istat.csv">femminicidi_italia_istat.csv</a>, <a href="data/controlli.csv">controlli.csv</a>, <a href="data/inventario_fonti.csv">inventario_fonti.csv</a> (fonti, licenze, data di scaricamento, impronta del file), <a href="data/riepilogo.json">riepilogo.json</a>.</p>

<p>Vedi anche: <a href="../reati-citta/">Reati e sicurezza in città</a> (denunce di maltrattamenti e stalking), <a href="../reati/">Reati denunciati a Milano</a>, <a href="../benessere/">Il benessere della Città metropolitana di Milano</a>.</p>

<footer>
<p><b>Fonti e licenze, scaricate il 2 novembre 2026.</b> Istat: <i>Il numero verde 1522: chi chiama, perché e cosa racconta &ndash; anno 2025</i> (<a href="https://www.istat.it/tavole-di-dati/il-numero-verde-1522-chi-chiama-perche-e-cosa-racconta-anno-2025/">istat.it</a>, tavole in Excel, nota metodologica, glossario; pubblicazione 4 settembre 2026, tavole sostituite il 19 ottobre 2026; la pagina non riporta una licenza propria, le condizioni d&rsquo;uso di istat.it sono Creative Commons Attribution 4.0, CC BY 4.0); <i>esploradati</i> (<a href="https://esploradati.istat.it/">esploradati.istat.it</a>): <i>Utenti del 1522</i> e <i>Vittime che si rivolgono al 1522</i> (dati fino al 2024), <i>Centri antiviolenza</i> (aggiornamento 23 luglio 2026 secondo i metadati), <i>Popolazione residente al 1° gennaio</i>; CC BY 4.0 (la pagina delle condizioni non è stata riletta il giorno dello scaricamento); <i>Le vittime di omicidio. Anno 2024</i> (<a href="https://www.istat.it/wp-content/uploads/2025/11/Report_Le-vittime-di-omicidio_Anno-2024.pdf">PDF</a>, 25 novembre 2025). Dati primari delle chiamate: Dipartimento per le pari opportunità, Presidenza del Consiglio dei Ministri. Regione Lombardia, <a href="https://www.dati.lombardia.it/">dati.lombardia.it</a>: elenchi dei centri antiviolenza e delle case rifugio, licenza Creative Commons Zero 1.0 (CC0), scaricati il 2 novembre 2026.</p>
<p><b>Se hai bisogno di aiuto: 1522, gratuito, anonimo, attivo 24 ore su 24. In pericolo immediato: 112.</b></p>
<p>Programmi e note: <a href="https://github.com/AndreottiVIII/milano-in-dati">github.com/AndreottiVIII/milano-in-dati</a>.</p>
</footer>
</main>
<script>
(function(){
'use strict';
var ACC='#00695c',NAVY='#1f3a5f',WARM='#c26a1b',GRY='#8a8a8a';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function nf(x,d){return x==null?'':Number(x).toLocaleString('it-IT',{minimumFractionDigits:d,maximumFractionDigits:d})}
function f0(x){return x==null?'':Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'.')}
function f1(x){return nf(x,1)}
function J(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.json()})}
function el(id){return document.getElementById(id)}
function setH(id,h){el(id).innerHTML=h}
function niceStep(r){var p=Math.pow(10,Math.floor(Math.log(r)/Math.LN10)),f=r/p;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p}
function lgdLine(items){return items.map(function(it){return '<span><i class="ln'+(it.dash?' d':'')+'" style="border-top-color:'+it.color+'"></i>'+it.t+'</span>'}).join('')}
function lgdBox(items){return items.map(function(it){return '<span><i style="background:'+it.color+'"></i>'+it.t+'</span>'}).join('')}
var D={};
function tipBind(box,svg,rect,W,pos,html){
  var tip=box.lastChild;
  function show(ev){var t=ev.touches?ev.touches[0]:ev,r=svg.getBoundingClientRect(),k=W/r.width,px=(t.clientX-r.left)*k;
    var i=pos(px);if(i<0)return;tip.innerHTML=html(i);tip.style.display='';
    var tw=tip.offsetWidth,left=(t.clientX-r.left)+10;if(left+tw>r.width)left=(t.clientX-r.left)-tw-10;if(left<0)left=0;tip.style.left=left+'px';tip.style.top='6px'}
  function hide(){tip.style.display='none'}
  rect.addEventListener('mousemove',show);rect.addEventListener('mouseleave',hide);rect.addEventListener('touchstart',show,{passive:true});rect.addEventListener('touchmove',show,{passive:true});
}
function barChart(box,o){
  box.innerHTML='';
  var W=box.clientWidth||320,H=o.h||280,m={l:o.ml||46,r:8,t:14,b:26},n=o.labels.length;
  var y1=0;o.vals.forEach(function(v){if(v!=null&&v>y1)y1=v});
  var sy=niceStep(y1/5);y1=Math.ceil(y1/sy)*sy;
  var pw=W-m.l-m.r,ph=H-m.t-m.b,bw=pw/n;
  function Y(v){return m.t+ph-v/y1*ph}
  var s='<svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" aria-hidden="true">';
  for(var v=0;v<=y1+sy/2;v+=sy)s+='<line x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#e3e3e3"/><text class="mu" x="'+(m.l-6)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+f0(v)+'</text>';
  var step=W<520?2:1;
  o.labels.forEach(function(l,i){var x=m.l+bw*i;
    if(o.vals[i]!=null)s+='<rect x="'+(x+bw*0.14).toFixed(1)+'" y="'+Y(o.vals[i]).toFixed(1)+'" width="'+(bw*0.72).toFixed(1)+'" height="'+(m.t+ph-Y(o.vals[i])).toFixed(1)+'" fill="'+o.cols[i]+'"/>';
    if(i%step===0)s+='<text class="mu" x="'+(x+bw/2).toFixed(1)+'" y="'+(m.t+ph+17)+'" text-anchor="middle">'+l+'</text>'});
  s+='<line x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+(m.t+ph)+'" y2="'+(m.t+ph)+'" stroke="#888"/><rect x="'+m.l+'" y="'+m.t+'" width="'+pw+'" height="'+ph+'" fill="transparent" style="touch-action:pan-y"/></svg>';
  box.innerHTML=s+'<div class="tip" style="display:none"></div>';
  var svg=box.firstChild,rect=svg.querySelector('rect:last-of-type');
  tipBind(box,svg,rect,W,function(px){var i=Math.floor((px-m.l)/bw);return i<0||i>=n?-1:i},function(i){return '<b>'+o.labels[i]+'</b><br>'+(o.vals[i]==null?'':f0(o.vals[i]))+(o.note?'<br>'+o.note[i]:'')});
}
function lineChart(box,o){
  box.innerHTML='';
  var W=box.clientWidth||320,H=o.h||280,m={l:o.ml||44,r:12,t:14,b:26};
  var xs=o.x,x0=xs[0],x1=xs[xs.length-1],y0=o.y0!=null?o.y0:0,y1=0;
  o.series.forEach(function(s){s.vals.forEach(function(v){if(v!=null&&v>y1)y1=v})});
  var sy=niceStep((y1-y0)/5);y1=Math.ceil(y1/sy)*sy;
  var pw=W-m.l-m.r,ph=H-m.t-m.b;
  function X(v){return m.l+(v-x0)/(x1-x0)*pw} function Y(v){return m.t+ph-(v-y0)/(y1-y0)*ph}
  var s='<svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" aria-hidden="true">';
  for(var v=y0;v<=y1+sy/2;v+=sy)s+='<line x1="'+m.l+'" x2="'+(W-m.r)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#e3e3e3"/><text class="mu" x="'+(m.l-6)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+nf(v,o.yd||0)+'</text>';
  var step=W<520?2:1;
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
var COL={'piattaforma precedente':ACC,'nuova piattaforma':NAVY};
function colOf(s){return COL[s]||WARM}
function ann(){
  var terr=D.terr||'i',mis=D.mis||'u';
  setH('ctl-ann','<span class="sub">Territorio:</span><button type="button" data-t="i" class="'+(terr==='i'?'on':'')+'">Italia</button><button type="button" data-t="l" class="'+(terr==='l'?'on':'')+'">Lombardia</button> <span class="sub">Che cosa:</span><button type="button" data-m="u" class="'+(mis==='u'?'on':'')+'">Chiamate valide</button><button type="button" data-m="v" class="'+(mis==='v'?'on':'')+'">Chiamate &ldquo;vittime&rdquo;</button>');
  Array.prototype.forEach.call(el('ctl-ann').querySelectorAll('button'),function(b){b.addEventListener('click',function(){if(b.getAttribute('data-t'))D.terr=b.getAttribute('data-t');if(b.getAttribute('data-m'))D.mis=b.getAttribute('data-m');ann()})});
  var k=mis+terr,rows=D.R.ann;
  setH('lg-ann',lgdBox([{t:'2013-2022: piattaforma precedente',color:ACC},{t:'2023-2024: nuova piattaforma',color:NAVY},{t:'2025: serie mista, non confrontabile',color:WARM}]));
  barChart(el('ch-ann'),{labels:rows.map(function(r){return r.anno}),vals:rows.map(function(r){return r['u'===mis?(terr==='i'?'ui':'ul'):(terr==='i'?'vi':'vl')]}),cols:rows.map(function(r){return colOf(r.serie)}),note:rows.map(function(r){return r.serie})});
  setH('src-ann',(mis==='u'?'Chiamate valide di utenti':'Chiamate registrate come &ldquo;vittime&rdquo; (chi chiede aiuto per sé o segnala un caso)')+', '+(terr==='i'?'Italia':'Lombardia')+'. Fonte: Istat (CC BY 4.0); dati primari: Dipartimento per le pari opportunità. Si contano chiamate, non persone.');
  var h='<tr><th>Anno</th><th class="r">Italia</th><th class="r">Lombardia</th><th>Serie</th></tr>';
  rows.forEach(function(r){var a=mis==='u'?r.ui:r.vi,b=mis==='u'?r.ul:r.vl;h+='<tr><td>'+r.anno+'</td><td class="r">'+f0(a)+'</td><td class="r">'+f0(b)+'</td><td>'+esc(r.serie)+'</td></tr>'});
  setH('tab-ann',h);
}
var MOTL={aiuto_violenza:'Richiesta di aiuto come vittima di violenza',aiuto_stalking:'Richiesta di aiuto come vittima di stalking',segnalazione_caso:'Segnalazione di un caso di violenza',info_centri_antiviolenza:'Informazioni sui centri antiviolenza',info_servizio_1522:'Informazioni sul servizio 1522',info_giuridiche:'Informazioni giuridiche',fuori_target:'Chiamate fuori target (non sul tema)',totale_valide:'Totale chiamate valide',totale_non_valide:'Chiamate non valide (scherzi, errori)',totale:'Totale chiamate'};
function mot(){
  var h='<tr><th>Motivo</th><th class="r">2023</th><th class="r">2024</th><th class="r">Variazione 2023-2024 (%)</th><th class="r">2025 (metodo diverso)</th></tr>';
  D.R.motivi.forEach(function(r){var tot=r[0].indexOf('totale')===0;h+='<tr'+(tot?' class="hl"':'')+'><td>'+MOTL[r[0]]+'</td><td class="r">'+f0(r[1])+'</td><td class="r">'+f0(r[2])+'</td><td class="r">'+(r[1]?(r[2]/r[1]*100-100>0?'+':'')+nf(r[2]/r[1]*100-100,1):'')+'</td><td class="r">'+f0(r[3])+'</td></tr>'});
  setH('tab-mot',h);
}
var MESI=['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'];
function punta(){
  var h='<tr><th>Anno</th><th class="r">Chiamate il 25 novembre</th><th class="r">Mediana dei giorni dell&rsquo;anno</th><th class="r">Rapporto</th></tr>';
  D.R.punta.forEach(function(r){h+='<tr><td>'+r.anno+'</td><td class="r">'+f0(r.n25)+'</td><td class="r">'+f0(r.mediana)+'</td><td class="r">'+nf(r.n25/r.mediana,1)+'</td></tr>'});
  setH('tab-punta',h);
}
function quota(){
  var Q=D.R.quota;
  setH('lg-q',lgdLine([{t:'Quota Lombardia nelle chiamate con regione nota',color:ACC},{t:'Quota di donne residenti in Lombardia',color:GRY,dash:true}]));
  lineChart(el('ch-q'),{x:Q.map(function(r){return r.anno}),yd:0,y0:10,fmt:f1,series:[{name:'Chiamate (regione nota)',color:ACC,vals:Q.map(function(r){return r.lom}),w:3},{name:'Donne residenti',color:GRY,dash:true,vals:Q.map(function(r){return r.pop})}]});
  var h='<tr><th>Anno</th><th class="r">Chiamate con regione ignota (%)</th><th class="r">Quota Lombardia, regione nota (%)</th><th class="r">Quota donne residenti (%)</th></tr>';
  Q.forEach(function(r){h+='<tr><td>'+r.anno+'</td><td class="r">'+f1(r.ignoto)+'</td><td class="r">'+f1(r.lom)+'</td><td class="r">'+(r.pop==null?'&ndash;':f1(r.pop))+'</td></tr>'});
  setH('tab-q',h);
}
function cav(){
  var I=D.R.cav.Italia,L=D.R.cav.Lombardia;
  function sp(s){var a=s.split('|');return a.map(function(x){return f1(+x)}).join(' / ')}
  var rows=[['Centri antiviolenza',f0(+I.centri_antiviolenza_2024),f0(+L.centri_antiviolenza_2024)],
   ['Ogni 100.000 donne residenti',nf(+I.centri_per_100mila_donne_residenti,2),nf(+L.centri_per_100mila_donne_residenti,2)],
   ['Centri che dicono di essere reperibili 24 ore su 24 (%)',f1(+I.reperibilita_24_ore_pct),f1(+L.reperibilita_24_ore_pct)],
   ['Centri che aderiscono al 1522 (%)',f1(+I.adesione_1522_pct),f1(+L.adesione_1522_pct)],
   ['Centri con 1, 2, 3, 4 o più sportelli (% dei centri con almeno uno sportello)',sp(I['centri_con_sportelli_composizione_pct_N1|N2|N3|N4+']),sp(L['centri_con_sportelli_composizione_pct_N1|N2|N3|N4+'])]];
  var h='<tr><th>2024</th><th class="r">Italia</th><th class="r">Lombardia</th></tr>';
  rows.forEach(function(r){h+='<tr><td>'+r[0]+'</td><td class="r">'+r[1]+'</td><td class="r">'+r[2]+'</td></tr>'});
  setH('tab-cav',h);
  var P=D.R.prov;
  h='<tr><th>Provincia</th><th class="r">Centri e sportelli, albo (apr. 2026)</th><th class="r">Centri e sportelli, convenzionati (set. 2026)</th><th class="r">di cui centri</th><th class="r">Case rifugio, voci (provincia della sede dell&rsquo;ente)</th></tr>';
  P.forEach(function(r){h+='<tr'+(r.prov==='Milano'?' class="hl"':'')+'><td>'+esc(r.prov)+'</td><td class="r">'+f0(r.albo)+'</td><td class="r">'+f0(r.conv)+'</td><td class="r">'+f0(r.centri)+'</td><td class="r">'+f0(r.cr)+'</td></tr>'});
  var t=P.reduce(function(a,r){return [a[0]+r.albo,a[1]+r.conv,a[2]+r.centri,a[3]+r.cr]},[0,0,0,0]);
  h+='<tr><th>Lombardia (somma)</th><th class="r">'+f0(t[0])+'</th><th class="r">'+f0(t[1])+'</th><th class="r">'+f0(t[2])+'</th><th class="r">'+f0(t[3])+'</th></tr>';
  setH('tab-prov',h);
}
function fem(){
  var h='<tr><th>Anno</th><th class="r">Omicidi con vittima donna</th><th class="r">Di cui femminicidi stimati</th></tr>';
  D.R.fem.forEach(function(r){h+='<tr><td>'+r.anno+'</td><td class="r">'+f0(r.donne)+'</td><td class="r">'+f0(r.fem)+'</td></tr>'});
  setH('tab-fem',h);
}
J('data/riepilogo.json').then(function(R){
  D.R=R;ann();mot();punta();quota();cav();fem();
  var tm=null,w0=window.innerWidth;window.addEventListener('resize',function(){if(window.innerWidth===w0)return;w0=window.innerWidth;clearTimeout(tm);tm=setTimeout(function(){ann();quota()},150)});
}).catch(function(e){setH('ctl-ann','<p>Non riesco a caricare i dati ('+esc(e.message)+'). Riprova più tardi.</p>')});
})();
</script>
</body></html>
'''

html = HTML
for k, v in REP.items():
    html = html.replace("__" + k + "__", str(v))
assert "__" not in html, [x for x in html.split() if "__" in x][:5]

# ---- controlli sul testo: il testo assume queste cose ----
assert ui(2024) > ui(2023) and ul(2024) > ul(2023)
assert float(qt[2023]["pct_regione_ignota"]) > 33 and float(qt[2024]["pct_regione_ignota"]) > 33 and float(qt[2025]["pct_regione_ignota"]) > 33, "il testo dice 'piu' di una su tre'"
assert n_nov_top >= len(punta) - 2, "il testo dice 'quasi tutti a novembre'"
assert N25[2024] / MED[2024] > 3
assert cav_lo / 1 == 53 and L["conv_centri"] == 53, "il testo dice che 53 centri Istat = 53 centri convenzionati"
assert float(cav[("Lombardia", "centri_per_100mila_donne_residenti")]) < float(cav[("Italia", "centri_per_100mila_donne_residenti")])
assert float(cav[("Lombardia", "reperibilita_24_ore_pct")]) > float(cav[("Italia", "reperibilita_24_ore_pct")])
assert float(qt[2024]["quota_lombardia_su_regione_nota_pct"]) > float(qt[2024]["quota_donne_residenti_lombardia_su_italia_pct_1gen_anno_dopo"])
assert mot[("info_centri_antiviolenza", 2024)] > mot[("info_centri_antiviolenza", 2023)] and mot[("info_centri_antiviolenza", 2025)] < mot[("info_centri_antiviolenza", 2024)]
assert round(100 * 106 / 116, 1) == 91.4, "il testo scrive 91,4%"
assert os.path.exists(os.path.join(P, "controlli.csv")) and "DIVERSO" not in open(os.path.join(P, "controlli.csv"), encoding="utf-8").read()

os.makedirs(os.path.join(DEST, "data"), exist_ok=True)
open(os.path.join(DEST, "index.html"), "w", encoding="utf-8").write(html)
json.dump(DATA, open(os.path.join(DEST, "data", "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False)
for f in ["1522_annuale_italia_lombardia.csv", "1522_regione_ignota_e_quota.csv", "1522_trimestri_regioni.csv", "1522_motivi_trimestri_italia.csv",
          "1522_mensile_italia.csv", "1522_giorni_di_punta.csv", "centri_lombardia_province.csv", "cav_istat_2024.csv", "femminicidi_italia_istat.csv",
          "controlli.csv", "inventario_fonti.csv"]:
    shutil.copyfile(os.path.join(P, f), os.path.join(DEST, "data", f))
print("pagina scritta:", os.path.join(DEST, "index.html"), len(html), "byte")
