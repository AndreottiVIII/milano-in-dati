"""Unisce ISD giornaliero (pulito/isd) + GSOD (raw/noaa/gsod) -> pulito/giorni_neve_nebbia.csv,
inverni_neve_nebbia.csv (Nov-Mar, etichetta = anno di gennaio), totali_annuali.csv, completezza_per_anno.csv.
Uso: python -I costruisci_giorni.py <cartella_strand>"""
import sys, os, glob
import pandas as pd, numpy as np

base = sys.argv[1]
P = lambda *a: os.path.join(base, *a)
ST = {"160800-99999": ("LINATE", "16080099999"), "160660-99999": ("MALPENSA", "16066099999"), "160810-99999": ("LINATE_160810", "16081099999")}


def gsod(sid):
    fs = sorted(glob.glob(P("raw", "noaa", "gsod", sid, "*.csv")))
    d = pd.concat([pd.read_csv(f, dtype={"FRSHTT": str, "STATION": str}) for f in fs], ignore_index=True)
    o = pd.DataFrame({"date": d["DATE"]})
    fr = d["FRSHTT"].fillna("000000").str.zfill(6)
    o["gsod_fog"] = fr.str[0].astype(int)
    o["gsod_rain"] = fr.str[1].astype(int)
    o["gsod_snow"] = fr.str[2].astype(int)
    o["gsod_hail"] = fr.str[3].astype(int)
    o["gsod_thunder"] = fr.str[4].astype(int)
    sn = d["SNDP"].astype(float)
    o["gsod_sndp_cm"] = np.where(sn >= 999, np.nan, sn * 2.54)
    pr = d["PRCP"].astype(float)
    o["gsod_prcp_mm"] = np.where(pr >= 99, np.nan, pr * 25.4)
    o["gsod_prcp_flag"] = d["PRCP_ATTRIBUTES"].astype(str).str.strip()
    vi = d["VISIB"].astype(float)
    o["gsod_visib_km"] = np.where(vi >= 999, np.nan, vi * 1.609344)
    t = d["TEMP"].astype(float)
    o["gsod_tmean_c"] = np.where(t >= 9999, np.nan, (t - 32) / 1.8)
    o["gsod_present"] = 1
    return o


rows = []
for st, (name, sid) in ST.items():
    i = pd.read_csv(P("pulito", "isd", "isd_giorni_%s.csv" % st), dtype={"date": str})
    g = gsod(sid)
    m = i.merge(g, on="date", how="outer")
    m["station"] = name
    m["usaf_wban"] = st
    m["gsod_present"] = m["gsod_present"].fillna(0).astype(int)
    rows.append(m)
D = pd.concat(rows, ignore_index=True)
D["isd_present"] = D["n_obs"].notna().astype(int)


def b(c, thr=1):
    return np.where(D[c].isna(), np.nan, (D[c] >= thr).astype(float))


D["snow_depth_suspect"] = np.where(D["snow_depth_cm"].isna() & D["gsod_sndp_cm"].isna(), np.nan,
                                   ((D["snow_depth_cm"] > 60) | (D["gsod_sndp_cm"] > 60)).astype(float))
