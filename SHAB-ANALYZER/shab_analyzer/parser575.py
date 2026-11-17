from __future__ import annotations

import re

from .parser55 import _FR_STANDALONE_GROUP_SIGNING
from .parser107 import _FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS
from .parser207 import _FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS
from .parser253 import _person_event

_TRIO = re.compile(
    r'Liquidateurs: les associés gérants (?P<name1>[^,.;\n]+), président, '
    r'(?P<name2>[^,.;\n]+) et (?P<name3>[^,.;\n]+), tous trois '
    r'; les pouvoirs de (?P=name2) '
    r'sont modifiés en ce sens\.?'
)


def extract_parser575_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the evidenced three associate-manager liquidator appointments."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_STANDALONE_GROUP_SIGNING,
        _FR_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS,
        _FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS,
    )):
        return [], text
    match = _TRIO.fullmatch(text.strip())
    if not match:
        return [], text
    names = [match[key].strip() for key in ('name1', 'name2', 'name3')]
    if len(set(names)) != 3:
        return [], text
    # The earlier group-signing rule can remove this phrase from the leftover.
    source_clause = (
        f'Liquidateurs: les associés gérants {match["name1"]}, président, '
        f'{match["name2"]} et {match["name3"]}, tous trois avec signature '
        f'collective à deux; les pouvoirs de {match["name2"]} sont modifiés en ce sens'
    )
    if not source_text.strip().removesuffix('.').endswith(source_clause):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [_person_event(
        *context, 'officer_changed',
        'fr.persons.three_associate_manager_liquidators_joint_signing.v1', name,
        role='associé-gérant président et liquidateur' if index == 0 else 'associé-gérant et liquidateur',
        signing='Kollektivunterschrift zu zweien',
        extra={'action': 'appointed_liquidator'},
    ) for index, name in enumerate(names)], ''
