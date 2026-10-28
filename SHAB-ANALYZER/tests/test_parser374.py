import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser374 import extract_parser374_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0dd9078e', 'de.text.registered_shares_cancelled_and_issued.v1', 1), ('122be2bc', 'fr.text.shares_converted_liquidation_preference_singular.v1', 1), ('2cad4436', 'fr.text.one_manager_exact_name_corrected.v1', 1), ('372b2440', 'fr.text.share_transfer_new_female_presiding_manager.v1', 2), ('69b4278e', 'fr.text.sole_female_manager_individual_signing.v1', 1), ('88212b54', 'fr.text.foundation_dissolved_two_liquidators_typo.v1', 3), ('a0b0c527', 'it.text.head_office_share_payment_corrected.v1', 1), ('bf55b354', 'fr.text.founder_purpose_reservation_absence_corrected.v1', 1), ('cacf9355', 'fr.text.board_presidency_changed_individual_signing.v1', 2), ('e2977a84', 'fr.text.two_foundation_members_unsigned_second_du_origin.v1', 2), ('e98fb040', 'fr.text.branch_removed_without_register_identifier.v1', 1), ('eccaddc0', 'it.text.wholly_owned_merger_deficit_subordinated_claims.v1', 1)]
SUPPLIED_SHA256 = {'0dd9078e': '0dd9078e48617132e051d63d9f66b4ecc8c2fb45826eb9c753e4cd3d30dfdd2a', '122be2bc': '122be2bc2e6c6e668bf93364dee2dcc8d91266ac5e60115a779dc22705437e6a', '2cad4436': '2cad44364e884116758cdd0bf457355610cdbf6149311dbe6c43709c7e61d2e5', '372b2440': '372b244056ae7f2849c1c66ffebcbc605d822f8be40cb4ffe146c58dafb1a54e', '69b4278e': '69b4278e1bd850ff35b4b6f3e5952f03cd8fb5f96103e615386bf69bd578ad4f', '88212b54': '88212b54d03f194095a8073ad8430dd98b602c114df9766d3002555797867bc9', 'a0b0c527': 'a0b0c52758afe8c939aa3658fa40af42bd08e357c5ed7b49ab5948511ce7cbda', 'bf55b354': 'bf55b354fbcb7c4e19302345fc1e839ee5c7822cc94fca77f3eb316d252026bd', 'cacf9355': 'cacf935505a49e25243e1fe8d38f438727bb8c4a3825cf9f5b3d134f018b4776', 'e2977a84': 'e2977a8428addfe33304300293eac02faf309e4a5db706de8a5de8ff32ed1b08', 'e98fb040': 'e98fb04079bb0ae8b602d2383bfd5ab473d27f2ea365ce7f343656b6aacc4eca', 'eccaddc0': 'eccaddc05616327905b3415dc88295f6f2081fc56b58ae4f571aed1df601b73c'}

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
        return extract_parser374_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser374_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser374_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 424
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser374_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser374_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser374_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser374_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser374_leftovers(*args)
    if prefix in ('122be2bc', '372b2440', '69b4278e', 'bf55b354'):
        assert not events and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e





@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_optional_metadata_absent(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser374_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




def test_payload_semantics():
    capital = selected('0dd9078e')[0]
    assert capital.event_type == 'capital_changed'
    assert (capital.payload['destroyed_count'], capital.payload['issued_count']) == ('100', '100')
    assert capital.payload['issued_fully_paid'] is True
    preferred = selected('122be2bc')[0].payload
    assert preferred['capital'] == "100'000"
    assert preferred['share_classes'] == [
        {'count': '95', 'nominal': "1'000", 'kind': 'registered', 'liquidation_preferred': False},
        {'count': '5', 'nominal': "1'000", 'kind': 'registered', 'liquidation_preferred': True},
    ]
    assert preferred['statutes_date'] == '16.10.2020'
    assert preferred['second_statutes_date'] == '22.10.2020'
    corrected = selected('2cad4436')[0]
    assert corrected.payload['name'] != corrected.payload['previous_name']
    transfer, manager = selected('372b2440')
    assert (transfer.payload['before'], transfer.payload['transferred'], transfer.payload['remaining']) == ('20', '10', '10')
    assert manager.signing == 'Einzelunterschrift'
    assert manager.role == 'Gesellschafterin und Präsidentin der Geschäftsführung'
    assert selected('69b4278e')[0].role == 'gérante unique'
    assert selected('69b4278e')[0].signing == 'Einzelunterschrift'
    dissolved, *liquidators = selected('88212b54')
    assert dissolved.payload['decision_date'] == '11.06.2020'
    assert all(e.role == 'Liquidator' and e.signing == 'Kollektivunterschrift zu zweien' for e in liquidators)
    payment = selected('a0b0c527')[0].payload
    assert (payment['currency'], payment['paid_per_share'], payment['paid_total']) == ('GBP', '0.00', '0.00')
    assert payment['previous_capital'] == "1'000'000.00"
    assert selected('bf55b354')[0].payload['purpose_change_reserved'] is False
    assert [e.role for e in selected('cacf9355')] == ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
    assert selected('cacf9355')[1].payload['previous_role'] == 'Präsident des Verwaltungsrates'
    assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in selected('e2977a84'))
    assert selected('e98fb040')[0].payload['place'] == 'Troistorrents'
    merger = selected('eccaddc0')[0]
    assert merger.event_type == 'company_merged'
    assert merger.payload['claims_subordinated'] is True
    assert merger.payload['wholly_owned'] is True
    assert merger.payload['capital_increase'] is False
    assert merger.payload['share_allocation'] is False
    assert merger.payload['deficit'] == "1'081'220.00"


@pytest.mark.parametrize('prefix', ['122be2bc', '372b2440', '69b4278e', 'bf55b354'])
def test_fragments_require_matching_original_source(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser374_leftovers(*args, source_text='Unrelated.') == ([], args[0])
    assert extract_parser374_leftovers(*args, source_text=kwargs['source_text'] + ' UNKNOWN.') == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('122be2bc', '95 actions', '96 actions'),
    ('372b2440', '20 parts', '21 parts'),
    ('a0b0c527', '1.00 liberate', '2.00 liberate'),
    ('eccaddc0', "1'081'220.00", "1'081'221.00"),
])
def test_invalid_balances_keep_leftover(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser374_leftovers(changed, *args[1:], source_text=kwargs['source_text'].replace(old, new)) == ([], changed)


@pytest.mark.parametrize('version,prefix', [
    (112, 'ac222af5'), (126, 'c1c6cf64'), (133, '6574d7ea'),
    (151, '280bc467'), (165, '54bd1632'), (178, '739dd0b1'),
    (369, '8733db9b'),
])
def test_existing_rules_keep_ownership_even_when_disabled(version, prefix):
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
    assert extract_parser374_leftovers(*args, **kwargs) == ([], args[0])
    with patch.object(parser, 'extract_parser374_leftovers', lambda text, *args, **kwargs: ([], text)):
        assert parse_publication_xml(path(prefix)) == actual
    with patch.object(parser, name, lambda text, *args, **kwargs: ([], text)):
        disabled = parse_publication_xml(path(prefix))
    assert not any(e.rule_id in {case[1] for case in CASES} for e in disabled.events)


@pytest.mark.parametrize('prefix', [
    '0a55ac5e', '13af8ca2', '35846617', '5965b13c', '6fd2616d', '700d20ff',
    '9e4d51cb', 'b42cdb94', 'bc558b02', 'cba82eaa', 'e43765aa', 'f5ea0e9d',
])
def test_parser373_results_unchanged(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser374_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
