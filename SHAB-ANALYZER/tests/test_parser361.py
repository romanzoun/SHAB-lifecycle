import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser361 import extract_parser361_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('15e29838', 'fr.text.definitive_moratorium_extended_written_dates.v1', 1), ('17480287', 'de.text.share_cancellation_repayment_deed.v1', 1), ('205a4cbb', 'fr.text.share_transfer_five_recipients.v1', 1), ('22136430', 'it.text.ordinary_share_capital_increase_stated.v1', 1), ('8de191f8', 'fr.text.board_president_vice_president_individual_signing.v1', 2), ('98ebffb7', 'de.text.business_asset_transfer_inventory.v1', 1), ('a8558951', 'fr.text.two_procurists_usage_names.v1', 2), ('bcc56754', 'fr.text.registered_share_classes_voting_privilege.v1', 1), ('e15e32b1', 'fr.text.authorized_conditional_participation_capital_clauses.v1', 1), ('e1d741ba', 'fr.text.bankruptcy_procedure_suspensive_effect.v1', 1), ('e9ce4f31', 'fr.text.family_foundation_supervision_auditor_exemption.v1', 1), ('ffd9e6d4', 'fr.text.executive_committee_member_without_signing.v1', 1)]
SUPPLIED_SHA256 = {'15e29838': '15e298380fe3715c662ba3606485c6ef920ce045c448820cc5382fb60e4b7fc3', '17480287': '174802877845da6c9b2f07630598687fc643d52dc6f51c8afce46ce0bd4a65e1', '205a4cbb': '205a4cbb95f4f531b0a0b75b8fff4d742eb94950b7837f8a808d67ab0b009bf0', '22136430': '221364300e33c45ab17ef945ef4b88ccfd1134b00f7f0867b87fd4cd881684a7', '8de191f8': '8de191f883e0d32fa77fadab5e9cf03039cd89a78e02588e4ec3c4105a22192b', '98ebffb7': '98ebffb786a3e43c3327233dde7de4c04b1ccf220f06cfed7ba32f51d67ed3e3', 'a8558951': 'a85589511961c1aee91905d33113d6955c662f750bce618fc8d02c66c871de8e', 'bcc56754': 'bcc567547bda6899026fbc0ded8d32798b7e03da7a9ce415cd3661389cfe5b8d', 'e15e32b1': 'e15e32b1f810ea5cc1c7885d11f6c6d37fc43f97ed0d45616e7edbd4fd60e1b8', 'e1d741ba': 'e1d741bae2ab399ea031b0d891b5d7943bcbf2083aeaef8327fb35ffd0ab6dd6', 'e9ce4f31': 'e9ce4f319c8b9f1f5b5e3b240f40f98cbf712ddb276ae2ac5518276f360d30be', 'ffd9e6d4': 'ffd9e6d4f72f953263a26474cb4841ac0b73a6bef01a1b9379420364a658a367'}

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
        return extract_parser361_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser361_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser361_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 364
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser361_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser361_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser361_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser361_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser361_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['26b61e10', '395a050f', '3ce26082', '565e7045', '6a4a5e9b', '799d3293', '843c84b0', '979b245c', 'bbd12670', 'd9ab9629', 'eed5c760', 'f7fe65f9'])
def test_parser360_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser361_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser361_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert selected('17480287')[0].payload['count'] == "31'900"
    assert selected('205a4cbb')[0].payload['remaining'] == '1'
    assert [e.signing for e in selected('8de191f8')] == ['Einzelunterschrift'] * 2
    assert selected('98ebffb7')[0].payload['consideration'] == '1.00'
    assert [e.signing for e in selected('a8558951')] == ['Kollektivprokura zu zweien'] * 2
    assert selected('bcc56754')[0].payload['class2'] == 'B'
    assert selected('e15e32b1')[0].payload['participation_date'] == '8 octobre 2020'
    assert selected('ffd9e6d4')[0].signing == 'ohne Zeichnungsberechtigung'


@pytest.mark.parametrize('prefix,key', [('15e29838', '24 septembre 2020'), ('e1d741ba', '21 octobre 2020')])
def test_invalid_written_dates(prefix, key):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(key, '31 février 2020')
    assert extract_parser361_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser361_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())


def test_inconsistent_share_allocation_preserved():
    _, (args, kwargs) = captured('205a4cbb')
    changed = args[0].replace('cède 299', 'cède 298')
    assert extract_parser361_leftovers(changed, *args[1:], **kwargs) == ([], changed)
