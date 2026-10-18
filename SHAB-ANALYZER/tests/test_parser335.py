import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser335 import extract_parser335_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('03f3a7e2', 'fr.text.partial_share_transfer_to_company.v1', 3), ('14bd8e0e', 'fr.text.board_member_without_signing.v1', 1), ('1b239b69', 'fr.text.statutes_copy_filed_supplement.v1', 1), ('2520e8be', 'it.text.subsidiary_merger_excess_liabilities.v1', 1), ('2df613fd', 'de.text.branch_purpose_recorded.v1', 1), ('2e2ec72c', 'de.text.branch_register_completed.v1', 1), ('335bc269', 'fr.text.common_owner_merger_subordinated_debt.v1', 1), ('9713ae8a', 'de.text.authorized_participation_capital_reinstated.v1', 1), ('aac76783', 'fr.text.share_transfer_and_manager_presidency.v1', 3), ('c238098a', 'it.text.asset_transfer_no_consideration.v1', 1), ('cd084f70', 'fr.text.all_shares_transferred_departing_managers.v1', 4), ('dfcb36ee', 'de.text.authorized_capital_increase_amended.v1', 1)]

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
        return extract_parser335_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser335_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser335_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 353
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser335_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser335_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser335_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {'03f3a7e2': '03f3a7e207577cf5d0266ec71037dec1aed364e9244019897023c8f5d90bab5d', '14bd8e0e': '14bd8e0e0ec857a963f1965125dcffe52c248cb97cf551983148e0c512f50cb4', '1b239b69': '1b239b69c5c3d9bf3748fd4b7c3fd51950c6012b653fb777bb48e44f77c938fe', '2520e8be': '2520e8bebf7148f10afd556c38bd3a17c406a1fa85bf6d4115cd0b821d17b133', '2df613fd': '2df613fd65636fd02cf92405f99206b7ff763affecc726be4cf7f688988e557e', '2e2ec72c': '2e2ec72cdcad41fffd92368a18befe93f5cd80e06dec3a0f8c0e1057282c2ed4', '335bc269': '335bc269ba92d9546fe6b6e321558ae9dc5215e1ef68857dbdd0814fed180981', '9713ae8a': '9713ae8acf9f2f8b2655fcb640db8deb2d053d538789b8ecd6ce1e0f1f7ec2f1', 'aac76783': 'aac767837ed22929ebf575feab3f7e43a6e5e6bf542ded8983fd8d27978ec8c7', 'c238098a': 'c238098a0368217bc59a2bb67e2b11cf955ef6e6105ddba781e256e3833da3e9', 'cd084f70': 'cd084f70d3ccf8c3b9da56fe073ba45fc3dbc0478a04eb47b5ecf3c8913bb20e', 'dfcb36ee': 'dfcb36ee1531a40e25ec08cc4609ba447dc66057313dc819c4164ccdda8c330e'}
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser335_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser335_leftovers(*args)
    if prefix == '2e2ec72c':
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    if prefix == 'aac76783':
        assert all(e.signing is None for e in events)
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser335_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


def test_payload_semantics():
    transfer, president, manager = selected('03f3a7e2')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred_count'] == '102'
    assert transfer.payload['previous_count'] == '200'
    assert transfer.payload['recipient_uid'] == 'CHE-479.065.533'
    assert president.signing == manager.signing == 'Einzelunterschrift'
    assert president.role == 'Geschäftsführer und Vorsitzender'
    assert president.payload['place'] == 'Cressier NE'
    assert manager.payload['place'] is None
    board = selected('14bd8e0e')[0]
    assert board.payload['name'] == 'Thémans Michaël Clément L.'
    assert board.signing == 'ohne Zeichnungsberechtigung'
    assert selected('1b239b69')[0].payload['entry_date'] == '19.06.2020'
    merger = selected('2520e8be')[0]
    assert merger.event_type == 'ownership_changed'
    assert merger.payload['assets'] == "197'844.00"
    assert merger.payload['liabilities'] == "278'885.00"
    assert merger.payload['excess_liabilities'] == "81'041.00"
    assert merger.payload['freely_available_equity_confirmed'] is True
    assert merger.payload['no_capital_increase'] is True
    assert merger.payload['no_share_allocation'] is True
    assert selected('2df613fd')[0].payload['purpose'].startswith('Erbringung von Dienstleistungen')
    branch = selected('2e2ec72c')[0]
    assert branch.payload['register'] == 'Oberwallis'
    assert branch.payload['branch_uid'] == 'CHE-133.876.502'
    merger = selected('335bc269')[0]
    assert merger.payload['subordinated_debt_confirmed'] is True
    assert merger.payload['excess_liabilities'] == "99'806.22"
    assert merger.payload['no_capital_increase'] is True
    capital = selected('9713ae8a')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['deletion_entry'] == '3209'
    transfer, president, manager = selected('aac76783')
    assert transfer.payload['retained_count'] == transfer.payload['received_count'] == '100'
    assert president.signing == manager.signing == 'Einzelunterschrift'
    assert president.role == 'Gesellschafter und Geschäftsführer und Vorsitzender'
    assert president.payload['place'] is None
    assert manager.payload['place'] == 'Carouge (GE)'
    asset = selected('c238098a')[0]
    assert asset.payload['no_consideration'] is True
    assert asset.payload['assets'] == "369'715.18"
    assert asset.payload['liabilities'] == '0.00'
    transfer, departed1, departed2, joined = selected('cd084f70')
    assert transfer.payload['count'] == '20'
    assert departed1.event_type == departed2.event_type == 'officer_removed'
    assert departed2.payload['name'] == 'Rodzaj ép. Sarrasin Monika Anna'
    assert joined.payload['name'] == 'Zeneli Adnan' and joined.signing is None
    capital = selected('dfcb36ee')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['article'] == '3a'
    assert capital.payload['decision_date'] == '14.07.2020'


@pytest.mark.parametrize('source', ['', 'Zweigniederlassung neu: [Sitz] Visp (CHE-133.876.502) HR Unbekannt.'])
def test_branch_fragment_requires_complete_source(source):
    _, (args, _) = captured('2e2ec72c')
    assert extract_parser335_leftovers(*args, source_text=source) == ([], args[0])


def test_shared_signing_requires_source_evidence():
    _, (args, kwargs) = captured('aac76783')
    events, leftover = extract_parser335_leftovers(*args, source_text=kwargs['source_text'].replace('avec signature individuelle', 'avec signature inconnue'))
    assert not leftover and len(events) == 3
    assert all(e.signing is None for e in events)
