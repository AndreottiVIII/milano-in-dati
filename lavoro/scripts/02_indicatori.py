"""Lavoro, passo 2: indicatori di lavoro per NIL (88) e per comune, anni 1991, 2001, 2011, 2021, 2023.
Uso: python -I -X utf8 02_indicatori.py <milano-in-dati>
Input : censimenti/pulito/sezioni_<anno>.csv e sezioni_armonizzate.csv (sezione -> NIL, gia' costruito dal filone censimenti),
        censimenti/pulito/variazioni_NIL_1991_2023.csv (campo 'robusto'), nil_2021_anagrafica.csv
Output: lavoro/out/sezioni_lavoro.csv        una riga per sezione e anno con i conteggi usati
        lavoro/out/lavoro_NIL.csv            una riga per NIL e anno: conteggi e indicatori
        lavoro/out/lavoro_comune.csv         una riga per anno: conteggi e indicatori per tutto il comune
        lavoro/out/controlli.txt             controlli aritmetici (somme, residui)
Definizioni (vedi NOTE.md):
  occupati ogni 100 residenti di 15-64 anni = occupati (di ogni eta' nel 1991-2011; 15-64 nel 2021-2023) / residenti 15-64
  tasso di disoccupazione 1991-2011 = (forze di lavoro - occupati) / forze di lavoro   [comprende chi cerca il primo lavoro]
  studenti, pensionati, casalinghe/i: ogni 100 residenti (tutte le eta')   [solo 1991, 2001, 2011]
"""
import sys
import numpy as np
import pandas as pd

root = sys.argv[1]
P = root + "/censimenti/pulito/"
O = root + "/lavoro/out/"
YEARS = [1991, 2001, 2011, 2021, 2023]
AGE_T = [f"P{i}" for i in range(17, 27)]   # 15-19 ... 60-64
AGE_M = [f"P{i}" for i in range(33, 43)]   # maschi 15-19 ... 60-64
log = []


def L(s):
    print(s); log.append(s)


def sez_frame(y):
    if y == 1991:
        d = pd.read_csv(P + "sezioni_1991.csv", low_memory=False); key = d["SEZIONE"]
    elif y == 2001:
        d = pd.read_csv(P + "sezioni_2001.csv", low_memory=False); key = d["SEZIONE"]
    elif y == 2011:
        d = pd.read_csv(P + "sezioni_2011.csv", low_memory=False); key = d["NSEZ"]
    else:
        d = pd.read_csv(P + f"sezioni_{y}.csv", low_memory=False); key = d["SEZ21_ID"].astype(str).str[-7:].astype(int)
    o = pd.DataFrame({"sez": key.values, "anno": y})
    o["pop"] = d["P1"].values
    o["pop_m"] = d["P2"].values
    o["p1564"] = d[AGE_T].sum(axis=1).values
    o["p1564_m"] = d[AGE_M].sum(axis=1).values
    o["p0_14"] = (d["P14"] + d["P15"] + d["P16"]).values
    if y == 1991:
        m = dict(occ="P61", occ_m="P67", fl="P60", stu="P149", stu_m="P150", cas="P148", rit="P151", rit_m="P152", nfl="P146")
        o["fl_m"] = (d["P69"] + d["P70"]).values
    elif y in (2001, 2011):
        m = dict(occ="P61", occ_m="P65", fl="P60", fl_m="P64", stu="P131", stu_m="P132", cas="P130",
                 rit=("P133" if y == 2001 else "P139"), rit_m=("P134" if y == 2001 else "P140"), nfl="P128")
    else:
        m = dict(occ="P101", occ_m="P102")
    for k, c in m.items():
        o[k] = d[c].values
    for k in ["occ", "occ_m", "fl", "fl_m", "stu", "stu_m", "cas", "rit", "rit_m", "nfl"]:
        if k not in o:
            o[k] = np.nan
    o["occ_f"] = d["P103"].values if y >= 2021 else np.nan
    return o


frames = []
for y in YEARS:
    f = sez_frame(y)
    s = f[["pop", "pop_m", "p1564", "p1564_m", "occ", "occ_m", "fl", "fl_m", "stu", "cas", "rit", "nfl"]].sum(min_count=1)
    L(f"[{y}] sezioni {len(f)}; residenti {int(s['pop'])}; 15-64 {int(s.p1564)}; occupati {s.occ:.0f}; forze lavoro {s.fl}; in cerca {s.fl - s.occ}")
    if y in (1991, 2001, 2011):
        resid = f.nfl - f.cas - f.stu - f.rit
        L(f"    non forze lavoro - casalinghe - studenti - ritirati = altra condizione: totale {resid.sum():.0f}, minimo per sezione {resid.min():.0f}")
        L(f"    forze di lavoro >= occupati in ogni sezione: {(f.fl >= f.occ).all()}; maschi: occ_m<=occ {(f.occ_m <= f.occ).all()}, fl_m<=fl {(f.fl_m <= f.fl).all()}")
    if y >= 2021:
        L(f"    P101 = P102 + P103 in ogni sezione: {(f.occ == f.occ_m + f.occ_f).all()}")
    frames.append(f)
S = pd.concat(frames, ignore_index=True)

