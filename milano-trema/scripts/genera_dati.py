# -*- coding: utf-8 -*-
"""
Pagina "Quante volte Milano ha tremato" (docs/milano-trema/).
Fonte: INGV, DBMI15 v4.0 (Database Macrosismico Italiano), licenza CC BY 4.0,
https://emidius.mi.ingv.it/CPTI15-DBMI15/  (file DBMI15_v4.0.xlsx, scaricato il 5/11/2026).
Dal file intero (123.981 osservazioni in tutta Italia) sono state estratte le righe con localita' "Milano":
milano-trema/dati/dbmi15_v4_milano.csv. Ogni riga e' un terremoto e l'intensita' con cui e' stato sentito a Milano
(scala Mercalli-Cancani-Sieberg: 2 appena avvertito, 3 lieve, 4 moderato, 5 forte, 6 danni leggeri, 7 danni).
Scrive in docs/milano-trema/data/: terremoti.json (letto dalla pagina), terremoti.csv (file scaricabile con parole al posto delle sigle)
e una copia del file di partenza.
Uso:  python milano-trema/scripts/genera_dati.py
"""
import csv, json, os, shutil, datetime

QUI = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(QUI))
IN = os.path.join(R, "milano-trema", "dati", "dbmi15_v4_milano.csv")
OUT = os.path.join(R, "docs", "milano-trema", "data")

# sigle del database: in parole semplici
SIGLE = {"NF": "non sentito", "NC": "non classificato", "F": "sentito, grado non indicato", "SF": "appena sentito",
         "HF": "sentito forte", "SD": "danni leggeri", "D": "danni, grado non indicato", "HD": "danni gravi, grado non indicato",
         "G": "notizia di danni"}


def parole(s):
    """Intensita' in parole: '5-6' -> 'grado 5-6'; sigla -> sua spiegazione."""
    if s in SIGLE:
        return SIGLE[s]
    return "grado " + s if s else ""


def main():
    eventi = []
    with open(IN, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["MDPplaceName"] != "Milano":
                continue
            num = float(r["MDPintNum"]) if r["MDPintNum"] else None
            eventi.append({
                "anno": int(r["Year"]), "mese": int(r["Mo"]) if r["Mo"] else None, "giorno": int(r["Da"]) if r["Da"] else None,
                "ora": int(r["Ho"]) if r["Ho"] else None, "min": int(r["Mi"]) if r["Mi"] else None,
                "zona": r["Ax"],
                "epic": r["Imax"], "epic_num": float(r["ImaxNum"]) if r["ImaxNum"] else None, "epic_parole": parole(r["Imax"]),
                "milano": r["MDPint"], "milano_num": num, "milano_parole": parole(r["MDPint"]),
                "n_localita": int(r["MdpN"]) if r["MdpN"] else None,
            })
    eventi.sort(key=lambda e: (e["anno"], e["mese"] or 0, e["giorno"] or 0))
    secoli = {}
    for e in eventi:
        s = (e["anno"] - 1) // 100 + 1
        c = secoli.setdefault(s, {"n": 0, "sentiti_4piu": 0, "danni": 0})
        c["n"] += 1
        if e["milano_num"] is not None and e["milano_num"] >= 4: c["sentiti_4piu"] += 1
        if e["milano_num"] is not None and e["milano_num"] >= 6: c["danni"] += 1
    forti = sorted([e for e in eventi if e["milano_num"]], key=lambda e: -e["milano_num"])[:10]
    dati = {
        "generato": datetime.date.today().isoformat(), "n": len(eventi), "primo": eventi[0]["anno"], "ultimo": eventi[-1]["anno"],
        "secoli": [{"secolo": k, **v} for k, v in sorted(secoli.items())], "piu_forti": forti, "eventi": eventi,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "terremoti.json"), "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "terremoti.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["anno", "mese", "giorno", "ora", "minuto", "area_di_origine", "grado_a_milano", "a_milano_in_parole",
                    "grado_all_epicentro", "all_epicentro_in_parole", "localita_dove_e_stato_osservato"])
        for e in eventi:
            w.writerow([e["anno"], e["mese"] or "", e["giorno"] or "", "" if e["ora"] is None else e["ora"], "" if e["min"] is None else e["min"],
                        e["zona"], e["milano"], e["milano_parole"], e["epic"], e["epic_parole"], e["n_localita"] or ""])
    shutil.copyfile(IN, os.path.join(OUT, "dbmi15_v4_milano.csv"))
    print("terremoti", len(eventi), "dal", eventi[0]["anno"], "al", eventi[-1]["anno"])


if __name__ == "__main__":
    main()
