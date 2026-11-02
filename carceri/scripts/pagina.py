"""Costruisce docs/carceri/data/ (file scaricabili + riepilogo.json letto dalla pagina).

Uso:  python -I -X utf8 pagina.py <percorso assoluto di carceri> <percorso assoluto di milano-in-dati>
Rilanciabile. Prima vanno eseguiti scarica.py, estrai.py, ipm.py (solo per i testi dei PDF), analisi.py.
La pagina docs/carceri/index.html e' scritta a mano e legge data/riepilogo.json.
"""
import csv, json, shutil, sys
from datetime import date
from pathlib import Path


def pct(a, b, d=1):
    return round(100.0 * a / b, d)


def main(root, base):
    root, base = Path(root), Path(base)
    pul = root / "pulito"
    out = base / "docs" / "carceri" / "data"
    out.mkdir(parents=True, exist_ok=True)
    R = json.loads((pul / "riepilogo.json").read_text(encoding="utf8"))
    NOME = {"SV": "Milano San Vittore", "BO": "Milano Bollate", "OP": "Milano Opera", "MZ": "Monza"}

    # ---------- file scaricabili ----------
    with open(out / "istituti_lombardia_milano_mensile.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "istituto", "capienza_regolamentare", "detenuti_presenti", "di_cui_donne",
                    "di_cui_stranieri_categoria_ministero", "presenti_ogni_100_posti"])
        for k in ("SV", "BO", "OP", "MZ"):
            for d, c, p, dn, s in R["serie"][k]:
                w.writerow([d, NOME[k], c, p, dn, s, pct(p, c)])
    with open(out / "italia_lombardia_mensile.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "area", "capienza_regolamentare", "detenuti_presenti", "di_cui_donne",
                    "di_cui_stranieri_categoria_ministero", "presenti_ogni_100_posti"])
        for lab, key in (("Italia (somma degli istituti)", "italia"), ("Lombardia (somma degli istituti)", "lombardia")):
            for d, c, p, dn, s in R[key]:
                w.writerow([d, lab, c, p, dn, s, pct(p, c)])
    with open(out / "classifica_istituti_ultimo_mese.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "istituto", "regione", "tipo", "capienza_regolamentare", "detenuti_presenti", "presenti_ogni_100_posti"])
        for c in R["classifica"]:
            w.writerow([R["ultima"], c["istituto"], c["regione"], c["tipo"], c["capienza"], c["presenti"], c["occ"]])
    for nome in ("posizione_giuridica_mensile.csv", "schede_milano.csv", "serie_nazionali_posizione_giuridica.csv",
                 "serie_nazionali_eventi_critici.csv", "ipm_milano_media_giornaliera.csv", "controlli.txt"):
        shutil.copy(pul / nome, out / nome)

    # ---------- numeri derivati, con l'origine ----------
    S = {s["scheda"]: s for s in R["schede"]}
    sv_m, sv_f, bo, op = S["MII158895"], S["MII178501"], S["MII172344"], S["MII179237"]
    ult = R["ultima"]
    ultimo = {k: R["serie"][k][-1] for k in R["serie"]}
    assert ultimo["SV"][1] == sv_m["posti_regolamentari"] + sv_f["posti_regolamentari"], "capienza San Vittore: tabella != schede"
    sv = dict(posti=sv_m["posti_regolamentari"] + sv_f["posti_regolamentari"], non_disp=sv_m["posti_non_disponibili"] + sv_f["posti_non_disponibili"],
              det=sv_m["detenuti"] + sv_f["detenuti"])
    sch = {
        "SV": dict(sv, nome="San Vittore", polizia_eff=sv_m["polizia_effettivi"], polizia_prev=sv_m["polizia_previsti"],
                   edu_eff=sv_m["educatori_effettivi"], edu_prev=sv_m["educatori_previsti"], det_maschile=sv_m["detenuti"],
                   stanze=sv_m["stanze"], stanze_nd=sv_m["stanze_non_disponibili"]),
        "BO": dict(posti=bo["posti_regolamentari"], non_disp=bo["posti_non_disponibili"], det=bo["detenuti"], nome="Bollate",
                   polizia_eff=bo["polizia_effettivi"], polizia_prev=bo["polizia_previsti"], edu_eff=bo["educatori_effettivi"],
                   edu_prev=bo["educatori_previsti"], det_maschile=bo["detenuti"], stanze=bo["stanze"], stanze_nd=bo["stanze_non_disponibili"]),
        "OP": dict(posti=op["posti_regolamentari"], non_disp=op["posti_non_disponibili"], det=op["detenuti"], nome="Opera",
                   polizia_eff=op["polizia_effettivi"], polizia_prev=op["polizia_previsti"], edu_eff=op["educatori_effettivi"],
                   edu_prev=op["educatori_previsti"], det_maschile=op["detenuti"], stanze=op["stanze"], stanze_nd=op["stanze_non_disponibili"]),
    }
    for k, v in sch.items():
        v["occ_regolamentare"] = pct(v["det"], v["posti"])
        v["occ_disponibili"] = pct(v["det"], v["posti"] - v["non_disp"])
        v["det_per_agente"] = round(v["det_maschile"] / v["polizia_eff"], 2)
        v["polizia_copertura"] = pct(v["polizia_eff"], v["polizia_prev"], 0)
        v["edu_copertura"] = pct(v["edu_eff"], v["edu_prev"], 0)
    # variazioni dall'inizio della serie
    var = {}
    for k in ("SV", "BO", "OP", "MZ"):
        a, b = R["serie"][k][0], R["serie"][k][-1]
        pic = max(R["serie"][k], key=lambda x: x[2] / x[1])
        mn = min(R["serie"][k], key=lambda x: x[2] / x[1])
        var[k] = dict(nome=NOME[k], inizio=a, fine=b, occ_inizio=pct(a[2], a[1], 0), occ_fine=pct(b[2], b[1], 0),
                      var_detenuti_pct=pct(b[2] - a[2], a[2]), picco=[pic[0], pct(pic[2], pic[1], 0)], minimo=[mn[0], pct(mn[2], mn[1], 0)],
                      stranieri_pct_fine=pct(b[4], b[2]), stranieri_pct_inizio=pct(a[4], a[2]), donne_fine=b[3], donne_inizio=a[3])
    # posizione giuridica: ultima e prima rilevazione
    p0, p1 = R["posiz"][0], R["posiz"][-1]
    pg = dict(prima=p0[0], ultima=p1[0],
              lom_attesa_pct=[pct(p0[1], p0[4]), pct(p1[1], p1[4])], it_attesa_pct=[pct(p0[5], p0[8]), pct(p1[5], p1[8])],
              lom_nondef_pct=[pct(p0[1] + p0[2], p0[4]), pct(p1[1] + p1[2], p1[4])],
              it_nondef_pct=[pct(p0[5] + p0[6], p0[8]), pct(p1[5] + p1[6], p1[8])],
              lom_attesa=p1[1], lom_nondef_tot=p1[2], lom_def=p1[3], lom_tot=p1[4], it_attesa=p1[5], it_nondef=p1[6], it_def=p1[7], it_tot=p1[8])
    # IPM
    ipm = [dict(anno=x["anno"], milano=x["milano"], nazionale=x["nazionale"], pag=x["pag_mi"], file=x["file"], pdf_id=x["pdf_id"]) for x in R["ipm"]]
    ev25 = [e for e in R["eventi"] if e[0] == 2025][0]
    numeri = dict(
        ultima=ult, schede_il="2026-11-01", personale_il="2026-09-30", scaricato_il=date.today().isoformat(),
        rank=R["rank"], sopra100=R["sopra100"], n_classifica=R["n_classifica"], mediana_occ=R["mediana_occ"],
        italia_occ=[pct(R["italia"][0][2], R["italia"][0][1]), pct(R["italia"][-1][2], R["italia"][-1][1])],
        lombardia_occ=[pct(R["lombardia"][0][2], R["lombardia"][0][1]), pct(R["lombardia"][-1][2], R["lombardia"][-1][1])],
        italia_stranieri_pct=pct(R["italia"][-1][4], R["italia"][-1][2]), lombardia_stranieri_pct=pct(R["lombardia"][-1][4], R["lombardia"][-1][2]),
        italia_donne_pct=pct(R["italia"][-1][3], R["italia"][-1][2]),
        sch=sch, var=var, pg=pg, ipm=ipm,
        suicidi_2025=dict(anno=2025, valore=ev25[3], per_10000=ev25[4], presenza_media=ev25[1]),
    )
    # ---------- riepilogo per la pagina ----------
    page = dict(
        date=R["date"], serie=R["serie"], italia=R["italia"], lombardia=R["lombardia"], distr=R["distr"], posiz=R["posiz"],
        posiz_annuale=R["posiz_annuale"], eventi=R["eventi"], numeri=numeri, classifica=R["classifica"],
        grandi=sorted([c for c in R["classifica"] if c["capienza"] >= 500], key=lambda c: -c["presenti"])[:14],
        origine=dict(
            serie="Ministero della giustizia, Dipartimento dell'amministrazione penitenziaria, statistiche 'Detenuti italiani e stranieri presenti e capienze per istituto' (una pagina per mese, gen 2019 - set 2026)",
            posiz="stesse statistiche, pagina mensile 'Detenuti presenti' (tabella 'per posizione giuridica', per regione; Italia = somma delle regioni)",
            schede="Ministero della giustizia, schede degli istituti (dettaglio_scheda.page), lette il " + date.today().isoformat(),
            ipm="Dipartimento per la giustizia minorile e di comunita', 'Istituti penali per i minorenni', PDF annuali (pagina indicata)",
            eventi="Ministero della giustizia, 'Eventi critici negli istituti penitenziari - Anni 1992-2025'"))
    (out / "riepilogo.json").write_text(json.dumps(page, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
    print("scritti:", sorted(p.name for p in out.iterdir()))
    print(json.dumps(numeri["sch"], ensure_ascii=False)[:900])
    print(json.dumps(numeri["pg"], ensure_ascii=False))
    for k, v in var.items():
        print(k, v)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
