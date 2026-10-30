"""Dalla tabella pulito/aperture.csv produce i dati della pagina docs/scala/prime/ (aperture.json, statistiche.json) e il registro delle differenze pulito/aperture_differenze.md.
Non pubblica nulla che venga da Operadis (solo controllo locale) ne' testi di Gatti/Marangoni (solo il flag 'confermato').
Uso (dalla cartella scala/): python -I -X utf8 scripts/aperture_pagina.py"""
import sys, os, re, json, collections
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aperture_lib import kt, strip_acc
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda *a: os.path.join(ROOT, *a)
OUT = os.path.join(ROOT, "..", "docs", "scala", "prime", "data")
os.makedirs(OUT, exist_ok=True)
a = pd.read_csv(P("pulito", "aperture.csv")).fillna("")
LOG = json.load(open(P("pulito", "_aperture_log.json"), encoding="utf8"))
b51 = a[a.blocco == "dal_1951"].copy(); b0 = a[a.blocco == "prima_1951"].copy()

SRC = {
 "WP": ["it.wikipedia, «Prime stagionali al Teatro alla Scala»", "CC BY-SA 4.0"],
 "SL": ["it.wikipedia, «Stagioni liriche del Teatro alla Scala»", "CC BY-SA 4.0"],
 "WD": ["Wikidata, voci «serata inaugurale della stagione del Teatro alla Scala»", "CC0"],
 "WPI": ["it.wikipedia, pagine delle singole opere (discografie)", "CC BY-SA 4.0"],
 "WPE": ["en.wikipedia, pagine delle singole opere", "CC BY-SA 4.0"],
 "SBN": ["Catalogo SBN – ICCU, programmi di sala", "licenza non indicata; solo fatti bibliografici"],
 "REG": ["Catalogo SBN – ICCU, registrazioni dal vivo datate 7 dicembre", "licenza non indicata; solo fatti"],
 "SC": ["Sito pubblico del Teatro alla Scala (pagine della serata inaugurale)", "(c) Teatro alla Scala; raccolta autorizzata"],
 "WEB": ["Stampa e siti specializzati (indirizzi nella colonna «controlli» della tabella locale)", "solo fatti, con la fonte"],
 "CA": ["Cambiasi, «Teatro alla Scala 1778-1881» (Ricordi 1881)", "pubblico dominio"],
 "RO": ["Romani, «Teatro alla Scala. Cronologia» (1862)", "pubblico dominio"],
 "MA": ["Marangoni e Vanbianchi, «La Scala 1906-1920» (1922)", "solo un riscontro di data"],
 "GA": ["C. Gatti, «Il Teatro alla Scala nella storia e nell'arte», vol. I (Ricordi 1964)", "solo fatti: il titolo citato nella stagione"],
}
def ncomp(c):
    c = re.sub(r"\(.*?\)", "", c).strip()
    c = c.split(" e ")[0].split(" + ")[0].split(" / ")[0].strip()
    return c
ITA = {"verdi", "puccini", "donizetti", "bellini", "rossini", "catalani", "spontini", "mascagni", "giordano", "salieri", "boito", "ponchielli", "cherubini", "leoncavallo",
       "respighi", "zandonai", "cilea", "mercadante", "pacini", "nicolini", "zingarelli", "cimarosa", "tarchi", "alessandri", "anfossi", "bianchi", "mortellari", "rispoli",
       "minoja", "campobasso", "nasolini", "asioli", "tritto", "pontelibero", "casella", "paer", "pucitta", "brambilla", "schira", "pugni", "ricci", "petrella", "buzzi",
       "mazzucato", "apolloni", "peri", "marchetti", "franchetti", "gomes", "mysliveček", "mayr", "pugni", "riccitelli", "ponchielli", "dall'argine", "vitale", "weigl"}
FOREIGN_EXC = {"mayr": "estero", "gomes": "estero", "mysliveček": "estero", "weigl": "estero", "mozart": "estero"}
def naz(c):
    s = strip_acc(ncomp(c)).lower().split()
    if not s: return "?"
    k = s[-1]
    if k in FOREIGN_EXC: return "estero"
    return "italiano" if k in ITA else "estero"

# --------------------------- aperture.json
def row(r):
    return dict(st=r.stagione, y=int(r.anno), tp=r.tipo, d=r.data, dt=r.data_tipo, dx=r.data_testo, t=r.titolo, c=r.compositore, dir=r.direttore, reg=r.regia,
                cast=r.interpreti, cs=r.interpreti_fonte, sala=r.sala, n=r.note, aff=r.affidabilita, cmp=r.completezza, f=r.fonti, df=r.direttore_fonti, rf=r.regia_fonti,
                alt=r.alternativa, ctl=(r.controlli if r.blocco == "prima_1951" else ""))
