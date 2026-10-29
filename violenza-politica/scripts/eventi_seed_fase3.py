# Fase 3 (29/10/2026): eventi aggiunti per colmare le lacune, correzioni di posizione e casi "DA DECIDERE" resi eventi (decisione di Davide, 29/10).
# Stesse regole delle fasi 1-2: fatti e link; responsabili esattamente come li scrive Wikipedia; nessun giudizio nostro.
# Campi extra rispetto a eventi_seed.py: link_only (la voce cita l'evento ma parla d'altro), vt (tipo di voce), riv/cond (sì/no scritti a mano),
# rev=(numero versione, data) per voci non italiane, coords_met (descrizione del metodo per coords=...), en (link inglese).
from eventi_seed import CRON_SQ, CRON_PB
VR = 'Volante Rossa "Martiri Partigiani"'
VR_EN = "https://en.wikipedia.org/wiki/Volante_Rossa"
EN_TERR_IT = "https://en.wikipedia.org/wiki/Terrorism_in_Italy"
EN_ISLAM = "https://en.wikipedia.org/wiki/Islamic_terrorism_in_Europe"
EN_LISTA = "https://en.wikipedia.org/wiki/List_of_terrorist_incidents"

SEEDS3 = [
 # --- 1920-1922 (Cronologia dello squadrismo; voce sulla strage del Diana)
 dict(k="1920-06-22-via-dante", data="1920-06-22", titolo="Sparatoria in via Dante e carica a Porta Venezia durante lo sciopero dei ferrovieri", tipo="scontro o custodia", wp=CRON_SQ, addr=("Via", "DANTE", None), morti=11, feriti=None,
      vittime="Riccardo Bassi (tornitore, via Dante); Enrico Nova (passante, Porta Venezia); gli altri nove non sono nominati dalla voce", resp="polizia e carabinieri (contro i manifestanti usciti dal comizio all'Arena)", fonte="wp-cronologia", conf="media", riv="no", cond="no",
      nota="Wikipedia scrive che «a fine giornata si contano complessivamente 11 morti»; il testo ne nomina due. Posizione: via Dante (la sparatoria); la carica dei carabinieri in cui morì Nova fu a Porta Venezia."),
 dict(k="1920-06-23-loreto-tram", data="1920-06-23", titolo="Tram bloccato a piazzale Loreto: il vicebrigadiere Ugolini uccide un operaio ed è linciato", tipo="scontro o custodia", wp=CRON_SQ, addr=("Piazzale", "LORETO", None), morti=3, feriti=None,
      vittime="Alfredo Cappelli (operaio); Giuseppe Ugolini (vicebrigadiere dei carabinieri); Francesco Bonini (ferito gravemente, morto qualche giorno dopo)", resp="un vicebrigadiere dei carabinieri (Cappelli, Bonini) e una folla di scioperanti (linciaggio di Ugolini)", fonte="wp-cronologia", conf="media", riv="no", cond="no",
      nota="La data è dedotta dal testo («il giorno seguente» agli scontri del 22 giugno)."),
 dict(k="1920-06-25-cova", data="1920-06-25", titolo="Bomba a mano contro le vetrine della pasticceria Cova: ucciso un capitano dell'esercito", tipo="attentato", wp="Strage del Diana", link_only=True, vt="voce che cita l'evento", addr=("Piazza", "SCALA (DELLA)", None), morti=1, feriti=None,
      vittime="un capitano dell'esercito (nome non indicato)", resp="non indicati", fonte="wp-voce (antefatti della strage del Diana)", conf="media", riv="no", cond="no",
      nota="La voce sulla strage del Diana ricorda l'episodio tra gli antefatti. Posizione approssimata a piazza della Scala: la cronologia dello squadrismo cita il Cova di piazza della Scala, la voce sulla pasticceria dice che nacque «a lato del Teatro alla Scala» (oggi è in via Montenapoleone 8)."),
 dict(k="1920-08-07-cova", data="1920-08-07", titolo="Seconda bomba contro il Cova, ritrovo dei fascisti milanesi", tipo="attentato", wp=CRON_SQ, addr=("Piazza", "SCALA (DELLA)", None), morti=0, feriti=3,
      vittime="tre cittadini svizzeri che erano nel locale (secondo la voce sul Diana)", resp="gli anarchici Giuseppe Mariani ed Ettore Aguggini", fonte="wp-cronologia + wp-voce (Diana)", conf="media", riv="no", cond="no",
      nota="La cronologia non dà feriti; i tre feriti sono nella voce sulla strage del Diana. Due giorni dopo la stessa coppia fece esplodere una bomba al Palazzo degli Esercenti, senza vittime (non contata). Posizione approssimata come per la bomba del 25 giugno."),
 dict(k="1920-10-15-albergo", data="1920-10-15", titolo="Due bombe contro un albergo che ospitava la delegazione britannica alla conferenza internazionale", tipo="attentato", wp=None, en=EN_LISTA, rev=(1382105948, "2026-10-26"), addr=None, morti=0, feriti=2,
      vittime="", resp="anarchici", fonte="wp-en List of terrorist incidents + wp-de Liste von Terroranschlägen bis 1968", conf="bassa", riv="no", cond="no",
      nota="Una riga della lista inglese (che cita il New York Times del 16/10/1920) e una della lista tedesca. Nessuna voce dedicata; albergo non indicato. Numero di versione: lista inglese."),
 dict(k="1922-04-30-pessina", data="1922-04-30", titolo="Accoltellato dai fascisti presso la Casa del Popolo di Chiaravalle Milanese l'operaio socialista Francesco Pessina", tipo="omicidio politico", wp=CRON_SQ, wp_coord_of="Chiaravalle (Milano)", morti=1, feriti=None,
      vittime="Francesco Pessina (operaio socialista, morto in ospedale qualche ora dopo)", resp="una squadraccia fascista", fonte="wp-cronologia", conf="media", riv="no", cond="no",
      nota="Posizione approssimata al quartiere di Chiaravalle (oggi parte del Comune di Milano)."),
 # --- 1944
 dict(k="1944-08-08-abruzzi", data="1944-08-08", titolo="Bombe contro un camion tedesco in viale Abruzzi", tipo="attentato", wp="Strage di Piazzale Loreto", link_only=True, vt="voce che cita l'evento", addr=("Viale", "ABRUZZI", None), morti=6, feriti=11,
      vittime="sei cittadini milanesi (nomi non indicati)", resp="ignoti; attribuito ai GAP, ma Giovanni Pesce lo negò; la voce riporta il sospetto (anche del tribunale militare di Torino, 1998) che fosse organizzato dai tedeschi", fonte="wp-voce (Loreto)", conf="media", riv="no", cond="no",
      nota="Pretesto della fucilazione di 15 partigiani il 10 agosto 1944 a piazzale Loreto. Nessun militare morto; l'autista tedesco ebbe lievi ferite (oltre agli 11 feriti). La voce su Piero Parini indica il 7 agosto."),
 # --- 1947-1949 (Volante Rossa, secondo dopoguerra)
 dict(k="1947-01-17-maciachini", data="1947-01-17", titolo="Uccisione di Eva Maciachini, ex ausiliaria delle Squadre d'Azione Mussolini", tipo="omicidio politico", wp=VR, link_only=True, vt="voce che cita l'evento", en=VR_EN, wp_coord_of="Lambrate", morti=1, feriti=None,
      vittime="Eva Maciachini (grafie delle voci: anche Macciacchini, Maciacchini)", resp="autori mai scoperti; modalità analoghe a quelle della Volante Rossa (secondo la voce)", fonte="wp-voce (Volante Rossa)", conf="media", riv="no", cond="no",
      nota="Uccisa lo stesso giorno di Brunilde Tanzi; il corpo fu trovato presso Lambrate (posizione = quartiere)."),
 dict(k="1947-03-14-deagazio", data="1947-03-14", titolo="Omicidio del giornalista Franco De Agazio, direttore del Meridiano d'Italia", tipo="omicidio politico", wp=VR, link_only=True, vt="voce che cita l'evento", en=VR_EN, addr=None, morti=1, feriti=None,
      vittime="Franco De Agazio", resp="Volante Rossa (azione che la voce dice rivendicata pubblicamente; la voce la elenca tra gli omicidi non del tutto accertati)", fonte="wp-voce (Volante Rossa)", conf="media", riv="sì", cond="no",
      nota="Luogo non indicato dalla voce."),
 dict(k="1947-07-06-mazzetti", data="1947-07-06", titolo="Bomba a mano nella casa del fascista Fulvio Mazzetti: ferito il lanciatore", tipo="attentato", wp=VR, link_only=True, vt="voce che cita l'evento", en=VR_EN, addr=None, morti=0, feriti=1,
      vittime="Mario Gandini detto «Mila» (della Volante Rossa, ferito dalle schegge e catturato dalla polizia)", resp="Volante Rossa", fonte="wp-voce (Volante Rossa)", conf="media", riv="no", cond="no",
      nota="Luogo non indicato dalla voce (abitazione di Mazzetti)."),
 dict(k="1947-11-04-gatti", data="1947-11-04", titolo="Uccisione del generale Ferruccio Gatti, responsabile milanese del MSI, nella sua abitazione", tipo="omicidio politico", wp=VR, link_only=True, vt="voce che cita l'evento", en=VR_EN, addr=None, morti=1, feriti=1,
      vittime="Ferruccio Gatti; ferito gravemente il figlio Riccardo (la sentenza di appello 1953 cita anche il tentato omicidio della moglie Margherita Bellingeri)", resp="membri della Volante Rossa", fonte="wp-voce (Volante Rossa)", conf="media", riv="no", cond="sì",
      nota="Luogo non indicato dalla voce (abitazione del generale)."),
 dict(k="1949-01-27-ghisalberti", data="1949-01-27", titolo="Uccisione di Felice Ghisalberti e di Leonardo Massaza", tipo="omicidio politico", wp=VR, link_only=True, vt="voce che cita l'evento", en=VR_EN, addr=None, morti=2, feriti=None,
      vittime="Felice Ghisalberti (ex milite della Legione Muti); Leonardo Massaza (impiegato della Siemens; nella voce inglese «Masazza»)", resp="Volante Rossa", fonte="wp-voce (Volante Rossa)", conf="media", riv="no", cond="sì",
      nota="Luogo non indicato dalla voce. Per entrambi gli omicidi la sentenza d'appello del 1953 condannò i membri del gruppo."),
 # --- dopo il 1993
 dict(k="2009-10-12-santa-barbara", data="2009-10-12", titolo="Attentato kamikaze alla caserma Santa Barbara (Baggio)", tipo="attentato", wp="Caserma Santa Barbara", link_only=True, vt="voce che cita l'evento", en=EN_TERR_IT, wp_coord_of="Caserma Santa Barbara", morti=0, feriti=3,
      vittime="l'attentatore (gravemente ferito) e due militari", resp="un cittadino libico (nome non indicato dalle voci); la valigetta con 2 kg di esplosivo fu realizzata da un complice, condannato a 3 anni e mezzo", fonte="wp-voce (caserma) + wp-it Terrorismo in Italia + wp-en Terrorism in Italy", conf="media", riv="no", cond="sì",
      nota="Data: 12 ottobre per «Terrorismo in Italia» e per la voce inglese; 11 ottobre per la voce sulla caserma. Wikipedia lo descrive come il primo attacco suicida ad alto potenziale stragista in Italia; per il DIS fu un atto isolato."),
 dict(k="2017-05-18-centrale", data="2017-05-18", titolo="Aggressione a militari e a un agente alla Stazione Centrale", tipo="attentato", wp=None, en=EN_TERR_IT, rev=(1354253397, "2026-05-15"), wp_coord_of="Stazione di Milano Centrale", morti=0, feriti=3,
      vittime="un poliziotto e due soldati", resp="Ismail Tommaso Hosni, simpatizzante dell'ISIS (voce inglese)", fonte="wp-en Terrorism in Italy + wp-de Liste von Terroranschlägen im Jahr 2017", conf="bassa", riv="no", cond="no",
      nota="La voce inglese cita l'attacco (maggio 2017) senza altri dettagli; coltello, 3 feriti e l'identificativo GTD del 18 maggio vengono dalla lista tedesca, che scrive 19 maggio. Numero di versione: voce inglese."),
 dict(k="2019-09-17-centrale", data="2019-09-17", titolo="Accoltellato un militare alla Stazione Centrale", tipo="attentato", wp=None, en=EN_ISLAM, rev=(1380742576, "2026-10-17"), wp_coord_of="Stazione di Milano Centrale", morti=0, feriti=1,
      vittime="un soldato italiano (sopravvissuto)", resp="un immigrato irregolare yemenita di 23 anni; Europol classificò l'attacco come terrorismo jihadista (voce inglese)", fonte="wp-en Islamic terrorism in Europe", conf="media", riv="no", cond="no",
      nota="Numero di versione: voce inglese."),
 # --- casi "DA DECIDERE" resi eventi (decisione di Davide, 29/10/2026): ognuno con la nota «Caso incerto»
 dict(k="1946-04-21-pasqua-rossa", data="1946-04-21", titolo="Pasqua Rossa: rivolta nel carcere di San Vittore", tipo="scontro o custodia", wp="Pasqua Rossa", vt="voce dedicata", wp_coord_of="Carcere di San Vittore", morti=5, feriti=100,
      vittime="quattro detenuti (nomi non indicati) e l'agente di custodia Salvatore Rap (dichiarato morto 3 giorni dopo la fine degli scontri)", resp="detenuti guidati da Ezio Barbieri, Athos Stelpi e Giuseppe Caradonna", fonte="wp-voce", conf="bassa", riv="no", cond="no",
      nota="Caso incerto: rivolta carceraria, non attentato né omicidio politico. La rivolta durò quattro giorni; feriti: «oltre un centinaio» (qui 100). La voce riporta che il governo di allora non la considerò di natura politica."),
 dict(k="1979-07-11-ambrosoli", data="1979-07-11", titolo="Omicidio dell'avvocato Giorgio Ambrosoli", tipo="omicidio politico", wp="Giorgio Ambrosoli", addr=("Via", "MOROZZO DELLA ROCCA", "1"), morti=1, feriti=None, s1="Omicidio di Giorgio Ambrosoli",
      vittime="Giorgio Ambrosoli (commissario liquidatore della Banca Privata Italiana)", resp="William Joseph Aricò, killer pagato da Michele Sindona; Sindona e Robert Venetucci condannati all'ergastolo nel 1986; mandanti ancora sconosciuti secondo la voce", fonte="wp-voce+tabella", conf="bassa", riv="no", cond="sì",
      nota="Caso incerto: ucciso da un killer professionista su incarico di Sindona (movente economico-criminale); Wikipedia lo mette però nell'elenco degli anni di piombo."),
 dict(k="1980-06-11-lahderi", data="1980-06-11", titolo="Omicidio dell'uomo d'affari libico Mohammed Lahderi Azzedin", tipo="omicidio politico", wp=CRON_PB, addr=None, morti=1, feriti=None,
      vittime="Mohammed Lahderi Azzedin (56 anni, residente in Italia)", resp="non indicati", fonte="wp-cronologia", conf="bassa", riv="no", cond="no",
      nota="Caso incerto: movente non indicato da Wikipedia. Luogo preciso non indicato."),
 dict(k="1982-04-27-abbruciati", data="1982-04-27", titolo="Morte di Danilo Abbruciati dopo il ferimento di Roberto Rosone", tipo="scontro o custodia", wp="Danilo Abbruciati", addr=None, morti=1, feriti=1, s1="Morte di Danilo Abbruciati",
      vittime="Danilo Abbruciati (Banda della Magliana); ferito Roberto Rosone (vicepresidente del Banco Ambrosiano)", resp="ucciso da una guardia giurata (Franco Germi) mentre fuggiva dopo aver gambizzato Rosone; la tabella scrive «Forze dell'ordine»", fonte="wp-voce+tabella", conf="bassa", riv="no", cond="no",
      nota="Caso incerto: criminale comune ucciso dopo il ferimento di Rosone, non violenza politica. Luogo preciso non indicato dalla voce."),
]

