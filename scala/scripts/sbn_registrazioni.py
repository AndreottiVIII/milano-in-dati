"""Registrazioni sonore alla Scala (catalogo SBN) -> sbn/sbn_registrazioni.csv  (FONTE DI CONTROLLO, non sono programmi di sala).
Legge sbn/_registrazioni_candidati.json (ricerche, scritto da sbn_registrazioni_cerca.py) e le schede complete in raw/sbn/full.
Tiene le registrazioni in cui la Scala compare come esecutore o come luogo; separa le DAL VIVO con data (note "Registrazione dal vivo, 4 febbraio 1954").
Uso (dalla cartella scala/):  python -I -X utf8 scripts/sbn_registrazioni.py"""
import sys, os, re, csv, json, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_nomi as N
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SBN = os.path.join(ROOT, "sbn")

RX_NUM = re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4}|\d{2})(?!\d)")
def date_reg(testi):
    """-> (iso, tipo) dalla prima data completa nelle note/titolo; tipo = 'giorno' o 'mese' o ''."""
    for t in testi:
        for d in N.date_in_testo(t):
            return d["iso"], "giorno"
        for m in RX_NUM.finditer(t):
            g, mo, a = int(m.group(1)), int(m.group(2)), m.group(3)
            a = int(a) if len(a) == 4 else (1900 + int(a) if int(a) > 30 else 2000 + int(a))
            if 1 <= g <= 31 and 1 <= mo <= 12 and 1900 < a < 2027:
                return "%04d-%02d-%02d" % (a, mo, g), "giorno"
    for t in testi:
        m = N.mese_in_testo(t)
        if m: return m, "mese"
    return "", ""

def main():
    cand = json.load(open(os.path.join(SBN, "_registrazioni_candidati.json"), encoding="utf8"))
    full = N.carica_full()
    rows = []
    for r in cand:
        bid = r["codiceIdentificativo"]; f = full.get(bid)
        if not f: continue
        note = f.get("note", []) or []
        titolo = f["titolo"]
        testi_note = [n for n in note if re.search(r"regist|dal vivo|live|esecuzione|concerto|rappresentazione|stagione", n, re.I)]
        live = bool(re.search(r"dal vivo|\blive\b|registrazione (di|della) (una )?(rappresentazione|serata|recita)|in diretta", " ".join(note) + " " + titolo, re.I))
        iso, tipo_d = date_reg(testi_note + [titolo])
        # persone con ruolo
        dirett, interp, comp = [], [], []
        for raw in f.get("nomi", []) or []:
            nome, chiave, ini = N.nome_pulito(raw)
            ruolo, dett, tag = N.ruolo_da_tag(raw)
            if N.ENTE.search(nome): continue
            if ruolo == "direttore": dirett.append(nome)
            elif ruolo == "interprete": interp.append(nome)
            elif ruolo == "compositore": comp.append(nome)
            elif not ruolo:
                # nome senza etichetta: ruolo dalla dichiarazione di responsabilita' del titolo
                for rr, s_, _c in [(a, b, "t") for a, b in N.dichiarazioni(titolo)]:
                    if N.parola_in(chiave, s_):
                        {"direttore": dirett, "interprete": interp, "compositore": comp}.get(rr, []).append(nome)
        if not dirett:
            for rr, s_ in N.dichiarazioni(titolo):
                if rr == "direttore": dirett += N.spezza_nomi(s_)
        for rr, s_ in N.dichiarazioni(titolo):
            if rr == "interprete": interp += N.spezza_nomi(s_)
        for m in re.finditer(r"(?:\[?(?:interpreti|cantanti)\]?\s*:?|;\s*con)\s+([^;]+)", titolo, re.I):
            interp += N.spezza_nomi(re.sub(r"\[[^\]]*\]", " ", m.group(1)))
        def senza_doppi(lst):
            visti, out = set(), []
            for n_ in lst:
                k = N.chiave_libera(n_)[0]
                if k and k not in visti: visti.add(k); out.append(n_)
            return out
        interp = senza_doppi([x for x in interp if x not in dirett]); dirett = senza_doppi(dirett)
        scala_esec = bool(re.search(r"(orchestra|coro|chorus|choeur|professori|solisti|filarmonica|corpo di ballo).{0,40}scala|scala.{0,30}(orchestra|chorus)", titolo + " " + " ".join(f.get("nomi", [])), re.I))
        scala_luogo = bool(re.search(r"teatro alla scala|la scala di milano|alla scala", titolo + " " + " ".join(note), re.I))
        if not (scala_esec or scala_luogo): continue
        m_anno = re.search(r"(19[0-9]\d|20[0-2]\d)", f.get("pubblicazione", "") or "")
        rows.append(dict(
            bid=bid, titolo=re.sub(r"\s+", " ", titolo)[:200], compositore="; ".join(dict.fromkeys(comp)), direttore="; ".join(dict.fromkeys(dirett)),
            interpreti="; ".join(dict.fromkeys(interp)), dal_vivo="si" if live else "no", data_registrazione=iso, data_tipo=tipo_d,
            nota_registrazione=" | ".join(testi_note)[:300], scala_come="esecutore" if scala_esec else "luogo",
            anno_pubblicazione=m_anno.group(1) if m_anno else "", etichetta=(f.get("pubblicazione") or "")[:80], url="https://opac.sbn.it/bid/" + N.norm(bid).upper().replace(" ", "") if False else "https://opac.sbn.it/bid/" + bid.replace("IT\\ICCU\\", "").replace("\\", ""),
            n_biblioteche=len(f.get("localizzazioni", []) or [])))
    with open(os.path.join(SBN, "sbn_registrazioni.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    c = collections.Counter((r["dal_vivo"], r["data_tipo"]) for r in rows)
    print("registrazioni con Scala:", len(rows), "su schede lette", sum(1 for r in cand if r["codiceIdentificativo"] in full), "su candidati", len(cand))
    print("dal vivo / tipo data:", dict(c))
    print("dal vivo con giorno:", sum(1 for r in rows if r["dal_vivo"] == "si" and r["data_tipo"] == "giorno"), "con direttore:", sum(1 for r in rows if r["direttore"]), "con interpreti:", sum(1 for r in rows if r["interpreti"]))
    # confronto con i programmi di sala: stessa data (data_iso) o stesso anno e stessa prima parola del titolo
    prog = list(csv.DictReader(open(os.path.join(SBN, "sbn_programmi.csv"), encoding="utf-8-sig")))
    per_data = collections.defaultdict(list)
    for p in prog:
        for d in (p.get("date_scala") or p.get("data_iso") or "").split(";"):
            if d: per_data[d].append(p)
    ok = 0
    for r in rows:
        if r["data_tipo"] == "giorno" and r["data_registrazione"] in per_data: ok += 1
    print("registrazioni con giorno che coincide con la data di un programma di sala:", ok)

if __name__ == "__main__":
    main()
