import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser330 import extract_parser330_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('05a6f15b', 'fr.text.covid_moratorium_commissioner.v1', 2),
    ('076b6cc6', 'fr.text.authorized_capital_offset_corrected.v1', 1),
    ('0f17b349', 'fr.text.manager_share_transfer_unsigned_associate.v1', 2),
    ('3774d2b6', 'fr.text.authorized_capital_clause_amended.v1', 1),
    ('54b4ab1b', 'de.text.business_office_address_replaced.v1', 1),
    ('58504ce5', 'fr.text.manager_share_transfer_remaining_unsigned.v1', 2),
    ('68ffaf6b', 'fr.text.associate_manager_becomes_president.v1', 3),
    ('87d4b8af', 'fr.text.three_registered_share_classes_corrected.v1', 1),
    ('950a846d', 'de.text.covid_moratorium_granted.v1', 1),
    ('a51340d6', 'fr.text.fully_paid_capital_corrected.v1', 1),
    ('bb7c8a65', 'fr.text.two_share_transfers_individual_managers.v1', 4),
    ('f970cd7e', 'fr.text.two_individual_procurations.v1', 2),
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
        return extract_parser330_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser330_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser330_leftovers(*args, **kwargs)[0]


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
    with patch.object(parser, 'extract_parser330_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser330_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser330_leftovers(args[0], 'en', *args[2:], **kwargs)
    assert not events and leftover == args[0]



@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_bytes_match_supplied_samples(prefix, rule, count):
    supplied_sha256 = {
        '05a6f15b': '05a6f15b4849cac58db87ab829aa03b051b75e78b85f69d7b505311d829c92ad',
        '076b6cc6': '076b6cc6f634c182f6fba95985f93a18526fcc18c90891c6aa080ef68c609490',
        '0f17b349': '0f17b349415fc47c4f0bf47fa80a4c2af3bd1c86a52d1b16ac5d668266823e6c',
        '3774d2b6': '3774d2b62aeebecacf512f944872a46f65d39b2b0aa34b008f882e35f1705d20',
        '54b4ab1b': '54b4ab1b7014c5c1a1c78ebf3d9c4188809a6daee9665815a05eafa88b445e13',
        '58504ce5': '58504ce5fd75fc91fc6ae5ee20b880e51dca94ba646c5b89e2aa1f2448648759',
        '68ffaf6b': '68ffaf6bb98b68f990c3b2a31da683cab798ae239dabe7c8bf009d24a680dc7a',
        '87d4b8af': '87d4b8afb2c1fa86260eb94ea4f5d27731f7b135e405a44454f60772e086e4ac',
        '950a846d': '950a846d44a3534155c9d292fb806c16e0a0af100e35ce1889d3ac018a657109',
        'a51340d6': 'a51340d6e670c3cedb0097db99f5e7f820618d3e5a86b2927515823639a10dc1',
        'bb7c8a65': 'bb7c8a6510c4f4f8b9ccf5d2e2ab8eeacb83cd221c2d2f5f8aac0700c5c19b74',
        'f970cd7e': 'f970cd7ef0599c2a77b9fe1771e225cb0bd13df93ea1780f0ecbceaf1b180af3',
    }
    fixture = path(prefix)
    assert fixture.stem == supplied_sha256[prefix]
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == supplied_sha256[prefix]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_dates_and_optional_source(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser330_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser330_leftovers(*args)
    if prefix in {'0f17b349', '87d4b8af', 'bb7c8a65'}:
        assert not events and leftover == args[0]
        for source in ['', kwargs['source_text'] + ' UNKNOWN_SUFFIX']:
            events, leftover = extract_parser330_leftovers(*args, source_text=source)
            assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', [
    '09f90c1f', '28528abc', '3e71da53', '762ea6e8', '7f11be01', '950a0991',
    '9c5c898c', 'bb4542dd', 'd518eb02', 'f63aa392', 'f663e109', 'f8fc2919',
    '03dcc069', '315da231', '353d9e29', '693c452c', '7c27565a', '8889623a',
    'a5f4be23', 'bbf607eb', 'c332722f', 'ce010fcd', 'cfbe1db2', 'f0fd9d83',
    '518fef8d', '5404cc5f', '54125ed4', '6d18ed72', '6d50c77a', '7a6515f3',
    '930507a1', 'a16a5540', 'a564e09d', 'b384c365', 'cf527290', 'ecba5198',
    '1cf200d1', 'c9cb541c', 'e3c5c5cd', '94b72118-d3cb-46f4-8cf3-8d526586b9f2',
])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser330_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old



