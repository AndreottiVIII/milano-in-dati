"""Aggiunge alla bozza il capitolo sulle badanti e scrive domestici.csv.
Parte dalla pagina pubblicata (docs/anziani/index.html). Uso: python -I -X utf8 anz_06_capitolo_badanti.py <cartella progetto>"""
import sys, os, json, csv
R = sys.argv[1]
s = open(os.path.join(R, 'docs/anziani/index.html'), encoding='utf-8').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)
# --- csv
D = json.load(open(os.path.join(R, 'docs/anziani/data/domestici.json'), encoding='utf-8'))
with open(os.path.join(R, 'docs/anziani/data/domestici.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['provincia', 'anno', 'badanti_donne', 'badanti_uomini', 'colf_donne', 'colf_uomini', 'italiani', 'stranieri'])
    for p, v in D['province'].items():
        for i, a in enumerate(D['anni']):
            w.writerow([p, a, v['bad_f'][i], v['bad_m'][i], v['colf_f'][i], v['colf_m'][i], v['ita'][i] if v.get('ita') else '', v['str'][i] if v.get('str') else ''])
# --- testi iniziali
rep("e molti anziani sono curati a casa o dalle famiglie: qui di questo non c’è niente. Sono solo conteggi.", "e molti anziani sono curati a casa, dalle famiglie o da badanti: per questo più sotto ci sono anche le badanti e le colf in regola. Sono solo conteggi.")
rep("Comune di Milano, residenti per età e quartiere al 31/12/2025 (CC BY).</p>\n\n<h2 id=\"milano\">", "Comune di Milano, residenti per età e quartiere al 31/12/2025 (CC BY); INPS, Osservatorio sui lavoratori domestici, dati annuali 2016-2025 (nessuna licenza dichiarata: dato aperto per legge, art. 52 del Codice dell’amministrazione digitale).</p>\n\n<h2 id=\"milano\">")
# --- capitolo HTML
cap = '''<h2 id="badanti">Chi cura a casa: badanti e colf</h2>
<p class="intro">Molti anziani non vanno in una RSA: sono assistiti a casa da badanti e colf. Qui si contano solo i rapporti di lavoro in regola, registrati all’INPS.</p>
<div class="fig">
  <h3 id="t-badanti-serie"></h3>
  <p class="sub">Lavoratori domestici con almeno un contributo versato all’INPS nell’anno, in provincia di Milano (la Città metropolitana, con la città dentro), dal 2016 al 2025. Tocca un punto per i numeri.</p>
  <div class="lg"><span><i class="ln" style="background:var(--m2)"></i>badanti</span><span><i class="ln" style="background:var(--ora)"></i>colf e altri lavoratori domestici</span></div>
  <div class="ch" id="ch-badanti-serie" role="img" aria-label="Linee: badanti e colf in regola in provincia di Milano, dal 2016 al 2025"></div>
  <ul class="notes">
    <li><b class="nb">1</b><span>Nel 2020 c’è stata una procedura di emersione dei rapporti di lavoro irregolari (decreto-legge 34/2020). Nello stesso anno i rapporti in regola salgono sia per le badanti sia per le colf. Da questi dati non si può dire quanta parte dell’aumento venga da lì.</span></li>
  </ul>
  <p class="src">Fonte: INPS, Osservatorio sui lavoratori domestici, dati annuali 2016-2025, <a href="https://servizi2.inps.it/servizi/osservatoristatistici/12">banca dati</a>, consultata il 15/11/2026 (nessuna licenza dichiarata: dato aperto per legge, art. 52 del Codice dell’amministrazione digitale). «Badante» e «colf» sono le categorie dell’INPS.</p>
</div>

<div class="fig">
  <h3 id="t-badanti-prov"></h3>
  <p class="sub">Per ogni provincia lombarda, due numeri ogni 100 persone con 80 anni o più: le badanti in regola (2025) e i posti in RSA. Le province sono in ordine di badanti. Tocca un pallino per i numeri.</p>
  <div class="lg"><span><i class="dot" style="background:var(--m2)"></i>badanti in regola</span><span><i class="dot" style="background:var(--m5)"></i>posti in RSA</span></div>
  <div class="ch" id="ch-badanti-prov" role="img" aria-label="Pallini su un asse: badanti in regola e posti in RSA ogni 100 persone con 80 anni o più, nelle 12 province lombarde"></div>
  <p class="sel"><b>Un confronto, non una prova.</b> Dove ci sono più badanti non vuol dire che mancano le RSA, né il contrario: contano le famiglie, i redditi, le abitudini e quante persone lavorano senza contratto, che qui non si vedono.</p>
  <p class="src">Fonte: INPS, Osservatorio sui lavoratori domestici, dati annuali 2025, consultata il 15/11/2026 (dato aperto per legge, art. 52 del Codice dell’amministrazione digitale); Regione Lombardia, elenco delle RSA, 14/11/2026 (stessa licenza); ISTAT, popolazione per età al 1° gennaio 2026 (CC BY 4.0). Le badanti sono contate nella provincia dichiarata all’INPS, i posti dove si trova la RSA.</p>
</div>

<div class="fig">
  <h3 id="t-badanti-chi"></h3>
  <p class="sub">I lavoratori domestici in regola in provincia di Milano nel 2025, divisi in tre modi. Ogni barra è il totale.</p>
  <div class="ch" id="ch-badanti-chi" role="img" aria-label="Tre barre divise: donne e uomini, stranieri e italiani, badanti e colf, tra i lavoratori domestici in provincia di Milano nel 2025"></div>
  <p class="src">Fonte: INPS, Osservatorio sui lavoratori domestici, dati annuali 2025, consultata il 15/11/2026 (dato aperto per legge, art. 52 del Codice dell’amministrazione digitale). Stranieri e italiani: cittadinanza.</p>
</div>

'''
rep('<h2 id="gestori">', cap + '<h2 id="gestori">')
# --- limiti, metodo, file, footer
rep("Per Milano non abbiamo trovato numeri aperti su colf e badanti, e l’elenco comunale dei servizi di cure domiciliari ('+RI.adi_milano+' servizi) non dice quante persone seguono. Quindi questa pagina racconta una parte sola della cura.", "Le badanti e le colf si contano solo se hanno un contratto in regola, e l’elenco comunale dei servizi di cure domiciliari ('+RI.adi_milano+' servizi) non dice quante persone seguono. Quindi questa pagina racconta solo una parte della cura.")
rep("   '<b>Correlazione non è causa.</b>", "   '<b>Badanti: solo i rapporti in regola.</b> Chi lavora senza contratto non c’è nei numeri, e non si sa quanto pesi. Una persona è contata nella provincia dichiarata all’INPS; i dati sono per provincia, non per la sola città di Milano. «Badante» e «colf» sono le categorie dell’INPS, e un lavoratore domestico non è per forza al servizio di un anziano. Le serie degli anni passati possono cambiare quando l’INPS le aggiorna.',\n   '<b>Correlazione non è causa.</b>")
rep("   '<b>Gestore.</b>", "   '<b>Badanti e colf.</b> Lavoratori domestici con almeno un contributo versato nell’anno, da INPS, per provincia (2016-2025). Badanti per 100 over 80: badanti del 2025 diviso le persone con 80 anni o più al 1° gennaio 2026.',\n   '<b>Gestore.</b>")
rep('<li><a href="data/riepilogo.json">', '<li><a href="data/domestici.csv">Badanti e colf in regola per provincia lombarda, 2016-2025</a></li>\n<li><a href="data/riepilogo.json">')
rep("<p>Pagine collegate:", "<p>INPS, <a href=\"https://servizi2.inps.it/servizi/osservatoristatistici/12\">Osservatorio sui lavoratori domestici</a>, dati annuali 2016-2025, banca dati consultata il 15/11/2026: nessuna licenza dichiarata, dato aperto per legge (art. 52 del Codice dell’amministrazione digitale).</p>\n<p>Pagine collegate:")
# --- JS
rep("'gestori.json','riepilogo.json']", "'gestori.json','riepilogo.json','domestici.json']")
rep("RI=a[6];", "RI=a[6];DO=a[7];")
rep("var GJ,Q,R,CO,PV,GE,RI,RD=[];", "var GJ,Q,R,CO,PV,GE,RI,DO,RD=[];")
rep("draw(province);draw(gestori);", "draw(province);draw(badSerie);draw(badProv);draw(badChi);draw(gestori);")
newhl = "{c:'#FFD500',h:'t-badanti-prov',n:f1(bad25('Milano')/provMi().posti),u:' volte',p:'le badanti in regola in provincia di Milano ('+f0(bad25('Milano'))+' nel 2025) rispetto ai posti in RSA ('+f0(provMi().posti)+').'},"
i = s.index("    {c:'#FFD500',h:'t-quartieri'"); j = s.index("\n", i)
s = s[:i] + "    " + newhl + s[j:]
# statico
a = s.index('<li><a href="#t-quartieri"><strong>1,7</strong>'); b = s.index('</li>', a) + 5
mi = D['province']['Milano']; b25 = mi['bad_f'][-1] + mi['bad_m'][-1]
posti = [x for x in json.load(open(os.path.join(R, 'docs/anziani/data/province.json'), encoding='utf-8')) if x['nome'] == 'Milano'][0]['posti']
fm = lambda n: format(n, ',').replace(',', '.')
s = s[:a] + '<li><a href="#t-badanti-prov"><strong>%s volte</strong> le badanti in regola in provincia di Milano (%s nel 2025) rispetto ai posti in RSA (%s).</a></li>' % (('%.1f' % (b25 / posti)).replace('.', ','), fm(b25), fm(posti)) + s[b:]
rep("</ol></div><!--/statico-->", '<li><a href="#t-badanti-serie">Le badanti in regola in provincia di Milano passano da %s nel 2016 a %s nel 2025; le colf calano</a></li></ol></div><!--/statico-->' % (fm(mi['bad_f'][0] + mi['bad_m'][0]), fm(b25)))
funcs = open(os.path.join(R, 'anziani/scripts/anz_badanti.js'), encoding='utf-8').read()
rep("\n/* ---------- 5. gestori ---------- */", "\n" + funcs + "\n/* ---------- 5. gestori ---------- */")
open(os.path.join(R, 'bozze-grafici/anziani-v2/index.html'), 'w', encoding='utf-8').write(s)
print('ok', len(s))
