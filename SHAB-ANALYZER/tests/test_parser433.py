import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser433 import extract_parser433_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '2653cb47e5ff860be80babf8d1d5db7411c0ecebc8ba782d85d271141bd8e7f4', '295c938772229a233efe0171afbc58b911146ce6c47a3d08aaccd85514ab6e57', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '73545b689d7ef51614ffba434c2912c2020dc486ad51e8776d28aec8002faf1a', '959fd0c28ee1187fdc7d980eca7d9dfb8593cd58c2df9f55308378bfa9248ae4', 'aaa55e0dd961ddc9c520490447cc61c13cbd38dee846b431caa9ea4f3a5b2a66', 'b0b674eafdb8e5894007facc9742c45fb67c7ecc5fce335bd18ebf2e21c33a8b', 'b5510be2d02a811229c03a96e01451ab97006b189cab9f21e99f24f1feec6535', 'b98be3ec262885c619f0f3c252900ecb2b29fab4144abccd83fe38186e98b29a', 'bc206b40fca4f78c01623d6807eaee22caa2be9afdf3eb4340d4c2adf57fa7bb', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 1, 1, 0, 1, 1, 1, 1, 2, 1, 1, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser433_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser433_leftovers', lambda text, *a, **kw: ([], text)):
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
        if not name.startswith('extract_parser') or name == 'extract_parser433_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (3, 55), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert result.leftover_text == args[0]
    assert old_extract(*args) == expected


@pytest.mark.parametrize('index,kind,action,expected', [
    (1, 'assets_transferred', 'sole_proprietor_asset_transfer_balance_receivable', {'assets': "806'620.90", 'liabilities': "233'862.85", 'receivable': "472'758.05", 'count': '100', 'nominal': "1'000.00", 'currency': 'CHF'}),
    (2, 'capital_changed', 'social_shares_split_manager_holdings', {'previous_count': '2', 'count': '200', 'nominal': '100', 'currency': 'CHF'}),
    (4, 'officer_changed', 'sole_female_administrator_corrected', {'nationality': 'italiana', 'corrected': True}),
    (5, 'address_changed', 'liquidation_address_corrected_notice_reference', {'corrected': True, 'scope': 'liquidation', 'notice_reference': '0/100508260'}),
    (6, 'officer_changed', 'female_management_member_appointed_proxy_revoked', {'proxy_revoked': True}),
    (7, 'capital_changed', 'registered_share_transfer_restrictions_removed_plain', {'transfer_restricted': False, 'count': "1'500"}),
    (8, 'officer_changed', 'associate_managers_liquidators_typo', {'previous_role': 'associé gérant'}),
    (9, 'status_changed', 'company_reinstated_summary_bankruptcy_reopened', {'reinstated': True, 'bankruptcy_reopened': True, 'procedure': 'summarisch', 'deletion_date': '02.02.2018', 'decision_date': '25.02.2021'}),
    (10, 'organization_changed', 'previous_head_office_identifier_removed', {'previous_head_office_id': 'CH-550-0177153-6', 'previous': True, 'scope': 'head_office'}),
])
def test_evidenced_semantics(index, kind, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert all(e.event_type == kind and e.payload['action'] == action for e in events)
    assert all(e.rule_id == f'{args[1]}.text.{action}.v1' for e in events)
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index == 4:
        assert events[0].role == 'amministratrice unica' and events[0].signing == 'Einzelunterschrift'
    elif index == 5:
        assert events[0].payload['address'] != events[0].payload['previous_address']
    elif index == 6:
        assert events[0].role == 'membre de la direction' and events[0].signing == 'Kollektivunterschrift zu zweien'
    elif index == 8:
        assert all(e.role == 'liquidateur' and e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert events[0].person_key != events[1].person_key


@pytest.mark.parametrize('index,before,after', [(1, '100 Namenaktien', '0 Namenaktien'), (2, '200 parts', '201 parts'), (7, "1'500", '0')])
def test_inconsistent_or_zero_amounts(index, before, after):
    _, _, (args, kwargs) = captured(index)
    text = args[0].replace(before, after)
    assert text != args[0]
    assert extract(text, *args[1:], **kwargs) == ([], text)