arm = pd.read_csv(P + "sezioni_armonizzate.csv", usecols=["sez", "anno", "nil", "speciale", "purezza_nil"])
S = S.merge(arm, on=["sez", "anno"], how="left", validate="one_to_one")
L(f"sezioni senza NIL (speciali o non collocate): {int(S.nil.isna().sum())}; di cui speciali {int(S.speciale.sum())}")
for y in YEARS:
    z = S[S.anno == y]
    L(f"  {y}: residenti non collocati {int(z[z.nil.isna()]['pop'].sum())} su {int(z['pop'].sum())}")
S.to_csv(O + "sezioni_lavoro.csv", index=False)

SUM = ["pop", "pop_m", "p1564", "p1564_m", "p0_14", "occ", "occ_m", "occ_f", "fl", "fl_m", "stu", "stu_m", "cas", "rit", "rit_m", "nfl"]


def indic(g):
    g = g.copy()
    g["pop_f"] = g["pop"] - g.pop_m
    g["p1564_f"] = g.p1564 - g.p1564_m
    g["occ_f"] = np.where(g.anno >= 2021, g.occ_f, g.occ - g.occ_m)
    g["fl_f"] = g.fl - g.fl_m
    g["tasso_occ"] = 100 * g.occ / g.p1564
    g["tasso_occ_m"] = 100 * g.occ_m / g.p1564_m
    g["tasso_occ_f"] = 100 * g.occ_f / g.p1564_f
    g["gap_occ_mf"] = g.tasso_occ_m - g.tasso_occ_f
    g["cerca"] = g.fl - g.occ
    g["cerca_m"] = g.fl_m - g.occ_m
    g["cerca_f"] = g.fl_f - g.occ_f
    g["tasso_disocc"] = 100 * g.cerca / g.fl
    g["tasso_disocc_m"] = 100 * g.cerca_m / g.fl_m
    g["tasso_disocc_f"] = 100 * g.cerca_f / g.fl_f
    g["studenti_100"] = 100 * g.stu / g["pop"]
    g["pensionati_100"] = 100 * g.rit / g["pop"]
    g["casalinghe_100"] = 100 * g.cas / g["pop"]
    g["casalinghe_100_donne"] = 100 * g.cas / g.pop_f
    g["altri_100"] = 100 * (g.nfl - g.stu - g.cas - g.rit) / g["pop"]
    g["occupati_100"] = 100 * g.occ / g["pop"]
    return g


def agg(by):
    out = []
    for y in YEARS:
        s = S[S.anno == y]
        if by:
            s = s[s[by].notna()]
            grp = s.groupby(by)[SUM].sum(min_count=1).reset_index()
        else:
            grp = s[SUM].sum(min_count=1).to_frame().T
        grp.insert(0, "anno", y)
        out.append(grp)
    return indic(pd.concat(out, ignore_index=True))


nil = agg("nil"); nil["nil"] = nil.nil.astype(int)
ana = pd.read_csv(P + "nil_2021_anagrafica.csv")
rob = pd.read_csv(P + "variazioni_NIL_1991_2023.csv")[["nil", "robusto"]]
nil = nil.merge(ana[["nil", "nil_nome", "municipio_prevalente", "area_km2"]], on="nil", how="left").merge(rob, on="nil", how="left")
# soglie: non si calcolano tassi se i denominatori sono troppo piccoli (niente tassi su pochi abitanti)
MIN_P1564, MIN_FL = 500, 300
nil["tassi_ok"] = nil.p1564 >= MIN_P1564
nil["disocc_ok"] = nil.fl >= MIN_FL
rate_cols = ["tasso_occ", "tasso_occ_m", "tasso_occ_f", "gap_occ_mf", "occupati_100", "studenti_100", "pensionati_100", "casalinghe_100", "casalinghe_100_donne", "altri_100"]
nil.loc[~nil.tassi_ok, rate_cols] = np.nan
dis_cols = ["tasso_disocc", "tasso_disocc_m", "tasso_disocc_f"]
nil.loc[~nil.disocc_ok, dis_cols] = np.nan
nil.loc[(nil.fl_m < MIN_FL / 2) | (nil.fl_f < MIN_FL / 2), ["tasso_disocc_m", "tasso_disocc_f"]] = np.nan
nil.to_csv(O + "lavoro_NIL.csv", index=False)
com = agg(None)
com.to_csv(O + "lavoro_comune.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
c = com.set_index("anno")
L("\n=== COMUNE (somma di tutte le sezioni, comprese le speciali) ===")
L(c[["pop", "p1564", "occ", "occ_m", "occ_f", "fl", "cerca", "tasso_occ", "tasso_occ_m", "tasso_occ_f", "gap_occ_mf",
     "tasso_disocc", "tasso_disocc_m", "tasso_disocc_f", "stu", "rit", "cas", "studenti_100", "pensionati_100", "casalinghe_100",
     "casalinghe_100_donne", "altri_100"]].round(2).T.to_string())
L("\n=== NIL: quanti con tassi calcolabili ===")
for y in YEARS:
    z = nil[nil.anno == y]
    L(f"  {y}: NIL {len(z)}; con 15-64 >= {MIN_P1564}: {int(z.tassi_ok.sum())}; con forze di lavoro >= {MIN_FL}: {int(z.disocc_ok.sum())}; "
      f"NIL non calcolabili: {', '.join(z[~z.tassi_ok].nil_nome.tolist())}")
open(O + "controlli.txt", "w", encoding="utf-8").write("\n".join(log))
