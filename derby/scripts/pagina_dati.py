# Fase 2: costruisce la pagina docs/derby/ (index.html + data/) dai file puliti di derby/pulito/
# uso: python -I scripts/pagina_dati.py [derby_dir] [docs_derby_dir]
#   derby_dir      default: la cartella sopra scripts/          (legge pulito/derby.csv, marcatori.csv, differenze.md, non_ufficiali_riepilogo.csv)
#   docs_derby_dir default: ../docs/derby                        (scrive index.html e data/)
# Rilanciabile: riscrive tutto da zero. Ogni numero del testo e' calcolato qui, nessuno e' scritto a mano.
import os, sys, re, json, math, html
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DER = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
OUT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(DER), "docs", "derby")
PUL = os.path.join(DER, "pulito")
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

E = html.escape
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
def dm(s): return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
def dl(s): return f"{int(s[8:10])} {MESI[int(s[5:7]) - 1]} {s[:4]}"
def mese_anno(s): return f"{MESI[int(s[5:7]) - 1]} {s[:4]}"
def sg(b): return f"+{b}" if b > 0 else ("−" + str(-b) if b < 0 else "0")
def pct(a, n): return f"{100 * a / n:.0f}%" if n else "-"
def pct1(a, n): return f"{100 * a / n:.1f}".replace(".", ",") + "%"
def lead(b): return f"Inter +{b}" if b > 0 else (f"Milan +{-b}" if b < 0 else "pari")
def fc(x): return f"{x:.2f}".replace(".", ",")
def num(x): return f"{x:,}".replace(",", ".")

d = pd.read_csv(os.path.join(PUL, "derby.csv")).sort_values(["date", "match_id"]).reset_index(drop=True)
m = pd.read_csv(os.path.join(PUL, "marcatori.csv"))
nu = pd.read_csv(os.path.join(PUL, "non_ufficiali_riepilogo.csv"))
# it.wikipedia, tabella "Partite complessive": competizioni non ufficiali = 72. Il riepilogo di fase 1 dava a "Tournee a Perth" 2 partite
# (Wikipedia non scrive il numero): per tornare a 72 ne vale 1.
NU_TOT = 72
_pm = nu.tournament.str.startswith("Tournee a Perth")
nu.loc[_pm, "matches"] = NU_TOT - int(nu.loc[~_pm, "matches"].sum())
assert int(nu.matches.sum()) == NU_TOT and int(nu.loc[_pm, "matches"].iloc[0]) >= 1
nu["tournament"] = nu.tournament.str.replace("Tournee", "Tournée").str.replace("Coppa Citta", "Coppa Città")
N = len(d)
assert N == 246, N

d["res"] = d.winner.map({"Inter": 1, "Milan": -1, "draw": 0})
d["w"] = d.winner.map({"Inter": "I", "Milan": "M", "draw": "D"})
d["bal"] = d.res.cumsum()
d["year"] = d.date.str[:4].astype(int)
d["gi"] = d.apply(lambda r: r.home_goals if r.home == "Inter" else r.away_goals, axis=1)  # gol Inter
d["gm"] = d.apply(lambda r: r.home_goals if r.home == "Milan" else r.away_goals, axis=1)  # gol Milan
d["awarded"] = d.result_note.fillna("").str.contains("awarded")
WI, DR, WM = int((d.res == 1).sum()), int((d.res == 0).sum()), int((d.res == -1).sum())
GI, GM = int(d.gi.sum()), int(d.gm.sum())
assert (WI, DR, WM, GI, GM) == (91, 71, 84, 341, 324), (WI, DR, WM, GI, GM)  # tabella riassuntiva di it.wikipedia
war = d[d.status != "official"]
off = d[d.status == "official"]
assert len(war) == 2
aw = d[d.awarded]
assert len(aw) == 1
AW = aw.iloc[0]
first, lastd = d.date.iloc[0], d.date.iloc[-1]
tg_real = len(m)  # gol con marcatore
assert tg_real + 2 == GI + GM

# etichette competizione (italiano)
CLAB = {"Prima Categoria": "Prima Categoria", "Divisione Nazionale": "Divisione Nazionale", "Serie A": "Serie A",
        "Campionato Alta Italia 1944": "Campionato Alta Italia 1944 (guerra)", "Coppa Italia": "Coppa Italia",
        "Supercoppa italiana": "Supercoppa italiana", "UEFA Champions League": "Champions League"}
d["comp"] = d.competition_group.map(CLAB)
assert d.comp.notna().all()
ROUND_IT = {"Group stage": "girone", "Final group": "girone finale", "Round 2": "secondo turno", "Final": "finale", "Semi-final": "semifinale",
            "Quarter-final": "quarti", "Round of 16": "ottavi"}
d["round_it"] = d["round"].map(ROUND_IT).fillna("")

