"""Pagina "Fonti e metodo" di Milano in dati: legge ogni pagina del sito e ne ricava
fonti (editore, dataset, link, licenza, data di scarico), limiti dei dati e "dati che non esistono in forma aperta".

Scrive:
  docs/fonti/data/fonti.json   tutti i numeri della pagina
  docs/fonti/data/fonti.csv    una riga per pagina e fonte (si apre in Excel)

Uso (Python 3.12):
  python -I -X utf8 pagina.py --radice <cartella milano-in-dati> [--cache <cartella>] [--aggiorna] [--senza-browser]

  --aggiorna       riscarica con il browser l'HTML "dopo JavaScript" di tutte le pagine (di norma si riusa la cache)
  --senza-browser  non usa il browser: legge l'HTML scritto sul disco (le parti scritte da JavaScript mancano)

Le correzioni a mano stanno in correzioni.json (accanto a questo file), con il motivo di ciascuna.
Si può rilanciare quante volte si vuole.
"""
import argparse
import csv
import datetime as dt
import html as htmllib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dom  # noqa: E402
import regole as R  # noqa: E402

PAGINE_FUORI = {"fonti", "elenco"}
ALIAS_NOTE = {  # cartella del filone -> pagine che ne escono (quando il nome non coincide)
    "donne-nelle-vie": ["vie"],
    "pioggia-e-caldo": ["pioggia", "caldo"],
    "popolazione": ["arrivi-partenze", "eta", "comunita"],
    "nomi-bambini": [],
    "film-e-libri": ["milano-raccontata"],
}
ALTRI_MARCATORI = re.compile(
    r"\s(?:Programmi e note|Programmi, note|Programmi e file|Altre pagine|Pagine collegate|Pagina sorella|Vedi anche|Torna alla)")
SEZ_FONTI = re.compile(r"^(?:fonti?\b|licenz|fonte e licenza|dati e fonti|da dove vengono)", re.I)
MESE_IT = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


# ------------------------------------------------------------------ utilità sul testo
def norm(s):
    s = s.replace("’", "’").replace("'", "’")
    return re.sub(r"\s+", " ", s).strip()


def tronca(s, n):
    s = norm(s)
    if len(s) <= n:
        return s
    t = s[:n]
    k = max(t.rfind(". "), t.rfind("; "))
    if k > n * 0.55:
        return t[:k + 1]
    return t[:t.rfind(" ")].rstrip(",;:") + "…"


def data_iso(m):
    """Da un match di DATA_ANY ritorna la lista di date ISO (1 o 2)."""
    g = m.groups()
    try:
        if g[0]:  # intervallo "1-2 novembre 2026"
            a, b, mese, y = int(g[0]), int(g[1]), R.MESI[g[2].lower()], int(g[3])
            return [dt.date(y, mese, a).isoformat(), dt.date(y, mese, b).isoformat()]
        if g[4]:
            return [dt.date(int(g[6]), R.MESI[g[5].lower()], int(g[4])).isoformat()]
        if g[7]:
            return [dt.date(int(g[9]), int(g[8]), int(g[7])).isoformat()]
        if g[10]:
            return [dt.date(int(g[10]), int(g[11]), int(g[12])).isoformat()]
    except (ValueError, KeyError):
        return []
    return []


def date_di_scarico(testo):
    """Date che seguono (o precedono di poco) parole come "scaricati", "interrogato", "letti"."""
    out = []
    for kw in R.PAROLA_SCARICO.finditer(testo):
        fin = testo[kw.end():kw.end() + 80]
        fin = re.split(r"(?<=[a-z\)])\.\s+[A-ZÀ-Ú«]", fin)[0]
        m = R.DATA_ANY.search(fin)
        if m:
            out += data_iso(m)
    return sorted(set(out))


def mostra_data(iso):
    y, m, d = iso.split("-")
    return f"{int(d)}/{int(m)}/{y}"


