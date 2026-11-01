"""Pagina "Appalti pubblici": prepara i file di dati in docs/appalti/data/.

Legge SOLO (in sola lettura) i file 60_*.csv del "Focus Milano" del progetto
appalti-anac e scrive in docs/appalti/data/ i csv e il riepilogo.json che usa la
pagina docs/appalti/index.html. Non scrive nulla nella cartella di appalti-anac.

Uso (percorsi assoluti):
  python -I -X utf8 pagina.py <appalti-anac\\risultati> <milano-in-dati\\docs\\appalti\\data>

Si puo' rilanciare quando i file 60_* cambiano. Il programma si ferma con un
errore se un numero chiave non coincide con quello scritto nel referto
(risultati/60_focus_milano.md): i numeri scritti a mano nel testo della pagina
sono quelli controllati qui sotto (funzione controlli()).

Licenza dei file prodotti: come la fonte, CC BY-SA 4.0 (dati ANAC, dati.anticorruzione.it).
Nei file non ci sono nomi di persone ne' di imprese: solo gruppi di enti, e due enti
pubblici (ARIA e Comune di Milano).
"""
import csv
import json
import os
import sys

# ---------------------------------------------------------------- utilita'

CITTA_ORDINE = ["MILANO", "ROMA", "TORINO", "NAPOLI", "BOLOGNA", "GENOVA", "FIRENZE", "PALERMO", "BARI"]
CF_ARIA = "05017630152"
CF_COMUNE = "01199250158"
RIF = "referto 60_focus_milano.md"


def pulisci(s):
    """Apostrofi al posto degli accenti (come nei csv di partenza) -> accenti veri."""
    for a, b in (("Citta'", "Città"), ("citta'", "città"), ("societa'", "società"), ("Societa'", "Società"),
                 ("Sanita'", "Sanità"), ("Universita'", "Università")):
        s = s.replace(a, b)
    return s


def leggi(cartella, nome):
    p = os.path.join(cartella, nome)
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def num(x):
    if x is None or x == "":
        return None
    return float(x)


def intero(x):
    v = num(x)
    return None if v is None else int(round(v))


def r6(x):
    return None if x is None else round(x, 6)


