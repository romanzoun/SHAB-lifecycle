import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser338 import extract_parser338_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('09959877', 'fr.text.three_collective_signatories.v1', 3), ('2889606f', 'fr.text.given_names_complemented.v1', 1), ('57b618c1', 'fr.text.committee_member_restricted_signing.v1', 1), ('679b9142', 'fr.text.principal_bankruptcy_branch_name.v1', 1), ('7a44efd2', 'de.text.branch_registration_practice_changed.v1', 1), ('915ad298', 'fr.text.corporate_share_transfer_to_manager.v1', 1), ('953589b6', 'it.text.unsigned_associate_corrected.v1', 1), ('a8b7b261', 'fr.text.successive_share_transfers.v1', 2), ('adc2b7d9', 'fr.text.foundation_signing_unrestricted.v1', 3), ('b5ac2015', 'fr.text.administrator_name_corrected_typo.v1', 1), ('d582e010', 'fr.text.share_transfer_unsigned_manager.v1', 2), ('d7503e33', 'fr.text.managers_collective_signing.v1', 3)]
SUPPLIED_SHA256 = {'09959877': '0995987728847cbd4eaaafdf93cab5968fd4e94b0b68f04ebf4a1738dab8008b', '2889606f': '2889606fbc2d6f1308dd9d3576fd17af5ad0c1816c0e32827fae8aeda6f23576', '57b618c1': '57b618c1628388b14ae5a12c951208bdb0b85b19cb0529ed32fb98b36046bf1e', '679b9142': '679b914274b637b2f3859a9958b570ff5c840dba76427e93b510eac37c174034', '7a44efd2': '7a44efd214086b4a6b49db7d5e6bb7eff1f60a5c25e7d69c4a117437c0283808', '915ad298': '915ad29862f6616a8bdab4df141469aa6b1111e8e89b100699d44a70ed353d65', '953589b6': '953589b69b4c20fc3db27b576358401308ff5fba025d67c8ee669eba66035f8e', 'a8b7b261': 'a8b7b2617ff80b19df02ebe59e04f609183f5f59ecc8539831872db5101b7f4d', 'adc2b7d9': 'adc2b7d9effe11f3b81dbba53592bb78f7ddf44dc75dbb4bf73e86a46fc6b249', 'b5ac2015': 'b5ac201515d5204cbc769a9de81e7a9b1eca7f3d95d0e0a97c60c55789b4f4ad', 'd582e010': 'd582e010b261556712e4eba478fe0c087ead4d5b8cb0a94fae621010a35c568c', 'd7503e33': 'd7503e330ed4eceab1488c1b4c3e460dbc2df0a5a633e385d141b7ea5c4eddeb'}

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
        return extract_parser338_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser338_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser338_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 445
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser338_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser338_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser338_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser338_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser338_leftovers(*args)
    if prefix in ('57b618c1', 'adc2b7d9', 'd7503e33'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser338_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



@pytest.mark.parametrize('prefix', ['57b618c1', 'adc2b7d9', 'd7503e33'])
def test_signing_requires_matching_source(prefix):
    _, (args, kwargs) = captured(prefix)
    source = kwargs['source_text'].replace('signature collective à deux', 'signature individuelle')
    assert extract_parser338_leftovers(*args, source_text=source) == ([], args[0])


def test_payload_semantics():
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('09959877'))
    assert selected('2889606f')[0].payload['given_names'] == 'Amala Suganya'
    assert selected('57b618c1')[0].signing == 'Kollektivunterschrift zu zweien mit dem Präsidenten oder dem Generaldirektor'
    bankruptcy = selected('679b9142')[0]
    assert bankruptcy.event_type == 'status_changed'
    assert bankruptcy.payload['effective_time'] == '10h59'
    branch = selected('7a44efd2')[0]
    assert branch.payload['branch_uid'] == 'CHE-439.991.037'
    assert branch.payload['previous_registration'] == 'CH-300.9.016.437-9'
    transfer = selected('915ad298')[0]
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred_count'] == '50'
    assert transfer.payload['retained_count'] == '110'
    assert transfer.payload['received_total'] == '90'
    corrected = selected('953589b6')[0]
    assert corrected.payload['name'] == 'Muggeo, Alessandra'
    assert corrected.payload['count'] == '100'
    assert corrected.signing == 'ohne Zeichnungsberechtigung'
    successive, associate = selected('a8b7b261')
    assert successive.payload['count'] == '20'
    assert successive.payload['retained_count'] == '90'
    assert associate.signing == 'ohne Zeichnungsberechtigung'
    foundation = selected('adc2b7d9')
    assert len(foundation) == 3
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in foundation)
    assert selected('b5ac2015')[0].payload['previous_name'] == 'Bolko Stefan Peter dit Hohaus'
    transfer, manager = selected('d582e010')
    assert transfer.payload['count1'] == '200' and transfer.payload['count2'] == '85'
    assert transfer.payload['transferred_count'] == '15'
    assert manager.signing == 'ohne Zeichnungsberechtigung'
    managers = selected('d7503e33')
    assert len(managers) == 3
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in managers)
    assert managers[2].role == 'Vorsitzender der Geschäftsführung'


@pytest.mark.parametrize('old,new', [('18 juin', '32 juin'), ('10h59', '25h59')])
def test_invalid_bankruptcy_date_or_time_preserved(old, new):
    _, (args, kwargs) = captured('679b9142')
    changed = args[0].replace(old, new)
    assert extract_parser338_leftovers(changed, *args[1:], **kwargs) == ([], changed)