def intervallo(date):
    if not date:
        return ""
    a, b = mostra_data(date[0]), mostra_data(date[-1])
    return a if a == b else f"{a} – {b}"


# ------------------------------------------------------------------ lettura di una pagina
def testo_con_link(n):
    """Come Node.text(), ma dopo ogni <a href=http...> aggiunge \x01url\x02 (poi estratto e tolto)."""
    out = []
    for c in n.children:
        if isinstance(c, str):
            out.append(c)
        else:
            if c.tag in dom.SKIP_TEXT:
                continue
            t = testo_con_link(c)
            if c.tag == "a" and (c.attrs.get("href") or "").startswith("http"):
                t += "\x01" + c.attrs["href"] + "\x02"
            if c.tag in ("p", "li", "div", "br", "h1", "h2", "h3", "h4", "tr", "ul", "ol", "table", "section", "details", "summary"):
                t = " " + t + " "
            out.append(t)
    return "".join(out)


def sezione(h):
    """Nodi che seguono l'intestazione h fino alla prossima intestazione dello stesso livello o superiore."""
    lvl = int(h.tag[1])
    sib = h.parent.children
    i = sib.index(h)
    out = []
    for c in sib[i + 1:]:
        if isinstance(c, dom.Node) and re.fullmatch(r"h[1-6]", c.tag) and int(c.tag[1]) <= lvl:
            break
        out.append(c)
    return out


def leggi_pagina(path):
    root = dom.parse(Path(path).read_text(encoding="utf-8", errors="replace"))
    body = next((n for n in root.iter() if n.tag == "body"), root)
    h1 = next((n for n in body.iter() if n.tag == "h1"), None)
    titolo = dom.clean(h1.text()) if h1 else ""
    # --- testo delle fonti: footer + sezioni "Fonti..." / "Licenze..."
    blocchi = []
    for n in body.iter():
        if n.tag == "footer":
            blocchi.append(taglia_coda(testo_con_link(n)))
    for n in body.iter():
        if n.tag in ("h2", "h3", "h4") and SEZ_FONTI.match(dom.clean(n.text())):
            if any(a.tag == "footer" for a in _antenati(n)):
                continue
            txt = dom.clean(n.text()) + ". " + " ".join(
                testo_con_link(c) if isinstance(c, dom.Node) else c for c in sezione(n) if not (isinstance(c, dom.Node) and c.tag in ("script", "style")))
            blocchi.append(taglia_coda(txt))
    # paragrafi che cominciano con "Fonte:" / "Licenze." fuori da footer e intestazioni (pagine scritte in modo diverso)
    if not blocchi:
        for n in body.iter():
            if n.tag in ("p", "div", "li") and re.match(r"^(?:Fonti?|Licenz\w+|Dati)\b[.:]", dom.clean(n.text())):
                blocchi.append(testo_con_link(n))
    # --- limiti
    limiti = estrai_limiti(body)
    # --- frasi del corpo (per "dati che non esistono")
    frasi = []
    for n in body.iter():
        if n.tag in ("p", "li") and not any(a.tag == "footer" for a in _antenati(n)):
            t = dom.clean(n.text())
            for f in re.split(r"(?<=[.;!?])\s+(?=[A-ZÀ-Ú«“])", t):
                if len(f) > 30:
                    frasi.append(norm(f))
    return {"titolo": titolo, "fonti_testo": "\n".join(blocchi), "limiti": limiti, "frasi": frasi}


def taglia_coda(t):
    """Toglie la coda "Programmi e note ... / Altre pagine ..." di un blocco."""
    m = ALTRI_MARCATORI.search(t)
    return t[:m.start()] if m and m.start() > 40 else t


def _antenati(n):
    p = n.parent
    while p is not None:
        yield p
        p = p.parent


