import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser352 import extract_parser352_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('0863601c', 'fr.text.associate_transfer_manager_president.v1', 3), ('127b7edf', 'fr.text.foundation_officers_unrestricted_collective_signing.v1', 5), ('13345d7d', 'fr.text.ancillary_obligations_mention_deleted_correction.v1', 1), ('1d2d21a9', 'fr.text.sole_proprietor_assets_transferred_for_claim.v1', 1), ('390c063f', 'de.text.covid_moratorium_extended.v1', 1), ('508e1ca0', 'fr.text.foundation_board_members_liquidators.v1', 3), ('5a66d788', 'fr.text.bankruptcy_suspensive_effect_revoked.v1', 1), ('5dab163c', 'de.text.foundation_auditor_exemption_revoked.v1', 1), ('6f8bcc41', 'fr.text.director_appointed_origin_changed.v1', 1), ('7dd23e4e', 'de.text.company_translation_complete.v1', 1), ('990046a6', 'fr.text.branch_mentions_deleted_and_seat_transferred.v1', 1), ('edea6f5d', 'it.text.merger_wholly_owned_available_equity_attestation.v1', 1)]
SUPPLIED_SHA256 = {'508e1ca0': '508e1ca07cd8770ab044cf5693a041fa63fe8adbe07cce321495eb97fec6b60e', '1d2d21a9': '1d2d21a9c5b5d7d872056aef18efc284d0472633fb68af7af5941edf714ee928', '5dab163c': '5dab163cf05605c04df663b2a673e8f91c098246f721d0cfe3478e1a5fb181d5', '13345d7d': '13345d7db376ae161a200e2778dbdfdd3183d4918723990d3822468abc25872f', '5a66d788': '5a66d788ce3c34bda4245bf67d3fbae5632c2f1aec23de88783d828e698792d0', '7dd23e4e': '7dd23e4e183679ae57d621be1fc02c78a12bd072cbc4db26ee601b425ce01e61', '0863601c': '0863601c96a93b97ba98137935f7d6da64bfe1a61f020259486acf56b4deba83', '390c063f': '390c063f786809ae52eea473065270749f95cff0d65610c596606e3bf59c5dda', '127b7edf': '127b7edf39a2ca978a915af4588b31138f8d8ed2e356fdce1c3b27fbe5d08231', '6f8bcc41': '6f8bcc41fb4f58ea66fd931a948efdfc47e3360e1b3cc5daaa76e7482c512cb6', 'edea6f5d': 'edea6f5d581cad01942db1daee1fda9c90e77202df0f0dbe7c50064bf5a7b40d', '990046a6': '990046a69df2f346d1330582264433590e9cc2131a1cd33a250a5fd3f0fc855a'}

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
        return extract_parser352_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser352_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser352_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 412
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser352_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser352_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser352_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser352_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser352_leftovers(*args)
    if prefix == '7dd23e4e':
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', ['bcf422aa', '2ee7eb0d', 'c5fa5c4d', 'f2300fb5', '360fedd4', '0ab39892', 'c9b3ebd6', 'a1e7ae61', '6fa3fe10', 'c9637524', 'a60779f4', 'fa9ce006'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser352_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(path(prefix))
    assert parse_publication_xml(path(prefix)) == baseline
    for old in baseline.events:
        assert Event(**vars(old)) == old


def test_legacy_event_without_optional_payload_attributes():
    old = Event(publication_id='fixture', published_at='', event_type='organization_changed', rule_id='legacy.v1')
    assert old.payload == {} and old.signing is None and old.role is None
    assert Event(**vars(old)) == old




@pytest.mark.parametrize('prefix', ['1f50b356', '255f9981', '3781a2a0', '498a458e', '680ea7b5', '868b9d7d', 'a9b1dc25', 'cf290fb1', 'd065834b', 'd6058d56', 'd6675037', 'e9370ab5'])
def test_parser350_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


@pytest.mark.parametrize('prefix', ['31b6ec0a', '38d06f88', '5ed52fc3', '615cef26', '72b9726e', '855bb8ea', '999b4701', '9cfdb36f', '9e98bf90', 'a3977920', 'ea39d01e', 'f097237d'])
def test_parser351_results_unchanged(prefix):
    test_previous_results_unchanged_without_optional_attributes(prefix)


def test_payload_and_person_semantics():
    assert [e.role for e in selected('0863601c')[1:]] == ['Vorsitzender der Geschäftsführung', 'Geschäftsführer']
    assert selected('0863601c')[2].signing is None
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in selected('127b7edf'))
    assert all(e.role == 'Liquidator' and e.signing is None for e in selected('508e1ca0'))
    assert selected('6f8bcc41')[0].payload['origin'] == 'Signy-Avenex'
    assert selected('7dd23e4e')[0].payload['translation'].endswith('(Switzerland) Ltd')
    assert selected('edea6f5d')[0].payload['capital_increased'] is False
    assert selected('edea6f5d')[0].payload['shares_allocated'] is False


@pytest.mark.parametrize('prefix,old,new', [('0863601c', '100 parts', '0 parts'), ('13345d7d', '26-07-2010', '31-02-2010'), ('5a66d788', '28 août', '32 août'), ('5a66d788', '11h00', '25h00')])
def test_invalid_values_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser352_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_translation_fragment_requires_matching_source():
    _, (args, kwargs) = captured('7dd23e4e')
    assert extract_parser352_leftovers(*args, source_text='Unrelated source') == ([], args[0])


def test_new_payload_facts():
    transfer = selected('0863601c')
    assert transfer[0].payload['count'] == '100'
    assert transfer[0].payload['remaining_count'] == '100'
    assert transfer[2].payload['place'] == 'Viti (Kosovo)'
    assert selected('1d2d21a9')[0].payload['assets'] == "100'000.00"
    assert selected('1d2d21a9')[0].payload['consideration'] == "100'000.00"
    assert selected('390c063f')[0].payload['months'] == '3'
    assert selected('390c063f')[0].payload['end_date'] == '31.12.2020'
    assert selected('5a66d788')[0].payload['time'] == '11h00'
    assert selected('5dab163c')[0].payload['revocation_date'] == '16.07.2020'
    assert selected('990046a6')[0].payload['previous_place'] == 'Genève'
    assert selected('990046a6')[0].payload['place'] == 'Lancy'
    assert selected('edea6f5d')[0].payload['assets'] == "3'407'666.00"
    assert selected('edea6f5d')[0].payload['liabilities'] == "3'190'130.00"
