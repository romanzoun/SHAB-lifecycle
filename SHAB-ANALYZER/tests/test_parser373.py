import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser373 import extract_parser373_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0a55ac5e', 'fr.text.manager_share_transfer_company_associate_balance.v1', 1), ('13af8ca2', 'de.text.initial_registration_missing_signing_corrected.v1', 1), ('35846617', 'fr.text.three_administrators_presidency_secretary_changed.v1', 3), ('5965b13c', 'fr.text.female_administrator_elected_liquidator.v1', 1), ('6fd2616d', 'fr.text.president_and_local_secretary_joint_signing.v1', 2), ('700d20ff', 'fr.text.two_managers_transfer_to_existing_manager.v1', 1), ('9e4d51cb', 'fr.text.female_manager_surname_corrected_notice.v1', 1), ('b42cdb94', 'it.text.commissioner_mandate_extended.v1', 1), ('bc558b02', 'de.text.association_assets_transferred_cash_consideration.v1', 1), ('cba82eaa', 'fr.text.exact_address_corrected_notice_masculine.v1', 1), ('e43765aa', 'fr.text.sole_proprietor_definitive_moratorium_final_extension.v1', 1), ('f5ea0e9d', 'fr.text.association_dissolved_two_continuing_liquidators.v1', 3)]
SUPPLIED_SHA256 = {'0a55ac5e': '0a55ac5ef95b8764305f119e81fa1436769b0ca3d92b052b200416ebdaf488c1', '13af8ca2': '13af8ca207a79082bd73f8ac3340da89aaec0847e90147d95ac4b3cc3736119c', '35846617': '35846617183bcb648b1c773bcb77c4aa3720cf43c37360b992a6e3ae92f2f443', '5965b13c': '5965b13c2e4f56ac0463f1c55613252d843c217ca0d404e60e493aa5bdf59f2f', '6fd2616d': '6fd2616de66a0fe2cd3cba6396129014938781008f6b408d6327ae511fba478f', '700d20ff': '700d20ff281fc32d509d90a935ebb71038c001540431a703612afe830e76cd1a', '9e4d51cb': '9e4d51cb58e036e9deb115c21af0cc0abef775a4f67a52a4fad791593b11bc8f', 'b42cdb94': 'b42cdb9453cda62a785ff113d1587a06161b717600ca2947f19b93ed24de1f23', 'bc558b02': 'bc558b02626755551339e1e5b72386ed3c2d9f3c3debbe41d899a2dde20931af', 'cba82eaa': 'cba82eaa9fe3778e7c2a5e0c888b1d6986a6bf773b3b1c7bc106562a417703df', 'e43765aa': 'e43765aa2d267eda07afb34a4eab14e3690040285b5576c5c318d502e6f0d858', 'f5ea0e9d': 'f5ea0e9da42d3a2d72c706639b74e1f38f865a59a72a85389ec9e6c6709dbc1d'}

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
        return extract_parser373_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser373_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser373_leftovers(*args, **kwargs)[0]


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
    with patch.object(parser, 'extract_parser373_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser373_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser373_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser373_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser373_leftovers(*args)
    if prefix in ('5965b13c',):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e





@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser373_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old


@pytest.mark.parametrize('prefix', ['01af6481', '165b7d48', '31970459', '492f86e8', '70c07974', '78b516a5', '84fd21eb', '8b7bb042', 'add76c1b', 'e35ee63e', 'e8fa09f6', 'f12bfe3c'])
def test_parser372_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser373_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline


def test_fragment_requires_source():
    _, (args, kwargs) = captured('5965b13c')
    assert extract_parser373_leftovers(*args, source_text='Unrelated') == ([], args[0])


def test_payload_semantics():
    transfer = selected('0a55ac5e')[0].payload
    assert (transfer['before'], transfer['remaining'], transfer['transferred'], transfer['total']) == ('56', '40', '16', '58')
    assert selected('13af8ca2')[0].signing == 'Einzelunterschrift'
    assert [e.role for e in selected('35846617')] == ['Präsident des Verwaltungsrates', 'Sekretär des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    assert selected('5965b13c')[0].role == 'Liquidatorin'
    assert selected('5965b13c')[0].signing == 'Einzelunterschrift'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('6fd2616d'))
    assert selected('700d20ff')[0].payload['remaining_each'] == '70'
    assert selected('9e4d51cb')[0].payload['surname'] != selected('9e4d51cb')[0].payload['previous_surname']
    assert selected('b42cdb94')[0].payload['until'] == '26 ottobre 2021'
    assert selected('bc558b02')[0].payload['assets'] == "492'990.00"
    assert selected('cba82eaa')[0].payload['address'].endswith('1170 Aubonne')
    assert selected('e43765aa')[0].payload['until'] == '30 octobre 2020'
    assert len(selected('f5ea0e9d')) == 3

@pytest.mark.parametrize('version,prefix', [
    (322, '6a2ac180'), (346, '57340b0a'), (346, 'ab18dfa5'),
    (354, '37417c6c'), (354, 'b08f4ea7'), (370, '26f74cca'),
    (370, '0956ab3f'), (372, 'e35ee63e'),
])
def test_existing_rule_ownership_with_earlier_rule_disabled(version, prefix):
    import shab_analyzer.parse as parser
    name = f'extract_parser{version}_leftovers'
    original = getattr(parser, name)
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)
    with patch.object(parser, name, capture):
        actual = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert original(*args, **kwargs)[0]
    assert extract_parser373_leftovers(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser373_leftovers', lambda text, *args, **kwargs: ([], text)):
        assert parse_publication_xml(path(prefix)) == actual


@pytest.mark.parametrize('prefix,old,new', [
    ('0a55ac5e', '40 parts', '41 parts'),
    ('0a55ac5e', '100.00', '101.00'),
    ('b42cdb94', '26 ottobre', '32 ottobre'),
    ('e43765aa', '25 septembre', '31 septembre'),
    ('e43765aa', '30 octobre', '32 octobre'),
])
def test_invalid_dates_and_share_balances_preserve_text(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser373_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('text,language,pattern,old', [
    ("Par décision du 25 septembre 2020, le Tribunal a prolongé le sursis concordataire accordé au titulaire jusqu'au 30 octobre 2020", 'fr',
     'shab_analyzer.parser111._FR_SOLE_PROPRIETOR_MORATORIUM_EXTENDED', 'shab_analyzer.parser111.extract_parser111_leftovers'),
    ("L'associée-gérante Exemple Anna est élue liquidatrice", 'fr',
     'shab_analyzer.parser120._FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR', 'shab_analyzer.parser120.extract_parser120_leftovers'),
    ("L'inscription n° 123 du 10.11.2020 est rectifiée en ce sens que l'adresse exacte est: Rue Exemple 1 (et non pas Rue Exemple 2)", 'fr',
     'shab_analyzer.parser134._FR_ADDRESS_CORRECTED', 'shab_analyzer.parser134.extract_parser134_leftovers'),
])
def test_reused_legacy_patterns_keep_ownership(text, language, pattern, old):
    import importlib
    def resolve(name):
        module, attribute = name.rsplit('.', 1)
        return getattr(importlib.import_module(module), attribute)
    assert resolve(pattern).fullmatch(text)
    args = language, 'fixture', '', None, None, None
    assert resolve(old)(text, *args)[0]
    assert extract_parser373_leftovers(text, *args) == ([], text)
