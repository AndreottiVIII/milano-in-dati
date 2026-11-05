"""Sezione "Quanti appalti senza gara" (Comune di Milano): scrive docs/appalti/data/diretti_comune.json.

Rifa' i numeri dai file originali ANAC (database appalti.duckdb del progetto appalti-anac, aperto in sola
lettura), per i soli CIG e smartcig del Comune di Milano (codice fiscale 01199250158), senza doppioni.
Li confronta con quelli del rapporto _idee/verifica_quattro_pagine.md (parte 2) e scrive ogni differenza
nel JSON (campo "differenze"). Si ferma con un errore se la serie principale non torna.

Serve duckdb: si usa il Python del progetto appalti-anac.
Uso:
  C:\\Users\\davide\\Desktop\\ClaudeTower\\appalti-anac\\.venv\\Scripts\\python.exe -I -X utf8 diretti_comune.py <duckdb> <uscita.json>
"""
import json
import sys
import datetime

import duckdb

CF = "01199250158"
DIRETTI = ("24", "32", "37", "40", "12", "18", "26")
IN_HOUSE = "25"
ADESIONE = "27"
ANNI = list(range(2019, 2026))
SOGLIA_MIN = 5000

# numeri del rapporto (verifica_quattro_pagine.md, parte 2)
R_TOT = {2019: 3764, 2020: 3136, 2021: 3418, 2022: 2915, 2023: 3186, 2024: 1862, 2025: 1745}
R_DIR = {2019: 2075, 2020: 1958, 2021: 2186, 2022: 2197, 2023: 2362, 2024: 1472, 2025: 1379}
R_VAL = {2019: 27.9, 2020: 23.0, 2021: 34.6, 2022: 33.6, 2023: 28.7, 2024: 111.1, 2025: 110.6}
R_QN5 = {2019: 31.8, 2020: 45.2, 2021: 43.7, 2022: 52.6, 2023: 45.7, 2024: 60.1, 2025: 62.4}
R_QV5 = {2019: 3.7, 2020: 2.7, 2021: 3.0, 2022: 5.1, 2023: 2.0, 2024: 11.4, 2025: 7.9}
R_SMART = {2024: 865, 2025: 776}
R_OVER40 = {2023: 108, 2024: 258}
R_AQ = {2024: 126, 2025: 182}
R_VINC = {2024: 594, 2025: 595}
R_F3 = {2024: 29.3, 2025: 28.1}
R_F3_SENZA_AQ = {2024: 17.2, 2025: 10.2}
R_PERS = {2024: 20, 2025: 51}
R_VINC_OLD = {2019: 8, 2020: 32, 2021: 42, 2022: 72, 2023: 78}

diff = []


def conf(nome, mio, rapp, tol=0.0):
    ok = abs(mio - rapp) <= tol
    if not ok:
        diff.append({"voce": nome, "ricalcolato": mio, "rapporto": rapp})
    return ok


