# Prepara i dati della pagina "Quanta corrente, quanta acqua": legge i file scaricati in consumi/raw/
# e scrive i file intermedi in consumi/out/ (giornaliero.csv, citta.json). Non scrive nulla in docs/.
# Uso: python -I -X utf8 prepara.py <radice del progetto>
import csv, datetime as dt, json, os, sys
import openpyxl

TEP_PER_GWH = 86.0          # fattore Istat (report "Trasformazioni e innovazioni nei consumi elettrici", glossario)
GRANDI = ['Torino', 'Genova', 'Milano', 'Venezia', 'Bologna', 'Firenze', 'Roma', 'Napoli', 'Bari',
          'Reggio di Calabria', 'Palermo', 'Messina', 'Catania', 'Cagliari']   # i 14 capoluoghi di citta' metropolitana


def norm(s):
    return ' '.join(str(s).replace('\n', ' ').split()).strip().lower().replace(' (b)', '').replace(' (a)', '').replace(' (c)', '')


def trova(righe, nome):
    for r in righe:
        if r and r[0] is not None and norm(r[0]) in (nome.lower(), nome.lower().replace(' di ', ' ')):
            return r
    raise SystemExit('citta non trovata: ' + nome)


def num(x):
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def nn(r, n):
    # i numeri della riga, nell'ordine, saltando le celle vuote e i segni "X"; ne servono esattamente n
    v = [num(x) for x in r[1:] if num(x) is not None]
    assert len(v) >= n, ('riga corta', r)
    return v[:n]


def foglio(path, nome):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    righe = [tuple(r) for r in wb[nome].iter_rows(values_only=True)]
    wb.close()
    return righe


def anni_riga(righe, cerca):
    for r in righe:
        if r and r[0] and cerca in str(r[0]):
            return [int(x) for x in r[1:] if isinstance(x, (int, float))]
    raise SystemExit('intestazione anni non trovata')