d51 = [row(r) for _, r in b51.iterrows()]
d0 = [row(r) for _, r in b0.iterrows()]
# nei controlli del blocco 1951+ ci sono indirizzi e dettagli: nel JSON restano solo per il blocco storico (sono i confronti CA/RO/MA/GA)
today = "2026-10-30"
cov = dict(
    totale=len(b51), con_titolo=int((b51.titolo != "").sum()), con_compositore=int((b51.compositore != "").sum()), con_direttore=int((b51.direttore != "").sum()),
    con_regia=int((b51.regia != "").sum()), con_cast=int((b51.interpreti != "").sum()), con_data=int((b51.data != "").sum()),
    completa=int((b51.completezza == "completa").sum()), senza_cast=int((b51.completezza == "senza cast").sum()),
    disaccordi=int((b51.completezza == "con disaccordi tra le fonti").sum()), una_fonte=int((b51.completezza == "una sola fonte per il direttore").sum()),
    gala=int(b51.completezza.str.startswith("gala").sum()),
    con_direttore_2_fonti=int((b51.direttore_fonti.str.count(r"\+") >= 1).sum()),
    prima_totale=len(b0), prima_con_titolo=int((b0.titolo != "").sum()), prima_chiuse=int((b0.affidabilita == "chiuso").sum()),
    prima_aff=b0.affidabilita.value_counts().to_dict(),
    prima_con_data=int((b0.data != "").sum()), prima_con_direttore=int((b0.direttore != "").sum()),
)
# registro delle lacune
gaps = []
for _, r in b51.iterrows():
    miss = []
    if not r.interpreti: miss.append("cast")
    if r.direttore_fonti.count("+") < 1 and r.anno != 2020: miss.append("seconda fonte per il direttore")
    if r.completezza == "con disaccordi tra le fonti": miss.append("disaccordo tra le fonti")
    if miss: gaps.append([int(r.anno), r.titolo, ", ".join(miss)])