def test_payload_semantics():
    moratorium, commissioner = selected('05a6f15b')
    assert moratorium.event_type == 'status_changed'
    assert moratorium.payload['until_date'] == '4 septembre 2020'
    assert moratorium.payload['moratorium_granted'] is True
    assert commissioner.role == 'Sachwalter' and commissioner.signing is None
    correction = selected('076b6cc6')[0]
    assert correction.event_type == 'capital_changed'
    assert correction.payload['claim'] == "3'158'100"
    assert correction.payload['previous_claim'] == "3'100'407.69"
    transfer, associate = selected('0f17b349')
    assert transfer.payload['transferred'] == transfer.payload['buyer_count'] == '5'
    assert associate.role == 'Gesellschafter' and associate.signing == 'ohne Zeichnungsberechtigung'
    assert associate.payload['country'] == 'FRA'
    clause = selected('3774d2b6')[0]
    assert clause.payload['authorization_date'] == '25 juin 2010'
    assert clause.payload['previous_decision_date'] == '26 septembre 2019'
    address = selected('54b4ab1b')[0]
    assert address.event_type == 'address_changed'
    assert address.payload['address_kind'] == 'Geschäftsstelle'
    assert address.payload['previous_address'] == 'Moosstrasse 31'
    assert address.payload['address'] == 'Moosstrasse 33a'
    transfer, associate = selected('58504ce5')
    assert (transfer.payload['before'], transfer.payload['transferred'], transfer.payload['remaining']) == ('200', '40', '160')
    assert associate.signing == 'ohne Zeichnungsberechtigung'
    president, *managers = selected('68ffaf6b')
    assert president.role == 'Gesellschafter, Geschäftsführer, Präsident'
    assert president.signing is None
    assert all(e.role == 'Geschäftsführer' and e.signing == 'Einzelunterschrift' for e in managers)
    shares = selected('87d4b8af')[0]
    assert shares.payload['corrected'] is True
    assert [shares.payload[f'count{i}'] for i in (1, 2, 3)] == ["10'000'000", "5'266'665", "5'952'379"]
    assert shares.payload['class2'] == 'A0' and shares.payload['class3'] == 'A'
    assert shares.payload['preferred_rights'] == 'produit de liquidation'
    assert selected('950a846d')[0].payload['until_date'] == '08.10.2020'
    paid = selected('a51340d6')[0]
    assert paid.payload['capital'] == "100'000" and paid.payload['fully_paid'] is True
    transfer, president, former_director, manager = selected('bb7c8a65')
    assert transfer.payload['transferred1'] == transfer.payload['transferred2'] == '66'
    assert all(e.signing == 'Einzelunterschrift' for e in [president, former_director, manager])
    assert former_director.payload['previous_role'] == 'Direktorin'
    assert former_director.role == 'Gesellschafterin, Geschäftsführerin'
    assert all(e.signing == 'Einzelprokura' and e.event_type == 'signing_authority_changed' for e in selected('f970cd7e'))


@pytest.mark.parametrize('prefix,old,new', [
    ('05a6f15b', 'a été octroyé', 'a été refusé'),
    ('076b6cc6', 'par compensation', 'sans compensation'),
    ('0f17b349', "n'exerce pas", 'exerce'),
    ('3774d2b6', 'a modifié', 'a supprimé'),
    ('54b4ab1b', 'Geschäftsstelle:', 'Sitz:'),
    ('58504ce5', 'sans signature', 'avec signature'),
    ('68ffaf6b', 'individuellement', 'collectivement à deux'),
    ('87d4b8af', 'produit de liquidation', 'droit de vote'),
    ('950a846d', 'bewilligt', 'abgelehnt'),
    ('a51340d6', 'entièrement libéré', 'partiellement libéré'),
    ('bb7c8a65', 'jusqu\'ici directrice', 'nouvelle directrice'),
    ('f970cd7e', 'individuelle', 'collective'),
    ('58504ce5', 'de 160 parts', 'de 159 parts'),
    ('0f17b349', 'pour 5 parts', 'pour 6 parts'),
    ('bb7c8a65', 'pour 66 parts', 'pour 67 parts'),
    ('05a6f15b', '4 juin 2020', '31 juin 2020'),
])
def test_unsupported_or_inconsistent_clauses_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    events, leftover = extract_parser330_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,old,new', [
    ('0f17b349', "il n'exerce pas", 'il exerce'),
    ('87d4b8af', 'avec restrictions', 'sans restrictions'),
    ('bb7c8a65', 'avec signature individuelle', 'avec signature collective à deux'),
])
def test_consumed_source_details_must_match(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = kwargs['source_text'].replace(old, new)
    assert changed != kwargs['source_text']
    events, leftover = extract_parser330_leftovers(*args, source_text=changed)
    assert not events and leftover == args[0]


@pytest.mark.parametrize('prefix', ['05a6f15b', '076b6cc6', '3774d2b6'])
def test_invalid_written_dates_preserved(prefix):
    _, (args, kwargs) = captured(prefix)
    dates = re.findall(r'\d{1,2} (?:juin|juillet|septembre|décembre) \d{4}', args[0])
    assert dates
    for date in dates:
        changed = args[0].replace(date, '31 février 2020')
        events, leftover = extract_parser330_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