def giornaliero(radice):
    raw = os.path.join(radice, 'consumi', 'raw')
    E = {}
    with open(os.path.join(raw, 'comune', 'ds1574.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            E[r['Data']] = (r['Giorno'], float(r['Totale (GWh)']))
    GAS = {}
    with open(os.path.join(raw, 'comune', 'ds1573.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            assert r['Data'] not in GAS and r['Anno'] == r['Data'][:4], r
            GAS[r['Data']] = (r['Giorno'], float(r['Totale (Smc)']))      # standard metri cubi (qualche riga ha .5)
    T = {}
    with open(os.path.join(radice, 'temperature', 'serie', 'serie_unica.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if '2019-01-01' <= r['date'] <= '2020-12-31':
                T[r['date']] = r
    assert len(E) == 731 and len(T) == 731 and set(E) == set(T) == set(GAS), 'date non allineate'
    assert all(GAS[d][0] == E[d][0] for d in E), 'nomi dei giorni del gas diversi da quelli della corrente'
    out = os.path.join(radice, 'consumi', 'out')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'giornaliero.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['data', 'giorno', 'gwh', 'tmin', 'tmax', 'tmean', 'fonte_temperatura', 'gas_smc'])
        for d in sorted(E):
            w.writerow([d, E[d][0], E[d][1], T[d]['tmin'], T[d]['tmax'], T[d]['tmean'], T[d]['fonte'], GAS[d][1]])


def energia(radice):
    raw = os.path.join(radice, 'consumi', 'raw')
    sto = os.path.join(raw, 'istat_energia', 'ENERGIA_serie_storiche-1.xlsx')
    d24 = os.path.join(raw, 'istat_ambiente', 'tavole', 'ENERGIA_2024.xlsx')
    res = {}
    tabs = {'tep': 'Tav.1.3', 'tep100': 'Tav.1.1', 'gas_tep': 'Tav.4.2', 'dom_tep': 'Tav.2.2', 'nondom_tep': 'Tav.3.2'}
    for k, sh in tabs.items():
        R = foglio(sto, sh)
        anni = anni_riga(R, 'COMUNI')
        for c in GRANDI:
            r = trova(R, c)
            vals = [num(x) for x in r[1:1 + len(anni)]]
            res.setdefault(c, {})[k] = {str(a): v for a, v in zip(anni, vals)}
    # controllo incrociato: GWh diretti 2018-2024 dalla Tav 6.3 del pacchetto "Ambiente urbano 2024"
    R = foglio(d24, 'Tav.6.3-energia')
    milano = trova(R, 'Milano')
    gw = [num(x) for x in milano[1:] if num(x) is not None]
    gwh_diretti = {str(2018 + i): gw[i * 2] for i in range(7)}      # alternati GWh e % del totale provinciale
    R = foglio(d24, 'Tav.6.4-energia')
    gm = [num(x) for x in trova(R, 'Milano')[1:] if num(x) is not None]
    gas_diretto = {str(2018 + i): gm[i * 2] for i in range(7)}
    # elettricita' del Comune (ds1537)
    ds1537 = {}
    with open(os.path.join(raw, 'comune', 'ds1537.csv'), encoding='utf-8-sig') as f:
        for r in csv.reader(f, delimiter=';'):
            if r and r[0].isdigit():
                ds1537[r[0]] = float(r[1].strip().rstrip('.'))       # il 2018 e' scritto "6750.1."
    # ds523: pro capite 2000-2011
    ds523 = {}
    with open(os.path.join(raw, 'comune', 'ds523.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            ds523.setdefault(r['anno'], {})[r['Consumo pro capite tipo']] = float(r['Consumo pro capite'])
    return res, gwh_diretti, gas_diretto, ds1537, ds523


def salto_2009_2010(radice):
    """Per tutti i comuni con elettricita' (Tav 1.3) e gas (Tav 4.2) positivi nel 2009 e nel 2010: variazioni 2009-2010."""
    sto = os.path.join(radice, 'consumi', 'raw', 'istat_energia', 'ENERGIA_serie_storiche-1.xlsx')
    AGG = ('Nord', 'Centro', 'Sud', 'Isole', 'Italia', 'Mezzogiorno', 'Capoluoghi')
    def leggi(sh):
        R = foglio(sto, sh)
        anni = anni_riga(R, 'COMUNI')
        i9, i10 = anni.index(2009), anni.index(2010)
        d = {}
        for r in R:
            if r and r[0] and not str(r[0]).startswith(('Tavola', 'Fonte', '(', 'COMUNI')) and not norm(r[0]).startswith(tuple(a.lower() for a in AGG)):
                a, b = num(r[1 + i9]), num(r[1 + i10])
                if a and b and a > 0 and b > 0:
                    d[norm(r[0])] = b / a - 1
        return d
    E, G = leggi('Tav.1.3'), leggi('Tav.4.2')
    comuni = sorted(set(E) & set(G))
    return dict(n_comuni=len(comuni), el_meno10_gas_piu20=[c for c in comuni if E[c] <= -0.10 and G[c] >= 0.20],
                gas_piu30=[c for c in comuni if G[c] >= 0.30], el_meno10=[c for c in comuni if E[c] <= -0.10])


def acqua(radice):
    raw = os.path.join(radice, 'consumi', 'raw')
    out = {}
    # 2018: Istat, tavole della Giornata mondiale dell'acqua 2021, Tavola 17 (immessa, erogata, perdite)
    R = foglio(os.path.join(raw, 'istat_acqua', 'Tavole_GMA2021.xlsx'), 'Tavola 17')
    for c in GRANDI:
        r = trova(R, c)
        v = nn(r, 5)
        out.setdefault(c, {})['2018'] = dict(immessa_vol=v[0], immessa_pc=v[1], erogata_vol=v[2], erogata_pc=v[3], perdite_pct=v[4])
    # 2020: Istat, Censimento delle acque per uso civile 2020, Tav 15 (immessa, erogata, perdite), Tav 16 (fatturata)
    p20 = os.path.join(raw, 'istat_acqua', 'Censimento_acque_2020.xlsx')
    R15, R16 = foglio(p20, 'Tav 15'), foglio(p20, 'Tav 16')
    for c in GRANDI:
        r, q = trova(R15, c), trova(R16, c)
        v = nn(r, 5)
        w = nn(q, 4)
        out[c]['2020'] = dict(immessa_vol=v[0], immessa_pc=v[1], erogata_vol=v[2], erogata_pc=v[3], perdite_pct=v[4],
                              fatturata_vol=w[0], fatturata_pc=w[1], domestica_vol=w[2], domestica_pc=w[3])
    # 2022: Istat, Le statistiche sull'acqua 2020-2023, Tav 5 e Tav 6
    p22 = os.path.join(raw, 'istat_acqua', 'Istat-GMA2024-Tavole.xlsx')
    R5, R6 = foglio(p22, 'Tav 5'), foglio(p22, 'Tav 6')
    for c in GRANDI:
        r, q = trova(R5, c), trova(R6, c)
        v = nn(r, 5)
        w = nn(q, 4)
        out[c]['2022'] = dict(immessa_vol=v[0], immessa_pc=v[1], erogata_vol=v[2], erogata_pc=v[3], perdite_pct=v[4],
                              fatturata_vol=w[0], fatturata_pc=w[1], domestica_vol=w[2], domestica_pc=w[3])
    # 2024: Istat, Ambiente urbano 2024, ACQUA_2024 Tav 1.1 e 1.2 (dati provvisori)
    p24 = os.path.join(raw, 'istat_ambiente', 'tavole', 'ACQUA_2024.xlsx')
    R11, R12 = foglio(p24, 'Tav 1.1 - Acqua_2024'), foglio(p24, 'Tav 1.2 - Acqua_2024')
    for c in GRANDI:
        r, q = trova(R11, c), trova(R12, c)
        v = nn(r, 5)
        w = nn(q, 4)
        out[c]['2024'] = dict(immessa_vol=v[0], immessa_pc=v[1], erogata_vol=v[2], erogata_pc=v[3], perdite_pct=v[4],
                              fatturata_vol=w[0], fatturata_pc=w[1], domestica_vol=w[2], domestica_pc=w[3])
    # ds1571 (Comune): stesso dato Istat 2018 per Milano, per controllo
    with open(os.path.join(raw, 'comune', 'ds1571.csv'), encoding='utf-8-sig') as f:
        rows = list(csv.reader(f, delimiter=';'))
    ds1571 = [float(x) for x in rows[1]]
    # ds523: acqua fatturata domestica 2000-2011 e' letta in energia()
    return out, ds1571


def terna_led_provincia(radice):
    raw = os.path.join(radice, 'consumi', 'raw')
    # Terna, centro download, "Energia elettrica per settore": somme annue gia' fatte da scarica_terna.py (licenza non indicata)
    terna = {}
    with open(os.path.join(raw, 'terna', 'settori_aggregati.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            terna.setdefault(r['anno'], {}).setdefault(r['provincia'], {})[r['settore']] = float(r['gwh'])
    # Istat, Ambiente urbano 2024, Tav 9.1: consumo totale per provincia, GWh, 2017-2024
    R = foglio(os.path.join(raw, 'istat_ambiente', 'tavole', 'ENERGIA_2024.xlsx'), 'Tav.9.1-energia')
    anni = [int(x) for x in next(r for r in R if r and r[0] and 'PROVINCE' in str(r[0]))[1:] if isinstance(x, (int, float))]
    istat91 = dict(zip([str(a) for a in anni], nn(trova(R, 'Milano'), len(anni))))
    # Comune di Milano, ds1576: lampade di illuminazione pubblica, tradizionali e LED
    led = {}
    with open(os.path.join(raw, 'comune', 'ds1576.csv'), encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            led[r['ANNO']] = [int(r['TRADIZIONALI']), int(r['LED'])]
    return terna, istat91, led


def main(radice):
    giornaliero(radice)
    en, gwh_diretti, gas_diretto, ds1537, ds523 = energia(radice)
    aq, ds1571 = acqua(radice)
    out = os.path.join(radice, 'consumi', 'out')
    terna, istat91, led = terna_led_provincia(radice)
    with open(os.path.join(out, 'citta.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(energia=en, gwh_diretti_milano=gwh_diretti, gas_milioni_m3_milano=gas_diretto, ds1537=ds1537,
                       ds523=ds523, acqua=aq, ds1571=ds1571, salto_2009_2010_comuni=salto_2009_2010(radice), terna=terna, istat_tav91_provincia_milano=istat91, led=led), f, ensure_ascii=False, indent=1)
    print('Scritti giornaliero.csv e citta.json in', out)


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
