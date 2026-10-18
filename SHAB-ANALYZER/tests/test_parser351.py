import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser351 import extract_parser351_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('31b6ec0a', 'fr.text.associate_managers_presidency_changed.v1', 2), ('38d06f88', 'fr.text.branch_non_representative_registration_deleted.v1', 5), ('5ed52fc3', 'fr.text.registered_shares_split_composition.v1', 1), ('615cef26', 'fr.text.foundation_board_members_appointed.v1', 2), ('72b9726e', 'fr.text.deputy_director_role_corrected.v1', 1), ('855bb8ea', 'fr.text.manager_collective_signing_corrected.v1', 1), ('999b4701', 'fr.text.associate_shares_transferred_managers.v1', 3), ('9cfdb36f', 'fr.text.corporate_associate_shares_transferred.v1', 1), ('9e98bf90', 'de.text.sole_proprietorship_reinstated_owner_request.v1', 1), ('a3977920', 'fr.text.associate_share_split.v1', 1), ('ea39d01e', 'fr.text.managers_presidency_corrected.v1', 2), ('f097237d', 'fr.text.directors_now_management_members.v1', 2)]
SUPPLIED_SHA256 = {'31b6ec0a': '31b6ec0a32e81c18130e6a3c9ab4f9ca509604295425be846a63474390929b9f', '38d06f88': '38d06f88be4ffe8f5fc3722c6b18e6e096687ead063c60299e9d7ff4f8da4bc5', '5ed52fc3': '5ed52fc35b27c5bc2b4394a0b5311afb100fe99bb0f6009ab740ed373eaf9909', '615cef26': '615cef266ffde6e81f39a721e3659f478ce24fb74f0a937f46c2d11bec627370', '72b9726e': '72b9726ea79d0fa28c230573626c5d3efc69339f47d8c0d75c8d1bc0a3aa68ed', '855bb8ea': '855bb8ea8f881085c62439315302d8b9d1996239ebabea3599b4c52ab3fcbcce', '999b4701': '999b470181a2b858d83c87893ded3baa7882d969ba1bdf3ebef9c8703b44aee4', '9cfdb36f': '9cfdb36fafc813cf8542d7f8f124ebc05b93bef4e08d5f0c51d987324823537e', '9e98bf90': '9e98bf9008749c03868df012b0eefd1cbfff805f7c8e3700332949238d0be278', 'a3977920': 'a3977920a0880f157f99b65c7aa0925f7e5417993627175f0685f640b5205468', 'ea39d01e': 'ea39d01e429973a343ba95bcda2ca69becd9ee7d4d13503ada4f24d298100612', 'f097237d': 'f097237d65b7977c2eaae311d13835bc4525ca99a879b4e09022d761086a53fc'}

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
        return extract_parser351_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser351_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser351_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 360
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser351_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser351_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser351_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser351_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser351_leftovers(*args)
    assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e


@pytest.mark.parametrize('prefix', ['bcf422aa', '2ee7eb0d', 'c5fa5c4d', 'f2300fb5', '360fedd4', '0ab39892', 'c9b3ebd6', 'a1e7ae61', '6fa3fe10', 'c9637524', 'a60779f4', 'fa9ce006'])
def test_previous_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser351_leftovers', lambda text, *args, **kwargs: ([], text)):
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


def test_payload_and_person_semantics():
    assert [e.role for e in selected('31b6ec0a')] == ['Geschäftsführer', 'Vorsitzender der Geschäftsführung']
    assert all(e.signing == 'Einzelunterschrift' for e in selected('31b6ec0a'))
    assert len({e.person_key for e in selected('38d06f88')}) == 5
    assert all(e.signing is None and e.payload['registration_deleted'] for e in selected('38d06f88'))
    assert all(e.role == 'Stiftungsrat' and e.signing is None for e in selected('615cef26'))
    assert selected('72b9726e')[0].role == 'stellvertretende Direktorin'
    assert selected('855bb8ea')[0].signing == 'Kollektivunterschrift zu zweien'
    assert selected('999b4701')[2].signing is None
    assert selected('9cfdb36f')[0].payload['remaining_count'] == '60'
    assert selected('a3977920')[0].payload['count'] == '200'
    assert [e.role for e in selected('ea39d01e')] == ['Geschäftsführer', 'Vorsitzender der Geschäftsführung']
    assert all(e.role == 'Mitglied der Geschäftsleitung' for e in selected('f097237d'))


@pytest.mark.parametrize('prefix,old,new', [('5ed52fc3', "500'000", "500'001"), ('5ed52fc3', 'Division de 100', 'Division de 101'), ('9cfdb36f', '60 parts', '61 parts'), ('a3977920', '200 parts', '201 parts'), ('999b4701', '18 parts', '0 parts')])
def test_invalid_share_arithmetic_preserved(prefix, old, new):
    _, (args, kwargs) = captured(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser351_leftovers(changed, *args[1:], **kwargs) == ([], changed)