D["snow_depth_cm_raw"] = D["snow_depth_cm"]
D["snow_depth_cm"] = D["snow_depth_cm"].where(~(D["snow_depth_cm"] > 60))      # profondita > 60 cm = quasi certamente errore di decodifica
D["gsod_sndp_cm"] = D["gsod_sndp_cm"].where(~(D["gsod_sndp_cm"] > 60))
out = pd.DataFrame({
    "date": D["date"], "station": D["station"], "usaf_wban": D["usaf_wban"],
    "isd_n_obs": D["n_obs"], "isd_n_hours": D["n_hours"], "isd_n_synoptic_hours": D["syn_n_hours"],
    "isd_n_obs_with_presentweather": D["n_obs_presentweather"],
    "snow_obs_strict": b("snow_strict_n"), "snow_obs_wide": b("snow_wide_n"), "snow_heavy_obs": b("snow_heavy_n"),
    "snow_depth_isd_cm": D["snow_depth_cm"], "snow_depth_isd_cm_raw": D["snow_depth_cm_raw"], "snow_depth_suspect_gt60": D["snow_depth_suspect"],
    "snow_depth_isd_gt0": np.where(D["snow_depth_cm"].isna(), np.nan, (D["snow_depth_cm"] > 0).astype(float)),
    "snow_synoptic_hours": b("syn_snow_strict_n"), "snow_metar_text": b("metar_text_snow_n"),
    "fog_code_strict": b("fog_code_strict_n"), "fog_code_wide": b("fog_code_wide_n"),
    "fog_code_vis_lt1km": b("fog_code_vis_lt1km_n"),
    "vis_lt1km_any": np.where(D["min_vis_m"].isna(), np.nan, (D["min_vis_m"] < 1000).astype(float)),
    "fog_synoptic_code": b("syn_fog_code_strict_n"), "fog_synoptic_code_vis_lt1km": b("syn_fog_code_vis_lt1km_n"),
    "fog_metar_text": b("metar_text_fog_n"), "fog_metar_text_dense": b("metar_text_fogdense_n"),
    "min_vis_m": D["min_vis_m"], "n_metar_text": D["metar_text_n"], "n_metar_auto": D["metar_auto_n"],
    "isd_daily_summary_snow": D["at_snow"], "isd_daily_summary_fog": D["at_fog"],
    "gsod_fog": D["gsod_fog"], "gsod_snow": D["gsod_snow"], "gsod_sndp_cm": D["gsod_sndp_cm"],
    "gsod_snow_depth_gt0": np.where(D["gsod_sndp_cm"].isna(), np.nan, (D["gsod_sndp_cm"] > 0).astype(float)),
    "gsod_prcp_mm": D["gsod_prcp_mm"], "gsod_prcp_flag": D["gsod_prcp_flag"], "gsod_visib_km": D["gsod_visib_km"],
    "gsod_tmean_c": D["gsod_tmean_c"],
    "gsod_present": D["gsod_present"], "isd_present": D["isd_present"], "report_types": D["report_types"],
})
out = out.sort_values(["station", "date"]).reset_index(drop=True)
num = out.select_dtypes("number").columns
out[num] = out[num].round(2)
out.to_csv(P("pulito", "giorni_neve_nebbia.csv"), index=False, encoding="utf-8")
print("giorni_neve_nebbia.csv", len(out))

# ---------- inverni e annuali ----------
out["dt"] = pd.to_datetime(out["date"])
out["year"] = out["dt"].dt.year
out["month"] = out["dt"].dt.month
out["winter"] = np.where(out["month"] >= 11, out["year"] + 1, out["year"])
inv = out[out["month"].isin([11, 12, 1, 2, 3])].copy()
br = pd.read_csv(os.path.join(os.path.dirname(base), "temperature", "serie", "serie_unica.csv"), parse_dates=["date"], usecols=["date", "tmean"])
br["month"] = br["date"].dt.month
brw = br[br["month"].isin([11, 12, 1, 2, 3])].copy()
brw["winter"] = np.where(brw["month"] >= 11, brw["date"].dt.year + 1, brw["date"].dt.year)
brm = brw.groupby("winter")["tmean"].agg(brera_tmean_nov_mar="mean", brera_days="count").round(2)


def agg(x):
    r = {}
    r["days_isd_any"] = int(x["isd_present"].sum())
    r["days_isd_ge4h"] = int((x["isd_n_hours"] >= 4).sum())
    r["days_isd_ge8h"] = int((x["isd_n_hours"] >= 8).sum())
    r["days_gsod"] = int(x["gsod_present"].sum())
    for c, nm in [("snow_obs_strict", "snow_days_strict"), ("snow_obs_wide", "snow_days_wide"), ("snow_heavy_obs", "snow_days_heavy"),
                  ("snow_depth_isd_gt0", "snow_days_depth_isd"), ("snow_synoptic_hours", "snow_days_synoptic"),
                  ("gsod_snow", "snow_days_gsod_flag"), ("gsod_snow_depth_gt0", "snow_days_gsod_depth"),
                  ("fog_code_strict", "fog_days_code_strict"), ("fog_code_wide", "fog_days_code_wide"),
                  ("fog_code_vis_lt1km", "fog_days_code_vis_lt1km"),
                  ("vis_lt1km_any", "fog_days_vis_lt1km_any"), ("fog_synoptic_code", "fog_days_synoptic"),
                  ("fog_metar_text", "fog_days_metar_text"), ("gsod_fog", "fog_days_gsod_flag")]:
        r[nm] = int(x[c].sum()) if x[c].notna().any() else np.nan
    u = ((x["snow_obs_strict"] == 1) | (x["snow_depth_isd_gt0"] == 1) | (x["gsod_snow"] == 1) | (x["gsod_snow_depth_gt0"] == 1))
    r["snow_days_union_any"] = int(u.sum())
    r["max_snow_depth_isd_cm"] = x["snow_depth_isd_cm"].max()
    r["max_snow_depth_gsod_cm"] = x["gsod_sndp_cm"].max()
    r["gsod_prcp_sum_on_snow_days_mm"] = x.loc[x["gsod_snow"] == 1, "gsod_prcp_mm"].sum(min_count=1)
    r["gsod_prcp_max_on_snow_day_mm"] = x.loc[x["gsod_snow"] == 1, "gsod_prcp_mm"].max()
    r["gsod_tmean_nov_mar_c"] = x["gsod_tmean_c"].mean()
    return pd.Series(r)


