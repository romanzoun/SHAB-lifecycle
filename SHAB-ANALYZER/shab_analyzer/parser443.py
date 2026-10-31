from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, NAME, UID


def extract_parser443_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only complete sample-backed residual clauses."""
    if language != 'fr':
        return [], text
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

    def person(action, name, *, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'fr.persons.{action}.v1', name,
                             role=role, signing=signing, place=place, extra={'action': action, **extra})

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}), signent désormais collectivement à deux, sans autre restriction')
    if m:
        return [person('four_signatories_restrictions_removed', m[f'name{i}'], signing='Kollektivunterschrift zu zweien', signing_restriction='sans autre restriction') for i in range(1, 5)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom exact du trésorier du comité est (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}), comme publié\)")
    if m:
        return [person('committee_treasurer_name_corrected', m['name'], role='trésorier du comité', correction=True, **{k: v for k, v in m.groupdict().items() if k != 'name'})], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\) est rectifiée en ce sens que l'organe de révision est (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\), à (?P<place>{NAME}) et non (?P<previous_auditor>{NAME}) \((?P<previous_auditor_uid>{UID})\)")
    if m:
        return [_event(*context, 'organization_changed', 'fr.text.auditor_identity_corrected_without_notice_page.v1', {'action': 'auditor_corrected', 'correction': True, **m.groupdict()})], ''

    m = match(rf'(?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}) est gérante')
    if m:
        return [person('female_manager_foreign_residence', m['name'], role='gérante', place=m['place'], origin=m['origin'], country=m['country'])], ''
    return [], text
