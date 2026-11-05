"""Numeri chiave per NOTE.md. Uso: python -I -X utf8 04_riepilogo.py <cartella omicidi>. Scrive out/riepilogo.txt"""
import sys, os, csv, collections, openpyxl, warnings
warnings.filterwarnings("ignore")
B = sys.argv[1]; P = lambda *a: os.path.join(B, *a); L = []
def say(*a):
    s = " ".join(str(x) for x in a); L.append(s); print(s)
rc = lambda f: list(csv.DictReader(open(P("pulito", f), encoding="utf-8")))
S = rc("serie_lunga_polizia_1983_2024.csv"); A = "Area milanese (Milano+Monza+Lodi)"
d = {(r["territorio"], int(r["anno"])): r for r in S}
c = lambda t, y: int(d[(t, y)]["omicidi_consumati"]); te = lambda t, y: int(d[(t, y)]["tentati_omicidi"])
t = lambda t_, y: float(d[(t_, y)]["omicidi_per_100mila"])
def per(a, b, T=A):
    n = sum(c(T, y) for y in range(a, b + 1)); p = sum(float(d[(T, y)]["popolazione_media"]) for y in range(a, b + 1))
    return n, round(n / (b - a + 1), 1), round(n / p * 1e5, 2)
say("picco", max(range(1983, 2025), key=lambda y: c(A, y)), "minimo", min(range(1983, 2025), key=lambda y: c(A, y)))
for a, b in ((1983, 1989), (1983, 1992), (1988, 1992), (1990, 1992), (2006, 2010), (2020, 2024)):
    say("area", a, b, per(a, b), "tentati media", round(sum(te(A, y) for y in range(a, b + 1)) / (b - a + 1), 1), "| Italia", per(a, b, "Italia"))
say("somma consumati+tentati media 1983-89", round(sum(c(A, y) + te(A, y) for y in range(1983, 1990)) / 7, 1), "1990-92", round(sum(c(A, y) + te(A, y) for y in range(1990, 1993)) / 3, 1))
say("anni con tasso area > Italia", [y for y in range(1983, 2025) if t(A, y) > t("Italia", y)])
say("rapporto area/Italia per periodo", [(f"{a}-{b}", round(per(a, b)[2] / per(a, b, "Italia")[2], 2)) for a, b in ((1983, 1987), (1988, 1992), (1993, 2002), (2003, 2012), (2013, 2024))])
M = rc("milano_moventi_1983_2003.csv")
for a, b in ((1983, 1987), (1988, 1992), (1993, 1997), (1998, 2003)):
    s = [r for r in M if a <= int(r["anno"]) <= b]; f = lambda k: sum(int(r[k]) for r in s)
    say("moventi Milano", a, b, {k: f(k) for k in ("om_consumati", "om_mafia", "om_onore_passionali", "om_furto_rapina", "om_terrorismo", "om_altri_motivi")})
say("preterintenzionali/infanticidi anomali:", [(r["anno"], r["preterintenzionali"], r["infanticidi"]) for r in M if int(r["preterintenzionali"]) > 5 or int(r["infanticidi"]) > 4])
C = rc("comune_milano_2003_2024.csv"); cv = {int(r["anno"]): r for r in C}
for a, b in ((2004, 2008), (2009, 2013), (2014, 2018), (2019, 2024)):
    n = sum(int(cv[y]["omicidi_consumati_comune"]) for y in range(a, b + 1)); p = sum(float(cv[y]["residenti_31dic_ds27"]) for y in range(a, b + 1))
    pv = sum(c(A, y) for y in range(a, b + 1))
    say("comune", a, b, "omicidi", n, "media", round(n / (b - a + 1), 1), "tasso", round(n / p * 1e5, 2), "quota su area", round(n / pv * 100, 1))
G = rc("grandi_comuni_periodi.csv")
for pe in ("2006-2010", "2021-2024"):
    say(pe, sorted([(float(r["per_100mila"] or 0), r["comune"], r["omicidi"]) for r in G if r["periodo"] == pe]))
D = rc("decessi_causa_omicidio_province_2003_2023.csv")
dd = collections.defaultdict(int)
for r in D:
    if r["base"] == "luogo_evento": dd[(r["area"], int(r["anno"]), r["sesso"])] += int(r["morti"])
for nome, ar in (("area milanese", ("ITC45", "IT108", "ITC49")), ("Italia", ("IT",)), ("Roma", ("ITE43",)), ("Napoli", ("ITF33",)), ("Torino", ("ITC11",))):
    o = []
    for a, b in ((2003, 2007), (2008, 2012), (2013, 2017), (2018, 2023)):
        m = sum(dd[(x, y, "M")] for x in ar for y in range(a, b + 1)); f = sum(dd[(x, y, "F")] for x in ar for y in range(a, b + 1))
        o.append((f"{a}-{b}", "M", m, "F", f, "quota F %", round(f / (m + f) * 100, 1)))
    say("decessi per causa", nome, o)
