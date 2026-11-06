# -*- coding: utf-8 -*-
"""Aggiunge alla pagina docs/vie/index.html (Donne nelle vie) due cose, con un solo campo di ricerca:
  1. l'anno di intitolazione di ogni via (registro dei civici del Comune, ds634, CC BY 4.0) + grafico per decennio;
  2. i nomi sulle mappe dal 1884 per le 36 vie di ds2914 (progetto LetMi, CC BY 4.0).
Scrive in docs/vie/data/: vie_anno.json, vie_nomi.json, vie_data_intitolazione.csv, intitolazioni_per_decennio.csv,
vie_anno_riepilogo.json. Poi inserisce (o sostituisce, e' ripetibile) i blocchi marcati nella pagina; a capo come nel file.
Uso: python -I -X utf8 pagina_vie_anno_nomi.py [cartella docs/vie]   (lo chiama anche 15_costruisci_pagina.py di donne-nelle-vie)
"""
import csv, json, os, re, sys, unicodedata
from collections import Counter

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(QUI))
DOCS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RADICE, "docs", "vie")
DATA = os.path.join(DOCS, "data")
CIVICI = os.path.join(RADICE, "donne-nelle-vie", "raw", "comune", "ds634", "ds634_civici_coordinategeografiche_20261001_final.csv")
CLASS = os.path.join(DATA, "strade_classificate_arricchite_v2.csv")
VIE36 = os.path.join(RADICE, "vie-storiche", "pulito", "vie.json")
RIEP36 = os.path.join(RADICE, "vie-storiche", "pulito", "riepilogo.json")
SEGNAPOSTO = {"17000101", "19000101"}
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# ---------- utilita ----------
def it(n):
    return f"{int(n):,}".replace(",", ".")

def pc(a, b, dec=0):
    return f"{a / b * 100:.{dec}f}".replace(".", ",") + "%"

def norm(s):
    s = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())

PICCOLE = {"di", "del", "dello", "della", "dei", "degli", "delle", "da", "dal", "dalla", "e", "ed", "in", "al", "alla", "alle",
           "agli", "ai", "a", "sul", "sulla", "nel", "nella", "per", "con", "su"}
