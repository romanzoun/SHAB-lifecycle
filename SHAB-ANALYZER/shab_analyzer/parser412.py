from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser121 import _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED
from .parser124 import _FR_ONE_COLLECTIVE_SIGNATORY_NOT_TOGETHER
from .parser234 import _FR_TWO_SIGNING_RESTRICTIONS_REMOVED
from .parser252 import _FR_LIQUIDATOR_AND_SHARE_RESTRICTION

_LEGACY = (_DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED,
           _FR_ONE_COLLECTIVE_SIGNATORY_NOT_TOGETHER,
           _FR_TWO_SIGNING_RESTRICTIONS_REMOVED,
           _FR_LIQUIDATOR_AND_SHARE_RESTRICTION)


def extract_parser412_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual clauses without replacing earlier events."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for value in re.findall(DATE, m[0]):
                    datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<authority>[^,;\n]+?) der Beschwerde gegen den Entscheid des Konkursrichters des (?P<court>{NAME}) vom (?P<bankruptcy_date>{DATE}) betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. \[gestrichen: Über den Inhaber dieses Einzelunternehmens ist mit Entscheid (?:der Konkursrichterin|des Konkursrichters) des (?P=court) vom (?P=bankruptcy_date) mit Wirkung ab dem (?P=bankruptcy_date), (?P<time>(?:[01]\d|2[0-3])[.:][0-5]\d) Uhr der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('owner_bankruptcy_appeal_entry_removed_decision', m, 'status_changed', bankruptcy_suspended=True, bankruptcy_entry_removed=True)], ''

    entry = rf'Nr\. (?P<entry1>\d+) vom (?P<entry_date1>{DATE}) \(SHAB vom (?P<notice_date1>{DATE}), Id (?P<notice_id1>\d+)\) und Nr\. (?P<entry2>\d+) vom (?P<entry_date2>{DATE}) \(SHAB vom (?P<notice_date2>{DATE}), Id (?P<notice_id2>\d+)\)'
    m = match(rf'Die Eintragungen {entry} sind wie folgt berichtigt: die richtige UID-Nummer lautet (?P<correct_uid>{UID}) \(und nicht (?P<previous_uid>{UID})\)\. Amtliche Eintragung infolge Fusion der Gemeinden (?P<municipalities>{NAME}), (?P<municipality2>[^,;\n]+?) und (?P<municipality3>{NAME}), Inkrafttreten am (?P<effective_date>{DATE})\. Neue Sitzbezeichnung: (?P<to>{NAME})', 'de')
    if m:
        return [event('uid_corrected_two_entries', m, corrected=True), event('municipality_merger_seat_designation', m, 'seat_changed', official_change=True, reason='municipality_merger')], ''

    # A preceding translation rule consumed the first nested closing parenthesis.
    m = match(r'(?P<suffix>SA\) \((?P<translation>[^\n()]+ \([^\n()]+\) SA)\))', 'de')
    if m:
        source = re.search(r'Uebersetzungen der Firma neu: (?P<translations>\([^\n]+\))\.$', source_text)
        if source and source['translations'].endswith(m[0]):
            return [event('nested_company_translations_completed', source)], ''

    m = match(rf"par (?P<name>[^\n;]+?) \((?P<liquidator_uid>{UID})\), à (?P<place>{NAME}), liquidatrice\. Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant la totalité du capital-actions, ne sont plus restreintes quant à la transmissibilité selon l'article (?P<legal_basis>685a, al\. 3 CO)")
    if m:
        return [person('corporate_liquidator_appointed', m, m['name'], 'Liquidatorin', place=m['place']), event('all_registered_share_restrictions_removed_article', m, 'capital_changed', transfer_restricted=False, currency='CHF')], ''

    m = match(rf"Rectification de l'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) Id (?P<notice_id>\d+)\): (?P<name>{NAME}), associé, (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non pas (?P<previous_count>{COUNT}) parts de CHF (?P=nominal)\), gérant, signature individuelle")
    if m:
        return [event('associate_share_count_corrected_notice', m, 'ownership_changed', corrected=True, currency='CHF'), person('associate_manager_share_count_corrected', m, m['name'], 'Gesellschafter und Geschäftsführer', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf"La commandite de (?P<name1>{NAME}) a été portée de CHF (?P<previous1>{MONEY}) à CHF (?P<amount1>{MONEY})\. La commandite de (?P<name2>{NAME}) a été portée de CHF (?P<previous2>{MONEY}) à CHF (?P<amount2>{MONEY})\. Nouvel associé commanditaire: (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country3>[A-Z]{{3}}), avec une commandite de CHF (?P<amount3>{MONEY}); n'exerce pas la signature")
    if m:
        return [event('two_limited_contributions_increased_new_partner', m, 'capital_changed', currency='CHF'), person('new_unsigned_limited_partner_abroad', m, m['name3'], 'Kommanditär', 'ohne Unterschrift', m['place3'])], ''

    m = match(rf"Les membres du conseil (?P<name1>{NAME}), nommée présidente, (?P<name2>{NAME}), nommée vice-présidente, (?P<name3>{NAME}), jusqu'ici président et (?P<name4>{NAME}), maintenant domicilié à (?P<place4>{NAME}), (?P<country4>[A-Z]{{3}}), jusqu'ici vice-président, continuent à signer collectivement à deux")
    if m:
        return [person('four_board_members_presidency_changed', m, m[f'name{i}'], ['Präsidentin des Verwaltungsrates', 'Vizepräsidentin des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Mitglied des Verwaltungsrates'][i-1], 'Kollektivunterschrift zu zweien', m['place4'] if i == 4 else None) for i in (1, 2, 3, 4)], ''

    m = match(rf'Procuration collective à deux, sauf entre eux a été conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}})')
    if m:
        return [person('two_procurists_not_together_abroad', m, m[f'name{i}'], signing='Kollektivprokura zu zweien', place=m[f'place{i}'], signing_restriction='sauf entre eux', excluded_signing_partners=[m[f'name{3-i}']]) for i in (1, 2)], ''

    m = match(rf'Transformation de (?P<before>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives, , en (?P<count1>{COUNT}) actions de CHF (?P<nominal1>{MONEY}), nominatives, liées selon statuts et priviliégiées quant au droit de vote\. Capital-actions: CHF (?P<capital>{MONEY}), libéré à concurrence de CHF (?P<paid>{MONEY}), divisé en (?P=count1) actions de CHF (?P=nominal1), priviliégiées quant au droit de vote, et (?P<count2>{COUNT}) actions de CHF (?P<nominal2>{MONEY}), toutes nominatives, liées selon statuts\. s')
    if m:
        n = lambda k: Decimal(m[k].replace("'", ''))
        source_clause = f"Transformation de {m['before']} actions de CHF {m['previous_nominal']}, nominatives, liées selon statuts, en {m['count1']} actions de CHF {m['nominal1']}, nominatives, liées selon statuts et priviliégiées quant au droit de vote."
        if source_clause not in source_text or n('before') * n('previous_nominal') != n('count1') * n('nominal1') or n('capital') != n('count1') * n('nominal1') + n('count2') * n('nominal2') or n('paid') > n('capital'):
            return [], text
        return [event('registered_voting_share_split_two_classes', m, 'capital_changed', currency='CHF', transfer_restricted=True, voting_privileged=True)], ''

    m = match(rf"(?P<name>{NAME}), membre du conseil d'administration, continue de signer collectivement à deux, mais désormais sans autre restriction")
    if m:
        return [person('board_member_signing_restrictions_removed', m, m['name'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', signing_restrictions_removed=True)], ''

    m = match(rf"L'associée-gérante (?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé et directeur pour (?P=count) parts de CHF (?P=nominal)")
    if m and re.search(re.escape(m[0]) + r' avec signature collective à deux\.?$', source_text):
        return [event('associate_manager_transfer_to_new_associate_director', m, 'ownership_changed', currency='CHF'), person('new_associate_director_joint_signing', m, m['buyer'], 'Gesellschafter und Direktor', 'Kollektivunterschrift zu zweien', m['place'])], ''
    return [], text
