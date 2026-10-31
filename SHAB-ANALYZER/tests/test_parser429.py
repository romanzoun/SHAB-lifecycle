import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser429 import extract_parser429_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['1b7b4a26a1a30caf7753df049605af2537cb7d79fc45c9e937b3cdd36a7e628b', '71b92a0db1b440ee8485deb391e45e320d0c4f30d620d38960ba3187677fd25a', '780331e9aa56f845ea5285c2025260229ca5416bd6d530ee41d88d294525c9ce', 'a34e59084a4b14c541cf6b122187e1cf4d1162289521cc00485a51d538f876bb', 'bc4d1c9725ab5f84a641b809a426398e50529f1d1ea018b278ff2e7565760444', 'c1a362a11e2afe2846c535270502a59b759750d143ceed3c254b6b9f9aa590c3', 'c3c21942b2ac7f06660b1b54ac6581acee2c0549f0cf2b3ed4743e694cbf020d', 'd6a369f6b43b14f579abe8a630a49de1c81fa9e4d34ee8d2fe076e27b35a34c8', 'eca828a7a5463aaebb9872f27db8e2b736ea4edf9857307db0a5555a7a3205e1', 'efad76dd80e79f3d4094fa3d3dfaab4966c9b20fec35f711e312a003dc705955', 'f1c0acf9bff4c06920532bfc0ea58042b652effcdd4ab52d081bd355ba92aa19', 'f2586a90687cc77b2891f7a4c8e88f8ed44a5e20b9c9d7b9d457720b0ae24830']
COUNTS = [1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser429_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser429_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 445
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
    if index == 11:
        assert (events, rest) == ([], args[0])
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
        if not name.startswith('extract_parser') or name == 'extract_parser429_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name



@pytest.mark.parametrize('index,kind', list(enumerate([
    'capital_changed', 'ownership_changed', 'status_changed', 'capital_changed',
    'capital_changed', 'organization_changed', 'ownership_changed', 'status_changed',
    'officer_changed', 'capital_changed', 'officer_changed', 'organization_changed'])))
def test_payload_semantics(index, kind):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == kind
    p = events[0].payload
    if index in (0, 4, 9):
        assert p['corrected'] is True
    if index == 1:
        assert p['buyer_signing'] == 'ohne Zeichnungsberechtigung'
        assert (p['remaining'], p['count'], p['nominal']) == ('180', '20', '100')
    if index == 2:
        assert p['month'] == 'septembre' and p['dissolved'] is True
    if index == 3:
        assert p['cancelled'] is True
    if index == 5:
        assert p['branch_entries_retained'] is True
        assert p['previous_uid'] != p['recipient_uid']
    if index == 6:
        assert int(p['count']) + int(p['remaining']) == int(p['split_count'])
        assert [e.role for e in events[1:]] == ['associée-gérante présidente', 'associée-gérante']
        assert all(e.signing is None for e in events[1:])
    if index == 7:
        assert p['reinstated'] is True and p['liquidator_facts_retained'] is True
    if index == 8:
        assert events[0].signing == 'ohne Zeichnungsberechtigung'
    if index == 10:
        assert events[0].signing == 'Einzelunterschrift'
        assert p['previous_signing'] == 'Kollektivunterschrift zu zweien'
    if index == 11:
        assert p['company_name'].endswith(' S.A., en liquidation')

@pytest.mark.parametrize('version,text,language', [
    (406, "Selon décision de son assemblée générale du 28 novembre 2020, l'association a prononcé sa dissolution", 'fr'),
    (384, 'Die Gesellschaft wird gemäss Entscheid des Kantonsgerichts Zug vom 22.02.2021 wieder in das Handelsregister eingetragen. [Die in Bezug auf den Liquidator und das Liquidationsdomizil bisher eingetragenen Tatsachen gelten weiterhin.]', 'de'),
    (364, "Rectificatif: l'inscription n° 3893 du 23.02.2021 (FOSC du 26.02.2021, p. 0/1005111383) est rectifiée en ce sens que le capital-actions de CHF 100'000, libéré à concurrence de CHF 100'000, est divisé en 1'000 actions nominatives de CHF 100, (et non divisé en 1'000 actions nominatives de CHF 1'000 comme publié)", 'fr'),
])
def test_related_old_rules_keep_ownership(version, text, language):
    import importlib
    old = getattr(importlib.import_module(f'shab_analyzer.parser{version}'), f'extract_parser{version}_leftovers')
    args = text, language, 'p', '', None, None, None
    events, rest = old(*args)
    assert events and rest == ''
    padded = '  ' + text + '  '
    assert extract(padded, *args[1:]) == ([], padded)


def test_fragment_requires_source_evidence():
    _, _, (args, _) = captured(11)
    assert extract(*args, source_text='Unrelated source.') == ([], args[0])

@pytest.mark.parametrize('index,old,new', [(0, '22 mars', '32 mars'), (2, '28 septembre', '31 septembre')])
def test_invalid_written_dates(index, old, new):
    _, _, (args, kwargs) = captured(index)
    text = args[0].replace(old, new)
    assert extract(text, *args[1:], **kwargs) == ([], text)
