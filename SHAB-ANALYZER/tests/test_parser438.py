import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser438 import extract_parser438_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '0b81c7422f14bd46ab1c57ec547fd69054086181e8d7ec00e2805a6667d9e3a1', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '5aac9954ca40ba32574693a42db5ef16adbed67841c9f3ce320cda458737214e', '5d4f247cd02dc5e7ca20d599bb1a692082e1dad3fef2bc557e8326c1195523dc', '728023fcc1aede49240cfe3401e6e9260971470740bfadd85f370fa56bbdf3bf', '979c0c731543f82667af03e08200256be6ae9b016a80fa124b1a5001e1f14df4', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'b1d9b41557d5b1089df8b45910b497514b18292c600a4c12b76efa19fe1e8b07', 'e5a1dae75db83dd3b18675d95518aa9a4e202b834e849e3f97e91bba7a550282', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 3, 0, 0, 1, 1, 1, 1, 0, 1, 2, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser438_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser438_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 441
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser438_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (2, 55), (3, 55), (8, 60), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*args) == expected


@pytest.mark.parametrize('index,event_type,action,expected', [
    (1, 'officer_changed', 'appointed', {'country': 'CIV', 'origin': "Côte d'Ivoire"}),
    (4, 'organization_changed', 'authorized_and_conditional_capital_amendments_with_history_typo', {'decision_date1': '18.03.2021', 'decision_date2': '22.04.2020', 'introduced_date3': '28.05.2019'}),
    (5, 'publication_corrected', 'original_statutes_date_corrected', {'corrected_date': '16.12.2005', 'previous_date': '16.12.2006'}),
    (6, 'publication_corrected', 'president_name_spelling_corrected', {'name': 'van Leemput Marie-Cécile', 'previous_name': 'van Leempul Marie-Cécile', 'notice_ref': '0/1004890111'}),
    (7, 'organization_changed', 'branch_uid_supplement_registration_requirements', {'branch_uid': 'CHE-351.653.527', 'place': 'Herisau', 'previous_place1': 'St. Gallen', 'previous_place2': 'Herisau'}),
    (9, 'organization_changed', 'share_transfer_restriction_statutory_clause_repealed', {'restriction_repealed': True}),
    (10, 'officer_changed', 'appointed', {'name': 'Landolt Haller Paola', 'place': 'Bourg-en-Lavaux'}),
])
def test_evidenced_semantics(index, event_type, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == event_type
    assert events[0].payload['action'] == action
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index in (1, 10):
        assert all(e.role == 'membre du conseil de fondation' for e in events)
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events)


def test_historical_capital_pattern_retains_ownership():
    from shab_analyzer.parser107 import extract_parser107_leftovers
    text = ('Die Generalversammlung hat mit Beschluss vom 18.03.2021 die '
            'Statutenbestimmung über die bedingte Kapitalerhöhung vom 28.05.2019 '
            'geändert. [bisher: Die Generalversammlung hat mit Beschluss vom '
            '22.04.2020 die Statutenbestimmung über die bedingte Kapitalerhöhung '
            'vom 28.05.2019 geändert.]')
    args = (text, 'de', 'p', '', None, None, None)
    events, rest = extract_parser107_leftovers(*args)
    assert events and not rest.strip(' .')
    assert extract(*args) == ([], text)