def voci(nodi):
    """Elementi li (o, in mancanza, p) dentro una lista di nodi, come testi puliti."""
    li, p = [], []
    for c in nodi:
        if not isinstance(c, dom.Node):
            continue
        for n in [c] + list(c.iter()):
            if n.tag == "li":
                li.append(dom.clean(n.text()))
            elif n.tag == "p":
                p.append(dom.clean(n.text()))
    v = li or p
    out = []
    for t in v:
        t = norm(t)
        if len(t) < 25 or re.match(r"^(Programmi|Vedi anche|Altre pagine|File\b)", t):
            continue
        out.append(t)
    return out


def estrai_limiti(body):
    out = []
    for h in [n for n in body.iter() if n.tag in ("h2", "h3")]:
        tit = dom.clean(h.text())
        if R.LIMITI_TITOLO.search(tit) and not re.match(r"^Fonti e licenz", tit):
            out += voci(sezione(h))
    if not out:  # riquadri "Prima di leggere" / avvisi
        for n in body.iter():
            if n.tag in ("div", "p") and set(n.cls) & {"warm", "warn"}:
                out += voci([n]) or [norm(dom.clean(n.text()))]
    visti, res = set(), []
    for t in out:
        k = t[:80]
        if k not in visti:
            visti.add(k)
            res.append(t)
    return res


# ------------------------------------------------------------------ fonti
def trova_editori(testo):
    """Menzioni di editori nel testo: (inizio, fine, nome). Le sovrapposizioni si risolvono a favore dell'inizio più basso e del primo in elenco."""
    cand = []
    for ordine, (nome, _g, rx) in enumerate(R.EDITORI_RE):
        for m in rx.finditer(testo):
            cand.append((m.start(), ordine, m.end(), nome))
    cand.sort()
    out, fine = [], -1
    for s, _o, e, nome in cand:
        if s < fine:
            continue
        out.append((s, e, nome))
        fine = e
    return out


def prof_parentesi(testo, pos):
    pre = testo[:pos]
    return pre.count("(") - pre.count(")"), pre.count("«") - pre.count("»")


def unita(testo):
    """Frasi e sotto-frasi (separate da punto e da punto e virgola)."""
    parti = re.split(r"(?<=[.;])\s+(?=[A-ZÀ-Ú«“©(]|\d{4}\b)", testo)
    return [x for x in (p.strip() for p in parti) if x]


def inizi_in(u):
    """Nelle unità: [(posizione, [nomi], fine)] delle fonti che si aprono."""
    inizi = []
    for s, e, nome in trova_editori(u):
        pd, pq = prof_parentesi(u, s)
        if pd > 0 or pq > 0:
            continue
        if R.NON_APRE.search(u[max(0, s - 40):s]):
            continue
        e_dominio = bool(re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,3}(?:/\S*)?", u[s:e]))
        if inizi:
            ult_s, nomi, ult_e = inizi[-1]
            gap = u[ult_e:s]
            if e_dominio and len(gap) < 220:
                continue  # solo l'indirizzo del portale dentro una fonte già aperta
            if nome in nomi and len(gap) < 160:
                inizi[-1] = (ult_s, nomi, e)
                continue
            if R.CONGIUNZIONE.match(gap) and nome not in nomi:
                nomi.append(nome)
                inizi[-1] = (ult_s, nomi, e)
                continue
        inizi.append((s, [nome], e))
    return inizi


def divide_in_blocchi(testo):
    """Taglia il testo delle fonti in blocchi, uno per fonte.
    Ogni frase appartiene all'editore che nomina; se ne nomina più d'uno si taglia a ogni menzione;
    se non ne nomina nessuno continua la fonte precedente."""
    blocchi, pre = [], ""
    for u in unita(testo):
        ini = inizi_in(u)
        if not ini:
            if blocchi:
                blocchi[-1]["testo"] += " " + u
            else:
                pre += " " + u
            continue
        for i, (s, nomi, _e) in enumerate(ini):
            fine = ini[i + 1][0] if i + 1 < len(ini) else len(u)
            da = s
            if i == 0 and s > 0 and ":" in u[:s]:
                da = 0  # "Etichetta (ds1, ds2): Editore, licenza"
            blocchi.append({"nomi": list(nomi), "testo": u[da:fine]})
    return blocchi, pre


