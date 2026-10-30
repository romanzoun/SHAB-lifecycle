import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser354 import extract_parser354_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1dfc5107', 'fr.text.sole_director_continued_individual_signing.v1', 1), ('37417c6c', 'it.text.ordinary_composition_confirmed_commissioner_execution.v1', 1), ('5eccf7b9', 'fr.text.ancillary_obligations_removal_supplement.v1', 1), ('7e10493c', 'fr.text.head_office_collective_procuration_corrected.v1', 1), ('81d123d2', 'de.text.provisional_moratorium_commissioner_appointed.v1', 1), ('9cf09657', 'fr.text.shares_transferred_remaining_holding.v1', 2), ('9f03ec20', 'fr.text.bankruptcy_suspensive_effect_ordered.v1', 1), ('a12e823d', 'fr.text.officer_residence_updated.v1', 2), ('b08f4ea7', 'fr.text.corporate_shares_transferred_remaining_holding.v1', 1), ('b59483ff', 'de.text.definitive_moratorium_extended.v1', 1), ('d33bd6ab', 'fr.text.given_name_correction_entry_reference.v1', 1), ('f3e48393', 'fr.text.committee_members_without_signing_appointed.v1', 2)]
SUPPLIED_SHA256 = {'1dfc5107': '1dfc510777b095953dfd8c2e8d628d1e40baf55051cc27a159709181c4f7f36a', '37417c6c': '37417c6c63d4b218905ef6f14dcab6f22446ade6f38678a941bfd64fc5279689', '5eccf7b9': '5eccf7b92c6e215aa5a85775bf915aa3b7a2eb0eb4ffb64c45fde2af63db0c3e', '7e10493c': '7e10493c0ea7e5b4c959960c8d7b2dea26c5aed3182c802cf265582026f67968', '81d123d2': '81d123d25addece2468e98437c93c415e290b8c10eb639b9a22e79c712c17709', '9cf09657': '9cf096579f6c19ca8dad9aff73146c3ca4b156af46e541442bde5ef1fda44a0e', '9f03ec20': '9f03ec20e4816f1b6822236c429ee7fd53b913327a32d5d5c637ce806fc0194f', 'a12e823d': 'a12e823df263f92a63fe3bf3c6a2c5cec87e193412e60a50a5e62a3dac999d84', 'b08f4ea7': 'b08f4ea7bbe2c4f3195d54ee7784f57c80c0e2c96c4f7c3d6c02e96f1ef97878', 'b59483ff': 'b59483ff95adf5988f2d24fd2f4e2a83cfaa035bc6acda200e2fa78f00b03865', 'd33bd6ab': 'd33bd6abf4c8f8a8f2bab3dbc095b8da35026516d598a2cb1dec8298554f4f71', 'f3e48393': 'f3e483935b9af50a93d77dff974a0c357e1c05d7eefc70713b92161724bc4602'}

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
        return extract_parser354_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser354_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser354_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 437
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser354_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser354_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser354_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser354_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser354_leftovers(*args)
    if prefix in ('9cf09657', 'd33bd6ab'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e



@pytest.mark.parametrize('prefix', ['0863601c', '127b7edf', '13345d7d', '1d2d21a9', '390c063f', '508e1ca0', '5a66d788', '5dab163c', '6f8bcc41', '7dd23e4e', '990046a6', 'edea6f5d'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser354_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    assert selected('1dfc5107')[0].payload['sole_director'] is True
    assert selected('1dfc5107')[0].signing == 'Einzelunterschrift'
    assert selected('7e10493c')[0].signing == 'Kollektivprokura zu zweien'
    assert selected('7e10493c')[0].payload['signing_scope'] == 'établissement principal'
    assert selected('81d123d2')[0].payload['end_date'] == '14.11.2020'
    assert selected('9cf09657')[0].payload['remaining'] == '160'
    assert selected('9cf09657')[1].signing == 'Einzelunterschrift'
    assert selected('a12e823d')[0].payload['place'] == 'Archamps'
    assert selected('a12e823d')[1].payload['origin2'] == 'Baden'
    assert selected('b08f4ea7')[0].payload['remaining'] == '4'
    assert selected('b59483ff')[0].payload['duration_months'] == '14'
    assert selected('d33bd6ab')[0].payload['entry'] == '4307'
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('f3e48393'))


@pytest.mark.parametrize('prefix', ['9cf09657', 'd33bd6ab'])
def test_missing_or_unrelated_source_preserves_residue(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser354_leftovers(*args, source_text='Unrelated source') == ([], args[0])
    assert extract_parser354_leftovers(*args, source_text=kwargs['source_text'] + ' UNKNOWN') == ([], args[0])

@pytest.mark.parametrize('prefix', ['0e514673', '34036b54', '50a1514a', '68337e64', '6ad145fa', '7ffdba77', '8d39d97c', 'ac348d22', 'af6307eb', 'bcf584d0', 'dc62f30b', 'fd9bcd5e'])
def test_parser353_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser354_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


@pytest.mark.parametrize('prefix,old,new', [
    ('9f03ec20', '28 août', '32 août'),
    ('b59483ff', '11. November', '31. November'),
    ('b08f4ea7', 'reste titulaire de 4', 'reste titulaire de 5'),
])
def test_invalid_dates_and_inconsistent_holdings_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser354_leftovers(changed, *args[1:], **kwargs) == ([], changed)
