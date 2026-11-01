from __future__ import annotations

import re

from .parser55 import _FR_STANDALONE_GROUP_SIGNING
from .parser99 import _FR_TWO_BOARD_MEMBERS
from .parser235 import _FR_TWO_FOREIGN_BOARD_MEMBERS, _person_event


_FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_LATE = re.compile(
    r"(?P<name1>[^,.;]+), (?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+), "
    r"à (?P<place1>[^,.;]+), (?P<country1>[A-Z]{3}), et "
    r"(?P<name2>[^,.;]+), (?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+), "
    r"à (?P<place2>[^,.;]+), (?P<country2>[A-Z]{3}), avec signature collective "
    r"à deux, sont membres du conseil d['’]administration\.?"
)


_FR_TWO_FOREIGN_MEMBERS_COLLECTIVE = re.compile(
    _FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_LATE.pattern.replace(
        'avec signature collective à deux, ', ''
    )
)


_FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_SOURCE = re.compile(
    _FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_LATE.pattern.replace(
        '(?P<country1>[A-Z]{3}), et ',
        '(?P<country1>[A-Z]{3}), avec signature individuelle, et '
    )
)


def extract_parser454_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle the evidenced pair without changing historical rule ownership."""
    if language != 'fr' or any(p.search(text.strip()) for p in (
        _FR_TWO_BOARD_MEMBERS, _FR_TWO_FOREIGN_BOARD_MEMBERS,
        _FR_STANDALONE_GROUP_SIGNING,
    )):
        return [], text
    match = _FR_TWO_FOREIGN_MEMBERS_COLLECTIVE.fullmatch(text.strip())
    source = _FR_TWO_FOREIGN_MEMBERS_COLLECTIVE_SOURCE.search(source_text)
    if not match or not source or match.groupdict() != {k: v.strip() for k, v in source.groupdict().items()}:
        return [], text
    return [
        _person_event(
            publication_id, published_at, org_uid, plz, canton,
            'officer_changed', 'fr.persons.two_foreign_members_mixed_signing.v1',
            match[f'name{i}'], place=match[f'place{i}'], role='administrateur',
            signing=('Einzelunterschrift' if i == 1 else 'Kollektivunterschrift zu zweien'),
            extra={'action': 'appointed', 'origin': match[f'origin{i}'].strip(),
                   'country': match[f'country{i}'], 'signing_authority': None},
        ) for i in (1, 2)
    ], ''