def scegli_licenza(testo):
    """Ritorna (tipo, versione, tutte_le_licenze_nel_testo)."""
    trovate = []
    for idx, (tipo, rx) in enumerate(R.LICENZE):
        for m in rx.finditer(testo):
            trovate.append((m.start(), idx, tipo, m))
    if not trovate:
        return None, "", []
    trovate.sort(key=lambda x: (x[0], x[1]))
    forti = [t for t in trovate if t[2] not in (R.LIC_TUTTI, R.LIC_CITAZIONE)]
    deboli = [t for t in trovate if t[2] in (R.LIC_TUTTI, R.LIC_CITAZIONE)]
    prima = forti[0] if forti else None
    if deboli and (not prima or (deboli[0][2] == R.LIC_TUTTI and deboli[0][0] < prima[0])):
        prima = deboli[0]
    if prima is None:
        prima = trovate[0]
    start, _, tipo, m = prima
    ver = ""
    if tipo in ("CC BY", "CC BY-SA", R.LIC_NC, "CC0", "IODL 2.0", "NLOD 2.0"):
        v = R.VERSIONE.search(testo[start:start + 90])
        if v:
            ver = v.group(1).replace(" ", "")
    altre = []
    for _s, _i, t, _m in trovate:
        if t != tipo and t not in altre:
            altre.append(t)
    return tipo, ver, altre


def nome_licenza(tipo, ver):
    if tipo == "CC BY" and ver:
        return f"CC BY {ver}"
    if tipo == "CC BY-SA":
        return f"CC BY-SA {ver or '4.0'}"
    if tipo == R.LIC_NC and ver:
        return "CC BY-NC"
    if tipo == "CC0":
        return "CC0 1.0"
    return tipo


def estrai_links(blocco):
    return [u for u in re.findall(r"\x01(http[^\x02]+)\x02", blocco)]


def pulisci(blocco):
    return norm(re.sub(r"\x01[^\x02]*\x02", "", blocco))


def estrai_fonti(slug, testo_fonti, correzioni):
    if not testo_fonti.strip():
        return [], "", None
    # taglia le code (Programmi e note, Altre pagine ...)
    t = testo_fonti
    pulito_tot = pulisci(t)
    blocchi, pre = divide_in_blocchi(t)
    data_pagina = date_di_scarico(pulisci(t))
    righe = []
    for b in blocchi:
        bt = pulisci(b["testo"])
        links = [u for u in estrai_links(b["testo"]) if "github.com" not in u and "openstreetmap.org/copyright" not in u]
        for nome in b["nomi"]:
            tipo, ver, altre = scegli_licenza(bt)
            default = False
            if tipo is None and nome in R.LICENZA_DEFAULT:
                tipo, ver, default = R.LICENZA_DEFAULT[nome], "", True
            if nome == "OpenStreetMap" and tipo in (None, R.LIC_CITAZIONE):
                tipo, ver, default = "ODbL", "", True
            ds = []
            for rx in (R.DS_ID, R.SOCRATA, R.EUROSTAT):
                for mm in rx.finditer(bt):
                    v = mm.group(0).strip()
                    if v.lower() not in [d.lower() for d in ds]:
                        ds.append(v)
            dom_ = []
            for mm in R.DOMINIO.finditer(bt):
                d = mm.group(0).rstrip(".")
                if d not in dom_ and "milano-in-dati" not in d and not d.lower().endswith(".csv") and not d.lower().endswith(".json"):
                    dom_.append(d)
            dd = date_di_scarico(bt)
            da_pagina = False
            if not dd and data_pagina:
                dd, da_pagina = data_pagina, True
            righe.append({
                "editore": nome, "gruppo": R.GRUPPO.get(nome, ""),
                "dataset": ds, "link": links[:3], "siti": dom_[:3],
                "licenza_tipo": tipo or R.LIC_NONDICH, "licenza": nome_licenza(tipo, ver) if tipo else R.LIC_NONDICH,
                "licenza_da_editore": default, "altre_licenze": altre,
                "date": dd, "data_da_pagina": da_pagina,
                "testo": tronca(bt, 420),
            })
    return righe, pulito_tot, data_pagina


