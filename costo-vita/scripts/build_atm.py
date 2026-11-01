"""Storico del biglietto ordinario ATM (urbano Milano) e di altri titoli. Valori trascritti A MANO dalle fonti elencate (non c'e' un dataset ufficiale).
Uso: python -I -X utf8 build_atm.py <costo-vita assoluto>"""
import sys, os, csv
C = sys.argv[1]
IL = "Il Giorno, 'Aumenta il costo del biglietto dei mezzi: dalle 1500 lire a oggi, storia dei rincari Atm', 9/1/2023, https://www.ilgiorno.it/milano/cronaca/atm-aumento-biglietto-storia-d513face (copia: raw/atm/ilgiorno_storia_biglietto.html, scaricata 1/11/2026)"
OP = "Open, 'Atm, il biglietto costera' due euro, ma aumentano le esenzioni', 26/6/2019, https://www.open.online/2019/06/26/milano-stangata-in-arrivo-su-bus-e-metro-da-luglio-il-biglietto-sale-a-2-euro/ (copia: raw/atm/open_2019.html)"
SK = "Sky TG24, 9/1/2023, https://tg24.sky.it/economia/2023/01/09/milano-aumento-biglietti-atm-trasporti (copia: raw/atm/skytg24_2023.html)"
AT = "ATM, pagine ufficiali 'Biglietti' e 'Abbonamenti' lette il 1/11/2026 (copie: raw/atm/atm_tipologie_biglietti.html, atm_tipologie_abbonamenti.html, atm_TARIFFE_ATM.pdf)"
rows = [
 ("", "biglietto ordinario", 0.77, 1500, "1.500 lire = 0,77 euro (conversione 1.936,27 lire/euro, calcolo nostro); valido 75 minuti. Data di inizio non indicata (prezzo in vigore prima di gennaio 2002): vale 'fino al 6/1/2002'", IL),
 ("2002-01", "biglietto ordinario", 1.00, 1950, "1.950 lire (+30%) da gennaio 2002, cioe' 1,00 euro (1.936,27 lire per euro; 1.950 lire = 1,007 euro); giorno esatto non indicato: i vecchi biglietti restano validi fino al 6/1/2002; doppio prezzo lira-euro fino al 28/2/2002; invariato per 'piu' di nove anni' fino al 1/9/2011", IL),
 ("2011-09-01", "biglietto ordinario", 1.50, "", "da 1 a 1,50 euro; durata da 75 a 90 minuti; carnet 10 viaggi a 13,80; abbonamenti mensili e annuali invariati", IL),
 ("2019-07-15", "biglietto ordinario", 2.00, "", "da 1,50 a 2 euro; delibera del Consiglio comunale del 25/6/2019, in vigore dal 15 luglio (Open); Il Giorno scrive solo 'giugno 2019'", OP),
 ("2023-01-09", "biglietto ordinario", 2.20, "", "da 2 a 2,20 euro, adeguamento Istat dopo due anni senza aumenti (Il Giorno)", IL + " ; " + SK),
 ("2026-11-01", "biglietto ordinario", 2.20, "", "prezzo in vigore alla data della lettura del sito ATM (90 minuti dalla prima convalida); dal 1/1/2026 niente piu' biglietto di carta (RicaricaMi)", AT),
 ("2019-07-15", "carnet 10 biglietti", 18.00, "", "da 13,80 a 18 euro", OP),
 ("2023-01-09", "carnet 10 biglietti", 19.50, "", "da 18 a 19,50 euro; ATM 1/11/2026: 19,50", SK + " ; " + AT),
 ("2019-07-15", "biglietto giornaliero", 7.00, "", "da 4,50 a 7 euro", OP),
 ("2023-01-09", "biglietto giornaliero", 7.60, "", "da 7 a 7,60 euro; ATM 1/11/2026: 7,60", SK + " ; " + AT),
 ("2011-09-01", "abbonamento mensile urbano ordinario", 35.00, "", "invariato nel 2011 (Il Giorno) e fino al 2019 (Open: 'da 35 a 39 euro' nel 2019)", IL + " ; " + OP),
 ("2019-07-15", "abbonamento mensile urbano ordinario", 39.00, "", "da 35 a 39 euro; ATM 1/11/2026: 39 euro (invariato)", OP + " ; " + AT),
 ("2019-07-15", "abbonamento annuale urbano ordinario", 330.00, "", "prezzo congelato per 3 anni nella delibera del 2019 (Open); ATM 1/11/2026: 330 euro", OP + " ; " + AT),
 ("2026-11-01", "abbonamento mensile urbano giovani fino a 27 anni", 22.00, "", "ATM 1/11/2026 (annuale 200 euro)", AT),
 ("2026-11-01", "abbonamento annuale urbano ISEE fino a 6.000", 50.00, "", "ATM 1/11/2026", AT),
]
with open(os.path.join(C, "pulito", "atm_tariffe_storico.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["data_inizio", "titolo", "prezzo_eur", "prezzo_lire", "nota", "fonte"]); w.writerows(rows)
print(len(rows), "righe scritte")
