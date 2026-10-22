from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, NAME

PERSON = r'[^,;.]+?'


def extract_parser371_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events without changing earlier parsers' results."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            # Fragmentary leftovers alone do not establish the original clause.
            source_match = re.search(r'(?:^|\. )' + source_pattern + r'\.$', source_text)
            if not source_match or any(source_match.groupdict().get(key) != value for key, value in m.groupdict().items()):
                return None
            m = source_match
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(r'Organisation neu: \[Streichung der Angaben zur Organisation auf Grund geänderter Eintragungsbestimmungen\.\]', 'de')
    if m:
        return [event('organization_disclosure_removed_register_rules', m)], ''

    m = match('modifiés', source_pattern=rf'Statuts modifiés le (?P<statutes_date>{DATE}) modifiés sur des points non soumis à publication')
    if m:
        return [event('statutes_non_publishable_points_repeated_modified', m)], ''

    m = match(rf"\[con decisione del (?P<decision_date>{DATE}) della (?P<court>[^;\[\]]+?) è stato ordinato il mantenimento dell'iscrizione nel registro di commercio della società\.\] \[radiati: \]", 'it')
    if m:
        return [event('court_order_registration_maintained', m)], ''

    reference = rf"Complément: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est compl"
    m = match(reference, source_pattern=reference + rf'étée en ce sens (?P<previous_name>{PERSON}) se nomme maintenant (?P<name>{PERSON})')
    if m:
        return [person('officer_name_supplemented_notice_reference', m, m['name'])], ''

    m = match(r"Iscrizione d'ufficio ai sensi dell'art\. (?P<article>152 ORC)", 'it')
    if m:
        return [event('official_registration_article_152', m)], ''

    managers = rf'Nouveaux gérants: (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), président et (?P<name2>{PERSON}), de et à (?P<place2>{PERSON}), vice-président, tous deux'
    m = match(managers, source_pattern=managers + r' avec signature individuelle')
    if m:
        return [person('two_new_presiding_managers_individual_signing', m, m[f'name{i}'], m[f'place{i}'], 'Präsident der Geschäftsführung' if i == 1 else 'Vizepräsident der Geschäftsführung', 'Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf"Les administrateurs (?P<name1>{PERSON}), nommé président, et (?P<name2>{PERSON}), jusqu'ici présidente, nommée vice-présidente, ils continuent à signer collectivement à deux")
    if m:
        return [person('administrators_presidency_changed_continued_signing', m, m[f'name{i}'], role='Präsident des Verwaltungsrates' if i == 1 else 'Vizepräsident des Verwaltungsrates', signing='Kollektivunterschrift zu zweien', **({'previous_role': 'Präsident des Verwaltungsrates'} if i == 2 else {})) for i in (1, 2)], ''

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>\d+), TR (?P<entry>\d+) vom (?P<entry_date>{DATE}) und Publikation im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) wurde als letztes SHAB-Zitat irrtümlich SHAB Nr\. (?P<incorrect_notice_number>\d+) vom (?P<incorrect_notice_date>{DATE}) genannt statt korrekt SHAB Nr\. (?P<correct_notice_number>\d+) vom (?P<correct_notice_date>{DATE})\. Das Statutendatum lautet richtig: (?P<statutes_date>{DATE}), nicht (?P<incorrect_statutes_date>{DATE})\. Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<previous_decision_date>{DATE}) eingeführte Bestimmung betreffend bedingter Kaiptalerhöhung gemäss näherer Umschreibung in den Statuten geändert', 'de')
    if m:
        return [event('notice_statutes_corrected_conditional_capital_changed_typo', m)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>[^;]+?) wurde eine COVID-19-Stundung für 3 Monate bis am (?P<end_date>{DATE}) bewilligt', 'de')
    if m:
        if re.fullmatch(NAME, m['court']):
            return [], leftover
        return [event('covid_moratorium_granted_until_date', m, duration_months='3')], ''

    m = match(rf'Signature collective à deux, toutefois pas entre eux, ni avec (?P<excluded_signers>[^;]+?), est conférée à (?P<name1>{PERSON}), à (?P<place1>{PERSON}), et (?P<name2>{PERSON}), à (?P<place2>{PERSON}), tous deux de (?P<origin>{PERSON})')
    if m:
        return [person('two_officers_restricted_joint_signing_shared_origin', m, m[f'name{i}'], m[f'place{i}'], signing='Kollektivunterschrift zu zweien', signing_restriction='pas entre eux, ni avec ' + m['excluded_signers']) for i in (1, 2)], ''

    m = match(rf'(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), (?P<country1>[A-Z]{{3}}) et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>[A-Z]{{3}}), sont membres du conseil de fondation, sans signature')
    if m:
        return [person('two_foundation_members_unsigned_country_codes', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Stiftungsrates', 'ohne Zeichnungsberechtigung') for i in (1, 2)], ''

    m = match(rf"La modifica di sede avviene in seguito all'aggregazione con il nuovo Comune denominato (?P<municipality>{PERSON}) sulla base del Decreto legislativo del (?P<decree_date>{DATE})", 'it')
    if m:
        return [event('seat_changed_municipal_merger_decree', m)], ''

    return [], leftover