W = inv.groupby(["station", "winter"]).apply(agg, include_groups=False).reset_index()


def expected(w):
    leap = (w % 4 == 0 and (w % 100 != 0 or w % 400 == 0))
    return 30 + 31 + 31 + (29 if leap else 28) + 31


W.insert(2, "days_expected", W["winter"].map(expected))
W["pct_days_ge4h"] = (100 * W["days_isd_ge4h"] / W["days_expected"]).round(0)
W["pct_days_gsod"] = (100 * W["days_gsod"] / W["days_expected"]).round(0)
W["winter_complete_isd"] = np.where(W["pct_days_ge4h"] >= 90, "si", "no")
W = W.merge(brm, left_on="winter", right_index=True, how="left")
W[W.select_dtypes("number").columns] = W.select_dtypes("number").round(2)
W = W[(W["days_isd_any"] > 0) | (W["days_gsod"] > 0)]
W.to_csv(P("pulito", "inverni_neve_nebbia.csv"), index=False, encoding="utf-8")
print("inverni", len(W))


def agg_y(x):
    return pd.Series(dict(
        days_isd_ge4h=int((x["isd_n_hours"] >= 4).sum()), days_gsod=int(x["gsod_present"].sum()),
        fog_days_code_strict=x["fog_code_strict"].sum(min_count=1), fog_days_code_wide=x["fog_code_wide"].sum(min_count=1),
        fog_days_code_vis_lt1km=x["fog_code_vis_lt1km"].sum(min_count=1), fog_days_vis_lt1km_any=x["vis_lt1km_any"].sum(min_count=1),
        fog_days_synoptic=x["fog_synoptic_code"].sum(min_count=1), fog_days_metar_text=x["fog_metar_text"].sum(min_count=1),
        fog_days_gsod_flag=x["gsod_fog"].sum(min_count=1),
        snow_days_strict=x["snow_obs_strict"].sum(min_count=1), snow_days_gsod_flag=x["gsod_snow"].sum(min_count=1)))


Y = out.groupby(["station", "year"]).apply(agg_y, include_groups=False).reset_index()
Y.to_csv(P("pulito", "totali_annuali.csv"), index=False, encoding="utf-8")

rows = []
for st, (name, sid) in ST.items():
    dg = pd.read_csv(P("pulito", "isd", "isd_diagnostica_%s.csv" % st)).fillna(0).set_index("year")
    ys = out[out["station"] == name].groupby("year")
    for y, x in ys:
        r = dict(station=name, year=y, days_in_year=366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365,
                 days_isd_any=int(x["isd_present"].sum()), days_isd_ge4h=int((x["isd_n_hours"] >= 4).sum()),
                 days_isd_ge20h=int((x["isd_n_hours"] >= 20).sum()),
                 mean_hours_per_day=round(x["isd_n_hours"].mean(), 1), mean_synoptic_hours_per_day=round(x["isd_n_synoptic_hours"].mean(), 1),
                 days_gsod=int(x["gsod_present"].sum()))
        if y in dg.index:
            d = dg.loc[y]
            n = d["obs"]
            r.update(isd_obs=int(n), pct_obs_with_presentweather=round(100 * d.get("pw_obs", 0) / n), pct_obs_with_visibility=round(100 * d.get("vis_ok", 0) / n),
                     n_synop_reports=int(d.get("type_FM-12", 0) + d.get("type_SY-MT", 0) + d.get("type_SY-SA", 0)),
                     n_metar_speci_reports=int(d.get("type_FM-15", 0) + d.get("type_FM-16", 0) + d.get("type_SAO", 0)),
                     n_obs_flagged_AUTO_type=int(d.get("type_AUTO", 0)), n_obs_aw_automatic_weather=int(d.get("aw_obs", 0)),
                     n_metar_text_full=int(d.get("metar_full", 0)), n_metar_AUTO_in_text=int(d.get("metar_auto", 0)),
                     pct_metar_text_AUTO=round(100 * d.get("metar_auto", 0) / d["metar_full"], 1) if d.get("metar_full", 0) > 0 else np.nan,
                     n_snowdepth_reports=int(d.get("aj_obs", 0)))
        rows.append(r)
C = pd.DataFrame(rows)
C.to_csv(P("pulito", "completezza_per_anno.csv"), index=False, encoding="utf-8")
print("completezza", len(C))
