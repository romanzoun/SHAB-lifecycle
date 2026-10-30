import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser371 import extract_parser371_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0b2d3eb7', 'de.text.organization_disclosure_removed_register_rules.v1', 1), ('1007be5f', 'fr.text.statutes_non_publishable_points_repeated_modified.v1', 1), ('3131ea15', 'it.text.court_order_registration_maintained.v1', 1), ('4848676d', 'fr.text.officer_name_supplemented_notice_reference.v1', 1), ('5c313c51', 'it.text.official_registration_article_152.v1', 1), ('7858766f', 'fr.text.two_new_presiding_managers_individual_signing.v1', 2), ('965fa26d', 'fr.text.administrators_presidency_changed_continued_signing.v1', 2), ('a5b7a664', 'de.text.notice_statutes_corrected_conditional_capital_changed_typo.v1', 1), ('c686757b', 'de.text.covid_moratorium_granted_until_date.v1', 1), ('dd72c018', 'fr.text.two_officers_restricted_joint_signing_shared_origin.v1', 2), ('e0b4d8c6', 'fr.text.two_foundation_members_unsigned_country_codes.v1', 2), ('e14df61f', 'it.text.seat_changed_municipal_merger_decree.v1', 1)]
SUPPLIED_SHA256 = {'0b2d3eb7': '0b2d3eb74bf358b0fc8bc8a49073cf4bf4ef178a3a7385f9e486d1aaeb836e52', '1007be5f': '1007be5f935cec844a71b46798e1c8fcd2bdd7bbb67ab7e7aeabad2f0a332fa1', '3131ea15': '3131ea15b7d1e709e0af42960536d5e5a6bf790be983d74edb182bc6b3ad6afb', '4848676d': '4848676d574317a4bf6d3367fe70a211a3c877753d5532daae1c84acacf55cfb', '5c313c51': '5c313c5106f0460a02e007cb069365d04fc605b284892f594c8ad55a1184b815', '7858766f': '7858766f9a64796954d7570975f175612304d780a18f37ace626a7c36aaee3f6', '965fa26d': '965fa26de2153b048dfac8011b2da0d132d9eabebe950b876b925933b4c0e875', 'a5b7a664': 'a5b7a664465a8b78e3e51e5bfb9210263f853d649db6e116e4827f0ee111b149', 'c686757b': 'c686757b17a3a898dba8661f72cd7e602437f809bffe98693b9e097b5dccf082', 'dd72c018': 'dd72c0189889aa262b0581bc2016e68b5f060114d1914092d2857258fede375b', 'e0b4d8c6': 'e0b4d8c651a7416d2b713918346b439da1797ff149990be572f3bab1ec82d06c', 'e14df61f': 'e14df61f789322e47bae3294ea9c1c1432ea0c29f1424573ac1c05241fd5dbc3'}

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
        return extract_parser371_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser371_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser371_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 438
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser371_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser371_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser371_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser371_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser371_leftovers(*args)
    if prefix in ('1007be5f', '4848676d', '7858766f'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['0956ab3f', '14d7c946', '26f74cca', '3c47d2f4', '3c8a17a2', '5dc62000', '7a8fb13b', '94a7c430', 'bfc5b5c7', 'd68b8a28', 'e34cb757', 'fbe2cf6f'])
def test_parser370_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser371_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser371_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser371_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())



def test_payload_semantics():
    assert selected('1007be5f')[0].payload['statutes_date'] == '08.10.2020'
    assert selected('3131ea15')[0].payload['decision_date'] == '19.10.2020'
    corrected = selected('4848676d')[0].payload
    assert (corrected['name'], corrected['previous_name'], corrected['notice_ref']) == ('Lani Mona', 'Lani Mouna', '0/1005006202')
    managers = selected('7858766f')
    assert [e.role for e in managers] == ['Präsident der Geschäftsführung', 'Vizepräsident der Geschäftsführung']
    assert all(e.signing == 'Einzelunterschrift' for e in managers)
    officers = selected('965fa26d')
    assert [e.role for e in officers] == ['Präsident des Verwaltungsrates', 'Vizepräsident des Verwaltungsrates']
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in officers)
    assert officers[1].payload['previous_role'] == 'Präsident des Verwaltungsrates'
    capital = selected('a5b7a664')[0].payload
    assert (capital['statutes_date'], capital['incorrect_statutes_date']) == ('28.09.2020', '28.08.2020')
    assert (capital['correct_notice_number'], capital['incorrect_notice_number']) == ('192', '100')
    covid = selected('c686757b')[0].payload
    assert (covid['duration_months'], covid['end_date']) == ('3', '19.01.2021')
    restricted = selected('dd72c018')
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in restricted)
    assert all(e.payload['signing_restriction'] == 'pas entre eux, ni avec ' + e.payload['excluded_signers'] for e in restricted)
    assert all(e.payload['origin'] == 'France' for e in restricted)
    foundation = selected('e0b4d8c6')
    assert all(e.role == 'Mitglied des Stiftungsrates' and e.signing == 'ohne Zeichnungsberechtigung' for e in foundation)
    assert all(e.payload['country1'] == e.payload['country2'] == 'CHN' for e in foundation)
    assert selected('e14df61f')[0].payload == {'action': 'seat_changed_municipal_merger_decree', 'municipality': 'Verzasca', 'decree_date': '10.12.2018'}
    assert selected('5c313c51')[0].payload['article'] == '152 ORC'
    assert selected('0b2d3eb7')[0].payload == {'action': 'organization_disclosure_removed_register_rules'}


@pytest.mark.parametrize('prefix', ['1007be5f', '4848676d', '7858766f'])
def test_fragment_requires_matching_source_and_valid_source_dates(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser371_leftovers(*args, source_text='Unrelated source') == ([], args[0])
    source = kwargs['source_text']
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', source)):
        if date in selected(prefix)[0].payload.values():
            assert extract_parser371_leftovers(*args, source_text=source.replace(date, '31.02.2020')) == ([], args[0])


def test_covid_moratorium_keeps_parser330_rule_ownership():
    import shab_analyzer.parse as parser
    original = parser.extract_parser330_leftovers
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    with patch.object(parser, 'extract_parser330_leftovers', capture):
        parse_publication_xml(path('950a846d'))
    assert len(calls) == 1
    args, kwargs = calls[0]
    old_events, old_leftover = original(*args, **kwargs)
    assert not old_leftover
    assert old_events[0].event_type == 'status_changed'
    assert old_events[0].rule_id == 'de.text.covid_moratorium_granted.v1'
    assert old_events[0].payload['moratorium_granted'] is True
    assert 'until_date' in old_events[0].payload
    assert extract_parser371_leftovers(*args, **kwargs) == ([], args[0])


def test_covid_moratorium_legacy_pipeline_unchanged_without_parser371():
    import shab_analyzer.parse as parser
    fixture = path('950a846d')
    actual = parse_publication_xml(fixture)
    with patch.object(parser, 'extract_parser371_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert actual == baseline
