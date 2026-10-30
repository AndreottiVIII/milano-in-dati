"""Fase 2, passo 2: da pulito/beni_milano.csv costruisce la pagina docs/beni-culturali/ (index.html + data/*).

uso: python -I 07_pagina.py <beni_milano.csv> <cartella_docs_beni_culturali> <problemi.md>
Tutti i numeri della pagina escono da qui (nessun numero scritto a mano nell'HTML).
"""
import csv
import gzip
import html
import json
import os
import shutil
import sys
from collections import Counter, defaultdict

CLASSE_COD = {
    "HistoricOrArtisticProperty": "H", "ArchaeologicalProperty": "A", "ScientificOrTechnologicalHeritage": "S",
    "ArchitecturalOrLandscapeHeritage": "L", "DemoEthnoAnthropologicalHeritage": "D", "PhotographicHeritage": "P",
    "NumismaticProperty": "N", "NaturalHeritage": "T", "MusicHeritage": "M",
}
CLASSE_INV = {v: k for k, v in CLASSE_COD.items()}


def it(n):
    return f"{n:,}".replace(",", ".")


def pct(a, b, dec=1):
    return f"{100 * a / b:.{dec}f}".replace(".", ",") + "%"


def esc(s):
    return html.escape(str(s), quote=True)


def prima_data(dt):
    return dt.split(" | ")[0] if dt else ""