# correzioni a eventi già presenti (posizioni, date, note). nota_add = testo aggiunto alla nota; gli altri campi sostituiscono quelli del seme.
PATCH = {
 "1919-06-08-bovisa": dict(wp_coord_of="Stazione di Milano Bovisa Politecnico", nota_add="Posizione approssimata: stazione di Bovisa (coordinate della stazione oggi chiamata Bovisa Politecnico)."),
 "1919-11-17-bomba-avanti": dict(addr=("Via", "DAMIANO (SAN)", None), nota_add="Posizione: via San Damiano, dove la voce sull'assalto del 15 aprile 1919 colloca la sede dell'Avanti!; per novembre 1919 la cronologia non indica l'indirizzo."),
 "1969-04-25-bombe": dict(coords=(45.474, 9.155), coords_met="Wikidata P625 (Fiera di Milano, stesso punto dell'attentato del 1928)",
      nota="Voce dedicata: alla Fiera (padiglione FIAT, ore 18:57) 5 persone colpite direttamente e circa 10 di striscio (5 ricoveri); alla Stazione Centrale (ufficio cambi, ore 20:45) esplose un secondo ordigno, senza feriti. La cronologia degli anni di piombo scrive invece 5 feriti e un ordigno «inesploso» alla stazione."),
 "1971-01-07-pirelli": dict(wp_coord_of="Bicocca (Milano)", nota_add="Posizione approssimata al quartiere Bicocca."),
 "1979-01-29-alessandrini": dict(addr=("Via", "MURATORI LODOVICO", None), nota_add="Posizione: incrocio tra viale Umbria e via Muratori (dalla voce); il punto è il centro dei civici di via Muratori."),
 "1980-11-12-briano": dict(wp_coord_of="Gorla (metropolitana di Milano)", nota_add="Posizione approssimata: fermata Gorla, dove gli assassini scesero; la voce dice che fu ucciso alle 8:20 su un convoglio della linea 1 diretto a Sesto Marelli."),
 "1980-11-28-mazzanti": dict(nota="Verificato sulla voce dedicata: ucciso in via Orseolo all'angolo con via Savona, Milano; il «Sesto San Giovanni» della tabella 1980 è il luogo di lavoro (stabilimento Falck Unione)."),
 "1972-03-tavecchio": dict(data="1972-03-11", data_morte="1972-03-14", addr=("Piazza", "CASTELLO", None), nota="Scontri dell'11 marzo 1972 (cronologia e tabella); la tabella 1972 data la morte al 14 marzo («ucciso in seguito agli scontri in piazza dell'11 marzo»). Qui: data = scontri, data_morte = 14 marzo. Nessuna voce propria. Posizione: piazza Castello, dove la voce «Sequestro Macchiarini» colloca il comizio di Niccolai e della Maggioranza silenziosa contro cui si manifestò; secondo quella voce fu colpito da un candelotto lacrimogeno sparato dalla polizia ad altezza d'uomo."),
 "1981-10-19-pattuglia": dict(addr=("Via", "VALLAZZE", None), nota_add="Posizione: via Vallazze; la voce su Gilberto Cavallini colloca l'inseguimento di un terzo agente ferito tra via Vallazze e via Teodosio."),
 "1928-04-12-fiera": dict(nota="La voce dedicata dice 14 morti subito e 6 nei giorni seguenti (20 in tutto); Wikidata (14) conta solo i morti immediati."),
 "1947-01-17-tanzi": dict(resp="autori mai scoperti; modalità analoghe a quelle della Volante Rossa (secondo le voci)", nota="Uccisa lo stesso giorno di Eva Maciachini. Le voci dicono che gli autori non furono mai scoperti e che le modalità richiamano la Volante Rossa."),
}