R_ = rc("italia_relazione_2002_2024.csv"); rv = {(int(r["anno"]), r["sesso"], r["relazione"]): (int(r["vittime"]) if r["vittime"] else 0) for r in R_}
for y in (2002, 2004, 2010, 2019, 2024):
    fam = sum(rv[(y, "T", k)] for k in ("partner", "ex_partner", "altro_parente")); ff = sum(rv[(y, "F", k)] for k in ("partner", "ex_partner", "altro_parente"))
    say("Italia", y, "famiglia+partner", fam, "di cui donne", ff, "totale", rv[(y, "T", "totale")], "non famiglia", rv[(y, "T", "totale")] - fam, "non identificato", rv[(y, "T", "non_identificato")], "donne tot", rv[(y, "F", "totale")])
Lm = rc("lombardia_relazione_anni.csv")
for y in (2019, 2023, 2024):
    for ar in ("Lombardia", "Italia"):
        g = {(r["sesso"], r["relazione"]): int(r["vittime"]) for r in Lm if int(r["anno"]) == y and r["area"] == ar}
        say(ar, y, "fam T", g[("T", "partner_ex")] + g[("T", "altro_parente")], "tot", g[("T", "totale")], "| F fam", g[("F", "partner_ex")] + g[("F", "altro_parente")], "F tot", g[("F", "totale")], "| M fam", g[("M", "partner_ex")] + g[("M", "altro_parente")], "M tot", g[("M", "totale")])
wb = openpyxl.load_workbook(P("raw/istat_tavole_2018/Tavole-e-figure-appendice-omicidi.xlsx"), data_only=True)
Rw = list(wb["app1-serie storica"].iter_rows(values_only=True))
an = next(r for r in Rw if r and any(str(x) == "1983" for x in r)); va = next(r for r in Rw if r and any(x and str(x).lower().startswith("omicidi volo") for x in r))
ie = next(i for i, x in enumerate(an) if str(x) == "1983"); iv = next(i for i, x in enumerate(va) if isinstance(x, (int, float)))
dif = [(1983 + k, c("Italia", 1983 + k), va[iv + k]) for k in range(21) if c("Italia", 1983 + k) != va[iv + k]]
say("controllo F Italia file storico vs report 2018, differenze 1983-2003:", dif)
I = rc("italia_tassi_1880_2024.csv")
say("Italia polizia/azione penale:", [(r["anno"], r["omicidi_volontari_azione_penale_per100mila"][:4], r["omicidi_volontari_polizia_per100mila"][:4]) for r in I if r["anno"] in ("1955", "1970", "1975", "1982", "1991", "2017", "2024")])
say("studio autopsie: polizia area 1991", c(A, 1991), "tasso", t(A, 1991), "2016", c(A, 2016), "2019 tasso", t(A, 2019), "somma 1991-2020", sum(c(A, y) for y in range(1991, 2021)), "media", round(sum(c(A, y) for y in range(1991, 2021)) / 30, 1))
say("decessi Monza per anno (evento, T):", {y: dd[("IT108", y, "T")] for y in range(2003, 2024)})
Pa = [c(A, y) for y in range(2003, 2024)]; Da = [sum(dd[(x, y, "T")] for x in ("ITC45", "IT108", "ITC49")) for y in range(2003, 2024)]
ma, mb = sum(Pa) / 21, sum(Da) / 21
say("polizia vs decessi, area milanese 2003-2023: correlazione", round(sum((u - ma) * (v - mb) for u, v in zip(Pa, Da)) / (sum((u - ma) ** 2 for u in Pa) * sum((v - mb) ** 2 for v in Da)) ** .5, 3), "somme", sum(Pa), sum(Da), "scarto massimo", max(abs(u - v) for u, v in zip(Pa, Da)))
say("donne e uomini, media annua decessi area:", [(a, b, round(sum(dd[(x, y, "F")] for x in ("ITC45", "IT108", "ITC49") for y in range(a, b + 1)) / (b - a + 1), 1), round(sum(dd[(x, y, "M")] for x in ("ITC45", "IT108", "ITC49") for y in range(a, b + 1)) / (b - a + 1), 1)) for a, b in ((2003, 2007), (2018, 2023))])
say("idem Italia:", [(a, b, round(sum(dd[("IT", y, "F")] for y in range(a, b + 1)) / (b - a + 1), 1), round(sum(dd[("IT", y, "M")] for y in range(a, b + 1)) / (b - a + 1), 1)) for a, b in ((2003, 2007), (2018, 2023))])
open(P("out/riepilogo.txt"), "w", encoding="utf-8").write("\n".join(L))
