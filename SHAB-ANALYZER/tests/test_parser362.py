import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser362 import extract_parser362_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('055ca238', 'fr.text.two_new_associates.v1', 2), ('104e4b61', 'fr.text.enterprise_erroneous_deletion_reinstated.v1', 1), ('268cf601', 'fr.text.share_transfer_existing_associate_manager.v1', 1), ('31a56c77', 'it.text.corporate_liquidator_modified.v1', 1), ('3c23f86c', 'fr.text.officer_first_given_name_corrected.v1', 1), ('3e22246c', 'fr.text.bankruptcy_appeal_suspensive_effect.v1', 1), ('4277fd71', 'de.text.board_membership_supplement_explained.v1', 1), ('6e972990', 'fr.text.demerger_to_new_company.v1', 1), ('bee03cb4', 'de.text.early_deletion_deferred_tax_consent.v1', 1), ('d9018797', 'fr.text.three_officers_joint_signing.v1', 3), ('e0d1f17e', 'de.text.head_office_identity_capital_changed.v1', 1), ('e56b3a1d', 'de.text.merger_common_shareholder_duplicated_uid_prefix.v1', 1)]
SUPPLIED_SHA256 = {'055ca238': '055ca23846af14550d7958afac7758b5401649c1d30cada1096ba18284ab3999', '104e4b61': '104e4b6155ce8751510f3e6edfca3c43f161310f206ea610134777b979e2656f', '268cf601': '268cf6016c1a7726dfcd483b8c68baced2e7a40338ea08a095807937673ba1da', '31a56c77': '31a56c776e629d86c106d54d65a59077b5cc5db9d41e29f2f079dd26798f07dd', '3c23f86c': '3c23f86cf1e0cfbec2b7b186e83262f1eb8cc9c373ac10c03b74dc3b2d39ecc6', '3e22246c': '3e22246ca8fd861303e6ed02519f1ee0b115739f5b715e7d98131b4199fb50e3', '4277fd71': '4277fd7188832219df8f79dc2fbbf8fdaa991992430d593f0219acde10ec6444', '6e972990': '6e9729909f739fc2c1d0c12a9b29a2f4be2f9328d0a53c5ca2d8851860136195', 'bee03cb4': 'bee03cb4fe11545b2fd5d3eb0b544e25f801d58185fbac5b6aa2b79abe67af33', 'd9018797': 'd9018797c3187ffe64f02ceffac592e18b7b5779ef7b3b89f710ee276a9312b2', 'e0d1f17e': 'e0d1f17ebb50e76787ae0c16cdfc49de09fcdd577d844b224ad668667aa404db', 'e56b3a1d': 'e56b3a1d21b7d5294f8b1e564f1a5ede615f7dbed158e78eac9a0e2cbc575cbd'}

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
        return extract_parser362_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser362_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser362_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 413
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser362_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser362_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser362_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser362_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser362_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['15e29838', '17480287', '205a4cbb', '22136430', '8de191f8', '98ebffb7', 'a8558951', 'bcc56754', 'e15e32b1', 'e1d741ba', 'e9ce4f31', 'ffd9e6d4'])
def test_parser361_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser362_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser362_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert [e.role for e in selected('055ca238')] == ['Gesellschafter'] * 2
    assert all(e.signing is None for e in selected('055ca238'))
    assert selected('104e4b61')[0].payload['notice_id'] == '4035843'
    assert selected('268cf601')[0].payload['remaining'] == '180'
    assert selected('268cf601')[0].payload['transferred'] == '20'
    assert selected('31a56c77')[0].role == 'Liquidatorin'
    assert selected('3c23f86c')[0].payload['given_name'] == 'Mathieu'
    assert selected('3c23f86c')[0].payload['previous_given_name'] == 'Matthieu'
    assert selected('3e22246c')[0].payload['bankruptcy_date'] == '05.10.2020'
    assert selected('4277fd71')[0].role == 'Mitglied des Verwaltungsrates'
    assert selected('4277fd71')[0].signing is None
    assert selected('6e972990')[0].payload['recipient_uid'] == 'CHE-485.626.405'
    assert selected('bee03cb4')[0].payload['confirmation_date'] == '16.03.2020'
    assert [e.signing for e in selected('d9018797')] == ['Kollektivunterschrift zu zweien'] * 3
    assert [e.role for e in selected('d9018797')] == ['Direktorin', None, None]
    assert selected('e0d1f17e')[0].payload['currency'] == 'GBP'
    assert selected('e0d1f17e')[0].payload['capital'] == "158'000'000.00"
    assert selected('e56b3a1d')[0].payload['absorbed_uid'] == 'CHE-109.261.441'
    assert selected('e56b3a1d')[0].payload['assets'] == "1'129'658.54"


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser362_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_inconsistent_share_nominal_preserved():
    _, (args, kwargs) = captured('268cf601')
    changed = args[0].replace('cession de 20 parts de CHF 100', 'cession de 20 parts de CHF 200')
    assert extract_parser362_leftovers(changed, *args[1:], **kwargs) == ([], changed)
