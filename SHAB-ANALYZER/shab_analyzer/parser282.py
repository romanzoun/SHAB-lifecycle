from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser282_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses; retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + (source_suffix or '') + r'\.?', leftover)
        if m and source_suffix and not re.search(re.escape(leftover.rstrip('.')) + r'\.?$', source_text):
            return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, event_type='officer_changed', **kw):
        return _person_event(*context, event_type, rule, name, **kw)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) ein genehmigtes Kapital gemäss näherer Umschreibung in den Statuten eingeführt\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P<previous_date>{DATE}) ein genehmigtes Kapital gemäss näherer Umschreibung in den Statuten eingeführt\.\]', 'de')
    if m:
        return [event('de.text.authorized_capital_renewed.v1', action='authorized_capital_renewed', **m.groupdict())], ''

    m = match(rf'Mit dem im SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisherige Text nicht richtig publiziert\. Korrekt ist: (?P<name>[^,;]+, Dr\. [^,;]+), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), Präsident des Verwaltungsrates, mit Kollektivunterschrift zu zweien \[bisher: Präsident des Verwaltungsrates, mit Einzelunterschrift, in (?P<previous_place>{NAME})\]', 'de')
    if m:
        return [person('de.persons.board_president_signing_place_corrected.v1', m['name'], role='Präsident des Verwaltungsrates', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'correction': True, 'previous_signing': 'Einzelunterschrift'})], ''

    m = match(rf"La società è sciolta con decisione dell'assemblea dei soci del (?P<decision_date>{DATE})", 'it')
    if m:
        return [event('it.text.members_dissolution.v1', action='dissolution', **m.groupdict())], ''

    m = match(rf"Réduction du capital-actions de CHF (?P<previous_capital>{MONEY}) à CHF (?P<reduced_capital>{MONEY}) par destruction de (?P<destroyed_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY}), pour supprimer un éxcédent de passifs constaté au bilan\. Augmentation ordinaire simultanée du capital-actions\. Nouveau capital-actions entièrement libéré: CHF (?P<capital>{MONEY}) divisé en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY})", 'fr', r', avec restrictions quant à la transmissibilité selon statuts')
    if m and num(m['reduced_capital']) == 0 and all(num(m[k]) > 0 for k in ('previous_capital', 'destroyed_count', 'previous_nominal', 'capital', 'count', 'nominal')) and num(m['previous_capital']) == num(m['destroyed_count']) * num(m['previous_nominal']) and num(m['capital']) == num(m['count']) * num(m['nominal']):
        return [event('fr.text.capital_reduction_zero_simultaneous_increase.v1', action='capital_reduction_simultaneous_increase', fully_paid=True, transfer_restricted=True, **m.groupdict())], ''

    m = match(r"La liquidazione è terminata\. La cancellazione non può essere effettuata mancando il consenso dell'autorità fiscale federale", 'it')
    if m:
        return [event('it.text.liquidation_completed_tax_consent_pending.v1', action='liquidation_completed', deletion_blocked=True, reason='federal_tax_consent_missing')], ''

    m = match(rf'Signature collective à deux, toutefois pas entre eux, est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sous-directeurs', 'fr')
    if m:
        return [person('fr.persons.two_deputy_directors_not_together.v1', m[f'name{i}'], role='sous-directeur', place=m[f'place{i}'], signing='Kollektivunterschrift zu zweien', extra={'origin': m[f'origin{i}'], 'signing_restriction': 'pas entre eux', 'excluded_co_signer': m[f'name{3-i}']}) for i in (1, 2)], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}), Verwaltungsratsmitglied, Einzelunterschfrift, neuer Name (?P<name>{NAME}), nun von (?P<origin>{NAME})', 'de')
    if m:
        return [person('de.persons.board_member_name_origin_changed.v1', m['name'], role='Verwaltungsratsmitglied', signing='Einzelunterschrift', extra={'previous_name': m['previous_name'], 'origin': m['origin']})], ''

    m = match(rf'Einteilung Aktienkapital neu: CHF (?P<capital>{MONEY}), voll liberiert, eingeteilt in (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) \(bisher (?P<previous_count>{COUNT}) Namenaktien zu CHF (?P<previous_nominal>{MONEY})\)\. Statuten geändert am (?P<statutes_date>{DATE})', 'de')
    if m and all(num(v) > 0 for k, v in m.groupdict().items() if not k.endswith('date')) and num(m['capital']) == num(m['count']) * num(m['nominal']) == num(m['previous_count']) * num(m['previous_nominal']):
        return [event('de.text.share_split_fully_paid.v1', action='share_split', fully_paid=True, **m.groupdict())], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) a rectifiée en ce sens que le directeur (?P<name>{NAME}) a la signature collective à deux avec un administrateur \(et non signature individuelle\)", 'fr')
    if m:
        return [person('fr.persons.director_signing_with_board_corrected.v1', m['name'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'correction': True, 'entry': m['entry'], 'entry_date': m['entry_date'], 'signing_restriction': 'avec un administrateur', 'previous_signing': 'Einzelunterschrift'})], ''

    # Initials in departing names are attested by the fixture.
    m = match(rf"(?P<name1>[^,;]+?) et (?P<name2>[^,;]+?) ne sont plus administrateurs; leurs pouvoirs sont radiés\. (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}) et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), sont membres du conseil d'administration", 'fr', r', avec signature collective à deux')
    if m:
        rule = 'fr.persons.two_board_departures_two_appointments.v1'
        return [person(rule, m[f'name{i}'], event_type='officer_removed', role="membre du conseil d'administration", extra={'powers_revoked': True}) for i in (1, 2)] + [person(rule, m[f'name{i}'], role="membre du conseil d'administration", place=m[f'place{i}'], signing='Kollektivunterschrift zu zweien', extra={'origin': m[f'origin{i}']}) for i in (3, 4)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom exact de l'unique associé-gérant est (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}), comme publié\)", 'fr')
    if m:
        return [person('fr.persons.sole_associate_manager_name_corrected.v1', m['name'], role='associé-gérant', extra={**m.groupdict(), 'correction': True, 'sole_associate': True})], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature, avec (?P=transferred) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) part de CHF (?P=nominal)", 'fr')
    if m and all(num(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'remaining')) and num(m['previous']) == num(m['transferred']) + num(m['remaining']) and num(m['remaining']) == 1:
        rule = 'fr.persons.transfer_new_unsigned_associate_one_remaining.v1'
        return [person(rule, m['seller'], role='associé', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'shares': int(num(m['transferred'])), 'share_nominal': m['nominal']})], ''

    return [], leftover
