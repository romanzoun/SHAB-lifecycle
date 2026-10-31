from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, COUNT, DATE


def extract_parser444_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete, sample-backed clauses without consuming other residue."""
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    if language == 'de':
        m = match(r'Zweigniederlassung neu: (?P<place>[^(),.;]+) \((?P<branch_canton>[A-Z]{2})\)')
        if m:
            return [_event(*context, 'branch_changed', 'de.text.branch_added_canton_without_uid.v1', {'action': 'added', **m.groupdict()})], ''
    if language != 'fr':
        return [], text

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que tous les membres du conseil de fondation signent individuellement et non collectivement à deux")
    if m:
        return [_event(*context, 'organization_changed', 'fr.text.foundation_all_members_signing_corrected.v1', {'action': 'signing_corrected', 'correction': True, 'scope': 'tous les membres du conseil de fondation', 'signing': 'Einzelunterschrift', 'previous_signing': 'Kollektivunterschrift zu zweien', **m.groupdict()})], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) résulte de l'obligation de publier le but dans son intégralité et non pas d'une modification matérielle du but social")
    if m:
        return [_event(*context, 'organization_changed', 'fr.text.purpose_full_publication_clarified.v1', {'action': 'purpose_publication_clarified', 'material_purpose_change': False, **m.groupdict()})], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici (?P<previous_role1>vice-président et caissier), et (?P<name2>{NAME}), jusqu'ici (?P<previous_role2>secrétaire), nommés coprésidents, continuent de signer collectivement à deux")
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.persons.two_copresidents_signing_continued.v1', m[f'name{i}'], role='coprésident', signing='Kollektivunterschrift zu zweien', extra={'action': 'role_changed', 'previous_role': m[f'previous_role{i}']}) for i in (1, 2)], ''
    return [], text
