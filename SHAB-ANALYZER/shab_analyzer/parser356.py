from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY

PERSON = r'[^,;.]+?'


def extract_parser356_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed residues after all earlier parsers."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed'):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, role=None, signing=None, kind='officer_changed'):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', m['name'], role=role, signing=signing, place=m.groupdict().get('place'), extra={'action': action, **m.groupdict()})

    def number(m, key):
        return Decimal(m[key].replace("'", ''))

    m = match(rf"Création d'un capital-participation de CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>\d+) bons de CHF (?P<nominal>{MONEY}), nominatifs")
    if m and number(m, 'capital') == number(m, 'count') * number(m, 'nominal'):
        return [event('participation_capital_created', m, 'capital_changed')], ''

    m = match(rf'Nouveau liquidateur : (?P<name>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON})')
    if m and re.search(r'Nouveau liquidateur avec signature individuelle: ' + re.escape(m['name'] + ', de ' + m['origin'] + ', à ' + m['place']) + r'\.?$', source_text):
        return [person('new_liquidator_individual_signing', m, 'Liquidator', 'Einzelunterschrift')], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{PERSON}) est membre du conseil de fondation \(et non pas (?P<previous_name>{PERSON})\)")
    if m:
        return [person('foundation_council_name_corrected', m, 'Mitglied des Stiftungsrats')], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat das (?P<court>[^.;]+?) die Nachlassstundung um (?P<duration>zwei Monate) bis am (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('moratorium_extended_by_judgment', m)], ''

    m = match(r'Eingetragene Person gelöscht: (?P<name>[^,;.]+), (?P<previous_signing>Einzelprokura)', 'de')
    if m:
        return [person('registered_procurist_deleted', m, kind='officer_removed')], ''

    m = match('des points non soumis à publication')
    if m and re.search(r'Statuts modifiés le (?P<day>\d{1,2}) septembre (?P<year>\d{4}) des points non soumis à publication\.?$', source_text):
        date = re.search(r'Statuts modifiés le (\d{1,2}) septembre (\d{4})', source_text)
        try:
            datetime(int(date[2]), 9, int(date[1]))
        except ValueError:
            return [], leftover
        return [event('unpublished_statutes_points_changed', m)], ''

    m = match(rf'(?P<transferor>{PERSON}) détient désormais (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>\d+) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), associée désormais pour (?P<recipient_holding>\d+) parts de CHF (?P=nominal)')
    if m and int(m['recipient_holding']) >= int(m['transferred']):
        return [event('shares_transferred_between_existing_associates', m)], ''

    m = match(rf'(?P<transferor>{PERSON}), maintenant à (?P<transferor_place>{PERSON}), cède une de ses (?P<previous>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<name>{PERSON}), maintenant à (?P<place>{PERSON}), nouvel associé et dont la procuration est éteinte, avec une part de CHF (?P=nominal); (?P=transferor) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)')
    if m and int(m['previous']) == int(m['remaining']) + 1 and re.search(re.escape(m['name'] + ', maintenant à ' + m['place']) + r', nouvel associé avec signature individuelle et dont la procuration est éteinte', source_text):
        return [event('single_share_transferred_procuration_terminated', m), person('new_associate_individual_signing_procuration_terminated', m, signing='Einzelunterschrift')], ''

    m = match(rf'(?P<transferor1>{PERSON}), (?P<transferor2>{PERSON}) et (?P<transferor3>{PERSON}) ont cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<name>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}), lequel est en outre nommé gérant Par conséquent, (?P=transferor1), (?P=transferor2) et (?P=transferor3) sont désormais associés pour (?P<remaining_each>\d+) parts de CHF (?P=nominal) chacun')
    if m and re.search(re.escape(m['name'] + ', de ' + m['origin'] + ', à ' + m['place']) + r', lequel est en outre nommé gérant avec signature collective à deux\.', source_text):
        return [event('three_associates_transfer_to_new_manager', m), person('transferee_manager_collective_signing', m, 'Geschäftsführer', 'Kollektivunterschrift zu zweien')], ''

    m = match(r'Die Adresse der a\.a\. Konkursverwaltung lautet: (?P<administrator>[^,]+), (?P<address>[^,]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+)\. \[bisher: Die Adresse der a\.a\. Konkursverwaltung lautet: (?P=administrator), (?P<previous_address>[^,]+), (?P<previous_postal_code>\d{4}) (?P<previous_place>[^.;]+)\.\]', 'de')
    if m:
        return [event('extraordinary_bankruptcy_administrator_address_changed', m)], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Erhöhung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\. \[bisher: Die Gesellschaft hat bei der Gründung vom (?P<foundation_date>{DATE}) eine bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]\. Die Generalversammlung hat mit Beschluss vom (?P=decision_date) genehmigtes Aktienkapital gemäss näherer Umschreibung in den Statuten geschaffen\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P<previous_date>{DATE}) eine Erhöhung und Anpassung des genehmigten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        return [event('conditional_capital_increased_authorized_capital_created', m, 'capital_changed')], ''

    m = match(rf'Aktienkapital neu: CHF (?P<capital>{MONEY}) \[bisher: CHF (?P=capital)\]\. Liberierung Aktienkapital neu: CHF (?P=capital) \[bisher: CHF (?P=capital)\]\. Aktien neu: (?P<count>\d+) Namenaktien zu CHF (?P<nominal>{MONEY}) \[bisher: (?P=count) Namenaktien zu CHF (?P=nominal)\]\. Bei der Kapitalherabsetzung vom (?P<reduction_date>{DATE}) wird der Nennwert der (?P=count) Namenaktien von CHF (?P=nominal) auf CHF (?P<reduced_nominal>0\.00) herabgesetzt\. Gleichzeitig werden bei der Kapitalerhöhung vom (?P<increase_date>{DATE}) (?P=count) voll liberierte Namenaktien zu CHF (?P=nominal) ausgegeben', 'de')
    if m and number(m, 'capital') == number(m, 'count') * number(m, 'nominal'):
        return [event('capital_written_down_and_reissued', m, 'capital_changed')], ''

    return [], leftover
