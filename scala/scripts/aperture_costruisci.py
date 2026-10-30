"""Costruisce la tabella delle aperture di stagione della Scala (1778 -> 2026) e il registro delle differenze tra le fonti.
Uscite (dalla cartella scala/):
  pulito/aperture.csv               una riga per apertura (blocco 'dal_1951' = serate del 7 dicembre; blocco 'prima_1951' = Santo Stefano / Carnevale)
  pulito/aperture_differenze.md     ogni disaccordo trovato tra le fonti
  pulito/_aperture_log.json         dettagli per il controllo
Fonti: it.wikipedia 'Prime stagionali' (WP), it.wikipedia 'Stagioni liriche' (SL), Wikidata 'serata inaugurale' (WD), SBN programmi (SBN) e registrazioni (REG),
sito pubblico della Scala (SC), Cambiasi 1881 (CA), Romani 1862 (RO), Marangoni-Vanbianchi (MA), Gatti vol. I (GA), Operadis (OP, solo controllo locale).
Uso: python -I -X utf8 scripts/aperture_costruisci.py"""
import sys, os, re, json, glob, csv
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aperture_lib import kt, sim, surname, same_person, strip_acc
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda *a: os.path.join(ROOT, *a)
LOG = []          # (anno, campo, testo)
def log(y, campo, testo): LOG.append((y, campo, testo))

# ---------------------------------------------------------------- caricamenti
wp = pd.read_csv(P("pulito", "_aperture_wp_lista.csv")).fillna("")
sl = pd.read_csv(P("pulito", "_wp_stagioni.csv")).fillna("")
cam = pd.read_csv(P("pulito", "_cambiasi_pulito.csv")).fillna("")
rom = pd.read_csv(P("pulito", "_romani_opere.csv")).fillna("")
mar = pd.read_csv(P("pulito", "_marangoni_opere.csv")).fillna("")
gat = pd.read_csv(P("pulito", "gatti_vol1_citazioni.csv")).fillna("")
cart = pd.read_csv(P("pulito", "cartellone.csv")).fillna("")
sbn = pd.read_csv(P("sbn", "sbn_programmi.csv"), encoding="utf-8-sig").fillna("")
reg = pd.read_csv(P("sbn", "sbn_registrazioni.csv"), encoding="utf-8-sig").fillna("")
opd = pd.read_csv(P("raw", "discografie", "operadis_scala.csv")).fillna("")
scala = json.load(open(P("pulito", "_aperture_scala_cast.json"), encoding="utf8"))
# Wikidata: voci 'serata inaugurale' con data, direttore (P3300), regia (P57), cast (P161)
lab = json.load(open(P("raw", "aperture_wikidata", "labels_all.json"), encoding="utf8"))
ents = {}
for f in glob.glob(P("raw", "aperture_wikidata", "entities_*.json")):
    ents.update(json.load(open(f, encoding="utf8"))["entities"])
def wvals(e, pid):
    out = []
    for x in e.get("claims", {}).get(pid, []):
        v = x["mainsnak"].get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v: out.append(lab.get(v["id"], v["id"]))
    return out
