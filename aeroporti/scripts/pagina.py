"""Costruisce i file della pagina docs/aeroporti/ (docs/aeroporti/data/).

Uso (percorsi assoluti; si puo' rilanciare quando arrivano nuovi dati):
    python -I -X utf8 pagina.py <cartella aeroporti> <cartella milano-in-dati>

Legge aeroporti/pulito/ (da 03_estrai_enac.py e 04_pulisci.py) e raw/eurostat per la classifica degli aeroporti italiani.
Scrive in docs/aeroporti/data/: riepilogo.json + CSV con ';' e punto decimale.
"""
import csv
import itertools
import json
import os
import shutil
import sys

AP = ["Linate", "Malpensa", "Bergamo"]
NOMI_ICAO = {"IT_LIRF": "Roma Fiumicino", "IT_LIRA": "Roma Ciampino", "IT_LIMC": "Milano Malpensa", "IT_LIML": "Milano Linate",
             "IT_LIME": "Bergamo Orio al Serio", "IT_LIRN": "Napoli", "IT_LICC": "Catania", "IT_LIPZ": "Venezia", "IT_LIPE": "Bologna",
             "IT_LICJ": "Palermo", "IT_LIRP": "Pisa", "IT_LIEE": "Cagliari", "IT_LIBD": "Bari", "IT_LIPH": "Treviso", "IT_LIRQ": "Firenze",
             "IT_LIMF": "Torino", "IT_LIEO": "Olbia", "IT_LIBR": "Brindisi", "IT_LICA": "Lamezia Terme", "IT_LIMJ": "Genova"}


