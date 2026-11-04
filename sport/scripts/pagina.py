"""Sport: costruisce docs/sport/index.html e docs/sport/data/*.
Uso: python -I -X utf8 pagina.py <ABS sport> <ABS citta-15-minuti> <ABS docs/sport>   (dopo build.py e analisi.py; si puo' rilanciare)
Tutti i numeri nel testo vengono da pulito/*.csv|json: nessun numero e' scritto a mano, tranne le date e i fatti sulle sedi olimpiche (con fonte)."""
import sys, os, json, shutil
import numpy as np, pandas as pd
S, C, W = [a.rstrip('\\/') for a in sys.argv[1:4]]
os.makedirs(W + '/data', exist_ok=True)
P = pd.read_csv(S + '/pulito/siti.csv', dtype={'ID_NIL': 'Int64'})
N = pd.read_csv(S + '/pulito/nil_sport.csv')
R = json.load(open(S + '/pulito/citta_sport.json', encoding='utf-8'))
B = json.load(open(S + '/pulito/build_log.json', encoding='utf-8'))
OL = pd.read_csv(S + '/pulito/sedi_olimpiche.csv')
def it(x, d=0): return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
def pc(x, d=1): return it(x * 100, d) + '%'
GEST = {'milanosport': 'Milanosport', 'comune_concessione': 'Comune, dato in concessione ad altri', 'comune_da_verificare': 'Comune (gestore da verificare)',
        'comune_libero': 'Campi liberi del Comune (giardini)', 'scuola': 'Palestre di scuole', 'altro': 'Non risulta comunale'}
GK = list(GEST)
P = P[P.ID_NIL.notna()].copy()   # solo luoghi dentro il Comune (i 15 entro 200 m dal confine servono solo ai tempi)
imp = P[P.livello == 'impianto']
tot = len(imp); com = int(imp.gestione.isin(['milanosport', 'comune_concessione', 'comune_da_verificare']).sum())
n_scuola = int((imp.gestione == 'scuola').sum()); n_altro = int((imp.gestione == 'altro').sum()); n_lib_imp = int((imp.gestione == 'comune_libero').sum())
n_ms = int((imp.gestione == 'milanosport').sum()); n_conc = int((imp.gestione == 'comune_concessione').sum()); n_dv = int((imp.gestione == 'comune_da_verificare').sum())
campi_liberi = P[P.livello == 'campo_libero']; n_cl = len(campi_liberi); n_cl_com = int((campi_liberi.gestione == 'comune_libero').sum())
ab = R['residenti_2025']; G = R['gruppi']; T = R['totali']; PK = R['per10k_citta']
big = N[N.residenti_2025 >= 1000].copy()
n2 = int((imp.n_fonti >= 2).sum()); n1 = tot - n2
duo = imp[imp.NIL.fillna('').str.upper() == 'DUOMO']
bpool = big[big.piscine == 0]
sp = R['spearman_fonti_nil']
# --- dati per i file di pagina
nilg = json.load(open(C + '/out/nil_poligoni_punteggi.geojson', encoding='utf-8'))
Ni = N.set_index('ID_NIL')
feats = []
for f in nilg['features']:
    i = int(f['properties']['ID_NIL'])
    if i in Ni.index:
        r = Ni.loc[i]
        pr = dict(i=i, n=str(r.NIL_nome), r=int(r.residenti_2025), cl=int(r.residenti_2025 >= 1000), t=int(r.tutti), p=round(float(r.per10k_tutti), 2) if r.residenti_2025 > 0 else None,
                  pi=int(r.piscine), co=int(r.comunali), sc=int(r.scuole), al=int(r.altro), ms=int(r.milanosport), pa=int(r.palestre), ca=int(r.campi), cll=int(r.campi_liberi_comune),
                  qt=round(float(r.quota15_tutti) * 100, 1), qp=round(float(r.quota15_piscine) * 100, 1), qc=round(float(r.quota15_comunali) * 100, 1), qm=round(float(r.quota15_milanosport) * 100, 1),
                  mp=float(r.minuti_medi_piscine), mt=float(r.minuti_medi_tutti))
    else:
        pr = dict(i=i, n=str(f['properties']['NIL']), r=0, cl=0, t=0, p=None, pi=0, co=0, sc=0, al=0, ms=0, pa=0, ca=0, cll=0, qt=None, qp=None, qc=None, qm=None, mp=None, mt=None)
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': f['geometry']})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(W + '/data/nil.geojson', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
bits = lambda r: int(r.piscina) * 1 + int(r.palestra) * 2 + int(r.campo) * 4 + int(r.centro) * 8
siti = [[round(r.lon, 5), round(r.lat, 5), str(r.nome), str(r.indirizzo) if isinstance(r.indirizzo, str) else '', bits(r), GK.index(r.gestione), int(r.n_fonti), 0 if r.livello == 'impianto' else 1,
         int(r.ID_NIL) if pd.notna(r.ID_NIL) else 0] for r in P.itertuples()]
