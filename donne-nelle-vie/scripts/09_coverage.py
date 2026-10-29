"""Copertura: unisce strade, etimologie Wikidata e matching; scrive strade_persone.csv e copertura.json."""
import sys, json, re, pandas as pd
units_csv, etim_csv, match_csv, osm_agg_csv, out_csv, out_json = sys.argv[1:7]
u = pd.read_csv(units_csv, dtype=str).fillna('')
et = pd.read_csv(etim_csv, dtype=str).fillna('').set_index('qid')
m = pd.read_csv(match_csv, dtype=str).fillna('')
osm = pd.read_csv(osm_agg_csv, dtype=str).fillna('')
core_hw = ('residential', 'tertiary', 'secondary', 'primary', 'unclassified', 'living_street', 'pedestrian', 'place=square', 'trunk')
u['core'] = u.apply(lambda r: r.origine == 'comune' or r.highway_osm.split(':')[0] in core_hw, axis=1)
u['chiave_match'] = u.apply(lambda r: r.codice_via if r.origine == 'comune' else 'osm:' + r.descrittivo, axis=1)
m['chiave_match'] = m.apply(lambda r: r.codice_via if r.origine == 'comune' else 'osm:' + r.nome_strada, axis=1)
mm = m.drop_duplicates('chiave_match').set_index('chiave_match')

rows = []
for _, r in u.iterrows():
    d = dict(codice_via=r.codice_via, origine=r.origine, core=int(r.core), nome=(r.tipo + ' ' + r.descrittivo).strip() if r.origine == 'comune' else r.descrittivo,
             tipo=r.tipo, data_intitolazione=r.data_intitolazione, fonte_persona='', stato='', qid='', persona_label='', sesso='', professioni_it='',
             anno_nascita='', anno_morte='', note='')
    qs = [q for q in r.qids_osm.split(';') if q]
    if qs:
        d['fonte_persona'] = 'tag_osm'
        hum = [q for q in qs if q in et.index and et.loc[q, 'umano'] == '1']
        if hum:
            sexes = {et.loc[q, 'sesso'] for q in hum}
            d['qid'] = ';'.join(hum)
            d['persona_label'] = ' | '.join(et.loc[q, 'label'] for q in hum)
            d['professioni_it'] = ' | '.join(et.loc[q, 'professioni_it'] for q in hum)
            d['anno_nascita'] = ' | '.join(et.loc[q, 'anno_nascita'] for q in hum)
            d['anno_morte'] = ' | '.join(et.loc[q, 'anno_morte'] for q in hum)
            if sexes == {'donna'}: d['sesso'] = 'donna'
            elif sexes == {'uomo'}: d['sesso'] = 'uomo'
            elif sexes == {''}: d['sesso'] = 'non indicato'
            else: d['sesso'] = 'misto/altro'
            d['stato'] = 'tag_persona'
            if len(hum) != len(qs): d['note'] = 'tag con piu QID, alcuni non umani'
        else:
            d['stato'] = 'tag_non_persona'
            d['qid'] = ';'.join(qs)
            d['persona_label'] = ' | '.join(et.loc[q, 'label'] for q in qs if q in et.index)
            d['note'] = ' | '.join(et.loc[q, 'p31_en'] for q in qs if q in et.index)[:80]
    elif r.chiave_match in mm.index:
        x = mm.loc[r.chiave_match]
        d['fonte_persona'] = 'matching_automatico'
        d['stato'] = {'persona|sicuro': 'match_sicuro', 'persona|incerto': 'match_incerto'}.get(f"{x.categoria}|{x.confidenza}", 'match_' + x.categoria)
        d['qid'] = x.candidati_qid; d['persona_label'] = x.candidati_label; d['sesso'] = x.sesso_primo
        d['anno_nascita'] = x.nascita_primo; d['anno_morte'] = x.morte_primo; d['note'] = x.motivo
    rows.append(d)
df = pd.DataFrame(rows)
df.to_csv(out_csv, index=False, encoding='utf-8-sig')

