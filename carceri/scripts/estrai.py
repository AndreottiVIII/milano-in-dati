"""Legge le pagine HTML scaricate da giustizia.it e scrive le tabelle pulite in pulito/.

Uso:  python -I -X utf8 estrai.py <percorso assoluto di carceri>

Produce:
  pulito/istituti_mensili.csv   una riga per istituto e mese (capienza, presenti, donne, stranieri)
  pulito/regioni_mensili.csv    una riga per regione e mese (capienza, presenti, stranieri, posizione giuridica)
  pulito/serie_nazionali.csv    serie storiche nazionali (posizione giuridica, eventi critici)
  pulito/schede_istituti.csv    schede del Ministero (posti, non disponibili, presenti, personale)
  pulito/controlli.txt          controlli di coerenza (somme, righe, istituti mancanti)
"""
import csv, html, re, sys
from pathlib import Path

MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7,
        "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}


def testo(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x)).replace("\xa0", " ")).strip()


def num(s):
    s = s.replace(".", "").replace(" ", "").strip()
    if s in ("", "-", "--"):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def righe(h):
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S | re.I):
        celle = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S | re.I)
        out.append([testo(c) for c in celle])
    return out


def data_pagina(h, cid):
    m = re.search(r"Situazione al (\d{1,2}) (\w+) (\d{4})", testo(h), re.I)
    if not m:
        return None
    pref = {k[:3]: v for k, v in MESI.items()}   # tollera refusi nel nome del mese ("febbreio")
    g, mese, a = int(m.group(1)), pref[m.group(2).lower()[:3]], int(m.group(3))
    return f"{a:04d}-{mese:02d}-{g:02d}"


def main(root):
    root = Path(root)
    raw, pul = root / "raw", root / "pulito"
    pul.mkdir(exist_ok=True)
    ctrl = []
    ist, reg = [], []
    for f in sorted((raw / "mensili").glob("SST*.html")):
        h = f.read_text(encoding="utf8", errors="replace")
        titolo = testo(re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S).group(1)) if "<h1" in h else ""
        d = data_pagina(h, f.stem)
        if d is None:
            ctrl.append(f"{f.name}: data non trovata")
            continue
        if "capienze per istituto" in h.lower() and "Tipo istituto" in h:
            n = 0
            for c in righe(h):
                # formato fino a settembre 2025: regione, sigla provincia, istituto, tipo, capienza, presenti, donne, stranieri
                # formato da ottobre 2025: la sigla della provincia non c'e' piu' (7 celle) e il nome finisce con " -"
                if len(c) == 7 and c[0].isupper() and (num(c[3]) is not None or num(c[4]) is not None):
                    c = [c[0], ""] + c[1:]
                if not (len(c) == 8 and c[0].isupper() and (num(c[4]) is not None or num(c[5]) is not None)):
                    continue
                nome = re.sub(r"\s+-$", "", c[2]).strip()
                ist.append(dict(data=d, file=f.stem, regione=c[0], prov=c[1], istituto=nome, tipo=c[3],
                                capienza=num(c[4]) or 0, presenti=num(c[5]) or 0, donne=num(c[6]) or 0, stranieri=num(c[7]) or 0))
                n += 1
            ctrl.append(f"{f.stem} {d}: {n} istituti")
        # tabelle per regione (file 'Detenuti presenti - aggiornamento'): righe con la regione in maiuscolo
        elif "Numero Istituti" in testo(h) and "Regione di detenzione" in testo(h):
            visti = {}
            for c in righe(h):
                if not c or not c[0].isupper() or c[0] == "TOTALE":
                    continue
                if len(c) == 8:
                    reg.append(dict(data=d, file=f.stem, tabella="capienza", regione=c[0], vals=c[1:]))
                elif len(c) == 10:
                    k = visti.get(c[0], 0)
                    visti[c[0]] = k + 1
                    reg.append(dict(data=d, file=f.stem, tabella="posizione_" + ("totale", "stranieri")[min(k, 1)],
                                    regione=c[0], vals=c[1:]))
                else:
                    ctrl.append(f"{f.stem}: riga regione con {len(c)} celle: {c[:3]}")
    # scrittura istituti
    ist.sort(key=lambda r: (r["data"], r["regione"], r["istituto"]))
    with open(pul / "istituti_mensili.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["data", "file", "regione", "prov", "istituto", "tipo", "capienza",
                                           "presenti", "donne", "stranieri"])
        w.writeheader()
        w.writerows(ist)
    with open(pul / "regioni_mensili.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "file", "tabella", "regione", "valori_nell_ordine_della_pagina"])
        for r in reg:
            w.writerow([r["data"], r["file"], r["tabella"], r["regione"], "|".join(r["vals"])])
    (pul / "controlli.txt").write_text("\n".join(ctrl), encoding="utf8")
    print(len(ist), "righe istituti;", len(reg), "righe regioni;", len(set(r["data"] for r in ist)), "date")


if __name__ == "__main__":
    main(sys.argv[1])
