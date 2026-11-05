"""Schema della metropolitana a 45 gradi, solo 2025: genera il blocco dentro docs/metro/index.html.
Legge docs/metro/data/*.csv e riscrive solo il testo tra i segnaposto <!--schema45--> e <!--/schema45--> della pagina:
il resto della pagina non viene toccato, quindi si puo' rilanciare (anche dopo pagina.py, che scrive solo i dati) senza perdere nulla.
Uso: python -I -X utf8 schema45.py <cartella milano-in-dati>"""
import csv, html, re, sys
ROOT = sys.argv[1]
OUT = ROOT + "/docs/metro/index.html"
COL = {"M1": "#E30613", "M2": "#00A651", "M3": "#FFD500", "M4": "#0072BC", "M5": "#8E4FB3"}
FS = 13

# nome -> (x, y, posizione etichetta). Posizioni: N S E W NE NW SE SW oppure (dx, dy, anchor)
P = {}
def add(seq):
    for n, x, y, pos in seq: P[n] = (x, y, pos)

add([("Rho Fiera Milano",-64,520,"W"),("Pero",-20,520,"N"),("Molino Dorino",24,520,"S"),("San Leonardo",68,520,"N"),
     ("Bonola",112,520,"S"),("Uruguay",156,520,"N"),("Lampugnano",200,520,(-8,19,"middle")),("QT8",244,520,(4,19,"middle")),("Lotto",288,520,(-6,19,"middle")),
     ("Amendola",332,520,(8,-11,"middle")),("Buonarroti",376,520,(-2,15,"end")),("Pagano",420,520,"N"),("Conciliazione",464,520,(-4,19,"middle")),
     ("Cadorna",508,520,(-9,-8,"end")),("Cairoli",552,520,"N"),("Cordusio",596,520,"S"),("Duomo",640,520,(-9,-8,"end")),("San Babila",712,520,(7,16,"start")),
     ("Palestro",738,494,"NW"),("Porta Venezia",764,468,"NW"),("Lima",790,442,"NW"),("Loreto",816,416,(8,18,"start")),
     ("Pasteur",816,380,"E"),("Rovereto",816,344,"E"),("Turro",816,308,"E"),("Gorla",816,272,"E"),("Precotto",816,236,"E"),
     ("Villa San Giovanni",816,200,"E"),("Sesto Marelli",816,164,"E"),("Sesto Rondò",816,128,"E"),("Sesto 1° Maggio",816,92,"E"),
     ("Wagner",394,546,(9,6,"start")),("Gambara",368,572,"W"),("De Angeli",342,598,"W"),("Bande Nere",316,624,"W"),
     ("Primaticcio",290,650,"W"),("Inganni",264,676,"W"),("Bisceglie",238,702,"W")])
add([("Lanza",508,484,"W"),("Moscova",532,452,"W"),("Garibaldi",568,416,(-2,21,"start")),("Gioia",604,416,"N"),("Centrale",640,416,"SE"),
     ("Caiazzo",728,416,"N"),("Piola",852,416,"N"),("Lambrate",888,416,(6,17,"start")),("Udine",924,416,(10,3,"start")),("Cimiano",950,390,"SE"),
     ("Crescenzago",976,364,"SE"),("Cascina Gobba",1002,338,"SE"),("Vimodrone",1028,312,"SE"),("Cascina Burrona",1054,286,"SE"),
     ("Cernusco sul Naviglio",1080,260,"SE"),("Villa Fiorita",1106,234,"SE"),("Cassina de' Pecchi",1132,208,"SE"),
     ("Villa Pompea",1158,182,"SE"),("Bussero",1184,156,"SE"),("Gorgonzola",1210,130,"SE"),("Cascina Antonietta",1236,104,"SE"),
     ("Gessate",1262,78,"SE"),("Cologno Sud",1002,302,"W"),("Cologno Centro",1002,266,"W"),("Cologno Nord",1002,230,"W"),
     ("Sant'Ambrogio",508,592,"NE"),("Sant'Agostino",436,664,"E"),("Porta Genova",436,700,"E"),("Romolo",436,736,"E"),
     ("Famagosta",436,772,"E"),("Abbiategrasso",436,808,"E"),("Assago Milanofiori Nord",410,798,"W"),("Assago Milanofiori Forum",384,824,"W")])
