import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser368 import extract_parser368_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1e36a4a8', 'de.text.associate_previous_details_corrected.v1', 1), ('3a9d3e4d', 'fr.text.participation_capital_created_authorization_deleted.v1', 1), ('3daf9912', 'fr.text.vice_president_name_corrected.v1', 1), ('6b0c71ca', 'fr.text.two_managers_joint_signing_with_manager.v1', 2), ('8cffc69b', 'fr.text.liquidating_foundation_partial_asset_transfer.v1', 1), ('9f121617', 'fr.text.associate_appointed_manager_individual_signing.v1', 1), ('a37a4549', 'fr.text.associate_ancillary_obligations_statutes.v1', 1), ('a9e3033c', 'fr.text.corporate_associate_name_uid_seat_changed.v1', 1), ('b804d142', 'fr.text.bankruptcy_opened_german_text_french_notice.v1', 1), ('cbf9efa0', 'fr.text.three_associates_transfer_unsigned_corporate_recipient.v1', 1), ('f1ce305c', 'fr.text.board_joint_signing_administration_typo.v1', 4), ('f3113a65', 'de.text.audit_exemption_revoked_by_supervisor.v1', 1)]
SUPPLIED_SHA256 = {'1e36a4a8': '1e36a4a88beacb9f99c3f73fbdd7d83fe6268a705525fcf20072157c70bc872a', '3a9d3e4d': '3a9d3e4d48ac3b949b2bb82e5c6ae7c6e97c3e9999ce881cf852a3fb362be6e4', '3daf9912': '3daf9912a186395ddd2dd1a74e7bdb02aaf4d4f1b0bede8f3c7f27b1824a6e66', '6b0c71ca': '6b0c71caedbe1c8e560f02345f0b1ac60021e0673ac89983bf3fc810f44d1859', '8cffc69b': '8cffc69bbc4a0e7c26a6b6cfb24cf05bb8be589f08210248e12660f13e280edc', '9f121617': '9f12161796107b89b84302549ffd18863d73dce06cca5cb3a2a408a964051da6', 'a37a4549': 'a37a45490ae7475749129b302277a1ef6442b862e0eb45ab78f034702d3fc54d', 'a9e3033c': 'a9e3033c2f26f8c1e34a4b48e7d6e41bdf2d600c1f772d025a7988810fac205b', 'b804d142': 'b804d1420f4eceea86217cbb6a95d067a7373bcf606b95693674428e1fed357f', 'cbf9efa0': 'cbf9efa0b1b4b3de27b56bc1d2ebd739eae04e8d4a21a01e528fdcc6ce0fc36b', 'f1ce305c': 'f1ce305cdd21f1c7ee88b2c1f012ce1952df0abe72e0147a948891115a49d5dc', 'f3113a65': 'f3113a65e4bbc35efb976f9d096dcdf044b98dc109ae7e998f817cbf08f7cb66'}

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
        return extract_parser368_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser368_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser368_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 422
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser368_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser368_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser368_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser368_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser368_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['97aa9560', '2d4d020d', '37e0ff28', '831e0472', '1b6eb4b8', 'e34d012c', '6098826f', '6ab95148', '77b6aefd', '15fca0c1', 'a00f3e3d', 'f9481940'])
def test_parser367_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser368_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser368_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser368_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_payload_semantics():
    previous = selected('1e36a4a8')[0]
    assert previous.role is None and previous.signing is None
    assert (previous.payload['previous_count'], previous.payload['previous_nominal'], previous.payload['previous_place']) == ('1', "3'000.00", 'Winterthur')
    capital = selected('3a9d3e4d')[0].payload
    assert (capital['capital'], capital['count'], capital['nominal'], capital['authorization_date']) == ("16'800.10", "168'001", '0.10', '26.07.2017')
    corrected = selected('3daf9912')[0]
    assert corrected.role == 'Vizepräsident'
    assert corrected.payload['name'] != corrected.payload['previous_name']
    managers = selected('6b0c71ca')
    assert [e.payload['place'] for e in managers] == ['Saint-Cergue', 'Lausanne']
    assert all(e.role == 'Geschäftsführer' and e.signing == 'Kollektivunterschrift zu zweien' and e.payload['signing_restriction'] == 'avec un gérant' for e in managers)
    transfer = selected('8cffc69b')[0].payload
    assert (transfer['first_contract_day'], transfer['first_contract_month'], transfer['contract_date'], transfer['decision_date']) == ('18', '05', '08.06.2020', '01.09.2020')
    assert (transfer['assets'], transfer['liabilities'], transfer['recipient_uid'], transfer['consideration']) == ("99'634'083.34", "99'634'082.34", 'CHE-109.587.664', 'aucune')
    manager = selected('9f121617')[0]
    assert manager.role == 'Geschäftsführer' and manager.signing == 'Einzelunterschrift'
    assert selected('a37a4549')[0].payload['details'] == 'statuts'
    assert selected('a9e3033c')[0].payload['uid'] == 'CHE-115.846.035'
    bankruptcy = selected('b804d142')[0].payload
    assert (bankruptcy['decision_date'], bankruptcy['effective_date'], bankruptcy['time']) == ('29.09.2020', '29.09.2020', '14.45')
    shares = selected('cbf9efa0')[0].payload
    assert (shares['count1'], shares['count2'], shares['count3'], shares['recipient_count'], shares['nominal']) == ('40', '80', '80', '200', '100')
    assert shares['recipient_signing'] == 'ohne Zeichnungsberechtigung'
    board = selected('f1ce305c')
    assert len(board) == 4 and all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert board[-1].role is None and board[0].payload['place'] is None
    assert selected('f3113a65')[0].payload['decision_date'] == '29.07.2020'


@pytest.mark.parametrize('time', ['24.00', '14.60'])
def test_invalid_bankruptcy_time_preserved(time):
    _, (args, kwargs) = captured('b804d142')
    changed = args[0].replace('14.45', time)
    assert extract_parser368_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_repeated_corporate_recipient_must_agree():
    _, (args, kwargs) = captured('cbf9efa0')
    changed = args[0].replace('200 parts de CHF 100', '200 parts de CHF 200')
    assert extract_parser368_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_invalid_partial_contract_date_preserved():
    _, (args, kwargs) = captured('8cffc69b')
    changed = args[0].replace('18.05 et', '31.02 et')
    assert extract_parser368_leftovers(changed, *args[1:], **kwargs) == ([], changed)
