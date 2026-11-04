from __future__ import annotations

import re

from .parser253 import _person_event

# The foreign-place pair handled by parser372 requires parenthesized countries;
# this grammar deliberately accepts only unqualified places.
_PAIR = (
    r'(?P<name1>[^,.;()]+), du (?P<origin1>[^,.;()]+), à (?P<place1>[^,.;()]+), '
    r'et (?P<name2>[^,.;()]+), de (?P<origin2>[^,.;()]+), à (?P<place2>[^,.;()]+)'
)
_LEFTOVER = re.compile(r'Nouveaux membres du comité : ' + _PAIR + r'\.?')
_SOURCE = re.compile(
    r'(?:^|\. )Nouveaux membres du comité avec signature collective à deux: '
    + _PAIR + r'\.$'
)


def extract_parser481_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete the du/de committee pair only with matching source evidence."""
    if language != 'fr':
        return [], text
    match = _LEFTOVER.fullmatch(text)
    source = _SOURCE.search(source_text)
    if not match or not source or match.groupdict() != source.groupdict():
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.text.two_new_committee_members_du_de.v1', match[f'name{i}'],
        place=match[f'place{i}'], role='Mitglied des Vorstandes',
        signing='Kollektivunterschrift zu zweien',
        extra={'action': 'two_new_committee_members_du_de', 'origin': match[f'origin{i}']},
    ) for i in (1, 2)], ''
