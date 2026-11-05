"""Interroga le tavole pubbliche di demo.istat.it (stesso modulo POST della pagina web, nessuna registrazione, nessun login)
e salva la risposta JSON grezza in raw/istat_demo/. Una richiesta ogni 2 secondi.
Uso: python -I -X utf8 download_istat_demo.py <raw_dir>"""
import sys, os, json, time, datetime, hashlib, urllib.parse, urllib.request
raw = os.path.join(sys.argv[1], "istat_demo"); os.makedirs(raw, exist_ok=True)
MI = dict(ripartizione="1", regione="03", provincia="015")
def req(name, app, q, **f):
    return (name, app, q, f)
R = [
 req("ma1_q1_comune_milano_rito", "MA1", 1, a="9999", comune="015146", **MI),
 req("ma1_q1_comuni_provincia_milano_rito", "MA1", 1, a="9999", comune="000000", **MI),
 req("ma1_q1_italia_rito", "MA1", 1, a="9999", ripartizione="IT"),
 req("ma1_q3_indicatori_provincia_milano", "MA1", 3, a="9999", **MI),
 req("ma1_q3_indicatori_italia", "MA1", 3, a="9999", ripartizione="IT"),
 req("ma1_q3_indicatori_lombardia", "MA1", 3, a="9999", ripartizione="1", regione="03", provincia="000"),
 req("ma1_q4_eta_media_sposi_provincia_milano", "MA1", 4, a="9999", sesso="1", **MI),
 req("ma1_q4_eta_media_spose_provincia_milano", "MA1", 4, a="9999", sesso="2", **MI),
 req("ma1_q4_eta_media_sposi_italia", "MA1", 4, a="9999", sesso="1", ripartizione="IT"),
 req("ma1_q4_eta_media_spose_italia", "MA1", 4, a="9999", sesso="2", ripartizione="IT"),
 req("ma3_q1_tipologia_coppia_provincia_milano", "MA3", 1, a="9999", territorio="015", tipodato="1"),
 req("ma3_q1_tipologia_coppia_italia", "MA3", 1, a="9999", territorio="IT", tipodato="1"),
 req("ma3_q1_tipologia_coppia_lombardia", "MA3", 1, a="9999", territorio="03", tipodato="1"),
 req("ma3_q1_tipologia_coppia_provincia_monza", "MA3", 1, a="9999", territorio="108", tipodato="1"),
 req("ma1_q3_indicatori_provincia_monza", "MA1", 3, a="9999", ripartizione="1", regione="03", provincia="108"),
 req("ma3_q3_rito_tipologia_provincia_milano", "MA3", 3, a="9999", territorio="015", tipodato="1"),
 req("ma3_q3_rito_tipologia_italia", "MA3", 3, a="9999", territorio="IT", tipodato="1"),
 req("ma4_q1_rito_serie_storica", "MA4", 1, tipodato="1"),
 req("ma4_q3_tipologia_coppia_serie_storica", "MA4", 3, tipodato="1"),
 req("ma4_q4_sposi_classe_eta_serie_storica", "MA4", 4, sesso="1"),
 req("ma4_q4_spose_classe_eta_serie_storica", "MA4", 4, sesso="2"),
 req("nu1_q1_primonuzialita_sposi_regioni", "NU1", 1, indicatore="1", territorio="REG"),
 req("nu1_q1_primonuzialita_spose_regioni", "NU1", 1, indicatore="4", territorio="REG"),
 req("nu1_q1_eta_media_sposi_primo_matrimonio_regioni", "NU1", 1, indicatore="7", territorio="REG"),
 req("nu1_q1_eta_media_spose_primo_matrimonio_regioni", "NU1", 1, indicatore="10", territorio="REG"),
 req("nu1_q1_eta_media_sposi_primo_matrimonio_ripartizioni", "NU1", 1, indicatore="7", territorio="RIP"),
 req("nu1_q1_eta_media_spose_primo_matrimonio_ripartizioni", "NU1", 1, indicatore="10", territorio="RIP"),
 req("uc2_q1_unioni_sesso_mese_provincia_milano", "UC2", 1, a="9999", **MI),
 req("uc2_q1_unioni_sesso_mese_italia", "UC2", 1, a="9999", ripartizione="IT"),
 req("uc4_q1_unioni_ripartizione", "UC4", 1, tipovalore="1"),
 req("uc4_q4_unioni_grandi_comuni_milano", "UC4", 4, tipovalore="1", grandicomuni="015146"),
 req("uc4_q4_unioni_grandi_comuni_totale", "UC4", 4, tipovalore="1", grandicomuni="777777"),
]
if len(sys.argv) > 2: R = [r for r in R if sys.argv[2] in r[0]]
log = open(os.path.join(sys.argv[1], "download_log.csv"), "a", encoding="utf-8")
for name, app, q, f in R:
    dst = os.path.join(raw, name + ".json")
    if os.path.exists(dst): continue
    d = {"query": str(q)}; d.update(f)
    d.update({"hid-i": app, "hid-a": "2024", "hid-l": "it", "hid-cat": ("FE2" if app == "NU1" else "MAT"), "hid-dati": "dati-form-%d" % (q-1), "hid-tavola": "tavola-form-%d" % (q-1)})
    r = urllib.request.Request("https://demo.istat.it/app/RPCCerca.php", data=urllib.parse.urlencode(d).encode(), headers={"User-Agent": "milano-in-dati/1.0"})
    body = urllib.request.urlopen(r, timeout=90).read()
    open(dst, "wb").write(body)
    ok = json.loads(body).get("Status")
    h = hashlib.sha256(body).hexdigest()[:16]
    log.write(f"{datetime.date.today()};istat_demo/{name};json;POST https://demo.istat.it/app/RPCCerca.php {urllib.parse.urlencode(d)};{len(body)};{h};;CC-BY 4.0 (note legali Istat)\n"); log.flush()
    print(name, len(body), ok); time.sleep(2)