core = df[df.core == 1]
cnt = lambda s: int(s.sum())
cov = dict()
cov['osm_nomi_unici_totale'] = len(osm)
cov['osm_nomi_unici_con_tag_etymology_wikidata'] = int((osm.etymology_wikidata != '').sum())
cov['registro_comune_codici_via'] = int((df.origine == 'comune').sum())
cov['osm_solo_osm_non_nel_registro'] = int((df.origine == 'solo_osm').sum())
cov['osm_solo_osm_core'] = int(((df.origine == 'solo_osm') & (df.core == 1)).sum())
cov['universo_core'] = len(core)
cov['core_con_tag'] = int((core.fonte_persona == 'tag_osm').sum())
cov['core_senza_tag'] = int((core.fonte_persona != 'tag_osm').sum())
tag = core[core.fonte_persona == 'tag_osm']
cov['tag_verso_persona'] = int((tag.stato == 'tag_persona').sum())
cov['tag_verso_persona_sesso_noto'] = int(tag.sesso.isin(['donna', 'uomo']).sum())
cov['tag_verso_non_persona'] = int((tag.stato == 'tag_non_persona').sum())
cov['tag_donne'] = int((tag.sesso == 'donna').sum()); cov['tag_uomini'] = int((tag.sesso == 'uomo').sum())
cov['tag_misto_altro_non_indicato'] = int(tag.sesso.isin(['misto/altro', 'non indicato']).sum())
un = core[core.fonte_persona != 'tag_osm']
cov['senza_tag_match_sicuro'] = int((un.stato == 'match_sicuro').sum())
cov['senza_tag_match_incerto'] = int((un.stato == 'match_incerto').sum())
cov['senza_tag_luogo'] = int((un.stato == 'match_luogo').sum())
cov['senza_tag_data_evento'] = int((un.stato == 'match_data_evento').sum())
cov['senza_tag_altro_non_persona'] = int((un.stato == 'match_altro_non_persona').sum())
cov['senza_tag_nessuno'] = int((un.stato == 'match_sconosciuto').sum())
cov['senza_tag_sicuro_donne'] = int(((un.stato == 'match_sicuro') & (un.sesso == 'donna')).sum())
cov['senza_tag_sicuro_uomini'] = int(((un.stato == 'match_sicuro') & (un.sesso == 'uomo')).sum())
cov['senza_tag_incerto_donne_primo_candidato'] = int(((un.stato == 'match_incerto') & (un.sesso == 'donna')).sum())
cov['senza_tag_incerto_uomini_primo_candidato'] = int(((un.stato == 'match_incerto') & (un.sesso == 'uomo')).sum())
cov['donne_tag_piu_sicuro'] = cov['tag_donne'] + cov['senza_tag_sicuro_donne']
cov['uomini_tag_piu_sicuro'] = cov['tag_uomini'] + cov['senza_tag_sicuro_uomini']
cov['persone_trovate_tag_piu_sicuro'] = cov['donne_tag_piu_sicuro'] + cov['uomini_tag_piu_sicuro']
cov['quota_donne_tra_persone_trovate'] = round(cov['donne_tag_piu_sicuro'] / max(1, cov['persone_trovate_tag_piu_sicuro']), 4)
# data di intitolazione
c = df[df.origine == 'comune']
cov['comune_con_data_intitolazione'] = int((c.data_intitolazione != '').sum())
cov['comune_data_segnaposto_17000101_19000101'] = int(c.data_intitolazione.isin(['17000101', '19000101']).sum())
fem = c[(c.sesso == 'donna') & (c.data_intitolazione != '')]
cov['strade_donne_con_data_intitolazione'] = len(fem)
cov['strade_donne_comune_totale'] = int((c.sesso == 'donna').sum())
json.dump(cov, open(out_json, 'w'), indent=1, ensure_ascii=False)
print(json.dumps(cov, indent=1, ensure_ascii=False))