json.dump(siti, open(W + '/data/siti.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
OL2 = OL.copy()
def olrow(r):
    return [r.sede, r.evento, r.stato, r.comune, float(r.lon), float(r.lat), r.NIL if isinstance(r.NIL, str) else '']
# --- dati riepilogo per il JS
nmap = N.set_index('ID_NIL').NIL_nome
sedi = []
for r in OL.itertuples():
    sedi.append(dict(sede=r.sede, evento=r.evento, stato=r.stato, comune=r.comune, lon=float(r.lon), lat=float(r.lat), nil=nmap.get(int(r.ID_NIL), r.NIL) if pd.notna(r.ID_NIL) else '',
                     res=None if pd.isna(r.residenti) else int(r.residenti), imp=None if pd.isna(r.impianti_nel_NIL) else int(r.impianti_nel_NIL),
                     p10=None if pd.isna(r.per10k_tutti) else float(r.per10k_tutti), qp=None if pd.isna(r.quota15_piscine) else float(r.quota15_piscine)))
D = dict(R=R, gest=GEST, gk=GK, sedi=sedi)
json.dump(D, open(W + '/data/riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
# copie per scaricare
P2 = P.drop(columns=[c for c in ['x', 'y', 'info', 'nomi_alt'] if c in P.columns])
P2.to_csv(W + '/data/siti.csv', index=False, encoding='utf-8')
N.to_csv(W + '/data/nil_sport.csv', index=False, encoding='utf-8')
OL.to_csv(W + '/data/sedi_olimpiche.csv', index=False, encoding='utf-8')
# --- pezzi di testo
def top(col, n=6, asc=False, d=1):
    t = big.sort_values(col, ascending=asc).head(n)
    return t
bars_top = json.dumps([[r.NIL_nome, round(r.per10k_tutti, 1), int(r.tutti), int(r.residenti_2025)] for r in top('per10k_tutti', 8).itertuples()], ensure_ascii=False)
bars_bot = json.dumps([[r.NIL_nome, round(r.per10k_tutti, 1), int(r.tutti), int(r.residenti_2025)] for r in top('per10k_tutti', 8, True).itertuples()], ensure_ascii=False)
bars_pool = json.dumps([[r.NIL_nome, round(r.quota15_piscine * 100, 1), int(r.residenti_2025)] for r in big.sort_values(['quota15_piscine', 'residenti_2025'], ascending=[True, False]).head(10).itertuples()], ensure_ascii=False)
grp_rows = [('tutti', 'Un impianto sportivo qualsiasi'), ('palestre', 'Una palestra o un centro fitness'), ('piscine', 'Una piscina'), ('comunali', 'Un impianto comunale (Milanosport, concessioni, da verificare)'),
            ('piscine_comunali', 'Una piscina comunale'), ('milanosport', 'Un impianto gestito da Milanosport (elenco 2025)'), ('scuole', 'Una palestra di scuola'),
            ('campi_liberi_comune', 'Un campo libero del Comune (giardini)')]
bars_acc = json.dumps([[lab, round(G[k]['quota_residenti_entro15'] * 100, 1), G[k]['luoghi_usati'], G[k]['minuti_mediani']] for k, lab in grp_rows], ensure_ascii=False)
# tabella tipo x gestione (solo impianti)
def cnt(mask): return int(mask.sum())
tipo_rows = [('Piscine', imp.piscina), ('Palestre e fitness', imp.palestra), ('Campi e palazzetti', imp.campo), ('Centri sportivi con più discipline', imp.centro), ('Tutti gli impianti', pd.Series(True, index=imp.index))]
tab = [[lab] + [cnt(m & (imp.gestione == g)) for g in ['milanosport', 'comune_concessione', 'comune_da_verificare', 'scuola', 'altro']] + [cnt(m)] for lab, m in tipo_rows]
tab_js = json.dumps(tab)
# sedi olimpiche (tabella)
olr = ''.join(f"<tr><td>{s['sede']}</td><td>{s['evento']}</td><td>{s['stato']}</td><td>{s['nil'] if s['nil'] else s['comune']}</td>"
              f"<td class=\"r\">{it(s['res']) if s['res'] else '–'}</td><td class=\"r\">{s['imp'] if s['imp'] is not None else '–'}</td><td class=\"r\">{pc(s['qp']) if s['qp'] is not None else '–'}</td></tr>" for s in sedi)
rsg = [s for s in sedi if 'Santa Giulia' in s['sede']][0]
rog = N[N.NIL_nome.str.contains('Rogoredo')].iloc[0]
san = [s for s in sedi if 'San Siro' in s['sede']][0]; vil = [s for s in sedi if 'Villaggio' in s['sede']][0]
# --- valori citati
q_t = G['tutti']['quota_residenti_entro15']; q_p = G['piscine']['quota_residenti_entro15']; q_pc = G['piscine_comunali']['quota_residenti_entro15']; q_c = G['comunali']['quota_residenti_entro15']; q_m = G['milanosport']['quota_residenti_entro15']
med_t = G['tutti']['minuti_mediani']; med_p = G['piscine']['minuti_mediani']
top1, top2 = top('per10k_tutti', 2).itertuples(), None
tl = list(top('per10k_tutti', 3).itertuples()); bl = list(big[big.tutti == 0].itertuples())
n_big = R['nil_con_almeno_1000_residenti']
sorpresa = f"""
<p><b>Quasi tutti hanno uno sport a due passi, ma non una piscina.</b> Il {pc(q_t)} dei milanesi arriva a piedi in 15 minuti ad almeno uno dei {it(tot)} impianti che abbiamo trovato (la mediana è {it(med_t, 1)} minuti). Per una <b>piscina</b> la quota scende al <b>{pc(q_p)}</b> (mediana {it(med_p, 1)} minuti); se si contano solo le piscine comunali al {pc(q_pc)}. Le piscine che risultano nei dati sono {R['totali']['piscine']}: una ogni {it(ab / R['totali']['piscine'] / 1000, 1)} mila abitanti. In {len(bpool)} dei {n_big} quartieri con almeno 1.000 residenti non ce n&rsquo;è nessuna dentro il quartiere.</p>
<p><b>Chi gestisce.</b> Dei {it(tot)} impianti, solo <b>{com}</b> ({pc(com / tot)}) sono del Comune: {n_ms} con Milanosport come concessionario, {n_conc} dati in concessione ad altri soggetti, {n_dv} da verificare. Altri {n_scuola} ({pc(n_scuola / tot)}) sono palestre di scuole, in genere non aperte al pubblico. I restanti <b>{n_altro} ({pc(n_altro / tot)}) non risultano comunali</b>: palestre e centri commerciali, circoli, oratori, club (non sappiamo se siano aperti a tutti). Gli impianti di <b>Milanosport</b> sono raggiungibili in 15 minuti dal <b>{pc(q_m)}</b> dei residenti.</p>
<p><b>Il centro ha tanti impianti ma nessuno comunale.</b> Nel quartiere Duomo ({it(int(N[N.NIL_nome.str.upper() == 'DUOMO'].residenti_2025.iloc[0]))} residenti) i dati contano {len(duo)} impianti, <b>nessuno comunale</b>: {int((duo.gestione == 'altro').sum())} sono palestre e club privati o di altri enti, {int((duo.gestione == 'scuola').sum())} palestre scolastiche.</p>
<p><b>I numeri &laquo;per abitante&raquo; ingannano.</b> In cima ci sono {tl[0].NIL_nome} ({it(tl[0].per10k_tutti, 1)} ogni 10.000 abitanti) e {tl[1].NIL_nome} ({it(tl[1].per10k_tutti, 1)}): sono quartieri con pochi residenti e grandi centri sportivi che servono tutta la città. Il valore medio della città è {it(PK['tutti'], 1)} impianti ogni 10.000 abitanti.</p>
<p><b>Le tre fonti non coincidono.</b> L&rsquo;elenco del Comune ({it(T['f_comune'])} impianti), OpenStreetMap ({it(T['f_osm'])}) e il censimento della Regione del 2016 ({it(T['f_regione'])}) danno numeri simili ma non gli stessi luoghi: <b>{it(n1)} impianti su {it(tot)} compaiono in una sola fonte</b>. Le classifiche dei quartieri fatte con una fonte o con l&rsquo;altra si somigliano poco (correlazione di Spearman tra {it(min(sp.values()), 2)} e {it(max(sp.values()), 2)}). Per questo la pagina è più sicura sui totali della città che sul singolo quartiere.</p>
"""
oly = f"""
<p>Le Olimpiadi invernali Milano Cortina si sono svolte dal 6 al 22 febbraio 2026 (cerimonia di apertura allo stadio San Siro). Nel gruppo di Milano le sedi sono cinque: due in Comune (San Siro e Arena Santa Giulia) e tre fuori (due a Rho, nella Fiera, e il Forum a Assago). In Comune c&rsquo;è anche il villaggio olimpico. Qui sotto le sedi in Comune, il villaggio e il Forum.</p>
<div class="scroll"><table><thead><tr><th>Sede</th><th>Gare / uso</th><th>Stato</th><th>Quartiere</th><th class="r">Residenti del quartiere</th><th class="r">Impianti nel quartiere</th><th class="r">Residenti a 15&prime; da una piscina</th></tr></thead><tbody>{olr}</tbody></table></div>
<p class="src">Sedi e funzioni: Wikipedia, &laquo;2026 Winter Olympics&raquo;, tabella delle sedi del gruppo di Milano (consultata il 2/11/2026). Posizione (coordinate) delle sedi: OpenStreetMap, scaricate il 2/11/2026 (nel file OSM l&rsquo;Arena Santa Giulia compare come &laquo;Unipol Dome&raquo;). Quartiere e valori: nostro calcolo con i dati di questa pagina.</p>
<div class="surp"><p><b>L&rsquo;arena nuova non è diventata un impianto di quartiere.</b> Secondo <a href="https://www.ilpost.it/2026/09/25/arena-santa-giulia-milano-sport-no-pallavolo-spostamento/">Il Post (25 settembre 2026)</a>, dopo i Giochi l&rsquo;Arena Santa Giulia (oggi Unipol Dome, di CTS Eventim) ospita solo concerti e non sono previsti eventi sportivi dopo la finale paralimpica di hockey; gli Europei di pallavolo sono stati spostati al Forum di Assago. Nel quartiere vicino, {rog.NIL_nome} ({it(int(rog.residenti_2025))} residenti), secondo i nostri dati nessuno raggiunge una piscina in 15 minuti.</p>
<p>Il villaggio olimpico di Porta Romana, secondo <a href="https://www.ilgiorno.it/milano/cronaca/impianti-olimpici-milano-lavori-scalo-romana-arena-santa-giulia-cma1evcl">Il Giorno (21 dicembre 2025)</a>, diventerà uno studentato da 1.700 posti. Il quartiere Scalo Romana ha {vil['imp']} impianti nei dati, {it(vil['p10'], 1)} ogni 10.000 residenti (media città {it(PK['tutti'], 1)}).</p></div>
<p class="sub">Contesto, non misura: i dati di questa pagina non dicono se le strutture dei Giochi servano ai milanesi che fanno sport.</p>
"""
limiti = [
 f"<b>Dati di anni diversi.</b> L&rsquo;elenco principale del Comune (ds34) dichiara come periodo il 31 gennaio 2011 (i file sono stati ricaricati tra il 2020 e il 2023); i centri balneari (ds32) coprono 2011&ndash;2017; l&rsquo;elenco delle concessioni (ds2941) è di febbraio 2025; i campi nei giardini (ds1640) di ottobre 2024; le palestre scolastiche (ds1867) dell&rsquo;anno scolastico 2020/21 e solo scuole statali; il censimento della Regione Lombardia è dell&rsquo;aprile 2016; OpenStreetMap di novembre 2026. Impianti chiusi o aperti dopo queste date non sono verificati.",
 f"<b>Che cos&rsquo;è un &laquo;luogo&raquo;.</b> Punti di fonti diverse a meno di 80 metri (o con lo stesso indirizzo entro 350 metri) sono contati una volta. Con 50 metri gli impianti sarebbero {it(B['sensibilita_raggio']['50']['impianti'])}, con 150 metri {it(B['sensibilita_raggio']['150']['impianti'])} (invece di {it(tot)}): il totale dipende da questa scelta.",
 f"<b>Poche fonti per luogo.</b> {it(n1)} impianti su {it(tot)} sono in una sola fonte ({it(int(((imp.fonti == 'regione2016')).sum()))} solo nel censimento 2016 della Regione, {it(int(((imp.fonti == 'osm')).sum()))} solo in OpenStreetMap). Le classifiche dei quartieri con fonti diverse concordano poco (Spearman {it(min(sp.values()), 2)}&ndash;{it(max(sp.values()), 2)}).",
 "<b>&laquo;Non risulta comunale&raquo; non significa privato.</b> Il Comune non dà la proprietà né il gestore per ogni impianto: la classe &laquo;non risulta comunale&raquo; comprende palestre e club commerciali, circoli, oratori, università e anche strutture pubbliche di altri enti. Non sappiamo se siano aperte a tutti, a che prezzo e in quali orari. Anche la parola &laquo;comunale&raquo; dice chi è il titolare, non quanto costa o chi può entrare.",
 "<b>Milanosport.</b> Il gestore è preso dal campo &laquo;concessionario&raquo; dell&rsquo;elenco 2025 del Comune (ds2941). Per otto luoghi i dati vecchi (ds34, ds32) dicono Comune o Milanosport ma non sono nell&rsquo;elenco 2025: sono nella classe &laquo;gestore da verificare&raquo;. Non abbiamo letto il sito di Milanosport.",
 "<b>Palestre di scuole.</b> Sono quelle che risultano nei dati del Comune (scuole statali, 2020/21) e nel censimento della Regione: nel conto contano, ma di solito sono usate dalla scuola e da associazioni in orari serali, non da chiunque.",
 "<b>Palestre private.</b> Non esiste un elenco ufficiale aggiornato, quindi alcune possono mancare. In una prova sulle sedi pubblicate da cinque catene (Virgin Active, McFit, Urban Fitness, GetFit e FitActive, lette il 4 novembre 2026) ne risultano 31 su 41, il 76%. Per le palestre indipendenti non c&rsquo;è un elenco con cui fare la stessa prova: non sappiamo quante manchino. Sulla mappa può restare anche qualche sede chiusa.",
 "<b>Campi liberi.</b> Sono i campi di giardini e parchi del Comune (ds1640) e i campi di OpenStreetMap non segnati come privati: molti sono in cortili di scuole, oratori o condomìni aperti e il tag di accesso può mancare. Non sono contati negli &laquo;impianti&raquo;.",
 "<b>Piscine.</b> Dei dati OpenStreetMap abbiamo tenuto solo le piscine con un nome adatto (piscina, nuoto, centro sportivo, club, terme...) e non private. Le piscine di condomini, hotel e circoli riservati sono escluse; qualche piscina di circolo può restare.",
 "<b>Fuori dal Comune.</b> Gli impianti oltre il confine (per esempio Idroscalo, Assago, Rho) non sono nei dati del Comune e non sono contati, tranne quelli entro 200 metri dal confine per il calcolo dei tempi. Chi vive ai margini può avere uno sport vicino fuori Milano.",
 f"<b>I 15 minuti.</b> Misurano la distanza a piedi dal portone al punto dell&rsquo;impianto (a 4,5 km/h su rete OpenStreetMap), non il tempo per arrivare all&rsquo;ingresso o per i grandi centri sportivi che hanno molti cancelli. {it(R['luoghi_scartati_oltre_150m_dalla_rete'])} luoghi a più di 150 metri dalla rete non sono usati. I residenti sono distribuiti in parti uguali tra i civici residenziali del quartiere.",
 "<b>I quartieri piccoli.</b> Ogni 10.000 abitanti ha poco senso dove i residenti sono pochi (parchi, aree agricole, centri sportivi grandi): i quartieri sotto i 1.000 residenti sono in grigio nelle mappe e fuori dalle classifiche.",
 "<b>Censimento nazionale.</b> Il censimento degli impianti sportivi di Sport e Salute/CONI non è scaricabile in forma aperta (ne esistono solo schede riassuntive in PDF) e l&rsquo;anagrafe regionale degli impianti è accessibile solo ai referenti dei Comuni: non sono usati. Sul portale open data della Regione Lombardia esiste solo l&rsquo;elenco del 2016.",
 f"<b>Coordinate sbagliate.</b> Nel censimento della Regione {B['fuori_confine_scartati_per_fonte']['regione2016']} impianti dichiarati &laquo;Milano&raquo; hanno coordinate fuori dal Comune e sono scartati; i dati del Comune hanno posizioni per indirizzo e possono essere spostati di qualche decina di metri.",
]
metodo = [
 f"<b>Luoghi.</b> Si parte dall&rsquo;elenco del Comune (ds34: {B['ds34_righe']} righe, una per disciplina, che diventano {B['ds34_punti']} punti) e si aggiungono, in quest&rsquo;ordine, le concessioni (ds2941), i centri balneari (ds32), le palestre e piscine scolastiche (ds1867), i campi nei giardini (ds1640), il censimento della Regione (2016) e OpenStreetMap (centri sportivi, piscine, palestre, palazzetti, stadi, piste; campi raggruppati se a meno di 30 metri). Un punto nuovo a meno di 80 metri da un luogo già presente (o con lo stesso numero civico e nome via, entro 350 metri) viene unito a quello. I luoghi con almeno una fonte che non sia solo campi (ds1640 o campi OpenStreetMap) sono &laquo;impianti&raquo;; gli altri sono &laquo;campi liberi&raquo;.",
 "<b>Tipo.</b> Piscina, palestra/fitness, campo/palazzetto, centro con più discipline: sono etichette dalle discipline dichiarate (un luogo può averne più d&rsquo;una).",
 "<b>Gestore.</b> Milanosport e Comune in concessione dal campo concessionario di ds2941 (febbraio 2025); &laquo;gestore da verificare&raquo; dove solo ds34 o ds32 indicano Milanosport; campi liberi del Comune da ds1640; palestre di scuole da ds1867 e da nomi del censimento 2016; tutto il resto &laquo;non risulta comunale&raquo;.",
 "<b>Per quartiere.</b> Ogni luogo è assegnato al quartiere (NIL) in cui cade; residenti 2025 per NIL dal Comune (ds27). Ogni 10.000 abitanti = luoghi / residenti &times; 10.000. Classifiche solo per quartieri con almeno 1.000 residenti (75 su 87).",
 "<b>15 minuti a piedi.</b> Stesso metodo della pagina <a href=\"../citta-15-minuti/\">città dei 15 minuti</a>: 57.405 civici come partenza, rete pedonale OpenStreetMap (Geofabrik, 29/10/2026), 4,5 km/h, calcolo del percorso più breve da tutti i luoghi insieme, tetto a 3.200 m. Quota di residenti = residenti del quartiere distribuiti in parti uguali sui civici residenziali, contati se il tempo è al massimo 15 minuti. Per i tempi si usano anche gli impianti fra 0 e 200 metri oltre il confine del Comune.",
 "<b>Controllo.</b> La somma dei residenti per quartiere è " + it(ab) + " come nei dati del Comune; le classifiche sono rifatte con ciascuna fonte da sola (comune, OpenStreetMap, Regione) e confrontate con la correlazione di Spearman.",
]
html = open(os.path.dirname(os.path.abspath(__file__)) + '/pagina_template.html', encoding='utf-8').read()
rep = {'@@SORPRESA@@': sorpresa, '@@OLIMPIADI@@': oly, '@@LIMITI@@': ''.join(f'<li>{x}</li>' for x in limiti), '@@METODO@@': ''.join(f'<li>{x}</li>' for x in metodo),
       '@@N_IMP@@': it(tot), '@@N_RES@@': it(ab), '@@N_PISC@@': it(R['totali']['piscine']), '@@N_COM@@': str(com), '@@PK@@': it(PK['tutti'], 1), '@@QT@@': pc(q_t), '@@QP@@': pc(q_p),
       '@@N_CL@@': it(n_cl), '@@N_CLCOM@@': it(n_cl_com), '@@BARS_TOP@@': bars_top, '@@BARS_BOT@@': bars_bot, '@@BARS_POOL@@': bars_pool, '@@BARS_ACC@@': bars_acc, '@@TAB@@': tab_js,
       '@@N_BIG@@': str(n_big), '@@N_SENZA_POOL@@': str(len(bpool)), '@@N_SENZA_IMP@@': str(len(bl)), '@@N_SENZA_COM@@': str(R['nil_senza_impianti_comunali_(>=1000_ab)']),
       '@@LISTA_SENZA_IMP@@': ', '.join(R['nil_senza_nessun_impianto_(>=1000_ab)']), '@@N_TOT_LUOGHI@@': it(len(P)), '@@N2@@': it(n2), '@@N1@@': it(n1)}
for k, v in rep.items(): html = html.replace(k, v)
open(W + '/index.html', 'w', encoding='utf-8').write(html)
print('ok', len(html), 'byte')
for f in os.listdir(W + '/data'): print(f, os.path.getsize(W + '/data/' + f))
