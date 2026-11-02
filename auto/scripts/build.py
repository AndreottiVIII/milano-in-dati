"""Le auto dei milanesi - passo 1: dai file grezzi alle tabelle pulite in auto/pulito/.
Fonti: ACI Autoritratto 2019-2025 (CC BY 4.0), Comune di Milano ds529/ds530 (CC-BY), ISTAT POSAS e bilancio demografico (CC BY 4.0).
Uso: python -I -X utf8 <...>/auto/scripts/build.py <cartella auto>      (percorso assoluto; rilanciabile)
"""
import csv
import io
import json
import os
import re
import sys
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import aci  # noqa: E402

AUTO = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
RAW = os.path.join(AUTO, "raw")
PUL = os.path.join(AUTO, "pulito")
ROOT = os.path.dirname(AUTO)
os.makedirs(PUL, exist_ok=True)

ANNI = aci.ANNI
CITTA = ["MILANO", "ROMA", "TORINO", "NAPOLI", "BOLOGNA", "FIRENZE", "GENOVA", "VERONA", "BARI", "PALERMO"]
NOME = {c: c.capitalize() for c in CITTA}
CODICE_PROV = {"MILANO": "015_Milano", "ROMA": "058_Roma", "TORINO": "001_Torino", "NAPOLI": "063_Napoli",
               "BOLOGNA": "037_Bologna", "FIRENZE": "048_Firenze", "GENOVA": "010_Genova", "VERONA": "023_Verona",
               "BARI": "072_Bari", "PALERMO": "082_Palermo"}
AVVISI = []


def aggregato(n):
    """True per le righe che non sono una provincia (totali regionali, di area, nazionali, riepiloghi, 'X TOTALE')."""
    n = n.upper().strip()
    return (not n or n.startswith("TOTALE") or n.endswith(" TOTALE") or n.startswith("ITALIA") or n.startswith("RIEPILOGO")
            or n.startswith("NON DEF") or n.startswith("AREA"))


def scrivi(nome, righe, campi):
    p = os.path.join(PUL, nome)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campi, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in righe:
            w.writerow({k: (int(v) if isinstance(v, float) and v.is_integer() else (round(v, 2) if isinstance(v, float) else v)) for k, v in r.items()})
    print("scritto", nome, len(righe), "righe")


# ----------------------------------------------------------------------------------------------------------
# lettura generica dei fogli ACI
KEYS = {"", "area geografica", "regione", "provincia", "comune", "alimentazione", "fascia", "uso"}


def leggi(righe):
    """Fogli ACI -> lista di dict. Colonne-etichetta a sinistra riempite verso il basso; totale -> 'TOT'."""
    head = [h.strip() for h in righe[1]]
    nk = 0
    while nk < len(head) and head[nk].lower() in KEYS:
        nk += 1
    nomi = []
    for i, h in enumerate(head):
        if i < nk:
            nomi.append(h.lower() if h else "provincia")
        else:
            hu = h.upper()
            nomi.append("TOT" if hu.startswith("TOTALE") else hu)
    out = []
    cur = [""] * nk
    for r in righe[2:]:
        r = list(r) + [""] * (len(head) - len(r))
        for i in range(nk):
            if r[i].strip():
                cur[i] = r[i].strip()
                for j in range(i + 1, nk):
                    if not r[j].strip():
                        cur[j] = ""
        d = {nomi[i]: cur[i] for i in range(nk)}
        for i in range(nk, len(head)):
            d[nomi[i]] = aci.num(r[i])
        out.append(d)
    return out


def foglio(anno, quale, nome):
    f = aci.fogli_anno(anno, quale, [nome])[nome]
    if f is None:
        return None
    return leggi(f)


# ----------------------------------------------------------------------------------------------------------
# popolazione ISTAT al 1 gennaio (POSAS)
def pop_posas(anno_1gen, quale):
    """quale = 'Regioni' (somma = Italia) oppure codice provincia '015_Milano'. Ritorna {nome comune/regione: totale} """
    nome = "POSAS_%d_it_%s.zip" % (anno_1gen, quale)
    z = zipfile.ZipFile(os.path.join(RAW, "istat_posas", nome))
    txt = z.read(z.namelist()[0]).decode("utf-8-sig", "replace")
    rd = csv.reader(io.StringIO(txt), delimiter=";")
    next(rd)
    head = next(rd)
    out = {}
    for r in rd:
        if len(r) < len(head):
            continue
        if r[2].strip() == "999":
            out[r[1].strip()] = int(r[-1])
    return out


