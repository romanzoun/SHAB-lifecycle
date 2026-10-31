import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser333 import extract_parser333_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('01927b94', 'fr.text.shares_transferred_two_new_managers.v1', 3),
    ('129135ad', 'fr.text.board_president_secretary_exchanged.v1', 2),
    ('1d268a23', 'de.text.company_asset_transfer_no_consideration.v1', 1),
    ('3450837a', 'de.text.participation_certificates_cancelled.v1', 1),
    ('3d59d275', 'de.text.branch_uid_register_entry_removed.v1', 1),
    ('5378918f', 'de.text.registered_share_nominal_reduced_repaid.v1', 1),
    ('5f87b480', 'it.text.merger_common_member_no_capital_increase.v1', 1),
    ('81f3bc9e', 'fr.text.officer_residence_changed.v1', 2),
    ('9291f6ad', 'fr.text.new_manager_without_signing.v1', 1),
    ('9765f439', 'it.text.company_name_translations_removed.v1', 1),
    ('aed2920b', 'de.text.branch_register_place_removed.v1', 1),
    ('d91cf46b', 'fr.text.board_collective_signing_updated.v1', 3),
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
        return extract_parser333_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser333_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser333_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 444
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser333_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser333_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser333_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {
        '01927b94': '01927b946134f14ac03749bd52eb10a8fc21f42b7888da593197f682338c9df4',
        '129135ad': '129135adeda0edfa0e1584e9e13f8978a70f3afe835cdced960a509bdd880b39',
        '1d268a23': '1d268a2394431c3191acad7f89549629914a4bf3708dc58640a8b6aedce3783f',
        '3450837a': '3450837a6047b0c68946a85316e56b81feedc53bb634558215bd5c785bcfac90',
        '3d59d275': '3d59d275792223a9c3d8813bcf05ec51a23c15bfefcbaa72d19061d3e8a13371',
        '5378918f': '5378918f52c7b38b1b6f48ad3fe3465f22a7fd730dbd13bf0d8c19f6ace9433e',
        '5f87b480': '5f87b480758f13d1caa7d15dbfe452a702f98a9b7b035e98d77814c54fad3b42',
        '81f3bc9e': '81f3bc9e45923fba1111eab3046cd707e9fbcb35af8f97ed53ad9acdd7094df3',
        '9291f6ad': '9291f6add6f1e185d358cc78131679cc512e4340cd240e74be3380e19e27ad2a',
        '9765f439': '9765f4390ee506f0b564763976af74d43d4f485df28715eedc221656d03eb3fe',
        'aed2920b': 'aed2920b15e08772e02f6561684c733abb4c56c87802d197d974fab3d742bf12',
        'd91cf46b': 'd91cf46b0f9f68c9ff6d5f7a893dc746c7a1aab9b7f3150d530b4b826d458567',
    }
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser333_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser333_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser333_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    transfer, *managers = selected('01927b94')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['count1'] == transfer.payload['count2'] == '3'
    assert transfer.payload['remaining'] == '4'
    assert transfer.payload['nominal'] == "1'000"
    assert all(e.role == 'Gesellschafter und Geschäftsführer' and e.signing == 'Kollektivunterschrift zu zweien' for e in managers)
    president, secretary = selected('129135ad')
    assert president.role == 'Verwaltungsrat, Präsident' and president.payload['previous_role'] == 'Sekretär'
    assert secretary.role == 'Verwaltungsrat, Sekretär' and secretary.payload['previous_role'] == 'Präsident'
    assert president.signing == secretary.signing == 'Einzelunterschrift'
    asset = selected('1d268a23')[0]
    assert asset.event_type == 'ownership_changed' and asset.payload['no_consideration'] is True
    assert asset.payload['assets'] == "2'546'490.00" and asset.payload['liabilities'] == "321'286.00"
    certificates = selected('3450837a')[0]
    assert certificates.event_type == 'capital_changed' and certificates.payload['previous_count'] == "5'400"
    assert selected('3d59d275')[0].payload['branch_uid'] == 'CHE-402. 696.489'
    capital = selected('5378918f')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['count'] == "5'000'000"
    assert capital.payload['previous_nominal'] == '1.00' and capital.payload['nominal'] == '0.90'
    assert capital.payload['repayment'] == '0.10'
    merger = selected('5f87b480')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['capital_increase'] is False and merger.payload['share_allocation'] is False
    assert merger.payload['assets'] == "279'222.88" and merger.payload['liabilities'] == "130'119.35"
    assert all(e.payload['place'] == 'Montreux' and e.role is None and e.signing is None for e in selected('81f3bc9e'))
    manager = selected('9291f6ad')[0]
    assert manager.role == 'Geschäftsführer' and manager.signing == 'ohne Zeichnungsberechtigung'
    assert selected('9765f439')[0].event_type == 'organization_changed'
    assert selected('aed2920b')[0].payload['place'] == 'St. Gallen'
    board = selected('d91cf46b')
    assert [e.role for e in board] == ['Verwaltungsrat, Präsident', 'Verwaltungsrat, Sekretär', None]
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in board)
    assert board[2].payload['place'] is None


def test_inconsistent_repayment_preserved():
    _, (args, kwargs) = captured('5378918f')
    changed = args[0].replace('CHF 0.10', 'CHF 0.11')
    events, leftover = extract_parser333_leftovers(changed, *args[1:], **kwargs)
    assert events == [] and leftover == changed
