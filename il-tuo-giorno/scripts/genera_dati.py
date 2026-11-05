# -*- coding: utf-8 -*-
"""
Pagina "Il tuo giorno a Milano" (docs/il-tuo-giorno/).
La pagina carica a richiesta i file gia' presenti nel sito (temperature/data/giorni.json, scala/data/serate/<decennio>.json,
derby/data/derby.csv, amministratori/data/sindaci_milano.csv, morti/data/milano_giorno.csv, area-c/data/giorni.json)
e due file propri, scritti da questo programma in docs/il-tuo-giorno/data/:
  - temperature.json : per ogni anno dal 1763, minima e massima di Brera giorno per giorno in forma compatta
    (serve per dire "il 12 piu' caldo su 260 anni": servono tutti gli anni dello stesso giorno);
  - elezioni.json : data -> elenco delle elezioni tenute quel giorno;
  - temperature_brera_giornaliere.csv : le stesse temperature, file scaricabile.
Uso:  python il-tuo-giorno/scripts/genera_dati.py
"""
import csv, json, os, datetime, calendar

QUI = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(QUI))
D = os.path.join(R, "docs")
OUT = os.path.join(D, "il-tuo-giorno", "data")

ALF = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def cod(v):
    """decimi di grado + 600, in base 64 su 2 caratteri; '__' = manca"""
    if v is None:
        return "__"
    n = max(0, min(4000, v + 600))
    return ALF[n // 64] + ALF[n % 64]


def main():
    os.makedirs(OUT, exist_ok=True)
    anni = {}
    n_ok = 0
    righe_csv = []
    with open(os.path.join(R, "temperature", "serie", "serie_unica_corretta.csv"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            d = datetime.date.fromisoformat(r["date"])
            a = anni.setdefault(d.year, [None] * 366)
            doy = d.timetuple().tm_yday - 1
            if not calendar.isleap(d.year) and doy >= 59:  # il 29 febbraio ha sempre l'indice 59
                doy += 1
            if r["tmin"] and r["tmax"]:
                a[doy] = [round(float(r["tmin"]) * 10), round(float(r["tmax"]) * 10)]
                n_ok += 1
                righe_csv.append((r["date"], r["tmin"], r["tmax"]))
    temps = {str(a): "".join(cod(g[0]) + cod(g[1]) if g else "____" for g in v) for a, v in sorted(anni.items())}
    with open(os.path.join(OUT, "temperature.json"), "w", encoding="utf-8") as f:
        json.dump({"anno_min": min(anni), "anno_max": max(anni), "temps": temps}, f, separators=(",", ":"))
    with open(os.path.join(OUT, "temperature_brera_giornaliere.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "minima_gradi", "massima_gradi"])
        w.writerows(righe_csv)
    with open(os.path.join(D, "elezioni", "data", "index.json"), encoding="utf-8") as f:
        idx = json.load(f)
    etichette = {t["id"]: t["label"] for t in idx.get("tipi", [])}
    el = {}
    for e in idx.get("elezioni", []):
        if not e.get("data"):
            continue
        et = e.get("label") or etichette.get(e.get("tipo"), e.get("tipo"))
        if et not in el.setdefault(e["data"], []):
            el[e["data"]].append(et)
    with open(os.path.join(OUT, "elezioni.json"), "w", encoding="utf-8") as f:
        json.dump(el, f, ensure_ascii=False, separators=(",", ":"))
    print("giorni con temperatura", n_ok, "anni", len(anni), "date con elezioni", len(el))


if __name__ == "__main__":
    main()
