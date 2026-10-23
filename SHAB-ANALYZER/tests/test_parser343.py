import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser343 import extract_parser343_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0de4e39b', 'de.text.cross_border_merger_wholly_owned_foreign_company.v1', 1), ('24d6f7bc', 'de.text.statutes_date_corrected.v1', 1), ('46fa377a', 'de.text.bankruptcy_revoked_company_continues.v1', 1), ('5d459649', 'fr.text.share_transfer_manager_president.v1', 3), ('667caef8', 'de.text.composition_agreement_approved_administrator_mandated.v1', 1), ('6ca57cbb', 'de.text.covid19_moratorium_extended.v1', 1), ('7bb4c54f', 'fr.text.complete_address_and_board_details.v1', 4), ('81b03e8e', 'fr.text.associate_manager_and_president_appointed.v1', 1), ('8d29c898', 'fr.text.foundation_member_now_vice_president.v1', 2), ('abdc2a7a', 'fr.text.conditional_participation_capital_clause_amended.v1', 1), ('da8606cf', 'fr.text.liquidation_address_completed.v1', 1), ('f5d91211', 'fr.text.executive_committee_member_appointed.v1', 2)]
SUPPLIED_SHA256 = {'0de4e39b': '0de4e39b228017a4badf07aba7d18734684376fec54af012acdbe4b4dec109eb', '24d6f7bc': '24d6f7bc7df0e5b9fa0e2c2127b3cae196e2ea2acc786b1506223e12afe61c9c', '46fa377a': '46fa377a1b6c6a68b9e56fccf38026d8b9871f8b76e024dfa001dc80db5c4ae8', '5d459649': '5d4596492427bb36a6aaa609862ae1288af15aa2906566e8519e832dd044a0ec', '667caef8': '667caef83506593967dab1cfcc612fe2be9fdc0dd6549221a106651bf9cfa0ae', '6ca57cbb': '6ca57cbb39104bdddd8286bc4b9ea4f0ecebe236a202ec810d11066615f53421', '7bb4c54f': '7bb4c54fd5557c0daf577ce2ae8a614646ea86cb35764571cc113e2aa9b18f0b', '81b03e8e': '81b03e8eb8b678e22fa68d6afebe62571c15157bf30ab5d75e03b89ef672fed5', '8d29c898': '8d29c8983bcaddd211f1f06c5af4e28d42ad2092a5d531e927f864685e3f1a6a', 'abdc2a7a': 'abdc2a7a8eb46aa8d836d14a4bcbb382816483482a1606b7cd4c40ec065e63e2', 'da8606cf': 'da8606cf34f1b5fdd85043043ecbc4140657e1ce4aecf776b9961a46667baebe', 'f5d91211': 'f5d91211934c81ced28582d1d0712becdbb5c62cc1c2c4b9185fa35a6d630b33'}

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
        return extract_parser343_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser343_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser343_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 380
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser343_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser343_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser343_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser343_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser343_leftovers(*args)
    if prefix == '24d6f7bc':
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    if prefix in ('5d459649', '81b03e8e', 'f5d91211'):
        assert all(e.signing is None for e in events)
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
    with patch.object(parser, 'extract_parser343_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old





@pytest.mark.parametrize('prefix,expected', [
    ('0de4e39b', {'foreign_id': 'FL-0002.458.480-7', 'agreement_date': '15.06.2020', 'balance_date': '31.12.2019', 'assets': "340'379.48", 'liabilities': "40'372.92", 'currency': 'CHF', 'capital_increase': False, 'share_allocation': False}),
    ('24d6f7bc', {'statutes_date': '28.07.2020', 'previous_statutes_date': '23.07.2020'}),
    ('46fa377a', {'decision_date': '11.08.2020', 'previous_decision_date': '07.08.2020', 'effective_date': '07.08.2020', 'effective_time': '11.40', 'court': 'Gerichtspräsidiums Zurzach'}),
    ('5d459649', {'name': 'Zheng Yuner', 'recipient': 'Laurent Jean-Luc', 'transferred_count': '1', 'nominal': '100', 'recipient_count': '2', 'remaining_count': '198', 'currency': 'CHF'}),
    ('667caef8', {'decision_date': '18.06.2020', 'administrator_uid': 'CHE-106.826.571', 'administrator': 'Bachmann Partner Sachwalter und Treuhand AG', 'previous_decision_date': '23.03.2020', 'previous_end_date': '21.05.2020'}),
    ('6ca57cbb', {'decision_date': '31.07.2020', 'end_date': '05.11.2020', 'duration_months': '3', 'court': 'Bezirksgerichts Zürich'}),
    ('7bb4c54f', {'address': 'Obertswilstrasse 63', 'postal_code': '1735', 'town': 'Giffers', 'previous_name2': 'Gurtner-Buntschu Martha', 'name2': 'Gurtner-Buntschu Martha Rita'}),
    ('81b03e8e', {'name': 'Bresolin Adrien', 'additional_role': 'Präsident'}),
    ('8d29c898', {'name': 'Schmid Rudolf', 'previous_role': 'Sekretär'}),
    ('abdc2a7a', {'decision_date': '23.07.2020', 'authorization_date': '02.10.2019'}),
    ('da8606cf', {'entry': '11787', 'entry_date': '10.07.2020', 'street': 'Boulevard Helvétique', 'house_number': '30', 'care_of': 'Geneva Wealth Capital Management SA', 'postal_code': '1207', 'place': 'Genève'}),
    ('f5d91211', {'name': 'Evéquoz Pauline', 'origin': 'Conthey', 'place': 'Genève'}),
])
def test_sample_payload_values(prefix, expected):
    assert selected(prefix)[0].payload.items() >= expected.items()


def test_event_types_roles_and_signing():
    assert selected('0de4e39b')[0].event_type == 'ownership_changed'
    transfer, president, manager = selected('5d459649')
    assert transfer.event_type == 'ownership_changed'
    assert president.role == 'Präsident' and president.signing is None
    assert manager.role == 'Geschäftsführer' and manager.signing == 'Einzelunterschrift'
    assert manager.payload['name'] == 'Laurent Jean-Luc'
    address, *board = selected('7bb4c54f')
    assert [e.role for e in board] == ['Präsident', 'Sekretärin', 'Vizepräsident']
    assert all(e.signing == 'Einzelunterschrift' for e in board)
    assert board[1].payload['name'] == 'Gurtner-Buntschu Martha Rita'
    assert board[1].payload['previous_signing'] == 'Kollektivunterschrift zu zweien'
    assert all(e.payload['origin'] == 'Kirchdorf BE' for e in board)
    manager = selected('81b03e8e')[0]
    assert manager.role == 'Geschäftsführer' and manager.signing == 'Einzelunterschrift'
    vice, member = selected('8d29c898')
    assert vice.role == 'Vizepräsident' and member.role == 'Stiftungsrat'
    assert member.payload['previous_role'] == 'Vizepräsident'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in (vice, member))
    assert selected('abdc2a7a')[0].event_type == 'capital_changed'
    first, second = selected('f5d91211')
    assert first.role == second.role == 'Vorstand'
    assert first.signing == second.signing == 'Kollektivunterschrift zu zweien'
    assert second.payload['name'] == 'Hofer Christian'
    assert second.payload['origin'] == 'Langnau im Emmental' and second.payload['place'] == 'Zurich'


@pytest.mark.parametrize('prefix', ['5d459649', '81b03e8e', 'f5d91211'])
def test_signing_never_inferred_without_matching_source(prefix):
    _, (args, _) = captured(prefix)
    events, leftover = extract_parser343_leftovers(*args, source_text='unrelated source')
    assert not leftover
    assert all(e.signing is None for e in events)


def test_correction_requires_valid_original_date():
    _, (args, kwargs) = captured('24d6f7bc')
    assert extract_parser343_leftovers(*args, source_text='unrelated source') == ([], args[0])
    changed = kwargs['source_text'].replace('23.07.2020', '31.02.2020')
    assert extract_parser343_leftovers(*args, source_text=changed) == ([], args[0])


def test_share_transfer_holder_must_agree():
    _, (args, kwargs) = captured('5d459649')
    changed = args[0].replace('Zheng Yuner reste', 'Autre Personne reste')
    assert extract_parser343_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix', ['1aa85cf4', '1f8ffa74', '311d3bbf', '5632f244', '7b1eb120', '8241c2ba', 'ab405e2d', 'afe72629', 'ba5f5ddf', 'df57ab86', 'f5cf3c65', 'fb6010b5'])
def test_parser342_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)