def unisci_righe(righe):
    """Una riga per (editore, tipo di licenza). Un blocco senza licenza propria si unisce alla riga con licenza dello stesso editore."""
    con = {r["editore"] for r in righe if r["licenza_tipo"] != R.LIC_NONDICH}
    primo = {}
    for r in righe:
        if r["licenza_tipo"] != R.LIC_NONDICH:
            primo.setdefault(r["editore"], r["licenza_tipo"])
    out = {}
    for r in sorted(righe, key=lambda x: x["licenza_tipo"] == R.LIC_NONDICH):
        t = r["licenza_tipo"]
        if t == R.LIC_NONDICH and r["editore"] in con:
            t = primo[r["editore"]]
        k = (r["editore"], t)
        if k not in out:
            out[k] = dict(r, testi=[r["testo"]])
            out[k].pop("testo")
            continue
        o = out[k]
        for campo in ("dataset", "link", "siti", "date"):
            for v in r[campo]:
                if v not in o[campo]:
                    o[campo].append(v)
        o["date"].sort()
        o["testi"].append(r["testo"])
        if r["licenza"] != o["licenza"] and o["licenza"].startswith("CC BY") and r["licenza"].startswith("CC BY"):
            pass
        o["licenza_da_editore"] = o["licenza_da_editore"] and r["licenza_da_editore"]
        o["data_da_pagina"] = o["data_da_pagina"] and r["data_da_pagina"]
    return list(out.values())


# ------------------------------------------------------------------ NOTE.md
def note_per_pagina(radice):
    m = {}
    for d in radice.iterdir():
        if d.is_dir() and (d / "NOTE.md").exists():
            for s in ALIAS_NOTE.get(d.name, [d.name]):
                m[s] = d / "NOTE.md"
    return m


# ------------------------------------------------------------------ correzioni a mano
def _lic(s):
    """Da un testo di licenza scritto a mano ("CC BY 4.0", "Uso con citazione, non aperta") a (tipo, nome)."""
    noti = {R.LIC_TUTTI, R.LIC_CITAZIONE, R.LIC_ANMIG, R.LIC_NC, R.LIC_PD, R.LIC_NONDICH}
    if s in noti:
        return s, s
    tipo, ver, _ = scegli_licenza(s)
    if tipo is None:
        raise ValueError(f"licenza non riconosciuta in correzioni.json: {s!r}")
    return tipo, nome_licenza(tipo, ver)


def _applica(r, mod):
    if "lic" in mod:
        r["licenza_tipo"], r["licenza"] = _lic(mod["lic"])
        r["licenza_da_editore"] = bool(mod.get("da_editore", False))
    if "ds" in mod:
        r["dataset"] = list(mod["ds"])
    if "data" in mod:
        d = mod["data"]
        r["date"] = [d] if isinstance(d, str) else list(d)
        r["data_da_pagina"] = False
    if "link" in mod:
        r["link"] = list(mod["link"])
    if "nota" in mod:
        r["nota"] = mod["nota"]
    r["corretta"] = True


