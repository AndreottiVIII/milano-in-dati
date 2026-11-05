"""Dati dei quattro grafici della pagina docs/scala/ (orari d'inizio, ritorno dei titoli d'opera, compositori per decennio).
Uso (da qualsiasi cartella):   python -I -X utf8 scripts/pagina_grafici.py
Legge:  ../docs/scala/data/serate/*.json  (una riga per recita)
Scrive: ../docs/scala/data/grafici.json
Viene lanciato anche da pagina_dati.py, cosi' il file resta allineato ai dati delle serate.
Riga di una serata: [AAAAMMGG, HHMM, tipo, titolo, autore, altri, sala, direttore, bambini, fonte].
Il grafico dei prezzi (poltrona / biglietto meno caro) si calcola nella pagina da serate/riepilogo.json: qui non serve."""
import os, json, glob, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "docs", "scala", "data")
SER = os.path.join(OUT, "serate")


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(SER, "*.json"))):
        if "riepilogo" in f:
            continue
        rows += json.load(open(f, encoding="utf-8"))
    yr = lambda r: int(r[0][:4])
    dec = lambda r: r[0][:3] + "0"

    # ---- orario d'inizio: serate dalle 18 in poi, dal 1944
    cod = ["p20", "2000", "2030", "2045", "2100", "2115"]   # prima delle 20, 20:00, 20:30, 20:45, 21:00, 21:15 o dopo

    def banda(h):
        return cod[0] if h < "2000" else cod[1] if h < "2030" else cod[2] if h < "2045" else cod[3] if h < "2100" else cod[4] if h < "2115" else cod[5]

    sera = [r for r in rows if r[1] and r[1] >= "1800" and yr(r) >= 1944]
    per = collections.defaultdict(collections.Counter)
    for r in sera:
        per[yr(r)][banda(r[1])] += 1
    anni = sorted(per)
    q = lambda y, k: 100 * per[y][k] / sum(per[y].values())
    senza_ora = [r for r in rows if not r[1]]
    sip = dict(
        anni=anni, bande=cod, conteggi=[[per[y][k] for k in cod] for y in anni],
        serate=len(sera), prima_delle_18=sum(1 for r in rows if r[1] and r[1] < "1800"), senza_ora=len(senza_ora),
        senza_ora_dal=min((yr(r) for r in senza_ora), default=None), senza_ora_fino=max((yr(r) for r in senza_ora), default=None),
        senza_ora_da_2024=sum(1 for r in senza_ora if yr(r) >= 2024),
        ultimo_21=max(y for y in anni if q(y, "2100") + q(y, "2115") > 50),
        primo_2030=min(y for y in anni if q(y, "2030") > 50),
        primo_2000=min(y for y in anni if q(y, "2000") > 50),
        poche=[y for y in anni if sum(per[y].values()) < 60],
    )

    # ---- ritorno dei titoli d'opera
    op = [r for r in rows if r[2] == "O"]
    anni_t, rec_t = collections.defaultdict(set), collections.Counter()
    for r in op:
        anni_t[r[3]].add(yr(r)); rec_t[r[3]] += 1
    gruppi = [("un anno solo", lambda k: k == 1), ("da 2 a 4 anni", lambda k: 2 <= k <= 4),
              ("da 5 a 9 anni", lambda k: 5 <= k <= 9), ("10 anni o più", lambda k: k >= 10)]
    gr = []
    for lab, f in gruppi:
        tt = [t for t in anni_t if f(len(anni_t[t]))]
        gr.append(dict(lab=lab, titoli=len(tt), recite=sum(rec_t[t] for t in tt)))
    top = sorted((t for t in anni_t if len(anni_t[t]) >= 10), key=lambda t: -rec_t[t])
    uno = [t for t in anni_t if len(anni_t[t]) == 1]
    rep = dict(titoli=len(anni_t), recite=len(op), gruppi=gr, top=[[t, rec_t[t], len(anni_t[t])] for t in top],
               mediana_un_anno=statistics.median(rec_t[t] for t in uno))

    # ---- compositori per decennio (solo opere, autore dalla sigla)
    decs = sorted(set(dec(r) for r in op))
    TOPN = 6
    rank, share = {}, {}
    for d in decs:
        c = collections.Counter(r[4] for r in op if dec(r) == d and r[4])
        t = sum(c.values())
        for i, (a, n) in enumerate(c.most_common()):
            rank[(d, a)] = i + 1
            share[(d, a)] = (n, round(100 * n / t))
    nomi = sorted(set(a for (d, a) in rank if rank[(d, a)] <= TOPN))
    comp = dict(decenni=decs, primi=TOPN, senza_autore=sum(1 for r in op if not r[4]),
                nomi=[dict(n=a, rk=[rank.get((d, a)) for d in decs], q=[share.get((d, a), (0, 0))[1] for d in decs],
                           nn=[share.get((d, a), (0, 0))[0] for d in decs]) for a in nomi])

    dati = dict(sipario=sip, repertorio=rep, compositori=comp)
    with open(os.path.join(OUT, "grafici.json"), "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, separators=(",", ":"))
    print("scritto grafici.json:", len(sera), "serate dalle 18,", len(anni_t), "titoli d'opera,", len(nomi), "compositori nei primi", TOPN)


if __name__ == "__main__":
    main()
