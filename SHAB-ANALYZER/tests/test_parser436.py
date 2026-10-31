import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser436 import extract_parser436_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '28d4d4f606b0b2703ca2f69b986fa4a25ef69a8d8e7f8966e483fd3699e07bfd', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '514a3851ef2705dfa0aa86db688db5b2e46711811baf81a05ae5f0287b40f1e1', '89f297df1b4606b487d96cea0119da147548d2f87ffeb89a193b638546723849', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a460dfcde942dcee7b99406195a914dd73bab5858aac4417f263ff5d95ba824d', 'aa83f09228e534bf3e2a6bee982fc8cdf7af60845aa8522623adc9369a92757c', 'c5ecd4dee383b84c5634b9800595b6de7930c72265659e22cf1356011365b356', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed', 'f7ef1c6312770dbc480d169907e2af7dce88b921069545619e788b9eef3f4081']
COUNTS = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser436_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser436_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 444
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
        if not name.startswith('extract_parser') or name == 'extract_parser436_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (1, 55), (3, 55), (6, 60), (10, 55)])
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


@pytest.mark.parametrize('index,kind,action,expected', [
    (2, 'status_changed', 'liquidation_finished_early_deletion_tax_consent_pending', {'liquidation_completed': True, 'early_deletion_pending': True, 'federal_tax_consent_pending': True}),
    (4, 'organization_changed', 'two_subsidiaries_merger_deficit_subordination_source_uid_typo', {'absorbed_uid_text1': 'CHE-115.1785.531', 'capital_increase': False, 'share_allocation': False}),
    (5, 'status_changed', 'definitive_composition_moratorium_granted_without_commissioner', {'moratorium_type': 'définitif', 'end_date': '31.05.2021'}),
    (7, 'officer_changed', 'associate_manager_role_entry_completed', {'name': 'Ghasemi Faridullah'}),
    (8, 'status_changed', 'bankruptcy_reopened_official_reinstatement', {'reinstated': True, 'bankruptcy_reopened': True}),
    (9, 'officer_changed', 'foundation_treasurer_appointed', {'name': 'Grognuz Clémence'}),
    (11, 'officer_changed', 'corporate_liquidator_appointed_article_821a', {'liquidator_uid': 'CHE-103.435.808', 'legal_basis': '821a CO'}),
])
def test_evidenced_semantics(index, kind, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index == 9:
        assert events[0].role == 'trésorière'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    if index == 7:
        assert events[0].role == 'gérant' and events[0].signing is None
    if index == 11:
        assert events[0].role == 'Liquidator' and events[0].signing is None


def test_signing_requires_original_evidence():
    _, _, (args, kwargs) = captured(9)
    events, rest = extract(*args)
    assert rest == '' and events[0].signing is None
    assert extract(*args, source_text='unrelated')[0][0].signing is None


def test_merger_rejects_inconsistent_amounts():
    _, _, (args, kwargs) = captured(4)
    for before, after in [("28'070.51", "28'070.52"), ("30'591.40", "30'591.41")]:
        text = args[0].replace(before, after)
        assert text != args[0]
        assert extract(text, *args[1:], **kwargs) == ([], text)