cov["lacune"] = gaps
meta = dict(generato=today, fonti=SRC, nota="Tabella costruita da scala/scripts/aperture_costruisci.py; il 2026 e' la serata programmata per il 7/12/2026")
json.dump(dict(meta=meta, cov=cov, dal1951=d51, prima1951=d0), open(os.path.join(OUT, "aperture.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# --------------------------- statistiche
st51 = b51[~b51.anno.isin([2020])]
def top(series, n=15):
    return [[k, v] for k, v in collections.Counter(series).most_common(n)]
comp51 = [ncomp(c) for c in st51.compositore if c]
cond = []
for v in b51.direttore:
    for p in re.split(r"\s*(?:/|;)\s*", v):
        if p: cond.append(p.strip())
tit = collections.Counter(); tit_names = {}
for t in st51.titolo:
    k = kt(re.sub(r"\(.*?\)", "", t).replace(" e L'amico Fritz", ""))
    tit[k] += 1; tit_names.setdefault(k, re.sub(r"\s*\(.*?\)", "", t))
rep = [[tit_names[k], v] for k, v in tit.most_common() if v >= 2]
# anni delle ripetizioni
rep_years = {}
for t, _ in rep:
    k = kt(t); rep_years[t] = [int(y) for y, tt in zip(st51.anno, st51.titolo) if kt(re.sub(r"\(.*?\)", "", tt)) == k]
dec = collections.OrderedDict()
for _, r in st51.iterrows():
    dk = f"{(int(r.anno)//10)*10}"
    dec.setdefault(dk, {"italiano": 0, "estero": 0})
    dec[dk][naz(r.compositore)] += 1
# tutti i tempi (1778-2026), solo righe con compositore
allc = collections.Counter();
for _, r in a.iterrows():
    for c in re.split(r"\s*\+\s*", r.compositore):
        if c and r.blocco and r.titolo and not str(r.titolo).startswith("A riveder"): allc[ncomp(c)] += 1
# direttori prima del 1951
cond0 = collections.Counter()
for v in b0.direttore:
    for p in re.split(r"\s*(?:/|;)\s*", v):
        if p and p.lower() not in ("il compositore", "il primo violino", "il primo violino e direttore") and not p.lower().startswith("il "): cond0[p.strip()] += 1
sala = collections.Counter(b51.sala)
stats = dict(compositori_1951=top(comp51, 12), direttori_1951=top(cond, 12), ripetute=rep[:14], ripetute_anni=rep_years,
             decenni=[[k, v["italiano"], v["estero"]] for k, v in dec.items()],
             compositori_tutti=[[k, v] for k, v in allc.most_common(12)], direttori_prima=[[k, v] for k, v in cond0.most_common(8)],
             sale=[[k, v] for k, v in sala.most_common()],
             sale_anni_arcimboldi=[int(r.anno) for _, r in b51.iterrows() if "Arcimboldi" in r.sala],
             dal_1951_italiani=sum(v["italiano"] for v in dec.values()), dal_1951_esteri=sum(v["estero"] for v in dec.values()))
json.dump(stats, open(os.path.join(OUT, "statistiche.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print("compositori 1951+:", stats["compositori_1951"][:6])
print("direttori 1951+:", stats["direttori_1951"][:8])
print("ripetute:", rep[:10])
print("decenni:", stats["decenni"])

# --------------------------- differenze.md
old = json.load(open(os.path.join(ROOT, "..", "docs", "scala", "data", "sette_dicembre.json"), encoding="utf8"))
oldmap = {r[0]: r for r in old["serate"]}
L = []
L.append("# Aperture di stagione della Scala: differenze tra le fonti\n")
L.append(f"Generato il {today} da `scripts/aperture_costruisci.py` e `scripts/aperture_pagina.py`. Ogni riga dice cosa dice ciascuna fonte e come e' stata decisa la voce in `aperture.csv`. Le righe che citano Operadis sono solo un controllo locale: non vanno pubblicate.\n")
L.append("## 1. Rispetto alla tabella precedente del sito (`docs/scala/data/sette_dicembre.json`)\n")
L.append(f"- Prima: {len(old['anni_con_data'])} serate su 76 (1951-2026) con una data del 7 dicembre nei dati. Mancavano 2017, 2018, 2020, 2021 (e 2026 non era ancora in elenco). Ora: 76 su 76.")
L.append("- 2017 Andrea Chénier, 2018 Attila: titolo, direttore, regia dalla lista it.wikipedia (+ Wikidata per il 2017, + cronistoria SL e stampa per il 2018).")
L.append("- 2020: nessuna opera: concerto-gala televisivo «A riveder le stelle» (Chailly, regia Livermore), a porte chiuse. Era prevista Lucia di Lammermoor (Chailly, regia Kokkos) secondo la lista WP.")
L.append("- 2021: Macbeth, il 7 dicembre (Chailly, Livermore). La cronistoria SL scrive «prima rappresentazione: 4 dicembre»: probabilmente e' l'anteprima per gli under 30 (dal 2008 precede la serata); la sera del 7 e' confermata dalla tabella degli ascolti TV (WP).")
L.append("- 1955 Norma e 1959 Otello: direttore Antonino Votto (lista WP, Wikidata; per il 1955 anche SBN); la tabella precedente li lasciava vuoti. Entrambe senza disaccordo.")
diffs = []
for y, r in oldmap.items():
    n = b51[b51.anno == y]
    if not len(n): continue
    n = n.iloc[0]
    if r[3] != n.direttore and r[3]: diffs.append(f"- {y}: direttore prima «{r[3]}», ora «{n.direttore}»")
    if r[4] and r[4] != n.regia and r[4].split(";")[0].strip() != n.regia: diffs.append(f"- {y}: regia prima «{r[4]}», ora «{n.regia}»")
    elif not r[4] and n.regia: diffs.append(f"- {y}: regia mancava, ora «{n.regia}»")
L += diffs
L.append("\n## 2. Disaccordi trovati (automatico)\n")
byy = collections.OrderedDict()
for y, c, t in LOG: byy.setdefault(y, []).append((c, t))
for y in sorted(byy):
    for c, t in byy[y]:
        L.append(f"- **{y}** ({c}): {t}")
L.append("\n## 3. Disaccordi decisi a mano\n")
HANDL = [
 "- **1954, direttore della Vestale.** La cronistoria SL dice Victor de Sabata; la lista WP e Wikidata dicono Antonino Votto; en.wikipedia (registrazione del 1954) scrive Votto. Tenuto Votto.",
 "- **1978.** La lista WP annota che questa serata non sarebbe un'inaugurazione ma una replica (Simon Boccanegra nella stagione del bicentenario); la cronistoria SL la da' come prima del 7 dicembre. Una scheda SBN (BID PAV0199737) data al 7/12/1978 una registrazione dal vivo di Boris Godunov (Abbado) mentre il sito della Scala (pagina del Boris 2022) e it.wikipedia datano il Boris di Abbado e Ljubimov al 7 dicembre 1979. Lasciato Boccanegra 1978 con riserva (affidabilita media); da verificare con l'archivio della Scala.",
 "- **1960.** SBN scrive «Franco Cordelli» per Franco Corelli: refuso.",
 "- **1963.** it.wikipedia «L'amico Fritz» data la registrazione del dittico (Gavazzeni, Freni, Raimondi) al «7 dicembre 1962»; SBN la data 7/12/1963 e la lista WP mette il dittico nel 1963. Preso il 1963; il 1962 e' un refuso.",
 "- **2003, regia.** La lista WP scrive «Luigi Ronconi»: refuso per Luca Ronconi (anche le altre fonti). La tabella precedente del sito riportava l'errore.",
 "- **2002-2004, sala.** Il mandato diceva «Arcimboldi 2002-2004». Le fonti (WP lista e sezione «Addobbo floreale») dicono: Arcimboldi per il 2002 e il 2003; il 7 dicembre 2004 e' la riapertura del Piermarini (L'Europa riconosciuta).",
 "- **2013, regia.** Lista WP «Dmitrij Cernjakov», SBN e SL «Dmitri Tcherniakov»: stessa persona, solo traslitterazione.",
 "- **2023, Filippo II.** Sito della Scala (pagina della sera del 7): Michele Pertusi; cronistoria SL: René Pape (e Ain Anger nell'anteprima). Preso il sito della Scala.",
 "- **1906/07, giornale citato.** La lista WP cita per Carmen un articolo del Corriere della Sera datato «19 dicembre 1904»; il Marangoni-Vanbianchi da' la prima della stagione 1906/07 il 19 dicembre 1906. Il 1904 e' un refuso. Preso il 19 dicembre 1906.",
 "- **1923, 1928, 1930 e altre aperture 1920-1930.** Wikidata mette come «serata inaugurale» il 26 dicembre (Tristano e Isotta 1923; I maestri cantori 1928; La fanciulla del West 1930) mentre la lista WP, con articoli del Corriere della Sera, indica un'apertura piu' precoce (16/11/1923; 15/11/1928; 6/12/1930). Probabile: in quegli anni la stagione partiva a novembre e il 26 dicembre apriva il periodo di Carnevale. Messa in tabella l'apertura WP e l'altra come alternativa.",
 "- **1948, direttore.** Wikidata dice Herbert von Karajan per Il trovatore del 26/12/1948; lista WP e SL dicono Victor de Sabata. Tenuto De Sabata (due fonti contro una).",
 "- **1827/28 (Il paria / Elisabetta).** Lista WP e Wikidata: Il paria (Brambilla); Cambiasi e cronistoria SL: Elisabetta regina d'Inghilterra (Rossini) il 26/12/1827. Aperta, affidabilita bassa.",
 "- **Cambiasi, anno sfalsato.** Nel libro 1881 l'anno di molte righe e' ricavato dal programma di lettura (non dal testo): in alcuni tratti (per esempio 1861-1868) l'anno risulta sfalsato di uno rispetto alla lista WP. Quando il primo titolo coincide con uno sfalsamento di un anno la riga e' segnata «primo (anno del libro sfalsato)».",
]
L += HANDL
L.append("\n## 4. Cose che non siamo riusciti a trovare\n")
L.append(f"- Cast: assente per {cov['totale'] - cov['con_cast']} aperture su 76 (1951-2026). Elenco in `pulito/aperture.csv` (colonna `interpreti` vuota).")
L.append("- Dove il cast c'e', i ruoli mancano per le aperture note solo da registrazioni SBN (1952, 1958, 1960-1969...): SBN dà solo i nomi.")
L.append("- 1973 L'italiana in Algeri: direttore e regia da una sola fonte (lista WP).")
L.append("- Stagioni 1796/97, 1797/98, 1807/08, 1809/10, 1816/17, 1823/24-1826/27, 1832/33, 1839/40, 1860/61, 1869/70: assenti dalla lista WP; titolo ricostruito da Wikidata o dal Cambiasi/Romani (OCR da controllare sul libro).")
open(P("pulito", "aperture_differenze.md"), "w", encoding="utf8").write("\n".join(L) + "\n")
print("md righe:", len(L))
print(json.dumps(cov, ensure_ascii=False)[:1200])
