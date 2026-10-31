from __future__ import annotations

import re

from .parser99 import _FR_TWO_BOARD_MEMBERS
from .parser168 import _FR_NEW_EXECUTIVE_COMMITTEE_PRESIDENT
from .parser253 import _person_event
from .parser267 import NAME


def extract_parser452_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only complete, sample-backed officer clauses."""
    if language != 'fr' or any(p.search(text.strip()) for p in (
        _FR_TWO_BOARD_MEMBERS, _FR_NEW_EXECUTIVE_COMMITTEE_PRESIDENT,
    )):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    m = re.fullmatch(rf'(?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), est membre du comité exécutif, sans signature\.?', text.strip())
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.persons.foreign_executive_committee_member_without_signing.v1', m['name'], place=m['place'], role='Mitglied des Exekutivkomitees', signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'country': m['country'], 'action': 'appointed'})], ''

    pattern = rf"(?P<name1>{NAME}), de et à (?P<place1>[^,.;]+?) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil d'administration"
    m = re.fullmatch(pattern + r'\.?', text.strip())
    # The earlier signing extractor removes this suffix. Require its source evidence.
    if m:
        source = re.search(pattern + r', avec signature collective à deux\.?$', source_text)
        if not source or {k: v.strip() for k, v in source.groupdict().items()} != m.groupdict():
            return [], text
        return [_person_event(*context, 'officer_changed', 'fr.persons.two_board_members_no_separator_comma.v1', m[f'name{i}'], place=m[f'place{i}'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'origin': m['place1'] if i == 1 else m['origin2'], 'action': 'appointed'}) for i in (1, 2)], ''
    return [], text
