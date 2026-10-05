from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser277_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed clauses and retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def num(raw):
        return Decimal(raw.replace("'", ''))

    p = rf"(?P<name1>{NAME}), jusqu'ici président, et (?P<name2>{NAME}), jusqu'ici vice-président, restent gérants et continuent à signer collectivement à deux\. (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), président, et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), vice-président, sont gérants"
    m = match(p + ' avec signature collective à deux', 'fr')
    if m:
        rule = 'fr.persons.manager_presidency_replaced.v1'
        return [person(rule, m['name'+str(i)], role='gérant', signing='Kollektivunterschrift zu zweien', extra={'previous_role': role, 'signing_continued': True}) for i, role in ((1, 'président'), (2, 'vice-président'))] + [person(rule, m['name'+str(i)], role='gérant '+role, place=m['place'+str(i)], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'+str(i)]}) for i, role in ((3, 'président'), (4, 'vice-président'))], ''

    m = match(rf"Les membres du conseil (?P<name1>{NAME}), jusqu'ici trésorière, nommée présidente, et (?P<name2>{NAME}), jusqu'ici président, continuent à signer collectivement à deux", 'fr')
    if m:
        rule = 'fr.persons.foundation_presidency_changed.v1'
        return [person(rule, m['name1'], role='membre du conseil présidente', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'trésorière', 'signing_continued': True}), person(rule, m['name2'], role='membre du conseil', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'président', 'signing_continued': True})], ''

    p = rf"L'associé (?P<name>{NAME}) a été nommé gérant"
    m = match(p + ' avec signature collective à deux', 'fr')
    if m:
        return [person('fr.persons.associate_appointed_manager_collective.v1', m['name'], role='associé-gérant', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"(?P<name1>{NAME}), associé-gérant, cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P<received>{COUNT}) parts de CHF (?P=nominal), sans signature\. (?P=name1) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m and num(m['nominal']) > 0 and 0 < num(m['transferred']) < num(m['previous']) and num(m['received']) == num(m['transferred']) and num(m['remaining']) == num(m['previous']) - num(m['transferred']):
        rule = 'fr.persons.manager_transfer_unsigned_associate.v1'
        return [person(rule, m['name1'], role='associé-gérant', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associée', place=m['place'], extra={'origin': m['origin'], 'shares': int(num(m['received'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    m = match(rf"(?P<name1>{NAME}), associé, a cédé (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]), nouvel associé, lequel n'exerce pas la signature sociale", 'fr')
    if m and num(m['nominal']) > 0 and 0 < num(m['transferred']) < num(m['previous']):
        rule = 'fr.persons.associate_transfer_unsigned_abroad.v1'
        return [person(rule, m['name1'], role='associé', extra={'shares': int(num(m['previous']) - num(m['transferred'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé', place=m['place'], extra={'origin': m['origin'], 'country': m['country'], 'received_shares': int(num(m['transferred'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    p = rf"(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) détiennent désormais chacun (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<name4>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P<received>{COUNT}) parts de CHF (?P=nominal)"
    m = match(p + ' avec signature individuelle', 'fr')
    if m and num(m['nominal']) > 0 and num(m['remaining']) > 0 and num(m['transferred']) > 0 and num(m['received']) == num(m['transferred']):
        rule = 'fr.persons.three_holders_transfer_new_manager.v1'
        return [person(rule, m['name'+str(i)], extra={'shares': int(num(m['remaining'])), 'share_nominal': m['nominal']}) for i in (1, 2, 3)] + [person(rule, m['name4'], role='associé-gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(num(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifée en ce sens que (?P<name1>{NAME}) et (?P<name2>{NAME}) signent collectivement à deux, toutefois avec (?P<partner1>{NAME}), (?P<partner2>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\) ou (?P<partner3>{NAME})", 'fr')
    if m:
        rule = 'fr.persons.restricted_signing_partner_corrected.v1'
        extra = {k: v for k, v in m.groupdict().items() if not k.startswith('name')}
        extra.update(correction=True, signing_partners=[m['partner1'], m['partner2'], m['partner3']])
        return [person(rule, m['name'+str(i)], signing='Kollektivunterschrift zu zweien', extra=extra) for i in (1, 2)], ''

    m = match(rf'Vermögensübertragung: Die Genossenschaft überträgt gemäss Verträgen vom (?P<contract_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient_name>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m and all(num(m[k]) >= 0 for k in ('assets', 'liabilities', 'consideration')):
        return [event('de.text.cooperative_asset_transfer_inventory.v1', action='asset_transfer', currency='CHF', **m.groupdict())], ''

    m = match(rf'Mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde die Konkurseröffnung aufgehoben\. Infolgedessen besteht die Firma entsprechend den früheren Eintragungen weiter\. \[bisher: Mit Verfügung des (?P=court) vom (?P<bankruptcy_date>{DATE}) ist über den Inhaber dieses Einzelunternehmens mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<hour>\d{{2}})\.(?P<minute>\d{{2}}) Uhr, der Konkurs eröffnet worden\.\]', 'de')
    if m and int(m['hour']) < 24 and int(m['minute']) < 60:
        return [event('de.text.sole_proprietor_bankruptcy_revoked.v1', action='bankruptcy_revoked', previous_effective_time=m['hour']+':'+m['minute'], continued=True, **m.groupdict())], ''

    p = rf"Les (?P<previous_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY}) formant la totalité du capital-actions, sont transformées en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), L'assemblée générale a introduit deux clauses statutaires relative à deux augmentations conditionnelles du capital par décision du (?P<day>\d{{1,2}}) janvier (?P<year>\d{{4}})\. Pour les détails, voir les statuts"
    source = p.replace(", L'assemblée", ", avec restrictions quant à la transmissibilité selon statuts\\. L'assemblée")
    m = match(source, 'fr')
    if m and all(num(m[k]) > 0 for k in ('previous_count', 'previous_nominal', 'count', 'nominal')) and num(m['previous_count'])*num(m['previous_nominal']) == num(m['count'])*num(m['nominal']):
        try:
            decision_date = datetime(int(m['year']), 1, int(m['day'])).date().isoformat()
        except ValueError:
            return [], leftover
        return [event('fr.text.share_split_two_conditional_capital_clauses.v1', action='share_split', transfer_restricted=True, conditional_capital_clauses=2, decision_date=decision_date, **m.groupdict())], ''

    p = rf"Les (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives, ne sont plus liées selon statuts\. Capital-actions: CHF (?P<capital>{MONEY}), entièrment libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives\. et"
    source = p.replace(r'\. et', rf'\. Statuts modifiés le (?P<statutes_date>{DATE}), et sur des points non soumis à publication')
    m = match(p, 'fr', source)
    if m and num(m['count']) > 0 and num(m['nominal']) > 0 and num(m['count'])*num(m['nominal']) == num(m['capital']):
        return [event('fr.text.share_transfer_restrictions_removed_paid_capital.v1', action='share_transfer_restrictions_removed', fully_paid=True, **m.groupdict())], ''

    p = rf"\[finora: Fr\. (?P<amount1>{COUNT})\.-- tramite conferimento in natura di accessoristica per impianti audio per autoveicoli marca (?P<brand1>{NAME}), da parte della Sig\.a (?P<surname1>{NAME}), (?P<given1>{NAME})\._Fr\. (?P<amount2>{COUNT})\.-- tramite conferimento in natura di un apparecchio Natel marca (?P<brand2>{NAME}) ed accessoristica per Natel, da parte del Sig\. (?P<surname2>{NAME}), (?P<given2>{NAME})\.\]"
    m = match(p, 'it', r'\[Le disposizioni statutarie relative ai conferimenti in natura e all\x27assunzione di beni sono abrogate\] ' + p)
    if m and num(m['amount1']) > 0 and num(m['amount2']) > 0:
        return [event('it.text.historical_in_kind_contributions_abrogated.v1', action='in_kind_contribution_provisions_removed', currency='CHF', **m.groupdict())], ''

    return [], leftover
