"""Pulizia: dai CSV grezzi POLLnet (raw/ispra/concentrazioni) alla tabella lunga pulita.

Uso: python -I -X utf8 build.py <P = cartella pollini assoluta>
Scrive:
  P/pulito/concentrazioni_giornaliere.csv   (data;stazione;stat_id;taxon;livello;gruppo;granuli_m3)
  P/pulito/stazioni.csv                      (stazioni scaricate con coordinate e distanza da Milano)
  P/pulito/controlli_pulizia.json            (cosa e' stato scartato e perche')
Niente viene corretto: i valori negativi, nulli, le date future e la data 1899-12-30 (zero di Excel)
vengono ESCLUSI e contati. Le unita' sono granuli per metro cubo d'aria, media giornaliera.
"""
import csv, glob, json, math, os, sys
import pandas as pd

OGGI = "2026-11-01"  # data dello scarico: date successive = errore di data
MILANO = (45.4642, 9.1900)  # Duomo, solo per la distanza


def km(lat, lon):
    r = 6371
    p1, p2 = math.radians(MILANO[0]), math.radians(lat)
    dl = math.radians(lon - MILANO[1])
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main():
    P = sys.argv[1]
    raw = os.path.join(P, "raw", "ispra")
    out = os.path.join(P, "pulito")
    os.makedirs(out, exist_ok=True)
    fs = sorted(glob.glob(os.path.join(raw, "concentrazioni", "*.csv")))
    d = pd.concat([pd.read_csv(f, dtype={"REMA_DATE": str}) for f in fs], ignore_index=True)
    ctrl = {"righe_grezze": int(len(d))}
    ctrl["senza_valore"] = int(d.REMA_CONCENTRATION.isna().sum())
    d = d[d.REMA_CONCENTRATION.notna()]
    neg = d.REMA_CONCENTRATION < 0
    ctrl["valori_negativi"] = int(neg.sum())
    ctrl["valori_negativi_per_stazione"] = d[neg].groupby("STAT_CODE").size().to_dict()
    d = d[~neg]
    nodate = d.REMA_DATE.isna() | (d.REMA_DATE < "1990-01-01")
    ctrl["data_mancante_o_prima_del_1990"] = int(nodate.sum())
    d = d[~nodate]
    fut = d.REMA_DATE > OGGI
    ctrl["date_future_dopo_scarico"] = int(fut.sum())
    ctrl["date_future_per_stazione"] = d[fut].groupby("STAT_CODE").REMA_DATE.agg(["min", "max", "count"]).astype(str).to_dict("index")
    d = d[~fut]
    dup = d.duplicated(["STAT_ID", "REMA_DATE", "PART_ID"], keep="first")
    ctrl["duplicati_stazione_data_taxon"] = int(dup.sum())
    d = d[~dup]
    t = pd.DataFrame({
        "data": d.REMA_DATE,
        "stazione": d.STAT_NAME_I,
        "codice_stazione": d.STAT_CODE,
        "stat_id": d.STAT_ID,
        "taxon": d.PART_NAME_L,
        "livello": d.PART_LEVEL,
        "gruppo": d.PART_PARENT_NAME_L,
        "granuli_m3": d.REMA_CONCENTRATION,
    }).sort_values(["codice_stazione", "data", "livello", "taxon"])
    t.to_csv(os.path.join(out, "concentrazioni_giornaliere.csv"), sep=";", index=False)
    ctrl["righe_pulite"] = int(len(t))
    # arrotondamenti: i valori sono interi o con decimali?
    ctrl["valori_non_interi"] = int((t.granuli_m3 % 1 != 0).sum())
    # stazioni
    st = pd.read_csv(os.path.join(raw, "stazioni.csv"))
    st = st[st.STAT_ID.isin(t.stat_id.unique())]
    st["km_da_milano_duomo"] = [round(km(a, b), 1) for a, b in zip(st.LATITUDE, st.LONGITUDE)]
    cov = t.groupby("stat_id").data.agg(prima="min", ultima="max", giorni_con_dati="nunique")
    st = st.merge(cov, left_on="STAT_ID", right_index=True)
    st[["STAT_ID", "STAT_CODE", "STAT_NAME_I", "REGI_NAME_I", "LATITUDE", "LONGITUDE",
        "km_da_milano_duomo", "prima", "ultima", "giorni_con_dati"]].to_csv(
        os.path.join(out, "stazioni.csv"), sep=";", index=False)
    json.dump(ctrl, open(os.path.join(out, "controlli_pulizia.json"), "w", encoding="utf8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(ctrl, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
