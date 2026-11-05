# -*- coding: utf-8 -*-
"""
Pagina "Indovina il quartiere" (gioco), docs/indovina-quartiere/.
Prende dalla scheda del quartiere (docs/quartiere/data/schede.json) gli 88 quartieri con una ventina di
indicatori che fanno da indizi, e dai confini (docs/quartiere/data/nil.geojson) il centro di ogni quartiere,
per dire a chi sbaglia in che direzione e a quanti chilometri sta il quartiere giusto.
Scrive docs/indovina-quartiere/data/indovina.json (per la pagina) e due CSV scaricabili.
Il riferimento "tutta Milano" ha la sua etichetta vera (campo ref di schede.json): per alcuni indicatori
e' la mediana dei quartieri, non il valore dell'intera citta'.
"""
import json, os, math, datetime, csv

QUI = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(QUI))
D = os.path.join(R, "docs")
OUT = os.path.join(D, "indovina-quartiere", "data")
OUT_JSON = os.path.join(OUT, "indovina.json")

INDIZI = ["residenti", "eta_media", "stranieri", "prezzo_vendita", "reddito", "alberi", "affluenza21", "locali",
          "famiglie_sole", "airbnb", "laureati", "c15_metro", "suolo", "botteghe", "aree_cani", "quota_65", "var_prezzo",
          "nuove_case", "biblioteche", "c15_parchi", "notte_calda", "alunni_var", "pietre", "aler"]


def centroide(anello):
    # centroide di un poligono (formula dell'area con segno), in gradi
    a = 0.0; cx = 0.0; cy = 0.0
    for i in range(len(anello) - 1):
        x0, y0 = anello[i]; x1, y1 = anello[i + 1]
        f = x0 * y1 - x1 * y0
        a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    if abs(a) < 1e-12:
        xs = [p[0] for p in anello]; ys = [p[1] for p in anello]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), abs(a)


def main():
    with open(os.path.join(D, "quartiere", "data", "schede.json"), encoding="utf-8") as f:
        s = json.load(f)
    with open(os.path.join(D, "quartiere", "data", "nil.geojson"), encoding="utf-8") as f:
        geo = json.load(f)
    centri = {}
    anelli = {}
    for ft in geo["features"]:
        g = ft["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        best = None
        for p in polys:
            x, y, a = centroide(p[0])
            if best is None or a > best[2]:
                best = (x, y, a)
        i = ft["properties"]["i"]
        centri[i] = [round(best[1], 5), round(best[0], 5)]
        # anello semplificato per una mappina (un punto ogni 4)
        ring = max(polys, key=lambda p: len(p[0]))[0]
        anelli[i] = [[round(p[1], 4), round(p[0], 4)] for p in ring[::4]]

    ind = {i["id"]: i for i in s["indicatori"]}
    indicatori = []
    for k in INDIZI:
        if k not in ind:
            print("manca indicatore", k); continue
        i = ind[k]
        indicatori.append({"id": k, "et": i["et"], "unita": i.get("unita"), "fmt": i.get("fmt"), "dec": i.get("dec"),
                           "tema": i.get("tema"), "citta": i.get("citta"), "ref": i.get("ref"), "tipo": i.get("tipo"), "min": i.get("min"), "max": i.get("max"),
                           "n": i.get("n"), "anno": i.get("anno"), "nota": i.get("nota")})
    quartieri = []
    for q in s["nil"]:
        v = s["valori"].get(str(q["id"]), {})
        vals = {}
        for k in INDIZI:
            x = v.get(k)
            if x is None:
                continue
            vals[k] = {"v": x.get("v"), "r": x.get("r")}
            if x.get("x") is not None:
                vals[k]["x"] = x["x"]
        quartieri.append({"id": q["id"], "nome": q["nome"], "municipio": q["municipio"], "residenti": q["residenti"],
                          "piccolo": q["piccolo"], "quasi_vuoto": q.get("quasi_vuoto", False),
                          "c": centri.get(q["id"]), "anello": anelli.get(q["id"]), "v": vals})
    dati = {"generato": datetime.date.today().isoformat(), "indicatori": indicatori, "quartieri": quartieri,
            "n_nil": s.get("n_nil")}
    os.makedirs(OUT, exist_ok=True)
    js = json.dumps(dati, ensure_ascii=False, separators=(",", ":"))
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(OUT, "indizi_indicatori.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "indicatore", "unita", "anno", "quartieri_in_classifica", "riferimento_valore", "riferimento_tipo", "nota"])
        for i in indicatori:
            w.writerow([i["id"], i["et"], i["unita"] or "", i["anno"] or "", i["n"] or "", "" if i["citta"] is None else i["citta"], i["ref"] or "", i["nota"] or ""])
    with open(os.path.join(OUT, "indizi_quartieri.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_nil", "quartiere", "municipio", "residenti_totali", "pochi_residenti"] + INDIZI)
        for q in quartieri:
            w.writerow([q["id"], q["nome"], q["municipio"], q["residenti"], "si" if q["piccolo"] else "no"] +
                       ["" if q["v"].get(k) is None else q["v"][k]["v"] for k in INDIZI])
    print("quartieri", len(quartieri), "indicatori", len(indicatori), len(js) // 1024, "KB")


if __name__ == "__main__":
    main()