def popolazioni():
    """{(territorio, anno_veicoli): popolazione al 1 gennaio dell'anno dopo}  territorio: 'COMUNE:MILANO', 'PROV:MILANO', 'ITALIA'"""
    P = {}
    for ay in ANNI:
        a1 = ay + 1
        reg = pop_posas(a1, "Regioni")
        P[("ITALIA", ay)] = sum(reg.values())
        for c in CITTA:
            d = pop_posas(a1, CODICE_PROV[c])
            P[("PROV:" + c, ay)] = sum(d.values())
            P[("COMUNE:" + c, ay)] = d[NOME[c]]
    return P


# ----------------------------------------------------------------------------------------------------------
def parte_aci():
    P = popolazioni()
    conf = []           # auto e moto per territorio e anno
    carb = []           # carburante per provincia
    eur_prov = []       # Euro per provincia
    eur_com = []        # Euro per comune
    eta_pot = []        # eta' e potenza per provincia
    uso = []            # persona giuridica, noleggio
    mc_eur = []         # moto per Euro nei comuni
    dieselmi = []       # diesel per classe Euro in provincia di Milano
    for ay in ANNI:
        print("ACI", ay)
        # 1) categorie per provincia e per comune
        pc = foglio(ay, "pv", "provincia categoria")
        prov = {}
        italia_auto = italia_moto = 0
        for r in pc:
            n = r["provincia"].upper()
            if aggregato(n):
                continue
            prov[n] = r
            italia_auto += r["AUTOVETTURE"]
            italia_moto += r["MOTOCICLI"]
        cc = foglio(ay, "pv", "comune categoria")
        com = {}
        for r in cc:
            if r["comune"].upper() == r["provincia"].upper() and r["provincia"].upper() in CITTA:
                com[r["provincia"].upper()] = r
        # controllo: capoluogo giusto, esiste
        for c in CITTA:
            if c not in com or c not in prov:
                AVVISI.append("manca %s %d" % (c, ay))
        conf.append(dict(anno=ay, territorio="Italia", tipo="Italia", autovetture=italia_auto, motocicli=italia_moto,
                         popolazione=P[("ITALIA", ay)]))
        for c in CITTA:
            conf.append(dict(anno=ay, territorio=NOME[c], tipo="comune", autovetture=com[c]["AUTOVETTURE"],
                             motocicli=com[c]["MOTOCICLI"], popolazione=P[("COMUNE:" + c, ay)]))
            conf.append(dict(anno=ay, territorio=NOME[c], tipo="provincia", autovetture=prov[c]["AUTOVETTURE"],
                             motocicli=prov[c]["MOTOCICLI"], popolazione=P[("PROV:" + c, ay)]))
        # resto della provincia di Milano
        conf.append(dict(anno=ay, territorio="Milano", tipo="resto_provincia",
                         autovetture=prov["MILANO"]["AUTOVETTURE"] - com["MILANO"]["AUTOVETTURE"],
                         motocicli=prov["MILANO"]["MOTOCICLI"] - com["MILANO"]["MOTOCICLI"],
                         popolazione=P[("PROV:MILANO", ay)] - P[("COMUNE:MILANO", ay)]))

        # 2) carburante per provincia (autovetture): righe con fascia 'Totale' o, in assenza, somma delle fasce
        ap = foglio(ay, "cop", "av per provincia")
        tot = defaultdict(lambda: defaultdict(float))     # (prov, alim) -> euro-colonna -> n
        for r in ap:
            p = r["provincia"].upper()
            f = r["fascia"].upper()
            al = r["alimentazione"].upper()
            totale = False
            if al.endswith(" TOTALE"):
                al, totale = al[:-7].strip(), True
            elif f.startswith("TOT"):
                totale = True
            if aggregato(p) or not totale or not al or al == "TOTALE" or al == p or al.startswith(p + " "):
                continue
            for k, v in r.items():
                if k in ("provincia", "regione", "alimentazione", "fascia"):
                    continue
                tot[(p, al)][k] += v
        eur_cols = [k for k in next(iter(tot.values())).keys()]
        provs_all = sorted({k[0] for k in tot})
        # Italia = somma di tutte le province
        for (p, al), d in list(tot.items()):
            for k, v in d.items():
                tot[("ITALIA", al)][k] += v
        for p in CITTA + ["ITALIA"]:
            gruppi = defaultdict(float)
            for (pp, al), d in tot.items():
                if pp != p:
                    continue
                t = d.get("TOT", 0)
                if al == "BENZINA":
                    g = "benzina"
                elif al == "GASOLIO":
                    g = "gasolio"
                elif al.startswith("IBRIDO"):
                    g = "ibrido"
                elif al.startswith("ELETTR"):
                    g = "elettrico"
                elif al in ("BENZINA E GAS LIQUIDO", "GASOLIO E GAS"):
                    g = "gpl"
                elif al in ("BENZINA E METANO", "METANO"):
                    g = "metano"
                else:
                    g = "altro"
                gruppi[g] += t
            tt = sum(gruppi.values())
            row = dict(anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]), totale=tt)
            for g in ("benzina", "gasolio", "ibrido", "elettrico", "gpl", "metano", "altro"):
                row[g] = gruppi.get(g, 0)
            carb.append(row)
            # Euro per provincia (tutte le alimentazioni sommate)
            e = defaultdict(float)
            for (pp, al), d in tot.items():
                if pp != p:
                    continue
                for k, v in d.items():
                    e[k] += v
            eur_prov.append(euro_riga(ay, "Italia" if p == "ITALIA" else NOME[p], e))
        # diesel in provincia di Milano per Euro
        d = tot[("MILANO", "GASOLIO")]
        dieselmi.append(euro_riga(ay, "Milano (gasolio)", d))
        d = tot[("MILANO", "BENZINA")]
        dieselmi.append(euro_riga(ay, "Milano (benzina)", d))

        # 3) Euro per comune
        ac = foglio(ay, "cop", "av per comune")
        for r in ac:
            if r["comune"].upper() == r["provincia"].upper() and r["provincia"].upper() in CITTA:
                eur_com.append(euro_riga(ay, NOME[r["provincia"].upper()], r))
        mm = foglio(ay, "cop", "mc per comune")
        for r in mm:
            if r["comune"].upper() == r["provincia"].upper() and r["provincia"].upper() in CITTA:
                mc_eur.append(euro_riga_moto(ay, NOME[r["provincia"].upper()], r))

        # 4) eta' e potenza per provincia
        anno_b = foglio(ay, "pv", "av provincia anno")
        kw = foglio(ay, "pv", "av provincia kw")
        cil = foglio(ay, "pv", "av provincia cilindrata")
        bande = [k for k in anno_b[0].keys() if k not in ("provincia", "regione", "NON DEFINITO", "TOT")]

        def per_prov(tab):
            d = {}
            for r in tab:
                n = r["provincia"].upper()
                if n:
                    d[n] = r
            return d

        A, K, C = per_prov(anno_b), per_prov(kw), per_prov(cil)
        # Italia = somma delle province
        def somma(tab):
            s = defaultdict(float)
            for r in tab:
                n = r["provincia"].upper()
                if aggregato(n):
                    continue
                for k, v in r.items():
                    if isinstance(v, float):
                        s[k] += v
            return dict(s)
        A["ITALIA"], K["ITALIA"], C["ITALIA"] = somma(anno_b), somma(kw), somma(cil)
        for p in CITTA + ["ITALIA"]:
            a, k, c = A[p], K[p], C[p]
            tot_a = sum(a[b] for b in bande)
            tot_k = sum(k[b] for b in ("FINO A 40", "41 - 55", "56 - 70", "71 - 85", "86 - 100", "101 - 115", "116 - 130", "OLTRE 130"))
            tot_c = sum(c[b] for b in ("FINO A 800", "801 - 1200", "1201 - 1600", "1601 - 1800", "1801 - 2000", "2001 - 2500", "2501 - 3000", "OLTRE 3000"))
            eta_pot.append(dict(
                anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]),
                vecchie16_pct=100 * a[bande[0]] / tot_a,
                ultimi2_pct=100 * a[bande[-1]] / tot_a,
                banda_vecchie=bande[0], banda_nuove=bande[-1],
                kw_oltre100_pct=100 * (k["101 - 115"] + k["116 - 130"] + k["OLTRE 130"]) / tot_k,
                kw_oltre130_pct=100 * k["OLTRE 130"] / tot_k,
                kw_fino70_pct=100 * (k["FINO A 40"] + k["41 - 55"] + k["56 - 70"]) / tot_k,
                cil_oltre2000_pct=100 * (c["2001 - 2500"] + c["2501 - 3000"] + c["OLTRE 3000"]) / tot_c,
                cil_fino1200_pct=100 * (c["FINO A 800"] + c["801 - 1200"]) / tot_c,
                n_autovetture=tot_a))
            if p == "MILANO" or p == "ITALIA" or p == "ROMA":
                pass
        # bande complete per Milano e Italia (per il grafico)
        for p in ("MILANO", "ITALIA"):
            for b in bande:
                uso.append(dict(anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]), tabella="anno_immatricolazione",
                                voce=b, valore=A[p][b]))
            for b in ("FINO A 40", "41 - 55", "56 - 70", "71 - 85", "86 - 100", "101 - 115", "116 - 130", "OLTRE 130"):
                uso.append(dict(anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]), tabella="kw", voce=b, valore=K[p][b]))
        # 5) uso e soggetto
        us = foglio(ay, "pv", "av provincia uso")
        if us:
            U = per_prov(us)
            U["ITALIA"] = somma(us)
            for p in CITTA + ["ITALIA"]:
                for v in ("PRIVATO", "NOLEGGIO CON CONDUCENTE", "NOLEGGIO SENZA CONDUCENTE", "PUBBLICO", "NON DEFINITO", "TOT"):
                    uso.append(dict(anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]), tabella="uso", voce=v, valore=U[p][v]))
        so = foglio(ay, "pv", "av provincia soggetto")
        if so:
            S = per_prov(so)
            S["ITALIA"] = somma(so)
            for p in CITTA + ["ITALIA"]:
                for v in ("PERSONA FISICA", "PERSONA GIURIDICA", "NON DEFINITO", "TOT"):
                    uso.append(dict(anno=ay, provincia=("Italia" if p == "ITALIA" else NOME[p]), tabella="soggetto", voce=v, valore=S[p][v]))
    return conf, carb, eur_prov, eur_com, eta_pot, uso, mc_eur, dieselmi


