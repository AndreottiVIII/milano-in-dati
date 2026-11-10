"""Scarica da dati.lombardia.it (Socrata, CENED+2, bbky-sde5) le colonne che servono per i soli attestati di Milano.
Uso: python -I -X utf8 01_scarica_cened2.py <cartella case-energia>
Regole: User-Agent generico, nessun login, 1 secondo tra una richiesta e l'altra (Crawl-delay del robots.txt).
Scrive raw/cened2_milano.csv (non va online: contiene gli indirizzi)."""
import sys, os, time, csv, json, urllib.request, urllib.parse
root = sys.argv[1]
COL = ['cod_ape','data_ins','residenziale','comune_catastale','indirizzo','sez_censimento','anno_costruzione','classe_energetica',
       'emissioni_co2','ep_gl_nren','superf_utile_riscaldata','nuova_costruzione','passaggio_proprieta','locazione',
       'ristrutturazione_importante','riqualificazione_energetica','climatizzazione_invernale','vettore_energetico',
       'ci_tipo_impianto_1','ci_vettore_energetico_1','ci_anno_installazione_1','consumi_teleriscaldamento','consumi_gas_naturale',
       'consumi_energia_elettrica','consumi_gasolio','consumi_gpl','consumi_biomasse_solide','consumi_solare_fotovoltaico','edificio_energia_quasi_zero']
H = {'User-Agent': 'milano-in-dati/1.0'}
URL = 'https://www.dati.lombardia.it/resource/bbky-sde5.json?'
out = os.path.join(root, 'raw', 'cened2_milano.csv')
n = 0; off = 0; PAGE = 50000
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(COL)
    while True:
        q = {'$select': ','.join(COL), '$where': "comune='MILANO'", '$order': ':id', '$limit': PAGE, '$offset': off}
        for tent in range(4):
            try:
                rows = json.loads(urllib.request.urlopen(urllib.request.Request(URL + urllib.parse.urlencode(q), headers=H), timeout=300).read().decode())
                break
            except Exception as e:
                print('errore', e, 'riprovo'); time.sleep(5)
        else:
            raise SystemExit('troppi errori')
        for r in rows: w.writerow([r.get(c, '') for c in COL])
        n += len(rows); off += PAGE; print(n, flush=True)
        if len(rows) < PAGE: break
        time.sleep(1)
print('fine', n)