# righe di esclusi.csv sostituite dagli eventi sopra (per nome dell'evento): non restano nell'elenco degli esclusi
ESCLUSI_TOGLI = {"Morte di Danilo Abbruciati", "Omicidio di Giorgio Ambrosoli", "Omicidio dell'uomo d'affari libico Mohammed Lahderi Azzedin", "Pasqua Rossa (rivolta nel carcere di San Vittore)", "Rapimento e morte di Carlo Saronio", "Bomba al ristorante Cova"}

ESCLUSI3 = [
 ("1975-03-11", "Rapimento e morte di Carlo Saronio", "decisione di Davide (29/10): includere se morto a Milano. Verifica: la voce dice che morì durante il trasferimento dopo il rapimento del 14 aprile 1975 (sequestro a scopo di autofinanziamento), senza indicare il luogo; il corpo fu trovato nel 1979. La tabella 1975 scrive «Milano» e data l'11 marzo, la voce il 14 aprile: non è dimostrato che sia morto nel Comune di Milano", "wp-tabella + wp-voce (verificato in fase 3)"),
 ("1920-08-09", "Bomba al Palazzo degli Esercenti (piazza San Sepolcro)", "esplosione senza vittime né feriti secondo la cronologia", "wp-cronologia"),
 ("1944-1945", "Rosa Bianchi e Liliana Sciaccaluga (madre e figlia, ex ausiliarie)", "uccise nel 1945, data e luogo non indicati dalla voce; imputati ma senza sentenza definitiva", "wp-voce (Volante Rossa)"),
 ("1945-11-05", "Cartelloni del cinema Odeon incendiati (Roma città aperta)", "incendio senza vittime", "wp-voce (Volante Rossa)"),
 ("1947-06-12", "Gelatina esplosiva davanti alla federazione del PCI (FAR)", "nessuna vittima indicata", "wp-voce (Fasci di Azione Rivoluzionaria)"),
 ("1947-06-16", "Assalto al bar di via Pacini (Volante Rossa)", "nessuna vittima indicata; sede del MSI di via Santa Radegonda (29/10/1947) e giornale Meridiano d'Italia: danni senza vittime", "wp-voce (Volante Rossa)"),
 ("1968-06-07", "Scontri di via Solferino durante uno sciopero", "12 feriti e 250 fermati, nessun morto", "wp-voce (Scioperi nell'Italia repubblicana)"),
 ("1969-08-09", "Bombe sui treni (Milano Centrale: ordigno inesploso)", "a Milano nessuna esplosione; le otto esplosioni avvennero altrove", "wp-voce (Attentati ai treni dell'estate 1969)"),
 ("1976-12-08", "Rogo alla Scala (riga della lista tedesca, 19 feriti)", "una sola riga della lista tedesca basata sulla Global Terrorism Database, senza riscontro nelle voci it/en", "wp-de Liste von Terroranschlägen im Jahr 1976"),
 ("1979-06-16", "Attentato dei NAR a un ufficio di partito a Milano (riga della lista tedesca, 23 feriti)", "una sola riga della lista tedesca basata sulla Global Terrorism Database, senza riscontro nelle voci it/en", "wp-de Liste von Terroranschlägen im Jahr 1979"),
 ("1980-04-28", "Tentativo di evasione da San Vittore (Alunni, Vallanzasca) e sparatoria", "nessun morto indicato", "wp-cronologia"),
 ("1998-2000", "Lettere-bomba, attentato a una stazione dei carabinieri e bombe di «Solidarietà Internazionale»", "nessuna vittima indicata dalle voci; le bombe del 1999 e le molotov del 2000 non esplosero", "wp-it/en Terrorismo in Italia"),
 ("2000-12-18", "Bomba sul tetto del Duomo", "ordigno disinnescato, non esploso", "wp-it/en Terrorismo in Italia"),
 ("2005-06-28", "Morte del giornalista kosovaro Bardhyl Ajeti", "ferito a Priština il 3 giugno, morto in un ospedale di Milano: il fatto non è avvenuto a Milano", "wp-voce"),
 ("2009-12-16", "Bomba alla Bocconi (rivendicata dalla FAI)", "esplosione parziale, nessuna vittima indicata dalle voci", "wp-it/en Terrorismo in Italia"),
 ("2016-12-23", "Uccisione di Anis Amri in uno scontro a fuoco", "avvenuta a Sesto San Giovanni, fuori dal Comune di Milano; non è un attentato a Milano", "wp-en List of terrorist incidents in 2016"),
 ("2023-10", "Accoltellamento di alcune persone a Milano citato in «Terrorismo in Italia»", "data, luogo e vittime non indicati dalla voce", "wp-it Terrorismo in Italia"),
]
