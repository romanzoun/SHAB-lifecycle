import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser355 import extract_parser355_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('27045d44', 'de.text.covid_moratorium_granted.v1', 1), ('2e063fc5', 'fr.text.shares_distributed_to_two_associates.v1', 4), ('31c7c531', 'de.text.bankruptcy_liquidation_resumed.v1', 1), ('51fd68a9', 'fr.text.definitive_moratorium_extension_ordered.v1', 1), ('6db5b6a1', 'fr.text.civil_status_name_changed.v1', 1), ('a2b69f83', 'fr.text.authorized_participation_capital_clause.v1', 1), ('a3812a5d', 'fr.text.foundation_dissolution_ordered.v1', 3), ('a9a10e1f', 'fr.text.collective_procuration_supplement.v1', 1), ('ad29dd99', 'fr.text.contributed_business_name_corrected.v1', 1), ('c1039cb2', 'de.text.covid_moratorium_extended.v1', 1), ('cdde2cfd', 'fr.text.director_residence_corrected.v1', 1), ('fcc86be0', 'fr.text.capital_reduced_and_simultaneously_increased.v1', 1)]
SUPPLIED_SHA256 = {'27045d44': '27045d444ac2b801571cb183b49911f3fdd91f132d6dcfd259b2c9f8dc380d97', '2e063fc5': '2e063fc5dd9f91e342ab26cf9870258c941fb91d8ae0577615a85e7e3831f93b', '31c7c531': '31c7c5313cdf5f9e64e84c0c7040247e7700182e11b6b85a054de37b732eb896', '51fd68a9': '51fd68a9b73a1a06fa4696e97d0239e79c0c22ff9232a7cb3e5a71702ced40c9', '6db5b6a1': '6db5b6a11813ed53909dd2f9533b0c14868f07becdd60f4b627d73f461b3b863', 'a2b69f83': 'a2b69f8347e6fc686fa6cac86fee5edfe6842d9c52e9ad6eb2d2a43ca8664deb', 'a3812a5d': 'a3812a5de3ba751a4fb8e544a6eda48c43de810dba35834e79f2bf85aa2dbad9', 'a9a10e1f': 'a9a10e1f118479c1dbea83c22e1f0cfb8120eb8732b2bae9bd2dc6159d879ee9', 'ad29dd99': 'ad29dd99df0a90974878fd04c4838e399dc10610641a89e49af7de91fbf2ae74', 'c1039cb2': 'c1039cb2acb59b0f2559477055a12d94ac9e4e50fc500ad07c20046f928aad86', 'cdde2cfd': 'cdde2cfd960b934d9c9a64bcabeacb7e04b7b701a9cd36fe1d1b707d4525241d', 'fcc86be0': 'fcc86be01caf359316cce1f1fc48daa4d6362dd86ff2d50464e37be9382a97aa'}

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
        return extract_parser355_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser355_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser355_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 385
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser355_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser355_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser355_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = SUPPLIED_SHA256
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser355_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser355_leftovers(*args)
    if prefix in ('2e063fc5',):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['1dfc5107', '37417c6c', '5eccf7b9', '7e10493c', '81d123d2', '9cf09657', '9f03ec20', 'a12e823d', 'b08f4ea7', 'b59483ff', 'd33bd6ab', 'f3e48393'])
def test_parser354_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser355_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    assert selected('27045d44')[0].payload['end_date'] == '07.12.2020'
    assert selected('c1039cb2')[0].payload['duration_months'] == '3'
    assert selected('31c7c531')[0].payload['opening_date'] == '19.12.2017'
    assert selected('6db5b6a1')[0].payload['previous_name'] != selected('6db5b6a1')[0].payload['name']
    assert selected('a2b69f83')[0].event_type == 'capital_changed'
    assert all(e.role == 'Liquidator' and e.signing == 'Kollektivunterschrift zu zweien' for e in selected('a3812a5d')[1:])
    assert selected('a9a10e1f')[0].signing == 'Kollektivprokura zu zweien'
    assert 'signing_condition' in selected('a9a10e1f')[0].payload
    assert selected('cdde2cfd')[0].payload['place'] == 'Sévaz'
    assert selected('cdde2cfd')[0].signing == 'Einzelunterschrift'
    assert selected('fcc86be0')[0].payload['reduced'] == "959'000"
    assert selected('2e063fc5')[0].payload['transferred'] == '198'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('2e063fc5')[1:])


@pytest.mark.parametrize('prefix,old,new', [
    ('51fd68a9', '3 septembre', '31 septembre'),
    ('fcc86be0', "959'000", "958'000"),
    ('2e063fc5', 'cédé 198', 'cédé 197'),
])
def test_invalid_dates_and_inconsistent_amounts_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser355_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_transfer_requires_matching_signing_source():
    _, (args, _) = captured('2e063fc5')
    assert extract_parser355_leftovers(*args, source_text='unrelated') == ([], args[0])
