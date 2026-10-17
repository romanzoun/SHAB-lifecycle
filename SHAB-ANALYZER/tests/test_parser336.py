import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser336 import extract_parser336_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('02b5ca0c', 'fr.text.registered_auditor_recorded.v1', 1), ('09bc2f9c', 'fr.text.dissolution_and_liquidation_name.v1', 3), ('148f865e', 'fr.text.authorized_capital_clause_deleted.v1', 1), ('28d3c0a2', 'fr.text.board_member_residence_and_role.v1', 2), ('3541dd30', 'fr.text.bankruptcy_and_suspension_no_assets.v1', 1), ('3b58dd44', 'de.text.directors_and_signatory_collective.v1', 4), ('509273fe', 'fr.text.partial_share_transfer_manager_presidency.v1', 3), ('576840da', 'fr.text.unlimited_partner_individual_signing.v1', 1), ('57bc9bf3', 'de.text.authorized_capital_provision_deleted.v1', 1), ('6e15897b', 'fr.text.single_share_transfer_restricted_signing.v1', 2), ('ed8453e2', 'fr.text.statutes_copy_filed_complement.v1', 1), ('fb236d36', 'fr.text.association_resources_replaced.v1', 1)]

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
        return extract_parser336_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser336_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser336_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 346
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser336_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser336_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser336_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {'02b5ca0c': '02b5ca0c23c3e1ed49536ef7cd7b06a7ba706e8cb5c996d32887abeb5294f59c', '09bc2f9c': '09bc2f9cfe81e9cd2a2dcb25d56eddab3d9b3153495bc31e2cf69373ccc484a3', '148f865e': '148f865e253017649dd0c5e3857ec5b6cc27515d9d324bbabaf4c49f9e019539', '28d3c0a2': '28d3c0a27904ad56792f350bafe3c99c3180ece48e4c47eac1c7efa45a9a163b', '3541dd30': '3541dd30ca52d7923035fd62e5785dbae853b094e77f0ca88571be8d6d9856a2', '3b58dd44': '3b58dd4423486d8199b12fb453599d5d1bcd04f004fa30c06417e781102608d7', '509273fe': '509273fe8aa0085b4f107a806073cb4409358505159776de9f47d41682bd54e9', '576840da': '576840da07d0e13e790f837bb402358723900d16b911c1cd4b50041b6b7051df', '57bc9bf3': '57bc9bf3c7329537110f37a8e4e65d514c0737dcc5c389a4595cd268c3115cde', '6e15897b': '6e15897b743ad1ccac568a576dfcbe25ba5822df28290975517d18b39534cf44', 'ed8453e2': 'ed8453e2504e8c060c97a36957d9dc537f305e08b13859088e27e7a05b16af48', 'fb236d36': 'fb236d360791b5957bd83a9c187cad26542cf43757b624ebdf8e7b4d2f4095b8'}
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser336_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser336_leftovers(*args)
    if prefix == '576840da':
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    if prefix == '28d3c0a2':
        assert events[0].signing == 'Einzelunterschrift'
        assert events[1].signing is None
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
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
    with patch.object(parser, 'extract_parser336_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



def test_payload_semantics():
    auditor = selected('02b5ca0c')[0]
    assert auditor.role == 'Revisionsstelle'
    assert auditor.payload['auditor_uid'] == 'CHE-102.503.904'
    assert auditor.payload['place'] == 'Zürich'
    dissolution, corrected, joined = selected('09bc2f9c')
    assert dissolution.payload['decision_date'] == '02.07.2020'
    assert corrected.payload['previous_name'] == 'Fässler Josef B.'
    assert corrected.payload['name'] == 'Fässler Joseph Bruno'
    assert corrected.role == 'Verwaltungsrat und Liquidator'
    assert corrected.signing == joined.signing == 'Einzelunterschrift'
    assert joined.payload['place'] == 'Düdingen'
    capital = selected('148f865e')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['authorization_date'] == '18.07.2018'
    board, president = selected('28d3c0a2')
    assert board.signing == president.signing == 'Einzelunterschrift'
    assert board.payload['place'] == president.payload['place'] == 'Grand-Saconnex'
    assert president.role == 'Verwaltungsrat und Präsident'
    bankruptcy = selected('3541dd30')[0]
    assert bankruptcy.payload['effective_time'] == '14:15'
    assert bankruptcy.payload['effective_date'] == '09.03.2020'
    assert bankruptcy.payload['suspension_date'] == '07.07.2020'
    signers = selected('3b58dd44')
    assert [e.role for e in signers] == ['Direktor'] * 3 + [None]
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in signers)
    assert signers[2].payload['place'] == 'Landeron'
    transfer, president, manager = selected('509273fe')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred_count'] == transfer.payload['received_count'] == '10'
    assert transfer.payload['previous_count'] == '200'
    assert transfer.payload['retained_count'] == '190'
    assert president.role == 'Gesellschafter und Geschäftsführer und Vorsitzender'
    assert president.signing is manager.signing is None
    partner = selected('576840da')[0]
    assert partner.signing == 'Einzelunterschrift'
    assert partner.payload['name'] == 'Skaanild Christian'
    assert partner.payload['place'] == 'Choulex'
    capital = selected('57bc9bf3')[0]
    assert capital.event_type == 'capital_changed'
    assert capital.payload['introduction_date'] == '29.02.2016'
    transfer, associate = selected('6e15897b')
    assert transfer.event_type == 'ownership_changed'
    assert transfer.payload['transferred_count'] == '1'
    assert transfer.payload['retained_count'] == '19'
    assert transfer.payload['nominal'] == "1'000"
    assert associate.role == 'Gesellschafter'
    assert associate.signing == 'Kollektivunterschrift zu zweien mit der Geschäftsführerin'
    assert selected('ed8453e2')[0].payload['entry'] == '4777'
    resources = selected('fb236d36')[0]
    assert resources.payload['previous_nominal'] == '100'
    assert resources.payload['resources'].startswith('terrains, immeubles et installations;')


@pytest.mark.parametrize('source', ['', 'Nouvel associé indéfiniment responsable: inconnu.'])
def test_partner_fragment_requires_complete_source(source):
    _, (args, _) = captured('576840da')
    assert extract_parser336_leftovers(*args, source_text=source) == ([], args[0])


def test_president_signing_requires_matching_source():
    _, (args, kwargs) = captured('28d3c0a2')
    source = kwargs['source_text'].replace('avec signature individuelle:', 'avec signature inconnue:')
    events, leftover = extract_parser336_leftovers(*args, source_text=source)
    assert not leftover
    assert events[0].signing == 'Einzelunterschrift'
    assert events[1].signing is None


@pytest.mark.parametrize('prefix,old,new', [
    ('3541dd30', '14:15', '24:15'),
    ('57bc9bf3', '29.08.2017', '30.08.2017'),
    ('509273fe', 'CHF 100, gérante', 'CHF 200, gérante'),
    ('6e15897b', 'avec la gérante', 'avec un tiers'),
])
def test_unsupported_variants_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    text = args[0].replace(old, new, 1)
    assert text != args[0]
    assert extract_parser336_leftovers(text, *args[1:], **kwargs) == ([], text)
