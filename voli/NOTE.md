# Dove si vola da Milano (voli)

Pagina nuova, bozza in `bozze-grafici/voli-v2/index.html`, anteprima con `python -I -X utf8 bozze-grafici/anteprima.py voli`. Non ancora pubblicata (15/11/2026): mancano menu, home, JOURNAL, favicon/condividi.png e testo statico.

## Dati
- **Eurostat `avia_par_it`**, passeggeri trasportati (PAS_CRD) per coppia aeroporto principale italiano / aeroporto partner. Annuale 1993-2024 (mancano 1999-2001 e molte rotte prima del 2002), mensile 2002-2024. Licenza CC BY 4.0. Aggiornamento Eurostat del 22/10/2025. Scaricato il 15/11/2026 con User-Agent `milano-in-dati/1.0`.
- Il codice della coppia è `IT_<aeroporto>_<paese>_<icao partner>`; la dimensione si chiama `airp_pr` (non `rep_airp`). L'API mensile non accetta `time=2024`: serve `sinceTimePeriod=2024-01&untilTimePeriod=2024-12`.
- **OurAirports** (coordinate degli aeroporti, pubblico dominio) e **Natural Earth 1:50m** (confini degli stati, pubblico dominio).
- `scripts/scarica.py` scarica in `grezzi/` (non va nel repository, 17 MB); `scripts/prepara.py` scrive in `docs/voli/data/` (tutti i file sotto i 200 KB).

## Scelte
- Anni completi 2004-2024 per classifiche, mappa e mesi. La rotta con Roma parte dal 1995 con un buco 1998-2001 (linea tratteggiata).
- Destinazione = città: gli aeroporti della stessa città sono sommati (tabella `c(...)` in prepara.py). Charleroi conta come Bruxelles, Beauvais come Parigi, Torp come Oslo.
- Coppie con partner «sconosciuto» o «sistema di aeroporti» (codice con cifre, ZZZZ) escluse dalle città: 2009 0,49 milioni, nel 2004 e 2024 zero.
- Aree della mappa per paese del partner; Gulf, Asia e Africa subsahariana e le Americhe/Canarie sono frecce fuori mappa. Gli archi sono disegnati (strisce da Milano al centro pesato di ogni area, poi fili alle città).
- Rotte «di vacanza» e «di lavoro» non esistono nei dati: le sei più stagionali (oltre 250 mila passeggeri, picco a luglio o agosto) e le sei con la quota di agosto più bassa (oltre 800 mila). Detto in pagina.
- Linate chiuso da fine luglio a fine ottobre 2019: nei dati mensili Linate ha 0 passeggeri ad agosto e settembre 2019 e 122 mila a ottobre.

## Copertura rispetto ai passeggeri dei tre aeroporti (pagina Aeroporti)
2024: Linate 97%, Malpensa 89%, Bergamo 84% (in `riepilogo.json`, chiave `copertura`).

## Da fare prima di pubblicare
- Aggiungere `voli` in `docs/menu.js`, `docs/temi.json`, home; voce nel JOURNAL.
- Aggiungere `!voli/scripts/*.py` e `voli/NOTE.md` al `.gitignore` se serve (ora `*` esclude tutto tranne `NOTE*.md`); `voli/grezzi/` va lasciata fuori.
- `condividi.png`, tag Open Graph e testo statico (`strumenti/statico.py`) come per le altre pagine.
