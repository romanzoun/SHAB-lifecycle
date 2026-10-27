import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser370 import extract_parser370_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0956ab3f', 'fr.text.presiding_associate_share_transfer.v1', 1), ('14d7c946', 'de.text.bankruptcy_dissolved_company_reinstated.v1', 1), ('26f74cca', 'fr.text.two_liquidators_continued_individual_signing.v1', 2), ('3c47d2f4', 'de.text.covid_moratorium_granted_and_extended.v1', 1), ('3c8a17a2', 'fr.text.share_transfer_to_relocated_associate_manager.v1', 2), ('5dc62000', 'fr.text.registered_share_classes_transformed.v1', 1), ('7a8fb13b', 'fr.text.foundation_members_appointed_liquidators.v1', 5), ('94a7c430', 'de.text.bankruptcy_proceedings_reopened_reinstatement.v1', 1), ('bfc5b5c7', 'de.text.branch_deleted_following_closure.v1', 1), ('d68b8a28', 'fr.text.proprietor_bankruptcy_annulled_registration_restored.v1', 1), ('e34cb757', 'fr.text.two_administrators_joint_signing.v1', 4), ('fbe2cf6f', 'fr.text.administrator_president_corrected_typo.v1', 1)]
SUPPLIED_SHA256 = {'0956ab3f': '0956ab3fc4b2c99880c3c4447a58acdae88661779833b286b992b95878b0357e', '14d7c946': '14d7c94622753648cc3e5790bd443258a6840f2b9d8574f916c620d74edeec7f', '26f74cca': '26f74cca794c7efc7e8a70441bc25bf496b5338db59c7135c24f8ec279fae2a4', '3c47d2f4': '3c47d2f453cb05df768a4892df673cb65138633cb2b3a1c207c07994d9832f08', '3c8a17a2': '3c8a17a21d39f7183a252598107eab4a27eed0fbee552254fa130138cb67edf7', '5dc62000': '5dc62000bcc1cd38af84cdb330a95075c0b6956a15c9d8f389a1c6cfed689459', '7a8fb13b': '7a8fb13b0f81e0b20df4f9e0c43c6b37e8616c8e49b467e784b4a66b2fa345a4', '94a7c430': '94a7c43047215a9362cb1ce6845b17ec6c6e449a0c157e15aade33d1b10ee7cb', 'bfc5b5c7': 'bfc5b5c7724e47e9afb7410f30d034782d55291c14819fd9732cb92e08abe84f', 'd68b8a28': 'd68b8a2821e36fd0a941bfd98b0a885d58acc03da281f822814223e6c57010b3', 'e34cb757': 'e34cb7575de70b071966bf72025a095280e718e48a8b45e9879534fe39b16526', 'fbe2cf6f': 'fbe2cf6f06e40a4ced81a05e6cea7b5760c2f3072e210ffd7880a2eb10eee438'}

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
        return extract_parser370_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser370_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser370_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 414
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser370_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser370_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser370_leftovers(args[0], 'en', *args[2:], **kwargs)
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
    for date in set(re.findall(r'\d{2}[-.]\d{2}[-.]\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        events, leftover = extract_parser370_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser370_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['2be1217c', '3d0fb8bb', '40bc6a34', '44f68acf', '4d5b0b09', '4ea787ef', '50807e75', '8733db9b', '9965ad1d', 'c4c22b5b', 'e45d8173', 'ecc918bf'])
def test_parser369_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser370_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for event in baseline.events:
        assert Event(**vars(event)) == event


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser370_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser370_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_payload_semantics():
    transfer = selected('0956ab3f')[0].payload
    assert (transfer['transferred'], transfer['previous_count'], transfer['remaining_count'], transfer['recipient_count']) == ('13', '15', '2', '28')
    assert transfer['currency'] == 'CHF'
    assert selected('14d7c946')[0].payload['deletion_date'] == '14.10.2020'
    assert all(e.role == 'Liquidator' and e.signing == 'Einzelunterschrift' for e in selected('26f74cca'))
    covid = selected('3c47d2f4')[0].payload
    assert (covid['grant_date'], covid['extension_date']) == ('03.07.2020', '05.10.2020')
    recipient = selected('3c8a17a2')[1]
    assert recipient.role == 'Gesellschafter und Geschäftsführer' and recipient.signing == 'Einzelunterschrift'
    assert recipient.payload['place'] == 'Genève'
    capital = selected('5dc62000')[0].payload
    assert (capital['count1'], capital['count2'], capital['count3'], capital['capital']) == ('98', '270', '125', "250'000")
    assert capital['fully_paid'] is True
    assert all(e.role == 'Liquidator' and e.signing is None for e in selected('7a8fb13b'))
    assert selected('94a7c430')[0].payload['opening_time'] == '08.00'
    assert selected('bfc5b5c7')[0].payload['previous_place'] == 'Wettswil am Albis'
    assert selected('d68b8a28')[0].payload['bankruptcy_date'] == '05.08.2020'
    officers = selected('e34cb757')
    assert [e.signing for e in officers] == ['ohne Zeichnungsberechtigung'] * 2 + ['Kollektivunterschrift zu zweien'] * 2
    corrected = selected('fbe2cf6f')[0]
    assert corrected.role == 'Präsident des Verwaltungsrates' and corrected.signing is None
    assert corrected.payload['entry_date'] == '07-10-2020'


@pytest.mark.parametrize('prefix,old,new', [
    ('0956ab3f', "2 parts de CHF 1'000", '2 parts de CHF 200'),
    ('5dc62000', "divisé en 98", 'divisé en 99'),
    ('94a7c430', '08.00 Uhr', '25.00 Uhr'),
])
def test_inconsistent_references_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser370_leftovers(changed, *args[1:], **kwargs) == ([], changed)