def leggi(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def num(x):
    return None if x in ("", None) else float(x)


def r1(x, d=1):
    return None if x is None else round(x, d)


def pct(a, b):
    return None if not a or not b else (a / b - 1) * 100


def main(base, root):
    P = lambda n: os.path.join(base, "pulito", n)
    out = os.path.join(root, "docs", "aeroporti", "data")
    os.makedirs(out, exist_ok=True)
    R = {}
    anni = list(range(1994, 2026))
    R["meta"] = {"anni": anni, "primo_anno_eurostat": 2004}

    # ---------------- annuale
    ann = leggi(P("annuale.csv"))
    A = {}
    for nome in AP:
        rows = {int(x["anno"]): x for x in ann if x["aeroporto"] == nome}
        g = lambda k: [num(rows[a][k]) if a in rows else None for a in anni]
        A[nome] = {"pax": g("passeggeri"), "nat": g("nazionali"), "intl": g("internazionali"), "ue": g("internazionali_ue"),
                   "extra": g("internazionali_extra_ue"), "voli": g("movimenti_o_voli"), "cargo": g("cargo_tonnellate")}
        A[nome]["quota_intl"] = [r1(i / p * 100, 1) if i and p else None for i, p in zip(A[nome]["intl"], A[nome]["pax"])]
        A[nome]["pax_per_volo"] = [r1(p / v, 0) if p and v and a >= 2004 else None for p, v, a in zip(A[nome]["pax"], A[nome]["voli"], anni)]
    R["aeroporti"] = A
    i = lambda a: anni.index(a)

    ita = {int(x["anno"]): x for x in leggi(P("italia_annuale.csv"))}
    gi = lambda k: [num(ita[a][k]) if a in ita else None for a in anni]
    R["italia"] = {"pax": gi("passeggeri"), "nat": gi("nazionali"), "intl": gi("internazionali"), "voli": gi("movimenti_o_voli"),
                   "cargo": gi("cargo_tonnellate"), "n_aeroporti": gi("n_aeroporti")}
    sis = [sum(A[n]["pax"][k] or 0 for n in AP) if all(A[n]["pax"][k] for n in AP) else None for k in range(len(anni))]
    R["sistema"] = {"pax": sis, "quota_italia_pct": [r1(s / t * 100, 1) if s and t else None for s, t in zip(sis, R["italia"]["pax"])],
                    "cargo": [sum(A[n]["cargo"][k] or 0 for n in AP) if all(A[n]["cargo"][k] for n in AP) else None for k in range(len(anni))]}
    R["sistema"]["quota_cargo_italia_pct"] = [r1(c / t * 100, 1) if c and t else None for c, t in zip(R["sistema"]["cargo"], R["italia"]["cargo"])]
    R["sistema"]["quota_linate_pct"] = [r1(A["Linate"]["pax"][k] / s * 100, 1) if s else None for k, s in enumerate(sis)]
    R["sistema"]["quota_malpensa_pct"] = [r1(A["Malpensa"]["pax"][k] / s * 100, 1) if s else None for k, s in enumerate(sis)]
    R["sistema"]["quota_bergamo_pct"] = [r1(A["Bergamo"]["pax"][k] / s * 100, 1) if s else None for k, s in enumerate(sis)]

    # ---------------- covid: indici 2019 = 100
    ys = list(range(2018, 2026))
    def idx(serie):
        return [r1(serie[i(a)] / serie[i(2019)] * 100, 1) if serie[i(a)] else None for a in ys]
    R["covid"] = {"anni": ys, **{n.lower(): idx(A[n]["pax"]) for n in AP}, "sistema": idx(sis), "italia": idx(R["italia"]["pax"])}

    # ---------------- mensile
    men = leggi(P("mensile.csv"))
    M = {}
    for x in men:
        M.setdefault(x["aeroporto"], {})[(int(x["anno"]), int(x["mese"]))] = x
    ultimo = max(k for k in M["Malpensa"] if M["Malpensa"][k]["passeggeri"])
    labels = [(a, m) for a in range(2018, ultimo[0] + 1) for m in range(1, 13) if (a, m) <= ultimo]
    R["mensile"] = {"etichette": [f"{a}-{m:02d}" for a, m in labels], "ultimo": f"{ultimo[0]}-{ultimo[1]:02d}"}
    for n in AP:
        R["mensile"][n.lower()] = [num(M[n][k]["passeggeri"]) if k in M[n] else None for k in labels]
    # chiusura di Linate 2019: luglio-novembre 2019 contro 2018 e 2020
    ch = {}
    for n in AP:
        ch[n] = {mese: [num(M[n][(a, mese)]["passeggeri"]) for a in (2018, 2019)] for mese in range(6, 12)}
    R["chiusura_linate_2019"] = ch
    tot18 = {n: sum(num(M[n][(2018, m)]["passeggeri"]) for m in (8, 9, 10)) for n in AP}
    tot19 = {n: sum(num(M[n][(2019, m)]["passeggeri"]) for m in (8, 9, 10)) for n in AP}
    R["chiusura_linate_2019_ago_ott"] = {"2018": tot18, "2019": tot19, "sistema_2018": sum(tot18.values()), "sistema_2019": sum(tot19.values())}
    # stagionalita' (quota di ogni mese), 2023-2025, solo anni interi
    st = {}
    for n in AP:
        tot = [sum(num(M[n][(a, m)]["passeggeri"]) for a in (2023, 2024, 2025)) for m in range(1, 13)]
        st[n] = [r1(t / sum(tot) * 100, 2) for t in tot]
    R["stagionalita_2023_2025"] = st

    # ---------------- classifica italiana (Eurostat, tutti gli aeroporti) 2025 e 2019
    d = json.load(open(os.path.join(base, "raw", "eurostat", "avia_paoa_A_pax_tutti_TOTAL.json"), encoding="utf-8"))
    ids = d["id"]
    cats = [list(d["dimension"][k]["category"]["index"].keys()) for k in ids]
    tab = {}
    for pos, combo in enumerate(itertools.product(*cats)):
        v = d["value"].get(str(pos)) if isinstance(d["value"], dict) else d["value"][pos]
        k = dict(zip(ids, combo))
        if k["rep_airp"].startswith("IT_") and v:
            tab[(k["rep_airp"], int(k["time"]))] = v
    for a in (2019, 2025):
        rk = sorted(((v, c) for (c, y), v in tab.items() if y == a), reverse=True)[:12]
        for v, c in rk:
            assert c in NOMI_ICAO, c
    R["classifica"] = {}
    for a in (2019, 2025):
        rk = sorted(((v, c) for (c, y), v in tab.items() if y == a), reverse=True)
        R["classifica"][str(a)] = [{"posto": k + 1, "aeroporto": NOMI_ICAO.get(c, c), "pax": v} for k, (v, c) in enumerate(rk[:12])]
        R["classifica"][str(a) + "_n"] = len(rk)

    # ---------------- controllo
    ctl = leggi(P("controllo_eurostat_enac.csv"))
    R["controllo"] = [{"aeroporto": x["aeroporto"], "anno": int(x["anno"]), "misura": x["misura"], "enac": num(x["ENAC"]), "eurostat": num(x["Eurostat"]),
                       "diff": num(x["differenza_pct"]), "fonte": x["fonte_enac"]} for x in ctl]

    # ---------------- numeri per le sorprese
    L, Mp, B = A["Linate"], A["Malpensa"], A["Bergamo"]
    S = {
        "linate_1998": L["pax"][i(1998)], "linate_1999": L["pax"][i(1999)], "linate_2000": L["pax"][i(2000)],
        "malpensa_1998": Mp["pax"][i(1998)], "malpensa_1999": Mp["pax"][i(1999)], "malpensa_2000": Mp["pax"][i(2000)],
        "bergamo_2000": B["pax"][i(2000)], "bergamo_2024": B["pax"][i(2024)], "bergamo_2025": B["pax"][i(2025)],
        "linate_2018": L["pax"][i(2018)], "linate_2019": L["pax"][i(2019)], "linate_2020": L["pax"][i(2020)], "linate_2024": L["pax"][i(2024)], "linate_2025": L["pax"][i(2025)],
        "malpensa_2018": Mp["pax"][i(2018)], "malpensa_2019": Mp["pax"][i(2019)], "malpensa_2007": Mp["pax"][i(2007)], "malpensa_2009": Mp["pax"][i(2009)],
        "malpensa_2020": Mp["pax"][i(2020)], "malpensa_2024": Mp["pax"][i(2024)], "malpensa_2025": Mp["pax"][i(2025)],
        "bergamo_2018": B["pax"][i(2018)], "bergamo_2019": B["pax"][i(2019)], "bergamo_2020": B["pax"][i(2020)],
        "sistema_2018": sis[i(2018)], "sistema_2019": sis[i(2019)], "sistema_2020": sis[i(2020)], "sistema_2025": sis[i(2025)],
        "linate_quota_intl_2004": L["quota_intl"][i(2004)], "linate_quota_intl_2025": L["quota_intl"][i(2025)],
        "linate_nat_2004": L["nat"][i(2004)], "linate_nat_2025": L["nat"][i(2025)], "linate_intl_2004": L["intl"][i(2004)], "linate_intl_2025": L["intl"][i(2025)],
        "linate_var_2019": r1(pct(L["pax"][i(2019)], L["pax"][i(2018)])), "malpensa_var_2019": r1(pct(Mp["pax"][i(2019)], Mp["pax"][i(2018)])),
        "bergamo_var_2019": r1(pct(B["pax"][i(2019)], B["pax"][i(2018)])), "sistema_var_2019": r1(pct(sis[i(2019)], sis[i(2018)])),
        "italia_2019": R["italia"]["pax"][i(2019)], "italia_2020": R["italia"]["pax"][i(2020)], "italia_2025": R["italia"]["pax"][i(2025)],
        "quota_sistema_2004": R["sistema"]["quota_italia_pct"][i(2004)], "quota_sistema_2019": R["sistema"]["quota_italia_pct"][i(2019)], "quota_sistema_2025": R["sistema"]["quota_italia_pct"][i(2025)],
        "cargo_malpensa_2025": Mp["cargo"][i(2025)], "cargo_italia_2025": R["italia"]["cargo"][i(2025)], "cargo_malpensa_2004": Mp["cargo"][i(2004)],
        "cargo_linate_2000": L["cargo"][i(2000)], "cargo_linate_1998": L["cargo"][i(1998)], "cargo_linate_2025": L["cargo"][i(2025)],
        "cargo_bergamo_2003": B["cargo"][i(2003)], "cargo_bergamo_2025": B["cargo"][i(2025)],
        "bergamo_supera_linate": next(a for a in range(2004, 2026) if B["pax"][i(a)] > L["pax"][i(a)] and all(B["pax"][i(b)] > L["pax"][i(b)] for b in range(a, 2026) if b not in (2019, 2020, 2021)) ),
        "movimenti_linate_1998": L["voli"][i(1998)], "movimenti_linate_1999": L["voli"][i(1999)],
        "pax_volo_malpensa_2025": Mp["pax_per_volo"][i(2025)], "pax_volo_bergamo_2025": B["pax_per_volo"][i(2025)], "pax_volo_linate_2025": L["pax_per_volo"][i(2025)],
        "pax_volo_malpensa_2004": Mp["pax_per_volo"][i(2004)], "pax_volo_bergamo_2004": B["pax_per_volo"][i(2004)], "pax_volo_linate_2004": L["pax_per_volo"][i(2004)],
    }
    S["linate_var_2020"] = r1(pct(S["linate_2020"], S["linate_2019"])); S["malpensa_var_2020"] = r1(pct(S["malpensa_2020"], S["malpensa_2019"]))
    S["bergamo_var_2020"] = r1(pct(S["bergamo_2020"], S["bergamo_2019"])); S["italia_var_2020"] = r1(pct(S["italia_2020"], S["italia_2019"]))
    S["sistema_var_2020"] = r1(pct(S["sistema_2020"], S["sistema_2019"]))
    R["sorprese"] = S

    # ---------------- file per il download
    shutil.copy(P("annuale.csv"), os.path.join(out, "annuale_tre_aeroporti.csv"))
    shutil.copy(P("mensile.csv"), os.path.join(out, "mensile_tre_aeroporti.csv"))
    shutil.copy(P("italia_annuale.csv"), os.path.join(out, "italia_annuale.csv"))
    shutil.copy(P("controllo_eurostat_enac.csv"), os.path.join(out, "controllo_eurostat_enac.csv"))
    with open(os.path.join(out, "riepilogo.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, separators=(",", ":"))
    print("scritto", out)
    print(json.dumps(S, ensure_ascii=False, indent=1))
    print(json.dumps(R["classifica"]["2025"], ensure_ascii=False))
    print(json.dumps(R["chiusura_linate_2019_ago_ott"], ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