add([("Comasina",640,164,"W"),("Affori FN",640,200,"W"),("Affori Centro",640,236,"W"),("Dergano",640,272,"W"),("Maciachini",640,308,"W"),
     ("Zara",640,344,"E"),("Sondrio",640,380,"E"),("Repubblica",640,442,"E"),("Turati",640,468,"W"),("Montenapoleone",640,494,(-10,2,"end")),
     ("Missori",640,556,"W"),("Crocetta",712,628,"E"),("Porta Romana",738,654,"E"),("Lodi",764,680,"E"),("Brenta",790,706,"E"),
     ("Corvetto",816,732,"E"),("Porto di Mare",842,758,"E"),("Rogoredo",868,784,"E"),("San Donato",894,810,"E")])
add([("Linate Aeroporto",1036,520,"E"),("Repetti",964,520,"S"),("Forlanini",924,520,"N"),("Argonne",884,520,"S"),("Susa",844,520,"N"),
     ("Dateo",804,520,(10,17,"middle")),("Tricolore",764,520,(4,-9,"middle")),("Sforza-Policlinico",712,556,"E"),("Santa Sofia",640,628,"S"),("Vetra",604,628,"N"),
     ("De Amicis",568,628,"S"),("Coni Zugna",472,592,(-6,-11,"middle")),("California",436,592,"W"),("Bolivar",410,618,"W"),("Tolstoj",384,644,"W"),
     ("Frattini",358,670,"W"),("Gelsomini",332,696,"W"),("Segneri",306,722,"W"),("San Cristoforo",280,748,"W")])
add([("Bignami",730,146,"W"),("Ponale",730,182,"W"),("Bicocca",730,218,"W"),("Ca' Granda",730,254,"W"),("Istria",700,284,"SE"),
     ("Marche",670,314,"SE"),("Isola",604,380,"NW"),("Monumentale",480,390,"S"),("Cenisio",418,390,(-3,-9,"middle")),("Gerusalemme",392,416,"NW"),
     ("Domodossola",366,442,"NW"),("Tre Torri",340,468,"NW"),("Portello",314,494,(10,2,"start")),("Segesta",262,494,"SW"),
     ("San Siro Ippodromo",236,468,"SW"),("San Siro Stadio",210,442,"SW")])

# percorsi: nomi di stazione, oppure ("@",x,y) = curva senza stazione
LINEE = {
 "M1": [["Rho Fiera Milano","Pero","Molino Dorino","San Leonardo","Bonola","Uruguay","Lampugnano","QT8","Lotto","Amendola","Buonarroti","Pagano","Conciliazione","Cadorna","Cairoli","Cordusio","Duomo","San Babila","Palestro","Porta Venezia","Lima","Loreto","Pasteur","Rovereto","Turro","Gorla","Precotto","Villa San Giovanni","Sesto Marelli","Sesto Rondò","Sesto 1° Maggio"],
        ["Bisceglie","Inganni","Primaticcio","Bande Nere","De Angeli","Gambara","Wagner","Pagano"]],
 "M2": [["Abbiategrasso","Famagosta","Romolo","Porta Genova","Sant'Agostino","Sant'Ambrogio","Cadorna","Lanza",("@",508,476),"Moscova","Garibaldi","Gioia","Centrale","Caiazzo","Loreto","Piola","Lambrate","Udine","Cimiano","Crescenzago","Cascina Gobba","Vimodrone","Cascina Burrona","Cernusco sul Naviglio","Villa Fiorita","Cassina de' Pecchi","Villa Pompea","Bussero","Gorgonzola","Cascina Antonietta","Gessate"],
        ["Assago Milanofiori Forum","Assago Milanofiori Nord","Famagosta"],
        ["Cascina Gobba","Cologno Sud","Cologno Centro","Cologno Nord"]],
 "M3": [["Comasina","Affori FN","Affori Centro","Dergano","Maciachini","Zara","Sondrio","Centrale","Repubblica","Turati","Montenapoleone","Duomo","Missori","Crocetta","Porta Romana","Lodi","Brenta","Corvetto","Porto di Mare","Rogoredo","San Donato"]],
 "M4": [["Linate Aeroporto","Repetti","Forlanini","Argonne","Susa","Dateo","Tricolore","San Babila","Sforza-Policlinico","Santa Sofia","Vetra","De Amicis",("@",544,628),"Sant'Ambrogio","Coni Zugna","California","Bolivar","Tolstoj","Frattini","Gelsomini","Segneri","San Cristoforo"]],
 "M5": [["Bignami","Ponale","Bicocca","Ca' Granda","Istria","Marche","Zara","Isola","Garibaldi",("@",542,390),"Monumentale","Cenisio","Gerusalemme","Domodossola","Tre Torri","Portello","Lotto","Segesta","San Siro Ippodromo","San Siro Stadio"]],
}

