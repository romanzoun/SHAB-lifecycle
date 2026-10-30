import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser360 import extract_parser360_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [('26b61e10', 'fr.text.foundation_members_without_signing.v1', 2), ('395a050f', 'de.text.definitive_composition_moratorium_extended.v1', 1), ('3ce26082', 'fr.text.board_member_name_corrected.v1', 2), ('565e7045', 'fr.text.asset_transfer_with_two_amendments.v1', 1), ('6a4a5e9b', 'de.text.board_delegate_role_changed.v1', 1), ('799d3293', 'fr.text.association_dissolved_by_general_meeting.v1', 3), ('843c84b0', 'fr.text.share_transfer_new_presiding_manager.v1', 2), ('979b245c', 'fr.text.authorized_capital_clause_removed_amount_reached.v1', 1), ('bbd12670', 'de.text.office_deleted_additional_address_added.v1', 1), ('d9ab9629', 'de.text.previous_share_capital_stated.v1', 1), ('eed5c760', 'fr.text.formal_statutes_registered_seat_indication.v1', 1), ('f7fe65f9', 'fr.text.person_name_corrected_notice_reference.v1', 1)]
SUPPLIED_SHA256 = {'26b61e10': '26b61e106965662eac02e765b3dc35bc9c2999f491cf090f1090fc3e40b6d118', '395a050f': '395a050f68b3916f2ab2a1f7685a2545ba4efb9effe1dde0fcfbb4cf6523f821', '3ce26082': '3ce26082a5264c6729d5ea4c701d93be061c16394a5a81b2c970c3c749a3936d', '565e7045': '565e704568202bfa49b1e13d1d1fff11307afd77f7d1f5333c493e9344552772', '6a4a5e9b': '6a4a5e9b623bf396e316a61b6e625ddfe8579cd3c6adbd4b7b23bf1b51a246ba', '799d3293': '799d32935feabf63ae8b0455086fa13140a2d68c93957e2e9b5cfe2a6a596901', '843c84b0': '843c84b06ded6bc3a62ad1b0073e61faadd3cdd0d21302d06afcb7731a36825f', '979b245c': '979b245cba2adef60ebf042d37e7964d255e3109e11bbabb40759677517e6688', 'bbd12670': 'bbd1267069bdd748d4806629ea6c66ad940c267540801355615c17e631ae1ac6', 'd9ab9629': 'd9ab96293bee576bf757a2bee31f5ba66933e521b1ea722f648ed3f930702a7a', 'eed5c760': 'eed5c76065880af86fc11cb327a45f635df4a85f0dda484c0c71c614a6c6e7ad', 'f7fe65f9': 'f7fe65f9cac9be458583f04a8f96890c91fd560877002048375055cd667f1004'}

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
        return extract_parser360_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser360_leftovers', capture):
        result = parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return result, calls[0]


def selected(prefix):
    _, (args, kwargs) = captured(prefix)
    return extract_parser360_leftovers(*args, **kwargs)[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete_and_legacy_events_preserved(prefix, rule, count):
    import shab_analyzer.parse as parser
    fixture = path(prefix)
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == fixture.stem
    result, _ = captured(prefix)
    assert PARSER_VERSION == 442
    assert result.status == 'FULLY_PARSED' and not result.leftover_text
    assert len(selected(prefix)) == count
    assert any(e.rule_id == rule for e in selected(prefix))
    with patch.object(parser, 'extract_parser360_leftovers', lambda text, *args, **kwargs: ([], text)):
        baseline = parse_publication_xml(fixture)
    assert result.events == baseline.events + selected(prefix)
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected(prefix))


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    events, leftover = extract_parser360_leftovers(changed, *args[1:], **kwargs)
    assert not events and leftover == changed


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    _, (args, kwargs) = captured(prefix)
    events, leftover = extract_parser360_leftovers(args[0], 'en', *args[2:], **kwargs)
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
        events, leftover = extract_parser360_leftovers(changed, *args[1:], **kwargs)
        assert not events and leftover == changed
    events, leftover = extract_parser360_leftovers(*args)
    if prefix in ('799d3293', '843c84b0'):
        assert events == [] and leftover == args[0]
    else:
        assert len(events) == count and not leftover
    for e in selected(prefix):
        assert Event(**vars(e)) == e




@pytest.mark.parametrize('prefix', ['0ff8b861', '195e4e8b', '2a96a47b', '48bf8c0f', '618c7acd', '824b7855', '9458794a', '9ca87f86', 'a05c6e34', 'b2ad6bc5', 'd55489e4', 'eef5e104'])
def test_parser359_results_unchanged_without_optional_attributes(prefix):
    import shab_analyzer.parse as parser
    with patch.object(parser, 'extract_parser360_leftovers', lambda text, *args, **kwargs: ([], text)):
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
    events, leftover = extract_parser360_leftovers(*args[:4], None, None, None, **kwargs)
    assert len(events) == count and not leftover
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    assert [e.payload for e in events] == [e.payload for e in selected(prefix)]



def test_payload_semantics():
    assert [e.signing for e in selected('26b61e10')] == ['ohne Zeichnungsberechtigung'] * 2
    assert len({e.person_key for e in selected('26b61e10')}) == 2
    assert selected('395a050f')[0].payload['end_date'] == '26.01.2021'
    assert all(e.payload['previous_name'] != e.payload['name'] for e in selected('3ce26082'))
    transfer = selected('565e7045')[0].payload
    assert transfer['assets'] == "39'173'834" and transfer['consideration'] == "4'243'214"
    assert selected('6a4a5e9b')[0].signing == 'Kollektivunterschrift zu zweien'
    assert [e.role for e in selected('799d3293')[1:]] == ['Liquidator'] * 2
    assert selected('843c84b0')[0].payload['transferred'] == '15'
    assert selected('843c84b0')[1].signing == 'Einzelunterschrift'
    assert selected('979b245c')[0].payload['authorization_date'] == '29.09.2017'
    assert selected('bbd12670')[0].payload['address'] != selected('bbd12670')[0].payload['previous_address']
    assert selected('d9ab9629')[0].payload['previous_capital'] == "100'000.00"
    assert selected('eed5c760')[0].payload['place'] == 'La Grande Béroche'
    assert selected('f7fe65f9')[0].signing is None


@pytest.mark.parametrize('prefix', ['799d3293', '843c84b0'])
def test_truncated_clauses_require_original_context(prefix):
    _, (args, kwargs) = captured(prefix)
    assert extract_parser360_leftovers(*args, source_text='unrelated') == ([], args[0])
    changed = kwargs['source_text'].replace('avec signature individuelle', 'sans signature').replace('avec signature collective à deux', 'sans signature')
    assert extract_parser360_leftovers(*args, source_text=changed) == ([], args[0])


@pytest.mark.parametrize('text', ['', 'Unsupported clause', '   '])
def test_empty_and_unknown_residuals(text):
    assert extract_parser360_leftovers(text, 'fr', 'fixture', '', None, None, None) == ([], text.strip())
