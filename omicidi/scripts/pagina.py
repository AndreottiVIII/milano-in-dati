"""Scrive docs/omicidi/data/ dai file di omicidi/pulito/. Uso: python -I -X utf8 pagina.py <omicidi> <milano-in-dati>
Tutti i numeri della pagina escono da qui (riepilogo.json); la pagina non ne contiene a mano."""
import csv, json, os, sys, collections
B, ROOT = sys.argv[1], sys.argv[2]
OUT = os.path.join(ROOT, "docs", "omicidi", "data"); os.makedirs(OUT, exist_ok=True)
rc = lambda f: list(csv.DictReader(open(os.path.join(B, "pulito", f), encoding="utf-8")))
def wcsv(name, rows, cols):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(cols)
        for r in rows: w.writerow([r[c] for c in cols])
fl = lambda x: float(x) if x not in ("", None) else None
AREA = "Area milanese (Milano+Monza+Lodi)"
S = rc("serie_lunga_polizia_1983_2024.csv")
ser = {(r["territorio"], int(r["anno"])): r for r in S}
R = {}
# --- grafico 1
g1 = []
for y in range(1983, 2025):
    a, i = ser[(AREA, y)], ser[("Italia", y)]
    g1.append(dict(anno=y, omicidi=int(a["omicidi_consumati"]), tentati=int(a["tentati_omicidi"]), tasso=round(float(a["omicidi_per_100mila"]), 2),
        tasso_5anni=fl(a["tasso_media_5anni_centrata"]), italia_omicidi=int(i["omicidi_consumati"]), italia_tasso=round(float(i["omicidi_per_100mila"]), 2),
        italia_tasso_5anni=fl(i["tasso_media_5anni_centrata"]), fonte=a["fonte_conteggi"]))
wcsv("area_milanese_italia_1983_2024.csv", g1, list(g1[0].keys()))
R["g1"] = g1
def pool(a, b, terr=AREA):
    n = sum(int(ser[(terr, y)]["omicidi_consumati"]) for y in range(a, b + 1))
    p = sum(float(ser[(terr, y)]["popolazione_media"]) for y in range(a, b + 1))
    return n, n / (b - a + 1), n / p * 1e5
pk = max(g1, key=lambda r: r["omicidi"]); mn = min(g1, key=lambda r: r["omicidi"])
n1, m1, t1 = pool(1990, 1992); n2, m2, t2 = pool(2020, 2024)
ni1, mi1, ti1 = pool(1990, 1992, "Italia"); ni2, mi2, ti2 = pool(2020, 2024, "Italia")
sotto = sum(1 for y in range(1983, 2025) if float(ser[(AREA, y)]["omicidi_per_100mila"]) < float(ser[("Italia", y)]["omicidi_per_100mila"]))
ten1 = sum(r["tentati"] for r in g1 if 1983 <= r["anno"] <= 1992) / 10; ten2 = sum(r["tentati"] for r in g1 if r["anno"] >= 2020) / 5
a03, a04 = g1[20], g1[21]
# calo calcolato sui tassi mostrati (0,41 su 2,24); sui valori esatti sarebbe -81,5
R["s"] = dict(picco_anno=pk["anno"], picco_n=pk["omicidi"], min_anno=mn["anno"], min_n=mn["omicidi"],
    m9092=round(m1), t9092=round(t1, 2), m2024=round(m2), t2024=round(t2, 2), calo=round((round(t2, 2) / round(t1, 2) - 1) * 100),
    it_t9092=round(ti1, 2), it_t2024=round(ti2, 2), it_calo=round((round(ti2, 2) / round(ti1, 2) - 1) * 100),
    anni_sotto_italia=sotto, anni_tot=len(g1), tent_8392=round(ten1), tent_2024=round(ten2), tent_calo=round((ten2 / ten1 - 1) * 100),
    om_2003=a03["omicidi"], om_2004=a04["omicidi"], it_2003=a03["italia_omicidi"], it_2004=a04["italia_omicidi"],
    t1984=g1[1]["tasso"], t1992=g1[9]["tasso"], m8389=round(sum(r["omicidi"] for r in g1 if r["anno"] <= 1989) / 7, 1),
    m8392=round(sum(r["omicidi"] for r in g1 if r["anno"] <= 1992) / 10, 1))