def euro_riga(ay, nome, d):
    g = lambda *ks: sum(d.get(k, 0) for k in ks)
    r = dict(anno=ay, territorio=nome, euro0=g("EURO 0"), euro1=g("EURO 1"), non_identificato=g("NON IDENTIFICATO"),
             euro0_1=g("EURO 0", "EURO 1"), euro2=g("EURO 2"), euro3=g("EURO 3"), euro4=g("EURO 4"),
             euro5=g("EURO 5", "EURO 5B"),
             euro6=g("EURO 6", "EURO 6A", "EURO 6B", "EURO 6C", "EURO 6D", "EURO 6D-TEMP", "EURO 6E", "EURO 6D TEMP"),
             non_contemplato=g("NON CONTEMPLATO"), non_definito=g("NON DEFINITO"), totale=d.get("TOT", 0))
    ctrl = sum(v for k, v in d.items() if isinstance(v, float) and k != "TOT")
    if abs(ctrl - r["totale"]) > 2:
        AVVISI.append("Euro %s %d: somma colonne %s diversa dal totale %s (colonne: %s)" % (
            nome, ay, ctrl, r["totale"], [k for k in d if k.startswith("EURO")]))
    return r


def euro_riga_moto(ay, nome, d):
    g = lambda *ks: sum(d.get(k, 0) for k in ks)
    return dict(anno=ay, territorio=nome, euro0_1=g("EURO 0", "EURO 1"), euro2=g("EURO 2"), euro3=g("EURO 3"),
                euro4=g("EURO 4"), euro5_6=g("EURO 5", "EURO 6", "EURO 6B"),
                non_contemplato=g("NON CONTEMPLATO"), non_definito=g("NON DEFINITO"), totale=d.get("TOT", 0))


