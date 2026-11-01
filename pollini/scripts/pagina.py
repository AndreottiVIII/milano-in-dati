"""Prepara i dati della pagina docs/pollini/ (solo valori aggregati, niente tabella giornaliera da 790k righe).

Uso: python -I -X utf8 pagina.py <P = cartella pollini assoluta> <M = cartella milano-in-dati assoluta>
Legge:  P/pulito/*.csv (prodotti da build.py, analisi.py, regione_ambrosia.py), P/raw/ats_milano/bollettini/Calendario*.pdf
        (solo per leggere i colori delle caselle del calendario ATS: il PDF non viene ripubblicato),
        M/temperature/serie/serie_unica.csv
Scrive: P/pulito/calendario_ats_milano.csv
        M/docs/pollini/data/pollini.json  (tutto quello che serve alla pagina)
        M/docs/pollini/data/*.csv         (copie degli aggregati, scaricabili)
Rieseguibile: sovrascrive i file.
"""
import csv, json, os, shutil, sys, glob
import numpy as np
import pandas as pd

ROW_NAMES = ["Alnus", "Betula", "Cannabaceae", "Cheno/Amaranthaceae", "Ambrosia", "Artemisia", "Carpinus", "Ostrya", "Corylus",
             "Cupressaceae/Taxaceae", "Castanea", "Fagus", "Quercus", "Gramineae", "Fraxinus", "Olea", "Cedrus", "Pinus",
             "Plantaginaceae", "Platanaceae", "Polygonaceae", "Populus", "Salix", "Urticaceae"]

TAXA = [  # chiave POLLnet, nome, tipo, mesi temperatura, riga calendario ATS
    ("Corylus", "Nocciolo", "albero", (1, 2), "Corylus"),
    ("Alnus", "Ontano", "albero", (1, 2), "Alnus"),
    ("Cupressaceae/Taxaceae", "Cipressi e affini", "albero", (1, 2), "Cupressaceae/Taxaceae"),
    ("Platanaceae", "Platano", "albero", (2, 3), "Platanaceae"),
    ("Betula", "Betulla", "albero", (2, 3), "Betula"),
    ("Fraxinus", "Frassino", "albero", (2, 3), "Fraxinus"),
    ("Quercus", "Quercia", "albero", (3, 4), "Quercus"),
    ("Gramineae", "Graminacee", "erba", (3, 4), "Gramineae"),
    ("Urticaceae", "Urticacee (parietaria)", "erba", (3, 4), "Urticaceae"),
    ("Artemisia", "Artemisia", "erba", (6, 7), "Artemisia"),
    ("Ambrosia", "Ambrosia", "erba", (6, 7), "Ambrosia"),
]


def calendario_ats(P):
    """Legge le caselle colorate del calendario ATS Milano (immagine nel PDF): bianco=assente, giallo=bassa, arancione=media, rosso=alta."""
    out = os.path.join(P, "pulito", "calendario_ats_milano.csv")
    pdfs = glob.glob(os.path.join(P, "raw", "ats_milano", "bollettini", "Calendario*.pdf"))
    try:
        import pymupdf as fitz
    except Exception:
        try:
            import fitz
        except Exception:
            fitz = None
    if pdfs and fitz:
        from PIL import Image
        import io
        d = fitz.open(pdfs[0])
        p = d[0]
        best = None
        for im in p.get_images(full=True):
            pix = fitz.Pixmap(d, im[0])
            if pix.width == 842 and pix.height == 437:
                best = pix
        if best is not None:
            img = np.array(Image.open(io.BytesIO(best.tobytes("png"))).convert("RGB")).astype(int)
            rows = []
            for r, n in enumerate(ROW_NAMES):
                y = int(48.5 + 16 * r + 8)
                for c in range(36):
                    x = int(204.5 + 17.6 * c + 8.8)
                    R, G, B = img[y - 3:y + 4, x - 3:x + 4].reshape(-1, 3).mean(0)
                    k = "0" if B > 200 else ("1" if G > 200 else ("2" if G > 110 else "3"))
                    rows.append((n, c + 1, k))
            with open(out, "w", encoding="utf8", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["riga", "decade", "classe"])  # decade 1-36 (3 per mese); classe 0 assente 1 bassa 2 media 3 alta
                w.writerows(rows)
    c = pd.read_csv(out, sep=";", dtype={"classe": str})
    return {n: "".join(g.sort_values("decade").classe) for n, g in c.groupby("riga")}