# --- grafico 2
P = rc("confronto_periodi_1983_2024.csv")
for r in P: r["territorio"] = "Area milanese" if r["territorio"].startswith("Area") else r["territorio"]
wcsv("confronto_periodi_province.csv", P, ["territorio", "periodo", "omicidi", "media_annua", "per_100mila"])
R["g2"] = [dict(t=r["territorio"], p=r["periodo"], n=int(r["omicidi"]), tasso=float(r["per_100mila"])) for r in P]
# --- grafico 3
C = rc("comune_milano_2003_2024.csv")
c3 = [dict(anno=int(r["anno"]), omicidi=int(r["omicidi_consumati_comune"]), tentati=int(r["tentati_comune"]), tasso=float(r["per_100mila"])) for r in C if r["omicidi_consumati_comune"]]
wcsv("comune_milano_2004_2024.csv", c3, ["anno", "omicidi", "tentati", "tasso"])
R["g3a"] = c3
cs = lambda a, b: sum(r["omicidi"] for r in c3 if a <= r["anno"] <= b)
R["s"].update(c2004=[r for r in c3 if r["anno"] == 2004][0]["omicidi"], c2024=[r for r in c3 if r["anno"] == 2024][0]["omicidi"],
    c_media0408=round(cs(2004, 2008) / 5, 1), c_media1924=round(cs(2019, 2024) / 6, 1))
G = rc("grandi_comuni_periodi.csv")
g21 = sorted([r for r in G if r["periodo"] == "2021-2024"], key=lambda r: -float(r["per_100mila"]))
g3b = [dict(comune=r["comune"], casi=int(r["omicidi"]), tasso=float(r["per_100mila"]), pos=i + 1) for i, r in enumerate(g21)]
wcsv("grandi_comuni_2021_2024.csv", g3b, ["comune", "casi", "tasso", "pos"])
wcsv("grandi_comuni_per_periodo.csv", [dict(comune=r["comune"], periodo=r["periodo"], casi=r["omicidi"], tasso=r["per_100mila"]) for r in G], ["comune", "periodo", "casi", "tasso"])
R["g3b"] = g3b; mi = [r for r in g3b if r["comune"] == "Milano"][0]
R["s"].update(mi_tasso=mi["tasso"], mi_casi=mi["casi"], mi_pos=mi["pos"], n_comuni=len(g3b))
# --- grafico 4: sesso (certificati di morte, luogo dell'evento)
D = rc("decessi_causa_omicidio_province_2003_2023.csv"); dd = collections.defaultdict(int)
for r in D:
    if r["base"] == "luogo_evento": dd[(r["area"], int(r["anno"]), r["sesso"])] += int(r["morti"])
g4 = []
for nome, ar in (("Area milanese", ("ITC45", "IT108", "ITC49")), ("Italia", ("IT",))):
    for a, b in ((2003, 2007), (2008, 2012), (2013, 2017), (2018, 2023)):
        m = sum(dd[(x, y, "M")] for x in ar for y in range(a, b + 1)); f = sum(dd[(x, y, "F")] for x in ar for y in range(a, b + 1))
        g4.append(dict(territorio=nome, periodo=f"{a}-{b}", anni=b - a + 1, donne=f, uomini=m, quota_donne=round(f / (m + f) * 100, 1), donne_anno=round(f / (b - a + 1), 1), uomini_anno=round(m / (b - a + 1), 1)))
