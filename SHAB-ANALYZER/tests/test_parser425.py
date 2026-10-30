import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser425 import extract_parser425_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['0ac43beb3ce35f48b399e925a1ed45345b75de530d3dc5d947adf84e10655f4e', '134fe0322557f9417879acc585646c2db2725b77657e235567941892ca648801', '1a4d1c28672af4b9104085b3af90b6988e8879a7badcb3d0fb5d7834c8f69268', '32811b979ad5a3e97e24fc46cb5f75028ff0c61067de2a60533d5577d728e8b2', '84c88e449aa94071c4a7eeb1a9ece1a8ef8f9c1ae61319b7ee7e2ba87896e873', '9378f8ee86fb988dfeea7c09594565ee6d431758a38f55f6627e19db6667779f', 'a113d4dffc340d8d503183a9ffbeb72f087a218b4fdf683317bfa52e35320a48', 'a33d00f54e700c6a5ee5922c01497df7cc47014669b7c1d96fb8d786417089b5', 'a349cdd8fceeae625ad5b8660a5fb33f01c34dd5994b9976ff57ddcecaf9a2b2', 'a79e061d2bdbf479bea0be540b919438ac30692d2af26e07c22e60f534461ada', 'c832b5eab446176cf955f35fcf20b471ee681ba86ff558a8acdd4dcb7eb0849f', 'dd596723e50fb0e4d2c6b16fbbd64920dfdb40805e0fecfb6d1276dd7aea1471']
COUNTS = [1, 1, 3, 1, 2, 1, 1, 1, 2, 3, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser425_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser425_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 436
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    if index in (2, 3, 8):
        assert events == [] and rest == args[0]
    else:
        assert len(events) == COUNTS[index] and rest == ''



def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None




@pytest.mark.parametrize('index', range(12))
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser425_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name






EXPECTED = [
    ('officer_changed', 'administrator_elected_continued_collective_signing'),
    ('address_changed', 'seat_municipality_renamed'),
    ('ownership_changed', 'share_transfer_associate_manager_president_pair'),
    ('organization_changed', 'deleted_historical_contribution_partnership_detail'),
    ('officer_changed', 'board_vice_president_corrected_notice'),
    ('officer_changed', 'procuration_residence_corrected_notice'),
    ('officer_changed', 'president_identity_corrected_notice'),
    ('status_changed', 'bankruptcy_closed_court_after_date'),
    ('officer_changed', 'new_managers_second_foreign_state'),
    ('officer_changed', 'three_council_members_unsigned'),
    ('organization_changed', 'three_branch_mentions_removed_legacy_ids'),
    ('organization_changed', 'branch_head_office_merger_continuation'),
]

@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert (events[0].event_type, events[0].payload['action']) == EXPECTED[index]
    if index == 2:
        assert events[0].payload['count'] == '100'
        assert [e.role for e in events[1:]] == ['gérant et président', 'gérant']
        assert all(e.signing == 'Einzelunterschrift' for e in events[1:])
    if index == 3:
        assert events[0].payload['historical'] is True
        assert events[0].payload['deleted'] is True
    if index == 8:
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
    if index == 9:
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events)
    if index == 11:
        assert events[0].payload['continues'] is True
        assert events[0].payload['head_office_uid'] != events[0].payload['previous_uid']

@pytest.mark.parametrize('index', [2, 3, 8])
def test_wrong_source_preserves_input(index):
    _, _, (args, kwargs) = captured(index)
    assert extract(*args, source_text='Unrelated source.') == ([], args[0])

@pytest.mark.parametrize('text,version', [
    ("Radiation de la mention de l'existence d'une succursale à Lausanne", 137),
    ('Le directeur Test Paul, maintenant à Lausanne, est élu administrateur et continue à signer collectivement à deux', 364),
])
def test_old_rule_ownership(text, version):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    events, rest = old(text, 'fr', 'p', '', None, None, None)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, 'fr', 'p', '', None, None, None) == ([], padded)
