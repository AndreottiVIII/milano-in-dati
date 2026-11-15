# Senza dimora (bozza, 15/11/2026)

Pagina: bozza in `bozze-grafici/senza-dimora-v2/index.html`, anteprima in `docs/anteprima/senza-dimora/`. Non pubblicata.

## Dati
- ISTAT, sezioni di censimento (CC BY 4.0). Le persone senza dimora iscritte in anagrafe sono nelle sezioni fittizie: 8888xxx nel 2001 e 2011, 888888x nel 2021 e 2023. A Roma (15, una per municipio) e Genova (4 nel 2021, 3 nel 2023) sono più d'una: sommate.
- Definizione ufficiale: `censimenti/raw/istat_documentazione/` (nota 2023, 9/6/2026; basi territoriali 2011 e 2021: sezioni 8888881-8888889 "persone senza dimora iscritte in anagrafe a un indirizzo convenzionale"; nota metodologica RSBL: Roma e Genova più sezioni).
- 2001: 24 sezioni con codici 8888[zona][nn], 1.225 persone. Non trovata nota ISTAT che ne dica il contenuto: dato dichiarato "meno sicuro" nella pagina.
- 2011: 6 sezioni (8888883-8888888), 266 persone. Nel 2011 ISTAT fece anche un conteggio in una notte nei grandi comuni (non in questi dati); dal 2021 la fonte sono i registri. Salto non confrontabile.
- Altre città: `censimenti/raw/istat_variabili_2021_comuni/Comuni_2021.zip` e `istat_variabili_2023/Comuni_2023.zip` (14 città, file per sezione, già scaricati in precedenza). Script `scripts/citta.py` (richiede openpyxl) -> `docs/senza-dimora/data/citta_2021_2023.csv`. Roma non ha 888888x ma 88888xx (una per municipio, 22.184 nel 2021, 26.241 nel 2023).
- Italia 2021: 96.197 (ISTAT, censimento e dinamica demografica 2021; confermato da più testate). Quota stranieri Italia 38%: non usata in pagina.
- `scripts/prepara.py` -> riepilogo.json, serie.csv, eta_2021_2023.csv, citta.csv.

## Numeri (ricalcolati con pandas, 2023)
10.038 iscritti (8.545 nel 2021); 73,2 ogni 10.000 abitanti (2ª dopo Roma 95,4); 20 quartieri abitati su 75 (esclusi i 13 sotto i 1.000 residenti) con meno abitanti; 32 volte 2011-2021 tolto dai numeri in alto, al suo posto 73% stranieri sotto i 15 anni; 1.610 sotto i 15 anni = 16,0%; uomini 63,0%; stranieri 62,0% contro 19,3% nel resto di Milano; 8.545/266 = 32,1 volte.

## Da sapere
- "Resto di Milano" = residenti nelle sezioni normali (totale meno la sezione fittizia).
- Messina 94 -> 513 e Bari 1.430 -> 584 in due anni: cambiano le iscrizioni, non le persone. Confronto tra città da prendere con cautela.