# ---- controlli contro i dati
ST = {}
for r in csv.DictReader(open(ROOT + "/docs/metro/data/stazioni_metro.csv", encoding="utf8")):
    ap = {}
    for part in r[[k for k in r if k.startswith("apertura")][0]].split(";"):
        l, d = part.split(":"); ap[l] = int(d[:4])
    ST[r["stazione"]] = ap
usate = {(n, l) for l, ch in LINEE.items() for c in ch for n in c if isinstance(n, str)}
nomi_disegnati = {n for n, l in usate}
assert nomi_disegnati == set(ST), (nomi_disegnati ^ set(ST))
assert set(P) == set(ST), (set(P) ^ set(ST))
for n, ap in ST.items():
    for l in ap: assert (n, l) in usate, (n, l)
for n, l in usate: assert l in ST[n], (n, l)
# ogni tratto orizzontale, verticale o a 45 gradi
def xy(p): return (p[1], p[2]) if isinstance(p, tuple) else P[p][:2]
for l, ch in LINEE.items():
    for c in ch:
        for a, b in zip(c, c[1:]):
            (x1, y1), (x2, y2) = xy(a), xy(b)
            dx, dy = abs(x1 - x2), abs(y1 - y2)
            assert dx == 0 or dy == 0 or dx == dy, (l, a, b)
PAS = {int(r["anno"]): r for r in csv.DictReader(open(ROOT + "/docs/metro/data/passeggeri_linea_anno.csv", encoding="utf8"))}
RETE = {int(r["anno"]): r for r in csv.DictReader(open(ROOT + "/docs/metro/data/rete_km_passeggeri.csv", encoding="utf8"))}

def it(v, dec=0):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

OFF = {"N": (0, -11, "middle"), "S": (0, 19, "middle"), "E": (10, 4, "start"), "W": (-10, 4, "end"),
       "NE": (8, -8, "start"), "NW": (-8, -8, "end"), "SE": (8, 15, "start"), "SW": (-8, 15, "end")}
def label(n):
    x, y, pos = P[n]
    dx, dy, an = OFF[pos] if isinstance(pos, str) else pos
    return x + dx, y + dy, an

def boxes():
    out = []
    for n in P:
        tx, ty, an = label(n)
        w = 0.55 * FS * len(n)
        x0 = tx if an == "start" else tx - w if an == "end" else tx - w / 2
        out.append((n, x0, ty - FS * 0.75, x0 + w, ty + FS * 0.2))
    return out

def controlla():
    B = boxes(); prob = []
    for i, a in enumerate(B):
        for b in B[i + 1:]:
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                prob.append(f"etichette {a[0]} / {b[0]}")
        for n, (x, y, _) in P.items():
            if n != a[0] and a[1] - 3 < x < a[3] + 3 and a[2] - 3 < y < a[4] + 3:
                prob.append(f"etichetta {a[0]} sopra stazione {n}")
    # etichette contro segmenti (campionati)
    for l, ch in LINEE.items():
        for c in ch:
            for s, e in zip(c, c[1:]):
                (x1, y1), (x2, y2) = xy(s), xy(e)
                k = 12
                for t in range(1, k):
                    px, py = x1 + (x2 - x1) * t / k, y1 + (y2 - y1) * t / k
                    for n, x0, y0, x3, y3 in B:
                        if x0 + 1 < px < x3 - 1 and y0 + 1 < py < y3 - 1:
                            prob.append(f"etichetta {n} attraversata da {l} {s}-{e}"); break
    return sorted(set(prob))

W0, H0 = 1540, 800
VB = f"-190 50 {W0} {H0}"

