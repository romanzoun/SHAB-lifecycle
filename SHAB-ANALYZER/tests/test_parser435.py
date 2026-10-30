import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser435 import extract_parser435_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '058ada8ddeb316bfba665ee56c5a95cba5b68ce155d816c9ba882156891995d4', '25e24dca776a18d640027fb0bb6a083caefba95d6e9467eaeb11fd96bc274306', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '960a9cc9511332bd8bfb1b3635646f7c607c4afa5d95c665a5453a44ef17e4cc', '9b89264bbaa933645dfba0deec7f2c6cd240bd674ca260f7cbd8087771139fe9', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a43b94b1a19f37b331ea2e9cc97935bcb98add2b26f632100ff6fdc9e543eba9', 'aedcd4bf77165af1ba0604d93fdc2d30107b9870d7591a320bad4518ec40200a', 'b14da067b63b23a3384d6a7b87bb0338a931c8aba792918cd806cf529736a2a7', 'e530905543b1e584437d5a56950e8fa101619e97e1aeed76ee255d6e8f9d53ad', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 1, 1, 0, 3, 3, 0, 1, 1, 2, 2, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser435_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser435_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 436
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
        if not name.startswith('extract_parser') or name == 'extract_parser435_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (3, 55), (6, 60), (11, 55)])
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
    (1, 'status_changed', 'sole_proprietor_bankruptcy_revoked_civil_judge', {'bankruptcy_revoked': True}),
    (2, 'capital_changed', 'participation_certificates_converted_profit_certificates_removed', {'profit_certificates_removed': True, 'deleted_count': '2'}),
    (4, 'ownership_changed', 'associate_share_transfer_managers_individual_signing', {'count': '99', 'previous_count': '200'}),
    (5, 'ownership_changed', 'share_transfer_female_manager_remaining_holdings', {'count': '10', 'remaining': '10'}),
    (7, 'organization_changed', 'enterprise_representation_information_removed_named_person', {'representation_information_removed': True}),
    (8, 'assets_transferred', 'foundation_asset_transfer_receivables_written_dates', {'receivables': "35'999'468.41", 'agreement_month': 'septembre'}),
    (9, 'officer_changed', 'board_president_continues_individual_signing', {'name1': 'Tandetnik Mikaël'}),
    (10, 'officer_changed', 'board_president_retained_correction', {'corrected': True}),
])
def test_evidenced_semantics(index, kind, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index in (4, 9, 10):
        assert events[-1].signing == ('Einzelunterschrift' if index == 4 else None)
    if index == 5:
        assert all(e.signing is None for e in events)


def test_written_dates_and_share_totals_reject_invalid_values():
    for index, before, after in [(8, '9 septembre', '31 septembre'), (5, 'reste titulaire de 10', 'reste titulaire de 11')]:
        _, _, (args, kwargs) = captured(index)
        text = args[0].replace(before, after)
        assert text != args[0]
        assert extract(text, *args[1:], **kwargs) == ([], text)
