# -*- coding: utf-8 -*-
"""
Pagina "Milano per chilometri dal Duomo", docs/chilometri-duomo/.
Incrocio di pagine gia' pronte: ogni quartiere (NIL) viene messo alla sua distanza dal Duomo (dal centro del
suo confine, docs/quartiere/data/nil.geojson) e i valori della scheda del quartiere (schede.json) vengono
riassunti per fasce di 2 km, pesando ogni quartiere con i suoi residenti. In piu':
  - la speranza di vita per quartiere (docs/speranza-vita/data/nil_finestre.csv, ultima finestra, uomini e donne);
  - il suolo cementato per anelli di 1 km (docs/suolo/data/anelli_duomo.csv, ISPRA), gia' calcolato dal sito.
Scrive dati/a3_chilometri.json e, se c'e' il modello, la bozza a3-chilometri-dal-duomo.html.
"""
import csv, json, os, math, datetime

QUI = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(QUI))
D = os.path.join(R, "docs")
OUT = os.path.join(D, "chilometri-duomo", "data")
OUT_JSON = os.path.join(OUT, "chilometri.json")
DUOMO = (45.4641, 9.1919)
FASCE = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 99)]
INDICATORI = ["eta_media", "quota_65", "stranieri", "laureati", "famiglie_sole", "reddito", "prezzo_vendita",
              "var_prezzo", "airbnb", "aler", "nuove_case", "c15_metro", "c15_parchi", "alberi", "suolo", "locali",
              "affluenza21", "botteghe", "pietre", "antenne"]


def distanza_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def centroide(anello):
    a = 0.0; cx = 0.0; cy = 0.0
    for i in range(len(anello) - 1):
        x0, y0 = anello[i]; x1, y1 = anello[i + 1]
        f = x0 * y1 - x1 * y0
        a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    a *= 0.5
    return cx / (6 * a), cy / (6 * a), abs(a)