def main(src, outdir, problemi_md):
    with open(src, encoding="utf-8", newline="") as f:
        tutti = list(csv.DictReader(f))
    mi = [r for r in tutti if r["sede_milano"] == "1"]
    N = len(mi)
    os.makedirs(os.path.join(outdir, "data"), exist_ok=True)

    # ---------------------------------------------------------- completezza
    c_aut = sum(1 for r in mi if r["autori"])
    c_dat = sum(1 for r in mi if r["datazione_testo"])
    c_coord = sum(1 for r in mi if r["coord_in_comune"] == "1")
    c_coord_any = sum(1 for r in mi if r["lat"])
    c_ist = sum(1 for r in mi if r["istituzione"] != "non indicata")
    prec = Counter(r["ubicazione_precisione"] for r in mi)
    c_luogo = prec["sito"] + prec["indirizzo"]
    c_mat = sum(1 for r in mi if r["materia_tecnica"])
    c_sogg = sum(1 for r in mi if r["soggetto"])

    # ---------------------------------------------------------- liste
    per_tipo = Counter((r["tipo_scheda"], r["tipo_scheda_etichetta"]) for r in mi)
    per_ist = Counter(r["istituzione"] for r in mi)
    nonind = per_ist.pop("non indicata", 0)
    sec = Counter()
    for r in mi:
        if r["secolo"] == "":
            sec["nd"] += 1
        else:
            sec[int(r["secolo"])] += 1
    aut = Counter()
    for r in mi:
        for a in r["autori"].split(" | ") if r["autori"] else []:
            aut[a] += 1
    sogg = Counter()
    for r in mi:
        for s in r["soggetto"].split(" | ") if r["soggetto"] else []:
            sogg[s] += 1
    n_autori_distinti = len(aut)

    # ---------------------------------------------------------- oggetti.json (ricerca + popup mappa)
    voci = []
    for r in mi:
        cod = CLASSE_COD.get(r["classe_bene"], "?")
        id_ = r["iri"].split("/", 1)[1]
        voci.append([r["titolo"], r["autori"], prima_data(r["datazione_testo"]),
                     r["tipo_scheda"], cod + id_, r["soggetto"] if r["soggetto"] and r["soggetto"].lower() != r["titolo"].lower() else ""])
    oggetti = {"classi": CLASSE_INV, "voci": voci}
    p_ogg = os.path.join(outdir, "data", "oggetti.json")
    with open(p_ogg, "w", encoding="utf-8") as f:
        json.dump(oggetti, f, ensure_ascii=False, separators=(",", ":"))

    # ---------------------------------------------------------- punti.json (mappa)
    gruppi = defaultdict(list)
    for i, r in enumerate(mi):
        if r["coord_in_comune"] == "1":
            gruppi[(r["lat"], r["long"])].append(i)
    punti = []
    for (la, lo), idxs in sorted(gruppi.items(), key=lambda kv: -len(kv[1])):
        cn = Counter(mi[i]["istituzione"] for i in idxs if mi[i]["istituzione"] != "non indicata")
        cl = Counter(mi[i]["luogo_attuale"] for i in idxs if mi[i]["luogo_attuale"])
        nome = cn.most_common(1)[0][0] if cn else (cl.most_common(1)[0][0] if cl else "")
        ct = Counter(mi[i]["tipo_scheda"] for i in idxs)
        punti.append({"la": float(la), "lo": float(lo), "n": len(idxs), "nome": nome,
                      "tipi": dict(ct.most_common(4)), "ids": idxs})
    p_pun = os.path.join(outdir, "data", "punti.json")
    with open(p_pun, "w", encoding="utf-8") as f:
        json.dump(punti, f, ensure_ascii=False, separators=(",", ":"))

    # ---------------------------------------------------------- numeri.json (per verifica)
    numeri = {
        "schede_sede_milano": N, "schede_totali_file": len(tutti),
        "schede_solo_luogo_collegato": len(tutti) - N,
        "autore_presente": c_aut, "datazione_presente": c_dat, "coordinate_in_comune": c_coord,
        "coordinate_presenti_totale": c_coord_any, "istituzione_nominata": c_ist,
        "luogo_preciso_sito_o_indirizzo": c_luogo, "luogo_solo_comune": prec["solo_comune"],
        "luogo_nessuno": prec["nessuna"], "materia_presente": c_mat, "soggetto_presente": c_sogg,
        "per_tipo": {k[0]: v for k, v in per_tipo.items()}, "istituzione_non_indicata": nonind,
        "punti_mappa": len(punti), "autori_distinti": n_autori_distinti,
        "per_secolo": {str(k): v for k, v in sec.items()},
    }
    json.dump(numeri, open(os.path.join(outdir, "data", "numeri.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # csv derivato (tutte le righe) compresso + problemi.md
    with open(src, "rb") as fi, gzip.open(os.path.join(outdir, "data", "beni_milano.csv.gz"), "wb", compresslevel=9) as fo:
        shutil.copyfileobj(fi, fo)
    shutil.copyfile(problemi_md, os.path.join(outdir, "data", "problemi.md"))

    # ---------------------------------------------------------- HTML
    def righe_tipo():
        out = []
        for (cod, et), n in per_tipo.most_common():
            out.append(f"<tr><td><b>{esc(cod)}</b></td><td>{esc(et)}</td><td class='r'>{it(n)}</td><td class='r'>{pct(n, N)}</td>"
                       f"<td class='bar'><i style='width:{100 * n / per_tipo.most_common(1)[0][1]:.1f}%'></i></td></tr>")
        return "\n".join(out)

    def righe_ist():
        top = per_ist.most_common(20)
        mx = max(top[0][1], nonind)  # stessa scala per tutte le barre, compresa "non indicata"
        out = [f"<tr class='mut'><td>non indicata nel catalogo</td><td class='r'>{it(nonind)}</td><td class='r'>{pct(nonind, N)}</td><td class='bar'><i class='g' style='width:{100 * nonind / mx:.1f}%'></i></td></tr>"]
        for nome, n in top:
            out.append(f"<tr><td>{esc(nome)}</td><td class='r'>{it(n)}</td><td class='r'>{pct(n, N)}</td><td class='bar'><i style='width:{100 * n / mx:.1f}%'></i></td></tr>")
        return "\n".join(out)

    ROM = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII",
           14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX", 21: "XXI"}

    def righe_secolo():
        a_c = sum(v for k, v in sec.items() if k != "nd" and k < 0)
        voci_s = [("a.C. (tutti i secoli prima di Cristo)", a_c)]
        for c in range(1, 22):
            voci_s.append((f"{ROM[c]} secolo ({(c - 1) * 100 + 1}&ndash;{c * 100})", sec.get(c, 0)))
        mx = max(v for _, v in voci_s)
        out = []
        for et, n in voci_s:
            out.append(f"<tr><td>{et}</td><td class='r'>{it(n)}</td><td class='r'>{pct(n, N)}</td><td class='bar'><i style='width:{100 * n / mx:.1f}%'></i></td></tr>")
        out.append(f"<tr class='mut'><td>data mancante o non interpretabile</td><td class='r'>{it(sec['nd'])}</td><td class='r'>{pct(sec['nd'], N)}</td><td class='bar'></td></tr>")
        return "\n".join(out)

    def righe_cls(counter, k):
        top = counter.most_common(k)
        mx = top[0][1]
        return "\n".join(f"<tr><td>{esc(n)}</td><td class='r'>{it(v)}</td><td class='bar'><i style='width:{100 * v / mx:.1f}%'></i></td></tr>" for n, v in top)

    n_arte = sum(v for (cod, _), v in per_tipo.items() if cod in ("OA", "D", "S", "OAC"))
    n_oa = per_tipo[("OA", [e for (c, e) in per_tipo if c == "OA"][0])]
    n_ign = 100 - 100 * c_aut / N
    kb_ogg = os.path.getsize(p_ogg) / 1024
    kb_pun = os.path.getsize(p_pun) / 1024

    prob = json.load(open(os.path.join(os.path.dirname(os.path.abspath(src)), "problemi_conteggi.json"), encoding="utf-8"))
    generici = sum(1 for r in mi if r["titolo"].lower() == r["tipo_oggetto"].lower())
    pagina = TEMPLATE
    sost = {
        "@@N@@": it(N), "@@NTOT@@": it(len(tutti)), "@@NSOLO@@": it(len(tutti) - N),
        "@@AUT@@": pct(c_aut, N), "@@AUTMANCA@@": pct(N - c_aut, N),
        "@@LUOGO@@": pct(c_luogo, N), "@@LUOGOMANCA@@": pct(N - c_luogo, N), "@@SOLOCOM@@": pct(prec["solo_comune"], N),
        "@@NESSUNA@@": pct(prec["nessuna"], N),
        "@@COORD@@": pct(c_coord, N), "@@COORDMANCA@@": pct(N - c_coord, N), "@@NCOORD@@": it(c_coord),
        "@@IST@@": pct(c_ist, N), "@@ISTMANCA@@": pct(N - c_ist, N), "@@DAT@@": pct(c_dat, N), "@@DATMANCA@@": pct(N - c_dat, N),
        "@@NARTE@@": it(n_arte), "@@NOA@@": it(n_oa), "@@NPUNTI@@": it(len(punti)), "@@NAUTORI@@": it(n_autori_distinti),
        "@@NNONIND@@": it(nonind), "@@MAX1@@": it(punti[0]["n"]), "@@NOME1@@": esc(punti[0]["nome"]),
        "@@TIPI@@": righe_tipo(), "@@IST_ROWS@@": righe_ist(), "@@SEC_ROWS@@": righe_secolo(),
        "@@AUT_ROWS@@": righe_cls(aut, 30), "@@SOGG_ROWS@@": righe_cls(sogg, 30),
        "@@KB@@": f"{(kb_ogg + kb_pun) / 1024:.1f}".replace(".", ","),
        "@@NTIPI@@": str(len(per_tipo)),
        "@@AUTN@@": it(c_aut), "@@DATN@@": it(c_dat), "@@ISTN@@": it(c_ist), "@@LUOGON@@": it(c_luogo),
        "@@SOLOCOMN@@": it(prec["solo_comune"]), "@@NESSUNAN@@": it(prec["nessuna"]),
        "@@NBRERA@@": it(sum(1 for r in mi if r["istituzione_iri"].endswith("DBunicoCG106788"))),
        "@@NGRUPPI@@": it(prob["conteggi"]["schede_quasi_identiche_gruppi"]),
        "@@GENERICI@@": pct(generici, N), "@@NCODICI@@": it(sum(1 for r in mi if r["istituzione_iri"])),
        "__TIPI__": json.dumps({k[0]: k[1] for k in per_tipo}, ensure_ascii=False),
    }
    for k, v in sost.items():
        pagina = pagina.replace(k, v)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)
    print(json.dumps(numeri, ensure_ascii=False, indent=1))
    print("oggetti.json KB", round(kb_ogg), "punti.json KB", round(kb_pun))


TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pagina_template.html"), encoding="utf-8").read()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
