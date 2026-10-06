from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser290_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed clauses; preserve unsupported text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=''):
        if language != lang:
            return None
        m = re.fullmatch(pattern + ('(?:' + re.escape(suffix) + ')?' if suffix else '') + r'\.?', leftover)
        if not m:
            return None
        if suffix and leftover.removesuffix('.').removesuffix(suffix) + suffix + '.' not in source_text:
            return None
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date') and v:
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'La succursale de (?P<previous_place>{NAME}) \((?P<uid>{UID})\) a transféré son siège à (?P<place>{NAME}) \((?P=uid)\)')
    if m:
        return [event('fr.text.branch_seat_transfer_same_uid.v1', action='branch_seat_transferred', **m.groupdict())], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}), signent désormais individuellement')
    if m:
        rule = 'fr.persons.two_administrators_individual_signing.v1'
        return [person(rule, m['name' + i], role='administrateur', signing='Einzelunterschrift') for i in ('1', '2')], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont désormais administrateurs', suffix=' avec signature collective à deux')
    if m:
        rule = 'fr.persons.three_administrators_collective_signing.v1'
        return [person(rule, m['name' + i], role='administrateur', signing='Kollektivunterschrift zu zweien') for i in ('1', '2', '3')], ''

    m = match(rf'Selon décision du (?P<authority>{NAME}) du (?P<decision_date>{DATE}), la fondation est dissoute\. Liquidateurs: les membres du conseil (?P<name1>{NAME}) et (?P<name2>{NAME}), lesquels continuent à signer collectivement à deux')
    if m:
        rule = 'fr.text.foundation_dissolution_board_liquidators.v1'
        return [event(rule, action='foundation_dissolved', authority=m['authority'], decision_date=m['decision_date'])] + [person(rule, m['name' + i], role='membre du conseil liquidateur', signing='Kollektivunterschrift zu zweien') for i in ('1', '2')], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<contract_date>{DATE}) la società ha trasferito alla (?P<recipient>{NAME} GmbH), in (?P<place>{NAME}) \((?P<uid>{UID})\), attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Controprestazione: (?P<consideration>nessuna)', 'it')
    if m and number(m['assets']) > 0 and number(m['liabilities']) >= 0:
        return [event('it.text.asset_transfer_no_consideration.v1', action='asset_transfer', currency='CHF', **m.groupdict())], ''

    m = match(rf'Abspaltung: Teile der Aktiven und Passiven gehen gemäss den Spaltungsverträgen vom (?P<contract_date>{DATE}) auf die (?P<recipient1>{NAME}), in (?P<place1>{NAME}) \((?P<uid1>{UID})\), und auf die (?P<recipient2>{NAME}), in (?P<place2>{NAME}) \((?P<uid2>{UID})\), über', 'de')
    if m and m['uid1'] != m['uid2']:
        return [event('de.text.demerger_two_recipients.v1', action='demerger', **m.groupdict())], ''

    months = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12}
    written_date = r'\d{1,2} (?:' + '|'.join(months) + r') \d{4}'
    m = match(rf"Par décision du (?P<decision>{written_date}), le président du (?P<court>[^.;]+?) a prolongé le sursis concordataire définitif accordé à (?P<company>{NAME} SA) jusqu'au (?P<until>{written_date})")
    if m:
        def date(value):
            day, month, year = value.split()
            return datetime(int(year), months[month], int(day))
        try:
            decision, until = date(m['decision']), date(m['until'])
        except ValueError:
            return [], leftover
        if decision < until:
            return [event('fr.text.definitive_moratorium_extended_written_dates.v1', action='definitive_moratorium_extended', decision_date=decision.strftime('%d.%m.%Y'), until_date=until.strftime('%d.%m.%Y'), **m.groupdict())], ''

    m = match(rf"(?P<seller>{NAME}), qui est maintenant à (?P<place>{NAME}), désormais associé gérant secrétaire, cède (?P<transferred>{COUNT}) parts de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), désormais associé gérant président et titulaire de (?P<buyer_total>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) a désormais (?P<remaining>{COUNT}) part de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'buyer_total', 'remaining')) and number(m['remaining']) + number(m['transferred']) == number(m['previous']) and number(m['buyer_total']) >= number(m['transferred']):
        rule = 'fr.persons.manager_share_transfer_secretary_president.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['seller'], role='associé gérant secrétaire', place=m['place'], extra={'shares': int(number(m['remaining'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé gérant président', extra={'shares': int(number(m['buyer_total'])), 'share_nominal': m['nominal']})], ''

    m = match(rf'Anteilscheine neu: Anteilscheine zu CHF (?P<nominal>{MONEY})', 'de')
    if m and number(m['nominal']) > 0:
        return [event('de.text.cooperative_share_nominal_changed.v1', action='cooperative_share_nominal_changed', currency='CHF', **m.groupdict())], ''

    m = match(rf"Nouveaux membres du conseil de fondation(?: avec signature collective à deux:| :) (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), du (?P<origin2>{NAME}), et (?P<name3>{NAME}), d'(?P<origin3>{NAME}), tous deux à (?P<place>{NAME})")
    if m and "Nouveaux membres du conseil de fondation avec signature collective à deux: " + leftover.split(': ', 1)[1].removesuffix('.') + '.' in source_text:
        rule = 'fr.persons.foundation_three_members_shared_residence.v1'
        return [person(rule, m['name' + i], role='membre du conseil de fondation', place=m['place1'] if i == '1' else m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin' + i]}) for i in ('1', '2', '3')], ''

    m = match(rf"Le membre du conseil (?P<name1>{NAME}), nommé secrétaire, signe désormais collectivement à deux\. La membre du conseil (?P<name2>{NAME}), jusqu'ici secrétaire, n'exerce plus la signature sociale")
    if m:
        rule = 'fr.persons.board_secretary_signing_reassigned.v1'
        return [person(rule, m['name1'], role='membre du conseil secrétaire', signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role='membre du conseil', signing='ohne Zeichnungsberechtigung', extra={'previous_role': 'secrétaire'})], ''

    # This clause explicitly restricts both signing groups. Keep the partners
    # and the original restriction wording rather than broadening authority.
    restricted_name = r'[^,;]+?'
    m = match(rf"Signature collective à deux, toutefois entre elles ou avec (?P<name3>{restricted_name}), (?P<name4>{restricted_name}) ou (?P<name5>{restricted_name}), est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), directeur, et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), sous-directrice\. Procuration collective à deux, toutefois entre elles ou avec (?P=name1) et (?P=name2), est conférée à (?P=name3), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P=name4), de (?P<origin4>[^,;]+?), à (?P<place4>{NAME}), et (?P=name5), de (?P<origin5>{NAME}), à (?P<place5>{NAME})")
    if m:
        rule = 'fr.persons.reciprocal_restricted_signing_procuration.v1'
        events = []
        for i in ('1', '2', '3', '4', '5'):
            partners = [m['name' + j] for j in (('3', '4', '5') if i in ('1', '2') else ('1', '2'))]
            events.append(person(rule, m['name' + i], role={'1': 'directeur', '2': 'sous-directrice'}.get(i), place=m['place' + i], signing='Kollektivunterschrift zu zweien' if i in ('1', '2') else 'Kollektivprokura zu zweien', extra={'origin': m['origin' + i], 'signing_restriction': leftover.split('Signature collective à deux, ', 1)[1].split(', est conférée', 1)[0] if i in ('1', '2') else leftover.split('Procuration collective à deux, ', 1)[1].split(', est conférée', 1)[0], 'signing_partners': partners, 'within_group_allowed': True}))
        return events, ''

    return [], leftover
