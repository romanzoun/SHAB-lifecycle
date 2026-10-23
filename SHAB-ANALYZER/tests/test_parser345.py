import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser345 import extract_parser345_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0c03925b', 'fr.text.shares_transferred_remaining_holding.v1', 1), ('26bec0b9', 'fr.text.manager_president_gender_corrected.v1', 1), ('34ba9e7e', 'de.text.branch_seat_previous_place.v1', 1), ('366516ce', 'fr.text.judicial_dissolution_bankruptcy_liquidation.v1', 1), ('54fa9aa4', 'fr.text.shareholder_resolution_dissolution.v1', 4), ('9681fa18', 'fr.text.shares_transferred_two_associates.v1', 3), ('9b049f70', 'fr.text.board_president_appointed_continued_signing.v1', 2), ('9c313ec4', 'fr.text.sole_associate_name_corrected.v1', 1), ('b34e5263', 'de.text.definitive_composition_moratorium_granted.v1', 1), ('e01c7759', 'fr.text.interim_order_confirmed.v1', 1), ('e5e4bce9', 'fr.text.shares_consolidated_by_holder.v1', 1), ('ea0cfdb0', 'fr.text.board_member_appointed_excluded_partners.v1', 1)]
SUPPLIED_SHA256 = {'0c03925b': '0c03925b4dffa93455364edcd6728cc2051c6403841770beb92831e77128b46c', '26bec0b9': '26bec0b9c35bc263198f1efc886971abb509e14ecb40858125d059ab2ef54e59', '34ba9e7e': '34ba9e7e125fdd799d403f84ae139ba5c50101458e78577929e14f643da93c66', '366516ce': '366516ce68302b6ab72b137d975a95a6de3190aba2513cc7dc7aa80c67dc3800', '54fa9aa4': '54fa9aa4bc4b2c426b47ad9c184a5f5e475e7d168a8cf2ec1cdde75538419469', '9681fa18': '9681fa1827cca1034a6af1eca2a20b391ab260207de9a02301a4a0c5da4eecbc', '9b049f70': '9b049f70490221811cdb30b6068806c79c55d4e44409a24e78d1656a188f3b4f', '9c313ec4': '9c313ec4f7ed178f73fbffd2a62dda4d732e1d9816fa2313aab5d692cf386039', 'b34e5263': 'b34e526307129a08767f87f74fdc8502e82b3434249d63b26a130f46c90c1cd2', 'e01c7759': 'e01c7759e18ca71f0a0429f4d5d12be4de695e9f520450dfac6007e43edf6824', 'e5e4bce9': 'e5e4bce9d2baab1ec608119fd62f7700dac3e1bc4d28637d9f903ccdd2d4be23', 'ea0cfdb0': 'ea0cfdb07e6239f2ecb45ebad0b8dd5a12f678db1572ece59ea22fbb73ede53b'}

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
        return extract_parser345_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser345_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser345_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 378
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser345_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser345_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser345_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser345_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser345_leftovers(*args)
    if prefix in ('34ba9e7e', '9b049f70', 'ea0cfdb0'):
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
    with patch.object(parser, 'extract_parser345_leftovers', lambda text, *args, **kwargs: ([], text)):
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

@pytest.mark.parametrize('prefix,expected', [
    ('0c03925b', {'count': '98', 'remaining': '102', 'buyer_uid': 'CHE-229.844.735', 'currency': 'CHF'}),
    ('26bec0b9', {'entry': '22250', 'entry_date': '27.11.2019', 'additional_role': 'Präsident'}),
    ('34ba9e7e', {'previous_place': 'Basel', 'place': 'Muttenz', 'branch_uid': 'CHE-135.531.439'}),
    ('366516ce', {'decision_date': '13.07.2020', 'legal_basis': 'article 154 ORC'}),
    ('54fa9aa4', {'decision_date': '22.07.2020', 'address': 'Meylandstrasse 8, 3280 Murten'}),
    ('9681fa18', {'count': '133', 'previous_count': '200', 'count1': '67', 'count2': '66', 'remaining': '67'}),
    ('9c313ec4', {'name': 'G LIFE', 'previous_name': 'G Life Sàrl'}),
    ('b34e5263', {'decision_date': '03.07.2020', 'court_place': 'Baden', 'months': '6'}),
    ('e01c7759', {'original_date': '21.04.2020', 'confirmation_date': '20.08.2020', 'entry': '6802'}),
    ('e5e4bce9', {'old_count1': "14'000", 'count1': '140', 'old_count2': "6'000", 'count2': '60'}),
])
def test_payload_values(prefix, expected):
    assert selected(prefix)[0].payload.items() >= expected.items()


def test_person_roles_and_signing():
    assert selected('26bec0b9')[0].role == 'Geschäftsführer'
    assert selected('26bec0b9')[0].signing is None
    liquidator = selected('54fa9aa4')[2]
    assert liquidator.role == 'Geschäftsführer'
    assert liquidator.signing == 'Einzelunterschrift'
    assert liquidator.payload['additional_role'] == 'Liquidator'
    assert [e.role for e in selected('9b049f70')] == ['Präsident', 'Verwaltungsrat']
    assert [e.signing for e in selected('9b049f70')] == ['Einzelunterschrift', 'Kollektivunterschrift zu zweien']
    assert all(e.role == 'Gesellschafter' and e.signing == 'ohne Zeichnungsberechtigung' for e in selected('9681fa18')[1:])
    member = selected('ea0cfdb0')[0]
    assert member.signing == 'Kollektivunterschrift zu zweien'
    assert member.payload['signing_restriction'] == 'not_with'
    assert len(member.payload['excluded_partners'].split(',')) == 6

@pytest.mark.parametrize('prefix,old,new', [
    ('9681fa18', '133 de ses', '134 de ses'),
    ('e5e4bce9', 'en 140 parts', 'en 141 parts'),
    ('366516ce', '13 juillet', '32 juillet'),
])
def test_inconsistent_numbers_and_dates_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    text = args[0].replace(old, new)
    assert text != args[0]
    assert extract_parser345_leftovers(text, *args[1:], **kwargs) == ([], text)

@pytest.mark.parametrize('prefix', ['34ba9e7e', '9b049f70', 'ea0cfdb0'])
def test_context_required(prefix):
    _, (args, _) = captured(prefix)
    assert extract_parser345_leftovers(*args, source_text='unrelated') == ([], args[0])

@pytest.mark.parametrize('prefix,types', [
    ('0c03925b', ['ownership_changed']),
    ('26bec0b9', ['officer_changed']),
    ('34ba9e7e', ['organization_changed']),
    ('366516ce', ['organization_changed']),
    ('54fa9aa4', ['organization_changed', 'organization_changed', 'officer_changed', 'organization_changed']),
    ('9681fa18', ['ownership_changed', 'officer_changed', 'officer_changed']),
    ('9b049f70', ['officer_changed', 'officer_changed']),
    ('9c313ec4', ['ownership_changed']),
    ('b34e5263', ['organization_changed']),
    ('e01c7759', ['organization_changed']),
    ('e5e4bce9', ['capital_changed']),
    ('ea0cfdb0', ['officer_changed']),
])
def test_existing_event_types(prefix, types):
    assert [e.event_type for e in selected(prefix)] == types