wcsv("donne_uomini_periodi.csv", g4, list(g4[0].keys())); R["g4"] = g4
# controllo polizia/certificati
Pa = [int(ser[(AREA, y)]["omicidi_consumati"]) for y in range(2003, 2024)]; Da = [sum(dd[(x, y, "T")] for x in ("ITC45", "IT108", "ITC49")) for y in range(2003, 2024)]
ma, mb = sum(Pa) / 21, sum(Da) / 21
cor = sum((u - ma) * (v - mb) for u, v in zip(Pa, Da)) / (sum((u - ma) ** 2 for u in Pa) * sum((v - mb) ** 2 for v in Da)) ** .5
ev = sum(int(r["morti"]) for r in D if r["area"] == "ITC45" and r["anno"] == "2004" and r["base"] == "luogo_evento" and r["sesso"] == "T")
rs = sum(int(r["morti"]) for r in D if r["area"] == "ITC45" and r["anno"] == "2004" and r["base"] == "residenza" and r["sesso"] == "T")
itp = sum(int(ser[("Italia", y)]["omicidi_consumati"]) for y in range(2003, 2024)); itd = sum(dd[("IT", y, "T")] for y in range(2003, 2024))
R["s"].update(pol_somma=sum(Pa), cert_somma=sum(Da), pol_cert_corr=round(cor, 2), cert_2004_luogo=ev, cert_2004_res=rs, it_cert_quota=round(itd / itp * 100))
# --- grafico 5: relazione
rv = collections.defaultdict(int)
for r in rc("italia_relazione_2002_2024.csv"): rv[(int(r["anno"]), r["sesso"], r["relazione"])] = int(r["vittime"] or 0)
FAM = ("partner", "ex_partner", "altro_parente")
g5 = []
for y in range(2002, 2025):
    fam = sum(rv[(y, "T", k)] for k in FAM); ni = rv[(y, "T", "non_identificato")]
    tot = rv[(y, "T", "totale")]; ff = sum(rv[(y, "F", k)] for k in FAM)
    g5.append(dict(anno=y, famiglia=fam, altri=tot - fam - ni, non_identificato=ni, totale=tot, donne_totale=rv[(y, "F", "totale")], donne_famiglia=ff))
wcsv("italia_relazione_2002_2024.csv", g5, list(g5[0].keys())); R["g5"] = g5
lv = {(int(r["anno"]), r["area"], r["sesso"], r["relazione"]): int(r["vittime"] or 0) for r in rc("lombardia_relazione_anni.csv")}
g5l = []
for y in (2019, 2023, 2024):
    row = dict(anno=y)
    for s_, k in (("T", "tutti"), ("F", "donne"), ("M", "uomini")):
        ks = [q for q in ("partner_ex", "partner", "ex_partner", "altro_parente") if (y, "Lombardia", s_, q) in lv]
        row[k + "_famiglia"] = sum(lv[(y, "Lombardia", s_, q)] for q in ks)
        row[k + "_totale"] = lv[(y, "Lombardia", s_, "totale")]
    g5l.append(row)
wcsv("lombardia_relazione_3_anni.csv", g5l, list(g5l[0].keys())); R["g5l"] = g5l
R["s"].update(fam_2002=g5[0]["famiglia"], fam_2024=g5[-1]["famiglia"], altri_2002=g5[0]["altri"], altri_2024=g5[-1]["altri"], ni_2002=g5[0]["non_identificato"], ni_2024=g5[-1]["non_identificato"], tot_2002=g5[0]["totale"], tot_2024=g5[-1]["totale"])
# --- moventi
M = rc("milano_moventi_1983_2003.csv"); mv = []
for a, b in ((1983, 1987), (1988, 1992), (1993, 1997), (1998, 2003)):
    rr = [r for r in M if a <= int(r["anno"]) <= b]; g = lambda k: sum(int(r[k]) for r in rr)
    mv.append(dict(periodo=f"{a}-{b}", omicidi=g("om_consumati"), mafia=g("om_mafia"), onore_passione=g("om_onore_passionali"), rapina=g("om_furto_rapina"),
        altri_motivi=g("om_altri_motivi") + g("om_terrorismo")))
wcsv("moventi_periodi.csv", mv, list(mv[0].keys())); R["moventi"] = mv
m88 = mv[1]; R["s"].update(mafia_8892=m88["mafia"], mov_tot_8892=m88["omicidi"], mafia_pct=round(m88["mafia"] / m88["omicidi"] * 100), altri_pct=round(m88["altri_motivi"] / m88["omicidi"] * 100))
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps(R["s"], ensure_ascii=False)); print(os.listdir(OUT))