def panel(anno):
    sv = [f'<svg viewBox="{VB}" role="img" aria-label="Schema della metropolitana di Milano nel {anno}" font-family="Helvetica Neue,Helvetica,Arial,sans-serif" font-size="{FS}">']
    sv.append(f'<rect x="-190" y="50" width="{W0}" height="{H0}" fill="#fff"/>')
    aperta = {n: {l: y <= anno for l, y in ap.items()} for n, ap in ST.items()}
    ordine = ["M1", "M2", "M3", "M5", "M4"]
    ordine.sort(key=lambda l: -float(PAS[anno][l]))  # le piu grosse sotto
    for l in ordine:
        mln = float(PAS[anno][l]); c = COL[l]
        for ch in LINEE[l]:
            pts = []
            for p in ch:
                x, y = xy(p)
                ok = True if isinstance(p, tuple) else aperta[p][l]
                pts.append((x, y, ok))
            d = "M" + " L".join(f"{x},{y}" for x, y, _ in pts)
            if mln > 0:
                sv.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{max(mln/12, 2.4):.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
            else:
                sv.append(f'<path d="{d}" fill="none" stroke="#bbb" stroke-width="1.6" stroke-dasharray="5 4" stroke-linejoin="round"/>')
    for n, (x, y, _) in P.items():
        linee_ok = [l for l, ok in aperta[n].items() if ok]
        if not linee_ok:
            sv.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#fff" stroke="#bbb" stroke-width="1.2"/>')
        elif len(linee_ok) >= 2:
            sv.append(f'<circle cx="{x}" cy="{y}" r="6.6" fill="#fff" stroke="#111" stroke-width="2.4"/>')
        else:
            sv.append(f'<circle cx="{x}" cy="{y}" r="3.6" fill="#fff" stroke="#111" stroke-width="1.3"/>')
    for n in P:
        tx, ty, an = label(n)
        linee_ok = [l for l, ok in aperta[n].items() if ok]
        fill = "#111" if linee_ok else "#aaa"
        fw = ' font-weight="700"' if len(linee_ok) >= 2 else ""
        sv.append(f'<text x="{tx}" y="{ty}" text-anchor="{an}" fill="{fill}"{fw}>{html.escape(n)}</text>')
    sv.append("</svg>")
    return "".join(sv)

def legend(anno):
    out = []
    for l in ["M1", "M2", "M3", "M4", "M5"]:
        v = float(PAS[anno][l]); v19 = float(PAS[2019][l]); tc = "#000" if l == "M3" else "#fff"
        if v19 > 0:
            d = (v / v19 - 1) * 100
            txt = f"2025: {it(v,1)} mln · 2019: {it(v19,1)} mln · {'+' if d>0 else '−'}{it(abs(d))}%"
        else:
            txt = f"2025: {it(v,1)} mln · nel 2019 non c&rsquo;era (apre nel 2022)"
        out.append(f'<span class="s45lg"><b style="background:{COL[l]};color:{tc}">{l}</b>{txt}</span>')
    return "".join(out)

css = """<style>
.s45fr{border:1px solid #ddd;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
.s45fr svg{display:block;width:100%;min-width:1100px;height:auto}
.s45lgs{display:flex;flex-direction:column;gap:4px;margin:.6em 0;font-size:.88rem}
.s45lg b{display:inline-block;min-width:30px;text-align:center;border-radius:12px;padding:1px 7px;margin-right:6px;font-size:.8rem}
</style>"""
blocco = (
    '<h3 id="schema45">Lo schema della rete, con lo spessore dei passeggeri (2025)</h3>'
    '<div class="warm"><b>Come leggerlo.</b> &Egrave; uno schema, non una mappa: linee dritte, angoli a 45&deg;, distanze non in scala. '
    'Lo spessore di ogni linea &egrave; il numero di passeggeri di quella linea nel 2025 ed &egrave; uguale lungo tutta la linea, perch&eacute; non esistono dati per tratta. '
    'I nomi in grassetto sono i cambi di linea. Sul telefono lo schema scorre di lato dentro il suo riquadro.</div>'
    f'<div class="s45fr">{panel(2025)}</div>'
    f'<div class="s45lgs">{legend(2025)}</div>'
    '<p class="src"><b>Fonte:</b> passeggeri per linea 2019: AMAT, Report della Mobilit&agrave; 2024 (letti dal grafico, &plusmn;0,5 milioni). '
    '2025: Wikipedia, voce &laquo;Metropolitana di Milano&raquo;, che cita il Report AMAT 2025; non verificato sull&rsquo;originale, tranne la M4 (34,5 milioni), confermata da una seconda fonte. '
    'Km e stazioni: ATM, Carte della Mobilit&agrave;. Stazioni, ordine e date di apertura: dati ATM/AMAT del Comune di Milano e Wikipedia (CC BY-SA 4.0). '
    'I passeggeri sono conteggiati per linea, non per tratta n&eacute; per stazione; chi cambia linea &egrave; contato pi&ugrave; volte. '
    'Disegno originale ispirato all&rsquo;impostazione di Bob Noorda, non &egrave; lo schema ufficiale ATM.</p>'
)
blocco = css + blocco
NL = "\n"
b = open(OUT, "rb").read().decode("utf8")
if "\r\n" in b: NL = "\r\n"
blocco = blocco.replace("\n", NL)
A, Z = "<!--schema45-->", "<!--/schema45-->"
assert b.count(A) == 1 and b.count(Z) == 1, "segnaposto mancanti in docs/metro/index.html"
i, j = b.index(A), b.index(Z)
b = b[:i + len(A)] + NL + blocco + NL + b[j:]
open(OUT, "wb").write(b.encode("utf8"))
print("schema scritto in", OUT, len(blocco) // 1024, "KB")
for p in controlla(): print("ATTENZIONE:", p)
