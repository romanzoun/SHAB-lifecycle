import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser340 import extract_parser340_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('2987f13e', 'de.text.cross_border_merger_wholly_owned.v1', 1), ('3285d09c', 'fr.text.committee_members_departed.v1', 4), ('63269358', 'fr.text.foundation_members_departed_powers_cancelled.v1', 3), ('77d5163e', 'fr.text.cooperative_share_nominal.v1', 1), ('976e168b', 'fr.text.directors_individual_signing.v1', 3), ('9dab1a36', 'fr.text.branch_limited_collective_signing.v1', 1), ('aedb98df', 'fr.text.foundation_members_restricted_collective_signing.v1', 4), ('b80ba80f', 'fr.text.company_name_translations_corrected.v1', 1), ('c4186931', 'fr.text.statutes_amendment_notice_corrected.v1', 1), ('d431ce77', 'fr.text.administrator_appointed_vice_president.v1', 2), ('e54bf477', 'fr.text.subsequent_capital_payment_corrected.v1', 1), ('e76aae5c', 'fr.text.associate_manager_name_corrected.v1', 1)]
SUPPLIED_SHA256 = {'2987f13e': '2987f13ef855237ba7a7eff1bde4aafdfb0f390e8d54ce3d0273b6c567bd28c1', '3285d09c': '3285d09cf1ae43578efa8fd400efc53be84f99fab49f7d86c966101328a64dc1', '63269358': '632693581a3607ca46f3c4c054006566c16a684d7b297eeb1f2628eb4ff87925', '77d5163e': '77d5163e753380b4846e2cad3cdc93be33fd182d4dc0e8c9526daef823c25ac9', '976e168b': '976e168b0598fa390204d9cee6897fc46d5f108c6b0baabb88a0bd72a82f68b2', '9dab1a36': '9dab1a3628cddb702400a25f1a92bbed258a35b53c1d9175dba10657767be4fd', 'aedb98df': 'aedb98dfa7d37a331258c2f641ef4d81d6386d2c3d380335c868949c655800e3', 'b80ba80f': 'b80ba80fa5b2c97bc3d872246e4ac8c5530565b084ccc7b63e6da8b4807cff83', 'c4186931': 'c41869313f9742f54c85204ad80c2cb117c97718935f8f0c93808e17482a309d', 'd431ce77': 'd431ce77b3324941d68ddfbb0e740b280819db156fd2c596e85dbadff31ea71a', 'e54bf477': 'e54bf477180bea8f9186cc3aff2a14d243701b39dd8c647572aabf81c5076e04', 'e76aae5c': 'e76aae5cdbb5e36c8ee70d6de477db17e6fc46256718e4500135dc14563c9431'}

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
        return extract_parser340_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser340_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser340_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 366
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser340_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser340_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser340_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser340_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser340_leftovers(*args)
    if prefix in ('aedb98df', 'd431ce77'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser340_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




@pytest.mark.parametrize('prefix', ['aedb98df', 'd431ce77'])
def test_signing_requires_matching_source(prefix):
    _, (args, kwargs) = captured(prefix)
    source = kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert extract_parser340_leftovers(*args, source_text=source) == ([], args[0])


def test_payload_semantics():
    merger = selected('2987f13e')[0]
    assert merger.event_type == 'ownership_changed'
    assert merger.payload['absorbed_foreign_id'] == 'FL-0001.012.770-5'
    assert merger.payload['assets'] == "3'417'595.42"
    assert all(e.payload['membership_ended'] for e in selected('3285d09c')[:2])
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('3285d09c')[2:])
    assert all(e.payload['powers_cancelled'] for e in selected('63269358'))
    assert selected('77d5163e')[0].payload['nominal'] == '100'
    assert all(e.signing == 'Einzelunterschrift' for e in selected('976e168b'))
    assert selected('9dab1a36')[0].payload['signing_scope'] == 'succursale'
    assert selected('9dab1a36')[0].signing == 'Kollektivunterschrift zu zweien beschränkt auf die Zweigniederlassung'
    assert all(e.payload['signing_with'] == 'président(e) ou vice-président(e)' for e in selected('aedb98df'))
    assert all(e.signing == 'Kollektivunterschrift zu zweien mit dem Präsidenten oder dem Vizepräsidenten' for e in selected('aedb98df'))
    assert selected('b80ba80f')[0].payload['translation2'] == 'ASTERIA Investment Managers AG'
    assert selected('c4186931')[0].payload['entry'] == '12462'
    officers = selected('d431ce77')
    assert officers[0].role == 'Vizepräsident' and officers[0].signing is None
    assert officers[1].payload['excluded_signatory'] == 'Basset José Henri'
    assert officers[1].signing == 'Kollektivunterschrift zu zweien, nicht mit Basset José Henri'
    capital = selected('e54bf477')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['capital'] == "125'000"
    assert capital.payload['previous_capital'] == "100'000"
    assert capital.payload['subsequent_payment'] == "50'000"
    corrected = selected('e76aae5c')[0]
    assert corrected.payload['name'] == 'Dias De Sousa Diogo'
    assert corrected.payload['previous_name'] == 'Dias De Dousa Diogo'
    assert corrected.signing is None
