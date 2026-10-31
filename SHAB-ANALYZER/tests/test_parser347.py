import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser347 import extract_parser347_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0ab39892', 'de.text.definitive_moratorium_six_month_extension_approved.v1', 1), ('2ee7eb0d', 'de.text.foundation_board_previous_place_corrected.v1', 1), ('360fedd4', 'fr.text.board_president_and_member_collective_signing.v1', 2), ('6fa3fe10', 'it.text.bankruptcy_revoked_previous_situation_restored.v1', 1), ('a1e7ae61', 'fr.text.new_associates_restricted_collective_signing.v1', 2), ('a60779f4', 'de.text.auditor_previous_registration_number_corrected.v1', 1), ('bcf422aa', 'fr.text.general_partnership_reinstated_by_court.v1', 1), ('c5fa5c4d', 'fr.text.auditor_name_and_seat_changed.v1', 1), ('c9637524', 'fr.text.deputy_director_signing_completed.v1', 1), ('c9b3ebd6', 'de.text.authorized_capital_increase_resolution_amended.v1', 1), ('f2300fb5', 'fr.text.bearer_share_count_corrected.v1', 1), ('fa9ce006', 'fr.text.board_president_and_members_collective_signing_typo.v1', 3)]
SUPPLIED_SHA256 = {'bcf422aa': 'bcf422aa24c384d67d6936a5ff6edeab0fd064ae4cf7d0b8b85ab3693f1fd9b2', '2ee7eb0d': '2ee7eb0dfacb58930ef83638d4788dad1e891b4ffa916e9e7ba96eb4db69ff98', 'c5fa5c4d': 'c5fa5c4d6205a37f4e1cccf39a06378c43773b8300cb35dc41c7c26e3cb9445e', 'f2300fb5': 'f2300fb5abc4094e6083f021744aad978f21f71d3a7344f5a007dc98a9d346da', '360fedd4': '360fedd4c1641f647c25cac7e1e68f9ecefcdd0b76bedc11fa245bbc11bc1879', '0ab39892': '0ab3989233ca89827f0ca0d8c5367f5db36af1aeb1342047bf3f865e776430d6', 'c9b3ebd6': 'c9b3ebd64e922e3f77b424c4ec1b5cf3d424409e3376eacfe7d30177a31100c1', 'a1e7ae61': 'a1e7ae61e6418ca76edb6351ec8e56ce7ff148e311f2af9a1f8a41434deb577a', '6fa3fe10': '6fa3fe10e2d361f93dcaadfb0415bd7b30200718b2ff4ae690f43920407c0cd5', 'c9637524': 'c9637524445c5a1fd39464b5ed36f0c7ed688cacf04d7897624fb670f3866dba', 'a60779f4': 'a60779f4aa86cd7bed66c3e9e075a37805522ef235f78cd495ccc32d3f61b4cf', 'fa9ce006': 'fa9ce006ded0d5899a34aa503645078c8d1ccf13821d229523a02c21d210cc4c'}

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
        return extract_parser347_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser347_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser347_leftovers(*args, **kwargs)[0]


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
    with patch.object(parser, 'extract_parser347_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser347_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser347_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser347_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser347_leftovers(*args)
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
    with patch.object(parser, 'extract_parser347_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old






@pytest.mark.parametrize('prefix', ['0de4e39b', '24d6f7bc', '46fa377a', '5d459649', '667caef8', '6ca57cbb', '7bb4c54f', '81b03e8e', '8d29c898', 'abdc2a7a', 'da8606cf', 'f5d91211', '1aa85cf4', '1f8ffa74', '311d3bbf', '5632f244', '7b1eb120', '8241c2ba', 'ab405e2d', 'afe72629', 'ba5f5ddf', 'df57ab86', 'f5cf3c65', 'fb6010b5'])
def test_recent_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix', ['12199924','495ee781','4b25a973','5227277b','9457810b','9ddc431e','b671b751','c1ab87b2','d16ef08d','d794d81f','dcabd534','fbaa4000'])
def test_parser344_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix', ['0c03925b','26bec0b9','34ba9e7e','366516ce','54fa9aa4','9681fa18','9b049f70','9c313ec4','b34e5263','e01c7759','e5e4bce9','ea0cfdb0'])
def test_parser345_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)

@pytest.mark.parametrize('prefix', ['0d5bd40b', '2dfa90cc', '32a8036e', '57340b0a', '74f19e4f', 'a321ccaf', 'ab18dfa5', 'bd7486d8', 'c1d41c77', 'c419f896', 'd3251a39', 'e87e3685'])
def test_parser346_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix,expected', [
    ('0ab39892', {'decision_date': '03.08.2020', 'end_date': '13.02.2021'}),
    ('2ee7eb0d', {'previous_place': 'Bremgarten bei Bern', 'previous_signing': 'Kollektivunterschrift zu zweien mit dem Präsidenten'}),
    ('6fa3fe10', {'decision_date': '13.08.2020', 'bankruptcy_date': '19.02.2016', 'effective_date': '22.02.2016', 'time': '15:00'}),
    ('a60779f4', {'uid': 'CHE-107.890.726', 'previous_uid': 'CH-020.3.928.812-0'}),
    ('c9b3ebd6', {'decision_date': '18.08.2020', 'authorization_date': '25.06.2019', 'previous_authorization_date': '30.11.2017'}),
    ('f2300fb5', {'capital': "200'000", 'count': "20'000'000", 'nominal': '0.01', 'previous_count': "2'000'000"}),
])
def test_payload_values(prefix, expected):
    assert selected(prefix)[0].payload.items() >= expected.items()


@pytest.mark.parametrize('prefix,roles,signings', [
    ('2ee7eb0d', ['Mitglied des Stiftungsrates'], ['Kollektivunterschrift zu zweien']),
    ('360fedd4', ['Präsident', 'Verwaltungsrat'], ['Kollektivunterschrift zu zweien'] * 2),
    ('a1e7ae61', ['Gesellschafter'] * 2, ['Kollektivunterschrift zu zweien mit Mathey-Doret dit Doret Marc oder Nunez Stéphanie oder Pirkl Peter'] * 2),
    ('c9637524', ['Vizedirektor'], ['Kollektivunterschrift zu zweien mit einem Verwaltungsrat']),
    ('fa9ce006', ['Präsident', 'Verwaltungsrat', 'Verwaltungsrat'], ['Kollektivunterschrift zu zweien'] * 3),
])
def test_roles_and_signing(prefix, roles, signings):
    events = selected(prefix)
    assert [e.role for e in events] == roles
    assert [e.signing for e in events] == signings
    assert len({e.person_key for e in events}) == len(events)


def test_invalid_time_preserved():
    _, (args, kwargs) = captured('6fa3fe10')
    text = args[0].replace('15:00', '25:00')
    assert extract_parser347_leftovers(text, *args[1:], **kwargs) == ([], text)
