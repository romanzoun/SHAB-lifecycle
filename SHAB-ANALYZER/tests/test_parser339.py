import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser339 import extract_parser339_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('05170f05', 'fr.text.authorized_capital_clause_removed.v1', 1), ('0534e4d1', 'fr.text.administrators_appointed_liquidators.v1', 3), ('17abb90d', 'de.text.merger_recipient_uid_corrected.v1', 1), ('1aca3e0c', 'de.text.asset_transfer_shares_and_credit.v1', 1), ('44a3c09b', 'it.text.surname_corrected_collective_procuration.v1', 1), ('6f482002', 'de.text.audit_exemption_revoked.v1', 1), ('90fdb042', 'fr.text.liquidation_name_translations.v1', 2), ('9971fec7', 'de.text.company_reinstated_for_liquidation.v1', 1), ('afa64fa2', 'fr.text.committee_treasurer_collective_signing.v1', 1), ('b0cc538a', 'de.text.asset_transfer_cash_consideration.v1', 1), ('cad77ea9', 'fr.text.registered_share_preference_changed.v1', 1), ('cb42b642', 'de.text.asset_transfer_investment_claims.v1', 1)]
SUPPLIED_SHA256 = {'05170f05': '05170f0584e700fa8e5bce882cebfe7e25a8be3b1479949c123b23e24f502e32', '0534e4d1': '0534e4d14a48bd4249c5cb6f50cca6573243f876e9d3927dc30d415c5aa524dd', '17abb90d': '17abb90de93659f5fdaef6a298ac04b7c0c71fd934a4fdc2af31d9eb672ab867', '1aca3e0c': '1aca3e0cb170a6960f2d0dad42e57b821998a521307f0024c99cf5d6392eab27', '44a3c09b': '44a3c09be52bb1850598a777160a7a87173a53c0fdca7d7b9c57660ef6129314', '6f482002': '6f482002c85665786d815c6b30f38be5e9aa9c00cd41550cd0e4d598a4bf2e15', '90fdb042': '90fdb04282d30e5ffc45e4dd80bd305b1585499d00e17401d89c454382e03fdd', '9971fec7': '9971fec78a5ae0e1b70fe2900107e005193c1227a5277bc2892bd7063f98e2cd', 'afa64fa2': 'afa64fa25807920cfbfc469e3ded8ae260dfde3d39116178b4e9bcf786b708cd', 'b0cc538a': 'b0cc538abae7e530421f92128ffaa32273b2cbd561a5421c302a7df9acb310ee', 'cad77ea9': 'cad77ea9ab3b5e7379e60f3915a9ff6cae319ae7c48083ac4c3a355827bd5967', 'cb42b642': 'cb42b642b4c791ad2fafb15f22edf71e96d852c9b5a0ae8eaff2d5ca7cdcdef3'}

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
        return extract_parser339_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser339_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser339_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 416
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser339_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser339_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser339_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser339_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser339_leftovers(*args)
    if prefix in ('0534e4d1', '90fdb042'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '09959877',
    '2889606f',
    '57b618c1',
    '679b9142',
    '7a44efd2',
    '915ad298',
    '953589b6',
    'a8b7b261',
    'adc2b7d9',
    'b5ac2015',
    'd582e010',
    'd7503e33',
    '02b01d21', '05f754ae', '28d8a9ab', '344fd637', '3fd951f1', '53049963', '74e2d459', '947e1202', 'a1b75c8f', 'ac7a80ad', 'b89de1db', 'f06a7e6a',
    '03f3a7e2', '14bd8e0e', '1b239b69', '2520e8be', '2df613fd', '2e2ec72c',
    '335bc269', '9713ae8a', 'aac76783', 'c238098a', 'cd084f70', 'dfcb36ee',
    '31628a88',
    '39ec36b8',
    '43a6bf54',
    '5b720f18',
    '6ac3eab0',
    '8ea39615',
    'aa9d9002',
    'aae43f2b',
    'c1edd5aa',
    'd8ea7c8b',
    'd92a31fa',
    'f13ce517',
    '9765f439',
    '3d59d275',
    'aed2920b',
    'd91cf46b',
    '1d268a23',
    '9291f6ad',
    '81f3bc9e',
    '3450837a',
    '129135ad',
    '5378918f',
    '01927b94',
    '5f87b480',
    '0629cb21', '08c613ba', '267dd215', '50985666', '5dad8aa2', '87ac66e7',
    'a9eb2fc1', 'c2b60397', 'ddedd79d', 'f632cfcf', 'f698c58d', 'f7ee7573',
    '09f90c1f', '28528abc', '3e71da53', '762ea6e8', '7f11be01', '950a0991',
    '9c5c898c', 'bb4542dd', 'd518eb02', 'f63aa392', 'f663e109', 'f8fc2919',
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '05a6f15b', '076b6cc6', '0f17b349', '3774d2b6', '54b4ab1b', '58504ce5',
    '68ffaf6b', '87d4b8af', '950a846d', 'a51340d6', 'bb7c8a65', 'f970cd7e',
    '20f4e032', '38b520f1', '433558ba', '4d97f0a8', '4e13c196', '732e61bf', '92ab8218', 'a7271172', 'ae9ac4da', 'bb279338', 'da10e733', 'fa099435',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser339_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




@pytest.mark.parametrize('prefix', ['0534e4d1', '90fdb042'])
def test_signing_requires_matching_source(prefix):
    _, (args, kwargs) = captured(prefix)
    source = kwargs['source_text'].replace('signature individuelle', 'signature collective à deux')
    assert extract_parser339_leftovers(*args, source_text=source) == ([], args[0])


def test_payload_semantics():
    assert selected('05170f05')[0].payload['authorization_date'] == '01.06.2018'
    assert selected('05170f05')[0].event_type == 'capital_changed'
    liquidators = selected('0534e4d1')
    assert [e.signing for e in liquidators[:2]] == ['Einzelunterschrift'] * 2
    assert [e.role for e in liquidators[:2]] == ['Verwaltungsrat und Liquidator'] * 2
    assert liquidators[2].payload['count'] == "1'000"
    assert liquidators[2].event_type == 'capital_changed'
    assert selected('17abb90d')[0].payload['recipient_uid'] == 'CHE-114.164.668'
    transfer = selected('1aca3e0c')[0]
    assert transfer.payload['liabilities'] == "50'195.00"
    assert transfer.payload['credit'] == "86'000.00"
    assert transfer.event_type == 'ownership_changed'
    corrected = selected('44a3c09b')[0]
    assert corrected.payload['name'] == 'Capozza-Bondareva, Anna'
    assert corrected.signing == 'Kollektivprokura zu zweien'
    assert selected('6f482002')[0].payload['revocation_date'] == '15.05.2020'
    assert selected('90fdb042')[1].signing == 'Einzelunterschrift'
    assert selected('9971fec7')[0].event_type == 'status_changed'
    assert selected('afa64fa2')[0].role == 'Kassierin'
    cash = selected('b0cc538a')[0].payload
    assert cash['assets'] == cash['consideration'] == "360'300'000.00"
    shares = selected('cad77ea9')[0].payload
    assert shares['capital_integer'] == "593'833'890" and shares['capital_fraction'] == '72'
    assert shares['converted_count'] == "1'513'218"
    claims = selected('cb42b642')[0].payload
    assert claims['claim_count'] == '98' and claims['claim_value'] == "107'730.7015"
    assert claims['cash_adjustment'] == "43'391.25"