def applica_correzioni(slug, righe, corr):
    c = corr.get(slug) or {}
    if c.get("sostituisci"):
        righe = []
    for rm in c.get("togli", []):
        ed, _, tipo = rm.partition("|")
        righe = [r for r in righe if not (r["editore"] == ed and (not tipo or r["licenza_tipo"] == tipo))]
    for chiave, mod in (c.get("modifica") or {}).items():
        ed, _, tipo = chiave.partition("|")
        trovati = [r for r in righe if r["editore"] == ed and (not tipo or r["licenza_tipo"] == tipo)]
        if not trovati:
            raise ValueError(f"correzioni.json: {slug}: nessuna riga per {chiave!r}")
        for r in trovati:
            _applica(r, mod)
    for nuova in c.get("aggiungi", []):
        n = {"editore": nuova["editore"], "gruppo": R.GRUPPO.get(nuova["editore"], nuova.get("gruppo", "")), "dataset": [], "link": [], "siti": [],
             "licenza_tipo": R.LIC_NONDICH, "licenza": R.LIC_NONDICH, "licenza_da_editore": False, "altre_licenze": [],
             "date": [], "data_da_pagina": False, "testi": []}
        _applica(n, nuova)
        righe.append(n)
    return righe


# ------------------------------------------------------------------ programma principale
def etichette_menu(docs):
    try:
        t = (docs / "menu.js").read_text(encoding="utf-8")
        return {m.group(2): m.group(4) for m in re.finditer(r"path:\s*(['\"])(.+?)/?\1\s*,\s*label:\s*(['\"])(.*?)\3\s*\}", t)}
    except OSError:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", required=True, help="cartella milano-in-dati (assoluta)")
    ap.add_argument("--cache", help="cartella con l'HTML dopo JavaScript")
    ap.add_argument("--aggiorna", action="store_true")
    ap.add_argument("--senza-browser", action="store_true")
    ap.add_argument("--porta", type=int, default=8879)
    ap.add_argument("--debug", action="store_true", help="stampa le fonti trovate pagina per pagina")
    a = ap.parse_args()
    radice = Path(a.radice)
    docs = radice / "docs"
    cache = Path(a.cache) if a.cache else radice / "fonti" / "cache"
    slugs = sorted(p.name for p in docs.iterdir() if (p / "index.html").exists() and p.name not in PAGINE_FUORI)
    menu = etichette_menu(docs)
    if menu:  # solo le pagine elencate nel menu del sito
        slugs = [s for s in slugs if s in menu]
    corr = json.loads((Path(__file__).parent / "correzioni.json").read_text(encoding="utf-8")) if (Path(__file__).parent / "correzioni.json").exists() else {}
    corr_pag = {k: v for k, v in corr.items() if not k.startswith("_")}

    if a.senza_browser:
        files = {s: docs / s / "index.html" for s in slugs}
        ricaduti = list(slugs)
    else:
        import render
        files, ricaduti = render.render_all(docs, slugs, cache, port=a.porta, refresh=a.aggiorna)
    etich = etichette_menu(docs)
    note = note_per_pagina(radice)

    pagine, fonti_tutte, non_esiste = [], [], []
    senza_fonti = []
    for s in slugs:
        d = leggi_pagina(files[s])
        righe, _tot, data_pag = estrai_fonti(s, d["fonti_testo"], corr_pag)
        righe = unisci_righe(righe)
        righe = applica_correzioni(s, righe, corr_pag)
        if not righe:
            senza_fonti.append(s)
        limiti = d["limiti"]
        cp = corr_pag.get(s) or {}
        if cp.get("limiti"):
            limiti = cp["limiti"]
        pag = {
            "slug": s, "url": f"../{s}/", "etichetta": etich.get(s, d["titolo"] or s), "titolo": d["titolo"],
            "n_fonti": len(righe), "data_scarico": intervallo(data_pag or []),
            "limiti": [tronca(x, 300) for x in limiti], "n_limiti": len(limiti),
            "nota_fonti": cp.get("nota_fonti", ""),
        }
        pagine.append(pag)
        for r in righe:
            r["pagina"] = s
            fonti_tutte.append(r)
        for f in d["frasi"]:
            if R.NON_ESISTE.search(f):
                non_esiste.append({"pagina": s, "testo": tronca(f, 330)})
        if a.debug:
            print("=====", s, "| fonti:", len(righe), "| limiti:", len(limiti), "| date:", data_pag)
            for r in righe:
                print("   ", r["editore"], "|", r["licenza"], "(def)" if r["licenza_da_editore"] else "", "|", intervallo(r["date"]), "|", ",".join(r["dataset"])[:60])
    uscita = costruisci(pagine, fonti_tutte, non_esiste, corr, ricaduti, senza_fonti)
    out_dir = docs / "fonti" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fonti.json").write_text(json.dumps(uscita, ensure_ascii=False, indent=1), encoding="utf-8")
    scrivi_csv(out_dir / "fonti.csv", uscita)
    print(f"pagine {len(pagine)} | righe fonte {len(fonti_tutte)} | editori {len(uscita['editori'])} | senza fonti: {senza_fonti} | ricaduti sull'HTML grezzo: {ricaduti}")