# ----------------------------------------------------------------------------------------------------------
def parte_comune():
    """Serie di Milano (comune) 2007-2025: ds529 (parco, immatricolazioni, radiazioni) + ds530 (Euro)"""
    s = defaultdict(dict)
    with open(os.path.join(ROOT, "parcheggi", "raw", "comune_veicoli", "ds529.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["Attributo"] == "Autoveicoli generici - Autovetture":
                k = {"Parco veicolare circolante": "autovetture", "Immatricolazioni": "immatricolazioni",
                     "Radiazioni": "radiazioni"}[r["Tipo consistenza veicoli"]]
                s[int(r["Anno"])][k] = int(r["Valore"] or 0)
            if r["Attributo"] == "Autoveicoli generici - Motocicli":
                k = {"Parco veicolare circolante": "motocicli", "Immatricolazioni": "moto_immatr",
                     "Radiazioni": "moto_radiaz"}[r["Tipo consistenza veicoli"]]
                s[int(r["Anno"])][k] = int(r["Valore"] or 0)
    # popolazione ISTAT: 2007-2018 bilancio ricostruito (31/12), 2019-2025 POSAS (1/1 dell'anno dopo)
    pop = {}
    with open(os.path.join(ROOT, "popolazione", "pulito", "istat_bilancio_milano_2001_2018.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["Sesso"] == "Maschi e femmine" and r["Cittadinanza"] == "Tutte":
                pop[int(r["Anno"])] = int(r["Popolazione fine periodo"])
    for ay in ANNI:
        pop[ay] = pop_posas(ay + 1, "015_Milano")["Milano"]
    righe = []
    for y in sorted(s):
        d = s[y]
        righe.append(dict(anno=y, autovetture=d["autovetture"], motocicli=d["motocicli"], immatricolazioni=d["immatricolazioni"],
                          radiazioni=d["radiazioni"], moto_immatr=d["moto_immatr"], moto_radiaz=d["moto_radiaz"],
                          popolazione=pop[y], per1000_auto=round(1000 * d["autovetture"] / pop[y], 1),
                          per1000_moto=round(1000 * d["motocicli"] / pop[y], 1),
                          fonte_pop=("ISTAT bilancio ricostruito, 31/12" if y <= 2018 else "ISTAT POSAS 1/1 anno dopo")))
    # Euro delle autovetture: ds1081 (Comune, 2007-2020, completo di Euro 0) per il 2007-2018; ACI per il 2019-2025.
    # ds530 (Comune) NON ha le righe "EURO 0" nel 2007-2023: serve solo come controllo (vedi avvisi).
    e1081 = defaultdict(lambda: defaultdict(float))
    with open(os.path.join(RAW, "comune_ds1081", "ds1081.csv"), encoding="utf-8-sig") as f:
        rd = csv.reader(f, delimiter=";")
        next(rd)
        for r in rd:
            if len(r) >= 3:
                e1081[int(r[0])][r[1].strip().upper()] += float(r[2] or 0)
    e530 = defaultdict(lambda: defaultdict(float))
    with open(os.path.join(RAW, "comune_ds530", "ds530_categorie_euro_2007_2025.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["TIPO VEICOLO"] == "Autovetture":
                e530[int(r["ANNO"])][r["CATEGORIA"].upper()] += float(r["VEICOLI"] or 0)
    ev = []
    for y in range(2007, 2019):
        d = dict(e1081[y])
        d["NON DEFINITO"] = d.get("NON DEFINITO", 0) + d.pop("NON IDENTIFICATO", 0)
        rr = euro_riga(y, "Milano", dict(d, TOT=sum(d.values())))
        rr["fonte"] = "Comune di Milano ds1081"
        ev.append(rr)
        # controllo con ds530 (stesse classi tranne Euro 0 che in ds530 manca)
        for k in ("EURO 1", "EURO 2", "EURO 3", "EURO 4", "EURO 5"):
            if abs(e530[y].get(k, 0) - e1081[y].get(k, 0)) > 1:
                AVVISI.append("ds530 e ds1081 diversi nel %d per %s: %s contro %s" % (y, k, e530[y].get(k, 0), e1081[y].get(k, 0)))
        if e530[y].get("EURO 0", 0) != 0:
            AVVISI.append("ds530 ha Euro 0 nel %d" % y)
    return righe, ev, e530, e1081




# ----------------------------------------------------------------------------------------------------------
def parte_2017():
    """Fotografia 2017 delle autovetture dei residenti a Milano (Motorizzazione, ds545): solo aggregati."""
    p = os.path.join(RAW, "comune_ds545", "x", "parco_circolante_Lombardia-MILANO.csv")
    n = 0
    a = defaultdict(float)
    cnt = lambda k, v=1: a.__setitem__(k, a[k] + v)
    destinazioni = defaultdict(int)
    kws, massa, co2 = [], [], []
    ages_m = []
    with open(p, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f, delimiter=";")
        for r in rd:
            if r["tipo_veicolo"] == "Autoveicolo":
                destinazioni[r["destinazione"]] += 1
            if r["tipo_veicolo"] == "Motoveicolo":
                cnt("moto")
                continue
            if not r["destinazione"].startswith("AUTOVETTURA PER TRASPORTO DI PERSONE"):
                continue
            cnt("auto")
            al = r["alimentazione"]
            if al == "BENZ":
                cnt("f_benzina")
            elif al == "GASOL":
                cnt("f_gasolio")
            elif al in ("B/GPL", "GPL"):
                cnt("f_gpl")
            elif al in ("B/MET", "METANO"):
                cnt("f_metano")
            elif al.startswith("IBRIDO"):
                cnt("f_ibrido")
            elif al == "ELETTR":
                cnt("f_elettrico")
            else:
                cnt("f_altro")
            e = r["classe_euro"]
            cnt("euro_" + (e if e in "0123456" and e != "" else "nd"))
            try:
                k = float(r["kw"])
                kws.append(k)
                if k > 130:
                    cnt("kw_oltre130")
                if k > 100:
                    cnt("kw_oltre100")
                if k <= 70:
                    cnt("kw_fino70")
                cnt("kw_valido")
            except ValueError:
                pass
            try:
                m = float(r["massa_complessiva"])
                if m > 0:
                    cnt("massa_valida")
                    if m >= 2000:
                        cnt("massa_oltre2000")
                    if m >= 1800:
                        cnt("massa_oltre1800")
            except ValueError:
                pass
            try:
                c = float(r["emissioni_co2"])
                if c > 0:
                    cnt("co2_n"); cnt("co2_somma", c)
            except ValueError:
                pass
            y = r["data_immatricolazione"][:4]
            if y.isdigit():
                yy = int(y)
                cnt("anno_valido")
                if yy <= 2001:
                    cnt("imm_fino2001")
                if yy >= 2015:
                    cnt("imm_2015_2017")
                cnt("eta_somma", 2017 - yy)
            u = r["uso"]
            if u.startswith("DI TERZI DA LOCARE"):
                cnt("uso_locazione")
            elif u == "PROPRIO":
                cnt("uso_proprio")
            else:
                cnt("uso_altro")
            ei = r["eta_intestatario"].strip()
            if ei == "":
                cnt("intest_giuridica")
            else:
                cnt("intest_persona")
                if r["sesso"] == "F":
                    cnt("intest_donne")
                try:
                    ee = int(ei)
                    if ee >= 65:
                        cnt("intest_65")
                    if ee < 35:
                        cnt("intest_under35")
                except ValueError:
                    pass
    d = dict(a)
    d["destinazioni_top"] = sorted(destinazioni.items(), key=lambda x: -x[1])[:6]
    d["co2_media"] = d["co2_somma"] / d["co2_n"] if d.get("co2_n") else None
    d["eta_media"] = d["eta_somma"] / d["anno_valido"] if d.get("anno_valido") else None
    d["istantanea"] = "fine 2017 (ultima immatricolazione presente nel file: 27/10/2017)"
    return d


# ----------------------------------------------------------------------------------------------------------
def parte_areac():
    """Composizione dei passaggi in Area C (feriali normali, % su tutti i passaggi, NC compreso): copia dal filone area-c."""
    p = os.path.join(ROOT, "area-c", "pulito", "tabella_composizione_pct.csv")
    righe = []
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            righe.append({k: r[k] for k in ("y", "euro_euro0", "euro_euro1", "euro_euro2", "euro_euro3", "euro_euro4", "euro_euro5",
                                            "euro_euro6", "euro_nc", "alim_benzina", "alim_diesel", "alim_elettrico", "alim_gpl",
                                            "alim_metano", "alim_ibrido", "alim_nc", "tipo_moto")})
    return righe


def main():
    conf, carb, eur_prov, eur_com, eta_pot, uso, mc_eur, dieselmi = parte_aci()
    campi_conf = ["anno", "territorio", "tipo", "autovetture", "motocicli", "popolazione"]
    for r in conf:
        r["per1000_auto"] = round(1000 * r["autovetture"] / r["popolazione"], 1)
        r["per1000_moto"] = round(1000 * r["motocicli"] / r["popolazione"], 1)
    scrivi("confronto_citta.csv", conf, campi_conf + ["per1000_auto", "per1000_moto"])
    scrivi("carburante_province.csv", carb, ["anno", "provincia", "totale", "benzina", "gasolio", "ibrido", "elettrico", "gpl", "metano", "altro"])
    ce = ["anno", "territorio", "euro0", "euro1", "euro0_1", "euro2", "euro3", "euro4", "euro5", "euro6", "non_contemplato", "non_definito", "totale"]
    scrivi("euro_province.csv", eur_prov, ce)
    scrivi("euro_comuni.csv", eur_com, ce)
    scrivi("euro_milano_provincia_per_carburante.csv", dieselmi, ce)
    scrivi("euro_moto_comuni.csv", mc_eur, ["anno", "territorio", "euro0_1", "euro2", "euro3", "euro4", "euro5_6", "non_contemplato", "non_definito", "totale"])
    scrivi("eta_potenza_province.csv", eta_pot, ["anno", "provincia", "n_autovetture", "banda_vecchie", "vecchie16_pct", "banda_nuove", "ultimi2_pct",
                                                 "kw_fino70_pct", "kw_oltre100_pct", "kw_oltre130_pct", "cil_fino1200_pct", "cil_oltre2000_pct"])
    scrivi("bande_uso_soggetto.csv", uso, ["anno", "provincia", "tabella", "voce", "valore"])
    serie, ev, e530, e1081 = parte_comune()
    # controlli: ds1081 contro ds529 (totale), ACI contro ds1081 (2019-2020) e contro ds530 (2021-2025, senza Euro 0 fino al 2023)
    tot529 = {r["anno"]: r["autovetture"] for r in serie}
    for r in ev:
        if abs(r["totale"] - tot529[r["anno"]]) > 1:
            AVVISI.append("ds1081 totale %d = %s contro ds529 %s" % (r["anno"], r["totale"], tot529[r["anno"]]))
    aci_mi = {r["anno"]: r for r in eur_com if r["territorio"] == "Milano"}
    for y, r in aci_mi.items():
        ev.append(dict(r, tipo="Autovetture", fonte="ACI Autoritratto"))
        if r["totale"] != tot529[y]:
            AVVISI.append("ACI autovetture Milano %d = %s contro ds529 %s" % (y, r["totale"], tot529[y]))
        for k, kk in (("euro0", "EURO 0"), ("euro1", "EURO 1"), ("euro2", "EURO 2"), ("euro3", "EURO 3"), ("euro4", "EURO 4")):
            if y in e1081 and y <= 2020 and abs(r[k] - e1081[y].get(kk, 0)) > 1:
                AVVISI.append("ACI e ds1081 diversi nel %d per %s: %s contro %s" % (y, kk, r[k], e1081[y].get(kk, 0)))
            if k != "euro0" and abs(r[k] - e530[y].get(kk, 0)) > 1:
                AVVISI.append("ACI e ds530 diversi nel %d per %s: %s contro %s" % (y, kk, r[k], e530[y].get(kk, 0)))
        if y >= 2024 and abs(r["euro0"] - e530[y].get("EURO 0", 0)) > 1:
            AVVISI.append("ACI e ds530 diversi nel %d per Euro 0: %s contro %s" % (y, r["euro0"], e530[y].get("EURO 0", 0)))
    ev.sort(key=lambda r: r["anno"])
    scrivi("serie_milano_comune.csv", serie, ["anno", "autovetture", "motocicli", "immatricolazioni", "radiazioni", "moto_immatr", "moto_radiaz",
                                              "popolazione", "per1000_auto", "per1000_moto", "fonte_pop"])
    scrivi("euro_milano_comune_2007_2025.csv", ev, ["anno", "fonte", "euro0", "euro1", "euro2", "euro3", "euro4", "euro5", "euro6", "non_contemplato", "non_definito", "totale"])
    d17 = parte_2017()
    json.dump(d17, open(os.path.join(PUL, "milano_2017_motorizzazione.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("scritto milano_2017_motorizzazione.json")
    ac = parte_areac()
    scrivi("areac_composizione_pct.csv", ac, list(ac[0].keys()))
    with open(os.path.join(PUL, "avvisi_build.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(AVVISI) + "\n")
    print("AVVISI:", len(AVVISI))
    for a in AVVISI[:40]:
        print(" -", a)


if __name__ == "__main__":
    main()
