from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from . import parser113, parser191, parser228, parser252, parser52, parser80, parser116, parser121, parser200, parser202, parser236, parser248, parser253, parser265, parser374, parser387

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
# Keep the earlier compiled expressions as the ownership boundary, even in isolation.
_LEGACY = tuple(p for module in (parser113, parser191, parser228, parser252, parser52, parser80, parser116, parser121, parser200, parser202, parser236, parser248, parser253, parser265, parser374, parser387) for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser388_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete, bounded variants documented by the 388 fixture corpus."""
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
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, place=extra.get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Nouvelle raison sociale du réviseur et nouveau siège: (?P<name>{NAME}) \((?P<uid>{UID})\), à (?P<place>{NAME})')
    if m:
        return [event('auditor_name_and_seat_changed', m)], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), dont la procuration est éteinte, qui est élu gérant désormais titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        number = lambda key: int(m[key].replace("'", ''))
        if number('count') > 0 and number('before') == number('count') + number('remaining') and number('buyer_count') >= number('count'):
            return [event('share_transfer_proxy_revoked_manager_elected', m, currency='CHF'), person('recipient_proxy_revoked', m, m['buyer'], 'Prokurist', None, kind='officer_removed'), person('recipient_manager_elected', m, m['buyer'], 'gérant', None)], ''
        return [], text

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est corrigée en ce sens que (?P<name>{NAME}) signe en réalité collectivement à deux \(et non pas collectivement à deux, sauf avec (?P<previous_exclusions>[^()]+)\)")
    if m:
        return [person('collective_signing_exclusions_corrected', m, m['name'], None, 'Kollektivunterschrift zu zweien', kind='publication_corrected')], ''

    m = match(rf'Gelöschte Person: (?P<name>{NAME}) \((?P<registry_id>CH-\d{{3}}-\d{{7}}-\d)\), Revisionsstelle', 'fr')
    if m:
        return [person('auditor_removed_legacy_registry_id', m, m['name'], 'Revisionsstelle', None, kind='officer_removed')], ''

    m = match(rf"(?P<removed>{NAME}), inscrit sans signature; n'est plus membre du comité\. Nouveaux membres du comité sans signature: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME})")
    if m:
        return [person('committee_unsigned_member_removed', m, m['removed'], 'membre du comité', 'ohne Zeichnungsberechtigung', kind='officer_removed')] + [person('committee_unsigned_member_added', m, m[f'name{i}'], 'membre du comité', 'ohne Zeichnungsberechtigung', kind='officer_changed', place=m[f'place{i}']) for i in range(1, 4)], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<cash>{MONEY}) und (?P<claims>{MONEY}) Ansprüche an der Gruppe (?P<group>{NAME}) der (?P=recipient) in der Höhe von je CHF (?P<claim_value>{MONEY}) aufgrund des per (?P<valuation_date>{DATE}) festgelegten Net Asset Value des Anlagevermögens der Anlagegruppe (?P=group) zuzüglich des Verwässerungsschutzes von CHF (?P<dilution_protection>{MONEY})', 'de')
    if m:
        return [event('foundation_transfer_cash_and_investment_claims', m, currency='CHF')], ''

    m = match(rf'(?P<previous_name>{NAME}), qui se nomme maintenant (?P<name>{NAME}), est désormais à (?P<place>{NAME})')
    if m:
        return [person('person_name_and_residence_changed', m, m['name'], None, None, place=m['place'])], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, et le directeur (?P<name2>{NAME}), lesquels signent individuellement, les pouvoirs de (?P=name2) sont modifiés en ce sens')
    if m:
        return [person('administrator_president_individual_signing', m, m['name1'], 'président', 'Einzelunterschrift'), person('director_individual_signing_changed', m, m['name2'], 'directeur', 'Einzelunterschrift')], ''

    m = match(rf"L'associé (?P<seller>{NAME}), maintenant domicilié à (?P<seller_place>{NAME}), (?P<seller_country>[A-Z]{{3}}), est désormais titulaire de (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), suite à la cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=count) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_foreign_residences', m, currency='CHF'), person('associate_residence_changed', m, m['seller'], 'associé', None, place=m['seller_place']), person('foreign_associate_added', m, m['buyer'], 'associé', None, kind='officer_changed', place=m['place'])], ''

    m = match(rf'\[bisher: (?P<place>{NAME}) \((?P<previous_registry_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]\. \[Anpassung der UID der ZN (?P=place) aufgrund geänderter Eintragungspraxis\]', 'de')
    if m:
        return [event('branch_uid_registration_practice_adjustment', m)], ''

    m = match(rf'La fondation est dissoute par décision de son autorité de surveillance du (?P<decision_date>{DATE})\. Liquidateurs: (?P<name1>{NAME}), présidente, et (?P<name2>{NAME}), secrétaire, membres du conseil de fondation, lesquels continuent de signer individuellement')
    if m:
        return [event('foundation_dissolved_supervisory_authority', m, 'status_changed')] + [person('foundation_council_liquidator_continued_signing', m, m[f'name{i}'], role, 'Einzelunterschrift', liquidator=True) for i, role in ((1, 'présidente'), (2, 'secrétaire'))], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>Dott\. jur\. {NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}) \((?P<country>[A-Z]{{2}})\), presidente del consiglio, con firma individuale', 'it')
    if m:
        return [person('council_president_person_corrected', m, m['surname'] + ', ' + m['given_names'], 'presidente del consiglio', 'Einzelunterschrift', kind='publication_corrected', place=m['place'])], ''
    return [], text
