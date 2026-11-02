"""Costruisce i file della pagina docs/musei/ (docs/musei/data/).

Uso (percorsi assoluti; si puo' rilanciare quando arrivano nuovi dati):
    python -I -X utf8 pagina.py <cartella musei> <cartella milano-in-dati>

Legge musei/pulito/*.csv (da 05_pulisci.py e due tabelle a mano con le cifre citate da Regione Lombardia).
Scrive in docs/musei/data/: riepilogo.json + CSV con ';' e punto decimale.
"""
import csv
import json
import os
import shutil
import sys


def leggi(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def r1(x, d=1):
    return None if x is None else round(x, d)


def pct(a, b):
    return None if not b else (a / b - 1) * 100


def main(base, root):
    P = lambda n: os.path.join(base, "pulito", n)
    out = os.path.join(root, "docs", "musei", "data")
    os.makedirs(out, exist_ok=True)
    R = {"meta": {}}

    # ---------------- musei civici 2007-2017
    ann = leggi(P("civici_annuali.csv"))
    mens = leggi(P("civici_mensili.csv"))
    inc = leggi(P("civici_incassi.csv"))
    anni = list(range(2007, 2018))
    R["meta"]["anni_civici"] = anni
    musei = {}
    for x in ann:
        m = musei.setdefault(x["museo"], {"nome": x["museo"], "vis": {}, "mesi": {}, "ingresso": {}})
        a = int(x["anno"])
        m["vis"][a] = int(x["visitatori"])
        m["mesi"][a] = int(x["mesi_con_dato"])
        m["ingresso"][a] = x["ingresso"]
    for x in inc:
        musei[x["museo"]].setdefault("incasso", {})[int(x["anno"])] = int(x["incasso_euro"])
    NUOVI = ["Museo del Novecento", "Mudec"]
    lista = []
    for nome, m in sorted(musei.items(), key=lambda kv: -kv[1]["vis"].get(2017, 0)):
        lista.append({"nome": nome, "vis": [m["vis"].get(a) for a in anni], "mesi": [m["mesi"].get(a) for a in anni],
                      "ingresso": [m["ingresso"].get(a) for a in anni], "incasso": [m.get("incasso", {}).get(a) for a in anni]})
    tot = [sum(m["vis"].get(a, 0) for m in musei.values()) for a in anni]
    tot_old = [sum(v for n, m in musei.items() if n not in NUOVI for v in [m["vis"].get(a, 0)]) for a in anni]
    grat = [sum(m["vis"].get(a, 0) for m in musei.values() if m["ingresso"].get(a) == "Gratuito") for a in anni]
    pag = [sum(m["vis"].get(a, 0) for m in musei.values() if m["ingresso"].get(a) == "A pagamento") for a in anni]
    nd = [sum(m["vis"].get(a, 0) for m in musei.values() if m["ingresso"].get(a) not in ("Gratuito", "A pagamento")) for a in anni]
    incasso = [sum(m.get("incasso", {}).get(a, 0) for m in musei.values()) for a in anni]
    # mesi mancanti: museo-anno con meno di 12 mesi
    incompleti = [(n, a, m["mesi"][a]) for n, m in musei.items() for a in sorted(m["mesi"]) if m["mesi"][a] < 12]
    # stagionalita': quota di ogni mese sul totale annuo, solo museo-anni con 12 mesi, 2011-2017
    mes = {}
    for x in mens:
        mes[(x["museo"], int(x["anno"]), int(x["mese"]))] = int(x["visitatori"])
    sea = [0] * 12
    sea_a = {}
    for n, m in musei.items():
        for a in range(2011, 2018):
            if m["mesi"].get(a) == 12:
                for k in range(12):
                    sea[k] += mes[(n, a, k + 1)]
                    sea_a.setdefault(a, [0] * 12)[k] += mes[(n, a, k + 1)]
    st = sum(sea)
    R["civici"] = {"musei": lista, "totale": tot, "totale_senza_novecento_mudec": tot_old, "gratuiti": grat, "a_pagamento": pag,
                   "non_pervenuto": nd, "incasso": incasso, "incompleti": incompleti, "stagionalita_pct": [r1(v / st * 100, 2) for v in sea],
                   "nuovi": NUOVI}
    # i 10 mesi
    mm = {}
    for (n, a, k), v in mes.items():
        mm[(a, k)] = mm.get((a, k), 0) + v
    R["civici"]["mese_picco_2017"] = max(range(1, 13), key=lambda k: mm[(2017, k)])

    # ---------------- statali a Milano 1996-2024
    sm = leggi(P("statali_milano.csv"))
    ay = list(range(1996, 2025))
    R["meta"]["anni_statali"] = ay
    ST = {}
    for x in sm:
        ST.setdefault(x["museo"], {})[int(x["anno"])] = {k: (float(x[k]) if x[k] else None) for k in ("paganti", "non_paganti", "totale", "introiti_lordi_euro")}
    def serie(n, k):
        return [ST[n][a][k] if a in ST[n] else None for a in ay]
    stm = {}
    for n, key in (("Pinacoteca di Brera", "brera"), ("Cenacolo Vinciano", "cenacolo")):
        stm[key] = {"nome": n, "totale": serie(n, "totale"), "paganti": serie(n, "paganti"), "non_paganti": serie(n, "non_paganti"),
                    "introiti_lordi": serie(n, "introiti_lordi_euro")}
    n = "Antiquarium Alda Levi e Anfiteatro romano"
    stm["anfiteatro"] = {"nome": n, "totale": serie(n, "totale")}
    # incasso lordo per visitatore pagante (calcolo nostro, approssimato)
    for key in ("brera", "cenacolo"):
        s = stm[key]
        s["euro_per_pagante"] = [r1(i / p, 2) if (i and p) else None for i, p in zip(s["introiti_lordi"], s["paganti"])]
        s["quota_non_paganti_pct"] = [r1(np_ / t * 100, 1) if t else None for np_, t in zip(s["non_paganti"], s["totale"])]
    R["statali_milano"] = stm

    # ---------------- Italia (Tavola 1 MiC)
    it = leggi(P("statali_italia.csv"))
    ITA = {}
    for x in it:
        ITA.setdefault(x["sezione"], {})[int(x["anno"])] = x
    def sit(sez, k):
        return [float(ITA[sez][a][k]) if a in ITA[sez] else None for a in ay]
    R["italia"] = {"totale_visitatori": sit("TOTALE", "totale_visitatori"), "introiti_lordi": sit("TOTALE", "introiti_lordi_euro"),
                   "istituti": sit("TOTALE", "istituti"),
                   "musei_visitatori": sit("MUSEI", "totale_visitatori"), "monumenti_visitatori": sit("MONUMENTI E AREE ARCHEOLOGICHE", "totale_visitatori"),
                   "totale_paganti": [float(ITA["TOTALE"][a]["paganti"]) for a in ay], "totale_non_paganti_ist_pag": [float(ITA["TOTALE"][a]["non_paganti"]) for a in ay],
                   "visitatori_gratuiti_ist": sit("TOTALE", "visitatori_istituti_gratuiti")}
    # quota di milanesi (Brera + Cenacolo + Anfiteatro) sul totale Italia
    sum_mi = [sum(v for v in (stm["brera"]["totale"][i], stm["cenacolo"]["totale"][i], stm["anfiteatro"]["totale"][i]) if v) for i in range(len(ay))]
    R["statali_milano"]["somma_tre"] = sum_mi
    R["statali_milano"]["quota_su_italia_pct"] = [r1(s / t * 100, 2) if t else None for s, t in zip(sum_mi, R["italia"]["totale_visitatori"])]

    # ---------------- Covid: indici 2019 = 100
    i19 = ay.index(2019)
    def idx(s):
        return [r1(s[ay.index(a)] / s[i19] * 100, 1) if s[ay.index(a)] else None for a in range(2019, 2025)]
    R["covid"] = {"anni": list(range(2019, 2025)),
                  "brera": idx(stm["brera"]["totale"]), "cenacolo": idx(stm["cenacolo"]["totale"]),
                  "italia": idx(R["italia"]["totale_visitatori"]), "italia_musei": idx(R["italia"]["musei_visitatori"]),
                  "italia_monumenti": idx(R["italia"]["monumenti_visitatori"])}
    # civici milano: dati fino al 2017, nessun confronto 2019: quindi non nel grafico

    # ---------------- top 30 Italia 2024 e province
    top = leggi(P("mic_top30_2024.csv"))
    R["top30"] = [{"posto": int(x["posto"]), "istituto": x["istituto"], "comune": x["comune"], "visitatori": int(x["visitatori"]),
                   "introiti": float(x["introiti_lordi_euro"])} for x in top]
    prov = {x["provincia"]: x for x in leggi(P("mic_province_2024.csv"))}
    R["province_2024"] = {k: {"istituti": int(v["istituti"]), "totale": int(v["totale"]), "introiti": float(v["introiti_lordi_euro"])} for k, v in prov.items()}

    # ---------------- Regione Lombardia (cifre citate)
    rl = leggi(P("regione_lombardia_totali.csv"))
    R["lombardia"] = [{"anno": int(x["anno"]), "visitatori": int(x["visitatori_musei_riconosciuti_lombardia"]),
                       "risposto": int(x["istituti_che_hanno_risposto"]) if x["istituti_che_hanno_risposto"] else None,
                       "riconosciuti": int(x["istituti_riconosciuti"]) if x["istituti_riconosciuti"] else None,
                       "var_2019": float(x["variazione_su_2019_stessi_musei_pct"]) if x["variazione_su_2019_stessi_musei_pct"] else None} for x in rl]
    t10 = leggi(P("regione_lombardia_top10_2024.csv"))
    R["lombardia_top10_2024"] = [{"posto": int(x["posto"]), "museo": x["museo"], "comune": x["comune"], "visitatori": int(x["visitatori_2024"])} for x in t10]
    R["lombardia_top10_2024_milano_somma"] = sum(int(x["visitatori_2024"]) for x in t10 if x["comune"] == "Milano")

    # ---------------- cifre dichiarate dal Comune (stampa)
    R["comune_dichiarato"] = [
        {"anno": 2023, "valore": 3197477, "cosa": "visitatori di mostre e musei del Comune (musei + mostre)", "fonte": "Italpress, 19/1/2024 (conferenza stampa di sindaco e assessore alla Cultura)"},
        {"anno": 2024, "valore": 3000000, "cosa": "visitatori dei musei civici e delle mostre, stima di fine anno", "fonte": "ANSA, 18/12/2024 (assessore alla Cultura)"},
        {"anno": 2025, "valore": 1774510, "cosa": "visitatori dei musei civici (esclusa le mostre)", "fonte": "primo Annual Report della Direzione Cultura, riportato da Finestre sull'Arte, 29/6/2026"},
        {"anno": 2025, "valore": 949812, "cosa": "visitatori delle 72 mostre nelle sedi civiche", "fonte": "come sopra"},
        {"anno": 2025, "valore": 2724322, "cosa": "totale musei civici + mostre", "fonte": "come sopra"}]

    # ---------------- sorprese / numeri chiave
    b, c = stm["brera"], stm["cenacolo"]
    ix = lambda a: ay.index(a)
    S = {
        "brera_2019": b["totale"][ix(2019)], "brera_2020": b["totale"][ix(2020)], "brera_2024": b["totale"][ix(2024)],
        "cenacolo_2019": c["totale"][ix(2019)], "cenacolo_2020": c["totale"][ix(2020)], "cenacolo_2024": c["totale"][ix(2024)],
        "ita_2019": R["italia"]["totale_visitatori"][ix(2019)], "ita_2020": R["italia"]["totale_visitatori"][ix(2020)], "ita_2024": R["italia"]["totale_visitatori"][ix(2024)],
        "brera_var_2020": r1(pct(b["totale"][ix(2020)], b["totale"][ix(2019)])), "cenacolo_var_2020": r1(pct(c["totale"][ix(2020)], c["totale"][ix(2019)])),
        "ita_var_2020": r1(pct(R["italia"]["totale_visitatori"][ix(2020)], R["italia"]["totale_visitatori"][ix(2019)])),
        "brera_var_2024": r1(pct(b["totale"][ix(2024)], b["totale"][ix(2019)])), "cenacolo_var_2024": r1(pct(c["totale"][ix(2024)], c["totale"][ix(2019)])),
        "ita_var_2024": r1(pct(R["italia"]["totale_visitatori"][ix(2024)], R["italia"]["totale_visitatori"][ix(2019)])),
        "cenacolo_introiti_2010": c["introiti_lordi"][ix(2010)], "cenacolo_introiti_2024": c["introiti_lordi"][ix(2024)],
        "cenacolo_vis_2010": c["totale"][ix(2010)], "cenacolo_vis_2024": c["totale"][ix(2024)],
        "cenacolo_euro_pagante_2010": c["euro_per_pagante"][ix(2010)], "cenacolo_euro_pagante_2024": c["euro_per_pagante"][ix(2024)],
        "brera_non_paganti_2024": b["quota_non_paganti_pct"][ix(2024)], "brera_non_paganti_2019": b["quota_non_paganti_pct"][ix(2019)],
        "cenacolo_non_paganti_2024": c["quota_non_paganti_pct"][ix(2024)], "brera_non_paganti_1996": b["quota_non_paganti_pct"][ix(1996)],
        "brera_non_paganti_2020": b["quota_non_paganti_pct"][ix(2020)],
        "civici_2007": tot[0], "civici_2017": tot[-1], "civici_var_07_17": r1(pct(tot[-1], tot[0])),
        "civici_senza_nuovi_2007": tot_old[0], "civici_senza_nuovi_2017": tot_old[-1], "civici_senza_nuovi_var": r1(pct(tot_old[-1], tot_old[0])),
        "milano_quota_ita_2019": R["statali_milano"]["quota_su_italia_pct"][ix(2019)], "milano_quota_ita_2024": R["statali_milano"]["quota_su_italia_pct"][ix(2024)],
        "posto_brera_top30": next(x["posto"] for x in R["top30"] if x["istituto"] == "Pinacoteca di Brera"),
        "posto_cenacolo_top30": next(x["posto"] for x in R["top30"] if x["istituto"] == "Cenacolo Vinciano"),
        "ita_non_paganti_quota_2024": r1(sum_non(R, ay.index(2024)), 1), "ita_non_paganti_quota_2019": r1(sum_non(R, ay.index(2019)), 1),
        "civici_gratuiti_quota_2017": r1(grat[-1] / tot[-1] * 100, 1), "civici_gratuiti_quota_2007": r1(grat[0] / tot[0] * 100, 1),
    }
    # quanta parte della crescita 2007-2017 viene dai due musei nuovi
    S["civici_crescita_da_nuovi_pct"] = r1((tot[-1] - tot[0] - (tot_old[-1] - tot_old[0])) / (tot[-1] - tot[0]) * 100, 0)
    R["sorprese"] = S

    # ---------------- file per il download
    shutil.copy(P("civici_annuali.csv"), os.path.join(out, "civici_per_museo_anno.csv"))
    shutil.copy(P("civici_mensili.csv"), os.path.join(out, "civici_mensili.csv"))
    shutil.copy(P("statali_milano.csv"), os.path.join(out, "statali_milano_1996_2024.csv"))
    shutil.copy(P("statali_italia.csv"), os.path.join(out, "statali_italia_1996_2024.csv"))
    shutil.copy(P("mic_top30_2024.csv"), os.path.join(out, "mic_top30_2024.csv"))
    shutil.copy(P("regione_lombardia_totali.csv"), os.path.join(out, "lombardia_totali_citati.csv"))
    with open(os.path.join(out, "riepilogo.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, separators=(",", ":"))
    print("scritto", out)
    print(json.dumps(S, ensure_ascii=False, indent=1))


def sum_non(R, i):
    """quota (%) dei non paganti sul totale dei visitatori degli istituti a pagamento, Italia"""
    pag = R["italia"]["totale_paganti"][i]
    non = R["italia"]["totale_non_paganti_ist_pag"][i]
    return non / (pag + non) * 100


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
