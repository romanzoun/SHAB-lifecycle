from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from .parser71 import _FR_FOUNDATION_DISSOLVED_LIQUIDATORS_PAIR
from .parser107 import _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY

_LEGACY = (_FR_FOUNDATION_DISSOLVED_LIQUIDATORS_PAIR,
           _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY)


def extract_parser422_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only complete sample-backed residual variants."""
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

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'\((?P<german_name>[^()\n]+ in Liquidation)\) \((?P<italian_name>[^()\n]+ in liquidazione)\) \((?P<english_name>[^()\n]+ in liquidation)\)\. (?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}) sont nommés liquidateurs')
    if m:
        return [event('liquidation_translations_four_liquidators', m),
                *[person('four_liquidators_appointed', m, m[f'name{i}'], 'liquidateur') for i in range(1, 5)]], ''

    m = match(r'\[bisher: Identifikationsnummer Hauptsitz: (?P<previous_head_office_id>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d) \]\. Bemerkungen zum Hauptsitz neu: \[(?P<reason>Anpassung des Sitzes infolge Namensänderung der Gemeinde)\]', 'de')
    if m:
        return [event('head_office_id_history_municipality_renamed', m)], ''

    m = match(rf"Selon décision de l'(?P<authority>Autorité cantonale de surveillance des fondations et des institutions de prévoyance) du (?P<decision_date>{DATE}), la fondation est dissoute\. Liquidatrices: les membres du conseil (?P<name1>{NAME}) et (?P<name2>{NAME}), lesquelles continuent à signer collectivement à deux")
    if m:
        return [event('foundation_dissolved_two_female_liquidators', m, 'status_changed'),
                *[person('foundation_female_liquidators', m, m[f'name{i}'], 'liquidatrice', 'Kollektivunterschrift zu zweien') for i in (1, 2)]], ''

    m = match(rf"Liquidateurs: l'associé (?P<name1>{NAME}) et le gérant (?P<name2>{NAME}), lesquels continuent à signer individuellement")
    if m:
        return [person('associate_manager_liquidators', m, m[f'name{i}'], 'liquidateur', 'Einzelunterschrift', previous_role=role) for i, role in ((1, 'associé'), (2, 'gérant'))], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la nouvelle gérante se nomme (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('new_manager_name_corrected', m, m['name'], 'gérante', corrected=True)], ''

    m = match(rf'(?P<seller>{NAME}), qui est nommé président, cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant titulaire (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('president_share_transfer_missing_de', m, 'ownership_changed', currency='CHF'),
                person('share_transfer_seller_president', m, m['seller'], 'président'),
                person('share_transfer_new_associate_manager', m, m['buyer'], 'associé-gérant', place=m['place'])], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que signature individuelle a été octroyée à (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('individual_signatory_name_corrected', m, m['name'], signing='Einzelunterschrift', corrected=True)], ''

    m = match(r'Angaben zur Zweigniederlassung neu: Diese Zweigniederlassung wurde irrtümlich ohne Zustimmung der Steuerverwaltungen gelöscht und wird entsprechend hiermit wieder eingetragen\. \[bisher: (?P<previous_annotation>Da der Geschäftsbetrieb der Zweigniederlassung aufgehört hat, wird der auf sie bezügliche Eintrag im Handelsregister gelöscht\.)\]', 'de')
    if m:
        return [event('branch_erroneous_deletion_reinstated_tax_consent', m, 'status_changed', reinstated=True)], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduced_date>{DATE}) eingeführte und mit Beschluss vom (?P<previous_amendment_date>{DATE}) geänderte Bestimmung betreffend bedingter Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert', 'de')
    if m:
        return [event('conditional_capital_clause_amended_history_betreffend', m, 'capital_changed')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), secrétaire, et (?P<name2>{NAME}), des (?P<origin>USA), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), président, lesquels signent individuellement; les pouvoirs de (?P=name1) sont modifiés en ce sens')
    if m:
        return [person('board_secretary_president_individual_signing', m, m['name1'], 'secrétaire', 'Einzelunterschrift'),
                person('board_secretary_president_individual_signing', m, m['name2'], 'président', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat die Konkursrichterin des (?P<court>{NAME}) über die Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, den Konkurs eröffnet; demnach ist die Gesellschaft aufgelöst\. Das Konkursverfahren ist mit Urteil der Konkursrichterin vom (?P<suspension_date>{DATE}) mangels Aktiven eingestellt worden', 'de')
    if m:
        return [event('bankruptcy_opened_suspended_female_judge', m, 'status_changed', dissolved=True, suspended_for_lack_of_assets=True)], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P=count) parts de CHF (?P=nominal), gérante (?P=seller), qui est nommé président, reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_new_manager_president_retained', m, 'ownership_changed', currency='CHF'),
                person('share_transfer_seller_president', m, m['seller'], 'président'),
                person('share_transfer_new_associate_manager', m, m['buyer'], 'associée-gérante', place=m['place'])], ''
    return [], text