def main(db, out):
    c = duckdb.connect(db, read_only=True)
    q = lambda s: c.execute(s).fetchall()
    base = f"""(
      SELECT cig, anno_cig AS anno, importo_lotto AS imp, flag_importo_anomalo AS anom, cod_tipo_scelta_contraente AS cod,
             'cig' AS o, cig_accordo_quadro AS aq
        FROM cig WHERE NOT flag_doppione AND cf_amministrazione_appaltante = '{CF}'
      UNION ALL
      SELECT cig, anno_cig, importo_lotto, flag_importo_anomalo, cod_tipo_scelta_contraente, 'smart', NULL
        FROM smartcig WHERE NOT flag_doppione AND cf_amministrazione_appaltante = '{CF}')"""
    D = "cod IN (" + ",".join(f"'{x}'" for x in DIRETTI) + ")"

    # controlli sui dati di partenza
    tot_righe = q(f"SELECT count(*), count(DISTINCT cig) FROM {base}")[0]
    assert tot_righe[0] == tot_righe[1], "CIG duplicati dopo aver tolto i doppioni"
    nulli = q(f"SELECT sum(CASE WHEN imp IS NULL THEN 1 ELSE 0 END), sum(CASE WHEN cod IS NULL THEN 1 ELSE 0 END), "
              f"sum(CASE WHEN anno IS NULL OR anno NOT BETWEEN 2019 AND 2025 THEN 1 ELSE 0 END) FROM {base}")[0]
    assert tuple(nulli) == (0, 0, 0), f"importi/codici/anni mancanti: {nulli}"
    anomali = q(f"SELECT count(*) FROM {base} WHERE anom")[0][0]

    serie = []
    for a in ANNI:
        r = {"anno": a}
        for nome, filtro in (("tutti", "TRUE"), ("da5000", f"imp >= {SOGLIA_MIN}")):
            t = q(f"""SELECT count(*),
                  sum(CASE WHEN {D} THEN 1 ELSE 0 END),
                  sum(CASE WHEN cod = '{IN_HOUSE}' THEN 1 ELSE 0 END),
                  sum(CASE WHEN cod = '{ADESIONE}' THEN 1 ELSE 0 END),
                  sum(CASE WHEN NOT anom THEN imp ELSE 0 END),
                  sum(CASE WHEN NOT anom AND {D} THEN imp ELSE 0 END),
                  sum(CASE WHEN anom THEN 1 ELSE 0 END)
                  FROM {base} WHERE anno = {a} AND {filtro}""")[0]
            n, nd, nh, na, v, vd, an = t
            r[nome] = {"n": n, "n_diretti": nd, "n_in_house": nh, "n_adesioni": na,
                       "quota_n": nd / n, "valore": v, "valore_diretti": vd, "quota_v": vd / v, "n_anomali": an}
        # alcuni numeri di contorno
        r["smartcig"] = q(f"SELECT count(*) FROM {base} WHERE anno={a} AND o='smart'")[0][0]
        r["diretti_sopra_40000"] = q(f"SELECT count(*) FROM {base} WHERE anno={a} AND {D} AND imp > 40000")[0][0]
        r["diretti_mediana_euro"] = q(f"SELECT median(imp) FROM {base} WHERE anno={a} AND {D}")[0][0]
        r["ordini_da_accordo_quadro"] = q(
            f"SELECT count(*) FROM {base} WHERE anno={a} AND cod='24' AND aq IS NOT NULL AND trim(aq)<>''")[0][0]
        serie.append(r)

    # --- confronto con il rapporto
    for r in serie:
        a = r["anno"]
        conf(f"CIG totali {a}", r["tutti"]["n"], R_TOT[a])
        conf(f"diretti {a}", r["tutti"]["n_diretti"], R_DIR[a])
        conf(f"valore diretti (mil. euro) {a}", round(r["tutti"]["valore_diretti"] / 1e6, 1), R_VAL[a], 0.05)
        conf(f"quota diretti sul numero da 5.000 euro {a} (%)", round(r["da5000"]["quota_n"] * 100, 1), R_QN5[a], 0.05)
        conf(f"quota diretti sul valore da 5.000 euro {a} (%)", round(r["da5000"]["quota_v"] * 100, 1), R_QV5[a], 0.05)
        if a in R_SMART:
            conf(f"smartcig {a}", r["smartcig"], R_SMART[a])
        if a in R_OVER40:
            conf(f"diretti sopra 40.000 euro {a}", r["diretti_sopra_40000"], R_OVER40[a])
        if a in R_AQ:
            conf(f"ordini da accordo quadro (codice 24) {a}", r["ordini_da_accordo_quadro"], R_AQ[a])
    gravi = [d for d in diff if d["voce"].startswith(("CIG totali", "diretti 20", "quota diretti sul numero"))]
    assert not gravi, f"la serie principale non torna con il rapporto: {gravi}"

    # --- fornitori con almeno 3 diretti nell'anno (solo 2024-2025: prima il vincitore non c'e')
    copertura = []
    for a in ANNI:
        nd, con_v = q(f"""SELECT count(*), count(w.cig) FROM {base} b LEFT JOIN
            (SELECT DISTINCT cig FROM aggiudicatari WHERE NOT flag_doppione AND NOT flag_cf_invalido AND codice_fiscale IS NOT NULL) w
            ON w.cig=b.cig WHERE b.anno={a} AND b.o='cig' AND {D.replace('cod', 'b.cod')}""")[0]
        nds = q(f"SELECT count(*) FROM {base} WHERE anno={a} AND {D}")[0][0]
        copertura.append({"anno": a, "diretti": nds, "diretti_ordinari_con_vincitore": con_v})
    for x in copertura:
        if x['anno'] in R_VINC_OLD:
            conf(f"diretti ordinari con vincitore noto {x['anno']}", x['diretti_ordinari_con_vincitore'], R_VINC_OLD[x['anno']], 0)
    fornitori = {}
    for a in (2024, 2025):
        # un vincitore per CIG: tolti ausiliari, mandanti e consorziati; codici fiscali non validi esclusi
        rows = q(f"""WITH w AS (
            SELECT b.cig, b.aq, min(ag.codice_fiscale) AS cf
              FROM {base} b JOIN aggiudicatari ag ON ag.cig=b.cig AND NOT ag.flag_doppione AND NOT ag.flag_cf_invalido
             WHERE b.anno={a} AND {D.replace('cod', 'b.cod')} AND ag.codice_fiscale IS NOT NULL
               AND (ag.ruolo IS NULL OR upper(ag.ruolo) NOT IN ('IMPRESA AUSILIARIA','MANDANTE','AUSILIARIA')
                    AND upper(ag.ruolo) NOT LIKE 'CONSORZIATO%')
             GROUP BY 1,2)
            SELECT cig, cf, (aq IS NOT NULL AND trim(aq)<>'') AS da_aq, length(cf)=16 AS pers FROM w""")
        def calcola(sub):
            from collections import Counter
            cnt = Counter(cf for _, cf, _, _ in sub)
            n = len(sub)
            out = {"diretti_con_vincitore": n, "fornitori_distinti": len(cnt)}
            for k in (3, 5, 10):
                out[f"quota_fornitori_{k}_o_piu"] = (sum(1 for _, cf, _, _ in sub if cnt[cf] >= k) / n) if n else None
            out["max_diretti_stesso_fornitore"] = max(cnt.values()) if cnt else 0
            out["fornitori_con_3_o_piu"] = sum(1 for v in cnt.values() if v >= 3)
            return out
        tutti = calcola(rows)
        senza_aq = calcola([r for r in rows if not r[2]])
        fornitori[a] = {"tutti": tutti, "senza_accordo_quadro": senza_aq,
                        "ordini_da_accordo_quadro_con_vincitore": sum(1 for r in rows if r[2]),
                        "persone_fisiche": sum(1 for r in rows if r[3])}
        conf(f"diretti con vincitore noto {a}", tutti["diretti_con_vincitore"], R_VINC[a], 0)
        conf(f"quota fornitori con 3+ diretti {a} (%)", round(tutti["quota_fornitori_3_o_piu"] * 100, 1), R_F3[a], 0.05)
        conf(f"quota fornitori con 3+ diretti senza accordi quadro {a} (%)",
             round(senza_aq["quota_fornitori_3_o_piu"] * 100, 1), R_F3_SENZA_AQ[a], 0.05)
        conf(f"persone fisiche tra i vincitori {a}", fornitori[a]["persone_fisiche"], R_PERS[a], 0)

    # --- segnali di proroga (solo per dire che sono pochi)
    prorog = []
    for a in ANNI:
        r = q(f"""SELECT count(DISTINCT v.cig) FILTER (WHERE v.cod_motivo_variante IN ('18','19') OR (v.cig_proroga IS NOT NULL AND trim(v.cig_proroga)<>''))
                  FROM {base} b JOIN varianti v ON v.cig=b.cig AND NOT v.flag_doppione WHERE b.anno={a}""")[0][0]
        prorog.append({"anno": a, "cig_con_segnale_proroga_o_rinnovo": r})


    # numeri scritti a mano nel testo della pagina: si ferma se non tornano
    S = {r["anno"]: r for r in serie}
    f = fornitori
    testo = {
        "ordinari": (tot_righe[0] - sum(r["smartcig"] for r in serie), 4987), "smartcig": (sum(r["smartcig"] for r in serie), 15039),
        "n 2019 %": (round(S[2019]["da5000"]["quota_n"] * 100), 32), "n 2025 %": (round(S[2025]["da5000"]["quota_n"] * 100), 62),
        "v 2025 %": (round(S[2025]["da5000"]["quota_v"] * 100, 1), 7.9), "v 2024 %": (round(S[2024]["da5000"]["quota_v"] * 100, 1), 11.4),
        "v 2023 %": (round(S[2023]["da5000"]["quota_v"] * 100, 1), 2.0), "n 2025 %.1": (round(S[2025]["da5000"]["quota_n"] * 100, 1), 62.4),
        "sopra 40k 2023": (S[2023]["diretti_sopra_40000"], 108), "sopra 40k 2024": (S[2024]["diretti_sopra_40000"], 258),
        "smart 2024": (S[2024]["smartcig"], 865), "smart 2025": (S[2025]["smartcig"], 776),
        "tot 2023": (S[2023]["tutti"]["n"], 3186), "tot 2024": (S[2024]["tutti"]["n"], 1862),
        "aq 2024": (S[2024]["ordini_da_accordo_quadro"], 126), "aq 2025": (S[2025]["ordini_da_accordo_quadro"], 182),
        "3+ 2024": (round(f[2024]["tutti"]["quota_fornitori_3_o_piu"] * 100), 31), "3+ 2025": (round(f[2025]["tutti"]["quota_fornitori_3_o_piu"] * 100), 28),
        "3+ senza aq 2024": (round(f[2024]["senza_accordo_quadro"]["quota_fornitori_3_o_piu"] * 100), 18),
        "3+ senza aq 2025": (round(f[2025]["senza_accordo_quadro"]["quota_fornitori_3_o_piu"] * 100), 10),
        "vincitori prima del 2024 sotto 100": (max(x["diretti_ordinari_con_vincitore"] for x in copertura if x["anno"] < 2024) < 100, True),
        "proroghe max fino al 2023": (max(p["cig_con_segnale_proroga_o_rinnovo"] for p in prorog if p["anno"] <= 2023), 20),
        "proroghe min fino al 2023": (min(p["cig_con_segnale_proroga_o_rinnovo"] for p in prorog if p["anno"] <= 2023), 3),
        "proroghe 2024-2025": (sum(p["cig_con_segnale_proroga_o_rinnovo"] for p in prorog if p["anno"] >= 2024), 0),
    }
    sbagliati = {k: v for k, v in testo.items() if v[0] != v[1]}
    assert not sbagliati, f"numeri del testo della pagina che non tornano: {sbagliati}"

    res = {
        "generato": datetime.date.today().isoformat(),
        "ente": "Comune di Milano",
        "definizioni": {
            "diretti": "codici ANAC 24, 32, 37, 40, 12, 18, 26 (affidamento diretto semplice, per varianti, forniture supplementari, modifiche, cooperative sociali, societa' raggruppate)",
            "in_house": "codice 25, esclusi dai diretti", "adesioni": "codice 27, esclusi dai diretti",
            "valore": "importo_lotto (stima a base di gara, non spesa), esclusi gli importi anomali",
            "soglia_minima_euro": SOGLIA_MIN},
        "controlli": {"righe_totali": tot_righe[0], "importi_anomali": anomali},
        "serie": serie, "copertura_vincitori": copertura, "fornitori": fornitori, "proroghe": prorog,
        "differenze": diff,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("scritto", out)
    print("differenze rispetto al rapporto:", json.dumps(diff, ensure_ascii=False, indent=1) if diff else "nessuna")
    for r in serie:
        print(r["anno"], r["da5000"]["n"], round(r["da5000"]["quota_n"] * 100, 1), round(r["da5000"]["quota_v"] * 100, 1))
    print(json.dumps(fornitori, ensure_ascii=False)); print(prorog)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
