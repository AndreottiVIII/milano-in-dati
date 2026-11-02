"""Scarica i file grezzi di reati-citta/raw (rieseguibile: salta i file gia' presenti).

Uso:  python -I -X utf8 scarica.py <cartella reati-citta assoluta> [--forza]

- User-Agent dichiarato (nessuna imitazione di un browser), pausa di 20 s tra due richieste ISTAT.
- Scrive pulito/inventario_fonti.csv con data di scaricamento (data di oggi se scaricato ora,
  altrimenti la data di modifica del file) e sha256.
"""
import sys, os, time, hashlib, csv, datetime, urllib.request

UA = "milano-in-dati-research/1.0 (davide.caniatti@gmail.com)"
SDMX = "https://esploradati.istat.it/SDMXWS/rest/data/IT1,{flow},1.0/"
FILES = [
    # (percorso relativo, url, accept, descrizione, licenza)
    ("raw/istat/altridelps2.csv", SDMX.format(flow="73_1187_DF_DCCV_ALTRIDELPS_2"), "application/vnd.sdmx.data+csv;version=1.0.0",
     "ISTAT, Altri delitti denunciati dalle forze di polizia - per mese del commesso delitto (73_1187_DF_DCCV_ALTRIDELPS_2)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/DF_DCSS_BEST_PPC_1_GC.csv", SDMX.format(flow="DF_DCSS_BEST_PPC_1_GC"), "application/vnd.sdmx.data+csv;version=1.0.0",
     "ISTAT, Famiglie per percezione del rischio di criminalita' nella zona - province e grandi comuni (DF_DCSS_BEST_PPC_1_GC)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/DF_DCSS_BEST_PPC_6_GC.csv", SDMX.format(flow="DF_DCSS_BEST_PPC_6_GC"), "application/vnd.sdmx.data+csv;version=1.0.0",
     "ISTAT, Persone 14+ per percezione della sicurezza camminando al buio da soli - province e grandi comuni (DF_DCSS_BEST_PPC_6_GC)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/bes_territ7.csv", SDMX.format(flow="DF_BES_TERRIT_7"), "application/vnd.sdmx.data+csv;version=1.0.0",
     "ISTAT, BES territoriale - Sicurezza (DF_BES_TERRIT_7) [solo esplorato, non usato nella pagina]", "CC BY 4.0 (ISTAT)"),
    ("raw/comune_ds516/ds516.csv",
     "https://dati.comune.milano.it/dataset/2105f590-5592-4b85-a5f3-696e90b72bcd/resource/4fbbb6a9-cfb5-492e-8374-8ee245f85a3d/download/ds516_interventi_118_2004-2015.csv",
     "text/csv", "Comune di Milano, ds516 Interventi del 118 Milano: tipologia e criticita' (2004-2015)", "CC BY (Comune di Milano; licenza dichiarata dal portale: cc-by)"),
    ("raw/comune_ds516/ds516_package.json",
     "https://dati.comune.milano.it/api/3/action/package_show?id=ds516_interventi-del-118-milano-tipologia-e-criticita-2004-2015",
     "application/json", "Comune di Milano, scheda CKAN di ds516", "CC BY"),
]

def main():
    base = sys.argv[1]
    forza = "--forza" in sys.argv
    inv = []
    first_istat = True
    for rel, url, acc, desc, lic in FILES:
        p = os.path.join(base, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if forza or not os.path.exists(p):
            if "istat.it" in url and not first_istat:
                time.sleep(20)
            if "istat.it" in url:
                first_istat = False
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": acc})
            with urllib.request.urlopen(req, timeout=300) as r, open(p, "wb") as f:
                f.write(r.read())
            print("scaricato", rel)
        else:
            print("gia' presente", rel)
        data = open(p, "rb").read()
        d = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
        inv.append([rel, url, desc, lic, d, hashlib.sha256(data).hexdigest(), len(data)])
    os.makedirs(os.path.join(base, "pulito"), exist_ok=True)
    with open(os.path.join(base, "pulito", "inventario_fonti.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "url", "descrizione", "licenza", "data_scaricamento", "sha256", "byte"])
        w.writerows(inv)

if __name__ == "__main__":
    main()