def main():
    with open(os.path.join(D, "quartiere", "data", "schede.json"), encoding="utf-8") as f:
        s = json.load(f)
    with open(os.path.join(D, "quartiere", "data", "nil.geojson"), encoding="utf-8") as f:
        geo = json.load(f)
    dist = {}
    for ft in geo["features"]:
        g = ft["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        best = max((centroide(p[0]) for p in polys), key=lambda t: t[2])
        dist[ft["properties"]["i"]] = round(distanza_km(DUOMO, (best[1], best[0])), 2)

    ind = {i["id"]: i for i in s["indicatori"]}
    # speranza di vita: ultima finestra
    sv = {}
    righe = []
    with open(os.path.join(D, "speranza-vita", "data", "nil_finestre.csv"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            righe.append(r)
    ultima = max(r["finestra"] for r in righe)
    for r in righe:
        if r["finestra"] == ultima and r["e0"] and r.get("piccolo_sotto_3000") != "True":
            try:
                e0 = float(r["e0"].replace(",", "."))
            except ValueError:
                continue
            if 60 < e0 < 100:  # scarta valori non finiti o assurdi dei quartieri con pochissimi decessi
                sv.setdefault(int(r["id_nil"]), {})[r["sesso"]] = e0

    quartieri = []
    for q in s["nil"]:
        v = s["valori"].get(str(q["id"]), {})
        row = {"id": q["id"], "nome": q["nome"], "res": q["residenti"], "km": dist.get(q["id"]), "piccolo": q["piccolo"], "v": {}}
        for k in INDICATORI:
            x = v.get(k)
            if x and isinstance(x.get("v"), (int, float)):
                row["v"][k] = x["v"]
        if q["id"] in sv:
            if "F" in sv[q["id"]]: row["v"]["vita_f"] = round(sv[q["id"]]["F"], 1)
            if "M" in sv[q["id"]]: row["v"]["vita_m"] = round(sv[q["id"]]["M"], 1)
        quartieri.append(row)

    indicatori = []
    for k in INDICATORI:
        i = ind[k]
        indicatori.append({"id": k, "et": i["et"], "unita": i.get("unita"), "fmt": i.get("fmt"), "dec": i.get("dec"),
                           "tema": i.get("tema"), "citta": i.get("citta"), "ref": i.get("ref"), "tipo": i.get("tipo"), "anno": i.get("anno"), "pagina": i.get("pagina"), "nota": i.get("nota")})
    indicatori.append({"id": "vita_f", "et": "Speranza di vita alla nascita, donne", "unita": "anni", "fmt": "dec", "dec": 1,
                       "tema": "Chi ci abita", "citta": None, "anno": ultima, "pagina": "speranza-vita",
                       "nota": "Stima dai decessi %s; i quartieri piccoli hanno intervalli larghi." % ultima})
    indicatori.append({"id": "vita_m", "et": "Speranza di vita alla nascita, uomini", "unita": "anni", "fmt": "dec", "dec": 1,
                       "tema": "Chi ci abita", "citta": None, "anno": ultima, "pagina": "speranza-vita",
                       "nota": "Stima dai decessi %s; i quartieri piccoli hanno intervalli larghi." % ultima})

    # fasce: media pesata con i residenti
    fasce = []
    for a, b in FASCE:
        qs = [q for q in quartieri if q["km"] is not None and a <= q["km"] < b]
        f = {"da": a, "a": (b if b < 99 else None), "n": len(qs), "res": sum(q["res"] for q in qs), "nomi": [q["nome"] for q in sorted(qs, key=lambda q: q["km"])], "v": {}}
        for i in indicatori:
            k = i["id"]
            coppie = [(q["v"][k], q["res"]) for q in qs if k in q["v"] and q["res"]]
            if coppie:
                w = sum(r for _, r in coppie)
                f["v"][k] = round(sum(x * r for x, r in coppie) / w, 2)
        fasce.append(f)

    anelli = []
    with open(os.path.join(D, "suolo", "data", "anelli_duomo.csv"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            anelli.append({"anello": r["anello_km_dal_duomo"], "pct_2025": float(r["pct_2025"]), "nuovo_ha": float(r["nuovo_2012_2025_ha"]), "area_ha": float(r["area_ha"])})

    dati = {"generato": datetime.date.today().isoformat(), "duomo": DUOMO, "indicatori": indicatori, "quartieri": quartieri,
            "fasce": fasce, "suolo_anelli": anelli,
            "fonte": "Valori della pagina Il tuo quartiere (schede.json), speranza di vita dalla pagina Speranza di vita, suolo per anelli dalla pagina Suolo (ISPRA). La distanza e' quella del centro geometrico del quartiere dal Duomo."}
    os.makedirs(OUT, exist_ok=True)
    js = json.dumps(dati, ensure_ascii=False, separators=(",", ":"))
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        f.write(js)
    ids = [i["id"] for i in indicatori]
    def nf(x):
        return str(x).replace(".", ",")
    with open(os.path.join(OUT, "fasce_2km.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["fascia_km", "quartieri", "residenti"] + ids)
        for fa in fasce:
            nome = ("%d-%d" % (fa["da"], fa["a"])) if fa["a"] else "oltre %d" % fa["da"]
            w.writerow([nome, fa["n"], fa["res"]] + [nf(fa["v"].get(k, "")) for k in ids])
    with open(os.path.join(OUT, "quartieri_distanza.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_nil", "quartiere", "residenti", "km_dal_duomo"] + ids)
        for q in quartieri:
            w.writerow([q["id"], q["nome"], q["res"], nf(q["km"])] + [nf(q["v"].get(k, "")) for k in ids])
    with open(os.path.join(OUT, "misure.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "misura", "unita", "anno", "valore_citta"])
        for i in indicatori:
            w.writerow([i["id"], i["et"], i["unita"] or "", i["anno"] or "", "" if i["citta"] is None else nf(i["citta"])])
    for f_ in fasce:
        print(f_["da"], f_["a"], f_["n"], f_["res"], {k: f_["v"].get(k) for k in ("reddito", "stranieri", "eta_media", "vita_f")})


if __name__ == "__main__":
    main()
