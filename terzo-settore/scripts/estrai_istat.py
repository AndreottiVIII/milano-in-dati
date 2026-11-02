"""Estrae dai due file ISTAT (censimento istituzioni non profit 2011 e 2015, dati comunali) le righe di Milano e di alcune grandi citta'.
Uso: python -I -X utf8 estrai_istat.py <terzo-settore_dir assoluto>
Legge raw/istat/ds_N01GCOM/estratto/... e ds_N01CCOM/estratto/... (zip ISTAT scaricati da esploradati.istat.it il 2/11/2026, estratti a mano da questo script se mancano)
Scrive pulito/istat_N01GCOM_citta.csv e pulito/istat_N01CCOM_citta.csv (codici originali; i nomi si aggiungono dopo)."""
import sys, os, csv, zipfile, glob
T = sys.argv[1]
CITTA = {"015146": "Milano", "001272": "Torino", "058091": "Roma", "063049": "Napoli", "037006": "Bologna", "048017": "Firenze",
         "010025": "Genova", "082053": "Palermo", "072006": "Bari", "027042": "Venezia", "023091": "Verona", "028060": "Padova",
         "032006": "Trieste", "087015": "Catania", "083048": "Messina", "017029": "Brescia", "034027": "Parma", "100005": "Prato"}
for sigla, cols in [("N01GCOM", ["territorio", "tipo_dato", "icnpo", "tipo_attivita", "finanziamento", "orientamento", "risorsa_umana", "anno", "valore", "flag"]),
                    ("N01CCOM", ["territorio", "tipo_dato", "icnpo", "forma_giuridica", "risorsa_umana", "classe", "anno", "valore", "flag"])]:
    d = os.path.join(T, "raw", "istat", f"ds_{sigla}")
    zp = os.path.join(d, f"DICA_{sigla}-data.zip")
    p = glob.glob(os.path.join(d, "estratto", "CSV - DATI SOLO CODICI*", "*.csv"))
    if not p:
        zipfile.ZipFile(zp).extractall(os.path.join(d, "estratto"))
        p = glob.glob(os.path.join(d, "estratto", "CSV - DATI SOLO CODICI*", "*.csv"))
    n = 0; tot = 0
    with open(p[0], encoding="utf8") as f, open(os.path.join(T, "pulito", f"istat_{sigla}_citta.csv"), "w", newline="", encoding="utf8") as o:
        w = csv.writer(o); w.writerow(["citta"] + cols)
        for l in f:
            tot += 1
            r = l.rstrip("\r\n").split("|")
            if r[0] in CITTA:
                w.writerow([CITTA[r[0]]] + r); n += 1
    print(sigla, "righe totali", tot, "righe citta'", n)