# ----------------------------------------------------------------- tabella per competizione
order = d.groupby("comp").date.min().sort_values().index.tolist()
rows = ""
for c in order:
    g = d[d.comp == c]
    a, b = g.season.iloc[0], g.season.iloc[-1]
    ya = g.date.min()[:4]; yb = g.date.max()[:4]
    per = ya if ya == yb else f"{ya}&ndash;{yb}"
    rows += (f"<tr><td>{E(c)}<br><span class='sub'>{per}</span></td><td class='r'>{len(g)}</td><td class='r'><b class='I'>{int((g.res == 1).sum())}</b></td>"
             f"<td class='r'>{int((g.res == 0).sum())}</td><td class='r'><b class='M'>{int((g.res == -1).sum())}</b></td>"
             f"<td class='r'>{int(g.gi.sum())}&ndash;{int(g.gm.sum())}</td><td><span class='sb' role='img' aria-label='Inter {int((g.res == 1).sum())}, pari {int((g.res == 0).sum())}, Milan {int((g.res == -1).sum())}'>"
             f"<i class='i' style='width:{100 * (g.res == 1).mean():.1f}%'></i><i class='d' style='width:{100 * (g.res == 0).mean():.1f}%'></i><i class='m' style='width:{100 * (g.res == -1).mean():.1f}%'></i></span></td></tr>")
rows += (f"<tr class='tot'><td>Totale</td><td class='r'>{N}</td><td class='r'><b class='I'>{WI}</b></td><td class='r'>{DR}</td><td class='r'><b class='M'>{WM}</b></td>"
         f"<td class='r'>{GI}&ndash;{GM}</td><td><span class='sb'><i class='i' style='width:{100 * WI / N:.1f}%'></i><i class='d' style='width:{100 * DR / N:.1f}%'></i><i class='m' style='width:{100 * WM / N:.1f}%'></i></span></td></tr>")
TAB_COMP = ("<table><tr><th>Competizione</th><th class='r'>Derby</th><th class='r'>Vitt. Inter</th><th class='r'>Pari</th><th class='r'>Vitt. Milan</th><th class='r'>Gol I&ndash;M</th><th></th></tr>"
            + rows + "</table>")

wi_off = int(((off.res == 1)).sum()); wm_off = int(((off.res == -1)).sum()); dr_off = int((off.res == 0).sum())
pending = "31 ottobre 2026"  # prossimo derby gia' in calendario (Serie A 2026-27), non ancora giocato
BIG = f"{N} derby: {WI} vittorie dell&rsquo;Inter, {DR} pareggi, {WM} del Milan. Gol: {GI} a {GM} per l&rsquo;Inter."
BREVE = f"""<ul>
<li>Sono i derby <b>ufficiali</b> dal {dl(first)} al {dl(lastd)}, in tutte le competizioni (campionato, Coppa Italia, Supercoppa, Champions League). Il totale &egrave; lo stesso della tabella riassuntiva di it.wikipedia.</li>
<li><b>Due partite del 1944</b> ({dm(war.date.iloc[0])} e {dm(war.date.iloc[1])}, campionato di guerra Alta Italia) sono contate perch&eacute; Wikipedia le conta, ma sono riconosciute solo a titolo onorifico. Senza, i derby sarebbero {len(off)}: Inter {wi_off}, pari {dr_off}, Milan {wm_off}. Nel resto della pagina compaiono sempre segnalate.</li>
<li><b>Il derby di Champions del {dm(AW.date)}</b> fu sospeso al 73&prime; sullo 0-1 (fumogeni dei tifosi interisti) e la UEFA diede 0-3 a tavolino. Qui vale 0-3, come nelle statistiche ufficiali: per questo {GI + GM - tg_real} dei {GI + GM} gol non hanno un marcatore.</li>
<li><b>Non sono contati</b> i prossimi derby gi&agrave; in calendario ({pending}, Serie A 2026-27, e quello di febbraio 2027) e le {int(nu.matches.sum())} partite non ufficiali (amichevoli, tornei minori, coppe di guerra).</li>
</ul>"""

# ----------------------------------------------------------------- saldo / decenni
gp = []
for i_ in range(1, N):
    if (pd.Timestamp(d.date[i_]) - pd.Timestamp(d.date[i_ - 1])).days > 3 * 365:
        gp.append(f"tra il {dl(d.date[i_ - 1])} e il {dl(d.date[i_])}")
gaps_txt = " e ".join(gp)

bal = d.bal.tolist()
mxi, mni = int(d.bal.idxmax()), int(d.bal.idxmin())
sgn = d.bal.apply(lambda x: (x > 0) - (x < 0)).tolist()
runs = []
s0 = 0
for i in range(1, N + 1):
    if i == N or sgn[i] != sgn[s0]:
        runs.append((sgn[s0], s0, i - 1)); s0 = i
long_runs = [(sg_, a, b) for sg_, a, b in runs if b - a + 1 >= 10]
pezzi = []
for sg_, a_, b_ in long_runs:
    who = "l&rsquo;Inter" if sg_ > 0 else "il Milan"
    pezzi.append(f"<li><b>{who}</b> in testa dal {dm(d.date[a_])} al {dm(d.date[b_])}: {b_ - a_ + 1} derby di fila con la linea {'sopra' if sg_ > 0 else 'sotto'} lo zero</li>")
# fasi "di mezzo": tra una fase lunga e l'altra (e prima della prima)
mid = []
edges = [(-1, -1)] + [(a_, b_) for _, a_, b_ in long_runs] + [(N, N)]
for (pa, pb), (na, nb) in zip(edges[:-1], edges[1:]):
    x, y = pb + 1, na - 1
    if y >= x:
        per_ = mese_anno(d.date[x]) if mese_anno(d.date[x]) == mese_anno(d.date[y]) else f"{mese_anno(d.date[x])} &ndash; {mese_anno(d.date[y])}"
        mid.append(f"{per_} ({y - x + 1} derby)")
