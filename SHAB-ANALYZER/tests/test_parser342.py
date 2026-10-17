import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser342 import extract_parser342_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('1aa85cf4', 'de.text.authorized_and_conditional_capital_clauses_amended.v1', 1), ('1f8ffa74', 'fr.text.share_transfer_president_and_new_manager.v1', 3), ('311d3bbf', 'fr.text.council_presidency_corrected.v1', 1), ('5632f244', 'de.text.branch_reinstated_principal_name_changed.v1', 1), ('7b1eb120', 'fr.text.liquidation_name_translations.v1', 2), ('8241c2ba', 'it.text.registered_member_corrected.v1', 1), ('ab405e2d', 'de.text.branch_erroneous_deletion_reinstated_reference.v1', 1), ('afe72629', 'fr.text.foundation_members_unsigned.v1', 2), ('ba5f5ddf', 'fr.text.administrator_appointed_unsigned_typo.v1', 1), ('df57ab86', 'fr.text.president_name_corrected_malformed_notice_date.v1', 1), ('f5cf3c65', 'fr.text.authorized_and_conditional_participation_capital.v1', 1), ('fb6010b5', 'de.text.court_order_reinstatement_after_bankruptcy_deletion.v1', 1)]
SUPPLIED_SHA256 = {'1aa85cf4': '1aa85cf4e2ae691ab1010ea3ed152525f16b04fc298c97bef4f8c6864517b2a9', '1f8ffa74': '1f8ffa74a22bb60a7ee512288933e42dca4bd81190c1a8b41de66c383af9358a', '311d3bbf': '311d3bbf746fbe359f714123f3c30344b9319a34722cf5ebe55c74a6517c0b68', '5632f244': '5632f244d4b288b407ccebd2beefb6bbaf4571fbc9755304b0e74ed2ed0dbc5c', '7b1eb120': '7b1eb1205127223efc2cc1e39fdcca2f7ce8643268bbf05a5bb80beeb95c0eb5', '8241c2ba': '8241c2ba223e6c3f746e53449ddd5c24f46c420bf4c9b8f7bce2837b8ba65cc8', 'ab405e2d': 'ab405e2d68a0670c221c2d97c332a633963a3ab2bc4538a7e6d2b1cb0cc9f80b', 'afe72629': 'afe726293dcac85e9c6cb90c605dd7d2dd61153ec53bc776384fc3c31fa42da9', 'ba5f5ddf': 'ba5f5ddff68a730bc8e82f2701283834f4d9190f3ef55b82ed08904b538a7185', 'df57ab86': 'df57ab86cb13a92fd3eab24f334ba0ec5f336eca958c8400314cbf2f63791335', 'f5cf3c65': 'f5cf3c65cdd8a74d26813d3b6d74a9a8fdbed60f85aec18b3a1db74d61d094d0', 'fb6010b5': 'fb6010b5e41a2b6c862cb1888ebc8ba01b3e625950154f8adf014f703197ded0'}

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
        return extract_parser342_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser342_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser342_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 342
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser342_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser342_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser342_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser342_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser342_leftovers(*args)
    if prefix in ('f5cf3c65',):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '082387c3',
    '0decdc6f',
    '3e890c4b',
    '4ffff852',
    '815e8cba',
    '85bfaa5e',
    'c3346b0d',
    'c5336706',
    'd0ea0ee1',
    'd6c330d8',
    'fe01b812',
    'fe9ab06f',
    '2987f13e', '3285d09c', '63269358', '77d5163e', '976e168b', '9dab1a36', 'aedb98df', 'b80ba80f', 'c4186931', 'd431ce77', 'e54bf477', 'e76aae5c',
    '05170f05',
    '0534e4d1',
    '17abb90d',
    '1aca3e0c',
    '44a3c09b',
    '6f482002',
    '90fdb042',
    '9971fec7',
    'afa64fa2',
    'b0cc538a',
    'cad77ea9',
    'cb42b642',
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
    with patch.object(parser, 'extract_parser342_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old





def test_payload_semantics():
    assert selected('1aa85cf4')[0].payload['resolution_date'] == '05.06.2020'
    transfer, president, manager = selected('1f8ffa74')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['remaining_count'] == transfer.payload['transferred_count'] == '100'
    assert president.role == 'Präsident' and manager.role == 'Geschäftsführer'
    assert president.signing is None and manager.signing is None
    correction = selected('311d3bbf')[0]
    assert correction.role is None and correction.signing is None
    assert correction.payload['presidency_ended'] is True
    assert selected('5632f244')[0].payload['principal_translation2'] == 'Manpower Ltd'
    assert selected('7b1eb120')[1].role == 'Liquidator'
    member = selected('8241c2ba')[0]
    assert member.role == 'Mitglied' and member.signing == 'Einzelunterschrift'
    assert member.payload['name'] == 'Salafia Bajoni Thomas'
    assert selected('ab405e2d')[0].payload['entry'] == '5449'
    assert all(e.role == 'Stiftungsrat' and e.signing == 'ohne Zeichnungsberechtigung' for e in selected('afe72629'))
    assert selected('ba5f5ddf')[0].signing == 'ohne Zeichnungsberechtigung'
    assert selected('df57ab86')[0].payload['notice_date_raw'] == '24.0302.20'
    participation = selected('f5cf3c65')[0]
    assert participation.event_type == 'capital_changed'
    assert participation.payload['capital'] == "5'886.91"
    assert participation.payload['count'] == "588'691"
    assert participation.payload['previous_capital'] == '936.50'
    assert participation.payload['transfer_restricted'] is True
    assert selected('fb6010b5')[0].payload['decision_date'] == '22.07.2020'


def test_required_source_must_match():
    _, (args, kwargs) = captured('f5cf3c65')
    assert extract_parser342_leftovers(*args, source_text='unrelated source') == ([], args[0])


def test_impossible_french_date_preserved():
    _, (args, kwargs) = captured('f5cf3c65')
    changed = args[0].replace('1er juillet 2020', '31 février 2020')
    assert extract_parser342_leftovers(changed, *args[1:], **kwargs) == ([], changed)
