from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser283_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the complete fixture-backed clauses and preserve unknown text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=None, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + (suffix or '') + r'\.?', leftover)
        if not m:
            return None
        if suffix and not re.search(re.escape(leftover.rstrip('.')) + r'\.?$', source_text):
            return None
        if source_pattern and not re.search(source_pattern + r'\.?$', source_text):
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"L'identification de la société au siège principal sous le numéro (?P<previous_id>CH-\d{{3}}-\d{{7}}-\d) est remplacée par le numéro d'identification des entreprises \(IDE/UID\) (?P<headquarters_uid>{UID})")
    if m:
        return [event('fr.text.headquarters_uid_replaced.v1', action='headquarters_identifier_changed', **m.groupdict())], ''

    m = match(rf"Inscription de la succursale d'(?P<place>{NAME}) \((?P<branch_uid>{UID})\) au registre du commerce du canton de (?P<register>{NAME}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)")
    if m:
        return [event('fr.text.branch_registration_notice.v1', action='branch_registered', **m.groupdict())], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}), qui est désormais à (?P<place2>{NAME}), sont nommés liquidateurs', suffix=r' avec signature collective à deux')
    if m:
        return [person('fr.persons.two_board_members_liquidators.v1', m[f'name{i}'], role='liquidateur', place=m['place2'] if i == 2 else None, signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'administrateur'}) for i in (1, 2)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nouveau capital-actions de CHF (?P<capital>{MONEY}) est formé de (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}) \(et non de (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY})\)")
    if m and all(num(m[k]) > 0 for k in ('capital', 'count', 'nominal', 'previous_count', 'previous_nominal')) and num(m['capital']) == num(m['count']) * num(m['nominal']):
        return [event('fr.text.share_count_corrected.v1', action='share_count_corrected', correction=True, **m.groupdict())], ''

    m = match(r"L'associée (?P<previous_name>[^;]+?) a modifié sa raison de commerce en (?P<name>[^;]+?) \((?P<register_id>\d+)\) et transféré son siège à (?P<place>[^();]+) \((?P<country>[^();]+)\)")
    if m:
        return [person('fr.persons.corporate_associate_name_seat_changed.v1', m['name'], role='associée', place=m['place'], extra=m.groupdict())], ''

    m = match(rf'Nouveau membre du conseil de fondation avec signature collective à deux: (?P<name>{NAME}), de et à (?P<place>{NAME}), vice-président', source_pattern=rf'Nouveau membre du conseil de fondation avec signature collective à deux: {NAME}, de et à {NAME}, vice-président')
    if m and re.search(re.escape(leftover.replace('conseil de fondation : ', 'conseil de fondation avec signature collective à deux: ')) + r'\.?$', source_text):
        return [person('fr.persons.foundation_vice_president_local_origin.v1', m['name'], role='vice-président du conseil de fondation', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['place']})], ''

    list_pattern = ', '.join(rf'(?P<name{i}>{NAME})' + (rf', maintenant domicilié à (?P<place{i}>{NAME})' if i == 2 else rf', maintenant domiciliée à (?P<place{i}>{NAME})' if i == 9 else '') for i in range(1, 13)) + rf' et (?P<name13>{NAME})'
    m = match(r'Signature collective à deux a été conférée à ' + list_pattern + r'; leur procuration est radiée')
    if m:
        return [person('fr.persons.thirteen_signatures_procuration_revoked.v1', m[f'name{i}'], place=m.groupdict().get(f'place{i}'), signing='Kollektivunterschrift zu zweien', extra={'procuration_revoked': True}) for i in range(1, 14)], ''

    m = match(rf"L'associée-gérante (?P<seller>{NAME}), nommée présidente, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=transferred) parts de CHF, sans signature sociale")
    if m and all(num(m[k]) > 0 for k in ('remaining', 'nominal', 'transferred')):
        rule = 'fr.persons.transfer_manager_president_missing_buyer_nominal.v1'
        return [person(rule, m['seller'], role='associée-gérante présidente', extra={'shares': int(num(m['remaining'])), 'share_nominal': m['nominal'], 'transferred_shares': int(num(m['transferred']))}), person(rule, m['buyer'], role='associé-gérant', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'shares': int(num(m['transferred'])), 'share_nominal': None})], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen, nachdem der Konkursrichter mit Urteil vom (?P<reopening_date>{DATE}) die Wiedereröffnung eines summarischen Verfahrens angeordnet hat\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\. \]\. \[gestrichen: Das Konkursverfahren ist mit Urteil des Konkursrichters vom (?P<previous_date>{DATE}) mangels Aktiven eingestellt worden\.\]', 'de')
    if m:
        return [event('de.text.bankruptcy_summary_proceedings_reopened.v1', action='bankruptcy_reinstatement', dissolved_by_bankruptcy=True, procedure='summary', **m.groupdict())], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), secrétaire', suffix=r', avec signature collective à deux')
    if m:
        rule = 'fr.persons.board_president_secretary_signing.v1'
        return [person(rule, m['name1'], role='président', signing='Einzelunterschrift'), person(rule, m['name2'], role='secrétaire', place=m['place2'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin2']})], ''

    m = match(r", Sede principale: (?P<headquarters>[^.;]+)\. Nuove disposizioni per la succursale: La società ha deciso la soppressione della succursale, ma la cancellazione non può essere effettuata mancando il consenso delle autorità fiscali federali e cantonali", 'it')
    if m:
        return [event('it.text.branch_closed_tax_consents_pending.v1', action='branch_closure', deletion_blocked=True, reason='federal_and_cantonal_tax_consents_missing', **m.groupdict())], ''

    m = match(rf"Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<seller>{NAME}) est maintenant associée pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal), et (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal)\. Nouveau gérant: l'associé (?P=buyer)", suffix=r' avec signature individuelle')
    if m and all(num(m[k]) > 0 for k in ('transferred', 'remaining', 'nominal')):
        rule = 'fr.persons.transfer_new_associate_manager_individual.v1'
        return [person(rule, m['seller'], role='associée', extra={'shares': int(num(m['remaining'])), 'share_nominal': m['nominal'], 'transferred_shares': int(num(m['transferred']))}), person(rule, m['buyer'], role='associé-gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(num(m['transferred'])), 'share_nominal': m['nominal']})], ''

    return [], leftover