def costruisci(pagine, fonti, non_esiste, corr, ricaduti, senza_fonti):
    for f in fonti:  # testo originale (breve) per controllare la riga
        f["testo"] = tronca(" … ".join(f.pop("testi", [])), 360)
        f.setdefault("nota", "")
    # editori
    ed = {}
    for f in fonti:
        e = ed.setdefault(f["editore"], {"nome": f["editore"], "gruppo": f["gruppo"], "pagine": set()})
        e["pagine"].add(f["pagina"])
    editori = sorted(({"nome": e["nome"], "gruppo": e["gruppo"], "n_pagine": len(e["pagine"]), "pagine": sorted(e["pagine"])} for e in ed.values()),
                     key=lambda x: (-x["n_pagine"], x["nome"]))
    # licenze: quota sulle coppie (pagina, editore, licenza)
    lic = {}
    for f in fonti:
        lic[f["licenza_tipo"]] = lic.get(f["licenza_tipo"], 0) + 1
    tot = sum(lic.values()) or 1
    licenze = sorted(({"tipo": k, "n": v, "quota": round(100 * v / tot, 1)} for k, v in lic.items()), key=lambda x: -x["n"])
    # dati che non esistono: tolgo i doppioni
    visti, ne = set(), []
    for x in non_esiste:
        k = re.sub(r"\W+", "", x["testo"].lower())[:90]
        if k not in visti:
            visti.add(k)
            ne.append(x)
    add = (corr.get("_non_esistono") or [])
    for x in add:
        k = re.sub(r"\W+", "", x["testo"].lower())[:90]
        if k not in visti:
            visti.add(k)
            ne.append(x)
    escl = [re.compile(p, re.I) for p in (corr.get("_non_esistono_escludi") or [])]
    ne = [x for x in ne if not any(rx.search(x["testo"]) for rx in escl)]
    return {
        "generato": dt.date.today().isoformat(),
        "conteggi": {
            "pagine": len(pagine), "righe_fonte": len(fonti), "editori": len(editori),
            "pagine_senza_fonti": senza_fonti, "dati_che_non_esistono": len(ne),
        },
        "pagine": pagine, "editori": editori, "licenze": licenze, "fonti": fonti, "non_esistono": ne,
    }


def scrivi_csv(path, u):
    pag = {p["slug"]: p for p in u["pagine"]}
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["pagina", "cartella_sul_sito", "editore", "gruppo", "dataset", "link", "licenza", "tipo_licenza", "licenza_non_scritta_nella_pagina",
                    "data_di_scarico", "limiti_principali"])
        for f in u["fonti"]:
            p = pag[f["pagina"]]
            w.writerow([p["etichetta"], f"{f['pagina']}/", f["editore"], f["gruppo"], " ".join(f["dataset"]),
                        " ".join(f["link"] or [("https://" + s) for s in f["siti"][:1]]), f["licenza"], f["licenza_tipo"],
                        "sì" if f["licenza_da_editore"] else "", intervallo(f["date"]), " | ".join(tronca(x, 170) for x in p["limiti"][:3])])


if __name__ == "__main__":
    main()