PREFISSI_PICCOLI = {"dell", "dall", "all", "nell", "sull"}
ACCENTI_A_MANO = {"ANDRE'": "André", "DUPRE'": "Dupré", "FAUCHE'": "Fauché", "TEULIE'": "Teulié", "DESSIE'": "Dessié", "FELICITE'": "Felicité", "F.LLI": "Fratelli"}
ACC = {"A": "à", "E": "è", "I": "ì", "O": "ò", "U": "ù"}
ROMANO = re.compile(r"^(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

def parola(w, primo):
    if w in ACCENTI_A_MANO:
        return ACCENTI_A_MANO[w]
    if len(w) >= 3 and w.endswith("'") and w[-2] in ACC and w != "DE'" and "'" not in w[:-1]:
        return w[:-2].capitalize() + ACC[w[-2]]
    if "-" in w:
        return "-".join(parola(x, True) for x in w.split("-"))
    if "'" in w:
        a, b = w.split("'", 1)
        pre = a.lower() if (a.lower() in PREFISSI_PICCOLI) else a.capitalize()
        return pre + "'" + parola(b, True)
    if len(w) >= 2 and w.isalpha() and ROMANO.match(w) and w not in ("DI", "MI", "LI", "CI", "DC"):
        return w
    if w.lower() in PICCOLE:
        return w.lower()
    if len(w) == 1 and w.isalpha():
        return w
    return w.capitalize()

def nome_bello(tipo, descr):
    tipo = tipo.strip()
    tipo = tipo[0].upper() + tipo[1:].lower()
    parole = descr.strip().split(" ")
    return tipo + " " + " ".join(parola(w, i == 0) for i, w in enumerate(parole))

def data_it(d):
    return f"{int(d[6:])} {MESI[int(d[4:6]) - 1]} {d[:4]}"

# ---------- 1. registro dei civici ----------
righe = list(csv.DictReader(open(CIVICI, encoding="utf-8", newline=""), delimiter=";"))
vie = {}
for r in righe:
    c = r["CODICE_VIA"]
    v = vie.setdefault(c, {"tipo": r["TIPO"], "descr": r["DESCRITTIVO"], "data": r["DATA_INTITOLAZIONE"].strip(), "mun": Counter(), "civici": 0})
    if r["MUNICIPIO"].strip():
        v["mun"][r["MUNICIPIO"].strip()] += 1
    v["civici"] += 1
assert len(vie) == 4030, len(vie)
n_data = sum(1 for v in vie.values() if v["data"])
n_segn = sum(1 for v in vie.values() if v["data"] in SEGNAPOSTO)
assert n_data == 1232 and n_segn == 14, (n_data, n_segn)
assert all(len(v["data"]) == 8 for v in vie.values() if v["data"])

# classificazione gia' usata dalla pagina
classe = {}
for r in csv.DictReader(open(CLASS, encoding="utf-8-sig", newline="")):
    if r["origine"] == "comune":
        classe[r["codice_via"]] = r
assert set(classe) == set(vie), "classificazione e registro non coincidono"
for c, v in vie.items():
    k = classe[c]
    assert (k["data_intitolazione"] or "") == v["data"], c
    v["cat"] = k["categoria"]
    v["conf"] = k["confidenza"]
    v["nome"] = nome_bello(v["tipo"], v["descr"])
    v["munis"] = sorted(v["mun"], key=lambda m: (-v["mun"][m], int(m)))
    v["mun1"] = v["munis"][0] if v["munis"] else ""

# ---------- 2. le 36 vie ----------
v36 = json.load(open(VIE36, encoding="utf-8"))
riep36 = json.load(open(RIEP36, encoding="utf-8"))
STOP = {"via", "viale", "corso", "piazza", "piazzale", "largo", "di", "del", "della", "dei", "delle", "dell", "delle", "dello", "da", "e"}

# abbinamento controllato a mano: nel registro e' scritto "CARDINAL CAPRARA"
MANUALI = {"Via Cardinale Caprara": "589"}

def trova(att):
    if att in MANUALI:
        assert vie[MANUALI[att]]["descr"] == "CARDINAL CAPRARA" and vie[MANUALI[att]]["tipo"] == "Via"
        return MANUALI[att]
    t = norm(att).split()
    tipo, resto = t[0], set(t[1:]) - STOP
    cand = []
    for c, v in vie.items():
        tv = norm(v["tipo"]).split()[0]
        pv = set(norm(v["descr"]).split()) - STOP
        if tv == tipo and resto and resto <= pv:
            cand.append((len(pv - resto), c))
    cand.sort()
    if len(cand) > 1:
        assert cand[0][0] < cand[1][0], ("ambiguo", att, cand)
    return cand[0][1] if cand else None

nomi36, voci_storiche_sole = [], []
abbinate = {}
for x in sorted(v36, key=lambda z: z["attuale"].lower()):
    cod = trova(x["attuale"])
    if cod:
        assert cod not in abbinate, ("doppio", cod)
        abbinate[cod] = x["id"]
    nomi36.append({"id": x["id"], "oggi": x["attuale"], "cod": cod, "n": sum(1 for e in x["eventi"] if e["tipo"] == "cambio"),
                   "righe": x["righe"], "nomi": sorted({c["raw"].strip() for c in x["celle"] if c["stato"] == "ok"})})
    if not cod:
        voci_storiche_sole.append(x["attuale"])
assert len(nomi36) == 36

# ---------- 3. file per la pagina ----------
voci = []
for c in sorted(vie, key=lambda k: int(k)):
    v = vie[c]
    voci.append({"c": int(c), "n": v["nome"], "m": "-".join(v["munis"]), "d": v["data"], "s": abbinate.get(c, 0)})
for x in nomi36:
    if not x["cod"]:
        voci.append({"c": 0, "n": x["oggi"], "m": "", "d": "", "s": x["id"], "x": 1})
with open(os.path.join(DATA, "vie_anno.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(voci, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(DATA, "vie_nomi.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(nomi36, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(DATA, "vie_data_intitolazione.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["codice_via", "via", "municipio", "data_intitolazione", "data_segnaposto", "classificazione", "tra_le_36_vie_con_nomi_storici"])
    for c in sorted(vie, key=lambda k: int(k)):
        v = vie[c]
        w.writerow([c, v["nome"], "-".join(v["munis"]), v["data"], 1 if v["data"] in SEGNAPOSTO else 0, v["cat"], 1 if c in abbinate else 0])

# ---------- 4. conti ----------
valide = {c: v for c, v in vie.items() if v["data"] and v["data"] not in SEGNAPOSTO}
n_val = len(valide)
assert n_val == 1218
dec = {}
for c, v in valide.items():
    d = int(v["data"][:4]) // 10 * 10
    z = dec.setdefault(d, {"tot": 0, "persone": 0, "donne": 0})
    z["tot"] += 1
    if v["cat"] in ("donna", "uomo", "misto"):
        z["persone"] += 1
    if v["cat"] == "donna" and v["conf"] in ("sicuro", "incerto"):
        z["donne"] += 1
assert sum(z["tot"] for z in dec.values()) == n_val
with open(os.path.join(DATA, "intitolazioni_per_decennio.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["decennio", "vie_con_data", "di_cui_intitolate_a_persone", "di_cui_intitolate_a_donne"])
    for d in sorted(dec):
        w.writerow([d, dec[d]["tot"], dec[d]["persone"], dec[d]["donne"]])
tot_donne_date = sum(z["donne"] for z in dec.values())
tot_persone_date = sum(z["persone"] for z in dec.values())

# campione: confronto vie con data e senza
con = [v for v in vie.values() if v["data"]]
senza = [v for v in vie.values() if not v["data"]]
fino49 = sum(z["tot"] for d, z in dec.items() if d < 1950)
dal2000 = sum(z["tot"] for d, z in dec.items() if d >= 2000)
anni2039 = sum(dec.get(d, {"tot": 0})["tot"] for d in (1920, 1930))
per_mun = {}
for v in vie.values():
    z = per_mun.setdefault(v["mun1"], [0, 0])
    z[1] += 1
    z[0] += 1 if v["data"] else 0
mun_altri = {m: z for m, z in per_mun.items() if m != "1"}
perc_altri = sorted(z[0] / z[1] for z in mun_altri.values())
corsi = [v for v in vie.values() if v["tipo"].lower() == "corso"]
corsi_con = sum(1 for v in corsi if v["data"])
pers = lambda L: sum(1 for v in L if v["cat"] in ("donna", "uomo", "misto"))
giorni = Counter(v["data"] for v in valide.values())
g_top, g_n = giorni.most_common(1)[0]
n_giorni_con_piu_di_10 = sum(1 for d, n in giorni.items() if n >= 10)
vie_in_giorni_10 = sum(n for d, n in giorni.items() if n >= 10)
assert sum(1 for v in senza if v["data"]) == 0

stat = {
    "vie_registro": len(vie), "vie_con_data_campo": n_data, "quota_con_data": n_data / len(vie), "segnaposto": n_segn,
    "valide": n_val, "fino_al_1949": fino49, "dal_2000": dal2000, "anni_venti_trenta": anni2039,
    "municipio1": {"con": per_mun["1"][0], "tot": per_mun["1"][1]},
    "altri_municipi_min": min(perc_altri), "altri_municipi_max": max(perc_altri),
    "corsi_con_data": corsi_con, "corsi_tot": len(corsi),
    "persone_tra_le_vie_con_data": [pers(con), len(con)], "persone_tra_le_vie_senza_data": [pers(senza), len(senza)],
    "data_piu_frequente": {"data": g_top, "vie": g_n}, "date_con_almeno_10_vie": [n_giorni_con_piu_di_10, vie_in_giorni_10],
    "donne_con_data_valida": tot_donne_date, "persone_con_data_valida": tot_persone_date,
    "vie_36_abbinate_al_registro": len(abbinate), "vie_36_non_nel_registro": voci_storiche_sole,
    "vie_36_con_data": sum(1 for c in abbinate if vie[c]["data"]),
}
with open(os.path.join(DATA, "vie_anno_riepilogo.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump({"stat": stat, "decenni": {str(k): dec[k] for k in sorted(dec)}, "mappe36": riep36}, f, ensure_ascii=False, indent=1)

# ---------- 5. HTML ----------
def barra(valore, massimo, classe):
    larg = valore / massimo * 100
    stile = f"width:{larg:.2f}%" + (";min-width:3px" if valore else "")
    return f'<span class="va-b {classe}" style="{stile}"></span>'

mx = max(z["tot"] for z in dec.values())
righe_gr = []
for d in sorted(dec):
    z = dec[d]
    righe_gr.append(
        f'<div class="va-r"><div class="va-rt"><b>Anni {d}</b><span>{it(z["tot"])} vie, di cui {it(z["donne"])} a donne</span></div>'
        f'<div class="va-bar" aria-hidden="true">{barra(z["tot"], mx, "t")}</div>'
        f'<div class="va-bar" aria-hidden="true">{barra(z["donne"], mx, "d")}</div></div>')
GRAFICO = "\n".join(righe_gr)

N36 = len(nomi36)
nasc = [v["attuale"] for v in v36 if v["attuale"] in riep36["nate_dopo_il_1884"]]
senza_cambio = riep36["senza_nessun_cambio"]
altre_senza = [n for n in senza_cambio if n not in nasc]
c1030 = riep36["per_intervallo"]["1910-1930"]
c3046 = riep36["per_intervallo"]["1930-1946"]
salti = sum(riep36["con_salto_mappa_illeggibile"].values())
assert riep36["vie"] == 36 and riep36["con_almeno_un_cambio"] == 33 and riep36["cambi_totali"] == 40 and c1030 == 19

def elenco(L):
    L = list(L)
    return L[0] if len(L) == 1 else ", ".join(L[:-1]) + " e " + L[-1]

m1 = stat["municipio1"]
lo, hi = stat["altri_municipi_min"], stat["altri_municipi_max"]
quota_pers_con = pc(*stat["persone_tra_le_vie_con_data"])
quota_pers_senza = pc(*stat["persone_tra_le_vie_senza_data"])
data_top = data_it(g_top)

BLOCCO = r"""<!-- vie-anno-nomi:inizio -->
<h2 id="cerca-via">Cerca la tua via</h2>
<div class="va">
<p>Scrivi il nome di una via di Milano. Se il registro dei numeri civici del Comune ha la data di intitolazione, la vedi qui sotto. Per @@N36@@ vie vedi anche come si chiamavano sulle mappe dal 1884.</p>
<p class="va-avviso"><b>Attenzione.</b> La data c&rsquo;&egrave; solo per circa un terzo delle vie: @@CON@@ su @@TOT@@ (@@QUOTA@@). I nomi sulle mappe storiche ci sono solo per @@N36@@ vie, scelte per un progetto su letteratura e turismo.</p>
<label class="va-et" for="va-q">Nome della via</label>
<input id="va-q" type="search" placeholder="per esempio: Monte Grappa" autocomplete="off" enterkeyhint="search">
<div class="va-sugg" id="va-sugg" role="listbox" aria-label="Vie trovate"></div>
<p class="va-prova">Oppure prova: <span id="va-prova"></span></p>
<div class="va-scheda" id="va-scheda" aria-live="polite"></div>
</div>

<h2 id="anno-nome">In che anno hanno preso il nome le vie</h2>
<div class="va">
<p>Il registro del Comune ha una data di intitolazione per @@CON@@ vie su @@TOT@@ (@@QUOTA@@). Per @@SEGN@@ di queste la data &egrave; un valore segnaposto (1 gennaio 1700 o 1 gennaio 1900), che non conto. Restano @@VALIDE@@ vie con una data vera, qui contate per decennio.</p>
<div class="va-leg"><span class="va-b t"></span> vie con data &nbsp; <span class="va-b d"></span> di cui intitolate a donne</div>
<div class="va-gr">
@@GRAFICO@@
</div>
<p class="va-pic">Le donne sono quelle che la pagina gi&agrave; riconosce come tali (persona, donna o uomo): in tutto @@DONNE@@ vie con data, su @@PERSONE@@ intitolate a persone. Per decennio i numeri delle donne sono piccoli. <a href="data/intitolazioni_per_decennio.csv">Numeri per decennio (CSV)</a> &middot; <a href="data/vie_data_intitolazione.csv">tutte le vie con la data (CSV)</a></p>

<h3>Le vie con una data sono un campione di tutte le vie?</h3>
<p>Non del tutto. Non sono solo vie recenti: @@FINO49@@ delle @@VALIDE@@ hanno una data fino al 1949, @@DAL2000@@ dal 2000 in poi. Ma non sono nemmeno scelte a caso:</p>
<ul>
<li>Nel Municipio 1 (il centro) ha la data il @@M1@@ delle vie; negli altri Municipi dal @@MLO@@ al @@MHI@@.</li>
<li>Tra le vie con data, @@PCON@@ sono intitolate a una persona; tra quelle senza data, @@PSEN@@.</li>
<li>Nessuno dei @@CORSI@@ corsi ha la data.</li>
<li>@@ANNI2030@@ delle date (oltre una su due) cadono negli anni Venti e Trenta del Novecento. Molte vie hanno la stessa data: @@GTOP@@ il @@DTOP@@; in tutto @@G10@@ vie condividono la data con almeno altre 9.</li>
</ul>
<p><b>Quindi il grafico dice solo quando risultano intitolate le vie che hanno una data nel registro.</b> Non dice quando sono nate le vie di Milano, n&eacute; quando sono state intitolate le altre, e non permette di dire come sia cambiata nel tempo la quota di donne in tutta la citt&agrave;. Non ne ricavo conclusioni sul passato. Il registro non spiega a quale nome si riferisca la data.</p>
</div>

<h2 id="come-si-chiamava">Come si chiamava</h2>
<div class="va">
<p class="va-avviso"><b>Sono solo @@N36@@ vie</b>, scelte per un progetto su letteratura e turismo (LetMi) del Comune. Non rappresentano le vie di Milano: da questi numeri non si ricava nulla sul resto della citt&agrave;.</p>
<p>Per queste vie il Comune ha letto il nome su dieci mappe: 1884, 1910, 1930, 1946, 1956, 1965, 1972, 1990, 2006, 2012. Per vederli, cerca la via nel campo qui sopra.</p>
<ul class="va-num">
<li><b>33 su 36</b> cambiano nome almeno una volta. @@ALTRE@@</li>
<li><b>19 cambi su 40</b> cadono tra la mappa del 1910 e quella del 1930 (20 anni); tra il 1930 e il 1946 (16 anni) sono @@C3046@@. Altri @@SALTI@@ cambi non si possono collocare, perch&eacute; in mezzo c&rsquo;&egrave; una mappa che non si legge.</li>
<li><b>La regola.</b> Conta come cambio solo un nome del tutto diverso. &laquo;Via Turati&raquo; e &laquo;Via Filippo Turati&raquo;, &laquo;Piazza XXIV Maggio&raquo; e &laquo;Piazza Ventiquattro Maggio&raquo;, o viale al posto di via, non contano. Se sulla mappa si aggiunge o si toglie un secondo nome, lo segno ma non lo conto.</li>
</ul>
<p class="va-pic">Un cambio &egrave; collocato tra due mappe, non in un anno preciso. I dati dicono quando, non perch&eacute;. I nomi sono quelli letti a mano dal Comune sulle mappe: non li ho controllati sulle mappe originali.</p>
<details class="va-elenco"><summary>Le @@N36@@ vie</summary><div id="va-elenco"></div></details>
</div>
<!-- vie-anno-nomi:fine -->"""

CSS = r"""/* vie-anno-nomi:inizio */
.va{min-width:0}.va *{min-width:0}
.va-avviso{border-left:6px solid var(--acc);background:#f6f6f6;padding:8px 10px;margin:10px 0}
.va-et{display:block;font-weight:700;margin:14px 0 6px}
#va-q{width:100%;font:inherit;font-size:18px;padding:12px;border:3px solid var(--ink);border-radius:0;background:#fff;color:var(--ink);-webkit-appearance:none;appearance:none}
.va-sugg{margin:0}.va-sugg button{display:block;width:100%;font:inherit;font-size:16px;text-align:left;padding:11px 8px;border:0;border-bottom:1px solid var(--line);background:#fff;color:var(--ink);cursor:pointer}
.va-sugg button small,.va-sugg p{display:block;color:var(--mut);font-size:14px}
.va-sugg p{margin:8px 0}
.va-prova{font-size:15px;margin:10px 0 0}.va-prova button,.va-elenco button{font:inherit;font-size:15px;border:2px solid var(--ink);background:#fff;color:var(--ink);padding:4px 9px;margin:4px 6px 0 0;cursor:pointer}
.va-scheda{margin-top:6px}.va-tit{font-size:1.5rem;font-weight:700;line-height:1.15;margin:18px 0 2px;overflow-wrap:anywhere}
.va-sub{font-size:14px;color:var(--mut)}
.va-scheda h4{font-size:1rem;margin:16px 0 4px;border-top:2px solid var(--ink);padding-top:8px}
.va-anno{font-size:1.4rem;font-weight:700;color:var(--acc);margin:2px 0}
.va-pic{font-size:14px;color:var(--mut)}
.va-gr{margin:10px 0}.va-r{margin:12px 0}
.va-rt{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 10px;font-size:15px}.va-rt span{color:var(--mut);font-size:14px}
.va-bar{height:14px;margin-top:3px;background:#f2f2f2}.va-b{display:block;height:100%}
.va-b.t{background:#555}.va-b.d{background:var(--acc)}
.va-leg{font-size:14px;color:var(--mut)}.va-leg .va-b{display:inline-block;width:18px;height:12px;vertical-align:middle}
.va h3{font-size:1.05rem;margin:20px 0 4px}
.va-num{padding-left:20px}.va-num li{margin:8px 0}
.va-linea{list-style:none;margin:6px 0 4px 6px;padding:0;border-left:6px solid var(--acc)}
.va-linea li{position:relative;padding:4px 0 14px 18px}
.va-linea li:before{content:"";position:absolute;left:-14px;top:7px;width:12px;height:12px;border-radius:50%;background:#fff;border:3px solid var(--ink)}
.va-linea li.cambia:before{background:var(--acc);border-color:var(--acc)}
.va-an{font-size:14px;font-weight:700}.va-nm{font-size:1.1rem;line-height:1.2;font-weight:700;overflow-wrap:anywhere}
.va-tag{display:inline-block;font-size:12px;font-weight:700;background:#e8e8e8;color:var(--ink);padding:1px 6px;margin-left:6px;vertical-align:2px}
.va-tag.c{background:var(--acc);color:#fff}
.va-det{font-size:14px;color:var(--mut)}
.va-elenco summary{cursor:pointer;font-weight:700;margin:10px 0}
@media(max-width:640px){#va-q{font-size:16px}.va-tit{font-size:1.3rem}}
/* vie-anno-nomi:fine */"""

LIMITI = r"""<!-- vie-anno-nomi-limiti:inizio -->
<li><b>Le vie con una data non sono un campione di tutte le vie.</b> Nel centro la data manca pi&ugrave; spesso, e molte date si ripetono per decine di vie: il grafico per decennio dice quando risultano intitolate le vie con una data, non quando sono state intitolate tutte le altre (sezione &laquo;In che anno hanno preso il nome le vie&raquo;).</li>
<li><b>I nomi sulle mappe storiche sono solo per @@N36@@ vie.</b> Il Comune le ha scelte per un progetto su letteratura e turismo: non dicono nulla sulle altre vie. I nomi sono letti dal Comune sulle mappe e qui non sono stati controllati sulle mappe originali.</li>
<li><b>Nel registro del Comune i nomi sono scritti tutti in maiuscolo.</b> Maiuscole e accenti dei nomi mostrati nella ricerca sono ricostruiti qui e possono avere qualche errore.</li>
<!-- vie-anno-nomi-limiti:fine -->
"""

FONTI = r"""<!-- vie-anno-nomi-fonti:inizio -->
<p>Anni di intitolazione: Comune di Milano, registro dei numeri civici con coordinate (<a href="https://dati.comune.milano.it/dataset/ds634-numeri-civici-coordinate">ds634</a>), licenza CC BY 4.0, dati del 1&deg; ottobre 2026. Nomi sulle mappe storiche: Comune di Milano, &laquo;Vie di Milano e corrispondenza toponomastica nelle mappe storiche dal 1884&raquo; (<a href="https://dati.comune.milano.it/dataset/ds2914-vie-di-milano-e-corrispondenza-toponomastica-nelle-mappe-storiche-dal-1884">ds2914</a>, progetto LetMi), licenza CC BY 4.0, ultima modifica dell&rsquo;8 maggio 2026. Sezioni &laquo;Cerca la tua via&raquo;, &laquo;In che anno&raquo; e &laquo;Come si chiamava&raquo; aggiunte il 6 novembre 2026.</p>
<!-- vie-anno-nomi-fonti:fine -->
"""

JS = r"""<!-- vie-anno-nomi-js:inizio -->
<script>
(function(){
  var VOCI=[],NOMI={},PRONTO=false;
  function pulisci(s){return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();}
  function el(t,c,h){var e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;}
  function es(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  var MESI=['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'];
  function dataIt(d){return parseInt(d.slice(6),10)+' '+MESI[parseInt(d.slice(4,6),10)-1]+' '+d.slice(0,4);}
  function periodo(r){var a=r.da,b=r.a;if(a===b)return a==='oggi'?'oggi':'mappa del '+a;return 'dal '+a+(b==='oggi'?' a oggi':' al '+b);}
  function linea(s){
    var ul=el('ul','va-linea');
    s.righe.forEach(function(r){
      var li=el('li',r.esito==='cambio'?'cambia':'');var tag='';
      if(r.esito==='cambio')tag='<span class="va-tag c">cambia</span>';
      else if(r.esito==='parziale')tag='<span class="va-tag">nome aggiunto o tolto</span>';
      else if(r.esito==='nasce')tag='<span class="va-tag">la via nasce</span>';
      var det=(r.varianti&&r.varianti.length)?'<div class="va-det">scritto anche: '+r.varianti.map(es).join('; ')+'</div>':'';
      li.innerHTML='<div class="va-an">'+es(periodo(r))+tag+'</div><div class="va-nm">'+es(r.nome.trim())+'</div>'+det;
      ul.appendChild(li);
    });
    return ul;
  }
  function mostra(v){
    var s=document.getElementById('va-scheda');s.innerHTML='';
    s.appendChild(el('div','va-tit',es(v.n)));
    if(v.m)s.appendChild(el('div','va-sub',(v.m.indexOf('-')>=0?'Municipi ':'Municipio ')+es(v.m.replace(/-/g,', '))));
    s.appendChild(el('h4','','In che anno ha preso il nome'));
    if(v.x){s.appendChild(el('p','','Questa via non c&rsquo;&egrave; nel registro dei numeri civici del Comune, quindi non ho una data.'));}
    else if(!v.d){s.appendChild(el('p','','Il registro del Comune non ha una data per questa via. Succede per @@SENZA100@@ vie su 100.'));}
    else if(v.d==='17000101'||v.d==='19000101'){s.appendChild(el('p','','Il registro ha per questa via la data '+dataIt(v.d)+', che &egrave; un valore segnaposto e non indica un anno vero.'));}
    else{s.appendChild(el('p','va-anno',v.d.slice(0,4)));s.appendChild(el('p','va-pic','Data di intitolazione nel registro del Comune: '+dataIt(v.d)+'. Il registro non spiega a quale nome si riferisca.'));}
    s.appendChild(el('h4','','Come si chiamava'));
    var st=v.s?NOMI[v.s]:null;
    if(st){
      var f=st.n===0?'Nessun cambio di nome sulle mappe.':(st.n===1?'Ha cambiato nome una volta.':'Ha cambiato nome '+st.n+' volte.');
      s.appendChild(el('p','',f+' Nomi letti sulle mappe dal 1884:'));
      s.appendChild(linea(st));
      s.appendChild(el('p','va-pic','Sono solo 36 vie, scelte per un progetto su letteratura e turismo.'));
    }else{
      s.appendChild(el('p','','I nomi sulle mappe storiche ci sono solo per 36 vie scelte dal Comune; questa non &egrave; tra quelle.'));
    }
  }
  function cerca(){
    var q=pulisci(document.getElementById('va-q').value),out=document.getElementById('va-sugg');out.innerHTML='';
    if(q.length<2)return;
    if(!PRONTO){out.appendChild(el('p','','Carico le vie&hellip;'));return;}
    var t=q.split(' ');
    var tro=VOCI.filter(function(v){return t.every(function(w){return v.k.some(function(p){return p.indexOf(w)===0;});});});
    tro.sort(function(a,b){return (b.s?1:0)-(a.s?1:0)||a.n.length-b.n.length||(a.n<b.n?-1:1);});
    if(!tro.length){out.appendChild(el('p','','Nessuna via trovata. Prova con meno parole, per esempio solo il cognome.'));return;}
    tro.slice(0,8).forEach(function(v){
      var b=el('button','',es(v.n));b.type='button';
      var extra=[];
      if(v.d&&v.d!=='17000101'&&v.d!=='19000101')extra.push('intitolata nel '+v.d.slice(0,4));
      if(v.s)extra.push('con i nomi sulle mappe storiche');
      if(!v.x&&v.m)extra.push((v.m.indexOf('-')>=0?'Municipi ':'Municipio ')+v.m.replace(/-/g,', '));
      var vecchio=v.s&&NOMI[v.s]?NOMI[v.s].nomi.filter(function(n){var p=pulisci(n);return t.every(function(w){return p.split(' ').some(function(x){return x.indexOf(w)===0;});})&&!t.every(function(w){return pulisci(v.n).split(' ').some(function(x){return x.indexOf(w)===0;});});})[0]:null;
      if(vecchio)extra.unshift('nome vecchio: '+vecchio.trim());
      if(extra.length)b.innerHTML+='<small>'+es(extra.join(' · '))+'</small>';
      b.onclick=function(){mostra(v);out.innerHTML='';document.getElementById('va-q').value='';document.getElementById('va-scheda').scrollIntoView({block:'nearest'});};
      out.appendChild(b);
    });
  }
  function vaiA(nome){
    var v=VOCI.filter(function(x){return x.n===nome;})[0];if(v){mostra(v);document.getElementById('va-sugg').innerHTML='';}
  }
  function pronto(){
    PRONTO=true;
    var p=document.getElementById('va-prova');
    ['Viale Monte Grappa','Via Filippo Turati','Via Cesare Lombroso'].forEach(function(n){
      if(!VOCI.some(function(x){return x.n===n;}))return;
      var b=el('button','',es(n));b.type='button';b.onclick=function(){vaiA(n);};p.appendChild(b);
    });
    var e=document.getElementById('va-elenco');
    VOCI.filter(function(x){return x.s;}).sort(function(a,b){return a.n<b.n?-1:1;}).forEach(function(v){
      var b=el('button','',es(v.n));b.type='button';b.onclick=function(){vaiA(v.n);document.getElementById('cerca-via').scrollIntoView();};e.appendChild(b);
    });
    cerca();
  }
  document.getElementById('va-q').addEventListener('input',cerca);
  document.getElementById('va-q').addEventListener('keydown',function(ev){if(ev.key==='Enter'){var b=document.querySelector('#va-sugg button');if(b)b.click();ev.preventDefault();}});
  Promise.all([fetch('data/vie_anno.json',{cache:'no-cache'}).then(function(r){return r.json();}),fetch('data/vie_nomi.json',{cache:'no-cache'}).then(function(r){return r.json();})]).then(function(r){
    r[1].forEach(function(x){NOMI[x.id]=x;});
    r[0].forEach(function(v){var chiavi=[v.n];if(v.s&&NOMI[v.s]){chiavi.push(NOMI[v.s].oggi);NOMI[v.s].nomi.forEach(function(n){chiavi.push(n);});}
      v.k=[];chiavi.forEach(function(c){pulisci(c).split(' ').forEach(function(w){if(w&&v.k.indexOf(w)<0)v.k.push(w);});});});
    VOCI=r[0];pronto();
  }).catch(function(){document.getElementById('va-sugg').innerHTML='<p>Non sono riuscito a caricare l&rsquo;elenco delle vie. Riprova pi&ugrave; tardi.</p>';});
})();
</script>
<!-- vie-anno-nomi-js:fine -->
"""

ALTRE = "Le altre 3 non cambiano: " + elenco(altre_senza + nasc) + "."
if nasc:
    ALTRE += (" L&rsquo;ultima non c&rsquo;&egrave; " if len(nasc) == 1 else " Le ultime due non ci sono ") + "sulla mappa del 1884."
assert len(senza_cambio) == 3
SOST = {
    "@@N36@@": str(N36), "@@SENZA100@@": str(round((len(vie) - n_data) / len(vie) * 100)), "@@CON@@": it(n_data), "@@TOT@@": it(len(vie)), "@@QUOTA@@": pc(n_data, len(vie)), "@@SEGN@@": str(n_segn),
    "@@VALIDE@@": it(n_val), "@@DONNE@@": it(tot_donne_date), "@@PERSONE@@": it(tot_persone_date),
    "@@FINO49@@": it(fino49), "@@DAL2000@@": it(dal2000), "@@M1@@": pc(m1["con"], m1["tot"]),
    "@@MLO@@": pc(lo, 1), "@@MHI@@": pc(hi, 1), "@@PCON@@": quota_pers_con, "@@PSEN@@": quota_pers_senza,
    "@@CORSI@@": str(len(corsi)), "@@ANNI2030@@": it(anni2039), "@@GTOP@@": it(g_n), "@@DTOP@@": data_top,
    "@@G10@@": it(vie_in_giorni_10), "@@C3046@@": str(c3046), "@@SALTI@@": str(salti), "@@ALTRE@@": ALTRE, "@@GRAFICO@@": GRAFICO,
}
assert stat["corsi_con_data"] == 0, "il testo dice che nessun corso ha la data"
assert anni2039 / n_val > 0.5 and m1["con"] / m1["tot"] < lo
assert stat["donne_con_data_valida"] == sum(1 for v in valide.values() if v["cat"] == "donna")

def compila(t):
    for k, v in SOST.items():
        t = t.replace(k, v)
    assert "@@" not in t, re.findall(r"@@\w+@@", t)
    return t

# ---------- 6. pagina ----------
PAG = os.path.join(DOCS, "index.html")
testo = open(PAG, encoding="utf-8", newline="").read()
a_capo = "\r\n" if "\r\n" in testo else "\n"
testo = testo.replace("\r\n", "\n")

def metti(testo, nome, blocco, ancora, prima=True):
    ini, fin = f"<!-- {nome}:inizio -->", f"<!-- {nome}:fine -->"
    if nome == "vie-anno-nomi" and False:
        pass
    if ini in testo:
        i, j = testo.index(ini), testo.index(fin) + len(fin)
        testo = testo[:i] + blocco.strip("\n") + testo[j:]
    else:
        assert testo.count(ancora) == 1, (nome, ancora, testo.count(ancora))
        i = testo.index(ancora)
        testo = testo[:i] + blocco.strip("\n") + "\n" + testo[i:] if prima else testo[:i + len(ancora)] + "\n" + blocco.strip("\n") + testo[i + len(ancora):]
    return testo

# CSS (marcato con commenti CSS)
cssi, cssf = "/* vie-anno-nomi:inizio */", "/* vie-anno-nomi:fine */"
css = compila(CSS)
if cssi in testo:
    i, j = testo.index(cssi), testo.index(cssf) + len(cssf)
    testo = testo[:i] + css + testo[j:]
else:
    assert testo.count("</style>") == 1
    testo = testo.replace("</style>", css + "\n</style>")
testo = metti(testo, "vie-anno-nomi", compila(BLOCCO), "<h2>La mappa</h2>")
# limiti: dentro la lista della sezione "Limiti dei dati", prima della sua chiusura
if "<!-- vie-anno-nomi-limiti:inizio -->" in testo:
    testo = metti(testo, "vie-anno-nomi-limiti", compila(LIMITI), None)
else:
    k = testo.index('<h2 id="limiti">')
    j = testo.index("</ul>", k)
    testo = testo[:j] + compila(LIMITI) + testo[j:]
testo = metti(testo, "vie-anno-nomi-fonti", compila(FONTI), "<p>Aggiornato al ")
testo = metti(testo, "vie-anno-nomi-js", compila(JS), "</body>")
open(PAG, "w", encoding="utf-8", newline="").write(testo.replace("\n", a_capo))
print("pagina aggiornata:", PAG, "| a capo:", repr(a_capo))
print(json.dumps(stat, ensure_ascii=False, indent=1))
