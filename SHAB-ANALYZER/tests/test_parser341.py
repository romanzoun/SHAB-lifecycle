import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser341 import extract_parser341_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('082387c3', 'fr.text.managers_appointed_unsigned.v1', 2), ('0decdc6f', 'it.text.cooperative_share_range_and_area.v1', 1), ('3e890c4b', 'fr.text.partial_share_transfer_manager_president.v1', 1), ('4ffff852', 'fr.text.administrators_membership_confirmed.v1', 2), ('815e8cba', 'fr.text.principal_establishment_uid.v1', 1), ('85bfaa5e', 'fr.text.collective_signing_notice_completed.v1', 3), ('c3346b0d', 'it.text.asset_transfer_registered_share_consideration.v1', 1), ('c5336706', 'fr.text.foundation_roles_collective_signing.v1', 4), ('d0ea0ee1', 'fr.text.erroneous_deletion_reinstated_reference.v1', 1), ('d6c330d8', 'it.text.new_branch_split_place.v1', 1), ('fe01b812', 'fr.text.capital_reduction_simultaneous_claim_increase.v1', 1), ('fe9ab06f', 'fr.text.foundation_member_appointed_unsigned.v1', 2)]
SUPPLIED_SHA256 = {'082387c3': '082387c3895e5ac099bede898c813153fcd49cbda54a5e382cbcdabbeba19c66', '0decdc6f': '0decdc6f48ae570d028127039ddc8b5d07e42669ad6b72f6bb0493e68c596e59', '3e890c4b': '3e890c4be0d82a77b7637ccf4bae0a0c64521d7b70d595d6b149ab40b3cf4082', '4ffff852': '4ffff85227daa0292cdaa610e271d98536aedc2299f7c048f8fa9d6159362907', '815e8cba': '815e8cbada93442a8132b2dc0f54734244fb6b1fc811f50d10c8f6e0a40b0de2', '85bfaa5e': '85bfaa5e32d20ebf32824ca5c364c12fb0c5c9d202b2ce339289abce25cf2bcf', 'c3346b0d': 'c3346b0d4a9185f8596646cb65584ff599a6cd6ca7ec2967abd5bfff6cb3b40d', 'c5336706': 'c53367063ee8fc73770fa21af3a48638fb4251ce98be0cb0b1f788b577384711', 'd0ea0ee1': 'd0ea0ee110539dee1f6332b24b4b8bec97cead7009ad6e8bd309635927af1515', 'd6c330d8': 'd6c330d850a46c15b01cd0e8455584d1961f0852faf17f7e41b98025e46a087e', 'fe01b812': 'fe01b812a4d153a792ed7a1cba634113aaca37d0bbe2ca8556553930d90c3675', 'fe9ab06f': 'fe9ab06f943f7176a960000ead3f93606c3e129c458084404af085e3ae5c6b7d'}

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
        return extract_parser341_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser341_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser341_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 442
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser341_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser341_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser341_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser341_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser341_leftovers(*args)
    if prefix in ('85bfaa5e', 'd6c330d8', 'fe01b812'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser341_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old





def test_payload_semantics():
    assert all(e.role == 'Geschäftsführer' and e.signing == 'ohne Zeichnungsberechtigung' for e in selected('082387c3'))
    shares = selected('0decdc6f')[0]
    assert shares.event_type == 'capital_changed'
    assert shares.payload['minimum'] == '200' and shares.payload['maximum'] == '500'
    transfer = selected('3e890c4b')[0]
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred'] == transfer.payload['remaining_count'] == '10'
    assert transfer.payload['previous_count'] == '20'
    officers = selected('4ffff852')
    assert [e.role for e in officers] == ['Präsident', 'Verwaltungsrat']
    assert all(e.signing is None for e in officers)
    assert selected('815e8cba')[0].payload['principal_uid'] == 'CHE-103.292.472'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' and e.payload['previous_signing'] == 'Einzelunterschrift' for e in selected('85bfaa5e'))
    assets = selected('c3346b0d')[0]
    assert assets.event_type == 'ownership_changed'
    assert assets.payload['assets'] == "26'093.00" and assets.payload['liabilities'] == '0.00'
    assert [e.role for e in selected('c5336706')] == ['Präsident', 'Sekretär', 'Kassier', 'Stiftungsrat']
    assert selected('d0ea0ee1')[0].payload['entry'] == '4022'
    branch = selected('d6c330d8')[0]
    assert branch.payload['branch_place'] == 'St. Moritz'
    assert branch.payload['normalized_branch_uid'] == 'CHE-176.767.732'
    capital = selected('fe01b812')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['capital'] == '400.000.00'
    assert capital.payload['reduced_capital'] == '0.00'
    corrected = selected('fe9ab06f')
    assert corrected[0].signing == 'ohne Zeichnungsberechtigung'
    assert corrected[1].payload['name'] == corrected[1].payload['corrected_name']
    assert corrected[1].signing == 'Kollektivunterschrift zu zweien mit dem Präsidenten'


@pytest.mark.parametrize('prefix', ['85bfaa5e', 'd6c330d8', 'fe01b812'])
def test_required_source_must_match(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser341_leftovers(*args, source_text='unrelated source') == ([], args[0])
