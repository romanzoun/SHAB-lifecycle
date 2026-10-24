import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser356 import extract_parser356_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2fc056e7', 'de.text.conditional_capital_increased_authorized_capital_created.v1', 1), ('41c0312e', 'fr.text.participation_capital_created.v1', 1), ('737a2075', 'fr.text.new_liquidator_individual_signing.v1', 1), ('7fd4abe3', 'fr.text.three_associates_transfer_to_new_manager.v1', 2), ('8029e9e8', 'fr.text.foundation_council_name_corrected.v1', 1), ('803e00f4', 'de.text.moratorium_extended_by_judgment.v1', 1), ('94e042ba', 'de.text.extraordinary_bankruptcy_administrator_address_changed.v1', 1), ('98e2725d', 'de.text.capital_written_down_and_reissued.v1', 1), ('9dd4882c', 'fr.text.shares_transferred_between_existing_associates.v1', 1), ('bb4d94f4', 'fr.text.single_share_transferred_procuration_terminated.v1', 2), ('c1a93404', 'fr.text.unpublished_statutes_points_changed.v1', 1), ('cc156f75', 'de.text.registered_procurist_deleted.v1', 1)]
SUPPLIED_SHA256 = {'2fc056e7': '2fc056e7c20494624e7229e85f929034ae54cb001aa70f4397711a1fdc349139', '41c0312e': '41c0312e959026f2688eb86c35dc6a57f5db95f498153a5e106a1c620fc1ae7c', '737a2075': '737a20755a8c6567b7caaa7723362d6edfccdbded42b8053bbd2e474ba50b6eb', '7fd4abe3': '7fd4abe3c00be9ac764c142bff3b8e79bf4fef88c5ace26ed2d5d28badf58eb7', '8029e9e8': '8029e9e885e7ea904fb78f305f551cee5f040e6fd024951e563857e5440c80ed', '803e00f4': '803e00f43a6fa18bc81cef8bd614080b041d8746125569ae260875dfca9ca82a', '94e042ba': '94e042ba8b62dcee8dbb3777037f563155202ec6cf68a08fcde3522c9eda4e49', '98e2725d': '98e2725deb9603cd2cf566df69747d32be3eff4f163cff8ade63673bca261260', '9dd4882c': '9dd4882c2a9d5ef607dd67386d46ecb7599e7db7dd41166abd1d605e6aaf356f', 'bb4d94f4': 'bb4d94f4c3019bf9042ba32810b302c0137213afb459fd6bae459551d01fd0c2', 'c1a93404': 'c1a93404018943cb18059ec00cdb7ae5c8d0bc019f53251f2b0405e7fdfe27af', 'cc156f75': 'cc156f75537df3b0c25ba81906f37afac9d6a720ba85333ffc4be09ec93418e9'}

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
        return extract_parser356_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser356_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser356_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 393
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser356_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser356_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser356_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser356_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser356_leftovers(*args)
    if prefix in ('737a2075', '7fd4abe3', 'bb4d94f4', 'c1a93404'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['27045d44', '2e063fc5', '31c7c531', '51fd68a9', '6db5b6a1', 'a2b69f83', 'a3812a5d', 'a9a10e1f', 'ad29dd99', 'c1039cb2', 'cdde2cfd', 'fcc86be0'])
def test_parser355_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser356_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,old,new', [
    ('41c0312e', "50'000", "49'000"),
    ('98e2725d', "120'000.00", "119'000.00"),
    ('bb4d94f4', '19 parts', '18 parts'),
    ('9dd4882c', '83 parts', '10 parts'),
])
def test_inconsistent_amounts_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser356_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['737a2075', '7fd4abe3', 'bb4d94f4', 'c1a93404'])
def test_source_required(prefix):
    _, (args, _) = captured(prefix)
    assert extract_parser356_leftovers(*args, source_text='unrelated') == ([], args[0])


def test_payload_semantics():
    assert selected('737a2075')[0].role == 'Liquidator'
    assert selected('737a2075')[0].signing == 'Einzelunterschrift'
    assert selected('7fd4abe3')[1].signing == 'Kollektivunterschrift zu zweien'
    assert selected('8029e9e8')[0].payload['name'] != selected('8029e9e8')[0].payload['previous_name']
    assert selected('803e00f4')[0].payload['end_date'] == '16.11.2020'
    assert selected('94e042ba')[0].payload['postal_code'] == '8703'
    assert selected('98e2725d')[0].payload['reduced_nominal'] == '0.00'
    assert selected('9dd4882c')[0].payload['recipient_holding'] == '83'
    assert selected('bb4d94f4')[1].signing == 'Einzelunterschrift'
    assert selected('cc156f75')[0].event_type == 'officer_removed'
    assert selected('cc156f75')[0].payload['previous_signing'] == 'Einzelprokura'


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser356_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('prefix', ['737a2075', '7fd4abe3', 'bb4d94f4'])
def test_signing_must_be_supported_by_source(prefix):
    _, (args, kwargs) = captured(prefix)
    source = kwargs['source_text']
    changed = source.replace('signature individuelle', 'signature collective à trois').replace('signature collective à deux', 'signature collective à trois')
    assert changed != source
    assert extract_parser356_leftovers(*args, source_text=changed) == ([], args[0])


def test_invalid_statutes_source_date_preserved():
    _, (args, kwargs) = captured('c1a93404')
    changed = kwargs['source_text'].replace('21 septembre', '31 septembre')
    assert changed != kwargs['source_text']
    assert extract_parser356_leftovers(*args, source_text=changed) == ([], args[0])