WD = []
for q, e in ents.items():
    d = e["claims"].get("P585", [{}])[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("time", "")[1:11]
    WD.append(dict(q=q, data=d, label=e["labels"].get("it", {}).get("value", ""), desc=e.get("descriptions", {}).get("it", {}).get("value", ""),
                   dir=", ".join(wvals(e, "P3300")), reg=", ".join(wvals(e, "P57")), cast=wvals(e, "P161"), opera=", ".join(wvals(e, "P4646"))))
WD.sort(key=lambda r: r["data"])

# ---------------------------------------------------------------- normalizzazione dei nomi
CANON = {"victor de sabata": "Victor de Sabata", "margarete wallmann": "Margherita Wallmann", "tat'jana pavlovna pavlova": "Tatiana Pavlova", "luigi ronconi": "Luca Ronconi",
         "chung myung-whun": "Myung-whun Chung", "myung-whun chung": "Myung-whun Chung", "jurij petrovic ljubimov": "Jurij Ljubimov", "gunther rennert": "Günther Rennert",
         "dmitrij cernjakov": "Dmitrij Černjakov", "patrice chereau": "Patrice Chéreau", "modest petrovic musorgskij": "Modest Musorgskij", "modest musorgskij": "Modest Musorgskij",
         "dmitrij dmitrievic sostakovic": "Dmitrij Šostakovič", "dmitrij sostakovic": "Dmitrij Šostakovič", "gioacchino rossini": "Gioachino Rossini",
         "mario frigerio": "Mario Frigerio", "carl ebert": "Carl Ebert", "hugo de ana": "Hugo de Ana", "alvis hermanis": "Alvis Hermanis", "wolfgang amadeus mozart": "Wolfgang Amadeus Mozart",
         "claus helmut drese": "Claus Helmut Drese", "giuseppe marchioro": "Giuseppe Marchioro", "alessandro sanine": "Alessandro Sanine"}
def canon(n):
    k = strip_acc(n).lower().strip()
    return CANON.get(k, n.strip())
def cn(s):
    s = re.sub(r"\s+", " ", str(s)).strip(" ;,.")
    parts = [canon(p) for p in re.split(r"\s*(?:;|/| e |, )\s*", s) if p.strip()] if re.search(r";|/", s) else [canon(s)]
    return "; ".join(parts)

# ---------------------------------------------------------------- composizione dei titoli (titolo corretto/per visualizzare)
TIT_FIX = {  # titolo come lo scriviamo, compositore, note
 "La battaglia": ("La battaglia di Legnano", None), "Lucia": ("Lucia di Lammermoor", None), "Lucia di Lammermoor": ("Lucia di Lammermoor", None),
 "Lady Macbeth del Distretto di Mcensk": ("Una Lady Macbeth del distretto di Mcensk", None), "Armida": ("Armida", None),
 "La dannazione di Faust": ("La dannazione di Faust", None), "Götterdämmerung": ("Götterdämmerung (Il crepuscolo degli dei)", None),
 "Il crepuscolo degli dei": ("Il crepuscolo degli dei (Götterdämmerung)", None), "Die Walküre": ("Die Walküre (La Valchiria)", None),
 "Tristan und Isolde": ("Tristan und Isolde", None), "Tristano e Isotta": ("Tristan und Isolde", None), "Iphigénie en Aulide": ("Iphigénie en Aulide", None),
 "Moïse et Pharaon": ("Moïse et Pharaon", None), "L'Europa riconosciuta": ("L'Europa riconosciuta", None), "Europa riconosciuta": ("L'Europa riconosciuta", None),
 "Guglielmo Tell": ("Guglielmo Tell", None), "Die Zauberflöte": ("Die Zauberflöte (Il flauto magico)", None), "Armide": ("Armide", None),
}
def fixtit(t): return TIT_FIX.get(t.strip(), (t.strip(), None))[0]

def pick_date_sl(Y, title, lo, hi, anno_fallback=None):
    x = sl[(sl.data.astype(str).between(lo, hi))]
    for _, r in x.iterrows():
        if sim(r.titolo, title) >= 0.8: return r.data, r
    if anno_fallback:
        x = sl[(sl.anno == anno_fallback)]
        for _, r in x.iterrows():
            if sim(r.titolo, title) >= 0.8: return r.data, r
    return "", None

# ================================================================ BLOCCO 1951-2026
rows = []
wp51 = wp[(wp.anno >= 1951) & (wp.anno <= 2026)].copy()
OVR = {  # correzioni a mano dove il parser della lista non basta (la fonte e' sempre la riga della lista it.wikipedia)
 2020: dict(opere="A riveder le stelle (serata di gala televisiva; nessuna opera in scena)", compositori="Autori vari", direttore="Riccardo Chailly", regia="Davide Livermore"),
 2021: dict(opere="Macbeth", compositori="Giuseppe Verdi"),
 2025: dict(opere="Una Lady Macbeth del distretto di Mcensk", compositori="Dmitrij Šostakovič"),
 2026: dict(direttore="Myung-whun Chung", regia="Damiano Michieletto"),
 1963: dict(opere="Cavalleria rusticana e L'amico Fritz (dittico)", compositori="Pietro Mascagni"),
 1983: dict(compositori="Giacomo Puccini (finale di Franco Alfano)"),
 1958: dict(compositori="Giacomo Puccini (finale di Franco Alfano)"),
 1964: dict(compositori="Giacomo Puccini (finale di Franco Alfano)"),
}
SALA = {2002: "Teatro degli Arcimboldi", 2003: "Teatro degli Arcimboldi"}
sbn_ok = sbn[sbn.tipo.isin(["produzione", "ospiti", "ospite"])]

def sbn_match(Y, title):
    """programmi di sala SBN della stessa stagione e dello stesso titolo"""
    st = f"{Y}-{(Y+1)%100:02d}"
    out = []
    for _, r in sbn_ok.iterrows():
        if str(r.stagione) != st and not str(r.data_prima).startswith(f"{Y}-12-0"): continue
        if sim(r.titolo, title) >= 0.8: out.append(r)
    return out

def reg_match(Y, title):
    out = []
    for _, r in reg.iterrows():
        if str(r.data_registrazione) == f"{Y}-12-07" and r.data_tipo == "giorno" and sim(r.opera, title) >= 0.8: out.append(r)
    return out

def opd_match(Y, title):
    out = []
    for _, r in opd.iterrows():
        if str(r.anno) == str(Y) and sim(r.opera, title) >= 0.8 and "dec" in str(r.date_scritte).lower() and re.search(r"\b7 December", str(r.date_scritte)):
            out.append(r)
    return out

# ascolti TV (tabella nella pagina it.wikipedia 'Prime stagionali')
ASC = {}
wt = json.load(open(P("raw", "wikipedia", "Prime_stagionali_al_Teatro_alla_Scala.json"), encoding="utf8"))["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
tb = wt[wt.find("== Ascolti =="):wt.find("== Addobbo floreale ==")]
cur_rete = ""; cur_cond = ""
for blk in tb.split("|-")[1:]:
    cells = [c.strip() for c in blk.strip().split("\n|") if c.strip()]
    cells = [re.sub(r"<ref.*?</ref>", "", c, flags=re.S) for c in cells]
    cells = [re.sub(r"\{\{formatnum:(\d+)\}\}", r"\1", c) for c in cells]
    cells = [re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", c).replace("''", "") for c in cells]
    if not cells or not re.match(r"^\|?\s*\d{4}/\d{2}", cells[0].lstrip("|").strip()): continue
    cells[0] = cells[0].lstrip("|").strip()
    y = int(cells[0][:4])
    rete = [re.sub(r"^rowspan=\"?\d+\"?\s*\|\s*", "", c).lstrip("| ").strip() for c in cells if re.search(r"Rai ?\d", c)]
    ASC[y] = dict(spett=int(cells[2]) if cells[2].isdigit() else None, share=cells[3] if len(cells) > 3 else "", rete=rete[0] if rete else "")
# la rete vale per tutte le righe del rowspan: Rai 5 (2010-2015), Rai 1 (2016-2025)
for y, a in ASC.items():
    if not a["rete"]: a["rete"] = "Rai 5" if y <= 2015 else "Rai 1"

COMPOSER_SRC = {}
for _, w in wp51.iterrows():
    Y = int(w.anno)
    o = dict(w)
    o.update(OVR.get(Y, {}))
    title = fixtit(o["opere"]); comp = o["compositori"]
    comp = cn(comp) if comp else ""
    cond = cn(o["direttore"]) if o["direttore"] else ""
    reg_ = cn(o["regia"]) if o["regia"] else ""
    if Y == 2013: reg_ = "Dmitrij Černjakov (regia e scene)"
    if Y == 2015: reg_ = "Moshe Leiser e Patrice Caurier"
    r = dict(blocco="dal_1951", anno=Y, stagione=f"{Y}/{str(Y+1)[2:]}", titolo=title, compositore=comp, direttore=cond, regia=reg_, sala=SALA.get(Y, "Teatro alla Scala (Piermarini)"))
    note = []; fonti = ["WP"]; srcs = {}
    r["tipo"] = "apertura della stagione lirica"
    # ---- date
    wdm = [x for x in WD if x["data"] == f"{Y}-12-07"]
    sd, srow = pick_date_sl(Y, title, f"{Y}-12-04", f"{Y}-12-08", anno_fallback=Y)
    date_src = []
    if wdm: date_src.append("WD")
    if sd == f"{Y}-12-07": date_src.append("SL")
    if str(Y) in scala: date_src.append("SC")
    if Y in ASC: date_src.append("TV(ascolti)")
    r["data"] = f"{Y}-12-07"; r["data_tipo"] = "esatta" if date_src else "attesa"
    if Y == 2026: r["data_tipo"] = "programmata"; note.append("Serata programmata per il 7 dicembre 2026 (non ancora avvenuta alla data di questa tabella); cast e direttore come annunciati dal Teatro")
    if Y == 2020: r["tipo"] = "apertura senza opera in scena (gala televisivo, Covid)"
    # ---- altre fonti per direttore/regia
    cand_dir = {"WP": cond}; cand_reg = {"WP": reg_}
    for x in wdm:
        if x["dir"]: cand_dir["WD"] = x["dir"]
        if x["reg"]: cand_reg["WD"] = x["reg"]
    if srow is not None:
        if srow.direttore: cand_dir["SL"] = srow.direttore.strip(" ;")
        if srow.regista: cand_reg["SL"] = srow.regista.strip(" ;")
    sm = sbn_match(Y, title) if Y < 2025 and Y != 2020 else []
    rg = reg_match(Y, title)
    if sm:
        for x in sm:
            if x.direttore: cand_dir["SBN"] = x.direttore
            if x.regista: cand_reg["SBN"] = x.regista
    for x in rg:
        if x.direttore: cand_dir["REG"] = x.direttore.split(";")[-1].strip() if "Veneziani" in x.direttore else x.direttore
    if str(Y) in scala:
        s = scala[str(Y)]
        cand_dir["SC"] = s.get("direttore", "").title(); cand_reg["SC"] = s.get("regia", "").title()
        if Y == 2026: cand_dir["SC"] = "Myung-Whun Chung"
    # conferme / differenze
    base_d = cond; base_r = reg_
    if not base_d:
        for k in ("SL", "WD", "SBN", "REG", "SC"):
            if cand_dir.get(k): base_d = cn(cand_dir[k]); log(Y, "direttore", f"mancava nella lista WP: preso da {k} ({cand_dir[k]})"); break
    if not base_r:
        for k in ("SL", "WD", "SBN", "SC"):
            if cand_reg.get(k): base_r = cn(cand_reg[k]); log(Y, "regia", f"mancava nella lista WP: presa da {k} ({cand_reg[k]})"); break
    r["direttore"] = base_d; r["regia"] = base_r
    ok_d = ["WP"] if cond else []; ok_r = ["WP"] if reg_ else []
    for k, v in cand_dir.items():
        if k == "WP" or not v: continue
        if base_d and any(same_person(a, v) for a in re.split(r"[;/]| e ", base_d)): ok_d.append(k)
        elif base_d: log(Y, "direttore", f"{k} dice «{v}», la lista WP dice «{base_d}»")
        else: ok_d.append(k)
    for k, v in cand_reg.items():
        if k == "WP" or not v: continue
        if base_r and any(same_person(a, v) for a in re.split(r"[;/]| e ", base_r)): ok_r.append(k)
        elif base_r: log(Y, "regia", f"{k} dice «{v}», la lista WP dice «{base_r}»")
        else: ok_r.append(k)
    r["direttore_fonti"] = "+".join(dict.fromkeys(ok_d)); r["regia_fonti"] = "+".join(dict.fromkeys(ok_r))
    # ---- cast
    cast = ""; cast_src = ""; extra = []
    if str(Y) in scala and scala[str(Y)]["cast"]:
        s = scala[str(Y)]; pairs = [p for p in s["cast"] if not p[0].startswith("*") and "Coro" != p[1] and len(p[0]) < 60][:10]
        cast = "; ".join(f"{b} ({a})" for a, b in pairs); cast_src = "SC"
        if Y == 2026: note.append("Cast annunciato dal sito della Scala (soggetto a variazioni)")
    elif w.cast_wp or (srow is not None and srow.interpreti):
        pass
    if not cast and srow is not None and srow.interpreti:
        cast = srow.interpreti.replace(";", "; ").replace("  ", " "); cast_src = "SL"
    if not cast and wp51.loc[wp51.anno == Y, "cast_wp"].iloc[0]:
        cast = wp51.loc[wp51.anno == Y, "cast_wp"].iloc[0]; cast_src = "WP"
    if not cast:
        for x in wdm:
            if x["cast"]: cast = "; ".join(x["cast"]); cast_src = "WD"
    if not cast and rg:
        names = []
        for x in rg:
            for n in str(x.interpreti).split(";"):
                n = n.strip()
                if n and n not in names: names.append(n)
        names = [n for n in names if surname(n) not in ("veneziani",)]
        cast = "; ".join(names[:8]); cast_src = "REG"
    if not cast and sm:
        for x in sm:
            if x.interpreti: cast = x.interpreti; cast_src = "SBN"; break
    r["interpreti"] = cast; r["interpreti_fonte"] = cast_src
    # altri cast (per il registro)
    others = {}
    for x in rg:
        if x.interpreti: others["REG"] = x.interpreti
    for x in sm:
        if x.interpreti: others["SBN"] = x.interpreti
    for x in wdm:
        if x["cast"]: others["WD"] = "; ".join(x["cast"])
    for k, v in others.items():
        if k != cast_src and cast:
            # nomi in v che non compaiono nel cast scelto
            mancanti = [n.strip() for n in re.split(r";", v) if n.strip() and not any(same_person(n, c) for c in re.split(r";|\(", re.sub(r"\([^)]*\)", "", cast)))]
            if mancanti: log(Y, "cast", f"{k} aggiunge: {', '.join(mancanti[:8])}")
    # controllo Operadis (solo locale)
    om = opd_match(Y, title)
    r["_cast_operadis"] = " | ".join(str(x.cast)[:400] for x in om)[:900]
    if om:
        names_op = []
        for x in om:
            for seg in str(x.cast).split("|"):
                n = seg.split(":")[-1].strip()
                if n: names_op.append(n)
        if cast:
            miss = [n for n in names_op[:6] if not any(same_person(n, c) for c in re.split(r";|\(", re.sub(r"\([^)]*\)", "", cast)))]
            if miss: log(Y, "cast", f"Operadis (solo controllo) cita anche: {', '.join(miss)}")
    # ---- fonti
    if wdm: fonti.append("WD")
    if srow is not None: fonti.append("SL")
    if sm: fonti.append("SBN")
    if rg: fonti.append("REG")
    if str(Y) in scala: fonti.append("SC")
    if om: fonti.append("OP(controllo)")
    # ---- note: TV, durata, prima assoluta, eventi
    tv = o["tv"]
    if tv: note.append(f"Trasmessa in diretta su {tv} (lista WP)")
    if Y in ASC and ASC[Y]["spett"]:
        a = ASC[Y]; note.append(f"TV {a['rete']}: {a['spett']:,} spettatori".replace(",", ".") + (f", share {a['share']}" if a["share"] else "") + " (tabella ascolti WP)")
    if o["nota_wp"]: note.append(o["nota_wp"][0].upper() + o["nota_wp"][1:] + " (lista WP)")
    if o["sala"]: note.append(f"Alla sala: {o['sala']} (teatro in ristrutturazione)" if Y in (2002, 2003) else f"Sala: {o['sala']}")
    r["note"] = "; ".join(note)
    r["_fonti"] = fonti
    r["fonti"] = "+".join(dict.fromkeys(f for f in fonti if not f.startswith("OP")))
    rows.append(r)

df51 = pd.DataFrame(rows)


# ---------------------------------------------------------------- cast aggiunti a mano da fonti lette (codice, testo, indirizzo/fonte)
CAST_EXTRA = {
 1955: ("WPI", "Maria Callas (Norma); Mario Del Monaco (Pollione); Giulietta Simionato (Adalgisa); Nicola Zaccaria (Oroveso)", "it.wikipedia 'Norma (opera)', discografia: «Teatro alla Scala, 7 dicembre» (ruoli dall'intestazione della tabella); stessi tre nomi principali in SBN"),
 1957: ("WPI", "Giuseppe Di Stefano (Riccardo); Maria Callas (Amelia); Ettore Bastianini (Renato); Giulietta Simionato (Ulrica); Eugenia Ratti (Oscar)", "it.wikipedia 'Un ballo in maschera', discografia (ruoli dall'intestazione); SBN"),
 1963: ("WPI", "L'amico Fritz: Mirella Freni (Suzel); Gianni Raimondi (Fritz); Bianca Maria Casoni (Beppe); Rolando Panerai (David); Piero De Palma (Federico)", "it.wikipedia 'L'amico Fritz', discografia: «Live 7 dicembre 1962» (anno che pare un refuso per 1963: SBN data la registrazione del dittico al 7/12/1963)"),
 2004: ("WPI", "Diana Damrau (Europa); Désirée Rancatore (Semele); Daniela Barcellona (Isseo); Giuseppe Sabbatini (Egisto); Genia Kühmeier (Asterio)", "it.wikipedia 'L'Europa riconosciuta', discografia: «Registrato alla Scala il 7 dicembre 2004»"),
 2005: ("WPE", "Steve Davislim; Monica Bacelli; Camilla Tilling; Emma Bell; Francesco Meli", "en.wikipedia 'Idomeneo' (registrazione RAI Trade, Harding 2005); Wikidata"),
 2006: ("WPE", "Violeta Urmana (Aida); Roberto Alagna (Radamès); Ildikó Komlósi; Roberto Bolle (danza)", "en.wikipedia 'Aida'; Wikidata"),
 2007: ("WEB", "Ian Storey (Tristan); Waltraud Meier (Isolde); Michelle DeYoung (Brangäne); Matti Salminen (König Marke); Gerd Grochowski (Kurwenal); Will Hartmann (Melot)", "wagnerdisco.net/atr/atr-2000-2009/2007-12-07-barenboim-milano/; thewholenote.com (recensione del video)"),
 2008: ("WEB", "Stuart Neill (Don Carlo); Fiorenza Cedolins (Elisabetta); Ferruccio Furlanetto (Filippo II)", "NPR, 19/12/2008 «Intrigue and uproar: Don Carlo at La Scala» (didascalia della foto); gli altri ruoli non trovati"),
 2009: ("WEB", "Anita Rachvelishvili (Carmen); Jonas Kaufmann (Don José); Erwin Schrott (Escamillo)", "Gramophone «Curtain rises on Carmen at La Scala»; operaonvideo.com (Escamillo)"),
 2013: ("WEB", "Diana Damrau (Violetta); Piotr Beczała (Alfredo); Željko Lučić (Giorgio Germont)", "culture.pl «Beczała kicks off 13-14 La Scala season»; opera-online.com"),
 2014: ("WEB", "Anja Kampe (Leonore); Klaus Florian Vogt (Florestan); Kwangchul Youn (Rocco); Peter Mattei (Don Fernando); Falk Struckmann (Don Pizarro); Mojca Erdmann (Marzelline)", "deborahwarner.com/2018-fidelio-milan (distribuzione 2014); bachtrack.com 7/12/2014"),
 2015: ("WPI", "Anna Netrebko (Giovanna); Francesco Meli; Devid Cecconi (al posto di Carlos Álvarez, ammalato)", "it.wikipedia 'Giovanna d'Arco (opera)'"),
 2016: ("WEB", "Maria José Siri (Cio-Cio-San); Bryan Hymel (Pinkerton); Carlos Álvarez (Sharpless); Annalisa Stroppa (Suzuki); Carlo Bosi (Goro)", "bachtrack.com/opera-event/madama-butterfly-1904-version-teatro-alla-scala-7-december-2016/253518; apemusicale.it"),
 2017: ("WEB", "Yusif Eyvazov (Andrea Chénier); Anna Netrebko (Maddalena di Coigny); Luca Salsi (Carlo Gérard); Annalisa Stroppa (Bersi); Mariana Pentcheva (contessa di Coigny)", "bachtrack.com 7/12/2017; myscena.org; Wikidata (Eyvazov, Netrebko)"),
 2018: ("WEB", "Ildar Abdrazakov (Attila); Saioa Hernández (Odabella); Fabio Sartori (Foresto); George Petean (Ezio)", "lapresse.it, operawire.com (7/12/2018); it.wikipedia 'Attila (opera)' per Abdrazakov"),
 2019: ("WEB", "Anna Netrebko (Tosca); Francesco Meli (Cavaradossi); Luca Salsi (Scarpia)", "agi.it 7/12/2019; sorrisi.com"),
 2021: ("WEB", "Luca Salsi; Anna Netrebko (Lady Macbeth); Francesco Meli; Ildar Abdrazakov", "agi.it 7/12/2021; tg24.sky.it; seenandheard-international.com (ruoli degli altri non trovati)"),
}
NOTE_EXTRA = {
 2008: "Avvenire titola «Fischi alla Scala, il direttore: andiamo oltre» sulla serata [avvenire.it]",
 2009: "Esordio nella regia lirica di Emma Dante; 14 minuti di applausi per Rachvelishvili [Gramophone, Il Giorno]",
 2013: "Prima nuova produzione di Traviata alla Scala dopo quella del 1990; serata nel bicentenario della nascita di Verdi [wantedinrome.com, opera-online.com]; i giornali riportano applausi e fischi [tgcom24]",
 2014: "Ultima serata di Barenboim come direttore musicale; 13 minuti di ovazione (Reuters) [malaymail.com]",
 2016: "14 minuti di applausi [LaPresse]",
 2017: "Terza apertura di Netrebko; esordio alla Scala di Yusif Eyvazov [operawire.com]",
 2018: "Terza apertura di Abdrazakov; trasmessa in diretta su Rai 1 e Radio 3; 14-15 minuti di applausi [lapresse.it, operawire.com]",
 2019: "Presente il presidente Mattarella; 16 minuti di applausi [agi.it]; Saioa Hernández subentra come Tosca il 2, 5 e 8 gennaio",
 2021: "Quarta apertura consecutiva di Chailly con Livermore; versione 1865 con la morte del protagonista del 1847 [agi.it, avvenire.it]",
}

# ---------------------------------------------------------------- note a mano, ogni voce con la fonte (solo fatti letti nelle fonti scaricate)
HAND = {
 1951: "Prima apertura il 7 dicembre voluta da Victor de Sabata (in precedenza la stagione cominciava il 26 dicembre); trionfo milanese di Maria Callas [it.wikipedia 'Teatro alla Scala']",
 1952: "Maria Callas, Enzo Mascherini, Gino Penno, Italo Tajo nella registrazione dal vivo del 7/12/1952 [SBN]",
 1953: "Prima del 1953: apertura con 'La Wally' diretta da Giulini [lista WP e Wikidata]",
 1954: "Prima regia lirica di Luchino Visconti; Maria Callas protagonista [en.wikipedia 'La vestale']; direttore Antonino Votto, non De Sabata come scrive la cronistoria SL: lo confermano la registrazione dal vivo del 7/12/1954 (Warner Classics) e i cataloghi NYPL; Victor de Sabata era allora direttore artistico del teatro; esordio alla Scala di Franco Corelli",
 1955: "Registrazione dal vivo del 7/12/1955: Callas, Del Monaco, Simionato; direttore Antonino Votto [SBN]; la tabella precedente del sito non aveva il direttore",
 1957: "Registrazione dal vivo del 7/12/1957: Callas, Di Stefano, Bastianini, Simionato [SBN]",
 1958: "Registrazione dal vivo del 7/12/1958: Birgit Nilsson, Di Stefano, Carteri [SBN]",
 1959: "Direttore Antonino Votto e regia di Margherita Wallmann [lista WP e Wikidata]; la tabella precedente del sito non aveva il direttore",
 1960: "Registrazione dal vivo del 7/12/1960: Callas, Corelli, Bastianini, Zaccaria [en.wikipedia 'Poliuto'; SBN registra 'Franco Cordelli' per Corelli]",
 1963: "Dittico in una sera",
 1968: "Primo di due Don Carlo diretti da Abbado il 7 dicembre (1968 e 1977) [sito Scala 2023]",
 1969: "Registrazione dal vivo del 7/12/1969: Domingo, Ghiaurov, Kabaivanska [SBN]",
 1977: "Secondo Don Carlo diretto da Abbado il 7 dicembre [sito Scala 2023]",
 1978: "Ripresa dell'allestimento di Strehler del 1971, dopo la tournée all'Opéra di Parigi (ottobre-novembre 1978). Il programma di sala della Scala indica «Prima rappresentazione 7 dicembre 1978» [teatrodel900.it, programma di sala]. La nota della lista WP («replica») va letta come ripresa di un vecchio allestimento, non come serata non inaugurale. La scheda SBN che data al 7/12/1978 un Boris Godunov è un errore di data: il Boris di Abbado e Ljubimov è del 7/12/1979 [sito Scala 2022]",
 1979: "Boris Godunov di Abbado e Ljubimov il 7 dicembre 1979, ricordato dalla stessa Scala nella pagina del Boris 2022",
 1981: "Prima rappresentazione 7 dicembre (8 recite) [SL]",
 1984: "Trasmessa in diretta alle 19,50 su Raiuno [SL]",
 1985: "Trasmessa in diretta alle 19,55 su Raidue e Rai Radio 3 [SL]; dal 1985 i fioristi milanesi addobbano il teatro per la serata [WP]",
 1986: "Trasmessa in diretta alle 19,45 su Raitre e Rai Radio 3 [SL]",
 1987: "Trasmessa in diretta alle 19,55 su Rai Radio 3 [SL]",
 1988: "Trasmessa in diretta alle 18,55 su Rai Radio 3 [SL]",
 1989: "Trasmessa in diretta alle 19,25 su Rai Radio 3 [SL]",
 1992: "Serata segnata dal clima di austerità dopo Mani Pulite; addobbo con 20 mila garofani [WP 'Addobbo floreale']",
 1993: "Addobbo pagato dall'Unione del Commercio (nessun produttore di fiori disponibile) [WP]",
 1994: "Polemica tra fioristi milanesi e sovrintendente sull'addobbo [WP]",
 2002: "Alla serata agli Arcimboldi: il teatro Piermarini era chiuso per la ristrutturazione",
 2003: "Alla serata agli Arcimboldi: il teatro Piermarini era chiuso per la ristrutturazione",
 2004: "Riapertura del teatro Piermarini dopo quasi tre anni di lavori; l'Europa riconosciuta di Salieri (opera inaugurale del 1778) non si rappresentava dal 1778 [en.wikipedia 'L'Europa riconosciuta']",
 2005: "Daniel Harding, regia di Luc Bondy; la lista WP non dà il regista: lo dà Wikidata",
 2006: "Prima di Chailly come direttore di un'apertura; ad Alagna, dopo i fischi alla seconda recita, la Scala tolse la parte [en.wikipedia 'Aida']",
 2008: "Dal 2008 la serata del 7 dicembre è preceduta dall'anteprima per i giovani under 30 [it.wikipedia 'Teatro alla Scala']",
 2012: "Il ruolo di Elsa: Ann Petersen il 4 dicembre, Annette Dasch il 7 dicembre [SL]",
 2016: "Madama Butterfly nella versione originale del 1904 [en.wikipedia 'Madama Butterfly']",
 2020: "Per la pandemia la 'prima' è stata annullata e sostituita da un concerto a porte chiuse in diretta TV, 'A riveder le stelle' (direttore Chailly, regia Livermore) [it.wikipedia 'Teatro alla Scala']; era prevista 'Lucia di Lammermoor' (Chailly, regia Kokkos) [lista WP]; è la nona apertura di Chailly se si conta anche questa [sito Scala 2022]",
 2021: "La cronistoria 'Stagioni liriche' scrive «prima rappresentazione: 4 dicembre»; la serata del 7 dicembre è confermata dalla tabella degli ascolti TV (martedì 7 dicembre 2021) [WP]",
 2022: "Nona apertura di Chailly; versione originale del 1869 (in quattro parti); Abbado e Ljubimov avevano aperto con questo titolo il 7 dicembre 1979 [sito Scala 2022]",
 2023: "Il sito della Scala indica Michele Pertusi come Filippo II nella sera del 7 dicembre; la lista WP riporta René Pape [SC contro SL]",
}
df51["controlli"] = ""
for y, (cod, txt, fonte) in CAST_EXTRA.items():
    i = df51.index[df51.anno == y][0]
    if df51.loc[i, "interpreti_fonte"] not in ("SC", "SL"):
        old = df51.loc[i, "interpreti"]
        df51.loc[i, "interpreti"] = txt; df51.loc[i, "interpreti_fonte"] = cod
        if old: log(y, "cast", f"cast sostituito da quello con i ruoli ({cod}): prima «{old[:120]}» ({df51.loc[i, 'interpreti_fonte']})")
        df51.loc[i, "fonti"] = df51.loc[i, "fonti"] + "+" + cod if df51.loc[i, "fonti"] else cod
        df51.loc[i, "controlli"] = (df51.loc[i, "controlli"] + "; " if df51.loc[i, "controlli"] else "") + "cast: " + fonte
        if cod in ("WEB", "WPI", "WPE") and y not in (1955, 1957, 1963):
            df51.loc[i, "direttore_fonti"] += "+" + cod
# 30/10/2026: cast dei due dubbi risolti online
for _y, _txt, _src in [
    (1954, "Maria Callas (Giulia); Franco Corelli (Licinio); Ebe Stignani (la Gran Vestale); Enzo Sordello (Cinna); Nicola Rossi-Lemeni (il Sommo Sacerdote)", "registrazione dal vivo 7/12/1954 (Warner Classics; catalogo NYPL); Operadis"),
    (1978, "Piero Cappuccilli (Simon Boccanegra); Mirella Freni (Amelia); Nicolai Ghiaurov (Fiesco); Veriano Luchetti (Gabriele Adorno); Felice Schiavi (Paolo)", "programma di sala della Scala 1978 (teatrodel900.it)")]:
    _i = df51.index[df51.anno == _y][0]
    df51.loc[_i, "interpreti"] = _txt; df51.loc[_i, "interpreti_fonte"] = "WEB"
    df51.loc[_i, "fonti"] = df51.loc[_i, "fonti"] + "+WEB"
    df51.loc[_i, "direttore_fonti"] = df51.loc[_i, "direttore_fonti"] + "+WEB"
    df51.loc[_i, "controlli"] = (df51.loc[_i, "controlli"] + "; " if df51.loc[_i, "controlli"] else "") + "cast: " + _src
df51.loc[df51.anno == 1978, "note"] = ""
for y, n in NOTE_EXTRA.items(): HAND[y] = (HAND[y] + "; " + n) if y in HAND else n
for y, n in HAND.items():
    i = df51.index[df51.anno == y]
    if len(i):
        cur = df51.loc[i[0], "note"]
        df51.loc[i[0], "note"] = (cur + "; " if cur else "") + n
# 1953: tolgo la nota ridondante
df51.loc[df51.anno == 1953, "note"] = df51.loc[df51.anno == 1953, "note"].str.replace("Prima del 1953: apertura con 'La Wally' diretta da Giulini [lista WP e Wikidata]", "", regex=False).str.strip("; ")

# ---------------------------------------------------------------- livello di documentazione 1951-2026
log(1978, "titolo", "RISOLTO 30/10/2026: la lista WP parla di replica, la cronistoria SL di prima del 7 dicembre; il programma di sala della Scala (teatrodel900.it) indica prima rappresentazione 7 dicembre 1978: fu l'apertura, con la ripresa dell'allestimento 1971. La scheda SBN del Boris al 7/12/1978 è un errore di data (Boris: 7/12/1979)")
log(1954, "direttore", "RISOLTO 30/10/2026: Votto, confermato da registrazione Warner Classics del 7/12/1954 e cataloghi NYPL; De Sabata nella cronistoria SL è un errore (era direttore artistico)")
CONFL = {}
for _y, _c, _t in LOG:
    if _c in ("direttore", "regia", "titolo", "data") and " dice " in _t and not _t.startswith("RISOLTO") and _y not in (1954, 1978): CONFL.setdefault(_y, []).append(_c)
def livello(r):
    if r["anno"] in CONFL and r["anno"] != 2020: return "con disaccordi tra le fonti"
    n_dir = len(r["direttore_fonti"].split("+")) if r["direttore_fonti"] else 0
    n_reg = len(r["regia_fonti"].split("+")) if r["regia_fonti"] else 0
    if r["anno"] == 2020: return "gala (nessuna opera): documentata"
    ok_base = bool(r["titolo"] and r["compositore"] and r["data"] and r["direttore"])
    cast_ok = bool(r["interpreti"])
    if ok_base and r["regia"] and n_dir >= 2 and cast_ok: return "completa"
    if ok_base and r["regia"] and n_dir >= 2: return "senza cast"
    if ok_base and r["regia"]: return "una sola fonte per il direttore"
    return "lacune"
df51["completezza"] = df51.apply(livello, axis=1)

# ================================================================ BLOCCO PRIMA DEL 1951
rows0 = []
def comp_lookup(title, Y):
    c = cart[(cart.anno.between(Y, Y + 2)) & (cart.fonte.isin(["wikipedia_it_stagioni_liriche", "wikidata_prime"]))]
    for _, r in c.iterrows():
        if sim(r.titolo, title) >= 0.85 and r.autore: return r.autore
    return ""

def plausible_sl(d): return bool(d) and str(d)[5:7] in ("10", "11", "12")

def cam_block(Y, off=1):
    x = cam[(cam.anno == Y + off) & (cam.stagione_nome == "Carnevale")]
    return x[~x.genere.astype(str).str.contains("ballo")]
def rom_block(Y, off=1):
    return rom[(rom.anno == Y + off) & (rom.stagione_nome.str.contains("Carnevale", case=False))]
def pulisci_ocr(t):
    t = re.sub(r"\s+[^\w\s]+\S*$", "", str(t)).strip()
    t = re.sub(r"\s+(?:-?[a-zA-Z]{1,2}|[#X\^\$\*]+)$", "", t).strip()
    t = re.sub(r"['’]{2,}$", "", t)
    return t
def mar_block(Y):
    return mar[(mar.anno.between(Y, Y + 1)) & (mar.stagione_nome.str.contains("Carnevale"))]
def in_blocks(df, title, years, extra=None):
    for _, r in df.iterrows():
        if sim(r.titolo, title) >= 0.8: return r
    return None

wp0 = wp[(wp.anno <= 1950)]
by_year = {}
for _, w in wp0.iterrows():
    key = (int(w.anno), "autunno" if w.tipo == "autunno 1778" else "car")
    by_year[key] = w
SEASON_NAMES = {}
for Y in range(1778, 1951):
    w = by_year.get((Y, "car"))
    wd_in = [x for x in WD if f"{Y}-07-01" <= x["data"] <= f"{Y+1}-06-30" and x["data"] != ""]
    # candidati WD che non siano l'autunno 1778
    if Y == 1778: wd_in = [x for x in wd_in if not x["data"].startswith("1778-08")]
    r = dict(blocco="prima_1951", anno=Y, stagione=f"{Y}/{str(Y+1)[2:]}" if Y != 1899 else "1899/00", sala="Teatro alla Scala (Piermarini)")
    r["tipo"] = w.tipo if w is not None and w.tipo else ""
    fonti = []; note = []
    title = ""; comp = ""; cond = ""; reg_ = ""; cast = ""; chiuso = False
    if w is not None:
        fonti.append("WP"); chiuso = bool(w.chiuso)
        title = w.opere; comp = w.compositori; cond = w.direttore; reg_ = w.regia; cast = w.cast_wp
        if w.sala: r["sala"] = w.sala + (" (teatro Piermarini distrutto dai bombardamenti del 1943)" if Y >= 1943 else "")
        if w.corriere: note.append("Giornale citato dalla lista WP: Corriere della Sera, " + w.corriere)
        if w.tv: note.append("Diretta " + w.tv)
    # fix titoli (parsing 'di')
    title = title.replace(" (ballo)", " (balletto)")
    r["chiuso"] = int(chiuso)
    # --- ricerca in Cambiasi / Romani / Marangoni / Gatti
    cb = cam_block(Y); rb = rom_block(Y); mb = mar_block(Y) if 1906 <= Y <= 1920 else mar.iloc[0:0]
    first_title = title.split(" + ")[0] if title else ""
    cam_first = cb.iloc[0] if len(cb) else None
    rom_first = rb.iloc[0] if len(rb) else None
    mar_first = mb.iloc[0] if len(mb) else None
    ev = {}
    if not chiuso and first_title:
        def check(df_fun, first, blk):
            if first is not None:
                if sim(first.titolo, first_title) >= 0.8: return "primo"
                for off in (2, 0):
                    b2 = df_fun(Y, off)
                    if len(b2) and sim(b2.iloc[0].titolo, first_title) >= 0.8: return "primo (anno del libro sfalsato di %+d)" % (off - 1)
                if in_blocks(blk, first_title, None) is not None: return "in stagione"
                return "assente"
            for off in (2, 0):
                b2 = df_fun(Y, off)
                if len(b2) and sim(b2.iloc[0].titolo, first_title) >= 0.8: return "primo (anno del libro sfalsato di %+d)" % (off - 1)
            return "nessun dato"
        ev["CA"] = check(cam_block, cam_first, cb)
        ev["RO"] = check(rom_block, rom_first, rb)
        if len(mb):
            if sim(mar_first.titolo, first_title) >= 0.8: ev["MA"] = "primo"
            elif in_blocks(mb, first_title, None) is not None: ev["MA"] = "in stagione"
            else: ev["MA"] = "assente"
        g = gat[(gat.anno.astype(str).str[:4].isin([str(Y), str(Y + 1)])) & (gat.segnale_spettacolo == "si")]
        if len(g): ev["GA"] = "citato" if any(sim(t, first_title) >= 0.85 for t in g.titolo) else "assente"
    # --- data
    date = ""; dtipo = ""; dtext = ""
    plaus = lambda d: bool(d) and d[5:7] in ("10", "11", "12")
    wd_in = [x for x in wd_in if plaus(x["data"])]
    wdc = [x for x in wd_in if (not first_title) or sim(x["label"], first_title) >= 0.7 or x["label"].startswith("serata") or (x["opera"] and sim(x["opera"], first_title) >= 0.7)]
    wd_conflict = [x for x in wd_in if x not in wdc]
    if wdc:
        date = wdc[0]["data"]; dtipo = "esatta"; fonti.append("WD")
    srow = None
    if first_title:
        sd, srow = pick_date_sl(Y, first_title, f"{Y}-07-01", f"{Y+1}-06-30")
        if not date and sd and plausible_sl(sd):
            date = sd; dtipo = "esatta"; fonti.append("SL")
        elif not date and sd:
            log(Y, "data", f"stagione {Y}/{str(Y+1)[2:]} «{first_title}»: la cronistoria SL data il titolo al {sd}, che non e' l'inizio del Carnevale: data dell'apertura non usata")
    if not date and cam_first is not None and ev.get("CA") == "primo" and cam_first.data and plausible_sl(cam_first.data):
        date = cam_first.data; dtipo = "esatta"; fonti.append("CA")
    if not date and len(mb) and ev.get("MA") == "primo":
        m0 = mar_first
        if m0.mese and m0.giorno != "":
            mm = {"Gennaio": 1, "Febbraio": 2, "Marzo": 3, "Aprile": 4, "Maggio": 5, "Giugno": 6, "Luglio": 7, "Agosto": 8, "Settembre": 9, "Ottobre": 10, "Novembre": 11, "Dicembre": 12}.get(str(m0.mese))
            if mm and mm >= 10: date = f"{Y}-{mm:02d}-{int(float(m0.giorno)):02d}"; dtipo = "esatta"; fonti.append("MA")
    r["data"] = date; r["data_tipo"] = dtipo or "solo anno"
    if not date and w is not None and w.corriere:
        dtext = w.corriere.split(" «")[0]
    # --- verdetto
    note_alt = ""
    alt = []
    if wd_conflict:
        for x in wd_conflict:
            alt.append(f"Wikidata dà come serata inaugurale {x['data']} «{x['label']}»")
            log(Y, "titolo", f"stagione {Y}/{str(Y+1)[2:]}: lista WP «{first_title}», Wikidata «{x['label']}» il {x['data']}")
    if ev.get("CA") == "assente" and cam_first is not None:
        alt.append(f"il Cambiasi elenca come primo della stagione «{cam_first.titolo}»")
        log(Y, "titolo", f"stagione {Y}/{str(Y+1)[2:]}: lista WP «{first_title}», Cambiasi (primo titolo della stagione) «{cam_first.titolo}» (data {cam_first.data or 'n.d.'})")
    if ev.get("RO") == "assente" and rom_first is not None and rom_first.titolo and sim(rom_first.titolo, first_title) < 0.8:
        alt.append(f"Romani elenca per prima «{rom_first.titolo}»")
        log(Y, "titolo", f"stagione {Y}/{str(Y+1)[2:]}: lista WP «{first_title}», Romani (primo titolo) «{rom_first.titolo}»")
    # --- livello di affidabilità
    ind_primo = [k for k in ("CA", "RO", "MA") if str(ev.get(k)).startswith("primo")]
    ind_pres = [k for k in ("CA", "RO", "MA", "GA") if str(ev.get(k)).startswith(("primo", "in stagione", "citato"))]
    fam = [f for f in fonti if f in ("WP", "WD", "SL")]
    has_press = bool(w is not None and w.corriere)
    if chiuso:
        aff = "chiuso"
    elif not first_title:
        aff = "nessun dato"
    else:
        if len(ind_primo) >= 1 and len(set(fam)) >= 1: aff = "alta"
        elif (len(ind_pres) >= 1 or has_press) and len(set(fam)) >= 2: aff = "alta" if (has_press and len(set(fam)) >= 2) else "media"
        elif (len(ind_pres) >= 1 or has_press) and len(set(fam)) >= 1: aff = "media"
        elif len(set(fam)) >= 2: aff = "media"
        else: aff = "bassa"
        if alt and aff == "alta": aff = "media"
        if alt and aff in ("media",) and (ev.get("CA") == "assente" and ev.get("RO") in ("assente", "nessun dato")): aff = "bassa"
    # stagioni senza riga nella lista WP: ricostruzione
    ric = ""
    if w is None or (not title and not chiuso):
        cands = []
        if wdc: cands.append(("WD", wdc[0]["label"]))
        if cam_first is not None: cands.append(("CA", cam_first.titolo))
        if rom_first is not None and rom_first.titolo: cands.append(("RO", rom_first.titolo))
        if cands and not (wdc and sim(wdc[0]["label"], "x") == 0 and wdc[0]["label"].startswith("serata")):
            pass
        t0 = ""
        if wdc and not wdc[0]["label"].startswith("serata"): t0 = wdc[0]["label"]; ric = "Wikidata"
        elif wdc and wdc[0]["opera"]: t0 = wdc[0]["opera"]; ric = "Wikidata"
        elif cam_first is not None: t0 = pulisci_ocr(cam_first.titolo); ric = "Cambiasi 1881 (primo titolo del Carnevale)"
        elif rom_first is not None and rom_first.titolo: t0 = pulisci_ocr(rom_first.titolo); ric = "Romani 1862 (primo titolo del Carnevale)"
        title = t0; first_title = t0
        if t0:
            note.append(f"Stagione assente dalla lista WP: titolo ricostruito da {ric} (lettura OCR: da controllare sul libro)")
            fonti = [f for f in fonti if f != "WP"]
            if ric.startswith("Cambiasi"): fonti.append("CA")
            if ric.startswith("Romani"): fonti.append("RO")
            aff = "bassa"
            if cam_first is not None and rom_first is not None and sim(cam_first.titolo, rom_first.titolo) >= 0.8: aff = "media"; fonti.append("RO")
            if cam_first is not None and rom_first is None and wdc: aff = "media"
            log(Y, "mancante", f"stagione {Y}/{str(Y+1)[2:]} assente dalla lista WP: ricostruita come «{t0}» da {ric}")
        else:
            aff = "nessun dato"
    r["titolo"] = fixtit(title).strip() if title else ""
    if not comp and r["titolo"]: comp = comp_lookup(first_title, Y)
    r["compositore"] = comp
    r["direttore"] = cn(cond) if cond else ""; r["regia"] = cn(reg_) if reg_ else ""
    r["interpreti"] = cast; r["interpreti_fonte"] = "WP" if cast else ""
    r["direttore_fonti"] = "WP" if cond else ""; r["regia_fonti"] = "WP" if reg_ else ""
    # direttore/regia da SL se la lista non li ha
    if first_title and (not cond or not reg_):
        sd, srow = pick_date_sl(Y, first_title, f"{Y}-07-01", f"{Y+1}-06-30")
        if srow is not None:
            if not cond and srow.direttore: r["direttore"] = cn(srow.direttore); r["direttore_fonti"] = "SL"
            if not reg_ and srow.regista: r["regia"] = cn(srow.regista); r["regia_fonti"] = "SL"
            if not cast and srow.interpreti: r["interpreti"] = srow.interpreti.replace(";", "; "); r["interpreti_fonte"] = "SL"
            if "assoluta" in str(srow.prima).lower(): note.append("Prima rappresentazione assoluta (cronistoria SL)")
    # WD: direttore (es. 1948 Karajan)
    for x in wdc[:1]:
        if x["dir"]:
            if r["direttore"] and not any(same_person(a, x["dir"]) for a in re.split(r"[;/]| e ", r["direttore"])):
                log(Y, "direttore", f"{Y}/{str(Y+1)[2:]} «{first_title}»: Wikidata dice «{x['dir']}», la lista WP dice «{r['direttore']}»")
                alt.append(f"Wikidata indica come direttore {x['dir']}")
            elif not r["direttore"]:
                r["direttore"] = x["dir"]; r["direttore_fonti"] = "WD"
        if x["reg"] and not r["regia"]:
            r["regia"] = x["reg"]; r["regia_fonti"] = "WD"
    # asterisco di Cambiasi = scritta per la Scala
    if cam_first is not None and ev.get("CA") == "primo" and str(cam_first.prima_per_la_scala) == "si":
        note.append("Scritta apposta per la Scala (asterisco nel Cambiasi)")
    if 1943 <= Y <= 1945: note.append("Il teatro Piermarini era distrutto (bombardamento dell'agosto 1943); riaperto l'11 maggio 1946")
    r["fonti"] = "+".join(dict.fromkeys(fonti))
    r["controlli"] = "; ".join(f"{k}:{v}" for k, v in ev.items())
    r["affidabilita"] = aff
    r["alternativa"] = "; ".join(alt)
    r["data_testo"] = dtext
    r["note"] = "; ".join(note)
    r["_fonti"] = fonti
    rows0.append(r)

# l'apertura del teatro, 3 agosto 1778
a0 = dict(blocco="prima_1951", anno=1778, stagione="1778 (autunno)", tipo="inaugurazione del teatro", titolo="L'Europa riconosciuta", compositore="Antonio Salieri",
          direttore="", regia="", sala="Teatro alla Scala (Piermarini)", data="1778-08-03", data_tipo="esatta",
          interpreti="Maria Balducci (Europa); Gaspare Pacchiarotti (Asterio); Francesca Danzi (Semele); Giovanni Rubinelli (Isséo); Antonio Prati (Egisto)", interpreti_fonte="SL",
          direttore_fonti="", regia_fonti="", fonti="WP+WD+SL+CA", controlli="CA:primo (Autunno 1778)", affidabilita="alta", alternativa="",
          data_testo="", note="Inaugurazione del teatro: opera scritta per l'occasione; scene dei fratelli Galliari; seguita da «Troia distrutta» di Mortellari [SL, Romani p. 1]; riproposta il 7 dicembre 2004 per la riapertura del Piermarini",
          chiuso=0, _fonti=["WP", "WD", "SL", "CA"])
df0 = pd.DataFrame([a0] + rows0)
# correzione manuale della stagione 1778/79 (la lista WP la elenca come 'Carnevale 1778/79: Calliroe')
df0.loc[(df0.anno == 1778) & (df0.stagione == "1778/79"), "tipo"] = "Carnevale"

# ---------------------------------------------------------------- scrittura
cols = ["blocco", "stagione", "anno", "tipo", "data", "data_tipo", "data_testo", "titolo", "compositore", "direttore", "regia", "interpreti", "interpreti_fonte",
        "sala", "note", "affidabilita", "completezza", "fonti", "direttore_fonti", "regia_fonti", "controlli", "alternativa"]
for c in cols:
    for d in (df51, df0):
        if c not in d.columns: d[c] = ""
df51["affidabilita"] = df51["completezza"].map(lambda s: "alta" if s in ("completa", "gala (nessuna opera): documentata") else ("media" if s in ("senza cast", "con disaccordi tra le fonti") else "bassa"))
df0["completezza"] = ""
full = pd.concat([df0[cols], df51[cols]], ignore_index=True)
full = full.sort_values(["blocco", "anno", "stagione"], key=lambda s: s.map({"prima_1951": 0, "dal_1951": 1}) if s.name == "blocco" else s, kind="stable").reset_index(drop=True)
full.to_csv(P("pulito", "aperture.csv"), index=False, encoding="utf-8-sig")
# colonna riservata (Operadis) solo in un file locale a parte
df51[["anno", "titolo", "_cast_operadis"]].to_csv(P("pulito", "_aperture_cast_operadis_LOCALE.csv"), index=False, encoding="utf-8-sig")
json.dump(LOG, open(P("pulito", "_aperture_log.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("righe:", len(full), "| dal_1951:", len(df51), "| prima_1951:", len(df0))
print(df51["completezza"].value_counts().to_dict())
print(df0["affidabilita"].value_counts().to_dict())
print("log:", len(LOG))
