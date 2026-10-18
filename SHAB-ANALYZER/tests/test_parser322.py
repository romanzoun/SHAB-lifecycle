import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser322 import extract_parser322_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('308db91d', 'it.text.common_owner_merger_subordinated_claims.v1', 1),
    ('36fceb37', 'de.text.erroneous_person_mutation_unchanged.v1', 1),
    ('4f6fc83d', 'fr.text.authorized_participation_capital_increase.v1', 1),
    ('5ceafc07', 'de.text.authorized_capital_clause_replaced.v1', 1),
    ('624c412f', 'fr.text.assets_transfer_fund_units_and_claim.v1', 1),
    ('6a2ac180', 'de.text.proprietor_assets_transfer.v1', 1),
    ('828d5d8a', 'fr.text.associates_correction_unsigned_second.v1', 3),
    ('82bb3513', 'it.text.proprietor_bankruptcy_appeal_suspended.v1', 1),
    ('9e29ee21', 'de.text.bracketed_authorized_capital_clause_removed.v1', 1),
    ('b299fa9e', 'de.text.common_owner_merger_equity_and_subordination.v1', 1),
    ('b522080a', 'de.text.partial_assets_transfer_without_consideration.v1', 1),
    ('d6e20ba9', 'fr.text.proprietor_partial_transfer_shares_and_claim.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


@lru_cache(None)
def captured(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser322_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser322_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    result, _ = captured(prefix)
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in result.events if e.rule_id == rule]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 349
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    with patch.object(parser, 'extract_parser322_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert [e for e in result.events if e.rule_id != rule] == baseline.events
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser322_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser322_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2'])
def test_previous_fixtures_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    with patch.object(parser, 'extract_parser322_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert parse_publication_xml(fixture) == baseline
    # Existing payloads can still construct events without any new attributes.
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_invalid_dates_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    dates = set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0]))
    for date in dates:
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser322_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed


def test_payload_semantics_and_missing_optional_attributes():
    assert selected('36fceb37')[0].payload['unchanged'] is True
    assert selected('36fceb37')[0].event_type == 'organization_changed'
    assert selected('4f6fc83d')[0].payload['fully_paid'] is True
    assert selected('5ceafc07')[0].payload['previous_clause_removed'] is True
    assert selected('9e29ee21')[0].payload['previous_clause_removed'] is True
    assert selected('624c412f')[0].payload['no_third_party_liabilities'] is True
    assert selected('624c412f')[0].payload['isin'].startswith('CH')
    assert 'liabilities' not in selected('6a2ac180')[0].payload
    assert selected('b522080a')[0].payload['no_consideration'] is True
    assert selected('82bb3513')[0].payload['suspensive_effect'] is True
    assert selected('b299fa9e')[0].payload['uid_format_valid'] is False
    assert selected('b299fa9e')[0].payload['absorbed_uid'].startswith('ChlE-')
    for prefix in ('308db91d', 'b299fa9e'):
        assert selected(prefix)[0].payload['capital_increase'] is False
        assert selected(prefix)[0].payload['share_allocation'] is False
    people = selected('828d5d8a')[1:]
    assert [e.signing for e in people] == [None, 'ohne Zeichnungsberechtigung']
    assert all(e.role == 'Gesellschafter' and e.payload['shares'] == '100' for e in people)
    assert selected('d6e20ba9')[0].payload['shares'] == '800'
    for prefix, _, _ in CASES:
        for old in selected(prefix):
            assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,old,new', [
    ('4f6fc83d', "1'188'443", "1'188'444"),
    ('82bb3513', '10:00', '25:00'),
    ('b299fa9e', '5. Juni 2020', '31. Juni 2020'),
    ('624c412f', '25 mai 2020', '32 mai 2020'),
    ('828d5d8a', "n'exerce pas", 'exerce'),
])
def test_inconsistent_or_unsupported_terms_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser322_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed
