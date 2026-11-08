from __future__ import annotations

import re

from .parser253 import _event


_ANNOTATION = re.compile(
    r'\[bisher: (?P<previous_place>[^\[\]\n]+)\] \[amtliche Gemeindeumbenennung\]'
)
_SOURCE = re.compile(
    r'Zweigniederlassung neu: (?P<place>[^()\[\];\n]+) '
    r'\((?P<branch_uid>CHE-\d{3}\.\d{3}\.\d{3})\) '
    r'(?P<annotation>\[bisher: [^\[\]\n]+\] \[amtliche Gemeindeumbenennung\])\.?$'
)


def extract_parser501_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read only the annotation left after the existing branch rule.

    A complete branch clause belongs to the historical rules. Its event and
    payload remain intact; this separate event records the official renaming.
    """
    if language != 'de':
        return [], text
    annotation = _ANNOTATION.fullmatch(text.strip().rstrip('.'))
    source = _SOURCE.search(source_text.strip())
    if not annotation or not source or source['annotation'] != annotation[0]:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'branch_changed', 'de.text.branch_municipality_renamed_annotation.v1',
        {'action': 'municipality_renamed', 'previous_place': annotation['previous_place'],
         'place': source['place'].strip(), 'branch_uid': source['branch_uid'],
         'official_change': True},
    )], ''