def scrivi_csv(cartella, nome, colonne, righe):
    with open(os.path.join(cartella, nome), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(colonne)
        for r in righe:
            w.writerow(["" if r[c] is None else r[c] for c in colonne])


def it(x, d=1):
    """Formato italiano con virgola."""
    return f"{x:.{d}f}".replace(".", ",")


def p(x, d=1):
    return it(x * 100, d)


def migliaia(n):
    return f"{int(round(n)):,}".replace(",", ".")


# ---------------------------------------------------------------- estrazioni

def perimetro(R):
    tot = leggi(R, "60_s0_totale.csv")[0]
    gr = leggi(R, "60_s0_gruppo.csv")
    top = {r["cf"]: r for r in leggi(R, "60_top30_enti_per_importo.csv")}
    aria = top[CF_ARIA]
    imp_citta = num(tot["imp_milano_citta"])
    totali = []
    for amb, k in (("Italia", "italia"), ("Lombardia", "lombardia"), ("Area metropolitana di Milano", "area_metropolitana"),
                   ("Milano città", "milano_citta")):
        nome = {"italia": "n_italia", "lombardia": "n_lombardia", "area_metropolitana": "n_area_metropolitana",
                "milano_citta": "n_milano_citta"}[k]
        imp = {"italia": "imp_italia", "lombardia": "imp_lombardia", "area_metropolitana": "imp_area_metropolitana",
               "milano_citta": "imp_milano_citta"}[k]
        n, i = num(tot[nome]), num(tot[imp])
        totali.append({
            "ambito": amb, "procedure": int(n), "importo_euro": int(round(i)),
            "quota_procedure_italia": r6(n / num(tot["n_italia"])),
            "quota_importo_italia": r6(i / num(tot["imp_italia"])),
            "quota_procedure_lombardia": r6(n / num(tot["n_lombardia"])),
        })
    gruppi = []
    for r in gr:
        gruppi.append({
            "gruppo": pulisci(r["gruppo"]), "enti_con_procedure": int(r["n_enti"]), "procedure": int(r["n"]),
            "importo_euro": int(round(num(r["imp"]))), "quota_procedure_area": r6(num(r["quota_n_area"])),
            "quota_importo_area": r6(num(r["quota_imp_area"])),
        })
    a = {"procedure": int(aria["n"]), "importo_euro": int(round(num(aria["imp"]))),
         "quota_importo_milano_citta": r6(num(aria["imp"]) / imp_citta)}
    senza100 = {"milano_citta_euro": int(round(num(tot["imp_senza_oltre_100mln_citta"]))),
                "italia_euro": int(round(num(tot["imp_senza_oltre_100mln_italia"]))),
                "quota": r6(num(tot["imp_senza_oltre_100mln_citta"]) / num(tot["imp_senza_oltre_100mln_italia"]))}
    mil = [r for r in leggi(R, "60_s0_citta.csv") if r["citta"] == "MILANO" and r["perimetro"] == "tutti"][0]
    return {"totali": totali, "gruppi": gruppi, "aria": a, "senza_oltre_100mln": senza100,
            "enti_milano_citta_con_procedure": int(mil["n_enti"])}


def soglia(R):
    cit = leggi(R, "60_s1_citta.csv")
    naz = leggi(R, "60_s1_nazionale.csv")[0]
    dim = leggi(R, "60_s1_dimensioni.csv")
    gr = leggi(R, "60_s1_gruppi.csv")
    righe = []
    for r in cit:
        if r["perimetro"] not in ("locale", "tutti"):
            continue
        righe.append({
            "citta": r["citta"].capitalize(),
            "ambito": "enti locali" if r["perimetro"] == "locale" else "tutti gli enti",
            "affidamenti_vicini_soglia": int(r["n_larga"]), "nell_ultimo_5pct": int(r["n_stretta"]),
            "quota": r6(num(r["quota"])), "quota_attesa": r6(num(r["quota_attesa"])),
            "rapporto": r6(num(r["rapporto"])),
            "rapporto_intervallo_basso": r6(num(r["rapporto_ic95_basso_enti"])),
            "rapporto_intervallo_alto": r6(num(r["rapporto_ic95_alto_enti"])),
            "esatti_a_un_euro": int(r["n_esatto_meno1"]) + int(r["n_esatto_meno001"]),
        })
    ordine = {c.capitalize(): i for i, c in enumerate(CITTA_ORDINE)}
    righe.sort(key=lambda x: (x["ambito"] != "enti locali", ordine[x["citta"]]))
    italia = {
        "affidamenti_vicini_soglia": int(naz["n_larga"]), "nell_ultimo_5pct": int(naz["n_stretta"]),
        "quota": r6(num(naz["quota"])), "esatti_a_un_euro": int(naz["n_esatto_meno1"]) + int(naz["n_esatto_meno001"]),
        "quota_esatti": r6((int(naz["n_esatto_meno1"]) + int(naz["n_esatto_meno001"])) / int(naz["n_stretta"])),
    }
    etich = {"1": "fino al 16/7/2020 (soglia 40.000 euro)", "2": "dal 17/7/2020 al 31/5/2021 (75.000)",
             "3": "dal 1/6/2021 al 30/6/2023 (139.000)", "4": "dal 1/7/2023 (140.000)"}
    periodi = []
    for k in "1234":
        m = [r for r in dim if r["dimensione"] == "per" and r["valore"] == k and r["ambito"].startswith("Milano")][0]
        i = [r for r in dim if r["dimensione"] == "per" and r["valore"] == k and r["ambito"] == "Italia"][0]
        periodi.append({"periodo": etich[k], "quota_milano": r6(num(m["quota"])), "quota_attesa_milano": r6(num(m["quota_attesa"])),
                        "rapporto_milano": r6(num(m["rapporto"])), "quota_italia": r6(num(i["quota"]))})
    # tutti gli enti di Milano: soli numeri per la riga "esatti a un euro"
    mt = [r for r in cit if r["citta"] == "MILANO" and r["perimetro"] == "tutti"][0]
    esatti_milano = {"n": int(mt["n_esatto_meno1"]) + int(mt["n_esatto_meno001"]), "su": int(mt["n_stretta"]),
                     "quota": r6(num(mt["quota_esatti"]))}
    gruppi = []
    for r in gr:
        gruppi.append({
            "gruppo": pulisci(r["gruppo"]), "enti": int(r["n_enti"]), "affidamenti_vicini_soglia": int(r["n_larga"]),
            "nell_ultimo_5pct": int(r["n_stretta"]), "quota": r6(num(r["quota"])), "quota_attesa": r6(num(r["quota_attesa"])),
            "rapporto": r6(num(r["rapporto"])),
            "rapporto_intervallo_basso": r6(num(r["rapporto_ic95_basso_enti"])),
            "rapporto_intervallo_alto": r6(num(r["rapporto_ic95_alto_enti"])),
        })
    t5 = leggi(R, "60_s1_milano_senza_top5.csv")[0]
    ea = leggi(R, "60_s1_enti_area.csv")
    spiccano = {
        "enti_con_almeno_100": sum(1 for r in ea if num(r["n_larga"]) >= 100),
        "rapporto_almeno_1_5_e_q_sotto_0_01": sum(1 for r in ea if num(r["rapporto"]) >= 1.5 and num(r["q_value_bh"]) < 0.01),
        "rapporto_almeno_2_e_q_sotto_0_01": sum(1 for r in ea if num(r["rapporto"]) >= 2 and num(r["q_value_bh"]) < 0.01),
        "rapporto_milano_senza_5_enti": r6(num(t5["rapporto_senza_5_enti"])),
    }
    return {"citta": righe, "italia": italia, "periodi": periodi, "esatti_milano": esatti_milano, "gruppi": gruppi,
            "enti_che_spiccano": spiccano}


def riga_off(r, **extra):
    d = {"lotti": int(float(r["n_lotti"])), "quota": r6(num(r["quota"])), "quota_attesa": r6(num(r["quota_attesa"])),
         "differenza_punti": r6(num(r["differenza_punti"])) if "differenza_punti" in r else None,
         "gare_distinte": intero(r.get("n_gare_distinte")),
         "quota_per_gara": r6(num(r.get("quota_per_gara"))), "quota_attesa_per_gara": r6(num(r.get("quota_attesa_per_gara"))),
         "differenza_per_gara_punti": r6(num(r.get("differenza_per_gara_punti")))}
    d.update(extra)
    return d


def offerente(R):
    g1 = leggi(R, "60_s2_2019_2023_gruppi.csv")
    g2 = {r["gruppo"]: r for r in leggi(R, "60_s2_2024_2025_gruppi.csv")}
    nz1 = leggi(R, "60_s2_2019_2023_nazionale.csv")[0]
    nz2 = leggi(R, "60_s2_2024_2025_nazionale.csv")[0]
    gruppi = []
    for r in g1:
        s = g2.get(r["gruppo"])
        gruppi.append(riga_off(r, gruppo=pulisci(r["gruppo"]), enti=int(r["n_enti"]),
                               lotti_2024_2025=int(float(s["n_lotti"])) if s else None,
                               quota_2024_2025=r6(num(s["quota"])) if s else None,
                               quota_attesa_2024_2025=r6(num(s["quota_attesa"])) if s else None))
    cit1 = leggi(R, "60_s2_2019_2023_citta.csv")
    citta = []
    for r in cit1:
        citta.append(riga_off(r, citta=r["citta"].capitalize(), ambito="enti locali" if r["perimetro"] == "locale" else "tutti gli enti"))
    ordine = {c.capitalize(): i for i, c in enumerate(CITTA_ORDINE)}
    citta.sort(key=lambda x: (x["ambito"] != "enti locali", ordine[x["citta"]]))
    # Milano in sintesi (due periodi)
    mil = []
    def agg(rows, periodo, ambito, filtro):
        for r in rows:
            if filtro(r):
                mil.append(riga_off(r, periodo=periodo, ambito=ambito))
                return
        raise SystemExit("riga non trovata: " + ambito + " " + periodo)
    agg(cit1, "2019-2023", "Milano città, tutti gli enti", lambda r: r["citta"] == "MILANO" and r["perimetro"] == "tutti")
    agg(cit1, "2019-2023", "Milano città, enti locali", lambda r: r["citta"] == "MILANO" and r["perimetro"] == "locale")
    sa1 = leggi(R, "60_s2_2019_2023_senza_aria.csv")
    agg(sa1, "2019-2023", "Milano città, senza ARIA", lambda r: r["ambito"].startswith("Milano") and "senza ARIA" in r["ambito"])
    cit2 = leggi(R, "60_s2_2024_2025_citta.csv")
    agg(cit2, "2024-2025", "Milano città, tutti gli enti", lambda r: r["citta"] == "MILANO" and r["perimetro"] == "tutti")
    agg(cit2, "2024-2025", "Milano città, enti locali", lambda r: r["citta"] == "MILANO" and r["perimetro"] == "locale")
    sa2 = leggi(R, "60_s2_2024_2025_senza_aria.csv")
    agg(sa2, "2024-2025", "Milano città, senza ARIA", lambda r: r["ambito"].startswith("Milano") and "senza ARIA" in r["ambito"])
    italia = {"2019-2023": {"lotti": int(nz1["n_lotti"]), "quota": r6(num(nz1["quota"])), "quota_per_gara": r6(num(nz1["quota_per_gara"]))},
              "2024-2025": {"lotti": int(nz2["n_lotti"]), "quota": r6(num(nz2["quota"])), "quota_per_gara": r6(num(nz2["quota_per_gara"]))}}
    cop = {r["ambito"]: num(r["quota_con_numero"]) for r in leggi(R, "60_s2_2019_2023_copertura.csv")}
    copertura = {"italia": r6(cop["Italia"]), "milano_citta": r6(cop["Milano citta'"])}
    # per tipo di acquisto (Milano citta')
    nome_tipo = {"FORNITURE": "Forniture", "SERVIZI": "Servizi", "LAVORI": "Lavori"}
    tipi = []
    for r in leggi(R, "60_s2_2019_2023_settore.csv"):
        if r["ambito"] == "Milano citta'" and r["og"] in nome_tipo:
            tipi.append(riga_off(r, tipo=nome_tipo[r["og"]]))
    tipi.sort(key=lambda x: ["Forniture", "Servizi", "Lavori"].index(x["tipo"]))
    # i due enti pubblici nominati
    enti = []
    for r in leggi(R, "60_s2_2019_2023_enti.csv"):
        if r["cf"] == CF_ARIA:
            enti.append(riga_off(r, ente="ARIA (centrale acquisti della Lombardia)", z_per_gara=r6(num(r["z_gara"]))))
        elif r["cf"] == CF_COMUNE:
            enti.append(riga_off(r, ente="Comune di Milano", z_per_gara=r6(num(r["z_gara"]))))
    enti.sort(key=lambda x: x["ente"] != "ARIA (centrale acquisti della Lombardia)")
    # settori principali di quei due enti
    cpv = leggi(R, "60_s2_2019_2023_cpv.csv")
    settori = []
    for amb, div, desc, ente in (("ARIA", "33", "farmaci e dispositivi medici", "ARIA (centrale acquisti della Lombardia)"),
                                 ("Comune di Milano (solo l'ente)", "85", "servizi sanitari e sociali", "Comune di Milano")):
        r = [x for x in cpv if x["ambito"] == amb and x["cpv2"] == div][0]
        settori.append({"ente": ente, "settore": desc, "lotti": int(r["n_lotti"]), "quota": r6(num(r["quota"])),
                        "quota_italia_stesso_settore": r6(num(r["quota_italia_stessa_divisione"]))})
    return {"gruppi": gruppi, "citta": citta, "milano": mil, "italia": italia, "copertura": copertura, "tipi": tipi,
            "enti": enti, "settori": settori}


def lavori(R):
    q = leggi(R, "60_s3_quadro.csv")
    fa = leggi(R, "60_s3_fascia.csv")
    gr = leggi(R, "60_s3_gruppi.csv")
    nome = {"Italia": "Italia", "Milano citta'": "Milano città", "Area metropolitana": "Area metropolitana di Milano"}
    quadro = []
    for r in q:
        quadro.append({
            "ambito": nome[r["ambito"]], "lavori": int(r["n_lavori"]), "attesi_finiti": int(r["n_attesi_finiti"]),
            "con_fine_registrata": int(r["n_con_tempi"]), "senza_fine": r6(num(r["quota_nessuna_fine"])),
            "senza_fine_attesa": r6(num(r["att_nessuna_fine"])), "ritardo_mediano_giorni": num(r["ritardo_mediano_gg"]),
            "oltre_50pct_durata": r6(num(r["quota_ritardo_oltre_50pct"])), "oltre_50pct_durata_attesa": r6(num(r["att_rit50"])),
            "costi_da_accordo_quadro": r6(num(r["quota_costi_da_accordo_quadro"])),
        })
    etich = {"1 sotto 40.000": "Sotto 40.000 euro", "2 da 40.000 a 150.000": "Da 40.000 a 150.000",
             "3 da 150.000 a 1 milione": "Da 150.000 a 1 milione", "4 da 1 a 5 milioni": "Da 1 a 5 milioni",
             "5 oltre 5 milioni": "Oltre 5 milioni"}
    fasce = []
    for k, e in etich.items():
        m = [r for r in fa if r["ambito"].startswith("Milano") and r["fascia_importo"] == k][0]
        i = [r for r in fa if r["ambito"] == "Italia" and r["fascia_importo"] == k][0]
        fasce.append({"fascia": e, "attesi_finiti_milano": int(m["n_attesi_finiti"]), "senza_fine_milano": r6(num(m["quota_nessuna_fine"])),
                      "attesi_finiti_italia": int(i["n_attesi_finiti"]), "senza_fine_italia": r6(num(i["quota_nessuna_fine"]))})
    gruppi = []
    for r in gr:
        gruppi.append({
            "gruppo": pulisci(r["gruppo"]), "lavori": int(r["n_lavori"]), "attesi_finiti": int(r["n_attesi_finiti"]),
            "con_fine_registrata": int(r["n_con_tempi"]), "senza_fine": r6(num(r["quota_nessuna_fine"])),
            "senza_fine_attesa": r6(num(r["att_nessuna_fine"])),
            "costi_da_accordo_quadro": r6(num(r["quota_costi_da_accordo_quadro"])),
        })
    of = [r for r in leggi(R, "60_s3_enti_con_attesi.csv") if r["cf"] == "09320630966"][0]
    operatore_fibra = {"lavori": int(of["n_lavori"]), "con_fine_registrata": int(of["n_conclusi"])}
    return {"quadro": quadro, "fasce": fasce, "gruppi": gruppi, "operatore_fibra": operatore_fibra}


def coppie(R):
    rows = leggi(R, "60_s4_coppie.csv")
    # totali nazionali delle coppie estreme: dal referto 60 (sez. 4), che li prende dal referto 10
    ita = {"competitiva": 70, "diretta": 751, "adesione_accordo_quadro": 193, "altro": 5}
    nome = {"competitiva": "Procedure competitive (gare)", "diretta": "Affidamenti diretti",
            "adesione_accordo_quadro": "Adesioni ad accordi quadro", "altro": "Altro"}
    out = []
    for k in ("competitiva", "diretta", "adesione_accordo_quadro", "altro"):
        s = [r for r in rows if r["classe"] == k]
        e = [r for r in s if r["estrema"] == "True"]
        out.append({
            "classe": nome[k], "coppie_milano": len(s), "estreme_milano": len(e), "estreme_italia": ita[k],
            "quota_estreme_italiane_di_milano": r6(len(e) / ita[k]),
            "estreme_in_tutte_le_varianti": sum(1 for r in e if r["regge_varianti_tecniche"] == "True"),
            "con_spiegazione_innocua": sum(1 for r in e if r["spiegazione_innocua"] == "True"),
            "con_spiegazione_oltre_all_essere_diretta": sum(1 for r in e if r["spiegazione_innocua_senza_diretti"] == "True"),
        })
    return {"classi": out, "coppie_milano_totale": len(rows), "coppie_italia_totale": 28896}


def pnrr(R):
    rows = {r["ambito"]: r for r in leggi(R, "60_s3_pnrr_quota.csv")}
    spec = leggi(R, "60_s3_speciali.csv")
    out = []
    for amb, nome in (("Italia", "Italia"), ("Area metropolitana", "Area metropolitana di Milano"), ("Milano citta'", "Milano città")):
        r = rows[amb]
        n_senza = int(r["n_lavori_senza_open_fiber"])
        pn_senza = int(round(num(r["quota_pnrr_senza_open_fiber"]) * n_senza))
        out.append({
            "ambito": nome, "lavori_2023_2025": int(r["n_lavori_2023_2025"]), "lavori_pnrr": int(r["n_pnrr"]),
            "quota_pnrr": r6(num(r["quota_pnrr"])), "quota_pnrr_senza_operatore_fibra": r6(num(r["quota_pnrr_senza_open_fiber"])),
            "lavori_pnrr_di_operatore_fibra": int(r["n_pnrr"]) - pn_senza,
            "importo_pnrr_euro": int(round(num(r["importo_pnrr"]))), "importo_pnrr_senza_operatore_fibra_euro": int(round(num(r["importo_pnrr_senza_open_fiber"]))),
        })
    pm = [r for r in spec if r["gruppo_lavori"].startswith("PNRR") and r["ambito"].startswith("Milano")][0]
    ol = leggi(R, "60_s3_olimpiadi_enti.csv")
    olimp = {"lavori": sum(int(r["n_lavori"]) for r in ol), "importo_euro": int(round(sum(num(r["importo"]) for r in ol))),
             "enti": len(ol), "anno_min": min(int(r["anno_min"]) for r in ol), "anno_max": max(int(r["anno_max"]) for r in ol),
             "lavori_del_primo_ente": max(int(r["n_lavori"]) for r in ol)}
    return {"ambiti": out, "pnrr_milano_con_fine_registrata": int(pm["n_con_tempi"]), "olimpiadi": olimp}


# ---------------------------------------------------------------- controlli sul referto

def controlli(D):
    """Confronta i numeri scritti a mano nella pagina con quelli dei csv (testo del referto)."""
    err = []

    def chk(nome, got, atteso):
        if str(got) != str(atteso):
            err.append(f"{nome}: csv {got!r} <> pagina {atteso!r}")

    P, S, O, L, C, N = D["perimetro"], D["soglia"], D["offerente"], D["lavori"], D["coppie"], D["pnrr"]
    t = {x["ambito"]: x for x in P["totali"]}
    mc = t["Milano città"]
    chk("procedure Milano", migliaia(mc["procedure"]), "967.936")
    chk("% procedure Italia", p(mc["quota_procedure_italia"]), "2,8")
    chk("% procedure Lombardia", p(mc["quota_procedure_lombardia"]), "17,9")
    chk("importo Milano mld", it(mc["importo_euro"] / 1e9), "215,0")
    chk("% importo Italia", p(mc["quota_importo_italia"]), "8,6")
    chk("procedure area", migliaia(t["Area metropolitana di Milano"]["procedure"]), "1.611.682")
    chk("% area", p(t["Area metropolitana di Milano"]["quota_procedure_italia"]), "4,6")
    chk("ARIA procedure", migliaia(P["aria"]["procedure"]), "31.095")
    chk("ARIA mld", it(P["aria"]["importo_euro"] / 1e9), "130,6")
    chk("ARIA % importo Milano", p(P["aria"]["quota_importo_milano_citta"], 0), "61")
    g = {x["gruppo"]: x for x in P["gruppi"]}
    chk("Regione % proc area", p(g["Regione Lombardia, ARIA e enti regionali"]["quota_procedure_area"], 0), "5")
    chk("Regione % imp area", p(g["Regione Lombardia, ARIA e enti regionali"]["quota_importo_area"], 0), "57")
    chk("gruppi procedure", [migliaia(x["procedure"]) for x in P["gruppi"]],
        ['62.381', '15.863', '397.770', '220.241', '78.184', '190.131', '276.456', '370.656'])
    chk("gruppi mld", [it(x["importo_euro"] / 1e9) for x in P["gruppi"]],
        ['20,9', '5,2', '24,7', '5,4', '150,0', '34,6', '10,5', '9,7'])
    # soglia
    ml = [x for x in S["citta"] if x["citta"] == "Milano" and x["ambito"] == "enti locali"][0]
    mt = [x for x in S["citta"] if x["citta"] == "Milano" and x["ambito"] == "tutti gli enti"][0]
    chk("soglia Milano quota", p(ml["quota"]), "21,8")
    chk("soglia Milano attesa", p(ml["quota_attesa"]), "20,0")
    chk("soglia rapporto", it(ml["rapporto"], 2), "1,09")
    chk("soglia ic", (it(ml["rapporto_intervallo_basso"], 2), it(ml["rapporto_intervallo_alto"], 2)), ("0,96", "1,20"))
    chk("soglia affidamenti Milano locale", migliaia(ml["affidamenti_vicini_soglia"]), "32.516")
    chk("soglia tutti", (p(mt["quota"]), p(mt["quota_attesa"])), ("18,9", "18,2"))
    chk("soglia Italia", (p(S["italia"]["quota"]), migliaia(S["italia"]["nell_ultimo_5pct"]), migliaia(S["italia"]["affidamenti_vicini_soglia"])),
        ("17,1", "247.734", "1.451.084"))
    chk("soglia altre citta", [p(x["quota"]) for x in S["citta"] if x["ambito"] == "enti locali"],
        ['21,8', '16,4', '13,1', '15,0', '20,3', '18,6', '18,4', '11,5', '13,5'])
    chk("periodi quota", [(p(x["quota_milano"]), p(x["quota_italia"]), it(x["rapporto_milano"], 2)) for x in S["periodi"]],
        [('32,8', '26,7', '1,04'), ('6,5', '6,9', '1,10'), ('8,6', '9,9', '1,01'), ('14,3', '13,9', '1,04')])
    chk("esatti Milano", (S["esatti_milano"]["n"], migliaia(S["esatti_milano"]["su"]), p(S["esatti_milano"]["quota"])), (143, "8.571", "1,7"))
    chk("esatti Italia", (migliaia(S["italia"]["esatti_a_un_euro"]), p(S["italia"]["quota_esatti"])), ("16.918", "6,8"))
    sg = {x["gruppo"]: x for x in S["gruppi"]}
    c = sg["Comune di Milano e sue società"]
    chk("soglia gruppo Comune", (it(c["rapporto"], 2), it(c["rapporto_intervallo_basso"], 2), it(c["rapporto_intervallo_alto"], 2)), ("1,22", "0,91", "1,55"))
    n = sg["Altri enti nazionali con sede a Milano"]
    chk("soglia gruppo nazionali", (it(n["rapporto"], 2), it(n["rapporto_intervallo_basso"], 2), it(n["rapporto_intervallo_alto"], 2)), ("0,78", "0,63", "0,94"))
    chk("enti Milano", P["enti_milano_citta_con_procedure"], 505)
    sp = S["enti_che_spiccano"]
    chk("enti che spiccano", (sp["enti_con_almeno_100"], sp["rapporto_almeno_1_5_e_q_sotto_0_01"], sp["rapporto_almeno_2_e_q_sotto_0_01"],
                              it(sp["rapporto_milano_senza_5_enti"], 2)), (108, 10, 2, "0,93"))
    # un solo offerente
    om = {(x["ambito"], x["periodo"]): x for x in O["milano"]}
    a = om[("Milano città, tutti gli enti", "2019-2023")]
    chk("offerente Milano", (p(a["quota"]), p(a["quota_attesa"]), migliaia(a["lotti"])), ("54,5", "43,0", "14.708"))
    chk("offerente Milano per gara", (p(a["quota_per_gara"]), p(a["quota_attesa_per_gara"])), ("43,2", "35,3"))
    chk("offerente Italia", p(O["italia"]["2019-2023"]["quota"]), "38,7")
    chk("offerente senza ARIA", (p(om[("Milano città, senza ARIA", "2019-2023")]["quota"]), p(om[("Milano città, senza ARIA", "2019-2023")]["quota_attesa"]),
                                  it(om[("Milano città, senza ARIA", "2019-2023")]["differenza_punti"])), ("38,2", "35,4", "2,7"))
    chk("offerente locali", (p(om[("Milano città, enti locali", "2019-2023")]["quota"]), p(om[("Milano città, enti locali", "2019-2023")]["quota_attesa"]),
                              it(om[("Milano città, enti locali", "2019-2023")]["differenza_punti"])), ("42,8", "37,7", "5,1"))
    ro = [x for x in O["citta"] if x["citta"] == "Roma" and x["ambito"] == "enti locali"][0]
    chk("offerente Roma", (p(ro["quota"]), p(ro["quota_attesa"])), ("42,4", "37,8"))
    b = om[("Milano città, tutti gli enti", "2024-2025")]
    chk("offerente 2024-25", (p(b["quota"]), p(b["quota_attesa"]), p(O["italia"]["2024-2025"]["quota"])), ("54,7", "43,2", "42,8"))
    chk("copertura", (p(O["copertura"]["milano_citta"], 0), p(O["copertura"]["italia"], 0)), ("58", "51"))
    e = {x["ente"]: x for x in O["enti"]}
    ar, co = e["ARIA (centrale acquisti della Lombardia)"], e["Comune di Milano"]
    chk("ARIA offerente", (migliaia(ar["lotti"]), p(ar["quota"]), p(ar["quota_attesa"]), it(ar["differenza_per_gara_punti"])), ("8.736", "65,7", "48,1", "18,3"))
    chk("Comune offerente", (migliaia(co["lotti"]), p(co["quota"]), p(co["quota_attesa"]), it(co["differenza_per_gara_punti"])), ("937", "60,4", "38,1", "19,6"))
    s = {x["ente"]: x for x in O["settori"]}
    chk("ARIA settore", (s["ARIA (centrale acquisti della Lombardia)"]["lotti"], p(s["ARIA (centrale acquisti della Lombardia)"]["lotti"] / ar["lotti"], 0)), (7587, "87"))
    chk("Comune settore", (s["Comune di Milano"]["lotti"], p(s["Comune di Milano"]["lotti"] / co["lotti"], 0)), (398, "42"))
    chk("tipi", [(p(x["quota"]), p(x["quota_attesa"])) for x in O["tipi"]], [('62,0', '48,1'), ('41,8', '35,1'), ('15,1', '13,3')])
    og = {x["gruppo"]: x for x in O["gruppi"]}
    chk("gruppi offerente", [(p(x["quota"], 0), p(x["quota_attesa"], 0), migliaia(x["lotti"])) for x in O["gruppi"]],
        [('46', '35', '1.746'), ('21', '29', '935'), ('46', '42', '2.324'), ('36', '36', '436'), ('61', '46', '9.941'), ('20', '26', '1.197'),
         ('24', '29', '1.482'), ('36', '33', '793')])
    # lavori
    q = {x["ambito"]: x for x in L["quadro"]}
    chk("lavori Milano", (migliaia(q["Milano città"]["lavori"]), migliaia(q["Milano città"]["attesi_finiti"]), p(q["Milano città"]["senza_fine"]),
                           p(q["Milano città"]["senza_fine_attesa"]), q["Milano città"]["con_fine_registrata"]), ("16.017", "3.374", "39,7", "39,9", 2033))
    chk("lavori Italia", (p(q["Italia"]["senza_fine"]), migliaia(q["Italia"]["attesi_finiti"])), ("30,7", "261.688"))
    chk("lavori oltre 50", (p(q["Milano città"]["oltre_50pct_durata"]), p(q["Italia"]["oltre_50pct_durata"]), p(q["Milano città"]["oltre_50pct_durata_attesa"])),
        ("30,0", "34,4", "38,6"))
    chk("lavori ritardo mediano", (q["Milano città"]["ritardo_mediano_giorni"], q["Italia"]["ritardo_mediano_giorni"]), (0.0, 1.0))
    chk("lavori accordo quadro", (p(q["Milano città"]["costi_da_accordo_quadro"]), p(q["Italia"]["costi_da_accordo_quadro"])), ("45,2", "11,1"))
    chk("fasce", [(p(x["senza_fine_milano"], 0), p(x["senza_fine_italia"], 0), x["attesi_finiti_milano"]) for x in L["fasce"]],
        [('44', '30', 186), ('21', '22', 839), ('36', '34', 1604), ('60', '61', 566), ('92', '79', 179)])
    lg = {x["gruppo"]: x for x in L["gruppi"]}
    chk("lavori Citta Metropolitana", (p(lg["Città Metropolitana e sue società"]["senza_fine"]), p(lg["Città Metropolitana e sue società"]["senza_fine_attesa"])), ("65,6", "37,4"))
    chk("lavori nazionali", (p(lg["Altri enti nazionali con sede a Milano"]["senza_fine"]), p(lg["Altri enti nazionali con sede a Milano"]["senza_fine_attesa"])), ("76,0", "49,1"))
    chk("operatore fibra", (migliaia(L["operatore_fibra"]["lavori"]), L["operatore_fibra"]["con_fine_registrata"]), ("6.883", 3))
    # coppie
    cl = {x["classe"]: x for x in C["classi"]}
    chk("coppie", [(x["coppie_milano"], x["estreme_milano"], x["estreme_italia"], x["estreme_in_tutte_le_varianti"], x["con_spiegazione_innocua"],
                    x["con_spiegazione_oltre_all_essere_diretta"]) for x in C["classi"]],
        [(359, 4, 70, 2, 4, 4), (1258, 37, 751, 17, 37, 33), (535, 24, 193, 4, 24, 24), (39, 1, 5, 0, 0, 0)])
    chk("coppie quote", [p(x["quota_estreme_italiane_di_milano"], 0) for x in C["classi"][:3]], ["6", "5", "12"])
    chk("coppie totale", (C["coppie_milano_totale"], migliaia(C["coppie_milano_totale"])), (2191, "2.191"))
    # pnrr e olimpiadi
    nm = {x["ambito"]: x for x in N["ambiti"]}
    chk("pnrr", (p(nm["Milano città"]["quota_pnrr"]), p(nm["Italia"]["quota_pnrr"]), p(nm["Milano città"]["quota_pnrr_senza_operatore_fibra"]),
                 p(nm["Italia"]["quota_pnrr_senza_operatore_fibra"])), ("40,8", "11,5", "7,6", "10,7"))
    chk("pnrr numeri", (migliaia(nm["Milano città"]["lavori_pnrr"]), migliaia(nm["Milano città"]["lavori_pnrr_di_operatore_fibra"])), ("4.593", "4.225"))
    chk("pnrr importi", (it(nm["Milano città"]["importo_pnrr_euro"] / 1e9), it(nm["Milano città"]["importo_pnrr_senza_operatore_fibra_euro"] / 1e9)), ("3,0", "0,9"))
    chk("pnrr fine registrata", N["pnrr_milano_con_fine_registrata"], 65)
    ol = N["olimpiadi"]
    chk("olimpiadi", (ol["lavori"], it(ol["importo_euro"] / 1e6), ol["anno_min"], ol["anno_max"], ol["lavori_del_primo_ente"]), (21, "27,8", 2024, 2025, 15))
    return err


# ---------------------------------------------------------------- scrittura

def main():
    if len(sys.argv) != 3 or not all(os.path.isabs(a) for a in sys.argv[1:]):
        print(__doc__)
        print("Servono due percorsi ASSOLUTI: cartella risultati di appalti-anac e cartella di uscita docs/appalti/data.")
        sys.exit(2)
    R, OUT = sys.argv[1], sys.argv[2]
    if not os.path.isdir(R):
        sys.exit("Cartella non trovata: " + R)
    os.makedirs(OUT, exist_ok=True)

    D = {"perimetro": perimetro(R), "soglia": soglia(R), "offerente": offerente(R), "lavori": lavori(R),
         "coppie": coppie(R), "pnrr": pnrr(R)}
    err = controlli(D)
    if err:
        print("I numeri dei file non coincidono con quelli scritti nella pagina:")
        for e in err:
            print(" -", e)
        sys.exit(1)

    D["meta"] = {"fonte": "ANAC open data, dati.anticorruzione.it, licenza CC BY-SA 4.0",
                 "periodo": "2019-2025", "analisi_del": "30 ottobre 2026",
                 "origine": "appalti-anac/risultati/60_*.csv (Focus Milano)"}

    # json della pagina
    with open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(D, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # csv scaricabili (stessi numeri del json)
    P, S, O, L, C, N = D["perimetro"], D["soglia"], D["offerente"], D["lavori"], D["coppie"], D["pnrr"]
    scrivi_csv(OUT, "perimetro_gruppi.csv",
               ["gruppo", "enti_con_procedure", "procedure", "importo_euro", "quota_procedure_area", "quota_importo_area"], P["gruppi"])
    scrivi_csv(OUT, "perimetro_totali.csv",
               ["ambito", "procedure", "importo_euro", "quota_procedure_italia", "quota_importo_italia", "quota_procedure_lombardia"], P["totali"])
    scrivi_csv(OUT, "soglia_citta.csv",
               ["citta", "ambito", "affidamenti_vicini_soglia", "nell_ultimo_5pct", "quota", "quota_attesa", "rapporto",
                "rapporto_intervallo_basso", "rapporto_intervallo_alto", "esatti_a_un_euro"], S["citta"])
    scrivi_csv(OUT, "soglia_periodi.csv", ["periodo", "quota_milano", "quota_attesa_milano", "rapporto_milano", "quota_italia"], S["periodi"])
    scrivi_csv(OUT, "soglia_gruppi.csv",
               ["gruppo", "enti", "affidamenti_vicini_soglia", "nell_ultimo_5pct", "quota", "quota_attesa", "rapporto",
                "rapporto_intervallo_basso", "rapporto_intervallo_alto"], S["gruppi"])
    cols_off = ["lotti", "quota", "quota_attesa", "differenza_punti", "gare_distinte", "quota_per_gara", "quota_attesa_per_gara", "differenza_per_gara_punti"]
    scrivi_csv(OUT, "offerente_gruppi.csv",
               ["gruppo", "enti"] + cols_off + ["lotti_2024_2025", "quota_2024_2025", "quota_attesa_2024_2025"], O["gruppi"])
    scrivi_csv(OUT, "offerente_citta.csv", ["citta", "ambito"] + cols_off, O["citta"])
    scrivi_csv(OUT, "offerente_milano.csv", ["ambito", "periodo"] + cols_off, O["milano"])
    scrivi_csv(OUT, "offerente_tipi.csv", ["tipo"] + cols_off, O["tipi"])
    scrivi_csv(OUT, "offerente_enti.csv", ["ente"] + cols_off + ["z_per_gara"], O["enti"])
    scrivi_csv(OUT, "offerente_settori.csv", ["ente", "settore", "lotti", "quota", "quota_italia_stesso_settore"], O["settori"])
    scrivi_csv(OUT, "lavori_quadro.csv",
               ["ambito", "lavori", "attesi_finiti", "con_fine_registrata", "senza_fine", "senza_fine_attesa", "ritardo_mediano_giorni",
                "oltre_50pct_durata", "oltre_50pct_durata_attesa", "costi_da_accordo_quadro"], L["quadro"])
    scrivi_csv(OUT, "lavori_fasce.csv",
               ["fascia", "attesi_finiti_milano", "senza_fine_milano", "attesi_finiti_italia", "senza_fine_italia"], L["fasce"])
    scrivi_csv(OUT, "lavori_gruppi.csv",
               ["gruppo", "lavori", "attesi_finiti", "con_fine_registrata", "senza_fine", "senza_fine_attesa", "costi_da_accordo_quadro"], L["gruppi"])
    scrivi_csv(OUT, "vincitori_coppie.csv",
               ["classe", "coppie_milano", "estreme_milano", "estreme_italia", "quota_estreme_italiane_di_milano",
                "estreme_in_tutte_le_varianti", "con_spiegazione_innocua", "con_spiegazione_oltre_all_essere_diretta"], C["classi"])
    scrivi_csv(OUT, "pnrr.csv",
               ["ambito", "lavori_2023_2025", "lavori_pnrr", "quota_pnrr", "quota_pnrr_senza_operatore_fibra", "lavori_pnrr_di_operatore_fibra",
                "importo_pnrr_euro", "importo_pnrr_senza_operatore_fibra_euro"], N["ambiti"])
    ol = N["olimpiadi"]
    scrivi_csv(OUT, "olimpiadi.csv", ["lavori", "importo_euro", "enti", "anno_min", "anno_max", "lavori_del_primo_ente"], [ol])

    print("Fatto. File in", OUT)
    for nome in sorted(os.listdir(OUT)):
        print(f"  {nome}  {os.path.getsize(os.path.join(OUT, nome))} byte")


if __name__ == "__main__":
    main()