def num(x, d=2):
    return None if pd.isna(x) else round(float(x), d)


def main():
    P, M = sys.argv[1], sys.argv[2]
    pul = os.path.join(P, "pulito")
    dst = os.path.join(M, "docs", "pollini", "data")
    os.makedirs(dst, exist_ok=True)
    S = pd.read_csv(os.path.join(pul, "stagioni_taxon_anno.csv"), sep=";")
    ST = pd.read_csv(os.path.join(pul, "stazioni.csv"), sep=";")
    RS = pd.read_csv(os.path.join(pul, "riepilogo_taxon_stazione.csv"), sep=";")
    TR = pd.read_csv(os.path.join(pul, "tendenze_regionali.csv"), sep=";")
    TS = pd.read_csv(os.path.join(pul, "tendenze_stazione.csv"), sep=";")
    IR = pd.read_csv(os.path.join(pul, "indicatore_regionale_anno.csv"), sep=";")
    LT = pd.read_csv(os.path.join(pul, "legame_temperature.csv"), sep=";")
    AL = pd.read_csv(os.path.join(pul, "alberi_contesto.csv"), sep=";")
    WY = pd.read_csv(os.path.join(pul, "anni_peggiori.csv"), sep=";")
    AM = pd.read_csv(os.path.join(pul, "ambrosia_prima_dopo_2013.csv"), sep=";")
    AR = pd.read_csv(os.path.join(pul, "ambrosia_regione_lombardia.csv"), sep=";")
    ctrl = json.load(open(os.path.join(pul, "controlli_pulizia.json"), encoding="utf8"))
    cal = calendario_ats(P)

    # ---- temperature di Brera: media dei mesi che precedono la stagione, stessa regola di analisi.py
    tt = pd.read_csv(os.path.join(M, "temperature", "serie", "serie_unica.csv"), parse_dates=["date"])
    tt["anno"] = tt.date.dt.year
    tt["mese"] = tt.date.dt.month

    def media_mesi(mesi):
        sel = tt[tt.mese.isin(mesi)]
        g = sel.groupby("anno").agg(t=("tmean", "mean"), n=("tmean", "count"))
        return g[g.n >= 0.8 * 28 * len(mesi)]["t"]

    out = {"meta": {"scaricato": "2026-11-01", "controlli": ctrl, "stagioni_totali": int(len(S)), "stagioni_valide": int(S.valida.sum()),
                    "note_scarto": S[~S.valida].nota.value_counts().to_dict(),
                    "soglie": {"integrale_min": 30, "copertura_finestra": 0.75, "copertura_attesa": 0.80, "giorni_anno_min": 200}}}
    out["taxa"] = [dict(k=k, nome=n, tipo=t, mesi_temp=list(m), ats=a, scheda_ats=cal.get(a, "")) for k, n, t, m, a in TAXA]
    out["stazioni"] = [dict(c=r.STAT_CODE, id=int(r.STAT_ID), n=r.STAT_NAME_I, reg=r.REGI_NAME_I, lat=round(r.LATITUDE, 4),
                            lon=round(r.LONGITUDE, 4), km=float(r.km_da_milano_duomo), prima=r.prima, ultima=r.ultima,
                            giorni=int(r.giorni_con_dati)) for r in ST.itertuples()]
    # stagioni per taxon e stazione: [anno, valida, inizio_doy, picco_doy, fine_doy, integrale, giorni_ge_medio, nota]
    stag = {}
    for (tx, stz), g in S.groupby(["taxon", "stazione"]):
        stag.setdefault(tx, {})[stz] = [[int(r.anno), int(bool(r.valida)), num(r.inizio_doy, 0), num(r.picco_doy, 0), num(r.fine_doy, 0),
                                         num(r.integrale, 0), num(r.giorni_ge_medio, 0), (r.nota if isinstance(r.nota, str) else "")]
                                        for r in g.sort_values("anno").itertuples()]
    out["stagioni"] = stag
    out["tipico"] = {tx: {r.stazione: dict(n=int(r.anni_validi), primo=int(r.primo), ultimo=int(r.ultimo), ini=num(r.inizio_doy, 0), pic=num(r.picco_doy, 0),
                                            fin=num(r.fine_doy, 0), dur=num(r.durata_mediana, 0), integ=num(r.integrale_mediano, 0),
                                            piccov=num(r.picco_valore_mediano, 0), gmed=num(r.giorni_ge_medio_mediani, 0))
                          for r in g.itertuples()} for tx, g in RS.groupby("taxon")}
    out["indicatore"] = {tx: {m: [[int(r.anno), round(r.anomalia_mediana, 3), int(r.n_stazioni)] for r in h.sort_values("anno").itertuples()]
                              for m, h in g.groupby("metrica")} for tx, g in IR.groupby("taxon")}
    out["trend_reg"] = {tx: {r.metrica: dict(n=int(r.n), anni=r.anni, pend=num(r.pendenza_dec, 2), lo=num(r.ic95_basso_dec, 2), hi=num(r.ic95_alto_dec, 2),
                                             p=num(r.p_mk, 3), f=num(r.fattore_integrale_per_decennio, 2), flo=num(r.fattore_ic95_basso, 2),
                                             fhi=num(r.fattore_ic95_alto, 2)) for r in g.itertuples()} for tx, g in TR.groupby("taxon")}
    ts = {}
    for r in TS.itertuples():
        ts.setdefault(r.taxon, {}).setdefault(r.stazione, {})[r.metrica] = dict(
            n=int(r.n), pend=num(r.pendenza_per_decennio, 2), lo=num(r.ic95_basso_dec, 2), hi=num(r.ic95_alto_dec, 2), p=num(r.p_mk, 3),
            f=num(r.fattore_integrale_per_decennio, 2))
    out["trend_staz"] = ts
    # temperature
    leg = []
    for r in LT.itertuples():
        leg.append(dict(taxon=r.taxon, serie=r.serie, mesi=r.mesi_temperatura, n=int(r.n_anni), anni=r.anni, rho=num(r.spearman_rho), p=num(r.p, 3),
                        gpg=num(r.giorni_per_grado), se=num(r.errore_std), rho_d=num(r.rho_senza_tendenza), p_d=num(r.p_senza_tendenza, 3),
                        tend=num(r.tendenza_temp_C_per_decennio)))
    out["legame"] = leg
    pts = {}
    for k, n, t, m, a in TAXA:
        gm = media_mesi(m)
        nov = {r[0]: r[2] for r in stag.get(k, {}).get("NO1", []) if r[1] and r[2] is not None}
        reg = {r[0]: r[1] for r in out["indicatore"].get(k, {}).get("inizio_doy", [])}
        pts[k] = [[int(y), round(float(gm[y]), 2), nov.get(y), reg.get(y)] for y in sorted(gm.index) if 2007 <= y <= 2026 and (y in nov)]
    out["punti_temp"] = pts
    ma = media_mesi((3, 4))
    out["brera_marapr"] = [[int(y), round(float(v), 2)] for y, v in ma.items() if 2007 <= y <= 2026]
    out["calendario_ats"] = cal
    out["alberi"] = [dict(g=r.gruppo, n=int(r.alberi_2025), q=float(r.quota_pct)) for r in AL.itertuples()]
    out["peggiori"] = [dict(taxon=r.taxon, pos=int(r.posizione), anno=int(r.anno), f=float(r.fattore_sulla_media), n=int(r.n_stazioni),
                            st=r.integrale_per_stazione) for r in WY.itertuples()]
    out["ambrosia_2013"] = [{k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in row.items()} for row in AM.to_dict("records")]
    out["ambrosia_regione"] = [dict(anno=int(r.anno), st=r.stazione, mx=int(r.massimo_giornaliero_granuli_m3),
                                    tot=(None if pd.isna(r.totale_stagionale_granuli_m3) else int(r.totale_stagionale_granuli_m3)), fonte=r.fonte)
                               for r in AR.itertuples()]
    json.dump(out, open(os.path.join(dst, "pollini.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    for f in ["stagioni_taxon_anno.csv", "riepilogo_taxon_stazione.csv", "tendenze_stazione.csv", "tendenze_regionali.csv",
              "indicatore_regionale_anno.csv", "legame_temperature.csv", "stazioni.csv", "ambrosia_prima_dopo_2013.csv",
              "ambrosia_regione_lombardia.csv", "alberi_contesto.csv", "anni_peggiori.csv", "calendario_ats_milano.csv"]:
        shutil.copy(os.path.join(pul, f), os.path.join(dst, f))
    print("pollini.json", os.path.getsize(os.path.join(dst, "pollini.json")), "byte")


if __name__ == "__main__":
    main()