SALDO_TXT = f"""<p>Le fasi lunghe, con lo stesso club in testa per almeno 10 derby di fila:</p>
<ul>{''.join(pezzi)}</ul>
<p>Nei periodi in mezzo la linea sta vicina allo zero e passa da una parte all&rsquo;altra: {'; '.join(mid)}. Il punto pi&ugrave; basso &egrave; {sg(int(d.bal[mni]))} ({dm(d.date[mni])}, Milan avanti), il pi&ugrave; alto {sg(int(d.bal[mxi]))} ({dm(d.date[mxi])}, Inter avanti); oggi il saldo &egrave; <b>{lead(int(bal[-1]))}</b>.</p>
<p class="warn">Il saldo conta solo vittorie, non gol e non la forza delle squadre in quegli anni. &ldquo;In testa&rdquo; vuol dire soltanto che aveva vinto pi&ugrave; derby fino a quel momento.</p>"""

# decenni: il 1909 (un solo derby) si unisce agli anni Dieci
d["dec"] = (d.year // 10 * 10).replace({1900: 1910})
rows = ""
for dec, g in d.groupby("dec"):
    lab = "1909&ndash;1919" if dec == 1910 else (f"{dec}&ndash;oggi" if dec == 2020 else f"{dec}&ndash;{dec + 9}")
    i_, p_, m_ = int((g.res == 1).sum()), int((g.res == 0).sum()), int((g.res == -1).sum())
    rows += (f"<tr><td>{lab}</td><td class='r'>{len(g)}</td><td class='r'><b class='I'>{i_}</b></td><td class='r'>{p_}</td><td class='r'><b class='M'>{m_}</b></td>"
             f"<td class='r'>{int(g.gi.sum())}&ndash;{int(g.gm.sum())}</td><td class='r'>{lead(i_ - m_)}</td><td class='r'>{lead(int(g.bal.iloc[-1]))}</td>"
             f"<td><span class='sb' role='img' aria-label='Inter {i_}, pari {p_}, Milan {m_}'><i class='i' style='width:{100 * i_ / len(g):.1f}%'></i><i class='d' style='width:{100 * p_ / len(g):.1f}%'></i><i class='m' style='width:{100 * m_ / len(g):.1f}%'></i></span></td></tr>")
TAB_DEC = ("<table><tr><th>Anni</th><th class='r'>Derby</th><th class='r'>Inter</th><th class='r'>Pari</th><th class='r'>Milan</th><th class='r'>Gol I&ndash;M</th><th class='r'>Nel decennio</th><th class='r'>Totale</th><th></th></tr>"
           + rows + "</table>")

# ----------------------------------------------------------------- serie
def streaks(cond):
    out, st = [], None
    for i, v in enumerate(cond):
        if v:
            st = i if st is None else st
        elif st is not None:
            out.append((st, i - 1)); st = None
    if st is not None: out.append((st, len(cond) - 1))
    return sorted(out, key=lambda t: (-(t[1] - t[0]), t[0]))
def top(cond, k=3):
    return streaks(list(cond))[:k]
def cell(sl, dfx=d):
    if not sl: return "&ndash;"
    return "<br>".join(f"<b>{b - a + 1}</b> &middot; {dm(dfx.date[a])} &rarr; {dm(dfx.date[b])}" for a, b in sl)
r = d.res
rows = ""
for lab, ci, cm in [("Vittorie di fila", r == 1, r == -1), ("Imbattuto (vittorie e pareggi)", r >= 0, r <= 0)]:
    rows += f"<tr><td>{lab}</td><td>{cell(top(ci))}</td><td>{cell(top(cm))}</td></tr>"
sn = top(r != 0, 2); sd = top(r == 0, 2)
rows += f"<tr><td>Senza pareggi (nessuno dei due club)</td><td colspan='2'>{cell(sn)}</td></tr><tr><td>Pareggi di fila</td><td colspan='2'>{cell(sd)}</td></tr>"
TAB_STREAK = "<table><tr><th>Serie</th><th class='I'>Inter</th><th class='M'>Milan</th></tr>" + rows + "</table><p class='src'>Lunghezza in grassetto, poi primo e ultimo derby della serie. Mostrate le tre pi&ugrave; lunghe.</p>"
# sensibilita' alle partite dubbie (1944, 2005)
dd = d[d.status == "official"].reset_index(drop=True)
notes = []
for (a_, b_) in streaks(list(r != 0))[:2]:
    if any(d.date[a_] <= x <= d.date[b_] for x in war.date):
        L = b_ - a_ + 1
        Loff = max(y - x + 1 for x, y in streaks(list(dd.res != 0)) if dd.date[x] >= d.date[a_] and dd.date[y] <= d.date[b_])
        notes.append(f"La serie senza pareggi di {L} derby ({dm(d.date[a_])} &rarr; {dm(d.date[b_])}) comprende i due derby di guerra del 1944: senza, nello stesso periodo la serie pi&ugrave; lunga sarebbe di {Loff}.")
STREAK_NOTE = ("<p class='src'>" + " ".join(notes + [f"Il derby di Champions del {dm(AW.date)} (0-3 a tavolino) conta come vittoria del Milan, che stava gi&agrave; vincendo 0-1 al momento della sospensione: non cambia nessuna serie."]) + "</p>")

# ----------------------------------------------------------------- goleade
d["mg"] = (d.gi - d.gm).abs(); d["tg"] = d.gi + d.gm
def mtxt(r_):
    return f"{E(r_.home)} <b>{int(r_.home_goals)}&ndash;{int(r_.away_goals)}</b> {E(r_.away)}"
def tab_matches(g, extra):
    t = "<table><tr><th>Data</th><th>Partita</th><th>Competizione</th></tr>"
    for _, x in g.iterrows():
        fl = " <span class='chip'>a tavolino</span>" if x.awarded else (" <span class='chip'>1944, onorifico</span>" if x.status != "official" else "")
        t += f"<tr><td>{dm(x.date)}</td><td>{mtxt(x)}{fl}</td><td>{E(x.comp)}</td></tr>"
    return t + "</table><p class='src'>" + extra + "</p>"
bg = d[d.mg >= 4].sort_values(["mg", "tg", "date"], ascending=[False, False, True])
hg = d[d.tg >= 8].sort_values(["tg", "mg", "date"], ascending=[False, False, True])
TAB_BIG = tab_matches(bg, f"Scarto di almeno 4 gol: {len(bg)} derby su {N}. Il massimo &egrave; {int(bg.mg.max())}.")
TAB_GOALS = tab_matches(hg, f"Almeno 8 gol in totale: {len(hg)} derby su {N}. In media {str(round(d.tg.mean(), 2)).replace('.', ',')} gol a partita.")

# ----------------------------------------------------------------- in casa?
S = d[(d.neutral_venue == 0) & (~d.awarded)].copy()
S["h"] = (S.home_goals > S.away_goals).astype(int); S["x"] = (S.home_goals == S.away_goals).astype(int); S["a"] = (S.home_goals < S.away_goals).astype(int)
CUT = "1947-01-01"
pre, post = S[S.date < CUT], S[S.date >= CUT]
assert (post.venue == "San Siro").all()
def stat(g):
    n = len(g)
    return dict(n=n, h=int(g.h.sum()), x=int(g.x.sum()), a=int(g.a.sum()), hg=g.home_goals.mean(), ag=g.away_goals.mean())
sp, sq = stat(pre), stat(post)
def se_diff(p1, n1, p2, n2): return math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
ph1, ph2 = sp["h"] / sp["n"], sq["h"] / sq["n"]
mar_pre = 100 * 1.96 * math.sqrt(ph1 * (1 - ph1) / sp["n"])
mar_post = 100 * 1.96 * math.sqrt(ph2 * (1 - ph2) / sq["n"])
mar_diff = 100 * 1.96 * se_diff(ph1, sp["n"], ph2, sq["n"])
diff_pt = 100 * (ph1 - ph2)
within = abs(diff_pt) <= mar_diff
# sensibilita': le 4 partite con etichetta casa/ospite contestata, invertite
disp_ids = ["D083", "D084", "D091", "D092"]
assert set(d[(d.home_label_disputed == 1) & (~d.match_id.isin(["D071", "D072"]))].match_id) == set(disp_ids)
fl = post.copy()
for i in fl.index[fl.match_id.isin(disp_ids)]:
    fl.loc[i, ["home_goals", "away_goals"]] = [fl.loc[i, "away_goals"], fl.loc[i, "home_goals"]]
flh = int((fl.home_goals > fl.away_goals).sum()); fla = int((fl.home_goals < fl.away_goals).sum())
def csb(i_, p_, a_):
    n = i_ + p_ + a_
    return (f"<span class='sb' role='img' aria-label='casa {i_}, pari {p_}, ospite {a_}'><i class='h' style='width:{100 * i_ / n:.1f}%'></i><i class='x' style='width:{100 * p_ / n:.1f}%'></i>"
            f"<i class='a' style='width:{100 * a_ / n:.1f}%'></i></span>")
vpre = pre.venue.fillna("stadio non noto").value_counts()
vtxt = ", ".join(f"{E(k)} {v}" for k, v in vpre.items())
CASA = f"""<p>Fino al 1946 i derby si sono giocati su campi diversi (vedi sotto) e non sempre la squadra &ldquo;di casa&rdquo; giocava nel proprio: gi&agrave; allora l&rsquo;etichetta era in parte solo del calendario. Dal 1947 Inter e Milan giocano <b>tutte e due a San Siro</b>: la squadra &ldquo;di casa&rdquo; nel derby &egrave; solo quella che il calendario mette per prima, il campo &egrave; lo stesso. Se giocare in casa aiutasse, il vantaggio dovrebbe vedersi (al massimo) nel primo periodo e sparire nel secondo. Qui sotto i conteggi, senza colori di club: casa, pareggio, ospite.</p>
<p class="key"><span class="sw h"></span>vince la squadra di casa<span class="sw x"></span>pareggio<span class="sw a"></span>vince la squadra ospite</p>
<div class="sc2"><div><b>Fino al 1946</b><br><span class="sub">{sp['n']} derby</span></div><div>{csb(sp['h'], sp['x'], sp['a'])}<span class="sub">casa {sp['h']} ({pct1(sp['h'], sp['n'])}) &middot; pari {sp['x']} ({pct1(sp['x'], sp['n'])}) &middot; ospite {sp['a']} ({pct1(sp['a'], sp['n'])})</span></div>
<div><b>Dal 1947</b><br><span class="sub">{sq['n']} derby, tutti a San Siro</span></div><div>{csb(sq['h'], sq['x'], sq['a'])}<span class="sub">casa {sq['h']} ({pct1(sq['h'], sq['n'])}) &middot; pari {sq['x']} ({pct1(sq['x'], sq['n'])}) &middot; ospite {sq['a']} ({pct1(sq['a'], sq['n'])})</span></div></div>
<div class="box"><table><tr><th>Squadra &ldquo;di casa&rdquo;</th><th class="r">Derby</th><th class="r">Vince la casa</th><th class="r">Pari</th><th class="r">Vince l&rsquo;ospite</th><th class="r">Gol casa</th><th class="r">Gol ospite</th></tr>
<tr><td>Fino al 1946</td><td class="r">{sp['n']}</td><td class="r">{sp['h']}</td><td class="r">{sp['x']}</td><td class="r">{sp['a']}</td><td class="r">{fc(sp['hg'])} a partita</td><td class="r">{fc(sp['ag'])} a partita</td></tr>
<tr><td>Dal 1947</td><td class="r">{sq['n']}</td><td class="r">{sq['h']}</td><td class="r">{sq['x']}</td><td class="r">{sq['a']}</td><td class="r">{fc(sq['hg'])} a partita</td><td class="r">{fc(sq['ag'])} a partita</td></tr></table></div>
<ul>
<li><b>Prima del 1947</b> la squadra di casa ha vinto il {pct1(sp['h'], sp['n'])} dei derby e quella ospite il {pct1(sp['a'], sp['n'])}.</li>
<li><b>Dal 1947</b>, con lo stesso campo per tutti, casa e ospite sono praticamente pari: {pct1(sq['h'], sq['n'])} contro {pct1(sq['a'], sq['n'])}. I pareggi sono pi&ugrave; frequenti ({pct1(sq['x'], sq['n'])} contro {pct1(sp['x'], sp['n'])}).</li>
<li><b>Numeri piccoli.</b> Prima del 1947 i derby sono solo {sp['n']}: con cos&igrave; poche partite una percentuale ha un margine di circa &plusmn;{mar_pre:.0f} punti ({sp['h']} vittorie su {sp['n']}); dopo il 1947 circa &plusmn;{mar_post:.0f}. La differenza tra i due periodi ({str(round(diff_pt, 1)).replace('.', ',')} punti) {'sta dentro' if within else 'supera'} il margine di circa &plusmn;{mar_diff:.0f} punti: {'quindi non basta per dire che prima del 1947 giocare in casa servisse davvero' if within else 'quindi &egrave; pi&ugrave; grande di quanto il solo caso renda facile'}. &Egrave; una descrizione, non una prova.</li>
</ul>
<p class="src">Dove si giocava prima del 1947 (derby nel confronto): {vtxt}. Esclusi dal conteggio i 3 derby su campo neutro (Supercoppa a Pechino 2011, Riad 2023 e 2025) e il derby del 2005 deciso a tavolino; compresi i 2 derby di guerra del 1944. Se si invertono le 4 partite del 1960-61 e 1964-65 con casa/ospite contestata (vedi <a href="#fonti">Fonti e differenze</a>), dal 1947 le vittorie della casa sarebbero {flh} (invece di {sq['h']}) e quelle dell&rsquo;ospite {fla} (invece di {sq['a']}) su {sq['n']}: non cambia il quadro.</p>"""

# ----------------------------------------------------------------- marcatori
goals_p = m[m.own_goal == 0]
byp = {}
for _, x in goals_p.iterrows():
    byp.setdefault(x.player, {"Inter": 0, "Milan": 0})
    byp[x.player][x.team_credited] += 1
assert all(k in ("Inter", "Milan") for v in byp for k in byp[v])
rank = sorted(byp.items(), key=lambda kv: (-(kv[1]["Inter"] + kv[1]["Milan"]), kv[0]))
THR = 5
topl = [(p, v) for p, v in rank if v["Inter"] + v["Milan"] >= THR]
mxg = max(v["Inter"] + v["Milan"] for p, v in topl)
sh = ""
for p, v in topl:
    tot = v["Inter"] + v["Milan"]
    club = "Inter" if v["Inter"] and not v["Milan"] else ("Milan" if v["Milan"] and not v["Inter"] else f"Inter {v['Inter']} + Milan {v['Milan']}")
    sh += (f"<div class='nm' title='{E(p)}'>{E(p)} <small>{club}</small></div><div class='bar'>"
           f"<i class='i' style='width:{100 * v['Inter'] / mxg:.1f}%'></i><i class='m' style='width:{100 * v['Milan'] / mxg:.1f}%'></i></div><div class='n'>{tot}</div>")
og = m[m.own_goal == 1].sort_values(["date", "minute"])
ogi = int((og.team_credited == "Inter").sum()); ogm = int((og.team_credited == "Milan").sum())
ogt = "<table><tr><th>Data</th><th>Autore dell&rsquo;autogol</th><th>Gol assegnato a</th></tr>" + "".join(
    f"<tr><td>{dm(x.date)}</td><td>{E(x.player)} <span class='sub'>({E(x.scorer_club)})</span></td><td>{E(x.team_credited)}</td></tr>" for _, x in og.iterrows()) + "</table>"
nomin = int((m.minute_known == 0).sum())
penal = int((m.penalty == "1").sum())
n_players = len(byp)
MARC = f"""<p>Giocatori con almeno {THR} gol nei derby ufficiali (autogol esclusi, rigori compresi). Il blu &egrave; per i gol con la maglia dell&rsquo;Inter, il rosso per il Milan; chi ha segnato per tutti e due ha la barra divisa. In totale hanno segnato nei derby {n_players} giocatori diversi.</p>
<div class="sc" role="list">{sh}</div>
<p class="src">Cinque giocatori col massimo: {', '.join(E(p) + ' ' + str(v['Inter'] + v['Milan']) for p, v in topl[:5])}. Nomi come sul tabellino di it.wikipedia (a volte con un&rsquo;ortografia diversa da altre fonti). {nomin} gol del 1910-1914 non hanno il minuto.</p>
<h3>Autogol</h3>
<p>{len(og)} autogol nei derby, contati a favore della squadra che li ha incassati ({ogi} a favore dell&rsquo;Inter, {ogm} del Milan). Non sono nella classifica dei marcatori e non sono assegnati a nessun giocatore come &ldquo;gol&rdquo;.</p>
<details><summary>Elenco delle {len(og)} autogol</summary><div class="box">{ogt}</div></details>
<p class="src">I marcatori sono il pezzo meno controllato: it.wikipedia &egrave; confrontata con altre fonti per i derby fino al 2000 (Almanacco nerazzurro, RSSSF) e per poche coppe; dal 2000 al 2025 il controllo &egrave; pi&ugrave; debole. Nel confronto ci sono 23 segnalazioni (quasi sempre un minuto di differenza), non corrette.</p>"""

# ----------------------------------------------------------------- partite.json
def goal_str(g):
    if g.empty: return ""
    def mkey(v):
        if pd.isna(v): return 999.0
        t = re.match(r"(\d+)(?:\+(\d+))?", str(v))
        return int(t.group(1)) + (int(t.group(2)) / 100 if t.group(2) else 0) if t else 998.0
    g = g.assign(k=g.minute.map(mkey)).sort_values("k", kind="stable")
    seen, items = [], {}
    for _, x in g.iterrows():
        key = (x.player, int(x.own_goal))
        if key not in items:
            items[key] = []; seen.append(key)
        mi = "" if pd.isna(x.minute) else str(x.minute).replace(".0", "") + "′"
        tag = " rig." if str(x.penalty) == "1" else ""
        items[key].append(((mi + tag).strip() if mi else tag.strip()))
    parts = []
    for key in seen:
        pl, ownf = key
        mins = [t for t in items[key] if t]
        s_ = pl + (" (aut.)" if ownf else "")
        gg = g[(g.player == pl) & (g.own_goal == ownf)]
        s_ += (" " + ", ".join(mins) if mins else "")
        if (gg.penalty.astype(str) == "some").any(): s_ += " (uno su rigore)"
        parts.append(s_)
    return ", ".join(parts)
mg = {k: v for k, v in m.groupby("match_id")}
def corr_note(rn):
    if not isinstance(rn, str): return None
    t = re.search(r"Date corrected from (\d{4}-\d\d-\d\d)", rn)
    if t: return f"data corretta (Wikipedia: {dm(t.group(1))})"
    if "Home/away label corrected" in rn: return "casa/ospite corretta rispetto a Wikipedia"
    return None
recs = []
for i, x in d.iterrows():
    g = mg.get(x.match_id, pd.DataFrame(columns=m.columns))
    gh = g[g.team_credited == x.home]; ga = g[g.team_credited == x.away]
    nts = []
    if x.status != "official": nts.append("1944, riconosciuto solo a titolo onorifico")
    if x.awarded: nts.append("sospesa al 73′ sullo 0-1 (fumogeni): 0-3 a tavolino")
    rn = x.result_note if isinstance(x.result_note, str) else ""
    if "After extra time" in rn: nts.append("dopo i tempi supplementari")
    if "away goals" in rn: nts.append("Milan qualificato per i gol in trasferta (1-1 nel totale)")
    c = corr_note(x.result_note)
    if c: nts.append(c)
    if x.home_label_disputed == 1 and x.match_id in disp_ids: nts.append("casa/ospite contestata tra le fonti")
    if x.neutral_venue == 1: nts.append("campo neutro")
    hist = []
    if x.home_club_name not in ("Milan", "Internazionale"): hist.append(f"{x.home_club_name} (casa)")
    if x.away_club_name not in ("Milan", "Internazionale"): hist.append(f"{x.away_club_name} (ospite)")
    recs.append(dict(id=x.match_id, date=x.date, season=x.season, comp=x.comp, round=x.round_it, home=x.home, away=x.away,
                     hg=int(x.home_goals), ag=int(x.away_goals), w=x.w, sb=int(x.bal), venue=x.venue if isinstance(x.venue, str) else "",
                     hist=", ".join(hist), sh=goal_str(gh), sa=goal_str(ga), notes=nts))
with open(os.path.join(OUT, "data", "partite.json"), "w", encoding="utf-8") as f:
    json.dump(recs, f, ensure_ascii=False, separators=(",", ":"))

# ----------------------------------------------------------------- csv pubblici (fatti di Wikipedia) e differenze.md
pubcols = ["match_id", "date", "season", "competition_group", "competition_detail", "round", "round_it_box", "status", "home", "away", "home_club_name", "away_club_name",
           "home_goals", "away_goals", "winner", "venue", "neutral_venue", "referee", "result_note", "home_label_disputed", "sources_checked", "sources_agree", "sources_disagree", "derby_nr_it", "nr_in_competition"]
raw = pd.read_csv(os.path.join(PUL, "derby.csv"))
raw[pubcols].to_csv(os.path.join(OUT, "data", "derby.csv"), index=False, encoding="utf-8")
m.to_csv(os.path.join(OUT, "data", "marcatori.csv"), index=False, encoding="utf-8")
txt = open(os.path.join(PUL, "differenze.md"), encoding="utf-8").read().splitlines()
txt = [ln for ln in txt if not (ln.startswith("| D") and "football-data" in ln)]  # nessun dato di football-data.co.uk
open(os.path.join(OUT, "data", "differenze.md"), "w", encoding="utf-8", newline="\n").write("\n".join(txt) + "\n")

# ----------------------------------------------------------------- fonti e differenze
corr = d[d.match_id.isin(["D022", "D057", "D071", "D072"])]
def line(x):
    return f"{dm(x.date)} &middot; {E(x.home)} {int(x.home_goals)}&ndash;{int(x.away_goals)} {E(x.away)}"
ctab = ("<table><tr><th>Partita (versione corretta)</th><th>Wikipedia diceva</th><th>Chi dice il contrario</th></tr>"
        f"<tr><td>{line(d[d.match_id == 'D022'].iloc[0])}</td><td>19/03/1931 (era un gioved&igrave;, San Giuseppe)</td><td>engsoccerdata, RSSSF, Almanacco Inter: 15/03/1931</td></tr>"
        f"<tr><td>{line(d[d.match_id == 'D057'].iloc[0])}</td><td>16/10/1948</td><td>le stesse tre fonti: 17/10/1948</td></tr>"
        f"<tr><td>{line(d[d.match_id == 'D071'].iloc[0])}</td><td>Inter 2&ndash;1 Milan (casa invertita)</td><td>le stesse tre fonti, e i minuti dei gol tornano con la versione corretta</td></tr>"
        f"<tr><td>{line(d[d.match_id == 'D072'].iloc[0])}</td><td>Milan 1&ndash;2 Inter (casa invertita)</td><td>idem</td></tr></table>")
dtab = "<table><tr><th>Partita (come in it.wikipedia)</th><th>Chi la scrive al contrario</th><th>Chi sta con it.wikipedia</th></tr>"
dis_who = {"D083": ("engsoccerdata", "RSSSF, Almanacco Inter, en.wikipedia"), "D084": ("engsoccerdata", "RSSSF, Almanacco Inter, en.wikipedia"),
           "D091": ("engsoccerdata, RSSSF", "Almanacco Inter, en.wikipedia"), "D092": ("engsoccerdata, RSSSF", "Almanacco Inter, en.wikipedia")}
for k, (a_, b_) in dis_who.items():
    dtab += f"<tr><td>{line(d[d.match_id == k].iloc[0])}</td><td>{a_}</td><td>{b_}</td></tr>"
dtab += "</table>"
nutab = "<table><tr><th>Torneo</th><th class='r'>Partite</th><th>Anni</th></tr>" + "".join(
    f"<tr><td>{E(x.tournament)}</td><td class='r'>{int(x.matches)}</td><td>{E(str(x.years))}</td></tr>" for _, x in nu.iterrows()) + "</table>"
nov = dl(d[d.venue.isna()].date.iloc[0])
FONTI = f"""<h3>Da dove vengono i numeri</h3>
<ul>
<li><b>Lista dei derby</b>: <a href="https://it.wikipedia.org/wiki/Derby_di_Milano">it.wikipedia, &laquo;Derby di Milano&raquo;</a> (revisione del 24 ottobre 2026): date, squadre, punteggi, stadi, marcatori con minuto. Licenza CC BY-SA 4.0: ho preso solo i fatti, nessun testo, e cito la fonte come richiesto dalla licenza. Controllo: <a href="https://en.wikipedia.org/wiki/Derby_della_Madonnina">en.wikipedia, &laquo;Derby della Madonnina&raquo;</a> (28 ottobre 2026) e le pagine delle singole edizioni (campionati, Coppa Italia, Supercoppa, Champions). Sono tutte pagine Wikipedia scritte dalla stessa comunit&agrave;: non sono controlli del tutto indipendenti.</li>
<li><b>Controlli esterni</b> (solo per confrontare, non copiati nella pagina): <b>Almanacco nerazzurro di interfc.it</b> (copia di web.archive.org del febbraio 2017; 149 derby fino al 27 gennaio 2000), <b>engsoccerdata</b> di James Curley (licenza GPL; 186 derby di Serie A dal 1929-30), <b>openfootball/italy</b> (CC0; 31 derby dal 2013-14), <b>RSSSF</b> (libera copia citando la fonte; 196 derby letti).</li>
<li><b>football-data.co.uk</b>: usato <b>solo per controllare data e punteggio</b> di 66 derby (1993-2026). I suoi termini d&rsquo;uso ammettono solo uso privato: nessun suo dato &egrave; ripubblicato qui o nei file scaricabili.</li>
<li>Wikidata: provato, inutilizzabile (le partite non ci sono). Dati raccolti il 30 ottobre 2026.</li>
</ul>
<h3>Quanto concordano</h3>
<p>Ogni derby &egrave; stato confrontato con <b>almeno un&rsquo;altra fonte non Wikipedia</b>, tranne le 3 Supercoppe (2011, 2023, 2025), che hanno solo Wikipedia. Il punteggio &egrave; uguale in tutte le fonti in 240 derby su {N}; le altre 6 differenze riguardano solo quale squadra &egrave; &ldquo;di casa&rdquo; (il vincitore non cambia mai): 2 le correggo, 4 restano contestate (sotto).</p>
<h3>Le 4 correzioni a Wikipedia</h3>
<p>Regola: correggo solo se almeno 3 fonti indipendenti da Wikipedia dicono la stessa cosa contro it.wikipedia ed en.wikipedia.</p>
<div class="box">{ctab}</div>
<h3>Casa/ospite contestati</h3>
<p>Per 4 derby le fonti si dividono su quale squadra fosse &ldquo;di casa&rdquo; (il risultato e il vincitore sono uguali per tutti). Ho lasciato la versione di it.wikipedia. Sono tutti dopo il 1947, quando il campo &egrave; lo stesso (San Siro): per la domanda &ldquo;conta giocare in casa?&rdquo; non cambia nulla di sostanziale.</p>
<div class="box">{dtab}</div>
<h3>Altre differenze, non corrette</h3>
<ul>
<li><b>Date</b>: pochi derby hanno una data diversa in una sola fonte (per esempio il 19 gennaio 1964 che engsoccerdata scrive 3 novembre 1963, o il 13 maggio 2001 contro l&rsquo;11). RSSSF usa spesso la data nominale della giornata e non quella reale. Dove una sola fonte discorda, resta la data di Wikipedia.</li>
<li><b>Stadio</b>: il primo derby (10 gennaio 1909) &egrave; a Porta Monforte per la lista, all&rsquo;Arena Civica per la pagina del campionato. Per il derby del {nov} non c&rsquo;&egrave; lo stadio.</li>
<li><b>Marcatori</b>: 23 segnalazioni (quasi tutte minuti spostati di 1; qualche caso pi&ugrave; grosso, come il 30 maggio 1946, ultimo gol al 75&prime; per Wikipedia e al 47&prime; per RSSSF e Almanacco).</li>
<li>Tutto l&rsquo;elenco con i numeri: <a href="data/differenze.md">differenze.md</a>.</li>
</ul>
<h3>Che cosa non c&rsquo;&egrave;</h3>
<ul>
<li><b>Partite non ufficiali</b>: ce ne sono {int(nu.matches.sum())} (amichevoli, tornei minori, coppe di guerra, Mundialito, tourn&eacute;e). Non sono nei conteggi e non le ho: in fonti libere esistono solo i totali per torneo.
<details><summary>Totali per torneo</summary><div class="box">{nutab}</div><p class="src">Per la tourn&eacute;e a Perth del 2026 Wikipedia non scrive il numero: l&rsquo;1 &egrave; ricavato dal suo totale di {NU_TOT}.</p></details></li>
<li><b>Prossimi derby</b>: {pending} (Serie A 2026-27) e febbraio 2027 non sono ancora giocati.</li>
<li><b>Numero di giornata</b> per il campionato e turno di Coppa Italia nelle prime edizioni: non disponibili.</li>
</ul>
<h3>Trappole da sapere</h3>
<ul>
<li>La squadra &ldquo;di casa&rdquo; &egrave; un&rsquo;etichetta del calendario, non sempre il campo (vedi la sezione sopra).</li>
<li>Nomi di un tempo: l&rsquo;Inter fu Ambrosiana (1929-31) e Ambrosiana-Inter (1931-44), il Milan fu Milano (1939-44). Qui sono sempre Inter e Milan; i nomi storici sono nell&rsquo;elenco, accanto allo stadio.</li>
<li>Le edizioni &ldquo;estive&rdquo; di Coppa Italia (giugno-luglio 1958, 1968, 1972, 1975, 1977, 1985) hanno come stagione l&rsquo;edizione, non l&rsquo;anno del calendario.</li>
<li>Lunghe pause senza derby: {gaps_txt}. Nelle fonti non ce ne sono.</li>
</ul>"""

# ----------------------------------------------------------------- composizione
tpl = open(os.path.join(HERE, "pagina_template.html"), encoding="utf-8").read()
subs = dict(BIG=BIG, BREVE=BREVE, TAB_COMP=TAB_COMP, SALDO_TXT=SALDO_TXT, TAB_DEC=TAB_DEC, TAB_STREAK=TAB_STREAK, STREAK_NOTE=STREAK_NOTE,
            TAB_BIG=TAB_BIG, GAPS=gaps_txt, TAB_GOALS=TAB_GOALS, CASA=CASA, MARC=MARC, FONTI=FONTI, N=str(N))
for k, v in subs.items():
    assert f"@@{k}@@" in tpl, k
    tpl = tpl.replace(f"@@{k}@@", v)
assert "@@" not in tpl
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(tpl)
print("scritto", OUT, "| derby", N, "| gol con marcatore", tg_real, "| giocatori", n_players, "| top", topl[0][0], sum(topl[0][1].values()))
print("casa pre", sp, "post", sq, "margini", round(mar_pre, 1), round(mar_post, 1), round(mar_diff, 1), "diff", round(diff_pt, 1), "flip", flh)
print("big", len(bg), "goals", len(hg))
for n_ in notes: print("NOTA", n_)
