# -*- coding: utf-8 -*-
"""
Pagina "Quanto aspetti alla fermata", docs/attesa-fermata/.
Legge il GTFS del trasporto pubblico di Milano (Comune di Milano / AMAT, dataset ds929, CC BY 4.0;
copia gia' scaricata il 29/10/2026 in bici-auto-mezzi/raw/gtfs/ext_comune_new/) e calcola, per un giorno
feriale tipo (quello con piu' corse tra martedi, mercoledi e giovedi del feed):
  - per ogni linea (metro, tram, bus, filobus): corse per ora e attesa media programmata (60 / corse per ora
    per direzione) ora per ora;
  - per ogni quartiere (NIL): partenze da tutte le fermate dentro il quartiere, ora per ora, e per 1.000 residenti;
    con le fermate contate e la quota di partenze serali (21-24) rispetto alla punta (7-9).
Scrive docs/attesa-fermata/data/fermate.json e due CSV scaricabili.
Uso: python genera_a4_fermate.py
"""
import csv, json, os, sys, collections, datetime

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(QUI))
GTFS = os.path.join(RADICE, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new")
NIL_GEO = os.path.join(RADICE, "docs", "quartiere", "data", "nil.geojson")
SCHEDE = os.path.join(RADICE, "docs", "quartiere", "data", "schede.json")
OUT = os.path.join(RADICE, "docs", "attesa-fermata", "data")
OUT_JSON = os.path.join(OUT, "fermate.json")
GIORNO_FISSO = "20261124"   # martedi 24 novembre 2026

csv.field_size_limit(10**9)


def leggi(nome):
    with open(os.path.join(GTFS, nome), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def punto_in_poligono(x, y, anello):
    dentro = False
    n = len(anello)
    j = n - 1
    for i in range(n):
        xi, yi = anello[i]
        xj, yj = anello[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            dentro = not dentro
        j = i
    return dentro


def main():
    # 1. giorno di riferimento: un martedi/mercoledi/giovedi con il massimo di servizi attivi
    cal = leggi("calendar_dates.txt")
    per_data = collections.defaultdict(set)
    for r in cal:
        if r["exception_type"] == "1":
            per_data[r["date"]].add(r["service_id"])
    candidati = []
    for d, s in per_data.items():
        wd = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday()
        if wd in (1, 2, 3):
            candidati.append((len(s), d))
    candidati.sort(reverse=True)
    n_serv, giorno = candidati[0]
    if giorno != GIORNO_FISSO:
        print("ATTENZIONE: il giorno con piu' servizi e'", giorno, "non", GIORNO_FISSO)
    giorno = GIORNO_FISSO
    servizi = per_data[giorno]
    n_serv = len(servizi)
    print("giorno di riferimento", giorno, "servizi attivi", n_serv)

    # 2. linee e corse di quel giorno
    rotte = {r["route_id"]: r for r in leggi("routes.txt")}
    tipo_nome = {"0": "tram", "1": "metro", "3": "bus"}
    corse = {}
    for t in leggi("trips.txt"):
        if t["service_id"] in servizi:
            corse[t["trip_id"]] = (t["route_id"], t["direction_id"] or "0")
    print("corse attive", len(corse))

    # 3. fermate -> quartiere
    with open(NIL_GEO, encoding="utf-8") as f:
        nil = json.load(f)
    poligoni = []
    for ft in nil["features"]:
        g = ft["geometry"]
        anelli = g["coordinates"] if g["type"] == "Polygon" else [p for mp in g["coordinates"] for p in mp]
        for an in anelli[:1] if g["type"] == "Polygon" else anelli:
            xs = [p[0] for p in an]; ys = [p[1] for p in an]
            poligoni.append((ft["properties"]["i"], ft["properties"]["n"], an, min(xs), max(xs), min(ys), max(ys)))
    fermate = leggi("stops.txt")
    fermata_nil = {}
    for s in fermate:
        if s.get("location_type") not in ("", "0", None):
            continue
        x, y = float(s["stop_lon"]), float(s["stop_lat"])
        for i, n, an, x0, x1, y0, y1 in poligoni:
            if x0 <= x <= x1 and y0 <= y <= y1 and punto_in_poligono(x, y, an):
                fermata_nil[s["stop_id"]] = i
                break
    print("fermate dentro Milano", len(fermata_nil), "su", len(fermate))

    # 4. stop_times: partenze per ora
    ore_linea = collections.defaultdict(lambda: collections.Counter())   # (route, dir) -> ora -> partenze al capolinea (sequenza 1)
    ore_nil = collections.defaultdict(lambda: collections.Counter())     # nil -> ora -> partenze
    fermate_nil_usate = collections.defaultdict(set)
    linee_nil = collections.defaultdict(set)
    n_righe = 0
    with open(os.path.join(GTFS, "stop_times.txt"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            n_righe += 1
            c = corse.get(r["trip_id"])
            if not c:
                continue
            ora = int(r["departure_time"][:2]) % 24
            if r["stop_sequence"] == "1":
                ore_linea[c][ora] += 1
            i = fermata_nil.get(r["stop_id"])
            if i is not None:
                ore_nil[i][ora] += 1
                fermate_nil_usate[i].add(r["stop_id"])
                linee_nil[i].add(c[0])
    print("righe stop_times lette", n_righe)

    # 5. per linea: partenze dal capolinea per ora, in tutte le direzioni. Per il metro il campo direction_id
    #    e' vuoto, quindi la regola e' la stessa per tutti: corse in una direzione = totale / 2
    #    (ogni linea ha due versi di marcia; le linee a rami, come la M1 e la M2, sono contate sul tronco comune).
    linee = {}
    for (rid, d), cnt in ore_linea.items():
        linee.setdefault(rid, collections.Counter()).update(cnt)
    out_linee = []
    for rid, cnt in linee.items():
        r = rotte.get(rid, {})
        tipo = tipo_nome.get(r.get("route_type", ""), "altro")
        ore = [round(cnt.get(h, 0) / 2.0, 1) for h in range(24)]
        tot = sum(cnt.values())
        out_linee.append({
            "id": rid, "n": r.get("route_short_name", rid), "nome": r.get("route_long_name", ""),
            "tipo": tipo, "corse": tot, "ore": ore,
        })
    ordine = {"metro": 0, "tram": 1, "bus": 2, "altro": 3}
    out_linee.sort(key=lambda l: (ordine[l["tipo"]], (int(''.join(ch for ch in l["n"] if ch.isdigit()) or 0), l["n"])))

    # 6. per quartiere
    with open(SCHEDE, encoding="utf-8") as f:
        sch = json.load(f)
    residenti = {q["id"]: q["residenti"] for q in sch["nil"]}
    nomi = {q["id"]: q["nome"] for q in sch["nil"]}
    out_nil = []
    for i in sorted(nomi):
        cnt = ore_nil.get(i, collections.Counter())
        ore = [cnt.get(h, 0) for h in range(24)]
        tot = sum(ore)
        res = residenti.get(i, 0)
        punta = sum(ore[7:10]) / 3.0
        sera = sum(ore[21:24]) / 3.0
        out_nil.append({
            "id": i, "nome": nomi[i], "residenti": res, "fermate": len(fermate_nil_usate.get(i, ())),
            "linee": len(linee_nil.get(i, ())), "ore": ore, "tot": tot,
            "per_1000": round(tot / res * 1000, 1) if res else None,
            "sera_su_punta": round(sera / punta, 2) if punta else None,
        })

    dati = {
        "generato": datetime.date.today().isoformat(),
        "giorno": giorno, "servizi": n_serv, "corse": len(corse),
        "fonte": "Comune di Milano, dati.comune.milano.it, dataset ds929 (orari del trasporto pubblico in formato GTFS, prodotto da AMAT su dati ATM), CC BY 4.0; copia scaricata il 29/10/2026, feed del 26/10/2026",
        "linee": out_linee, "quartieri": out_nil,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(OUT, "linee_corse_per_ora.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_linea", "tipo", "numero", "nome", "corse_nel_giorno_due_versi"] + ["ora_%02d" % h for h in range(24)])
        for l in out_linee:
            w.writerow([l["id"], l["tipo"], l["n"], l["nome"], l["corse"]] + [str(x).replace(".", ",") for x in l["ore"]])
    with open(os.path.join(OUT, "quartieri_passaggi_per_ora.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_nil", "quartiere", "residenti", "fermate", "linee", "passaggi_nel_giorno", "passaggi_ogni_1000_residenti", "sera_su_punta"] + ["ora_%02d" % h for h in range(24)])
        for q in out_nil:
            w.writerow([q["id"], q["nome"], q["residenti"], q["fermate"], q["linee"], q["tot"],
                        "" if q["per_1000"] is None else str(q["per_1000"]).replace(".", ","),
                        "" if q["sera_su_punta"] is None else str(q["sera_su_punta"]).replace(".", ",")] + q["ore"])
    print("scritto", OUT_JSON)


if __name__ == "__main__":
    main()
